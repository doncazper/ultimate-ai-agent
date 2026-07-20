from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import ultimate_ai_agent.core.governed_browser.operation_proofs as operation_proofs_module
from tests.test_governed_browser_replay_provenance import (
    _receipt,
    _ref,
    _rehash_receipt,
    _request,
)
from ultimate_ai_agent.core.governed_browser.contracts import (
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    stable_governed_browser_ref,
)
from ultimate_ai_agent.core.governed_browser.operation_proofs import (
    MAX_GOVERNED_BROWSER_OPERATION_PROOF_BYTES,
    BrowserActionPlanOperationProofMaterial,
    BrowserObservationOperationProofMaterial,
    GovernedBrowserOperationProof,
    GovernedBrowserOperationProofError,
    GovernedBrowserOperationProofStore,
    GovernedBrowserTerminalReceiptBinding,
    _attest_operation_proof,
    _operation_proof_store_for_kernel,
    _proof_filename,
    _record_operation_proof,
    _terminal_binding_filename,
)
from ultimate_ai_agent.core.governed_browser.replay_provenance import (
    ExternalActionReplayEvidenceExpectation,
    _build_external_action_replay_validation_context,
)
from ultimate_ai_agent.core.governed_browser.transaction import (
    ExternalActionTransactionStore,
    GovernedExternalActionKernel,
    _register_external_action_kernel_replay_source,
)


OBSERVATION_LANE_REF = (
    "replay-lane-ref:governed-browser-observation:v1"
)
ACTION_LANE_REF = "replay-lane-ref:governed-browser-action:v1"
OBSERVATION_OPERATION_REF = (
    "replay-operation-ref:governed-browser-observation:test"
)
ACTION_OPERATION_REF = (
    "replay-operation-ref:governed-browser-action:test"
)
SCOPE_REFS = ("recipe-ref:governed-browser:operation-proof-test",)


def _kernel_and_store(
    tmp_path: Path,
    *,
    name: str = "operation-proof",
) -> tuple[GovernedExternalActionKernel, ExternalActionTransactionStore]:
    store = ExternalActionTransactionStore(tmp_path / f"{name}.sqlite3")
    kernel = object.__new__(GovernedExternalActionKernel)
    kernel._store = store
    _register_external_action_kernel_replay_source(kernel, store=store)
    return kernel, store


def _observation_proof(
    kernel: GovernedExternalActionKernel,
    request: ExternalActionExecutionRequest,
    *,
    suffix: str = "observation",
) -> GovernedBrowserOperationProof:
    evidence_ref = _ref("evidence", suffix)
    return _record_operation_proof(
        kernel,
        expected_execution=request,
        lane_ref=OBSERVATION_LANE_REF,
        operation_ref=OBSERVATION_OPERATION_REF,
        scope_refs=SCOPE_REFS,
        dispatch_outcome="succeeded",
        base_evidence_refs=(evidence_ref,),
        material=BrowserObservationOperationProofMaterial(
            evidence_ref=evidence_ref,
            profile_ref=_ref("browser-profile", suffix),
        ),
    )


def _action_proof(
    kernel: GovernedExternalActionKernel,
    request: ExternalActionExecutionRequest,
    *,
    suffix: str = "action",
) -> GovernedBrowserOperationProof:
    plan_ref = _ref("browser-action-plan", suffix)
    projection_ref = _ref("browser-action-plan-projection", suffix)
    return _record_operation_proof(
        kernel,
        expected_execution=request,
        lane_ref=ACTION_LANE_REF,
        operation_ref=ACTION_OPERATION_REF,
        scope_refs=SCOPE_REFS,
        dispatch_outcome="succeeded",
        base_evidence_refs=(plan_ref, projection_ref),
        material=BrowserActionPlanOperationProofMaterial(
            plan_ref=plan_ref,
            projection_ref=projection_ref,
            profile_ref=_ref("browser-profile", suffix),
        ),
    )


def _proof_path(
    store: GovernedBrowserOperationProofStore,
    proof_ref: str,
) -> Path:
    return store.proof_directory / _proof_filename(proof_ref)


