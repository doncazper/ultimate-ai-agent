from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.enums import (
    ExecutionRunStatus,
    ExecutionStepStatus,
    ExecutionTransitionKind,
    ExecutionTransitionStatus,
)
from ultimate_ai_agent.core.execution.receipts import ExecutionReceiptPlan
from ultimate_ai_agent.core.execution.validation import (
    raw_input_reasons,
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


class ExecutionTransitionRequest(BaseModel):
    run_id: str = Field(..., min_length=1)
    target_step_id: Optional[str] = None
    transition_id: Optional[str] = None
    transition_kind: ExecutionTransitionKind
    replay_key: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1)
    approval_ref: Optional[str] = None
    execution_requested: bool = False
    auto_run_requested: bool = False
    schedule_requested: bool = False
    background_worker_requested: bool = False
    side_effect_execution_enabled: bool = False
    contains_raw_prompt: bool = False
    contains_raw_model_output: bool = False
    contains_raw_file_content: bool = False
    contains_raw_transcript: bool = False
    contains_secret_like_content: bool = False
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> Any:
        validate_execution_ref(self.run_id, "run_id")
        if self.target_step_id:
            validate_execution_ref(self.target_step_id, "target_step_id")
        if self.transition_id:
            validate_execution_ref(self.transition_id, "transition_id")
        validate_execution_ref(self.replay_key, "replay_key")
        validate_safe_execution_text(self.safe_summary, "safe_summary")
        if self.approval_ref:
            validate_safe_execution_text(self.approval_ref, "approval_ref")
        for ref in self.metadata_refs:
            validate_execution_ref(ref, "metadata_ref")
        for reason in raw_input_reasons(self):
            raise ValueError(reason)
        validate_safe_execution_payload(self.metadata, "metadata")
        return self


class ExecutionTransitionDecision(BaseModel):
    decision_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    target_step_id: Optional[str] = None
    status: ExecutionTransitionStatus
    run_status: ExecutionRunStatus
    step_status: Optional[ExecutionStepStatus] = None
    transition_kind: ExecutionTransitionKind
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    receipt_plan: Optional[ExecutionReceiptPlan] = None
    execution_authorized: bool = False
    execution_performed: bool = False
    side_effects_performed: List[str] = Field(default_factory=list)
    scheduler_registered: bool = False
    background_worker_registered: bool = False
    no_task_execution_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_memory_write_performed: bool = True
    no_file_mutation_performed: bool = True
    no_network_call_performed: bool = True
    no_model_call_performed: bool = True
    no_event_ledger_mutation_performed: bool = True
    no_scheduler_registered: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision(self) -> Any:
        if self.execution_authorized:
            raise ValueError("M30 transition decisions must not authorize real execution")
        if self.execution_performed:
            raise ValueError("M30 transition decisions must not perform real execution")
        if self.side_effects_performed:
            raise ValueError("M30 transition decisions must not report side effects")
        if self.scheduler_registered or self.background_worker_registered:
            raise ValueError("M30 transition decisions must not register schedulers or workers")
        for field_name in [
            "no_task_execution_performed",
            "no_tool_execution_performed",
            "no_action_execution_performed",
            "no_memory_write_performed",
            "no_file_mutation_performed",
            "no_network_call_performed",
            "no_model_call_performed",
            "no_event_ledger_mutation_performed",
            "no_scheduler_registered",
        ]:
            if not getattr(self, field_name):
                raise ValueError(f"M30 execution decision invariant failed: {field_name}")
        validate_execution_ref(self.decision_id, "decision_id")
        validate_execution_ref(self.run_id, "run_id")
        if self.target_step_id:
            validate_execution_ref(self.target_step_id, "target_step_id")
        validate_safe_execution_text(self.safe_message, "safe_message")
        return self
