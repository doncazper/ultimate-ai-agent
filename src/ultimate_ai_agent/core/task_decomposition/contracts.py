from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.task_decomposition.enums import (
    AmbiguityLevel,
    CapabilityCallStatus,
    CapabilityKind,
    CapabilityOutcomeStatus,
    CostHint,
    DAGExecutionStatus,
    DataSensitivity,
    ExecutionMode,
    ComplexityLevel,
    NodeExecutionStatus,
    PlanStrategy,
    PlanValidationStatus,
    RiskLevel,
    TaskNodeStrategy,
)
from ultimate_ai_agent.core.time import utc_now


RISK_RANK: dict[RiskLevel, int] = {
    RiskLevel.low: 1,
    RiskLevel.medium: 2,
    RiskLevel.high: 3,
    RiskLevel.critical: 4,
}

SENSITIVITY_RANK: dict[DataSensitivity, int] = {
    DataSensitivity.public: 1,
    DataSensitivity.internal: 2,
    DataSensitivity.private: 3,
    DataSensitivity.secret: 4,
}

SAFE_EXECUTION_MODES = {
    ExecutionMode.python_callable,
    ExecutionMode.agent_as_tool,
    ExecutionMode.workflow,
}


def risk_rank(value: RiskLevel) -> int:
    return RISK_RANK[RiskLevel(value)]


def sensitivity_rank(value: DataSensitivity) -> int:
    return SENSITIVITY_RANK[DataSensitivity(value)]


def permission_requires_approval(permission: str) -> bool:
    lowered = permission.lower()
    markers = (
        "write",
        "delete",
        "mutate",
        "shell",
        "subprocess",
        "network",
        "external",
        "api",
        "private",
        "secret",
        "credential",
        "publish",
        "send",
        "spend",
    )
    return any(marker in lowered for marker in markers)


