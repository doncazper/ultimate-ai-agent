from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.run_storage import (
    AppendFirstRunStorage,
    DurableRunStorageEntryKind,
)
from ultimate_ai_agent.core.execution.validation import (
    dedupe_reasons,
    validate_execution_ref,
    validate_safe_execution_payload,
    validate_safe_execution_text,
)


BACKGROUND_COWORKER_WORKER_IDENTITY_SCHEMA_VERSION = "background_coworker_worker_identity.v1"
BACKGROUND_COWORKER_HANDOFF_ENVELOPE_SCHEMA_VERSION = "background_coworker_handoff_envelope.v1"
BACKGROUND_COWORKER_WORKER_EVENT_SCHEMA_VERSION = "background_coworker_worker_event.v1"
BACKGROUND_COWORKER_WORKER_EVENT_RECEIPT_SCHEMA_VERSION = "background_coworker_worker_event_receipt.v1"
BACKGROUND_COWORKER_READ_MODEL_SCHEMA_VERSION = "background_coworker_read_model.v1"
BACKGROUND_COWORKER_WORKER_STATUS_SCHEMA_VERSION = "background_coworker_worker_status.v1"
BACKGROUND_COWORKER_RUN_TREE_SCHEMA_VERSION = "background_coworker_run_tree.v1"

BackgroundCoworkerWorkerKind = Literal[
    "metadata_worker",
    "review_worker",
    "handoff_worker",
    "external_agent_metadata",
    "deterministic_worker_metadata",
]

BackgroundCoworkerWorkerEventType = Literal[
    "lease_requested",
    "lease_granted_metadata_only",
    "heartbeat_recorded",
    "heartbeat_stale",
    "lease_expired",
    "worker_blocked",
    "handoff_recorded",
    "cancel_requested",
    "resume_requested",
]

BackgroundCoworkerExecutionState = Literal["metadata_only_blocked", "planned_blocked", "inspection_only"]

BACKGROUND_COWORKER_WORKER_KINDS: tuple[BackgroundCoworkerWorkerKind, ...] = (
    "metadata_worker",
    "review_worker",
    "handoff_worker",
    "external_agent_metadata",
    "deterministic_worker_metadata",
)

BACKGROUND_COWORKER_WORKER_EVENT_TYPES: tuple[BackgroundCoworkerWorkerEventType, ...] = (
    "lease_requested",
    "lease_granted_metadata_only",
    "heartbeat_recorded",
    "heartbeat_stale",
    "lease_expired",
    "worker_blocked",
    "handoff_recorded",
    "cancel_requested",
    "resume_requested",
)

_RAW_CONTEXT_FIELD_RE = re.compile(
    r"(?i)(^|[_-])("
    r"raw|prompt|response|provider[_-]?payload|tool[_-]?payload|payload|"
    r"context[_-]?payload|raw[_-]?context|local[_-]?path|env[_-]?dump|credential|"
    r"cookie|token|secret|api[_-]?key|password|username|hostname|file[_-]?content"
    r")($|[_-])"
)
_RAW_CONTEXT_VALUE_RE = re.compile(
    r"(?i)(raw\s+(prompt|response|context|payload|local\s+path|file\s+content)|"
    r"context[\s_-]?payload|provider[\s_-]?payload|tool[\s_-]?payload|env[\s_-]?dump|"
    r"credential|secret|api[_-]?key|bearer\s+|cookie|token|/Users/|/home/|"
    r"-----BEGIN)"
)
_RAW_CONTEXT_ALLOWED_KEYS = {
    "raw_payloads_persisted",
    "raw_context_payload_persisted",
    "raw_context_omitted",
}


def _stable_ref(prefix: str, *parts: str) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(payload).hexdigest()[:24]}"


def _sorted_unique(refs: Iterable[str | None]) -> list[str]:
    safe_refs: list[str] = []
    for ref in refs:
        if not ref:
            continue
        validate_execution_ref(ref, "background_coworker_ref")
        safe_refs.append(ref)
    return sorted(dict.fromkeys(safe_refs))


