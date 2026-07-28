from __future__ import annotations

import json
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import ultimate_ai_agent.core.runtime_gateway.goal_runtime as goal_runtime_module
from ultimate_ai_agent.core.runtime_gateway.goal_runtime import (
    AcceptedLocalRunType,
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
    build_goal_completion_evidence_ref,
    RunEventReplayStatus,
    capture_exact_goal_mutation_approval,
)
from ultimate_ai_agent.core.runtime_gateway import (
    GovernedCommandRuntimeAdapter,
    RuntimeCommandExecutionRequest,
    RuntimeCommandRunResult,
    RuntimeGateway,
    RuntimeInvocationStore,
)
from tests.authority_helpers import workspace_execute_authority_lease

EVENT_AUTHORITY_DECISION_REF = "authority-decision-ref:accepted-local:test"
ROOT = Path(__file__).resolve().parents[1]


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
            criterion_proof_refs=bound_criterion_proof_refs,
            plan_ref=plan_ref,
        ),
        verifier_ref=GOAL_COMPLETION_VERIFIER_REF,
    )


def _append_event(
    service: GoalRuntimeService,
    request: DurableRunEventAppendRequest,
) -> DurableRunEvent:
    if request.event_kind in {
        DurableRunEventKind.receipt_recorded.value,
        DurableRunEventKind.completion_verified.value,
        DurableRunEventKind.cancelled.value,
        DurableRunEventKind.failed_terminal.value,
        DurableRunEventKind.dead_lettered.value,
    }:
        return service._events.append(request)  # noqa: SLF001
    approval = capture_exact_goal_mutation_approval(
        operation="append-run-event",
        subject_ref=request.run_ref,
        request_payload=request.model_dump(mode="json"),
        idempotency_ref=request.idempotency_ref,
    )
    return service.append_run_event(request, approval_binding=approval)


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
    _append_event(
        service,
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="The accepted local read task recorded a redacted receipt.",
            proof_refs=[
                "proof-ref:accepted-local:one",
                "proof-ref:accepted-local:criterion:2",
            ],
            receipt_refs=["receipt-ref:accepted-local:one"],
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
    approval = capture_exact_goal_mutation_approval(
        operation="create",
        subject_ref="goal-ref:new",
        request_payload=request.model_dump(mode="json"),
        idempotency_ref=idempotency_ref,
    )
    return service.create_goal(
        request,
        idempotency_ref=idempotency_ref,
        approval_binding=approval,
    )


def _edit_goal(
    service: GoalRuntimeService,
    goal_ref: str,
    request: GoalEditRequest,
    *,
    idempotency_ref: str,
):
    approval = capture_exact_goal_mutation_approval(
        operation="edit",
        subject_ref=goal_ref,
        request_payload=request.model_dump(mode="json"),
        idempotency_ref=idempotency_ref,
    )
    return service.edit_goal(
        goal_ref,
        request,
        idempotency_ref=idempotency_ref,
        approval_binding=approval,
    )


def _transition_goal(
    service: GoalRuntimeService,
    goal_ref: str,
    request: GoalTransitionRequest,
    *,
    idempotency_ref: str,
):
    approval = capture_exact_goal_mutation_approval(
        operation=f"transition-{request.transition}",
        subject_ref=goal_ref,
        request_payload=request.model_dump(mode="json"),
        idempotency_ref=idempotency_ref,
    )
    return service.transition_goal(
        goal_ref,
        request,
        idempotency_ref=idempotency_ref,
        approval_binding=approval,
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


def test_goal_store_rejects_fabricated_approval_binding(
    tmp_path: Path,
) -> None:
    service = GoalRuntimeService(tmp_path)
    request = _create_request()
    fabricated = GoalMutationApprovalBinding(
        approval_ref="approval-ref:fabricated",
        approval_request_ref="approval-request-ref:fabricated",
        approval_decision_ref="approval-decision-ref:fabricated",
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
    ) -> DurableRunEvent:
        if request.event_kind == DurableRunEventKind.completion_verified.value:
            raise OSError("simulated completion projection interruption")
        return original_append(request)

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
    fabricated = GoalMutationApprovalBinding(
        approval_ref="approval-ref:fabricated",
        approval_request_ref="approval-request-ref:fabricated",
        approval_decision_ref="approval-decision-ref:fabricated",
        exact_scope_ref="exact-scope-ref:fabricated",
        request_fingerprint_ref="request-fingerprint-ref:fabricated",
    )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_BINDING_MISMATCH",
    ):
        recovered.transition_goal(
            created.goal_ref,
            transition,
            idempotency_ref="idempotency-ref:replay-approval:verify",
            approval_binding=fabricated,
        )

    assert not any(
        event.event_kind == DurableRunEventKind.completion_verified.value
        for event in recovered.events.replay(evidence.run_ref).events
    )


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
    ) -> DurableRunEvent:
        nonlocal failed_once
        if (
            not failed_once
            and request.event_kind == DurableRunEventKind.completion_verified.value
        ):
            failed_once = True
            raise OSError("simulated completion event commit interruption")
        return original_append(request)

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
    assert completion_events[0].receipt_refs == [evidence.receipt_ref]
    assert completion_events[0].proof_refs == list(
        dict.fromkeys([evidence.proof_ref, *evidence.criterion_proof_refs])
    )

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

    restored = GoalRuntimeService(tmp_path)
    restored.reconcile_durable_events()
    replay = restored.events.replay(evidence.run_ref)
    assert replay.events[-1].event_kind == (
        DurableRunEventKind.completion_verified.value
    )
    assert replay.events[-1].plan_ref == "plan-ref:accepted-local:one"
    assert replay.events[-1].authority_decision_ref == (
        verified_entry.approval_decision_ref
    )
    assert replay.events[-1].authority_decision_ref != (
        service.goals.latest_entry(created.goal_ref).approval_decision_ref
    )


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
            "GOAL_COMPLETION_CRITERION_PROOF_ARITY_MISMATCH",
        ),
        (
            [
                "proof-ref:accepted-local:one",
                "proof-ref:substituted:criterion:2",
            ],
            "GOAL_COMPLETION_CRITERION_PROOF_NOT_FOUND",
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

    goal_service = GoalRuntimeService(goal_dir)
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
    restored = GoalRuntimeService(goal_dir)
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
                idempotency_ref=(
                    f"idempotency-ref:journal-rollback:target:{index}"
                ),
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
        json.loads(line)
        for line in event_path.read_text(encoding="utf-8").splitlines()
    ]
    if rollback == "whole-run":
        rows = [row for row in rows if row["run_ref"] != rolled_back_run_ref]
    elif rollback == "oldest-retained":
        rows = [
            row
            for row in rows
            if not (
                row["run_ref"] == rolled_back_run_ref and row["sequence"] == 2
            )
        ]
    else:
        rows = [
            row
            for row in rows
            if not (
                row["run_ref"] == rolled_back_run_ref and row["sequence"] == 4
            )
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
    approval = capture_exact_goal_mutation_approval(
        operation="create",
        subject_ref="goal-ref:new",
        request_payload=request.model_dump(mode="json"),
        idempotency_ref="idempotency-ref:goal-lock-failure",
    )
    with pytest.raises(
        GoalRuntimeError,
        match="GOAL_RUNTIME_STORAGE_UNAVAILABLE",
    ):
        GoalRuntimeService(goal_dir).goals.create(
            request,
            idempotency_ref="idempotency-ref:goal-lock-failure",
            approval_binding=approval,
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
    wrong_approval = capture_exact_goal_mutation_approval(
        operation="append-run-event",
        subject_ref=wrong_request.run_ref,
        request_payload=wrong_request.model_dump(mode="json"),
        idempotency_ref=wrong_request.idempotency_ref,
    )

    assert not hasattr(service.events, "append")
    with pytest.raises(
        GoalTransitionDeniedError,
        match="GOAL_MUTATION_APPROVAL_BINDING_MISMATCH",
    ):
        service.append_run_event(request, approval_binding=wrong_approval)
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
    approval = capture_exact_goal_mutation_approval(
        operation="append-run-event",
        subject_ref=request.run_ref,
        request_payload=request.model_dump(mode="json"),
        idempotency_ref=request.idempotency_ref,
    )

    with pytest.raises(
        GoalTransitionDeniedError,
        match="RUN_EVENT_TRUSTED_PRODUCER_REQUIRED",
    ):
        service.append_run_event(request, approval_binding=approval)
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
        (
            event_bytes
            if limit_name == "MAX_RUN_EVENT_STORE_BYTES"
            else tombstone_bytes
        )
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
    eviction_credit = len(
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

    completed = service._events.append(  # noqa: SLF001
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.completion_verified,
            safe_summary="The linked receipt deterministically verified completion.",
            proof_refs=["proof-ref:fences:receipt"],
            receipt_refs=["receipt-ref:fences:receipt"],
            goal_ref="goal-ref:fences",
            idempotency_ref="idempotency-ref:fences:completion",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )
    )
    assert completed.sequence == 2
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
        match="RUN_EVENT_COMPLETION_RECEIPT_NOT_FOUND",
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
            "idempotency-set-hash-ref:goal-journal:sha256:"
            + "0" * 64
        )
        head_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(GoalRuntimeCorruptionError, match=expected_code):
        GoalRuntimeService(tmp_path).goals.get(created.goal_ref)


def test_goal_journal_recovers_one_entry_ahead_manifest_on_mutation(
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

    replayed = _edit_goal(
        GoalRuntimeService(tmp_path),
        created.goal_ref,
        GoalEditRequest(
            expected_version=created.version,
            text_redaction_posture="operator_authored_redacted_summary_only",
            objective="The journal commit survived before its head update.",
        ),
        idempotency_ref="idempotency-ref:goal-head-recovery:edit",
    )

    assert replayed == edited
    assert json.loads(
        (tmp_path / "goal_journal_head.json").read_text(encoding="utf-8")
    )["entry_count"] == 2


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
