from __future__ import annotations

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.web_access import (
    WEB_RUNTIME_AUTHORITY_PROMOTION_LADDER,
    WEB_RUNTIME_AUTHORITY_PROMOTION_LADDER_STATUSES,
    WEB_RUNTIME_CANONICAL_NOUNS,
    WEB_RUNTIME_PROMOTION_STEPS,
    WEB_RUNTIME_REQUIRED_OPERATOR_LABELS,
    WEB_RUNTIME_REQUIRED_SIDE_EFFECTS,
    WebApprovalLinkageContract,
    WebCatalogManifestVisibilityContract,
    WebProviderDiagnosticContract,
    WebRuntimeCostGovernorPostureContract,
    WebRuntimeAuditRecordContract,
    WebRuntimeNoun,
    WebRuntimePromotionLadderStepContract,
    WebSideEffectLedgerContract,
    build_web_runtime_authority_contract,
)


def _audit_record(**overrides: object) -> WebRuntimeAuditRecordContract:
    payload = {
        "audit_record_ref": "web-audit-record-ref:test",
        "web_request_ref": "web-request-ref:test",
        "web_evidence_refs": ("web-evidence-ref:test",),
        "policy_decision_ref": "policy-decision-ref:test",
        "scope_ref": "scope-ref:web-runtime:test",
        "actor_ref": "actor-ref:test",
        "redacted_summary": "Safe redacted runtime posture summary.",
    }
    payload.update(overrides)
    return WebRuntimeAuditRecordContract(**payload)


def test_canonical_web_runtime_nouns_are_complete() -> None:
    contract = build_web_runtime_authority_contract()

    assert contract.scope_posture == "broad_unrestricted_ladder_only"
    assert contract.exact_lanes_do_not_promote_broad_authority is True
    assert WEB_RUNTIME_CANONICAL_NOUNS == (
        "web_request",
        "web_observation",
        "web_evidence",
        "web_approval",
        "web_action_plan",
        "web_audit_record",
    )
    assert tuple(contract.model_dump(mode="python")["canonical_nouns"]) == (
        WEB_RUNTIME_CANONICAL_NOUNS
    )

    with pytest.raises((ValidationError, ValueError)):
        contract.model_copy(
            update={"canonical_nouns": (WebRuntimeNoun.WEB_REQUEST,)}
        )


def test_web_audit_record_rejects_raw_private_provider_exchange_content() -> None:
    _audit_record()

    for unsafe_summary in [
        "raw prompt content leaked",
        "provider_exchange body leaked",
        "path /Users/example/private.txt leaked",
        "credential: provider-token-placeholder leaked",
    ]:
        with pytest.raises((ValidationError, ValueError)):
            _audit_record(redacted_summary=unsafe_summary)

    with pytest.raises((ValidationError, ValueError)):
        _audit_record(audit_record_ref="/Users/example/raw-log")

    with pytest.raises((ValidationError, ValueError)):
        WebRuntimeAuditRecordContract(
            audit_record_ref="web-audit-record-ref:test",
            web_request_ref="web-request-ref:test",
            policy_decision_ref="policy-decision-ref:test",
            scope_ref="scope-ref:web-runtime:test",
            actor_ref="actor-ref:test",
            redacted_summary="Safe redacted runtime posture summary.",
            raw_provider_payload="forbidden",
        )


def test_post_click_form_download_upload_have_blocked_ledger_states() -> None:
    contract = build_web_runtime_authority_contract()
    ledger_by_effect = {
        entry.model_dump(mode="python")["side_effect"]: entry
        for entry in contract.side_effect_ledger
    }

    assert set(ledger_by_effect) == set(WEB_RUNTIME_REQUIRED_SIDE_EFFECTS)
    for side_effect in ["POST", "click", "form", "download", "upload"]:
        entry = ledger_by_effect[side_effect]
        assert entry.blocked_before_execution is True
        assert entry.execution_allowed is False
        assert entry.action_plan_only is True
        assert entry.model_dump(mode="python")["ledger_state"].startswith("blocked_")
        assert entry.verification_lane_ref.startswith(
            "verification-lane:web-runtime-authority:"
        )

    with pytest.raises((ValidationError, ValueError)):
        WebSideEffectLedgerContract(
            side_effect="POST",
            ledger_state_ref="ledger-state-ref:web-runtime:post:blocked",
            verification_lane_ref="verification-lane:web-runtime-authority:side-effect-ledger-post",
            execution_allowed=True,
        )


