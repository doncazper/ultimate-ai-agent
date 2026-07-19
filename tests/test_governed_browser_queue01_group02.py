from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from scripts.verify_governed_browser_queue01_group02 import verify
from ultimate_ai_agent.core.governed_browser import (
    ExternalActionAuthorityBinding,
    ExternalActionExecutionRequest,
    ExternalActionInboxStatus,
    ExternalActionReceipt,
    ExternalActionReconciliationStatus,
    ExternalActionRetryPosture,
    ExternalActionSideEffectPosture,
    ExternalActionState,
    ExternalActionTargetKind,
    build_external_action_inbox_envelope,
    stable_governed_browser_ref,
)


NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def _ref(prefix: str, suffix: str) -> str:
    return f"{prefix}-ref:governed-browser:{suffix}"


def _origin_ref(origin: str) -> str:
    return stable_governed_browser_ref(
        "origin-ref:governed-browser", {"origin": origin}
    )


def _binding(
    *,
    suffix: str = "one",
    target_kind: ExternalActionTargetKind = ExternalActionTargetKind.local_validation,
    human_present: bool = True,
    deadline: datetime | None = None,
) -> ExternalActionAuthorityBinding:
    origin = (
        "http://127.0.0.1:8765"
        if target_kind == ExternalActionTargetKind.local_validation
        else "https://external-target.invalid"
    )
    return ExternalActionAuthorityBinding(
        target_kind=target_kind,
        origin=origin,
        origin_ref=_origin_ref(origin),
        recipient_ref=_ref("recipient", suffix),
        field_schema_ref=_ref("field-schema", suffix),
        transaction_ref=_ref("transaction", suffix),
        artifact_refs=[_ref("artifact", suffix)],
        resource_refs=[_ref("resource", suffix)],
        action_count=1,
        page_snapshot_ref=_ref("page-snapshot", suffix),
        start_deadline=deadline or NOW + timedelta(minutes=10),
        human_presence_ref=_ref("human-presence", suffix),
        human_present=human_present,
    )


def _request(
    binding: ExternalActionAuthorityBinding,
    *,
    approval_ref: str = "approval-ref:governed-browser:exact",
) -> ExternalActionExecutionRequest:
    suffix = binding.transaction_ref.rsplit(":", 1)[-1]
    run_ref = _ref("run", suffix)
    task_ref = _ref("task", suffix)
    lease_ref = _ref("authority-lease", suffix)
    intent_ref = stable_governed_browser_ref(
        "intent-ref:governed-external-action",
        {
            "binding_ref": binding.binding_ref,
            "run_ref": run_ref,
            "task_ref": task_ref,
            "lease_ref": lease_ref,
        },
    )
    return ExternalActionExecutionRequest(
        binding=binding,
        run_ref=run_ref,
        task_ref=task_ref,
        intent_ref=intent_ref,
        idempotency_ref=stable_governed_browser_ref(
            "idempotency-ref:governed-external-action",
            {"intent_ref": intent_ref},
        ),
        lease_ref=lease_ref,
        approval_ref=approval_ref,
    )


def _receipt(
    request: ExternalActionExecutionRequest,
    state: ExternalActionState,
    *,
    reason_refs_override: list[str] | None = None,
) -> ExternalActionReceipt:
    evidence_refs = (
        [_ref("evidence", "verified")]
        if state == ExternalActionState.succeeded
        else [_ref("evidence", "dispatch-observed")]
    )
    reason_refs = (
        reason_refs_override
        if reason_refs_override is not None
        else (
            [_ref("reason", "outcome-uncertain")]
            if state == ExternalActionState.outcome_ambiguous
            else []
        )
    )
    payload = {
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "state": state.value,
        "approval_validation_ref": _ref("approval-validation", "recorded"),
        "authority_decision_ref": _ref("authority-decision", "exact"),
        "budget_reservation_ref": _ref("budget-reservation", "exact"),
        "budget_settlement_ref": (
            _ref("budget-settlement", "exact")
            if state == ExternalActionState.succeeded
            else None
        ),
        "evidence_refs": evidence_refs,
        "reason_refs": reason_refs,
    }
    return ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            payload,
        ),
        **payload,
    )


def _envelope(
    request: ExternalActionExecutionRequest,
    *,
    receipt: ExternalActionReceipt | None = None,
    safe_disable_active: bool = False,
    kill_switch_engaged: bool = False,
    now: datetime = NOW,
):  # type: ignore[no-untyped-def]
    return build_external_action_inbox_envelope(
        request,
        receipt=receipt,
        safe_disable_active=safe_disable_active,
        kill_switch_engaged=kill_switch_engaged,
        now=now,
    )


