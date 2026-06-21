import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.enums import ApprovalStatus, ApprovalSubjectType
from ultimate_ai_agent.core.approvals.grants import ApprovalGrant
from ultimate_ai_agent.core.approvals.validation import assert_approval_secret_clean
from ultimate_ai_agent.core.time import utc_now


class ApprovalReceipt(BaseModel):
    receipt_id: str = Field(default_factory=lambda: f"appr_rcpt_{uuid.uuid4().hex[:12]}")
    approval_ref: str = Field(..., min_length=1)
    approval_request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    subject_type: ApprovalSubjectType
    subject_id: str = Field(..., min_length=1)
    status: ApprovalStatus
    approved_actions: List[str] = Field(default_factory=list)
    approved_resource_refs: List[str] = Field(default_factory=list)
    approved_by_actor_id: str = Field(..., min_length=1)
    granted_to_actor_id: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    reason_codes: List[str] = Field(default_factory=list)
    redactions_applied: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @classmethod
    def from_grant(cls, grant: ApprovalGrant, reason_codes: list[str] | None = None) -> "ApprovalReceipt":
        return cls(
            approval_ref=grant.approval_ref,
            approval_request_id=grant.approval_request_id,
            run_id=grant.run_id,
            subject_type=grant.subject_type,
            subject_id=grant.subject_id,
            status=grant.status,
            approved_actions=grant.approved_actions,
            approved_resource_refs=grant.approved_resource_refs,
            approved_by_actor_id=grant.approved_by_actor_id,
            granted_to_actor_id=grant.granted_to_actor_id,
            created_at=grant.created_at,
            expires_at=grant.expires_at,
            revoked_at=grant.revoked_at,
            reason_codes=reason_codes or [],
            redactions_applied=[],
            event_ref=grant.event_ref,
        )

    @model_validator(mode="after")
    def receipt_must_be_secret_clean(self) -> Any:
        assert_approval_secret_clean(self.model_dump(mode="json"), "Approval receipt")
        return self
