from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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
    build_external_action_replay_validation_context,
    replay_validation_context,
    require_external_action_replay_provenance,
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
) -> ExternalActionReceipt:
    payload = {
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
        "state": ExternalActionState.succeeded.value,
        "approval_validation_ref": _ref("approval-validation", proof_suffix),
        "authority_decision_ref": _ref("authority-decision", proof_suffix),
        "budget_reservation_ref": _ref("budget-reservation", proof_suffix),
        "budget_settlement_ref": _ref("budget-settlement", proof_suffix),
        "evidence_refs": list(evidence_refs),
        "reason_refs": [],
    }
    return ExternalActionReceipt(
        receipt_ref=stable_governed_browser_ref(
            "receipt-ref:governed-external-action",
            payload,
        ),
        **payload,
        replayed=replayed,
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


def _context_fixture(
    suffix: str = "clean",
) -> tuple[
    _FakeKernel,
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
    kernel = _FakeKernel(request, terminal)
    context = build_external_action_replay_validation_context(
        kernel,
        expected_execution=request,
        replay_receipt=replay,
        expectation=_expectation(evidence_refs),
    )
    return kernel, replay, context


def test_clean_proof_calls_both_lookups_and_builds_deterministic_envelope() -> None:
    kernel, replay, context = _context_fixture()

    authenticated = require_external_action_replay_provenance(
        replay_validation_context(context),
        lane_ref=LANE_REF,
        operation_ref=OPERATION_REF,
        candidate=replay,
    )

    assert authenticated is context
    assert kernel.replay_calls == 1
    assert kernel.terminal_calls == 1
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
def test_missing_or_wrong_context_fails_closed(invalid_context: object) -> None:
    _, replay, _ = _context_fixture("context")

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
) -> None:
    _, replay, context = _context_fixture("wrong-scope")

    with pytest.raises(ValueError, match=error):
        require_external_action_replay_provenance(
            replay_validation_context(context),
            lane_ref=lane_ref,
            operation_ref=operation_ref,
            candidate=replay,
        )


def test_expected_request_fingerprint_mismatch_fails_closed() -> None:
    request = _request("fingerprint-a")
    other_request = _request("fingerprint-b")
    terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "fingerprint"),),
        proof_suffix="fingerprint",
    )
    kernel = _FakeKernel(request, terminal)

    with pytest.raises(ValueError, match="PROVENANCE_TERMINAL_REQUIRED"):
        build_external_action_replay_validation_context(
            kernel,
            expected_execution=other_request,
            replay_receipt=terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(terminal.evidence_refs),
        )
    assert kernel.replay_calls == 1
    assert kernel.terminal_calls == 1


def test_authenticated_context_rejects_recomputed_wrong_request_fingerprint() -> None:
    _, replay, context = _context_fixture("context-fingerprint")
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

    with pytest.raises(ValueError, match="PROVENANCE_REQUEST_MISMATCH"):
        require_external_action_replay_provenance(
            replay_validation_context(context),
            lane_ref=LANE_REF,
            operation_ref=OPERATION_REF,
            candidate=replay,
        )


def test_cross_transaction_substitution_fails_closed() -> None:
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
    kernel = _FakeKernel(request_a, terminal_a)

    with pytest.raises(ValueError, match="PROVENANCE_TERMINAL_REQUIRED"):
        build_external_action_replay_validation_context(
            kernel,
            expected_execution=request_a,
            replay_receipt=terminal_b.model_copy(update={"replayed": True}),
            expectation=_expectation(terminal_a.evidence_refs),
        )
    assert kernel.replay_calls == 1
    assert kernel.terminal_calls == 1


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
    kernel = _FakeKernel(request, forged_terminal)

    with pytest.raises(ValueError, match="PROVENANCE_EVIDENCE_MISMATCH"):
        build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=forged_terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(expected_evidence),
        )
    assert kernel.replay_calls == 1
    assert kernel.terminal_calls == 1


def test_forged_context_object_and_dict_fail_closed() -> None:
    _, replay, _ = _context_fixture("forged-context")
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


def test_terminal_receipt_must_not_be_marked_replayed() -> None:
    request = _request("terminal-replay-flag")
    replayed_terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "terminal-replay-flag"),),
        proof_suffix="terminal-replay-flag",
        replayed=True,
    )
    kernel = _FakeKernel(
        request,
        replayed_terminal,
        replay_override=replayed_terminal,
    )

    with pytest.raises(ValueError, match="PROVENANCE_REPLAY_STATE_INVALID"):
        build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=replayed_terminal,
            expectation=_expectation(replayed_terminal.evidence_refs),
        )
    assert kernel.replay_calls == 1
    assert kernel.terminal_calls == 1


def test_exact_full_candidate_mismatch_fails_even_with_valid_recomputed_hash() -> None:
    _, replay, context = _context_fixture("candidate-mismatch")
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
