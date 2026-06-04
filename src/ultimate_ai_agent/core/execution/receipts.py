from typing import List

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref, validate_safe_execution_text


class ExecutionReceiptPlan(BaseModel):
    receipt_plan_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    target_step_id: str = Field(..., min_length=1)
    execution_authorized: bool = False
    execution_performed: bool = False
    raw_content_stored: bool = False
    memory_write_performed: bool = False
    file_mutation_performed: bool = False
    network_call_performed: bool = False
    model_call_performed: bool = False
    tool_execution_performed: bool = False
    action_execution_performed: bool = False
    event_ledger_mutation_performed: bool = False
    scheduler_registered: bool = False
    background_worker_registered: bool = False
    safe_summary: str = "Non-authoritative execution-state-machine receipt plan."
    metadata_refs: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_receipt(self):
        blocked_fields = [
            "execution_authorized",
            "execution_performed",
            "raw_content_stored",
            "memory_write_performed",
            "file_mutation_performed",
            "network_call_performed",
            "model_call_performed",
            "tool_execution_performed",
            "action_execution_performed",
            "event_ledger_mutation_performed",
            "scheduler_registered",
            "background_worker_registered",
        ]
        for field_name in blocked_fields:
            if getattr(self, field_name):
                raise ValueError(f"M30 receipt plans must keep {field_name}=False")
        for ref, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.run_id, "run_id"),
            (self.transition_id, "transition_id"),
            (self.target_step_id, "target_step_id"),
        ]:
            validate_execution_ref(ref, field_name)
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        return self

