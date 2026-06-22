#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    print_failures_or_success,
)


MANIFEST_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_MANIFEST_PATH = "docs/control_center/route_status_manifest.json"
ROUTES_PATH = "apps/control-center/src/routes.tsx"
DOC_PATH = "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"
SCHEMA_PATH = "docs/schemas/control_center_release_surface.schema.json"
SUCCESS_MESSAGE = "FCC-V1-000 Control Center release surface verification passed."

STATUS_VOCABULARY = ["ship", "partial", "blocked", "experimental"]
ROUTE_STATUS_TO_RELEASE_STATUS = {
    "status_available_not_completion": "partial",
    "preview_available_not_execution": "experimental",
    "partial_backend_not_product_ready": "partial",
    "mock_only_not_product_ready": "experimental",
    "local_ui_state_only_not_evidence": "experimental",
    "blocked_missing_backend": "blocked",
}
TOP_LEVEL_REQUIRED = {
    "schema_version",
    "status",
    "baseline",
    "milestone_ref",
    "source_routes_ref",
    "route_status_manifest_ref",
    "status_vocabulary",
    "promotion_rules_ref",
    "release_claims_enabled",
    "runtime_authority_added",
    "public_beta_claim_enabled",
    "production_readiness_claim_enabled",
    "routes",
}
ROUTE_REQUIRED = {
    "path",
    "label",
    "group",
    "ui_status",
    "status",
    "backend_routes",
    "side_effect_class",
    "route_classification",
    "approval_required",
    "proof_lanes",
    "blocked_capabilities",
    "evidence_refs",
    "owner",
}
TOP_LEVEL_ALLOWED = TOP_LEVEL_REQUIRED
ROUTE_ALLOWED = ROUTE_REQUIRED
FALSE_FLAGS = [
    "release_claims_enabled",
    "runtime_authority_added",
    "public_beta_claim_enabled",
    "production_readiness_claim_enabled",
]
FORBIDDEN_CLAIMS = [
    "all routes ship",
    "all routes shipped",
    "public beta ready",
    "public release ready",
    "product ready",
    "production ready",
    "ready for production",
    "ready to ship",
    "release ready",
    "runtime authority enabled",
    "connector writes enabled",
]


def _read_text(root: Path, rel_path: str) -> str:
    return (root / rel_path).read_text(encoding="utf-8")


def _load_json(root: Path, rel_path: str) -> Any:
    return json.loads(_read_text(root, rel_path))


def _nav_items(routes_text: str) -> list[dict[str, str]]:
    match = re.search(r"export const navItems: NavItem\[] = \[(.*?)\];", routes_text, re.S)
    if not match:
        return []
    nav_items = []
    for object_match in re.finditer(r"\{([^{}]+)\}", match.group(1)):
        item_text = object_match.group(1)
        fields = {
            field: _field_value(item_text, field)
            for field in ["path", "label", "group", "status", "releaseStatus", "role"]
        }
        if not fields["path"]:
            continue
        nav_items.append(
            {
                "path": fields["path"],
                "label": fields["label"],
                "group": fields["group"],
                "ui_status": fields["status"],
                "release_status": fields["releaseStatus"],
                "role": fields["role"],
            }
        )
    return nav_items


def _field_value(item_text: str, field: str) -> str:
    match = re.search(rf"\b{re.escape(field)}:\s*\"([^\"]+)\"", item_text)
    return match.group(1) if match else ""


