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
    _bounded_external_action_reason_refs,
    _register_external_action_kernel_replay_source,
)


LANE_REF = "replay-lane-ref:governed-browser:test"
OPERATION_REF = "replay-operation-ref:governed-browser:test"
APPROVAL_VALIDATION_REF = stable_governed_browser_ref(
    "approval-validation-ref:governed-external-action",
    {"test": "blocked-provenance"},
)
AUTHORITY_DECISION_REF = f"authority-policy-decision-ref:sha256:{'a' * 24}"


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
        "approval_validation_ref": APPROVAL_VALIDATION_REF,
        "authority_decision_ref": AUTHORITY_DECISION_REF,
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


def _blocked_receipt(
    request: ExternalActionExecutionRequest,
    *,
    reason_refs: tuple[str, ...],
    approval_validation_ref: str | None,
    authority_decision_ref: str | None,
    budget_reservation_ref: str | None = None,
    budget_release_ref: str | None = None,
) -> ExternalActionReceipt:
    return _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(),
            proof_suffix="blocked-provenance",
            state=ExternalActionState.blocked,
            reason_refs=reason_refs,
        ),
        approval_validation_ref=approval_validation_ref,
        authority_decision_ref=authority_decision_ref,
        budget_reservation_ref=budget_reservation_ref,
        budget_release_ref=budget_release_ref,
        budget_settlement_ref=None,
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
    record_terminal_binding: bool = True,
) -> GovernedExternalActionKernel:
    store = ExternalActionTransactionStore(tmp_path / f"{database_name}.sqlite3")
    state, prior = store.prepare(request)
    assert state == ExternalActionState.prepared
    assert prior is None
    if record_terminal_binding:
        store.finish(terminal, expected_state=ExternalActionState.prepared)
    else:
        with store._lock, store._connect() as connection:
            connection.execute(
                "UPDATE governed_external_actions "
                "SET state = ?, receipt_json = ? WHERE transaction_ref = ?",
                (
                    terminal.state,
                    ExternalActionReceipt.model_dump_json(terminal),
                    terminal.transaction_ref,
                ),
            )
            connection.commit()
    kernel = object.__new__(GovernedExternalActionKernel)
    kernel._store = store
    _register_external_action_kernel_replay_source(
        kernel,
        store=store,
    )
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
    assert context.envelope.terminal_binding_ref.startswith(
        "terminal-binding-ref:governed-browser:sha256:"
    )
    assert context.envelope.terminal_receipt_ref == replay.receipt_ref
    assert context.envelope.terminal_transaction_ref == replay.transaction_ref
    reparsed = ExternalActionReplayEvidenceEnvelope.model_validate(
        context.envelope.model_dump(mode="json")
    )
    assert reparsed == context.envelope


def test_clean_generic_ambiguity_replay_requires_terminal_binding(
    tmp_path: Path,
) -> None:
    request = _request("clean-generic-ambiguity")
    evidence_suffix = "dispatch-timeout"
    evidence_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:dispatch-timeout",
        {
            "reason": evidence_suffix,
            "transaction_ref": request.binding.transaction_ref,
            "intent_ref": request.intent_ref,
            "binding_ref": request.binding.binding_ref,
        },
    )
    terminal = _receipt(
        request,
        evidence_refs=(evidence_ref,),
        proof_suffix="clean-generic-ambiguity",
        state=ExternalActionState.outcome_ambiguous,
        reason_refs=(
            "reason-ref:governed-external-action:dispatch-timeout",
        ),
    )
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request,
        terminal=terminal,
        database_name="clean-generic-ambiguity",
    )

    context = _build_external_action_replay_validation_context(
        kernel,
        expected_execution=request,
        replay_receipt=terminal.model_copy(update={"replayed": True}),
        expectation=_expectation((evidence_ref,)),
    )

    assert context.envelope.operation_proof_ref is None
    assert context.envelope.terminal_binding_ref.startswith(
        "terminal-binding-ref:governed-browser:sha256:"
    )


def test_legacy_terminal_without_binding_fails_closed(tmp_path: Path) -> None:
    request = _request("legacy-terminal-binding-missing")
    terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "legacy-terminal"),),
        proof_suffix="legacy-terminal-binding-missing",
    )
    kernel = _concrete_kernel_with_terminal(
        tmp_path,
        request=request,
        terminal=terminal,
        database_name="legacy-terminal-binding-missing",
        record_terminal_binding=False,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(terminal.evidence_refs),
        )


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
        record_terminal_binding=False,
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


@pytest.mark.parametrize(
    "updates",
    [
        {
            "approval_validation_ref": stable_governed_browser_ref(
                "approval-validation-ref:governed-external-action",
                {"test": "same-shape-substitution"},
            )
        },
        {
            "authority_decision_ref": (
                f"authority-policy-decision-ref:sha256:{'b' * 24}"
            )
        },
        {
            "budget_reservation_ref": _ref(
                "budget-reservation",
                "same-shape-substitution",
            )
        },
        {
            "budget_settlement_ref": _ref(
                "budget-settlement",
                "same-shape-substitution",
            )
        },
        {
            "evidence_refs": (
                _ref("evidence", "terminal-binding-one"),
                _ref("evidence", "same-shape-substitution"),
            )
        },
    ],
    ids=[
        "approval-validation",
        "authority-decision",
        "budget-reservation",
        "budget-settlement",
        "operation-evidence",
    ],
)
def test_exact_terminal_binding_rejects_same_shape_proof_substitution(
    updates: dict[str, object],
    tmp_path: Path,
) -> None:
    _, replay, context = _context_fixture(tmp_path, "terminal-binding")
    forged = _rehash_receipt(replay, **updates).model_copy(
        update={"replayed": True}
    )

    with pytest.raises(ValueError, match="PROVENANCE_RECEIPT_MISMATCH"):
        require_external_action_replay_provenance(
            replay_validation_context(context),
            lane_ref=LANE_REF,
            operation_ref=OPERATION_REF,
            candidate=forged,
        )


