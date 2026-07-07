#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from scripts.verification.repo import (  # noqa: E402
    append_forbidden_claims,
    print_failures_or_success,
)
from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402


MANIFEST_PATH = "docs/control_center/capability_surface_manifest.json"
DOC_PATH = "docs/control_center/CAPABILITY_SURFACE_COVERAGE.md"
SCHEMA_PATH = "docs/schemas/control_center_capability_surface.schema.json"
ROUTE_STATUS_MANIFEST_PATH = "docs/control_center/route_status_manifest.json"
RELEASE_SURFACE_MANIFEST_PATH = "docs/control_center/release_surface_manifest.json"
UI_WIRING_REPORT_PATH = "docs/control_center/UI_WIRING_REPORT.md"
SUCCESS_MESSAGE = "Control Center capability surface coverage verification passed."

STATUS_VOCABULARY = [
    "ui_api_cli_wired",
    "partial_surface_coverage",
    "backend_or_cli_only",
    "mock_or_static_only",
    "blocked_intentionally",
]
TOP_LEVEL_REQUIRED = {
    "schema_version",
    "status",
    "baseline",
    "scope",
    "route_status_manifest_ref",
    "release_surface_manifest_ref",
    "ui_wiring_report_ref",
    "api_manifest_ref",
    "status_vocabulary",
    "runtime_authority_added",
    "public_beta_claim_enabled",
    "production_readiness_claim_enabled",
    "capabilities",
}
CAPABILITY_REQUIRED = {
    "capability_id",
    "label",
    "python_core_owner",
    "api_routes",
    "cli_paths",
    "ui_routes",
    "control_action_ids",
    "authority_posture",
    "status",
    "missing_reason",
    "tests_evidence_refs",
}
TOP_LEVEL_ALLOWED = TOP_LEVEL_REQUIRED
CAPABILITY_ALLOWED = CAPABILITY_REQUIRED
FALSE_FLAGS = [
    "runtime_authority_added",
    "public_beta_claim_enabled",
    "production_readiness_claim_enabled",
]
FILE_REF_PREFIXES = ("docs/", "scripts/", "src/", "tests/")
SAFE_REF_PREFIXES = ("evidence-ref:", "proof-ref:", "visual-baseline:", "route-ref:")
FORBIDDEN_CLAIMS = [
    "all capabilities wired",
    "all features accessible",
    "public beta ready",
    "public release ready",
    "production ready",
    "ready for production",
    "ready to ship",
    "runtime authority enabled",
    "connector writes enabled",
]


def _read_text(root: Path, rel_path: str) -> str:
    return (root / rel_path).read_text(encoding="utf-8")


def _load_json(root: Path, rel_path: str) -> Any:
    return json.loads(_read_text(root, rel_path))


def verify(
    root: Path = ROOT,
    *,
    manifest: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
    route_status_manifest: dict[str, Any] | None = None,
    release_surface_manifest: dict[str, Any] | None = None,
    check_files: bool = True,
) -> list[str]:
    failures: list[str] = []
    if check_files:
        _append_required_file_failures(failures, root)
    if failures:
        return failures

    manifest = manifest if manifest is not None else _load_json(root, MANIFEST_PATH)
    schema = schema if schema is not None else _load_json(root, SCHEMA_PATH)
    route_status_manifest = (
        route_status_manifest
        if route_status_manifest is not None
        else _load_json(root, ROUTE_STATUS_MANIFEST_PATH)
    )
    release_surface_manifest = (
        release_surface_manifest
        if release_surface_manifest is not None
        else _load_json(root, RELEASE_SURFACE_MANIFEST_PATH)
    )
    live_backend_routes = {
        (route.method, route.path): route for route in build_api_manifest(app).routes
    }

    _append_manifest_shape_failures(failures, manifest)
    _append_schema_consistency_failures(failures, schema)
    _append_capability_failures(
        failures,
        root,
        manifest,
        route_status_manifest,
        release_surface_manifest,
        live_backend_routes,
    )
    if check_files:
        append_forbidden_claims(failures, [MANIFEST_PATH, DOC_PATH], FORBIDDEN_CLAIMS)
    return failures


def _append_required_file_failures(failures: list[str], root: Path) -> None:
    for rel_path in [
        MANIFEST_PATH,
        DOC_PATH,
        SCHEMA_PATH,
        ROUTE_STATUS_MANIFEST_PATH,
        RELEASE_SURFACE_MANIFEST_PATH,
        UI_WIRING_REPORT_PATH,
    ]:
        if not (root / rel_path).exists():
            failures.append(f"missing required capability-surface file: {rel_path}")


