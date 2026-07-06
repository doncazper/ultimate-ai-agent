import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center import (
    GovernedProviderInvocationReadiness,
    ProviderCostGovernorBinding,
    ProviderCredentialReadinessPosture,
    ProviderCredentialReadinessItem,
    ProviderCredentialReadinessSummary,
    ProviderCredentialValidationReadiness,
    ProviderCredentialVaultAdapterReadiness,
    ProviderSettingsDiagnosticItem,
    ProviderSettingsDiagnosticsSummary,
    build_control_center_dashboard,
    build_provider_credential_readiness_summary,
)
from ultimate_ai_agent.core.local_model_management.gateway import (
    UAA_LLAMA_CPP_GATEWAY_ENV,
    UAA_LLAMA_CPP_GATEWAY_KEY_ENV,
)
from ultimate_ai_agent.core.task_decomposition.api_safety import (
    TASK_DECOMPOSITION_API_BEARER_ENV,
    TASK_DECOMPOSITION_API_ENV,
)


def test_control_center_dashboard_snapshot_is_safe_summary_only() -> None:
    snapshot = build_control_center_dashboard(
        baseline_version="0.16.0",
        api_route_count=74,
        foundation_gate_status="passed",
    )

    assert snapshot.system_status.status == "available_read_only"
    assert snapshot.foundation_gate_summary.status == "passed"
    assert snapshot.runtime_readiness_summary.production_ready is False
    assert snapshot.api_summary.route_count == 74
    assert snapshot.api_summary.control_center_route_count == 60
    assert snapshot.approval_summary.pending_count == 0
    assert snapshot.remote_worker_summary.execution_enabled is False
    assert snapshot.private_mesh_summary.status == "planned_disabled"
    assert snapshot.mobile_planning_summary.sensor_access_enabled is False
    assert snapshot.plugin_governance_summary.plugin_enablement_allowed is False
    assert snapshot.plugin_governance_summary.skill_bundle_proposal_count == 1
    assert (
        snapshot.plugin_governance_summary.skill_bundle_proposal_refs
        == ["skill-bundle-proposal:founder-loop-review"]
    )
    assert snapshot.plugin_governance_summary.skill_bundle_activation_enabled is False
    assert (
        snapshot.plugin_governance_summary.skill_bundle_tool_execution_enabled is False
    )
    assert snapshot.provider_credential_readiness.status == "reference_readiness_only"
    assert snapshot.provider_credential_readiness.invocation_enabled is False
    assert snapshot.provider_credential_readiness.raw_key_collection_enabled is False
    assert snapshot.provider_credential_readiness.credential_material_stored is False
    assert snapshot.provider_credential_readiness.vault_adapter_configured is False
    assert snapshot.provider_credential_readiness.cost_governor_binding_required is True
    assert snapshot.provider_credential_readiness.provider_model_refs_required is True
    assert snapshot.provider_credential_readiness.cost_estimate_ref_required is True
    assert snapshot.provider_credential_readiness.budget_decision_ref_required is True
    assert snapshot.provider_credential_readiness.max_approved_usd_ref_required is True
    assert snapshot.provider_credential_readiness.future_receipt_refs_required is True
    assert (
        snapshot.provider_credential_readiness.unknown_paid_cost_requires_approval
        is True
    )
    assert (
        snapshot.provider_credential_readiness.estimated_cost_above_budget_blocks_use
        is True
    )
    assert (
        snapshot.provider_credential_readiness.provider_usage_claim_requires_receipt_refs
        is True
    )
    assert (
        snapshot.provider_credential_readiness.provider_runtime_authority_denied is True
    )
    assert (
        snapshot.provider_credential_readiness.provider_spend_authority_denied is True
    )
    assert (
        snapshot.provider_credential_readiness.vault_adapter_readiness.adapter_runtime_enabled
        is False
    )
    assert (
        snapshot.provider_credential_readiness.enrollment_readiness.enrollment_enabled
        is False
    )
    assert (
        snapshot.provider_credential_readiness.validation_readiness.validation_enabled
        is False
    )
    assert (
        snapshot.provider_credential_readiness.invocation_readiness.invocation_enabled
        is False
    )
    assert (
        snapshot.provider_credential_readiness.router_dry_run_readiness.proposal_only
        is True
    )
    assert (
        snapshot.provider_credential_readiness.router_dry_run_readiness.invocation_authorized
        is False
    )
    assert (
        snapshot.provider_credential_readiness.router_dry_run_readiness.fallback_execution_authorized
        is False
    )
    assert (
        snapshot.provider_credential_readiness.router_dry_run_readiness.provider_sdk_call_performed
        is False
    )
    assert (
        snapshot.provider_credential_readiness.router_dry_run_readiness.billing_authority_granted
        is False
    )
    assert snapshot.operator_loop_summary.milestone_ref == "UAA-P1-011"
    assert snapshot.operator_loop_summary.frontend_authority is False
    assert snapshot.operator_loop_summary.production_ready is False
    assert snapshot.next_recommended_action == "review_status_and_previews_only"


