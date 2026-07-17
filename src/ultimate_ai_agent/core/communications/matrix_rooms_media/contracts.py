from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .constants import (
    MATRIX_MEDIA_CANCEL_POLICY_REF,
    MATRIX_MEDIA_PREVIEW_POLICY_REF,
    MATRIX_MEDIA_PROGRESS_POLICY_REF,
    MATRIX_MEDIA_QUARANTINE_POLICY_REF,
    MATRIX_MEDIA_RETRY_POLICY_REF,
    MATRIX_MEDIA_ROOT_POLICY_REF,
    MATRIX_ROOMS_MEDIA_BUDGET_REF,
    MATRIX_ROOMS_MEDIA_KILL_SWITCH_REF,
    MATRIX_ROOMS_MEDIA_LIMIT_POLICY_REF,
    MATRIX_ROOMS_MEDIA_PROVIDER_REF,
    MATRIX_ROOMS_MEDIA_RETENTION_REF,
    MATRIX_ROOMS_MEDIA_RUNTIME_REF,
    MATRIX_ROOMS_MEDIA_SAFE_DISABLE_REF,
    MATRIX_ROOMS_MEDIA_SCHEMA_VERSION,
    MATRIX_ROOMS_MEDIA_TARGET_REF,
    MATRIX_SEARCH_INDEX_POLICY_REF,
    MEDIA_OPERATIONS,
    MatrixRoomsMediaOperation,
    matrix_rooms_media_lane,
    matrix_rooms_media_rollback_ref,
)


