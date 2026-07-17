from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.control_center.capability_surface import (
    build_control_center_capability_surface_read_model,
)
from ultimate_ai_agent.core.evals import (
    CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF,
    CAPABILITY_MATURITY_BASELINE_SOURCE_REF,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_control_center_capability_surface.py"
GENERATOR_SCRIPT = ROOT / "scripts/generate_control_center_capability_surface.py"
MANIFEST_PATH = ROOT / "docs/control_center/capability_surface_manifest.json"
GENERATED_OVERLAY_PATH = (
    ROOT / "docs/control_center/capability_surface_generated_overlay.json"
)
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
RELEASE_SURFACE_MANIFEST_PATH = (
    ROOT / "docs/control_center/release_surface_manifest.json"
)


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


def load_generator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "generate_control_center_capability_surface",
        GENERATOR_SCRIPT,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_generated_overlay() -> dict[str, Any]:
    return json.loads(GENERATED_OVERLAY_PATH.read_text(encoding="utf-8"))


def load_route_status_manifest() -> dict[str, Any]:
    return json.loads(ROUTE_STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def load_release_surface_manifest() -> dict[str, Any]:
    return json.loads(RELEASE_SURFACE_MANIFEST_PATH.read_text(encoding="utf-8"))


def test_control_center_capability_surface_verifier_passes_current_repo() -> None:
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []


def test_capability_surface_generated_overlay_is_current() -> None:
    generator = load_generator()
    overlay = load_generated_overlay()

    assert generator.check_generated_overlay(ROOT) == []
    assert overlay["schema_version"] == (
        "uaa-control-center-capability-surface-generated-overlay.v1"
    )
    assert overlay["runtime_authority_added"] is False
    assert overlay["public_beta_claim_enabled"] is False
    assert overlay["production_readiness_claim_enabled"] is False
    assert overlay["source_truth_counts"]["missing_release_routes"] == []
    assert overlay["source_truth_counts"]["missing_visible_actions"] == []
    assert overlay["source_truth_counts"]["covered_release_route_count"] == 43
    assert overlay["source_truth_counts"]["covered_visible_action_count"] == 46
    today = next(
        item
        for item in overlay["capabilities"]
        if item["capability_id"] == "today_daily_loop_summary"
    )
    assert today["source_truth_status"] == "current"
    assert today["api_routes"][0] == {
        "method": "GET",
        "path": "/control-center/today/summary",
        "operation_id": "get_control_center_today_summary",
        "side_effect_class": "local_dev_workspace_only",
        "route_classification": "local_sensitive",
        "approval_posture": "not_required_for_route_classification",
        "source_truth_status": "current",
    }


def test_capability_surface_read_model_is_safe_bounded_and_source_backed() -> None:
    api_manifest = build_api_manifest(app)
    read_model = build_control_center_capability_surface_read_model(
        root=ROOT,
        live_api_routes=api_manifest.routes,
    )
    payload = read_model.model_dump(mode="json")

    assert (
        payload["schema_version"] == "control-center-capability-surface-read-model.v1"
    )
    assert payload["backend_owned"] is True
    assert payload["read_only"] is True
    assert payload["safe_refs_only"] is True
    assert payload["raw_manifest_dump_included"] is False
    assert payload["runtime_authority_added"] is False
    assert payload["public_beta_claim_enabled"] is False
    assert payload["production_readiness_claim_enabled"] is False
    assert payload["summary"]["capability_count"] == 31
    assert payload["summary"]["missing_release_routes"] == []
    assert payload["summary"]["missing_visible_actions"] == []
    assert payload["maturity"]["verification_posture"] == "evaluation_required"
    assert payload["maturity"]["component_count"] == 16
    assert payload["maturity"]["uplift_target_count"] == 12
    assert payload["maturity"]["uplift_proven_count"] == 0
    assert payload["maturity"]["automated_evidence_ready_count"] == 0
    assert payload["maturity"]["baseline_weighted_score"] == 87.5
    assert payload["maturity"]["target_weighted_score"] == 94.8
    assert (
        payload["maturity"]["baseline_source_ref"]
        == CAPABILITY_MATURITY_BASELINE_SOURCE_REF
    )
    assert (
        payload["maturity"]["baseline_source_fingerprint_ref"]
        == CAPABILITY_MATURITY_BASELINE_FINGERPRINT_REF
    )
    assert payload["maturity"]["score_increase_requires_independent_acceptance"] is True
    assert payload["maturity"]["trusted_acceptance_verification_implemented"] is False
    assert payload["maturity"]["authority_granted"] is False
    assert all(
        item["verified_score"] == item["baseline_score"]
        for item in payload["maturity"]["components"]
    )
    extensibility = next(
        item
        for item in payload["maturity"]["components"]
        if item["component_id"] == "extensibility_ecosystem"
    )
    assert (extensibility["baseline_score"], extensibility["target_score"]) == (
        7,
        8,
    )
    capability_surface = next(
        row
        for row in payload["rows"]
        if row["capability_id"] == "control_center_capability_surface"
    )
    assert capability_surface["status"] == "ui_api_cli_wired"
    assert capability_surface["missing_reason"] == "none"
    assert capability_surface["api_routes"][0]["route_ref"] == (
        "GET /control-center/capabilities/surface"
    )
    assert capability_surface["api_routes"][0]["source_truth_status"] == "current"
    assert capability_surface["ui_routes"][0]["path"] == "/capabilities"
    assert capability_surface["cli_paths"] == ["scripts/dev/uaa_capability_surface.py"]
    serialized = json.dumps(payload)
    assert "raw_manifest_dump" in serialized
    assert "raw prompt" not in serialized.lower()
    assert "provider payload" not in serialized.lower()


def test_capability_surface_api_route_and_cli_expose_same_safe_model() -> None:
    client = TestClient(app)
    response = client.get("/control-center/capabilities/surface")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_capability_surface"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "bounded_capability_rows_only",
        "raw_manifest_dump_omitted",
        "raw_route_payloads_omitted",
        "raw_logs_prompts_paths_and_provider_payloads_omitted",
    ]
    assert body["data"]["route_ref"] == "GET /control-center/capabilities/surface"
    assert body["data"]["summary"]["covered_release_route_count"] == 43

    cli = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_capability_surface.py",
            "inspect",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(cli.stdout)
    assert cli_payload["read_model_ref"] == body["data"]["read_model_ref"]
    assert cli_payload["summary"]["covered_visible_action_count"] == 46
    assert cli_payload["maturity"] == body["data"]["maturity"]
    assert cli_payload["runtime_authority_added"] is False


def test_capability_surface_manifest_covers_current_visible_routes_and_actions() -> (
    None
):
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
    visible_routes = {route["path"] for route in release_surface["routes"]}
    visible_actions = {
        action["action_id"] for action in route_status["visible_actions"]
    }

    assert len(visible_routes) == 43
    assert visible_routes == covered_routes
    assert visible_actions <= covered_actions
    assert {
        "action_inbox_decision_lanes",
        "control_center_capability_surface",
        "memory_review_decisions",
        "runtime_readiness_and_manual_smoke",
        "api_route_inventory",
    } <= {capability["capability_id"] for capability in manifest["capabilities"]}
    messenger = next(
        capability
        for capability in manifest["capabilities"]
        if capability["capability_id"] == "messenger_fixture_preview"
    )
    assert messenger["api_routes"] == [
        {
            "method": "GET",
            "path": "/control-center/communications/matrix-sync/posture",
            "operation_id": "get_control_center_communications_matrix_sync_posture",
        },
        {
            "method": "GET",
            "path": "/control-center/communications/matrix-crypto/posture",
            "operation_id": "get_control_center_communications_matrix_crypto_posture",
        },
        {
            "method": "GET",
            "path": "/control-center/communications/matrix-messaging/posture",
            "operation_id": "get_control_center_communications_matrix_messaging_posture",
        },
        {
            "method": "GET",
            "path": "/control-center/communications/matrix-rooms-media/posture",
            "operation_id": "get_control_center_communications_matrix_rooms_media_posture",
        },
    ]
    assert messenger["cli_paths"] == [
        "scripts/dev/uaa_communications.py"
    ]
    assert messenger["ui_routes"] == ["/messenger"]
    assert messenger["control_action_ids"] == ["navigate-messenger"]
    assert messenger["status"] == "partial_surface_coverage"


def test_capability_surface_verifier_flags_missing_visible_route() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()
    manifest = copy.deepcopy(manifest)
    capability = next(
        item
        for item in manifest["capabilities"]
        if item["capability_id"] == "start_here_read_model"
    )
    capability["ui_routes"] = []

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status,
        release_surface_manifest=release_surface,
        check_files=False,
    )

    assert any(
        "missing UI route coverage" in failure and "/start" in failure
        for failure in failures
    )


