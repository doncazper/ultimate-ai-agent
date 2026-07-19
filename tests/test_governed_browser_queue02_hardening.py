from __future__ import annotations

import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from pydantic import ValidationError

import ultimate_ai_agent.core.governed_browser.transaction as transaction_module
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
    ExternalActionDispatchOutcome,
    ExternalActionReadiness,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTransactionConflict,
    ExternalActionTransactionStore,
    ExactBrowserActionReceipt,
    ExactBrowserActionResult,
    ExactBrowserObservationReceipt,
    ExactPostFormResult,
    GovernedArtifactTransferReceipt,
    GovernedBrowserActivationPosture,
    GovernedBrowserOriginSessionReceipt,
    GovernedBrowserLaneActivationEvidence,
    GovernedBrowserQueue02Lane,
    GovernedExternalOperationReceipt,
    GovernedFinancialReceipt,
    GovernedHumanChallengeHandoffReceipt,
    GovernedTaskCompositionReceipt,
    build_external_action_approval_request,
    build_external_action_readiness,
    decide_governed_browser_lane_activation,
    governed_browser_queue02_inactive_activation_matrix,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.transaction import BudgetSettlement
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


def _wait_for_terminal(kernel, request, *, timeout: float = 2.0):  # type: ignore[no-untyped-def]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        receipt = kernel._store.replay_if_terminal(request)
        if receipt is not None:
            return receipt
        time.sleep(0.005)
    raise AssertionError("governed external-action terminal receipt was not persisted")


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


@pytest.mark.parametrize(
    "receipt_prefix",
    (
        "receipt-ref:governed-browser-action",
        "receipt-ref:governed-post-form",
    ),
)
def test_browser_action_receipt_identity_binds_budget_release_proof(
    receipt_prefix: str,
) -> None:
    payload = {
        "recipe_ref": _ref("recipe", "release-proof"),
        "transaction_ref": _ref("transaction", "release-proof"),
        "intent_ref": _ref("intent", "release-proof"),
        "binding_ref": _ref("binding", "release-proof"),
        "status": "transaction_blocked",
        "external_action_state": ExternalActionState.blocked,
        "external_action_receipt_ref": _ref("receipt", "external-action"),
        "budget_reservation_ref": _ref("budget-reservation", "release-proof"),
        "budget_release_ref": _ref("budget-release", "original"),
        "reason_refs": [_ref("reason", "release-proof")],
    }
    receipt_ref = stable_governed_browser_ref(
        receipt_prefix,
        ExactBrowserActionReceipt.model_construct(
            receipt_ref=f"{receipt_prefix}:pending",
            **payload,
        ).model_dump(mode="json", exclude={"receipt_ref"}),
    )
    receipt = ExactBrowserActionReceipt(receipt_ref=receipt_ref, **payload)

    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_ACTION_RECEIPT_REF_MISMATCH",
    ):
        ExactBrowserActionReceipt.model_validate(
            {
                **receipt.model_dump(mode="json"),
                "budget_release_ref": _ref("budget-release", "substituted"),
            }
        )


def test_browser_action_and_post_form_results_reject_cross_lane_receipts() -> None:
    payload = {
        "recipe_ref": _ref("recipe", "lane-bound-result"),
        "transaction_ref": _ref("transaction", "lane-bound-result"),
        "intent_ref": _ref("intent", "lane-bound-result"),
        "binding_ref": _ref("binding", "lane-bound-result"),
        "status": "transaction_blocked",
        "external_action_state": ExternalActionState.blocked,
        "external_action_receipt_ref": _ref("receipt", "external-action"),
        "reason_refs": [_ref("reason", "lane-bound-result")],
    }

    def receipt(prefix: str) -> ExactBrowserActionReceipt:
        receipt_ref = stable_governed_browser_ref(
            prefix,
            ExactBrowserActionReceipt.model_construct(
                receipt_ref=f"{prefix}:pending",
                **payload,
            ).model_dump(mode="json", exclude={"receipt_ref"}),
        )
        return ExactBrowserActionReceipt(receipt_ref=receipt_ref, **payload)

    action_receipt = receipt("receipt-ref:governed-browser-action")
    post_form_receipt = receipt("receipt-ref:governed-post-form")

    ExactBrowserActionResult(receipt=action_receipt)
    ExactPostFormResult(receipt=post_form_receipt)
    with pytest.raises(
        ValidationError,
        match="GOVERNED_BROWSER_ACTION_RESULT_RECEIPT_KIND_MISMATCH",
    ):
        ExactBrowserActionResult(receipt=post_form_receipt)
    with pytest.raises(
        ValidationError,
        match="GOVERNED_POST_FORM_RESULT_RECEIPT_KIND_MISMATCH",
    ):
        ExactPostFormResult(receipt=action_receipt)