def test_action_inbox_envelope_is_readable_content_free_and_inactive() -> None:
    request = _request(_binding())

    envelope = _envelope(request)

    assert envelope.status == ExternalActionInboxStatus.review_required.value
    assert (
        envelope.side_effect_posture
        == ExternalActionSideEffectPosture.validation_only.value
    )
    assert envelope.data_classification == "project_private"
    assert envelope.expiry_posture == "active"
    assert (
        envelope.retry_posture
        == ExternalActionRetryPosture.fresh_approval_and_revalidation_required.value
    )
    assert envelope.approval_ref_is_identifier_only is True
    assert envelope.approval_validation_ref is None
    assert envelope.approval_revalidation_required_before_dispatch is True
    assert envelope.uaa_execution_enabled is False
    assert envelope.real_external_targets_enabled is False
    assert envelope.automatic_retry_allowed is False
    assert len(envelope.expected_receipt_refs) == 2
    assert request.lease_ref in envelope.exact_scope_refs
    payload = json.dumps(envelope.model_dump(mode="json"), sort_keys=True)
    assert "127.0.0.1" not in payload
    assert request.approval_ref not in payload
    assert "raw prompt" not in payload.lower()


def test_manual_controls_are_visible_but_cannot_open_or_execute_a_browser() -> None:
    envelope = _envelope(_request(_binding()))

    assert envelope.open_in_browser.label == "Open in browser"
    assert envelope.open_in_browser.status == "manual_handoff_only"
    assert envelope.open_in_browser.visible is True
    assert envelope.open_in_browser.available is True
    assert envelope.open_in_browser.uaa_execution_enabled is False
    assert envelope.open_in_browser.browser_automation_enabled is False
    assert envelope.open_in_browser.external_mutation_enabled is False
    assert envelope.open_in_browser.performed is False
    assert envelope.human_takeover.label == "Human takeover"
    assert envelope.human_takeover.uaa_execution_enabled is False
    assert envelope.human_takeover.performed is False


def test_approval_fingerprint_and_scope_bind_exact_request_fields() -> None:
    original = _request(_binding(suffix="original"))
    drifted_scope = _request(_binding(suffix="drifted"))
    drifted_approval = _request(
        original.binding,
        approval_ref="approval-ref:governed-browser:different",
    )

    original_envelope = _envelope(original)
    same_envelope = _envelope(original)
    scope_envelope = _envelope(drifted_scope)
    approval_envelope = _envelope(drifted_approval)

    assert original_envelope == same_envelope
    assert original_envelope.exact_scope_refs != scope_envelope.exact_scope_refs
    assert (
        original_envelope.approval_fingerprint_ref
        != scope_envelope.approval_fingerprint_ref
    )
    assert (
        original_envelope.approval_fingerprint_ref
        != approval_envelope.approval_fingerprint_ref
    )


def test_approval_identifier_alone_never_enables_execution_and_missing_scope_denies() -> (
    None
):
    request = _request(
        _binding(), approval_ref="approval-ref:governed-browser:unregistered"
    )

    envelope = _envelope(request)

    assert envelope.approval_validation_ref is None
    assert envelope.uaa_execution_enabled is False
    assert envelope.approval_revalidation_required_before_dispatch is True
    payload = request.model_dump(mode="json")
    payload.pop("lease_ref")
    with pytest.raises(ValidationError):
        ExternalActionExecutionRequest.model_validate(payload)


def test_envelope_rejects_execution_flags_and_unregistered_authority_fields() -> None:
    envelope = _envelope(_request(_binding(suffix="denied-flags")))
    payload = envelope.model_dump(mode="json")

    with pytest.raises(ValidationError):
        type(envelope).model_validate({**payload, "uaa_execution_enabled": True})
    with pytest.raises(ValidationError):
        type(envelope).model_validate({**payload, "approval_validated": True})
    open_control = dict(payload["open_in_browser"])
    open_control["performed"] = True
    with pytest.raises(ValidationError):
        type(envelope).model_validate({**payload, "open_in_browser": open_control})


@pytest.mark.parametrize(
    ("action_request", "safe_disable", "kill_switch", "now", "expected_reason"),
    [
        (
            _request(_binding(suffix="safe-disable")),
            True,
            False,
            NOW,
            "reason-ref:governed-external-action:safe-disable-active",
        ),
        (
            _request(_binding(suffix="kill-switch")),
            False,
            True,
            NOW,
            "reason-ref:governed-external-action:kill-switch-engaged",
        ),
        (
            _request(_binding(suffix="human", human_present=False)),
            False,
            False,
            NOW,
            "reason-ref:governed-external-action:human-presence-required",
        ),
        (
            _request(
                _binding(
                    suffix="expired",
                    deadline=NOW - timedelta(seconds=1),
                )
            ),
            False,
            False,
            NOW,
            "reason-ref:governed-external-action:deadline-expired",
        ),
    ],
)
def test_current_safety_posture_is_visible_and_fail_closed(
    action_request: ExternalActionExecutionRequest,
    safe_disable: bool,
    kill_switch: bool,
    now: datetime,
    expected_reason: str,
) -> None:
    envelope = _envelope(
        action_request,
        safe_disable_active=safe_disable,
        kill_switch_engaged=kill_switch,
        now=now,
    )

    assert envelope.status in {
        ExternalActionInboxStatus.blocked_inactive.value,
        ExternalActionInboxStatus.expired.value,
    }
    assert expected_reason in envelope.reason_refs
    assert envelope.uaa_execution_enabled is False
    if envelope.expiry_posture == "expired":
        assert envelope.open_in_browser.status == "request_expired"
        assert envelope.open_in_browser.available is False


