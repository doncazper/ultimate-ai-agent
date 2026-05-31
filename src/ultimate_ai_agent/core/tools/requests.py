from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.consent.enums import DataBoundary

class ToolRequest(BaseModel):
    request_id: str
    run_id: str
    step_id: Optional[str] = None
    tool_id: str
    actor_context: ActorContext
    requested_action: str
    purpose: str
    input_summary: str = ""
    input_refs: List[str] = Field(default_factory=list)
    data_classification: DataBoundary
    idempotency_key: Optional[str] = None
    approval_ref: Optional[str] = None
    consent_refs: List[str] = Field(default_factory=list)
    dry_run_requested: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