def _route_status_actions(
    route_status_manifest: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    actions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for action in route_status_manifest.get("visible_actions", []):
        frontend_route = action.get("frontend_route")
        if frontend_route:
            actions[frontend_route].append(action)
    return dict(actions)


def verify(
    root: Path = ROOT,
    *,
    manifest: dict[str, Any] | None = None,
    routes_text: str | None = None,
    route_status_manifest: dict[str, Any] | None = None,
    check_files: bool = True,
) -> list[str]:
    failures: list[str] = []
    if check_files:
        _append_required_file_failures(failures, root)
    if failures:
        return failures

    manifest = manifest if manifest is not None else _load_json(root, MANIFEST_PATH)
    schema = _load_json(root, SCHEMA_PATH) if check_files else None
    routes_text = routes_text if routes_text is not None else _read_text(root, ROUTES_PATH)
    route_status_manifest = (
        route_status_manifest
        if route_status_manifest is not None
        else _load_json(root, ROUTE_STATUS_MANIFEST_PATH)
    )

    nav_items = _nav_items(routes_text)
    actions_by_path = _route_status_actions(route_status_manifest)
    routes = manifest.get("routes", [])
    manifest_routes = {
        route.get("path"): route for route in routes if isinstance(route, dict)
    }

    _append_manifest_shape_failures(failures, manifest, routes)
    if schema is not None:
        _append_schema_consistency_failures(failures, schema)
    _append_route_coverage_failures(failures, nav_items, manifest_routes, actions_by_path)
    _append_route_detail_failures(failures, nav_items, manifest_routes, actions_by_path)
    if check_files:
        append_forbidden_claims(failures, [MANIFEST_PATH, DOC_PATH], FORBIDDEN_CLAIMS)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [MANIFEST_PATH, ROUTE_STATUS_MANIFEST_PATH, ROUTES_PATH, DOC_PATH, SCHEMA_PATH]:
        if not (root / rel_path).exists():
            failures.append(f"missing required release-surface file: {rel_path}")


def _append_manifest_shape_failures(
    failures: list[str], manifest: dict[str, Any], routes: Any
) -> None:
    missing = TOP_LEVEL_REQUIRED - set(manifest)
    if missing:
        failures.append(f"release surface manifest missing fields: {sorted(missing)}")
    extra = set(manifest) - TOP_LEVEL_ALLOWED
    if extra:
        failures.append(f"release surface manifest has unexpected fields: {sorted(extra)}")
    if manifest.get("schema_version") != "uaa-control-center-release-surface.v1":
        failures.append("release surface manifest schema_version drifted")
    if manifest.get("milestone_ref") != "FCC-V1-000":
        failures.append("release surface manifest milestone_ref must be FCC-V1-000")
    if manifest.get("source_routes_ref") != ROUTES_PATH:
        failures.append("release surface manifest source_routes_ref drifted")
    if manifest.get("route_status_manifest_ref") != ROUTE_STATUS_MANIFEST_PATH:
        failures.append("release surface manifest route_status_manifest_ref drifted")
    if manifest.get("promotion_rules_ref") != DOC_PATH:
        failures.append("release surface manifest promotion_rules_ref drifted")
    if manifest.get("status_vocabulary") != STATUS_VOCABULARY:
        failures.append("release surface status_vocabulary must be ship/partial/blocked/experimental")
    for flag in FALSE_FLAGS:
        if manifest.get(flag) is not False:
            failures.append(f"release surface manifest enables denied flag {flag}")
    if not isinstance(routes, list) or not routes:
        failures.append("release surface manifest routes must be a non-empty list")


def _append_schema_consistency_failures(
    failures: list[str], schema: dict[str, Any]
) -> None:
    if schema.get("$defs", {}).get("route", {}).get("required") is None:
        failures.append("release surface schema missing route required fields")
        return
    schema_top_required = set(schema.get("required", []))
    if schema_top_required != TOP_LEVEL_REQUIRED:
        failures.append("release surface schema top-level required fields drifted")
    schema_route_required = set(schema["$defs"]["route"].get("required", []))
    if schema_route_required != ROUTE_REQUIRED:
        failures.append("release surface schema route required fields drifted")


def _append_route_coverage_failures(
    failures: list[str],
    nav_items: list[dict[str, str]],
    manifest_routes: dict[str, dict[str, Any]],
    actions_by_path: dict[str, list[dict[str, Any]]],
) -> None:
    if not nav_items:
        failures.append("release surface verifier found no navItems in routes.tsx")
        return
    nav_paths = {item["path"] for item in nav_items}
    manifest_paths = set(manifest_routes)
    action_paths = set(actions_by_path)
    missing_manifest = nav_paths - manifest_paths
    extra_manifest = manifest_paths - nav_paths
    missing_actions = nav_paths - action_paths
    if missing_manifest:
        failures.append(f"release surface manifest missing visible routes: {sorted(missing_manifest)}")
    if extra_manifest:
        failures.append(f"release surface manifest has non-visible routes: {sorted(extra_manifest)}")
    if missing_actions:
        failures.append(f"route status manifest missing visible route actions: {sorted(missing_actions)}")


def _append_route_detail_failures(
    failures: list[str],
    nav_items: list[dict[str, str]],
    manifest_routes: dict[str, dict[str, Any]],
    actions_by_path: dict[str, list[dict[str, Any]]],
) -> None:
    for nav_item in nav_items:
        path = nav_item["path"]
        route = manifest_routes.get(path)
        actions = actions_by_path.get(path, [])
        if not route or not actions:
            continue
        for field in ["label", "group", "ui_status", "release_status", "role"]:
            if not nav_item.get(field):
                failures.append(f"{path} nav item missing {field}")
        missing = ROUTE_REQUIRED - set(route)
        if missing:
            failures.append(f"{path} release surface route missing fields: {sorted(missing)}")
        extra = set(route) - ROUTE_ALLOWED
        if extra:
            failures.append(f"{path} release surface route has unexpected fields: {sorted(extra)}")
        if route.get("label") != nav_item["label"]:
            failures.append(f"{path} release surface label drifted from routes.tsx")
        if route.get("group") != nav_item["group"]:
            failures.append(f"{path} release surface group drifted from routes.tsx")
        if route.get("ui_status") != nav_item["ui_status"]:
            failures.append(f"{path} release surface ui_status drifted from routes.tsx")
        if route.get("status") != nav_item["release_status"]:
            failures.append(f"{path} release surface status drifted from routes.tsx")
        if route.get("status") not in STATUS_VOCABULARY:
            failures.append(f"{path} release surface status is not allowed")
        expected_statuses = {
            ROUTE_STATUS_TO_RELEASE_STATUS[action.get("release_status")]
            for action in actions
            if action.get("release_status") in ROUTE_STATUS_TO_RELEASE_STATUS
        }
        if expected_statuses and route.get("status") not in expected_statuses:
            failures.append(f"{path} release surface status drifted from route status manifest")
        owners = {action.get("owner") for action in actions if action.get("owner")}
        if len(owners) == 1 and route.get("owner") != next(iter(owners)):
            failures.append(f"{path} release surface owner drifted from route status manifest")
        if len(owners) > 1 and route.get("owner") != "mixed":
            failures.append(f"{path} release surface owner must be mixed for multi-owner actions")
        if not isinstance(route.get("approval_required"), bool):
            failures.append(f"{path} release surface approval_required must be boolean")
        expected_backend_routes = _dedupe_backend_routes(
            backend_route
            for action in actions
            for backend_route in action.get("backend_routes", [])
        )
        route_backend_keys = _backend_route_keys(route.get("backend_routes", []))
        expected_backend_keys = _backend_route_keys(expected_backend_routes)
        missing_backend = expected_backend_keys - route_backend_keys
        if missing_backend:
            failures.append(
                f"{path} release surface missing backend route refs: {sorted(missing_backend)}"
            )
        mutating_expected = any(
            backend_route.get("route_classification") == "mutating_requires_authority"
            for backend_route in expected_backend_routes
        )
        if mutating_expected and route.get("approval_required") is not True:
            failures.append(f"{path} mutating backend refs require approval_required=true")
        _append_backend_route_failures(failures, path, route)
        _append_ship_posture_failures(failures, path, route)


def _dedupe_backend_routes(routes: Any) -> list[dict[str, Any]]:
    deduped = []
    seen: set[tuple[str, str, str]] = set()
    for route in routes:
        if not isinstance(route, dict):
            continue
        key = (
            str(route.get("method", "")),
            str(route.get("path", "")),
            str(route.get("operation_id", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(route)
    return deduped


def _backend_route_keys(routes: Any) -> set[str]:
    if not isinstance(routes, list):
        return set()
    return {
        f"{route.get('method')} {route.get('path')} {route.get('operation_id')}"
        for route in routes
        if isinstance(route, dict)
    }


def _append_backend_route_failures(
    failures: list[str], path: str, route: dict[str, Any]
) -> None:
    backend_routes = route.get("backend_routes")
    if not isinstance(backend_routes, list):
        failures.append(f"{path} backend_routes must be a list")
        return
    for backend_route in backend_routes:
        if not isinstance(backend_route, dict):
            failures.append(f"{path} backend route entry must be an object")
            continue
        for field in ["method", "path", "operation_id", "side_effect_class", "route_classification"]:
            if not backend_route.get(field):
                failures.append(f"{path} backend route missing {field}")


def _append_ship_posture_failures(
    failures: list[str], path: str, route: dict[str, Any]
) -> None:
    if route.get("status") != "ship":
        return
    if not route.get("backend_routes"):
        failures.append(f"{path} cannot be ship without backend route refs")
    if not route.get("proof_lanes"):
        failures.append(f"{path} cannot be ship without proof lanes")
    if route.get("blocked_capabilities"):
        failures.append(f"{path} cannot be ship with blocked capabilities")


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
