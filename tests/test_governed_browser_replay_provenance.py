from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from ultimate_ai_agent.core.governed_browser.contracts import (
    ExternalActionAuthorityBinding,
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    ExternalActionReplayEvidenceEnvelope,
    ExternalActionReplayEvidenceExpectation,
    ExternalActionReplayValidationContext,
    _build_external_action_replay_validation_context,
    _require_operation_replay_evidence_envelope,
    replay_validation_context,
    require_external_action_replay_provenance,
)
from ultimate_ai_agent.core.governed_browser.transaction import (
    ExternalActionTransactionStore,
    GovernedExternalActionKernel,
)


LANE_REF = "replay-lane-ref:governed-browser:test"
OPERATION_REF = "replay-operation-ref:governed-browser:test"


def _ref(prefix: str, suffix: str) -> str:
    return f"{prefix}-ref:governed-browser:{suffix}"


def _request(suffix: str) -> ExternalActionExecutionRequest:
    origin = "http://127.0.0.1:8765"
    binding = ExternalActionAuthorityBinding(
        target_kind=ExternalActionTargetKind.local_validation,
        origin=origin,
        origin_ref=stable_governed_browser_ref(
            "origin-ref:governed-browser",
            {"origin": origin},
        ),
        recipient_ref=_ref("recipient", suffix),
        field_schema_ref=_ref("field-schema", suffix),
        transaction_ref=_ref("transaction", suffix),
        artifact_refs=(_ref("artifact", suffix),),
        resource_refs=(_ref("resource", suffix),),
        page_snapshot_ref=_ref("page-snapshot", suffix),
        start_deadline=datetime(2027, 1, 1, tzinfo=timezone.utc),
        human_presence_ref=_ref("human-presence", suffix),
        human_present=True,
    )
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
        approval_ref=_ref("approval", suffix),
    )


def _receipt(
    request: ExternalActionExecutionRequest,
    *,
    evidence_refs: tuple[str, ...],
    proof_suffix: str,
    replayed: bool = False,
    state: ExternalActionState = ExternalActionState.succeeded,
    reason_refs: tuple[str, ...] = (),
) -> ExternalActionReceipt:
    payload = {
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "state": state.value,
        "approval_validation_ref": _ref("approval-validation", proof_suffix),
        "authority_decision_ref": _ref("authority-decision", proof_suffix),
        "budget_reservation_ref": _ref("budget-reservation", proof_suffix),
        "budget_settlement_ref": _ref("budget-settlement", proof_suffix),
        "evidence_refs": list(evidence_refs),
        "reason_refs": list(reason_refs),
    }
    return ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            payload,
        ),
        **payload,
        replayed=replayed,
    )


def _rehash_receipt(
    receipt: ExternalActionReceipt,
    **updates: object,
) -> ExternalActionReceipt:
    payload = receipt.model_dump(mode="json")
    payload.update(updates)
    payload.pop("receipt_ref")
    payload.pop("replayed")
    identity_payload = {
        key: payload[key]
        for key in (
            "transaction_ref",
            "intent_ref",
            "binding_ref",
            "state",
            "approval_validation_ref",
            "authority_decision_ref",
            "budget_reservation_ref",
            "budget_settlement_ref",
            "evidence_refs",
            "reason_refs",
        )
    }
    if payload["budget_release_ref"] is not None:
        identity_payload["budget_release_ref"] = payload["budget_release_ref"]
    return ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            identity_payload,
        ),
        **payload,
    )


@dataclass
class _FakeKernel:
    expected_execution: ExternalActionExecutionRequest
    terminal_receipt: ExternalActionReceipt
    replay_override: ExternalActionReceipt | None = None
    replay_calls: int = 0
    terminal_calls: int = 0

    def replay_if_terminal(
        self,
        request: ExternalActionExecutionRequest,
    ) -> ExternalActionReceipt | None:
        self.replay_calls += 1
        if request != self.expected_execution:
            return None
        if self.replay_override is not None:
            return self.replay_override
        return ExternalActionReceipt.model_validate(
            {
                **self.terminal_receipt.model_dump(mode="json"),
                "replayed": True,
            }
        )

    def terminal_receipt_by_ref(
        self,
        *,
        transaction_ref: str,
        receipt_ref: str,
    ) -> ExternalActionReceipt | None:
        self.terminal_calls += 1
        if (
            transaction_ref != self.expected_execution.binding.transaction_ref
            or receipt_ref != self.terminal_receipt.receipt_ref
        ):
            return None
        return self.terminal_receipt


