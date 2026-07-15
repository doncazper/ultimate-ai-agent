from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .constants import (
    MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS,
    MATRIX_SYNC_BACKUP_POSTURE_REF,
    MATRIX_SYNC_BUDGET_REF,
    MATRIX_SYNC_CACHE_BACKEND_REF,
    MATRIX_SYNC_CACHE_SCHEMA_REF,
    MATRIX_SYNC_CREDENTIAL_BACKEND_REF,
    MATRIX_SYNC_KILL_SWITCH_REF,
    MATRIX_SYNC_MAX_BYTES,
    MATRIX_SYNC_MAX_EVENTS,
    MATRIX_SYNC_MAX_ROOMS,
    MATRIX_SYNC_PROVIDER_REF,
    MATRIX_SYNC_RETENTION_REF,
    MATRIX_SYNC_SAFE_DISABLE_REF,
    MATRIX_SYNC_SCHEMA_VERSION,
    MATRIX_SYNC_TARGET_REF,
    MatrixSyncOperation,
    matrix_sync_lane,
)


def stable_matrix_sync_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class _MatrixSyncModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixSyncFreshness(str, Enum):
    current = "current"
    stale = "stale"
    unknown = "unknown"
    locked = "locked"
    unavailable = "unavailable"


class MatrixSyncRuntimeStatus(str, Enum):
    ready = "ready"
    configuration_required = "configuration_required"
    blocked = "blocked"
    unavailable = "unavailable"
    unknown = "unknown"


class MatrixSyncReadinessStatus(str, Enum):
    ready = "ready"
    blocked = "blocked"
    stale = "stale"
    unknown = "unknown"


class MatrixSyncDependencyStatus(str, Enum):
    ready = "ready"
    unavailable = "unavailable"
    locked = "locked"
    unknown = "unknown"


_MATRIX_SYNC_READINESS_MAX_LIFETIME = timedelta(minutes=2)
_MATRIX_SYNC_READINESS_FUTURE_TOLERANCE = timedelta(seconds=1)