def _validate_ref_list(values: Iterable[str], field_name: str) -> None:
    for value in values:
        validate_execution_ref(value, field_name)


def _validate_optional_ref(value: str | None, field_name: str) -> None:
    if value:
        validate_execution_ref(value, field_name)


def _raw_context_reasons(value: Any) -> list[str]:
    reasons: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text not in _RAW_CONTEXT_ALLOWED_KEYS and _RAW_CONTEXT_FIELD_RE.search(key_text):
                reasons.append("BACKGROUND_COWORKER_RAW_CONTEXT_FIELD_BLOCKED")
            reasons.extend(_raw_context_reasons(item))
        return dedupe_reasons(reasons)
    if isinstance(value, list):
        for item in value:
            reasons.extend(_raw_context_reasons(item))
        return dedupe_reasons(reasons)
    if isinstance(value, str) and _RAW_CONTEXT_VALUE_RE.search(value):
        reasons.append("BACKGROUND_COWORKER_RAW_CONTEXT_VALUE_BLOCKED")
    return dedupe_reasons(reasons)


def validate_background_coworker_contract_payload(value: Mapping[str, Any]) -> list[str]:
    """Return fail-closed reason codes for unsafe raw-context-shaped data."""

    return _raw_context_reasons(value)


def _validate_safe_summary(value: str, field_name: str) -> None:
    validate_safe_execution_text(value, field_name)
    reasons = _raw_context_reasons(value)
    if reasons:
        raise ValueError(f"{field_name.upper()}_RAW_CONTEXT_DENIED")


def _deny_true_flags(model: Any, field_names: Iterable[str], reason_prefix: str) -> None:
    for field_name in field_names:
        if getattr(model, field_name):
            raise ValueError(f"{reason_prefix}:{field_name}")


class _BackgroundCoworkerContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True, validate_assignment=True)


