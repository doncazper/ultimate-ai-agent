from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.policies import DataClassification
from ultimate_ai_agent.core.model_runtime.enums import ModelRuntimeOutputFormat, ModelRuntimeSafetyMode
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean
from ultimate_ai_agent.core.time import utc_now


class ModelRuntimeRequest(BaseModel):
    runtime_request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    route_decision_ref: Optional[str] = None
    model_profile_id: str = Field(..., min_length=1)
    model_id: str = Field(..., min_length=1)
    adapter_id: str = Field(..., min_length=1)
    actor_context: ActorContext
    prompt_summary: str = Field(..., min_length=1)
    input_refs: List[str] = Field(default_factory=list)
    output_format: ModelRuntimeOutputFormat
    estimated_input_tokens: int = Field(..., ge=0)
    max_output_tokens: int = Field(..., ge=0)
    safety_mode: ModelRuntimeSafetyMode
    data_classification: DataClassification
    consent_refs: List[str] = Field(default_factory=list)
    approval_ref: Optional[str] = None
    secret_handle_refs: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None
    trace_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def request_must_be_simulated_and_secret_clean(self) -> Any:
        if self.safety_mode == ModelRuntimeSafetyMode.disabled:
            raise ValueError("Model runtime request cannot use disabled safety mode.")
        assert_secret_clean(self.prompt_summary, "Model runtime request prompt_summary")
        assert_secret_clean(self.metadata, "Model runtime request metadata")
        assert_secret_clean(self.input_refs, "Model runtime request input_refs")
        return self
