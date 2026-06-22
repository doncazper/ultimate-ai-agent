from typing import Any

from fastapi import APIRouter, FastAPI

from ultimate_ai_agent.api.route_registration import register_router_once
from scripts.verification import api_lane
from scripts.verification.api_routes import (
    EXPECTED_ROUTE_COUNT,
    ROUTE_FIXTURE_SCHEMA_VERSION,
    projected_routes,
    route_fixture,
)


def test_frozen_api_route_inventory_matches_current_contract() -> None:
    fixture = route_fixture()
    manifest = api_lane.default_api_verifier_context().manifest

    assert fixture["schema_version"] == ROUTE_FIXTURE_SCHEMA_VERSION
    assert fixture["route_count"] == EXPECTED_ROUTE_COUNT
    assert fixture["route_classification_vocabulary"] == manifest["route_classification_vocabulary"]
    assert fixture["route_classification_summary"] == manifest["route_classification_summary"]
    assert fixture["route_auth_posture_summary"] == manifest["route_auth_posture_summary"]
    assert fixture["route_approval_posture_summary"] == manifest["route_approval_posture_summary"]
    assert fixture["route_idempotency_posture_summary"] == manifest["route_idempotency_posture_summary"]
    assert fixture["idempotency_audit_policy_ref"] == manifest["idempotency_audit_policy_ref"]
    assert fixture["route_rate_limit_posture_summary"] == manifest["route_rate_limit_posture_summary"]
    assert fixture["rate_limit_policy_ref"] == manifest["rate_limit_policy_ref"]
    assert fixture["routes"] == projected_routes(manifest)


def test_register_router_once_is_method_aware_for_same_path_routes() -> None:
    local_app = FastAPI()

    @local_app.get("/shared")
    def existing_get() -> Any:
        return {"status": "existing"}

    router = APIRouter()

    @router.get("/shared")
    def duplicate_get() -> Any:
        return {"status": "duplicate"}

    @router.post("/shared")
    def new_post() -> Any:
        return {"status": "new"}

    register_router_once(local_app, router, state_attr="_test_routes_registered")
    register_router_once(local_app, router, state_attr="_test_routes_registered")

    methods = sorted(local_app.openapi()["paths"]["/shared"])
    assert methods == ["get", "post"]
