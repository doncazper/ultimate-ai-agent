from typing import Any
from fastapi.testclient import TestClient
from pathlib import Path
import json
import re

import pytest

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
    action_approval_request,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF,
    FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF,
    FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF,
    FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF,
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
PRODUCT_LANGUAGE_RULES_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"


def _load_route_status_manifest() -> dict:
    return json.loads(ROUTE_STATUS_MANIFEST_PATH.read_text(encoding="utf-8"))


def _visible_frontend_routes() -> set[str]:
    routes_text = (ROOT / "apps/control-center/src/routes.tsx").read_text(
        encoding="utf-8"
    )
    return set(re.findall(r'\{\s*path:\s*"([^"]+)",\s*label:', routes_text))


def _api_route_index() -> Any:
    manifest = build_api_manifest(app)
    return {(route.method, route.path): route for route in manifest.routes}


def _approval_grant_for_request(approval_request, approval_ref: str):
    authority = LocalApprovalAuthority()
    authority.create_request(approval_request)
    return authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="local-api-test-reviewer",
        approval_ref=approval_ref,
    )


def _approve_local_task_seed_action(repo: FounderLoopRepository) -> dict[str, object]:
    action = next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    request = FounderLoopActionDecisionRequest(
        decision_reason_ref="decision-reason-ref:api-local-task-action-approval"
    )
    approval_request = action_approval_request(
        item_ref=str(action["item_ref"]),
        actor_context=request.actor_context,
        risk_class=str(action["risk_class"]),
        resource_refs=[
            str(action["item_ref"]),
            str(action["action_envelope_ref"]),
            str(action["action_scope_ref"]),
            str(action["action_approval_requirement_ref"]),
        ],
    )
    grant = _approval_grant_for_request(
        approval_request,
        "approval-ref:api-local-task-action-approve",
    )
    repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            approval_ref=grant.approval_ref,
            approval_grants=[grant],
            decision_reason_ref="decision-reason-ref:api-local-task-action-approval",
        ),
        idempotency_key_ref="idempotency-ref:api-local-task-action-approval",
    )
    return next(
        item
        for item in repo.list_action_inbox()
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )


def _local_task_commit_api_body(
    action: dict[str, object],
    *,
    approval_ref: str | None = None,
) -> dict[str, object]:
    request = FounderLoopLocalTaskCommitRequest(
        approval_ref=approval_ref or str(action["local_task_commit_approval_ref"]),
        decision_reason_ref="decision-reason-ref:api-local-task-commit",
        metadata_refs=["metadata-ref:api-local-task-commit"],
    )
    return request.model_dump(mode="json")


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
        "/control-center/settings/status",
        "/control-center/local-models/status",
        "/control-center/today/summary",
        "/control-center/evidence/timeline",
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


def test_control_center_settings_status_is_backend_owned_read_only() -> None:
    response = client.get("/control-center/settings/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_settings_status"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "raw_paths_omitted",
        "credentials_omitted",
        "no_runtime_values",
    ]

    data = body["data"]
    assert data["status"] == "read_only_status"
    assert data["maturity_gate_status"] == "active_promotion_gate"
    assert data["proposal_review_only"] is True
    assert "settings-proposal:kill-switch-status-route" in data["review_proposals"]
    assert data["maturity_manifest_ref"] == (
        "docs/control_center/operational_maturity_manifest.json"
    )
    assert data["verifier_ref"] == "scripts/verify_operational_maturity.py"
    assert data["feature_flag_mutation_enabled"] is False
    assert data["kill_switch_mutation_enabled"] is False
    assert data["settings_mutation_enabled"] is False
    assert data["production_authority_enabled"] is False
    assert "kill_switch_mutation" in data["blocked_authorities"]


def test_control_center_local_models_status_is_read_only_and_blocks_lifecycle() -> None:
    response = client.get("/control-center/local-models/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_local_models_status"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "raw_paths_omitted",
        "credentials_omitted",
        "no_model_calls",
    ]

    data = body["data"]
    assert data["status"] == "read_only_status"
    assert data["proposal_review_only"] is True
    assert "local-models-proposal:lifecycle-status-route" in data["review_proposals"]
    assert data["inventory"]["schema_version"] == "uaa_local_model_inventory.v1"
    assert data["gateway_posture"]["local_gateway_enabled"] is False
    assert data["gateway_posture"]["bearer_env_configured"] is False
    assert all(enabled is False for enabled in data["lifecycle_actions"].values())
    assert "model_download" in data["blocked_authorities"]
    assert "provider_model_authority" in data["blocked_authorities"]