def _finish_terminal(
    store: ExternalActionTransactionStore,
    request: ExternalActionExecutionRequest,
    *,
    evidence_refs: tuple[str, ...],
    suffix: str,
    state: ExternalActionState = ExternalActionState.succeeded,
    reason_refs: tuple[str, ...] = (),
) -> ExternalActionReceipt:
    prepared_state, prior = store.prepare(request)
    assert prepared_state == ExternalActionState.prepared
    assert prior is None
    terminal = _receipt(
        request,
        evidence_refs=evidence_refs,
        proof_suffix=suffix,
        state=state,
        reason_refs=reason_refs,
    )
    store.finish(
        terminal,
        expected_state=ExternalActionState.prepared,
    )
    return terminal


def _rewrite_terminal_row(
    store: ExternalActionTransactionStore,
    terminal: ExternalActionReceipt,
) -> None:
    with store._lock, store._connect() as connection:
        connection.execute(
            "UPDATE governed_external_actions SET state = ?, receipt_json = ? "
            "WHERE transaction_ref = ?",
            (
                terminal.state,
                ExternalActionReceipt.model_dump_json(terminal),
                terminal.transaction_ref,
            ),
        )
        connection.commit()


def _terminal_binding_path(
    store: GovernedBrowserOperationProofStore,
    terminal_receipt_ref: str,
) -> Path:
    return (
        store.terminal_binding_directory
        / _terminal_binding_filename(terminal_receipt_ref)
    )


def _replay_expectation(
    proof: GovernedBrowserOperationProof,
) -> ExternalActionReplayEvidenceExpectation:
    return ExternalActionReplayEvidenceExpectation(
        lane_ref=proof.lane_ref,
        operation_ref=proof.operation_ref,
        scope_refs=proof.scope_refs,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        operation_proof_ref=proof.proof_ref,
    )


def test_store_save_is_idempotent_and_ignores_instance_method_shadows(
    tmp_path: Path,
) -> None:
    request = _request("proof-idempotent")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    proof_store = _operation_proof_store_for_kernel(kernel)

    proof_store.load = lambda **_kwargs: None  # type: ignore[method-assign]
    proof_store.save = lambda _proof: None  # type: ignore[method-assign]

    loaded = GovernedBrowserOperationProofStore.load(
        proof_store,
        proof_ref=proof.proof_ref,
    )
    saved_again = GovernedBrowserOperationProofStore.save(proof_store, proof)

    assert loaded == proof
    assert saved_again == proof
    assert len(tuple(proof_store.proof_directory.glob("*.json"))) == 1


def test_terminal_binding_attestation_ignores_instance_method_shadows(
    tmp_path: Path,
) -> None:
    request = _request("terminal-binding-method-shadow")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        suffix="terminal-binding-method-shadow",
    )
    proof_store = _operation_proof_store_for_kernel(kernel)
    proof_store.load_terminal_binding = (  # type: ignore[method-assign]
        lambda **_kwargs: None
    )
    proof_store.save_terminal_binding = (  # type: ignore[method-assign]
        lambda _binding: None
    )

    context = _build_external_action_replay_validation_context(
        kernel,
        expected_execution=request,
        replay_receipt=terminal.model_copy(update={"replayed": True}),
        expectation=_replay_expectation(proof),
    )

    assert context.envelope.terminal_receipt_ref == terminal.receipt_ref


def test_recreated_terminal_binding_directory_changes_store_identity(
    tmp_path: Path,
) -> None:
    proof_store = GovernedBrowserOperationProofStore(
        tmp_path / "terminal-binding-directory-identity"
    )
    original_store_ref = proof_store.store_ref
    original_directory = proof_store.terminal_binding_directory
    original_directory.rename(
        proof_store.root / "terminal-bindings-original"
    )
    original_directory.mkdir(mode=0o700)

    replacement_store = GovernedBrowserOperationProofStore(
        proof_store.root
    )

    assert replacement_store.store_ref != original_store_ref
    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_STORE_SUBSTITUTION_DENIED",
    ):
        GovernedBrowserOperationProofStore.load_terminal_binding(
            proof_store,
            terminal_receipt_ref=(
                "receipt-ref:governed-external-action:sha256:" + ("0" * 64)
            ),
        )