class CapabilityRoutingCard(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    kind: CapabilityKind
    summary: str = Field(..., min_length=1)
    use_when: List[str] = Field(default_factory=list)
    do_not_use_when: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    input_hints: List[str] = Field(default_factory=list)
    output_hints: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.low
    requires_approval: bool = False
    typical_latency_ms: Optional[int] = Field(default=None, ge=0)
    cost_hint: CostHint = CostHint.free
    reliability_score: float = Field(default=1.0, ge=0.0, le=1.0)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def high_risk_requires_approval(self):
        if self.risk_level in {RiskLevel.high, RiskLevel.critical} and not self.requires_approval:
            raise ValueError("HIGH_RISK_CAPABILITY_REQUIRES_APPROVAL")
        return self


class CapabilityContract(BaseModel):
    card: CapabilityRoutingCard
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    side_effects: List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    data_sensitivity: DataSensitivity = DataSensitivity.public
    execution_mode: ExecutionMode = ExecutionMode.python_callable
    handler_ref: Optional[str] = None
    timeout_s: int = Field(default=30, ge=1)
    retry_policy: Dict[str, Any] = Field(default_factory=lambda: {"max_attempts": 1, "backoff_s": 0.0})
    cache_policy: Dict[str, Any] = Field(default_factory=dict)
    concurrency_limit: int = Field(default=1, ge=1)
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    healthcheck_ref: Optional[str] = None
    eval_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def risky_permissions_require_approval(self):
        if any(permission_requires_approval(permission) for permission in self.required_permissions):
            if not self.card.requires_approval:
                raise ValueError("DANGEROUS_PERMISSION_REQUIRES_APPROVAL")
        if self.data_sensitivity in {DataSensitivity.private, DataSensitivity.secret} and not self.card.requires_approval:
            raise ValueError("PRIVATE_DATA_CAPABILITY_REQUIRES_APPROVAL")
        if any(effect for effect in self.side_effects if effect.lower() not in {"none", "no_effect", "read_only"}):
            if not self.card.requires_approval:
                raise ValueError("SIDE_EFFECTING_CAPABILITY_REQUIRES_APPROVAL")
        return self


class CapabilityOutcomeMetrics(BaseModel):
    capability_id: str
    total_calls: int = Field(default=0, ge=0)
    succeeded: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    approval_required: int = Field(default=0, ge=0)
    validation_failed: int = Field(default=0, ge=0)
    average_latency_ms: Optional[float] = Field(default=None, ge=0)
    last_summary: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return self.succeeded / self.total_calls


class CapabilityOutcomeRecord(BaseModel):
    capability_id: str
    status: CapabilityOutcomeStatus
    latency_ms: Optional[float] = Field(default=None, ge=0)
    safe_summary: str = Field(..., min_length=1)
    reason_codes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")


class CapabilityRankScore(BaseModel):
    capability_id: str
    total_score: float
    semantic_score: float = 0.0
    schema_score: float = 0.0
    tag_domain_score: float = 0.0
    historical_score: float = 0.0
    cost_latency_score: float = 0.0
    permission_score: float = 0.0
    risk_score: float = 0.0
    reason_codes: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class CapabilityCallContext(BaseModel):
    run_id: str = Field(default="task-decomposition-run:local")
    actor_id: str = Field(default="local_actor")
    max_risk_level: RiskLevel = RiskLevel.medium
    allowed_permissions: List[str] = Field(
        default_factory=lambda: ["read", "validate", "summarize", "compute", "workflow"]
    )
    data_sensitivity_ceiling: DataSensitivity = DataSensitivity.internal
    approved_capability_ids: List[str] = Field(default_factory=list)
    approval_refs: Dict[str, str] = Field(default_factory=dict)
    dry_run: bool = False
    budget: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    def is_approved(self, capability_id: str) -> bool:
        return capability_id in set(self.approved_capability_ids)


class CapabilityCallValidationResult(BaseModel):
    capability_id: str
    valid: bool
    status: CapabilityCallStatus
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str
    approval_required: bool = False

    model_config = ConfigDict(extra="forbid")


class CapabilityCallResult(BaseModel):
    capability_id: str
    status: CapabilityCallStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    observations: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    attempts: int = Field(default=1, ge=0)
    latency_ms: Optional[float] = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid")


class TaskIntent(BaseModel):
    goal: str = Field(..., min_length=1)
    raw_request: str = Field(..., min_length=1)
    constraints: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    ambiguity_level: AmbiguityLevel = AmbiguityLevel.low
    complexity: ComplexityLevel = ComplexityLevel.simple
    risk_level: RiskLevel = RiskLevel.low
    expected_output: Optional[str] = None
    success_criteria: List[str] = Field(default_factory=list)
    budget: Dict[str, Any] = Field(default_factory=dict)
    requires_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class TaskNode(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    depends_on: List[str] = Field(default_factory=list)
    decomposition_strategy: TaskNodeStrategy = TaskNodeStrategy.direct
    candidate_capabilities: List[str] = Field(default_factory=list)
    selected_capability: Optional[str] = None
    input_bindings: Dict[str, Any] = Field(default_factory=dict)
    expected_output_schema: Optional[Dict[str, Any]] = None
    success_criteria: List[str] = Field(default_factory=list)
    failure_modes: List[str] = Field(default_factory=list)
    fallback_node_ids: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.low
    requires_approval: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def selected_capability_must_be_candidate(self):
        if self.selected_capability and self.selected_capability not in self.candidate_capabilities:
            raise ValueError("SELECTED_CAPABILITY_NOT_IN_CANDIDATES")
        if self.risk_level in {RiskLevel.high, RiskLevel.critical} and not self.requires_approval:
            raise ValueError("HIGH_RISK_TASK_NODE_REQUIRES_APPROVAL")
        return self


class TaskPlan(BaseModel):
    plan_id: str = Field(..., min_length=1)
    goal: str = Field(..., min_length=1)
    assumptions: List[str] = Field(default_factory=list)
    non_goals: List[str] = Field(default_factory=list)
    strategy: PlanStrategy = PlanStrategy.direct
    nodes: List[TaskNode] = Field(..., min_length=1)
    final_success_criteria: List[str] = Field(default_factory=list)
    max_iterations: int = Field(default=1, ge=1)
    budget: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class PlanValidationIssue(BaseModel):
    node_id: Optional[str] = None
    reason_code: str
    safe_message: str

    model_config = ConfigDict(extra="forbid")


class PlanValidationContext(BaseModel):
    max_nodes: int = Field(default=100, ge=1)
    max_iterations: int = Field(default=10, ge=1)
    max_budget: Dict[str, float] = Field(default_factory=dict)
    call_context: CapabilityCallContext = Field(default_factory=CapabilityCallContext)

    model_config = ConfigDict(extra="forbid")


class PlanValidationResult(BaseModel):
    plan_id: str
    valid: bool
    status: PlanValidationStatus
    reason_codes: List[str] = Field(default_factory=list)
    issues: List[PlanValidationIssue] = Field(default_factory=list)
    safe_message: str
    approval_required_node_ids: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class NodeExecutionRecord(BaseModel):
    node_id: str
    status: NodeExecutionStatus
    selected_capability: Optional[str] = None
    attempts: int = Field(default=0, ge=0)
    output: Dict[str, Any] = Field(default_factory=dict)
    observations: List[str] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")


class TaskDecompositionDurableBinding(BaseModel):
    run_id: str = Field(..., min_length=1)
    durable_run_ref: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    generation: int = Field(..., ge=0)
    audit_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    replay_refs: List[str] = Field(default_factory=list)
    rollback_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    approval_refs: List[str] = Field(default_factory=list)
    handler_refs: List[str] = Field(default_factory=list)
    idempotency_keys_seen: List[str] = Field(default_factory=list)
    restart_refs: List[str] = Field(default_factory=list)
    replay_validation_ref: Optional[str] = None
    duplicate_mutation_denied: bool = False
    no_runtime_authority: bool = True
    safe_summary: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class DAGExecutionResult(BaseModel):
    plan_id: str
    status: DAGExecutionStatus
    node_records: List[NodeExecutionRecord] = Field(default_factory=list)
    outputs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    reason_codes: List[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    repair_requested: bool = False
    repair_node_ids: List[str] = Field(default_factory=list)
    durable_binding: Optional[TaskDecompositionDurableBinding] = None

    model_config = ConfigDict(extra="forbid")


class ReflectionRecord(BaseModel):
    reflection_id: str
    plan_id: str
    node_id: Optional[str] = None
    capability_id: Optional[str] = None
    safe_summary: str = Field(..., min_length=1)
    reason_codes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")


class PromotionCandidate(BaseModel):
    candidate_id: str
    fragment_key: str
    plan_ids: List[str] = Field(default_factory=list)
    capability_ids: List[str] = Field(default_factory=list)
    success_count: int = Field(default=0, ge=0)
    promoted: bool = False
    safe_summary: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")
