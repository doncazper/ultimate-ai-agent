from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from ultimate_ai_agent.core.tools.enums import (
    ToolCategory,
    ToolExecutionMode,
    ToolRiskLevel,
    ToolPermissionKind,
)
from ultimate_ai_agent.core.consent.enums import DataBoundary

class ToolPermissionManifest(BaseModel):
    required_permissions: List[ToolPermissionKind] = Field(default_factory=list)
    filesystem_roots: List[str] = Field(default_factory=list)
    network_domains: List[str] = Field(default_factory=list)
    credentials_keys: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

class ToolManifest(BaseModel):
    tool_id: str
    display_name: str
    category: ToolCategory
    description: str
    execution_mode: ToolExecutionMode
    risk_level: ToolRiskLevel
    input_schema_ref: Optional[str] = None
    output_schema_ref: Optional[str] = None
    permissions_required: List[ToolPermissionKind] = Field(default_factory=list)
    permission_manifest: Optional[ToolPermissionManifest] = None
    data_boundaries: List[DataBoundary] = Field(default_factory=list)
    requires_consent: bool = True
    requires_approval: bool = False
    supports_dry_run: bool = False
    supports_rollback: bool = False
    idempotency_required: bool = False
    foundation_gate_required: bool = False
    capability_flag: str
    owner: str
    source: str
    version: str
    event_refs: Optional[List[str]] = None

    model_config = ConfigDict(extra="forbid")

class DryRunPlan(BaseModel):
    plan_id: str
    tool_id: str
    estimated_risk: ToolRiskLevel
    steps: List[str] = Field(default_factory=list)
    side_effects_prevented: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
