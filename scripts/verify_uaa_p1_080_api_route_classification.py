#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402


ALLOWED_CLASSIFICATIONS = {
    "public_metadata",
    "local_readonly",
    "local_sensitive",
    "mutating_requires_authority",
}
EXPECTED_SIDE_EFFECT_MIX = {
    "validation_only": 65,
    "none": 4,
    "local_dev_workspace_only": 42,
    "governed_network_read_only": 1,
}
EXPECTED_PUBLIC_METADATA_PATHS = {
    ("GET", "/api/manifest"),
    ("GET", "/health"),
    ("GET", "/version"),
}
HIGH_RISK_EXPECTATIONS = {
    ("POST", "/v1/chat/completions"): "mutating_requires_authority",
    ("GET", "/v1/models"): "local_sensitive",
    ("POST", "/files/write/propose"): "local_sensitive",
    ("POST", "/memory/write/evaluate"): "local_sensitive",
    ("POST", "/secrets/access/evaluate"): "local_sensitive",
    ("GET", "/observability/session-events"): "local_sensitive",
    ("POST", "/observability/client-errors"): "local_sensitive",
    ("POST", "/task-decomposition/run"): "mutating_requires_authority",
    ("POST", "/task-decomposition/approvals/grants/capture"): "mutating_requires_authority",
    ("POST", "/integrations/mattermost/events/message"): "mutating_requires_authority",
    ("POST", "/integrations/mattermost/roles/bind"): "mutating_requires_authority",
    ("POST", "/web-evidence/request"): "local_sensitive",
}
REQUIRED_DOC_SNIPPETS = {
    "docs/api/openapi_contract.md": [
        "UAA-P1-080",
        "public_metadata",
        "local_readonly",
        "local_sensitive",
        "mutating_requires_authority",
        "implemented OpenAPI/API manifest invariant",
        "does not add middleware, auth, CORS, headers, rate limits, dependencies, or runtime authority",
    ],
    "docs/api/route_inventory.md": [
        "UAA-P1-080",
        "public/protected route inventory",
        "public_metadata",
        "local_readonly",
        "local_sensitive",
        "mutating_requires_authority",
        "Current route classification summary",
    ],
    "docs/api/UAA_P1_080_API_ROUTE_CLASSIFICATION_INVENTORY.md": [
        "Status: Implemented",
        "112",
        "public_metadata",
        "local_readonly",
        "local_sensitive",
        "mutating_requires_authority",
        "No middleware",
        "UAA-P1-081",
    ],
}
FORBIDDEN_CLAIMS = [
    "public beta is ready",
    "public release ready",
    "auth implemented by UAA-P1-080",
    "middleware implemented by UAA-P1-080",
    "cors implemented by UAA-P1-080",
    "rate limits implemented by UAA-P1-080",
]


def _load_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _compact(path: str) -> str:
    return " ".join((ROOT / path).read_text(encoding="utf-8").lower().split())


def _fixture_routes_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    routes = [
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
    return sorted(routes, key=lambda item: (item["path"], item["method"]))


def main() -> int:
    failures: list[str] = []
    manifest = build_api_manifest(app).model_dump(mode="json")
    routes = manifest["routes"]

    if manifest["route_count"] != 112:
        failures.append(f"/api/manifest route_count changed: {manifest['route_count']}")
    if manifest["route_classification_vocabulary"] != [
        "public_metadata",
        "local_readonly",
        "local_sensitive",
        "mutating_requires_authority",
    ]:
        failures.append("/api/manifest route_classification_vocabulary is wrong")

    classifications = Counter(route.get("route_classification") for route in routes)
    side_effects = Counter(route.get("side_effect_class") for route in routes)
    if set(classifications) != ALLOWED_CLASSIFICATIONS:
        failures.append(f"unexpected route classifications: {dict(classifications)}")
    if dict(side_effects) != EXPECTED_SIDE_EFFECT_MIX:
        failures.append(f"side-effect mix drifted: {dict(side_effects)}")
    if dict(classifications) != manifest.get("route_classification_summary"):
        failures.append("route_classification_summary does not match route inventory")

    route_index = {(route["method"], route["path"]): route for route in routes}
    public_metadata_paths = {
        key for key, route in route_index.items() if route["route_classification"] == "public_metadata"
    }
    if public_metadata_paths != EXPECTED_PUBLIC_METADATA_PATHS:
        failures.append(f"public_metadata routes are too broad or stale: {sorted(public_metadata_paths)}")
    for key, expected in HIGH_RISK_EXPECTATIONS.items():
        actual = route_index.get(key, {}).get("route_classification")
        if actual != expected:
            failures.append(f"{key[0]} {key[1]} classified as {actual}, expected {expected}")
    for route in routes:
        if not route.get("classification_reason"):
            failures.append(f"{route['method']} {route['path']} missing classification_reason")
        expected_protected = route["route_classification"] != "public_metadata"
        if route.get("protected_route") is not expected_protected:
            failures.append(f"{route['method']} {route['path']} protected_route mismatch")
        if route.get("requires_auth_future") is not True:
            failures.append(f"{route['method']} {route['path']} requires_auth_future drifted")
        if route.get("blocked_from_production") is not True:
            failures.append(f"{route['method']} {route['path']} blocked_from_production drifted")

    fixture = _load_json("tests/fixtures/api_route_inventory_112.json")
    if fixture.get("routes") != _fixture_routes_from_manifest(manifest):
        failures.append("tests/fixtures/api_route_inventory_112.json does not match live manifest")
    if fixture.get("route_classification_summary") != manifest.get("route_classification_summary"):
        failures.append("fixture route_classification_summary is stale")

    route_status = _load_json("docs/control_center/route_status_manifest.json")
    for section_name, route_key in (
        ("surfaces", "current_backend_routes"),
        ("visible_actions", "backend_routes"),
    ):
        for item in route_status.get(section_name, []):
            for route in item.get(route_key, []):
                key = (route.get("method"), route.get("path"))
                expected = route_index.get(key)
                if expected is None:
                    continue
                if route.get("route_classification") != expected["route_classification"]:
                    failures.append(
                        f"route status manifest {key[0]} {key[1]} classification mismatch"
                    )

    for doc_path, snippets in REQUIRED_DOC_SNIPPETS.items():
        path = ROOT / doc_path
        if not path.exists():
            failures.append(f"missing doc: {doc_path}")
            continue
        compact = _compact(doc_path)
        for snippet in snippets:
            if " ".join(snippet.lower().split()) not in compact:
                failures.append(f"{doc_path} missing '{snippet}'")
    scan_paths = [
        "docs/api/UAA_P1_080_API_ROUTE_CLASSIFICATION_INVENTORY.md",
        "docs/api/openapi_contract.md",
        "docs/api/route_inventory.md",
        "README.md",
        "VERSION.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
        "docs/kanban/current_board.md",
    ]
    for scan_path in scan_paths:
        if not (ROOT / scan_path).exists():
            continue
        compact = _compact(scan_path)
        for forbidden in FORBIDDEN_CLAIMS:
            if forbidden in compact:
                failures.append(f"{scan_path} contains forbidden claim '{forbidden}'")

    frontend = (ROOT / "apps/control-center/src/components/ApiRouteInventoryPanel.tsx").read_text(
        encoding="utf-8"
    )
    frontend_compact = " ".join(frontend.split())
    for snippet in ["Classification", "route_classification", "Classification is posture evidence only"]:
        if snippet not in frontend_compact:
            failures.append(f"API Routes panel missing {snippet}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("UAA-P1-080 API route classification verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
