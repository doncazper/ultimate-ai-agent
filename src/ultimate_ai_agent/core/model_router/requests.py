from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.context_budget import ContextBudget
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.policies import DataClassification
from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.model_router.enums import ModelTaskCapability
from ultimate_ai_agent.core.model_router.policies import ModelRoutingPolicy
from ultimate_ai_agent.core.model_router.profiles import ModelCapabilityProfile


class ModelRouteRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    actor_context: ActorContext
    task_class: str = Field(..., min_length=1)
    prompt_summary: str = Field(..., min_length=1)
    data_classification: DataClassification
    required_capabilities: List[ModelTaskCapability] = Field(default_factory=list)
    estimated_input_tokens: int = Field(..., ge=0)
    estimated_output_tokens: int = Field(..., ge=0)
    context_budget: Optional[ContextBudget] = None
    routing_policy: ModelRoutingPolicy
    available_profiles: List[ModelCapabilityProfile] = Field(default_factory=list)
    credential_availability: Dict[str, bool] = Field(default_factory=dict)
    consent_refs: List[str] = Field(default_factory=list)
    approval_ref: Optional[str] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def prompt_summary_must_be_secret_clean(self) -> Any:
        if scan_payload_for_secrets(self.prompt_summary):
            raise ValueError("Model route prompt_summary contains secret-like content.")
        return self

    @property
    def total_estimated_tokens(self) -> int:
        return self.estimated_input_tokens + self.estimated_output_tokens
