#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.verification.repo import print_failures_or_success  # noqa: E402
from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402


MANIFEST_PATH = "docs/control_center/capability_surface_manifest.json"
GENERATED_OVERLAY_PATH = (
    "docs/control_center/capability_surface_generated_overlay.json"
)
ROUTE_STATUS_MANIFEST_PATH = "docs/control_center/route_status_manifest.json"
RELEASE_SURFACE_MANIFEST_PATH = "docs/control_center/release_surface_manifest.json"
SCHEMA_VERSION = "uaa-control-center-capability-surface-generated-overlay.v1"
SUCCESS_MESSAGE = "Control Center capability surface generated overlay is current."


def _enum_value(value: Any) -> str:
    candidate = getattr(value, "value", value)
    return str(candidate)


def _read_json(root: Path, rel_path: str) -> Any:
    return json.loads((root / rel_path).read_text(encoding="utf-8"))


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2) + "\n"


def build_generated_overlay(root: Path = ROOT) -> dict[str, Any]:
    manifest = _read_json(root, MANIFEST_PATH)
    route_status_manifest = _read_json(root, ROUTE_STATUS_MANIFEST_PATH)
    release_surface_manifest = _read_json(root, RELEASE_SURFACE_MANIFEST_PATH)
    api_manifest = build_api_manifest(app)

    live_api_routes = {
        (route.method, route.path): route for route in api_manifest.routes
    }
    release_routes = {
        route["path"]: route
        for route in release_surface_manifest.get("routes", [])
        if isinstance(route, dict) and route.get("path")
    }
    visible_actions = {
        action["action_id"]: action
        for action in route_status_manifest.get("visible_actions", [])
        if isinstance(action, dict) and action.get("action_id")
    }

    capability_entries: list[dict[str, Any]] = []
    covered_release_routes: set[str] = set()
    covered_visible_actions: set[str] = set()
    for capability in manifest.get("capabilities", []):
        if not isinstance(capability, dict):
            continue
        api_routes = [
            _generated_api_route(route, live_api_routes)
            for route in capability.get("api_routes", [])
            if isinstance(route, dict)
        ]
        ui_routes = [
            _generated_ui_route(route, release_routes)
            for route in capability.get("ui_routes", [])
            if isinstance(route, str)
        ]
        control_actions = [
            _generated_control_action(action_id, visible_actions)
            for action_id in capability.get("control_action_ids", [])
            if isinstance(action_id, str)
        ]
        covered_release_routes.update(
            route["path"] for route in ui_routes if route.get("source_truth_status") == "current"
        )
        covered_visible_actions.update(
            action["action_id"]
            for action in control_actions
            if action.get("source") == "route_status_manifest"
        )
        capability_entries.append(
            {
                "capability_id": capability.get("capability_id"),
                "api_routes": api_routes,
                "ui_routes": ui_routes,
                "control_action_ids": control_actions,
                "source_truth_status": _source_truth_status(
                    api_routes=api_routes,
                    ui_routes=ui_routes,
                    control_actions=control_actions,
                ),
            }
        )

    release_route_set = set(release_routes)
    visible_action_set = set(visible_actions)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "generated_source_truth_overlay_no_runtime_authority",
        "generated_by": "scripts/generate_control_center_capability_surface.py",
        "human_manifest_ref": MANIFEST_PATH,
        "api_manifest_ref": "/api/manifest",
        "route_status_manifest_ref": ROUTE_STATUS_MANIFEST_PATH,
        "release_surface_manifest_ref": RELEASE_SURFACE_MANIFEST_PATH,
        "runtime_authority_added": False,
        "public_beta_claim_enabled": False,
        "production_readiness_claim_enabled": False,
        "source_truth_counts": {
            "api_manifest_route_count": api_manifest.route_count,
            "release_surface_route_count": len(release_route_set),
            "visible_action_count": len(visible_action_set),
            "human_capability_count": len(capability_entries),
            "covered_release_route_count": len(covered_release_routes),
            "covered_visible_action_count": len(covered_visible_actions),
            "missing_release_routes": sorted(release_route_set - covered_release_routes),
            "missing_visible_actions": sorted(visible_action_set - covered_visible_actions),
        },
        "capabilities": capability_entries,
    }


def _generated_api_route(
    route: dict[str, Any],
    live_api_routes: dict[tuple[str, str], Any],
) -> dict[str, Any]:
    method = str(route.get("method", "")).upper()
    path = str(route.get("path", ""))
    live_route = live_api_routes.get((method, path))
    if live_route is None:
        return {
            "method": method,
            "path": path,
            "operation_id": str(route.get("operation_id", "")),
            "side_effect_class": "missing_from_api_manifest",
            "route_classification": "missing_from_api_manifest",
            "approval_posture": "missing_from_api_manifest",
            "source_truth_status": "missing_from_api_manifest",
        }
    return {
        "method": method,
        "path": path,
        "operation_id": live_route.operation_id,
        "side_effect_class": _enum_value(live_route.side_effect_class),
        "route_classification": _enum_value(live_route.route_classification),
        "approval_posture": _enum_value(live_route.approval_posture),
        "source_truth_status": "current",
    }


