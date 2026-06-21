from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.enums import ExecutionRunStatus, ExecutionStepStatus
from ultimate_ai_agent.core.execution.steps import ExecutionStep
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


class ExecutionRun(BaseModel):
    run_id: str = Field(..., min_length=1)
    source_task_plan_ref: str = Field(..., min_length=1)
    steps: List[ExecutionStep] = Field(..., min_length=1)
    status: ExecutionRunStatus = ExecutionRunStatus.planned
    replay_keys_seen: List[str] = Field(default_factory=list)
    transition_ids_seen: List[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    approval_ref: Optional[str] = None
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_run(self) -> Any:
        validate_execution_ref(self.run_id, "run_id")
        validate_execution_ref(self.source_task_plan_ref, "source_task_plan_ref")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.approval_ref:
            validate_safe_execution_text(self.approval_ref, "approval_ref")
        for ref in [*self.replay_keys_seen, *self.transition_ids_seen, *self.metadata_refs]:
            validate_execution_ref(ref, "metadata_ref")
        validate_safe_execution_payload(self.metadata, "metadata")
        return self

    def step_by_id(self, step_id: str) -> ExecutionStep | None:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def completed_step_ids(self) -> set[str]:
        return {
            step.step_id
            for step in self.steps
            if step.status == ExecutionStepStatus.completed_no_effect
        }

    def ready_steps(self) -> List[ExecutionStep]:
        completed = self.completed_step_ids()
        return sorted(
            [
                step
                for step in self.steps
                if step.status in {ExecutionStepStatus.pending, ExecutionStepStatus.ready}
                and all(dependency in completed for dependency in step.depends_on)
            ],
            key=lambda step: step.step_id,
        )