class MatrixSyncCommand(_MatrixSyncModel):
    schema_version: Literal["uaa-matrix-sync.v1"] = MATRIX_SYNC_SCHEMA_VERSION
    operation: MatrixSyncOperation
    request_ref: str = Field(..., max_length=240)
    task_ref: str = Field(..., max_length=240)
    mission_ref: str = Field(..., max_length=240)
    run_ref: str = Field(..., max_length=240)
    dispatch_ref: str = Field(..., max_length=240)
    idempotency_ref: str = Field(..., max_length=240)
    lease_ref: str = Field(..., max_length=240)
    homeserver_ref: str = Field(..., max_length=240)
    endpoint_class_ref: str = Field(..., max_length=240)
    account_ref: str = Field(..., max_length=240)
    device_ref: str = Field(..., max_length=240)
    session_ref: str = Field(..., max_length=240)
    session_generation_ref: str = Field(..., max_length=240)
    credential_item_ref: str = Field(..., max_length=240)
    credential_version_ref: str = Field(..., max_length=240)
    room_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=MATRIX_SYNC_MAX_ROOMS)
    event_class_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    sync_cursor_ref: str = Field(..., max_length=240)
    pagination_cursor_ref: str | None = Field(default=None, max_length=240)
    cache_ref: str = Field(..., max_length=240)
    cache_schema_ref: str = MATRIX_SYNC_CACHE_SCHEMA_REF
    cache_generation_ref: str = Field(..., max_length=240)
    cache_key_item_ref: str = Field(..., max_length=240)
    cache_key_version_ref: str = Field(..., max_length=240)
    next_cache_key_version_ref: str | None = Field(default=None, max_length=240)
    retention_ref: str = MATRIX_SYNC_RETENTION_REF
    backup_posture_ref: str = MATRIX_SYNC_BACKUP_POSTURE_REF
    target_ref: str = MATRIX_SYNC_TARGET_REF
    provider_ref: str = MATRIX_SYNC_PROVIDER_REF
    credential_backend_ref: str = MATRIX_SYNC_CREDENTIAL_BACKEND_REF
    cache_backend_ref: str = MATRIX_SYNC_CACHE_BACKEND_REF
    budget_ref: str = MATRIX_SYNC_BUDGET_REF
    kill_switch_ref: str = MATRIX_SYNC_KILL_SWITCH_REF
    safe_disable_ref: str = MATRIX_SYNC_SAFE_DISABLE_REF
    readiness_ref: str = Field(..., max_length=240)
    rollback_ref: str = Field(..., max_length=240)
    max_events: int = Field(default=MATRIX_SYNC_MAX_EVENTS, ge=1, le=MATRIX_SYNC_MAX_EVENTS)
    max_bytes: int = Field(default=MATRIX_SYNC_MAX_BYTES, ge=1, le=MATRIX_SYNC_MAX_BYTES)
    max_duration_ms: int = Field(default=10_000, ge=100, le=30_000)
    max_cost_microusd: int = Field(default=0, ge=0, le=0)
    request_created_at: datetime
    start_deadline: datetime
    request_fingerprint_ref: str = Field(..., max_length=240)

    @model_validator(mode="after")
    def validate_command(self) -> "MatrixSyncCommand":
        refs = (
            self.request_ref, self.task_ref, self.mission_ref, self.run_ref,
            self.dispatch_ref, self.idempotency_ref, self.lease_ref,
            self.homeserver_ref, self.endpoint_class_ref, self.account_ref,
            self.device_ref, self.session_ref, self.session_generation_ref,
            self.credential_item_ref, self.credential_version_ref,
            *self.room_refs, *self.event_class_refs, self.sync_cursor_ref,
            self.pagination_cursor_ref, self.cache_ref, self.cache_schema_ref,
            self.cache_generation_ref, self.cache_key_item_ref,
            self.cache_key_version_ref, self.next_cache_key_version_ref,
            self.retention_ref, self.backup_posture_ref, self.target_ref,
            self.provider_ref, self.credential_backend_ref, self.cache_backend_ref,
            self.budget_ref, self.kill_switch_ref, self.safe_disable_ref,
            self.readiness_ref, self.rollback_ref, self.request_fingerprint_ref,
        )
        for value in refs:
            if value is not None:
                validate_execution_ref(value, "matrix_sync_command_ref")
        if len(self.room_refs) != len(set(self.room_refs)):
            raise ValueError("MATRIX_SYNC_DUPLICATE_ROOM_REF")
        if len(self.event_class_refs) != len(set(self.event_class_refs)):
            raise ValueError("MATRIX_SYNC_DUPLICATE_EVENT_CLASS_REF")
        expected_static = {
            "cache_schema_ref": MATRIX_SYNC_CACHE_SCHEMA_REF,
            "retention_ref": MATRIX_SYNC_RETENTION_REF,
            "backup_posture_ref": MATRIX_SYNC_BACKUP_POSTURE_REF,
            "target_ref": MATRIX_SYNC_TARGET_REF,
            "provider_ref": MATRIX_SYNC_PROVIDER_REF,
            "credential_backend_ref": MATRIX_SYNC_CREDENTIAL_BACKEND_REF,
            "cache_backend_ref": MATRIX_SYNC_CACHE_BACKEND_REF,
            "budget_ref": MATRIX_SYNC_BUDGET_REF,
            "kill_switch_ref": MATRIX_SYNC_KILL_SWITCH_REF,
            "safe_disable_ref": MATRIX_SYNC_SAFE_DISABLE_REF,
        }
        for name, value in expected_static.items():
            if getattr(self, name) != value:
                raise ValueError(f"MATRIX_SYNC_{name.upper()}_SUBSTITUTION_DENIED")
        if self.request_created_at.tzinfo is None or self.start_deadline.tzinfo is None:
            raise ValueError("MATRIX_SYNC_TIMEZONE_REQUIRED")
        if self.request_created_at >= self.start_deadline:
            raise ValueError("MATRIX_SYNC_DEADLINE_ORDER_INVALID")
        if self.operation == MatrixSyncOperation.timeline_paginate_read:
            if len(self.room_refs) != 1 or not self.pagination_cursor_ref:
                raise ValueError("MATRIX_SYNC_EXACT_PAGINATION_SCOPE_REQUIRED")
        elif self.pagination_cursor_ref is not None:
            raise ValueError("MATRIX_SYNC_PAGINATION_SCOPE_FORBIDDEN")
        if self.operation in {
            MatrixSyncOperation.room_state_read,
            MatrixSyncOperation.receipt_project_read,
            MatrixSyncOperation.typing_project_read,
        } and not self.room_refs:
            raise ValueError("MATRIX_SYNC_ROOM_SCOPE_REQUIRED")
        if self.operation == MatrixSyncOperation.cache_key_rotate:
            if not self.next_cache_key_version_ref:
                raise ValueError("MATRIX_SYNC_NEXT_KEY_VERSION_REQUIRED")
            if self.next_cache_key_version_ref == self.cache_key_version_ref:
                raise ValueError("MATRIX_SYNC_KEY_VERSION_REUSE_DENIED")
        elif self.next_cache_key_version_ref is not None:
            raise ValueError("MATRIX_SYNC_NEXT_KEY_VERSION_FORBIDDEN")
        if self.operation in {
            MatrixSyncOperation.sync_read,
            MatrixSyncOperation.timeline_paginate_read,
            MatrixSyncOperation.room_state_read,
        } and not self.event_class_refs:
            raise ValueError("MATRIX_SYNC_EVENT_SCOPE_REQUIRED")
        expected = matrix_sync_request_fingerprint_ref(
            **self.model_dump(mode="python", exclude={"request_fingerprint_ref"})
        )
        if self.request_fingerprint_ref != expected:
            raise ValueError("MATRIX_SYNC_REQUEST_FINGERPRINT_MISMATCH")
        return self


