from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.costs.enums import BudgetScope
from ultimate_ai_agent.core.time import utc_now


class CostBudget(BaseModel):
    budget_id: str = Field(..., min_length=1)
    scope: BudgetScope
    scope_id: Optional[str] = None
    max_cost_usd: Optional[float] = Field(None, ge=0)
    max_input_tokens: Optional[int] = Field(None, ge=0)
    max_output_tokens: Optional[int] = Field(None, ge=0)
    max_total_tokens: Optional[int] = Field(None, ge=0)
    max_runtime_seconds: Optional[float] = Field(None, ge=0)
    max_local_memory_gb: Optional[float] = Field(None, ge=0)
    max_local_vram_gb: Optional[float] = Field(None, ge=0)
    period: Optional[str] = None
    warning_threshold_percent: int = Field(default=80, ge=0, le=100)
    hard_limit: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