def test_approval_linkage_refs_do_not_authorize_execution() -> None:
    linkage = WebApprovalLinkageContract(
        approval_ref="approval-ref:web-runtime:test",
        approval_scope_ref="approval-scope-ref:web-runtime:test",
        linked_web_request_ref="web-request-ref:test",
        linked_web_evidence_ref="web-evidence-ref:test",
        linked_web_audit_record_ref="web-audit-record-ref:test",
        policy_decision_ref="policy-decision-ref:test",
    )

    assert linkage.exact_scope_validation_required is True
    assert linkage.approval_ref_authority is False
    assert linkage.execution_authorized is False
    assert linkage.scoped_execution_allowed is False

    for update in [
        {"approval_ref_authority": True},
        {"execution_authorized": True},
        {"exact_scope_validation_required": False},
    ]:
        with pytest.raises((ValidationError, ValueError)):
            linkage.model_copy(update=update)


def test_operator_labels_include_blocked_degraded_partial() -> None:
    contract = build_web_runtime_authority_contract()

    assert {state.model_dump(mode="python")["label"] for state in contract.operator_states} == (
        set(WEB_RUNTIME_REQUIRED_OPERATOR_LABELS)
    )
    assert all(state.runtime_authority_granted is False for state in contract.operator_states)


def test_promotion_steps_have_named_verification_lanes() -> None:
    contract = build_web_runtime_authority_contract()

    assert {step.model_dump(mode="python")["step"] for step in contract.promotion_steps} == (
        set(WEB_RUNTIME_PROMOTION_STEPS)
    )
    for step in contract.promotion_steps:
        assert step.verification_lane_ref.startswith(
            "verification-lane:web-runtime-authority:"
        )
        assert step.required_nouns
        assert step.promotion_allowed is False
        assert step.runtime_authority_granted is False

    with pytest.raises((ValidationError, ValueError)):
        contract.promotion_steps[0].model_copy(update={"verification_lane_ref": "missing-lane"})


def test_provider_diagnostics_do_not_imply_provider_authority() -> None:
    diagnostic = WebProviderDiagnosticContract(
        provider_diagnostic_ref="provider-diagnostic-ref:web-runtime:test",
        provider_manifest_ref="provider-manifest-ref:web-runtime:test",
    )

    assert diagnostic.diagnostic_only is True
    assert diagnostic.provider_authority_granted is False
    assert diagnostic.provider_sdk_call_allowed is False
    assert diagnostic.provider_network_call_allowed is False
    assert diagnostic.callable_runtime_authority is False
    assert diagnostic.execution_authorized is False

    for update in [
        {"provider_authority_granted": True},
        {"provider_sdk_call_allowed": True},
        {"provider_network_call_allowed": True},
        {"callable_runtime_authority": True},
    ]:
        with pytest.raises((ValidationError, ValueError)):
            diagnostic.model_copy(update=update)


