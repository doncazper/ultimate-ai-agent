from __future__ import annotations

import json
import stat
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import ultimate_ai_agent.core.runtime_gateway.goal_runtime as goal_runtime_module
from ultimate_ai_agent.core.runtime_gateway.command import invoke_governed_command
from ultimate_ai_agent.core.runtime_gateway.contracts import (
    RuntimeAuthority,
    RuntimeCriterionVerificationBinding,
    RuntimeInvocationRecord,
    RuntimeInvocationReceipt,
    RuntimeInvocationRequest,
    RuntimeInvocationStatus,
    RuntimeProfile,
    RuntimeSafeDisableRequest,
)
from ultimate_ai_agent.core.runtime_gateway.goal_runtime import (
    AcceptedLocalRunType,
    DurableCriterionVerifierBinding,
    DurableRunEvent,
    DurableRunEventAppendRequest,
    DurableRunEventKind,
    GoalCompletionEvidence,
    GoalCreateRequest,
    GoalEditRequest,
    GoalIdempotencyConflictError,
    GoalMutationApprovalBinding,
    GoalRuntimeCorruptionError,
    GoalRuntimeError,
    GoalRuntimeService,
    GoalState,
    GoalTransitionDeniedError,
    GoalTransitionKind,
    GoalTransitionRequest,
    GoalVersionConflictError,
    GOAL_COMPLETION_VERIFIER_REF,
    PersistentGoal,
    build_goal_criterion_ref,
    build_goal_completion_evidence_ref,
    RunEventReplayStatus,
)
from ultimate_ai_agent.core.runtime_gateway.run_events import (
    build_runtime_run_events_read_model,
)
from ultimate_ai_agent.core.runtime_gateway.storage import (
    RuntimeInvocationStorageError,
)
from ultimate_ai_agent.core.runtime_gateway import (
    GovernedCommandRuntimeAdapter,
    LocalModelRuntimeAdapter,
    RuntimeCommandExecutionRequest,
    RuntimeCommandGatewayResult,
    RuntimeCommandRunResult,
    RuntimeExecuteRequest,
    RuntimeGateway,
    RuntimeInvocationStore,
    RuntimeLocalModelCallRequest,
    RuntimeLocalModelMessage,
)
from tests.authority_helpers import workspace_execute_authority_lease

EVENT_AUTHORITY_DECISION_REF = "authority-decision-ref:accepted-local:test"
ROOT = Path(__file__).resolve().parents[1]


def _criterion_bindings(
    goal: PersistentGoal,
    criterion_proof_refs: list[str],
) -> list[DurableCriterionVerifierBinding]:
    return [
        DurableCriterionVerifierBinding(
            goal_ref=goal.goal_ref,
            goal_version=goal.version,
            criterion_ref=build_goal_criterion_ref(
                goal,
                criterion_index=index,
                criterion_summary=criterion,
            ),
            proof_ref=proof_ref,
            verifier_ref=GOAL_COMPLETION_VERIFIER_REF,
            evaluator_receipt_ref=(f"evaluator-receipt-ref:accepted-local:{index + 1}"),
        )
        for index, (criterion, proof_ref) in enumerate(
            zip(goal.success_criteria, criterion_proof_refs, strict=True)
        )
    ]


def _completion_evidence(
    goal: PersistentGoal,
    *,
    run_ref: str = "run-ref:accepted-local:one",
    receipt_ref: str = "receipt-ref:accepted-local:one",
    proof_ref: str = "proof-ref:accepted-local:one",
    criterion_proof_refs: list[str] | None = None,
    plan_ref: str | None = "plan-ref:accepted-local:one",
) -> GoalCompletionEvidence:
    bound_criterion_proof_refs = criterion_proof_refs or [
        proof_ref,
        *[
            f"proof-ref:accepted-local:criterion:{index}"
            for index in range(2, len(goal.success_criteria) + 1)
        ],
    ]
    bindings = _criterion_bindings(goal, bound_criterion_proof_refs)
    return GoalCompletionEvidence(
        goal_ref=goal.goal_ref,
        goal_version=goal.version,
        run_ref=run_ref,
        receipt_ref=receipt_ref,
        proof_ref=proof_ref,
        criterion_proof_refs=bound_criterion_proof_refs,
        evidence_ref=build_goal_completion_evidence_ref(
            goal,
            run_ref=run_ref,
            receipt_ref=receipt_ref,
            proof_ref=proof_ref,
            criterion_verifier_bindings=bindings,
            plan_ref=plan_ref,
        ),
        verifier_ref=GOAL_COMPLETION_VERIFIER_REF,
    )


def _approved_mutation_ref(
    service: GoalRuntimeService,
    *,
    operation: str,
    goal_ref: str | None,
    request: GoalCreateRequest
    | GoalEditRequest
    | GoalTransitionRequest
    | DurableRunEventAppendRequest,
    idempotency_ref: str,
) -> str:
    spec = service.prepare_goal_mutation_approval(
        operation=operation,
        goal_ref=goal_ref,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    service.decide_goal_mutation_approval(
        approval_request_ref=spec.approval_request_ref,
        decision="approve",
        decision_reason_ref="reason-ref:test-explicit-goal-mutation-approval",
    )
    return spec.approval_ref


def _append_event(
    service: GoalRuntimeService,
    request: DurableRunEventAppendRequest,
) -> DurableRunEvent:
    if (
        request.event_kind == DurableRunEventKind.receipt_recorded.value
        and request.goal_ref is not None
        and not request.criterion_verifier_bindings
    ):
        try:
            goal = service.goals.get(request.goal_ref)
        except GoalRuntimeError:
            goal = None
        if goal is not None and len(request.proof_refs) >= len(goal.success_criteria):
            criterion_proof_refs = request.proof_refs[: len(goal.success_criteria)]
            bindings = _criterion_bindings(goal, criterion_proof_refs)
            request = request.model_copy(
                update={
                    "proof_refs": list(
                        dict.fromkeys(
                            [
                                *request.proof_refs,
                                *(
                                    binding.evaluator_receipt_ref
                                    for binding in bindings
                                ),
                            ]
                        )
                    ),
                    "criterion_verifier_bindings": bindings,
                }
            )
    if request.event_kind in {
        DurableRunEventKind.receipt_recorded.value,
        DurableRunEventKind.cancelled.value,
        DurableRunEventKind.failed_terminal.value,
        DurableRunEventKind.dead_lettered.value,
    }:
        request_fingerprint_ref = service._events._request_fingerprint(  # noqa: SLF001
            request
        )
        runtime_store = RuntimeInvocationStore(
            service.state_dir / "trusted_evaluator_runtime"
        )
        invocation_idempotency_ref = goal_runtime_module._sha256_ref(  # noqa: SLF001
            "idempotency-ref:trusted-evaluator-receipt",
            {"request_fingerprint_ref": request_fingerprint_ref},
        )
        created = runtime_store.create_invocation(
            RuntimeInvocationRequest(
                requested_authority=RuntimeAuthority.local_model,
                input_ref=request_fingerprint_ref,
                safe_summary=(
                    "Record one exact trusted evaluator receipt projection."
                ),
                mission_ref=request.goal_ref,
                action_ref=request.run_ref,
                metadata_refs=[request_fingerprint_ref],
            ),
            idempotency_ref=invocation_idempotency_ref,
            local_model_gateway_validated=True,
        ).record
        receipt = RuntimeInvocationReceipt(
            receipt_ref=request.receipt_refs[0],
            invocation_ref=created.invocation_ref,
            policy_decision_ref=created.policy_decision.policy_decision_ref,
            invocation_status=RuntimeInvocationStatus.receipt_recorded,
            evidence_refs=[request_fingerprint_ref],
            criterion_verification_bindings=[
                RuntimeCriterionVerificationBinding.model_validate(
                    binding.model_dump(mode="json")
                )
                for binding in request.criterion_verifier_bindings
            ],
            safe_summary=request.safe_summary,
        )
        runtime_store.record_receipt(
            created.invocation_ref,
            receipt,
            idempotency_ref=goal_runtime_module._sha256_ref(  # noqa: SLF001
                "idempotency-ref:trusted-evaluator-receipt-record",
                {"request_fingerprint_ref": request_fingerprint_ref},
            ),
        )
        return service._events.append(  # noqa: SLF001
            request,
            trusted_source=goal_runtime_module.TrustedRunEventSourceBinding(
                source_kind="runtime_evaluator_receipt",
                source_ref=created.invocation_ref,
                source_fingerprint_ref=request_fingerprint_ref,
            ),
        )
    if request.event_kind in {
        DurableRunEventKind.completion_verified.value,
    }:
        return service._events.append(request)  # noqa: SLF001
    approval_ref = _approved_mutation_ref(
        service,
        operation="append-run-event",
        goal_ref=None,
        request=request,
        idempotency_ref=request.idempotency_ref,
    )
    return service.append_run_event(request, approval_ref=approval_ref)


def _create_request(
    *, run_ref: str = "run-ref:accepted-local:one"
) -> GoalCreateRequest:
    return GoalCreateRequest(
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective="Deliver the accepted local operator outcome.",
        desired_outcome="A durable, proof-backed completion state.",
        success_criteria=[
            "The accepted local read task has a receipt.",
            "The receipt and proof are linked to this goal.",
        ],
        constraints=["No external execution or standing authority."],
        in_scope_resource_refs=["resource-ref:local-workspace:bounded"],
        stop_condition="Stop on cancellation, authority denial, or evidence failure.",
        links={
            "plan_refs": ["plan-ref:accepted-local:one"],
            "run_refs": [run_ref],
            "action_inbox_refs": ["action-inbox-ref:accepted-local:one"],
            "work_board_refs": ["work-board-ref:accepted-local:one"],
        },
        evidence_refs=["evidence-ref:goal-created"],
    )


def _append_receipt(
    service: GoalRuntimeService,
    *,
    goal_ref: str,
    run_ref: str = "run-ref:accepted-local:one",
) -> None:
    goal = service.goals.get(goal_ref)
    proof_refs = [
        "proof-ref:accepted-local:one",
        "proof-ref:accepted-local:criterion:2",
    ][: len(goal.success_criteria)]
    bindings = _criterion_bindings(goal, proof_refs)
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="The accepted local read task recorded a redacted receipt.",
            proof_refs=[
                *proof_refs,
                *(binding.evaluator_receipt_ref for binding in bindings),
            ],
            receipt_refs=["receipt-ref:accepted-local:one"],
            criterion_verifier_bindings=bindings,
            goal_ref=goal_ref,
            plan_ref="plan-ref:accepted-local:one",
            idempotency_ref="idempotency-ref:event-receipt-one",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )


def _create_goal(
    service: GoalRuntimeService,
    request: GoalCreateRequest,
    *,
    idempotency_ref: str,
):
    approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    goal, _approval = service.create_goal(
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=approval_ref,
    )
    return goal


def _edit_goal(
    service: GoalRuntimeService,
    goal_ref: str,
    request: GoalEditRequest,
    *,
    idempotency_ref: str,
):
    approval_ref = _approved_mutation_ref(
        service,
        operation="edit",
        goal_ref=goal_ref,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    goal, _approval = service.edit_goal(
        goal_ref,
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=approval_ref,
    )
    return goal


def _transition_goal(
    service: GoalRuntimeService,
    goal_ref: str,
    request: GoalTransitionRequest,
    *,
    idempotency_ref: str,
):
    approval_ref = _approved_mutation_ref(
        service,
        operation="transition",
        goal_ref=goal_ref,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    goal, _approval = service.transition_goal(
        goal_ref,
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=approval_ref,
    )
    return goal


def _replace_goal_journal_for_tamper(
    service: GoalRuntimeService,
    entries: list[goal_runtime_module.GoalJournalEntry],
    *,
    rewrite_independent_anchor: bool = False,
) -> None:
    service.goals.path.write_text(  # noqa: SLF001
        service.goals._journal_content(entries),  # noqa: SLF001
        encoding="utf-8",
    )
    service.goals._write_head_manifest(  # noqa: SLF001
        service.goals._build_head_manifest(entries)  # noqa: SLF001
    )
    if rewrite_independent_anchor:
        state = service._submissions._load_state()  # noqa: SLF001
        service._submissions._write(  # noqa: SLF001
            list(state.records),
            list(state.rejection_tombstones),
            goal_journal_anchor=service._submissions._journal_anchor(  # noqa: SLF001
                entries
            ),
        )


def test_goal_lifecycle_persists_replays_and_detects_version_conflicts(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()

    created = _create_goal(
        service,
        request,
        idempotency_ref="idempotency-ref:goal-create-one",
    )
    replayed = _create_goal(
        service,
        request,
        idempotency_ref="idempotency-ref:goal-create-one",
    )

    assert replayed == created
    assert created.state == GoalState.active.value
    assert created.version == 1

    with pytest.raises(GoalIdempotencyConflictError):
        _create_goal(
            service,
            request.model_copy(update={"objective": "A different bounded objective."}),
            idempotency_ref="idempotency-ref:goal-create-one",
        )

    paused = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=1,
            transition=GoalTransitionKind.pause,
            reason_ref="reason-ref:operator-pause",
        ),
        idempotency_ref="idempotency-ref:goal-pause-one",
    )
    assert paused.state == GoalState.paused.value
    assert paused.version == 2

    with pytest.raises(GoalVersionConflictError):
        _edit_goal(
            service,
            created.goal_ref,
            GoalEditRequest(
                expected_version=1,
                text_redaction_posture=("operator_authored_redacted_summary_only"),
                stop_condition="Stop on a newly identified bounded condition.",
            ),
            idempotency_ref="idempotency-ref:goal-stale-edit",
        )

    restored = GoalRuntimeService(tmp_path).goals.get(created.goal_ref)
    assert restored == paused


def test_goal_edits_append_evidence_and_transitions_persist_reason(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-audit-create",
    )
    edited = _edit_goal(
        service,
        created.goal_ref,
        GoalEditRequest(
            expected_version=1,
            text_redaction_posture=("operator_authored_redacted_summary_only"),
            objective="Deliver the accepted outcome with durable audit evidence.",
            evidence_refs=["evidence-ref:goal-edited"],
        ),
        idempotency_ref="idempotency-ref:goal-audit-edit",
    )
    assert edited.evidence_refs == [
        "evidence-ref:goal-created",
        "evidence-ref:goal-edited",
    ]

    reason_ref = "reason-ref:goal-audit-pause"
    paused = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=edited.version,
            transition=GoalTransitionKind.pause,
            reason_ref=reason_ref,
        ),
        idempotency_ref="idempotency-ref:goal-audit-pause",
    )
    entry = service.goals.latest_entry(created.goal_ref)
    assert paused.state == GoalState.paused.value
    assert entry.transition_reason_ref == reason_ref

    restarted = GoalRuntimeService(tmp_path)
    assert (
        restarted.goals.latest_entry(created.goal_ref).transition_reason_ref
        == reason_ref
    )


def test_repeated_transitions_roll_up_evidence_and_pin_create_identity(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    create_submission_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:"
        f"{'a' * 64}:ordinal:1"
    )
    request = _create_request().model_copy(
        update={"evidence_refs": [create_submission_ref]}
    )
    service.record_goal_mutation_submission(
        submission_ref="submission-ref:bounded-evidence:create",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:bounded-evidence:create",
    )
    current = _create_goal(
        service,
        request,
        idempotency_ref="idempotency-ref:bounded-evidence:create",
    )

    transition_evidence_refs: list[str] = []
    for index in range(40):
        transition = (
            GoalTransitionKind.pause
            if current.state == GoalState.active.value
            else GoalTransitionKind.resume
        )
        evidence_ref = f"evidence-ref:bounded-transition:{index + 1}"
        transition_evidence_refs.append(evidence_ref)
        current = _transition_goal(
            service,
            current.goal_ref,
            GoalTransitionRequest(
                expected_version=current.version,
                transition=transition,
                reason_ref=f"reason-ref:bounded-transition:{index + 1}",
                evidence_refs=[evidence_ref],
            ),
            idempotency_ref=f"idempotency-ref:bounded-transition:{index + 1}",
        )

    assert current.version == 41
    assert len(current.evidence_refs) == 32
    assert current.evidence_refs[0] == create_submission_ref
    assert current.evidence_refs[1].startswith(
        "evidence-rollup-ref:goal-runtime:sha256:"
    )
    assert transition_evidence_refs[-1] in current.evidence_refs
    assert transition_evidence_refs[0] not in current.evidence_refs
    provenance = service.goals.mutation_provenance(current.goal_ref)
    assert provenance.entry_count == 41
    assert [entry.transition_reason_ref for entry in provenance.entries[1:]] == [
        f"reason-ref:bounded-transition:{index + 1}" for index in range(40)
    ]


def test_goal_snapshot_and_provenance_share_one_journal_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:atomic-goal-detail:create",
    )
    original_load = service.goals._load_entries  # noqa: SLF001
    load_count = 0

    def counted_load(
        *,
        repair_manifest: bool = False,
    ) -> list[object]:
        nonlocal load_count
        load_count += 1
        return original_load(repair_manifest=repair_manifest)

    monkeypatch.setattr(service.goals, "_load_entries", counted_load)
    goal, provenance = service.goals.goal_with_provenance(created.goal_ref)

    assert load_count == 1
    assert goal.version == provenance.entries[-1].goal_version
    assert goal.goal_ref == provenance.goal_ref


def test_goal_mutation_provenance_preserves_submission_fingerprints(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    create_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "1" * 64
    )
    create_request = _create_request().model_copy(
        update={"evidence_refs": [create_evidence_ref]}
    )
    create_idempotency_ref = "idempotency-ref:goal-provenance:create"
    create_submission = service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-provenance:create",
        operation="create",
        goal_ref=None,
        request=create_request,
        idempotency_ref=create_idempotency_ref,
    )
    created = _create_goal(
        service,
        create_request,
        idempotency_ref=create_idempotency_ref,
    )

    edit_evidence_ref = (
        "evidence-ref:control-center-goal-update-submission:edit:sha256:" + "2" * 64
    )
    edit_request = GoalEditRequest(
        expected_version=created.version,
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective="Preserve the exact durable edit provenance.",
        evidence_refs=[edit_evidence_ref],
    )
    edit_idempotency_ref = "idempotency-ref:goal-provenance:edit"
    edit_submission = service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-provenance:edit",
        operation="edit",
        goal_ref=created.goal_ref,
        request=edit_request,
        idempotency_ref=edit_idempotency_ref,
    )
    _edit_goal(
        service,
        created.goal_ref,
        edit_request,
        idempotency_ref=edit_idempotency_ref,
    )

    provenance = service.goals.mutation_provenance(created.goal_ref)
    assert [entry.goal_submission_fingerprint_ref for entry in provenance.entries] == [
        create_submission.request_fingerprint_ref,
        edit_submission.request_fingerprint_ref,
    ]


def test_goal_store_rejects_fabricated_approval_binding(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    fabricated = GoalMutationApprovalBinding(
        approval_ref="approval-ref:fabricated",
        approval_request_ref="approval-request-ref:fabricated",
        approval_decision_ref="approval-decision-ref:fabricated",
        approval_ledger_entry_hash_ref="entry-hash-ref:fabricated",
        exact_scope_ref="exact-scope-ref:fabricated",
        request_fingerprint_ref="request-fingerprint-ref:fabricated",
    )

    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_BINDING_MISMATCH",
    ):
        service.goals.create(
            request,
            idempotency_ref="idempotency-ref:fabricated-binding",
            approval_binding=fabricated,
        )


@pytest.mark.parametrize(
    ("approval_state", "expected_code"),
    [
        ("unknown", "GOAL_MUTATION_APPROVAL_UNKNOWN"),
        ("pending", "GOAL_MUTATION_APPROVAL_REQUIRED"),
        ("denied", "GOAL_MUTATION_APPROVAL_DENIED"),
        ("revoked", "GOAL_MUTATION_APPROVAL_REVOKED"),
        ("expired", "GOAL_MUTATION_APPROVAL_EXPIRED"),
    ],
)
def test_goal_mutation_requires_current_exact_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    approval_state: str,
    expected_code: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    idempotency_ref = f"idempotency-ref:approval-state:{approval_state}"
    approval_ref = "approval-ref:unknown"
    if approval_state != "unknown":
        spec = service.prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref=idempotency_ref,
        )
        approval_ref = spec.approval_ref
        if approval_state in {"denied", "revoked", "expired"}:
            service.decide_goal_mutation_approval(
                approval_request_ref=spec.approval_request_ref,
                decision=("deny" if approval_state == "denied" else "approve"),
                decision_reason_ref=f"reason-ref:approval-state:{approval_state}",
            )
        if approval_state == "revoked":
            service.revoke_goal_mutation_approval(
                approval_ref=spec.approval_ref,
                decision_reason_ref="reason-ref:approval-state:revoked",
            )
        if approval_state == "expired":
            monkeypatch.setattr(
                goal_runtime_module,
                "utc_now",
                lambda: spec.expires_at + timedelta(seconds=1),
            )

    with pytest.raises(GoalTransitionDeniedError, match=expected_code):
        service.create_goal(
            request,
            idempotency_ref=idempotency_ref,
            approval_ref=approval_ref,
        )
    assert service.goals.list() == []


def test_goal_approval_prepare_is_non_authorizing_and_restart_durable(
    tmp_path: Path,
) -> None:
    request = _create_request()
    idempotency_ref = "idempotency-ref:approval-prepare-restart"
    service = GoalRuntimeService(tmp_path)
    spec = service.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )

    assert service.goals.list() == []
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_REQUIRED",
    ):
        GoalRuntimeService(tmp_path).create_goal(
            request,
            idempotency_ref=idempotency_ref,
            approval_ref=spec.approval_ref,
        )

    restarted = GoalRuntimeService(tmp_path)
    decision = restarted.decide_goal_mutation_approval(
        approval_request_ref=spec.approval_request_ref,
        decision="approve",
        decision_reason_ref="reason-ref:approval-prepare-restart",
    )
    created, binding = restarted.create_goal(
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=spec.approval_ref,
    )
    assert created.state == GoalState.active.value
    assert binding.approval_ledger_entry_hash_ref == decision.entry_hash_ref


@pytest.mark.parametrize("failure_boundary", ["ledger", "head", "cleanup"])
def test_goal_approval_first_append_recovers_only_from_exact_append_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_boundary: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    original_atomic_write = goal_runtime_module._atomic_write
    original_cleanup = service._approvals._delete_append_intent  # noqa: SLF001
    failed = False

    if failure_boundary in {"ledger", "head"}:

        def fail_selected_write(path: Path, content: str) -> None:
            nonlocal failed
            if not failed and (
                (
                    failure_boundary == "ledger"
                    and path.name == "goal_mutation_approvals.jsonl"
                )
                or (
                    failure_boundary == "head"
                    and path.name == "goal_mutation_approvals_head.json"
                )
            ):
                failed = True
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_atomic_write(path, content)

        monkeypatch.setattr(goal_runtime_module, "_atomic_write", fail_selected_write)
    else:

        def fail_cleanup() -> None:
            nonlocal failed
            if not failed:
                failed = True
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_cleanup()

        monkeypatch.setattr(
            service._approvals,  # noqa: SLF001
            "_delete_append_intent",
            fail_cleanup,
        )

    request = _create_request()
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        service.prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref=f"idempotency-ref:approval-genesis:{failure_boundary}",
        )
    assert failed
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_APPEND_RECOVERY_REQUIRED",
    ):
        GoalRuntimeService(tmp_path)._approvals._load_consistent_entries()  # noqa: SLF001

    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)
    if failure_boundary == "cleanup":
        monkeypatch.setattr(
            service._approvals,  # noqa: SLF001
            "_delete_append_intent",
            original_cleanup,
        )
    recovered = GoalRuntimeService(tmp_path).prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=f"idempotency-ref:approval-genesis:{failure_boundary}",
    )

    assert recovered.operation == "create"
    assert (
        json.loads(
            (tmp_path / "goal_mutation_approvals_head.json").read_text(encoding="utf-8")
        )["entry_count"]
        == 1
    )
    assert not (tmp_path / "goal_mutation_approvals_append_intent.json").exists()


@pytest.mark.parametrize("failure_boundary", ["ledger", "head", "cleanup"])
def test_goal_approval_later_append_recovers_only_from_exact_append_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_boundary: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    spec = service.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=f"idempotency-ref:approval-append:{failure_boundary}",
    )
    original_atomic_write = goal_runtime_module._atomic_write
    original_cleanup = service._approvals._delete_append_intent  # noqa: SLF001
    failed = False

    if failure_boundary in {"ledger", "head"}:

        def fail_selected_write(path: Path, content: str) -> None:
            nonlocal failed
            if not failed and (
                (
                    failure_boundary == "ledger"
                    and path.name == "goal_mutation_approvals.jsonl"
                )
                or (
                    failure_boundary == "head"
                    and path.name == "goal_mutation_approvals_head.json"
                )
            ):
                failed = True
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_atomic_write(path, content)

        monkeypatch.setattr(goal_runtime_module, "_atomic_write", fail_selected_write)
    else:

        def fail_cleanup() -> None:
            nonlocal failed
            if not failed:
                failed = True
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_cleanup()

        monkeypatch.setattr(
            service._approvals,  # noqa: SLF001
            "_delete_append_intent",
            fail_cleanup,
        )

    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        service.decide_goal_mutation_approval(
            approval_request_ref=spec.approval_request_ref,
            decision="approve",
            decision_reason_ref=f"reason-ref:approval-append:{failure_boundary}",
        )
    assert failed
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_APPEND_RECOVERY_REQUIRED",
    ):
        GoalRuntimeService(tmp_path)._approvals._load_consistent_entries()  # noqa: SLF001

    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)
    if failure_boundary == "cleanup":
        monkeypatch.setattr(
            service._approvals,  # noqa: SLF001
            "_delete_append_intent",
            original_cleanup,
        )
    recovered = GoalRuntimeService(tmp_path).decide_goal_mutation_approval(
        approval_request_ref=spec.approval_request_ref,
        decision="approve",
        decision_reason_ref=f"reason-ref:approval-append:{failure_boundary}",
    )

    assert recovered.status == "approved"
    assert (
        json.loads(
            (tmp_path / "goal_mutation_approvals_head.json").read_text(encoding="utf-8")
        )["entry_count"]
        == 2
    )
    assert not (tmp_path / "goal_mutation_approvals_append_intent.json").exists()


def test_aggregate_read_repairs_an_exact_approval_append_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    original_atomic_write = goal_runtime_module._atomic_write
    failed = False

    def fail_head_once(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goal_mutation_approvals_head.json":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    monkeypatch.setattr(goal_runtime_module, "_atomic_write", fail_head_once)
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        service.prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=_create_request(),
            idempotency_ref="idempotency-ref:aggregate-approval-repair",
        )
    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)

    snapshot = GoalRuntimeService(tmp_path).aggregate_read_snapshot(
        run_ref=None,
        after_sequence=0,
        limit=10,
    )

    assert snapshot[3].goals == []
    assert not service._approvals.append_intent_path.exists()  # noqa: SLF001
    assert service._approvals._load_consistent_entries()[0].status == "pending"  # noqa: SLF001


def test_goal_approval_one_ahead_without_append_intent_fails_closed(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    spec = service.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:approval-unanchored-one-ahead",
    )
    old_head = (tmp_path / "goal_mutation_approvals_head.json").read_text(
        encoding="utf-8"
    )
    service.decide_goal_mutation_approval(
        approval_request_ref=spec.approval_request_ref,
        decision="approve",
        decision_reason_ref="reason-ref:approval-unanchored-one-ahead",
    )
    (tmp_path / "goal_mutation_approvals_head.json").write_text(
        old_head,
        encoding="utf-8",
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_HEAD_MANIFEST_MISMATCH",
    ):
        GoalRuntimeService(tmp_path)._approvals._load_consistent_entries()  # noqa: SLF001
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_HEAD_MANIFEST_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref="idempotency-ref:approval-unanchored-one-ahead",
        )


def test_goal_approval_append_intent_rejects_mismatch_and_old_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    spec = service.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:approval-intent-tamper",
    )
    original_atomic_write = goal_runtime_module._atomic_write
    interrupted = False

    def interrupt_head(path: Path, content: str) -> None:
        nonlocal interrupted
        if not interrupted and path.name == "goal_mutation_approvals_head.json":
            interrupted = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    monkeypatch.setattr(goal_runtime_module, "_atomic_write", interrupt_head)
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        service.decide_goal_mutation_approval(
            approval_request_ref=spec.approval_request_ref,
            decision="approve",
            decision_reason_ref="reason-ref:approval-intent-tamper",
        )
    intent_path = tmp_path / "goal_mutation_approvals_append_intent.json"
    exact_intent = intent_path.read_text(encoding="utf-8")
    tampered = json.loads(exact_intent)
    tampered["ledger_content_hash_ref"] = (
        "ledger-content-hash-ref:goal-mutation-approvals:sha256:" + "0" * 64
    )
    intent_path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_APPEND_INTENT_STATE_MISMATCH",
    ):
        GoalRuntimeService(tmp_path)._approvals._load_entries(  # noqa: SLF001
            repair_manifest=True
        )

    intent_path.write_text(exact_intent, encoding="utf-8")
    recovered = GoalRuntimeService(tmp_path)
    recovered.decide_goal_mutation_approval(
        approval_request_ref=spec.approval_request_ref,
        decision="approve",
        decision_reason_ref="reason-ref:approval-intent-tamper",
    )
    recovered.revoke_goal_mutation_approval(
        approval_ref=spec.approval_ref,
        decision_reason_ref="reason-ref:approval-intent-replay",
    )
    intent_path.write_text(exact_intent, encoding="utf-8")

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_APPEND_INTENT_STATE_MISMATCH",
    ):
        GoalRuntimeService(tmp_path)._approvals._load_entries(  # noqa: SLF001
            repair_manifest=True
        )


def test_goal_approval_valid_prefix_rollback_after_revoke_fails_closed(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    spec = service.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:approval-prefix-rollback",
    )
    service.decide_goal_mutation_approval(
        approval_request_ref=spec.approval_request_ref,
        decision="approve",
        decision_reason_ref="reason-ref:approval-prefix-rollback",
    )
    ledger_path = tmp_path / "goal_mutation_approvals.jsonl"
    approved_prefix = ledger_path.read_text(encoding="utf-8")
    service.revoke_goal_mutation_approval(
        approval_ref=spec.approval_ref,
        decision_reason_ref="reason-ref:approval-prefix-rollback-revoked",
    )
    ledger_path.write_text(approved_prefix, encoding="utf-8")

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_HEAD_MANIFEST_MISMATCH",
    ):
        GoalRuntimeService(tmp_path)._approvals._load_consistent_entries()  # noqa: SLF001


def test_goal_approval_rejects_cross_scope_and_decision_conflicts(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    spec = service.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:approval-cross-scope",
    )
    approved = service._approvals.decide(  # noqa: SLF001
        approval_request_ref=spec.approval_request_ref,
        decision="approve",
        decision_reason_ref="reason-ref:approval-cross-scope",
        actor_ref="operator-ref:local-user",
    )
    assert (
        service._approvals.decide(  # noqa: SLF001
            approval_request_ref=spec.approval_request_ref,
            decision="approve",
            decision_reason_ref="reason-ref:approval-cross-scope",
            actor_ref="operator-ref:local-user",
        ).entry_hash_ref
        == approved.entry_hash_ref
    )
    with pytest.raises(
        GoalIdempotencyConflictError,
        match="GOAL_MUTATION_APPROVAL_DECISION_CONFLICT",
    ):
        service._approvals.decide(  # noqa: SLF001
            approval_request_ref=spec.approval_request_ref,
            decision="approve",
            decision_reason_ref="reason-ref:approval-cross-scope",
            actor_ref="operator-ref:different-user",
        )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH",
    ):
        service.create_goal(
            request.model_copy(
                update={"objective": "A different exact request payload."}
            ),
            idempotency_ref="idempotency-ref:approval-cross-scope",
            approval_ref=spec.approval_ref,
        )

    revoked = service._approvals.revoke(  # noqa: SLF001
        approval_ref=spec.approval_ref,
        decision_reason_ref="reason-ref:approval-cross-scope-revoke",
        actor_ref="operator-ref:local-user",
    )
    assert (
        service._approvals.revoke(  # noqa: SLF001
            approval_ref=spec.approval_ref,
            decision_reason_ref="reason-ref:approval-cross-scope-revoke",
            actor_ref="operator-ref:local-user",
        ).entry_hash_ref
        == revoked.entry_hash_ref
    )
    with pytest.raises(
        GoalIdempotencyConflictError,
        match="GOAL_MUTATION_APPROVAL_REVOCATION_CONFLICT",
    ):
        service._approvals.revoke(  # noqa: SLF001
            approval_ref=spec.approval_ref,
            decision_reason_ref="reason-ref:approval-cross-scope-revoke",
            actor_ref="operator-ref:different-user",
        )