@pytest.mark.parametrize(
    ("field_name", "mutated_value"),
    [
        (
            "lane_ref",
            "replay-lane-ref:governed-browser:mutated",
        ),
        (
            "operation_ref",
            "replay-operation-ref:governed-browser:mutated",
        ),
        (
            "scope_refs",
            ("replay-scope-ref:governed-browser:mutated",),
        ),
        (
            "evidence_refs",
            (
                _ref("evidence", "envelope-fields-one"),
                _ref("evidence", "mutated"),
            ),
        ),
        (
            "operation_proof_ref",
            _ref("evidence", "envelope-fields-two"),
        ),
        (
            "expected_request_fingerprint_ref",
            _ref("request-fingerprint", "mutated"),
        ),
        (
            "terminal_binding_ref",
            _ref("terminal-binding", "mutated"),
        ),
        (
            "terminal_receipt_ref",
            _ref("receipt", "mutated"),
        ),
        (
            "terminal_transaction_ref",
            _ref("transaction", "mutated"),
        ),
    ],
    ids=[
        "lane",
        "operation",
        "scope",
        "evidence",
        "operation-proof",
        "request-fingerprint",
        "terminal-binding",
        "terminal-receipt",
        "terminal-transaction",
    ],
)
def test_recomputed_envelope_hash_cannot_rebind_any_provenance_field(
    field_name: str,
    mutated_value: object,
    tmp_path: Path,
) -> None:
    _, _, context = _context_fixture(tmp_path, "envelope-fields")
    forged_payload = context.envelope.model_dump(mode="json")
    forged_payload[field_name] = mutated_value
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


class _ExplodingContextManager:
    def __enter__(self) -> object:
        raise AssertionError("instance shadow must not execute")

    def __exit__(self, *_args: object) -> None:
        return None


def test_concrete_store_attestation_ignores_connector_and_lock_shadows(
    tmp_path: Path,
) -> None:
    kernel, replay, _ = _context_fixture(tmp_path, "store-shadow")
    kernel._store._connect = lambda: (_ for _ in ()).throw(
        AssertionError("shadow connector executed")
    )
    kernel._store._lock = _ExplodingContextManager()
    kernel._store.attest_terminal_replay = (
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("shadow attestor executed")
        )
    )

    context = _build_external_action_replay_validation_context(
        kernel,
        expected_execution=_request("store-shadow"),
        replay_receipt=replay,
        expectation=_expectation(replay.evidence_refs),
    )

    assert context.terminal_receipt.receipt_ref == replay.receipt_ref


def test_connector_shadow_cannot_redirect_attestation_to_another_ledger(
    tmp_path: Path,
) -> None:
    request = _request("connector-redirect")
    terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "connector-redirect"),),
        proof_suffix="connector-redirect",
    )
    real_store = ExternalActionTransactionStore(tmp_path / "real.sqlite3")
    real_store.prepare(request)
    fake_store = ExternalActionTransactionStore(tmp_path / "fake.sqlite3")
    fake_store.prepare(request)
    fake_store.finish(terminal, expected_state=ExternalActionState.prepared)
    kernel = object.__new__(GovernedExternalActionKernel)
    kernel._store = real_store
    _register_external_action_kernel_replay_source(kernel, store=real_store)
    real_store._connect = fake_store._connect

    with pytest.raises(ValueError, match="TERMINAL_REQUIRED"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=terminal.model_copy(update={"replayed": True}),
            expectation=_expectation(terminal.evidence_refs),
        )


def test_store_path_or_whole_store_substitution_fails_closed(
    tmp_path: Path,
) -> None:
    request = _request("source-substitution")
    terminal = _receipt(
        request,
        evidence_refs=(_ref("evidence", "source-substitution"),),
        proof_suffix="source-substitution",
    )
    real_store = ExternalActionTransactionStore(tmp_path / "real.sqlite3")
    real_store.prepare(request)
    fake_store = ExternalActionTransactionStore(tmp_path / "fake.sqlite3")
    fake_store.prepare(request)
    fake_store.finish(terminal, expected_state=ExternalActionState.prepared)
    kernel = object.__new__(GovernedExternalActionKernel)
    kernel._store = real_store
    _register_external_action_kernel_replay_source(kernel, store=real_store)
    replay = terminal.model_copy(update={"replayed": True})

    real_store.path = fake_store.path
    with pytest.raises(ValueError, match="PROVENANCE_SOURCE_INVALID"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=replay,
            expectation=_expectation(terminal.evidence_refs),
        )

    real_store.path = tmp_path / "real.sqlite3"
    kernel._store = fake_store
    with pytest.raises(ValueError, match="PROVENANCE_SOURCE_INVALID"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=replay,
            expectation=_expectation(terminal.evidence_refs),
        )


