from typing import Any
import pytest

from ultimate_ai_agent.core.macos_setup_assistant import (
    MacOSSetupApprovalEnvelope,
    MacOSSetupApprovalEnvelopeStatus,
    MacOSSetupStep,
    MacOSSetupStepKind,
    MacOSSetupStepStatus,
    build_default_macos_setup_assistant_plan,
    recommend_local_model_options,
)


def test_default_macos_setup_assistant_plan_is_dry_run_only() -> None:
    plan = build_default_macos_setup_assistant_plan()

    assert plan.macos_first is True
    assert plan.local_first is True
    assert plan.disabled_by_default is True
    assert plan.native_macos_app_ready is False
    assert plan.installer_side_effects_enabled is False
    assert plan.lifecycle.status == "blocked_by_authority"
    assert plan.lifecycle.current_state.value == "prerequisites"
    assert plan.setup_question_assistant_enabled is False
    assert plan.model_output_authoritative is False
    assert "daily loop" in plan.full_strength_goal
    assert "Read-only setup plan" in plan.repo_safe_scope
    assert "public distribution" in plan.blocked_authority_summary
    assert "loop-ref:setup-to-daily-loop:v1" in plan.first_run_loop_refs
    assert "contract-ref:start-here-local-loop:v1" in plan.first_run_loop_refs
    assert "packaging-proof:local-macos-app-bundle" in plan.local_package_proof_refs
    assert "script:verify-local-macos-app-bundle-proof" in plan.local_package_proof_refs
    assert "promotion-path-ref:setup:exact-approved-mutation-pr" in (
        plan.promotion_path_refs
    )
    assert plan.local_package_proof_status == (
        "local_unsigned_loopback_package_proof_available_runtime_launch_blocked"
    )
    assert {step.kind for step in plan.steps} == {
        MacOSSetupStepKind.first_launch,
        MacOSSetupStepKind.runtime_health,
        MacOSSetupStepKind.local_model_readiness,
        MacOSSetupStepKind.model_selection,
        MacOSSetupStepKind.model_download_planning,
        MacOSSetupStepKind.launch_agent_setup_planning,
        MacOSSetupStepKind.local_bridge_setup_planning,
        MacOSSetupStepKind.background_service_setup_planning,
        MacOSSetupStepKind.setup_question,
        MacOSSetupStepKind.openwebui_bridge,
        MacOSSetupStepKind.mattermost_bridge,
        MacOSSetupStepKind.approval,
        MacOSSetupStepKind.receipt_audit_latency,
        MacOSSetupStepKind.rollback_uninstall,
    }
    assert all(step.terminal_command_executed is False for step in plan.steps)
    assert all(step.state_change_performed is False for step in plan.steps)
    assert all(step.model_download_performed is False for step in plan.steps)
    assert all(step.raw_log_stored is False for step in plan.steps)
    assert len(plan.approval_envelopes) == 7
    assert {
        "macos-setup-model-download",
        "macos-setup-launch-agent-change",
        "macos-setup-background-service-change",
        "macos-setup-bridge-enablement",
        "macos-setup-credential-storage",
        "macos-setup-rollback-execution",
        "macos-setup-signed-distribution",
        "macos-setup-production-authority",
    }.issubset(set(plan.blocked_capabilities))


def test_model_recommendations_are_safe_ref_only_and_approval_gated() -> None:
    recommendations = recommend_local_model_options()

    assert [item.model_ref for item in recommendations] == [
        "local-model-option:small-chat-gguf",
        "local-model-option:balanced-assistant-gguf",
        "local-model-option:coding-assistant-gguf",
        "local-model-option:bring-your-own-gguf",
    ]
    assert recommendations[0].selected_by_default is True
    assert all(item.approval_required_before_download is True for item in recommendations)
    assert all(item.model_download_performed is False for item in recommendations)
    assert all(item.model_call_performed is False for item in recommendations)
    assert all(item.raw_model_url_included is False for item in recommendations)


def test_secret_like_log_preview_is_rejected() -> None:
    with pytest.raises(ValueError, match="LOG_PREVIEW_SECRET_LIKE"):
        MacOSSetupStep(
            step_id="macos-setup-step:secret-log",
            kind=MacOSSetupStepKind.first_launch,
            label="Secret log",
            status=MacOSSetupStepStatus.dry_run_only,
            safe_summary="Secret-like terminal previews are rejected.",
            receipt_ref="receipt-plan:macos-setup-secret-log",
            rollback_ref="rollback-plan:macos-setup-secret-log",
            log_preview=["Authorization: Bearer abcdefghijklmnop"],
        )