class MatrixSyncReadinessObservation(_MatrixSyncModel):
    schema_version: Literal["uaa-matrix-sync-readiness.v1"] = (
        "uaa-matrix-sync-readiness.v1"
    )
    observation_ref: str = Field(..., max_length=240)
    request_fingerprint_ref: str = Field(..., max_length=240)
    readiness_ref: str = Field(..., max_length=240)
    provider_ref: Literal["provider-ref:communications:matrix"] = (
        MATRIX_SYNC_PROVIDER_REF
    )
    adapter_ref: str = Field(..., max_length=240)
    status: MatrixSyncReadinessStatus
    adapter_status: MatrixSyncDependencyStatus
    credential_status: MatrixSyncDependencyStatus
    cache_status: MatrixSyncDependencyStatus
    kill_switch_engaged: StrictBool
    safe_disable_active: StrictBool
    observed_at: datetime
    expires_at: datetime
    reason_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    raw_content_included: Literal[False] = False
    redaction_status: Literal["safe_refs_only"] = "safe_refs_only"

    @model_validator(mode="after")
    def validate_observation(self) -> "MatrixSyncReadinessObservation":
        for value in (
            self.observation_ref,
            self.request_fingerprint_ref,
            self.readiness_ref,
            self.provider_ref,
            self.adapter_ref,
            *self.reason_refs,
        ):
            validate_execution_ref(value, "matrix_sync_readiness_ref")
        if self.observed_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("MATRIX_SYNC_READINESS_TIMEZONE_REQUIRED")
        if self.observed_at >= self.expires_at:
            raise ValueError("MATRIX_SYNC_READINESS_EXPIRY_INVALID")
        now = datetime.now(timezone.utc)
        if self.observed_at > now + _MATRIX_SYNC_READINESS_FUTURE_TOLERANCE:
            raise ValueError("MATRIX_SYNC_READINESS_OBSERVED_IN_FUTURE")
        if self.expires_at - self.observed_at > _MATRIX_SYNC_READINESS_MAX_LIFETIME:
            raise ValueError("MATRIX_SYNC_READINESS_LIFETIME_EXCEEDED")
        expected_ref = matrix_sync_readiness_observation_ref(
            **self.model_dump(mode="python", exclude={"observation_ref"})
        )
        if self.observation_ref != expected_ref:
            raise ValueError("MATRIX_SYNC_READINESS_OBSERVATION_REF_MISMATCH")
        if self.status == MatrixSyncReadinessStatus.ready:
            if (
                self.adapter_status != MatrixSyncDependencyStatus.ready
                or self.credential_status != MatrixSyncDependencyStatus.ready
                or self.cache_status != MatrixSyncDependencyStatus.ready
                or self.kill_switch_engaged
                or self.safe_disable_active
                or self.reason_refs
            ):
                raise ValueError("MATRIX_SYNC_READY_OBSERVATION_INVALID")
        return self


