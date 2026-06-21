from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.enums import ModelRuntimeOutputFormat, ModelRuntimeResponseStatus
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean
from ultimate_ai_agent.core.time import utc_now


class ModelRuntimeResponse(BaseModel):
    runtime_response_id: str = Field(..., min_length=1)
    runtime_request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    status: ModelRuntimeResponseStatus
    output_format: ModelRuntimeOutputFormat
    output_summary: str = Field(..., min_length=1)
    structured_output: Optional[Dict[str, Any]] = None
    refusal_reason: Optional[str] = None
    simulated_latency_ms: Optional[int] = Field(None, ge=0)
    simulated_token_usage: Dict[str, int] = Field(default_factory=dict)
    model_profile_id: str = Field(..., min_length=1)
    adapter_id: str = Field(..., min_length=1)
    event_refs: List[str] = Field(default_factory=list)
    redactions_applied: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    response_origin: str = "simulated"

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def response_must_be_simulated_and_secret_clean(self) -> Any:
        if str(self.status) not in {
            ModelRuntimeResponseStatus.simulated_success.value,
            ModelRuntimeResponseStatus.simulated_refusal.value,
            ModelRuntimeResponseStatus.simulated_error.value,
            ModelRuntimeResponseStatus.validation_failed.value,
            ModelRuntimeResponseStatus.local_loopback_success.value,
            ModelRuntimeResponseStatus.local_loopback_error.value,
        }:
            raise ValueError("Model runtime response must be simulated or local loopback dev.")
        assert_secret_clean(self.output_summary, "Model runtime response output_summary")
        assert_secret_clean(self.structured_output, "Model runtime response structured_output")
        assert_secret_clean(self.metadata, "Model runtime response metadata")
        assert_secret_clean(self.warnings, "Model runtime response warnings")
        assert_secret_clean(self.errors, "Model runtime response errors")
        assert_secret_clean(self.response_origin, "Model runtime response response_origin")
        return self


def response_is_truth_authority(response: ModelRuntimeResponse) -> bool:
    return False