def test_committed_goal_replay_survives_revocation_with_original_ref_only(
    tmp_path: Path,
) -> None:
    request = _create_request()
    idempotency_ref = "idempotency-ref:committed-approval-replay"
    service = GoalRuntimeService(tmp_path)
    approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    created, binding = service.create_goal(
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=approval_ref,
    )
    entry_count = len(service.goals._load_consistent_entries())  # noqa: SLF001
    service.revoke_goal_mutation_approval(
        approval_ref=approval_ref,
        decision_reason_ref="reason-ref:committed-approval-replay-revoke",
    )

    restarted = GoalRuntimeService(tmp_path)
    replayed, replay_binding = restarted.create_goal(
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=approval_ref,
    )
    assert replayed == created
    assert replay_binding == binding
    assert len(restarted.goals._load_consistent_entries()) == entry_count  # noqa: SLF001
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH",
    ):
        restarted.create_goal(
            request,
            idempotency_ref=idempotency_ref,
            approval_ref="approval-ref:different",
        )
    assert len(restarted.goals._load_consistent_entries()) == entry_count  # noqa: SLF001


def test_committed_run_event_replay_survives_revocation_with_original_ref_only(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:committed-event-approval-replay",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.run_started,
        safe_summary="A bounded run began with exact approval provenance.",
        idempotency_ref="idempotency-ref:committed-event-approval-replay",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    approval_ref = _approved_mutation_ref(
        service,
        operation="append-run-event",
        goal_ref=None,
        request=request,
        idempotency_ref=request.idempotency_ref,
    )
    created = service.append_run_event(request, approval_ref=approval_ref)
    service.revoke_goal_mutation_approval(
        approval_ref=approval_ref,
        decision_reason_ref="reason-ref:committed-event-approval-replay-revoke",
    )

    restarted = GoalRuntimeService(tmp_path)
    assert restarted.append_run_event(request, approval_ref=approval_ref) == created
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH",
    ):
        restarted.append_run_event(
            request,
            approval_ref="approval-ref:different",
        )
    assert len(restarted.events.replay(request.run_ref).events) == 1


@pytest.mark.parametrize(
    "reserved_ref",
    [
        "idempotency-ref:goal-completion-event:forged",
        "idempotency-ref:runtime-run-started:forged",
        "idempotency-ref:runtime-receipt-recorded:forged",
        "idempotency-ref:runtime-failed-terminal:forged",
    ],
)
def test_public_event_approval_rejects_trusted_core_idempotency_namespaces(
    tmp_path: Path,
    reserved_ref: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:reserved-trusted-core-namespace",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.run_started,
        safe_summary="A public metadata event attempted a reserved namespace.",
        idempotency_ref=reserved_ref,
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="RUN_EVENT_TRUSTED_IDEMPOTENCY_NAMESPACE_RESERVED",
    ):
        service.prepare_goal_mutation_approval(
            operation="append-run-event",
            goal_ref=None,
            request=request,
            idempotency_ref=reserved_ref,
        )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="RUN_EVENT_TRUSTED_IDEMPOTENCY_NAMESPACE_RESERVED",
    ):
        service.append_run_event(
            request,
            approval_ref="approval-ref:forged",
        )
    assert not service._approvals.path.exists()  # noqa: SLF001
    assert not service._events.path.exists()  # noqa: SLF001


def test_committed_goal_and_event_replay_survive_approval_expiry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    goal_request = _create_request()
    goal_idempotency_ref = "idempotency-ref:committed-goal-expired-approval"
    goal_approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=goal_request,
        idempotency_ref=goal_idempotency_ref,
    )
    created_goal, _goal_binding = service.create_goal(
        goal_request,
        idempotency_ref=goal_idempotency_ref,
        approval_ref=goal_approval_ref,
    )
    event_request = DurableRunEventAppendRequest(
        run_ref="run-ref:committed-event-expired-approval",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.run_started,
        safe_summary="A bounded run began before its exact approval expired.",
        idempotency_ref="idempotency-ref:committed-event-expired-approval",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    event_approval_ref = _approved_mutation_ref(
        service,
        operation="append-run-event",
        goal_ref=None,
        request=event_request,
        idempotency_ref=event_request.idempotency_ref,
    )
    created_event = service.append_run_event(
        event_request,
        approval_ref=event_approval_ref,
    )
    monkeypatch.setattr(
        goal_runtime_module,
        "utc_now",
        lambda: datetime(2036, 7, 25, tzinfo=timezone.utc),
    )

    restarted = GoalRuntimeService(tmp_path)
    replayed_goal, _replay_binding = restarted.create_goal(
        goal_request,
        idempotency_ref=goal_idempotency_ref,
        approval_ref=goal_approval_ref,
    )
    replayed_event = restarted.append_run_event(
        event_request,
        approval_ref=event_approval_ref,
    )
    assert replayed_goal == created_goal
    assert replayed_event == created_event
    assert len(restarted.goals._load_consistent_entries()) == 1  # noqa: SLF001
    assert len(restarted.events.replay(event_request.run_ref).events) == 1


def test_pre_ledger_goal_replay_fails_closed(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    idempotency_ref = "idempotency-ref:pre-ledger-replay"
    approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    service.create_goal(
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=approval_ref,
    )
    [entry] = service.goals._load_consistent_entries()  # noqa: SLF001
    legacy_draft = entry.model_copy(
        update={
            "schema_version": "goal_journal.v1",
            "approval_ledger_entry_hash_ref": None,
            "approval_request_fingerprint_ref": None,
            "approval_exact_scope_ref": None,
            "request_payload": None,
            "entry_hash_ref": "entry-hash-ref:pending",
        }
    )
    legacy = legacy_draft.model_copy(
        update={"entry_hash_ref": service.goals._entry_hash(legacy_draft)}  # noqa: SLF001
    )
    _replace_goal_journal_for_tamper(
        service,
        [legacy],
        rewrite_independent_anchor=True,
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_PROVENANCE_MISSING",
    ):
        GoalRuntimeService(tmp_path).create_goal(
            request,
            idempotency_ref=idempotency_ref,
            approval_ref=approval_ref,
        )


def test_v2_goal_journal_remains_read_compatible(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:v2-journal-compatibility:create",
    )
    [entry] = service.goals._load_consistent_entries()  # noqa: SLF001
    v2_draft = entry.model_copy(
        update={
            "schema_version": "goal_journal.v2",
            "request_payload": None,
            "entry_hash_ref": "entry-hash-ref:pending",
        }
    )
    v2_entry = v2_draft.model_copy(
        update={
            "entry_hash_ref": service.goals._entry_hash(v2_draft)  # noqa: SLF001
        }
    )
    _replace_goal_journal_for_tamper(
        service,
        [v2_entry],
        rewrite_independent_anchor=True,
    )

    [recovered] = GoalRuntimeService(tmp_path).goal_lifecycle_read_model(
        include_cleared=True,
    ).goals

    assert recovered == created


@pytest.mark.parametrize(
    ("grant_field", "replacement"),
    [
        ("run_id", "run-ref:tampered"),
        ("approved_actions", ["goal_mutation_edit"]),
        ("approved_resource_refs", ["resource-ref:tampered"]),
        ("purpose", "A different safe purpose."),
        ("event_ref", "event-ref:tampered"),
        ("trace_id", "trace-ref:tampered"),
    ],
)
def test_committed_replay_rejects_tampered_canonical_grant_scope(
    tmp_path: Path,
    grant_field: str,
    replacement: object,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    idempotency_ref = f"idempotency-ref:grant-tamper:{grant_field}"
    approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    service.create_goal(
        request,
        idempotency_ref=idempotency_ref,
        approval_ref=approval_ref,
    )
    entries = service._approvals._load_entries()  # noqa: SLF001
    approved = entries[-1]
    assert approved.approval_grant is not None
    tampered_grant = approved.approval_grant.model_copy(
        update={grant_field: replacement}
    )
    tampered_draft = approved.model_copy(
        update={
            "approval_grant": tampered_grant,
            "entry_hash_ref": "entry-hash-ref:pending",
        }
    )
    tampered = tampered_draft.model_copy(
        update={
            "entry_hash_ref": service._approvals._entry_hash(tampered_draft)  # noqa: SLF001
        }
    )
    tampered_approval_entries = [*entries[:-1], tampered]
    service._approvals.path.write_text(  # noqa: SLF001
        "".join(entry.model_dump_json() + "\n" for entry in tampered_approval_entries),
        encoding="utf-8",
    )
    service._approvals._write_head_manifest(  # noqa: SLF001
        service._approvals._build_head_manifest(  # noqa: SLF001
            tampered_approval_entries
        )
    )
    [journal_entry] = service.goals._load_consistent_entries()  # noqa: SLF001
    tampered_decision_ref = goal_runtime_module._sha256_ref(  # noqa: SLF001
        "approval-decision-ref:goal-mutation",
        {
            "approval_ref": approval_ref,
            "ledger_entry_hash_ref": tampered.entry_hash_ref,
            "status": "approved",
        },
    )
    journal_draft = journal_entry.model_copy(
        update={
            "approval_decision_ref": tampered_decision_ref,
            "approval_ledger_entry_hash_ref": tampered.entry_hash_ref,
            "entry_hash_ref": "entry-hash-ref:pending",
        }
    )
    tampered_journal = journal_draft.model_copy(
        update={
            "entry_hash_ref": service.goals._entry_hash(journal_draft)  # noqa: SLF001
        }
    )
    _replace_goal_journal_for_tamper(
        service,
        [tampered_journal],
        rewrite_independent_anchor=True,
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_PROVENANCE_INVALID",
    ):
        GoalRuntimeService(tmp_path).create_goal(
            request,
            idempotency_ref=idempotency_ref,
            approval_ref=approval_ref,
        )


def test_revoke_serializes_after_inflight_goal_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    idempotency_ref = "idempotency-ref:approval-revoke-race"
    approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    entered_commit = threading.Event()
    release_commit = threading.Event()
    original_create = service.goals.create

    def blocked_create(*args: object, **kwargs: object) -> PersistentGoal:
        entered_commit.set()
        assert release_commit.wait(timeout=5)
        return original_create(*args, **kwargs)

    monkeypatch.setattr(service.goals, "create", blocked_create)
    results: dict[str, object] = {}

    def mutate() -> None:
        try:
            results["goal"] = service.create_goal(
                request,
                idempotency_ref=idempotency_ref,
                approval_ref=approval_ref,
            )[0]
        except BaseException as exc:  # pragma: no cover - diagnostic guard
            results["mutation_error"] = exc

    def revoke() -> None:
        try:
            results["revoked"] = service.revoke_goal_mutation_approval(
                approval_ref=approval_ref,
                decision_reason_ref="reason-ref:approval-revoke-race",
            )
        except BaseException as exc:  # pragma: no cover - diagnostic guard
            results["revoke_error"] = exc

    mutation_thread = threading.Thread(target=mutate)
    revoke_thread = threading.Thread(target=revoke)
    mutation_thread.start()
    assert entered_commit.wait(timeout=5)
    revoke_thread.start()
    assert revoke_thread.is_alive()
    release_commit.set()
    mutation_thread.join(timeout=5)
    revoke_thread.join(timeout=5)

    assert not mutation_thread.is_alive()
    assert not revoke_thread.is_alive()
    assert "mutation_error" not in results
    assert "revoke_error" not in results
    assert isinstance(results["goal"], PersistentGoal)
    assert getattr(results["revoked"], "status", None) == "revoked"
    assert (
        service._approvals._load_entries()[-1].status  # noqa: SLF001
        == "revoked"
    )
    assert (
        GoalRuntimeService(tmp_path).create_goal(
            request,
            idempotency_ref=idempotency_ref,
            approval_ref=approval_ref,
        )[0]
        == results["goal"]
    )


def test_transition_replay_rejects_fabricated_approval_before_recovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:replay-approval:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:replay-approval:request",
        ),
        idempotency_ref="idempotency-ref:replay-approval:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    evidence = _completion_evidence(requested)
    transition = GoalTransitionRequest(
        expected_version=requested.version,
        transition=GoalTransitionKind.verify_completion,
        reason_ref="reason-ref:replay-approval:verify",
        completion_evidence=evidence,
    )
    original_append = service._events._append_locked  # noqa: SLF001

    def interrupt_completion_event(
        request: DurableRunEventAppendRequest,
        **kwargs: object,
    ) -> DurableRunEvent:
        if request.event_kind == DurableRunEventKind.completion_verified.value:
            raise OSError("simulated completion projection interruption")
        return original_append(request, **kwargs)

    monkeypatch.setattr(
        service._events,  # noqa: SLF001
        "_append_locked",
        interrupt_completion_event,
    )
    with pytest.raises(OSError, match="simulated completion projection interruption"):
        _transition_goal(
            service,
            created.goal_ref,
            transition,
            idempotency_ref="idempotency-ref:replay-approval:verify",
        )

    recovered = GoalRuntimeService(tmp_path)
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH",
    ):
        recovered.transition_goal(
            created.goal_ref,
            transition,
            idempotency_ref="idempotency-ref:replay-approval:verify",
            approval_ref="approval-ref:fabricated",
        )

    assert not any(
        event.event_kind == DurableRunEventKind.completion_verified.value
        for event in recovered.events.replay(evidence.run_ref).events
    )


def test_aggregate_read_repairs_committed_completion_projection_after_crash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:aggregate-completion:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:aggregate-completion:request",
        ),
        idempotency_ref="idempotency-ref:aggregate-completion:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    evidence = _completion_evidence(requested)
    transition = GoalTransitionRequest(
        expected_version=requested.version,
        transition=GoalTransitionKind.verify_completion,
        reason_ref="reason-ref:aggregate-completion:verify",
        completion_evidence=evidence,
    )
    original_append = service._events._append_locked  # noqa: SLF001

    def interrupt_completion_event(
        request: DurableRunEventAppendRequest,
        **kwargs: object,
    ) -> DurableRunEvent:
        if request.event_kind == DurableRunEventKind.completion_verified.value:
            raise OSError("simulated completion projection interruption")
        return original_append(request, **kwargs)

    monkeypatch.setattr(
        service._events,  # noqa: SLF001
        "_append_locked",
        interrupt_completion_event,
    )
    with pytest.raises(OSError, match="simulated completion projection interruption"):
        _transition_goal(
            service,
            created.goal_ref,
            transition,
            idempotency_ref="idempotency-ref:aggregate-completion:verify",
        )
    monkeypatch.setattr(
        service._events,  # noqa: SLF001
        "_append_locked",
        original_append,
    )

    replay = GoalRuntimeService(tmp_path).aggregate_read_snapshot(
        run_ref=evidence.run_ref,
        after_sequence=0,
        limit=10,
    )[0]

    assert replay is not None
    assert replay.events[-1].event_kind == (
        DurableRunEventKind.completion_verified.value
    )
    assert evidence.receipt_ref in replay.events[-1].receipt_refs
    assert evidence.proof_ref in replay.events[-1].proof_refs
    assert evidence.evidence_ref in replay.events[-1].proof_refs
    assert replay.events[-1].criterion_verifier_bindings


def test_goal_completion_requires_linked_durable_receipt_and_proof(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-create-completion",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=1,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:success-criteria-claimed",
        ),
        idempotency_ref="idempotency-ref:goal-completion-request",
    )
    evidence = _completion_evidence(requested)

    with pytest.raises(
        ValueError,
        match="GOAL_UNVERIFIED_COMPLETION_PROOF_DENIED",
    ):
        PersistentGoal.model_validate(
            requested.model_copy(
                update={"completion_plan_ref": "plan-ref:accepted-local:one"}
            ).model_dump()
        )

    with pytest.raises(
        GoalTransitionDeniedError,
        match="DURABLE_RECEIPT_NOT_FOUND",
    ):
        _transition_goal(
            service,
            created.goal_ref,
            GoalTransitionRequest(
                expected_version=requested.version,
                transition=GoalTransitionKind.verify_completion,
                reason_ref="reason-ref:deterministic-verifier",
                completion_evidence=evidence,
            ),
            idempotency_ref="idempotency-ref:goal-verify-before-receipt",
        )

    _append_receipt(service, goal_ref=created.goal_ref)
    verified = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=requested.version,
            transition=GoalTransitionKind.verify_completion,
            reason_ref="reason-ref:deterministic-verifier",
            completion_evidence=evidence,
        ),
        idempotency_ref="idempotency-ref:goal-verify-after-receipt",
    )

    assert verified.state == GoalState.verified_complete.value
    assert verified.completion_receipt_ref == evidence.receipt_ref
    assert verified.completion_proof_ref == evidence.proof_ref
    assert verified.completion_criterion_proof_refs == evidence.criterion_proof_refs
    assert verified.completion_verifier_ref == evidence.verifier_ref
    assert verified.completion_plan_ref == "plan-ref:accepted-local:one"
    assert evidence.evidence_ref in verified.evidence_refs
    assert verified.model_output_authoritative is False


def test_completion_rejects_recomputed_public_event_producer_substitution(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:completion-producer:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:completion-producer:request",
        ),
        idempotency_ref="idempotency-ref:completion-producer:request",
    )
    evidence = _completion_evidence(requested)
    public_request = DurableRunEventAppendRequest(
        run_ref=evidence.run_ref,
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.evidence_linked,
        safe_summary="The operator linked bounded metadata evidence.",
        proof_refs=["proof-ref:completion-producer:metadata"],
        goal_ref=requested.goal_ref,
        plan_ref="plan-ref:accepted-local:one",
        idempotency_ref="idempotency-ref:completion-producer:public-event",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    approval_ref = _approved_mutation_ref(
        service,
        operation="append-run-event",
        goal_ref=None,
        request=public_request,
        idempotency_ref=public_request.idempotency_ref,
    )
    public_event = service.append_run_event(
        public_request,
        approval_ref=approval_ref,
    )
    substituted_draft = goal_runtime_module.DurableRunEvent.model_validate(
        {
            **public_event.model_dump(mode="json"),
            "producer_class": "trusted_core",
            "event_kind": DurableRunEventKind.receipt_recorded.value,
            "event_ref": goal_runtime_module._sha256_ref(  # noqa: SLF001
                "runtime-run-event-ref",
                {
                    "run_ref": public_event.run_ref,
                    "sequence": public_event.sequence,
                    "event_kind": DurableRunEventKind.receipt_recorded.value,
                },
            ),
            "proof_refs": list(
                dict.fromkeys(
                    [
                        *evidence.criterion_proof_refs,
                        evidence.proof_ref,
                        *(
                            binding.evaluator_receipt_ref
                            for binding in _criterion_bindings(
                                requested,
                                evidence.criterion_proof_refs,
                            )
                        ),
                    ]
                )
            ),
            "receipt_refs": [evidence.receipt_ref],
            "criterion_verifier_bindings": [
                binding.model_dump(mode="json")
                for binding in _criterion_bindings(
                    requested,
                    evidence.criterion_proof_refs,
                )
            ],
            "goal_mutation_approval_ref": None,
            "goal_mutation_approval_decision_ref": None,
            "goal_mutation_approval_ledger_entry_hash_ref": None,
            "trusted_source_record_hash_ref": goal_runtime_module._sha256_ref(  # noqa: SLF001
                "record-hash-ref:trusted-run-event-source",
                {"forged_from": public_event.event_ref},
            ),
            "event_hash_ref": "event-hash-ref:pending",
        }
    )
    substituted = substituted_draft.model_copy(
        update={
            "event_hash_ref": service._events._event_hash(  # noqa: SLF001
                substituted_draft
            )
        }
    )
    events = service._events._load_events()  # noqa: SLF001
    service._events._write_events(  # noqa: SLF001
        [
            substituted if event.event_ref == public_event.event_ref else event
            for event in events
        ]
    )
    tombstones = service._events._load_idempotency_tombstones(  # noqa: SLF001
        events
    )
    key = (public_event.run_ref, public_event.idempotency_ref)
    prior_tombstone = tombstones[key]
    substituted_request = (
        goal_runtime_module.DurableRunEventAppendRequest.model_validate(
            service._events._event_request_payload(substituted)  # noqa: SLF001
        )
    )
    substituted_tombstone_draft = prior_tombstone.model_copy(
        update={
            "request_fingerprint_ref": service._events._request_fingerprint(  # noqa: SLF001
                substituted_request
            ),
            "event": substituted,
            "tombstone_hash_ref": "tombstone-hash-ref:pending",
        }
    )
    substituted_tombstone = substituted_tombstone_draft.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                substituted_tombstone_draft
            )
        }
    )
    tombstones[key] = substituted_tombstone
    service._events._write_idempotency_tombstones(  # noqa: SLF001
        tombstones.values()
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_GENERATION_HEAD_MISMATCH",
    ):
        _transition_goal(
            GoalRuntimeService(tmp_path),
            requested.goal_ref,
            GoalTransitionRequest(
                expected_version=requested.version,
                transition=GoalTransitionKind.verify_completion,
                reason_ref="reason-ref:completion-producer:verify",
                completion_evidence=evidence,
            ),
            idempotency_ref="idempotency-ref:completion-producer:verify",
        )
    assert (
        GoalRuntimeService(tmp_path).goals.get(requested.goal_ref).state
        == GoalState.complete_requested.value
    )


def test_receipt_event_rejects_self_attested_trusted_core_provenance(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:trusted-source-tombstone",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.receipt_recorded,
        safe_summary="The trusted Core claimed a bounded successful receipt.",
        proof_refs=["proof-ref:trusted-source-tombstone"],
        receipt_refs=["receipt-ref:trusted-source-tombstone"],
        idempotency_ref="idempotency-ref:trusted-source-test",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="RUN_EVENT_TRUSTED_PRODUCER_REQUIRED",
    ):
        service._events.append(  # noqa: SLF001
            request,
            trusted_source=goal_runtime_module.TrustedRunEventSourceBinding(
                source_kind="trusted_core_internal",
                source_ref="source-ref:trusted-source-tombstone",
                source_fingerprint_ref=(
                    "source-fingerprint-ref:trusted-source-tombstone"
                ),
            ),
        )
    assert not service._events.path.exists()  # noqa: SLF001


def test_runtime_trusted_event_must_equal_canonical_producer_projection(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=service,
    )
    result = gateway.invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            mission_ref="mission-ref:trusted-projection-binding",
            safe_summary="Inspect bounded status for canonical projection binding.",
        ),
        idempotency_ref="idempotency-ref:trusted-projection-binding",
    )
    events = service._events._load_events()  # noqa: SLF001
    terminal = next(
        event
        for event in events
        if event.run_ref == result.record.invocation_ref
        and event.event_kind == DurableRunEventKind.receipt_recorded.value
    )
    key = (terminal.run_ref, terminal.idempotency_ref)
    event_key_ref = service._events._event_key_ref(*key)  # noqa: SLF001
    trusted_sources = service._events._load_trusted_sources()  # noqa: SLF001
    original_source = trusted_sources[event_key_ref]
    substituted_request = DurableRunEventAppendRequest.model_validate(
        {
            **service._events._event_request_payload(terminal),  # noqa: SLF001
            "safe_summary": (
                "A recomputed wrapper claims a different accepted projection."
            ),
        }
    )
    substituted_fingerprint = service._events._request_fingerprint(  # noqa: SLF001
        substituted_request
    )
    substituted_source = service._events._trusted_source_record(  # noqa: SLF001
        event_key_ref=event_key_ref,
        request_fingerprint_ref=substituted_fingerprint,
        binding=goal_runtime_module.TrustedRunEventSourceBinding(
            source_kind=original_source.source_kind,
            source_ref=original_source.source_ref,
            source_fingerprint_ref=original_source.source_fingerprint_ref,
        ),
    )
    substituted_draft = terminal.model_copy(
        update={
            "safe_summary": substituted_request.safe_summary,
            "trusted_source_record_hash_ref": substituted_source.record_hash_ref,
            "event_hash_ref": "event-hash-ref:pending",
        }
    )
    substituted = substituted_draft.model_copy(
        update={
            "event_hash_ref": service._events._event_hash(  # noqa: SLF001
                substituted_draft
            )
        }
    )
    tombstones = service._events._load_idempotency_tombstones(events)  # noqa: SLF001
    tombstone_draft = tombstones[key].model_copy(
        update={
            "request_fingerprint_ref": substituted_fingerprint,
            "event": substituted,
            "tombstone_hash_ref": "tombstone-hash-ref:pending",
        }
    )
    tombstones[key] = tombstone_draft.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                tombstone_draft
            )
        }
    )
    substituted_events = [
        substituted if event.event_ref == terminal.event_ref else event
        for event in events
    ]
    service._events._write_events(substituted_events)  # noqa: SLF001
    service._events._write_idempotency_tombstones(  # noqa: SLF001
        tombstones.values()
    )
    trusted_sources[event_key_ref] = substituted_source
    service._events._write_trusted_sources(trusted_sources.values())  # noqa: SLF001
    service._events._write_run_event_generation_head(  # noqa: SLF001
        service._events._build_run_event_generation_head(  # noqa: SLF001
            substituted_events,
            list(tombstones.values()),
            list(trusted_sources.values()),
        )
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_TRUSTED_SOURCE_BINDING_MISMATCH",
    ):
        service.aggregate_read_snapshot(
            run_ref=result.record.invocation_ref,
            after_sequence=0,
            limit=10,
        )


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("run_ref", "run-ref:substituted-evaluator-event"),
        ("plan_ref", "plan-ref:substituted-evaluator-event"),
        ("proof_refs", "append-proof-ref"),
    ],
)
def test_runtime_evaluator_event_must_equal_producer_bound_request(
    tmp_path: Path,
    field_name: str,
    replacement: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref=f"idempotency-ref:evaluator-event-binding:{field_name}",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    events = service._events._load_events()  # noqa: SLF001
    original = next(
        event
        for event in events
        if event.goal_ref == created.goal_ref
        and event.event_kind == DurableRunEventKind.receipt_recorded.value
    )
    old_key = (original.run_ref, original.idempotency_ref)
    old_event_key_ref = service._events._event_key_ref(*old_key)  # noqa: SLF001
    sources = service._events._load_trusted_sources()  # noqa: SLF001
    original_source = sources[old_event_key_ref]
    assert original_source.source_kind == "runtime_evaluator_receipt"
    effective_replacement: str | list[str] = (
        [*original.proof_refs, "proof-ref:substituted-evaluator-event"]
        if field_name == "proof_refs"
        else replacement
    )

    substituted_request = DurableRunEventAppendRequest.model_validate(
        {
            **service._events._event_request_payload(original),  # noqa: SLF001
            field_name: effective_replacement,
        }
    )
    substituted_fingerprint = service._events._request_fingerprint(  # noqa: SLF001
        substituted_request
    )
    new_key = (
        substituted_request.run_ref,
        substituted_request.idempotency_ref,
    )
    new_event_key_ref = service._events._event_key_ref(*new_key)  # noqa: SLF001
    substituted_source = service._events._trusted_source_record(  # noqa: SLF001
        event_key_ref=new_event_key_ref,
        request_fingerprint_ref=substituted_fingerprint,
        binding=goal_runtime_module.TrustedRunEventSourceBinding(
            source_kind=original_source.source_kind,
            source_ref=original_source.source_ref,
            source_fingerprint_ref=original_source.source_fingerprint_ref,
        ),
    )
    substituted_draft = original.model_copy(
        update={
            field_name: effective_replacement,
            "event_ref": goal_runtime_module._sha256_ref(  # noqa: SLF001
                "runtime-run-event-ref",
                {
                    "run_ref": substituted_request.run_ref,
                    "sequence": original.sequence,
                    "event_kind": original.event_kind,
                },
            ),
            "trusted_source_record_hash_ref": substituted_source.record_hash_ref,
            "event_hash_ref": "event-hash-ref:pending",
        }
    )
    substituted = substituted_draft.model_copy(
        update={
            "event_hash_ref": service._events._event_hash(  # noqa: SLF001
                substituted_draft
            )
        }
    )
    tombstones = service._events._load_idempotency_tombstones(events)  # noqa: SLF001
    prior_tombstone = tombstones.pop(old_key)
    substituted_tombstone_draft = prior_tombstone.model_copy(
        update={
            "run_ref": substituted.run_ref,
            "request_fingerprint_ref": substituted_fingerprint,
            "event": substituted,
            "tombstone_hash_ref": "tombstone-hash-ref:pending",
        }
    )
    substituted_tombstone = substituted_tombstone_draft.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                substituted_tombstone_draft
            )
        }
    )
    tombstones[new_key] = substituted_tombstone
    substituted_events = [
        substituted if event.event_ref == original.event_ref else event
        for event in events
    ]
    sources.pop(old_event_key_ref)
    sources[new_event_key_ref] = substituted_source
    service._events._write_events(substituted_events)  # noqa: SLF001
    service._events._write_idempotency_tombstones(  # noqa: SLF001
        tombstones.values()
    )
    service._events._write_trusted_sources(sources.values())  # noqa: SLF001
    service._events._write_run_event_generation_head(  # noqa: SLF001
        service._events._build_run_event_generation_head(  # noqa: SLF001
            substituted_events,
            list(tombstones.values()),
            list(sources.values()),
        )
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_TRUSTED_SOURCE_PROVENANCE_MISMATCH",
    ):
        service.aggregate_read_snapshot(
            run_ref=substituted.run_ref,
            after_sequence=0,
            limit=10,
        )


