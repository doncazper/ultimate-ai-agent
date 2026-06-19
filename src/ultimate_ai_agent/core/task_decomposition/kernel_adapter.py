from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from ultimate_ai_agent.core.task_decomposition.contracts import DAGExecutionResult, PlanValidationResult, TaskIntent, TaskPlan
from ultimate_ai_agent.core.task_decomposition.runtime import (
    TaskDecompositionRequest,
    TaskDecompositionRunRequest,
    TaskDecompositionRunResult,
    TaskDecompositionService,
)


class KernelTaskDecompositionPreview(BaseModel):
    intent: TaskIntent
    plan: TaskPlan
    validation: PlanValidationResult
    safe_summary: str = "Kernel task decomposition preview completed."

    model_config = ConfigDict(extra="forbid")


class KernelTaskDecompositionRun(BaseModel):
    intent: TaskIntent
    plan: TaskPlan
    validation: PlanValidationResult
    execution: DAGExecutionResult | None = None
    safe_summary: str = "Kernel task decomposition local/dev run completed."

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionKernelAdapter:
    def __init__(self, service: TaskDecompositionService | None = None):
        self.service = service or TaskDecompositionService.from_env()

    def preview(self, raw_request: str, context: dict[str, Any] | None = None) -> KernelTaskDecompositionPreview:
        result = self.service.decompose(TaskDecompositionRequest(raw_request=raw_request, context=context or {}))
        return KernelTaskDecompositionPreview(
            intent=result.intent,
            plan=result.plan,
            validation=result.validation,
        )

    def run(self, request: TaskDecompositionRunRequest) -> KernelTaskDecompositionRun:
        result: TaskDecompositionRunResult = self.service.run_sync(request)
        return KernelTaskDecompositionRun(
            intent=result.intent,
            plan=result.plan,
            validation=result.validation,
            execution=result.execution,
        )
