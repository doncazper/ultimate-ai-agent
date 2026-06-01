from typing import Dict, List, Optional
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.time import utc_now


class RemotePolicyDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"remote_dec_{uuid.uuid4().hex[:12]}")
    allowed: bool
    status: str = Field(..., min_length=1)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    event_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def decision_must_be_safe(self):
        from ultimate_ai_agent.core.remote_workers.validation import assert_remote_secret_clean

        assert_remote_secret_clean(self.model_dump(mode="json"), "Remote policy decision")
        return self


def allowed_decision(reason_codes: list[str], safe_message: str, **metadata) -> RemotePolicyDecision:
    return RemotePolicyDecision(
        allowed=True,
        status="allowed",
        reason_codes=reason_codes,
        safe_message=safe_message,
        metadata=metadata,
    )


def denied_decision(reason_codes: list[str], safe_message: str, **metadata) -> RemotePolicyDecision:
    return RemotePolicyDecision(
        allowed=False,
        status="denied",
        reason_codes=sorted(set(reason_codes)),
        safe_message=safe_message,
        metadata=metadata,
    )