def test_concrete_serializers_ignore_request_replay_and_expectation_shadows(
    tmp_path: Path,
) -> None:
    kernel, replay, _ = _context_fixture(tmp_path, "serializer-shadow")
    exact_request = _request("serializer-shadow")

    wrong_request = _request("serializer-shadow-wrong")
    object.__setattr__(
        wrong_request,
        "model_dump",
        lambda *_args, **_kwargs: ExternalActionExecutionRequest.model_dump(
            exact_request,
            mode="json",
        ),
    )
    with pytest.raises(ValueError, match="TERMINAL_REQUIRED"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=wrong_request,
            replay_receipt=replay,
            expectation=_expectation(replay.evidence_refs),
        )

    forged_replay = _rehash_receipt(
        replay,
        evidence_refs=(_ref("evidence", "forged-replay"),),
    ).model_copy(update={"replayed": True})
    object.__setattr__(
        forged_replay,
        "model_dump",
        lambda *_args, **_kwargs: ExternalActionReceipt.model_dump(
            replay,
            mode="json",
        ),
    )
    with pytest.raises(ValueError, match="PROVENANCE_LOOKUP_FAILED"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=exact_request,
            replay_receipt=forged_replay,
            expectation=_expectation(replay.evidence_refs),
        )

    forged_expectation = _expectation(
        (_ref("evidence", "forged-expectation"),)
    )
    legitimate_expectation = _expectation(replay.evidence_refs)
    object.__setattr__(
        forged_expectation,
        "model_dump",
        lambda *_args, **_kwargs: (
            ExternalActionReplayEvidenceExpectation.model_dump(
                legitimate_expectation,
                mode="json",
            )
        ),
    )
    with pytest.raises(ValueError, match="PROVENANCE_EVIDENCE_MISMATCH"):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=exact_request,
            replay_receipt=replay,
            expectation=forged_expectation,
        )


def test_candidate_model_dump_shadow_cannot_bypass_whole_receipt_match(
    tmp_path: Path,
) -> None:
    _, replay, context = _context_fixture(tmp_path, "candidate-shadow")
    forged = _rehash_receipt(
        replay,
        evidence_refs=(_ref("evidence", "candidate-forged"),),
    ).model_copy(update={"replayed": True})
    object.__setattr__(
        forged,
        "model_dump",
        lambda *_args, **_kwargs: ExternalActionReceipt.model_dump(
            replay,
            mode="json",
        ),
    )

    with pytest.raises(ValueError, match="PROVENANCE_RECEIPT_MISMATCH"):
        require_external_action_replay_provenance(
            replay_validation_context(context),
            lane_ref=LANE_REF,
            operation_ref=OPERATION_REF,
            candidate=forged,
        )


