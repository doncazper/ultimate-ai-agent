from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from ultimate_ai_agent.core.tools.enums import ToolDecisionStatus, ToolRiskLevel
from ultimate_ai_agent.core.tools.manifests import DryRunPlan

class ToolDecision(BaseModel):
    decision_id: str
    request_id: str
    tool_id: str
    status: ToolDecisionStatus
    risk_level: ToolRiskLevel
    approval_required: bool = False
    consent_required: bool = False
    missing_permissions: List[str] = Field(default_factory=list)
    matched_consent_refs: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    event_ref: Optional[str] = None
    rollback_required: bool = False
    dry_run_plan: Optional[DryRunPlan] = None
    redactions_applied: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")

class ToolResult(BaseModel):
    result_id: str
    request_id: str
    status: str  # success, failure, dry_run_success, blocked
    redacted_output: str
    event_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

class ToolAuditMetadata(BaseModel):
    audit_id: str
    decision_id: str
    actor_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    actions_checked: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
