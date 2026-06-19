import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.model_router.enums import ModelRouteStatus
from ultimate_ai_agent.core.time import utc_now


class ModelRouteDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"mroute_{uuid.uuid4().hex[:12]}")
    request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    status: ModelRouteStatus
    selected_profile_id: Optional[str] = None
    selected_model_id: Optional[str] = None
    candidate_profile_ids: List[str] = Field(default_factory=list)
    rejected_profile_ids: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    estimated_cost: Optional[float] = Field(None, ge=0)
    estimated_latency_ms: Optional[float] = Field(None, ge=0)
    cost_mode: Optional[str] = None
    fallback_plan_ref: Optional[str] = None
    fallback_used: bool = False
    verification_required: bool = False
    verification_route_id: Optional[str] = None
    eval_result_id: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    privacy_notes: List[str] = Field(default_factory=list)
    required_approval: bool = False
    consent_refs: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