def test_completion_event_must_equal_canonical_journal_projection(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:completion-projection:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:completion-projection:request",
        ),
        idempotency_ref="idempotency-ref:completion-projection:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=requested.version,
            transition=GoalTransitionKind.verify_completion,
            reason_ref="reason-ref:completion-projection:verify",
            completion_evidence=_completion_evidence(requested),
        ),
        idempotency_ref="idempotency-ref:completion-projection:verify",
    )
    events = service._events._load_events()  # noqa: SLF001
    completion = next(
        event
        for event in events
        if event.event_kind == DurableRunEventKind.completion_verified.value
    )
    key = (completion.run_ref, completion.idempotency_ref)
    event_key_ref = service._events._event_key_ref(*key)  # noqa: SLF001
    sources = service._events._load_trusted_sources()  # noqa: SLF001
    original_source = sources[event_key_ref]
    substituted_request = DurableRunEventAppendRequest.model_validate(
        {
            **service._events._event_request_payload(completion),  # noqa: SLF001
            "goal_ref": "goal-ref:sha256:" + "f" * 64,
        }
    )
    substituted_fingerprint = service._events._request_fingerprint(  # noqa: SLF001
        substituted_request
    )
    substituted_source = service._events._trusted_source_record(  # noqa: SLF001
        event_key_ref=event_key_ref,
        request_fingerprint_ref=substituted_fingerprint,
        binding=goal_runtime_module.TrustedRunEventSourceBinding(
            source_kind=original_source.source_kind,
            source_ref=original_source.source_ref,
            source_fingerprint_ref=original_source.source_fingerprint_ref,
        ),
    )
    substituted_draft = completion.model_copy(
        update={
            "goal_ref": substituted_request.goal_ref,
            "trusted_source_record_hash_ref": substituted_source.record_hash_ref,
            "event_hash_ref": "event-hash-ref:pending",
        }
    )
    substituted = substituted_draft.model_copy(
        update={
            "event_hash_ref": service._events._event_hash(  # noqa: SLF001
                substituted_draft
            )
        }
    )
    tombstones = service._events._load_idempotency_tombstones(events)  # noqa: SLF001
    tombstone_draft = tombstones[key].model_copy(
        update={
            "request_fingerprint_ref": substituted_fingerprint,
            "event": substituted,
            "tombstone_hash_ref": "tombstone-hash-ref:pending",
        }
    )
    tombstones[key] = tombstone_draft.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                tombstone_draft
            )
        }
    )
    service._events._write_events(  # noqa: SLF001
        [
            substituted if event.event_ref == completion.event_ref else event
            for event in events
        ]
    )
    service._events._write_idempotency_tombstones(  # noqa: SLF001
        tombstones.values()
    )
    sources[event_key_ref] = substituted_source
    service._events._write_trusted_sources(sources.values())  # noqa: SLF001

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_GENERATION_HEAD_MISMATCH",
    ):
        service.aggregate_read_snapshot(
            run_ref=completion.run_ref,
            after_sequence=0,
            limit=10,
        )


@pytest.mark.parametrize(
    "entry_point",
    ["reconcile", "runtime_projection_guard", "sync_runtime_invocations"],
)
def test_completion_reconciliation_requires_exact_approval_generation(
    tmp_path: Path,
    entry_point: str,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref=f"idempotency-ref:reconcile-approval:{entry_point}:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref=f"reason-ref:reconcile-approval:{entry_point}:request",
        ),
        idempotency_ref=f"idempotency-ref:reconcile-approval:{entry_point}:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    evidence = _completion_evidence(requested)
    verified = _transition_goal(
        service,
        requested.goal_ref,
        GoalTransitionRequest(
            expected_version=requested.version,
            transition=GoalTransitionKind.verify_completion,
            reason_ref=f"reason-ref:reconcile-approval:{entry_point}:verify",
            completion_evidence=evidence,
        ),
        idempotency_ref=f"idempotency-ref:reconcile-approval:{entry_point}:verify",
    )
    assert verified.state == GoalState.verified_complete.value
    events = service._events._load_events()  # noqa: SLF001
    retained = [
        event
        for event in events
        if event.event_kind != DurableRunEventKind.completion_verified.value
    ]
    tombstones = service._events._load_idempotency_tombstones(events)  # noqa: SLF001
    retained_tombstones = [
        tombstone
        for tombstone in tombstones.values()
        if tombstone.event.event_kind != DurableRunEventKind.completion_verified.value
    ]
    service._events._write_events(retained)  # noqa: SLF001
    service._events._write_idempotency_tombstones(  # noqa: SLF001
        retained_tombstones
    )
    service._approvals.head_path.unlink()  # noqa: SLF001
    restarted = GoalRuntimeService(tmp_path / "goals")

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_HEAD_MANIFEST_MISSING",
    ):
        if entry_point == "reconcile":
            restarted.reconcile_durable_events()
        elif entry_point == "runtime_projection_guard":
            with restarted.runtime_projection_guard(
                None,
                operation_idempotency_ref=(
                    "idempotency-ref:reconcile-approval:runtime-guard"
                ),
            ):
                pass
        else:
            restarted.sync_runtime_invocations(
                [],
                invocation_store=RuntimeInvocationStore(tmp_path / "runtime"),
            )
    assert not any(
        event.event_kind == DurableRunEventKind.completion_verified.value
        for event in restarted._events._load_events()  # noqa: SLF001
    )


def test_goal_completion_rejects_already_terminal_run_before_journal_commit(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:terminal-preflight:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:terminal-preflight:request",
        ),
        idempotency_ref="idempotency-ref:terminal-preflight:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:accepted-local:one",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.cancelled,
            safe_summary="The accepted local run ended with a proof-backed cancellation.",
            proof_refs=["proof-ref:terminal-preflight:cancelled"],
            receipt_refs=["receipt-ref:terminal-preflight:cancelled"],
            goal_ref=created.goal_ref,
            idempotency_ref="idempotency-ref:terminal-preflight:cancelled",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    evidence = _completion_evidence(requested)

    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_COMPLETION_TERMINAL_STREAM_FENCE",
    ):
        _transition_goal(
            service,
            created.goal_ref,
            GoalTransitionRequest(
                expected_version=requested.version,
                transition=GoalTransitionKind.verify_completion,
                reason_ref="reason-ref:terminal-preflight:verify",
                completion_evidence=evidence,
            ),
            idempotency_ref="idempotency-ref:terminal-preflight:verify",
        )

    restored = GoalRuntimeService(tmp_path).goals.get(created.goal_ref)
    assert restored.state == GoalState.complete_requested.value
    assert restored.version == requested.version


def test_goal_completion_intent_recovery_revalidates_authoritative_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:completion-intent:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:completion-intent:request",
        ),
        idempotency_ref="idempotency-ref:completion-intent:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    transition = GoalTransitionRequest(
        expected_version=requested.version,
        transition=GoalTransitionKind.verify_completion,
        reason_ref="reason-ref:completion-intent:verify",
        completion_evidence=_completion_evidence(requested),
    )
    operation_idempotency_ref = "idempotency-ref:completion-intent:verify"
    approval_ref = _approved_mutation_ref(
        service,
        operation="transition",
        goal_ref=created.goal_ref,
        request=transition,
        idempotency_ref=operation_idempotency_ref,
    )
    original_atomic_write = goal_runtime_module._atomic_write
    failed = False

    def interrupt_journal_install(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goals.jsonl":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    monkeypatch.setattr(
        goal_runtime_module,
        "_atomic_write",
        interrupt_journal_install,
    )
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        service.transition_goal(
            created.goal_ref,
            transition,
            idempotency_ref=operation_idempotency_ref,
            approval_ref=approval_ref,
        )
    monkeypatch.setattr(
        goal_runtime_module,
        "_atomic_write",
        original_atomic_write,
    )
    assert service.goals.append_intent_path.exists()  # noqa: SLF001
    for path in (
        service._events.path,  # noqa: SLF001
        service._events.idempotency_path,  # noqa: SLF001
        service._events.trusted_sources_path,  # noqa: SLF001
        service._events.generation_head_path,  # noqa: SLF001
        service._events.append_intent_path,  # noqa: SLF001
        service._events.reservations_path,  # noqa: SLF001
    ):
        path.unlink(missing_ok=True)

    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_COMPLETION_DURABLE_RECEIPT_NOT_FOUND",
    ):
        GoalRuntimeService(tmp_path).goal_lifecycle_read_model(
            include_cleared=True
        )
    assert service.goals.append_intent_path.exists()  # noqa: SLF001
    durable_entries = [
        goal_runtime_module.GoalJournalEntry.model_validate_json(line)
        for line in service.goals.path.read_text(encoding="utf-8").splitlines()  # noqa: SLF001
    ]
    assert durable_entries[-1].goal.state == GoalState.complete_requested.value


def test_verified_completion_recovers_exact_terminal_event_after_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-create-recovery",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:completion-recovery-request",
        ),
        idempotency_ref="idempotency-ref:goal-completion-recovery-request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    evidence = _completion_evidence(requested)
    transition = GoalTransitionRequest(
        expected_version=requested.version,
        transition=GoalTransitionKind.verify_completion,
        reason_ref="reason-ref:deterministic-recovery-verifier",
        completion_evidence=evidence,
    )
    original_append = service._events._append_locked
    failed_once = False

    def fail_terminal_append_once(
        request: DurableRunEventAppendRequest,
        **kwargs: object,
    ) -> DurableRunEvent:
        nonlocal failed_once
        if (
            not failed_once
            and request.event_kind == DurableRunEventKind.completion_verified.value
        ):
            failed_once = True
            raise OSError("simulated completion event commit interruption")
        return original_append(request, **kwargs)

    monkeypatch.setattr(
        service._events,
        "_append_locked",
        fail_terminal_append_once,
    )
    with pytest.raises(
        OSError,
        match="simulated completion event commit interruption",
    ):
        _transition_goal(
            service,
            created.goal_ref,
            transition,
            idempotency_ref="idempotency-ref:goal-verify-recovery",
        )

    recovered = GoalRuntimeService(tmp_path)
    replayed_goal = _transition_goal(
        recovered,
        created.goal_ref,
        transition,
        idempotency_ref="idempotency-ref:goal-verify-recovery",
    )
    replay = recovered.events.replay(
        "run-ref:accepted-local:one",
        after_sequence=0,
    )
    completion_events = [
        event
        for event in replay.events
        if event.event_kind == DurableRunEventKind.completion_verified.value
    ]

    assert replayed_goal.state == GoalState.verified_complete.value
    assert replayed_goal.version == requested.version + 1
    assert len(completion_events) == 1
    assert completion_events[0].receipt_refs == list(
        dict.fromkeys(
            [
                evidence.receipt_ref,
                *(
                    binding.evaluator_receipt_ref
                    for binding in replayed_goal.completion_criterion_verifier_bindings
                ),
            ]
        )
    )
    assert completion_events[0].proof_refs == list(
        dict.fromkeys(
            [
                evidence.proof_ref,
                evidence.evidence_ref,
                *evidence.criterion_proof_refs,
                *(
                    binding.evaluator_receipt_ref
                    for binding in replayed_goal.completion_criterion_verifier_bindings
                ),
            ]
        )
    )
    assert completion_events[0].criterion_verifier_bindings == [
        DurableCriterionVerifierBinding.model_validate(binding.model_dump(mode="json"))
        for binding in replayed_goal.completion_criterion_verifier_bindings
    ]

    cleared = _transition_goal(
        recovered,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=replayed_goal.version,
            transition=GoalTransitionKind.clear,
            reason_ref="reason-ref:clear-verified-goal",
        ),
        idempotency_ref="idempotency-ref:goal-clear-verified",
    )
    assert cleared.state == GoalState.cleared.value
    assert cleared.completion_receipt_ref == evidence.receipt_ref

    restored_goal = _transition_goal(
        recovered,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=cleared.version,
            transition=GoalTransitionKind.restore,
            reason_ref="reason-ref:restore-cleared-verified-goal",
        ),
        idempotency_ref="idempotency-ref:goal-restore-verified",
    )
    assert restored_goal.state == GoalState.verified_complete.value
    assert restored_goal.version == cleared.version + 1
    assert restored_goal.completion_receipt_ref == evidence.receipt_ref
    restored_service = GoalRuntimeService(tmp_path)
    restored_service.reconcile_durable_events()
    completion_events_after_restore = [
        event
        for event in restored_service.events.replay(
            "run-ref:accepted-local:one",
            after_sequence=0,
        ).events
        if event.event_kind == DurableRunEventKind.completion_verified.value
    ]
    assert len(completion_events_after_restore) == 1


def test_completion_binds_exact_receipt_plan_and_rejects_substitution(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:plan-binding:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:plan-binding:request",
        ),
        idempotency_ref="idempotency-ref:plan-binding:request",
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:accepted-local:one",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="A substituted plan recorded bounded receipt evidence.",
            proof_refs=[
                "proof-ref:accepted-local:one",
                "proof-ref:accepted-local:criterion:2",
            ],
            receipt_refs=["receipt-ref:accepted-local:one"],
            goal_ref=created.goal_ref,
            plan_ref="plan-ref:substituted",
            idempotency_ref="idempotency-ref:plan-binding:receipt",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    evidence = _completion_evidence(
        requested,
        plan_ref="plan-ref:substituted",
    )

    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_COMPLETION_PLAN_NOT_LINKED",
    ):
        _transition_goal(
            service,
            created.goal_ref,
            GoalTransitionRequest(
                expected_version=requested.version,
                transition=GoalTransitionKind.verify_completion,
                reason_ref="reason-ref:plan-binding:verify",
                completion_evidence=evidence,
            ),
            idempotency_ref="idempotency-ref:plan-binding:verify",
        )
    assert service.goals.get(created.goal_ref).state == (
        GoalState.complete_requested.value
    )


def test_cleared_verified_goal_recovers_missing_terminal_event(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:cleared-recovery:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:cleared-recovery:request",
        ),
        idempotency_ref="idempotency-ref:cleared-recovery:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    evidence = _completion_evidence(requested)
    verified = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=requested.version,
            transition=GoalTransitionKind.verify_completion,
            reason_ref="reason-ref:cleared-recovery:verify",
            completion_evidence=evidence,
        ),
        idempotency_ref="idempotency-ref:cleared-recovery:verify",
    )
    verify_request = GoalTransitionRequest(
        expected_version=requested.version,
        transition=GoalTransitionKind.verify_completion,
        reason_ref="reason-ref:cleared-recovery:verify",
        completion_evidence=evidence,
    )
    verified_entry = service.goals.transition_entry(
        created.goal_ref,
        verify_request,
        idempotency_ref="idempotency-ref:cleared-recovery:verify",
    )
    assert verified_entry is not None
    assert verified.completion_plan_ref == "plan-ref:accepted-local:one"
    cleared = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=verified.version,
            transition=GoalTransitionKind.clear,
            reason_ref="reason-ref:cleared-recovery:clear",
        ),
        idempotency_ref="idempotency-ref:cleared-recovery:clear",
    )
    assert cleared.state == GoalState.cleared.value

    events_path = tmp_path / "run_events.jsonl"
    tombstones_path = tmp_path / "run_event_idempotency.jsonl"
    events = [
        DurableRunEvent.model_validate_json(line)
        for line in events_path.read_text(encoding="utf-8").splitlines()
    ]
    retained = [
        event
        for event in events
        if event.event_kind != DurableRunEventKind.completion_verified.value
    ]
    events_path.write_text(
        "".join(event.model_dump_json() + "\n" for event in retained),
        encoding="utf-8",
    )
    tombstones = [
        json.loads(line)
        for line in tombstones_path.read_text(encoding="utf-8").splitlines()
    ]
    tombstones_path.write_text(
        "".join(
            json.dumps(item, sort_keys=True) + "\n"
            for item in tombstones
            if item["event"]["event_kind"]
            != DurableRunEventKind.completion_verified.value
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_GENERATION_HEAD_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).reconcile_durable_events()


def test_goal_terminal_states_fail_closed(tmp_path: Path) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-create-terminal",
    )
    cancelled = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=1,
            transition=GoalTransitionKind.cancel,
            reason_ref="reason-ref:operator-cancel",
        ),
        idempotency_ref="idempotency-ref:goal-cancel",
    )

    with pytest.raises(GoalTransitionDeniedError, match="TERMINAL_EDIT_DENIED"):
        _edit_goal(
            service,
            created.goal_ref,
            GoalEditRequest(
                expected_version=cancelled.version,
                text_redaction_posture=("operator_authored_redacted_summary_only"),
                objective="Attempted late success edit.",
            ),
            idempotency_ref="idempotency-ref:goal-late-edit",
        )
    with pytest.raises(GoalTransitionDeniedError, match="TRANSITION_DENIED"):
        _transition_goal(
            service,
            created.goal_ref,
            GoalTransitionRequest(
                expected_version=cancelled.version,
                transition=GoalTransitionKind.request_completion,
                reason_ref="reason-ref:late-success",
            ),
            idempotency_ref="idempotency-ref:goal-late-success",
        )


def test_run_event_cursor_replay_restart_and_bounded_retention(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path, retention_limit=3)
    run_ref = "run-ref:accepted-local:cursor"
    kinds = [
        DurableRunEventKind.goal_linked,
        DurableRunEventKind.plan_linked,
        DurableRunEventKind.approval_wait_entered,
        DurableRunEventKind.approval_resumed,
        DurableRunEventKind.receipt_recorded,
    ]
    for index, kind in enumerate(kinds, start=1):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref=run_ref,
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=kind,
                safe_summary=f"Durable event {index} – bounded Unicode ✓.",
                proof_refs=[f"proof-ref:cursor:{index}"],
                receipt_refs=(
                    [f"receipt-ref:cursor:{index}"]
                    if kind == DurableRunEventKind.receipt_recorded
                    else []
                ),
                goal_ref="goal-ref:cursor",
                plan_ref=(
                    "plan-ref:cursor"
                    if kind == DurableRunEventKind.plan_linked
                    else None
                ),
                idempotency_ref=f"idempotency-ref:cursor:{index}",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )

    restored = GoalRuntimeService(tmp_path, retention_limit=3)
    lost = restored.events.replay(run_ref, after_sequence=0)
    assert lost.status == RunEventReplayStatus.retention_loss.value
    assert lost.first_retained_sequence == 3
    assert lost.next_cursor == 2
    assert lost.gap_detected is True

    page_one = restored.events.replay(run_ref, after_sequence=2, limit=2)
    assert page_one.status == RunEventReplayStatus.ok.value
    assert [event.sequence for event in page_one.events] == [3, 4]
    page_two = restored.events.replay(
        run_ref,
        after_sequence=page_one.next_cursor,
        limit=2,
    )
    assert [event.sequence for event in page_two.events] == [5]
    assert not {event.event_ref for event in page_one.events}.intersection(
        event.event_ref for event in page_two.events
    )

    stale = restored.events.replay(run_ref, after_sequence=99)
    assert stale.status == RunEventReplayStatus.stale_cursor.value
    assert stale.next_cursor == 5
    unknown = restored.events.replay("run-ref:accepted-local:missing")
    assert unknown.status == RunEventReplayStatus.unknown_run.value


def test_run_event_idempotency_survives_payload_retention(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path, retention_limit=3)
    requests: list[DurableRunEventAppendRequest] = []
    for index in range(1, 6):
        request = DurableRunEventAppendRequest(
            run_ref="run-ref:retained-idempotency",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.goal_linked,
            safe_summary=f"Bounded retained event {index}.",
            proof_refs=[f"proof-ref:retained-idempotency:{index}"],
            goal_ref="goal-ref:retained-idempotency",
            idempotency_ref=f"idempotency-ref:retained-idempotency:{index}",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )
        requests.append(request)
        _append_event(service, request)

    replayed = _append_event(
        GoalRuntimeService(tmp_path, retention_limit=3),
        requests[0],
    )
    assert replayed.sequence == 1
    assert [
        event.sequence
        for event in service.events.retained_events(
            run_ref="run-ref:retained-idempotency"
        )
    ] == [3, 4, 5]
    with pytest.raises(
        GoalIdempotencyConflictError,
        match="RUN_EVENT_IDEMPOTENCY_CONFLICT",
    ):
        _append_event(
            service,
            requests[0].model_copy(
                update={"safe_summary": "A conflicting delayed retry."}
            ),
        )


def test_completion_receipt_remains_verifiable_after_payload_retention(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path, retention_limit=3)
    created = _create_goal(
        service,
        _create_request(run_ref="run-ref:retained-completion"),
        idempotency_ref="idempotency-ref:retained-completion:create",
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:retained-completion",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="The retained completion receipt was recorded.",
            proof_refs=[
                "proof-ref:retained-completion",
                "proof-ref:accepted-local:criterion:2",
            ],
            receipt_refs=["receipt-ref:retained-completion"],
            goal_ref=created.goal_ref,
            plan_ref="plan-ref:accepted-local:one",
            idempotency_ref="idempotency-ref:retained-completion:receipt",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    for index in range(4):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref="run-ref:retained-completion",
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.evidence_linked,
                safe_summary=f"Later retained evidence event {index}.",
                proof_refs=[f"proof-ref:retained-completion:later:{index}"],
                goal_ref=created.goal_ref,
                idempotency_ref=(f"idempotency-ref:retained-completion:later:{index}"),
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )
    assert [
        event.event_kind
        for event in service.events.retained_events(
            run_ref="run-ref:retained-completion"
        )
    ] == [DurableRunEventKind.evidence_linked.value] * 3
    assert service.events.has_completion_evidence(
        run_ref="run-ref:retained-completion",
        receipt_ref="receipt-ref:retained-completion",
        proof_ref="proof-ref:retained-completion",
        goal_ref=created.goal_ref,
    )

    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=1,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:retained-completion:request",
        ),
        idempotency_ref="idempotency-ref:retained-completion:request",
    )
    criterion_proof_refs = [
        "proof-ref:retained-completion",
        "proof-ref:accepted-local:criterion:2",
    ]
    criterion_bindings = _criterion_bindings(requested, criterion_proof_refs)
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:retained-completion",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary=("The trusted evaluator bound the requested goal criteria."),
            proof_refs=[
                *criterion_proof_refs,
                *(binding.evaluator_receipt_ref for binding in criterion_bindings),
            ],
            receipt_refs=["receipt-ref:retained-completion"],
            criterion_verifier_bindings=criterion_bindings,
            goal_ref=created.goal_ref,
            plan_ref="plan-ref:accepted-local:one",
            idempotency_ref=(
                "idempotency-ref:retained-completion:criterion-verification"
            ),
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    verified = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=requested.version,
            transition=GoalTransitionKind.verify_completion,
            reason_ref="reason-ref:retained-completion:verify",
            completion_evidence=_completion_evidence(
                requested,
                run_ref="run-ref:retained-completion",
                receipt_ref="receipt-ref:retained-completion",
                proof_ref="proof-ref:retained-completion",
                plan_ref="plan-ref:accepted-local:one",
            ),
        ),
        idempotency_ref="idempotency-ref:retained-completion:verify",
    )
    assert verified.state == GoalState.verified_complete.value


def test_retained_completion_receipt_rejects_recomputed_tombstone_wrapper(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path, retention_limit=2)
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:retained-tombstone-tamper",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="The retained receipt was recorded.",
            proof_refs=["proof-ref:retained-tombstone-tamper"],
            receipt_refs=["receipt-ref:retained-tombstone-tamper"],
            goal_ref="goal-ref:retained-tombstone-tamper",
            idempotency_ref="idempotency-ref:retained-tombstone-tamper:receipt",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:retained-tombstone-tamper",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.evidence_linked,
            safe_summary="Another later event completed receipt eviction.",
            proof_refs=["proof-ref:retained-tombstone-tamper:last"],
            goal_ref="goal-ref:retained-tombstone-tamper",
            idempotency_ref="idempotency-ref:retained-tombstone-tamper:last",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:retained-tombstone-tamper",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.evidence_linked,
            safe_summary="A later event evicted the receipt payload.",
            proof_refs=["proof-ref:retained-tombstone-tamper:later"],
            goal_ref="goal-ref:retained-tombstone-tamper",
            idempotency_ref="idempotency-ref:retained-tombstone-tamper:later",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )

    path = tmp_path / "run_event_idempotency.jsonl"
    rows = [
        goal_runtime_module.RunEventIdempotencyTombstone.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    receipt = rows[0]
    tampered_event = receipt.event.model_copy(
        update={"proof_refs": ["proof-ref:substituted"]}
    )
    recomputed_wrapper = receipt.model_copy(update={"event": tampered_event})
    recomputed_wrapper = recomputed_wrapper.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                recomputed_wrapper
            )
        }
    )
    path.write_text(
        "".join(
            row.model_dump_json() + "\n" for row in [recomputed_wrapper, *rows[1:]]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_IDEMPOTENCY_EVENT_HASH_MISMATCH",
    ):
        service.events.has_completion_evidence(
            run_ref="run-ref:retained-tombstone-tamper",
            receipt_ref="receipt-ref:retained-tombstone-tamper",
            proof_ref="proof-ref:retained-tombstone-tamper",
            goal_ref="goal-ref:retained-tombstone-tamper",
        )


def test_projection_reservations_are_reused_and_expired_crash_leases_reclaimed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 26, 20, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(goal_runtime_module, "utc_now", lambda: now)
    service = GoalRuntimeService(tmp_path)

    first_ref = service._events.reserve_runtime_projection(  # noqa: SLF001
        None,
        operation_idempotency_ref="idempotency-ref:reservation:reused",
    )
    replayed_ref = service._events.reserve_runtime_projection(  # noqa: SLF001
        None,
        operation_idempotency_ref="idempotency-ref:reservation:reused",
    )
    assert replayed_ref == first_ref
    reservation_path = tmp_path / "run_event_projection_reservations.jsonl"
    assert len(reservation_path.read_text(encoding="utf-8").splitlines()) == 1

    now += timedelta(
        seconds=(goal_runtime_module.RUN_EVENT_PROJECTION_RESERVATION_TTL_SECONDS + 1)
    )
    second_ref = service._events.reserve_runtime_projection(  # noqa: SLF001
        None,
        operation_idempotency_ref="idempotency-ref:reservation:after-crash",
    )
    rows = [
        json.loads(line)
        for line in reservation_path.read_text(encoding="utf-8").splitlines()
    ]
    assert second_ref != first_ref
    assert [row["reservation_ref"] for row in rows] == [second_ref]


def test_runtime_projection_reservation_is_refreshed_after_mission_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 7, 30, 1, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(goal_runtime_module, "utc_now", lambda: now)
    monkeypatch.setattr(
        goal_runtime_module,
        "RUN_EVENT_PROJECTION_RESERVATION_TTL_SECONDS",
        1,
    )
    service = GoalRuntimeService(tmp_path / "goals")
    goal = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:reservation-refresh:create",
    )
    original_guard = service.runtime_mission_execution_guard

    @contextmanager
    def expire_before_dispatch(*args: object, **kwargs: object):
        nonlocal now
        with original_guard(*args, **kwargs):
            now += timedelta(seconds=2)
            yield

    monkeypatch.setattr(
        service,
        "runtime_mission_execution_guard",
        expire_before_dispatch,
    )
    runner_calls = 0
    refresh_times: list[datetime] = []
    runner_times: list[datetime] = []
    original_refresh = service.refresh_runtime_projection_reservation

    def record_boundary_refresh(*args: object, **kwargs: object) -> None:
        refresh_times.append(now)
        original_refresh(*args, **kwargs)

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal runner_calls
        runner_calls += 1
        runner_times.append(now)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    monkeypatch.setattr(
        service,
        "refresh_runtime_projection_reservation",
        record_boundary_refresh,
    )
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=service,
    )
    original_create_invocation = gateway.store.create_invocation

    def delayed_invocation_preflight(*args: object, **kwargs: object):
        nonlocal now
        result = original_create_invocation(*args, **kwargs)
        now += timedelta(seconds=2)
        return result

    monkeypatch.setattr(
        gateway.store,
        "create_invocation",
        delayed_invocation_preflight,
    )
    result = gateway.invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            mission_ref=goal.goal_ref,
            safe_summary="Inspect bounded status after exact mission admission.",
        ),
        idempotency_ref="idempotency-ref:reservation-refresh:invoke",
    )

    assert result.record.receipt is not None
    assert runner_calls == 1
    assert refresh_times == runner_times
    assert len(service.events.replay(result.record.invocation_ref).events) == 2


def test_runtime_projection_refresh_failure_prevents_adapter_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")
    goal = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:reservation-refresh-failure:create",
    )
    runner_calls = 0
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        mission_ref=goal.goal_ref,
        safe_summary="Do not dispatch after reservation refresh fails.",
    )
    original_refresh = service.refresh_runtime_projection_reservation

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal runner_calls
        runner_calls += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    def reject_refresh(*_args: object, **_kwargs: object) -> None:
        raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED")

    monkeypatch.setattr(
        service,
        "refresh_runtime_projection_reservation",
        reject_refresh,
    )
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=service,
    )
    with pytest.raises(
        GoalRuntimeError,
        match="RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED",
    ):
        gateway.invoke_command(
            request,
            idempotency_ref="idempotency-ref:reservation-refresh-failure:invoke",
        )

    assert runner_calls == 0
    [pending] = gateway.store.list_invocations()
    assert pending.receipt is None
    assert pending.adapter_dispatch_protocol_ref is not None
    assert pending.adapter_dispatch_started is False

    monkeypatch.setattr(
        service,
        "refresh_runtime_projection_reservation",
        original_refresh,
    )
    retried = gateway.invoke_command(
        request,
        idempotency_ref="idempotency-ref:reservation-refresh-failure:invoke",
    )
    assert runner_calls == 1
    assert retried.record.receipt is not None
    assert retried.record.adapter_dispatch_started is True


def test_goal_journal_capacity_fails_closed_before_unbounded_growth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(goal_runtime_module, "MAX_GOAL_JOURNAL_ENTRIES", 2)
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:bounded-journal:create",
    )
    edited = _edit_goal(
        service,
        created.goal_ref,
        GoalEditRequest(
            expected_version=1,
            text_redaction_posture=("operator_authored_redacted_summary_only"),
            objective="Bounded edit one.",
        ),
        idempotency_ref="idempotency-ref:bounded-journal:edit-one",
    )

    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_JOURNAL_CAPACITY_EXCEEDED",
    ):
        _edit_goal(
            service,
            created.goal_ref,
            GoalEditRequest(
                expected_version=edited.version,
                text_redaction_posture=("operator_authored_redacted_summary_only"),
                objective="Bounded edit two must fail closed.",
            ),
            idempotency_ref="idempotency-ref:bounded-journal:edit-two",
        )

    assert service.goals.get(created.goal_ref).version == edited.version
    assert len((tmp_path / "goals.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_goal_commit_reserves_next_independent_anchor_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:anchor-capacity:create",
    )
    evidence_ref = (
        "evidence-ref:control-center-goal-update-submission:edit:sha256:"
        + "a" * 64
    )
    request = GoalEditRequest(
        expected_version=created.version,
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective="Reserve the exact next independent journal anchor.",
        evidence_refs=[evidence_ref],
    )
    idempotency_ref = "idempotency-ref:anchor-capacity:edit"
    service.record_goal_mutation_submission(
        submission_ref="submission-ref:anchor-capacity:edit",
        operation="edit",
        goal_ref=created.goal_ref,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    state = service._submissions._load_state()  # noqa: SLF001
    current_terminal_bytes = len(
        service._submissions._state_content(  # noqa: SLF001
            service._submissions._worst_case_terminal_records(  # noqa: SLF001
                list(state.records)
            ),
            list(state.rejection_tombstones),
            state.goal_journal_anchor,
        ).encode("utf-8")
    )
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_GOAL_MUTATION_SUBMISSION_STATE_BYTES",
        current_terminal_bytes,
    )
    journal_before = service.goals.path.read_bytes()

    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_SUBMISSION_STATE_CAPACITY_EXCEEDED",
    ):
        _edit_goal(
            service,
            created.goal_ref,
            request,
            idempotency_ref=idempotency_ref,
        )

    assert service.goals.path.read_bytes() == journal_before
    assert service.goals.get(created.goal_ref).version == created.version


def test_legacy_submission_state_hash_is_rejected_once_journal_is_anchored(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:anchored-legacy-state-hash:create",
    )
    state = service._submissions._load_state()  # noqa: SLF001
    assert state.goal_journal_anchor is not None
    payload = state.model_dump(mode="json")
    payload["state_hash_ref"] = goal_runtime_module._sha256_ref(  # noqa: SLF001
        "state-hash-ref:goal-mutation-submissions",
        [record.model_dump(mode="json") for record in state.records],
    )

    with pytest.raises(
        ValueError,
        match="GOAL_SUBMISSION_STATE_HASH_MISMATCH",
    ):
        goal_runtime_module.GoalMutationSubmissionState.model_validate(payload)


