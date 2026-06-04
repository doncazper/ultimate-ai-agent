import pytest

from ultimate_ai_agent.core.execution import (
    ExecutionReceiptPlan,
    ExecutionRun,
    ExecutionStep,
    ExecutionStepInputBoundary,
    ExecutionStepMode,
    ExecutionTransitionKind,
    ExecutionTransitionRequest,
    evaluate_execution_transition,
)


def test_receipt_plan_is_non_authoritative_and_summary_only():
    run = ExecutionRun(
        run_id="execution-run:m30-receipt",
        source_task_plan_ref="plan:m30-receipt",
        steps=[
            ExecutionStep(
                step_id="execution-step:m30-receipt",
                safe_summary="Validate receipt only.",
                mode=ExecutionStepMode.no_effect,
                input_boundary=ExecutionStepInputBoundary(input_refs=["canonical:m30"]),
            )
        ],
        safe_summary="Receipt run.",
    )
    request = ExecutionTransitionRequest(
        run_id="execution-run:m30-receipt",
        target_step_id="execution-step:m30-receipt",
        transition_kind=ExecutionTransitionKind.complete_no_effect_step,
        replay_key="replay:m30-receipt",
        safe_summary="Complete receipt step.",
    )

    decision = evaluate_execution_transition(run, request)

    assert decision.receipt_plan is not None
    assert decision.receipt_plan.execution_authorized is False
    assert decision.receipt_plan.execution_performed is False
    assert decision.receipt_plan.raw_content_stored is False
    assert decision.receipt_plan.safe_summary


def test_receipt_plan_rejects_execution_or_raw_storage_claims():
    receipt = ExecutionReceiptPlan(
        receipt_plan_ref="execution-receipt:m30",
        run_id="execution-run:m30",
        transition_id="execution-transition:m30",
        target_step_id="execution-step:m30",
        safe_summary="Receipt plan.",
    )

    with pytest.raises(ValueError):
        receipt.model_copy(update={"execution_performed": True}).model_validate(
            receipt.model_copy(update={"execution_performed": True}).model_dump()
        )

    with pytest.raises(ValueError):
        receipt.model_copy(update={"raw_content_stored": True}).model_validate(
            receipt.model_copy(update={"raw_content_stored": True}).model_dump()
        )
