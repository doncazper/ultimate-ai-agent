from __future__ import annotations

from scripts import verify_uaa_p1_086_api_boundary_enforcement_tests as p1_086
from scripts.verification import api_lane
from scripts.verification.api_routes import (
    EXPECTED_APPROVAL_POSTURE_SUMMARY,
    EXPECTED_AUTH_POSTURE_SUMMARY,
    EXPECTED_MUTATING_ROUTES,
    EXPECTED_RATE_LIMIT_GROUPS,
    projected_routes,
    route_fixture,
)
from ultimate_ai_agent.api.idempotency import API_IDEMPOTENCY_AUDIT_POLICY_REF
from ultimate_ai_agent.api.rate_limits import API_TARGETED_RATE_LIMIT_POLICY_REF


def test_p1_086_api_boundary_enforcement_verifier_passes_current_repo() -> None:
    assert p1_086.verify(api_lane.default_api_verifier_context()) == []


def test_openapi_manifest_and_fixture_share_route_identity_and_operation_ids() -> None:
    context = api_lane.default_api_verifier_context()
    schema = context.app.openapi()
    openapi_operation_ids = {
        (method.upper(), path): operation["operationId"]
        for path, methods in schema["paths"].items()
        for method, operation in methods.items()
        if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    }

    assert set(openapi_operation_ids) == set(context.routes_by_key)
    assert len(openapi_operation_ids.values()) == len(set(openapi_operation_ids.values()))
    for key, route in context.routes_by_key.items():
        assert openapi_operation_ids[key] == route["operation_id"]
    assert route_fixture()["routes"] == projected_routes(context.manifest)


def test_protected_mutating_and_targeted_routes_keep_enforcement_posture() -> None:
    context = api_lane.default_api_verifier_context()
    routes = context.routes_by_key

    public_routes = {
        key for key, route in routes.items()
        if route["route_classification"] == "public_metadata"
    }
    assert public_routes == p1_086.PUBLIC_METADATA_ROUTES

    mutating_routes = {
        key for key, route in routes.items()
        if route["route_classification"] == "mutating_requires_authority"
    }
    assert mutating_routes == EXPECTED_MUTATING_ROUTES

    targeted_groups = {
        route["rate_limit_group"]
        for route in routes.values()
        if route["rate_limit_targeted"] is True
    }
    assert targeted_groups == EXPECTED_RATE_LIMIT_GROUPS

    for route in routes.values():
        assert route["protected_route"] is (route["route_classification"] != "public_metadata")
        assert route["requires_auth_future"] is True
        assert route["blocked_from_production"] is True
        assert route["auth_posture"] == (
            "public_metadata_no_auth"
            if route["route_classification"] == "public_metadata"
            else "protected_local_bearer_required"
        )
        assert route["approval_posture"] == (
            "required_before_mutation_authority"
            if route["route_classification"] == "mutating_requires_authority"
            else "not_required_for_route_classification"
        )
        if route["route_classification"] == "mutating_requires_authority":
            assert route["idempotency_required"] is True
            assert route["idempotency_policy_ref"] == API_IDEMPOTENCY_AUDIT_POLICY_REF
            assert "authority" in route["classification_reason"]
        if route["rate_limit_targeted"]:
            assert route["rate_limit_policy_ref"] == API_TARGETED_RATE_LIMIT_POLICY_REF
    assert context.manifest["route_auth_posture_summary"] == EXPECTED_AUTH_POSTURE_SUMMARY
    assert context.manifest["route_approval_posture_summary"] == EXPECTED_APPROVAL_POSTURE_SUMMARY


def test_route_status_manifest_matches_manifest_route_posture() -> None:
    context = api_lane.default_api_verifier_context()
    failures: list[str] = []

    p1_086._append_route_status_manifest_failures(failures, context)

    assert failures == []