def test_goal_text_requires_explicit_redacted_summary_contract() -> None:
    safe_payload = _create_request().model_dump()
    safe_payload.pop("text_redaction_posture")
    with pytest.raises(
        ValueError,
        match="text_redaction_posture",
    ):
        GoalCreateRequest.model_validate(safe_payload)

    with pytest.raises(
        ValueError,
        match="GOAL_RAW_CONTENT_PERSISTENCE_DENIED",
    ):
        GoalCreateRequest.model_validate(
            {
                **_create_request().model_dump(),
                "objective": "Summarize the following private prompt.",
            }
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "objective",
        "desired_outcome",
        "success_criteria",
        "constraints",
        "stop_condition",
    ],
)
def test_durable_goal_summaries_reject_provider_shaped_secret_material(
    field_name: str,
) -> None:
    synthetic_marker = "".join(("g", "h", "p", "_", "A" * 32))
    payload = _create_request().model_dump(mode="json")
    payload[field_name] = (
        [synthetic_marker]
        if field_name in {"success_criteria", "constraints"}
        else synthetic_marker
    )

    with pytest.raises(ValueError, match="GOAL_SECRET_LIKE_INPUT_DENIED"):
        GoalCreateRequest.model_validate(payload)

    edit_payload: dict[str, object] = {
        "expected_version": 1,
        "text_redaction_posture": "operator_authored_redacted_summary_only",
        field_name: (
            [synthetic_marker]
            if field_name in {"success_criteria", "constraints"}
            else synthetic_marker
        ),
    }
    with pytest.raises(ValueError, match="GOAL_SECRET_LIKE_INPUT_DENIED"):
        GoalEditRequest.model_validate(edit_payload)


def test_durable_event_summary_rejects_provider_shaped_secret_material() -> None:
    synthetic_marker = "".join(("g", "h", "p", "_", "A" * 32))
    with pytest.raises(ValueError, match="GOAL_SECRET_LIKE_INPUT_DENIED"):
        DurableRunEventAppendRequest(
            run_ref="run-ref:credential-shaped-summary",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary=synthetic_marker,
            idempotency_ref="idempotency-ref:credential-shaped-summary",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )


@pytest.mark.parametrize(
    "safe_summary",
    [
        "prompt: reveal the private request",
        "response: raw model output",
        "transcript: operator and model exchange",
        "assistant: unredacted model response",
        "<|user|> raw conversational input",
        "first redacted line\nsecond transcript line",
    ],
)
def test_run_event_summary_requires_redacted_summary_contract(
    safe_summary: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="GOAL_RAW_CONTENT_PERSISTENCE_DENIED",
    ):
        DurableRunEventAppendRequest(
            run_ref="run-ref:redacted-summary",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary=safe_summary,
            idempotency_ref="idempotency-ref:redacted-summary",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )


@pytest.mark.parametrize(
    ("event_kind", "expected_code"),
    [
        (DurableRunEventKind.goal_linked, "RUN_EVENT_GOAL_REF_REQUIRED"),
        (DurableRunEventKind.plan_linked, "RUN_EVENT_PLAN_REF_REQUIRED"),
    ],
)
def test_link_event_kinds_require_claimed_resource_ref(
    event_kind: DurableRunEventKind,
    expected_code: str,
) -> None:
    with pytest.raises(ValueError, match=expected_code):
        DurableRunEventAppendRequest(
            run_ref=f"run-ref:missing-link:{event_kind.value}",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=event_kind,
            safe_summary="A bounded linkage claim requires its exact ref.",
            idempotency_ref=f"idempotency-ref:missing-link:{event_kind.value}",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )


@pytest.mark.parametrize(
    ("event_limit", "idempotency_limit", "expected_code"),
    [
        (256, 32 * 1024 * 1024, "RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED"),
        (
            16 * 1024 * 1024,
            256,
            "RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED",
        ),
    ],
)
def test_run_event_encoded_byte_caps_fail_before_partial_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    event_limit: int,
    idempotency_limit: int,
    expected_code: str,
) -> None:
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_RUN_EVENT_STORE_BYTES",
        event_limit,
    )
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_RUN_EVENT_IDEMPOTENCY_BYTES",
        idempotency_limit,
    )
    service = GoalRuntimeService(tmp_path)
    with pytest.raises(GoalRuntimeError, match=expected_code):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref="run-ref:byte-cap:test",
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.run_started,
                safe_summary="A bounded event must preflight both durable stores.",
                idempotency_ref="idempotency-ref:byte-cap:test",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )
    assert not (tmp_path / "run_events.jsonl").exists()
    assert not (tmp_path / "run_event_idempotency.jsonl").exists()


@pytest.mark.parametrize(
    ("field_name", "replacement", "expected_code"),
    [
        (
            "verifier_ref",
            "verifier-ref:untrusted:substitution",
            "GOAL_COMPLETION_VERIFIER_NOT_TRUSTED",
        ),
        (
            "evidence_ref",
            "evidence-ref:unbound:substitution",
            "GOAL_COMPLETION_VERIFIER_BINDING_MISMATCH",
        ),
    ],
)
def test_goal_completion_rejects_untrusted_or_unbound_verifier_evidence(
    tmp_path: Path,
    field_name: str,
    replacement: str,
    expected_code: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:verifier-binding:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:verifier-binding:request",
        ),
        idempotency_ref="idempotency-ref:verifier-binding:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    evidence = _completion_evidence(requested).model_copy(
        update={field_name: replacement}
    )
    with pytest.raises(GoalTransitionDeniedError, match=expected_code):
        _transition_goal(
            service,
            created.goal_ref,
            GoalTransitionRequest(
                expected_version=requested.version,
                transition=GoalTransitionKind.verify_completion,
                reason_ref="reason-ref:verifier-binding:reject",
                completion_evidence=evidence,
            ),
            idempotency_ref=(f"idempotency-ref:verifier-binding:{field_name}"),
        )
    assert service.goals.get(created.goal_ref).state == (
        GoalState.complete_requested.value
    )


@pytest.mark.parametrize(
    ("criterion_proof_refs", "expected_code"),
    [
        (
            ["proof-ref:accepted-local:one"],
            "GOAL_COMPLETION_CRITERION_PROOF_BINDING_MISMATCH",
        ),
        (
            [
                "proof-ref:accepted-local:one",
                "proof-ref:substituted:criterion:2",
            ],
            "GOAL_COMPLETION_CRITERION_PROOF_BINDING_MISMATCH",
        ),
    ],
)
def test_goal_completion_rejects_unbound_criterion_proofs(
    tmp_path: Path,
    criterion_proof_refs: list[str],
    expected_code: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:criterion-binding:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:criterion-binding:request",
        ),
        idempotency_ref="idempotency-ref:criterion-binding:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    evidence = _completion_evidence(requested)
    if len(criterion_proof_refs) == len(requested.success_criteria):
        evidence = _completion_evidence(
            requested,
            criterion_proof_refs=criterion_proof_refs,
        )
    else:
        evidence = evidence.model_copy(
            update={"criterion_proof_refs": criterion_proof_refs}
        )
    with pytest.raises(GoalTransitionDeniedError, match=expected_code):
        _transition_goal(
            service,
            created.goal_ref,
            GoalTransitionRequest(
                expected_version=requested.version,
                transition=GoalTransitionKind.verify_completion,
                reason_ref="reason-ref:criterion-binding:reject",
                completion_evidence=evidence,
            ),
            idempotency_ref=(
                f"idempotency-ref:criterion-binding:{expected_code.lower()}"
            ),
        )


@pytest.mark.parametrize(
    "event_kind",
    [
        DurableRunEventKind.cancelled,
        DurableRunEventKind.failed_terminal,
        DurableRunEventKind.dead_lettered,
    ],
)
def test_terminal_run_events_require_receipt_proof(
    tmp_path: Path,
    event_kind: DurableRunEventKind,
) -> None:
    service = GoalRuntimeService(tmp_path)
    with pytest.raises(ValueError, match="RUN_EVENT_TERMINAL_RECEIPT_PROOF_REQUIRED"):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref=f"run-ref:terminal-proof:{event_kind.value}",
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=event_kind,
                safe_summary="An unsupported terminal claim must fail closed.",
                idempotency_ref=(f"idempotency-ref:terminal-proof:{event_kind.value}"),
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )


def test_runtime_gateway_projects_accepted_receipt_into_durable_events(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_dir = tmp_path / "runtime"
    goal_dir = tmp_path / "goals"

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    goal_service = GoalRuntimeService(
        goal_dir,
        runtime_invocation_state_dir=runtime_dir,
    )
    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            runtime_dir,
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=goal_service,
    )
    result = gateway.invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="Inspect current repository status with redacted output.",
        ),
        idempotency_ref="idempotency-ref:runtime-event-producer",
    )

    assert result.record.status == "receipt_recorded"
    replay = goal_service.events.replay(result.record.invocation_ref)
    assert [event.event_kind for event in replay.events] == [
        DurableRunEventKind.run_started.value,
        DurableRunEventKind.receipt_recorded.value,
    ]
    assert replay.events[-1].receipt_refs == [result.record.receipt.receipt_ref]

    class _SubstitutingInvocationStore:
        @staticmethod
        def get_invocation(_invocation_ref: str) -> object:
            substituted_ref = "runtime-invocation-ref:substituted"
            return result.record.model_copy(
                update={
                    "invocation_ref": substituted_ref,
                    "receipt": result.record.receipt.model_copy(
                        update={"invocation_ref": substituted_ref}
                    ),
                }
            )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_DURABLE_INVOCATION_REF_MISMATCH",
    ):
        goal_service.record_accepted_runtime_invocation(
            result.record,
            invocation_store=_SubstitutingInvocationStore(),  # type: ignore[arg-type]
        )

    class _MalformedInvocationStore:
        @staticmethod
        def get_invocation(_invocation_ref: str) -> object:
            return object()

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_DURABLE_INVOCATION_INVALID",
    ):
        goal_service.record_accepted_runtime_invocation(
            result.record,
            invocation_store=_MalformedInvocationStore(),  # type: ignore[arg-type]
        )
    reservations_path = goal_dir / "run_event_projection_reservations.jsonl"
    assert reservations_path.read_text(encoding="utf-8") == ""
    assert stat.S_IMODE(reservations_path.stat().st_mode) == 0o600
    restored = GoalRuntimeService(
        goal_dir,
        runtime_invocation_state_dir=runtime_dir,
    )
    restored_runtime_store = RuntimeInvocationStore(
        runtime_dir,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    records = restored_runtime_store.list_invocations()
    tombstone_write_calls = 0

    def reject_redundant_tombstone_write(
        _tombstones: object,
    ) -> None:
        nonlocal tombstone_write_calls
        tombstone_write_calls += 1
        raise AssertionError("fully projected history must not be rewritten")

    monkeypatch.setattr(
        restored._events,  # noqa: SLF001
        "_write_idempotency_tombstones",
        reject_redundant_tombstone_write,
    )
    assert (
        restored.sync_runtime_invocations(
            records,
            invocation_store=restored_runtime_store,
        )
        == []
    )
    assert tombstone_write_calls == 0
    assert len(restored.events.replay(result.record.invocation_ref).events) == 2
    restored_runtime_store.path.unlink()
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_TRUSTED_SOURCE_PROVENANCE_MISMATCH",
    ):
        restored.events.replay(result.record.invocation_ref)


def test_aggregate_read_projects_committed_runtime_receipt_after_crash(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_store = RuntimeInvocationStore(
        runtime_dir,
        active_authority_leases=[workspace_execute_authority_lease()],
    )

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    committed = invoke_governed_command(
        store=runtime_store,
        adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        request=RuntimeCommandExecutionRequest(
            intent="git_status",
            mission_ref="mission-ref:aggregate-crash-recovery",
            safe_summary="Inspect bounded status before aggregate recovery.",
        ),
        idempotency_ref="idempotency-ref:aggregate-crash-recovery",
    ).record
    service = GoalRuntimeService.for_runtime_store(runtime_dir)
    assert service.events.retained_events(run_ref=committed.invocation_ref) == []

    replay, retained, summaries, _goals, _submissions = (
        service.aggregate_read_snapshot(
            run_ref=committed.invocation_ref,
            after_sequence=0,
            limit=10,
        )
    )

    assert replay is not None
    assert [event.event_kind for event in replay.events] == [
        DurableRunEventKind.run_started.value,
        DurableRunEventKind.receipt_recorded.value,
    ]
    assert retained == replay.events
    assert summaries[0].run_ref == committed.invocation_ref
    assert summaries[0].successful_receipt_recorded is True


@pytest.mark.parametrize("runtime_state", ["empty", "nonterminal"])
def test_aggregate_read_does_not_initialize_goal_state_without_committed_receipt(
    tmp_path: Path,
    runtime_state: str,
) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    runtime_path = runtime_dir / "runtime_gateway_invocations.jsonl"
    if runtime_state == "empty":
        runtime_path.write_text("", encoding="utf-8")
    else:
        RuntimeInvocationStore(runtime_dir).create_invocation(
            RuntimeInvocationRequest(
                requested_authority=RuntimeAuthority.allowlisted_command,
                requested_profile=RuntimeProfile.sealed,
                input_ref="command-input-ref:aggregate-nonterminal",
                mission_ref="mission-ref:aggregate-nonterminal",
                safe_summary="Retain one bounded nonterminal runtime request.",
            ),
            idempotency_ref="idempotency-ref:aggregate-nonterminal",
        )
    service = GoalRuntimeService.for_runtime_store(runtime_dir)
    assert not service.state_dir.exists()

    replay, retained, summaries, goals, submissions = service.aggregate_read_snapshot(
        run_ref=None,
        after_sequence=0,
        limit=10,
    )

    assert replay is None
    assert retained == []
    assert summaries == []
    assert goals.goals == []
    assert submissions.records == []
    assert not service.state_dir.exists()


def test_safe_disabled_committed_receipt_replays_and_projects_from_receipt_truth(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_store = RuntimeInvocationStore(
        runtime_dir,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    runner_call_count = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal runner_call_count
        runner_call_count += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        mission_ref="mission-ref:safe-disabled-committed",
        safe_summary="Inspect bounded status before safe-disable.",
    )
    idempotency_ref = "idempotency-ref:safe-disabled-committed"
    committed = invoke_governed_command(
        store=runtime_store,
        adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        request=request,
        idempotency_ref=idempotency_ref,
    ).record
    runtime_store.safe_disable(
        RuntimeSafeDisableRequest(
            reason_ref="reason-ref:safe-disabled-committed"
        ),
        idempotency_ref="idempotency-ref:safe-disabled-committed-posture",
    )
    disabled = runtime_store.get_invocation(committed.invocation_ref)
    assert disabled.status == "safe_disabled"
    assert disabled.receipt is not None
    assert committed.receipt is not None
    assert disabled.receipt.receipt_ref == committed.receipt.receipt_ref
    assert disabled.receipt.invocation_status == "receipt_recorded"

    service = GoalRuntimeService.for_runtime_store(runtime_dir)
    replay, _retained, _summaries, _goals, _submissions = (
        service.aggregate_read_snapshot(
            run_ref=committed.invocation_ref,
            after_sequence=0,
            limit=10,
        )
    )
    assert replay is not None
    assert [event.event_kind for event in replay.events] == [
        DurableRunEventKind.run_started.value,
        DurableRunEventKind.receipt_recorded.value,
    ]

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            runtime_dir,
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=service,
    )
    exact_replay = gateway.invoke_command(request, idempotency_ref=idempotency_ref)
    assert exact_replay.record.receipt == disabled.receipt
    assert runner_call_count == 1


def test_runtime_gateway_rejects_unknown_goal_mission_before_execution(
    tmp_path: Path,
) -> None:
    runner_called = False

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal runner_called
        runner_called = True
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=GoalRuntimeService(tmp_path / "goals"),
    )
    with pytest.raises(GoalRuntimeError, match="GOAL_NOT_FOUND"):
        gateway.invoke_command(
            RuntimeCommandExecutionRequest(
                intent="git_status",
                mission_ref="goal-ref:sha256:" + "f" * 64,
                safe_summary=(
                    "Inspect current repository status with redacted output."
                ),
            ),
            idempotency_ref="idempotency-ref:unknown-goal-mission",
        )
    assert not runner_called
    assert gateway.store.list_invocations() == []

    with pytest.raises(GoalRuntimeError, match="GOAL_NOT_FOUND"):
        gateway.execute_approved_command(
            "invocation-ref:unknown-goal-retry",
            RuntimeCommandExecutionRequest(
                intent="git_status",
                mission_ref="goal-ref:sha256:" + "f" * 64,
                safe_summary=("Retry a bounded inspection only for a durable goal."),
            ),
            RuntimeExecuteRequest(),
            idempotency_ref="idempotency-ref:unknown-goal-retry",
        )
    assert not runner_called
    assert gateway.store.list_invocations() == []

    local_store = RuntimeInvocationStore(tmp_path / "local-runtime")
    local_gateway = RuntimeGateway(
        store=local_store,
        local_model_adapter=LocalModelRuntimeAdapter(),
        local_model_runtime_enabled=True,
        goal_runtime_service=GoalRuntimeService(tmp_path / "local-goals"),
    )
    with pytest.raises(GoalRuntimeError, match="GOAL_NOT_FOUND"):
        local_gateway.invoke_local_model(
            RuntimeLocalModelCallRequest(
                base_url="http://127.0.0.1:8080",
                model_ref="uaa-local-runtime",
                messages=[
                    RuntimeLocalModelMessage(
                        role="user",
                        content="[redacted-test-input]",
                    )
                ],
                mission_ref="goal-ref:sha256:" + "e" * 64,
                safe_summary="Run a bounded local model proposal.",
            ),
            idempotency_ref="idempotency-ref:unknown-local-goal-mission",
        )
    assert local_store.list_invocations() == []

    allowed = gateway.invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            mission_ref="mission-ref:bounded-local-inspection",
            safe_summary="Inspect current repository status with redacted output.",
        ),
        idempotency_ref="idempotency-ref:non-goal-mission",
    )
    assert allowed.record.status == "receipt_recorded"
    assert runner_called
    with pytest.raises(GoalRuntimeError, match="GOAL_NOT_FOUND"):
        gateway.invoke_command(
            RuntimeCommandExecutionRequest(
                intent="git_status",
                mission_ref="goal-ref:sha256:" + "d" * 64,
                safe_summary=(
                    "Inspect current repository status with redacted output."
                ),
            ),
            idempotency_ref="idempotency-ref:non-goal-mission",
        )


@pytest.mark.parametrize(
    ("transition", "expected_state"),
    [
        (GoalTransitionKind.pause, GoalState.paused),
        (GoalTransitionKind.block, GoalState.blocked),
        (GoalTransitionKind.wait, GoalState.waiting),
        (GoalTransitionKind.request_completion, GoalState.complete_requested),
        (GoalTransitionKind.cancel, GoalState.cancelled),
        (GoalTransitionKind.clear, GoalState.cleared),
    ],
)
def test_runtime_gateway_rejects_non_runnable_goal_mission_before_execution(
    tmp_path: Path,
    transition: GoalTransitionKind,
    expected_state: GoalState,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")
    goal = _create_goal(
        service,
        _create_request(),
        idempotency_ref=f"idempotency-ref:mission-state-create:{transition.value}",
    )
    transitioned = _transition_goal(
        service,
        goal.goal_ref,
        GoalTransitionRequest(
            expected_version=goal.version,
            transition=transition,
            reason_ref=f"reason-ref:mission-state:{transition.value}",
        ),
        idempotency_ref=f"idempotency-ref:mission-state:{transition.value}",
    )
    assert transitioned.state == expected_state.value

    runner_called = False

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal runner_called
        runner_called = True
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=service,
    )
    with pytest.raises(GoalRuntimeError, match="GOAL_MISSION_NOT_RUNNABLE"):
        gateway.invoke_command(
            RuntimeCommandExecutionRequest(
                intent="git_status",
                mission_ref=goal.goal_ref,
                safe_summary="Inspect bounded status only for a runnable goal.",
            ),
            idempotency_ref=(
                f"idempotency-ref:mission-state-invoke:{transition.value}"
            ),
        )
    assert not runner_called
    assert gateway.store.list_invocations() == []


def test_runtime_goal_state_is_pinned_across_adapter_dispatch(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")
    goal = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:mission-race-create",
    )
    cancel_request = GoalTransitionRequest(
        expected_version=goal.version,
        transition=GoalTransitionKind.cancel,
        reason_ref="reason-ref:mission-race-cancel",
    )
    cancel_idempotency_ref = "idempotency-ref:mission-race-cancel"
    cancel_approval_ref = _approved_mutation_ref(
        service,
        operation="transition",
        goal_ref=goal.goal_ref,
        request=cancel_request,
        idempotency_ref=cancel_idempotency_ref,
    )
    runner_started = threading.Event()
    release_runner = threading.Event()
    transition_started = threading.Event()
    results: list[RuntimeCommandGatewayResult] = []
    errors: list[BaseException] = []
    runner_call_count = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal runner_call_count
        runner_call_count += 1
        runner_started.set()
        assert release_runner.wait(timeout=15)
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=service,
    )
    runtime_request = RuntimeCommandExecutionRequest(
        intent="git_status",
        mission_ref=goal.goal_ref,
        safe_summary="Inspect bounded status while the goal remains runnable.",
    )

    def invoke() -> None:
        try:
            results.append(
                gateway.invoke_command(
                    runtime_request,
                    idempotency_ref="idempotency-ref:mission-race-invoke",
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    def cancel() -> None:
        transition_started.set()
        try:
            service.transition_goal(
                goal.goal_ref,
                cancel_request,
                idempotency_ref=cancel_idempotency_ref,
                approval_ref=cancel_approval_ref,
            )
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    invoke_thread = threading.Thread(target=invoke)
    invoke_thread.start()
    assert runner_started.wait(timeout=15)
    cancel_thread = threading.Thread(target=cancel)
    cancel_thread.start()
    assert transition_started.wait(timeout=15)
    cancel_thread.join(timeout=0.2)
    assert cancel_thread.is_alive()

    release_runner.set()
    invoke_thread.join(timeout=15)
    cancel_thread.join(timeout=15)
    assert not invoke_thread.is_alive()
    assert not cancel_thread.is_alive()
    assert errors == []
    assert len(results) == 1
    assert service.goals.get(goal.goal_ref).state == GoalState.cancelled.value

    replay = gateway.invoke_command(
        runtime_request,
        idempotency_ref="idempotency-ref:mission-race-invoke",
    )
    assert replay.record.invocation_ref == results[0].record.invocation_ref
    assert replay.record.receipt == results[0].record.receipt
    assert runner_call_count == 1


def test_runtime_gateway_rechecks_committed_replay_at_mission_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")
    goal = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:mission-stale-replay-create",
    )
    runner_call_count = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal runner_call_count
        runner_call_count += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=service,
    )
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        mission_ref=goal.goal_ref,
        safe_summary="Inspect bounded status for exact committed replay.",
    )
    idempotency_ref = "idempotency-ref:mission-stale-replay-invoke"
    committed = gateway.invoke_command(
        request,
        idempotency_ref=idempotency_ref,
    )
    cancelled = _transition_goal(
        service,
        goal.goal_ref,
        GoalTransitionRequest(
            expected_version=goal.version,
            transition=GoalTransitionKind.cancel,
            reason_ref="reason-ref:mission-stale-replay-cancel",
        ),
        idempotency_ref="idempotency-ref:mission-stale-replay-cancel",
    )
    assert cancelled.state == GoalState.cancelled.value

    original_lookup = gateway.store.get_invocation_for_idempotency
    original_locked_lookup = gateway.store.get_invocation_for_idempotency_locked
    lookup_count = 0
    locked_lookup_count = 0

    def stale_then_current(value: str) -> RuntimeInvocationRecord | None:
        nonlocal lookup_count
        lookup_count += 1
        if lookup_count == 1:
            return None
        return original_lookup(value)

    def locked_current(value: str) -> RuntimeInvocationRecord | None:
        nonlocal locked_lookup_count
        locked_lookup_count += 1
        return original_locked_lookup(value)

    monkeypatch.setattr(
        gateway.store,
        "get_invocation_for_idempotency",
        stale_then_current,
    )
    monkeypatch.setattr(
        gateway.store,
        "get_invocation_for_idempotency_locked",
        locked_current,
    )
    refresh_calls = 0

    def reject_replay_refresh(*_args: object, **_kwargs: object) -> None:
        nonlocal refresh_calls
        refresh_calls += 1
        raise GoalRuntimeError("RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED")

    monkeypatch.setattr(
        service,
        "refresh_runtime_projection_reservation",
        reject_replay_refresh,
    )

    replay = gateway.invoke_command(request, idempotency_ref=idempotency_ref)

    assert replay.record.invocation_ref == committed.record.invocation_ref
    assert replay.record.receipt == committed.record.receipt
    assert lookup_count == 1
    assert locked_lookup_count >= 1
    assert refresh_calls == 0
    assert runner_call_count == 1


def test_runtime_gateway_reloads_cross_store_committed_replay_at_admission(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")
    goal = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:cross-store-replay-create",
    )
    runtime_dir = tmp_path / "runtime"
    first_store = RuntimeInvocationStore(
        runtime_dir,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    stale_store = RuntimeInvocationStore(
        runtime_dir,
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    idempotency_ref = "idempotency-ref:cross-store-replay-invoke"
    assert stale_store.get_invocation_for_idempotency(idempotency_ref) is None
    runner_call_count = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal runner_call_count
        runner_call_count += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    adapter = GovernedCommandRuntimeAdapter(
        workspace_root=ROOT,
        runner=runner,
    )
    request = RuntimeCommandExecutionRequest(
        intent="git_status",
        mission_ref=goal.goal_ref,
        safe_summary="Inspect bounded status for cross-store exact replay.",
    )
    first_gateway = RuntimeGateway(
        store=first_store,
        command_adapter=adapter,
        goal_runtime_service=service,
    )
    committed = first_gateway.invoke_command(
        request,
        idempotency_ref=idempotency_ref,
    )
    cancelled = _transition_goal(
        service,
        goal.goal_ref,
        GoalTransitionRequest(
            expected_version=goal.version,
            transition=GoalTransitionKind.cancel,
            reason_ref="reason-ref:cross-store-replay-cancel",
        ),
        idempotency_ref="idempotency-ref:cross-store-replay-cancel",
    )
    assert cancelled.state == GoalState.cancelled.value

    replay = RuntimeGateway(
        store=stale_store,
        command_adapter=adapter,
        goal_runtime_service=service,
    ).invoke_command(
        request,
        idempotency_ref=idempotency_ref,
    )

    assert replay.record.invocation_ref == committed.record.invocation_ref
    assert replay.record.receipt == committed.record.receipt
    assert runner_call_count == 1


def test_legacy_unknown_goal_receipt_is_quarantined_without_blocking_sync(
    tmp_path: Path,
) -> None:
    future_goal = _create_goal(
        GoalRuntimeService(tmp_path / "future-goal"),
        _create_request(),
        idempotency_ref="idempotency-ref:future-quarantined-goal",
    )

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    store = RuntimeInvocationStore(
        tmp_path / "runtime",
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    adapter = GovernedCommandRuntimeAdapter(
        workspace_root=ROOT,
        runner=runner,
    )
    legacy = invoke_governed_command(
        store=store,
        adapter=adapter,
        request=RuntimeCommandExecutionRequest(
            intent="git_status",
            mission_ref=future_goal.goal_ref,
            safe_summary="A historical opaque goal mission completed locally.",
        ),
        idempotency_ref="idempotency-ref:legacy-goal-receipt",
    ).record
    current = invoke_governed_command(
        store=store,
        adapter=adapter,
        request=RuntimeCommandExecutionRequest(
            intent="git_status",
            mission_ref="mission-ref:current-bounded-inspection",
            safe_summary="A current bounded inspection completed locally.",
        ),
        idempotency_ref="idempotency-ref:current-receipt",
    ).record

    service = GoalRuntimeService(tmp_path / "goals")
    projected = service.sync_runtime_invocations(
        [legacy, current],
        invocation_store=store,
    )
    assert {event.run_ref for event in projected} == {current.invocation_ref}
    incompatibilities = service.events.projection_incompatibilities()
    assert len(incompatibilities) == 1
    assert incompatibilities[0].invocation_ref == legacy.invocation_ref
    quarantine_path = service.state_dir / "runtime_projection_incompatibilities.jsonl"
    first_quarantine = quarantine_path.read_bytes()
    quarantine_path.write_bytes(first_quarantine + b"\n")
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUNTIME_PROJECTION_INCOMPATIBILITY_HEAD_MISMATCH",
    ):
        service.events.projection_incompatibilities()
    quarantine_path.write_bytes(first_quarantine)

    restarted = GoalRuntimeService(tmp_path / "goals")
    assert (
        restarted.sync_runtime_invocations(
            store.list_invocations(),
            invocation_store=store,
        )
        == []
    )
    assert quarantine_path.read_bytes() == first_quarantine
    assert restarted.events.projection_incompatibilities() == incompatibilities
    assert len(restarted.events.replay(current.invocation_ref).events) == 2

    substituted = legacy.model_copy(
        update={
            "payload_fingerprint_ref": ("runtime-payload-fingerprint-ref:substituted")
        }
    )
    assert (
        restarted.sync_runtime_invocations(
            [substituted],
            invocation_store=store,
        )
        == []
    )

    class _SubstitutingDurableStore:
        def get_invocation(self, _invocation_ref: str) -> object:
            return current

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_DURABLE_INVOCATION_REF_MISMATCH",
    ):
        restarted.sync_runtime_invocations(
            [legacy],
            invocation_store=_SubstitutingDurableStore(),  # type: ignore[arg-type]
        )

    class _SameRefSubstitutingDurableStore:
        def get_invocation(self, _invocation_ref: str) -> object:
            return substituted

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUNTIME_PROJECTION_INCOMPATIBILITY_BINDING_MISMATCH",
    ):
        restarted.sync_runtime_invocations(
            [legacy],
            invocation_store=(  # type: ignore[arg-type]
                _SameRefSubstitutingDurableStore()
            ),
        )

    class _MissingDurableStore:
        def get_invocation(self, _invocation_ref: str) -> object:
            raise RuntimeInvocationStorageError("missing")

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_DURABLE_INVOCATION_NOT_FOUND",
    ):
        restarted.sync_runtime_invocations(
            [legacy],
            invocation_store=_MissingDurableStore(),  # type: ignore[arg-type]
        )

    admitted_goal = _create_goal(
        restarted,
        _create_request(),
        idempotency_ref="idempotency-ref:future-quarantined-goal",
    )
    assert admitted_goal.goal_ref == future_goal.goal_ref
    newly_projected = restarted.sync_runtime_invocations(
        [legacy],
        invocation_store=store,
    )
    assert {event.run_ref for event in newly_projected} == {
        legacy.invocation_ref
    }
    assert len(restarted.events.replay(legacy.invocation_ref).events) == 2


