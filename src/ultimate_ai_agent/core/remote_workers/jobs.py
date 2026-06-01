from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.remote_workers.audit import RemoteAuditContext
from ultimate_ai_agent.core.remote_workers.enums import RemoteRiskLevel
from ultimate_ai_agent.core.remote_workers.validation import assert_remote_secret_clean
from ultimate_ai_agent.core.time import utc_now


class RemoteJobEnvelope(BaseModel):
    job_id: str = Field(..., min_length=1)
    correlation_id: str = Field(..., min_length=1)
    node_id: str = Field(..., min_length=1)
    transport_id: str = Field(..., min_length=1)
    task_summary: str = Field(..., min_length=1, max_length=500)
    requested_capabilities: List[str] = Field(default_factory=list)
    risk_level: RemoteRiskLevel = RemoteRiskLevel.safe
    audit_context: RemoteAuditContext
    input_refs: List[str] = Field(default_factory=list)
    policy_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def envelope_must_be_safe(self):
        if self.correlation_id != self.audit_context.correlation_id:
            raise ValueError("REMOTE_CORRELATION_ID_MISMATCH")
        assert_remote_secret_clean(self.task_summary, "Remote job task_summary")
        assert_remote_secret_clean(self.input_refs, "Remote job input_refs")
        assert_remote_secret_clean(self.metadata, "Remote job metadata")
        return self