def test_request_scope_is_deep_frozen_before_provider_callbacks(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="deep-frozen-scope"))
    provider_observed_immutable_scope = False

    def readiness(item):  # type: ignore[no-untyped-def]
        nonlocal provider_observed_immutable_scope
        assert isinstance(item.binding.artifact_refs, tuple)
        assert isinstance(item.binding.resource_refs, tuple)
        with pytest.raises(AttributeError):
            item.binding.resource_refs.append(_ref("resource", "injected"))
        provider_observed_immutable_scope = True
        return _readiness(item)

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    receipt = kernel.execute(request, dispatch=_success)

    assert provider_observed_immutable_scope is True
    assert receipt.state == ExternalActionState.succeeded.value


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
            proof_ref for allowed, proof_ref in approval_proof_refs if not allowed
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
    dispatch_entered = threading.Event()
    allow_dispatch_to_stop = threading.Event()
    dispatch_stopped = threading.Event()

    def slow_dispatch(item):  # type: ignore[no-untyped-def]
        dispatch_entered.set()
        assert allow_dispatch_to_stop.wait(timeout=2)
        dispatch_stopped.set()
        return _success(item)

    started = time.monotonic()
    receipt = kernel.execute(request, dispatch=slow_dispatch)
    elapsed = time.monotonic() - started

    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert dispatch_entered.is_set()
    assert dispatch_stopped.is_set() is False
    assert elapsed < 0.2
    assert "reason-ref:governed-external-action:dispatch-timeout" in (
        receipt.reason_refs
    )
    assert receipt.automatic_retry_allowed is False
    assert kernel._store.state_if_exact(request) == ExternalActionState.started
    assert kernel._store.dispatch_slot_is_owned_by(request) is True
    started_at = kernel._store.started_at_if_exact(request)
    assert started_at is not None
    kernel._clock = lambda: started_at + timedelta(seconds=36)
    assert kernel.recover_if_prior_start(request) is None
    still_live = kernel.execute(request, dispatch=_success)
    assert still_live.replayed is False
    assert "reason-ref:governed-external-action:start-already-claimed" in (
        still_live.reason_refs
    )

    allow_dispatch_to_stop.set()
    assert dispatch_stopped.wait(timeout=2)
    terminal = _wait_for_terminal(kernel, request)
    assert terminal.state == ExternalActionState.outcome_ambiguous.value
    assert kernel._store.dispatch_slot_is_owned_by(request) is False
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
    assert _wait_for_terminal(first_kernel, first_request).state == (
        ExternalActionState.outcome_ambiguous.value
    )
    assert _wait_for_terminal(second_kernel, second_request).state == (
        ExternalActionState.outcome_ambiguous.value
    )


