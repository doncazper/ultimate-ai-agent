from __future__ import annotations

import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from pydantic import ValidationError

from scripts.verify_governed_browser_queue02_hardening import verify
from tests.test_governed_browser_queue01_group01 import (
    _authorized_kernel,
    _binding,
    _readiness,
    _ref,
    _request,
    _success,
)
from ultimate_ai_agent.core.governed_browser import (
    ExternalActionAdversarialSignals,
    ExternalActionReadiness,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTransactionConflict,
    ExternalActionTransactionStore,
    GovernedBrowserActivationPosture,
    GovernedBrowserLaneActivationEvidence,
    GovernedBrowserQueue02Lane,
    build_external_action_approval_request,
    build_external_action_readiness,
    decide_governed_browser_lane_activation,
    governed_browser_queue02_inactive_activation_matrix,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.time import utc_now


_BOOLEAN_ADVERSARIAL_SIGNALS = (
    "cross_origin_redirect_detected",
    "dom_swap_detected",
    "hidden_field_detected",
    "changed_form_action_detected",
    "misleading_control_detected",
    "unexpected_popup_detected",
    "unexpected_download_detected",
    "page_mutation_after_approval_detected",
    "duplicate_submission_detected",
    "session_fixation_detected",
    "origin_confusion_detected",
    "upload_artifact_substitution_detected",
    "download_filename_attack_detected",
    "download_media_type_attack_detected",
    "download_signature_attack_detected",
    "recipient_substitution_detected",
    "content_substitution_detected",
    "amount_substitution_detected",
    "total_substitution_detected",
    "secret_canary_detected",
    "credential_canary_detected",
    "prompt_injection_detected",
    "raw_content_leak_detected",
    "raw_path_leak_detected",
    "cross_lane_interference_detected",
    "retry_requested",
    "resource_limit_exceeded",
)


def _signals(**updates: bool | int) -> ExternalActionAdversarialSignals:
    payload = ExternalActionAdversarialSignals.clear_local_validation().model_dump(
        mode="python"
    )
    payload.update(updates)
    return ExternalActionAdversarialSignals.model_validate(payload)


@pytest.mark.parametrize(
    ("signal", "case_number"),
    tuple((signal, index) for index, signal in enumerate(_BOOLEAN_ADVERSARIAL_SIGNALS)),
)
def test_every_hostile_signal_blocks_before_dispatch(
    tmp_path,
    signal: str,
    case_number: int,  # type: ignore[no-untyped-def]
) -> None:
    request = _request(_binding(suffix=f"hostile-{case_number}"))
    calls = 0

    def readiness(item):  # type: ignore[no-untyped-def]
        now = utc_now()
        return build_external_action_readiness(
            item,
            status="ready",
            observed_at=now - timedelta(seconds=1),
            expires_at=min(
                now + timedelta(minutes=1),
                item.binding.start_deadline - timedelta(seconds=1),
            ),
            broker_integrity_verified=True,
            external_mutation_enabled=True,
            safe_disable_active=False,
            kill_switch_engaged=False,
            adversarial_signals=_signals(**{signal: True}),
        )

    def dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(item)

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    receipt = kernel.execute(request, dispatch=dispatch)

    assert receipt.state == ExternalActionState.blocked.value
    assert calls == 0
    assert any("adversarial:" in ref for ref in receipt.reason_refs)
    assert receipt.automatic_retry_allowed is False


def test_simultaneous_hostile_signals_return_a_bounded_blocked_receipt(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="all-hostile-signals"))

    def readiness(item):  # type: ignore[no-untyped-def]
        now = utc_now()
        return build_external_action_readiness(
            item,
            status="ready",
            observed_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(seconds=10),
            broker_integrity_verified=True,
            external_mutation_enabled=True,
            safe_disable_active=False,
            kill_switch_engaged=False,
            adversarial_signals=_signals(
                **{signal: True for signal in _BOOLEAN_ADVERSARIAL_SIGNALS}
            ),
        )

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.state == ExternalActionState.blocked.value
    assert len(receipt.reason_refs) <= 16
    assert any("reason-overflow" in ref for ref in receipt.reason_refs)