@pytest.mark.parametrize(
    "failure_boundary",
    ["intent", "records", "head", "intent-delete"],
)
def test_projection_incompatibility_append_recovers_every_persistence_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_boundary: str,
) -> None:
    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    goal_ref = "goal-ref:sha256:" + "3" * 64
    runtime_store = RuntimeInvocationStore(
        tmp_path / "runtime",
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    record = invoke_governed_command(
        store=runtime_store,
        adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        request=RuntimeCommandExecutionRequest(
            intent="git_status",
            mission_ref=goal_ref,
            safe_summary="Record one bounded historical projection mismatch.",
        ),
        idempotency_ref=(
            f"idempotency-ref:projection-incompatibility:{failure_boundary}"
        ),
    ).record
    service = GoalRuntimeService(tmp_path / "goals")
    with service._runtime_projection_goal_absence_guard(  # noqa: SLF001
        goal_ref
    ) as goal_absence_proof_ref:
        assert goal_absence_proof_ref is not None
        original_atomic_write = goal_runtime_module._atomic_write  # noqa: SLF001
        target_path = {
            "intent": service._events.incompatibilities_append_intent_path,
            "records": service._events.incompatibilities_path,
            "head": service._events.incompatibilities_head_path,
        }.get(failure_boundary)

        def interrupt_atomic_write(path: Path, content: str) -> None:
            if target_path is not None and path == target_path:
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_atomic_write(path, content)

        original_delete = (
            service._events._delete_projection_incompatibility_append_intent
        )

        def interrupt_delete() -> None:
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")

        monkeypatch.setattr(
            goal_runtime_module,
            "_atomic_write",
            interrupt_atomic_write,
        )
        if failure_boundary == "intent-delete":
            monkeypatch.setattr(
                service._events,
                "_delete_projection_incompatibility_append_intent",
                interrupt_delete,
            )
        with pytest.raises(
            GoalRuntimeError,
            match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
        ):
            service._events.quarantine_projection_incompatibility(  # noqa: SLF001
                record,
                goal_absence_proof_ref=goal_absence_proof_ref,
            )

        monkeypatch.setattr(
            goal_runtime_module,
            "_atomic_write",
            original_atomic_write,
        )
        monkeypatch.setattr(
            service._events,
            "_delete_projection_incompatibility_append_intent",
            original_delete,
        )
        if failure_boundary == "intent":
            assert service.events.projection_incompatibilities() == []
            recovered = service._events.quarantine_projection_incompatibility(  # noqa: SLF001
                record,
                goal_absence_proof_ref=goal_absence_proof_ref,
            )
        else:
            recovered = service.events.projection_incompatibilities()[0]

    assert recovered.invocation_ref == record.invocation_ref
    assert not service._events.incompatibilities_append_intent_path.exists()
    assert GoalRuntimeService(
        tmp_path / "goals"
    ).events.projection_incompatibilities() == [recovered]


def test_projection_incompatibility_read_retries_first_lock_generation_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")
    original_read_lock = goal_runtime_module._nonmutating_goal_runtime_read_lock
    attempts = 0

    @contextmanager
    def first_generation_changes(*args: object, **kwargs: object):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise goal_runtime_module._GoalRuntimeGenerationChanged
        with original_read_lock(*args, **kwargs):
            yield

    monkeypatch.setattr(
        goal_runtime_module,
        "_nonmutating_goal_runtime_read_lock",
        first_generation_changes,
    )

    assert service.events.projection_incompatibilities() == []
    assert attempts == 2


def test_projection_incompatibility_read_fails_after_bounded_generation_races(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path / "goals")
    attempts = 0

    @contextmanager
    def generation_always_changes(*_args: object, **_kwargs: object):
        nonlocal attempts
        attempts += 1
        raise goal_runtime_module._GoalRuntimeGenerationChanged
        yield  # pragma: no cover

    monkeypatch.setattr(
        goal_runtime_module,
        "_nonmutating_goal_runtime_read_lock",
        generation_always_changes,
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUNTIME_PROJECTION_INCOMPATIBILITY_GENERATION_UNSTABLE",
    ):
        service.events.projection_incompatibilities()
    assert attempts == 3


def test_runtime_gateway_projects_failed_receipt_as_terminal_failure(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "runtime"
    goal_service = GoalRuntimeService(tmp_path / "goals")

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=1,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_FAILURE",
        )

    result = RuntimeGateway(
        store=RuntimeInvocationStore(
            runtime_dir,
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=goal_service,
    ).invoke_command(
        RuntimeCommandExecutionRequest(
            intent="git_status",
            safe_summary="Inspect current repository status with redacted output.",
        ),
        idempotency_ref="idempotency-ref:runtime-event-failed-producer",
    )

    replay = goal_service.events.replay(result.record.invocation_ref)
    assert [event.event_kind for event in replay.events] == [
        DurableRunEventKind.run_started.value,
        DurableRunEventKind.failed_terminal.value,
    ]
    assert replay.events[-1].receipt_refs == [result.record.receipt.receipt_ref]
    assert not any(
        event.event_kind == DurableRunEventKind.receipt_recorded.value
        for event in replay.events
    )


@pytest.mark.parametrize("journal_state", ["missing", "empty"])
def test_event_journal_cannot_disappear_while_tombstones_remain(
    tmp_path: Path,
    journal_state: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:journal-disappearance",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="A durable local run started.",
            idempotency_ref="idempotency-ref:journal-disappearance",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    path = tmp_path / "run_events.jsonl"
    if journal_state == "missing":
        path.unlink()
    else:
        path.write_text("", encoding="utf-8")

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_JOURNAL_MISSING_WITH_IDEMPOTENCY_HISTORY",
    ):
        GoalRuntimeService(tmp_path).events.replay("run-ref:journal-disappearance")


@pytest.mark.parametrize(
    "rollback",
    ["whole-run", "oldest-retained", "latest-suffix"],
)
def test_event_journal_rejects_individual_run_rollback(
    tmp_path: Path,
    rollback: str,
) -> None:
    service = GoalRuntimeService(tmp_path, retention_limit=3)
    rolled_back_run_ref = "run-ref:journal-rollback:target"
    for index in range(1, 5):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref=rolled_back_run_ref,
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.evidence_linked,
                safe_summary=f"Bounded target event {index}.",
                proof_refs=[f"proof-ref:journal-rollback:target:{index}"],
                idempotency_ref=(f"idempotency-ref:journal-rollback:target:{index}"),
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:journal-rollback:survivor",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="The unrelated retained stream remains present.",
            idempotency_ref="idempotency-ref:journal-rollback:survivor",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    event_path = tmp_path / "run_events.jsonl"
    rows = [
        json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()
    ]
    if rollback == "whole-run":
        rows = [row for row in rows if row["run_ref"] != rolled_back_run_ref]
    elif rollback == "oldest-retained":
        rows = [
            row
            for row in rows
            if not (row["run_ref"] == rolled_back_run_ref and row["sequence"] == 2)
        ]
    else:
        rows = [
            row
            for row in rows
            if not (row["run_ref"] == rolled_back_run_ref and row["sequence"] == 4)
        ]
    event_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_JOURNAL_RETAINED_SUFFIX_MISMATCH",
    ):
        GoalRuntimeService(tmp_path, retention_limit=3).events.replay(
            rolled_back_run_ref
        )


def test_event_generation_head_rejects_paired_valid_prefix_rollback(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    run_ref = "run-ref:paired-prefix-rollback"
    prior_events = b""
    prior_tombstones = b""
    for index in range(2):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref=run_ref,
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.evidence_linked,
                safe_summary="Retain bounded evidence for rollback detection.",
                proof_refs=[f"proof-ref:paired-prefix-rollback:{index}"],
                idempotency_ref=f"idempotency-ref:paired-prefix-rollback:{index}",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )
        if index == 0:
            prior_events = service._events.path.read_bytes()  # noqa: SLF001
            prior_tombstones = (  # noqa: SLF001
                service._events.idempotency_path.read_bytes()
            )

    service._events.path.write_bytes(prior_events)  # noqa: SLF001
    service._events.idempotency_path.write_bytes(prior_tombstones)  # noqa: SLF001

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_GENERATION_HEAD_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).events.replay(run_ref)


def test_atomic_storage_failure_is_normalized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)

    def fail_replace(*_args: object, **_kwargs: object) -> None:
        raise OSError("raw storage failure")

    monkeypatch.setattr(goal_runtime_module.os, "replace", fail_replace)
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        _create_goal(
            service,
            _create_request(),
            idempotency_ref="idempotency-ref:storage-failure:create",
        )


def test_atomic_storage_rejects_unsynced_parent_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    original_open = goal_runtime_module.os.open

    def fail_parent_directory_open(
        path: str | bytes | Path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        if dir_fd is None and Path(path) == tmp_path:
            raise OSError("directory fsync descriptor unavailable")
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(
        goal_runtime_module.os,
        "open",
        fail_parent_directory_open,
    )
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        goal_runtime_module._atomic_write(target, "{}\n")  # noqa: SLF001


def test_atomic_storage_rejects_parent_directory_fsync_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "state.json"
    original_fsync = goal_runtime_module.os.fsync
    file_fsync_completed = False

    def fail_parent_directory_fsync(descriptor: int) -> None:
        nonlocal file_fsync_completed
        descriptor_mode = goal_runtime_module.os.fstat(descriptor).st_mode
        if stat.S_ISDIR(descriptor_mode):
            assert file_fsync_completed
            raise OSError("directory fsync failed")
        file_fsync_completed = True
        original_fsync(descriptor)

    monkeypatch.setattr(
        goal_runtime_module.os,
        "fsync",
        fail_parent_directory_fsync,
    )
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        goal_runtime_module._atomic_write(target, "{}\n")  # noqa: SLF001
    assert file_fsync_completed


def test_goal_runtime_files_are_private(tmp_path: Path) -> None:
    state_dir = tmp_path / "private-state"
    service = GoalRuntimeService(state_dir)
    assert not state_dir.exists()
    _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:private-files:create",
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:private-files",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="A bounded local run started.",
            idempotency_ref="idempotency-ref:private-files:event",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )

    assert stat.S_IMODE(state_dir.stat().st_mode) == 0o700
    for path in (
        state_dir / "goals.jsonl",
        state_dir / "goal_journal_head.json",
        state_dir / "run_events.jsonl",
        state_dir / "run_event_idempotency.jsonl",
    ):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.parametrize("substitution", ["symlink", "directory"])
@pytest.mark.parametrize(
    ("file_name", "read_surface", "expected_code"),
    [
        ("goals.jsonl", "goals", "GOAL_JOURNAL_CORRUPT"),
        (
            "goal_journal_head.json",
            "goals",
            "GOAL_JOURNAL_HEAD_MANIFEST_CORRUPT",
        ),
        ("run_events.jsonl", "events", "RUN_EVENT_STORE_CORRUPT"),
        (
            "run_event_idempotency.jsonl",
            "events",
            "RUN_EVENT_IDEMPOTENCY_STORE_CORRUPT",
        ),
        (
            "run_event_projection_reservations.jsonl",
            "reservations",
            "RUN_EVENT_PROJECTION_RESERVATION_STORE_CORRUPT",
        ),
    ],
)
def test_goal_runtime_durable_reads_reject_link_and_nonregular_substitution(
    tmp_path: Path,
    substitution: str,
    file_name: str,
    read_surface: str,
    expected_code: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:safe-file-reader:create",
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:safe-file-reader",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="A bounded local run started.",
            idempotency_ref="idempotency-ref:safe-file-reader:event",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    service._events.reserve_runtime_projection(  # noqa: SLF001
        None,
        operation_idempotency_ref="idempotency-ref:safe-file-reader:reservation",
    )

    path = tmp_path / file_name
    if substitution == "symlink":
        preserved = tmp_path / f"{file_name}.preserved"
        path.replace(preserved)
        path.symlink_to(preserved.name)
    else:
        path.unlink()
        path.mkdir()

    with pytest.raises(GoalRuntimeCorruptionError, match=expected_code):
        if read_surface == "goals":
            service.goals.read_model()
        elif read_surface == "events":
            service.events.summaries()
        else:
            service._events._load_projection_reservations()  # noqa: SLF001


def test_goal_journal_head_manifest_rejects_schema_drift(tmp_path: Path) -> None:
    service = GoalRuntimeService(tmp_path)
    _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:head-schema-drift:create",
    )
    head_path = tmp_path / "goal_journal_head.json"
    payload = json.loads(head_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "goal_journal_head.v2"
    head_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_HEAD_MANIFEST_CORRUPT",
    ):
        service.goals.read_model()


def test_goal_runtime_reads_do_not_initialize_storage(tmp_path: Path) -> None:
    state_dir = tmp_path / "read-only-state"
    service = GoalRuntimeService(state_dir)

    goals = service.goals.read_model()
    summaries = service.events.summaries()
    replay = service.events.replay("run-ref:read-only:missing")

    assert goals.goal_count == 0
    assert summaries == []
    assert replay.status == RunEventReplayStatus.unknown_run.value
    assert not state_dir.exists()

    existing_state_dir = tmp_path / "existing-read-only-state"
    existing_state_dir.mkdir(mode=0o755)
    existing_service = GoalRuntimeService(existing_state_dir)
    assert existing_service.goals.read_model().goal_count == 0
    assert existing_service.events.summaries() == []
    assert stat.S_IMODE(existing_state_dir.stat().st_mode) == 0o755
    assert list(existing_state_dir.iterdir()) == []


def test_first_lock_creation_race_retries_event_and_goal_generations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event_dir = tmp_path / "event-race"
    event_reader = GoalRuntimeService(event_dir)
    event_writer = GoalRuntimeService(event_dir)
    original_load_events = event_reader._events._load_events  # noqa: SLF001
    event_raced = False

    def race_event_generation() -> list[DurableRunEvent]:
        nonlocal event_raced
        if not event_raced:
            event_raced = True
            _append_event(
                event_writer,
                DurableRunEventAppendRequest(
                    run_ref="run-ref:first-lock-race",
                    run_type=AcceptedLocalRunType.local_read_task,
                    event_kind=DurableRunEventKind.run_started,
                    safe_summary="The first writer created a consistent generation.",
                    idempotency_ref="idempotency-ref:first-lock-race",
                    authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
                ),
            )
        return original_load_events()

    monkeypatch.setattr(
        event_reader._events,  # noqa: SLF001
        "_load_events",
        race_event_generation,
    )
    replay = event_reader.events.replay("run-ref:first-lock-race")
    assert event_raced is True
    assert [event.sequence for event in replay.events] == [1]

    goal_dir = tmp_path / "goal-race"
    goal_reader = GoalRuntimeService(goal_dir)
    goal_writer = GoalRuntimeService(goal_dir)
    original_load_entries = goal_reader.goals._load_entries  # noqa: SLF001
    goal_raced = False

    def race_goal_generation(
        *,
        repair_manifest: bool = False,
    ) -> list[object]:
        nonlocal goal_raced
        if not goal_raced:
            goal_raced = True
            _create_goal(
                goal_writer,
                _create_request(),
                idempotency_ref="idempotency-ref:first-goal-lock-race",
            )
        return original_load_entries(repair_manifest=repair_manifest)

    monkeypatch.setattr(
        goal_reader.goals,
        "_load_entries",
        race_goal_generation,
    )
    assert goal_reader.goals.read_model().goal_count == 1
    assert goal_raced is True


def test_goal_runtime_lock_failures_are_normalized(tmp_path: Path) -> None:
    event_dir = tmp_path / "event-lock-failure"
    event_dir.mkdir()
    (event_dir / ".locks").write_text("blocked", encoding="utf-8")
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        GoalRuntimeService(event_dir)._events.append(  # noqa: SLF001
            DurableRunEventAppendRequest(
                run_ref="run-ref:lock-failure",
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.run_started,
                safe_summary="A lock failure must remain safely normalized.",
                idempotency_ref="idempotency-ref:lock-failure",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            )
        )

    goal_dir = tmp_path / "goal-lock-failure"
    goal_dir.mkdir()
    (goal_dir / ".locks").write_text("blocked", encoding="utf-8")
    request = _create_request()
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        GoalRuntimeService(goal_dir).prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref="idempotency-ref:goal-lock-failure",
        )


@pytest.mark.parametrize(
    ("writer_key", "read_surface"),
    [
        ("run-events", "events"),
        ("goal-journal", "goals"),
    ],
)
def test_goal_runtime_reads_reject_dangling_lock_symlinks(
    tmp_path: Path,
    writer_key: str,
    read_surface: str,
) -> None:
    state_dir = tmp_path / writer_key
    lock_dir = state_dir / ".locks"
    lock_dir.mkdir(parents=True)
    (lock_dir / f"{writer_key}.lock").symlink_to("missing-lock-target")
    service = GoalRuntimeService(state_dir)

    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        if read_surface == "events":
            service.events.summaries()
        else:
            service.goals.read_model()


def test_run_event_writer_requires_exact_approval_and_is_not_on_reader(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:writer-authority",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.run_started,
        safe_summary="A bounded local run started.",
        idempotency_ref="idempotency-ref:writer-authority",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    wrong_request = request.model_copy(
        update={"safe_summary": "A different bounded local run started."}
    )
    wrong_approval_ref = _approved_mutation_ref(
        service,
        operation="append-run-event",
        goal_ref=None,
        request=wrong_request,
        idempotency_ref=wrong_request.idempotency_ref,
    )

    assert not hasattr(service.events, "append")
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_SCOPE_MISMATCH",
    ):
        service.append_run_event(request, approval_ref=wrong_approval_ref)
    assert service.events.replay(request.run_ref).events == []


@pytest.mark.parametrize(
    "event_kind",
    [
        DurableRunEventKind.receipt_recorded,
        DurableRunEventKind.completion_verified,
        DurableRunEventKind.cancelled,
        DurableRunEventKind.failed_terminal,
        DurableRunEventKind.dead_lettered,
    ],
)
def test_run_event_writer_rejects_trusted_producer_events(
    tmp_path: Path,
    event_kind: DurableRunEventKind,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref=f"run-ref:trusted-producer:{event_kind.value}",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=event_kind,
        safe_summary="A fabricated receipt-bearing event must fail closed.",
        proof_refs=[f"proof-ref:trusted-producer:{event_kind.value}"],
        receipt_refs=[f"receipt-ref:trusted-producer:{event_kind.value}"],
        goal_ref="goal-ref:trusted-producer",
        idempotency_ref=f"idempotency-ref:trusted-producer:{event_kind.value}",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="RUN_EVENT_TRUSTED_PRODUCER_REQUIRED",
    ):
        service.append_run_event(
            request,
            approval_ref="approval-ref:trusted-producer-not-consumed",
        )
    assert service.events.replay(request.run_ref).events == []


def test_runtime_projection_capacity_fails_before_adapter_side_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal_service = GoalRuntimeService(tmp_path / "goals")
    _append_event(
        goal_service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:capacity:existing",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="An existing bounded run occupied the event index.",
            idempotency_ref="idempotency-ref:capacity:existing",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_RUN_EVENT_IDEMPOTENCY_RECORDS",
        2,
    )
    calls = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        calls += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=goal_service,
    )
    with pytest.raises(
        GoalRuntimeError,
        match="RUN_EVENT_IDEMPOTENCY_CAPACITY_EXCEEDED",
    ):
        gateway.invoke_command(
            RuntimeCommandExecutionRequest(
                intent="git_status",
                safe_summary="Inspect repository status with redacted output.",
            ),
            idempotency_ref="idempotency-ref:capacity:new-runtime",
        )

    assert calls == 0
    assert gateway.store.list_invocations() == []


def test_runtime_projection_byte_capacity_fails_before_adapter_side_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    goal_service = GoalRuntimeService(tmp_path / "goals")
    _append_event(
        goal_service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:byte-capacity:existing",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="An existing bounded run occupied encoded event bytes.",
            idempotency_ref="idempotency-ref:byte-capacity:existing",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    event_bytes = goal_service._events.path.stat().st_size  # noqa: SLF001
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_RUN_EVENT_STORE_BYTES",
        event_bytes + 2 * goal_runtime_module.MAX_RESERVED_RUN_EVENT_BYTES - 1,
    )
    calls = 0

    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        nonlocal calls
        calls += 1
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    gateway = RuntimeGateway(
        store=RuntimeInvocationStore(
            tmp_path / "runtime",
            active_authority_leases=[workspace_execute_authority_lease()],
        ),
        command_adapter=GovernedCommandRuntimeAdapter(
            workspace_root=ROOT,
            runner=runner,
        ),
        goal_runtime_service=goal_service,
    )
    with pytest.raises(
        GoalRuntimeError,
        match="RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED",
    ):
        gateway.invoke_command(
            RuntimeCommandExecutionRequest(
                intent="git_status",
                safe_summary="Inspect repository status with redacted output.",
            ),
            idempotency_ref="idempotency-ref:byte-capacity:new-runtime",
        )

    assert calls == 0
    assert gateway.store.list_invocations() == []


@pytest.mark.parametrize(
    ("limit_name", "expected_code"),
    [
        ("MAX_RUN_EVENT_STORE_BYTES", "RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED"),
        (
            "MAX_RUN_EVENT_IDEMPOTENCY_BYTES",
            "RUN_EVENT_IDEMPOTENCY_BYTE_CAPACITY_EXCEEDED",
        ),
    ],
)
def test_nonreserved_append_preserves_active_projection_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit_name: str,
    expected_code: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    reservation_ref = service._events.reserve_runtime_projection(  # noqa: SLF001
        None,
        operation_idempotency_ref="idempotency-ref:reserved-byte-allowance",
    )
    event_bytes = (
        service._events.path.stat().st_size  # noqa: SLF001
        if service._events.path.exists()  # noqa: SLF001
        else 0
    )
    tombstone_bytes = (
        service._events.idempotency_path.stat().st_size  # noqa: SLF001
        if service._events.idempotency_path.exists()  # noqa: SLF001
        else 0
    )
    reserved_bytes = 2 * (
        goal_runtime_module.MAX_RESERVED_RUN_EVENT_BYTES
        if limit_name == "MAX_RUN_EVENT_STORE_BYTES"
        else goal_runtime_module.MAX_RESERVED_RUN_EVENT_TOMBSTONE_BYTES
    )
    monkeypatch.setattr(
        goal_runtime_module,
        limit_name,
        (event_bytes if limit_name == "MAX_RUN_EVENT_STORE_BYTES" else tombstone_bytes)
        + reserved_bytes,
    )

    with pytest.raises(GoalRuntimeError, match=expected_code):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref="run-ref:unrelated-reserved-bytes",
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.run_started,
                safe_summary="An unrelated append cannot consume reserved bytes.",
                idempotency_ref="idempotency-ref:unrelated-reserved-bytes",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )

    assert reservation_ref in service._events._load_projection_reservations()  # noqa: SLF001


def test_completion_event_capacity_fails_before_goal_transition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:completion-capacity:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:completion-capacity:request",
        ),
        idempotency_ref="idempotency-ref:completion-capacity:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    event_bytes = service._events.path.stat().st_size  # noqa: SLF001
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_RUN_EVENT_STORE_BYTES",
        event_bytes + goal_runtime_module.MAX_RESERVED_RUN_EVENT_BYTES - 1,
    )

    with pytest.raises(
        GoalRuntimeError,
        match="RUN_EVENT_STORE_BYTE_CAPACITY_EXCEEDED",
    ):
        _transition_goal(
            service,
            created.goal_ref,
            GoalTransitionRequest(
                expected_version=requested.version,
                transition=GoalTransitionKind.verify_completion,
                reason_ref="reason-ref:completion-capacity:verify",
                completion_evidence=_completion_evidence(requested),
            ),
            idempotency_ref="idempotency-ref:completion-capacity:verify",
        )

    unchanged = service.goals.get(created.goal_ref)
    assert unchanged.state == GoalState.complete_requested.value
    assert unchanged.version == requested.version
    assert not any(
        event.event_kind == DurableRunEventKind.completion_verified.value
        for event in service.events.retained_events()
    )


def test_completion_capacity_credits_exact_retention_eviction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path, retention_limit=2)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:completion-retention:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:completion-retention:request",
        ),
        idempotency_ref="idempotency-ref:completion-retention:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:accepted-local:one",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.evidence_linked,
            safe_summary="Additional bounded evidence reached the retention limit.",
            proof_refs=["proof-ref:completion-retention:additional"],
            goal_ref=created.goal_ref,
            plan_ref="plan-ref:accepted-local:one",
            idempotency_ref="idempotency-ref:completion-retention:additional",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    retained_before = service.events.retained_events(
        run_ref="run-ref:accepted-local:one"
    )
    event_bytes = service._events.path.stat().st_size  # noqa: SLF001
    persisted_event = service._events._event_json(retained_before[0])  # noqa: SLF001
    eviction_credit = len((persisted_event + "\n").encode("utf-8"))
    assert eviction_credit < len(
        (retained_before[0].model_dump_json() + "\n").encode("utf-8")
    )
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_RUN_EVENT_STORE_BYTES",
        (
            event_bytes
            + goal_runtime_module.MAX_RESERVED_RUN_EVENT_BYTES
            - eviction_credit
        ),
    )

    verified = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=requested.version,
            transition=GoalTransitionKind.verify_completion,
            reason_ref="reason-ref:completion-retention:verify",
            completion_evidence=_completion_evidence(requested),
        ),
        idempotency_ref="idempotency-ref:completion-retention:verify",
    )
    retained_after = service.events.retained_events(
        run_ref="run-ref:accepted-local:one"
    )

    assert verified.state == GoalState.verified_complete.value
    assert [event.sequence for event in retained_after] == [2, 3]
    assert retained_after[-1].event_kind == (
        DurableRunEventKind.completion_verified.value
    )


def test_projection_byte_reservation_bounds_maximal_event_and_tombstone(
    tmp_path: Path,
) -> None:
    def maximal_ref(prefix: str, discriminator: str) -> str:
        suffix_length = goal_runtime_module.MAX_EXECUTION_REF_LENGTH - len(prefix)
        return prefix + discriminator + "x" * (suffix_length - len(discriminator))

    service = GoalRuntimeService(tmp_path)
    event = _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref=maximal_ref("run-ref:", "r"),
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="s" * goal_runtime_module.MAX_GOAL_TEXT,
            proof_refs=[
                maximal_ref("proof-ref:", f"{index:02d}")
                for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
            ],
            receipt_refs=[
                maximal_ref("receipt-ref:", f"{index:02d}")
                for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
            ],
            goal_ref=maximal_ref("goal-ref:", "g"),
            plan_ref=maximal_ref("plan-ref:", "p"),
            idempotency_ref=maximal_ref("idempotency-ref:", "i"),
            authority_decision_ref=maximal_ref("authority-decision-ref:", "a"),
        ),
    )
    tombstone = service._events._load_idempotency_tombstones(  # noqa: SLF001
        [event]
    )[(event.run_ref, event.idempotency_ref)]

    assert len((event.model_dump_json() + "\n").encode("utf-8")) <= (
        goal_runtime_module.MAX_RESERVED_RUN_EVENT_BYTES
    )
    assert len((tombstone.model_dump_json() + "\n").encode("utf-8")) <= (
        goal_runtime_module.MAX_RESERVED_RUN_EVENT_TOMBSTONE_BYTES
    )


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("event_hash_ref", "RUN_EVENT_HASH_MISMATCH"),
        ("sequence", "RUN_EVENT_REF_BINDING_MISMATCH"),
        ("predecessor_hash_ref", "RUN_EVENT_PREDECESSOR_HASH_MISMATCH"),
        ("run_type", "RUN_EVENT_TYPE_SUBSTITUTION"),
    ],
)
def test_run_event_tampering_fails_closed(
    tmp_path: Path,
    mutation: str,
    expected_code: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    run_ref = "run-ref:accepted-local:tamper"
    for index in range(1, 3):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref=run_ref,
                run_type=AcceptedLocalRunType.local_metadata_action,
                event_kind=DurableRunEventKind.goal_linked,
                safe_summary=f"Bounded event {index}.",
                proof_refs=[f"proof-ref:tamper:{index}"],
                goal_ref="goal-ref:tamper",
                idempotency_ref=f"idempotency-ref:tamper:{index}",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )

    path = tmp_path / "run_events.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if mutation == "event_hash_ref":
        rows[1][mutation] = "event-hash-ref:tampered"
    elif mutation == "sequence":
        rows[1][mutation] = 9
        rows[1]["event_hash_ref"] = service._events._event_hash(  # noqa: SLF001
            service._events._load_events()[1].model_copy(  # noqa: SLF001
                update={"sequence": 9, "event_hash_ref": "event-hash-ref:pending"}
            )
        )
    elif mutation == "predecessor_hash_ref":
        rows[1][mutation] = "event-hash-ref:tampered-predecessor"
        event = service._events._load_events()[1].model_copy(  # noqa: SLF001
            update={
                "predecessor_hash_ref": rows[1][mutation],
                "event_hash_ref": "event-hash-ref:pending",
            }
        )
        rows[1]["event_hash_ref"] = service._events._event_hash(event)  # noqa: SLF001
    else:
        rows[1][mutation] = AcceptedLocalRunType.local_read_task.value
        event = service._events._load_events()[1].model_copy(  # noqa: SLF001
            update={
                "run_type": rows[1][mutation],
                "event_hash_ref": "event-hash-ref:pending",
            }
        )
        rows[1]["event_hash_ref"] = service._events._event_hash(event)  # noqa: SLF001
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(GoalRuntimeCorruptionError, match=expected_code):
        GoalRuntimeService(tmp_path).events.replay(run_ref)


def test_run_event_reorder_idempotency_completion_and_terminal_fences(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    run_ref = "run-ref:accepted-local:fences"
    receipt_request = DurableRunEventAppendRequest(
        run_ref=run_ref,
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.receipt_recorded,
        safe_summary="The accepted local read recorded bounded receipt evidence.",
        proof_refs=["proof-ref:fences:receipt"],
        receipt_refs=["receipt-ref:fences:receipt"],
        goal_ref="goal-ref:fences",
        idempotency_ref="idempotency-ref:fences:receipt",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    receipt = _append_event(service, receipt_request)
    assert _append_event(service, receipt_request) == receipt
    with pytest.raises(
        GoalIdempotencyConflictError,
        match="RUN_EVENT_IDEMPOTENCY_CONFLICT",
    ):
        _append_event(
            service,
            receipt_request.model_copy(
                update={"safe_summary": "A conflicting idempotent event."}
            ),
        )

    terminal = _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.failed_terminal,
            safe_summary="The bounded run reached a proof-backed terminal fence.",
            proof_refs=["proof-ref:fences:receipt"],
            receipt_refs=["receipt-ref:fences:receipt"],
            goal_ref="goal-ref:fences",
            idempotency_ref="idempotency-ref:fences:terminal",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    assert terminal.sequence == 2
    with pytest.raises(
        GoalTransitionDeniedError,
        match="RUN_EVENT_TERMINAL_STREAM_FENCE",
    ):
        service._events.append(  # noqa: SLF001
            DurableRunEventAppendRequest(
                run_ref=run_ref,
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.run_started,
                safe_summary="A late success event must not cross the terminal fence.",
                idempotency_ref="idempotency-ref:fences:late-success",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            )
        )

    unmatched_run_ref = "run-ref:accepted-local:unmatched-completion"
    _append_event(
        service,
        receipt_request.model_copy(
            update={
                "run_ref": unmatched_run_ref,
                "idempotency_ref": "idempotency-ref:fences:unmatched-receipt",
            }
        ),
    )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="RUN_EVENT_TRUSTED_PRODUCER_REQUIRED",
    ):
        service._events.append(  # noqa: SLF001
            DurableRunEventAppendRequest(
                run_ref=unmatched_run_ref,
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.completion_verified,
                safe_summary="Mismatched evidence must not verify completion.",
                proof_refs=["proof-ref:fences:other"],
                receipt_refs=["receipt-ref:fences:other"],
                goal_ref="goal-ref:fences",
                idempotency_ref="idempotency-ref:fences:unmatched-completion",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            )
        )

    reorder_dir = tmp_path / "reordered"
    reorder_service = GoalRuntimeService(reorder_dir)
    for index in range(1, 3):
        _append_event(
            reorder_service,
            DurableRunEventAppendRequest(
                run_ref="run-ref:accepted-local:reordered",
                run_type=AcceptedLocalRunType.local_metadata_action,
                event_kind=DurableRunEventKind.goal_linked,
                safe_summary=f"Ordered event {index}.",
                goal_ref="goal-ref:reordered",
                idempotency_ref=f"idempotency-ref:reordered:{index}",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )
    event_path = reorder_dir / "run_events.jsonl"
    rows = event_path.read_text(encoding="utf-8").splitlines()
    event_path.write_text("\n".join(reversed(rows)) + "\n", encoding="utf-8")
    with pytest.raises(GoalRuntimeCorruptionError, match="RUN_EVENT_SEQUENCE_GAP"):
        GoalRuntimeService(reorder_dir).events.replay(
            "run-ref:accepted-local:reordered"
        )


def test_goal_journal_tampering_fails_closed(tmp_path: Path) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-create-tamper",
    )
    _edit_goal(
        service,
        created.goal_ref,
        GoalEditRequest(
            expected_version=1,
            text_redaction_posture=("operator_authored_redacted_summary_only"),
            objective="A safely edited objective.",
        ),
        idempotency_ref="idempotency-ref:goal-edit-tamper",
    )
    path = tmp_path / "goals.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[1]["goal"]["objective"] = "A recomputed wrapper was not supplied."
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_ENTRY_HASH_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).goals.get(created.goal_ref)