def test_control_center_dashboard_contains_no_raw_or_secret_content() -> None:
    snapshot = build_control_center_dashboard(baseline_version="0.16.0")
    dump = snapshot.model_dump_json().lower()

    forbidden_fragments = [
        "api_key='abcdefghijklmnop'",
        "raw_prompt",
        "file_contents",
        "memory_contents",
        "credential_value",
        "private_key",
        "remote execution enabled",
        "mobile sensor enabled",
        "plugin enabled",
        "provider invocation enabled",
        "credential material stored",
        "raw provider credential",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in dump


def test_operator_loop_summary_reports_local_backend_prerequisites_without_authority() -> (
    None
):
    snapshot = build_control_center_dashboard(
        env={
            UAA_LLAMA_CPP_GATEWAY_ENV: "1",
            UAA_LLAMA_CPP_GATEWAY_KEY_ENV: "local-test-placeholder",
            TASK_DECOMPOSITION_API_ENV: "1",
            TASK_DECOMPOSITION_API_BEARER_ENV: "local-task-placeholder",
        }
    )

    loop = snapshot.operator_loop_summary
    statuses = {step.step_id: step.status for step in loop.steps}

    assert loop.status == "local_backend_loop_inspectable"
    assert loop.frontend_authority is False
    assert loop.control_center_mutation_allowed is False
    assert loop.model_output_authoritative is False
    assert loop.blocked_prerequisites == []
    assert statuses["runtime_health"] == "route_ready"
    assert statuses["local_model_readiness"] == "gateway_enabled_requires_bearer"
    assert statuses["uaa_v1_chat"] == "gateway_enabled_requires_bearer"
    assert (
        statuses["task_decomposition_plan"] == "local_authority_enabled_requires_bearer"
    )
    assert (
        statuses["safe_capability_approval"]
        == "local_authority_enabled_requires_bearer"
    )
    assert statuses["receipt_audit_latency_rollback"] == "inspection_route_ready"
    assert "/v1/chat/completions" in loop.inspection_route_refs
    assert "/task-decomposition/metrics" in loop.inspection_route_refs


def test_provider_credential_readiness_is_reference_only() -> None:
    summary = build_provider_credential_readiness_summary()

    assert summary.status == "reference_readiness_only"
    assert summary.invocation_enabled is False
    assert summary.raw_key_collection_enabled is False
    assert summary.credential_material_stored is False
    assert summary.vault_adapter_configured is False
    assert (
        summary.vault_adapter_readiness.readiness_status
        == "blocked_no_approved_backend"
    )
    assert summary.vault_adapter_readiness.adapter_available is False
    assert summary.vault_adapter_readiness.supports_write is False
    assert summary.vault_adapter_readiness.supports_read_handle is False
    assert summary.vault_adapter_readiness.supports_revoke is False
    assert summary.vault_adapter_readiness.credential_material_stored_by_repo is False
    assert summary.vault_adapter_readiness.raw_key_visible is False
    assert summary.vault_adapter_readiness.adapter_runtime_enabled is False
    assert (
        summary.enrollment_readiness.readiness_status == "blocked_disabled_by_default"
    )
    assert summary.enrollment_readiness.enrollment_enabled is False
    assert summary.enrollment_readiness.raw_key_collection_enabled is False
    assert summary.enrollment_readiness.credential_material_stored_by_repo is False
    assert summary.validation_readiness.readiness_status == "validation_blocked"
    assert summary.validation_readiness.validation_enabled is False
    assert summary.validation_readiness.external_validation_allowed is False
    assert summary.validation_readiness.provider_response_persistence_allowed is False
    assert summary.validation_readiness.exact_approval_required is True
    assert "approval required" in summary.validation_readiness.ui_states
    assert summary.invocation_readiness.readiness_status == "blocked_not_scoped"
    assert summary.invocation_readiness.invocation_enabled is False
    assert summary.invocation_readiness.policy_engine_required is True
    assert summary.invocation_readiness.local_approval_required is True
    assert summary.invocation_readiness.model_output_authoritative is False
    assert set(summary.supported_readiness_postures) == set(
        ProviderCredentialReadinessPosture
    )
    assert summary.posture_counts[ProviderCredentialReadinessPosture.configured] == 0
    assert summary.posture_counts[
        ProviderCredentialReadinessPosture.not_configured
    ] == len(summary.providers)
    assert summary.posture_counts[ProviderCredentialReadinessPosture.cost_blocked] == 0
    assert summary.cost_governor_binding_required is True
    assert summary.unknown_paid_cost_requires_approval is True
    assert summary.provider_usage_claim_requires_receipt_refs is True
    assert summary.provider_settings_diagnostics.status == "readable_diagnostics_only"
    assert summary.provider_settings_diagnostics.provider_sdk_call_enabled is False
    assert summary.provider_settings_diagnostics.model_invocation_enabled is False
    assert summary.provider_settings_diagnostics.provider_validation_performed is False
    assert summary.provider_settings_diagnostics.router_execution_authorized is False
    assert summary.provider_settings_diagnostics.paid_authority_granted is False
    assert (
        summary.provider_settings_diagnostics.model_dump(mode="json")[
            "billing_authority_granted"
        ]
        is False
    )
    assert summary.provider_settings_diagnostics.settings_mutation_enabled is False
    assert summary.provider_settings_diagnostics.production_authority_enabled is False
    assert summary.provider_settings_diagnostics.supported_states == [
        "configured",
        "missing",
        "blocked",
        "degraded",
        "revoked",
        "expired",
        "cost_blocked",
        "disabled",
        "future_scoped",
    ]
    assert summary.provider_settings_diagnostics.state_counts["missing"] == len(
        summary.providers
    )
    assert summary.provider_settings_diagnostics.state_counts["cost_blocked"] == 1
    assert summary.provider_settings_diagnostics.state_counts["disabled"] == 3
    assert summary.provider_settings_diagnostics.state_counts["future_scoped"] == 2
    diagnostic_labels = {
        item.label for item in summary.provider_settings_diagnostics.items
    }
    assert "CostGovernor provider spend boundary" in diagnostic_labels
    assert "Provider credential validation" in diagnostic_labels
    assert "Provider router dry-run" in diagnostic_labels
    assert "PROVIDER_INVOCATION_NOT_SCOPED" in summary.blocker_codes
    assert "CREDENTIAL_REFERENCE_NOT_BOUND" in summary.blocker_codes
    assert "VAULT_ADAPTER_NOT_SCOPED" in summary.blocker_codes
    assert len(summary.providers) >= 3

    for provider in summary.providers:
        assert provider.provider_manifest_ref.startswith("provider-manifest-ref:")
        assert provider.credential_ref.startswith("credential-ref:")
        assert provider.consent_ref.startswith("consent-ref:")
        assert provider.policy_ref.startswith("policy-ref:")
        assert provider.revocation_ref.startswith("revocation-ref:")
        assert provider.approval_ref.startswith("approval-ref:")
        assert provider.invocation_enabled is False
        assert provider.credential_material_stored is False
        assert provider.raw_key_visible is False
        assert provider.readiness_status == "blocked_reference_only"
        assert (
            provider.readiness_posture
            == ProviderCredentialReadinessPosture.not_configured
        )
        assert provider.cost_governor_binding.provider_ref == provider.provider_id
        assert provider.cost_governor_binding.credential_ref == provider.credential_ref
        assert provider.cost_governor_binding.provider_ref_status == "present"
        assert provider.cost_governor_binding.model_ref_status == "missing"
        assert (
            provider.cost_governor_binding.unknown_paid_cost_requires_approval is True
        )
        assert (
            provider.cost_governor_binding.provider_usage_claim_requires_receipt_refs
            is True
        )
        assert provider.cost_governor_binding.provider_use_authority_granted is False
        assert (
            "UNKNOWN_PAID_COST_REQUIRES_APPROVAL"
            in provider.cost_governor_binding.blocker_codes
        )
        assert (
            "COST_ESTIMATE_REF_REQUIRED" in provider.cost_governor_binding.blocker_codes
        )
        assert (
            "BUDGET_DECISION_REF_REQUIRED"
            in provider.cost_governor_binding.blocker_codes
        )
        assert (
            "FUTURE_RECEIPT_REFS_REQUIRED"
            in provider.cost_governor_binding.blocker_codes
        )

    for item in summary.provider_settings_diagnostics.items:
        assert item.reason_codes
        assert item.safe_summary
        assert item.next_safe_action
        assert item.blocked_authority_refs
        assert item.evidence_refs
        assert item.cli_inspection_refs
        assert item.provider_sdk_call_enabled is False
        assert item.model_invocation_enabled is False
        assert item.provider_validation_performed is False
        assert item.router_execution_authorized is False
        assert item.paid_authority_granted is False
        assert item.model_dump(mode="json")["billing_authority_granted"] is False
        assert item.raw_credential_visible is False
        assert item.raw_provider_payload_persisted is False


def test_provider_credential_readiness_rejects_authority_or_secret_like_refs() -> None:
    with pytest.raises(ValidationError, match="AUTHORITY_DENIED"):
        ProviderCredentialReadinessSummary(invocation_enabled=True, providers=[])

    with pytest.raises(ValidationError, match="COST_GOVERNOR_GATE_DENIED"):
        ProviderCredentialReadinessSummary(
            cost_governor_binding_required=False, providers=[]
        )

    with pytest.raises(ValidationError, match="COST_AUTHORITY_DENIED"):
        ProviderCredentialReadinessSummary(
            provider_runtime_authority_denied=False, providers=[]
        )

    with pytest.raises(ValidationError, match="COST_AUTHORITY_DENIED"):
        ProviderCredentialReadinessSummary(
            provider_spend_authority_denied=False, providers=[]
        )

    with pytest.raises(ValidationError, match="POSTURE_COUNTS_MISMATCH"):
        ProviderCredentialReadinessSummary(
            posture_counts={ProviderCredentialReadinessPosture.configured: 99},
            providers=[],
        )

    with pytest.raises(ValidationError, match="CONFIGURED_REF_POSTURE_MISMATCH"):
        ProviderCredentialReadinessItem(
            provider_id="provider:openai-compatible:reference",
            provider_label="OpenAI-compatible provider",
            provider_kind="frontier_model",
            provider_manifest_ref="provider-manifest-ref:openai-compatible:reference-only",
            credential_ref="credential-ref:openai-compatible:not-configured",
            credential_ref_status="reference_missing",
            consent_ref="consent-ref:provider-runtime:not-granted",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            revocation_ref="revocation-ref:provider-runtime:not-active",
            approval_ref="approval-ref:provider-runtime:not-granted",
            credential_configured=True,
            safe_summary="Provider readiness is metadata only.",
        )

    with pytest.raises(ValidationError, match="PROVIDER_MODEL_REF_BOUND_MISMATCH"):
        ProviderCredentialReadinessItem(
            provider_id="provider:openai-compatible:reference",
            provider_label="OpenAI-compatible provider",
            provider_kind="frontier_model",
            provider_manifest_ref="provider-manifest-ref:openai-compatible:reference-only",
            credential_ref="credential-ref:openai-compatible:not-configured",
            credential_ref_status="reference_missing",
            consent_ref="consent-ref:provider-runtime:not-granted",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            revocation_ref="revocation-ref:provider-runtime:not-active",
            approval_ref="approval-ref:provider-runtime:not-granted",
            provider_model_refs_bound=True,
            safe_summary="Provider readiness is metadata only.",
        )

    with pytest.raises(ValidationError, match="PROVIDER_REF_MISMATCH"):
        ProviderCredentialReadinessItem(
            provider_id="provider:openai-compatible:reference",
            provider_label="OpenAI-compatible provider",
            provider_kind="frontier_model",
            provider_manifest_ref="provider-manifest-ref:openai-compatible:reference-only",
            credential_ref="credential-ref:openai-compatible:not-configured",
            credential_ref_status="reference_missing",
            consent_ref="consent-ref:provider-runtime:not-granted",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            revocation_ref="revocation-ref:provider-runtime:not-active",
            approval_ref="approval-ref:provider-runtime:not-granted",
            provider_model_refs_bound=True,
            cost_governor_binding=ProviderCostGovernorBinding(
                provider_ref="provider:anthropic-compatible:reference",
                provider_ref_status="present",
                model_ref="model-ref:anthropic-compatible:selected",
                model_ref_status="present",
                credential_ref="credential-ref:openai-compatible:not-configured",
            ),
            safe_summary="Provider readiness is metadata only.",
        )

    with pytest.raises(ValidationError, match="CREDENTIAL_REF_MISMATCH"):
        ProviderCredentialReadinessItem(
            provider_id="provider:openai-compatible:reference",
            provider_label="OpenAI-compatible provider",
            provider_kind="frontier_model",
            provider_manifest_ref="provider-manifest-ref:openai-compatible:reference-only",
            credential_ref="credential-ref:openai-compatible:not-configured",
            credential_ref_status="reference_missing",
            consent_ref="consent-ref:provider-runtime:not-granted",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            revocation_ref="revocation-ref:provider-runtime:not-active",
            approval_ref="approval-ref:provider-runtime:not-granted",
            cost_governor_binding=ProviderCostGovernorBinding(
                provider_ref="provider:openai-compatible:reference",
                provider_ref_status="present",
                credential_ref="credential-ref:anthropic-compatible:reference",
            ),
            safe_summary="Provider readiness is metadata only.",
        )

    with pytest.raises(ValidationError, match="STORAGE_DENIED"):
        ProviderCredentialReadinessSummary(
            credential_material_stored=True, providers=[]
        )

    with pytest.raises(ValidationError, match="VAULT_AUTHORITY_DENIED"):
        ProviderCredentialVaultAdapterReadiness(adapter_runtime_enabled=True)

    with pytest.raises(ValidationError, match="ENROLLMENT_AUTHORITY_DENIED"):
        ProviderCredentialReadinessSummary(
            enrollment_readiness={"enrollment_enabled": True},
            providers=[],
        )

    with pytest.raises(ValidationError, match="VALIDATION_AUTHORITY_DENIED"):
        ProviderCredentialValidationReadiness(validation_enabled=True)

    with pytest.raises(ValidationError, match="INVOCATION_AUTHORITY_DENIED"):
        GovernedProviderInvocationReadiness(invocation_enabled=True)

    unsafe_ref = "token=" + ("A" * 16)
    with pytest.raises(ValidationError, match="SECRET_LIKE_VALUE_REJECTED"):
        ProviderCredentialReadinessItem(
            provider_id="provider:unsafe:reference",
            provider_label="Unsafe reference",
            provider_kind="frontier_model",
            provider_manifest_ref="provider-manifest-ref:unsafe:reference-only",
            credential_ref=unsafe_ref,
            credential_ref_status="reference_missing",
            consent_ref="consent-ref:provider-runtime:not-granted",
            policy_ref="policy-ref:provider-runtime:disabled-by-default",
            revocation_ref="revocation-ref:provider-runtime:not-active",
            approval_ref="approval-ref:provider-runtime:not-granted",
            blocker_codes=["CREDENTIAL_REFERENCE_NOT_BOUND"],
            safe_summary="Unsafe credential ref is rejected before readiness is persisted.",
        )

    with pytest.raises(ValidationError, match="DIAGNOSTIC_AUTHORITY_DENIED"):
        ProviderSettingsDiagnosticItem(
            diagnostic_ref="provider-settings-diagnostic:test",
            label="Unsafe provider diagnostic",
            state="blocked",
            state_label="Blocked",
            reason_codes=["UNSAFE"],
            safe_summary="Unsafe diagnostic.",
            next_safe_action="Review only.",
            blocked_authority_refs=["blocked-state:test"],
            evidence_refs=["evidence-ref:test"],
            cli_inspection_refs=["scripts/inspect_provider_credential_readiness.py"],
            provider_sdk_call_enabled=True,
        )

    with pytest.raises(ValidationError, match="DIAGNOSTICS_AUTHORITY_DENIED"):
        ProviderSettingsDiagnosticsSummary(
            provider_sdk_call_enabled=True,
            items=[
                ProviderSettingsDiagnosticItem(
                    diagnostic_ref="provider-settings-diagnostic:test",
                    label="Provider diagnostic",
                    state="blocked",
                    state_label="Blocked",
                    reason_codes=["BLOCKED"],
                    safe_summary="Provider diagnostic is blocked.",
                    next_safe_action="Review only.",
                    blocked_authority_refs=["blocked-state:test"],
                    evidence_refs=["evidence-ref:test"],
                    cli_inspection_refs=[
                        "scripts/inspect_provider_credential_readiness.py"
                    ],
                )
            ],
        )