def test_web_runtime_promotion_ladder_is_ordered_and_blocked() -> None:
    contract = build_web_runtime_authority_contract()
    ladder = contract.promotion_ladder

    assert tuple(step.model_dump(mode="python")["step"] for step in ladder) == (
        WEB_RUNTIME_AUTHORITY_PROMOTION_LADDER
    )
    assert tuple(step.sequence for step in ladder) == tuple(range(1, 10))
    assert tuple(step.model_dump(mode="python")["status"] for step in ladder) == (
        WEB_RUNTIME_AUTHORITY_PROMOTION_LADDER_STATUSES
    )
    assert all(step.web_access_gateway_required is True for step in ladder)
    assert all(step.exact_approval_required_before_execution is True for step in ladder)
    assert all(
        step.cost_governor_binding_required_before_paid_provider_use is True
        for step in ladder
    )
    assert all(step.runtime_authority_granted is False for step in ladder)
    assert all(step.live_web_fetching_allowed is False for step in ladder)
    assert all(step.browser_automation_allowed is False for step in ladder)
    assert all(step.provider_sdk_call_allowed is False for step in ladder)
    assert all(step.generic_public_web_mutation_allowed is False for step in ladder)
    assert all(step.callable_runtime_authority is False for step in ladder)

    callable_runtime_step = ladder[-1]
    assert "frontier paid usage without cost receipts" in (
        callable_runtime_step.keep_blocked
    )

    with pytest.raises((ValidationError, ValueError)):
        WebRuntimePromotionLadderStepContract(
            sequence=1,
            step="roadmap_currentness_stitching",
            first_safe_mode="Active roadmap and board promotion only.",
            keep_blocked=(),
            verification_lane_ref=(
                "verification-lane:web-runtime-authority:"
                "roadmap-currentness-stitching"
            ),
        )

    with pytest.raises((ValidationError, ValueError)):
        callable_runtime_step.model_copy(update={"callable_runtime_authority": True})

    with pytest.raises((ValidationError, ValueError)):
        build_web_runtime_authority_contract().model_copy(
            update={
                "promotion_ladder": (
                    *ladder[:-1],
                    callable_runtime_step.model_copy(update={"status": "shaping"}),
                )
            }
        )


def test_cost_governor_posture_blocks_paid_frontier_provider_use() -> None:
    posture = WebRuntimeCostGovernorPostureContract()

    assert posture.cost_governor_required_before_paid_provider_use is True
    assert posture.unknown_paid_cost_requires_explicit_approval is True
    assert posture.estimated_cost_ref_required is True
    assert posture.budget_decision_ref_required is True
    assert posture.cost_receipt_refs_required_for_frontier_usage_claims is True
    assert posture.provider_model_refs_required_before_frontier_usage is True
    assert posture.budget_exceeded_blocks_execution is True
    assert posture.frontier_ai_scope_separated_from_web_provider_scope is True
    assert posture.web_provider_diagnostics_are_not_frontier_ai_authority is True
    assert posture.provider_sdk_calls_allowed is False
    assert posture.runtime_model_calls_allowed is False
    assert posture.callable_runtime_authority is False

    for update in [
        {"unknown_paid_cost_requires_explicit_approval": False},
        {"cost_receipt_refs_required_for_frontier_usage_claims": False},
        {"provider_model_refs_required_before_frontier_usage": False},
        {"provider_sdk_calls_allowed": True},
        {"runtime_model_calls_allowed": True},
        {"callable_runtime_authority": True},
    ]:
        with pytest.raises((ValidationError, ValueError)):
            posture.model_copy(update=update)


def test_catalog_manifest_visibility_is_metadata_not_callable_runtime() -> None:
    visibility = WebCatalogManifestVisibilityContract(
        catalog_ref="catalog-ref:web-runtime:test",
        manifest_ref="manifest-ref:web-runtime:test",
    )

    assert visibility.catalog_visible is True
    assert visibility.manifest_visible is True
    assert visibility.catalog_manifest_visibility_only is True
    assert visibility.callable_runtime is False
    assert visibility.runtime_import_allowed is False
    assert visibility.provider_authority_granted is False
    assert visibility.execution_authority_granted is False

    for update in [
        {"callable_runtime": True},
        {"runtime_import_allowed": True},
        {"provider_authority_granted": True},
        {"execution_authority_granted": True},
    ]:
        with pytest.raises((ValidationError, ValueError)):
            visibility.model_copy(update=update)
