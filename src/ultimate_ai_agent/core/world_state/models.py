from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class WorldStateStep(BaseModel):
    step_id: str
    step_type: str
    tool_or_component_ref: Optional[str] = None
    parameters_ref: Optional[str] = None  # Or parameters summary
    outcome: Optional[str] = None
    artifact_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    rollback_ref: Optional[str] = None
    event_ids: List[str] = Field(default_factory=list)

class StructuredWorldState(BaseModel):
    world_state_id: str
    run_id: str
    schema_version: str = "world_state.v0"
    current_phase: str
    current_step: str
    completed_steps: List[WorldStateStep] = Field(default_factory=list)
    open_decisions: List[str] = Field(default_factory=list)
    active_constraints: List[str] = Field(default_factory=list)
    active_assumptions: List[str] = Field(default_factory=list)
    artifact_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    rollback_refs: List[str] = Field(default_factory=list)
    last_event_id: str
    created_at: datetime
    updated_at: datetime