@pytest.mark.parametrize(
    "snapshot_name",
    ["envelope", "expected_execution", "terminal_receipt"],
)
def test_context_model_dump_json_shadow_cannot_hide_snapshot_mutation(
    snapshot_name: str,
    tmp_path: Path,
) -> None:
    _, _, context = _context_fixture(
        tmp_path,
        f"context-serializer-{snapshot_name}",
    )
    snapshot = getattr(context, snapshot_name)
    exact_type = type(snapshot)
    original_json = exact_type.model_dump_json(snapshot)
    mutated_field = {
        "envelope": ("lane_ref", _ref("lane", "mutated")),
        "expected_execution": ("task_ref", _ref("task", "mutated")),
        "terminal_receipt": (
            "evidence_refs",
            (_ref("evidence", "mutated"),),
        ),
    }[snapshot_name]
    object.__setattr__(snapshot, mutated_field[0], mutated_field[1])
    object.__setattr__(
        snapshot,
        "model_dump_json",
        lambda *_args, **_kwargs: original_json,
    )

    with pytest.raises(ValueError, match="PROVENANCE_CONTEXT_INVALID"):
        replay_validation_context(context)


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
        (
            ExternalActionState.blocked,
            "empty",
            False,
            False,
            (
                "reason-ref:governed-external-action:"
                "local-validation-disabled",
            ),
        ),
        (
            ExternalActionState.outcome_ambiguous,
            "lane",
            True,
            False,
            (
                "reason-ref:governed-external-action:"
                "budget-settlement-ambiguous",
            ),
        ),
        (
            ExternalActionState.outcome_ambiguous,
            "lane",
            False,
            True,
            (
                "reason-ref:governed-external-action:"
                "budget-settlement-ambiguous",
            ),
        ),
        (
            ExternalActionState.outcome_ambiguous,
            "kernel",
            False,
            False,
            (
                "reason-ref:governed-external-action:dispatch-timeout",
            ),
        ),
        (
            ExternalActionState.outcome_ambiguous,
            "guard",
            False,
            False,
            (
                "reason-ref:governed-external-action:"
                "post-start-revalidation-denied",
                "reason-ref:governed-external-action:deadline-expired",
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
            stable_governed_browser_ref(
                "evidence-ref:governed-external-action:post-start-guard",
                {
                    "intent_ref": request.intent_ref,
                    "reason_refs": list(reason_refs),
                },
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
    if (
        state == ExternalActionState.outcome_ambiguous
        and evidence_kind == "lane"
    ):
        receipt = _rehash_receipt(receipt, budget_settlement_ref=None)
    elif state == ExternalActionState.blocked:
        receipt = _rehash_receipt(
            receipt,
            approval_validation_ref=None,
            authority_decision_ref=None,
            budget_reservation_ref=None,
            budget_settlement_ref=None,
        )
    elif evidence_kind == "guard":
        receipt = _rehash_receipt(
            receipt,
            budget_release_ref=_ref("budget-release", "guard"),
            budget_settlement_ref=None,
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
    ("evidence_suffix", "required_reason_ref"),
    [
        (
            "dispatch-capacity-check-failed",
            "reason-ref:governed-external-action:"
            "dispatch-capacity-check-failed",
        ),
        (
            "dispatch-capacity-bounded",
            "reason-ref:governed-external-action:dispatch-capacity-bounded",
        ),
        (
            "dispatch-start-revalidation-denied",
            "reason-ref:governed-external-action:"
            "post-start-revalidation-denied",
        ),
        (
            "dispatch-timeout",
            "reason-ref:governed-external-action:dispatch-timeout",
        ),
        (
            "dispatch-exception",
            "reason-ref:governed-external-action:dispatch-exception",
        ),
        (
            "dispatch-result-invalid",
            "reason-ref:governed-external-action:dispatch-result-invalid",
        ),
        (
            "dispatch-worker-start-failed",
            "reason-ref:governed-external-action:"
            "dispatch-worker-start-failed",
        ),
        (
            "prior-start-recovery",
            "reason-ref:governed-external-action:prior-start-unsettled",
        ),
    ],
)
def test_kernel_ambiguity_evidence_requires_its_exact_primary_reason(
    evidence_suffix: str,
    required_reason_ref: str,
) -> None:
    request = _request(f"ambiguity-reason-{evidence_suffix}")
    common_payload = {
        "transaction_ref": request.binding.transaction_ref,
        "intent_ref": request.intent_ref,
        "binding_ref": request.binding.binding_ref,
    }
    evidence_ref = stable_governed_browser_ref(
        f"evidence-ref:governed-external-action:{evidence_suffix}",
        (
            common_payload
            if evidence_suffix == "prior-start-recovery"
            else {"reason": evidence_suffix, **common_payload}
        ),
    )
    valid = _receipt(
        request,
        evidence_refs=(evidence_ref,),
        proof_suffix=f"ambiguity-reason-{evidence_suffix}",
        state=ExternalActionState.outcome_ambiguous,
        reason_refs=(required_reason_ref,),
    )
    if evidence_suffix in {
        "dispatch-capacity-check-failed",
        "dispatch-capacity-bounded",
    }:
        valid = _rehash_receipt(
            valid,
            budget_reservation_ref=None,
            budget_settlement_ref=None,
        )
    elif evidence_suffix == "prior-start-recovery":
        valid = _rehash_receipt(
            valid,
            approval_validation_ref=None,
            authority_decision_ref=None,
        )
    elif evidence_suffix in {
        "dispatch-start-revalidation-denied",
        "dispatch-worker-start-failed",
    }:
        valid = _rehash_receipt(
            valid,
            reason_refs=(
                (
                    required_reason_ref,
                    "reason-ref:governed-external-action:deadline-expired",
                )
                if evidence_suffix == "dispatch-start-revalidation-denied"
                else (required_reason_ref,)
            ),
            budget_release_ref=_ref(
                "budget-release",
                f"ambiguity-reason-{evidence_suffix}",
            ),
            budget_settlement_ref=None,
        )
    _require_operation_replay_evidence_envelope(
        valid,
        success_evidence_valid=False,
        failure_evidence_valid=False,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )

    for tampered_reasons in (
        (),
        ("reason-ref:governed-external-action:unrelated",),
        (
            "reason-ref:governed-external-action:unrelated",
            required_reason_ref,
        ),
    ):
        tampered = _rehash_receipt(valid, reason_refs=tampered_reasons)
        with pytest.raises(
            ValueError,
            match="TEST_REPLAY_EVIDENCE_MISMATCH",
        ):
            _require_operation_replay_evidence_envelope(
                tampered,
                success_evidence_valid=False,
                failure_evidence_valid=False,
                mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
            )


@pytest.mark.parametrize(
    "primary_reason_ref",
    [
        "reason-ref:governed-external-action:"
        "post-start-revalidation-denied",
        "reason-ref:governed-external-action:"
        "dispatch-wait-interrupted-before-start",
    ],
)
def test_post_start_guard_replay_recomputes_the_complete_reason_envelope(
    primary_reason_ref: str,
) -> None:
    request = _request(f"guard-envelope-{primary_reason_ref.rsplit(':', 1)[-1]}")
    reason_refs = (
        primary_reason_ref,
        *(
            ("reason-ref:governed-external-action:deadline-expired",)
            if primary_reason_ref.endswith("post-start-revalidation-denied")
            else ()
        ),
        "reason-ref:governed-external-action:budget-release-failed",
        "reason-ref:governed-external-action:budget-release-unconfirmed",
    )
    evidence_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:post-start-guard",
        {
            "intent_ref": request.intent_ref,
            "reason_refs": list(reason_refs),
        },
    )
    valid = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(evidence_ref,),
            proof_suffix="guard-envelope",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=reason_refs,
        ),
        budget_settlement_ref=None,
    )
    _require_operation_replay_evidence_envelope(
        valid,
        success_evidence_valid=False,
        failure_evidence_valid=False,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )

    tampered_receipts = (
        _rehash_receipt(
            valid,
            evidence_refs=(
                "evidence-ref:governed-external-action:"
                f"post-start-guard:sha256:{'a' * 64}",
            ),
        ),
        _rehash_receipt(valid, intent_ref=_ref("intent", "guard-wrong")),
        _rehash_receipt(valid, reason_refs=reason_refs[:-1]),
        _rehash_receipt(
            valid,
            reason_refs=(reason_refs[1], reason_refs[0], *reason_refs[2:]),
        ),
        _rehash_receipt(
            valid,
            reason_refs=(
                "reason-ref:governed-external-action:unrelated",
                *reason_refs[1:],
            ),
        ),
        _rehash_receipt(
            valid,
            budget_release_ref=_ref("budget-release", "inconsistent"),
        ),
    )
    for tampered in tampered_receipts:
        with pytest.raises(
            ValueError,
            match="TEST_REPLAY_EVIDENCE_MISMATCH",
        ):
            _require_operation_replay_evidence_envelope(
                tampered,
                success_evidence_valid=False,
                failure_evidence_valid=False,
                mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
            )


def test_post_start_guard_overflow_uses_the_exact_bounded_reason_envelope() -> None:
    request = _request("guard-overflow")
    reasons = [
        "reason-ref:governed-external-action:"
        "post-start-revalidation-denied",
        *[
            stable_governed_browser_ref(
                "reason-ref:governed-external-action:adversarial",
                {"index": index},
            )
            for index in range(20)
        ],
        "reason-ref:governed-external-action:budget-release-unconfirmed",
    ]
    bounded = _bounded_external_action_reason_refs(request, reasons)
    assert len(bounded) == 16
    evidence_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:post-start-guard",
        {
            "intent_ref": request.intent_ref,
            "reason_refs": bounded,
        },
    )
    receipt = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(evidence_ref,),
            proof_suffix="guard-overflow",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=tuple(bounded),
        ),
        budget_settlement_ref=None,
    )
    _require_operation_replay_evidence_envelope(
        receipt,
        success_evidence_valid=False,
        failure_evidence_valid=False,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )


@pytest.mark.parametrize(
    ("source_state", "success_valid", "failure_valid"),
    [
        (ExternalActionState.succeeded, True, False),
        (ExternalActionState.failed, False, True),
    ],
)
def test_lane_evidence_cannot_change_to_ambiguous_without_transition_proof(
    source_state: ExternalActionState,
    success_valid: bool,
    failure_valid: bool,
) -> None:
    request = _request(f"lane-state-drift-{source_state.value}")
    original = _receipt(
        request,
        evidence_refs=(_ref("evidence", f"lane-{source_state.value}"),),
        proof_suffix=f"lane-state-drift-{source_state.value}",
        state=source_state,
    )
    forged = _rehash_receipt(
        original,
        state=ExternalActionState.outcome_ambiguous.value,
    )
    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
            success_evidence_valid=success_valid,
            failure_evidence_valid=failure_valid,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


@pytest.mark.parametrize(
    ("reason_refs", "settlement_ref"),
    [
        (
            (
                "reason-ref:governed-external-action:"
                "budget-settlement-ambiguous",
            ),
            None,
        ),
        (
            (
                "reason-ref:governed-external-action:"
                "post-dispatch-revalidation-denied",
                "reason-ref:governed-external-action:deadline-expired",
            ),
            _ref("budget-settlement", "post-dispatch"),
        ),
    ],
)
def test_lane_ambiguity_requires_an_exact_transition_and_accounting_shape(
    reason_refs: tuple[str, ...],
    settlement_ref: str | None,
) -> None:
    request = _request(
        f"lane-ambiguity-{reason_refs[0].rsplit(':', 1)[-1]}"
    )
    valid = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(_ref("evidence", "lane-ambiguity"),),
            proof_suffix="lane-ambiguity",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=reason_refs,
        ),
        budget_settlement_ref=settlement_ref,
    )
    _require_operation_replay_evidence_envelope(
        valid,
        success_evidence_valid=True,
        failure_evidence_valid=False,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )

    inconsistent = _rehash_receipt(
        valid,
        budget_release_ref=_ref("budget-release", "unexpected"),
        budget_settlement_ref=None,
    )
    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            inconsistent,
            success_evidence_valid=True,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


def test_post_dispatch_ambiguity_requires_a_concrete_revalidation_reason() -> None:
    request = _request("post-dispatch-reason-required")
    receipt = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(_ref("evidence", "post-dispatch"),),
            proof_suffix="post-dispatch-reason-required",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=(
                "reason-ref:governed-external-action:"
                "post-dispatch-revalidation-denied",
            ),
        ),
        budget_settlement_ref=_ref(
            "budget-settlement",
            "post-dispatch-reason-required",
        ),
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            receipt,
            success_evidence_valid=True,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


def test_operation_specific_ambiguity_requires_explicit_classification() -> None:
    request = _request("operation-ambiguity")
    receipt = _receipt(
        request,
        evidence_refs=(_ref("evidence", "operation-ambiguity"),),
        proof_suffix="operation-ambiguity",
        state=ExternalActionState.outcome_ambiguous,
        reason_refs=(
            "reason-ref:governed-external-action:"
            "dispatch-outcome-ambiguous",
        ),
    )
    _require_operation_replay_evidence_envelope(
        receipt,
        success_evidence_valid=False,
        failure_evidence_valid=False,
        operation_ambiguity_evidence_valid=True,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )
    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            receipt,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


@pytest.mark.parametrize(
    ("updates", "valid"),
    [
        ({}, True),
        (
            {
                "budget_settlement_ref": None,
                "reason_refs": (
                    "reason-ref:governed-external-action:"
                    "dispatch-outcome-ambiguous",
                    "reason-ref:governed-external-action:"
                    "budget-settlement-ambiguous",
                ),
            },
            True,
        ),
        ({"budget_settlement_ref": None}, False),
        ({"budget_reservation_ref": None}, False),
        (
            {
                "budget_release_ref": _ref(
                    "budget-release",
                    "operation-ambiguity-invalid",
                ),
                "budget_settlement_ref": None,
            },
            False,
        ),
    ],
    ids=[
        "settled",
        "settlement-ambiguous",
        "missing-settlement-proof",
        "missing-reservation",
        "release-is-not-settlement",
    ],
)
def test_operation_ambiguity_requires_exact_settlement_provenance(
    updates: dict[str, object],
    valid: bool,
) -> None:
    request = _request("operation-ambiguity-settlement")
    receipt = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(_ref("evidence", "operation-ambiguity"),),
            proof_suffix="operation-ambiguity-settlement",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=(
                "reason-ref:governed-external-action:"
                "dispatch-outcome-ambiguous",
            ),
        ),
        **updates,
    )

    def validate() -> None:
        _require_operation_replay_evidence_envelope(
            receipt,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            operation_ambiguity_evidence_valid=True,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )

    if valid:
        validate()
    else:
        with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
            validate()