def test_cleanup_failure_and_resource_bounds_fail_closed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="cleanup-unverified"))

    def readiness(item):  # type: ignore[no-untyped-def]
        now = utc_now()
        return build_external_action_readiness(
            item,
            status="ready",
            observed_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(seconds=10),
            broker_integrity_verified=True,
            external_mutation_enabled=True,
            safe_disable_active=False,
            kill_switch_engaged=False,
            adversarial_signals=_signals(
                cleanup_verified=False,
                active_resource_count=4,
            ),
        )

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.state == ExternalActionState.blocked.value
    assert any("cleanup-unverified" in ref for ref in receipt.reason_refs)
    with pytest.raises(ValidationError):
        _signals(active_resource_count=5)


@pytest.mark.parametrize(
    ("field", "reason_fragment"),
    (
        ("observed_origin_ref", "observed-origin-mismatch"),
        ("observed_recipient_ref", "observed-recipient-mismatch"),
        ("observed_field_schema_ref", "observed-field-schema-mismatch"),
        ("observed_transaction_ref", "observed-transaction-mismatch"),
        ("observed_artifact_refs", "observed-artifact-scope-mismatch"),
        ("observed_resource_refs", "observed-resource-scope-mismatch"),
        ("page_snapshot_ref", "snapshot-changed"),
    ),
)
def test_every_observed_scope_dimension_is_revalidated(
    tmp_path,
    field: str,
    reason_fragment: str,  # type: ignore[no-untyped-def]
) -> None:
    request = _request(_binding(suffix=f"scope-{field}"))
    override: str | tuple[str, ...]
    if field in {"observed_artifact_refs", "observed_resource_refs"}:
        override = (_ref("drift", field),)
    else:
        override = _ref("drift", field)

    def readiness(item):  # type: ignore[no-untyped-def]
        now = utc_now()
        return build_external_action_readiness(
            item,
            status="ready",
            observed_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(seconds=10),
            broker_integrity_verified=True,
            external_mutation_enabled=True,
            safe_disable_active=False,
            kill_switch_engaged=False,
            **{field: override},
        )

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.state == ExternalActionState.blocked.value
    assert any(reason_fragment in ref for ref in receipt.reason_refs)


def test_readiness_and_receipt_refs_are_intrinsically_bound() -> None:
    request = _request(_binding(suffix="intrinsic-refs"))
    readiness = _readiness(request)
    with pytest.raises(ValidationError, match="READINESS_REF_MISMATCH"):
        ExternalActionReadiness.model_validate(
            {
                **readiness.model_dump(mode="json"),
                "readiness_ref": _ref("readiness", "forged"),
            }
        )

    payload = {
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "state": ExternalActionState.failed.value,
        "approval_validation_ref": None,
        "authority_decision_ref": None,
        "budget_reservation_ref": None,
        "budget_settlement_ref": None,
        "evidence_refs": [],
        "reason_refs": ["reason-ref:governed-external-action:test-failure"],
    }
    receipt = ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action", payload
        ),
        **payload,
    )
    with pytest.raises(ValidationError, match="RECEIPT_REF_MISMATCH"):
        ExternalActionReceipt.model_validate(
            {
                **receipt.model_dump(mode="json"),
                "reason_refs": ["reason-ref:governed-external-action:tampered-failure"],
            }
        )
    with pytest.raises(ValidationError, match="RECEIPT_REF_MISMATCH"):
        ExternalActionReceipt.model_validate(
            {
                **receipt.model_dump(mode="json"),
                "budget_release_ref": _ref("budget-release", "forged"),
            }
        )


def test_mutable_caller_alias_drift_is_rejected_before_durable_prepare(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="caller-alias"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    request.binding.resource_refs.append(_ref("resource", "injected"))

    with pytest.raises(ValidationError, match="INTENT_REF_MISMATCH"):
        kernel.execute(request, dispatch=_success)
    with sqlite3.connect(tmp_path / "transactions.sqlite3") as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM governed_external_actions"
        ).fetchone()[0]
    assert count == 0