def _append_manifest_shape_failures(
    failures: list[str], manifest: dict[str, Any]
) -> None:
    missing = TOP_LEVEL_REQUIRED - set(manifest)
    if missing:
        failures.append(f"capability surface manifest missing fields: {sorted(missing)}")
    extra = set(manifest) - TOP_LEVEL_ALLOWED
    if extra:
        failures.append(f"capability surface manifest has unexpected fields: {sorted(extra)}")
    if manifest.get("schema_version") != "uaa-control-center-capability-surface.v1":
        failures.append("capability surface manifest schema_version drifted")
    if manifest.get("status") != "active_capability_surface_coverage_seed_no_runtime_authority":
        failures.append("capability surface manifest status drifted")
    if manifest.get("scope") != (
        "operator-facing capabilities only; internal helper functions are out of scope"
    ):
        failures.append("capability surface manifest scope drifted")
    if manifest.get("route_status_manifest_ref") != ROUTE_STATUS_MANIFEST_PATH:
        failures.append("capability surface manifest route_status_manifest_ref drifted")
    if manifest.get("release_surface_manifest_ref") != RELEASE_SURFACE_MANIFEST_PATH:
        failures.append("capability surface manifest release_surface_manifest_ref drifted")
    if manifest.get("ui_wiring_report_ref") != UI_WIRING_REPORT_PATH:
        failures.append("capability surface manifest ui_wiring_report_ref drifted")
    if manifest.get("api_manifest_ref") != "/api/manifest":
        failures.append("capability surface manifest api_manifest_ref drifted")
    if manifest.get("status_vocabulary") != STATUS_VOCABULARY:
        failures.append("capability surface manifest status_vocabulary drifted")
    for flag in FALSE_FLAGS:
        if manifest.get(flag) is not False:
            failures.append(f"capability surface manifest enables denied flag {flag}")
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        failures.append("capability surface manifest capabilities must be a non-empty list")


def _append_schema_consistency_failures(
    failures: list[str], schema: dict[str, Any]
) -> None:
    if set(schema.get("required", [])) != TOP_LEVEL_REQUIRED:
        failures.append("capability surface schema top-level required fields drifted")
    capability_schema = schema.get("$defs", {}).get("capability", {})
    if set(capability_schema.get("required", [])) != CAPABILITY_REQUIRED:
        failures.append("capability surface schema capability required fields drifted")
    status_enum = (
        capability_schema.get("properties", {})
        .get("status", {})
        .get("enum", [])
    )
    if status_enum != STATUS_VOCABULARY:
        failures.append("capability surface schema status enum drifted")


def _append_capability_failures(
    failures: list[str],
    root: Path,
    manifest: dict[str, Any],
    route_status_manifest: dict[str, Any],
    release_surface_manifest: dict[str, Any],
    live_backend_routes: dict[tuple[str, str], Any],
) -> None:
    release_routes = {
        route.get("path")
        for route in release_surface_manifest.get("routes", [])
        if isinstance(route, dict) and route.get("path")
    }
    visible_action_ids = {
        action.get("action_id")
        for action in route_status_manifest.get("visible_actions", [])
        if isinstance(action, dict) and action.get("action_id")
    }
    if not release_routes:
        failures.append("capability verifier found no release-surface routes")
    if not visible_action_ids:
        failures.append("capability verifier found no visible route-status actions")

    capabilities = manifest.get("capabilities", [])
    capability_ids: list[str] = []
    covered_routes: set[str] = set()
    covered_actions: set[str] = set()
    for index, capability in enumerate(capabilities):
        if not isinstance(capability, dict):
            failures.append(f"capability entry {index} must be an object")
            continue
        capability_id = str(capability.get("capability_id", f"entry-{index}"))
        capability_ids.append(capability_id)
        missing = CAPABILITY_REQUIRED - set(capability)
        if missing:
            failures.append(f"{capability_id} capability missing fields: {sorted(missing)}")
        extra = set(capability) - CAPABILITY_ALLOWED
        if extra:
            failures.append(f"{capability_id} capability has unexpected fields: {sorted(extra)}")
        if not re.match(r"^[a-z0-9][a-z0-9_-]*$", capability_id):
            failures.append(f"{capability_id} capability_id is not stable snake/kebab case")
        _append_owner_ref_failure(failures, root, capability_id, capability)
        _append_api_route_failures(failures, capability_id, capability, live_backend_routes)
        _append_cli_path_failures(failures, root, capability_id, capability)
        _append_ui_route_failures(
            failures, capability_id, capability, release_routes, covered_routes
        )
        _append_control_action_failures(
            failures, capability_id, capability, visible_action_ids, covered_actions
        )
        _append_status_failures(failures, capability_id, capability)
        _append_evidence_ref_failures(failures, root, capability_id, capability)

    duplicates = sorted(
        capability_id for capability_id in set(capability_ids) if capability_ids.count(capability_id) > 1
    )
    if duplicates:
        failures.append(f"capability surface manifest duplicate capability ids: {duplicates}")

    missing_routes = sorted(release_routes - covered_routes)
    missing_actions = sorted(visible_action_ids - covered_actions)
    if missing_routes:
        failures.append(f"capability surface manifest missing UI route coverage: {missing_routes}")
    if missing_actions:
        failures.append(f"capability surface manifest missing visible action coverage: {missing_actions}")


def _append_owner_ref_failure(
    failures: list[str],
    root: Path,
    capability_id: str,
    capability: dict[str, Any],
) -> None:
    owner = capability.get("python_core_owner")
    if not isinstance(owner, str) or not owner:
        failures.append(f"{capability_id} python_core_owner must be non-empty")
        return
    if owner.startswith(FILE_REF_PREFIXES) and not (root / owner).exists():
        failures.append(f"{capability_id} python_core_owner does not exist: {owner}")


