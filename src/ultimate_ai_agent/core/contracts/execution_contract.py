from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ultimate_ai_agent.core.contracts.enums import (
    AgentMode,
    TaskClass,
    RiskLevel,
    AutonomyLevel,
    GroundingMode,
    ContractStatus,
    ContractMaturity,
)
from ultimate_ai_agent.core.contracts.versioning import EXECUTION_CONTRACT_SCHEMA_VERSION
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.temporal_context import TemporalContext
from ultimate_ai_agent.core.hygiene.policies import (
    IdempotencyPolicy,
    DataClassification,
    RedactionPolicy,
)

class ExecutionContract(BaseModel):
    contract_id: str = Field(..., pattern=r"^ec_[A-Za-z0-9_:-]+$")
    schema_version: str = EXECUTION_CONTRACT_SCHEMA_VERSION
    run_id: str = Field(..., min_length=1)
    workspace_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    origin: str = Field(default="user_request")
    request_summary: str = Field(..., min_length=1)
    user_request: Optional[str] = None
    goal: str = Field(..., min_length=1)
    deliverable: str = Field(..., min_length=1)
    mode: AgentMode
    project_id: Optional[str] = None
    task_class: Optional[TaskClass] = None
    risk_level: RiskLevel = RiskLevel.low
    autonomy_level: AutonomyLevel = AutonomyLevel.L0_answer_only
    grounding_mode: GroundingMode = GroundingMode.none
    assumptions: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(..., min_length=1)
    required_evidence: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    forbidden_tools: List[str] = Field(default_factory=list)
    required_model_classes: List[str] = Field(default_factory=list)
    required_subagents: List[str] = Field(default_factory=list)
    canonical_files_to_read: List[str] = Field(default_factory=list)
    canonical_files_to_update: List[str] = Field(default_factory=list)
    memory_scopes_to_read: List[str] = Field(default_factory=list)
    memory_scopes_to_write: List[str] = Field(default_factory=list)
    approval_policy: Dict[str, Any] = Field(default_factory=dict)
    privacy_policy: Dict[str, Any] = Field(default_factory=dict)
    cost_policy: Dict[str, Any] = Field(default_factory=dict)
    rollback_policy: Dict[str, Any] = Field(default_factory=dict)
    event_logging_policy: Dict[str, Any] = Field(default_factory=dict)
    idempotency_policy: Optional[IdempotencyPolicy] = None
    actor_context: Optional[ActorContext] = None
    temporal_context: Optional[TemporalContext] = None
    data_classification: Optional[DataClassification] = None
    redaction_policy: Optional[RedactionPolicy] = None
    capability_flags_required: List[str] = Field(default_factory=list)
    status: ContractStatus = ContractStatus.draft
    verification_contract_refs: List[str] = Field(default_factory=list)
    contract_maturity: ContractMaturity = ContractMaturity.draft
    provisional_until: Optional[str] = None
    autonomy_policy_ref: Optional[str] = None
    tcb_touchpoints: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_acceptance_criteria(cls, v: List[str]) -> List[str]:
        if not v or len(v) == 0:
            raise ValueError("acceptance_criteria cannot be empty")
        return v
