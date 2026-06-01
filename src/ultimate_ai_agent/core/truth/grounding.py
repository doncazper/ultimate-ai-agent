from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.truth.enums import GroundingMode, TruthSourceType, TruthTaskClass


FACTUAL_TASKS = {
    TruthTaskClass.factual_answer,
    TruthTaskClass.research,
    TruthTaskClass.policy,
    TruthTaskClass.live_status,
    TruthTaskClass.weather,
    TruthTaskClass.news,
    TruthTaskClass.metrics,
    TruthTaskClass.code_status,
    TruthTaskClass.project_truth,
}

HIGH_STAKES_TASKS = {
    TruthTaskClass.legal,
    TruthTaskClass.medical,
    TruthTaskClass.financial,
    TruthTaskClass.security,
}

FRESHNESS_REQUIRED_TASKS = {
    TruthTaskClass.live_status,
    TruthTaskClass.weather,
    TruthTaskClass.news,
    TruthTaskClass.metrics,
}


class GroundingPolicy(BaseModel):
    policy_id: str
    task_class: TruthTaskClass
    grounding_mode: GroundingMode
    required_source_types: List[TruthSourceType] = Field(default_factory=list)
    preferred_source_types: List[TruthSourceType] = Field(default_factory=list)
    forbidden_source_types: List[TruthSourceType] = Field(default_factory=list)
    min_evidence_count: int = Field(default=1, ge=0)
    require_citations: bool = True
    require_freshness: bool = False
    max_source_age_seconds: Optional[int] = Field(None, ge=0)
    allow_memory_only: bool = False
    require_conflict_check: bool = True
    require_human_review: bool = False
    unsupported_claim_behavior: str = "ask_for_source"

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_grounding_requirements(self):
        if self.task_class in FACTUAL_TASKS and self.grounding_mode == GroundingMode.none:
            raise ValueError("grounding is required for factual and truth-sensitive tasks.")
        if self.task_class in HIGH_STAKES_TASKS and not self.require_human_review:
            raise ValueError("human_review is required for high-stakes truth tasks.")
        if self.task_class in FRESHNESS_REQUIRED_TASKS and not self.require_freshness:
            raise ValueError("freshness is required for live, weather, news, and metrics tasks.")
        if self.task_class in FRESHNESS_REQUIRED_TASKS and self.allow_memory_only:
            raise ValueError("memory-only grounding is not allowed for hard/live facts.")
        return self