def _append_api_route_failures(
    failures: list[str],
    capability_id: str,
    capability: dict[str, Any],
    live_backend_routes: dict[tuple[str, str], Any],
) -> None:
    api_routes = capability.get("api_routes")
    if not isinstance(api_routes, list):
        failures.append(f"{capability_id} api_routes must be a list")
        return
    seen: set[tuple[str, str]] = set()
    for index, route in enumerate(api_routes):
        if not isinstance(route, dict):
            failures.append(f"{capability_id} api route {index} must be an object")
            continue
        for field in ["method", "path", "operation_id"]:
            if not route.get(field):
                failures.append(f"{capability_id} api route {index} missing {field}")
        key = (route.get("method"), route.get("path"))
        if key in seen:
            failures.append(f"{capability_id} duplicate api route: {key}")
        seen.add(key)
        live_route = live_backend_routes.get(key)
        if live_route is None:
            failures.append(f"{capability_id} api route missing from live API manifest: {key}")
            continue
        if route.get("operation_id") != live_route.operation_id:
            failures.append(
                f"{capability_id} operation_id drift for {key}: "
                f"{route.get('operation_id')} != {live_route.operation_id}"
            )


def _append_cli_path_failures(
    failures: list[str],
    root: Path,
    capability_id: str,
    capability: dict[str, Any],
) -> None:
    cli_paths = capability.get("cli_paths")
    if not isinstance(cli_paths, list):
        failures.append(f"{capability_id} cli_paths must be a list")
        return
    for cli_path in cli_paths:
        if not isinstance(cli_path, str) or not cli_path:
            failures.append(f"{capability_id} cli path must be a non-empty string")
            continue
        if not (root / cli_path).exists():
            failures.append(f"{capability_id} cli path does not exist: {cli_path}")


def _append_ui_route_failures(
    failures: list[str],
    capability_id: str,
    capability: dict[str, Any],
    release_routes: set[str],
    covered_routes: set[str],
) -> None:
    ui_routes = capability.get("ui_routes")
    if not isinstance(ui_routes, list):
        failures.append(f"{capability_id} ui_routes must be a list")
        return
    for route in ui_routes:
        if route not in release_routes:
            failures.append(f"{capability_id} UI route not in release surface: {route}")
        else:
            covered_routes.add(route)


def _append_control_action_failures(
    failures: list[str],
    capability_id: str,
    capability: dict[str, Any],
    visible_action_ids: set[str],
    covered_actions: set[str],
) -> None:
    control_action_ids = capability.get("control_action_ids")
    if not isinstance(control_action_ids, list):
        failures.append(f"{capability_id} control_action_ids must be a list")
        return
    for action_id in control_action_ids:
        if not isinstance(action_id, str) or not action_id:
            failures.append(f"{capability_id} control action id must be a non-empty string")
            continue
        if action_id.startswith("ui-control:"):
            continue
        if action_id not in visible_action_ids:
            failures.append(f"{capability_id} unknown visible action id: {action_id}")
        else:
            covered_actions.add(action_id)


def _append_status_failures(
    failures: list[str],
    capability_id: str,
    capability: dict[str, Any],
) -> None:
    status = capability.get("status")
    if status not in STATUS_VOCABULARY:
        failures.append(f"{capability_id} status is not allowed: {status}")
    missing_reason = capability.get("missing_reason")
    if not isinstance(missing_reason, str) or not missing_reason:
        failures.append(f"{capability_id} missing_reason must be non-empty")
    if status == "ui_api_cli_wired":
        for field in ["api_routes", "cli_paths", "ui_routes", "control_action_ids"]:
            if not capability.get(field):
                failures.append(f"{capability_id} ui_api_cli_wired requires {field}")
        if missing_reason != "none":
            failures.append(f"{capability_id} wired capability must use missing_reason=none")
    elif missing_reason == "none":
        failures.append(f"{capability_id} non-wired capability must explain missing_reason")
    if not capability.get("authority_posture"):
        failures.append(f"{capability_id} authority_posture must be non-empty")


def _append_evidence_ref_failures(
    failures: list[str],
    root: Path,
    capability_id: str,
    capability: dict[str, Any],
) -> None:
    refs = capability.get("tests_evidence_refs")
    if not isinstance(refs, list) or not refs:
        failures.append(f"{capability_id} tests_evidence_refs must be a non-empty list")
        return
    for ref in refs:
        if not isinstance(ref, str) or not ref:
            failures.append(f"{capability_id} evidence ref must be a non-empty string")
            continue
        if ref.startswith(SAFE_REF_PREFIXES):
            continue
        if ref.startswith(FILE_REF_PREFIXES):
            path_ref = ref.split("::", 1)[0]
            if not (root / path_ref).exists():
                failures.append(f"{capability_id} evidence ref path does not exist: {ref}")
            continue
        failures.append(f"{capability_id} evidence ref has unsupported prefix: {ref}")


def main() -> int:
    return print_failures_or_success(verify(), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
