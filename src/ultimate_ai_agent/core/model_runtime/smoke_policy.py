import ipaddress
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.model_runtime.loopback import SECRET_QUERY_KEYS, LoopbackRuntimeEndpoint
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean
from ultimate_ai_agent.core.time import utc_now

DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT = "Respond with exactly UAA_LOCAL_SMOKE_OK. This is a local smoke test. Do not include secrets."

SMOKE_ACTION = "execute_manual_local_loopback_smoke"

USER_CONTENT_MARKERS = (
    "user prompt",
    "user data",
    "file content",
    "memory content",
    "context pack",
    "context_pack",
    "execution contract",
    "task content",
    "summarize this",
    "respond to the user",
)


class ManualLoopbackSmokePolicy(BaseModel):
    policy_id: str = Field(..., min_length=1)
    enable_manual_smoke: bool = False
    allowed_hosts: List[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost", "::1"])
    allowed_schemes: List[str] = Field(default_factory=lambda: ["http"])
    require_loopback: bool = True
    require_approval: bool = True
    require_fixed_smoke_prompt: bool = True
    forbid_user_content: bool = True
    forbid_credentials: bool = True
    timeout_seconds: float = Field(5.0, gt=0, le=30)
    max_response_bytes: int = Field(4096, ge=1, le=65536)
    event_logging_required: bool = True
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def policy_must_be_loopback_and_secret_clean(self) -> Any:
        if self.require_loopback is not True:
            raise ValueError("SMOKE_LOOPBACK_REQUIRED")
        if self.forbid_credentials is not True:
            raise ValueError("SMOKE_CREDENTIALS_MUST_BE_FORBIDDEN")
        if self.require_fixed_smoke_prompt is not True:
            raise ValueError("SMOKE_FIXED_PROMPT_REQUIRED")
        for host in self.allowed_hosts:
            if not is_loopback_host(host):
                raise ValueError("SMOKE_ALLOWED_HOST_NOT_LOOPBACK")
        assert_secret_clean(self.model_dump(mode="json"), "Manual loopback smoke policy")
        return self


class ManualLoopbackSmokeRequest(BaseModel):
    smoke_request_id: str = Field(default_factory=lambda: f"smoke_req_{uuid.uuid4().hex[:12]}")
    run_id: str = Field(..., min_length=1)
    endpoint: LoopbackRuntimeEndpoint
    model_id: str = Field(..., min_length=1)
    approval_ref: Optional[str] = None
    fixed_prompt: str = DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT
    expected_marker: Optional[str] = "UAA_LOCAL_SMOKE_OK"
    policy: ManualLoopbackSmokePolicy
    actor_context: ActorContext
    data_classification: DataClassification = Field(
        default_factory=lambda: DataClassification(classification=ClassificationValue.public, source="manual_loopback_smoke")
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def request_must_be_fixed_loopback_and_secret_clean(self) -> Any:
        if self.policy.require_fixed_smoke_prompt and self.fixed_prompt != DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT:
            raise ValueError("SMOKE_PROMPT_MUST_MATCH_FIXED_PROMPT")
        if self.policy.forbid_user_content and _contains_user_content_marker(self.fixed_prompt):
            raise ValueError("SMOKE_PROMPT_MUST_NOT_INCLUDE_USER_CONTENT")
        endpoint_reasons = smoke_endpoint_reason_codes(self.endpoint, self.policy)
        if endpoint_reasons:
            raise ValueError(",".join(endpoint_reasons))
        assert_secret_clean(self.fixed_prompt, "Manual loopback smoke prompt")
        assert_secret_clean(self.metadata, "Manual loopback smoke metadata")
        return self


class ManualLoopbackSmokeResult(BaseModel):
    smoke_result_id: str = Field(default_factory=lambda: f"smoke_res_{uuid.uuid4().hex[:12]}")
    smoke_request_id: str = Field(..., min_length=1)
    allowed: bool
    success: bool
    status: str = Field(..., min_length=1)
    reason_codes: List[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    response_preview: Optional[str] = None
    response_origin: str = Field(..., min_length=1)
    elapsed_ms: Optional[int] = Field(None, ge=0)
    redactions_applied: List[str] = Field(default_factory=list)
    event_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=lambda: {"truth_authority": False, "runtime_boundary": "local_loopback_smoke"})
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def result_must_be_non_authoritative_and_secret_clean(self) -> Any:
        if self.metadata.get("truth_authority") is not False:
            raise ValueError("SMOKE_RESULT_NOT_TRUTH_AUTHORITY")
        assert_secret_clean(self.response_preview, "Manual loopback smoke response preview")
        assert_secret_clean(self.safe_message, "Manual loopback smoke safe message")
        assert_secret_clean(self.reason_codes, "Manual loopback smoke reason codes")
        assert_secret_clean(self.metadata, "Manual loopback smoke metadata")
        return self


def smoke_endpoint_reason_codes(endpoint: LoopbackRuntimeEndpoint, policy: ManualLoopbackSmokePolicy) -> list[str]:
    reasons: list[str] = []
    parsed = endpoint.parsed_url
    host = endpoint.host
    if not endpoint.enabled:
        reasons.append("ENDPOINT_DISABLED")
    if parsed.scheme not in set(policy.allowed_schemes):
        reasons.append("SCHEME_NOT_ALLOWED")
    if policy.forbid_credentials and (parsed.username or parsed.password):
        reasons.append("URL_CREDENTIALS_DENIED")
    if SECRET_QUERY_KEYS.intersection(endpoint.query_keys):
        reasons.append("SECRET_QUERY_DENIED")
    if host not in set(policy.allowed_hosts):
        reasons.append("HOST_NOT_ALLOWLISTED")
    if policy.require_loopback and not is_loopback_host(host):
        reasons.append("NON_LOOPBACK_HOST_DENIED")
    return reasons


def is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower().strip("[]")
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _contains_user_content_marker(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(marker in lowered for marker in USER_CONTENT_MARKERS)