def test_store_rejects_preexisting_symlink_root(tmp_path: Path) -> None:
    target = tmp_path / "operation-proof-root-target"
    target.mkdir(mode=0o700)
    symlink_root = tmp_path / "operation-proof-root-symlink"
    symlink_root.symlink_to(target, target_is_directory=True)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_ROOT_UNSAFE",
    ):
        GovernedBrowserOperationProofStore(symlink_root)


def test_terminal_binding_write_failure_never_backfills_or_redispatches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("terminal-binding-write-failure")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    evidence_refs = (_ref("evidence", "terminal-binding-write-failure"),)
    state, prior = transaction_store.prepare(request)
    assert state == ExternalActionState.prepared
    assert prior is None
    terminal = _receipt(
        request,
        evidence_refs=evidence_refs,
        proof_suffix="terminal-binding-write-failure",
    )

    def fail_terminal_binding_write(
        _store: GovernedBrowserOperationProofStore,
        _binding: GovernedBrowserTerminalReceiptBinding,
    ) -> GovernedBrowserTerminalReceiptBinding:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_TERMINAL_BINDING_WRITE_FAILED"
        )

    monkeypatch.setattr(
        GovernedBrowserOperationProofStore,
        "save_terminal_binding",
        fail_terminal_binding_write,
    )
    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_TERMINAL_BINDING_WRITE_FAILED",
    ):
        transaction_store.finish(
            terminal,
            expected_state=ExternalActionState.prepared,
        )

    # The exact idempotent finish must not synthesize a binding after the
    # commit/write boundary failed.
    transaction_store.finish(
        terminal,
        expected_state=ExternalActionState.prepared,
    )
    dispatch_called = False

    def dispatch(_request: ExternalActionExecutionRequest) -> object:
        nonlocal dispatch_called
        dispatch_called = True
        raise AssertionError("terminal replay must not redispatch")

    replay = kernel.execute(request, dispatch=dispatch)  # type: ignore[arg-type]
    assert replay.replayed
    assert not dispatch_called
    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=replay,
            expectation=ExternalActionReplayEvidenceExpectation(
                lane_ref=OBSERVATION_LANE_REF,
                operation_ref=OBSERVATION_OPERATION_REF,
                scope_refs=SCOPE_REFS,
                evidence_refs=evidence_refs,
            ),
        )


def test_full_store_keeps_existing_save_idempotent_and_rejects_new_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_request = _request("proof-full-first")
    second_request = _request("proof-full-second")
    kernel, _ = _kernel_and_store(tmp_path)
    first = _observation_proof(kernel, first_request, suffix="full-first")
    proof_store = _operation_proof_store_for_kernel(kernel)
    monkeypatch.setattr(
        operation_proofs_module,
        "MAX_GOVERNED_BROWSER_OPERATION_PROOFS",
        1,
    )

    assert GovernedBrowserOperationProofStore.save(proof_store, first) == first
    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_STORE_FULL",
    ):
        _observation_proof(kernel, second_request, suffix="full-second")
    assert tuple(proof_store.proof_directory.glob("*.json")) == (
        _proof_path(proof_store, first.proof_ref),
    )


def test_store_rejects_tampered_proof_without_recomputed_ref(
    tmp_path: Path,
) -> None:
    request = _request("proof-tamper")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    proof_store = _operation_proof_store_for_kernel(kernel)
    path = _proof_path(proof_store, proof.proof_ref)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["material"]["profile_ref"] = _ref(
        "browser-profile",
        "tampered",
    )
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_INVALID",
    ):
        GovernedBrowserOperationProofStore.load(
            proof_store,
            proof_ref=proof.proof_ref,
        )


def test_attestation_rejects_missing_proof(tmp_path: Path) -> None:
    request = _request("proof-missing")
    kernel, _ = _kernel_and_store(tmp_path)
    missing_ref = (
        "operation-proof-ref:governed-browser:sha256:" + ("0" * 64)
    )

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_REQUIRED",
    ):
        _attest_operation_proof(
            kernel,
            expected_execution=request,
            proof_ref=missing_ref,
            lane_ref=OBSERVATION_LANE_REF,
            operation_ref=OBSERVATION_OPERATION_REF,
            scope_refs=SCOPE_REFS,
            base_evidence_refs=(_ref("evidence", "missing"),),
        )


