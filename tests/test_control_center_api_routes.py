from typing import Any
from fastapi.testclient import TestClient
from pathlib import Path
import json
import re

import pytest

from scripts.verification.api_routes import (
    EXPECTED_OPENAPI_PATH_COUNT,
    EXPECTED_ROUTE_COUNT,
)
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.authority import (
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
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
from ultimate_ai_agent.core.decision_router import TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS
from ultimate_ai_agent.core.storage import FounderLoopRepository


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
ROUTE_STATUS_MANIFEST_PATH = ROOT / "docs/control_center/route_status_manifest.json"
PRODUCT_LANGUAGE_RULES_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"


def _issue_workspace_write_lease(state_dir: Path) -> None:
    issue_authority_lease_with_test_approval(
        AuthorityLeaseStore(state_dir),
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.write],
            },
            decision_reason_ref="decision-reason-ref:api-local-task-authority-lease",
            safe_summary=(
                "Test session lease grants Workspace write for local task commit."
            ),
        ),
        idempotency_ref="idempotency-ref:api-local-task-authority-lease",
        approval_ref="approval-ref:test-authority:api-local-task-authority-lease",
    )


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


def _approve_local_task_seed_action(repo: FounderLoopRepository) -> dict[str, object]:
    repo.record_action_decision(
        action_id="local-task-create-scorecard",
        decision="approve",
        request=FounderLoopActionDecisionRequest(
            expected_revision_ref=next(
                str(item["action_revision_ref"])
                for item in repo.list_action_inbox(limit=200)
                if item["item_ref"]
                == "founder-action:local-task-create-scorecard"
            ),
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
        "/control-center/capabilities/availability",
        "/control-center/capabilities/surface",
        "/control-center/approvals/summary",
        "/control-center/approvals/queue",
        "/control-center/runs/observability",
        "/control-center/runtime-readiness/summary",
        "/control-center/foundation-gate/summary",
        "/control-center/setup-assistant/summary",
        "/control-center/settings/status",
        "/control-center/local-models/status",
        "/control-center/today/summary",
        "/control-center/start-here/summary",
        "/control-center/proof/index",
        "/control-center/proof/proof-ref:test:not-present",
        "/control-center/trust-authority/matrix",
        "/control-center/coding/session",
        "/control-center/coding/context",
        "/control-center/coding/patch-apply-readiness",
        "/control-center/coding/patch-proposal",
        "/control-center/coding/git-review",
        "/control-center/coding/live-preview",
        "/control-center/coding/multi-agent-review",
        "/control-center/coding/test-command-readiness",
        "/control-center/evidence/timeline",
        "/control-center/actions/inbox",
        "/control-center/backend-truth",
            "/control-center/morning-briefing/summary",
            "/control-center/news-signals/summary",
        "/control-center/sources/readiness",
        "/control-center/storage/status",
        "/control-center/agent-loop/thread",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["success"] is True

    manifest = client.get("/control-center/manifest").json()["data"]
    assert manifest["metadata"]["frontend_implemented"] is False
    assert "runtime_execution" in manifest["blocked_capabilities"]


def test_control_center_approval_queue_is_backend_owned_read_only() -> None:
    response = client.get("/control-center/approvals/queue")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_approvals_queue"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "approval_refs_identifier_only",
        "raw_payloads_omitted",
        "read_only_control_center_projection",
    ]
    data = body["data"]
    assert data["schema_version"] == "run_attached_approval_queue.v1"
    assert data["source"] == "python_core_run_attached_approval_queue_read_model"
    assert data["backend_owned"] is True
    assert data["safe_refs_only"] is True
    assert data["raw_payloads_persisted"] is False
    assert data["approval_refs_are_identifiers_only"] is True
    assert data["approval_authority_enabled"] is False
    assert data["execution_authority_enabled"] is False
    assert data["ui_mutation_controls_enabled"] is False
    connector_review = data["connector_delivery_review_queue"]
    assert connector_review["schema_version"] == "connector_delivery_review_queue.v1"
    assert connector_review["source"] == "python_core_connector_delivery_review_queue_read_model"
    assert connector_review["backend_owned"] is True
    assert connector_review["safe_refs_only"] is True
    assert connector_review["raw_payloads_persisted"] is False
    assert connector_review["no_send_action"] is True
    assert connector_review["connector_sends_enabled"] is False
    assert connector_review["connector_writes_enabled"] is False
    assert connector_review["delivery_execution_enabled"] is False
    assert connector_review["background_delivery_worker_enabled"] is False
    assert "approve" not in data


def test_control_center_source_readiness_route_is_backend_owned_read_only() -> None:
    response = client.get("/control-center/sources/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_sources_readiness"
    assert body["redactions_applied"] == [
        "safe_refs_only",
        "bounded_summaries_only",
        "raw_content_omitted",
        "connector_runtime_omitted",
    ]

    data = body["data"]
    assert data["schema_version"] == "founder_loop_source_readiness.v1"
    assert data["source"] == "python_core_source_readiness_read_model"
    assert data["backend_owned"] is True
    assert data["route_ref"] == "/control-center/sources/readiness"
    assert "GET /control-center/sources/readiness" in data["route_refs"]
    assert data["source_readiness_items"]
    assert {item["status"] for item in data["source_readiness_items"]} >= {
        "ready",
        "blocked",
        "metadata_only",
        "not_configured",
    }
    assert set(data["supported_statuses"]) >= {
        "ready",
        "blocked",
        "missing",
        "metadata_only",
        "unavailable",
        "not_configured",
    }
    posture = data["source_readiness_posture"]
    assert posture["source"] == "python_core_source_readiness_read_model"
    assert posture["backend_owned"] is True
    assert posture["connector_runtime_enabled"] is False
    assert posture["source_refresh_enabled"] is False
    assert posture["notification_delivery_enabled"] is False
    assert posture["account_auth_enabled"] is False
    assert posture["raw_source_ingestion_enabled"] is False
    assert posture["write_authority_enabled"] is False
    for field in [
        "connector_runtime_enabled",
        "source_refresh_enabled",
        "notification_delivery_enabled",
        "account_auth_enabled",
        "raw_source_ingestion_enabled",
        "write_authority_enabled",
    ]:
        assert data[field] is False
    for ref in [
        "contract-ref:email-read-only-missing",
        "contract-ref:calendar-read-only-missing",
    ]:
        assert ref in data["missing_contract_refs"]
    for ref in [
        "blocked-state:no-connector-write",
        "blocked-state:no-account-auth",
        "blocked-state:no-background-polling",
    ]:
        assert ref in data["blocked_authority_refs"]
    proposals = data["source_readiness_proposal_candidates"]
    assert {proposal["title"] for proposal in proposals} == {
        "Define email read-only metadata contract",
        "Define calendar read-only metadata contract",
        "Resolve missing account-auth boundary",
    }
    for proposal in proposals:
        assert proposal["source"] == "python_core_source_readiness_read_model"
        assert proposal["backend_owned"] is True
        assert proposal["proposal_classification"] == "proposal_only_no_execution_path"
        assert proposal["action_kind"] == "source_readiness_contract_proposal"
        assert proposal["approval_required"] is False
        assert proposal["local_task_commit_eligible"] is False
        assert proposal["connector_runtime_enabled"] is False
        assert proposal["account_auth_enabled"] is False
        assert proposal["source_refresh_enabled"] is False
        assert proposal["raw_source_ingestion_enabled"] is False
        assert proposal["write_authority_enabled"] is False
    draft_proposals = data["connector_draft_proposals"]
    assert draft_proposals["schema_version"] == "connector_draft_proposal_read_model.v1"
    assert draft_proposals["source"] == "python_core_connector_draft_proposal_read_model"
    assert draft_proposals["backend_owned"] is True
    assert draft_proposals["status"] == "draft_proposals_ready_no_send_write"
    assert draft_proposals["proposal_count"] == 2
    assert draft_proposals["connector_runtime_enabled"] is False
    assert draft_proposals["account_auth_enabled"] is False
    assert draft_proposals["connector_writes_enabled"] is False
    assert draft_proposals["connector_sends_enabled"] is False
    assert draft_proposals["provider_model_calls_enabled"] is False
    assert draft_proposals["memory_write_enabled"] is False
    assert draft_proposals["context_injection_enabled"] is False
    assert "credential_collection_enabled" not in draft_proposals
    assert {proposal["draft_kind"] for proposal in draft_proposals["proposals"]} == {
        "email_response",
        "calendar_event_hold",
    }
    for proposal in draft_proposals["proposals"]:
        assert proposal["status"] == "draft_proposal_ready"
        assert proposal["approval_required_to_draft"] is False
        assert proposal["approval_required_to_send"] is True
        assert proposal["connector_write_enabled"] is False
        assert proposal["connector_send_enabled"] is False
        assert proposal["connector_write_performed"] is False
        assert proposal["connector_send_performed"] is False
        assert proposal["delivery_execution_performed"] is False
        assert "credential_collection_enabled" not in proposal
        assert "blocked-state:no-connector-write" in proposal[
            "blocked_authority_refs"
        ]

    serialized = response.text.lower()
    for forbidden in [
        "raw_prompt",
        "raw_response",
        "provider_payload",
        "api_key",
        "credential",
        "email_body",
        "calendar_body",
        "account_identifier",
        "hostname",
        "username",
    ]:
        assert forbidden not in serialized


def test_backend_truth_route_is_revision_bound_read_only_and_redacted() -> None:
    response = client.get("/control-center/backend-truth")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["operation"] == "control_center_backend_truth"
    truth = payload["data"]
    assert truth["schema_version"] == "uaa-control-center-backend-truth.v1"
    assert len(truth["critical_surfaces"]) == 14
    assert truth["safe_refs_only"] is True
    assert truth["raw_content_included"] is False
    assert truth["raw_paths_included"] is False
    assert response.headers["X-UAA-Backend-Revision-Ref"] == truth[
        "backend_revision_ref"
    ]
    assert response.headers["X-UAA-Backend-Instance-Ref"] == truth[
        "backend_instance_ref"
    ]
    assert truth["authority_posture"]["control_center_grants_authority"] is False
    assert truth["authority_posture"]["production_authority_enabled"] is False
    assert payload["evidence"] == [
        {"evidence_ref": truth["envelope_integrity_ref"]}
    ]


def test_founder_loop_daily_loop_read_routes_expose_safe_product_behavior() -> None:
    today = client.get("/control-center/today/summary").json()["data"]
    actions = client.get("/control-center/actions/inbox").json()["data"]
    briefing = client.get("/control-center/morning-briefing/summary").json()["data"]
    source_readiness = client.get("/control-center/sources/readiness").json()["data"]

    assert today["daily_loop_summary"]["home_surface"] == "Morning Briefing"
    assert today["daily_loop_summary"]["action_execution_enabled"] is False
    assert today["source_readiness_route_ref"] == "/control-center/sources/readiness"
    assert today["source_readiness_items"]
    assert today["source_readiness_posture"]["backend_owned"] is True
    assert (
        today["source_readiness_posture"]["source"]
        == "python_core_source_readiness_read_model"
    )
    assert today["source_readiness_posture"]["connector_runtime_enabled"] is False
    assert today["source_readiness_posture"]["source_refresh_enabled"] is False
    assert today["source_readiness_posture"]["notification_delivery_enabled"] is False
    assert today["source_readiness_items"] == source_readiness[
        "source_readiness_items"
    ]
    assert today["source_readiness_posture"] == source_readiness[
        "source_readiness_posture"
    ]
    assert {item["status"] for item in today["source_readiness_items"]} >= {
        "ready",
        "blocked",
        "metadata_only",
        "not_configured",
    }
    assert set(today["source_readiness_posture"]["supported_statuses"]) >= {
        "ready",
        "blocked",
        "missing",
        "metadata_only",
        "unavailable",
        "not_configured",
    }
    assert today["source_readiness_posture"]["blocked_source_count"] >= 1
    assert today["source_readiness_posture"]["not_configured_source_count"] >= 1
    assert today["source_readiness_posture"]["metadata_only_source_count"] >= 1
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
    assert actions["source_readiness_route_ref"] == "/control-center/sources/readiness"
    assert (
        actions["source_readiness_proposal_binding_contract_ref"]
        == "contract-ref:founder-loop-source-readiness-draft-proposals:v1"
    )
    assert actions["source_readiness_proposal_candidates"] == source_readiness[
        "source_readiness_proposal_candidates"
    ]
    source_readiness_actions = [
        item
        for item in actions["items"]
        if item.get("action_kind") == "source_readiness_contract_proposal"
    ]
    assert len(source_readiness_actions) == 3
    assert {item["title"] for item in source_readiness_actions} == {
        "Define email read-only metadata contract",
        "Define calendar read-only metadata contract",
        "Resolve missing account-auth boundary",
    }
    for item in source_readiness_actions:
        assert item["action_group_id"] == "proposal_only_no_execution_path"
        assert item["approval_required"] is False
        assert item["local_task_commit_eligible"] is False
        assert item["source_readiness_backend_owned"] is True
        assert item["source_readiness_proposal_classification"] == (
            "proposal_only_no_execution_path"
        )
        assert "blocked-state:no-connector-write" in item[
            "source_readiness_blocked_authority_refs"
        ]
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
    assert briefing["source_readiness_route_ref"] == "/control-center/sources/readiness"
    assert briefing["source_readiness_items"][0]["source_kind"] == "inbox"
    assert briefing["source_readiness_items"][0]["status"] == "blocked"
    assert briefing["source_readiness_posture"] == today["source_readiness_posture"]
    assert briefing["source_readiness_items"] == source_readiness[
        "source_readiness_items"
    ]
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
    assert data["lifecycle"]["status"] == "blocked_by_authority"
    assert data["lifecycle"]["current_state"] == "prerequisites"
    assert [item["operation"] for item in data["lifecycle"]["operations"]] == [
        "plan",
        "status",
        "install",
        "verify",
        "repair",
        "stop",
        "rollback",
        "receipts",
    ]
    assert data["macos_first"] is True
    assert data["local_first"] is True
    assert data["disabled_by_default"] is True
    assert data["installer_side_effects_enabled"] is False
    assert data["native_macos_app_ready"] is False
    assert data["setup_question_assistant_enabled"] is False
    assert data["model_output_authoritative"] is False
    assert "daily loop" in data["full_strength_goal"]
    assert "Read-only setup plan" in data["repo_safe_scope"]
    assert "public distribution" in data["blocked_authority_summary"]
    assert "loop-ref:setup-to-daily-loop:v1" in data["first_run_loop_refs"]
    assert "packaging-proof:local-macos-app-bundle" in data["local_package_proof_refs"]
    assert "script:verify-local-macos-app-bundle-proof" in data[
        "local_package_proof_refs"
    ]
    assert "promotion-path-ref:setup:exact-approved-mutation-pr" in data[
        "promotion_path_refs"
    ]

    diagnostics = {item["diagnostic_ref"]: item for item in data["diagnostics"]}
    assert diagnostics["macos-setup-diagnostic:read-only-plan"]["status"] == "ready"
    assert diagnostics["macos-setup-diagnostic:native-app"]["status"] == "missing"
    assert diagnostics["macos-setup-diagnostic:live-health-proof"]["status"] == "blocked"
    assert diagnostics["macos-setup-diagnostic:rollback-proof"]["status"] == "blocked"
    for diagnostic in diagnostics.values():
        assert diagnostic["read_only"] is True
        assert diagnostic["live_probe_performed"] is False
        assert diagnostic["state_change_performed"] is False
        assert diagnostic["source_refs"]
        assert diagnostic["reason_codes"]

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
    assert rollback_plan["rollback_available_after_approval"] is False
    assert rollback_plan["rollback_contract_defined"] is True
    assert rollback_plan["rollback_execution_available"] is False
    assert rollback_plan["rollback_rehearsal_completed"] is False
    assert rollback_plan["restore_proof_available"] is False
    assert rollback_plan["blocked_reason_refs"]
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


def test_control_center_turn_router_preview_api_matches_no_effect_samples() -> None:
    expected = {
        "diy-desk": "answer_directly",
        "office-memory": "answer_with_reviewed_memory",
        "shopping-list": "draft_or_plan",
        "current-lumber-prices": "prepare_tool_or_action",
        "order-materials": "approval_required",
        "card-pickup": "approval_required",
        "base-answer-bypass": "approval_required",
    }

    for sample_id, selected_contract in expected.items():
        response = client.post(
            "/control-center/turn-router/preview",
            json={"sample_id": sample_id},
        )
        body = response.json()

        assert response.status_code == 200
        assert body["success"] is True
        assert body["operation"] == "control_center_turn_router_preview"
        assert body["data"]["selected_turn_contract"] == selected_contract
        assert body["data"]["request_kind"] == "sample"
        assert body["data"]["sample_id"] == sample_id
        assert body["data"]["no_effect_proof"]["no_runtime_model_call_performed"] is True
        assert body["data"]["no_effect_proof"]["no_tool_execution_performed"] is True
        assert body["data"]["no_effect_proof"]["no_action_execution_performed"] is True
        assert TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS[sample_id] not in response.text


def test_control_center_turn_router_preview_api_omits_ephemeral_text_and_secret() -> None:
    secret = "api_key='abcdefghijklmnop'"
    response = client.post(
        "/control-center/turn-router/preview",
        json={"text": secret},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["data"]["selected_turn_contract"] == "approval_required"
    assert body["data"]["request_kind"] == "ephemeral_text"
    assert body["data"]["sample_id"] is None
    assert body["data"]["ephemeral_request_text_omitted"] is True
    assert "secret_like_input_safely_summarized" in body["redactions_applied"]
    assert secret not in response.text
    assert body["data"]["policy_summary"]["tool_execution_allowed"] is False


def test_control_center_openapi_routes_and_operation_ids_are_safe() -> None:
    schema = app.openapi()
    paths = schema["paths"]
    required = {
        "/control-center/manifest",
        "/control-center/dashboard",
        "/control-center/status",
        "/control-center/routes",
        "/control-center/capabilities/surface",
        "/control-center/approvals/summary",
        "/control-center/runtime-readiness/summary",
        "/control-center/foundation-gate/summary",
        "/control-center/setup-assistant/summary",
        "/control-center/actions/preview",
        "/control-center/backend-truth",
        "/control-center/turn-router/preview",
        "/control-center/today/summary",
        "/control-center/start-here/summary",
        "/control-center/proof/index",
        "/control-center/proof/{proof_ref}",
        "/control-center/trust-authority/matrix",
        "/control-center/coding/session",
        "/control-center/coding/context",
        "/control-center/coding/patch-apply-readiness",
        "/control-center/coding/patch-proposal",
        "/control-center/coding/git-review",
        "/control-center/coding/live-preview",
        "/control-center/coding/multi-agent-review",
        "/control-center/coding/test-command-readiness",
        "/control-center/actions/inbox",
        "/control-center/morning-briefing/summary",
        "/control-center/storage/status",
        "/control-center/memory/feedback",
        "/control-center/memory/observation-candidates",
        "/control-center/memory/probe",
        "/control-center/memory/contradictions",
        "/control-center/crm/summary",
        "/control-center/crm/relationships",
        "/control-center/crm/timeline",
        "/control-center/crm/follow-ups",
        "/control-center/crm/pipelines",
        "/control-center/crm/smart-lists",
        "/control-center/crm/local-mutations",
        "/control-center/providers/runtime-control-plane",
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
    assert "/control-center/sources/readiness" in paths
    assert "/api/runtime/usage-cost-analytics" in paths
    assert "/api/runtime/prompt-stability-tiers" in paths
    assert "/api/runtime/context-budget-pressure" in paths
    assert "/api/runtime/hardline-command-blocklist" in paths
    assert "/api/runtime/managed-scope-policy" in paths
    assert "/api/runtime/doctor-diagnostics" in paths
    assert "/api/runtime/session-continuity" in paths
    assert "/api/runtime/mcp-catalog-filtering" in paths
    assert "/api/runtime/background-jobs" in paths
    assert "/api/runtime/subagent-isolation" in paths
    assert "/api/runtime/worktree-per-agent" in paths
    assert "/api/runtime/lsp-diagnostics" in paths
    assert "/api/runtime/preview-rail" in paths
    assert "/api/runtime/slash-command-registry" in paths
    assert "/api/runtime/voice-media-posture" in paths
    assert "/api/runtime/messaging-gateway-posture" in paths
    assert "/api/runtime/remote-execution-posture" in paths
    assert "/api/runtime/plugin-metadata-posture" in paths
    assert "/api/runtime/skill-marketplace-posture" in paths
    assert "/api/runtime/authority-decisions/preview" in paths
    assert "/api/runtime/authority-missions/plan" in paths
    assert "/api/runtime/authority-state" in paths
    assert "/api/runtime/authority-leases" in paths
    assert "/api/runtime/authority-leases/approve-and-issue" in paths
    assert "/api/runtime/authority-leases/revoke" in paths
    assert len(paths) == EXPECTED_OPENAPI_PATH_COUNT
    assert len(operation_ids) == len(set(operation_ids)) == EXPECTED_ROUTE_COUNT


def test_control_center_action_local_task_commit_requires_exact_approval_and_receipts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    authority_state_dir = tmp_path / "authority"
    _issue_workspace_write_lease(authority_state_dir)
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
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
    assert receipt["authority_decision_ref"].startswith(
        "authority-policy-decision-ref:sha256:"
    )
    assert receipt["authority_decision_outcome"] == "ask"
    assert receipt["authority_lease_ref"].startswith("authority-lease-ref:sha256:")
    assert receipt["authority_domain_ref"] == "authority-domain-ref:workspace"
    assert receipt["authority_capability_ref"] == "authority-capability-ref:write"

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
    authority_state_dir = tmp_path / "authority"
    _issue_workspace_write_lease(authority_state_dir)
    monkeypatch.setenv(AUTHORITY_STATE_DIR_ENV, str(authority_state_dir))
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