def test_founder_loop_daily_loop_read_routes_expose_safe_product_behavior() -> None:
    today = client.get("/control-center/today/summary").json()["data"]
    actions = client.get("/control-center/actions/inbox").json()["data"]
    briefing = client.get("/control-center/morning-briefing/summary").json()["data"]

    assert today["daily_loop_summary"]["home_surface"] == "Morning Briefing"
    assert today["daily_loop_summary"]["action_execution_enabled"] is False
    assert today["source_readiness_items"]
    assert today["source_readiness_posture"]["backend_owned"] is True
    assert today["source_readiness_posture"]["connector_runtime_enabled"] is False
    assert today["source_readiness_posture"]["source_refresh_enabled"] is False
    assert today["source_readiness_posture"]["notification_delivery_enabled"] is False
    assert today["crm_lite_followups"]
    assert today["memory_why_shown_items"]
    assert today["weekly_review_narrative"]["status"] == "safe_ref_history_ready"
    assert today["dogfood_capture"]["public_beta_claim_enabled"] is False
    assert today["dogfood_capture"]["auto_apply_enabled"] is False

    assert actions["review_queue_groups"]
    assert {facet["facet_id"] for facet in actions["review_filter_facets"]} == {
        "status",
        "action_kind",
        "risk",
        "authority_requirement",
        "receipt_state",
        "source_surface",
    }
    assert actions["dogfood_capture"]["action_execution_enabled"] is False
    assert actions["crm_lite_followups"][0]["crm_write_enabled"] is False
    for item in actions["items"]:
        envelope = item["approval_envelope"]
        assert envelope["schema_version"] == "founder_loop_action_approval_envelope.v1"
        assert envelope["contract_ref"] == (
            "contract-ref:founder-loop-action-approval-envelope:v1"
        )
        assert envelope["source"] == "python_core_action_inbox_read_model"
        assert envelope["backend_owned"] is True
        assert envelope["action_kind"] == item.get("action_kind", "review_only")
        assert envelope["exact_scope"]
        assert envelope["risk_class"] == item["risk_class"]
        assert envelope["side_effect_class"] == item["side_effect_class"]
        assert envelope["approval_requirement"]
        assert envelope["idempotency_ref"]
        assert envelope["expected_receipt_refs"]
        assert envelope["blocked_authority_refs"]
        assert envelope["evidence_refs"]
        visibility = item["receipt_visibility"]
        assert (
            visibility["schema_version"] == "founder_loop_action_receipt_visibility.v1"
        )
        assert visibility["contract_ref"] == (
            "contract-ref:founder-loop-action-receipt-visibility:v1"
        )
        assert visibility["source"] == "python_core_action_inbox_read_model"
        assert visibility["backend_owned"] is True
        assert visibility["decision_receipt_ref"]
        assert visibility["local_task_ref"]
        assert visibility["local_task_commit_receipt_ref"]
        assert visibility["evidence_timeline_event_ref"]
        assert visibility["replay_posture"]
        assert visibility["conflict_posture"]

    assert briefing["daily_loop_summary"]["home_surface"] == "Morning Briefing"
    assert briefing["daily_loop_sections"]
    assert briefing["source_readiness_items"][0]["source_kind"] == "inbox"
    assert briefing["source_readiness_posture"] == today["source_readiness_posture"]
    assert briefing["dogfood_capture"]["public_distribution_enabled"] is False


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
    approval_step_kinds = {
        step["kind"] for step in data["steps"] if step["approval_required"]
    }
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


def test_control_center_action_preview_api_denies_execute_and_does_not_echo_secret() -> (
    None
):
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
    assert "/control-center/actions/{action_id}/local-task/commit" in paths
    assert len(paths) == 135
    assert len(operation_ids) == len(set(operation_ids)) == 135