class MatrixSyncReceipt(_MatrixSyncModel):
    schema_version: Literal["uaa-matrix-sync-receipt.v1"] = "uaa-matrix-sync-receipt.v1"
    receipt_ref: str
    operation: MatrixSyncOperation
    request_fingerprint_ref: str
    account_ref: str
    cache_ref: str
    status: Literal["succeeded", "blocked", "failed", "replayed"]
    freshness: MatrixSyncFreshness
    reason_refs: tuple[str, ...] = ()
    blocker_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    event_count: int = Field(default=0, ge=0, le=MATRIX_SYNC_MAX_EVENTS)
    byte_count: int = Field(default=0, ge=0, le=MATRIX_SYNC_MAX_BYTES)
    network_read_performed: StrictBool
    local_cache_mutated: StrictBool
    external_write_performed: Literal[False] = False
    raw_content_included: Literal[False] = False
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True
    redaction_status: Literal["safe_refs_only"] = "safe_refs_only"
    created_at: datetime

    @model_validator(mode="after")
    def validate_receipt(self) -> "MatrixSyncReceipt":
        for value in (
            self.receipt_ref, self.request_fingerprint_ref, self.account_ref,
            self.cache_ref, *self.reason_refs, *self.blocker_refs, *self.evidence_refs,
        ):
            validate_execution_ref(value, "matrix_sync_receipt_ref")
        lane = matrix_sync_lane(self.operation)
        if self.network_read_performed != lane.network_read:
            if self.status == "succeeded":
                raise ValueError("MATRIX_SYNC_NETWORK_RECEIPT_MISMATCH")
        if self.local_cache_mutated != (self.operation in {
            MatrixSyncOperation.cache_write,
            MatrixSyncOperation.cache_migrate,
            MatrixSyncOperation.cache_purge,
            MatrixSyncOperation.cache_key_create,
            MatrixSyncOperation.cache_key_rotate,
            MatrixSyncOperation.cache_key_delete,
        }) and self.status == "succeeded":
            raise ValueError("MATRIX_SYNC_CACHE_RECEIPT_MISMATCH")
        return self


