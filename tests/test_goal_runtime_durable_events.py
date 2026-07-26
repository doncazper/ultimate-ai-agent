from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

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
    GoalRuntimeService,
    GoalState,
    GoalTransitionDeniedError,
    GoalTransitionKind,
    GoalTransitionRequest,
    GoalVersionConflictError,
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


def _create_request(*, run_ref: str = "run-ref:accepted-local:one") -> GoalCreateRequest:
    return GoalCreateRequest(
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
    service.events.append(
        DurableRunEventAppendRequest(
            run_ref=run_ref,
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.receipt_recorded,
            safe_summary="The accepted local read task recorded a redacted receipt.",
            proof_refs=["proof-ref:accepted-local:one"],
            receipt_refs=["receipt-ref:accepted-local:one"],
            goal_ref=goal_ref,
            plan_ref="plan-ref:accepted-local:one",
            idempotency_ref="idempotency-ref:event-receipt-one",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )
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
                stop_condition="Stop on a newly identified bounded condition.",
            ),
            idempotency_ref="idempotency-ref:goal-stale-edit",
        )

    restored = GoalRuntimeService(tmp_path).goals.get(created.goal_ref)
    assert restored == paused


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
    evidence = GoalCompletionEvidence(
        goal_ref=created.goal_ref,
        goal_version=requested.version,
        run_ref="run-ref:accepted-local:one",
        receipt_ref="receipt-ref:accepted-local:one",
        proof_ref="proof-ref:accepted-local:one",
        evidence_ref="evidence-ref:accepted-local:one",
        verifier_ref="verifier-ref:deterministic-receipt-binding:v1",
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
    assert verified.completion_verifier_ref == evidence.verifier_ref
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
    service.events.append(
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
        )
    )
    evidence = GoalCompletionEvidence(
        goal_ref=created.goal_ref,
        goal_version=requested.version,
        run_ref="run-ref:accepted-local:one",
        receipt_ref="receipt-ref:accepted-local:one",
        proof_ref="proof-ref:accepted-local:one",
        evidence_ref="evidence-ref:terminal-preflight:completion",
        verifier_ref="verifier-ref:terminal-preflight:v1",
    )

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
    evidence = GoalCompletionEvidence(
        goal_ref=created.goal_ref,
        goal_version=requested.version,
        run_ref="run-ref:accepted-local:one",
        receipt_ref="receipt-ref:accepted-local:one",
        proof_ref="proof-ref:accepted-local:one",
        evidence_ref="evidence-ref:accepted-local:completion-recovery",
        verifier_ref="verifier-ref:deterministic-receipt-binding:v1",
    )
    transition = GoalTransitionRequest(
        expected_version=requested.version,
        transition=GoalTransitionKind.verify_completion,
        reason_ref="reason-ref:deterministic-recovery-verifier",
        completion_evidence=evidence,
    )
    original_append = service.events.append
    failed_once = False

    def fail_terminal_append_once(
        request: DurableRunEventAppendRequest,
    ) -> DurableRunEvent:
        nonlocal failed_once
        if (
            not failed_once
            and request.event_kind
            == DurableRunEventKind.completion_verified.value
        ):
            failed_once = True
            raise OSError("simulated completion event commit interruption")
        return original_append(request)

    monkeypatch.setattr(service.events, "append", fail_terminal_append_once)
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
    assert completion_events[0].proof_refs == [evidence.proof_ref]

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
        service.events.append(
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
                idempotency_ref=f"idempotency-ref:cursor:{index}",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            )
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
    assert not {
        event.event_ref for event in page_one.events
    }.intersection(event.event_ref for event in page_two.events)

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
        service.events.append(request)

    replayed = GoalRuntimeService(
        tmp_path, retention_limit=3
    ).events.append(requests[0])
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
        service.events.append(
            requests[0].model_copy(
                update={"safe_summary": "A conflicting delayed retry."}
            )
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
        service.events.append(
            DurableRunEventAppendRequest(
                run_ref=f"run-ref:terminal-proof:{event_kind.value}",
                run_type=AcceptedLocalRunType.local_read_task,
                event_kind=event_kind,
                safe_summary="An unsupported terminal claim must fail closed.",
                idempotency_ref=(
                    f"idempotency-ref:terminal-proof:{event_kind.value}"
                ),
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            )
        )


def test_runtime_gateway_projects_accepted_receipt_into_durable_events(
    tmp_path: Path,
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
    assert replay.events[-1].receipt_refs == [
        result.record.receipt.receipt_ref
    ]
    restored = GoalRuntimeService(goal_dir)
    restored.sync_runtime_invocations(
        RuntimeInvocationStore(
            runtime_dir,
            active_authority_leases=[workspace_execute_authority_lease()],
        ).list_invocations()
    )
    assert len(restored.events.replay(result.record.invocation_ref).events) == 2


def test_goal_runtime_files_are_private(tmp_path: Path) -> None:
    state_dir = tmp_path / "private-state"
    service = GoalRuntimeService(state_dir)
    _create_goal(
        service,
        _create_request(),
        idempotency_ref="idempotency-ref:private-files:create",
    )
    service.events.append(
        DurableRunEventAppendRequest(
            run_ref="run-ref:private-files",
            run_type=AcceptedLocalRunType.local_read_task,
            event_kind=DurableRunEventKind.run_started,
            safe_summary="A bounded local run started.",
            idempotency_ref="idempotency-ref:private-files:event",
            authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
        )
    )

    assert stat.S_IMODE(state_dir.stat().st_mode) == 0o700
    for path in (
        state_dir / "goals.jsonl",
        state_dir / "run_events.jsonl",
        state_dir / "run_event_idempotency.jsonl",
    ):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


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
        service.events.append(
            DurableRunEventAppendRequest(
                run_ref=run_ref,
                run_type=AcceptedLocalRunType.local_metadata_action,
                event_kind=DurableRunEventKind.goal_linked,
                safe_summary=f"Bounded event {index}.",
                proof_refs=[f"proof-ref:tamper:{index}"],
                goal_ref="goal-ref:tamper",
                idempotency_ref=f"idempotency-ref:tamper:{index}",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            )
        )

    path = tmp_path / "run_events.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if mutation == "event_hash_ref":
        rows[1][mutation] = "event-hash-ref:tampered"
    elif mutation == "sequence":
        rows[1][mutation] = 9
        rows[1]["event_hash_ref"] = service.events._event_hash(  # noqa: SLF001
            service.events._load_events()[1].model_copy(  # noqa: SLF001
                update={"sequence": 9, "event_hash_ref": "event-hash-ref:pending"}
            )
        )
    elif mutation == "predecessor_hash_ref":
        rows[1][mutation] = "event-hash-ref:tampered-predecessor"
        event = service.events._load_events()[1].model_copy(  # noqa: SLF001
            update={
                "predecessor_hash_ref": rows[1][mutation],
                "event_hash_ref": "event-hash-ref:pending",
            }
        )
        rows[1]["event_hash_ref"] = service.events._event_hash(event)  # noqa: SLF001
    else:
        rows[1][mutation] = AcceptedLocalRunType.local_read_task.value
        event = service.events._load_events()[1].model_copy(  # noqa: SLF001
            update={
                "run_type": rows[1][mutation],
                "event_hash_ref": "event-hash-ref:pending",
            }
        )
        rows[1]["event_hash_ref"] = service.events._event_hash(event)  # noqa: SLF001
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
    receipt = service.events.append(receipt_request)
    assert service.events.append(receipt_request) == receipt
    with pytest.raises(
        GoalIdempotencyConflictError,
        match="RUN_EVENT_IDEMPOTENCY_CONFLICT",
    ):
        service.events.append(
            receipt_request.model_copy(
                update={"safe_summary": "A conflicting idempotent event."}
            )
        )

    completed = service.events.append(
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
        service.events.append(
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
    service.events.append(
        receipt_request.model_copy(
            update={
                "run_ref": unmatched_run_ref,
                "idempotency_ref": "idempotency-ref:fences:unmatched-receipt",
            }
        )
    )
    with pytest.raises(
        GoalTransitionDeniedError,
        match="RUN_EVENT_COMPLETION_RECEIPT_NOT_FOUND",
    ):
        service.events.append(
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
        reorder_service.events.append(
            DurableRunEventAppendRequest(
                run_ref="run-ref:accepted-local:reordered",
                run_type=AcceptedLocalRunType.local_metadata_action,
                event_kind=DurableRunEventKind.goal_linked,
                safe_summary=f"Ordered event {index}.",
                goal_ref="goal-ref:reordered",
                idempotency_ref=f"idempotency-ref:reordered:{index}",
                authority_decision_ref=EVENT_AUTHORITY_DECISION_REF,
            )
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