@pytest.mark.parametrize("race", ("safe-disable", "kill-switch"))
def test_stop_posture_race_after_start_becomes_ambiguous(
    tmp_path,
    race: str,  # type: ignore[no-untyped-def]
) -> None:
    request = _request(_binding(suffix=f"race-{race}"))
    reads = 0

    def readiness(item):  # type: ignore[no-untyped-def]
        nonlocal reads
        reads += 1
        return _readiness(
            item,
            safe_disable=race == "safe-disable" and reads >= 2,
            kill_switch=race == "kill-switch" and reads >= 2,
        )

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert any("post-start-revalidation-denied" in ref for ref in receipt.reason_refs)
    assert any(race in ref for ref in receipt.reason_refs)
    assert receipt.budget_release_ref is not None
    assert receipt.budget_settlement_ref is None


@pytest.mark.parametrize("race", ("approval", "lease"))
def test_authority_revocation_race_after_reservation_blocks_start(
    tmp_path,
    race: str,  # type: ignore[no-untyped-def]
) -> None:
    request = _request(_binding(suffix=f"revocation-{race}"))
    authority_holder = []
    changed = False

    def readiness(item):  # type: ignore[no-untyped-def]
        nonlocal changed
        if not changed:
            changed = True
            authority = authority_holder[0]
            if race == "approval":
                authority.revoke(
                    request.approval_ref,
                    "Operator withdrew exact approval before dispatch.",
                )
            else:
                authority.revoke_authority_lease(
                    request.lease_ref,
                    "reason-ref:governed-browser-queue02:lease-race",
                )
        return _readiness(item)

    kernel, authority = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    approval_proof_refs: list[tuple[bool, str]] = []
    authority_proof_refs: list[tuple[str, str]] = []
    original_validate = authority.validate
    original_evaluate = authority.evaluate_authority_scope

    def recording_validate(validation):  # type: ignore[no-untyped-def]
        decision = original_validate(validation)
        approval_proof_refs.append(
            (
                decision.allowed,
                stable_governed_browser_ref(
                    "approval-validation-ref:governed-external-action",
                    decision.model_dump(mode="json"),
                ),
            )
        )
        return decision

    def recording_evaluate(action):  # type: ignore[no-untyped-def]
        decision = original_evaluate(action)
        authority_proof_refs.append((decision.outcome, decision.decision_ref))
        return decision

    authority.validate = recording_validate  # type: ignore[method-assign]
    authority.evaluate_authority_scope = recording_evaluate  # type: ignore[method-assign]
    authority_holder.append(authority)
    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.state == ExternalActionState.blocked.value
    assert any(race in ref for ref in receipt.reason_refs)
    assert receipt.budget_release_ref is not None
    if race == "approval":
        assert receipt.approval_validation_ref in {
            proof_ref
            for allowed, proof_ref in approval_proof_refs
            if not allowed
        }
    else:
        assert receipt.authority_decision_ref in {
            proof_ref
            for outcome, proof_ref in authority_proof_refs
            if outcome not in {"allow", "ask"}
        }


def test_authority_revocation_waits_for_final_validation_and_dispatch(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="atomic-dispatch-authority"))
    kernel, authority = _authorized_kernel(tmp_path, request)
    entered = threading.Event()
    proceed = threading.Event()

    def dispatch(item):  # type: ignore[no-untyped-def]
        entered.set()
        assert proceed.wait(timeout=2)
        return _success(item)

    with ThreadPoolExecutor(max_workers=2) as pool:
        owner_future = pool.submit(kernel.execute, request, dispatch=dispatch)
        assert entered.wait(timeout=2)
        revoke_future = pool.submit(
            authority.revoke,
            request.approval_ref,
            "Operator revoked after the final dispatch validation.",
        )
        time.sleep(0.03)
        assert not revoke_future.done()
        proceed.set()
        receipt = owner_future.result(timeout=2)
        revoke_future.result(timeout=2)

    assert receipt.state == ExternalActionState.succeeded.value