def test_dispatch_cannot_start_when_worker_misses_the_deadline(
    tmp_path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="worker-start-timeout"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    kernel._dispatch_timeout_seconds = 0.01
    allow_worker_start = threading.Event()
    real_thread = threading.Thread
    calls = 0

    class DelayedThread:
        def __init__(self, *, target, name, daemon):  # type: ignore[no-untyped-def]
            self._target = target
            self._thread = real_thread(
                target=self._run,
                name=name,
                daemon=daemon,
            )

        def _run(self) -> None:
            assert allow_worker_start.wait(timeout=2)
            self._target()

        def start(self) -> None:
            self._thread.start()

    monkeypatch.setattr(transaction_module, "Thread", DelayedThread)

    def dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(item)

    receipt = kernel.execute(request, dispatch=dispatch)

    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert calls == 0
    assert receipt.budget_release_ref is not None
    assert receipt.budget_settlement_ref is None
    assert kernel._store.state_if_exact(request) == ExternalActionState.outcome_ambiguous
    assert kernel._store.dispatch_slot_is_owned_by(request) is False

    allow_worker_start.set()
    terminal = _wait_for_terminal(kernel, request)
    assert calls == 0
    assert terminal.state == ExternalActionState.outcome_ambiguous.value
    assert terminal.budget_release_ref is not None
    assert terminal.budget_settlement_ref is None
    assert kernel._store.dispatch_slot_is_owned_by(request) is False


def test_worker_rechecks_expired_readiness_before_dispatch(
    tmp_path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="worker-readiness-expired"))
    readiness_expires_at = utc_now() + timedelta(seconds=1)

    def readiness(item):  # type: ignore[no-untyped-def]
        return build_external_action_readiness(
            item,
            status="ready",
            observed_at=utc_now() - timedelta(seconds=1),
            expires_at=readiness_expires_at,
            broker_integrity_verified=True,
            external_mutation_enabled=True,
            safe_disable_active=False,
            kill_switch_engaged=False,
        )

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    kernel._dispatch_timeout_seconds = 2
    worker_waiting = threading.Event()
    allow_worker_start = threading.Event()
    real_thread = threading.Thread
    calls = 0

    class DelayedThread:
        def __init__(self, *, target, name, daemon):  # type: ignore[no-untyped-def]
            self._target = target
            self._thread = real_thread(
                target=self._run,
                name=name,
                daemon=daemon,
            )

        def _run(self) -> None:
            worker_waiting.set()
            assert allow_worker_start.wait(timeout=3)
            self._target()

        def start(self) -> None:
            self._thread.start()

    monkeypatch.setattr(transaction_module, "Thread", DelayedThread)

    def dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(item)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(kernel.execute, request, dispatch=dispatch)
        assert worker_waiting.wait(timeout=2)
        time.sleep(
            max(0.0, (readiness_expires_at - utc_now()).total_seconds()) + 0.05
        )
        allow_worker_start.set()
        receipt = future.result(timeout=2)

    assert calls == 0
    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert "reason-ref:governed-external-action:readiness-fail-closed" in (
        receipt.reason_refs
    )
    assert receipt.budget_release_ref is not None
    assert receipt.budget_settlement_ref is None
    assert kernel._store.dispatch_slot_is_owned_by(request) is False


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
    assert (
        store.claim_start(
            request,
            budget_reservation_ref=reservation.reservation_ref,
        )
        is True
    )
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


