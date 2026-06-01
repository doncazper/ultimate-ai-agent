from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.time import utc_now


class CostEstimate(BaseModel):
    estimate_id: str = Field(..., min_length=1)
    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)
    estimated_cost_usd: Optional[float] = Field(..., ge=0)
    estimated_runtime_seconds: Optional[float] = Field(None, ge=0)
    estimated_memory_gb: Optional[float] = Field(None, ge=0)
    estimated_vram_gb: Optional[float] = Field(None, ge=0)
    model_profile_id: Optional[str] = None
    provider_id: Optional[str] = None
    unknown_cost: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def total_tokens_match(self):
        if self.total_tokens != self.input_tokens + self.output_tokens:
            raise ValueError("total_tokens must equal input_tokens + output_tokens.")
        return self