def test_real_external_target_is_explicitly_inactive_in_action_inbox() -> None:
    request = _request(
        _binding(
            suffix="external",
            target_kind=ExternalActionTargetKind.external,
        )
    )

    envelope = _envelope(request)

    assert envelope.status == ExternalActionInboxStatus.blocked_inactive.value
    assert (
        envelope.side_effect_posture
        == ExternalActionSideEffectPosture.external_mutation_inactive.value
    )
    assert (
        "reason-ref:governed-external-action:real-targets-inactive"
        in envelope.reason_refs
    )
    assert envelope.real_external_targets_enabled is False


def test_success_receipt_is_exactly_bound_and_reconciliation_is_verified() -> None:
    request = _request(_binding(suffix="success"))
    receipt = _receipt(request, ExternalActionState.succeeded)

    envelope = _envelope(request, receipt=receipt)

    assert envelope.status == ExternalActionInboxStatus.receipt_recorded.value
    assert (
        envelope.reconciliation_status
        == ExternalActionReconciliationStatus.verified.value
    )
    assert envelope.reconciliation_required is False
    assert envelope.retry_posture == ExternalActionRetryPosture.terminal_no_retry.value
    assert receipt.receipt_ref in envelope.receipt_refs
    assert receipt.budget_settlement_ref in envelope.receipt_refs
    assert envelope.evidence_refs == list(receipt.evidence_refs)
    assert envelope.approval_validation_ref == receipt.approval_validation_ref


def test_succeeded_receipt_with_ambiguous_settlement_requires_reconciliation() -> (
    None
):
    request = _request(_binding(suffix="success-accounting-ambiguous"))
    receipt = _receipt(
        request,
        ExternalActionState.succeeded,
        reason_refs_override=[
            "reason-ref:governed-external-action:budget-settlement-ambiguous"
        ],
    )

    envelope = _envelope(request, receipt=receipt)

    assert envelope.status == ExternalActionInboxStatus.reconciliation_required.value
    assert (
        envelope.reconciliation_status
        == ExternalActionReconciliationStatus.required.value
    )
    assert envelope.reconciliation_required is True
    assert envelope.retry_posture == ExternalActionRetryPosture.terminal_no_retry.value
    assert envelope.automatic_retry_allowed is False


def test_ambiguous_receipt_requires_manual_reconciliation_and_never_retries() -> None:
    request = _request(_binding(suffix="ambiguous"))
    receipt = _receipt(request, ExternalActionState.outcome_ambiguous)

    envelope = _envelope(request, receipt=receipt)

    assert envelope.status == ExternalActionInboxStatus.reconciliation_required.value
    assert (
        envelope.reconciliation_status
        == ExternalActionReconciliationStatus.required.value
    )
    assert envelope.reconciliation_required is True
    assert (
        envelope.retry_posture
        == ExternalActionRetryPosture.manual_reconciliation_required_no_retry.value
    )
    assert envelope.automatic_retry_allowed is False


def test_blocked_receipt_with_unconfirmed_budget_release_requires_reconciliation() -> (
    None
):
    request = _request(_binding(suffix="blocked-release-unconfirmed"))
    receipt = _receipt(
        request,
        ExternalActionState.blocked,
        reason_refs_override=[
            "reason-ref:governed-external-action:budget-release-unconfirmed"
        ],
    )

    envelope = _envelope(request, receipt=receipt)

    assert envelope.status == ExternalActionInboxStatus.reconciliation_required.value
    assert (
        envelope.reconciliation_status
        == ExternalActionReconciliationStatus.required.value
    )
    assert envelope.reconciliation_required is True
    assert envelope.retry_posture == ExternalActionRetryPosture.terminal_no_retry.value
    assert envelope.automatic_retry_allowed is False


def test_receipt_from_a_different_transaction_is_rejected() -> None:
    request = _request(_binding(suffix="expected"))
    other = _request(_binding(suffix="other"))
    mismatched = _receipt(other, ExternalActionState.succeeded)

    with pytest.raises(ValueError, match="RECEIPT_BINDING_MISMATCH"):
        _envelope(request, receipt=mismatched)


def test_verifier_passes_current_tree() -> None:
    assert verify() == []
