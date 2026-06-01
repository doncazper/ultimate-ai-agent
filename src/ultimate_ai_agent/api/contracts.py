from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiRouteSideEffectClass(str, Enum):
    none = "none"
    validation_only = "validation_only"
    local_dev_workspace_only = "local_dev_workspace_only"


class ApiRouteInventoryItem(BaseModel):
    path: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    operation_id: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    summary: str = Field(..., min_length=1)
    validation_only: bool
    side_effect_class: ApiRouteSideEffectClass
    requires_auth_future: bool = True
    blocked_from_production: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class ApiManifest(BaseModel):
    title: str = Field(..., min_length=1)
    api_version: str = Field(..., min_length=1)
    package_version: str = Field(..., min_length=1)
    active_baseline: str = Field(..., min_length=1)
    route_count: int = Field(..., ge=0)
    route_groups: List[str] = Field(default_factory=list)
    routes: List[ApiRouteInventoryItem] = Field(default_factory=list)
    foundation_gate_status: Optional[str] = None
    capabilities_declared: List[str] = Field(default_factory=list)
    capabilities_blocked: List[str] = Field(default_factory=list)
    no_runtime_integrations: bool = True

    model_config = ConfigDict(extra="forbid")


class ApiContractStatus(BaseModel):
    version_consistent: bool
    openapi_generated: bool
    route_inventory_valid: bool
    operation_ids_unique: bool
    unsafe_routes_detected: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")