def test_store_rejects_symlinked_proof_file(tmp_path: Path) -> None:
    request = _request("proof-symlink")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    proof_store = _operation_proof_store_for_kernel(kernel)
    path = _proof_path(proof_store, proof.proof_ref)
    target = proof_store.proof_directory / "symlink-target.json"
    path.rename(target)
    path.symlink_to(target.name)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_REQUIRED",
    ):
        GovernedBrowserOperationProofStore.load(
            proof_store,
            proof_ref=proof.proof_ref,
        )


def test_store_rejects_hardlinked_proof_file(tmp_path: Path) -> None:
    request = _request("proof-hardlink")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    proof_store = _operation_proof_store_for_kernel(kernel)
    path = _proof_path(proof_store, proof.proof_ref)
    os.link(path, proof_store.proof_directory / "hardlink-alias.json")

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_REQUIRED",
    ):
        GovernedBrowserOperationProofStore.load(
            proof_store,
            proof_ref=proof.proof_ref,
        )


def test_store_rejects_fifo_in_place_of_proof_file(tmp_path: Path) -> None:
    request = _request("proof-fifo")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    proof_store = _operation_proof_store_for_kernel(kernel)
    path = _proof_path(proof_store, proof.proof_ref)
    path.unlink()
    os.mkfifo(path, mode=0o600)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_REQUIRED",
    ):
        GovernedBrowserOperationProofStore.load(
            proof_store,
            proof_ref=proof.proof_ref,
        )


def test_store_rejects_oversize_proof_file(tmp_path: Path) -> None:
    request = _request("proof-oversize")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    proof_store = _operation_proof_store_for_kernel(kernel)
    path = _proof_path(proof_store, proof.proof_ref)
    path.write_bytes(
        b"x" * (MAX_GOVERNED_BROWSER_OPERATION_PROOF_BYTES + 1)
    )

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_REQUIRED",
    ):
        GovernedBrowserOperationProofStore.load(
            proof_store,
            proof_ref=proof.proof_ref,
        )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("lane_ref", "replay-lane-ref:governed-browser-post-form:v1"),
        (
            "operation_ref",
            "replay-operation-ref:governed-browser-action:foreign",
        ),
        (
            "scope_refs",
            ("recipe-ref:governed-browser:foreign",),
        ),
    ],
)
def test_attestation_rejects_cross_operation_scope_substitution(
    tmp_path: Path,
    field: str,
    replacement: str | tuple[str, ...],
) -> None:
    request = _request(f"proof-cross-{field}")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _action_proof(kernel, request)
    arguments: dict[str, object] = {
        "lane_ref": proof.lane_ref,
        "operation_ref": proof.operation_ref,
        "scope_refs": proof.scope_refs,
    }
    arguments[field] = replacement

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_PROVENANCE_MISMATCH",
    ):
        _attest_operation_proof(
            kernel,
            expected_execution=request,
            proof_ref=proof.proof_ref,
            base_evidence_refs=proof.base_evidence_refs,
            **arguments,  # type: ignore[arg-type]
        )


def test_attestation_rejects_cross_transaction_substitution(
    tmp_path: Path,
) -> None:
    original_request = _request("proof-transaction-original")
    foreign_request = _request("proof-transaction-foreign")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, original_request)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_PROVENANCE_MISMATCH",
    ):
        _attest_operation_proof(
            kernel,
            expected_execution=foreign_request,
            proof_ref=proof.proof_ref,
            lane_ref=proof.lane_ref,
            operation_ref=proof.operation_ref,
            scope_refs=proof.scope_refs,
            base_evidence_refs=proof.base_evidence_refs,
        )


@pytest.mark.parametrize(
    "tampered_evidence",
    [
        lambda refs: tuple(reversed(refs)),
        lambda refs: refs[:1],
        lambda refs: (*refs, _ref("evidence", "extra")),
        lambda refs: (_ref("evidence", "replacement"), refs[1]),
    ],
    ids=("order", "arity-drop", "arity-add", "field-replacement"),
)
def test_attestation_rejects_evidence_order_arity_and_field_tampering(
    tmp_path: Path,
    tampered_evidence,
) -> None:  # type: ignore[no-untyped-def]
    request = _request("proof-evidence-envelope")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _action_proof(kernel, request)

    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_PROVENANCE_MISMATCH",
    ):
        _attest_operation_proof(
            kernel,
            expected_execution=request,
            proof_ref=proof.proof_ref,
            lane_ref=proof.lane_ref,
            operation_ref=proof.operation_ref,
            scope_refs=proof.scope_refs,
            base_evidence_refs=tampered_evidence(
                proof.base_evidence_refs
            ),
        )


