from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.remote_workers.enums import RemoteNodeStatus, RemoteOutputTrustLevel
from ultimate_ai_agent.core.remote_workers.validation import assert_remote_secret_clean
from ultimate_ai_agent.core.time import utc_now


class NodeIdentity(BaseModel):
    node_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    labels: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def identity_must_be_safe(self):
        assert_remote_secret_clean(self.model_dump(mode="json"), "Remote node identity")
        return self


class NodeCapabilitySet(BaseModel):
    can_execute_jobs: bool = False
    can_launch_subagents: bool = False
    can_call_tools: bool = False
    can_use_sandbox: bool = False
    can_access_network: bool = False
    can_access_personal_data: bool = False
    can_write_files: bool = False
    can_send_messages: bool = False
    can_approve_actions: bool = False
    can_run_critical: bool = False
    supports_background: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def capability_set_must_not_enable_blocked_authority(self):
        if self.can_approve_actions is True:
            raise ValueError("REMOTE_APPROVAL_CAPABILITY_DENIED")
        if self.can_run_critical is True:
            raise ValueError("REMOTE_CRITICAL_CAPABILITY_DENIED")
        return self


class RemoteNode(BaseModel):
    node_id: str = Field(..., min_length=1)
    identity: NodeIdentity
    status: RemoteNodeStatus = RemoteNodeStatus.unknown
    capabilities: NodeCapabilitySet = Field(default_factory=NodeCapabilitySet)
    allowed_transport_ids: List[str] = Field(default_factory=list)
    trust_level: RemoteOutputTrustLevel = RemoteOutputTrustLevel.untrusted_remote_output
    created_at: datetime = Field(default_factory=utc_now)
    event_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def node_must_be_safe(self):
        if self.node_id != self.identity.node_id:
            raise ValueError("REMOTE_NODE_IDENTITY_MISMATCH")
        assert_remote_secret_clean(self.model_dump(mode="json"), "Remote node")
        return self

