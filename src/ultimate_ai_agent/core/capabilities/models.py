from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Type

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityHealthStatus,
    CapabilityKind,
    CoordinationMode,
    PolicyDecisionStatus,
    RiskLevel as CoordinationRiskLevel,
    SideEffectLevel,
    TaskNodeStatus,
)


CAPABILITY_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
CAPABILITY_SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")
KNOWN_CAPABILITY_SOURCES = {"python", "internal", "mcp", "openapi", "langchain", "pydantic_ai", "other"}
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|client[_-]?secret|auth[_-]?token|secret|token|password)\s*="
    r"(?:['\"][A-Za-z0-9_\-\.\:/]{12,}['\"]|[A-Za-z0-9_\-\.\:/]{16,})"
)


class RiskLevel(str, Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    EXTERNAL_NETWORK = "external_network"
    SHELL = "shell"
    SECRET_ACCESS = "secret_access"
    safe = "safe"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"


class CapabilityPolicy(BaseModel):
    allowed_agents: set[str] = Field(default_factory=set)
    required_scopes: set[str] = Field(default_factory=set)
    risk: RiskLevel = RiskLevel.READ_ONLY
    requires_approval: bool = False
    timeout_s: float = Field(30.0, gt=0)
    max_retries: int = Field(0, ge=0)
    rate_limit_key: str | None = None
    idempotent: bool = True
    redact_output: bool = False
    sandbox_required: bool = False

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    @field_validator("allowed_agents")
    @classmethod
    def validate_allowed_agents(cls, value: set[str]) -> set[str]:
        for item in value:
            if not item or not CAPABILITY_NAME_PATTERN.fullmatch(item):
                raise ValueError("capability policy labels must use letters, numbers, underscore, hyphen, or dot")
        return value

    @field_validator("required_scopes")
    @classmethod
    def validate_required_scopes(cls, value: set[str]) -> set[str]:
        for item in value:
            if not item or not CAPABILITY_SCOPE_PATTERN.fullmatch(item):
                raise ValueError("capability scopes must use letters, numbers, underscore, hyphen, colon, or dot")
        return value


class CapabilitySpec(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    tags: set[str] = Field(default_factory=set)
    input_schema: dict[str, Any] = Field(default_factory=lambda: {"type": "object", "additionalProperties": True})
    output_schema: dict[str, Any] | None = None
    policy: CapabilityPolicy = Field(default_factory=CapabilityPolicy)
    source: str = "python"
    metadata: dict[str, Any] = Field(default_factory=dict)
    callable_ref: str | None = None
    instructions: str | None = None
    examples: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not CAPABILITY_NAME_PATTERN.fullmatch(value):
            raise ValueError("capability name must use letters, numbers, underscore, hyphen, or dot")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: set[str]) -> set[str]:
        for item in value:
            if not item or not CAPABILITY_NAME_PATTERN.fullmatch(item):
                raise ValueError("capability tags must use letters, numbers, underscore, hyphen, or dot")
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        if not value:
            raise ValueError("capability source is required")
        return value

    @field_validator("instructions")
    @classmethod
    def validate_instructions(cls, value: str | None) -> str | None:
        if value is not None and SECRET_PATTERN.search(value):
            raise ValueError("capability instructions must not contain secret-like values")
        return value

    @model_validator(mode="after")
    def validate_schema_shapes(self):
        if not isinstance(self.input_schema, dict):
            raise ValueError("capability input_schema must be a mapping")
        if self.output_schema is not None and not isinstance(self.output_schema, dict):
            raise ValueError("capability output_schema must be a mapping")
        return self

    def model_facing_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json", exclude={"callable_ref", "metadata"})
        data["policy"] = {
            "risk": self.policy.risk.value,
            "requires_approval": self.policy.requires_approval,
            "required_scopes": sorted(self.policy.required_scopes),
        }
        data["tags"] = sorted(self.tags)
        return data


class CapabilityResult(BaseModel):
    capability_name: str
    ok: bool
    content: str | None = None
    structured_content: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def success(
        cls,
        capability_name: str,
        *,
        content: str | None = None,
        structured_content: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "CapabilityResult":
        return cls(
            capability_name=capability_name,
            ok=True,
            content=content,
            structured_content=structured_content,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        capability_name: str,
        *,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> "CapabilityResult":
        return cls(capability_name=capability_name, ok=False, error=error, metadata=metadata or {})


class CapabilityRunContext(BaseModel):
    agent_name: str = "default"
    user_scopes: set[str] = Field(default_factory=set)
    approval_ref: str | None = None
    trace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


@dataclass(frozen=True)
class CapabilityRegistration:
    spec: CapabilitySpec
    fn: Callable[..., Any] | None = None
    input_model: Type[BaseModel] | None = None
    output_model: Type[BaseModel] | None = None


@dataclass(frozen=True)
class CapabilityPack:
    name: str
    version: str = "1.0.0"
    capabilities: tuple[CapabilityRegistration | CapabilitySpec, ...] = ()


_SIDE_EFFECT_RANK: dict[SideEffectLevel, int] = {
    SideEffectLevel.none: 0,
    SideEffectLevel.read: 1,
    SideEffectLevel.write: 2,
    SideEffectLevel.external: 3,
    SideEffectLevel.destructive: 4,
}

_COORDINATION_RISK_RANK: dict[CoordinationRiskLevel, int] = {
    CoordinationRiskLevel.safe: 0,
    CoordinationRiskLevel.low: 1,
    CoordinationRiskLevel.medium: 2,
    CoordinationRiskLevel.high: 3,
    CoordinationRiskLevel.critical: 4,
    CoordinationRiskLevel.forbidden: 5,
}


def side_effect_rank(level: SideEffectLevel) -> int:
    return _SIDE_EFFECT_RANK[level]


def risk_rank(level: CoordinationRiskLevel) -> int:
    return _COORDINATION_RISK_RANK[level]


def is_read_only_side_effect(level: SideEffectLevel) -> bool:
    return side_effect_rank(level) <= side_effect_rank(SideEffectLevel.read)


def is_mutating_side_effect(level: SideEffectLevel) -> bool:
    return side_effect_rank(level) >= side_effect_rank(SideEffectLevel.write)


def _assert_secret_clean(value: Any, label: str) -> None:
    if _scan_payload_for_secrets(value):
        raise ValueError(f"{label} contains secret-like content.")


def _scan_payload_for_secrets(value: Any) -> bool:
    if isinstance(value, str):
        return bool(SECRET_PATTERN.search(value))
    if isinstance(value, dict):
        return any(_scan_payload_for_secrets(key) or _scan_payload_for_secrets(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_scan_payload_for_secrets(item) for item in value)
    return False


class _CoordinatorCapabilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ContextPolicy(_CoordinatorCapabilityModel):
    required_context_keys: list[str] = Field(default_factory=list)
    optional_context_keys: list[str] = Field(default_factory=list)
    max_context_refs: int = Field(default=20, ge=0)
    allow_memory_refs: bool = True
    allow_raw_content: bool = False
    require_task_envelope: bool = True
    compaction_supported: bool = True
    notes_supported: bool = True

    @model_validator(mode="after")
    def validate_context_policy(self):
        if self.allow_raw_content:
            raise ValueError("Capability context policy must not allow raw content by default.")
        _assert_secret_clean(self.model_dump(mode="json"), "context_policy")
        return self


class RuntimePolicy(_CoordinatorCapabilityModel):
    timeout_seconds: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=0, ge=0, le=5)
    max_concurrency: int = Field(default=1, ge=1)
    max_input_tokens: int | None = Field(default=None, ge=0)
    max_output_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    estimated_latency_ms: float | None = Field(default=None, ge=0)
    deterministic: bool = False


class SafetyPolicy(_CoordinatorCapabilityModel):
    allow_parallel: bool = False
    require_single_writer: bool = False
    approval_required: bool = False
    deny_untrusted_context: bool = True
    deny_if_unhealthy: bool = True
    deny_if_deprecated: bool = True
    max_risk_level: CoordinationRiskLevel = CoordinationRiskLevel.medium
    max_side_effect_level: SideEffectLevel = SideEffectLevel.read


class QualitySignals(_CoordinatorCapabilityModel):
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    success_rate: float | None = Field(default=None, ge=0, le=1)
    freshness_score: float | None = Field(default=None, ge=0, le=1)
    test_coverage_refs: list[str] = Field(default_factory=list)
    owner_reviewed: bool = False
    deprecated: bool = False

    @model_validator(mode="after")
    def validate_quality(self):
        _assert_secret_clean(self.model_dump(mode="json"), "quality")
        return self


class CapabilityManifest(_CoordinatorCapabilityModel):
    id: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    kind: CapabilityKind
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    long_description: str | None = None
    owner: str | None = None
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    anti_examples: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    input_modes: list[str] = Field(default_factory=list)
    output_modes: list[str] = Field(default_factory=list)
    side_effects: SideEffectLevel = SideEffectLevel.none
    risk_level: CoordinationRiskLevel = CoordinationRiskLevel.low
    approval_required: bool | str | None = None
    auth_scopes: list[str] = Field(default_factory=list)
    data_classes: list[str] = Field(default_factory=list)
    sandbox_profile: str | None = None
    allowed_coordination_modes: list[CoordinationMode] = Field(default_factory=list)
    concurrency_safe: bool = False
    single_writer_required: bool = False
    dependencies: list[str] = Field(default_factory=list)
    conflicts_with: list[str] = Field(default_factory=list)
    context_policy: ContextPolicy = Field(default_factory=ContextPolicy)
    runtime_policy: RuntimePolicy = Field(default_factory=RuntimePolicy)
    safety: SafetyPolicy = Field(default_factory=SafetyPolicy)
    quality: QualitySignals = Field(default_factory=QualitySignals)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tags", "examples", "anti_examples", "input_modes", "output_modes", "auth_scopes", "data_classes")
    @classmethod
    def strip_blank_items(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value and value.strip()]

    @model_validator(mode="after")
    def validate_manifest(self):
        _assert_secret_clean(self.model_dump(mode="json"), "capability_manifest")
        if not self.examples:
            raise ValueError("Capability manifests require at least one positive example.")
        if not self.anti_examples:
            raise ValueError("Capability manifests require at least one anti-example.")
        if not self.input_schema:
            raise ValueError("Capability manifests require an input_schema.")
        if not self.output_schema:
            raise ValueError("Capability manifests require an output_schema.")
        if not self.input_modes:
            raise ValueError("Capability manifests require input_modes.")
        if not self.output_modes:
            raise ValueError("Capability manifests require output_modes.")
        if not self.allowed_coordination_modes:
            raise ValueError("Capability manifests require allowed_coordination_modes.")
        if self.risk_level == CoordinationRiskLevel.forbidden:
            raise ValueError("Forbidden capabilities cannot be registered.")
        if is_mutating_side_effect(self.side_effects) and not self.single_writer_required:
            raise ValueError("Mutating capabilities must require single-writer coordination.")
        if is_mutating_side_effect(self.side_effects) and not self.safety.require_single_writer:
            raise ValueError("Mutating capabilities must set safety.require_single_writer.")
        if self.approval_required and self.risk_level in {CoordinationRiskLevel.safe, CoordinationRiskLevel.low}:
            if isinstance(self.approval_required, bool):
                raise ValueError("Low-risk approval requirements must include a reason string.")
        return self


class CapabilityCatalogEntry(_CoordinatorCapabilityModel):
    id: str
    kind: CapabilityKind
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    anti_examples: list[str] = Field(default_factory=list)
    input_modes: list[str] = Field(default_factory=list)
    output_modes: list[str] = Field(default_factory=list)
    side_effects: SideEffectLevel
    risk_level: CoordinationRiskLevel
    allowed_coordination_modes: list[CoordinationMode] = Field(default_factory=list)
    concurrency_safe: bool = False
    single_writer_required: bool = False
    approval_required: bool | str | None = None
    auth_scopes: list[str] = Field(default_factory=list)
    deprecated: bool = False
    health_status: CapabilityHealthStatus = CapabilityHealthStatus.unknown
    score: float = 0.0
    reason_codes: list[str] = Field(default_factory=list)

    @classmethod
    def from_manifest(
        cls,
        manifest: CapabilityManifest,
        *,
        health_status: CapabilityHealthStatus = CapabilityHealthStatus.unknown,
        score: float = 0.0,
        reason_codes: list[str] | None = None,
    ) -> "CapabilityCatalogEntry":
        return cls(
            id=manifest.id,
            kind=manifest.kind,
            name=manifest.name,
            description=manifest.description,
            tags=list(manifest.tags),
            examples=list(manifest.examples[:2]),
            anti_examples=list(manifest.anti_examples[:2]),
            input_modes=list(manifest.input_modes),
            output_modes=list(manifest.output_modes),
            side_effects=manifest.side_effects,
            risk_level=manifest.risk_level,
            allowed_coordination_modes=list(manifest.allowed_coordination_modes),
            concurrency_safe=manifest.concurrency_safe,
            single_writer_required=manifest.single_writer_required,
            approval_required=manifest.approval_required,
            auth_scopes=list(manifest.auth_scopes),
            deprecated=manifest.quality.deprecated,
            health_status=health_status,
            score=score,
            reason_codes=reason_codes or [],
        )


class TaskEnvelope(_CoordinatorCapabilityModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    user_request: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    background: str | None = None
    scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    selected_capability_ids: list[str] = Field(default_factory=list)
    allowed_tool_ids: list[str] = Field(default_factory=list)
    required_output_schema: dict[str, Any] | None = None
    acceptance_criteria: list[str] = Field(default_factory=list)
    budget: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    memory_refs: list[str] = Field(default_factory=list)
    parent_trace_id: str | None = None

    @model_validator(mode="after")
    def validate_envelope(self):
        _assert_secret_clean(self.model_dump(mode="json"), "task_envelope")
        return self


class TaskNode(_CoordinatorCapabilityModel):
    node_id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:12]}")
    capability_id: str = Field(..., min_length=1)
    mode: CoordinationMode
    envelope: TaskEnvelope
    depends_on: list[str] = Field(default_factory=list)
    parallel_group: str | None = None
    expected_side_effects: SideEffectLevel = SideEffectLevel.none
    risk_level: CoordinationRiskLevel = CoordinationRiskLevel.low
    requires_approval: bool = False
    approval_ref: str | None = None
    status: TaskNodeStatus = TaskNodeStatus.pending
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_node(self):
        _assert_secret_clean(self.model_dump(mode="json"), "task_node")
        return self


class TaskPlan(_CoordinatorCapabilityModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    user_request: str = Field(..., min_length=1)
    nodes: list[TaskNode] = Field(..., min_length=1)
    coordinator_capability_id: str = "coordinator:central"
    final_synthesis_required: bool = True
    single_writer_node_id: str | None = None
    safe_summary: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_plan(self):
        _assert_secret_clean(self.model_dump(mode="json"), "task_plan")
        mutating_nodes = [node for node in self.nodes if is_mutating_side_effect(node.expected_side_effects)]
        if len(mutating_nodes) == 1 and self.single_writer_node_id is None:
            self.single_writer_node_id = mutating_nodes[0].node_id
        return self


class Artifact(_CoordinatorCapabilityModel):
    artifact_id: str = Field(default_factory=lambda: f"artifact_{uuid.uuid4().hex[:12]}")
    producer_capability_id: str = Field(..., min_length=1)
    kind: str = Field(..., min_length=1)
    content: Any
    summary: str = Field(..., min_length=1)
    citations_or_refs: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    side_effects_performed: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_artifact(self):
        _assert_secret_clean(self.model_dump(mode="json"), "artifact")
        return self


class CapabilitySelection(_CoordinatorCapabilityModel):
    selection_id: str = Field(default_factory=lambda: f"selection_{uuid.uuid4().hex[:12]}")
    query: str = Field(..., min_length=1)
    selected_capability_ids: list[str] = Field(default_factory=list)
    rejected_capability_ids: list[str] = Field(default_factory=list)
    candidate_scores: dict[str, float] = Field(default_factory=dict)
    selector_kind: str = "deterministic"
    reason_codes: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)
    requires_manifest_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_selection(self):
        _assert_secret_clean(self.model_dump(mode="json"), "capability_selection")
        return self


class CapabilitySearchFilters(_CoordinatorCapabilityModel):
    kinds: list[CapabilityKind] | None = None
    input_modes: list[str] | None = None
    output_modes: list[str] | None = None
    allowed_coordination_modes: list[CoordinationMode] | None = None
    required_auth_scopes: list[str] = Field(default_factory=list)
    max_side_effects: SideEffectLevel = SideEffectLevel.destructive
    max_risk_level: CoordinationRiskLevel = CoordinationRiskLevel.critical
    require_concurrency_safe: bool = False
    require_read_only: bool = False
    include_unhealthy: bool = False
    include_deprecated: bool = False
    tenant_id: str | None = None
    user_id: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class CapabilityHealthReport(_CoordinatorCapabilityModel):
    capability_id: str
    status: CapabilityHealthStatus
    reason_codes: list[str] = Field(default_factory=list)
    latency_ms: float | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyDecision(_CoordinatorCapabilityModel):
    status: PolicyDecisionStatus
    allowed: bool = False
    requires_approval: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    capability_id: str | None = None
    task_id: str | None = None


class TelemetryEvent(_CoordinatorCapabilityModel):
    event_id: str = Field(default_factory=lambda: f"cap_event_{uuid.uuid4().hex[:12]}")
    event_name: str = Field(..., min_length=1)
    trace_id: str | None = None
    capability_id: str | None = None
    task_id: str | None = None
    success: bool | None = None
    reason_codes: list[str] = Field(default_factory=list)
    latency_ms: float | None = Field(default=None, ge=0)
    estimated_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