def _expectation(
    evidence_refs: tuple[str, ...],
) -> ExternalActionReplayEvidenceExpectation:
    return ExternalActionReplayEvidenceExpectation(
        lane_ref=LANE_REF,
        operation_ref=OPERATION_REF,
        evidence_refs=evidence_refs,
    )


def _concrete_kernel_with_terminal(
    tmp_path: Path,
    *,
    request: ExternalActionExecutionRequest,
    terminal: ExternalActionReceipt,
    database_name: str,
) -> GovernedExternalActionKernel:
    store = ExternalActionTransactionStore(tmp_path / f"{database_name}.sqlite3")
    state, prior = store.prepare(request)
    assert state == ExternalActionState.prepared
    assert prior is None
    store.finish(terminal, expected_state=ExternalActionState.prepared)
    kernel = object.__new__(GovernedExternalActionKernel)
    kernel._store = store
    return kernel


def _context_fixture(
    tmp_path: Path,
    suffix: str = "clean",
) -> tuple[
    GovernedExternalActionKernel,
    ExternalActionReceipt,
    ExternalActionReplayValidationContext,
]:
    request = _request(suffix)
    evidence_refs = (
        _ref("evidence", f"{suffix}-one"),
        _ref("evidence", f"{suffix}-two"),
    )
    terminal = _receipt(
        request,
        evidence_refs=evidence_refs,
        proof_suffix=suffix,
    )
    replay = terminal.model_copy(update={"replayed": True})
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request,
        terminal=terminal,
        database_name=suffix,
    )
    context = _build_external_action_replay_validation_context(
        kernel,
        expected_execution=request,
        replay_receipt=replay,
        expectation=_expectation(evidence_refs),
    )
    return kernel, replay, context


def test_clean_proof_uses_atomic_row_and_builds_deterministic_envelope(
    tmp_path: Path,
) -> None:
    _, replay, context = _context_fixture(tmp_path)

    authenticated = require_external_action_replay_provenance(
        replay_validation_context(context),
        lane_ref=LANE_REF,
        operation_ref=OPERATION_REF,
        candidate=replay,
    )

    assert authenticated is context
    assert context.envelope.evidence_refs == replay.evidence_refs
    assert context.envelope.terminal_receipt_ref == replay.receipt_ref
    assert context.envelope.terminal_transaction_ref == replay.transaction_ref
    reparsed = ExternalActionReplayEvidenceEnvelope.model_validate(
        context.envelope.model_dump(mode="json")
    )
    assert reparsed == context.envelope


@pytest.mark.parametrize(
    "invalid_context",
    [
        None,
        {},
        {"lane_ref": LANE_REF, "operation_ref": OPERATION_REF},
        SimpleNamespace(context=None),
        SimpleNamespace(context={}),
    ],
)
def test_missing_or_wrong_context_fails_closed(
    invalid_context: object,
    tmp_path: Path,
) -> None:
    _, replay, _ = _context_fixture(tmp_path, "context")

    with pytest.raises(ValueError, match="PROVENANCE_CONTEXT_REQUIRED"):
        require_external_action_replay_provenance(
            invalid_context,
            lane_ref=LANE_REF,
            operation_ref=OPERATION_REF,
            candidate=replay,
        )


@pytest.mark.parametrize(
    ("lane_ref", "operation_ref", "error"),
    [
        (
            "replay-lane-ref:governed-browser:other",
            OPERATION_REF,
            "PROVENANCE_LANE_MISMATCH",
        ),
        (
            LANE_REF,
            "replay-operation-ref:governed-browser:other",
            "PROVENANCE_OPERATION_MISMATCH",
        ),
    ],
)
def test_wrong_lane_or_operation_fails_closed(
    lane_ref: str,
    operation_ref: str,
    error: str,
    tmp_path: Path,
) -> None:
    _, replay, context = _context_fixture(tmp_path, "wrong-scope")

    with pytest.raises(ValueError, match=error):
        require_external_action_replay_provenance(
            replay_validation_context(context),
            lane_ref=lane_ref,
            operation_ref=operation_ref,
            candidate=replay,
        )


