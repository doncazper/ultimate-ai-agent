from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.remote_workers.validation import assert_remote_secret_clean
from ultimate_ai_agent.core.time import utc_now


class RemoteAuditContext(BaseModel):
    run_id: str = Field(..., min_length=1)
    correlation_id: str = Field(..., min_length=1)
    actor_context: ActorContext
    approval_refs: List[str] = Field(default_factory=list)
    consent_refs: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    trace_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def audit_context_must_be_safe(self) -> Any:
        assert_remote_secret_clean(self.model_dump(mode="json"), "Remote audit context")
        return self

