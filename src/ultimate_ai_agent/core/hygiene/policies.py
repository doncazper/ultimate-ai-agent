from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class OperationType(str, Enum):
    validation = "validation"
    read_local = "read_local"
    read_provider = "read_provider"
    file_write = "file_write"
    memory_write = "memory_write"
    notification_send = "notification_send"
    external_send = "external_send"
    payment_or_destructive = "payment_or_destructive"
    other = "other"

class RetryClass(str, Enum):
    never_retry = "never_retry"
    safe_retry = "safe_retry"
    retry_with_same_idempotency_key = "retry_with_same_idempotency_key"
    retry_after_backoff = "retry_after_backoff"
    manual_review_required = "manual_review_required"

class OutcomeStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    succeeded = "succeeded"
    failed = "failed"
    outcome_unknown = "outcome_unknown"

class IdempotencyPolicy(BaseModel):
    idempotency_key: str = Field(..., min_length=8)
    dedupe_key: Optional[str] = None
    operation_type: OperationType
    retry_class: RetryClass
    attempt_number: int = Field(..., ge=1)
    max_attempts: int = Field(default=1, ge=1)
    backoff_seconds: Optional[float] = Field(None, ge=0.0)
    outcome_status: OutcomeStatus = OutcomeStatus.not_started

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

class ClassificationValue(str, Enum):
    public = "public"
    user_private = "user_private"
    project_private = "project_private"
    sensitive_personal = "sensitive_personal"
    credential_secret = "credential_" + "secret"
    regulated = "regulated"
    third_party_confidential = "third_party_confidential"
    system_internal = "system_internal"
    tcb_protected = "tcb_protected"

class DataClassification(BaseModel):
    classification: ClassificationValue
    source: str = Field(..., min_length=1)
    reason: Optional[str] = None
    allowed_sinks: List[str] = Field(default_factory=list)
    forbidden_sinks: List[str] = Field(default_factory=list)
    requires_redaction: bool = False
    requires_consent: bool = False
    retention_policy: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

class RedactionSurface(str, Enum):
    prompts = "prompts"
    model_outputs = "model_outputs"
    tool_inputs = "tool_inputs"
    tool_outputs = "tool_outputs"
    provider_requests = "provider_requests"
    provider_responses = "provider_responses"
    error_messages = "error_messages"
    event_ledger_payloads = "event_ledger_payloads"
    receipts = "receipts"
    debug_bundles = "debug_bundles"
    file_previews = "file_previews"
    memory_snippets = "memory_snippets"

class RedactionAction(str, Enum):
    omit = "omit"
    mask = "mask"
    hash = "hash"
    summarize = "summarize"
    store_by_reference = "store_by_reference"
    classify_only = "classify_only"
    quarantine = "quarantine"

class RedactionPolicy(BaseModel):
    policy_id: str = Field(..., min_length=1)
    surfaces: List[RedactionSurface] = Field(..., min_length=1)
    never_log_patterns: List[str] = Field(default_factory=list)
    actions: List[RedactionAction] = Field(..., min_length=1)
    default_action: RedactionAction = RedactionAction.mask
    debug_bundle_allowed: bool = False
    notes: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

class Stage(str, Enum):
    M0 = "M0"
    M0_5 = "M0.5"
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M3_5 = "M3.5"
    M4 = "M4"
    M5 = "M5"
    M6 = "M6"
    post_gate = "post_gate"
    later = "later"

class Status(str, Enum):
    draft = "draft"
    ready_for_build = "ready_for_build"
    spec_review = "spec_review"
    blocked = "blocked"
    enabled = "enabled"
    disabled = "disabled"

class CapabilityFlag(BaseModel):
    capability_id: str = Field(..., min_length=1)
    enabled: bool
    stage: Stage
    requires_foundation_gate: bool
    required_contracts: List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    required_evals: List[str] = Field(default_factory=list)
    kill_switch: bool = True
    owner: Optional[str] = None
    status: Status = Status.draft

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