def test_goal_journal_snapshot_cannot_relabel_an_approved_transition(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:snapshot-binding:create",
    )
    paused = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.pause,
            reason_ref="reason-ref:snapshot-binding:pause",
        ),
        idempotency_ref="idempotency-ref:snapshot-binding:pause",
    )
    approval_entries = service._approvals._load_consistent_entries()  # noqa: SLF001
    journal_entries = service.goals._load_consistent_entries()  # noqa: SLF001
    original = journal_entries[-1]
    substituted_request = GoalTransitionRequest(
        expected_version=created.version,
        transition=GoalTransitionKind.cancel,
        reason_ref="reason-ref:snapshot-binding:cancel",
    )
    substituted_goal = service.goals._transitioned_goal(  # noqa: SLF001
        journal_entries[0].goal,
        substituted_request,
        completion_verified=False,
        completion_plan_ref=None,
        completion_criterion_verifier_bindings=[],
        restore_goal=None,
        updated_at=original.recorded_at,
    )
    substituted = original.model_copy(
        update={
            "request_payload": substituted_request.model_dump(mode="json"),
            "request_fingerprint_ref": goal_runtime_module._sha256_ref(  # noqa: SLF001
                "request-fingerprint-ref:goal-transition",
                {
                    "goal_ref": created.goal_ref,
                    "request": substituted_request.model_dump(mode="json"),
                },
            ),
            "transition_reason_ref": substituted_request.reason_ref,
            "goal": substituted_goal,
        }
    )
    substituted = substituted.model_copy(
        update={
            "entry_hash_ref": service.goals._entry_hash(substituted)  # noqa: SLF001
        }
    )
    service.goals._validate_snapshot_transition(  # noqa: SLF001
        substituted,
        journal_entries[:-1],
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_PROVENANCE_MISMATCH",
    ):
        service._approvals.validate_goal_provenance(  # noqa: SLF001
            approval_entries,
            [journal_entries[0], substituted],
        )
    assert paused.state == GoalState.paused.value


@pytest.mark.parametrize(
    ("tamper", "expected_code"),
    [
        ("empty-journal", "GOAL_JOURNAL_EMPTY_ROLLBACK"),
        ("prefix-rollback", "GOAL_JOURNAL_HEAD_MANIFEST_MISMATCH"),
        ("missing-manifest", "GOAL_JOURNAL_HEAD_MANIFEST_MISSING"),
        ("manifest-mismatch", "GOAL_JOURNAL_HEAD_MANIFEST_MISMATCH"),
    ],
)
def test_goal_journal_head_manifest_rejects_rollback(
    tmp_path: Path,
    tamper: str,
    expected_code: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-head:create",
    )
    _edit_goal(
        service,
        created.goal_ref,
        GoalEditRequest(
            expected_version=created.version,
            text_redaction_posture="operator_authored_redacted_summary_only",
            objective="A second entry anchors the independent journal head.",
        ),
        idempotency_ref="idempotency-ref:goal-head:edit",
    )
    journal_path = tmp_path / "goals.jsonl"
    head_path = tmp_path / "goal_journal_head.json"
    if tamper == "empty-journal":
        journal_path.write_text("", encoding="utf-8")
    elif tamper == "prefix-rollback":
        journal_path.write_text(
            journal_path.read_text(encoding="utf-8").splitlines()[0] + "\n",
            encoding="utf-8",
        )
    elif tamper == "missing-manifest":
        head_path.unlink()
    else:
        manifest = json.loads(head_path.read_text(encoding="utf-8"))
        manifest["idempotency_set_hash_ref"] = (
            "idempotency-set-hash-ref:goal-journal:sha256:" + "0" * 64
        )
        head_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(GoalRuntimeCorruptionError, match=expected_code):
        GoalRuntimeService(tmp_path).goals.get(created.goal_ref)


def test_goal_journal_rejects_unbound_one_entry_ahead_manifest_on_mutation(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-head-recovery:create",
    )
    old_manifest = (tmp_path / "goal_journal_head.json").read_text(encoding="utf-8")
    edited = _edit_goal(
        service,
        created.goal_ref,
        GoalEditRequest(
            expected_version=created.version,
            text_redaction_posture="operator_authored_redacted_summary_only",
            objective="The journal commit survived before its head update.",
        ),
        idempotency_ref="idempotency-ref:goal-head-recovery:edit",
    )
    (tmp_path / "goal_journal_head.json").write_text(
        old_manifest,
        encoding="utf-8",
    )

    assert edited.version == 2
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_HEAD_MANIFEST_MISMATCH",
    ):
        _edit_goal(
            GoalRuntimeService(tmp_path),
            created.goal_ref,
            GoalEditRequest(
                expected_version=created.version,
                text_redaction_posture="operator_authored_redacted_summary_only",
                objective="The journal commit survived before its head update.",
            ),
            idempotency_ref="idempotency-ref:goal-head-recovery:edit",
        )


@pytest.mark.parametrize("surface", ["list", "show"])
def test_direct_goal_reads_reject_unbound_one_entry_ahead_manifest(
    tmp_path: Path,
    surface: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-direct-recovery:create",
    )
    old_manifest = (tmp_path / "goal_journal_head.json").read_text(
        encoding="utf-8"
    )
    edited = _edit_goal(
        service,
        created.goal_ref,
        GoalEditRequest(
            expected_version=created.version,
            text_redaction_posture="operator_authored_redacted_summary_only",
            objective="Direct goal reads recover the exact committed generation.",
        ),
        idempotency_ref="idempotency-ref:goal-direct-recovery:edit",
    )
    (tmp_path / "goal_journal_head.json").write_text(
        old_manifest,
        encoding="utf-8",
    )

    assert edited.version == 2
    restarted = GoalRuntimeService(tmp_path)
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_HEAD_MANIFEST_MISMATCH",
    ):
        if surface == "list":
            restarted.goal_lifecycle_read_model(include_cleared=True)
        else:
            restarted.goal_with_provenance(created.goal_ref)


@pytest.mark.parametrize(
    "failure_boundary",
    ["intent", "journal", "head", "cleanup"],
)
def test_goal_journal_recovers_only_exact_precommitted_append(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_boundary: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref=f"idempotency-ref:append-intent:{failure_boundary}:create",
    )
    request = GoalEditRequest(
        expected_version=created.version,
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective="Recover only the exact precommitted journal append.",
    )
    edit_idempotency_ref = (
        f"idempotency-ref:append-intent:{failure_boundary}:edit"
    )
    original_atomic_write = goal_runtime_module._atomic_write
    original_cleanup = service.goals._delete_append_intent  # noqa: SLF001
    failed = False

    if failure_boundary != "cleanup":

        def fail_selected_write(path: Path, content: str) -> None:
            nonlocal failed
            if not failed and (
                (
                    failure_boundary == "intent"
                    and path.name == "goal_journal_append_intent.json"
                )
                or (failure_boundary == "journal" and path.name == "goals.jsonl")
                or (
                    failure_boundary == "head"
                    and path.name == "goal_journal_head.json"
                )
            ):
                failed = True
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_atomic_write(path, content)

        monkeypatch.setattr(
            goal_runtime_module,
            "_atomic_write",
            fail_selected_write,
        )
    else:

        def fail_cleanup() -> None:
            nonlocal failed
            if not failed:
                failed = True
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_cleanup()

        monkeypatch.setattr(service.goals, "_delete_append_intent", fail_cleanup)

    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        _edit_goal(
            service,
            created.goal_ref,
            request,
            idempotency_ref=edit_idempotency_ref,
        )
    assert failed

    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)
    if failure_boundary == "cleanup":
        monkeypatch.setattr(service.goals, "_delete_append_intent", original_cleanup)
    recovered = _edit_goal(
        GoalRuntimeService(tmp_path),
        created.goal_ref,
        request,
        idempotency_ref=edit_idempotency_ref,
    )

    assert recovered.version == 2
    assert recovered.objective == request.objective
    assert not (tmp_path / "goal_journal_append_intent.json").exists()


def test_goal_journal_append_recovery_validates_approval_before_promotion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:append-provenance:create",
    )
    request = GoalEditRequest(
        expected_version=created.version,
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective="Never promote copied approval provenance.",
    )
    original_atomic_write = goal_runtime_module._atomic_write
    failed = False

    def fail_head_once(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goal_journal_head.json":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    monkeypatch.setattr(goal_runtime_module, "_atomic_write", fail_head_once)
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        _edit_goal(
            service,
            created.goal_ref,
            request,
            idempotency_ref="idempotency-ref:append-provenance:edit",
        )
    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)

    approval_entries = service._approvals._load_consistent_entries()  # noqa: SLF001
    create_approval = next(
        entry
        for entry in approval_entries
        if entry.status == "approved" and entry.spec.operation == "create"
    )
    intent = service.goals._load_append_intent()  # noqa: SLF001
    assert intent is not None
    raw_entries = [
        goal_runtime_module.GoalJournalEntry.model_validate_json(line)
        for line in service.goals.path.read_text(encoding="utf-8").splitlines()
    ]
    substituted = raw_entries[-1].model_copy(
        update={
            "approval_ref": create_approval.spec.approval_ref,
            "approval_decision_ref": (
                service._approvals._binding_from_approved_entry(  # noqa: SLF001
                    create_approval
                ).approval_decision_ref
            ),
            "approval_ledger_entry_hash_ref": create_approval.entry_hash_ref,
            "approval_request_fingerprint_ref": (
                create_approval.spec.request_fingerprint_ref
            ),
            "approval_exact_scope_ref": create_approval.spec.exact_scope_ref,
        }
    )
    substituted = substituted.model_copy(
        update={
            "entry_hash_ref": service.goals._entry_hash(substituted)  # noqa: SLF001
        }
    )
    substituted_entries = [*raw_entries[:-1], substituted]
    substituted_intent = goal_runtime_module.GoalJournalAppendIntent(
        previous_head_manifest=intent.previous_head_manifest,
        next_entry=substituted,
        next_head_manifest=service.goals._build_head_manifest(  # noqa: SLF001
            substituted_entries
        ),
        journal_content_hash_ref=service.goals._journal_content_hash(  # noqa: SLF001
            substituted_entries
        ),
    )
    service.goals.path.write_text(  # noqa: SLF001
        service.goals._journal_content(substituted_entries),  # noqa: SLF001
        encoding="utf-8",
    )
    service.goals.append_intent_path.write_text(  # noqa: SLF001
        substituted_intent.model_dump_json() + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_PROVENANCE_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).goal_lifecycle_read_model(
            include_cleared=True
        )
    assert json.loads(
        service.goals.head_path.read_text(encoding="utf-8")  # noqa: SLF001
    )["entry_count"] == 1
    assert service.goals.append_intent_path.exists()  # noqa: SLF001


@pytest.mark.parametrize("intent_kind", ["genesis", "append"])
def test_goal_journal_intent_recovery_validates_candidate_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    intent_kind: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    original_atomic_write = goal_runtime_module._atomic_write
    failed = False

    def interrupt_journal_install(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goals.jsonl":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    if intent_kind == "genesis":
        request: GoalCreateRequest | GoalEditRequest = _create_request()
        operation_idempotency_ref = (
            "idempotency-ref:intent-snapshot:genesis"
        )
        approval_ref = _approved_mutation_ref(
            service,
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref=operation_idempotency_ref,
        )
        monkeypatch.setattr(
            goal_runtime_module,
            "_atomic_write",
            interrupt_journal_install,
        )
        with pytest.raises(
            GoalRuntimeError,
            match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
        ):
            service.create_goal(
                request,
                idempotency_ref=operation_idempotency_ref,
                approval_ref=approval_ref,
            )
        monkeypatch.setattr(
            goal_runtime_module,
            "_atomic_write",
            original_atomic_write,
        )
        intent = service.goals._load_genesis_intent()  # noqa: SLF001
        assert intent is not None
        substituted_entry = intent.entry.model_copy(
            update={
                "goal": intent.entry.goal.model_copy(
                    update={"state": GoalState.cancelled.value}
                )
            }
        )
        substituted_entry = substituted_entry.model_copy(
            update={
                "entry_hash_ref": service.goals._entry_hash(  # noqa: SLF001
                    substituted_entry
                )
            }
        )
        substituted_entries = [substituted_entry]
        substituted_intent = goal_runtime_module.GoalJournalGenesisIntent(
            entry=substituted_entry,
            head_manifest=service.goals._build_head_manifest(  # noqa: SLF001
                substituted_entries
            ),
            journal_content_hash_ref=service.goals._journal_content_hash(  # noqa: SLF001
                substituted_entries
            ),
        )
        service.goals.genesis_intent_path.write_text(  # noqa: SLF001
            substituted_intent.model_dump_json() + "\n",
            encoding="utf-8",
        )
    else:
        created = _create_goal(
            service,
            _create_request(),
            idempotency_ref="idempotency-ref:intent-snapshot:create",
        )
        request = GoalEditRequest(
            expected_version=created.version,
            text_redaction_posture="operator_authored_redacted_summary_only",
            objective="Install only a request-derived edit snapshot.",
        )
        operation_idempotency_ref = "idempotency-ref:intent-snapshot:edit"
        approval_ref = _approved_mutation_ref(
            service,
            operation="edit",
            goal_ref=created.goal_ref,
            request=request,
            idempotency_ref=operation_idempotency_ref,
        )
        monkeypatch.setattr(
            goal_runtime_module,
            "_atomic_write",
            interrupt_journal_install,
        )
        with pytest.raises(
            GoalRuntimeError,
            match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
        ):
            service.edit_goal(
                created.goal_ref,
                request,
                idempotency_ref=operation_idempotency_ref,
                approval_ref=approval_ref,
            )
        monkeypatch.setattr(
            goal_runtime_module,
            "_atomic_write",
            original_atomic_write,
        )
        intent = service.goals._load_append_intent()  # noqa: SLF001
        assert intent is not None
        substituted_entry = intent.next_entry.model_copy(
            update={
                "goal": intent.next_entry.goal.model_copy(
                    update={"state": GoalState.cancelled.value}
                )
            }
        )
        substituted_entry = substituted_entry.model_copy(
            update={
                "entry_hash_ref": service.goals._entry_hash(  # noqa: SLF001
                    substituted_entry
                )
            }
        )
        prior_entries = [
            goal_runtime_module.GoalJournalEntry.model_validate_json(line)
            for line in service.goals.path.read_text(encoding="utf-8").splitlines()  # noqa: SLF001
        ]
        substituted_entries = [*prior_entries, substituted_entry]
        substituted_intent = goal_runtime_module.GoalJournalAppendIntent(
            previous_head_manifest=intent.previous_head_manifest,
            next_entry=substituted_entry,
            next_head_manifest=service.goals._build_head_manifest(  # noqa: SLF001
                substituted_entries
            ),
            journal_content_hash_ref=service.goals._journal_content_hash(  # noqa: SLF001
                substituted_entries
            ),
        )
        service.goals.append_intent_path.write_text(  # noqa: SLF001
            substituted_intent.model_dump_json() + "\n",
            encoding="utf-8",
        )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_SNAPSHOT_TRANSITION_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).goal_lifecycle_read_model(
            include_cleared=True
        )
    assert not service.goals.path.exists() or len(  # noqa: SLF001
        service.goals.path.read_text(encoding="utf-8").splitlines()  # noqa: SLF001
    ) == (0 if intent_kind == "genesis" else 1)


@pytest.mark.parametrize("substitution", ["symlink", "directory"])
def test_goal_journal_append_recovery_rejects_nonregular_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    substitution: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:append-intent-substitution:create",
    )
    request = GoalEditRequest(
        expected_version=created.version,
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective="Reject substituted append intent state.",
    )
    original_atomic_write = goal_runtime_module._atomic_write
    failed = False

    def interrupt_journal_install(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goals.jsonl":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    monkeypatch.setattr(
        goal_runtime_module,
        "_atomic_write",
        interrupt_journal_install,
    )
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        _edit_goal(
            service,
            created.goal_ref,
            request,
            idempotency_ref="idempotency-ref:append-intent-substitution:edit",
        )
    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)

    intent_path = service.goals.append_intent_path  # noqa: SLF001
    if substitution == "symlink":
        preserved = tmp_path / "goal_journal_append_intent.preserved"
        intent_path.replace(preserved)
        intent_path.symlink_to(preserved.name)
    else:
        intent_path.unlink()
        intent_path.mkdir()

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_APPEND_INTENT_CORRUPT",
    ):
        _edit_goal(
            GoalRuntimeService(tmp_path),
            created.goal_ref,
            request,
            idempotency_ref="idempotency-ref:append-intent-substitution:edit",
        )


def test_direct_goal_read_repairs_bound_first_generation_genesis_intent(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-direct-genesis:create",
    )
    [entry] = service.goals._load_consistent_entries()  # noqa: SLF001
    manifest = service.goals._build_head_manifest([entry])  # noqa: SLF001
    intent = goal_runtime_module.GoalJournalGenesisIntent(
        entry=entry,
        head_manifest=manifest,
        journal_content_hash_ref=service.goals._journal_content_hash([entry]),  # noqa: SLF001
    )
    service.goals._write_genesis_intent(intent)  # noqa: SLF001
    service.goals.path.unlink()  # noqa: SLF001
    service.goals.head_path.unlink()  # noqa: SLF001

    [recovered] = GoalRuntimeService(tmp_path).goal_lifecycle_read_model(
        include_cleared=True
    ).goals
    assert recovered == created
    assert not service.goals.genesis_intent_path.exists()  # noqa: SLF001


@pytest.mark.parametrize("surface", ["read", "mission"])
def test_independent_goal_journal_anchor_rejects_paired_prefix_rollback(
    tmp_path: Path,
    surface: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-anchor-rollback:create",
    )
    journal_path = tmp_path / "goals.jsonl"
    head_path = tmp_path / "goal_journal_head.json"
    original_journal = journal_path.read_text(encoding="utf-8")
    original_head = head_path.read_text(encoding="utf-8")
    _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.cancel,
            reason_ref="reason-ref:goal-anchor-rollback:cancel",
        ),
        idempotency_ref="idempotency-ref:goal-anchor-rollback:cancel",
    )
    journal_path.write_text(original_journal, encoding="utf-8")
    head_path.write_text(original_head, encoding="utf-8")

    restarted = GoalRuntimeService(tmp_path)
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_ROLLBACK_DETECTED",
    ):
        if surface == "read":
            restarted.goal_lifecycle_read_model(include_cleared=True)
        else:
            with restarted.runtime_mission_execution_guard(created.goal_ref):
                pass


def test_goal_transition_reason_tampering_fails_closed(tmp_path: Path) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-reason-tamper-create",
    )
    _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=1,
            transition=GoalTransitionKind.pause,
            reason_ref="reason-ref:goal-reason-original",
        ),
        idempotency_ref="idempotency-ref:goal-reason-tamper-pause",
    )
    path = tmp_path / "goals.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    rows[1]["transition_reason_ref"] = "reason-ref:goal-reason-substituted"
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_ENTRY_HASH_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).goals.get(created.goal_ref)


@pytest.mark.parametrize(
    "failure_boundary",
    ["intent", "journal", "head", "cleanup"],
)
def test_first_goal_commit_recovers_only_from_bound_genesis_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_boundary: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    original_atomic_write = goal_runtime_module._atomic_write
    original_cleanup = service.goals._delete_genesis_intent  # noqa: SLF001
    failed = False

    if failure_boundary in {"intent", "journal", "head"}:

        def fail_selected_write(path: Path, content: str) -> None:
            nonlocal failed
            if not failed and (
                (
                    failure_boundary == "intent"
                    and path.name == "goal_journal_genesis_intent.json"
                )
                or (failure_boundary == "journal" and path.name == "goals.jsonl")
                or (
                    failure_boundary == "head" and path.name == "goal_journal_head.json"
                )
            ):
                failed = True
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_atomic_write(path, content)

        monkeypatch.setattr(goal_runtime_module, "_atomic_write", fail_selected_write)
    else:

        def fail_cleanup() -> None:
            nonlocal failed
            if not failed:
                failed = True
                raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
            original_cleanup()

        monkeypatch.setattr(service.goals, "_delete_genesis_intent", fail_cleanup)

    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        _create_goal(
            service,
            request,
            idempotency_ref=f"idempotency-ref:genesis:{failure_boundary}",
        )
    assert failed

    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)
    if failure_boundary == "cleanup":
        monkeypatch.setattr(service.goals, "_delete_genesis_intent", original_cleanup)
    recovered = _create_goal(
        GoalRuntimeService(tmp_path),
        request,
        idempotency_ref=f"idempotency-ref:genesis:{failure_boundary}",
    )

    assert recovered.version == 1
    assert (tmp_path / "goals.jsonl").is_file()
    assert (tmp_path / "goal_journal_head.json").is_file()
    assert not (tmp_path / "goal_journal_genesis_intent.json").exists()


def test_unanchored_first_goal_journal_is_never_recovered(tmp_path: Path) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:unanchored-genesis:create",
    )
    (tmp_path / "goal_journal_head.json").unlink()

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_HEAD_MANIFEST_MISSING",
    ):
        GoalRuntimeService(tmp_path).goals.get(created.goal_ref)


@pytest.mark.parametrize("substitution", ["symlink", "directory"])
def test_genesis_intent_recovery_rejects_nonregular_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    substitution: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    original_atomic_write = goal_runtime_module._atomic_write
    failed = False

    def interrupt_journal_install(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goals.jsonl":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    monkeypatch.setattr(
        goal_runtime_module,
        "_atomic_write",
        interrupt_journal_install,
    )
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        _create_goal(
            service,
            _create_request(),
            idempotency_ref="idempotency-ref:genesis-substitution:create",
        )
    monkeypatch.setattr(
        goal_runtime_module,
        "_atomic_write",
        original_atomic_write,
    )
    intent_path = tmp_path / "goal_journal_genesis_intent.json"
    if substitution == "symlink":
        preserved = tmp_path / "goal_journal_genesis_intent.preserved"
        intent_path.replace(preserved)
        intent_path.symlink_to(preserved.name)
    else:
        intent_path.unlink()
        intent_path.mkdir()

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_JOURNAL_GENESIS_INTENT_CORRUPT",
    ):
        _create_goal(
            GoalRuntimeService(tmp_path),
            _create_request(),
            idempotency_ref="idempotency-ref:genesis-substitution:create",
        )


def test_lagging_tombstone_repairs_before_next_event_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    original_write = service._events._write_idempotency_tombstones  # noqa: SLF001
    first = DurableRunEventAppendRequest(
        run_ref="run-ref:tombstone-repair",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.goal_linked,
        safe_summary="The first event commits before its provenance tombstone.",
        goal_ref="goal-ref:tombstone-repair",
        idempotency_ref="idempotency-ref:tombstone-repair:one",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )

    monkeypatch.setattr(
        service._events,  # noqa: SLF001
        "_write_idempotency_tombstones",
        lambda _rows: (_ for _ in ()).throw(
            GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        ),
    )
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        _append_event(service, first)

    write_count = 0

    def repair_then_interrupt_second_tombstone(rows: object) -> None:
        nonlocal write_count
        write_count += 1
        if write_count == 2:
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_write(rows)

    monkeypatch.setattr(
        service._events,  # noqa: SLF001
        "_write_idempotency_tombstones",
        repair_then_interrupt_second_tombstone,
    )
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        _append_event(
            service,
            first.model_copy(
                update={
                    "safe_summary": (
                        "The next event is installed only after provenance repair."
                    ),
                    "idempotency_ref": "idempotency-ref:tombstone-repair:two",
                }
            ),
        )
    assert write_count == 2
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_APPEND_RECOVERY_REQUIRED",
    ):
        service.events.replay(
            "run-ref:tombstone-repair",
            after_sequence=0,
        )

    monkeypatch.setattr(
        service._events,  # noqa: SLF001
        "_write_idempotency_tombstones",
        original_write,
    )
    _append_event(
        service,
        first.model_copy(
            update={
                "safe_summary": (
                    "The next event is installed only after provenance repair."
                ),
                "idempotency_ref": "idempotency-ref:tombstone-repair:two",
            }
        ),
    )
    assert [
        event.sequence
        for event in service.events.replay(
            "run-ref:tombstone-repair",
            after_sequence=0,
        ).events
    ] == [1, 2]
    _append_event(
        service,
        first.model_copy(
            update={
                "safe_summary": "The third event follows a repaired generation.",
                "idempotency_ref": "idempotency-ref:tombstone-repair:three",
            }
        ),
    )
    assert [
        event.sequence
        for event in service.events.replay(
            "run-ref:tombstone-repair",
            after_sequence=0,
        ).events
    ] == [1, 2, 3]


@pytest.mark.parametrize(
    "failure_method",
    [
        "_write_trusted_sources",
        "_write_events",
        "_write_idempotency_tombstones",
        "_write_run_event_generation_head",
        "_delete_run_event_append_intent",
    ],
)
def test_run_event_append_intent_recovers_every_persistence_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_method: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref=f"run-ref:append-intent:{failure_method}",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.run_started,
        safe_summary="Precommit one exact bounded run-event generation.",
        idempotency_ref=f"idempotency-ref:append-intent:{failure_method}",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    binding = goal_runtime_module.TrustedRunEventSourceBinding(
        source_kind="trusted_core_internal",
        source_ref=f"source-ref:append-intent:{failure_method}",
        source_fingerprint_ref=(
            f"source-fingerprint-ref:append-intent:{failure_method}"
        ),
    )
    original = getattr(service._events, failure_method)  # noqa: SLF001

    def interrupt(*_args: object, **_kwargs: object) -> None:
        raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")

    monkeypatch.setattr(service._events, failure_method, interrupt)  # noqa: SLF001
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        service._events.append(request, trusted_source=binding)  # noqa: SLF001

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_APPEND_RECOVERY_REQUIRED",
    ):
        service.events.replay(request.run_ref)

    monkeypatch.setattr(service._events, failure_method, original)  # noqa: SLF001
    replayed = service._events.append(  # noqa: SLF001
        request,
        trusted_source=binding,
    )
    assert service.events.replay(request.run_ref).events == [replayed]
    assert not service._events.append_intent_path.exists()  # noqa: SLF001


@pytest.mark.parametrize(
    "unsafe_summary",
    [
        "Read /tmp/operator-data before continuing.",
        "Inspect /root/project/private.txt.",
        "Use /workspace/ultimate-ai-agent/private.txt.",
        r"Read C:\Users\operator\private.txt.",
        r"Read \\server\share\private.txt.",
        "Read file:///private/operator-data.",
        "Review path:/workspace/private.txt.",
        "Inspect artifact:/opt/company/private.txt.",
        "Inspect artifact-ref:bounded:/workspace/private.txt.",
        "Inspect artifact-ref:bounded://root/private.txt.",
        "Inspect artifact,/home/operator/private.txt.",
        "Inspect artifact;/Users/operator/private.txt.",
        "Inspect artifact|/home/operator/private.txt.",
        "Inspect artifact!/tmp/operator/private.txt.",
        "Inspect artifact{/root/operator/private.txt.",
        "Inspect artifact}/workspace/operator/private.txt.",
        "Inspect artifact#/var/operator/private.txt.",
        r"Inspect artifact|C:\Users\operator\private.txt.",
        r"Inspect artifact!\\server\share\private.txt.",
    ],
)
def test_durable_summaries_reject_every_absolute_local_path_family(
    unsafe_summary: str,
) -> None:
    with pytest.raises(ValueError, match="GOAL_RAW_CONTENT_PERSISTENCE_DENIED"):
        _create_request().model_copy(
            update={"objective": unsafe_summary}
        ).model_validate(
            _create_request()
            .model_copy(update={"objective": unsafe_summary})
            .model_dump()
        )
    with pytest.raises(ValueError, match="GOAL_RAW_CONTENT_PERSISTENCE_DENIED"):
        DurableRunEventAppendRequest(
            run_ref="run-ref:absolute-path",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary=unsafe_summary,
            idempotency_ref="idempotency-ref:absolute-path",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )


@pytest.mark.parametrize(
    "delimiter",
    list("!\"#$%&'()*+,-.;<=>?@[\\]^_`{|}~"),
)
def test_durable_summaries_reject_ascii_punctuation_path_delimiters(
    delimiter: str,
) -> None:
    unsafe_summary = f"Inspect artifact{delimiter}/home/operator/private.txt."

    with pytest.raises(ValueError, match="GOAL_RAW_CONTENT_PERSISTENCE_DENIED"):
        GoalCreateRequest.model_validate(
            _create_request()
            .model_copy(update={"objective": unsafe_summary})
            .model_dump(mode="json")
        )


@pytest.mark.parametrize(
    "safe_summary",
    [
        "Reviewed https://example.test/bounded-evidence.",
        "Recorded urn:uaa:evidence:bounded.",
        "Recorded artifact-ref:bounded/path.",
        "Recorded artifact-ref:bounded./path.",
        "Recorded artifact-ref:bounded-/path.",
        "Recorded artifact-ref:bounded@/path.",
        "Recorded artifact-ref:bounded_/path.",
    ],
)
def test_valid_uri_or_safe_ref_is_not_misclassified_as_a_local_path(
    safe_summary: str,
) -> None:
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:https-summary",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.run_started,
        safe_summary=safe_summary,
        idempotency_ref="idempotency-ref:https-summary",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    assert request.safe_summary == safe_summary


def test_goal_refs_reject_trailing_newlines() -> None:
    payload = _create_request().model_dump(mode="json")
    payload["evidence_refs"] = ["evidence-ref:bounded\n"]

    with pytest.raises(ValueError, match="structured safe ref"):
        GoalCreateRequest.model_validate(payload)


def test_maximum_unicode_goal_envelope_fits_derived_genesis_budget(
    tmp_path: Path,
) -> None:
    maximum_summary = "😀" * goal_runtime_module.MAX_GOAL_TEXT

    def distinct_summary(index: int) -> str:
        return ("😀" * (goal_runtime_module.MAX_GOAL_TEXT - 2)) + f"{index:02x}"

    request = GoalCreateRequest(
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective=maximum_summary,
        desired_outcome=maximum_summary,
        success_criteria=[
            distinct_summary(index)
            for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
        ],
        constraints=[
            distinct_summary(index + goal_runtime_module.MAX_GOAL_LIST_ITEMS)
            for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
        ],
        in_scope_resource_refs=[
            goal_runtime_module._maximum_typed_ref(  # noqa: SLF001
                "resource-ref:max-unicode",
                index,
            )
            for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
        ],
        stop_condition=maximum_summary,
        budget=goal_runtime_module.GoalBudget(
            operation_limit=10_000,
            cost_budget_microusd=10_000_000_000,
            deadline_at=datetime.max.replace(tzinfo=timezone.utc),
        ),
        links=goal_runtime_module.GoalLinks(
            plan_refs=[
                goal_runtime_module._maximum_typed_ref(  # noqa: SLF001
                    "plan-ref:max-unicode",
                    index,
                )
                for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
            ],
            run_refs=[
                goal_runtime_module._maximum_typed_ref(  # noqa: SLF001
                    "run-ref:max-unicode",
                    index,
                )
                for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
            ],
            action_inbox_refs=[
                goal_runtime_module._maximum_typed_ref(  # noqa: SLF001
                    "action-inbox-ref:max-unicode",
                    index,
                )
                for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
            ],
            work_board_refs=[
                goal_runtime_module._maximum_typed_ref(  # noqa: SLF001
                    "work-board-ref:max-unicode",
                    index,
                )
                for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
            ],
        ),
        evidence_refs=[
            goal_runtime_module._maximum_typed_ref(  # noqa: SLF001
                "evidence-ref:max-unicode",
                index,
            )
            for index in range(goal_runtime_module.MAX_GOAL_LIST_ITEMS)
        ],
    )
    service = GoalRuntimeService(tmp_path)

    created = _create_goal(
        service,
        request,
        idempotency_ref="idempotency-ref:max-unicode-envelope",
    )

    assert created.objective == maximum_summary
    assert service.goals.path.stat().st_size <= (
        goal_runtime_module.MAX_GOAL_JOURNAL_GENESIS_INTENT_BYTES
    )


