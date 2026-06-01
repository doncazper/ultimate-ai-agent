from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.remote_workers.enums import PrivateMeshProviderKind, RemoteTransportKind, RemoteTransportStatus
from ultimate_ai_agent.core.remote_workers.validation import assert_remote_secret_clean
from ultimate_ai_agent.core.time import utc_now


class RemoteTransportDescriptor(BaseModel):
    transport_id: str = Field(..., min_length=1)
    kind: RemoteTransportKind
    provider_kind: PrivateMeshProviderKind = PrivateMeshProviderKind.none
    status: RemoteTransportStatus = RemoteTransportStatus.disabled
    display_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    planned_only: bool = True
    enabled: bool = False
    requires_network: bool = False
    requires_credentials: bool = False
    supports_dispatch: bool = False
    supports_file_transfer: bool = False
    supports_subagents: bool = False
    trust_boundary: str = "metadata_only"
    owner: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def descriptor_must_be_safe(self):
        assert_remote_secret_clean(self.model_dump(mode="json"), "Remote transport descriptor")
        return self