def test_expected_request_fingerprint_mismatch_fails_closed(
    tmp_path: Path,
) -> None:
    request = _request("fingerprint-a")
    other_request = _request("fingerprint-b")
    terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "fingerprint"),),
        proof_suffix="fingerprint",
    )
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request,
        terminal=terminal,
        database_name="fingerprint",
    )

    with pytest.raises(ValueError, match="PROVENANCE_TERMINAL_REQUIRED"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=other_request,
            replay_receipt=terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(terminal.evidence_refs),
        )

def test_authenticated_context_rejects_recomputed_wrong_request_fingerprint(
    tmp_path: Path,
) -> None:
    _, replay, context = _context_fixture(tmp_path, "context-fingerprint")
    wrong_request = _request("context-fingerprint-other")
    forged_payload = context.envelope.model_dump(mode="json")
    forged_payload["expected_request_fingerprint_ref"] = (
        stable_governed_browser_ref(
            "request-fingerprint-ref:governed-external-action",
            wrong_request.model_dump(mode="json"),
        )
    )
    forged_payload["envelope_ref"] = stable_governed_browser_ref(
        "replay-evidence-envelope-ref:governed-external-action",
        {
            key: value
            for key, value in forged_payload.items()
            if key != "envelope_ref"
        },
    )
    forged_envelope = ExternalActionReplayEvidenceEnvelope.model_validate(
        forged_payload
    )
    object.__setattr__(context, "envelope", forged_envelope)

    with pytest.raises(ValueError, match="PROVENANCE_CONTEXT_INVALID"):
        replay_validation_context(context)


def test_cross_transaction_substitution_fails_closed(tmp_path: Path) -> None:
    request_a = _request("transaction-a")
    request_b = _request("transaction-b")
    terminal_a = _receipt(
        request_a,
        evidence_refs=(_ref("evidence", "transaction-a"),),
        proof_suffix="transaction-a",
    )
    terminal_b = _receipt(
        request_b,
        evidence_refs=(_ref("evidence", "transaction-b"),),
        proof_suffix="transaction-b",
    )
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request_a,
        terminal=terminal_a,
        database_name="cross-transaction",
    )

    with pytest.raises(ValueError, match="PROVENANCE_LOOKUP_FAILED"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request_a,
            replay_receipt=terminal_b.model_copy(update={"replayed": True}),
            expectation=_expectation(terminal_a.evidence_refs),
        )
@pytest.mark.parametrize(
    "mutated_evidence",
    [
        (
            _ref("evidence", "two"),
            _ref("evidence", "one"),
        ),
        (_ref("evidence", "one"),),
        (
            _ref("evidence", "one"),
            _ref("evidence", "two"),
            _ref("evidence", "three"),
        ),
        (
            _ref("evidence", "one"),
            _ref("evidence", "tampered"),
        ),
    ],
    ids=["reordered", "wrong-arity-short", "wrong-arity-long", "tampered"],
)
def test_recomputed_receipt_hash_cannot_rebind_expected_evidence(
    mutated_evidence: tuple[str, ...],
    tmp_path: Path,
) -> None:
    request = _request("evidence")
    expected_evidence = (
        _ref("evidence", "one"),
        _ref("evidence", "two"),
    )
    forged_terminal = _receipt(
        request,
        evidence_refs=mutated_evidence,
        proof_suffix="evidence",
    )
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request,
        terminal=forged_terminal,
        database_name=f"evidence-{len(mutated_evidence)}-{mutated_evidence[-1][-8:]}",
    )

    with pytest.raises(ValueError, match="PROVENANCE_EVIDENCE_MISMATCH"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=forged_terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(expected_evidence),
        )

def test_forged_context_object_and_dict_fail_closed(tmp_path: Path) -> None:
    _, replay, _ = _context_fixture(tmp_path, "forged-context")
    forged = object.__new__(ExternalActionReplayValidationContext)
    object.__setattr__(forged, "_authentication_token", object())

    for invalid in (
        forged,
        {"uaa_external_action_replay_validation_context": forged},
        SimpleNamespace(
            context={"uaa_external_action_replay_validation_context": forged}
        ),
    ):
        with pytest.raises(ValueError, match="PROVENANCE_CONTEXT_INVALID"):
            require_external_action_replay_provenance(
                invalid,
                lane_ref=LANE_REF,
                operation_ref=OPERATION_REF,
                candidate=replay,
            )