def test_side_effect_flags_are_rejected_in_foundation_slice() -> None:
    with pytest.raises(ValueError, match="MACOS_SETUP_TERMINAL_EXECUTION_DENIED"):
        MacOSSetupStep(
            step_id="macos-setup-step:exec-denied",
            kind=MacOSSetupStepKind.first_launch,
            label="Exec denied",
            status=MacOSSetupStepStatus.dry_run_only,
            safe_summary="The foundation slice cannot execute terminal commands.",
            receipt_ref="receipt-plan:macos-setup-exec-denied",
            rollback_ref="rollback-plan:macos-setup-exec-denied",
            terminal_command_executed=True,
        )


def test_plan_exposes_approval_receipt_latency_and_rollback_refs() -> None:
    plan = build_default_macos_setup_assistant_plan()
    model_step = next(step for step in plan.steps if step.kind == MacOSSetupStepKind.model_selection)
    rollback_step = next(step for step in plan.steps if step.kind == MacOSSetupStepKind.rollback_uninstall)

    assert model_step.status == MacOSSetupStepStatus.approval_required
    assert model_step.approval_required is True
    assert model_step.approval_ref == "approval-ref:macos-setup-model-selection"
    assert model_step.receipt_ref.startswith("receipt-plan:")
    assert model_step.latency_ref.startswith("latency-ref:")
    assert rollback_step.rollback_ref.startswith("rollback-plan:")
    assert plan.receipt_plan.raw_log_stored is False
    assert plan.receipt_plan.credential_material_stored is False
    assert plan.rollback_plan.rollback_available_after_approval is True
    assert plan.rollback_plan.rollback_executed is False


def test_default_plan_exposes_dry_run_setup_approval_envelopes() -> None:
    plan = build_default_macos_setup_assistant_plan()
    steps_by_id = {step.step_id: step for step in plan.steps}
    envelopes_by_kind = {envelope.setup_step_kind: envelope for envelope in plan.approval_envelopes}

    assert set(envelopes_by_kind) == {
        MacOSSetupStepKind.model_selection,
        MacOSSetupStepKind.model_download_planning,
        MacOSSetupStepKind.launch_agent_setup_planning,
        MacOSSetupStepKind.local_bridge_setup_planning,
        MacOSSetupStepKind.background_service_setup_planning,
        MacOSSetupStepKind.openwebui_bridge,
        MacOSSetupStepKind.mattermost_bridge,
    }
    assert (
        envelopes_by_kind[MacOSSetupStepKind.model_selection].status
        == MacOSSetupApprovalEnvelopeStatus.approval_required
    )
    assert (
        envelopes_by_kind[MacOSSetupStepKind.model_download_planning].status
        == MacOSSetupApprovalEnvelopeStatus.approval_required
    )
    assert (
        envelopes_by_kind[MacOSSetupStepKind.launch_agent_setup_planning].status
        == MacOSSetupApprovalEnvelopeStatus.blocked_prerequisite_missing
    )
    assert (
        envelopes_by_kind[MacOSSetupStepKind.local_bridge_setup_planning].status
        == MacOSSetupApprovalEnvelopeStatus.approval_required
    )
    assert (
        envelopes_by_kind[MacOSSetupStepKind.background_service_setup_planning].status
        == MacOSSetupApprovalEnvelopeStatus.not_scoped
    )
    assert (
        envelopes_by_kind[MacOSSetupStepKind.openwebui_bridge].status
        == MacOSSetupApprovalEnvelopeStatus.approval_required
    )
    assert (
        envelopes_by_kind[MacOSSetupStepKind.mattermost_bridge].status
        == MacOSSetupApprovalEnvelopeStatus.approval_required
    )

    approval_required_steps = {step.kind for step in plan.steps if step.approval_required}
    assert approval_required_steps.issubset(set(envelopes_by_kind))

    for envelope in plan.approval_envelopes:
        step = steps_by_id[envelope.setup_step_id]
        assert envelope.dry_run_only is True
        assert envelope.approval_required is True
        assert envelope.approval_ref_is_identifier_only is True
        assert envelope.exact_scope_required is True
        assert envelope.idempotency_required is True
        assert envelope.rollback_required is True
        assert envelope.redaction_required is True
        assert envelope.disabled_by_default is True
        assert envelope.side_effect_class == "validation_only"
        assert envelope.approval_request_ref == step.approval_ref
        assert envelope.expected_receipt_ref == step.receipt_ref
        assert envelope.rollback_plan_ref == step.rollback_ref
        assert envelope.idempotency_key_ref.startswith("idempotency-ref:")
        assert envelope.requested_scope_refs
        assert all(ref.startswith("scope-ref:") for ref in envelope.requested_scope_refs)
        assert envelope.not_scoped_actions
        assert envelope.blocked_runtime_authority
        assert envelope.evidence_refs
        assert envelope.verifier_refs
        assert envelope.stale_state_handling
        assert envelope.redaction_summary
        assert envelope.real_execution_requested is False
        assert envelope.real_installation_requested is False
        assert envelope.subprocess_execution_requested is False
        assert envelope.model_download_requested is False
        assert envelope.launchctl_requested is False
        assert envelope.launch_agent_load_requested is False
        assert envelope.launch_agent_start_requested is False
        assert envelope.background_service_start_requested is False
        assert envelope.approval_grant_captured is False
        assert envelope.receipt_created is False
        assert envelope.audit_event_created is False
        assert envelope.rollback_executed is False