def test_control_center_action_local_task_commit_requires_exact_approval_and_receipts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    api_client = TestClient(app)
    repo = FounderLoopRepository.from_env()
    action = _approve_local_task_seed_action(repo)

    missing_idempotency = api_client.post(
        "/control-center/actions/local-task-create-scorecard/local-task/commit",
        json={"approval_ref": "approval-ref:api-local-task-missing-idempotency"},
    )
    assert missing_idempotency.status_code == 428
    assert missing_idempotency.json()["code"] == "API_IDEMPOTENCY_REQUIRED"

    missing_approval = api_client.post(
        "/control-center/actions/local-task-create-scorecard/local-task/commit",
        json={"approval_ref": "approval-ref:api-local-task-missing-approval"},
        headers={
            "x-uaa-idempotency-key": ("idempotency-ref:api-local-task-missing-approval")
        },
    )
    assert missing_approval.status_code == 403
    assert missing_approval.json()["detail"]["code"] == (
        "FOUNDER_LOOP_LOCAL_TASK_APPROVAL_DENIED"
    )

    forged_grant = api_client.post(
        "/control-center/actions/local-task-create-scorecard/local-task/commit",
        json={
            **_local_task_commit_api_body(action),
            "approval_grants": [
                {
                    "approval_ref": "approval-ref:forged-local-task",
                    "approved_actions": ["commit_founder_loop_local_task"],
                }
            ],
        },
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:api-local-task-forged-grant"
        },
    )
    assert forged_grant.status_code == 422

    response = api_client.post(
        "/control-center/actions/local-task-create-scorecard/local-task/commit",
        json=_local_task_commit_api_body(action),
        headers={"x-uaa-idempotency-key": "idempotency-ref:api-local-task-commit"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_action_local_task_commit"
    receipt = body["data"]
    assert receipt["contract_ref"] == FOUNDER_LOOP_LOCAL_TASK_COMMIT_CONTRACT_REF
    assert receipt["action_kind"] == FOUNDER_LOOP_LOCAL_TASK_CREATE_ACTION_KIND
    assert receipt["local_task_created"] is True
    assert receipt["safe_disable_ref"] == FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF
    assert receipt["rollback_ref"] == FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF
    assert receipt["safe_disable_posture_ref"] == (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_POSTURE_REF
    )
    assert receipt["safe_disable_enabled"] is True
    assert receipt["rollback_execution_enabled"] is False
    assert receipt["rollback_blocker_refs"] == [
        FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_BLOCKED_REF
    ]
    assert receipt["raw_content_stored"] is False
    assert receipt["external_side_effect_performed"] is False

    receipt_response = api_client.get(
        "/control-center/actions/local-task-create-scorecard/receipt"
    )
    assert receipt_response.status_code == 200
    assert receipt_response.json()["data"]["receipt_ref"] == receipt["receipt_ref"]

    inbox = api_client.get("/control-center/actions/inbox").json()["data"]
    committed = next(
        item
        for item in inbox["items"]
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert committed["local_task_commit_eligible"] is False
    assert committed["local_task_commit_receipt_ref"] == receipt["receipt_ref"]
    assert committed["local_task_ref"] == receipt["local_task_ref"]
    assert committed["action_group_id"] == "receipt_recorded"
    assert committed["local_task_safe_disable_ref"] == (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLE_REF
    )
    assert committed["local_task_rollback_ref"] == FOUNDER_LOOP_LOCAL_TASK_ROLLBACK_REF
    assert committed["local_task_safe_disable_active"] is False
    assert committed["local_task_rollback_execution_enabled"] is False
    assert committed["local_task_safe_disable_posture"]["backend_owned"] is True
    visibility = committed["receipt_visibility"]
    assert visibility["decision_receipt_ref"].startswith("receipt:founder-loop-action:")
    assert visibility["local_task_ref"] == receipt["local_task_ref"]
    assert visibility["local_task_commit_receipt_ref"] == receipt["receipt_ref"]
    assert (
        visibility["evidence_timeline_event_ref"]
        == receipt["evidence_timeline_event_ref"]
    )
    assert visibility["replay_posture"] == "idempotency_replay_available"
    assert visibility["conflict_posture"] == "conflicting_idempotency_payload_rejected"
    action_groups = {group["group_id"]: group for group in inbox["action_groups"]}
    assert action_groups["receipt_recorded"]["count"] == 1

    timeline = api_client.get("/control-center/evidence/timeline").json()["data"]
    assert "local_task_created" in timeline["event_types"]
    assert any(
        event["event_type"] == "local_task_created"
        and event["receipt_refs"] == [receipt["receipt_ref"]]
        for event in timeline["events"]
    )


def test_control_center_action_local_task_commit_denies_safe_disabled_lane(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    api_client = TestClient(app)
    repo = FounderLoopRepository.from_env()
    action = _approve_local_task_seed_action(repo)
    repo._disable_local_task_create_lane_for_test(
        disabled_reason_refs=["safe-disable-reason:api-local-task-disabled"],
    )

    inbox = api_client.get("/control-center/actions/inbox").json()["data"]
    disabled = next(
        item
        for item in inbox["items"]
        if item["item_ref"] == "founder-action:local-task-create-scorecard"
    )
    assert disabled["local_task_commit_eligible"] is False
    assert disabled["local_task_safe_disable_active"] is True
    assert (
        FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED_BLOCKED_REF
        in disabled["local_task_commit_blocked_reasons"]
    )

    response = api_client.post(
        "/control-center/actions/local-task-create-scorecard/local-task/commit",
        json=_local_task_commit_api_body(action),
        headers={
            "x-uaa-idempotency-key": "idempotency-ref:api-local-task-safe-disabled"
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == (
        "FOUNDER_LOOP_LOCAL_TASK_SAFE_DISABLED"
    )
    assert repo.storage_status()["counts"]["local_tasks"] == 0


def test_control_center_operator_shell_gap_map_is_current_and_safe() -> None:
    doc_path = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
    text = doc_path.read_text(encoding="utf-8")
    compact = " ".join(text.lower().split())

    assert "status: active uaa-p0-007 operator-shell gap map" in compact
    assert "api boundary: current fastapi manifest has 135 openapi paths" in compact
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
        "`post /control-center/actions/{action_id}/local-task/commit`",
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