@pytest.mark.parametrize(
    ("updates", "valid"),
    [
        ({}, True),
        (
            {
                "budget_settlement_ref": None,
                "reason_refs": (
                    "reason-ref:governed-external-action:dispatch-timeout",
                    "reason-ref:governed-external-action:"
                    "budget-settlement-ambiguous",
                ),
            },
            True,
        ),
        ({"budget_settlement_ref": None}, False),
        ({"budget_reservation_ref": None}, False),
        (
            {
                "budget_release_ref": _ref(
                    "budget-release",
                    "lane-timeout-invalid",
                ),
                "budget_settlement_ref": None,
            },
            False,
        ),
    ],
    ids=[
        "settled",
        "settlement-ambiguous",
        "missing-settlement-proof",
        "missing-reservation",
        "release-is-not-settlement",
    ],
)
def test_exact_lane_timeout_requires_settlement_not_release(
    updates: dict[str, object],
    valid: bool,
) -> None:
    request = _request("lane-timeout-settlement")
    receipt = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(_ref("evidence", "exact-lane-timeout-proof"),),
            proof_suffix="lane-timeout-settlement",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=(
                "reason-ref:governed-external-action:dispatch-timeout",
            ),
        ),
        **updates,
    )
    def validate() -> None:
        _require_operation_replay_evidence_envelope(
            receipt,
            success_evidence_valid=True,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )

    if valid:
        validate()
    else:
        with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
            validate()


def test_late_operation_ambiguity_timeout_accepts_exact_evidence() -> None:
    receipt = _receipt(
        _request("late-operation-ambiguity-timeout"),
        evidence_refs=(_ref("evidence", "late-operation-ambiguity-timeout"),),
        proof_suffix="late-operation-ambiguity-timeout",
        state=ExternalActionState.outcome_ambiguous,
        reason_refs=(
            "reason-ref:governed-external-action:dispatch-timeout",
        ),
    )

    _require_operation_replay_evidence_envelope(
        receipt,
        success_evidence_valid=False,
        failure_evidence_valid=False,
        operation_ambiguity_evidence_valid=True,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            receipt,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            operation_ambiguity_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


@pytest.mark.parametrize(
    ("evidence_suffix", "reason_ref", "accounting", "tamper"),
    [
        (
            "dispatch-exception",
            "reason-ref:governed-external-action:dispatch-exception",
            "settlement",
            {"budget_settlement_ref": None},
        ),
        (
            "dispatch-result-invalid",
            "reason-ref:governed-external-action:dispatch-result-invalid",
            "settlement",
            {"budget_reservation_ref": None},
        ),
        (
            "dispatch-worker-start-failed",
            (
                "reason-ref:governed-external-action:"
                "dispatch-worker-start-failed"
            ),
            "release",
            {"budget_release_ref": None},
        ),
        (
            "dispatch-start-revalidation-denied",
            (
                "reason-ref:governed-external-action:"
                "post-start-revalidation-denied"
            ),
            "release",
            {"budget_reservation_ref": None},
        ),
    ],
)
def test_kernel_ambiguity_rejects_missing_accounting_provenance(
    evidence_suffix: str,
    reason_ref: str,
    accounting: str,
    tamper: dict[str, object],
) -> None:
    request = _request(f"kernel-accounting-{evidence_suffix}")
    reason_refs = (
        (
            reason_ref,
            "reason-ref:governed-external-action:deadline-expired",
        )
        if evidence_suffix == "dispatch-start-revalidation-denied"
        else (reason_ref,)
    )
    evidence_ref = stable_governed_browser_ref(
        f"evidence-ref:governed-external-action:{evidence_suffix}",
        {
            "reason": evidence_suffix,
            "transaction_ref": request.binding.transaction_ref,
            "intent_ref": request.intent_ref,
            "binding_ref": request.binding.binding_ref,
        },
    )
    valid = _receipt(
        request,
        evidence_refs=(evidence_ref,),
        proof_suffix=f"kernel-accounting-{evidence_suffix}",
        state=ExternalActionState.outcome_ambiguous,
        reason_refs=reason_refs,
    )
    if accounting == "release":
        valid = _rehash_receipt(
            valid,
            budget_release_ref=_ref(
                "budget-release",
                f"kernel-accounting-{evidence_suffix}",
            ),
            budget_settlement_ref=None,
        )
    _require_operation_replay_evidence_envelope(
        valid,
        success_evidence_valid=False,
        failure_evidence_valid=False,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )

    forged = _rehash_receipt(valid, **tamper)
    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


@pytest.mark.parametrize(
    "tampered_reasons",
    [
        (
            "reason-ref:governed-external-action:"
            "post-dispatch-revalidation-denied",
            "reason-ref:governed-external-action:deadline-expired",
            "reason-ref:governed-external-action:"
            "budget-settlement-ambiguous",
            "reason-ref:governed-external-action:safe-disable-active",
        ),
        (
            "reason-ref:governed-external-action:"
            "post-dispatch-revalidation-denied",
            "reason-ref:governed-external-action:"
            "budget-settlement-ambiguous",
            "reason-ref:governed-external-action:deadline-expired",
        ),
    ],
    ids=["trailing-reason", "marker-reordered"],
)
def test_settlement_ambiguity_marker_must_be_terminal(
    tampered_reasons: tuple[str, ...],
) -> None:
    request = _request("settlement-marker-terminal")
    valid = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(_ref("evidence", "settlement-marker"),),
            proof_suffix="settlement-marker-terminal",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=(
                "reason-ref:governed-external-action:"
                "post-dispatch-revalidation-denied",
                "reason-ref:governed-external-action:deadline-expired",
                "reason-ref:governed-external-action:"
                "budget-settlement-ambiguous",
            ),
        ),
        budget_settlement_ref=None,
    )
    _require_operation_replay_evidence_envelope(
        valid,
        success_evidence_valid=True,
        failure_evidence_valid=False,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )

    forged = _rehash_receipt(valid, reason_refs=tampered_reasons)
    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
            success_evidence_valid=True,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