def test_schema_maximum_envelopes_define_all_storage_reservations() -> None:
    maximum_intent = goal_runtime_module._MAXIMUM_GOAL_GENESIS_INTENT  # noqa: SLF001
    maximum_append_intent = (
        goal_runtime_module._MAXIMUM_GOAL_APPEND_INTENT  # noqa: SLF001
    )
    maximum_event = goal_runtime_module._MAXIMUM_RUN_EVENT  # noqa: SLF001
    maximum_tombstone = (
        goal_runtime_module._MAXIMUM_RUN_EVENT_TOMBSTONE  # noqa: SLF001
    )

    revalidated_goal = PersistentGoal.model_validate(
        maximum_intent.entry.goal.model_dump(mode="json")
    )
    assert revalidated_goal.objective == goal_runtime_module._maximum_typed_summary(  # noqa: SLF001
        0
    )
    assert (
        len((maximum_intent.model_dump_json() + "\n").encode("utf-8"))
        == goal_runtime_module.MAX_GOAL_JOURNAL_GENESIS_INTENT_BYTES
    )
    assert goal_runtime_module.MAX_GOAL_JOURNAL_GENESIS_INTENT_BYTES > 128 * 1024
    assert (
        len((maximum_append_intent.model_dump_json() + "\n").encode("utf-8"))
        == goal_runtime_module.MAX_GOAL_JOURNAL_APPEND_INTENT_BYTES
    )
    assert (
        goal_runtime_module.GoalJournalAppendIntent.model_validate(
            maximum_append_intent.model_dump(mode="json")
        )
        == maximum_append_intent
    )
    assert maximum_append_intent.next_head_manifest.entry_count == (
        goal_runtime_module.MAX_GOAL_JOURNAL_ENTRIES
    )
    assert len(maximum_event.proof_refs) == (
        goal_runtime_module.MAX_RUN_EVENT_PROOF_REFS
    )
    assert len(maximum_event.receipt_refs) == (
        goal_runtime_module.MAX_RUN_EVENT_RECEIPT_REFS
    )
    assert len(maximum_event.criterion_verifier_bindings) == (
        goal_runtime_module.MAX_GOAL_LIST_ITEMS
    )
    assert (
        len((maximum_event.model_dump_json() + "\n").encode("utf-8"))
        == goal_runtime_module.MAX_RESERVED_RUN_EVENT_BYTES
    )
    assert (
        len((maximum_tombstone.model_dump_json() + "\n").encode("utf-8"))
        == goal_runtime_module.MAX_RESERVED_RUN_EVENT_TOMBSTONE_BYTES
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "goal_ref",
        "goal_version",
        "criterion_ref",
        "proof_ref",
        "verifier_ref",
        "evaluator_receipt_ref",
    ],
)
def test_verified_goal_snapshot_rejects_tampered_evaluator_envelope(
    tmp_path: Path,
    field_name: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:envelope-tamper:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:envelope-tamper:request",
        ),
        idempotency_ref="idempotency-ref:envelope-tamper:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    verified = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=requested.version,
            transition=GoalTransitionKind.verify_completion,
            reason_ref="reason-ref:envelope-tamper:verify",
            completion_evidence=_completion_evidence(requested),
        ),
        idempotency_ref="idempotency-ref:envelope-tamper:verify",
    )
    bindings = list(verified.completion_criterion_verifier_bindings)
    replacement: object = "proof-ref:substituted-envelope"
    if field_name == "goal_version":
        replacement = verified.completion_source_goal_version + 1
    bindings[0] = bindings[0].model_copy(update={field_name: replacement})

    with pytest.raises(ValueError, match="GOAL_COMPLETION_CRITERION_BINDING"):
        PersistentGoal.model_validate(
            verified.model_copy(
                update={"completion_criterion_verifier_bindings": bindings}
            ).model_dump()
        )


def test_aggregate_snapshot_blocks_cross_store_mutation_until_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:aggregate-snapshot:create",
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref="run-ref:aggregate-snapshot",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.goal_linked,
            safe_summary="The aggregate snapshot starts from one durable event.",
            goal_ref=created.goal_ref,
            idempotency_ref="idempotency-ref:aggregate-snapshot:event",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    original_load = service._events._load_events  # noqa: SLF001
    reader_entered = threading.Event()
    release_reader = threading.Event()
    snapshot_holder: list[object] = []
    edit_holder: list[PersistentGoal] = []

    def slow_load() -> list[DurableRunEvent]:
        events = original_load()
        reader_entered.set()
        assert release_reader.wait(timeout=5)
        return events

    monkeypatch.setattr(service._events, "_load_events", slow_load)  # noqa: SLF001

    reader = threading.Thread(
        target=lambda: snapshot_holder.append(
            build_runtime_run_events_read_model(service=service)
        )
    )
    reader.start()
    assert reader_entered.wait(timeout=5)
    writer = threading.Thread(
        target=lambda: edit_holder.append(
            _edit_goal(
                service,
                created.goal_ref,
                GoalEditRequest(
                    expected_version=created.version,
                    text_redaction_posture=("operator_authored_redacted_summary_only"),
                    objective="The writer advances only after the snapshot.",
                ),
                idempotency_ref="idempotency-ref:aggregate-snapshot:edit",
            )
        )
    )
    writer.start()
    assert writer.is_alive()
    release_reader.set()
    reader.join(timeout=5)
    writer.join(timeout=5)

    assert not reader.is_alive()
    assert not writer.is_alive()
    snapshot = snapshot_holder[0]
    assert snapshot.goal_lifecycle.goals[0].version == created.version
    assert edit_holder[0].version == created.version + 1


def test_completion_rejects_cross_criterion_and_recomputed_client_evidence(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:criterion-provenance:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:criterion-provenance:request",
        ),
        idempotency_ref="idempotency-ref:criterion-provenance:request",
    )
    _append_receipt(service, goal_ref=created.goal_ref)
    correct = _completion_evidence(requested)
    receipt = service._events.assert_completion_appendable(  # noqa: SLF001
        run_ref=correct.run_ref,
        receipt_ref=correct.receipt_ref,
        proof_ref=correct.proof_ref,
        goal_ref=correct.goal_ref,
    )
    reversed_bindings = list(reversed(receipt.criterion_verifier_bindings))
    recomputed = correct.model_copy(
        update={
            "criterion_proof_refs": list(reversed(correct.criterion_proof_refs)),
            "evidence_ref": build_goal_completion_evidence_ref(
                requested,
                run_ref=correct.run_ref,
                receipt_ref=correct.receipt_ref,
                proof_ref=correct.proof_ref,
                criterion_verifier_bindings=reversed_bindings,
                plan_ref=receipt.plan_ref,
            ),
        }
    )

    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_COMPLETION_CRITERION_PROOF_BINDING_MISMATCH",
    ):
        _transition_goal(
            service,
            created.goal_ref,
            GoalTransitionRequest(
                expected_version=requested.version,
                transition=GoalTransitionKind.verify_completion,
                reason_ref="reason-ref:criterion-provenance:cross-criterion",
                completion_evidence=recomputed,
            ),
            idempotency_ref=("idempotency-ref:criterion-provenance:cross-criterion"),
        )


def test_receipt_producer_rejects_cross_transaction_verifier_binding(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:cross-transaction:create",
    )
    requested = _transition_goal(
        service,
        created.goal_ref,
        GoalTransitionRequest(
            expected_version=created.version,
            transition=GoalTransitionKind.request_completion,
            reason_ref="reason-ref:cross-transaction:request",
        ),
        idempotency_ref="idempotency-ref:cross-transaction:request",
    )
    proof_refs = [
        "proof-ref:cross-transaction:one",
        "proof-ref:cross-transaction:two",
    ]
    bindings = [
        binding.model_copy(update={"goal_ref": "goal-ref:other-transaction"})
        for binding in _criterion_bindings(requested, proof_refs)
    ]
    with pytest.raises(
        ValueError,
        match="RUNTIME_CRITERION_VERIFICATION_GOAL_BINDING_MISMATCH",
    ):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref="run-ref:accepted-local:one",
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.receipt_recorded,
                safe_summary="A different transaction cannot verify this goal.",
                proof_refs=[
                    *proof_refs,
                    *(binding.evaluator_receipt_ref for binding in bindings),
                ],
                receipt_refs=["receipt-ref:cross-transaction"],
                criterion_verifier_bindings=bindings,
                goal_ref=created.goal_ref,
                plan_ref="plan-ref:accepted-local:one",
                idempotency_ref="idempotency-ref:cross-transaction:receipt",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )


def test_goal_mutation_submission_recovery_survives_restart_and_marks_commit(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    submission_ref = "submission-ref:control-center-goal-mutation:restart"
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "a" * 64
    )
    request = _create_request().model_copy(
        update={
            "evidence_refs": [
                "evidence-ref:goal-created",
                submission_evidence_ref,
            ]
        }
    )
    idempotency_ref = "idempotency-ref:control-center-goal-create:restart"

    service.record_goal_mutation_submission(
        submission_ref=submission_ref,
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    pending = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert pending.pending_count == 1
    assert pending.records[0].submission_ref == submission_ref
    assert pending.records[0].request_payload == request.model_dump(mode="json")
    assert pending.records[0].status == "pending"

    created = _create_goal(
        GoalRuntimeService(tmp_path),
        request,
        idempotency_ref=idempotency_ref,
    )
    committed = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert committed.committed_count == 1
    assert committed.records[0].status == "committed"
    assert committed.records[0].committed_goal_ref == created.goal_ref


def test_goal_mutation_submission_rejection_survives_restart_and_blocks_replay(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    submission_ref = "submission-ref:control-center-goal-mutation:rejected"
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "c" * 64
    )
    request = _create_request().model_copy(
        update={"evidence_refs": [submission_evidence_ref]}
    )
    idempotency_ref = "idempotency-ref:control-center-goal-create:rejected"
    prepared = service.record_goal_mutation_submission(
        submission_ref=submission_ref,
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    rejected = service.reject_goal_mutation_submission(
        submission_ref=submission_ref,
        request_fingerprint_ref=prepared.request_fingerprint_ref,
        rejection_reason_ref=(
            "reason-ref:goal-mutation-rejected:goal-store-capacity-exceeded"
        ),
    )
    assert rejected.resolution_status == "rejected"
    restarted = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert restarted.rejected_count == 1
    assert restarted.records[0].status == "rejected"

    recovery = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert recovery.pending_count == 0
    assert recovery.committed_count == 0
    assert recovery.rejected_count == 1
    assert recovery.records[0].status == "rejected"
    assert recovery.records[0].rejection_reason_ref == (
        "reason-ref:goal-mutation-rejected:goal-store-capacity-exceeded"
    )
    assert recovery.records[0].resolved_at is not None

    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_SUBMISSION_PREVIOUSLY_REJECTED",
    ):
        GoalRuntimeService(tmp_path).record_goal_mutation_submission(
            submission_ref=submission_ref,
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref=idempotency_ref,
        )


@pytest.mark.parametrize("terminal_action", ["deny", "revoke"])
def test_terminal_approval_converges_linked_submission_before_ledger_commit(
    tmp_path: Path,
    terminal_action: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "d" * 64
    )
    request = _create_request().model_copy(update={"evidence_refs": [evidence_ref]})
    idempotency_ref = f"idempotency-ref:approval-submission:{terminal_action}"
    service.record_goal_mutation_submission(
        submission_ref=f"submission-ref:approval-submission:{terminal_action}",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    spec = service.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    reason_ref = f"reason-ref:approval-submission:{terminal_action}"
    if terminal_action == "deny":
        terminal = service.decide_goal_mutation_approval(
            approval_request_ref=spec.approval_request_ref,
            decision="deny",
            decision_reason_ref=reason_ref,
        )
        replayed = GoalRuntimeService(tmp_path).decide_goal_mutation_approval(
            approval_request_ref=spec.approval_request_ref,
            decision="deny",
            decision_reason_ref=reason_ref,
        )
    else:
        service.decide_goal_mutation_approval(
            approval_request_ref=spec.approval_request_ref,
            decision="approve",
            decision_reason_ref="reason-ref:approval-submission:approve",
        )
        terminal = service.revoke_goal_mutation_approval(
            approval_ref=spec.approval_ref,
            decision_reason_ref=reason_ref,
        )
        replayed = GoalRuntimeService(tmp_path).revoke_goal_mutation_approval(
            approval_ref=spec.approval_ref,
            decision_reason_ref=reason_ref,
        )
    assert replayed.entry_hash_ref == terminal.entry_hash_ref
    recovery = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    [record] = recovery.records
    assert record.status == "rejected"
    assert record.rejection_reason_ref == reason_ref
    assert record.approval_recovery.posture == (
        "denied" if terminal_action == "deny" else "revoked"
    )
    assert record.approval_recovery.authoritative_current


def test_goal_mutation_submission_exact_replay_rejects_substitution(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    submission_ref = "submission-ref:control-center-goal-mutation:exact-replay"
    request = _create_request().model_copy(
        update={
            "evidence_refs": [
                "evidence-ref:control-center-goal-create-submission:sha256:" + "b" * 64
            ]
        }
    )
    kwargs = {
        "submission_ref": submission_ref,
        "operation": "create",
        "goal_ref": None,
        "request": request,
        "idempotency_ref": "idempotency-ref:control-center-goal-create:exact",
    }
    first = service.record_goal_mutation_submission(**kwargs)
    assert service.record_goal_mutation_submission(**kwargs) == first

    with pytest.raises(
        GoalIdempotencyConflictError,
        match="GOAL_SUBMISSION_IDEMPOTENCY_CONFLICT",
    ):
        service.record_goal_mutation_submission(
            **{
                **kwargs,
                "idempotency_ref": (
                    "idempotency-ref:control-center-goal-create:substituted"
                ),
            }
        )


def test_goal_mutation_submission_commit_requires_full_journal_binding(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "d" * 64
    )
    request = _create_request().model_copy(
        update={"evidence_refs": [submission_evidence_ref]}
    )
    prepared = service.record_goal_mutation_submission(
        submission_ref="submission-ref:control-center-goal-mutation:binding",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:control-center-goal-create:binding",
    )

    _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:control-center-goal-create:other",
    )
    recovery = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert recovery.pending_count == 1
    assert recovery.records[0].status == "pending"

    with pytest.raises(
        GoalIdempotencyConflictError,
        match="GOAL_SUBMISSION_BINDING_CONFLICT",
    ):
        service.record_goal_mutation_submission(
            submission_ref=("submission-ref:control-center-goal-mutation:substituted"),
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref=prepared.idempotency_ref,
        )
    with pytest.raises(
        GoalIdempotencyConflictError,
        match="GOAL_SUBMISSION_BINDING_CONFLICT",
    ):
        service.record_goal_mutation_submission(
            submission_ref=(
                "submission-ref:control-center-goal-mutation:reused-evidence"
            ),
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref=(
                "idempotency-ref:control-center-goal-create:other-binding"
            ),
        )


def test_goal_mutation_submission_recovery_rejects_envelope_substitution(
    tmp_path: Path,
) -> None:
    journal_service = GoalRuntimeService(tmp_path / "journal")
    exact_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "1" * 64
    )
    exact_request = _create_request().model_copy(
        update={"evidence_refs": [exact_evidence_ref]}
    )
    exact_idempotency_ref = "idempotency-ref:control-center-goal-create:journal-binding"
    exact_record = journal_service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:journal-binding",
        operation="create",
        goal_ref=None,
        request=exact_request,
        idempotency_ref=exact_idempotency_ref,
    )
    _create_goal(
        journal_service,
        exact_request,
        idempotency_ref=exact_idempotency_ref,
    )
    create_entry = journal_service.goals._load_consistent_entries()[0]  # noqa: SLF001
    assert (
        create_entry.goal_submission_fingerprint_ref
        == exact_record.request_fingerprint_ref
    )
    exact_recovery = journal_service._submissions.recovery_read_model(  # noqa: SLF001
        [create_entry]
    )
    assert exact_recovery.committed_count == 1

    for label, substituted_request in (
        (
            "request",
            exact_request.model_copy(
                update={"objective": "Substitute the caller-controlled request."}
            ),
        ),
        (
            "evidence",
            exact_request.model_copy(
                update={
                    "evidence_refs": [
                        "evidence-ref:control-center-goal-create-submission:"
                        "sha256:" + "2" * 64
                    ]
                }
            ),
        ),
    ):
        request_store_service = GoalRuntimeService(tmp_path / f"{label}-substitution")
        request_store_service.record_goal_mutation_submission(
            submission_ref=f"submission-ref:goal-mutation:{label}-substitution",
            operation="create",
            goal_ref=None,
            request=substituted_request,
            idempotency_ref=exact_idempotency_ref,
        )
        substituted_recovery = request_store_service._submissions.recovery_read_model(  # noqa: SLF001
            [create_entry]
        )
        assert substituted_recovery.pending_count == 1
        assert substituted_recovery.committed_count == 0

    submission_store_service = GoalRuntimeService(tmp_path / "submission-substitution")
    submission_store_service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:substituted-envelope",
        operation="create",
        goal_ref=None,
        request=exact_request,
        idempotency_ref=exact_idempotency_ref,
    )
    substituted_submission_recovery = (
        submission_store_service._submissions.recovery_read_model(  # noqa: SLF001
            [create_entry]
        )
    )
    assert substituted_submission_recovery.pending_count == 1
    assert substituted_submission_recovery.committed_count == 0

    edit_evidence_ref = (
        "evidence-ref:control-center-goal-update-submission:edit:sha256:" + "3" * 64
    )
    operation_store_service = GoalRuntimeService(tmp_path / "operation-substitution")
    operation_store_service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:operation-substitution",
        operation="edit",
        goal_ref=create_entry.goal_ref,
        request=GoalEditRequest(
            expected_version=1,
            text_redaction_posture="operator_authored_redacted_summary_only",
            objective="Substitute the operation envelope.",
            evidence_refs=[edit_evidence_ref],
        ),
        idempotency_ref=exact_idempotency_ref,
    )
    substituted_operation_recovery = (
        operation_store_service._submissions.recovery_read_model(  # noqa: SLF001
            [create_entry]
        )
    )
    assert substituted_operation_recovery.pending_count == 1
    assert substituted_operation_recovery.committed_count == 0

    unrelated_store_service = GoalRuntimeService(tmp_path / "unrelated-idempotency")
    unrelated_store_service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:unrelated-idempotency",
        operation="create",
        goal_ref=None,
        request=exact_request,
        idempotency_ref="idempotency-ref:goal-create:unrelated",
    )
    unrelated = unrelated_store_service._submissions.recovery_read_model(  # noqa: SLF001
        [create_entry]
    )
    assert unrelated.pending_count == 1
    assert unrelated.committed_count == 0

    edit_request = GoalEditRequest(
        expected_version=1,
        text_redaction_posture="operator_authored_redacted_summary_only",
        objective="Record the exact durable edit.",
        evidence_refs=[edit_evidence_ref],
    )
    edit_idempotency_ref = "idempotency-ref:goal-edit:journal-binding"
    journal_service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:edit-journal-binding",
        operation="edit",
        goal_ref=create_entry.goal_ref,
        request=edit_request,
        idempotency_ref=edit_idempotency_ref,
    )
    _edit_goal(
        journal_service,
        create_entry.goal_ref,
        edit_request,
        idempotency_ref=edit_idempotency_ref,
    )
    edit_entry = journal_service.goals._load_consistent_entries()[-1]  # noqa: SLF001
    goal_store_service = GoalRuntimeService(tmp_path / "goal-substitution")
    goal_store_service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:goal-substitution",
        operation="edit",
        goal_ref="goal-ref:sha256:" + "4" * 64,
        request=edit_request,
        idempotency_ref=edit_idempotency_ref,
    )
    substituted_goal_recovery = goal_store_service._submissions.recovery_read_model(  # noqa: SLF001
        [edit_entry]
    )
    assert substituted_goal_recovery.pending_count == 1
    assert substituted_goal_recovery.committed_count == 0


def test_goal_mutation_submission_rejects_journal_idempotency_collision_before_write(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    original_request = _create_request()
    idempotency_ref = "idempotency-ref:goal-submission:journal-collision"
    _create_goal(
        service,
        original_request,
        idempotency_ref=idempotency_ref,
    )
    anchored_state = service._submissions.path.read_bytes()  # noqa: SLF001
    colliding_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "7" * 64
    )
    colliding_request = original_request.model_copy(
        update={
            "objective": "A different bounded create must not reuse the journal key.",
            "evidence_refs": [colliding_evidence_ref],
        }
    )

    with pytest.raises(
        GoalIdempotencyConflictError,
        match="GOAL_IDEMPOTENCY_CONFLICT",
    ):
        service.record_goal_mutation_submission(
            submission_ref="submission-ref:goal-submission:journal-collision",
            operation="create",
            goal_ref=None,
            request=colliding_request,
            idempotency_ref=idempotency_ref,
        )

    assert service._submissions.path.read_bytes() == anchored_state  # noqa: SLF001
    recovery = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert recovery.records == []


def test_reserved_submission_evidence_requires_exact_durable_record(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request().model_copy(
        update={
            "evidence_refs": [
                "evidence-ref:control-center-goal-create-submission:sha256:" + "8" * 64
            ]
        }
    )

    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_SUBMISSION_RECORD_REQUIRED",
    ):
        _create_goal(
            service,
            request,
            idempotency_ref="idempotency-ref:reserved-evidence:missing",
        )

    assert service.goals._load_consistent_entries() == []  # noqa: SLF001


def test_goal_mutation_submission_admission_reserves_terminal_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "e" * 64
    )
    request = _create_request().model_copy(
        update={"evidence_refs": [submission_evidence_ref]}
    )
    kwargs = {
        "submission_ref": "submission-ref:control-center-goal-mutation:bytes",
        "operation": "create",
        "goal_ref": None,
        "request": request,
        "idempotency_ref": "idempotency-ref:control-center-goal-create:bytes",
    }
    record = service.record_goal_mutation_submission(**kwargs)
    store = service._submissions  # noqa: SLF001
    exact_terminal_bytes = len(
        store._state_content(  # noqa: SLF001
            store._worst_case_terminal_records([record])  # noqa: SLF001
        ).encode("utf-8")
    )
    store.path.unlink()
    store.head_path.unlink()  # noqa: SLF001
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_GOAL_MUTATION_SUBMISSION_STATE_BYTES",
        exact_terminal_bytes - 1,
    )
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_SUBMISSION_STATE_CAPACITY_EXCEEDED",
    ):
        service.record_goal_mutation_submission(**kwargs)

    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_GOAL_MUTATION_SUBMISSION_STATE_BYTES",
        exact_terminal_bytes,
    )
    accepted = service.record_goal_mutation_submission(**kwargs)
    rejected = service.reject_goal_mutation_submission(
        submission_ref=accepted.submission_ref,
        request_fingerprint_ref=accepted.request_fingerprint_ref,
        rejection_reason_ref=goal_runtime_module._maximum_typed_ref(  # noqa: SLF001
            "reason-ref:goal-mutation-rejected",
            0,
        ),
    )
    assert rejected.resolution_status == "rejected"


def test_submission_rejection_head_blocks_state_rollback(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "d" * 64
    )
    request = _create_request().model_copy(
        update={"evidence_refs": [submission_evidence_ref]}
    )
    record = service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-rejection-rollback",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:goal-rejection-rollback",
    )
    pending_state = service._submissions.path.read_text(encoding="utf-8")  # noqa: SLF001
    service.reject_goal_mutation_submission(
        submission_ref=record.submission_ref,
        request_fingerprint_ref=record.request_fingerprint_ref,
        rejection_reason_ref="reason-ref:goal-rejection-rollback",
    )

    service._submissions.path.write_text(pending_state, encoding="utf-8")  # noqa: SLF001
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_SUBMISSION_HEAD_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).aggregate_read_snapshot(
            run_ref=None,
            after_sequence=0,
            limit=10,
        )


@pytest.mark.parametrize("failure_boundary", ["state", "head", "cleanup"])
def test_submission_rejection_recovers_only_from_exact_write_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_boundary: str,
) -> None:
    service = GoalRuntimeService(tmp_path)
    evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "f" * 64
    )
    request = _create_request().model_copy(update={"evidence_refs": [evidence_ref]})
    record = service.record_goal_mutation_submission(
        submission_ref=f"submission-ref:goal-rejection-crash:{failure_boundary}",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=f"idempotency-ref:goal-rejection-crash:{failure_boundary}",
    )
    original_atomic_write = goal_runtime_module._atomic_write
    original_cleanup = service._submissions._delete_write_intent  # noqa: SLF001
    failed = False

    def fail_head_once(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goal_mutation_submissions_head.json":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    def fail_state_once(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goal_mutation_submissions.json":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    def fail_cleanup_once() -> None:
        nonlocal failed
        if not failed:
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_cleanup()

    if failure_boundary == "state":
        monkeypatch.setattr(goal_runtime_module, "_atomic_write", fail_state_once)
    elif failure_boundary == "head":
        monkeypatch.setattr(goal_runtime_module, "_atomic_write", fail_head_once)
    else:
        monkeypatch.setattr(
            service._submissions,  # noqa: SLF001
            "_delete_write_intent",
            fail_cleanup_once,
        )
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        service.reject_goal_mutation_submission(
            submission_ref=record.submission_ref,
            request_fingerprint_ref=record.request_fingerprint_ref,
            rejection_reason_ref="reason-ref:goal-rejection-crash",
        )
    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)
    monkeypatch.setattr(
        service._submissions,  # noqa: SLF001
        "_delete_write_intent",
        original_cleanup,
    )

    recovered = GoalRuntimeService(tmp_path).reject_goal_mutation_submission(
        submission_ref=record.submission_ref,
        request_fingerprint_ref=record.request_fingerprint_ref,
        rejection_reason_ref="reason-ref:goal-rejection-crash",
    )

    assert recovered.resolution_status == "rejected"
    assert not service._submissions.write_intent_path.exists()  # noqa: SLF001


def test_submission_state_loss_with_head_fails_closed(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "a" * 64
    )
    service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-state-loss",
        operation="create",
        goal_ref=None,
        request=_create_request().model_copy(
            update={"evidence_refs": [evidence_ref]}
        ),
        idempotency_ref="idempotency-ref:goal-state-loss",
    )
    service._submissions.path.unlink()  # noqa: SLF001

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_SUBMISSION_STATE_MISSING_WITH_HEAD",
    ):
        GoalRuntimeService(tmp_path).aggregate_read_snapshot(
            run_ref=None,
            after_sequence=0,
            limit=10,
        )


def test_aggregate_read_repairs_exact_submission_write_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "d" * 64
    )
    record = service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-aggregate-write-repair",
        operation="create",
        goal_ref=None,
        request=_create_request().model_copy(
            update={"evidence_refs": [evidence_ref]}
        ),
        idempotency_ref="idempotency-ref:goal-aggregate-write-repair",
    )
    original_atomic_write = goal_runtime_module._atomic_write  # noqa: SLF001
    failed = False

    def fail_head_once(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goal_mutation_submissions_head.json":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    monkeypatch.setattr(goal_runtime_module, "_atomic_write", fail_head_once)
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        service.reject_goal_mutation_submission(
            submission_ref=record.submission_ref,
            request_fingerprint_ref=record.request_fingerprint_ref,
            rejection_reason_ref="reason-ref:goal-aggregate-write-repair",
        )
    monkeypatch.setattr(goal_runtime_module, "_atomic_write", original_atomic_write)

    recovery = GoalRuntimeService(tmp_path).aggregate_read_snapshot(
        run_ref=None,
        after_sequence=0,
        limit=10,
    )[4]

    assert recovery.pending_count == 0
    assert recovery.rejected_count == 1
    assert recovery.records[0].submission_ref == record.submission_ref
    assert not service._submissions.write_intent_path.exists()  # noqa: SLF001


@pytest.mark.parametrize("approved_before_expiry", [False, True])
def test_expired_approval_durably_rejects_linked_submission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    approved_before_expiry: bool,
) -> None:
    service = GoalRuntimeService(tmp_path)
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "e" * 64
    )
    request = _create_request().model_copy(
        update={"evidence_refs": [submission_evidence_ref]}
    )
    submission = service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-approval-expiration",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:goal-approval-expiration",
    )
    spec = service.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=submission.idempotency_ref,
        ttl_minutes=5,
    )
    if approved_before_expiry:
        service.decide_goal_mutation_approval(
            approval_request_ref=spec.approval_request_ref,
            decision="approve",
            decision_reason_ref="reason-ref:goal-approval-before-expiration",
        )
    monkeypatch.setattr(
        goal_runtime_module,
        "utc_now",
        lambda: spec.expires_at + timedelta(seconds=1),
    )

    recovery = service.aggregate_read_snapshot(
        run_ref=None,
        after_sequence=0,
        limit=10,
    )[4]

    assert recovery.pending_count == 0
    assert recovery.rejected_count == 1
    assert recovery.records[0].approval_recovery.posture == "expired"
    assert recovery.records[0].rejection_reason_ref == (
        "reason-ref:goal-mutation-rejected:approval-expired"
    )
    assert service._approvals._load_consistent_entries()[-1].status == "expired"  # noqa: SLF001


def test_durable_refs_reject_the_canonical_secret_detector(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        goal_runtime_module,
        "contains_obvious_secret",
        lambda value: value == "evidence-ref:synthetic-sensitive",
    )
    with pytest.raises(ValueError, match="credential-like material"):
        GoalCreateRequest(
            **{
                **_create_request().model_dump(mode="python"),
                "evidence_refs": ["evidence-ref:synthetic-sensitive"],
            }
        )


def test_goal_mutation_submission_state_rejects_symlink_substitution(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "goal_mutation_submissions.json").symlink_to(outside)

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_SUBMISSION_STATE_CORRUPT",
    ):
        build_runtime_run_events_read_model(service=GoalRuntimeService(state_dir))


def test_goal_runtime_rejects_symlinked_state_root_ancestor(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    aliased_parent = tmp_path / "configured"
    aliased_parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        GoalRuntimeService(aliased_parent / "goal-runtime")
    assert list(outside.iterdir()) == []


def test_goal_runtime_pinned_state_root_rejects_ancestor_substitution(
    tmp_path: Path,
) -> None:
    configured_parent = tmp_path / "configured"
    configured_parent.mkdir()
    state_dir = configured_parent / "goal-runtime"
    service = GoalRuntimeService(state_dir)
    goal = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:state-root-pin-create",
    )
    original_parent = tmp_path / "configured-original"
    configured_parent.rename(original_parent)
    outside = tmp_path / "outside"
    outside.mkdir()
    configured_parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        service.goal_with_provenance(goal.goal_ref)
    assert list(outside.iterdir()) == []


