from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ActorType(str, Enum):
    human_user = "human_user"
    orchestrator = "orchestrator"
    subagent = "subagent"
    scheduled_job = "scheduled_job"
    scanner = "scanner"
    tool_broker = "tool_broker"
    provider_adapter = "provider_adapter"
    system_worker = "system_worker"
    self_improvement_worker = "self_improvement_worker"
    admin = "admin"
    external_callback = "external_callback"

class AuthoritySource(str, Enum):
    explicit_user_request = "explicit_user_request"
    approved_execution_contract = "approved_execution_contract"
    active_consent_grant = "active_consent_grant"
    standing_approval = "standing_approval"
    admin_policy = "admin_policy"
    system_policy = "system_policy"
    foundation_test = "foundation_test"
    manual_operator_action = "manual_operator_action"

class ActorContext(BaseModel):
    actor_type: ActorType
    actor_id: str = Field(..., min_length=1)
    actor_display_name: Optional[str] = None
    on_behalf_of_user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    authority_source: AuthoritySource
    execution_contract_id: Optional[str] = None
    consent_ref: Optional[str] = None
    approval_ref: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