@pytest.mark.parametrize(
    "state",
    [ExternalActionState.succeeded, ExternalActionState.failed],
)
@pytest.mark.parametrize(
    "updates",
    [
        {"approval_validation_ref": None},
        {"authority_decision_ref": None},
        {"budget_reservation_ref": None},
        {"budget_settlement_ref": None},
        {
            "reason_refs": (
                "reason-ref:governed-external-action:unrelated",
            )
        },
    ],
    ids=[
        "approval-missing",
        "authority-missing",
        "reservation-missing",
        "settlement-missing",
        "reason-injected",
    ],
)
def test_completed_dispatch_replay_requires_complete_provenance(
    state: ExternalActionState,
    updates: dict[str, object],
) -> None:
    receipt = _rehash_receipt(
        _receipt(
            _request(f"completed-provenance-{state.value}"),
            evidence_refs=(_ref("evidence", state.value),),
            proof_suffix=f"completed-provenance-{state.value}",
            state=state,
        ),
        **updates,
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            receipt,
            success_evidence_valid=state == ExternalActionState.succeeded,
            failure_evidence_valid=state == ExternalActionState.failed,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


def test_release_ambiguity_marker_must_be_terminal() -> None:
    request = _request("release-marker-terminal")
    reason_refs = (
        "reason-ref:governed-external-action:"
        "post-start-revalidation-denied",
        "reason-ref:governed-external-action:deadline-expired",
        "reason-ref:governed-external-action:budget-release-unconfirmed",
        "reason-ref:governed-external-action:budget-release-failed",
    )
    evidence_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:post-start-guard",
        {
            "intent_ref": request.intent_ref,
            "reason_refs": list(reason_refs),
        },
    )
    forged = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(evidence_ref,),
            proof_suffix="release-marker-terminal",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=reason_refs,
        ),
        budget_settlement_ref=None,
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


