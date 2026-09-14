from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.finance_workspace import (
    FINANCE_WORKSPACE_MAX_BODY_BYTES,
    FINANCE_WORKSPACE_PATH,
    get_finance_workspace,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.build_identity import build_identity
from ultimate_ai_agent.core.control_center.backend_truth import (
    backend_instance_ref,
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.workspace import (
    FinanceWorkspace,
    FinanceWorkspaceConfiguration,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


ORIGIN = "http://127.0.0.1:5173"
SHA = "8" * 40


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    monkeypatch.setenv("UAA_BUILD_COMMIT", SHA)
    workspace = FinanceWorkspace(
        FinanceWorkspaceConfiguration(tmp_path / "book", tmp_path / "helper", "a" * 64),
        crypto_backend=InMemoryFinanceCryptoBackend(),
    )
    app.dependency_overrides[get_finance_workspace] = lambda: workspace
    truth = build_control_center_backend_truth(
        repo=FounderLoopRepository(tmp_path / "truth"),
        identity=build_identity(env={"UAA_BUILD_COMMIT": SHA}),
    )
    headers = {
        "Origin": ORIGIN,
        "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1",
        "X-UAA-Expected-Backend-Revision-Ref": f"commit-ref:git:{SHA}",
        "X-UAA-Expected-Backend-Instance-Ref": backend_instance_ref(),
        "X-UAA-Expected-Backend-Truth-Ref": truth["envelope_integrity_ref"],
    }
    try:
        yield TestClient(app), workspace, headers
    finally:
        app.dependency_overrides.pop(get_finance_workspace, None)


def _intent(operation="create", revision=0, suffix="create", **fields):
    return {
        "operation": operation,
        "expected_revision": revision,
        "request_ref": f"request-ref:finance:api:{suffix}",
        "idempotency_ref": f"idempotency-ref:finance:api:{suffix}",
        **fields,
    }


def _prepare(boundary, intent):
    client, _workspace, headers = boundary
    bound = {**headers, "X-UAA-Idempotency-Key": intent["idempotency_ref"]}
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/preview", json=intent, headers=bound
    )
    assert response.status_code == 200, response.text
    return response.json(), bound


def _commit(boundary, intent):
    prepared, headers = _prepare(boundary, intent)
    response = boundary[0].post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert response.status_code == 200, response.text
    return prepared, response.json(), headers


def test_api_setup_import_review_reopen_replay_and_undo(boundary):
    client, workspace, _headers = boundary
    initial = client.get(FINANCE_WORKSPACE_PATH)
    assert initial.status_code == 200
    assert initial.json()["status"] == "book_setup_required"
    assert initial.headers["cache-control"] == "no-store"
    assert not workspace.configuration.repository_dir.exists()
    _commit(boundary, _intent())
    _commit(boundary, _intent("import_commit", 1, "import"))
    read = client.get(FINANCE_WORKSPACE_PATH).json()
    assert read["item_count"] == 2
    prepared, result, headers = _commit(
        boundary,
        _intent(
            "review_decision",
            2,
            "review",
            review_item_ref=read["review_items"][0]["review_item_ref"],
            decision="confirm",
        ),
    )
    reopened = client.get(FINANCE_WORKSPACE_PATH).json()
    assert reopened["review_items"][0]["state"] == "confirmed"
    replay = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert replay.status_code == 200
    assert replay.json()["receipt"]["replayed"] is True
    assert replay.json()["receipt"]["receipt_ref"] == result["receipt"]["receipt_ref"]
    _commit(
        boundary,
        _intent(
            "review_undo",
            3,
            "undo",
            review_item_ref=reopened["review_items"][0]["review_item_ref"],
            compensates_event_ref=reopened["review_items"][0]["effective_decision_ref"],
        ),
    )
    final = client.get(FINANCE_WORKSPACE_PATH).json()
    assert final["review_items"][0]["state"] == "needs_review"
    assert final["history_count"] == 2


def test_api_authentication_is_required_even_for_setup_status(boundary, monkeypatch):
    client, workspace, _headers = boundary
    monkeypatch.delenv("UAA_API_LOCAL_AUTH_DISABLED_FOR_DEV_ONLY", raising=False)
    bearer = uuid4().hex
    monkeypatch.setenv("UAA_API_LOCAL_BEARER", bearer)
    response = client.get(FINANCE_WORKSPACE_PATH)
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"
    assert (
        client.get(
            FINANCE_WORKSPACE_PATH, headers={"Authorization": f"Bearer {bearer}"}
        ).status_code
        == 200
    )
    assert not workspace.configuration.repository_dir.exists()


@pytest.mark.parametrize("route", ["preview", "refresh", "commit"])
def test_api_always_requires_current_backend_identity(boundary, route):
    client, workspace, headers = boundary
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/{route}",
        json={},
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:finance:missing-binding"},
    )
    assert response.status_code == 409
    changed = {
        **headers,
        "X-UAA-Expected-Backend-Instance-Ref": "backend-instance-ref:stale",
    }
    stale = client.post(f"{FINANCE_WORKSPACE_PATH}/{route}", json={}, headers=changed)
    assert stale.status_code == 409
    assert stale.headers["access-control-allow-origin"] == ORIGIN
    assert not workspace.configuration.repository_dir.exists()


@pytest.mark.parametrize("confirmation", [None, "false", "1", "TRUE"])
def test_api_requires_literal_confirmation_of_exact_preparation(boundary, confirmation):
    prepared, headers = _prepare(boundary, _intent())
    if confirmation is not None:
        headers["X-UAA-Operator-Confirmed"] = confirmation
    response = boundary[0].post(
        f"{FINANCE_WORKSPACE_PATH}/commit", json=prepared, headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"]["commit_outcome"] == "not_attempted"
    assert not boundary[1].configuration.repository_dir.exists()


def test_idempotency_aliases_and_body_are_exactly_bound(boundary):
    client, workspace, headers = boundary
    request = _intent()
    for extra, expected_status in (
        ({}, 428),
        ({"X-UAA-Idempotency-Key": "idempotency-ref:finance:other"}, 409),
        (
            {
                "X-UAA-Idempotency-Key": request["idempotency_ref"],
                "X-UAA-Idempotency-Ref": "idempotency-ref:finance:conflict",
            },
            400,
        ),
    ):
        response = client.post(
            f"{FINANCE_WORKSPACE_PATH}/preview",
            json=request,
            headers={**headers, **extra},
        )
        assert response.status_code == expected_status
    assert not workspace.configuration.repository_dir.exists()


@pytest.mark.parametrize(
    "payload",
    [
        b" " * (FINANCE_WORKSPACE_MAX_BODY_BYTES + 1),
        b"[" * 10_000 + b"0" + b"]" * 10_000,
        ("[" * 100 + "0" + "]" * 100).encode("utf-16"),
    ],
)
def test_body_guard_rejects_before_decode_with_cors_and_no_store(boundary, payload):
    client, workspace, headers = boundary
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/preview",
        content=payload,
        headers={
            **headers,
            "Content-Type": "application/json",
            "X-UAA-Idempotency-Key": "idempotency-ref:finance:body-bound",
        },
    )
    assert response.status_code == 413
    assert response.json()["code"] == "FINANCE_WORKSPACE_REQUEST_BODY_LIMIT_EXCEEDED"
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert response.headers["cache-control"] == "no-store"
    assert not workspace.configuration.repository_dir.exists()


def test_body_guard_ignores_structural_characters_inside_json_strings(boundary):
    client, _workspace, headers = boundary
    payload = _intent()
    payload["request_ref"] = "request-ref:" + "[" * 100
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/preview",
        json=payload,
        headers={**headers, "X-UAA-Idempotency-Key": payload["idempotency_ref"]},
    )
    assert response.status_code == 422


