from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalStatus, ApprovalSubjectType
from ultimate_ai_agent.core.approvals.validation import assert_approval_secret_clean
from ultimate_ai_agent.core.hygiene.policies import DataClassification
from ultimate_ai_agent.core.time import utc_now


class ApprovalGrant(BaseModel):
    approval_ref: str = Field(..., min_length=1)
    approval_request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    subject_type: ApprovalSubjectType
    subject_id: str = Field(..., min_length=1)
    granted_to_actor_id: str = Field(..., min_length=1)
    approved_by_actor_id: str = Field(..., min_length=1)
    approved_actions: List[str] = Field(default_factory=list)
    approved_resource_refs: List[str] = Field(default_factory=list)
    risk_level: ApprovalRiskLevel
    data_classification: DataClassification
    purpose: str = Field(..., min_length=1)
    status: ApprovalStatus = ApprovalStatus.granted
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    event_ref: Optional[str] = None
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def grant_must_be_scoped_and_secret_clean(self) -> Any:
        if not self.approved_actions:
            raise ValueError("ApprovalGrant must approve at least one action.")
        assert_approval_secret_clean(self.model_dump(mode="json"), "Approval grant")
        return self
