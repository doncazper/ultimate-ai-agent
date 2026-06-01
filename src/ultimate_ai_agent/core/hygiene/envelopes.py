from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from enum import Enum
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

class ErrorCategory(str, Enum):
    validation_error = "validation_error"
    authentication_error = "authentication_error"
    authorization_error = "authorization_error"
    consent_denied = "consent_denied"
    policy_denied = "policy_denied"
    rate_limited = "rate_limited"
    provider_error = "provider_error"
    tool_error = "tool_error"
    model_error = "model_error"
    not_found = "not_found"
    conflict = "conflict"
    timeout = "timeout"
    internal_error = "internal_error"
    security_blocked = "security_blocked"

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class Classification(str, Enum):
    public = "public"
    user_private = "user_private"
    project_private = "project_private"
    sensitive_personal = "sensitive_personal"
    credential_secret = "credential_" + "secret"
    regulated = "regulated"
    third_party_confidential = "third_party_confidential"
    system_internal = "system_internal"
    tcb_protected = "tcb_protected"

class ErrorEnvelope(BaseModel):
    code: str = Field(..., min_length=1)
    category: ErrorCategory
    message: Optional[str] = None
    safe_message: str = Field(..., min_length=1)
    severity: Severity
    retryable: bool
    user_action_required: Optional[bool] = None
    details_redacted: bool
    source: str = Field(..., min_length=1)
    caused_by: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

class ResultEnvelope(BaseModel):
    success: bool
    operation: str = Field(..., min_length=1)
    service: str = Field(..., min_length=1)
    run_id: Optional[str] = None
    step_id: Optional[str] = None
    trace_id: str = Field(..., min_length=1)
    correlation_id: Optional[str] = None
    data: Any = None
    error: Optional[ErrorEnvelope] = None
    warnings: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    cost_attribution: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = Field(None, ge=0.0)
    redactions_applied: List[str] = Field(default_factory=list)
    rollback_ref: Optional[str] = None
    classification: Optional[Classification] = None
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