def test_legitimate_token_cannot_authenticate_a_copied_context(
    tmp_path: Path,
) -> None:
    _, replay, legitimate = _context_fixture(tmp_path, "copied-auth")
    forged = object.__new__(ExternalActionReplayValidationContext)
    for field_name in (
        "envelope",
        "expected_execution",
        "terminal_receipt",
        "_authentication_token",
    ):
        object.__setattr__(
            forged,
            field_name,
            getattr(legitimate, field_name),
        )

    with pytest.raises(ValueError, match="PROVENANCE_CONTEXT_INVALID"):
        require_external_action_replay_provenance(
            {
                "uaa_external_action_replay_validation_context": forged,
            },
            lane_ref=LANE_REF,
            operation_ref=OPERATION_REF,
            candidate=replay,
        )


def test_terminal_receipt_must_not_be_marked_replayed(tmp_path: Path) -> None:
    request = _request("terminal-replay-flag")
    replayed_terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "terminal-replay-flag"),),
        proof_suffix="terminal-replay-flag",
        replayed=True,
    )
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request,
        terminal=replayed_terminal,
        database_name="terminal-replay-flag",
    )

    with pytest.raises(ValueError, match="PROVENANCE_LOOKUP_FAILED"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=replayed_terminal,
            expectation=_expectation(replayed_terminal.evidence_refs),
        )

def test_exact_full_candidate_mismatch_fails_even_with_valid_recomputed_hash(
    tmp_path: Path,
) -> None:
    _, replay, context = _context_fixture(tmp_path, "candidate-mismatch")
    forged = _receipt(
        context.expected_execution,
        evidence_refs=replay.evidence_refs,
        proof_suffix="different-proof-chain",
        replayed=True,
    )

    with pytest.raises(ValueError, match="PROVENANCE_RECEIPT_MISMATCH"):
        require_external_action_replay_provenance(
            replay_validation_context(context),
            lane_ref=LANE_REF,
            operation_ref=OPERATION_REF,
            candidate=forged,
        )


def test_structurally_compatible_fake_source_cannot_mint_context() -> None:
    request = _request("fake-source")
    terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "fake-source"),),
        proof_suffix="fake-source",
    )
    fake_kernel = _FakeKernel(request, terminal)

    with pytest.raises(ValueError, match="PROVENANCE_SOURCE_INVALID"):
        _build_external_action_replay_validation_context(
            fake_kernel,
            expected_execution=request,
            replay_receipt=terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(terminal.evidence_refs),
        )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda context: object.__setattr__(
            context.envelope,
            "lane_ref",
            "replay-lane-ref:governed-browser:mutated",
        ),
        lambda context: object.__setattr__(
            context.expected_execution.binding,
            "transaction_ref",
            "transaction-ref:governed-browser:mutated",
        ),
        lambda context: object.__setattr__(
            context.terminal_receipt,
            "evidence_refs",
            (_ref("evidence", "mutated"),),
        ),
    ],
    ids=["envelope", "nested-request", "terminal-receipt"],
)
def test_in_place_context_snapshot_mutation_fails_closed(
    mutate: object,
    tmp_path: Path,
) -> None:
    _, _, context = _context_fixture(tmp_path, "in-place-context")
    mutate(context)

    with pytest.raises(ValueError, match="PROVENANCE_CONTEXT_INVALID"):
        replay_validation_context(context)


def test_concrete_attestation_ignores_instance_method_substitution(
    tmp_path: Path,
) -> None:
    kernel, replay, _ = _context_fixture(tmp_path, "instance-substitution")
    kernel.attest_terminal_replay = lambda *_args, **_kwargs: None

    context = _build_external_action_replay_validation_context(
        kernel,
        expected_execution=_request("instance-substitution"),
        replay_receipt=replay,
        expectation=_expectation(replay.evidence_refs),
    )

    assert context.terminal_receipt.receipt_ref == replay.receipt_ref


