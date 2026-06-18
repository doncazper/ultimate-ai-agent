from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.enums import LocalModelRuntimeKind
from ultimate_ai_agent.core.time import utc_now


M23_FIXED_LOCAL_MODEL_PROMPT_ID = "m23_fixed_local_model_smoke_v1"
M23_FIXED_LOCAL_MODEL_PROMPT_TEXT = (
    "Respond with exactly UAA_M23_LOCAL_MODEL_CALL_OK. "
    "This is an M23 local-only fixed-prompt smoke call. Do not include secrets."
)
M23_LOCAL_MODEL_CALL_ACTION = "execute_m23_fixed_local_model_call"
M23_MAX_PROMPT_CHARS = 180
M23_MAX_RESPONSE_CHARS = 1000
M23_MAX_TIMEOUT_SECONDS = 10.0


class _M23LocalModelCallModel(BaseModel):
    model_config = ConfigDict(use_enum_values=False, extra="forbid", protected_namespaces=())


class LocalModelFixedPrompt(_M23LocalModelCallModel):
    prompt_id: str = M23_FIXED_LOCAL_MODEL_PROMPT_ID
    prompt_text: str = M23_FIXED_LOCAL_MODEL_PROMPT_TEXT
    content_policy: str = "fixed-non-sensitive-local-smoke"
    contains_user_content: bool = False
    contains_secret_like_content: bool = False
    allowed_for_m23: bool = True
    max_prompt_chars: int = Field(M23_MAX_PROMPT_CHARS, ge=1, le=M23_MAX_PROMPT_CHARS)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LocalModelCallRequest(_M23LocalModelCallModel):
    request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    runtime_kind: LocalModelRuntimeKind
    endpoint_url: str = Field(..., min_length=1)
    safe_endpoint_label: str = Field(..., min_length=1)
    model_ref: str = Field(..., min_length=1)
    fixed_prompt_id: str = M23_FIXED_LOCAL_MODEL_PROMPT_ID
    prompt_text: str = M23_FIXED_LOCAL_MODEL_PROMPT_TEXT
    contains_user_content: bool = False
    contains_secret_like_content: bool = False
    tool_call_requested: bool = False
    memory_write_requested: bool = False
    file_write_requested: bool = False
    openwebui_context_requested: bool = False
    approval_ref: str | None = None
    timeout_seconds: float = Field(5.0, gt=0, le=M23_MAX_TIMEOUT_SECONDS)
    max_response_chars: int = Field(512, ge=1, le=M23_MAX_RESPONSE_CHARS)
    dry_run: bool = True
    execute_local_call: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class LocalModelCallDecision(_M23LocalModelCallModel):
    decision_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    allowed: bool = False
    status: str = Field(..., min_length=1)
    reason_codes: list[str] = Field(default_factory=list)
    safe_message: str = Field(..., min_length=1)
    required_next_action: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class LocalModelCallTransportResult(_M23LocalModelCallModel):
    transport_result_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    transport_kind: Literal["none", "fake", "manual_stdlib_loopback", "manual_stdlib_openai_completions"]
    call_performed: bool = False
    endpoint_contacted: bool = False
    network_scope: Literal["none", "loopback"] = "none"
    status_code: int | None = Field(None, ge=100, le=599)
    response_received: bool = False
    raw_response_stored: bool = False
    response_truncated: bool = False
    redaction_applied: bool = False
    safe_response_text: str | None = None
    safe_response_summary: str | None = None
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def contact_scope_must_match_call(self):
        if self.call_performed and not self.endpoint_contacted:
            raise ValueError("M23 call_performed requires endpoint_contacted.")
        if self.endpoint_contacted and self.network_scope != "loopback":
            raise ValueError("M23 endpoint contact must remain loopback scoped.")
        if self.raw_response_stored:
            raise ValueError("M23 raw responses must not be stored.")
        return self


class LocalModelCallReceipt(_M23LocalModelCallModel):
    receipt_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    runtime_kind: LocalModelRuntimeKind
    endpoint_label: str = Field(..., min_length=1)
    fixed_prompt_id: str = M23_FIXED_LOCAL_MODEL_PROMPT_ID
    call_performed: bool = False
    model_output_non_authoritative: bool = True
    tools_executed: list[str] = Field(default_factory=list)
    memory_written: bool = False
    files_written: bool = False
    provider_called: bool = False
    remote_called: bool = False
    response_summary: str | None = None
    redaction_status: Literal["none", "applied", "blocked"] = "none"
    event_refs: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class LocalModelCallResult(_M23LocalModelCallModel):
    result_id: str = Field(..., min_length=1)
    request_id: str = Field(..., min_length=1)
    decision: LocalModelCallDecision
    transport_result: LocalModelCallTransportResult
    receipt: LocalModelCallReceipt
    safe_message: str = Field(..., min_length=1)
    warnings: list[str] = Field(default_factory=list)
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