_OPERATION_SCOPE_FIELDS: dict[MatrixRoomsMediaOperation, frozenset[str]] = {
    MatrixRoomsMediaOperation.dm_create: frozenset({"member_ref", "transaction_ref"}),
    MatrixRoomsMediaOperation.room_create: frozenset(
        {"desired_state_ref", "transaction_ref"}
    ),
    MatrixRoomsMediaOperation.room_join: frozenset(
        {"room_ref", "transaction_ref", "prior_state_ref"}
    ),
    MatrixRoomsMediaOperation.room_leave: frozenset(
        {"room_ref", "transaction_ref", "prior_state_ref"}
    ),
    MatrixRoomsMediaOperation.invite_send: frozenset(
        {"room_ref", "member_ref", "transaction_ref", "prior_state_ref"}
    ),
    MatrixRoomsMediaOperation.invite_accept: frozenset(
        {"room_ref", "transaction_ref", "prior_state_ref"}
    ),
    MatrixRoomsMediaOperation.invite_reject: frozenset(
        {"room_ref", "transaction_ref", "prior_state_ref"}
    ),
    MatrixRoomsMediaOperation.invite_withdraw: frozenset(
        {"room_ref", "member_ref", "transaction_ref", "prior_state_ref"}
    ),
    MatrixRoomsMediaOperation.room_power_role_write: frozenset(
        {
            "room_ref",
            "member_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        }
    ),
    MatrixRoomsMediaOperation.space_mapping_write: frozenset(
        {
            "room_ref",
            "space_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        }
    ),
    MatrixRoomsMediaOperation.notification_settings_write: frozenset(
        {"room_ref", "prior_state_ref", "desired_state_ref", "transaction_ref"}
    ),
    MatrixRoomsMediaOperation.history_visibility_write: frozenset(
        {"room_ref", "prior_state_ref", "desired_state_ref", "transaction_ref"}
    ),
    MatrixRoomsMediaOperation.pin_write: frozenset(
        {
            "room_ref",
            "event_ref",
            "prior_state_ref",
            "desired_state_ref",
            "transaction_ref",
        }
    ),
    MatrixRoomsMediaOperation.account_room_preference_write: frozenset(
        {"room_ref", "prior_state_ref", "desired_state_ref", "transaction_ref"}
    ),
    MatrixRoomsMediaOperation.search_local_read: frozenset(
        {"room_ref", "search_index_ref", "query_ref", "room_allowlist_ref"}
    ),
    MatrixRoomsMediaOperation.media_upload: frozenset(
        {
            "room_ref",
            "media_ref",
            "source_file_ref",
            "filesystem_root_ref",
            "declared_media_type_ref",
            "transaction_ref",
        }
    ),
    MatrixRoomsMediaOperation.media_download_quarantine: frozenset(
        {
            "room_ref",
            "event_ref",
            "media_ref",
            "quarantine_ref",
            "filesystem_root_ref",
            "declared_media_type_ref",
            "transaction_ref",
        }
    ),
    MatrixRoomsMediaOperation.media_materialize: frozenset(
        {
            "media_ref",
            "quarantine_ref",
            "materialization_ref",
            "filesystem_root_ref",
            "declared_media_type_ref",
        }
    ),
    MatrixRoomsMediaOperation.media_preview: frozenset(
        {
            "media_ref",
            "quarantine_ref",
            "filesystem_root_ref",
            "parser_ref",
            "declared_media_type_ref",
        }
    ),
    MatrixRoomsMediaOperation.media_cleanup: frozenset(
        {
            "media_ref",
            "quarantine_ref",
            "materialization_ref",
            "filesystem_root_ref",
            "prior_state_ref",
            "declared_media_type_ref",
        }
    ),
}

_OPTIONAL_OPERATION_SCOPE_FIELDS: dict[MatrixRoomsMediaOperation, frozenset[str]] = {
    MatrixRoomsMediaOperation.search_local_read: frozenset({"room_ref"}),
    MatrixRoomsMediaOperation.media_cleanup: frozenset({"materialization_ref"}),
}
_ALL_OPERATION_SCOPE_FIELDS = frozenset().union(*_OPERATION_SCOPE_FIELDS.values())


def stable_matrix_rooms_media_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode()
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixRoomsMediaCommand(_Model):
    schema_version: Literal["uaa-matrix-rooms-media.v1"] = (
        MATRIX_ROOMS_MEDIA_SCHEMA_VERSION
    )
    operation: MatrixRoomsMediaOperation
    request_ref: str = Field(max_length=240)
    task_ref: str = Field(max_length=240)
    mission_ref: str = Field(max_length=240)
    run_ref: str = Field(max_length=240)
    dispatch_ref: str = Field(max_length=240)
    idempotency_ref: str = Field(max_length=240)
    lease_ref: str = Field(max_length=240)
    account_ref: str = Field(max_length=240)
    homeserver_ref: str = Field(max_length=240)
    device_ref: str = Field(max_length=240)
    room_ref: str | None = Field(default=None, max_length=240)
    member_ref: str | None = Field(default=None, max_length=240)
    event_ref: str | None = Field(default=None, max_length=240)
    transaction_ref: str | None = Field(default=None, max_length=240)
    space_ref: str | None = Field(default=None, max_length=240)
    media_ref: str | None = Field(default=None, max_length=240)
    source_file_ref: str | None = Field(default=None, max_length=240)
    quarantine_ref: str | None = Field(default=None, max_length=240)
    materialization_ref: str | None = Field(default=None, max_length=240)
    filesystem_root_ref: str | None = Field(default=None, max_length=240)
    search_index_ref: str | None = Field(default=None, max_length=240)
    query_ref: str | None = Field(default=None, max_length=240)
    room_allowlist_ref: str | None = Field(default=None, max_length=240)
    prior_state_ref: str | None = Field(default=None, max_length=240)
    desired_state_ref: str | None = Field(default=None, max_length=240)
    declared_media_type_ref: str | None = Field(default=None, max_length=240)
    parser_ref: Literal["parser-ref:matrix-media:metadata-only-v1"] | None = None
    target_ref: Literal["target-ref:communications:matrix-rooms-media-exact-scope"] = (
        MATRIX_ROOMS_MEDIA_TARGET_REF
    )
    provider_ref: Literal["provider-ref:communications:matrix"] = (
        MATRIX_ROOMS_MEDIA_PROVIDER_REF
    )
    runtime_ref: Literal["runtime-ref:matrix-rust-sdk:0.18.0"] = (
        MATRIX_ROOMS_MEDIA_RUNTIME_REF
    )
    media_root_policy_ref: Literal[
        "filesystem-root-policy-ref:matrix-media:app-owned-v1"
    ] = MATRIX_MEDIA_ROOT_POLICY_REF
    quarantine_policy_ref: Literal[
        "quarantine-policy-ref:matrix-media:before-preview-v1"
    ] = MATRIX_MEDIA_QUARANTINE_POLICY_REF
    preview_policy_ref: Literal[
        "preview-policy-ref:matrix-media:metadata-allowlist-v1"
    ] = MATRIX_MEDIA_PREVIEW_POLICY_REF
    progress_policy_ref: Literal["progress-policy-ref:matrix-media:content-free-v1"] = (
        MATRIX_MEDIA_PROGRESS_POLICY_REF
    )
    cancel_policy_ref: Literal[
        "cancel-policy-ref:matrix-media:bounded-process-termination-v1"
    ] = MATRIX_MEDIA_CANCEL_POLICY_REF
    retry_policy_ref: Literal[
        "retry-policy-ref:matrix-media:manual-idempotent-no-auto-uncertain-v1"
    ] = MATRIX_MEDIA_RETRY_POLICY_REF
    search_index_policy_ref: Literal[
        "search-index-policy-ref:matrix:encrypted-hmac-v1"
    ] = MATRIX_SEARCH_INDEX_POLICY_REF
    retention_ref: Literal["retention-ref:matrix-rooms-media:bounded-v1"] = (
        MATRIX_ROOMS_MEDIA_RETENTION_REF
    )
    limit_policy_ref: Literal["limit-policy-ref:matrix-rooms-media:bounded-v1"] = (
        MATRIX_ROOMS_MEDIA_LIMIT_POLICY_REF
    )
    budget_ref: Literal["budget-ref:matrix-rooms-media:zero-cost-v1"] = (
        MATRIX_ROOMS_MEDIA_BUDGET_REF
    )
    readiness_ref: str = Field(max_length=240)
    safe_disable_ref: Literal["safe-disable-ref:matrix-messenger:enabled"] = (
        MATRIX_ROOMS_MEDIA_SAFE_DISABLE_REF
    )
    kill_switch_ref: Literal["kill-switch-ref:matrix-messenger:clear"] = (
        MATRIX_ROOMS_MEDIA_KILL_SWITCH_REF
    )
    rollback_ref: str = Field(max_length=240)
    max_bytes: int = Field(default=24_576, ge=1, le=24_576)
    max_result_count: int = Field(default=50, ge=1, le=100)
    request_created_at: datetime
    start_deadline: datetime
    max_duration_ms: int = Field(default=30_000, ge=100, le=300_000)
    max_cost_microusd: Literal[0] = 0
    request_fingerprint_ref: str = Field(max_length=240)
    human_commanded: Literal[True] = True
    autonomous_action: Literal[False] = False

    @model_validator(mode="after")
    def validate_command(self) -> MatrixRoomsMediaCommand:
        for name, value in self.model_dump(mode="python").items():
            if name in {"schema_version", "operation"}:
                continue
            if isinstance(value, str):
                validate_execution_ref(value, f"matrix_rooms_media_{name}")
        if self.request_created_at.tzinfo is None or self.start_deadline.tzinfo is None:
            raise ValueError("MATRIX_ROOMS_MEDIA_TIMEZONE_REQUIRED")
        if not self.request_created_at < self.start_deadline:
            raise ValueError("MATRIX_ROOMS_MEDIA_DEADLINE_ORDER_INVALID")
        if self.start_deadline - self.request_created_at > timedelta(minutes=5):
            raise ValueError("MATRIX_ROOMS_MEDIA_DEADLINE_WINDOW_EXCEEDED")
        self._validate_operation_scope()
        if self.rollback_ref != matrix_rooms_media_rollback_ref(self.operation):
            raise ValueError("MATRIX_ROOMS_MEDIA_ROLLBACK_POSTURE_MISMATCH")
        expected = matrix_rooms_media_request_fingerprint_ref(
            **self.model_dump(mode="python", exclude={"request_fingerprint_ref"})
        )
        if self.request_fingerprint_ref != expected:
            raise ValueError("MATRIX_ROOMS_MEDIA_REQUEST_FINGERPRINT_MISMATCH")
        return self

    def _validate_operation_scope(self) -> None:
        allowed = _OPERATION_SCOPE_FIELDS[self.operation]
        optional = _OPTIONAL_OPERATION_SCOPE_FIELDS.get(self.operation, frozenset())
        required = allowed - optional
        missing = [name for name in required if getattr(self, name) is None]
        if missing:
            raise ValueError("MATRIX_ROOMS_MEDIA_EXACT_SCOPE_REQUIRED")
        forbidden = [
            name
            for name in _ALL_OPERATION_SCOPE_FIELDS - allowed
            if getattr(self, name) is not None
        ]
        if forbidden:
            raise ValueError("MATRIX_ROOMS_MEDIA_EXTRANEOUS_SCOPE_FORBIDDEN")
        if self.operation in MEDIA_OPERATIONS and self.filesystem_root_ref is None:
            raise ValueError("MATRIX_ROOMS_MEDIA_FILESYSTEM_ROOT_REQUIRED")


class MatrixRoomsMediaReadiness(_Model):
    readiness_ref: str
    request_fingerprint_ref: str
    adapter_ref: str
    status: Literal["ready", "blocked", "unknown"]
    observed_at: datetime
    expires_at: datetime
    kill_switch_engaged: StrictBool
    safe_disable_active: StrictBool
    broker_integrity_verified: StrictBool
    filesystem_root_verified: StrictBool
    encrypted_index_available: StrictBool
    reason_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)

    @model_validator(mode="after")
    def validate_readiness(self) -> MatrixRoomsMediaReadiness:
        for value in (
            self.readiness_ref,
            self.request_fingerprint_ref,
            self.adapter_ref,
            *self.reason_refs,
        ):
            validate_execution_ref(value, "matrix_rooms_media_readiness_ref")
        ready = (
            not self.kill_switch_engaged
            and not self.safe_disable_active
            and self.broker_integrity_verified
            and self.filesystem_root_verified
            and self.encrypted_index_available
        )
        if self.observed_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("MATRIX_ROOMS_MEDIA_READINESS_TIMEZONE_REQUIRED")
        if (
            not self.observed_at < self.expires_at
            or self.expires_at - self.observed_at > timedelta(seconds=60)
        ):
            raise ValueError("MATRIX_ROOMS_MEDIA_READINESS_WINDOW_INVALID")
        if (self.status == "ready") != ready:
            raise ValueError("MATRIX_ROOMS_MEDIA_READINESS_STATUS_MISMATCH")
        return self


class MatrixRoomsMediaProposal(_Model):
    schema_version: Literal["uaa-matrix-rooms-media-proposal.v1"] = (
        "uaa-matrix-rooms-media-proposal.v1"
    )
    proposal_ref: str
    operation: MatrixRoomsMediaOperation
    request_fingerprint_ref: str
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    target_ref: str
    lease_ref: str
    idempotency_ref: str
    side_effect_class: str
    request_scoped_evaluation_required: Literal[True] = True
    approval_ref_authorizes_execution: Literal[False] = False
    execution_permitted: Literal[False] = False
    mutation_performed: Literal[False] = False
    raw_content_included: Literal[False] = False
    safe_summary: str = Field(min_length=1, max_length=240)


class MatrixRoomsMediaPosture(_Model):
    schema_version: Literal["uaa-matrix-rooms-media-posture.v1"] = (
        "uaa-matrix-rooms-media-posture.v1"
    )
    posture_ref: str
    runtime_status: Literal["configuration_required"] = "configuration_required"
    authority_lane_refs: tuple[str, ...]
    implemented_core_operation_refs: tuple[str, ...]
    blocked_live_operation_refs: tuple[str, ...]
    media_max_bytes: Literal[24576] = 24_576
    media_type_policy_ref: str
    quarantine_policy_ref: str
    preview_policy_ref: str
    progress_policy_ref: str
    cancel_policy_ref: str
    retry_policy_ref: str
    search_index_policy_ref: str
    element_interoperability_status: Literal["external_facility_required"] = (
        "external_facility_required"
    )
    reason_refs: tuple[str, ...]
    request_scoped_evaluation_required: Literal[True] = True
    standing_authority_granted: Literal[False] = False
    multi_account_enabled: Literal[False] = False
    raw_content_included: Literal[False] = False


class MatrixRoomsMediaDispatchMetadata(_Model):
    command: MatrixRoomsMediaCommand
    start_deadline_ref: str

    @model_validator(mode="after")
    def validate_metadata(self) -> MatrixRoomsMediaDispatchMetadata:
        expected = matrix_rooms_media_start_deadline_ref(self.command.start_deadline)
        if self.start_deadline_ref != expected:
            raise ValueError("MATRIX_ROOMS_MEDIA_START_DEADLINE_REF_MISMATCH")
        return self


def matrix_rooms_media_request_fingerprint_ref(**payload: object) -> str:
    return stable_matrix_rooms_media_ref(
        "request-fingerprint-ref:matrix-rooms-media", payload
    )


def build_matrix_rooms_media_command(**payload: object) -> MatrixRoomsMediaCommand:
    candidate = MatrixRoomsMediaCommand.model_construct(
        **payload,
        request_fingerprint_ref="request-fingerprint-ref:matrix-rooms-media:pending",
    )
    normalized = candidate.model_dump(
        mode="python", exclude={"request_fingerprint_ref"}
    )
    normalized["request_fingerprint_ref"] = matrix_rooms_media_request_fingerprint_ref(
        **normalized
    )
    return MatrixRoomsMediaCommand.model_validate(normalized)


def build_matrix_rooms_media_proposal(
    command: MatrixRoomsMediaCommand,
) -> MatrixRoomsMediaProposal:
    lane = matrix_rooms_media_lane(command.operation)
    values = {
        "operation": command.operation,
        "request_fingerprint_ref": command.request_fingerprint_ref,
        "lane_ref": lane.lane_ref,
        "capability_ref": lane.capability_ref,
        "adapter_ref": lane.adapter_ref,
        "target_ref": command.target_ref,
        "lease_ref": command.lease_ref,
        "idempotency_ref": command.idempotency_ref,
        "side_effect_class": lane.side_effect_class,
        "safe_summary": "Review one exact room, local-search, or media operation; this proposal grants no authority and performs no mutation.",
    }
    values["proposal_ref"] = stable_matrix_rooms_media_ref(
        "proposal-ref:matrix-rooms-media", values
    )
    return MatrixRoomsMediaProposal.model_validate(values)


def matrix_rooms_media_start_deadline_ref(value: datetime) -> str:
    return stable_matrix_rooms_media_ref(
        "start-deadline-ref:matrix-rooms-media", {"value": value.isoformat()}
    )


def matrix_rooms_media_exact_resource_refs(
    command: MatrixRoomsMediaCommand,
) -> tuple[str, ...]:
    lane = matrix_rooms_media_lane(command.operation)
    refs = [
        command.request_ref,
        command.task_ref,
        command.mission_ref,
        command.run_ref,
        command.dispatch_ref,
        command.idempotency_ref,
        command.lease_ref,
        command.account_ref,
        command.homeserver_ref,
        command.device_ref,
        command.target_ref,
        command.provider_ref,
        command.runtime_ref,
        command.media_root_policy_ref,
        command.quarantine_policy_ref,
        command.preview_policy_ref,
        command.progress_policy_ref,
        command.cancel_policy_ref,
        command.retry_policy_ref,
        command.search_index_policy_ref,
        command.retention_ref,
        command.limit_policy_ref,
        command.budget_ref,
        command.readiness_ref,
        command.safe_disable_ref,
        command.kill_switch_ref,
        command.rollback_ref,
        command.request_fingerprint_ref,
        matrix_rooms_media_start_deadline_ref(command.start_deadline),
        lane.lane_ref,
        lane.capability_ref,
        lane.adapter_ref,
        lane.tool_ref,
    ]
    refs.extend(
        value
        for value in (
            command.room_ref,
            command.member_ref,
            command.event_ref,
            command.transaction_ref,
            command.space_ref,
            command.media_ref,
            command.source_file_ref,
            command.quarantine_ref,
            command.materialization_ref,
            command.filesystem_root_ref,
            command.search_index_ref,
            command.query_ref,
            command.room_allowlist_ref,
            command.prior_state_ref,
            command.desired_state_ref,
            command.declared_media_type_ref,
            command.parser_ref,
        )
        if value is not None
    )
    return tuple(dict.fromkeys(refs))


__all__ = [
    "MatrixRoomsMediaCommand",
    "MatrixRoomsMediaDispatchMetadata",
    "MatrixRoomsMediaPosture",
    "MatrixRoomsMediaProposal",
    "MatrixRoomsMediaReadiness",
    "build_matrix_rooms_media_command",
    "build_matrix_rooms_media_proposal",
    "matrix_rooms_media_exact_resource_refs",
    "matrix_rooms_media_request_fingerprint_ref",
    "matrix_rooms_media_start_deadline_ref",
    "stable_matrix_rooms_media_ref",
]
