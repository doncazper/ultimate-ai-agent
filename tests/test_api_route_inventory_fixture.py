import json
from pathlib import Path

from fastapi import APIRouter, FastAPI

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.route_registration import register_router_once


FIXTURE_PATH = Path("tests/fixtures/api_route_inventory_112.json")


def test_frozen_api_route_inventory_matches_current_contract():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    manifest = build_api_manifest(app).model_dump(mode="json")
    current_routes = [
        {
            "path": route["path"],
            "method": route["method"],
            "operation_id": route["operation_id"],
            "tags": route["tags"],
            "summary": route["summary"],
            "side_effect_class": route["side_effect_class"],
        }
        for route in manifest["routes"]
    ]
    current_routes.sort(key=lambda item: (item["path"], item["method"]))

    assert fixture["schema_version"] == "uaa-api-route-inventory.v1"
    assert fixture["route_count"] == 112
    assert fixture["routes"] == current_routes


def test_register_router_once_is_method_aware_for_same_path_routes():
    local_app = FastAPI()

    @local_app.get("/shared")
    def existing_get():
        return {"status": "existing"}

    router = APIRouter()

    @router.get("/shared")
    def duplicate_get():
        return {"status": "duplicate"}

    @router.post("/shared")
    def new_post():
        return {"status": "new"}

    register_router_once(local_app, router, state_attr="_test_routes_registered")
    register_router_once(local_app, router, state_attr="_test_routes_registered")

    methods = sorted(local_app.openapi()["paths"]["/shared"])
    assert methods == ["get", "post"]