def test_capability_surface_verifier_flags_missing_visible_action() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()
    manifest = copy.deepcopy(manifest)
    capability = next(
        item
        for item in manifest["capabilities"]
        if item["capability_id"] == "action_preview_preflight"
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
        "missing visible action coverage" in failure
        and "submit-action-preview" in failure
        for failure in failures
    )


def test_capability_surface_verifier_flags_stale_operation_id() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()
    manifest = copy.deepcopy(manifest)
    capability = next(
        item
        for item in manifest["capabilities"]
        if item["capability_id"] == "api_route_inventory"
    )
    capability["api_routes"][0]["operation_id"] = "stale_operation_id"

    failures = verifier.verify(
        ROOT,
        manifest=manifest,
        route_status_manifest=route_status,
        release_surface_manifest=release_surface,
        check_files=False,
    )

    assert any(
        "operation_id drift" in failure and "/api/manifest" in failure
        for failure in failures
    )


def test_capability_surface_verifier_flags_fake_fully_wired_capability() -> None:
    verifier = load_verifier()
    manifest = load_manifest()
    route_status = load_route_status_manifest()
    release_surface = load_release_surface_manifest()
    manifest = copy.deepcopy(manifest)
    capability = next(
        item
        for item in manifest["capabilities"]
        if item["capability_id"] == "approval_queue_summary"
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