def test_recomputed_proof_hash_cannot_cross_operation_boundary(
    tmp_path: Path,
) -> None:
    request = _request("proof-recomputed")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    proof_store = _operation_proof_store_for_kernel(kernel)
    payload = proof.model_dump(mode="json")
    payload["operation_ref"] = (
        "replay-operation-ref:governed-browser-observation:substituted"
    )
    payload["proof_ref"] = stable_governed_browser_ref(
        "operation-proof-ref:governed-browser",
        {key: value for key, value in payload.items() if key != "proof_ref"},
    )
    substituted = GovernedBrowserOperationProof.model_validate(payload)
    substituted_path = _proof_path(proof_store, substituted.proof_ref)
    substituted_path.write_text(
        substituted.model_dump_json() + "\n",
        encoding="utf-8",
    )
    substituted_path.chmod(0o600)

    assert (
        GovernedBrowserOperationProofStore.load(
            proof_store,
            proof_ref=substituted.proof_ref,
        )
        == substituted
    )
    with pytest.raises(
        GovernedBrowserOperationProofError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_PROVENANCE_MISMATCH",
    ):
        _attest_operation_proof(
            kernel,
            expected_execution=request,
            proof_ref=substituted.proof_ref,
            lane_ref=proof.lane_ref,
            operation_ref=proof.operation_ref,
            scope_refs=proof.scope_refs,
            base_evidence_refs=proof.base_evidence_refs,
        )


def test_recomputed_proof_hash_cannot_reclassify_dispatch_outcome(
    tmp_path: Path,
) -> None:
    request = _request("proof-recomputed-outcome")
    kernel, _ = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    payload = proof.model_dump(mode="json")
    payload["dispatch_outcome"] = "failed"
    payload["proof_ref"] = stable_governed_browser_ref(
        "operation-proof-ref:governed-browser",
        {key: value for key, value in payload.items() if key != "proof_ref"},
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_BROWSER_OPERATION_PROOF_SUCCESS_OUTCOME_MISMATCH",
    ):
        GovernedBrowserOperationProof.model_validate(payload)


def test_replay_context_binds_exact_operation_proof(tmp_path: Path) -> None:
    request = _request("proof-replay-clean")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        suffix="proof-replay-clean",
    )
    replay = terminal.model_copy(update={"replayed": True})

    context = _build_external_action_replay_validation_context(
        kernel,
        expected_execution=request,
        replay_receipt=replay,
        expectation=_replay_expectation(proof),
    )

    assert context.envelope.operation_proof_ref == proof.proof_ref
    assert context.envelope.evidence_refs == (
        *proof.base_evidence_refs,
        proof.proof_ref,
    )
    assert context.envelope.terminal_receipt_ref == terminal.receipt_ref


def test_terminal_binding_rejects_ambiguity_rewritten_as_success(
    tmp_path: Path,
) -> None:
    request = _request("terminal-ambiguity-to-success")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        suffix="terminal-ambiguity-to-success",
        state=ExternalActionState.outcome_ambiguous,
        reason_refs=(
            "reason-ref:governed-external-action:"
            "post-dispatch-revalidation-denied",
        ),
    )
    substituted = _rehash_receipt(
        terminal,
        state=ExternalActionState.succeeded.value,
        reason_refs=(),
    )
    _rewrite_terminal_row(transaction_store, substituted)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=substituted.model_copy(update={"replayed": True}),
            expectation=_replay_expectation(proof),
        )