def test_kernel_ambiguity_rejects_extra_reason_arity() -> None:
    request = _request("kernel-extra-reason")
    suffix = "dispatch-exception"
    evidence_ref = stable_governed_browser_ref(
        f"evidence-ref:governed-external-action:{suffix}",
        {
            "reason": suffix,
            "transaction_ref": request.binding.transaction_ref,
            "intent_ref": request.intent_ref,
            "binding_ref": request.binding.binding_ref,
        },
    )
    forged = _receipt(
        request,
        evidence_refs=(evidence_ref,),
        proof_suffix="kernel-extra-reason",
        state=ExternalActionState.outcome_ambiguous,
        reason_refs=(
            "reason-ref:governed-external-action:dispatch-exception",
            "reason-ref:governed-external-action:unrelated",
        ),
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


@pytest.mark.parametrize(
    ("reason_refs", "operation_ambiguity"),
    [
        (
            (
                "reason-ref:governed-external-action:"
                "dispatch-outcome-ambiguous",
                "reason-ref:governed-external-action:"
                "budget-settlement-failed",
                "reason-ref:governed-external-action:"
                "budget-settlement-ambiguous",
            ),
            True,
        ),
        (
            (
                "reason-ref:governed-external-action:"
                "budget-settlement-failed",
                "reason-ref:governed-external-action:"
                "budget-settlement-ambiguous",
            ),
            False,
        ),
    ],
    ids=["operation-ambiguity", "accounting-only"],
)
def test_settlement_detail_precedes_terminal_marker(
    reason_refs: tuple[str, ...],
    operation_ambiguity: bool,
) -> None:
    receipt = _rehash_receipt(
        _receipt(
            _request(f"settlement-detail-{operation_ambiguity}"),
            evidence_refs=(_ref("evidence", "settlement-detail"),),
            proof_suffix=f"settlement-detail-{operation_ambiguity}",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=reason_refs,
        ),
        budget_settlement_ref=None,
    )

    _require_operation_replay_evidence_envelope(
        receipt,
        success_evidence_valid=not operation_ambiguity,
        failure_evidence_valid=False,
        operation_ambiguity_evidence_valid=operation_ambiguity,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )


def test_release_path_rejects_settlement_detail_substitution() -> None:
    request = _request("release-cross-accounting")
    reason_refs = (
        "reason-ref:governed-external-action:"
        "dispatch-wait-interrupted-before-start",
        "reason-ref:governed-external-action:budget-settlement-failed",
        "reason-ref:governed-external-action:budget-release-unconfirmed",
    )
    evidence_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:post-start-guard",
        {
            "intent_ref": request.intent_ref,
            "reason_refs": list(reason_refs),
        },
    )
    forged = _rehash_receipt(
        _receipt(
            request,
            evidence_refs=(evidence_ref,),
            proof_suffix="release-cross-accounting",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=reason_refs,
        ),
        budget_settlement_ref=None,
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


def test_settlement_path_rejects_release_detail_substitution() -> None:
    forged = _rehash_receipt(
        _receipt(
            _request("settlement-cross-accounting"),
            evidence_refs=(_ref("evidence", "settlement-cross-accounting"),),
            proof_suffix="settlement-cross-accounting",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=(
                "reason-ref:governed-external-action:"
                "dispatch-outcome-ambiguous",
                "reason-ref:governed-external-action:budget-release-failed",
                "reason-ref:governed-external-action:"
                "budget-settlement-ambiguous",
            ),
        ),
        budget_settlement_ref=None,
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            operation_ambiguity_evidence_valid=True,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


def test_settlement_path_rejects_interleaved_lifecycle_and_accounting() -> None:
    forged = _rehash_receipt(
        _receipt(
            _request("settlement-interleaved"),
            evidence_refs=(_ref("evidence", "settlement-interleaved"),),
            proof_suffix="settlement-interleaved",
            state=ExternalActionState.outcome_ambiguous,
            reason_refs=(
                "reason-ref:governed-external-action:"
                "dispatch-outcome-ambiguous",
                "reason-ref:governed-external-action:"
                "post-dispatch-revalidation-denied",
                "reason-ref:governed-external-action:deadline-expired",
                "reason-ref:governed-external-action:"
                "budget-settlement-failed",
                "reason-ref:governed-external-action:safe-disable-active",
                "reason-ref:governed-external-action:"
                "budget-settlement-ambiguous",
            ),
        ),
        budget_settlement_ref=None,
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            operation_ambiguity_evidence_valid=True,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


def test_deny_by_default_budget_receipt_has_canonical_blocked_provenance() -> None:
    receipt = _blocked_receipt(
        _request("deny-by-default-budget"),
        reason_refs=(
            "reason-ref:governed-external-action:"
            "budget-reservation-denied",
            "reason-ref:governed-external-action:budget-gate-missing",
        ),
        approval_validation_ref=APPROVAL_VALIDATION_REF,
        authority_decision_ref=AUTHORITY_DECISION_REF,
    )

    _require_operation_replay_evidence_envelope(
        receipt,
        success_evidence_valid=False,
        failure_evidence_valid=False,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )


def test_blocked_reservation_rejects_arbitrary_secondary_reason() -> None:
    receipt = _blocked_receipt(
        _request("blocked-arbitrary-secondary"),
        reason_refs=(
            "reason-ref:governed-external-action:budget-reservation-denied",
            "reason-ref:governed-external-action:unrelated",
        ),
        approval_validation_ref=APPROVAL_VALIDATION_REF,
        authority_decision_ref=AUTHORITY_DECISION_REF,
    )

    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            receipt,
            success_evidence_valid=False,
            failure_evidence_valid=False,
            mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
        )


@pytest.mark.parametrize(
    (
        "reason_refs",
        "approval_ref",
        "authority_ref",
        "reservation_ref",
        "release_ref",
    ),
    [
        (
            (
                "reason-ref:governed-external-action:"
                "local-validation-disabled",
            ),
            None,
            None,
            None,
            None,
        ),
        (
            (
                "reason-ref:governed-external-action:approval-invalid",
                stable_governed_browser_ref(
                    "approval-reason-ref:governed-external-action",
                    {"code": "approval-missing"},
                ),
            ),
            APPROVAL_VALIDATION_REF,
            None,
            None,
            None,
        ),
        (
            ("reason-ref:governed-external-action:exact-lease-required",),
            APPROVAL_VALIDATION_REF,
            AUTHORITY_DECISION_REF,
            None,
            None,
        ),
        (
            (
                "reason-ref:governed-external-action:"
                "budget-reservation-denied",
                "reason-ref:authority-budget:operation-budget-exhausted",
            ),
            APPROVAL_VALIDATION_REF,
            AUTHORITY_DECISION_REF,
            None,
            None,
        ),
        (
            ("reason-ref:governed-external-action:safe-disable-active",),
            APPROVAL_VALIDATION_REF,
            AUTHORITY_DECISION_REF,
            _ref("budget-reservation", "blocked-released"),
            _ref("budget-release", "blocked-released"),
        ),
        (
            (
                "reason-ref:governed-external-action:safe-disable-active",
                "reason-ref:governed-external-action:budget-release-failed",
                "reason-ref:governed-external-action:"
                "budget-release-unconfirmed",
            ),
            APPROVAL_VALIDATION_REF,
            AUTHORITY_DECISION_REF,
            _ref("budget-reservation", "blocked-unconfirmed"),
            None,
        ),
    ],
)
def test_blocked_replay_accepts_only_stage_consistent_provenance(
    reason_refs: tuple[str, ...],
    approval_ref: str | None,
    authority_ref: str | None,
    reservation_ref: str | None,
    release_ref: str | None,
) -> None:
    receipt = _blocked_receipt(
        _request(f"blocked-stage-{reason_refs[0].rsplit(':', 1)[-1]}"),
        reason_refs=reason_refs,
        approval_validation_ref=approval_ref,
        authority_decision_ref=authority_ref,
        budget_reservation_ref=reservation_ref,
        budget_release_ref=release_ref,
    )
    _require_operation_replay_evidence_envelope(
        receipt,
        success_evidence_valid=False,
        failure_evidence_valid=False,
        mismatch_error="TEST_REPLAY_EVIDENCE_MISMATCH",
    )


@pytest.mark.parametrize(
    "updates",
    [
        {
            "reason_refs": (
                "reason-ref:governed-external-action:safe-disable-active",
            )
        },
        {
            "approval_validation_ref": AUTHORITY_DECISION_REF,
            "authority_decision_ref": APPROVAL_VALIDATION_REF,
        },
        {
            "reason_refs": (
                "reason-ref:governed-external-action:"
                "budget-release-unconfirmed",
                "reason-ref:governed-external-action:safe-disable-active",
            )
        },
        {"budget_settlement_ref": _ref("budget-settlement", "blocked")},
        {"reason_refs": ("reason-ref:governed-external-action:unrelated",)},
        {"evidence_refs": (_ref("evidence", "blocked"),)},
    ],
    ids=[
        "release-marker-dropped",
        "governance-refs-swapped",
        "release-marker-reordered",
        "settlement-injected",
        "reason-substituted",
        "evidence-injected",
    ],
)
def test_blocked_replay_fails_closed_on_provenance_tampering(
    updates: dict[str, object],
) -> None:
    valid = _blocked_receipt(
        _request("blocked-provenance-tampering"),
        reason_refs=(
            "reason-ref:governed-external-action:safe-disable-active",
            "reason-ref:governed-external-action:"
            "budget-release-unconfirmed",
        ),
        approval_validation_ref=APPROVAL_VALIDATION_REF,
        authority_decision_ref=AUTHORITY_DECISION_REF,
        budget_reservation_ref=_ref(
            "budget-reservation",
            "blocked-provenance-tampering",
        ),
    )
    forged = _rehash_receipt(valid, **updates)
    with pytest.raises(ValueError, match="TEST_REPLAY_EVIDENCE_MISMATCH"):
        _require_operation_replay_evidence_envelope(
            forged,
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
