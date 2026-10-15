from __future__ import annotations

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event

import pytest
from fastapi.testclient import TestClient
from ultimate_ai_agent.api.rate_limits import reset_api_rate_limit_state

import ultimate_ai_agent.api.app as api_app
import ultimate_ai_agent.core.chat.local_turn as turns
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.control_center.backend_truth import (
    backend_instance_ref, build_control_center_backend_truth,
)
from ultimate_ai_agent.core.local_model_management.gateway import (
    FakeM164GatewayTransport, M164ChatCompletionRequest, build_m164_gateway_model_from_env,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository
from ultimate_ai_agent.core.time import utc_now


@pytest.fixture
def lane(monkeypatch, tmp_path):
    reset_api_rate_limit_state()
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "1")
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "fixture-gateway-value")
    monkeypatch.setenv("UAA_LLAMA_CPP_MODEL_ID", "fixture-local-model")
    monkeypatch.setenv("UAA_LLAMA_CPP_BASE_URL", "http://127.0.0.1:1234")
    monkeypatch.setenv("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", "0")
    monkeypatch.setenv("UAA_API_LOCAL_BEARER", "fixture-session-value")
    monkeypatch.setenv("UAA_BUILD_COMMIT", "7" * 40)
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "turn-state"))
    repo = FounderLoopRepository(tmp_path / "turn-state", seed_defaults=False)
    request = M164ChatCompletionRequest(
        model="fixture-local-model", messages=[{"role": "user", "content": "x" * 8}],
    )
    yield repo, request, FakeM164GatewayTransport(content="y" * 12)
    reset_api_rate_limit_state()


def _send(lane, **overrides):
    repo, request, transport = lane
    arguments = {
        "confirmed": True,
        "idempotency_key_ref": "idempotency-ref:chat:one",
        "backend_revision_ref": build_identity().commit_ref,
        "expected_backend_instance_ref": backend_instance_ref(),
        "gateway_model": build_m164_gateway_model_from_env(),
        "repository": repo,
        "transport": transport,
        **overrides,
    }
    return turns.send_local_conversation_turn(request, **arguments)


def _attempt(key="idempotency-ref:chat:one"):
    return "chat-attempt-ref:sha256:" + hashlib.sha256(key.encode()).hexdigest()


def _headers(lane):
    truth = build_control_center_backend_truth(repo=lane[0], identity=build_identity())
    return {
        "Authorization": "Bearer fixture-session-value",
        "X-UAA-Idempotency-Key": "idempotency-ref:chat:one",
        "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
        "X-UAA-Expected-Backend-Revision-Ref": build_identity().commit_ref,
        "X-UAA-Expected-Backend-Instance-Ref": backend_instance_ref(),
        "X-UAA-Expected-Backend-Truth-Ref": truth["envelope_integrity_ref"],
    }


def test_explicit_send_captures_validates_and_commits_exact_scope_before_transport(lane):
    repo, request, transport = lane
    authority = LocalApprovalAuthority()
    result = _send(lane, approval_authority=authority)
    proof = result["uaa_safety"]["local_turn_approval"]
    assert proof["attempt_ref"] == _attempt()
    assert proof["exact_approval_validated"] is True
    assert proof["durable_start_recorded"] is True
    assert proof["status"] == "completed"
    assert len(transport.calls) == 1
    assert transport.calls[0].max_tokens == 1024
    grant = authority.get_grant(proof["approval_ref"])
    assert grant.subject_id == proof["scope_ref"]
    assert grant.approved_actions == ["send_one_local_chat_turn"]
    assert turns.inspect_local_turn_attempt(_attempt(), repository=repo)["status"] == "completed"
    with repo._connect() as conn:
        row = dict(conn.execute("SELECT * FROM chat_local_turn_attempts").fetchone())
    stored = json.dumps(row)
    assert request.messages[0].content not in stored
    assert transport.content not in stored
    assert "http://" not in stored
    assert "fixture-local-model" not in stored
    assert "fixture-session-value" not in stored