def _safe_setup_approval_envelope(**overrides: Any) -> Any:
    payload = {
        "envelope_ref": "macos-setup-approval-envelope:test",
        "status": MacOSSetupApprovalEnvelopeStatus.approval_required,
        "setup_step_id": "macos-setup-step:model-download-planning",
        "setup_step_kind": MacOSSetupStepKind.model_download_planning,
        "safe_summary": "Dry-run setup approval envelope for safe test metadata only.",
        "requested_scope_refs": ["scope-ref:macos-setup-test"],
        "approval_request_ref": "approval-ref:macos-setup-test",
        "expected_receipt_ref": "receipt-plan:macos-setup-test",
        "rollback_plan_ref": "rollback-plan:macos-setup-test",
        "idempotency_key_ref": "idempotency-ref:macos-setup-test",
        "risk_class": "high",
        "side_effect_class": "validation_only",
        "not_scoped_actions": ["model-download-execution"],
        "blocked_runtime_authority": ["control-center-setup-model-downloads"],
        "evidence_refs": ["docs-ref:uaa-setup-assistant-plan"],
        "verifier_refs": ["pytest:test-macos-setup-assistant"],
        "operator_next_action": "review-test-envelope",
        "stale_state_handling": "Stale if setup refs change before review.",
        "redaction_summary": "Safe refs only; raw logs and credentials are omitted.",
    }
    payload.update(overrides)
    return MacOSSetupApprovalEnvelope(**payload)