class BackgroundCoworkerWorkerIdentityContract(_BackgroundCoworkerContractModel):
    schema_version: str = BACKGROUND_COWORKER_WORKER_IDENTITY_SCHEMA_VERSION
    worker_ref: str = Field(..., min_length=1)
    worker_kind: BackgroundCoworkerWorkerKind = "metadata_worker"
    capability_scope_refs: list[str] = Field(default_factory=list)
    allowed_run_type_refs: list[str] = Field(default_factory=list)
    denied_authority_refs: list[str] = Field(default_factory=list)
    lease_ref: str = Field(..., min_length=1)
    heartbeat_ref: str = Field(..., min_length=1)
    parent_run_ref: str = Field(..., min_length=1)
    child_run_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(
        default="Worker identity is metadata only; worker refs grant no execution authority.",
        min_length=1,
    )
    safe_refs_only: bool = True
    no_execution_authority: bool = True
    worker_ref_grants_authority: bool = False
    raw_payloads_persisted: bool = False
    background_execution_enabled: bool = False
    scheduler_enabled: bool = False
    autonomous_model_calls_enabled: bool = False
    provider_sdk_calls_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_writes_enabled: bool = False
    live_web_runtime_enabled: bool = False
    interactive_surface_runtime_enabled: bool = False
    local_command_runtime_enabled: bool = False
    external_process_started: bool = False
    queue_consumer_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_identity(self) -> Any:
        for value, field_name in [
            (self.worker_ref, "worker_ref"),
            (self.lease_ref, "lease_ref"),
            (self.heartbeat_ref, "heartbeat_ref"),
            (self.parent_run_ref, "parent_run_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for ref in [
            *self.capability_scope_refs,
            *self.allowed_run_type_refs,
            *self.denied_authority_refs,
            *self.child_run_refs,
        ]:
            validate_execution_ref(ref, "background_coworker_identity_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.worker_kind, "worker_kind"),
            (self.safe_summary, "safe_summary"),
        ]:
            _validate_safe_summary(text, field_name)
        if not self.safe_refs_only:
            raise ValueError("BACKGROUND_COWORKER_SAFE_REFS_REQUIRED")
        if not self.no_execution_authority:
            raise ValueError("BACKGROUND_COWORKER_NO_EXECUTION_AUTHORITY_REQUIRED")
        if not self.denied_authority_refs:
            raise ValueError("BACKGROUND_COWORKER_DENIED_AUTHORITY_REFS_REQUIRED")
        _deny_true_flags(
            self,
            [
                "worker_ref_grants_authority",
                "raw_payloads_persisted",
                "background_execution_enabled",
                "scheduler_enabled",
                "autonomous_model_calls_enabled",
                "provider_sdk_calls_enabled",
                "tool_execution_enabled",
                "connector_writes_enabled",
                "live_web_runtime_enabled",
                "interactive_surface_runtime_enabled",
                "local_command_runtime_enabled",
                "external_process_started",
                "queue_consumer_enabled",
                "production_authority_enabled",
            ],
            "BACKGROUND_COWORKER_AUTHORITY_DENIED",
        )
        return self


class BackgroundCoworkerHandoffEnvelopeContract(_BackgroundCoworkerContractModel):
    schema_version: str = BACKGROUND_COWORKER_HANDOFF_ENVELOPE_SCHEMA_VERSION
    handoff_ref: str = Field(..., min_length=1)
    parent_run_ref: str = Field(..., min_length=1)
    child_run_ref: str = Field(..., min_length=1)
    objective_safe_summary_ref: str = Field(..., min_length=1)
    context_pack_ref: str = Field(..., min_length=1)
    approval_scope_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    timeout_ref: str = Field(..., min_length=1)
    expected_output_schema_ref: str = Field(..., min_length=1)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(
        default="Coworker handoff envelope is safe-ref-only metadata; dispatch remains blocked.",
        min_length=1,
    )
    safe_refs_only: bool = True
    raw_context_payload_persisted: bool = False
    context_injection_enabled: bool = False
    worker_dispatch_enabled: bool = False
    execution_authority_enabled: bool = False
    approval_ref_grants_authority: bool = False
    connector_writes_enabled: bool = False
    model_calls_enabled: bool = False
    tool_execution_enabled: bool = False

    @model_validator(mode="after")
    def validate_handoff(self) -> Any:
        for value, field_name in [
            (self.handoff_ref, "handoff_ref"),
            (self.parent_run_ref, "parent_run_ref"),
            (self.child_run_ref, "child_run_ref"),
            (self.objective_safe_summary_ref, "objective_safe_summary_ref"),
            (self.context_pack_ref, "context_pack_ref"),
            (self.approval_scope_ref, "approval_scope_ref"),
            (self.timeout_ref, "timeout_ref"),
            (self.expected_output_schema_ref, "expected_output_schema_ref"),
        ]:
            validate_execution_ref(value, field_name)
        _validate_ref_list(self.evidence_refs, "evidence_ref")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.safe_summary, "safe_summary"),
        ]:
            _validate_safe_summary(text, field_name)
        if self.parent_run_ref == self.child_run_ref:
            raise ValueError("BACKGROUND_COWORKER_PARENT_CHILD_RUN_REF_MUST_DIFFER")
        if not self.blocked_authority_refs:
            raise ValueError("BACKGROUND_COWORKER_HANDOFF_BLOCKED_AUTHORITY_REFS_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("BACKGROUND_COWORKER_HANDOFF_SAFE_REFS_REQUIRED")
        if _raw_context_reasons(self.model_dump(mode="json")):
            raise ValueError("BACKGROUND_COWORKER_HANDOFF_RAW_CONTEXT_DENIED")
        _deny_true_flags(
            self,
            [
                "raw_context_payload_persisted",
                "context_injection_enabled",
                "worker_dispatch_enabled",
                "execution_authority_enabled",
                "approval_ref_grants_authority",
                "connector_writes_enabled",
                "model_calls_enabled",
                "tool_execution_enabled",
            ],
            "BACKGROUND_COWORKER_HANDOFF_AUTHORITY_DENIED",
        )
        return self


class BackgroundCoworkerWorkerEventContract(_BackgroundCoworkerContractModel):
    schema_version: str = BACKGROUND_COWORKER_WORKER_EVENT_SCHEMA_VERSION
    event_ref: str = Field(..., min_length=1)
    worker_ref: str = Field(..., min_length=1)
    worker_kind: BackgroundCoworkerWorkerKind = "metadata_worker"
    event_type: BackgroundCoworkerWorkerEventType
    run_ref: str = Field(..., min_length=1)
    parent_run_ref: str | None = None
    child_run_ref: str | None = None
    handoff_ref: str | None = None
    lease_ref: str | None = None
    heartbeat_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    idempotency_key_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1)
    metadata_only: bool = True
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    execution_performed: bool = False
    live_worker_control_performed: bool = False
    background_execution_enabled: bool = False
    scheduler_enabled: bool = False
    external_process_started: bool = False
    queue_consumer_enabled: bool = False
    provider_model_called: bool = False
    tool_executed: bool = False
    connector_write_performed: bool = False

    @model_validator(mode="after")
    def validate_event(self) -> Any:
        for value, field_name in [
            (self.event_ref, "event_ref"),
            (self.worker_ref, "worker_ref"),
            (self.run_ref, "run_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.parent_run_ref, "parent_run_ref"),
            (self.child_run_ref, "child_run_ref"),
            (self.handoff_ref, "handoff_ref"),
            (self.lease_ref, "lease_ref"),
            (self.heartbeat_ref, "heartbeat_ref"),
        ]:
            _validate_optional_ref(value, field_name)
        for ref in [
            *self.evidence_refs,
            *self.blocked_authority_refs,
            *self.receipt_refs,
            *self.audit_refs,
            *self.replay_refs,
            *self.rollback_refs,
            *self.idempotency_key_refs,
        ]:
            validate_execution_ref(ref, "background_coworker_event_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.worker_kind, "worker_kind"),
            (self.event_type, "event_type"),
            (self.safe_summary, "safe_summary"),
        ]:
            _validate_safe_summary(text, field_name)
        if self.event_type in {"lease_requested", "lease_granted_metadata_only", "lease_expired"} and not self.lease_ref:
            raise ValueError("BACKGROUND_COWORKER_LEASE_REF_REQUIRED")
        if self.event_type in {"heartbeat_recorded", "heartbeat_stale"} and not self.heartbeat_ref:
            raise ValueError("BACKGROUND_COWORKER_HEARTBEAT_REF_REQUIRED")
        if self.event_type == "handoff_recorded" and (
            not self.parent_run_ref or not self.child_run_ref or not self.handoff_ref
        ):
            raise ValueError("BACKGROUND_COWORKER_HANDOFF_REFS_REQUIRED")
        if self.event_type == "worker_blocked" and not self.blocked_authority_refs:
            raise ValueError("BACKGROUND_COWORKER_BLOCKED_AUTHORITY_REFS_REQUIRED")
        if not self.metadata_only:
            raise ValueError("BACKGROUND_COWORKER_EVENT_METADATA_ONLY_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("BACKGROUND_COWORKER_EVENT_SAFE_REFS_REQUIRED")
        if _raw_context_reasons(self.model_dump(mode="json")):
            raise ValueError("BACKGROUND_COWORKER_EVENT_RAW_CONTEXT_DENIED")
        _deny_true_flags(
            self,
            [
                "raw_payloads_persisted",
                "execution_performed",
                "live_worker_control_performed",
                "background_execution_enabled",
                "scheduler_enabled",
                "external_process_started",
                "queue_consumer_enabled",
                "provider_model_called",
                "tool_executed",
                "connector_write_performed",
            ],
            "BACKGROUND_COWORKER_EVENT_AUTHORITY_DENIED",
        )
        return self

    def to_receipt_summary(self) -> dict[str, Any]:
        return {
            "schema_version": BACKGROUND_COWORKER_WORKER_EVENT_RECEIPT_SCHEMA_VERSION,
            "coworker_event_type": self.event_type,
            "event_ref": self.event_ref,
            "worker_ref": self.worker_ref,
            "worker_kind": self.worker_kind,
            "run_ref": self.run_ref,
            "parent_run_ref": self.parent_run_ref,
            "child_run_ref": self.child_run_ref,
            "handoff_ref": self.handoff_ref,
            "lease_ref": self.lease_ref,
            "heartbeat_ref": self.heartbeat_ref,
            "evidence_refs": list(self.evidence_refs),
            "blocked_authority_refs": list(self.blocked_authority_refs),
            "safe_refs_only": True,
            "metadata_only": True,
            "raw_payloads_persisted": False,
            "runtime_execution_performed": False,
            "worker_runtime_started": False,
            "queue_consumer_started": False,
            "process_control_performed": False,
        }


class BackgroundCoworkerRunTreeReadModel(_BackgroundCoworkerContractModel):
    schema_version: str = BACKGROUND_COWORKER_RUN_TREE_SCHEMA_VERSION
    parent_run_ref: str = Field(..., min_length=1)
    child_run_refs: list[str] = Field(default_factory=list)
    worker_refs: list[str] = Field(default_factory=list)
    handoff_refs: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True
    execution_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_tree(self) -> Any:
        validate_execution_ref(self.parent_run_ref, "parent_run_ref")
        for ref in [*self.child_run_refs, *self.worker_refs, *self.handoff_refs]:
            validate_execution_ref(ref, "background_coworker_tree_ref")
        if not self.safe_refs_only:
            raise ValueError("BACKGROUND_COWORKER_RUN_TREE_SAFE_REFS_REQUIRED")
        if self.execution_authority_enabled:
            raise ValueError("BACKGROUND_COWORKER_RUN_TREE_AUTHORITY_DENIED")
        return self


class BackgroundCoworkerWorkerStatusReadModel(_BackgroundCoworkerContractModel):
    schema_version: str = BACKGROUND_COWORKER_WORKER_STATUS_SCHEMA_VERSION
    worker_ref: str = Field(..., min_length=1)
    worker_kind: BackgroundCoworkerWorkerKind = "metadata_worker"
    latest_event_type: BackgroundCoworkerWorkerEventType | None = None
    parent_run_ref: str | None = None
    child_run_refs: list[str] = Field(default_factory=list)
    lease_ref: str | None = None
    heartbeat_ref: str | None = None
    stale_heartbeat_visible: bool = False
    lease_expiry_visible: bool = False
    execution_state: BackgroundCoworkerExecutionState = "metadata_only_blocked"
    blocked_authority_refs: list[str] = Field(default_factory=list)
    safe_refs_only: bool = True
    worker_ref_grants_authority: bool = False
    background_execution_enabled: bool = False
    scheduler_enabled: bool = False
    external_process_started: bool = False
    queue_consumer_enabled: bool = False

    @model_validator(mode="after")
    def validate_status(self) -> Any:
        validate_execution_ref(self.worker_ref, "worker_ref")
        for value, field_name in [
            (self.parent_run_ref, "parent_run_ref"),
            (self.lease_ref, "lease_ref"),
            (self.heartbeat_ref, "heartbeat_ref"),
        ]:
            _validate_optional_ref(value, field_name)
        for ref in [*self.child_run_refs, *self.blocked_authority_refs]:
            validate_execution_ref(ref, "background_coworker_status_ref")
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.worker_kind, "worker_kind"),
            (self.execution_state, "execution_state"),
        ]:
            _validate_safe_summary(text, field_name)
        if self.latest_event_type:
            _validate_safe_summary(self.latest_event_type, "latest_event_type")
        if not self.safe_refs_only:
            raise ValueError("BACKGROUND_COWORKER_STATUS_SAFE_REFS_REQUIRED")
        _deny_true_flags(
            self,
            [
                "worker_ref_grants_authority",
                "background_execution_enabled",
                "scheduler_enabled",
                "external_process_started",
                "queue_consumer_enabled",
            ],
            "BACKGROUND_COWORKER_STATUS_AUTHORITY_DENIED",
        )
        return self


