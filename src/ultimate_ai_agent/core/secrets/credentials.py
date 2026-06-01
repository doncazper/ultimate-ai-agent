from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.secrets.enums import (
    CredentialAuthType,
    CredentialScope,
    CredentialStatus,
)


class CredentialReference(BaseModel):
    credential_ref: str = Field(..., min_length=1)
    provider_id: Optional[str] = None
    tool_id: Optional[str] = None
    auth_type: CredentialAuthType
    scope: CredentialScope
    owner_user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    status: CredentialStatus = CredentialStatus.pending
    allowed_purposes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    consent_ref: Optional[str] = None
    event_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class CredentialMetadata(BaseModel):
    credential_ref: str
    auth_type: CredentialAuthType
    scope: CredentialScope
    status: CredentialStatus
    provider_id: Optional[str] = None
    tool_id: Optional[str] = None
    owner_user_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class SecretAccessRequest(BaseModel):
    credential_ref: str
    requester_actor_id: str = "system"
    purpose: str
    provider_id: Optional[str] = None
    tool_id: Optional[str] = None
    consent_ref: Optional[str] = None
    policy_ref: Optional[str] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