def test_execute_automatically_recovers_a_stale_started_transaction(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="automatic-stale-start-recovery"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    approval_validation = build_external_action_approval_request(
        request
    ).to_validation_request(request.approval_ref)
    reservation = kernel._budget_gate.reserve(request, approval_validation)
    assert reservation.allowed is True
    assert reservation.reservation_ref is not None
    kernel._store.prepare(request)
    assert (
        kernel._store.claim_start(
            request,
            budget_reservation_ref=reservation.reservation_ref,
        )
        is True
    )
    started_at = kernel._store.started_at_if_exact(request)
    assert started_at is not None
    kernel._clock = lambda: started_at + timedelta(seconds=36)
    calls = 0

    def dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(item)

    recovered = kernel.execute(request, dispatch=dispatch)

    assert calls == 0
    assert recovered.state == ExternalActionState.outcome_ambiguous.value
    assert recovered.budget_reservation_ref == reservation.reservation_ref
    assert recovered.budget_settlement_ref is not None


def test_recovery_reuses_a_prior_durable_settlement_proof(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="prior-settlement-recovery"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    approval_validation = build_external_action_approval_request(
        request
    ).to_validation_request(request.approval_ref)
    reservation = kernel._budget_gate.reserve(request, approval_validation)
    assert reservation.allowed is True
    assert reservation.reservation_ref is not None
    kernel._store.prepare(request)
    assert (
        kernel._store.claim_start(
            request,
            budget_reservation_ref=reservation.reservation_ref,
        )
        is True
    )
    prior_settlement = kernel._budget_gate.settle(
        request,
        reservation.reservation_ref,
        ExternalActionDispatchOutcome.succeeded,
        [_ref("evidence", "prior-durable-settlement")],
    )
    assert prior_settlement.allowed is True
    assert prior_settlement.receipt_ref is not None
    started_at = kernel._store.started_at_if_exact(request)
    assert started_at is not None
    kernel._clock = lambda: started_at + timedelta(seconds=36)
    calls = 0

    def dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(item)

    recovered = kernel.execute(request, dispatch=dispatch)

    assert calls == 0
    assert recovered.state == ExternalActionState.outcome_ambiguous.value
    assert recovered.budget_settlement_ref == prior_settlement.receipt_ref
    assert not any(
        marker in reason
        for reason in recovered.reason_refs
        for marker in ("budget-settlement-ambiguous", "budget-settlement-failed")
    )


def test_recovery_reuses_a_prior_durable_release_proof(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="prior-release-recovery"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    approval_validation = build_external_action_approval_request(
        request
    ).to_validation_request(request.approval_ref)
    reservation = kernel._budget_gate.reserve(request, approval_validation)
    assert reservation.allowed is True
    assert reservation.reservation_ref is not None
    kernel._store.prepare(request)
    assert (
        kernel._store.claim_start(
            request,
            budget_reservation_ref=reservation.reservation_ref,
        )
        is True
    )
    prior_release = kernel._budget_gate.release(
        request,
        reservation.reservation_ref,
        "reason-ref:governed-external-action:test-no-dispatch",
    )
    assert prior_release.allowed is True
    assert prior_release.receipt_ref is not None
    started_at = kernel._store.started_at_if_exact(request)
    assert started_at is not None
    kernel._clock = lambda: started_at + timedelta(seconds=36)

    recovered = kernel.recover_if_prior_start(request)

    assert recovered is not None
    assert recovered.state == ExternalActionState.outcome_ambiguous.value
    assert recovered.budget_release_ref == prior_release.receipt_ref
    assert recovered.budget_settlement_ref is None
    assert "reason-ref:governed-external-action:prior-start-release-reconciled" in (
        recovered.reason_refs
    )


def test_dispatch_slot_remains_owned_through_settlement_and_terminal_close(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="settlement-owner"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    settlement_entered = threading.Event()
    allow_settlement = threading.Event()
    original_settle = kernel._budget_gate.settle

    def blocking_settle(*args, **kwargs):  # type: ignore[no-untyped-def]
        settlement_entered.set()
        assert allow_settlement.wait(timeout=2)
        return original_settle(*args, **kwargs)

    kernel._budget_gate.settle = blocking_settle  # type: ignore[method-assign]
    with ThreadPoolExecutor(max_workers=1) as pool:
        owner_future = pool.submit(kernel.execute, request, dispatch=_success)
        assert settlement_entered.wait(timeout=2)
        started_at = kernel._store.started_at_if_exact(request)
        assert started_at is not None
        kernel._clock = lambda: started_at + timedelta(seconds=36)
        assert kernel._store.dispatch_slot_is_owned_by(request) is True
        assert kernel.recover_if_prior_start(request) is None
        assert kernel._store.state_if_exact(request) == ExternalActionState.started
        contender = kernel.execute(request, dispatch=_success)
        assert contender.replayed is False
        assert "reason-ref:governed-external-action:start-already-claimed" in (
            contender.reason_refs
        )
        allow_settlement.set()
        receipt = owner_future.result(timeout=2)

    assert receipt.state == ExternalActionState.succeeded.value
    assert kernel._store.dispatch_slot_is_owned_by(request) is False


def test_dispatch_slot_is_owned_before_post_claim_revalidation(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="pre-revalidation-owner"))
    post_claim_entered = threading.Event()
    allow_post_claim = threading.Event()
    readiness_reads = 0
    calls = 0

    def readiness(item):  # type: ignore[no-untyped-def]
        nonlocal readiness_reads
        readiness_reads += 1
        if readiness_reads == 2:
            post_claim_entered.set()
            assert allow_post_claim.wait(timeout=2)
        return _readiness(item)

    def dispatch(item):  # type: ignore[no-untyped-def]
        nonlocal calls
        calls += 1
        return _success(item)

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    with ThreadPoolExecutor(max_workers=1) as pool:
        owner_future = pool.submit(kernel.execute, request, dispatch=dispatch)
        assert post_claim_entered.wait(timeout=2)
        started_at = kernel._store.started_at_if_exact(request)
        assert started_at is not None
        kernel._clock = lambda: started_at + timedelta(seconds=36)
        assert kernel._store.dispatch_slot_is_owned_by(request) is True
        assert kernel.recover_if_prior_start(request) is None
        assert kernel._store.state_if_exact(request) == ExternalActionState.started
        allow_post_claim.set()
        receipt = owner_future.result(timeout=2)

    assert calls == 1
    assert receipt.state == ExternalActionState.succeeded.value
    assert kernel._store.dispatch_slot_is_owned_by(request) is False


def test_replayed_denied_budget_release_remains_denied(tmp_path) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="replayed-denied-release"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    reservation_ref = _ref("budget-reservation", "missing")
    reason_ref = "reason-ref:governed-external-action:test-unused-release"

    first = kernel._budget_gate.release(request, reservation_ref, reason_ref)
    replay = kernel._budget_gate.release(request, reservation_ref, reason_ref)

    assert first.allowed is False
    assert replay.allowed is False
    assert first.receipt_ref is not None
    assert replay.receipt_ref is not None


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
    assert second.budget_reservation_ref is None
    assert second.budget_release_ref is None
    assert second.budget_settlement_ref is None


def test_lost_start_claim_releases_only_a_distinct_unused_reservation(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="lost-start-claim-release"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    original_claim_start = kernel._store.claim_start
    owner_reservation_ref = _ref("budget-reservation", "winning-owner")

    def lose_claim(item, *, budget_reservation_ref=None):  # type: ignore[no-untyped-def]
        assert budget_reservation_ref is not None
        assert original_claim_start(
            item,
            budget_reservation_ref=owner_reservation_ref,
        )
        return False

    kernel._store.claim_start = lose_claim  # type: ignore[method-assign]
    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert receipt.budget_reservation_ref is not None
    assert receipt.budget_reservation_ref != owner_reservation_ref
    assert receipt.budget_release_ref is not None
    assert receipt.budget_settlement_ref is None
    assert kernel._store.started_budget_reservation_ref_if_exact(request) == (
        owner_reservation_ref
    )


def test_lost_start_claim_preserves_the_winners_shared_reservation(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="lost-start-claim-shared-reservation"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    original_claim_start = kernel._store.claim_start

    def lose_shared_claim(
        item,
        *,
        budget_reservation_ref=None,
    ):  # type: ignore[no-untyped-def]
        assert budget_reservation_ref is not None
        assert original_claim_start(
            item,
            budget_reservation_ref=budget_reservation_ref,
        )
        return False

    kernel._store.claim_start = lose_shared_claim  # type: ignore[method-assign]
    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert receipt.budget_reservation_ref is not None
    assert receipt.budget_release_ref is None
    assert receipt.budget_settlement_ref is None
    assert kernel._store.started_budget_reservation_ref_if_exact(request) == (
        receipt.budget_reservation_ref
    )


def test_same_request_contender_never_releases_live_owner_reservation(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="preclaim-live-owner"))
    preclaim_entered = threading.Event()
    allow_preclaim = threading.Event()
    release_refs: list[str] = []
    readiness_reads = 0

    def readiness(item):  # type: ignore[no-untyped-def]
        nonlocal readiness_reads
        readiness_reads += 1
        if readiness_reads == 1:
            preclaim_entered.set()
            assert allow_preclaim.wait(timeout=2)
        return _readiness(item)

    kernel, _ = _authorized_kernel(
        tmp_path,
        request,
        readiness_provider=readiness,
    )
    original_release = kernel._budget_gate.release

    def record_release(item, reservation_ref, reason_ref):  # type: ignore[no-untyped-def]
        release_refs.append(reservation_ref)
        return original_release(item, reservation_ref, reason_ref)

    kernel._budget_gate.release = record_release  # type: ignore[method-assign]
    with ThreadPoolExecutor(max_workers=1) as pool:
        owner_future = pool.submit(kernel.execute, request, dispatch=_success)
        assert preclaim_entered.wait(timeout=2)
        contender = kernel.execute(request, dispatch=_success)
        allow_preclaim.set()
        owner = owner_future.result(timeout=2)

    assert release_refs == []
    assert contender.state == ExternalActionState.outcome_ambiguous.value
    assert contender.budget_reservation_ref is None
    assert contender.budget_release_ref is None
    assert owner.state == ExternalActionState.succeeded.value, owner
    assert owner.budget_reservation_ref is not None
    assert owner.budget_settlement_ref is not None


def test_lost_start_claim_surfaces_distinct_local_release_proof_after_terminal(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="lost-start-terminal-release"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    original_claim_start = kernel._store.claim_start
    owner_reservation_ref = _ref("budget-reservation", "terminal-owner")

    def terminalize_before_losing_claim(
        item,
        *,
        budget_reservation_ref=None,
    ):  # type: ignore[no-untyped-def]
        assert budget_reservation_ref is not None
        assert original_claim_start(
            item,
            budget_reservation_ref=owner_reservation_ref,
        )
        terminal = kernel._build_receipt(
            item,
            ExternalActionState.failed,
            ["reason-ref:governed-external-action:winning-owner-failed"],
            budget_reservation_ref=owner_reservation_ref,
        )
        kernel._store.finish(
            terminal,
            expected_state=ExternalActionState.started,
        )
        return False

    kernel._store.claim_start = terminalize_before_losing_claim  # type: ignore[method-assign]
    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.replayed is False
    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert receipt.budget_reservation_ref is not None
    assert receipt.budget_reservation_ref != owner_reservation_ref
    assert receipt.budget_release_ref is not None
    assert receipt.budget_settlement_ref is None
    assert "reason-ref:governed-external-action:start-claim-conflict" in (
        receipt.reason_refs
    )


def test_lost_start_claim_rejects_release_without_receipt_proof(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="lost-start-release-proof-missing"))
    kernel, _ = _authorized_kernel(tmp_path, request)
    original_claim_start = kernel._store.claim_start

    def lose_to_distinct_owner(
        item,
        *,
        budget_reservation_ref=None,
    ):  # type: ignore[no-untyped-def]
        assert budget_reservation_ref is not None
        assert original_claim_start(
            item,
            budget_reservation_ref=_ref("budget-reservation", "distinct-owner"),
        )
        return False

    kernel._store.claim_start = lose_to_distinct_owner  # type: ignore[method-assign]
    kernel._budget_gate.release = (  # type: ignore[method-assign]
        lambda _request, _reservation_ref, _reason_ref: BudgetSettlement(
            allowed=True,
        )
    )

    receipt = kernel.execute(request, dispatch=_success)

    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert receipt.budget_release_ref is None
    assert "reason-ref:governed-external-action:budget-release-unconfirmed" in (
        receipt.reason_refs
    )


def test_prestart_finish_cas_loss_returns_current_ambiguous_state(
    tmp_path,
) -> None:  # type: ignore[no-untyped-def]
    request = _request(_binding(suffix="prestart-finish-cas"))
    kernel, authority = _authorized_kernel(tmp_path, request)
    authority.revoke(
        request.approval_ref,
        "Operator withdrew the exact approval before execution.",
    )
    original_finish = kernel._store.finish
    raced = False

    def start_before_finish(receipt, *, expected_state):  # type: ignore[no-untyped-def]
        nonlocal raced
        if not raced and expected_state == ExternalActionState.prepared:
            raced = True
            assert kernel._store.claim_start(request) is True
        return original_finish(receipt, expected_state=expected_state)

    kernel._store.finish = start_before_finish  # type: ignore[method-assign]
    receipt = kernel.execute(request, dispatch=_success)

    assert raced is True
    assert receipt.state == ExternalActionState.outcome_ambiguous.value
    assert "reason-ref:governed-external-action:finish-ownership-lost" in (
        receipt.reason_refs
    )
    assert kernel._store.state_if_exact(request) == ExternalActionState.started


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


@pytest.mark.parametrize(
    "receipt_type",
    (
        ExactBrowserActionReceipt,
        ExactBrowserObservationReceipt,
        GovernedArtifactTransferReceipt,
        GovernedBrowserOriginSessionReceipt,
        GovernedExternalOperationReceipt,
        GovernedFinancialReceipt,
        GovernedHumanChallengeHandoffReceipt,
        GovernedTaskCompositionReceipt,
    ),
)
def test_every_operator_receipt_contract_retains_budget_release_proof(
    receipt_type: type,
) -> None:
    assert "budget_release_ref" in receipt_type.model_fields


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