@pytest.mark.parametrize(
    (
        "state",
        "evidence_kind",
        "success_valid",
        "failure_valid",
        "reason_refs",
    ),
    [
        (ExternalActionState.succeeded, "lane", True, False, ()),
        (ExternalActionState.failed, "lane", False, True, ()),
        (ExternalActionState.blocked, "empty", False, False, ()),
        (ExternalActionState.outcome_ambiguous, "lane", True, False, ()),
        (ExternalActionState.outcome_ambiguous, "lane", False, True, ()),
        (ExternalActionState.outcome_ambiguous, "kernel", False, False, ()),
        (
            ExternalActionState.outcome_ambiguous,
            "guard",
            False,
            False,
            (
                "reason-ref:governed-external-action:"
                "post-start-revalidation-denied",
            ),
        ),
    ],
)
def test_complete_terminal_evidence_envelope_accepts_only_defined_shapes(
    state: ExternalActionState,
    evidence_kind: str,
    success_valid: bool,
    failure_valid: bool,
    reason_refs: tuple[str, ...],
) -> None:
    request = _request(f"state-{state.value}-{evidence_kind}")
    if evidence_kind == "empty":
        evidence_refs: tuple[str, ...] = ()
    elif evidence_kind == "kernel":
        reason = "dispatch-timeout"
        evidence_refs = (
            stable_governed_browser_ref(
                f"evidence-ref:governed-external-action:{reason}",
                {
                    "reason": reason,
                    "transaction_ref": request.binding.transaction_ref,
                    "intent_ref": request.intent_ref,
                    "binding_ref": request.binding.binding_ref,
                },
            ),
        )
    elif evidence_kind == "guard":
        evidence_refs = (
            (
                "evidence-ref:governed-external-action:"
                f"post-start-guard:sha256:{'a' * 64}"
            ),
        )
    else:
        evidence_refs = (_ref("evidence", f"lane-{state.value}"),)
    receipt = _receipt(
        request,
        evidence_refs=evidence_refs,
        proof_suffix=f"state-{state.value}-{evidence_kind}",
        state=state,
        reason_refs=reason_refs,
    )

    _require_operation_replay_evidence_envelope(
        receipt,
        success_evidence_valid=success_valid,
        failure_evidence_valid=failure_valid,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )


@pytest.mark.parametrize(
    ("state", "evidence_refs"),
    [
        (ExternalActionState.prepared, ()),
        (ExternalActionState.started, ()),
        (ExternalActionState.blocked, (_ref("evidence", "blocked"),)),
        (
            ExternalActionState.outcome_ambiguous,
            (_ref("evidence", "arbitrary-ambiguous"),),
        ),
        (
            ExternalActionState.outcome_ambiguous,
            (
                "evidence-ref:governed-external-action:"
                f"post-start-guard:sha256:{'b' * 64}",
            ),
        ),
    ],
)
def test_undefined_terminal_evidence_envelopes_fail_closed(
    state: ExternalActionState,
    evidence_refs: tuple[str, ...],
) -> None:
    request = _request(f"invalid-state-{state.value}-{len(evidence_refs)}")
    receipt = _receipt(
        request,
        evidence_refs=evidence_refs,
        proof_suffix=f"invalid-state-{state.value}",
        state=state,
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            receipt,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


@pytest.mark.parametrize(
    "mismatched_field",
    ["intent_ref", "binding_ref"],
)
def test_atomic_attestation_rejects_request_scope_drift(
    mismatched_field: str,
    tmp_path: Path,
) -> None:
    request = _request(f"scope-drift-{mismatched_field}")
    terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "scope-drift"),),
        proof_suffix="scope-drift",
    )
    forged_terminal = _rehash_receipt(
        terminal,
        **{mismatched_field: _ref(mismatched_field.removesuffix("_ref"), "wrong")},
    )
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request,
        terminal=forged_terminal,
        database_name=f"scope-drift-{mismatched_field}",
    )

    with pytest.raises(ValueError, match="PROVENANCE_LOOKUP_FAILED"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=forged_terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(forged_terminal.evidence_refs),
        )


def test_atomic_attestation_rejects_nonterminal_row_state(tmp_path: Path) -> None:
    request = _request("nonterminal-row")
    terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "nonterminal-row"),),
        proof_suffix="nonterminal-row",
    )
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request,
        terminal=terminal,
        database_name="nonterminal-row",
    )
    with kernel._store._lock, kernel._store._connect() as connection:
        connection.execute(
            "UPDATE governed_external_actions SET state = ? "
            "WHERE transaction_ref = ?",
            (
                ExternalActionState.started.value,
                request.binding.transaction_ref,
            ),
        )
        connection.commit()

    with pytest.raises(ValueError, match="PROVENANCE_LOOKUP_FAILED"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(terminal.evidence_refs),
        )