def test_terminal_binding_rejects_success_rewritten_as_generic_ambiguity(
    tmp_path: Path,
) -> None:
    request = _request("terminal-success-to-generic-ambiguity")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        suffix="terminal-success-to-generic-ambiguity",
    )
    evidence_suffix = "dispatch-timeout"
    generic_evidence_ref = stable_governed_browser_ref(
        "evidence-ref:governed-external-action:dispatch-timeout",
        {
            "reason": evidence_suffix,
            "transaction_ref": terminal.transaction_ref,
            "intent_ref": terminal.intent_ref,
            "binding_ref": terminal.binding_ref,
        },
    )
    substituted = _rehash_receipt(
        terminal,
        state=ExternalActionState.outcome_ambiguous.value,
        evidence_refs=(generic_evidence_ref,),
        reason_refs=(
            "reason-ref:governed-external-action:dispatch-timeout",
        ),
    )
    _rewrite_terminal_row(transaction_store, substituted)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=substituted.model_copy(update={"replayed": True}),
            expectation=ExternalActionReplayEvidenceExpectation(
                lane_ref=proof.lane_ref,
                operation_ref=proof.operation_ref,
                scope_refs=proof.scope_refs,
                evidence_refs=(generic_evidence_ref,),
            ),
        )


@pytest.mark.parametrize(
    "tampered_evidence",
    [
        lambda refs: (refs[1], refs[0], refs[2]),
        lambda refs: (refs[0], refs[2]),
        lambda refs: (refs[0], refs[1], _ref("evidence", "extra"), refs[2]),
        lambda refs: (refs[0], _ref("evidence", "replacement"), refs[2]),
    ],
    ids=("order", "arity-drop", "arity-add", "field-replacement"),
)
def test_terminal_binding_rejects_recomputed_evidence_envelope_tampering(
    tmp_path: Path,
    tampered_evidence,
) -> None:  # type: ignore[no-untyped-def]
    request = _request("terminal-evidence-envelope")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    proof = _action_proof(kernel, request)
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        suffix="terminal-evidence-envelope",
    )
    evidence_refs = tampered_evidence(terminal.evidence_refs)
    substituted = _rehash_receipt(
        terminal,
        evidence_refs=evidence_refs,
    )
    _rewrite_terminal_row(transaction_store, substituted)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=substituted.model_copy(update={"replayed": True}),
            expectation=ExternalActionReplayEvidenceExpectation(
                lane_ref=proof.lane_ref,
                operation_ref=proof.operation_ref,
                scope_refs=proof.scope_refs,
                evidence_refs=evidence_refs,
                operation_proof_ref=proof.proof_ref,
            ),
        )


@pytest.mark.parametrize(
    "updates",
    [
        {
            "reason_refs": (
                "reason-ref:governed-external-action:substituted",
            )
        },
        {
            "approval_validation_ref": (
                "approval-validation-ref:governed-browser:substituted"
            )
        },
        {
            "authority_decision_ref": (
                "authority-decision-ref:governed-browser:substituted"
            )
        },
        {
            "budget_reservation_ref": (
                "budget-reservation-ref:governed-browser:substituted"
            )
        },
        {
            "budget_settlement_ref": (
                "budget-settlement-ref:governed-browser:substituted"
            )
        },
        {
            "budget_settlement_ref": None,
            "budget_release_ref": (
                "budget-release-ref:governed-browser:substituted"
            ),
        },
    ],
    ids=(
        "reasons",
        "approval",
        "authority",
        "reservation",
        "settlement",
        "release",
    ),
)
def test_terminal_binding_rejects_recomputed_reason_and_accounting_changes(
    tmp_path: Path,
    updates: dict[str, object],
) -> None:
    request = _request("terminal-reason-accounting")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        suffix="terminal-reason-accounting",
    )
    substituted = _rehash_receipt(terminal, **updates)
    _rewrite_terminal_row(transaction_store, substituted)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=substituted.model_copy(update={"replayed": True}),
            expectation=_replay_expectation(proof),
        )


def test_terminal_binding_rejects_cross_operation_proof_substitution(
    tmp_path: Path,
) -> None:
    request = _request("terminal-cross-operation")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    original = _action_proof(kernel, request, suffix="original-operation")
    foreign = _observation_proof(kernel, request, suffix="foreign-operation")
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*original.base_evidence_refs, original.proof_ref),
        suffix="terminal-cross-operation",
    )
    substituted = _rehash_receipt(
        terminal,
        evidence_refs=(*foreign.base_evidence_refs, foreign.proof_ref),
    )
    _rewrite_terminal_row(transaction_store, substituted)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=substituted.model_copy(update={"replayed": True}),
            expectation=_replay_expectation(foreign),
        )