def test_goal_runtime_lock_uses_pinned_root_across_path_exchange(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_dir = tmp_path / "goal-runtime"
    preserved_dir = tmp_path / "goal-runtime-preserved"
    substituted_dir = tmp_path / "goal-runtime-substituted"
    substituted_dir.mkdir()
    service = GoalRuntimeService(state_dir)
    created = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-root-lock-pin:create",
    )
    (state_dir / ".locks" / "goal-journal.lock").unlink()
    manager = service.goals._locks  # noqa: SLF001
    original_acquire = manager.acquire_from_parent
    exchanged = False

    @contextmanager
    def exchange_during_lock_admission(
        parent_descriptor: int,
        lock_dir_name: str,
        writer_key: str,
    ):
        nonlocal exchanged
        if exchanged:
            with original_acquire(
                parent_descriptor,
                lock_dir_name,
                writer_key,
            ) as lease_ref:
                yield lease_ref
            return
        state_dir.rename(preserved_dir)
        substituted_dir.rename(state_dir)
        exchanged = True
        try:
            with original_acquire(
                parent_descriptor,
                lock_dir_name,
                writer_key,
            ) as lease_ref:
                state_dir.rename(substituted_dir)
                preserved_dir.rename(state_dir)
                yield lease_ref
        finally:
            if preserved_dir.exists():
                if state_dir.exists():
                    state_dir.rename(substituted_dir)
                preserved_dir.rename(state_dir)

    monkeypatch.setattr(
        manager,
        "acquire_from_parent",
        exchange_during_lock_admission,
    )
    updated = _edit_goal(
        service,
        created.goal_ref,
        GoalEditRequest(
            expected_version=created.version,
            text_redaction_posture="operator_authored_redacted_summary_only",
            objective="Use the descriptor-pinned journal lock.",
        ),
        idempotency_ref="idempotency-ref:goal-root-lock-pin:edit",
    )

    assert exchanged is True
    assert updated.version == created.version + 1
    assert (state_dir / ".locks" / "goal-journal.lock").is_file()
    assert not (
        substituted_dir / ".locks" / "goal-journal.lock"
    ).exists()


def test_exact_submission_retry_repairs_bound_genesis_intent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    submission_evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "9" * 64
    )
    request = _create_request().model_copy(
        update={"evidence_refs": [submission_evidence_ref]}
    )
    kwargs = {
        "submission_ref": "submission-ref:goal-mutation:genesis-retry",
        "operation": "create",
        "goal_ref": None,
        "request": request,
        "idempotency_ref": "idempotency-ref:goal-mutation:genesis-retry",
    }
    prepared = service.record_goal_mutation_submission(**kwargs)
    original_atomic_write = goal_runtime_module._atomic_write
    failed = False

    def fail_journal_install_once(path: Path, content: str) -> None:
        nonlocal failed
        if not failed and path.name == "goals.jsonl":
            failed = True
            raise GoalRuntimeError("GOAL_RUNTIME_STORAGE_UNAVAILABLE")
        original_atomic_write(path, content)

    monkeypatch.setattr(
        goal_runtime_module,
        "_atomic_write",
        fail_journal_install_once,
    )
    with pytest.raises(GoalRuntimeError, match="GOAL_RUNTIME_STORAGE_UNAVAILABLE"):
        _create_goal(
            service,
            request,
            idempotency_ref=kwargs["idempotency_ref"],
        )
    assert (tmp_path / "goal_journal_genesis_intent.json").is_file()
    assert not (tmp_path / "goals.jsonl").exists()

    monkeypatch.setattr(
        goal_runtime_module,
        "_atomic_write",
        original_atomic_write,
    )
    assert (
        GoalRuntimeService(tmp_path).record_goal_mutation_submission(**kwargs)
        == prepared
    )
    recovery = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert recovery.committed_count == 1
    assert (tmp_path / "goals.jsonl").is_file()
    assert (tmp_path / "goal_journal_head.json").is_file()
    assert not (tmp_path / "goal_journal_genesis_intent.json").exists()


def test_submission_rejection_prefers_an_exact_committed_journal_entry(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "a" * 64
    )
    request = _create_request().model_copy(update={"evidence_refs": [evidence_ref]})
    idempotency_ref = "idempotency-ref:goal-mutation:commit-wins"
    prepared = service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:commit-wins",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    _create_goal(service, request, idempotency_ref=idempotency_ref)

    unchanged = service.reject_goal_mutation_submission(
        submission_ref=prepared.submission_ref,
        request_fingerprint_ref=prepared.request_fingerprint_ref,
        rejection_reason_ref="reason-ref:goal-mutation-rejected:stale-failure",
    )
    assert unchanged.resolution_status == "pending"
    recovery = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert recovery.committed_count == 1
    assert recovery.rejected_count == 0


def test_concurrent_stale_rejection_waits_for_exact_journal_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "f" * 64
    )
    request = _create_request().model_copy(update={"evidence_refs": [evidence_ref]})
    idempotency_ref = "idempotency-ref:goal-mutation:concurrent-commit"
    prepared = service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:concurrent-commit",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    stale_rejection_ready = threading.Event()
    admit_stale_rejection = threading.Event()
    rejection_attempting_lock = threading.Event()
    mutation_holds_journal = threading.Event()
    original_write_entries = service.goals._write_entries  # noqa: SLF001
    results: dict[str, object] = {}
    errors: list[BaseException] = []

    def paused_write(entries: list[goal_runtime_module.GoalJournalEntry]) -> None:
        mutation_holds_journal.set()
        admit_stale_rejection.set()
        assert rejection_attempting_lock.wait(timeout=5)
        original_write_entries(entries)

    monkeypatch.setattr(service.goals, "_write_entries", paused_write)

    def commit_exact_mutation() -> None:
        try:
            results["goal"] = _create_goal(
                service,
                request,
                idempotency_ref=idempotency_ref,
            )
        except BaseException as exc:  # pragma: no cover - asserted below
            errors.append(exc)

    def reject_stale_failure() -> None:
        try:
            stale_rejection_ready.set()
            assert admit_stale_rejection.wait(timeout=5)
            rejection_attempting_lock.set()
            results["rejection"] = service.reject_goal_mutation_submission(
                submission_ref=prepared.submission_ref,
                request_fingerprint_ref=prepared.request_fingerprint_ref,
                rejection_reason_ref=(
                    "reason-ref:goal-mutation-rejected:stale-concurrent-failure"
                ),
            )
        except BaseException as exc:  # pragma: no cover - asserted below
            errors.append(exc)

    rejection_thread = threading.Thread(target=reject_stale_failure)
    rejection_thread.start()
    assert stale_rejection_ready.wait(timeout=5)
    mutation_thread = threading.Thread(target=commit_exact_mutation)
    mutation_thread.start()
    assert mutation_holds_journal.wait(timeout=5)
    mutation_thread.join(timeout=5)
    rejection_thread.join(timeout=5)

    assert not mutation_thread.is_alive()
    assert not rejection_thread.is_alive()
    assert errors == []
    assert isinstance(results["goal"], PersistentGoal)
    assert results["rejection"].resolution_status == "pending"
    recovery = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path)
    ).goal_mutation_submissions
    assert recovery.committed_count == 1
    assert recovery.rejected_count == 0


def test_concurrent_exact_rejection_blocks_and_prevents_goal_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GoalRuntimeService(tmp_path)
    evidence_ref = (
        "evidence-ref:control-center-goal-create-submission:sha256:" + "e" * 64
    )
    request = _create_request().model_copy(update={"evidence_refs": [evidence_ref]})
    idempotency_ref = "idempotency-ref:goal-mutation:concurrent-rejection"
    prepared = service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:concurrent-rejection",
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref=idempotency_ref,
    )
    rejection_holds_submission = threading.Event()
    release_rejection = threading.Event()
    original_write = service._submissions._write  # noqa: SLF001
    results: dict[str, object] = {}
    errors: dict[str, BaseException] = {}

    def paused_write(*args: object, **kwargs: object) -> None:
        rejection_holds_submission.set()
        assert release_rejection.wait(timeout=5)
        original_write(*args, **kwargs)

    monkeypatch.setattr(service._submissions, "_write", paused_write)  # noqa: SLF001

    def reject_exact_submission() -> None:
        try:
            results["rejection"] = service.reject_goal_mutation_submission(
                submission_ref=prepared.submission_ref,
                request_fingerprint_ref=prepared.request_fingerprint_ref,
                rejection_reason_ref=(
                    "reason-ref:goal-mutation-rejected:exact-concurrent-failure"
                ),
            )
        except BaseException as exc:  # pragma: no cover - asserted below
            errors["rejection"] = exc

    def commit_exact_mutation() -> None:
        try:
            results["goal"] = _create_goal(
                service,
                request,
                idempotency_ref=idempotency_ref,
            )
        except BaseException as exc:  # pragma: no cover - asserted below
            errors["mutation"] = exc

    rejection_thread = threading.Thread(target=reject_exact_submission)
    rejection_thread.start()
    assert rejection_holds_submission.wait(timeout=5)
    mutation_thread = threading.Thread(target=commit_exact_mutation)
    mutation_thread.start()
    assert mutation_thread.is_alive()
    release_rejection.set()
    rejection_thread.join(timeout=5)
    mutation_thread.join(timeout=5)

    assert not rejection_thread.is_alive()
    assert not mutation_thread.is_alive()
    assert "rejection" not in errors
    assert results["rejection"].resolution_status == "rejected"
    assert isinstance(errors["mutation"], GoalRuntimeError)
    assert "GOAL_SUBMISSION_PREVIOUSLY_REJECTED" in str(errors["mutation"])
    restarted = GoalRuntimeService(tmp_path)
    recovery = build_runtime_run_events_read_model(
        service=restarted
    ).goal_mutation_submissions
    assert recovery.rejected_count == 1
    assert recovery.committed_count == 0
    assert restarted.goals.read_model().goals == []


def test_approval_admission_reserves_exact_revocation_count_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_GOAL_MUTATION_APPROVAL_ENTRIES",
        2,
    )
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_MUTATION_APPROVAL_LEDGER_CAPACITY_EXCEEDED",
    ):
        service.prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref="idempotency-ref:approval-reserve-count",
        )
    assert not service._approvals.path.exists()  # noqa: SLF001


def test_goal_reads_fail_closed_when_approval_ledger_is_missing(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    goal = _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:goal-read-missing-approval-ledger",
    )
    service._approvals.path.unlink()  # noqa: SLF001
    restarted = GoalRuntimeService(tmp_path)

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_LEDGER_MISSING_WITH_HEAD",
    ):
        restarted.goal_lifecycle_read_model()
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_LEDGER_MISSING_WITH_HEAD",
    ):
        restarted.goal_with_provenance(goal.goal_ref)
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_LEDGER_MISSING_WITH_HEAD",
    ):
        restarted.aggregate_read_snapshot(
            run_ref="run-ref:accepted-local:one",
            after_sequence=0,
            limit=10,
        )


def test_public_event_producer_class_survives_recomputed_wrapper_tampering(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:public-producer-strip",
        run_type=AcceptedLocalRunType.local_metadata_action,
        event_kind=DurableRunEventKind.evidence_linked,
        safe_summary="Operator metadata retained one bounded evidence link.",
        proof_refs=["proof-ref:public-producer-strip"],
        idempotency_ref="idempotency-ref:public-producer-strip",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    event = _append_event(service, request)
    assert event.producer_class == "operator_public_metadata"
    tombstones = service._events._load_idempotency_tombstones([event])  # noqa: SLF001
    tombstone = tombstones[(event.run_ref, event.idempotency_ref)]

    stripped_draft = event.model_copy(
        update={
            "goal_mutation_approval_ref": None,
            "goal_mutation_approval_decision_ref": None,
            "goal_mutation_approval_ledger_entry_hash_ref": None,
            "event_hash_ref": "event-hash-ref:pending",
        }
    )
    stripped = stripped_draft.model_copy(
        update={"event_hash_ref": service._events._event_hash(stripped_draft)}  # noqa: SLF001
    )
    recomputed_tombstone = tombstone.model_copy(
        update={
            "event": stripped,
            "tombstone_hash_ref": "tombstone-hash-ref:pending",
        }
    )
    recomputed_tombstone = recomputed_tombstone.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                recomputed_tombstone
            )
        }
    )
    service._events._write_events([stripped])  # noqa: SLF001
    service._events._write_idempotency_tombstones(  # noqa: SLF001
        [recomputed_tombstone]
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_STORE_CORRUPT",
    ):
        GoalRuntimeService(tmp_path).events.replay(event.run_ref)


def test_public_event_cannot_be_reclassified_as_trusted_core(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:public-producer-substitution",
        run_type=AcceptedLocalRunType.local_metadata_action,
        event_kind=DurableRunEventKind.evidence_linked,
        safe_summary="Operator metadata retained one bounded evidence link.",
        proof_refs=["proof-ref:public-producer-substitution"],
        idempotency_ref="idempotency-ref:public-producer-substitution",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    event = _append_event(service, request)
    tombstone = service._events._load_idempotency_tombstones([event])[  # noqa: SLF001
        (event.run_ref, event.idempotency_ref)
    ]
    substituted_draft = event.model_copy(
        update={
            "producer_class": "trusted_core",
            "goal_mutation_approval_ref": None,
            "goal_mutation_approval_decision_ref": None,
            "goal_mutation_approval_ledger_entry_hash_ref": None,
            "trusted_source_record_hash_ref": (
                "record-hash-ref:trusted-run-event-source:sha256:" + "f" * 64
            ),
            "event_hash_ref": "event-hash-ref:pending",
        }
    )
    substituted = substituted_draft.model_copy(
        update={
            "event_hash_ref": service._events._event_hash(  # noqa: SLF001
                substituted_draft
            )
        }
    )
    recomputed_tombstone = tombstone.model_copy(
        update={
            "event": substituted,
            "tombstone_hash_ref": "tombstone-hash-ref:pending",
        }
    )
    recomputed_tombstone = recomputed_tombstone.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                recomputed_tombstone
            )
        }
    )
    service._events._write_events([substituted])  # noqa: SLF001
    service._events._write_idempotency_tombstones(  # noqa: SLF001
        [recomputed_tombstone]
    )

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="RUN_EVENT_GENERATION_HEAD_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).events.replay(event.run_ref)


def test_public_event_read_fails_when_exact_approval_ledger_is_missing(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:public-producer-missing-ledger",
        run_type=AcceptedLocalRunType.local_metadata_action,
        event_kind=DurableRunEventKind.evidence_linked,
        safe_summary="Operator metadata retained one bounded evidence link.",
        proof_refs=["proof-ref:public-producer-missing-ledger"],
        idempotency_ref="idempotency-ref:public-producer-missing-ledger",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    event = _append_event(service, request)
    service._approvals.path.unlink()  # noqa: SLF001

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_LEDGER_MISSING_WITH_HEAD",
    ):
        GoalRuntimeService(tmp_path).events.replay(event.run_ref)


def test_trusted_and_legacy_event_epochs_remain_readable_without_approval_ledger(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = DurableRunEventAppendRequest(
        run_ref="run-ref:trusted-producer-legacy",
        run_type=AcceptedLocalRunType.local_read_task,
        event_kind=DurableRunEventKind.run_started,
        safe_summary="Trusted Core retained one bounded run start.",
        idempotency_ref="idempotency-ref:trusted-producer-legacy",
        authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
    )
    event = service._events.append(request)  # noqa: SLF001
    assert event.producer_class == "trusted_core"
    assert service.events.replay(event.run_ref).events == [event]

    tombstone = service._events._load_idempotency_tombstones([event])[  # noqa: SLF001
        (event.run_ref, event.idempotency_ref)
    ]
    legacy_draft = event.model_copy(
        update={
            "schema_version": "durable_run_event.v1",
            "producer_class": None,
            "event_hash_ref": "event-hash-ref:pending",
        }
    )
    legacy = legacy_draft.model_copy(
        update={"event_hash_ref": service._events._event_hash(legacy_draft)}  # noqa: SLF001
    )
    legacy_tombstone = tombstone.model_copy(
        update={"event": legacy, "tombstone_hash_ref": "tombstone-hash-ref:pending"}
    )
    legacy_tombstone = legacy_tombstone.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                legacy_tombstone
            )
        }
    )
    service._events._write_events([legacy])  # noqa: SLF001
    service._events._write_idempotency_tombstones([legacy_tombstone])  # noqa: SLF001
    service._events.trusted_sources_path.unlink()  # noqa: SLF001
    service._events._write_run_event_generation_head(  # noqa: SLF001
        service._events._build_run_event_generation_head(  # noqa: SLF001
            [legacy],
            [legacy_tombstone],
            [],
        )
    )

    replayed = GoalRuntimeService(tmp_path).events.replay(event.run_ref).events
    assert replayed[0].schema_version == "durable_run_event.v1"
    assert replayed[0].producer_class is None


@pytest.mark.parametrize(
    ("schema_version", "producer_class"),
    [
        ("durable_run_event.v1", None),
        ("durable_run_event.v2", "trusted_core"),
    ],
)
def test_legacy_receipt_events_never_grant_completion_authority(
    tmp_path: Path,
    schema_version: str,
    producer_class: str | None,
) -> None:
    service = GoalRuntimeService(tmp_path)
    run_ref = "run-ref:legacy-completion-authority"
    goal_ref = "goal-ref:legacy-completion-authority"
    receipt_ref = "receipt-ref:legacy-completion-authority"
    proof_ref = "proof-ref:legacy-completion-authority"
    event = _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="A legacy receipt remains readable but non-authoritative.",
            proof_refs=[proof_ref],
            receipt_refs=[receipt_ref],
            goal_ref=goal_ref,
            idempotency_ref="idempotency-ref:legacy-completion-authority",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    tombstone = service._events._load_idempotency_tombstones([event])[  # noqa: SLF001
        (event.run_ref, event.idempotency_ref)
    ]
    legacy_draft = event.model_copy(
        update={
            "schema_version": schema_version,
            "producer_class": producer_class,
            "trusted_source_record_hash_ref": None,
            "event_hash_ref": "event-hash-ref:pending",
        }
    )
    legacy = legacy_draft.model_copy(
        update={"event_hash_ref": service._events._event_hash(legacy_draft)}  # noqa: SLF001
    )
    legacy_tombstone = tombstone.model_copy(
        update={"event": legacy, "tombstone_hash_ref": "tombstone-hash-ref:pending"}
    )
    legacy_tombstone = legacy_tombstone.model_copy(
        update={
            "tombstone_hash_ref": service._events._tombstone_hash(  # noqa: SLF001
                legacy_tombstone
            )
        }
    )
    service._events._write_events([legacy])  # noqa: SLF001
    service._events._write_idempotency_tombstones([legacy_tombstone])  # noqa: SLF001
    service._events.trusted_sources_path.unlink()  # noqa: SLF001
    service._events._write_run_event_generation_head(  # noqa: SLF001
        service._events._build_run_event_generation_head(  # noqa: SLF001
            [legacy],
            [legacy_tombstone],
            [],
        )
    )

    restarted = GoalRuntimeService(tmp_path)
    assert restarted.events.replay(run_ref).events == [legacy]
    assert (
        restarted.events.has_completion_evidence(
            run_ref=run_ref,
            receipt_ref=receipt_ref,
            proof_ref=proof_ref,
            goal_ref=goal_ref,
        )
        is False
    )


def test_goal_read_rejects_same_idempotency_cross_request_approval_substitution(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    idempotency_ref = "idempotency-ref:goal-read-cross-request-substitution"
    original = _create_request()
    original_approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=original,
        idempotency_ref=idempotency_ref,
    )
    service.create_goal(
        original,
        idempotency_ref=idempotency_ref,
        approval_ref=original_approval_ref,
    )
    substituted_request = original.model_copy(
        update={"objective": "A different bounded approval request."}
    )
    substituted_approval_ref = _approved_mutation_ref(
        service,
        operation="create",
        goal_ref=None,
        request=substituted_request,
        idempotency_ref=idempotency_ref,
    )
    approval_entries = service._approvals._load_entries()  # noqa: SLF001
    substituted_approval = next(
        entry
        for entry in reversed(approval_entries)
        if entry.status == "approved"
        and entry.spec.approval_ref == substituted_approval_ref
    )
    substituted_binding = service._approvals._binding_from_approved_entry(  # noqa: SLF001
        substituted_approval
    )
    [journal_entry] = service.goals._load_consistent_entries()  # noqa: SLF001
    tampered_draft = journal_entry.model_copy(
        update={
            "approval_ref": substituted_binding.approval_ref,
            "approval_decision_ref": substituted_binding.approval_decision_ref,
            "approval_ledger_entry_hash_ref": (
                substituted_binding.approval_ledger_entry_hash_ref
            ),
            "approval_request_fingerprint_ref": (
                substituted_binding.request_fingerprint_ref
            ),
            "approval_exact_scope_ref": substituted_binding.exact_scope_ref,
            "entry_hash_ref": "entry-hash-ref:pending",
        }
    )
    tampered = tampered_draft.model_copy(
        update={"entry_hash_ref": service.goals._entry_hash(tampered_draft)}  # noqa: SLF001
    )
    _replace_goal_journal_for_tamper(service, [tampered])

    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_MUTATION_APPROVAL_PROVENANCE_MISMATCH",
    ):
        GoalRuntimeService(tmp_path).goal_lifecycle_read_model()


def test_approval_admission_reserves_encoded_revocation_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    probe = GoalRuntimeService(tmp_path / "probe")
    request = _create_request().model_copy(
        update={"objective": "é" * goal_runtime_module.MAX_GOAL_TEXT}
    )
    probe_spec = probe.prepare_goal_mutation_approval(
        operation="create",
        goal_ref=None,
        request=request,
        idempotency_ref="idempotency-ref:approval-reserve-bytes",
    )
    probe.decide_goal_mutation_approval(
        approval_request_ref=probe_spec.approval_request_ref,
        decision="approve",
        decision_reason_ref="reason-ref:approval-reserve-bytes",
    )
    approved_entries = probe._approvals._load_entries()  # noqa: SLF001
    approved_bytes = len(
        probe._approvals._ledger_content(approved_entries).encode("utf-8")  # noqa: SLF001
    )
    projected = [
        *approved_entries,
        probe._approvals._maximum_revocation_entry(  # noqa: SLF001
            approved_entries[-1],
            previous_entry_hash_ref=approved_entries[-1].entry_hash_ref,
            index=0,
        ),
    ]
    projected_bytes = len(
        probe._approvals._ledger_content(projected).encode("utf-8")  # noqa: SLF001
    )
    assert projected_bytes > approved_bytes

    service = GoalRuntimeService(tmp_path / "subject")
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_GOAL_MUTATION_APPROVAL_LEDGER_BYTES",
        approved_bytes,
    )
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_MUTATION_APPROVAL_LEDGER_CAPACITY_EXCEEDED",
    ):
        service.prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref="idempotency-ref:approval-reserve-bytes",
        )
    assert not service._approvals.path.exists()  # noqa: SLF001


def test_multiple_approved_requests_retain_independent_revocation_slots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_GOAL_MUTATION_APPROVAL_ENTRIES",
        6,
    )
    service = GoalRuntimeService(tmp_path)
    approvals: list[str] = []
    for index in range(2):
        request = _create_request().model_copy(
            update={"objective": f"Bounded approval request {index}."}
        )
        spec = service.prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref=f"idempotency-ref:approval-reserve-multiple:{index}",
        )
        service.decide_goal_mutation_approval(
            approval_request_ref=spec.approval_request_ref,
            decision="approve",
            decision_reason_ref=f"reason-ref:approval-reserve-multiple:{index}",
        )
        approvals.append(spec.approval_ref)

    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_MUTATION_APPROVAL_LEDGER_CAPACITY_EXCEEDED",
    ):
        service.prepare_goal_mutation_approval(
            operation="create",
            goal_ref=None,
            request=_create_request().model_copy(
                update={"objective": "A third request must not consume rollback."}
            ),
            idempotency_ref="idempotency-ref:approval-reserve-multiple:third",
        )
    for index, approval_ref in enumerate(approvals):
        revoked = service.revoke_goal_mutation_approval(
            approval_ref=approval_ref,
            decision_reason_ref=f"reason-ref:approval-reserve-multiple:revoke:{index}",
        )
        assert revoked.status == "revoked"
    assert len(service._approvals._load_entries()) == 6  # noqa: SLF001


def test_compacted_rejection_identity_remains_terminal_after_restart(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    first_kwargs: dict[str, object] | None = None
    for index in range(65):
        suffix = f"{index:064x}"
        kwargs: dict[str, object] = {
            "submission_ref": f"submission-ref:goal-mutation:rejected:{index}",
            "operation": "create",
            "goal_ref": None,
            "request": _create_request().model_copy(
                update={
                    "evidence_refs": [
                        (
                            "evidence-ref:control-center-goal-create-submission:"
                            f"sha256:{suffix}"
                        )
                    ]
                }
            ),
            "idempotency_ref": f"idempotency-ref:goal-mutation:rejected:{index}",
        }
        prepared = service.record_goal_mutation_submission(**kwargs)
        service.reject_goal_mutation_submission(
            submission_ref=prepared.submission_ref,
            request_fingerprint_ref=prepared.request_fingerprint_ref,
            rejection_reason_ref=f"reason-ref:goal-mutation-rejected:{index}",
        )
        if index == 0:
            first_kwargs = kwargs

    assert first_kwargs is not None
    state = json.loads(
        (tmp_path / "goal_mutation_submissions.json").read_text(encoding="utf-8")
    )
    assert any(
        tombstone["submission_ref"] == first_kwargs["submission_ref"]
        for tombstone in state["rejection_tombstones"]
    )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_SUBMISSION_PREVIOUSLY_REJECTED",
    ):
        GoalRuntimeService(tmp_path).record_goal_mutation_submission(**first_kwargs)


@pytest.mark.parametrize(
    "reserved_refs",
    [
        [
            (
                "evidence-ref:control-center-goal-update-submission:"
                "edit:sha256:" + "b" * 64
            )
        ],
        [
            ("evidence-ref:control-center-goal-create-submission:sha256:" + "c" * 64),
            (
                "evidence-ref:control-center-goal-update-submission:"
                "transition:sha256:" + "d" * 64
            ),
        ],
    ],
)
def test_submission_rejects_cross_operation_reserved_evidence_on_prepare_and_reload(
    tmp_path: Path,
    reserved_refs: list[str],
) -> None:
    request = _create_request().model_copy(update={"evidence_refs": reserved_refs})
    with pytest.raises(
        ValueError,
        match="GOAL_SUBMISSION_EVIDENCE_BINDING_REQUIRED",
    ):
        GoalRuntimeService(tmp_path / "prepare").record_goal_mutation_submission(
            submission_ref="submission-ref:goal-mutation:cross-operation",
            operation="create",
            goal_ref=None,
            request=request,
            idempotency_ref="idempotency-ref:goal-mutation:cross-operation",
        )

    state_dir = tmp_path / "reload"
    service = GoalRuntimeService(state_dir)
    valid_ref = "evidence-ref:control-center-goal-create-submission:sha256:" + "e" * 64
    valid_request = _create_request().model_copy(update={"evidence_refs": [valid_ref]})
    service.record_goal_mutation_submission(
        submission_ref="submission-ref:goal-mutation:reload",
        operation="create",
        goal_ref=None,
        request=valid_request,
        idempotency_ref="idempotency-ref:goal-mutation:reload",
    )
    state_path = state_dir / "goal_mutation_submissions.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["records"][0]["request_payload"]["evidence_refs"] = reserved_refs
    state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
    with pytest.raises(
        GoalRuntimeCorruptionError,
        match="GOAL_SUBMISSION_STATE_CORRUPT",
    ):
        build_runtime_run_events_read_model(service=GoalRuntimeService(state_dir))


@pytest.mark.parametrize("control_character", ["\x1b", "\b", "\x7f", "\x9b"])
def test_durable_goal_and_event_summaries_reject_terminal_controls(
    control_character: str,
) -> None:
    create_payload = _create_request().model_dump(mode="json")
    create_payload["objective"] = f"Bounded{control_character}operator summary."
    with pytest.raises(ValueError, match="GOAL_RAW_CONTENT_PERSISTENCE_DENIED"):
        GoalCreateRequest.model_validate(create_payload)
    with pytest.raises(ValueError, match="GOAL_RAW_CONTENT_PERSISTENCE_DENIED"):
        DurableRunEventAppendRequest(
            run_ref="run-ref:terminal-control",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary=f"Bounded{control_character}event summary.",
            idempotency_ref="idempotency-ref:terminal-control",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )


def test_successful_receipt_summary_survives_later_events_and_compaction(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path, retention_limit=2)
    run_ref = "run-ref:receipt-summary:compacted"
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="The bounded local run started.",
            idempotency_ref="idempotency-ref:receipt-summary:started",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="The successful local receipt was recorded.",
            proof_refs=["proof-ref:receipt-summary:success"],
            receipt_refs=["receipt-ref:receipt-summary:success"],
            idempotency_ref="idempotency-ref:receipt-summary:receipt",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        ),
    )
    for index in range(2):
        _append_event(
            service,
            DurableRunEventAppendRequest(
                run_ref=run_ref,
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=DurableRunEventKind.evidence_linked,
                safe_summary="Additional bounded evidence metadata was linked.",
                proof_refs=[f"proof-ref:receipt-summary:later:{index}"],
                idempotency_ref=f"idempotency-ref:receipt-summary:later:{index}",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            ),
        )

    read_model = build_runtime_run_events_read_model(
        service=GoalRuntimeService(tmp_path, retention_limit=2)
    )
    summary = next(
        item for item in read_model.stream_summaries if item.run_ref == run_ref
    )
    assert summary.successful_receipt_recorded is True
    assert summary.terminal_event_kind is None
    assert summary.first_retained_sequence == 3
    assert summary.last_sequence == 4
    assert summary.retained_event_count == 2
    assert read_model.retained_event_count == 2
    assert read_model.completed_run_count == 1


def test_quarantine_capacity_fails_closed_before_later_receipt_sync(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def runner(**_kwargs: object) -> RuntimeCommandRunResult:
        return RuntimeCommandRunResult(
            exit_code=0,
            timed_out=False,
            duration_ms=1,
            output_bytes=b"SAFE_STATUS",
        )

    store = RuntimeInvocationStore(
        tmp_path / "runtime",
        active_authority_leases=[workspace_execute_authority_lease()],
    )
    adapter = GovernedCommandRuntimeAdapter(
        workspace_root=ROOT,
        runner=runner,
    )
    records = [
        invoke_governed_command(
            store=store,
            adapter=adapter,
            request=RuntimeCommandExecutionRequest(
                intent="git_status",
                mission_ref=mission_ref,
                safe_summary="A bounded historical or current inspection completed.",
            ),
            idempotency_ref=f"idempotency-ref:quarantine-capacity:{index}",
        ).record
        for index, mission_ref in enumerate(
            (
                "goal-ref:sha256:" + "1" * 64,
                "goal-ref:sha256:" + "2" * 64,
                "mission-ref:current-after-quarantine-capacity",
            )
        )
    ]
    monkeypatch.setattr(
        goal_runtime_module,
        "MAX_RUNTIME_PROJECTION_INCOMPATIBILITIES",
        1,
    )
    service = GoalRuntimeService(tmp_path / "goals")
    with pytest.raises(
        GoalRuntimeError,
        match="RUNTIME_PROJECTION_INCOMPATIBILITY_CAPACITY_EXCEEDED",
    ):
        service.sync_runtime_invocations(
            records,
            invocation_store=store,
        )

    incompatibilities = service.events.projection_incompatibilities()
    assert [item.invocation_ref for item in incompatibilities] == [
        records[0].invocation_ref
    ]
    restarted = GoalRuntimeService(tmp_path / "goals")
    with pytest.raises(
        GoalRuntimeError,
        match="RUNTIME_PROJECTION_INCOMPATIBILITY_CAPACITY_EXCEEDED",
    ):
        restarted.sync_runtime_invocations(
            records,
            invocation_store=store,
        )
    assert not restarted.events.replay(records[-1].invocation_ref).events
