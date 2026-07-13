from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .api_contract_snapshot import (
    ROUTE_PROJECTION_FIELDS,
    SNAPSHOT_PATH,
    SNAPSHOT_SCHEMA_VERSION,
    load_snapshot,
)
from .api_route_policy_floor import (
    MUTATING_ROUTES,
    TARGETED_RATE_LIMIT_GROUPS,
    TARGETED_RATE_LIMIT_ROUTE_COUNT,
)


ROUTE_FIXTURE_PATH = SNAPSHOT_PATH
ROUTE_FIXTURE_SCHEMA_VERSION = SNAPSHOT_SCHEMA_VERSION
_CANONICAL_API_SNAPSHOT = load_snapshot()
EXPECTED_ROUTE_COUNT = _CANONICAL_API_SNAPSHOT["route_operation_count"]
EXPECTED_OPENAPI_PATH_COUNT = _CANONICAL_API_SNAPSHOT["openapi_path_count"]
EXPECTED_AUTH_POSTURE_SUMMARY = _CANONICAL_API_SNAPSHOT["route_auth_posture_summary"]
EXPECTED_APPROVAL_POSTURE_SUMMARY = _CANONICAL_API_SNAPSHOT[
    "route_approval_posture_summary"
]
EXPECTED_IDEMPOTENCY_POSTURE_SUMMARY = _CANONICAL_API_SNAPSHOT[
    "route_idempotency_posture_summary"
]
EXPECTED_RATE_LIMIT_POSTURE_SUMMARY = _CANONICAL_API_SNAPSHOT[
    "route_rate_limit_posture_summary"
]
EXPECTED_MUTATING_ROUTE_COUNT = _CANONICAL_API_SNAPSHOT["mutating_route_count"]
EXPECTED_TARGETED_RATE_LIMIT_ROUTE_COUNT = _CANONICAL_API_SNAPSHOT[
    "targeted_rate_limit_route_count"
]
EXPECTED_CONTROL_CENTER_ROUTE_COUNT = _CANONICAL_API_SNAPSHOT[
    "control_center_route_count"
]
EXPECTED_MUTATING_ROUTES = set(MUTATING_ROUTES)
EXPECTED_RATE_LIMIT_GROUPS = set(TARGETED_RATE_LIMIT_GROUPS)
if EXPECTED_TARGETED_RATE_LIMIT_ROUTE_COUNT != TARGETED_RATE_LIMIT_ROUTE_COUNT:
    raise ValueError("API_CONTRACT_RATE_LIMIT_POLICY_FLOOR_DRIFT")


def route_key(route: dict[str, Any]) -> tuple[str, str]:
    return (route["method"], route["path"])


def route_index(manifest: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {route_key(route): route for route in manifest["routes"]}


def projected_routes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    routes = [
        {field: route[field] for field in ROUTE_PROJECTION_FIELDS}
        for route in manifest["routes"]
    ]
    return sorted(routes, key=lambda item: (item["path"], item["method"]))


def route_fixture(path: str | Path = ROUTE_FIXTURE_PATH) -> dict[str, Any]:
    return load_snapshot(Path(path))


def classification_counter(manifest: dict[str, Any]) -> Counter[str]:
    return Counter(route.get("route_classification") for route in manifest["routes"])


def side_effect_counter(manifest: dict[str, Any]) -> Counter[str]:
    return Counter(route.get("side_effect_class") for route in manifest["routes"])


def append_expected_route_count(failures: list[str], manifest: dict[str, Any]) -> None:
    if manifest["route_count"] != EXPECTED_ROUTE_COUNT:
        failures.append(f"/api/manifest route_count changed: {manifest['route_count']}")


def append_route_fixture_mismatches(
    failures: list[str],
    manifest: dict[str, Any],
    *,
    label: str = "route inventory fixture",
) -> None:
    fixture = route_fixture()
    if fixture.get("schema_version") != ROUTE_FIXTURE_SCHEMA_VERSION:
        failures.append(f"{label} schema_version is stale")
    projected = projected_routes(manifest)
    if fixture.get("routes") != projected:
        failures.append(f"{label} does not match live manifest")
        fixture_routes = fixture.get("routes", [])
        if isinstance(fixture_routes, list):
            fixture_keys = {
                route_key(route)
                for route in fixture_routes
                if isinstance(route, dict) and "method" in route and "path" in route
            }
            projected_keys = {route_key(route) for route in projected}
            for method, path in sorted(fixture_keys - projected_keys):
                failures.append(f"{label} live manifest missing {method} {path}")
            for method, path in sorted(projected_keys - fixture_keys):
                failures.append(f"{label} live manifest added {method} {path}")
    for key in [
        "route_classification_vocabulary",
        "route_classification_summary",
        "route_auth_posture_summary",
        "route_approval_posture_summary",
        "route_idempotency_posture_summary",
        "idempotency_audit_policy_ref",
        "route_rate_limit_posture_summary",
        "rate_limit_policy_ref",
    ]:
        if fixture.get(key) != manifest.get(key):
            failures.append(f"{label} {key} is stale")


def expected_summary_total(summary: dict[str, int]) -> int:
    return sum(summary.values())