@pytest.mark.parametrize("confirmed", [False, None, "true", 1])
def test_core_requires_literal_confirmation_before_any_authority_or_transport(lane, confirmed):
    with pytest.raises(turns.LocalTurnError, match="CONFIRMATION_REQUIRED"):
        _send(lane, confirmed=confirmed)
    assert not lane[2].calls
    assert turns.inspect_local_turn_attempt(_attempt(), repository=lane[0])["status"] == "missing"


@pytest.mark.parametrize("confirmation", [None, "true", "send-one-local-turn.v0"])
def test_api_session_and_diagnostic_probe_cannot_authorize_a_turn(lane, monkeypatch, confirmation):
    import ultimate_ai_agent.core.local_model_management.gateway as gateway

    monkeypatch.setattr(gateway, "StdlibM164LlamaCppGatewayTransport", lambda: lane[2])
    headers = _headers(lane)
    if confirmation is not None:
        headers["X-UAA-Operator-Confirmed"] = confirmation
    client = TestClient(api_app.app)
    assert client.get("/v1/models", headers=headers).status_code == 200
    denied = client.post("/v1/chat/completions", headers=headers, json=lane[1].model_dump())
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "LOCAL_TURN_CONFIRMATION_REQUIRED"
    assert not lane[2].calls
    assert turns.inspect_local_turn_attempt(_attempt(), repository=lane[0])["status"] == "missing"


@pytest.mark.parametrize("alias", ["X-UAA-Idempotency-Key", "X-UAA-Idempotency-Ref"])
def test_api_explicit_send_uses_existing_aliases_and_denies_replay(lane, monkeypatch, alias):
    import ultimate_ai_agent.core.local_model_management.gateway as gateway

    monkeypatch.setattr(gateway, "StdlibM164LlamaCppGatewayTransport", lambda: lane[2])
    headers = _headers(lane)
    headers[alias] = headers.pop("X-UAA-Idempotency-Key")
    headers["X-UAA-Operator-Confirmed"] = turns.LOCAL_TURN_CONFIRMATION
    client = TestClient(api_app.app)
    reply = client.post("/v1/chat/completions", headers=headers, json=lane[1].model_dump())
    assert reply.status_code == 200
    assert reply.json()["uaa_safety"]["local_turn_approval"]["exact_approval_validated"] is True
    replay = client.post("/v1/chat/completions", headers=headers, json=lane[1].model_dump())
    assert replay.status_code == 409
    assert len(lane[2].calls) == 1


def test_api_credential_collision_cannot_select_legacy_lane(lane, monkeypatch):
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_KEY", "fixture-session-value")
    client = TestClient(api_app.app)
    headers = _headers(lane)
    assert client.post("/v1/chat/completions", headers=headers, json=lane[1].model_dump()).status_code == 403
    headers.pop("X-UAA-Control-Center-Mutation-Binding")
    assert client.post("/v1/chat/completions", headers=headers, json=lane[1].model_dump()).status_code == 409
    assert not lane[2].calls


def test_api_conflicting_attempt_aliases_are_denied_before_transport(lane):
    headers = _headers(lane)
    headers["X-UAA-Operator-Confirmed"] = turns.LOCAL_TURN_CONFIRMATION
    headers["X-UAA-Idempotency-Ref"] = "idempotency-ref:chat:other"
    response = TestClient(api_app.app).post("/v1/chat/completions", headers=headers, json=lane[1].model_dump())
    assert response.status_code == 400
    assert not lane[2].calls


