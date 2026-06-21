from collections import defaultdict
from typing import Any, Iterable

from pydantic import ValidationError

from ultimate_ai_agent.core.planning.contracts import (
    TaskPlan,
    TaskPlanDecision,
    TaskPlanDecisionStatus,
    TaskPlanReceiptPlan,
    TaskPlanningRequest,
    boundary_reason_codes,
)
from ultimate_ai_agent.core.planning.enums import TaskPlanAuthorityLevel
from ultimate_ai_agent.core.planning.validation import (
    hidden_side_effect_reasons,
    plan_derived_risk_level,
    step_kind_reasons,
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


def _dedupe(reasons: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(reason for reason in reasons if reason))


def _validation_reason(exc: Exception, fallback: str = "TASK_PLAN_REVALIDATION_FAILED") -> list[str]:
    message = str(exc).lower()
    if "unsafe content" in message or "secret" in message:
        return ["SECRET_METADATA_DENIED", fallback]
    if "raw_" in message or "raw " in message:
        return ["RAW_INPUT_DENIED", fallback]
    return [fallback]


def _safe_decision(
    plan_id: str,
    status: TaskPlanDecisionStatus,
    reasons: list[str],
    safe_message: str,
    derived_plan_risk_level: Any,
) -> TaskPlanDecision:
    decision_id = f"task-plan-decision:{plan_id.split(':', 1)[-1]}"
    receipt_plan = TaskPlanReceiptPlan(
        receipt_plan_ref=f"task-plan-receipt:{plan_id.split(':', 1)[-1]}",
        plan_id=plan_id,
        decision_id=decision_id,
        authority_level=TaskPlanAuthorityLevel.non_authoritative,
        derived_plan_risk_level=derived_plan_risk_level,
        safe_summary="Non-authoritative task planning receipt plan.",
    )
    return TaskPlanDecision(
        decision_id=decision_id,
        plan_id=plan_id,
        status=status,
        valid_for_review=status == TaskPlanDecisionStatus.valid_for_review,
        execution_authorized=False,
        execution_performed=False,
        scheduler_registered=False,
        reason_codes=_dedupe(reasons),
        safe_message=safe_message,
        receipt_plan=receipt_plan,
        derived_plan_risk_level=derived_plan_risk_level,
    )


def _request_and_plan(value: TaskPlan | TaskPlanningRequest) -> tuple[TaskPlanningRequest | None, TaskPlan]:
    if isinstance(value, TaskPlanningRequest):
        return value, value.plan
    return None, value


def _revalidate_plan_for_evaluation(plan: TaskPlan) -> list[str]:
    reasons: list[str] = []
    for value, field_name in [
        (getattr(plan, "plan_id", None), "plan_id"),
        (getattr(plan, "approval_ref", None), "approval_ref"),
    ]:
        if value:
            try:
                if field_name == "approval_ref":
                    validate_safe_task_text(value, field_name)
                else:
                    validate_task_ref(value, field_name)
            except ValueError as exc:
                reasons.extend(_validation_reason(exc))
    try:
        validate_safe_task_text(getattr(plan, "safe_summary", ""), "safe_summary")
        validate_safe_task_payload(getattr(plan, "metadata", {}), "metadata")
    except ValueError as exc:
        reasons.extend(_validation_reason(exc))
    if getattr(plan, "approval_ref", None):
        reasons.append("APPROVAL_REF_NOT_TASK_AUTHORITY")
        if str(getattr(plan, "approval_ref")).startswith("approval_test_"):
            reasons.append("APPROVAL_TEST_REF_DENIED")
    if getattr(plan, "authority_level", TaskPlanAuthorityLevel.review_plan_only) == TaskPlanAuthorityLevel.blocked_authority:
        reasons.append("TASK_PLAN_AUTHORITY_DENIED")
    try:
        TaskPlan.model_validate(plan.model_dump())
    except (ValidationError, ValueError) as exc:
        reasons.extend(_validation_reason(exc))
    return reasons


def _revalidate_request_for_evaluation(request: TaskPlanningRequest | None) -> list[str]:
    if request is None:
        return []
    reasons: list[str] = []
    if bool(getattr(request, "execution_requested", False)):
        reasons.append("TASK_EXECUTION_REQUEST_DENIED")
    if bool(getattr(request, "auto_run_requested", False)):
        reasons.append("TASK_AUTO_RUN_DENIED")
    if bool(getattr(request, "schedule_requested", False)):
        reasons.append("TASK_SCHEDULER_DENIED")
    try:
        validate_safe_task_payload(getattr(request, "metadata", {}), "metadata")
        TaskPlanningRequest.model_validate(request.model_dump())
    except (ValidationError, ValueError) as exc:
        reasons.extend(_validation_reason(exc, fallback="TASK_PLANNING_REQUEST_REVALIDATION_FAILED"))
    return reasons


def _step_reasons(plan: TaskPlan) -> list[str]:
    reasons: list[str] = []
    for step in getattr(plan, "steps", []):
        try:
            validate_task_ref(getattr(step, "step_id", ""), "step_id")
            validate_safe_task_text(getattr(step, "safe_summary", ""), "safe_summary")
            validate_safe_task_payload(getattr(step, "metadata", {}), "metadata")
        except ValueError as exc:
            reasons.extend(_validation_reason(exc, fallback="TASK_STEP_REVALIDATION_FAILED"))
        reasons.extend(
            step_kind_reasons(
                getattr(step, "step_kind", None),
                getattr(step, "declared_risk_level", None),
            )
        )
        reasons.extend(hidden_side_effect_reasons(step))
        reasons.extend(boundary_reason_codes(getattr(step, "input_boundary", None)))
    return reasons


def _dependency_reasons(plan: TaskPlan) -> list[str]:
    steps = list(getattr(plan, "steps", []))
    step_ids = [getattr(step, "step_id", "") for step in steps]
    step_id_set = set(step_ids)
    reasons: list[str] = []
    if len(step_ids) != len(step_id_set):
        reasons.append("DUPLICATE_STEP_ID_DENIED")

    graph: dict[str, list[str]] = defaultdict(list)
    for step in steps:
        step_id = getattr(step, "step_id", "")
        for dependency_id in list(getattr(step, "depends_on", [])):
            if dependency_id not in step_id_set:
                reasons.append("MISSING_DEPENDENCY_STEP_DENIED")
            else:
                graph[dependency_id].append(step_id)

    for dependency in getattr(plan, "dependencies", []):
        before = getattr(dependency, "before_step_id", "")
        after = getattr(dependency, "after_step_id", "")
        if before not in step_id_set or after not in step_id_set:
            reasons.append("MISSING_DEPENDENCY_STEP_DENIED")
        else:
            graph[before].append(after)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(step_id: str) -> bool:
        if step_id in visiting:
            return True
        if step_id in visited:
            return False
        visiting.add(step_id)
        has_cycle = any(visit(next_step) for next_step in graph.get(step_id, []))
        visiting.remove(step_id)
        visited.add(step_id)
        return has_cycle

    if any(visit(step_id) for step_id in step_id_set):
        reasons.append("DEPENDENCY_CYCLE_DENIED")
    return reasons


def evaluate_task_plan(value: TaskPlan | TaskPlanningRequest) -> TaskPlanDecision:
    request, plan = _request_and_plan(value)
    plan_id = getattr(plan, "plan_id", "plan:m29-invalid")
    reasons: list[str] = []
    reasons.extend(_revalidate_request_for_evaluation(request))
    reasons.extend(_revalidate_plan_for_evaluation(plan))
    reasons.extend(_step_reasons(plan))
    reasons.extend(_dependency_reasons(plan))
    reasons = _dedupe(reasons)
    derived_risk = plan_derived_risk_level(list(getattr(plan, "steps", [])))

    if reasons:
        return _safe_decision(
            plan_id,
            TaskPlanDecisionStatus.denied,
            reasons,
            "Task plan denied for review-only safety policy.",
            derived_risk,
        )
    return _safe_decision(
        plan_id,
        TaskPlanDecisionStatus.valid_for_review,
        ["TASK_PLAN_VALID_FOR_REVIEW"],
        "Task plan is valid for non-authoritative human review.",
        derived_risk,
    )
