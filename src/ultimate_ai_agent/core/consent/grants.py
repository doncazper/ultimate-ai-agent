from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from ultimate_ai_agent.core.consent.enums import (
    ConsentStatus,
    ConsentScopeType,
    ConsentSubjectType,
    PermissionAction,
    DataBoundary,
)

class ConsentConstraint(BaseModel):
    constraint_id: str
    constraint_type: str  # max_tokens, rate_limit, path_prefix, domain_whitelist
    value: str

class ConsentAuditRef(BaseModel):
    run_id: Optional[str] = None
    trace_id: Optional[str] = None
    step_id: Optional[str] = None

class ConsentGrant(BaseModel):
    consent_id: str
    subject_type: ConsentSubjectType
    subject_id: str
    granted_to_actor: str
    on_behalf_of_user_id: str
    scope_type: ConsentScopeType
    scope_id: Optional[str] = None
    allowed_actions: List[PermissionAction] = Field(default_factory=list)
    denied_actions: List[PermissionAction] = Field(default_factory=list)
    allowed_resources: List[str] = Field(default_factory=list)
    denied_resources: List[str] = Field(default_factory=list)
    allowed_data_boundaries: List[DataBoundary] = Field(default_factory=list)
    denied_data_boundaries: List[DataBoundary] = Field(default_factory=list)
    allowed_purposes: List[str] = Field(default_factory=list)
    denied_purposes: List[str] = Field(default_factory=list)
    constraints: List[ConsentConstraint] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    status: ConsentStatus = ConsentStatus.active
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    approval_ref: Optional[str] = None
    event_ref: Optional[str] = None
    notes: Optional[str] = None

class RevocationRecord(BaseModel):
    consent_id: str
    revoked_at: datetime = Field(default_factory=datetime.utcnow)
    reason: str
    revoked_by: str