@pytest.mark.parametrize("mutation", ["body", "model", "revision", "instance", "restart"])
def test_replay_or_rebound_attempt_never_reaches_transport(lane, monkeypatch, mutation):
    _send(lane)
    overrides = {}
    if mutation == "body":
        lane[1].messages[0].content = "z" * 9
    if mutation == "model":
        monkeypatch.setenv("UAA_LLAMA_CPP_MODEL_ID", "fixture-other-model")
        lane[1].model = "fixture-other-model"
    if mutation == "revision":
        monkeypatch.setenv("UAA_BUILD_COMMIT", "8" * 40)
    if mutation == "instance":
        import ultimate_ai_agent.core.control_center.backend_truth as truth
        monkeypatch.setattr(truth, "_BACKEND_INSTANCE_REF", "backend-instance-ref:control-center:" + "b" * 32)
    if mutation == "restart":
        monkeypatch.setattr(turns, "_COMMITMENT_KEY", bytes(range(32)))
        overrides["repository"] = FounderLoopRepository(lane[0].state_dir, seed_defaults=False)
    with pytest.raises(turns.LocalTurnError, match="ALREADY_ATTEMPTED"):
        _send(lane, **overrides)
    assert len(lane[2].calls) == 1


def test_concurrent_replay_is_denied_after_durable_start(lane):
    entered, finish = Event(), Event()

    class PausedTransport(FakeM164GatewayTransport):
        def chat_completions(self, *args, **kwargs):
            assert turns.inspect_local_turn_attempt(_attempt(), repository=lane[0])["status"] == "started"
            entered.set()
            assert finish.wait(5)
            return super().chat_completions(*args, **kwargs)

    transport = PausedTransport()
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(_send, lane, transport=transport)
        try:
            assert entered.wait(5)
            with pytest.raises(turns.LocalTurnError, match="ALREADY_ATTEMPTED"):
                _send(lane)
        finally:
            finish.set()
        assert future.result()["uaa_safety"]["local_turn_approval"]["status"] == "completed"
    assert len(transport.calls) == 1
    assert not lane[2].calls


@pytest.mark.parametrize("failure", ["unknown", "expired", "revoked", "resources"])
def test_invalid_exact_approval_cannot_start(lane, failure):
    class DeniedAuthority(LocalApprovalAuthority):
        def grant(self, *args, **kwargs):
            if failure == "expired":
                kwargs["expires_at"] = utc_now() - timedelta(seconds=1)
            result = super().grant(*args, **kwargs)
            if failure == "unknown":
                self.remove_grant_for_rollback(result.approval_ref)
            if failure == "revoked":
                self.revoke(result.approval_ref, "fixture-revocation")
            if failure == "resources":
                result.approved_resource_refs = []
                self.load_grant_for_validation(result)
            return result

    with pytest.raises(turns.LocalTurnError, match="APPROVAL_DENIED"):
        _send(lane, approval_authority=DeniedAuthority())
    assert not lane[2].calls
    assert turns.inspect_local_turn_attempt(_attempt(), repository=lane[0])["status"] == "missing"


def test_storage_failure_before_start_never_calls_transport(lane, monkeypatch):
    def fail(_repo):
        raise sqlite3.OperationalError("fixture-storage-failure")

    monkeypatch.setattr(turns, "_ensure_schema", fail)
    with pytest.raises(turns.LocalTurnError):
        _send(lane)
    assert not lane[2].calls


@pytest.mark.parametrize("failure", ["transport", "sanitize", "settle", "crash"])
def test_post_start_failure_never_reopens_attempt(lane, monkeypatch, failure):
    class FailedTransport(FakeM164GatewayTransport):
        def chat_completions(self, *args, **kwargs):
            result = super().chat_completions(*args, **kwargs)
            if failure == "transport":
                raise ValueError("fixture-private-transport-detail")
            if failure == "crash":
                raise KeyboardInterrupt
            if failure == "sanitize":
                result["choices"] = []
            return result

    def fail_settle(*args):
        raise sqlite3.OperationalError("fixture-private-storage-detail")

    transport = FailedTransport()
    if failure == "settle":
        monkeypatch.setattr(turns, "_settle", fail_settle)
    with pytest.raises(KeyboardInterrupt if failure == "crash" else turns.LocalTurnError):
        _send(lane, transport=transport)
    assert turns.inspect_local_turn_attempt(_attempt(), repository=lane[0])["status"] in {"started", "outcome_uncertain"}
    with pytest.raises(turns.LocalTurnError, match="ALREADY_ATTEMPTED"):
        _send(lane, transport=transport)
    assert len(transport.calls) == 1