def test_dispatch_timeout_is_ambiguous_non_retryable_and_capacity_bounded(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="timeout"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    kernel._dispatch_timeout_seconds = 0.01
    dispatch_stopped = False

    def slow_dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal dispatch_stopped
        time.sleep(0.08)
        dispatch_stopped = True
        return _success(item)

    receipt = kernel.execute(request, dispatch=slow_dispatch)

    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert dispatch_stopped is True
    assert "reason-ref:governed-external-action:dispatch-timeout" in (
        receipt.reason_refs
    )
    assert receipt.automatic_retry_allowed is False
    replay = kernel.execute(request, dispatch=_success)
    assert replay.replayed is True
    assert replay.state == ExternalActionState.outcome_ambiguous.value


def test_ambiguous_dispatch_evidence_is_bound_to_each_exact_request(tmp_path) -> None:  # type: ignore[no-untyped-def]
    first_request = _request(_binding(suffix="timeout-evidence-first"))
    second_request = _request(_binding(suffix="timeout-evidence-second"))
    first_kernel, _ = _authorized_kernel(tmp_path / "first", first_request)
    second_kernel, _ = _authorized_kernel(tmp_path / "second", second_request)
    first_kernel._dispatch_timeout_seconds = 0.001
    second_kernel._dispatch_timeout_seconds = 0.001

    def slow_success(item):  # type: ignore[no-untyped-def]
        time.sleep(0.01)
        return _success(item)

    first = first_kernel.execute(first_request, dispatch=slow_success)
    second = second_kernel.execute(second_request, dispatch=slow_success)

    assert first.state == second.state == ExternalActionState.outcome_ambiguous.value
    assert first.evidence_refs != second.evidence_refs


def test_concurrent_execute_never_clobbers_the_dispatch_owner(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="concurrent-owner"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    entered = threading.Event()
    proceed = threading.Event()
    calls = 0

    def dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        entered.set()
        assert proceed.wait(timeout=2)
        return _success(item)

    with ThreadPoolExecutor(max_workers=2) as pool:
        owner_future = pool.submit(kernel.execute, request, dispatch=dispatch)
        assert entered.wait(timeout=2)
        contender = kernel.execute(request, dispatch=dispatch)
        proceed.set()
        owner = owner_future.result(timeout=2)

    assert calls == 1
    assert contender.state == ExternalActionState.outcome_ambiguous.value
    assert "reason-ref:governed-external-action:start-already-claimed" in (
        contender.reason_refs
    )
    assert owner.state == ExternalActionState.succeeded.value
    replay = kernel.execute(request, dispatch=dispatch)
    assert replay.replayed is True
    assert replay.state == ExternalActionState.succeeded.value
    assert calls == 1


def test_restart_recovery_cannot_terminalize_a_fresh_live_start(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="fresh-start-recovery"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    store = ExternalActionTransactionStore(tmp_path / "transactions.sqlite3")
    store.prepare(request)
    assert store.claim_start(request) is True

    assert kernel.recover_if_prior_start(request) is None
    assert store.state_if_exact(request) == ExternalActionState.started
    assert store.replay_if_terminal(request) is None


def test_restart_recovery_uses_the_maximum_owner_dispatch_window(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="max-owner-window"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    store = ExternalActionTransactionStore(tmp_path / "transactions.sqlite3")
    store.prepare(request)
    assert store.claim_start(request) is True
    started_at = store.started_at_if_exact(request)
    assert started_at is not None

    kernel._dispatch_timeout_seconds = 0.001
    kernel._clock = lambda: started_at + timedelta(seconds=10)
    assert kernel.recover_if_prior_start(request) is None
    assert store.state_if_exact(request) == ExternalActionState.started

    kernel._clock = lambda: started_at + timedelta(seconds=36)
    recovered = kernel.recover_if_prior_start(request)
    assert recovered is not None
    assert recovered.state == ExternalActionState.outcome_ambiguous.value


def test_restart_recovery_reaps_stale_process_slot_and_settles_budget(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="stale-slot-recovery"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    store = ExternalActionTransactionStore(tmp_path / "transactions.sqlite3")
    approval_validation = build_external_action_approval_request(
        request
    ).to_validation_request(request.approval_ref)
    reservation = kernel._budget_gate.reserve(request, approval_validation)
    assert reservation.allowed is True
    assert reservation.reservation_ref is not None
    store.prepare(request)
    assert store.claim_start(
        request,
        budget_reservation_ref=reservation.reservation_ref,
    ) is True
    process_lock_fd = store.claim_dispatch_slot(request)
    assert process_lock_fd is not None
    store._release_dispatch_process_lock(process_lock_fd)
    started_at = store.started_at_if_exact(request)
    assert started_at is not None
    kernel._clock = lambda: started_at + timedelta(seconds=36)

    recovered = kernel.recover_if_prior_start(request)

    assert recovered is not None
    assert recovered.state == ExternalActionState.outcome_ambiguous.value
    assert recovered.budget_reservation_ref == reservation.reservation_ref
    assert recovered.budget_settlement_ref is not None
    with sqlite3.connect(tmp_path / "transactions.sqlite3") as connection:
        slot_count = connection.execute(
            "SELECT COUNT(*) FROM governed_external_action_dispatch_slot"
        ).fetchone()[0]
    assert slot_count == 0


def test_stale_dispatch_slot_is_reaped_before_capacity_denial(tmp_path) -> None:  # type: ignore[no-untyped-def]
    stale_request = _request(_binding(suffix="stale-slot-owner"))
    next_request = _request(_binding(suffix="stale-slot-next"))
    store = ExternalActionTransactionStore(tmp_path / "transactions.sqlite3")
    store.prepare(stale_request)
    assert store.claim_start(stale_request) is True
    process_lock_fd = store.claim_dispatch_slot(stale_request)
    assert process_lock_fd is not None
    store._release_dispatch_process_lock(process_lock_fd)
    next_kernel, _ = _authorized_kernel(tmp_path / "next", next_request)
    next_kernel._store = store

    receipt = next_kernel.execute(next_request, dispatch=_success)

    assert receipt.state == ExternalActionState.succeeded.value
    assert not any("dispatch-capacity-bounded" in ref for ref in receipt.reason_refs)


def test_dispatch_capacity_is_shared_durably_across_kernel_instances(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    first_request = _request(_binding(suffix="shared-slot-first"))
    second_request = _request(_binding(suffix="shared-slot-second"))
    first_kernel, _ = _authorized_kernel(tmp_path / "first", first_request)
    second_kernel, _ = _authorized_kernel(tmp_path / "second", second_request)
    shared_path = tmp_path / "shared-transactions.sqlite3"
    first_kernel._store = ExternalActionTransactionStore(shared_path)
    second_kernel._store = ExternalActionTransactionStore(shared_path)
    entered = threading.Event()
    proceed = threading.Event()
    calls = 0

    def dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        entered.set()
        assert proceed.wait(timeout=2)
        return _success(item)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(
            first_kernel.execute,
            first_request,
            dispatch=dispatch,
        )
        assert entered.wait(timeout=2)
        second = second_kernel.execute(second_request, dispatch=dispatch)
        proceed.set()
        first = first_future.result(timeout=2)

    assert calls == 1
    assert first.state == ExternalActionState.succeeded.value
    assert second.state == ExternalActionState.outcome_ambiguous.value
    assert "reason-ref:governed-external-action:dispatch-capacity-bounded" in (
        second.reason_refs
    )


def test_terminal_compare_and_swap_rejects_overwrite(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="terminal-cas"))
    store = ExternalActionTransactionStore(tmp_path / "transactions.sqlite3")
    store.prepare(request)
    assert store.claim_start(request) is True
    first_payload = {
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "state": ExternalActionState.failed.value,
        "approval_validation_ref": None,
        "authority_decision_ref": None,
        "budget_reservation_ref": None,
        "budget_settlement_ref": None,
        "evidence_refs": [],
        "reason_refs": ["reason-ref:governed-external-action:first-terminal"],
    }
    first = ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action", first_payload
        ),
        **first_payload,
    )
    store.finish(first, expected_state=ExternalActionState.started)
    second_payload = {
        **first_payload,
        "reason_refs": ["reason-ref:governed-external-action:second-terminal"],
    }
    second = ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action", second_payload
        ),
        **second_payload,
    )
    with pytest.raises(
        ExternalActionTransactionConflict,
        match="TERMINAL_RECEIPT_CONFLICT",
    ):
        store.finish(second, expected_state=ExternalActionState.started)


def test_reason_bounding_preserves_terminal_accounting_failures(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="accounting-reason-priority"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    reasons = [_ref("reason", f"hostile-{index}") for index in range(20)]
    reasons.extend(
        [
            "reason-ref:governed-external-action:budget-release-unconfirmed",
            "reason-ref:governed-external-action:budget-settlement-ambiguous",
        ]
    )

    receipt = kernel._build_receipt(
        request,
        ExternalActionState.outcome_ambiguous,
        reasons,
    )

    assert len(receipt.reason_refs) <= 16
    assert "reason-ref:governed-external-action:budget-release-unconfirmed" in (
        receipt.reason_refs
    )
    assert "reason-ref:governed-external-action:budget-settlement-ambiguous" in (
        receipt.reason_refs
    )
    assert any("reason-overflow" in ref for ref in receipt.reason_refs)


def _activation_evidence(**updates: bool):  # type: ignore[no-untyped-def]
    payload = {
        "lane": GovernedBrowserQueue02Lane.external_action_kernel,
        "implementation_verified": True,
        "focused_tests_verified": True,
        "adversarial_tests_verified": True,
        "request_scoped_policy_verified": True,
        "exact_approval_verified": True,
        "authority_lease_verified": True,
        "target_readiness_verified": True,
        "adapter_readiness_verified": True,
        "budget_posture_verified": True,
        "kill_switch_verified": True,
        "safe_disable_verified": True,
        "deadline_verified": True,
        "idempotency_verified": True,
        "receipt_verified": True,
        "reconciliation_verified": True,
        "recovery_verified": True,
        "macos_packaged_golden_verified": True,
        "activation_configuration_complete": True,
        "external_facility_available": True,
        "live_external_evidence_verified": True,
        "evidence_refs": ("evidence-ref:governed-browser-queue02:complete",),
    }
    payload.update(updates)
    evidence_ref = stable_governed_browser_ref(
        "activation-evidence-ref:governed-browser-queue02",
        {
            key: value.value if isinstance(value, GovernedBrowserQueue02Lane) else value
            for key, value in payload.items()
        },
    )
    return GovernedBrowserLaneActivationEvidence(
        evidence_ref=evidence_ref,
        **payload,
    )


@pytest.mark.parametrize(
    ("override", "posture"),
    (
        ({"adapter_readiness_verified": False}, "adapter_required"),
        (
            {"activation_configuration_complete": False},
            "configuration_required",
        ),
        ({"external_facility_available": False}, "external_facility_required"),
        (
            {"target_readiness_verified": False},
            "blocked_pending_live_evidence",
        ),
        (
            {"recovery_verified": False},
            "blocked_pending_live_evidence",
        ),
        (
            {"live_external_evidence_verified": False},
            "blocked_pending_live_evidence",
        ),
    ),
)
def test_activation_decision_is_exact_and_never_activates(
    override: dict[str, bool], posture: str
) -> None:
    decision = decide_governed_browser_lane_activation(_activation_evidence(**override))

    assert decision.posture == posture
    assert decision.activation_performed is False
    assert decision.real_external_targets_enabled is False
    assert decision.browser_action_enabled is False
    assert decision.live_network_enabled is False
    assert decision.external_mutation_enabled is False
    assert decision.standing_authority_granted is False


def test_complete_evidence_only_becomes_eligible_for_separate_review() -> None:
    decision = decide_governed_browser_lane_activation(_activation_evidence())
    assert (
        decision.posture
        == GovernedBrowserActivationPosture.eligible_for_separate_activation_review.value
    )
    assert decision.activation_performed is False
    assert decision.reason_refs == (
        "reason-ref:governed-browser-queue02:separate-review-required",
    )


def test_honest_matrix_covers_every_lane_and_keeps_every_lane_inactive() -> None:
    matrix = governed_browser_queue02_inactive_activation_matrix(
        macos_packaged_golden_verified=True
    )

    assert len(matrix) == len(GovernedBrowserQueue02Lane) == 13
    assert {decision.lane for decision in matrix} == {
        lane.value for lane in GovernedBrowserQueue02Lane
    }
    assert not any(decision.activation_performed for decision in matrix)
    assert not any(decision.real_external_targets_enabled for decision in matrix)
    assert {decision.posture for decision in matrix} <= {
        "adapter_required",
        "configuration_required",
        "external_facility_required",
        "blocked_pending_live_evidence",
    }


def test_queue02_static_verifier_passes() -> None:
    assert verify() == []
