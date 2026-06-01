from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.approvals.validation import assert_approval_secret_clean
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.policies import DataClassification
from ultimate_ai_agent.core.time import utc_now


class ApprovalRequest(BaseModel):
    approval_request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    subject_type: ApprovalSubjectType
    subject_id: str = Field(..., min_length=1)
    actor_context: ActorContext
    requested_action: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=1)
    risk_level: ApprovalRiskLevel
    data_classification: DataClassification
    resource_refs: List[str] = Field(default_factory=list)
    tool_id: Optional[str] = None
    model_profile_id: Optional[str] = None
    runtime_request_id: Optional[str] = None
    provider_id: Optional[str] = None
    file_ref: Optional[str] = None
    cost_estimate_ref: Optional[str] = None
    consent_refs: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None
    trace_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def request_must_be_secret_clean(self):
        assert_approval_secret_clean(self.model_dump(mode="json"), "Approval request")
        return self

    def to_validation_request(self, approval_ref: str) -> ApprovalValidationRequest:
        return ApprovalValidationRequest(
            approval_ref=approval_ref,
            run_id=self.run_id,
            subject_type=self.subject_type,
            subject_id=self.subject_id,
            requested_action=self.requested_action,
            actor_context=self.actor_context,
            resource_refs=self.resource_refs,
            risk_level=self.risk_level,
            data_classification=self.data_classification,
            purpose=self.purpose,
            event_ref=self.event_ref,
        )