@pytest.mark.parametrize("invalid", ["system", "empty", "null", "order", "count", "size", "temperature", "limit", "tools"])
def test_server_enforces_ordinary_turn_bounds_even_without_the_shell(lane, invalid):
    request = lane[1]
    if invalid == "system":
        request.messages[0].role = "system"
    if invalid == "empty":
        request.messages[0].content = " "
    if invalid == "null":
        request.messages[0].content = None
    if invalid == "order":
        request.messages.append(request.messages[0].model_copy())
    if invalid == "count":
        request.messages *= 65
    if invalid == "size":
        request.messages[0].content = "x" * 64_001
    if invalid == "temperature":
        request.temperature = float("nan")
    if invalid == "limit":
        request.max_tokens = 1025
    if invalid == "tools":
        request.tools = []
    with pytest.raises(turns.LocalTurnError, match="REQUEST_DENIED"):
        _send(lane)
    assert not lane[2].calls


def test_follow_up_uses_separate_explicit_attempt_with_context(lane):
    first = _send(lane)
    lane[1].messages.extend([
        lane[1].messages[0].model_copy(update={"role": "assistant", "content": first["choices"][0]["message"]["content"]}),
        lane[1].messages[0].model_copy(update={"content": "z" * 8}),
    ])
    lane[2].content = "w" * 12
    second = _send(lane, idempotency_key_ref="idempotency-ref:chat:two")
    assert second["uaa_safety"]["message_count"] == 3
    assert len(lane[2].calls) == 2
    assert first["uaa_safety"]["local_turn_approval"]["scope_ref"] != second["uaa_safety"]["local_turn_approval"]["scope_ref"]


def test_disable_and_changed_target_fail_before_transport(lane, monkeypatch):
    previous = build_m164_gateway_model_from_env()
    monkeypatch.setenv("UAA_LLAMA_CPP_BASE_URL", "http://127.0.0.1:9999")
    with pytest.raises(turns.LocalTurnError, match="TARGET_CHANGED"):
        _send(lane, gateway_model=previous)
    monkeypatch.setenv("UAA_LLAMA_CPP_GATEWAY_ENABLED", "0")
    with pytest.raises(turns.LocalTurnError, match="DISABLED"):
        _send(lane)
    assert not lane[2].calls


def test_openapi_retains_operation_and_exposes_explicit_turn_confirmation():
    route = api_app.app.openapi()["paths"]["/v1/chat/completions"]["post"]
    assert route["operationId"] == "post_v1_chat_completions"
    assert any(p["name"] == "x-uaa-operator-confirmed" for p in route["parameters"])
    assert {"403", "409", "503"}.issubset(route["responses"])


def test_history_capacity_fails_closed_without_retiring_old_replay_keys(lane, monkeypatch):
    monkeypatch.setattr(turns, "LOCAL_TURN_HISTORY_LIMIT", 1)
    _send(lane)
    with pytest.raises(turns.LocalTurnError, match="HISTORY_FULL"):
        _send(lane, idempotency_key_ref="idempotency-ref:chat:two")
    assert len(lane[2].calls) == 1


def test_local_model_transport_never_honors_external_proxy_environment(lane, monkeypatch):
    from ultimate_ai_agent.core.local_model_management import gateway

    destinations = []

    def capture_without_socket(_handler, request):
        destinations.append(request.host)
        raise ValueError("fixture-stop-before-socket")

    monkeypatch.setenv("http_proxy", "http://proxy.invalid:3128")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("no_proxy", "")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(gateway.request.HTTPHandler, "http_open", capture_without_socket)
    with pytest.raises(ValueError, match="fixture-stop-before-socket"):
        gateway.StdlibM164LlamaCppGatewayTransport().chat_completions(
            build_m164_gateway_model_from_env(), lane[1], api_key="fixture-backend-value",
        )
    assert destinations == ["127.0.0.1:1234"]
