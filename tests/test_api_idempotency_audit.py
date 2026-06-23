import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.idempotency import (
    API_IDEMPOTENCY_AUDIT_POLICY_REF,
    api_idempotency_audit_policy_payload,
)
from ultimate_ai_agent.api.manifest import build_api_manifest
from scripts.verification.api_routes import (
    EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY,
    EXPECTED_MUTATING_ROUTES,
)

IDEMPOTENCY_HEADERS = {"X-UAA-Idempotency-Key": "idempotency:test-p1-084"}


def _manifest() -> dict[str, object]:
    return build_api_manifest(app).model_dump(mode="json")


def test_mutating_route_rejects_missing_or_invalid_idempotency_before_handler() -> None:
    client = TestClient(app)

    missing = client.post("/task-decomposition/run", json={"raw_request": "safe summary"})
    invalid = client.post(
        "/task-decomposition/run",
        headers={"X-UAA-Idempotency-Key": "short"},
        json={"raw_request": "safe summary"},
    )
    allowed_to_handler = client.post(
        "/task-decomposition/run",
        headers=IDEMPOTENCY_HEADERS,
        json={"raw_request": "safe summary"},
    )

    assert missing.status_code == 428
    assert missing.json()["code"] == "API_IDEMPOTENCY_REQUIRED"
    assert missing.json()["policy_ref"] == API_IDEMPOTENCY_AUDIT_POLICY_REF
    assert missing.headers["X-Content-Type-Options"] == "nosniff"
    assert "safe summary" not in missing.text
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "API_IDEMPOTENCY_INVALID"
    assert "short" not in invalid.text
    assert allowed_to_handler.status_code == 403
    assert "disabled by default" in allowed_to_handler.json()["detail"]


def test_non_mutating_route_does_not_require_idempotency_header() -> None:
    client = TestClient(app)

    response = client.post("/files/tree/preview", json={"unsafe": "shape"})

    assert response.status_code != 428
    assert "API_IDEMPOTENCY_REQUIRED" not in response.text


def test_mutating_routes_declare_idempotency_requirement_before_authority() -> None:
    manifest = _manifest()
    routes = manifest["routes"]
    route_index = {(route["method"], route["path"]): route for route in routes}

    assert manifest["idempotency_audit_policy_ref"] == API_IDEMPOTENCY_AUDIT_POLICY_REF
    assert manifest["route_idempotency_posture_summary"] == EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY
    assert {
        key
        for key, route in route_index.items()
        if route["idempotency_posture"] == "required_before_mutation_authority"
    } == EXPECTED_MUTATING_ROUTES

    for key in EXPECTED_MUTATING_ROUTES:
        route = route_index[key]
        assert route["route_classification"] == "mutating_requires_authority"
        assert route["idempotency_required"] is True
        assert route["idempotency_policy_ref"] == API_IDEMPOTENCY_AUDIT_POLICY_REF
        assert "idempotency key or scoped idempotency ref" in route["idempotency_reason"]

    for key, route in route_index.items():
        if key in EXPECTED_MUTATING_ROUTES:
            continue
        assert route["idempotency_required"] is False
        assert route["idempotency_posture"] == "not_required_for_route_classification"
        assert route["idempotency_policy_ref"] is None


def test_idempotency_audit_declares_capability_without_runtime_authority_claims() -> None:
    manifest = _manifest()

    assert "mutating_route_idempotency_audit" in manifest["capabilities_declared"]
    for blocked in [
        "idempotency_audit_as_exactly_once_execution",
        "idempotency_audit_as_durable_dedupe_store",
        "idempotency_audit_as_mutation_authority",
        "idempotency_audit_as_production_authority",
    ]:
        assert blocked in manifest["capabilities_blocked"]


def test_idempotency_audit_policy_payload_matches_schema() -> None:
    schema = json.loads(
        Path("docs/schemas/api_mutating_route_idempotency_audit.schema.json").read_text(
            encoding="utf-8"
        )
    )
    payload = api_idempotency_audit_policy_payload(mutating_route_count=25)

    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: error.path)
    assert errors == []
    assert payload["runtime_middleware_added"] is True
    assert payload["durable_dedupe_store_added"] is False
    assert payload["request_header_required_by_middleware"] is True
    assert payload["mutation_authority_granted"] is False
    assert payload["production_authority_enabled"] is False
