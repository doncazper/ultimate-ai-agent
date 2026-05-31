from typing import Optional
from pydantic import BaseModel, Field

class ContextBudget(BaseModel):
    model_context_limit: int
    system_prompt_tokens: int = 0
    tool_schema_tokens: int = 0
    world_state_tokens: int = 0
    context_pack_tokens: int = 0
    completion_reserve_tokens: int = 2000
    safety_margin_tokens: int = 1000
    token_calibration_factor: float = Field(default=1.0, ge=1.0)
    unknown_limit_fails_closed: bool = True

    @property
    def available_history_tokens(self) -> int:
        if self.model_context_limit <= 0:
            if self.unknown_limit_fails_closed:
                raise ValueError("Context limit is unknown and fail-closed is active.")
            # Fallback to conservative limit if configured not to fail-closed
            return 4000 - self.system_prompt_tokens - self.tool_schema_tokens - self.world_state_tokens - self.context_pack_tokens - self.completion_reserve_tokens - self.safety_margin_tokens
        
        fixed_costs = (
            self.system_prompt_tokens
            + self.tool_schema_tokens
            + self.world_state_tokens
            + self.context_pack_tokens
            + self.completion_reserve_tokens
            + self.safety_margin_tokens
        )
        available = self.model_context_limit - fixed_costs
        return max(0, available)

class ContextTrimPolicy(BaseModel):
    trim_large_tool_outputs_first: bool = True
    preserve_user_instructions: bool = True
    preserve_execution_contract: bool = True
    preserve_context_pack: bool = True
    preserve_world_state: bool = True
    preserve_safety_constraints: bool = True

class ContextTrimEvent(BaseModel):
    event_id: str
    run_id: str
    trimmed_component_ref: str
    original_token_count: int
    trimmed_token_count: int
    reference_to_ledger_id: Optional[str] = None
    reason: str

class TokenCalibrationEvent(BaseModel):
    event_id: str
    run_id: str
    estimated_tokens: int
    actual_tokens: int
    new_calibration_factor: float
