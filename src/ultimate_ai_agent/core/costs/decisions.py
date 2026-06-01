import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.costs.enums import BudgetStatus


class CostDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"cost_{uuid.uuid4().hex[:12]}")
    allowed: bool
    status: BudgetStatus
    budget_id: Optional[str] = None
    estimate_id: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    remaining_cost_usd: Optional[float] = Field(None, ge=0)
    remaining_tokens: Optional[int] = Field(None, ge=0)
    approval_required: bool = False
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