def test_unexpected_commit_failure_does_not_claim_no_change_or_leak_details(
    boundary, monkeypatch
):
    prepared, headers = _prepare(boundary, _intent())

    def fail(*args, **kwargs):
        raise RuntimeError("sensitive implementation diagnostic must not leave Core")

    monkeypatch.setattr(boundary[1], "commit", fail)
    response = boundary[0].post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**headers, "X-UAA-Operator-Confirmed": "true"},
    )
    assert response.status_code == 503
    assert response.json()["detail"]["commit_outcome"] == "unconfirmed"
    assert "sensitive implementation" not in response.text


def test_finance_openapi_and_manifest_publish_exact_contracts(boundary):
    client, _workspace, _headers = boundary
    schema = client.get("/openapi.json").json()
    for action in ("preview", "refresh", "commit"):
        route = schema["paths"][f"{FINANCE_WORKSPACE_PATH}/{action}"]["post"]
        body_limit = route["responses"]["413"]["content"]["application/json"]["schema"]
        assert body_limit["$ref"].endswith("FinanceWorkspaceBodyLimitResponse")
        parameters = {item["name"]: item for item in route["parameters"]}
        for header in (
            "X-UAA-Expected-Backend-Revision-Ref",
            "X-UAA-Expected-Backend-Instance-Ref",
            "X-UAA-Expected-Backend-Truth-Ref",
            "X-UAA-Control-Center-Mutation-Binding",
        ):
            assert parameters[header]["in"] == "header"
            assert parameters[header]["required"] is True
        assert "x-uaa-idempotency-key" in parameters
        assert "x-uaa-idempotency-ref" in parameters
    manifest = build_api_manifest(app)
    routes = [
        route
        for route in manifest.routes
        if route.path.startswith(FINANCE_WORKSPACE_PATH)
    ]
    assert len(routes) == 4
    for route in routes:
        assert route.auth_posture == "protected_local_bearer_required"
        assert route.blocked_from_production is True
        assert route.side_effect_class == "local_dev_workspace_only"
        if route.method == "POST":
            assert route.rate_limit_targeted is True
            assert route.rate_limit_group == "finance_workspace"
        else:
            assert route.rate_limit_targeted is False
        if route.path.endswith("/commit"):
            assert route.route_classification == "mutating_requires_authority"
            assert route.idempotency_enforcement == "route_owned_durable_replay"
            assert (
                route.durable_idempotency_owner_ref
                == "idempotency-owner:finance-protected-repository-receipts:v1"
            )
        else:
            assert route.route_classification == "local_sensitive"
    assert len({route.operation_id for route in routes}) == 4


