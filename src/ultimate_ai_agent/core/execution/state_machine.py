from pydantic import ValidationError

from ultimate_ai_agent.core.execution.enums import (
    ExecutionRunStatus,
    ExecutionStepStatus,
    ExecutionTransitionKind,
    ExecutionTransitionStatus,
)
from ultimate_ai_agent.core.execution.receipts import ExecutionReceiptPlan
from ultimate_ai_agent.core.execution.runs import ExecutionRun
from ultimate_ai_agent.core.execution.transitions import ExecutionTransitionDecision, ExecutionTransitionRequest
from ultimate_ai_agent.core.execution.validation import (
    boundary_reason_codes,
    dedupe_reasons,
    hidden_side_effect_reasons,
    step_mode_reason,
    validate_safe_execution_payload,
    validation_reason,
)


def dependency_graph_reason_codes(run: ExecutionRun) -> list[str]:
    step_ids = [step.step_id for step in run.steps]
    step_id_set = set(step_ids)
    reasons: list[str] = []
    if len(step_ids) != len(step_id_set):
        reasons.append("DUPLICATE_EXECUTION_STEP_ID_DENIED")

    graph: dict[str, list[str]] = {step_id: [] for step_id in step_id_set}
    for step in run.steps:
        for dependency_id in step.depends_on:
            if dependency_id not in step_id_set:
                reasons.append("MISSING_EXECUTION_DEPENDENCY_DENIED")
            else:
                graph.setdefault(dependency_id, []).append(step.step_id)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step_id: str) -> bool:
        if step_id in visiting:
            return True
        if step_id in visited:
            return False
        visiting.add(step_id)
        has_cycle = any(visit(next_step_id) for next_step_id in graph.get(step_id, []))
        visiting.remove(step_id)
        visited.add(step_id)
        return has_cycle

    if any(visit(step_id) for step_id in step_id_set):
        reasons.append("EXECUTION_DEPENDENCY_CYCLE_DENIED")
    return dedupe_reasons(reasons)


