from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SecretHandle(BaseModel):
    handle_id: str = Field(..., min_length=1)
    credential_ref: str = Field(..., min_length=1)
    provider_id: Optional[str] = None
    tool_id: Optional[str] = None
    issued_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")


class RedactedSecretView(BaseModel):
    credential_ref: str
    provider_id: Optional[str] = None
    tool_id: Optional[str] = None
    redacted_value: str = "[REDACTED_SECRET]"
    redactions_applied: List[str] = Field(default_factory=lambda: ["secret_value"])

    model_config = ConfigDict(extra="forbid")


class SecretAccessDecision(BaseModel):
    decision_id: str
    allowed: bool
    credential_ref: str
    secret_handle: Optional[SecretHandle] = None
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    redactions_applied: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")


class SecretRedactionReport(BaseModel):
    report_id: str
    redacted: bool
    redactions_applied: List[str] = Field(default_factory=list)
    safe_preview: str

    model_config = ConfigDict(extra="forbid")