def test_finance_originless_commit_cannot_bypass_idempotency_or_backend_binding(boundary):
    client, workspace, _headers = boundary
    assert client.post(f"{FINANCE_WORKSPACE_PATH}/commit", json={}).status_code == 428
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json={},
        headers={"X-UAA-Idempotency-Key": "idempotency-ref:finance:originless"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "BACKEND_TRUTH_MUTATION_PROVENANCE_MISMATCH"
    assert not workspace.configuration.repository_dir.exists()


def test_finance_exact_post_routes_share_a_bounded_request_budget(boundary, monkeypatch):
    from ultimate_ai_agent.api.rate_limits import (
        API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV,
        reset_api_rate_limit_state,
    )

    reset_api_rate_limit_state()
    monkeypatch.setenv(API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV, "2")
    client, workspace, headers = boundary
    prepared, bound = _prepare(boundary, _intent())
    response = client.post(
        f"{FINANCE_WORKSPACE_PATH}/refresh", json=prepared, headers=bound
    )
    # Create is not an eligible review refresh; the rejected request still counts.
    assert response.status_code == 409
    denied = client.post(
        f"{FINANCE_WORKSPACE_PATH}/commit",
        json=prepared,
        headers={**bound, "X-UAA-Operator-Confirmed": "true"},
    )
    assert denied.status_code == 429
    assert denied.json()["rate_limit_group"] == "finance_workspace"
    assert denied.headers["access-control-allow-origin"] == ORIGIN
    assert denied.headers["cache-control"] == "no-store"
    assert not workspace.configuration.repository_dir.exists()
    assert client.get(FINANCE_WORKSPACE_PATH, headers=headers).status_code == 200
