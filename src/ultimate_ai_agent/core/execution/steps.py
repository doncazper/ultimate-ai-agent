from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.enums import (
    ExecutionInputTrustLevel,
    ExecutionStepMode,
    ExecutionStepStatus,
)
from ultimate_ai_agent.core.execution.validation import (
    raw_input_reasons,
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


class ExecutionStepInputBoundary(BaseModel):
    input_refs: List[str] = Field(default_factory=list)
    input_trust_level: ExecutionInputTrustLevel = ExecutionInputTrustLevel.safe_reference
    contains_raw_prompt: bool = False
    contains_raw_model_output: bool = False
    contains_raw_file_content: bool = False
    contains_raw_transcript: bool = False
    contains_secret_like_content: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_input_boundary(self):
        for ref in [*self.input_refs, *self.metadata_refs]:
            validate_execution_ref(ref, "input_ref")
        for reason in raw_input_reasons(self):
            raise ValueError(reason)
        validate_safe_execution_payload(self.metadata, "metadata")
        return self


class ExecutionStep(BaseModel):
    step_id: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    mode: ExecutionStepMode = ExecutionStepMode.no_effect
    status: ExecutionStepStatus = ExecutionStepStatus.pending
    input_boundary: ExecutionStepInputBoundary = Field(default_factory=ExecutionStepInputBoundary)
    depends_on: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_step(self):
        validate_execution_ref(self.step_id, "step_id")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in [*self.depends_on, *self.metadata_refs]:
            validate_execution_ref(ref, "step_ref")
        validate_safe_execution_payload(self.metadata, "metadata")
        return self

    @property
    def is_completed_no_effect(self) -> bool:
        return self.status == ExecutionStepStatus.completed_no_effect