def _generated_ui_route(
    route_path: str,
    release_routes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    release_route = release_routes.get(route_path)
    if release_route is None:
        return {
            "path": route_path,
            "label": "missing from release surface",
            "group": "missing",
            "ui_status": "missing",
            "release_status": "missing_from_release_surface",
            "owner": "missing",
            "backend_route_count": 0,
            "blocked_capability_count": 0,
            "visual_proof_status": "missing",
            "source_truth_status": "missing_from_release_surface",
        }
    return {
        "path": route_path,
        "label": str(release_route.get("label", "")),
        "group": str(release_route.get("group", "")),
        "ui_status": str(release_route.get("ui_status", "")),
        "release_status": str(release_route.get("status", "")),
        "owner": str(release_route.get("owner", "")),
        "backend_route_count": len(release_route.get("backend_routes", [])),
        "blocked_capability_count": len(release_route.get("blocked_capabilities", [])),
        "visual_proof_status": str(release_route.get("visual_proof_status", "")),
        "source_truth_status": "current",
    }


def _generated_control_action(
    action_id: str,
    visible_actions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if action_id.startswith("ui-control:"):
        return {
            "action_id": action_id,
            "source": "human_capability_ui_control_ref",
            "frontend_route": "manual_ui_control",
            "ui_surface": "manual_ui_control",
            "release_status": "manual_ui_control_ref",
            "side_effect_class": "manual_ui_control_ref",
            "risk_class": "manual_ui_control_ref",
            "backend_route_count": 0,
            "missing_backend_route_count": 0,
            "source_truth_status": "human_owned",
        }
    action = visible_actions.get(action_id)
    if action is None:
        return {
            "action_id": action_id,
            "source": "missing_from_route_status_manifest",
            "frontend_route": "missing",
            "ui_surface": "missing",
            "release_status": "missing_from_route_status_manifest",
            "side_effect_class": "missing_from_route_status_manifest",
            "risk_class": "missing_from_route_status_manifest",
            "backend_route_count": 0,
            "missing_backend_route_count": 0,
            "source_truth_status": "missing_from_route_status_manifest",
        }
    return {
        "action_id": action_id,
        "source": "route_status_manifest",
        "frontend_route": str(action.get("frontend_route", "")),
        "ui_surface": str(action.get("ui_surface", "")),
        "release_status": str(action.get("release_status", "")),
        "side_effect_class": str(action.get("side_effect_class", "")),
        "risk_class": str(action.get("risk_class", "")),
        "backend_route_count": len(action.get("backend_routes", [])),
        "missing_backend_route_count": len(action.get("missing_backend_routes", [])),
        "source_truth_status": "current",
    }


def _source_truth_status(
    *,
    api_routes: list[dict[str, Any]],
    ui_routes: list[dict[str, Any]],
    control_actions: list[dict[str, Any]],
) -> str:
    generated_rows = [*api_routes, *ui_routes, *control_actions]
    if any(
        str(row.get("source_truth_status", "")).startswith("missing_from")
        for row in generated_rows
    ):
        return "source_truth_gap"
    return "current"


def check_generated_overlay(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    overlay_path = root / GENERATED_OVERLAY_PATH
    if not overlay_path.exists():
        return [f"missing generated capability-surface overlay: {GENERATED_OVERLAY_PATH}"]
    expected = build_generated_overlay(root)
    try:
        actual = json.loads(overlay_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"generated capability-surface overlay is invalid JSON: {exc}"]
    if actual != expected:
        failures.append(
            "generated capability-surface overlay drifted; run "
            "PYTHONPATH=src .venv/bin/python "
            "scripts/generate_control_center_capability_surface.py --write"
        )
    return failures


def write_generated_overlay(root: Path = ROOT) -> None:
    overlay = build_generated_overlay(root)
    (root / GENERATED_OVERLAY_PATH).write_text(
        _canonical_json(overlay),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate or check the source-truth overlay for the Control Center "
            "capability surface manifest."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail when the generated overlay is stale.")
    mode.add_argument("--write", action="store_true", help="Rewrite the generated overlay deterministically.")
    args = parser.parse_args(argv)

    if args.write:
        write_generated_overlay(ROOT)
        print(f"Wrote {GENERATED_OVERLAY_PATH}")
        return 0
    return print_failures_or_success(check_generated_overlay(ROOT), SUCCESS_MESSAGE)


if __name__ == "__main__":
    raise SystemExit(main())
