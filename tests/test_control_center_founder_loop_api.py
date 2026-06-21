from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.api.manifest import build_api_manifest
from ultimate_ai_agent.core.storage import TODAY_PRODUCT_SPINE_CONTRACT_REF


client = TestClient(app)


def test_control_center_founder_loop_routes_are_storage_backed_and_safe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))

    for path, operation in [
        ("/control-center/today/summary", "control_center_today_summary"),
        ("/control-center/actions/inbox", "control_center_actions_inbox"),
        ("/control-center/morning-briefing/summary", "control_center_morning_briefing_summary"),
        ("/control-center/storage/status", "control_center_storage_status"),
    ]:
        response = client.get(path)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["operation"] == operation
        assert "safe_refs_only" in body["redactions_applied"]
        serialized = response.text.lower()
        assert str(tmp_path).lower() not in serialized
        assert "raw_prompt" not in serialized
        assert "raw_response" not in serialized
        assert "provider_payload" not in serialized
        assert "api_key" not in serialized

    inbox = client.get("/control-center/actions/inbox").json()["data"]
    assert inbox["route_ref"] == "/control-center/actions/inbox"
    assert inbox["mutating_controls_enabled"] is False
    assert "GET /control-center/storage/status" in inbox["read_only_route_refs"]
    assert "capability-ref:local-approval-authority" in inbox["local_prerequisite_refs"]
    assert "no_approval_grant_capture_route" in inbox["blocked_states"]

    setup_item = next(
        item
        for item in inbox["items"]
        if item["item_ref"] == "founder-action:setup-assistant-hardening"
    )
    assert setup_item["approval_required"] is True
    assert (
        setup_item["approval_envelope_ref"]
        == "approval-envelope:founder-loop:setup-assistant-hardening"
    )
    assert setup_item["approval_envelope_status"] == "dry_run_ref_available"
    assert (
        setup_item["state_change_readiness"]
        == "blocked_pending_scoped_mutation_contract"
    )
    assert setup_item["receipt_refs"] == [
        "receipt-plan:founder-loop:setup-assistant-hardening"
    ]
    assert setup_item["audit_refs"] == [
        "audit-plan:founder-loop:setup-assistant-hardening"
    ]
    assert (
        setup_item["idempotency_key_ref"]
        == "idempotency-ref:founder-loop:setup-assistant-hardening"
    )
    assert setup_item["rollback_ref"] == "rollback-plan:founder-loop:setup-assistant-hardening"
    assert setup_item["safe_disable_ref"] == "safe-disable:founder-loop:setup-assistant-hardening"

    briefing = client.get("/control-center/morning-briefing/summary").json()["data"]
    assert briefing["route_ref"] == "/control-center/morning-briefing/summary"
    assert briefing["bounded_preview_only"] is True
    assert briefing["refresh_enabled"] is False
    assert briefing["notification_delivery_enabled"] is False
    assert briefing["source_readiness"] == (
        "blocked_missing_email_calendar_notification_contracts"
    )
    assert "contract-ref:email-read-only-missing" in briefing["missing_contract_refs"]
    assert "no_background_refresh" in briefing["blocked_states"]
    assert "no_notification_delivery" in briefing["blocked_states"]

    briefing_item = next(
        item
        for item in briefing["items"]
        if item["briefing_ref"] == "briefing:api-boundary-modularization"
    )
    assert briefing_item["priority"] == "high"
    assert briefing_item["source_readiness"] == "local_status_refs_only"
    assert briefing_item["source_refs"] == ["source-ref:control-center-route-status"]
    assert (
        "contract-ref:notification-delivery-missing"
        in briefing_item["missing_contract_refs"]
    )
    assert "no_background_refresh" in briefing_item["blocked_states"]
    assert briefing_item["stale_state"] == "recheck_route_status_before_briefing_use"
    assert "source evidence is bound" in briefing_item["evidence_gap"]
    assert "define source contracts" in briefing_item["next_safe_action"]

    today = client.get("/control-center/today/summary").json()["data"]
    assert today["product_spine_contract_ref"] == TODAY_PRODUCT_SPINE_CONTRACT_REF
    assert today["required_loop_surfaces"] == [
        "Today",
        "Actions",
        "Evidence",
        "Memory",
    ]
    assert {
        item["signal"]
        for item in today["required_today_signals"]
    } == {
        "priorities",
        "blockers",
        "follow_ups",
        "plan_action_state",
        "memory_review_count",
        "stale_source_posture",
        "next_safe_actions",
    }
    assert today["module_completion_contract"]["visibility_is_sufficient_for_completion"] is False
    assert today["module_completion_contract"]["standalone_module_complete_allowed"] is False
    module_feeds = {
        item["module"]: item
        for item in today["module_feed_contract"]
    }
    assert {"Today", "Actions", "Plans", "Memory", "Evidence", "Chat", "Code"} <= set(module_feeds)
    assert module_feeds["Chat"]["status"] == "planned_blocked_until_uaa_p1_074"
    assert module_feeds["Code"]["status"] == "planned_blocked_until_uaa_p1_075"
    assert today["plan_action_state"]["execution_authorized"] is False
    assert today["plan_action_state"]["mutating_controls_enabled"] is False
    assert today["stale_source_posture"]["connector_runtime_enabled"] is False
    assert today["next_safe_actions"]
    assert today["memory_review_route_ref"] == "/memory"
    assert (
        today["memory_review_backend_route_ref"]
        == "GET /control-center/today/summary"
    )
    assert today["memory_review_status"] == "storage_backed_review_queue"
    assert today["memory_write_enabled"] is False
    assert today["memory_delete_enabled"] is False
    assert today["context_injection_enabled"] is False
    assert (
        "contract-ref:memory-write-policy-binding-missing"
        in today["memory_review_missing_contract_refs"]
    )
    assert "no_memory_write" in today["memory_review_blocked_states"]
    assert "no_context_injection" in today["memory_review_blocked_states"]
    assert "no_raw_source_display" in today["memory_review_blocked_states"]
    memory_item = next(
        item
        for item in today["memory_review_queue"]
        if item["review_ref"] == "memory-review:founder-loop-preferences"
    )
    assert memory_item["candidate_kind"] == "operator_preference"
    assert memory_item["priority"] == "high"
    assert memory_item["review_state"] == "review_needed"
    assert memory_item["provenance_refs"] == [
        "provenance-ref:founder-loop-memory:preferences"
    ]
    assert memory_item["source_refs"] == ["source-ref:founder-loop-storage"]
    assert (
        "contract-ref:memory-retention-delete-missing"
        in memory_item["missing_contract_refs"]
    )
    assert (
        memory_item["correction_posture"]
        == "correction_requires_scoped_memory_write_contract"
    )
    assert (
        memory_item["rejection_posture"]
        == "rejection_is_review_state_only_until_capture_contract"
    )
    assert memory_item["retention_posture"] == "retention_policy_not_bound"
    assert memory_item["delete_posture"] == "delete_execution_not_scoped"
    assert memory_item["confidence_posture"] == "safe_summary_unverified"
    assert memory_item["stale_state"] == "recheck_source_refs_before_memory_use"
    assert "no_model_provider_authority" in memory_item["blocked_states"]
    assert "scoped memory policy milestone" in memory_item["next_safe_action"]


def test_control_center_founder_loop_routes_are_in_manifest_with_local_state_class(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(tmp_path / "founder_loop"))
    manifest = build_api_manifest(app)
    routes = {route.path: route for route in manifest.routes}

    assert manifest.route_count == 112
    for path in [
        "/control-center/today/summary",
        "/control-center/actions/inbox",
        "/control-center/morning-briefing/summary",
        "/control-center/storage/status",
    ]:
        assert path in routes
        assert routes[path].method == "GET"
        assert routes[path].side_effect_class == "local_dev_workspace_only"
        assert routes[path].operation_id.startswith("get_control_center_")

    assert "control_center_founder_loop_storage_summaries" in manifest.capabilities_declared
