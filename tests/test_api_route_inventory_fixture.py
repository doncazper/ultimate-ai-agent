from typing import Any
import json
from pathlib import Path

from fastapi import APIRouter, FastAPI

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.api.route_registration import register_router_once


FIXTURE_PATH = Path("tests/fixtures/api_route_inventory_112.json")


def test_frozen_api_route_inventory_matches_current_contract() -> None:
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
            "route_classification": route["route_classification"],
        }
        for route in manifest["routes"]
    ]
    current_routes.sort(key=lambda item: (item["path"], item["method"]))

    assert fixture["schema_version"] == "uaa-api-route-inventory.v1"
    assert fixture["route_count"] == 112
    assert fixture["route_classification_vocabulary"] == manifest["route_classification_vocabulary"]
    assert fixture["route_classification_summary"] == manifest["route_classification_summary"]
    assert fixture["routes"] == current_routes


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
