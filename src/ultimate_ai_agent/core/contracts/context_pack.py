from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ContextPackScope(str, Enum):
    run = "run"
    subtask = "subtask"
    verifier = "verifier"
    memory_curator = "memory_curator"
    tool_execution = "tool_execution"
    notification_decision = "notification_decision"
    self_improvement_review = "self_improvement_review"

class AuthorityType(str, Enum):
    user_instruction = "user_instruction"
    canonical = "canonical"
    active_spec = "active_spec"
    approved_decision = "approved_decision"
    memory = "memory"
    conversation = "conversation"
    model_knowledge = "model_knowledge"
    external_evidence = "external_evidence"

class ContentRole(str, Enum):
    instruction = "instruction"
    policy = "policy"
    evidence_only = "evidence_only"
    reference = "reference"
    candidate_output = "candidate_output"

class ContextSource(BaseModel):
    source_id: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    path: Optional[str] = None
    authority: AuthorityType
    summary: str = Field(..., min_length=1)
    sensitivity: Optional[str] = None
    trust_level: Optional[str] = None
    content_role: Optional[ContentRole] = None

    model_config = ConfigDict(
        use_enum_values=True,
        extra="allow",  # Allow extra metadata for extensibility
    )

class ContextPack(BaseModel):
    context_pack_id: str = Field(..., pattern=r"^cp_[A-Za-z0-9_:-]+$")
    schema_version: str = "0.5.8"
    run_id: str = Field(..., min_length=1)
    contract_id: str = Field(..., min_length=1)
    workspace_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    project_id: Optional[str] = None
    pack_scope: ContextPackScope = ContextPackScope.run
    source_precedence_policy: str = "canonical_wins"
    
    # Prompt-specified properties
    current_user_instruction: Optional[str] = None
    project_state: Optional[str] = None
    canonical_file_refs: List[str] = Field(default_factory=list)
    active_spec_refs: List[str] = Field(default_factory=list)
    memory_snippets: List[str] = Field(default_factory=list)
    file_snippets: List[str] = Field(default_factory=list)
    event_summaries: List[str] = Field(default_factory=list)
    world_state_snapshot_ref: Optional[str] = None
    tool_permissions: List[str] = Field(default_factory=list)
    model_policy: Optional[str] = None
    cost_policy: Optional[str] = None
    grounding_policy: Optional[str] = None
    evidence_requirements: List[str] = Field(default_factory=list)
    redactions_applied: List[str] = Field(default_factory=list)
    source_conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    freshness_context: Optional[str] = None
    data_classification: Optional[str] = None
    token_budget_summary: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

    # Schema-specified properties
    user_instruction_summary: Optional[str] = None
    project_summary: Optional[str] = None
    active_goal: str = Field(..., min_length=1)
    active_spec_summary: Optional[str] = None
    canonical_sources: List[ContextSource] = Field(default_factory=list)
    memory_sources: List[ContextSource] = Field(default_factory=list)
    file_sources: List[ContextSource] = Field(default_factory=list)
    tool_policy_summary: Optional[str] = None
    permission_policy_summary: Optional[str] = None
    model_policy_summary: Optional[str] = None
    cost_policy_summary: Optional[str] = None
    retrieved_items: List[ContextSource] = Field(default_factory=list)
    redacted_items: List[Dict[str, Any]] = Field(default_factory=list)
    excluded_items: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    untrusted_content_boundaries: List[Dict[str, Any]] = Field(default_factory=list)
    token_budget: int = Field(..., ge=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
    )
