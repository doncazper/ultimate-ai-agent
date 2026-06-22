from typing import Any
from fastapi.testclient import TestClient
from pathlib import Path
import json
import re

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
PRODUCT_LANGUAGE_RULES_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"


def _load_route_status_manifest() -> dict:
    return json.loads(ROUTE_STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def _visible_frontend_routes() -> set[str]:
    routes_text = (ROOT / "apps/control-center/src/routes.tsx").read_text(encoding="utf-8")
    return set(re.findall(r'\{\s*path:\s*"([^"]+)",\s*label:', routes_text))


def _api_route_index() -> Any:
    manifest = build_api_manifest(app)
    return {(route.method, route.path): route for route in manifest.routes}


def test_control_center_api_routes_are_read_only_preview_only() -> None:
    for path in [
        "/control-center/manifest",
        "/control-center/dashboard",
        "/control-center/status",
        "/control-center/routes",
        "/control-center/approvals/summary",
        "/control-center/runtime-readiness/summary",
        "/control-center/foundation-gate/summary",
        "/control-center/setup-assistant/summary",
        "/control-center/today/summary",
        "/control-center/actions/inbox",
        "/control-center/morning-briefing/summary",
        "/control-center/storage/status",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["success"] is True

    manifest = client.get("/control-center/manifest").json()["data"]
    assert manifest["metadata"]["frontend_implemented"] is False
    assert "runtime_execution" in manifest["blocked_capabilities"]


def test_control_center_setup_assistant_summary_is_dry_run_only() -> None:
    response = client.get("/control-center/setup-assistant/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_setup_assistant_summary"
    assert body["redactions_applied"] == ["setup_summary_only", "raw_logs_omitted"]

    data = body["data"]
    assert data["status"] == "dry_run_only"
    assert data["macos_first"] is True
    assert data["local_first"] is True
    assert data["disabled_by_default"] is True
    assert data["installer_side_effects_enabled"] is False
    assert data["native_macos_app_ready"] is False
    assert data["setup_question_assistant_enabled"] is False
    assert data["model_output_authoritative"] is False

    for step in data["steps"]:
        assert step["state_change_allowed"] is False
        assert step["state_change_performed"] is False
        assert step["terminal_command_executed"] is False
        assert step["model_download_performed"] is False
        assert step["launch_agent_changed"] is False
        assert step["background_service_changed"] is False
        assert step["raw_log_stored"] is False
        assert step["raw_prompt_stored"] is False
        assert step["credential_material_stored"] is False
        assert step["model_output_authoritative"] is False
        assert step["receipt_ref"]
        assert step["rollback_ref"]
        for line in step["log_preview"]:
            assert 0 < len(line) <= 400

    approval_steps = [step for step in data["steps"] if step["approval_required"]]
    assert approval_steps
    for step in approval_steps:
        assert step["approval_ref"]
        assert step["receipt_ref"]
        assert step["rollback_ref"]

    for recommendation in data["model_recommendations"]:
        assert recommendation["approval_required_before_download"] is True
        assert recommendation["model_download_performed"] is False
        assert recommendation["model_file_read_performed"] is False
        assert recommendation["model_call_performed"] is False
        assert recommendation["raw_model_url_included"] is False
        assert recommendation["raw_local_path_included"] is False

    approval_envelopes = data["approval_envelopes"]
    assert len(approval_envelopes) == 7
    envelope_kinds = {envelope["setup_step_kind"] for envelope in approval_envelopes}
    assert envelope_kinds == {
        "model_selection",
        "model_download_planning",
        "launch_agent_setup_planning",
        "local_bridge_setup_planning",
        "background_service_setup_planning",
        "openwebui_bridge",
        "mattermost_bridge",
    }
    approval_step_kinds = {step["kind"] for step in data["steps"] if step["approval_required"]}
    assert approval_step_kinds.issubset(envelope_kinds)
    for envelope in approval_envelopes:
        assert envelope["dry_run_only"] is True
        assert envelope["approval_required"] is True
        assert envelope["approval_ref_is_identifier_only"] is True
        assert envelope["exact_scope_required"] is True
        assert envelope["idempotency_required"] is True
        assert envelope["rollback_required"] is True
        assert envelope["redaction_required"] is True
        assert envelope["disabled_by_default"] is True
        assert envelope["side_effect_class"] == "validation_only"
        assert envelope["requested_scope_refs"]
        assert envelope["approval_request_ref"].startswith("approval-ref:")
        assert envelope["expected_receipt_ref"].startswith("receipt-plan:")
        assert envelope["rollback_plan_ref"].startswith("rollback-plan:")
        assert envelope["idempotency_key_ref"].startswith("idempotency-ref:")
        assert envelope["not_scoped_actions"]
        assert envelope["blocked_runtime_authority"]
        assert envelope["evidence_refs"]
        assert envelope["verifier_refs"]
        assert envelope["stale_state_handling"]
        assert envelope["redaction_summary"]
        assert envelope["real_execution_requested"] is False
        assert envelope["real_installation_requested"] is False
        assert envelope["subprocess_execution_requested"] is False
        assert envelope["launchctl_requested"] is False
        assert envelope["launch_agent_load_requested"] is False
        assert envelope["launch_agent_start_requested"] is False
        assert envelope["model_download_requested"] is False
        assert envelope["background_service_start_requested"] is False
        assert envelope["approval_grant_captured"] is False
        assert envelope["receipt_created"] is False
        assert envelope["audit_event_created"] is False
        assert envelope["rollback_executed"] is False

    for capability in [
        "macos-setup-model-download",
        "macos-setup-launch-agent-change",
        "macos-setup-background-service-change",
        "macos-setup-bridge-enablement",
        "macos-setup-credential-storage",
        "macos-setup-rollback-execution",
        "macos-setup-signed-distribution",
        "macos-setup-production-authority",
    ]:
        assert capability in data["blocked_capabilities"]

    receipt_plan = data["receipt_plan"]
    assert receipt_plan["receipt_created"] is False
    assert receipt_plan["audit_event_created"] is False
    assert receipt_plan["raw_log_stored"] is False
    assert receipt_plan["raw_prompt_stored"] is False
    assert receipt_plan["raw_provider_payload_stored"] is False
    assert receipt_plan["credential_material_stored"] is False

    rollback_plan = data["rollback_plan"]
    assert rollback_plan["rollback_available_after_approval"] is True
    assert rollback_plan["rollback_executed"] is False
    assert rollback_plan["launch_agent_removed"] is False
    assert rollback_plan["model_files_removed"] is False
    assert rollback_plan["config_removed"] is False


def test_control_center_action_preview_api_denies_execute_and_does_not_echo_secret() -> None:
    secret = "api_key='abcdefghijklmnop'"
    response = client.post(
        "/control-center/actions/preview",
        json={
            "request_id": "cc_api_preview_secret",
            "actor_context": {"actor_type": "user", "actor_id": "local_operator"},
            "action_kind": "preview_action",
            "target_ref": "runtime/execute/model",
            "purpose": "try to execute",
            "risk_level": "medium",
            "data_classification": "system_internal",
            "consent_refs": [],
            "metadata": {"claim": secret},
        },
    )

    body = response.text
    assert response.status_code == 200
    assert response.json()["success"] is False
    assert "RUNTIME_EXECUTION_BLOCKED" in response.json()["data"]["reason_codes"]
    assert "SECRET_LIKE_VALUE_REJECTED" in response.json()["data"]["reason_codes"]
    assert secret not in body


def test_control_center_openapi_routes_and_operation_ids_are_safe() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    required = {
        "/control-center/manifest",
        "/control-center/dashboard",
        "/control-center/status",
        "/control-center/routes",
        "/control-center/approvals/summary",
        "/control-center/runtime-readiness/summary",
        "/control-center/foundation-gate/summary",
        "/control-center/setup-assistant/summary",
        "/control-center/actions/preview",
        "/control-center/today/summary",
        "/control-center/actions/inbox",
        "/control-center/morning-briefing/summary",
        "/control-center/storage/status",
    }
    assert required.issubset(paths)
    for forbidden in [
        "/control-center/actions/execute",
        "/control-center/plugins/enable",
        "/control-center/runtime/execute",
        "/control-center/remote-workers/dispatch",
        "/control-center/mobile/sensors",
        "/control-center/frontend",
    ]:
        assert forbidden not in paths

    operation_ids = [
        spec["operationId"]
        for methods in paths.values()
        for spec in methods.values()
        if isinstance(spec, dict) and "operationId" in spec
    ]
    assert "/files/review/approvals/capture" in paths
    assert "/v1/models" in paths
    assert "/v1/chat/completions" in paths
    assert "/task-decomposition/run" in paths
    assert "/files/tree/preview" in paths
    assert "/extensions/catalog" in paths
    assert "/observability/session-events" in paths
    assert "/observability/client-errors" in paths
    assert "/integrations/mattermost/events/message" in paths
    assert len(paths) == 125
    assert len(operation_ids) == len(set(operation_ids)) == 125


def test_control_center_operator_shell_gap_map_is_current_and_safe() -> None:
    doc_path = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
    text = doc_path.read_text(encoding="utf-8")
    compact = " ".join(text.lower().split())

    assert "status: active uaa-p0-007 operator-shell gap map" in compact
    assert "api boundary: current fastapi manifest has 125 openapi paths" in compact
    assert (
        "| surface | current frontend component/page | current backend route(s) | "
        "missing backend route(s) | authority boundary | side-effect class | "
        "approval requirement | evidence/audit output | readiness status | "
        "production-readiness blocker |"
    ) in compact

    for surface in [
        "chat local operator",
        "setup assistant",
        "plans",
        "models",
        "approvals",
        "files",
        "runtime",
        "evidence",
        "settings",
    ]:
        assert f"| {surface} |" in compact

    for route in [
        "`get /v1/models`",
        "`post /v1/chat/completions`",
        "`post /task-decomposition/classify`",
        "`post /task-decomposition/decompose`",
        "`post /files/tree/preview`",
        "`post /files/read/preview`",
        "`get /observability/session-events`",
        "`post /observability/client-errors`",
        "`get /control-center/setup-assistant/summary`",
        "`get /control-center/today/summary`",
        "`get /control-center/actions/inbox`",
        "`get /control-center/morning-briefing/summary`",
        "`get /control-center/storage/status`",
        "`get /control-center/routes`",
    ]:
        assert route in compact

    for rule in [
        "no hidden authority",
        "no fake completion",
        "no raw json as primary ui for operator-critical flows",
    ]:
        assert rule in compact

    for forbidden in [
        "production ready for external users",
        "public distribution is available",
        "control center executes actions",
        "plugin runtime import is enabled",
    ]:
        assert forbidden not in compact


def test_control_center_route_status_manifest_covers_visible_actions() -> None:
    manifest = _load_route_status_manifest()
    visible_actions = manifest["visible_actions"]
    action_routes = {
        action["frontend_route"] for action in visible_actions if action.get("frontend_route")
    }

    assert manifest["schema_version"] == "uaa-control-center-route-status.v1"
    assert manifest["status"] == "active UAA-P1-030 route status manifest"
    assert manifest["operator_readiness_taxonomy_ref"] == (
        "docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md"
    )
    assert manifest["openapi_path_count"] == 125
    assert _visible_frontend_routes().issubset(action_routes)

    required_fields = {
        "action_id",
        "label",
        "owner",
        "auth_posture",
        "side_effect_class",
        "risk_class",
        "release_status",
        "ui_surface",
        "frontend_route",
        "approval_requirement",
        "evidence_audit_output",
        "backend_routes",
        "missing_backend_routes",
    }
    action_ids = [action["action_id"] for action in visible_actions]
    assert len(action_ids) == len(set(action_ids))

    allowed_statuses = set(manifest["allowed_release_statuses"])
    assert manifest["release_status_taxonomy_map"] == {
        "status_available_not_completion": "status_only",
        "preview_available_not_execution": "preview_only",
        "partial_backend_not_product_ready": "partial",
        "mock_only_not_product_ready": "mock_only",
        "local_ui_state_only_not_evidence": "local_ui_state_only",
        "blocked_missing_backend": "blocked",
    }
    for action in visible_actions:
        assert required_fields.issubset(action)
        assert action["release_status"] in allowed_statuses
        assert action["risk_class"] in {"low", "medium", "high"}
        assert action["approval_requirement"]
        assert action["evidence_audit_output"]

    for action_id in [
        "navigate-setup-assistant",
        "submit-action-preview",
        "select-local-detail-card",
        "toggle-review-only-file-decision",
    ]:
        assert action_id in action_ids

    evidence_action = next(
        action
        for action in visible_actions
        if action["action_id"] == "navigate-evidence"
    )
    assert {
        "method": "GET",
        "path": "/control-center/today/summary",
        "operation_id": "get_control_center_today_summary",
        "side_effect_class": "local_dev_workspace_only",
        "route_classification": "local_sensitive",
    } in evidence_action["backend_routes"]


def test_control_center_route_status_manifest_matches_openapi_and_api_manifest() -> None:
    route_status = _load_route_status_manifest()
    api_routes = _api_route_index()
    openapi_paths = app.openapi()["paths"]

    manifest_routes = []
    for section_name in ["surfaces", "visible_actions"]:
        route_key = "current_backend_routes" if section_name == "surfaces" else "backend_routes"
        for item in route_status[section_name]:
            manifest_routes.extend(item.get(route_key, []))

    assert manifest_routes
    for route in manifest_routes:
        key = (route["method"], route["path"])
        assert key in api_routes
        assert route["operation_id"] == api_routes[key].operation_id
        side_effect_class = getattr(
            api_routes[key].side_effect_class,
            "value",
            api_routes[key].side_effect_class,
        )
        assert route["side_effect_class"] == side_effect_class
        route_classification = getattr(
            api_routes[key].route_classification,
            "value",
            api_routes[key].route_classification,
        )
        assert route["route_classification"] == route_classification
        assert route["path"] in openapi_paths
        assert route["method"].lower() in openapi_paths[route["path"]]
        assert route["operation_id"] == openapi_paths[route["path"]][route["method"].lower()]["operationId"]


def test_control_center_route_status_manifest_keeps_unready_actions_unready() -> None:
    manifest = _load_route_status_manifest()
    surfaces = {surface["surface"]: surface for surface in manifest["surfaces"]}
    actions = {action["action_id"]: action for action in manifest["visible_actions"]}
    release_available = {"status_available_not_completion", "preview_available_not_execution"}

    for surface in [
        "Chat Local Operator",
        "Plans",
        "Models",
        "Approvals",
        "Files",
        "Runtime",
        "Evidence",
        "Settings",
    ]:
        assert surface in surfaces

    assert surfaces["Settings"]["release_status"] == "blocked_missing_backend"
    assert (
        surfaces["Chat Local Operator"]["release_status"]
        == "partial_backend_not_product_ready"
    )
    assert surfaces["Runtime"]["release_status"] == "status_available_not_completion"

    for action in actions.values():
        if not action["backend_routes"] or action["missing_backend_routes"]:
            assert action["release_status"] not in release_available


def test_control_center_product_language_rules_are_current_and_enforced() -> None:
    doc_text = PRODUCT_LANGUAGE_RULES_PATH.read_text(encoding="utf-8").lower()
    doc_compact = " ".join(doc_text.split())
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    agents_compact = " ".join(agents_text.split())

    for fragment in [
        "status: active uaa-p1-031 product language rules",
        "cli is a first-class operator surface",
        "product behavior must not live only in react state",
        "no hidden authority",
        "no fake completion",
        "no frontend-only product behavior",
        "no raw json as primary ui for operator-critical flows",
        "no production/public distribution claims without evidence",
        "no model/provider output as authority",
        "no completed-state language for blocked/skipped/pending work",
        "today, inbox, plans, actions, memory, evidence, and settings",
    ]:
        assert fragment in doc_compact

    for fragment in [
        "cli is a first-class operator surface",
        "product behavior must not live only in react state",
        "python core/api contract",
        "command-line or repo-local script inspection path",
        "tests and redacted evidence",
    ]:
        assert fragment in agents_compact

    for rel_path in [
        "README.md",
        "docs/README.md",
        "docs/DOCUMENTATION_INDEX.md",
        "docs/canonical/CANONICAL_DOC_MAP.md",
        "docs/control_center/OPERATOR_SHELL_GAP_MAP.md",
        "docs/control_center/ROUTE_STATUS_MANIFEST.md",
        "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        "docs/kanban/current_board.md",
    ]:
        assert "docs/control_center/product_language_rules.md" in (
            ROOT / rel_path
        ).read_text(encoding="utf-8").lower()

    for frontend_path in [
        ROOT / "apps/control-center/src/components/RuntimeReadinessPanel.tsx",
        ROOT / "apps/control-center/src/components/LocalRuntimeStatusPanel.tsx",
        ROOT / "apps/control-center/src/components/ActionPreviewForm.tsx",
        ROOT / "apps/control-center/src/components/FileReviewSurfacePanel.tsx",
    ]:
        frontend_text = frontend_path.read_text(encoding="utf-8")
        for unsafe in [
            "Production ready",
            "Public release",
            "Public distribution",
            "Completed successfully",
            "Execution completed",
            "Model output is authority",
            "Provider output is authority",
            "Raw JSON",
        ]:
            assert unsafe not in frontend_text

    manifest = _load_route_status_manifest()
    actions = {action["action_id"]: action for action in manifest["visible_actions"]}
    completion_words = re.compile(r"\b(complete|completed|done|finished|succeeded)\b")
    for item in [*manifest["surfaces"], *manifest["visible_actions"]]:
        release_status = item["release_status"]
        if not any(marker in release_status for marker in ["blocked", "partial", "mock", "local_ui_state"]):
            continue
        checked_text = " ".join(
            str(item.get(field, ""))
            for field in ["label", "approval_requirement", "evidence_audit_output"]
        ).lower()
        assert completion_words.search(checked_text) is None

    assert actions["submit-action-preview"]["release_status"] == "preview_available_not_execution"
    assert actions["submit-action-preview"]["backend_routes"][0]["operation_id"] == (
        "post_control_center_actions_preview"
    )
    assert actions["toggle-review-only-file-decision"]["backend_routes"] == []
    assert actions["toggle-review-only-file-decision"]["release_status"] == (
        "local_ui_state_only_not_evidence"
    )

    serialized = json.dumps(manifest).lower()
    for forbidden in [
        "production_ready",
        "public_release_ready",
        "broad_autonomy_enabled",
        "shell_authority_enabled",
        "connector_writes_enabled",
        "plugin_runtime_enabled",
    ]:
        assert forbidden not in serialized
