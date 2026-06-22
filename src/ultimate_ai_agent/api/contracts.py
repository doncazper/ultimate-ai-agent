from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiRouteSideEffectClass(str, Enum):
    none = "none"
    validation_only = "validation_only"
    local_dev_workspace_only = "local_dev_workspace_only"
    governed_network_read_only = "governed_network_read_only"


class ApiRouteClassification(str, Enum):
    public_metadata = "public_metadata"
    local_readonly = "local_readonly"
    local_sensitive = "local_sensitive"
    mutating_requires_authority = "mutating_requires_authority"


class ApiRouteAuthPosture(str, Enum):
    public_metadata_no_auth = "public_metadata_no_auth"
    protected_local_bearer_required = "protected_local_bearer_required"


class ApiRouteApprovalPosture(str, Enum):
    not_required_for_route_classification = "not_required_for_route_classification"
    required_before_mutation_authority = "required_before_mutation_authority"


class ApiRouteIdempotencyPosture(str, Enum):
    not_required_for_route_classification = "not_required_for_route_classification"
    required_before_mutation_authority = "required_before_mutation_authority"


class ApiRouteRateLimitPosture(str, Enum):
    not_targeted_for_route = "not_targeted_for_route"
    targeted_local_fixed_window = "targeted_local_fixed_window"


class ApiRouteInventoryItem(BaseModel):
    path: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    operation_id: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    summary: str = Field(..., min_length=1)
    validation_only: bool
    side_effect_class: ApiRouteSideEffectClass
    route_classification: ApiRouteClassification
    protected_route: bool
    auth_posture: ApiRouteAuthPosture
    approval_posture: ApiRouteApprovalPosture
    classification_reason: str = Field(..., min_length=1)
    idempotency_required: bool
    idempotency_posture: ApiRouteIdempotencyPosture
    idempotency_policy_ref: Optional[str] = None
    idempotency_reason: str = Field(..., min_length=1)
    rate_limit_targeted: bool
    rate_limit_posture: ApiRouteRateLimitPosture
    rate_limit_policy_ref: Optional[str] = None
    rate_limit_group: Optional[str] = None
    rate_limit_reason: str = Field(..., min_length=1)
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
    route_classification_vocabulary: List[ApiRouteClassification] = Field(default_factory=list)
    route_classification_summary: dict[str, int] = Field(default_factory=dict)
    route_auth_posture_summary: dict[str, int] = Field(default_factory=dict)
    route_approval_posture_summary: dict[str, int] = Field(default_factory=dict)
    idempotency_audit_policy_ref: Optional[str] = None
    route_idempotency_posture_summary: dict[str, int] = Field(default_factory=dict)
    rate_limit_policy_ref: Optional[str] = None
    route_rate_limit_posture_summary: dict[str, int] = Field(default_factory=dict)
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