class MatrixSyncPosture(_MatrixSyncModel):
    schema_version: Literal["uaa-matrix-sync-posture.v1"] = "uaa-matrix-sync-posture.v1"
    provider_ref: Literal["provider-ref:communications:matrix"] = MATRIX_SYNC_PROVIDER_REF
    adapter_ref: str
    runtime_status: MatrixSyncRuntimeStatus
    freshness: MatrixSyncFreshness
    credential_posture_ref: str
    cache_posture_ref: str
    authority_lane_refs: tuple[str, ...]
    concrete_transport_operation_refs: tuple[str, ...]
    uncomposed_executor_operation_refs: tuple[str, ...]
    blocker_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safe_summary: str = Field(..., max_length=500)
    sync_enabled: StrictBool
    connector_writes_enabled: Literal[False] = False
    message_sends_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    encrypted_content_materialization_enabled: Literal[False] = False
    content_untrusted: Literal[True] = True
    not_instruction_authority: Literal[True] = True
    raw_content_included: Literal[False] = False
    desktop_only: Literal[True] = True

    @model_validator(mode="after")
    def validate_posture(self) -> "MatrixSyncPosture":
        for value in (
            self.adapter_ref, self.credential_posture_ref, self.cache_posture_ref,
            *self.authority_lane_refs, *self.concrete_transport_operation_refs,
            *self.uncomposed_executor_operation_refs, *self.blocker_refs,
            *self.evidence_refs,
        ):
            validate_execution_ref(value, "matrix_sync_posture_ref")
        expected_composed = {
            f"operation-ref:matrix-sync:{operation.value.replace('_', '-')}"
            for operation in MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS
        }
        expected_uncomposed = {
            f"operation-ref:matrix-sync:{operation.value.replace('_', '-')}"
            for operation in set(MatrixSyncOperation)
            - MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS
        }
        if set(self.concrete_transport_operation_refs) != expected_composed:
            raise ValueError("MATRIX_SYNC_CONCRETE_TRANSPORT_TRUTH_MISMATCH")
        if set(self.uncomposed_executor_operation_refs) != expected_uncomposed:
            raise ValueError("MATRIX_SYNC_UNCOMPOSED_EXECUTOR_TRUTH_MISMATCH")
        if self.sync_enabled != (self.runtime_status == MatrixSyncRuntimeStatus.ready):
            raise ValueError("MATRIX_SYNC_POSTURE_READINESS_MISMATCH")
        if self.runtime_status == MatrixSyncRuntimeStatus.ready:
            if self.freshness != MatrixSyncFreshness.current or self.blocker_refs:
                raise ValueError("MATRIX_SYNC_READY_TRUTH_INVALID")
        elif self.runtime_status == MatrixSyncRuntimeStatus.configuration_required:
            if not self.blocker_refs:
                raise ValueError("MATRIX_SYNC_CONFIGURATION_BLOCKER_REQUIRED")
        return self


class MatrixSyncDispatchMetadata(_MatrixSyncModel):
    command: MatrixSyncCommand
    start_deadline_ref: str
    target_ref: str = MATRIX_SYNC_TARGET_REF
    provider_ref: str = MATRIX_SYNC_PROVIDER_REF

    @model_validator(mode="after")
    def validate_metadata(self) -> "MatrixSyncDispatchMetadata":
        for value in (self.start_deadline_ref, self.target_ref, self.provider_ref):
            validate_execution_ref(value, "matrix_sync_dispatch_metadata_ref")
        if self.start_deadline_ref != matrix_sync_start_deadline_ref(
            self.command.start_deadline
        ):
            raise ValueError("MATRIX_SYNC_DISPATCH_DEADLINE_BINDING_MISMATCH")
        return self


def matrix_sync_request_fingerprint_ref(**values: object) -> str:
    payload = {
        "room_refs": (),
        "event_class_refs": (),
        "pagination_cursor_ref": None,
        "cache_schema_ref": MATRIX_SYNC_CACHE_SCHEMA_REF,
        "next_cache_key_version_ref": None,
        "retention_ref": MATRIX_SYNC_RETENTION_REF,
        "backup_posture_ref": MATRIX_SYNC_BACKUP_POSTURE_REF,
        "target_ref": MATRIX_SYNC_TARGET_REF,
        "provider_ref": MATRIX_SYNC_PROVIDER_REF,
        "credential_backend_ref": MATRIX_SYNC_CREDENTIAL_BACKEND_REF,
        "cache_backend_ref": MATRIX_SYNC_CACHE_BACKEND_REF,
        "budget_ref": MATRIX_SYNC_BUDGET_REF,
        "kill_switch_ref": MATRIX_SYNC_KILL_SWITCH_REF,
        "safe_disable_ref": MATRIX_SYNC_SAFE_DISABLE_REF,
        "max_events": MATRIX_SYNC_MAX_EVENTS,
        "max_bytes": MATRIX_SYNC_MAX_BYTES,
        "max_duration_ms": 10_000,
        "max_cost_microusd": 0,
        **values,
    }
    operation = MatrixSyncOperation(payload.pop("operation"))
    payload.pop("schema_version", None)
    return stable_matrix_sync_ref(
        "request-fingerprint-ref:matrix-sync",
        {"operation": operation.value, **payload},
    )