@pytest.mark.parametrize(
    ("field_name", "reason"),
    [
        ("real_execution_requested", "MACOS_SETUP_APPROVAL_ENVELOPE_EXECUTION_DENIED"),
        ("real_installation_requested", "MACOS_SETUP_APPROVAL_ENVELOPE_INSTALLATION_DENIED"),
        ("subprocess_execution_requested", "MACOS_SETUP_APPROVAL_ENVELOPE_SUBPROCESS_DENIED"),
        ("launchctl_requested", "MACOS_SETUP_APPROVAL_ENVELOPE_LAUNCHCTL_DENIED"),
        (
            "launch_agent_load_requested",
            "MACOS_SETUP_APPROVAL_ENVELOPE_LAUNCH_AGENT_LOAD_DENIED",
        ),
        (
            "launch_agent_start_requested",
            "MACOS_SETUP_APPROVAL_ENVELOPE_LAUNCH_AGENT_START_DENIED",
        ),
        ("model_download_requested", "MACOS_SETUP_APPROVAL_ENVELOPE_MODEL_DOWNLOAD_DENIED"),
        (
            "background_service_start_requested",
            "MACOS_SETUP_APPROVAL_ENVELOPE_BACKGROUND_SERVICE_DENIED",
        ),
        (
            "network_or_cache_write_requested",
            "MACOS_SETUP_APPROVAL_ENVELOPE_NETWORK_CACHE_WRITE_DENIED",
        ),
        (
            "provider_or_model_call_requested",
            "MACOS_SETUP_APPROVAL_ENVELOPE_PROVIDER_MODEL_CALL_DENIED",
        ),
        ("credential_capture_requested", "MACOS_SETUP_APPROVAL_ENVELOPE_CREDENTIAL_DENIED"),
        ("connector_write_requested", "MACOS_SETUP_APPROVAL_ENVELOPE_CONNECTOR_WRITE_DENIED"),
        ("approval_grant_captured", "MACOS_SETUP_APPROVAL_GRANT_CAPTURE_DENIED"),
        ("receipt_created", "MACOS_SETUP_APPROVAL_ENVELOPE_RECEIPT_CREATION_DENIED"),
        ("audit_event_created", "MACOS_SETUP_APPROVAL_ENVELOPE_AUDIT_CREATION_DENIED"),
        ("rollback_executed", "MACOS_SETUP_APPROVAL_ENVELOPE_ROLLBACK_EXECUTION_DENIED"),
        ("raw_path_included", "MACOS_SETUP_APPROVAL_ENVELOPE_RAW_PATH_DENIED"),
        ("raw_log_included", "MACOS_SETUP_APPROVAL_ENVELOPE_RAW_LOG_DENIED"),
        ("raw_prompt_included", "MACOS_SETUP_APPROVAL_ENVELOPE_RAW_PROMPT_DENIED"),
        (
            "raw_provider_payload_included",
            "MACOS_SETUP_APPROVAL_ENVELOPE_RAW_PROVIDER_PAYLOAD_DENIED",
        ),
        ("secret_like_value_included", "MACOS_SETUP_APPROVAL_ENVELOPE_SECRET_LIKE_DENIED"),
        ("unscoped_authority_requested", "MACOS_SETUP_APPROVAL_ENVELOPE_UNSCOPED_DENIED"),
        (
            "production_authority_requested",
            "MACOS_SETUP_APPROVAL_ENVELOPE_PRODUCTION_AUTHORITY_DENIED",
        ),
    ],
)
def test_setup_approval_envelope_rejects_unsafe_authority_requests(field_name: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        _safe_setup_approval_envelope(**{field_name: True})


def test_setup_approval_envelope_rejects_launchctl_and_raw_paths() -> None:
    with pytest.raises(ValueError, match="MACOS_SETUP_APPROVAL_ENVELOPE_RUNTIME_TEXT_DENIED"):
        _safe_setup_approval_envelope(stale_state_handling="Run launchctl load now.")

    with pytest.raises(ValueError, match="MACOS_SETUP_APPROVAL_ENVELOPE_RAW_PATH_DENIED"):
        _safe_setup_approval_envelope(
            safe_summary="Use /Users/local/operator/Library path for setup."
        )


def test_setup_approval_envelope_requires_safe_refs_and_validation_only_side_effect_class() -> None:
    with pytest.raises(ValueError, match="APPROVAL_REQUEST_REF_PREFIX_REQUIRED"):
        _safe_setup_approval_envelope(approval_request_ref="approval-placeholder")

    with pytest.raises(ValueError, match="MACOS_SETUP_APPROVAL_TEST_REF_DENIED"):
        _safe_setup_approval_envelope(approval_request_ref="approval_test_ref")

    with pytest.raises(ValueError, match="EXPECTED_RECEIPT_REF_PREFIX_REQUIRED"):
        _safe_setup_approval_envelope(expected_receipt_ref="receipt:test")

    with pytest.raises(ValueError, match="ROLLBACK_PLAN_REF_PREFIX_REQUIRED"):
        _safe_setup_approval_envelope(rollback_plan_ref="rollback:test")

    with pytest.raises(ValueError, match="IDEMPOTENCY_KEY_REF_PREFIX_REQUIRED"):
        _safe_setup_approval_envelope(idempotency_key_ref="idempotency:test")

    with pytest.raises(ValueError, match="REQUESTED_SCOPE_REF_PREFIX_REQUIRED"):
        _safe_setup_approval_envelope(requested_scope_refs=["unsafe-scope:test"])

    with pytest.raises(ValueError, match="MACOS_SETUP_APPROVAL_ENVELOPE_SIDE_EFFECT_CLASS_DENIED"):
        _safe_setup_approval_envelope(side_effect_class="local_dev_workspace_only")
