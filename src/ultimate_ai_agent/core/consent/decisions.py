from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from ultimate_ai_agent.core.consent.enums import PermissionAction, PermissionRisk, ApprovalRequirement, DataBoundary
from ultimate_ai_agent.core.consent.grants import ConsentAuditRef

class ConsentQuery(BaseModel):
    actor_id: str
    action: PermissionAction
    resource: str
    data_classification: Optional[DataBoundary] = None
    purpose: str
    risk_level: PermissionRisk = PermissionRisk.low
    audit_ref: Optional[ConsentAuditRef] = None

class ConsentDecision(BaseModel):
    decision_id: str
    allowed: bool
    matched_grants: List[str] = Field(default_factory=list)
    missing_permissions: List[str] = Field(default_factory=list)
    required_approval: ApprovalRequirement = ApprovalRequirement.none
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    event_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
