import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.enums import ApprovalDecisionStatus, ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.approvals.validation import assert_approval_secret_clean
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.policies import DataClassification
from ultimate_ai_agent.core.time import utc_now


class ApprovalValidationRequest(BaseModel):
    approval_ref: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    subject_type: ApprovalSubjectType
    subject_id: str = Field(..., min_length=1)
    requested_action: str = Field(..., min_length=1)
    actor_context: ActorContext
    resource_refs: List[str] = Field(default_factory=list)
    risk_level: ApprovalRiskLevel
    data_classification: DataClassification
    purpose: str = Field(..., min_length=1)
    current_time: Optional[datetime] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validation_request_must_be_secret_clean(self) -> Any:
        assert_approval_secret_clean(self.model_dump(mode="json"), "Approval validation request")
        return self

    @classmethod
    def from_approval_request(cls, request: Any, approval_ref: str) -> "ApprovalValidationRequest":
        return request.to_validation_request(approval_ref)


class ApprovalValidationDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"appr_dec_{uuid.uuid4().hex[:12]}")
    approval_ref: Optional[str] = None
    allowed: bool
    status: ApprovalDecisionStatus
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    matched_grant_ref: Optional[str] = None
    required_next_action: Optional[str] = None
    event_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def decision_must_be_secret_clean(self) -> Any:
        assert_approval_secret_clean(self.model_dump(mode="json"), "Approval validation decision")
        return self