class BackgroundCoworkerReadModel(_BackgroundCoworkerContractModel):
    schema_version: str = BACKGROUND_COWORKER_READ_MODEL_SCHEMA_VERSION
    source: str = "python_core_background_coworker_read_model"
    backend_owned: bool = True
    cli_ref: str = "python -m ultimate_ai_agent.core.task_decomposition.cli inspect-coworker-workers"
    route_ref: str = "planned:none"
    event_count: int = Field(..., ge=0)
    worker_count: int = Field(..., ge=0)
    run_tree_count: int = Field(..., ge=0)
    events: list[BackgroundCoworkerWorkerEventContract] = Field(default_factory=list)
    worker_statuses: list[BackgroundCoworkerWorkerStatusReadModel] = Field(default_factory=list)
    run_trees: list[BackgroundCoworkerRunTreeReadModel] = Field(default_factory=list)
    event_type_counts: dict[str, int] = Field(default_factory=dict)
    supported_worker_kinds: list[BackgroundCoworkerWorkerKind] = Field(
        default_factory=lambda: list(BACKGROUND_COWORKER_WORKER_KINDS)
    )
    supported_event_types: list[BackgroundCoworkerWorkerEventType] = Field(
        default_factory=lambda: list(BACKGROUND_COWORKER_WORKER_EVENT_TYPES)
    )
    safe_summary: str = Field(
        default="Background coworker worker state is metadata-only and blocked from runtime execution.",
        min_length=1,
    )
    all_execution_states_blocked_or_planned: bool = True
    safe_refs_only: bool = True
    raw_payloads_persisted: bool = False
    worker_refs_grant_authority: bool = False
    background_execution_enabled: bool = False
    scheduler_enabled: bool = False
    autonomous_model_calls_enabled: bool = False
    provider_sdk_calls_enabled: bool = False
    tool_execution_enabled: bool = False
    connector_writes_enabled: bool = False
    live_web_runtime_enabled: bool = False
    interactive_surface_runtime_enabled: bool = False
    local_command_runtime_enabled: bool = False
    external_process_started: bool = False
    queue_consumer_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_read_model(self) -> Any:
        for text, field_name in [
            (self.schema_version, "schema_version"),
            (self.source, "source"),
            (self.cli_ref, "cli_ref"),
            (self.route_ref, "route_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            _validate_safe_summary(text, field_name)
        validate_safe_execution_payload(
            self.model_dump(mode="json", exclude={"events", "worker_statuses", "run_trees"}),
            "background_coworker_read_model",
        )
        if not self.backend_owned:
            raise ValueError("BACKGROUND_COWORKER_BACKEND_OWNED_REQUIRED")
        if self.event_count != len(self.events):
            raise ValueError("BACKGROUND_COWORKER_EVENT_COUNT_MISMATCH")
        if self.worker_count != len(self.worker_statuses):
            raise ValueError("BACKGROUND_COWORKER_WORKER_COUNT_MISMATCH")
        if self.run_tree_count != len(self.run_trees):
            raise ValueError("BACKGROUND_COWORKER_RUN_TREE_COUNT_MISMATCH")
        if not self.all_execution_states_blocked_or_planned:
            raise ValueError("BACKGROUND_COWORKER_EXECUTION_STATES_BLOCKED_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("BACKGROUND_COWORKER_READ_MODEL_SAFE_REFS_REQUIRED")
        _deny_true_flags(
            self,
            [
                "raw_payloads_persisted",
                "worker_refs_grant_authority",
                "background_execution_enabled",
                "scheduler_enabled",
                "autonomous_model_calls_enabled",
                "provider_sdk_calls_enabled",
                "tool_execution_enabled",
                "connector_writes_enabled",
                "live_web_runtime_enabled",
                "interactive_surface_runtime_enabled",
                "local_command_runtime_enabled",
                "external_process_started",
                "queue_consumer_enabled",
                "production_authority_enabled",
            ],
            "BACKGROUND_COWORKER_READ_MODEL_AUTHORITY_DENIED",
        )
        return self


def background_coworker_event_from_receipt_summary(
    receipt_summary: Mapping[str, Any],
) -> BackgroundCoworkerWorkerEventContract | None:
    if receipt_summary.get("schema_version") != BACKGROUND_COWORKER_WORKER_EVENT_RECEIPT_SCHEMA_VERSION:
        return None
    event_type = receipt_summary.get("coworker_event_type")
    if event_type not in BACKGROUND_COWORKER_WORKER_EVENT_TYPES:
        return None
    return BackgroundCoworkerWorkerEventContract(
        event_ref=str(receipt_summary["event_ref"]),
        worker_ref=str(receipt_summary["worker_ref"]),
        worker_kind=receipt_summary.get("worker_kind", "metadata_worker"),
        event_type=event_type,
        run_ref=str(receipt_summary["run_ref"]),
        parent_run_ref=receipt_summary.get("parent_run_ref"),
        child_run_ref=receipt_summary.get("child_run_ref"),
        handoff_ref=receipt_summary.get("handoff_ref"),
        lease_ref=receipt_summary.get("lease_ref"),
        heartbeat_ref=receipt_summary.get("heartbeat_ref"),
        evidence_refs=_sorted_unique(receipt_summary.get("evidence_refs", [])),
        blocked_authority_refs=_sorted_unique(receipt_summary.get("blocked_authority_refs", [])),
        safe_summary="Background coworker event was restored from safe receipt metadata.",
    )


def record_background_coworker_worker_event(
    storage: AppendFirstRunStorage,
    event: BackgroundCoworkerWorkerEventContract,
    *,
    idempotency_key_ref: str,
    audit_ref: str,
    receipt_ref: str,
    rollback_ref: str,
) -> None:
    validated = BackgroundCoworkerWorkerEventContract.model_validate(event.model_dump(mode="python"))
    for value, field_name in [
        (idempotency_key_ref, "idempotency_key_ref"),
        (audit_ref, "audit_ref"),
        (receipt_ref, "receipt_ref"),
        (rollback_ref, "rollback_ref"),
    ]:
        validate_execution_ref(value, field_name)
    storage.append_receipt_summary(
        run_id=validated.run_ref,
        receipt_ref=receipt_ref,
        idempotency_key=idempotency_key_ref,
        audit_ref=audit_ref,
        rollback_ref=rollback_ref,
        safe_summary="Background coworker metadata event was recorded as safe refs only.",
        receipt_summary=validated.to_receipt_summary(),
        evidence_refs=validated.evidence_refs,
    )


def background_coworker_events_from_storage(
    storage: AppendFirstRunStorage,
    *,
    run_ref: str | None = None,
    limit: int = 100,
) -> list[BackgroundCoworkerWorkerEventContract]:
    events: list[BackgroundCoworkerWorkerEventContract] = []
    bounded_limit = max(1, min(limit, 200))
    for entry in storage.list_entries(run_ref):
        if entry.kind != DurableRunStorageEntryKind.receipt or not entry.receipt_summary:
            continue
        event = background_coworker_event_from_receipt_summary(entry.receipt_summary)
        if event is None:
            continue
        events.append(
            event.model_copy(
                update={
                    "receipt_refs": _sorted_unique([entry.receipt_ref, *event.receipt_refs]),
                    "audit_refs": _sorted_unique([entry.audit_ref, *event.audit_refs]),
                    "replay_refs": _sorted_unique([entry.replay_validation_ref, *event.replay_refs]),
                    "rollback_refs": _sorted_unique([entry.rollback_ref, *event.rollback_refs]),
                    "idempotency_key_refs": _sorted_unique([entry.idempotency_key, *event.idempotency_key_refs]),
                }
            )
        )
    return events[-bounded_limit:]


def _build_worker_statuses(
    events: list[BackgroundCoworkerWorkerEventContract],
) -> list[BackgroundCoworkerWorkerStatusReadModel]:
    by_worker: dict[str, list[BackgroundCoworkerWorkerEventContract]] = defaultdict(list)
    for event in events:
        by_worker[event.worker_ref].append(event)

    statuses: list[BackgroundCoworkerWorkerStatusReadModel] = []
    for worker_ref, worker_events in sorted(by_worker.items()):
        latest = worker_events[-1]
        statuses.append(
            BackgroundCoworkerWorkerStatusReadModel(
                worker_ref=worker_ref,
                worker_kind=latest.worker_kind,
                latest_event_type=latest.event_type,
                parent_run_ref=latest.parent_run_ref,
                child_run_refs=_sorted_unique(event.child_run_ref for event in worker_events),
                lease_ref=latest.lease_ref,
                heartbeat_ref=latest.heartbeat_ref,
                stale_heartbeat_visible=any(event.event_type == "heartbeat_stale" for event in worker_events),
                lease_expiry_visible=any(event.event_type == "lease_expired" for event in worker_events),
                execution_state="metadata_only_blocked",
                blocked_authority_refs=_sorted_unique(
                    ref for event in worker_events for ref in event.blocked_authority_refs
                ),
            )
        )
    return statuses


def _build_run_trees(
    events: list[BackgroundCoworkerWorkerEventContract],
) -> list[BackgroundCoworkerRunTreeReadModel]:
    children_by_parent: dict[str, list[str]] = defaultdict(list)
    workers_by_parent: dict[str, list[str]] = defaultdict(list)
    handoffs_by_parent: dict[str, list[str]] = defaultdict(list)
    for event in events:
        if not event.parent_run_ref:
            continue
        if event.child_run_ref:
            children_by_parent[event.parent_run_ref].append(event.child_run_ref)
        workers_by_parent[event.parent_run_ref].append(event.worker_ref)
        if event.handoff_ref:
            handoffs_by_parent[event.parent_run_ref].append(event.handoff_ref)
    return [
        BackgroundCoworkerRunTreeReadModel(
            parent_run_ref=parent_run_ref,
            child_run_refs=_sorted_unique(children_by_parent[parent_run_ref]),
            worker_refs=_sorted_unique(workers_by_parent[parent_run_ref]),
            handoff_refs=_sorted_unique(handoffs_by_parent[parent_run_ref]),
        )
        for parent_run_ref in sorted(children_by_parent)
    ]


def build_background_coworker_read_model(
    storage: AppendFirstRunStorage,
    *,
    run_ref: str | None = None,
    limit: int = 100,
) -> BackgroundCoworkerReadModel:
    if run_ref is not None:
        validate_execution_ref(run_ref, "run_ref")
    events = background_coworker_events_from_storage(storage, run_ref=run_ref, limit=limit)
    statuses = _build_worker_statuses(events)
    run_trees = _build_run_trees(events)
    event_counts = Counter(event.event_type for event in events)
    return BackgroundCoworkerReadModel(
        event_count=len(events),
        worker_count=len(statuses),
        run_tree_count=len(run_trees),
        events=events,
        worker_statuses=statuses,
        run_trees=run_trees,
        event_type_counts=dict(sorted(event_counts.items())),
    )
