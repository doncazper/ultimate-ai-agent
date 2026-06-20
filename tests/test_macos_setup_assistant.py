import pytest

from ultimate_ai_agent.core.macos_setup_assistant import (
    MacOSSetupStep,
    MacOSSetupStepKind,
    MacOSSetupStepStatus,
    build_default_macos_setup_assistant_plan,
    recommend_local_model_options,
)


def test_default_macos_setup_assistant_plan_is_dry_run_only():
    plan = build_default_macos_setup_assistant_plan()

    assert plan.macos_first is True
    assert plan.local_first is True
    assert plan.disabled_by_default is True
    assert plan.native_macos_app_ready is False
    assert plan.installer_side_effects_enabled is False
    assert plan.setup_question_assistant_enabled is False
    assert plan.model_output_authoritative is False
    assert {step.kind for step in plan.steps} == {
        MacOSSetupStepKind.first_launch,
        MacOSSetupStepKind.runtime_health,
        MacOSSetupStepKind.local_model_readiness,
        MacOSSetupStepKind.model_selection,
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


def test_model_recommendations_are_safe_ref_only_and_approval_gated():
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


def test_secret_like_log_preview_is_rejected():
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


def test_side_effect_flags_are_rejected_in_foundation_slice():
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


def test_plan_exposes_approval_receipt_latency_and_rollback_refs():
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