def test_terminal_binding_rejects_cross_transaction_proof_substitution(
    tmp_path: Path,
) -> None:
    request = _request("terminal-cross-transaction")
    foreign_request = _request("terminal-cross-transaction-foreign")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    original = _observation_proof(kernel, request, suffix="original-transaction")
    foreign = _observation_proof(
        kernel,
        foreign_request,
        suffix="foreign-transaction",
    )
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*original.base_evidence_refs, original.proof_ref),
        suffix="terminal-cross-transaction",
    )
    substituted = _rehash_receipt(
        terminal,
        evidence_refs=(*foreign.base_evidence_refs, foreign.proof_ref),
    )
    _rewrite_terminal_row(transaction_store, substituted)

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=substituted.model_copy(update={"replayed": True}),
            expectation=ExternalActionReplayEvidenceExpectation(
                lane_ref=foreign.lane_ref,
                operation_ref=foreign.operation_ref,
                scope_refs=foreign.scope_refs,
                evidence_refs=(
                    *foreign.base_evidence_refs,
                    foreign.proof_ref,
                ),
                operation_proof_ref=foreign.proof_ref,
            ),
        )


def test_recomputed_terminal_binding_hash_cannot_rebind_request(
    tmp_path: Path,
) -> None:
    request = _request("terminal-binding-recomputed")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    proof = _observation_proof(kernel, request)
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        suffix="terminal-binding-recomputed",
    )
    proof_store = _operation_proof_store_for_kernel(kernel)
    binding = GovernedBrowserOperationProofStore.load_terminal_binding(
        proof_store,
        terminal_receipt_ref=terminal.receipt_ref,
    )
    payload = binding.model_dump(mode="json")
    payload["request_fingerprint_ref"] = stable_governed_browser_ref(
        "request-fingerprint-ref:governed-external-action",
        {"request": "substituted"},
    )
    payload["terminal_binding_ref"] = stable_governed_browser_ref(
        "terminal-binding-ref:governed-browser",
        {
            key: value
            for key, value in payload.items()
            if key != "terminal_binding_ref"
        },
    )
    substituted = GovernedBrowserTerminalReceiptBinding.model_validate(payload)
    _terminal_binding_path(
        proof_store,
        terminal.receipt_ref,
    ).write_text(
        substituted.model_dump_json() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=terminal.model_copy(update={"replayed": True}),
            expectation=_replay_expectation(proof),
        )


def test_recomputed_terminal_receipt_cannot_substitute_proven_evidence(
    tmp_path: Path,
) -> None:
    request = _request("proof-replay-tampered")
    kernel, transaction_store = _kernel_and_store(tmp_path)
    proof = _action_proof(kernel, request)
    tampered_base = (
        proof.base_evidence_refs[0],
        _ref("browser-action-plan-projection", "substituted"),
    )
    terminal = _finish_terminal(
        transaction_store,
        request,
        evidence_refs=(*proof.base_evidence_refs, proof.proof_ref),
        suffix="proof-replay-tampered",
    )
    tampered_terminal = _rehash_receipt(
        terminal,
        evidence_refs=(*tampered_base, proof.proof_ref),
    )
    _rewrite_terminal_row(transaction_store, tampered_terminal)
    replay = tampered_terminal.model_copy(update={"replayed": True})
    expectation = ExternalActionReplayEvidenceExpectation(
        lane_ref=proof.lane_ref,
        operation_ref=proof.operation_ref,
        scope_refs=proof.scope_refs,
        evidence_refs=(*tampered_base, proof.proof_ref),
        operation_proof_ref=proof.proof_ref,
    )

    with pytest.raises(
        ValueError,
        match="GOVERNED_EXTERNAL_ACTION_REPLAY_TERMINAL_BINDING_INVALID",
    ):
        _build_external_action_replay_validation_context(
            kernel,
            expected_execution=request,
            replay_receipt=replay,
            expectation=expectation,
        )