def _revalidate_run(run: ExecutionRun) -> list[str]:
    reasons: list[str] = []
    try:
        validate_safe_execution_payload(getattr(run, "metadata", {}), "metadata")
        ExecutionRun.model_validate(run.model_dump())
    except (ValidationError, ValueError) as exc:
        reasons.extend(validation_reason(exc, fallback="EXECUTION_RUN_REVALIDATION_FAILED"))
    if getattr(run, "approval_ref", None):
        reasons.append("APPROVAL_REF_NOT_EXECUTION_AUTHORITY")
        if str(getattr(run, "approval_ref")).startswith("approval_test_"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
    return reasons


def _revalidate_request(request: ExecutionTransitionRequest) -> list[str]:
    reasons: list[str] = []
    try:
        validate_safe_execution_payload(getattr(request, "metadata", {}), "metadata")
        ExecutionTransitionRequest.model_validate(request.model_dump())
    except (ValidationError, ValueError) as exc:
        reasons.extend(validation_reason(exc, fallback="EXECUTION_REQUEST_REVALIDATION_FAILED"))
    if getattr(request, "approval_ref", None):
        reasons.append("APPROVAL_REF_NOT_EXECUTION_AUTHORITY")
        if str(getattr(request, "approval_ref")).startswith("approval_test_"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
    if bool(getattr(request, "execution_requested", False)):
        reasons.append("EXECUTION_REQUEST_DENIED")
    if bool(getattr(request, "auto_run_requested", False)):
        reasons.append("AUTO_RUN_DENIED")
    if bool(getattr(request, "schedule_requested", False)):
        reasons.append("SCHEDULE_DENIED")
    if bool(getattr(request, "background_worker_requested", False)):
        reasons.append("BACKGROUND_WORKER_DENIED")
    if bool(getattr(request, "side_effect_execution_enabled", False)):
        reasons.append("SIDE_EFFECT_EXECUTION_DENIED")
    if not getattr(request, "transition_id", None):
        reasons.append("EXECUTION_TRANSITION_ID_REQUIRED")
    return reasons


def _step_reason_codes(run: ExecutionRun) -> list[str]:
    reasons: list[str] = []
    for step in run.steps:
        try:
            validate_safe_execution_payload(getattr(step, "metadata", {}), "metadata")
            step.__class__.model_validate(step.model_dump())
        except (ValidationError, ValueError) as exc:
            reasons.extend(validation_reason(exc, fallback="EXECUTION_STEP_REVALIDATION_FAILED"))
        reason = step_mode_reason(step.mode)
        if reason:
            reasons.append(reason)
        reasons.extend(boundary_reason_codes(step.input_boundary))
        reasons.extend(hidden_side_effect_reasons(getattr(step, "metadata", {})))
        reasons.extend(hidden_side_effect_reasons(getattr(step.input_boundary, "metadata", {})))
    return reasons


def _target_step_reason_codes(run: ExecutionRun, request: ExecutionTransitionRequest) -> tuple[list[str], ExecutionStepStatus | None]:
    if not request.target_step_id:
        return ["EXECUTION_TARGET_STEP_REQUIRED"], None
    step = run.step_by_id(request.target_step_id)
    if step is None:
        return ["UNKNOWN_EXECUTION_STEP_DENIED"], None
    completed = run.completed_step_ids()
    unmet = [dependency_id for dependency_id in step.depends_on if dependency_id not in completed]
    if unmet:
        return ["EXECUTION_DEPENDENCY_UNMET_DENIED"], ExecutionStepStatus.waiting_for_dependency
    if step.status == ExecutionStepStatus.blocked:
        return ["EXECUTION_STEP_BLOCKED_DENIED"], step.status
    if step.status in {
        ExecutionStepStatus.denied,
        ExecutionStepStatus.paused,
        ExecutionStepStatus.waiting_for_dependency,
        ExecutionStepStatus.skipped,
    }:
        return ["INVALID_EXECUTION_STEP_STATUS_DENIED"], step.status
    if step.status == ExecutionStepStatus.completed_no_effect:
        return ["EXECUTION_STEP_ALREADY_COMPLETED_DENIED"], step.status
    if request.transition_kind == ExecutionTransitionKind.mark_step_ready:
        if step.status == ExecutionStepStatus.ready:
            return [], ExecutionStepStatus.ready
        if step.status != ExecutionStepStatus.pending:
            return ["INVALID_EXECUTION_STEP_STATUS_DENIED"], step.status
        return [], ExecutionStepStatus.ready
    if request.transition_kind == ExecutionTransitionKind.complete_no_effect_step:
        if step.status != ExecutionStepStatus.ready:
            return ["EXECUTION_STEP_NOT_READY_DENIED"], step.status
        return [], ExecutionStepStatus.completed_no_effect
    if request.transition_kind == ExecutionTransitionKind.wait_for_dependency:
        return [], ExecutionStepStatus.ready if step.status == ExecutionStepStatus.pending else step.status
    return [], step.status


def _run_status_reason(run: ExecutionRun, request: ExecutionTransitionRequest) -> str | None:
    terminal_statuses = {
        ExecutionRunStatus.blocked,
        ExecutionRunStatus.completed_no_effect,
        ExecutionRunStatus.denied,
    }
    advancing_kinds = {
        ExecutionTransitionKind.mark_step_ready,
        ExecutionTransitionKind.complete_no_effect_step,
        ExecutionTransitionKind.wait_for_dependency,
        ExecutionTransitionKind.finalize_no_effect_run,
    }
    if run.status in terminal_statuses:
        return "INVALID_EXECUTION_RUN_STATUS_DENIED"
    if run.status == ExecutionRunStatus.paused and request.transition_kind in advancing_kinds:
        return "INVALID_EXECUTION_RUN_STATUS_DENIED"
    return None


def _finalize_reason_codes(run: ExecutionRun) -> list[str]:
    reasons: list[str] = []
    for step in run.steps:
        if step.status == ExecutionStepStatus.blocked:
            reasons.append("EXECUTION_RUN_FINALIZE_BLOCKED_DENIED")
        elif step.status not in {
            ExecutionStepStatus.completed_no_effect,
            ExecutionStepStatus.skipped,
        }:
            reasons.append("EXECUTION_RUN_FINALIZE_INCOMPLETE_DENIED")
    return dedupe_reasons(reasons)


def _receipt(run_id: str, request: ExecutionTransitionRequest) -> ExecutionReceiptPlan:
    suffix = request.replay_key.split(":", 1)[-1]
    target = request.target_step_id or "execution-step:m30-none"
    return ExecutionReceiptPlan(
        receipt_plan_ref=f"execution-receipt:{suffix}",
        run_id=run_id,
        transition_id=request.transition_id or f"execution-transition:{suffix}",
        target_step_id=target,
        safe_summary="Non-authoritative execution-state-machine receipt plan.",
    )


def _decision(
    run: ExecutionRun,
    request: ExecutionTransitionRequest,
    status: ExecutionTransitionStatus,
    reasons: list[str],
    safe_message: str,
    step_status: ExecutionStepStatus | None = None,
    run_status: ExecutionRunStatus | None = None,
) -> ExecutionTransitionDecision:
    suffix = request.replay_key.split(":", 1)[-1]
    return ExecutionTransitionDecision(
        decision_id=f"execution-decision:{suffix}",
        run_id=run.run_id,
        target_step_id=request.target_step_id,
        status=status,
        run_status=run_status or (ExecutionRunStatus.running_no_effect if status == ExecutionTransitionStatus.approved_no_effect_transition else ExecutionRunStatus.denied),
        step_status=step_status,
        transition_kind=request.transition_kind,
        reason_codes=dedupe_reasons(reasons),
        safe_message=safe_message,
        receipt_plan=_receipt(run.run_id, request),
    )


def evaluate_execution_transition(run: ExecutionRun, request: ExecutionTransitionRequest) -> ExecutionTransitionDecision:
    reasons: list[str] = []
    reasons.extend(_revalidate_run(run))
    reasons.extend(_revalidate_request(request))
    reasons.extend(dependency_graph_reason_codes(run))
    reasons.extend(_step_reason_codes(run))

    if request.run_id != run.run_id:
        reasons.append("EXECUTION_RUN_REF_MISMATCH_DENIED")
    if request.replay_key in run.replay_keys_seen:
        reasons.append("EXECUTION_REPLAY_DENIED")
    if getattr(request, "transition_id", None) and request.transition_id in run.transition_ids_seen:
        reasons.append("EXECUTION_TRANSITION_REPLAY_DENIED")
    run_status_reason = _run_status_reason(run, request)
    if run_status_reason:
        reasons.append(run_status_reason)

    target_reasons: list[str] = []
    target_step_status: ExecutionStepStatus | None = None
    if request.transition_kind in {
        ExecutionTransitionKind.complete_no_effect_step,
        ExecutionTransitionKind.mark_step_ready,
        ExecutionTransitionKind.wait_for_dependency,
    }:
        target_reasons, target_step_status = _target_step_reason_codes(run, request)
        reasons.extend(target_reasons)
    if request.transition_kind == ExecutionTransitionKind.finalize_no_effect_run:
        reasons.extend(_finalize_reason_codes(run))

    reasons = dedupe_reasons(reasons)
    if reasons:
        run_status = ExecutionRunStatus.waiting_for_dependency if "EXECUTION_DEPENDENCY_UNMET_DENIED" in reasons else ExecutionRunStatus.denied
        return _decision(
            run,
            request,
            ExecutionTransitionStatus.denied,
            reasons,
            "Execution-state-machine transition denied by no-effect safety policy.",
            step_status=target_step_status,
            run_status=run_status,
        )

    if request.transition_kind == ExecutionTransitionKind.pause_run:
        return _decision(
            run,
            request,
            ExecutionTransitionStatus.paused,
            ["EXECUTION_RUN_PAUSED_NO_EFFECT"],
            "Execution-state-machine run paused without side effects.",
            run_status=ExecutionRunStatus.paused,
        )
    if request.transition_kind == ExecutionTransitionKind.block_run:
        return _decision(
            run,
            request,
            ExecutionTransitionStatus.blocked,
            ["EXECUTION_RUN_BLOCKED_NO_EFFECT"],
            "Execution-state-machine run blocked without side effects.",
            run_status=ExecutionRunStatus.blocked,
        )
    if request.transition_kind == ExecutionTransitionKind.finalize_no_effect_run:
        return _decision(
            run,
            request,
            ExecutionTransitionStatus.approved_no_effect_transition,
            ["EXECUTION_RUN_FINALIZED_NO_EFFECT"],
            "Execution-state-machine run finalized without side effects.",
            run_status=ExecutionRunStatus.completed_no_effect,
        )
    return _decision(
        run,
        request,
        ExecutionTransitionStatus.approved_no_effect_transition,
        ["EXECUTION_TRANSITION_ALLOWED_NO_EFFECT"],
        "Execution-state-machine transition allowed for no-effect state advancement only.",
        step_status=target_step_status,
    )
