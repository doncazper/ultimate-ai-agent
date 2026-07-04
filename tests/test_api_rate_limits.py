from fastapi.testclient import TestClient

from tests.m7_helpers import local_profile, policy, route_request
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.local_auth import (
    LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV,
    LOCAL_API_BEARER_ENV,
)
from ultimate_ai_agent.api.rate_limits import (
    API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV,
    API_TARGETED_RATE_LIMIT_POLICY_REF,
    API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV,
    reset_api_rate_limit_state,
    route_rate_limit_group,
)


IDEMPOTENCY_HEADERS = {"X-UAA-Idempotency-Key": "idempotency:test-p1-085"}


def _model_route_payload(prompt_summary: str = "safe route summary") -> dict:
    payload = route_request(
        profiles=[local_profile()],
        routing_policy=policy(prefer_local=True),
    ).model_dump(mode="json")
    payload["prompt_summary"] = prompt_summary
    return payload


def _client(monkeypatch):
    reset_api_rate_limit_state()
    monkeypatch.setenv(API_TARGETED_RATE_LIMIT_MAX_REQUESTS_ENV, "1")
    monkeypatch.setenv(API_TARGETED_RATE_LIMIT_WINDOW_SECONDS_ENV, "60")
    return TestClient(app)


def test_targeted_route_returns_redacted_429_after_local_limit(monkeypatch) -> None:
    client = _client(monkeypatch)

    first = client.post(
        "/models/route/preview",
        json=_model_route_payload("raw prompt should not echo"),
    )
    second = client.post(
        "/models/route/preview",
        json=_model_route_payload("raw prompt should not echo"),
    )

    assert first.status_code != 429
    assert second.status_code == 429
    body = second.json()
    assert body["code"] == "API_TARGETED_RATE_LIMITED"
    assert body["policy_ref"] == API_TARGETED_RATE_LIMIT_POLICY_REF
    assert body["rate_limit_group"] == "local_model_validation"
    assert body["retry_after_seconds"] >= 1
    assert second.headers["Retry-After"] == str(body["retry_after_seconds"])
    assert second.headers["X-UAA-Rate-Limit-Policy"] == API_TARGETED_RATE_LIMIT_POLICY_REF
    assert second.headers["X-Content-Type-Options"] == "nosniff"
    assert "raw prompt should not echo" not in second.text


def test_targeted_429_exposes_local_loopback_cors_headers(monkeypatch) -> None:
    client = _client(monkeypatch)
    headers = {"Origin": "http://localhost:5173"}

    client.post(
        "/models/route/preview",
        headers=headers,
        json=_model_route_payload(),
    )
    response = client.post(
        "/models/route/preview",
        headers=headers,
        json=_model_route_payload(),
    )

    assert response.status_code == 429
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    expose_headers = response.headers["Access-Control-Expose-Headers"]
    assert "Retry-After" in expose_headers
    assert "X-UAA-Rate-Limit-Policy" in expose_headers


def test_mutating_route_missing_idempotency_is_not_masked_by_rate_limit(monkeypatch) -> None:
    client = _client(monkeypatch)

    first = client.post("/task-decomposition/run", json={"raw_request": "safe summary"})
    second = client.post("/task-decomposition/run", json={"raw_request": "safe summary"})

    assert first.status_code == 428
    assert first.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
    assert second.status_code == 428
    assert second.json()["code"] == "API_IDEMPOTENCY_REQUIRED"


def test_local_auth_failure_is_not_masked_by_rate_limit(monkeypatch) -> None:
    client = _client(monkeypatch)
    monkeypatch.setenv(LOCAL_API_AUTH_DISABLED_FOR_DEV_ONLY_ENV, "")
    monkeypatch.setenv(LOCAL_API_BEARER_ENV, "p1-085-local-bearer")

    first = client.post("/models/route/preview", json=_model_route_payload())
    second = client.post("/models/route/preview", json=_model_route_payload())

    assert first.status_code == 401
    assert first.json()["code"] == "LOCAL_API_AUTH_REQUIRED"
    assert second.status_code == 401
    assert second.json()["code"] == "LOCAL_API_AUTH_REQUIRED"


def test_mutating_route_with_idempotency_is_rate_limited_before_handler_reentry(monkeypatch) -> None:
    client = _client(monkeypatch)

    first = client.post(
        "/task-decomposition/run",
        headers=IDEMPOTENCY_HEADERS,
        json={"raw_request": "safe summary"},
    )
    second = client.post(
        "/task-decomposition/run",
        headers=IDEMPOTENCY_HEADERS,
        json={"raw_request": "safe summary"},
    )

    assert first.status_code == 403
    assert second.status_code == 429
    assert second.json()["rate_limit_group"] == "task_decomposition"


def test_non_targeted_public_metadata_route_is_not_rate_limited(monkeypatch) -> None:
    client = _client(monkeypatch)

    first = client.get("/health")
    second = client.get("/health")

    assert first.status_code == 200
    assert second.status_code == 200


def test_wrong_method_on_targeted_path_is_not_rate_limited(monkeypatch) -> None:
    client = _client(monkeypatch)

    first = client.post("/v1/models")
    second = client.post("/v1/models")

    assert first.status_code != 429
    assert second.status_code != 429


def test_unregistered_task_decomposition_path_does_not_consume_bucket(monkeypatch) -> None:
    client = _client(monkeypatch)

    typo = client.get("/task-decomposition-typo")
    status = client.get("/task-decomposition/status")

    assert typo.status_code != 429
    assert status.status_code != 429


def test_concrete_memory_context_pack_action_proposal_path_is_targeted() -> None:
    assert (
        route_rate_limit_group(
            "POST",
            "/control-center/memory/context-packs/context-pack-ref:proposal:safe/action-proposal",
        )
        == "memory_context_pack_action_proposal"
    )


def test_concrete_task_decomposition_run_lifecycle_path_is_targeted() -> None:
    assert (
        route_rate_limit_group(
            "GET",
            "/task-decomposition/runs/task-decomposition-run:demo/lifecycle",
        )
        == "task_decomposition"
    )


def test_dynamic_context_pack_action_proposal_returns_redacted_429(monkeypatch) -> None:
    client = _client(monkeypatch)
    headers = {
        "X-UAA-Idempotency-Key": "idempotency:memory-context-pack-action-proposal"
    }
    payload = {
        "exact_approval_scope_ref": "approval-scope-ref:memory-context-pack-action-proposal",
        "approval_ref": "approval-ref:memory-context-pack-action-proposal",
        "metadata_refs": ["metadata-ref:memory-context-pack-action-proposal"],
    }
    path = "/control-center/memory/context-packs/context-pack-ref:proposal:safe/action-proposal"

    first = client.post(path, headers=headers, json=payload)
    second = client.post(path, headers=headers, json=payload)

    assert first.status_code != 429
    assert second.status_code == 429
    body = second.json()
    assert body["code"] == "API_TARGETED_RATE_LIMITED"
    assert body["rate_limit_group"] == "memory_context_pack_action_proposal"
    assert "context-pack-ref:proposal:safe" not in second.text