def matrix_sync_readiness_observation_ref(**values: object) -> str:
    payload = dict(values)
    payload.pop("schema_version", None)
    return stable_matrix_sync_ref("readiness-observation-ref:matrix-sync", payload)


def build_matrix_sync_readiness_observation(
    command: MatrixSyncCommand,
    *,
    observed_at: datetime,
    expires_at: datetime,
    status: MatrixSyncReadinessStatus = MatrixSyncReadinessStatus.ready,
    adapter_status: MatrixSyncDependencyStatus = MatrixSyncDependencyStatus.ready,
    credential_status: MatrixSyncDependencyStatus = MatrixSyncDependencyStatus.ready,
    cache_status: MatrixSyncDependencyStatus = MatrixSyncDependencyStatus.ready,
    kill_switch_engaged: bool = False,
    safe_disable_active: bool = False,
    reason_refs: tuple[str, ...] = (),
) -> MatrixSyncReadinessObservation:
    values: dict[str, object] = {
        "request_fingerprint_ref": command.request_fingerprint_ref,
        "readiness_ref": command.readiness_ref,
        "provider_ref": command.provider_ref,
        "adapter_ref": matrix_sync_lane(command.operation).adapter_ref,
        "status": status,
        "adapter_status": adapter_status,
        "credential_status": credential_status,
        "cache_status": cache_status,
        "kill_switch_engaged": kill_switch_engaged,
        "safe_disable_active": safe_disable_active,
        "observed_at": observed_at,
        "expires_at": expires_at,
        "reason_refs": reason_refs,
        "raw_content_included": False,
        "redaction_status": "safe_refs_only",
    }
    values["observation_ref"] = matrix_sync_readiness_observation_ref(**values)
    return MatrixSyncReadinessObservation(**values)


def matrix_sync_start_deadline_ref(value: datetime) -> str:
    return stable_matrix_sync_ref(
        "start-deadline-ref:matrix-sync", {"start_deadline": value.isoformat()}
    )


def matrix_sync_exact_resource_refs(command: MatrixSyncCommand) -> tuple[str, ...]:
    lane = matrix_sync_lane(command.operation)
    refs = {
        lane.lane_ref, lane.capability_ref, lane.adapter_ref, lane.tool_ref,
        command.request_ref, command.task_ref, command.mission_ref, command.run_ref,
        command.dispatch_ref, command.idempotency_ref, command.lease_ref,
        command.homeserver_ref, command.endpoint_class_ref, command.account_ref,
        command.device_ref, command.session_ref, command.session_generation_ref,
        command.credential_item_ref, command.credential_version_ref,
        *command.room_refs, *command.event_class_refs, command.sync_cursor_ref,
        command.cache_ref, command.cache_schema_ref, command.cache_generation_ref,
        command.cache_key_item_ref, command.cache_key_version_ref,
        command.retention_ref, command.backup_posture_ref, command.target_ref,
        command.provider_ref, command.credential_backend_ref,
        command.cache_backend_ref, command.budget_ref, command.kill_switch_ref,
        command.safe_disable_ref, command.readiness_ref, command.rollback_ref,
        command.request_fingerprint_ref,
        matrix_sync_start_deadline_ref(command.start_deadline),
    }
    if command.pagination_cursor_ref:
        refs.add(command.pagination_cursor_ref)
    if command.next_cache_key_version_ref:
        refs.add(command.next_cache_key_version_ref)
    return tuple(sorted(refs))
