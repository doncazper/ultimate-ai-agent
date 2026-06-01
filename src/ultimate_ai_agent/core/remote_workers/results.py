from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.remote_workers.enums import RemoteJobStatus, RemoteOutputTrustLevel
from ultimate_ai_agent.core.remote_workers.validation import assert_remote_secret_clean
from ultimate_ai_agent.core.time import utc_now


class RemoteJobResult(BaseModel):
    job_id: str = Field(..., min_length=1)
    correlation_id: str = Field(..., min_length=1)
    status: RemoteJobStatus
    dispatch_performed: bool = False
    remote_execution_performed: bool = False
    subagent_launched: bool = False
    tools_executed: List[str] = Field(default_factory=list)
    network_connections_opened: List[str] = Field(default_factory=list)
    output_trust_level: RemoteOutputTrustLevel
    output_summary: str = Field(..., min_length=1)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    event_refs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def result_must_be_safe_and_inert(self):
        if self.dispatch_performed is True:
            raise ValueError("REMOTE_DISPATCH_MUST_REMAIN_FALSE")
        if self.remote_execution_performed is True:
            raise ValueError("REMOTE_EXECUTION_MUST_REMAIN_FALSE")
        if self.subagent_launched is True:
            raise ValueError("REMOTE_SUBAGENT_MUST_REMAIN_FALSE")
        if self.tools_executed:
            raise ValueError("REMOTE_TOOLS_MUST_REMAIN_EMPTY")
        if self.network_connections_opened:
            raise ValueError("REMOTE_CONNECTIONS_MUST_REMAIN_EMPTY")
        if self.output_trust_level not in {
            RemoteOutputTrustLevel.untrusted_remote_output,
            RemoteOutputTrustLevel.model_output,
            RemoteOutputTrustLevel.local_mock_output,
        }:
            raise ValueError("REMOTE_OUTPUT_TRUST_LEVEL_INVALID")
        assert_remote_secret_clean(self.model_dump(mode="json"), "Remote job result")
        return self

