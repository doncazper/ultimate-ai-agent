from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_control_center_capability_surface.py"
MANIFEST_PATH = ROOT / "docs/control_center/capability_surface_manifest.json"
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
RELEASE_SURFACE_MANIFEST_PATH = ROOT / "docs/control_center/release_surface_manifest.json"


def load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location(
        "verify_control_center_capability_surface",
        SCRIPT,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_route_status_manifest() -> dict[str, Any]:
    return json.loads(ROUTE_STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def load_release_surface_manifest() -> dict[str, Any]:
    return json.loads(RELEASE_SURFACE_MANIFEST_PATH.read_text(encoding="utf-8"))


def test_control_center_capability_surface_verifier_passes_current_repo() -> None:
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []


def test_capability_surface_manifest_covers_current_visible_routes_and_actions() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()

    assert manifest["schema_version"] == "uaa-control-center-capability-surface.v1"
    assert manifest["runtime_authority_added"] is False
    assert manifest["public_beta_claim_enabled"] is False
    assert manifest["production_readiness_claim_enabled"] is False
    assert manifest["status_vocabulary"] == verifier.STATUS_VOCABULARY
    assert len(manifest["capabilities"]) >= 20

    covered_routes = {
        route
        for capability in manifest["capabilities"]
        for route in capability["ui_routes"]
    }
    covered_actions = {
        action_id
        for capability in manifest["capabilities"]
        for action_id in capability["control_action_ids"]
        if not action_id.startswith("ui-control:")
    }
    visible_routes = {
        route["path"]
        for route in release_surface["routes"]
    }
    visible_actions = {
        action["action_id"]
        for action in route_status["visible_actions"]
    }

    assert len(visible_routes) == 39
    assert visible_routes == covered_routes
    assert visible_actions <= covered_actions
    assert {
        "action_inbox_decision_lanes",
        "memory_review_decisions",
        "runtime_readiness_and_manual_smoke",
        "api_route_inventory",
    } <= {capability["capability_id"] for capability in manifest["capabilities"]}


def test_capability_surface_verifier_flags_missing_visible_route() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()
    manifest = copy.deepcopy(manifest)
    capability = next(
        item for item in manifest["capabilities"] if item["capability_id"] == "start_here_read_model"
    )
    capability["ui_routes"] = []

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status,
        release_surface_manifest=release_surface,
        check_files=False,
    )

    assert any("missing UI route coverage" in failure and "/start" in failure for failure in failures)


def test_capability_surface_verifier_flags_missing_visible_action() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()
    manifest = copy.deepcopy(manifest)
    capability = next(
        item for item in manifest["capabilities"] if item["capability_id"] == "action_preview_preflight"
    )
    capability["control_action_ids"] = ["ui-control:action-preview.local-only"]

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status,
        release_surface_manifest=release_surface,
        check_files=False,
    )

    assert any(
        "missing visible action coverage" in failure and "submit-action-preview" in failure
        for failure in failures
    )


def test_capability_surface_verifier_flags_stale_operation_id() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()
    manifest = copy.deepcopy(manifest)
    capability = next(
        item for item in manifest["capabilities"] if item["capability_id"] == "api_route_inventory"
    )
    capability["api_routes"][0]["operation_id"] = "stale_operation_id"

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status,
        release_surface_manifest=release_surface,
        check_files=False,
    )

    assert any("operation_id drift" in failure and "/api/manifest" in failure for failure in failures)


def test_capability_surface_verifier_flags_fake_fully_wired_capability() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()
    manifest = copy.deepcopy(manifest)
    capability = next(
        item for item in manifest["capabilities"] if item["capability_id"] == "approval_queue_summary"
    )
    capability["status"] = "ui_api_cli_wired"
    capability["missing_reason"] = "none"

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status,
        release_surface_manifest=release_surface,
        check_files=False,
    )

    assert any("ui_api_cli_wired requires cli_paths" in failure for failure in failures)
