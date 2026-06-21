import uuid
import ipaddress
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean


class LoopbackRuntimePolicy(BaseModel):
    policy_id: str = Field(..., min_length=1)
    allow_real_loopback_execution: bool = False
    allowed_hosts: List[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost", "::1"])
    allowed_schemes: List[str] = Field(default_factory=lambda: ["http"])
    require_approval: bool = True
    require_local_dev_mode: bool = True
    require_simulated_fallback: bool = True
    max_input_tokens: Optional[int] = Field(None, ge=0)
    max_output_tokens: Optional[int] = Field(None, ge=0)
    timeout_seconds: float = Field(2.0, gt=0, le=30)
    deny_credentials: bool = True
    deny_non_loopback: bool = True
    event_logging_required: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def policy_must_be_secret_clean(self) -> Any:
        if self.deny_non_loopback is not True:
            raise ValueError("POLICY_CANNOT_DISABLE_LOOPBACK_GUARD")
        non_loopback_hosts = [host for host in self.allowed_hosts if not _is_loopback_allowed_host(host)]
        if non_loopback_hosts:
            raise ValueError("ALLOWED_HOST_NOT_LOOPBACK")
        assert_secret_clean(self.model_dump(mode="json"), "Loopback runtime policy")
        return self


class LocalRuntimeExecutionDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: f"lrt_dec_{uuid.uuid4().hex[:12]}")
    allowed: bool
    status: str = Field(..., min_length=1)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    endpoint_id: Optional[str] = None
    adapter_id: Optional[str] = None
    runtime_request_id: Optional[str] = None
    simulated_fallback_available: bool = False
    event_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def decision_must_be_secret_clean(self) -> Any:
        assert_secret_clean(self.model_dump(mode="json"), "Local runtime execution decision")
        return self


def _is_loopback_allowed_host(host: str) -> bool:
    normalized = host.strip().lower().strip("[]")
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False
