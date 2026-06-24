#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.verification.api_routes import (  # noqa: E402
    append_expected_route_count,
    append_route_fixture_mismatches,
    classification_counter,
    side_effect_counter,
)
from scripts.verification.api_lane import (  # noqa: E402
    ApiVerifierContext,
    default_api_verifier_context,
)
from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    append_missing_doc_snippets,
    load_json,
    print_failures_or_success,
    read_text,
)


ALLOWED_CLASSIFICATIONS = {
    "public_metadata",
    "local_readonly",
    "local_sensitive",
    "mutating_requires_authority",
}
EXPECTED_SIDE_EFFECT_MIX = {
    "validation_only": 67,
    "none": 4,
    "local_dev_workspace_only": 80,
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
    ("POST", "/control-center/actions/{action_id}/local-task/commit"): "mutating_requires_authority",
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
        "152",
        "public_metadata",
        "local_readonly",
        "local_sensitive",
        "mutating_requires_authority",
        "No middleware",
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
SUCCESS_MESSAGE = "UAA-P1-080 API route classification verification passed."


def verify(context: ApiVerifierContext | None = None) -> list[str]:
    context = context or default_api_verifier_context()
    failures: list[str] = []
    manifest = context.manifest
    routes = manifest["routes"]
    routes_by_key = context.routes_by_key

    append_expected_route_count(failures, manifest)
    if manifest["route_classification_vocabulary"] != [
        "public_metadata",
        "local_readonly",
        "local_sensitive",
        "mutating_requires_authority",
    ]:
        failures.append("/api/manifest route_classification_vocabulary is wrong")

    classifications = classification_counter(manifest)
    side_effects = side_effect_counter(manifest)
    if set(classifications) != ALLOWED_CLASSIFICATIONS:
        failures.append(f"unexpected route classifications: {dict(classifications)}")
    if dict(side_effects) != EXPECTED_SIDE_EFFECT_MIX:
        failures.append(f"side-effect mix drifted: {dict(side_effects)}")
    if dict(classifications) != manifest.get("route_classification_summary"):
        failures.append("route_classification_summary does not match route inventory")

    public_metadata_paths = {
        key for key, route in routes_by_key.items() if route["route_classification"] == "public_metadata"
    }
    if public_metadata_paths != EXPECTED_PUBLIC_METADATA_PATHS:
        failures.append(f"public_metadata routes are too broad or stale: {sorted(public_metadata_paths)}")
    for key, expected in HIGH_RISK_EXPECTATIONS.items():
        actual = routes_by_key.get(key, {}).get("route_classification")
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

    append_route_fixture_mismatches(
        failures,
        manifest,
        label="tests/fixtures/api_route_inventory_133.json",
    )

    route_status = load_json("docs/control_center/route_status_manifest.json")
    for section_name, route_key in (
        ("surfaces", "current_backend_routes"),
        ("visible_actions", "backend_routes"),
    ):
        for item in route_status.get(section_name, []):
            for route in item.get(route_key, []):
                key = (route.get("method"), route.get("path"))
                expected = routes_by_key.get(key)
                if expected is None:
                    continue
                if route.get("route_classification") != expected["route_classification"]:
                    failures.append(
                        f"route status manifest {key[0]} {key[1]} classification mismatch"
                    )

    append_missing_doc_snippets(failures, REQUIRED_DOC_SNIPPETS)
    scan_paths = [
        "docs/api/UAA_P1_080_API_ROUTE_CLASSIFICATION_INVENTORY.md",
        "docs/api/openapi_contract.md",
        "docs/api/route_inventory.md",
        "README.md",
        "VERSION.md",
        "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md",
        "docs/kanban/current_board.md",
    ]
    append_forbidden_claims(failures, scan_paths, FORBIDDEN_CLAIMS)

    frontend = read_text("apps/control-center/src/components/ApiRouteInventoryPanel.tsx")
    frontend_compact = " ".join(frontend.split())
    for snippet in ["Classification", "route_classification", "Classification is posture evidence only"]:
        if snippet not in frontend_compact:
            failures.append(f"API Routes panel missing {snippet}")

    return failures


def main() -> int:
    return print_failures_or_success(failures=verify(), success_message=SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
