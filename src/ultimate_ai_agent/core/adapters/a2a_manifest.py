from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class A2AAgentInterfaceV1(BaseModel):
    """Spec-shaped A2A 1.0 interface declaration parsed as inert metadata."""

    url: str
    protocol_binding: str = Field(alias="protocolBinding")
    protocol_version: str = Field(alias="protocolVersion")
    tenant: Optional[str] = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class A2AAgentProviderV1(BaseModel):
    organization: str
    url: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class A2AAgentCapabilitiesV1(BaseModel):
    streaming: bool = False
    push_notifications: bool = Field(default=False, alias="pushNotifications")
    extended_agent_card: bool = Field(default=False, alias="extendedAgentCard")
    extensions: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class A2AAgentSkillV1(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    input_modes: list[str] = Field(default_factory=list, alias="inputModes")
    output_modes: list[str] = Field(default_factory=list, alias="outputModes")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class A2AAgentCardV1(BaseModel):
    """Official A2A 1.0 Agent Card shape parsed for safe metadata import only.

    This model is not a transport client, does not discover cards, and does not
    authorize remote dispatch.
    """

    name: str
    description: str
    supported_interfaces: list[A2AAgentInterfaceV1] = Field(alias="supportedInterfaces")
    provider: Optional[A2AAgentProviderV1] = None
    icon_url: Optional[str] = Field(default=None, alias="iconUrl")
    version: str
    documentation_url: Optional[str] = Field(default=None, alias="documentationUrl")
    capabilities: A2AAgentCapabilitiesV1
    security_schemes: dict[str, dict[str, Any]] = Field(default_factory=dict, alias="securitySchemes")
    security: list[dict[str, Any]] = Field(default_factory=list)
    default_input_modes: list[str] = Field(default_factory=list, alias="defaultInputModes")
    default_output_modes: list[str] = Field(default_factory=list, alias="defaultOutputModes")
    skills: list[A2AAgentSkillV1]
    signatures: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class UAAA2AAgentCardMetadataImport(BaseModel):
    """UAA-local inert metadata import for external A2A-shaped agent data.

    Real delegation remains blocked.
    """

    agent_id: str
    schema_version: str = "uaa_a2a_agent_card_metadata_import.v1"
    name: str
    owner: str
    declared_capabilities: List[str] = Field(default_factory=list)
    endpoint_url: Optional[str] = None
    version: str

    model_config = ConfigDict(extra="forbid")


# Backwards-compatible import alias for older internal tests/docs. This is not
# an official A2A protocol Agent Card and must remain metadata-only.
A2AAgentCardMinimal = UAAA2AAgentCardMetadataImport
