from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .constants import (
    CONTENT_FINGERPRINT_OPERATIONS,
    EVENT_SCOPED_OPERATIONS,
    MATRIX_MESSAGING_BUDGET_REF,
    MATRIX_MESSAGING_KILL_SWITCH_REF,
    MATRIX_MESSAGING_NOTIFICATION_DISCLOSURE_REF,
    MATRIX_MESSAGING_NOTIFICATION_POLICY_REF,
    MATRIX_MESSAGING_NOTIFICATION_TARGET_REF,
    MATRIX_MESSAGING_OUTBOX_KEY_ITEM_REF,
    MATRIX_MESSAGING_OUTBOX_KEY_VERSION_REF,
    MATRIX_MESSAGING_OUTBOX_SCHEMA_REF,
    MATRIX_MESSAGING_PROVIDER_REF,
    MATRIX_MESSAGING_RUNTIME_REF,
    MATRIX_MESSAGING_SAFE_DISABLE_REF,
    MATRIX_MESSAGING_SCHEMA_VERSION,
    MATRIX_MESSAGING_TARGET_REF,
    LOCAL_OUTBOX_OPERATIONS,
    OUTBOX_SCOPED_OPERATIONS,
    TRANSACTION_SCOPED_OPERATIONS,
    MatrixMessagingOperation,
    matrix_messaging_lane,
    matrix_messaging_rollback_ref,
)


def stable_matrix_messaging_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class _MessagingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixOutboxState(str, Enum):
    draft = "draft"
    queued = "queued"
    sending = "sending"
    server_acknowledged = "server_acknowledged"
    remote_echo = "remote_echo"
    failed = "failed"
    outcome_uncertain = "outcome_uncertain"
    discarded = "discarded"


class MatrixMessagingCommand(_MessagingModel):
    schema_version: Literal["uaa-matrix-messaging.v1"] = (
        MATRIX_MESSAGING_SCHEMA_VERSION
    )
    operation: MatrixMessagingOperation
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
    event_ref: str | None = Field(default=None, max_length=240)
    transaction_ref: str | None = Field(default=None, max_length=240)
    content_fingerprint_ref: str | None = Field(default=None, max_length=240)
    outbox_ref: str | None = Field(default=None, max_length=240)
    outbox_generation_ref: str | None = Field(default=None, max_length=240)
    next_outbox_generation_ref: str | None = Field(default=None, max_length=240)
    outbox_message_operation: MatrixMessagingOperation | None = None
    expected_outbox_state: MatrixOutboxState | None = None
    next_outbox_state: MatrixOutboxState | None = None
    notification_target_ref: str | None = Field(default=None, max_length=240)
    notification_policy_ref: str | None = Field(default=None, max_length=240)
    notification_disclosure_ref: str | None = Field(default=None, max_length=240)
    notification_generation_ref: str | None = Field(default=None, max_length=240)
    target_ref: Literal["target-ref:communications:matrix-exact-message"] = (
        MATRIX_MESSAGING_TARGET_REF
    )
    provider_ref: Literal["provider-ref:communications:matrix"] = (
        MATRIX_MESSAGING_PROVIDER_REF
    )
    runtime_ref: Literal["runtime-ref:matrix-rust-sdk:0.18.0"] = (
        MATRIX_MESSAGING_RUNTIME_REF
    )
    outbox_schema_ref: Literal["outbox-schema-ref:matrix:encrypted-v1"] = (
        MATRIX_MESSAGING_OUTBOX_SCHEMA_REF
    )
    outbox_key_item_ref: Literal["key-item-ref:matrix-outbox:dedicated-v1"] = (
        MATRIX_MESSAGING_OUTBOX_KEY_ITEM_REF
    )
    outbox_key_version_ref: Literal["key-version-ref:matrix-outbox:v1"] = (
        MATRIX_MESSAGING_OUTBOX_KEY_VERSION_REF
    )
    budget_ref: Literal["budget-ref:matrix-messaging:zero-cost-v1"] = (
        MATRIX_MESSAGING_BUDGET_REF
    )
    readiness_ref: str = Field(max_length=240)
    safe_disable_ref: Literal["safe-disable-ref:matrix-messenger:enabled"] = (
        MATRIX_MESSAGING_SAFE_DISABLE_REF
    )
    kill_switch_ref: Literal["kill-switch-ref:matrix-messenger:clear"] = (
        MATRIX_MESSAGING_KILL_SWITCH_REF
    )
    rollback_ref: str = Field(max_length=240)
    request_created_at: datetime
    start_deadline: datetime
    max_duration_ms: int = Field(default=30_000, ge=100, le=300_000)
    max_cost_microusd: Literal[0] = 0
    request_fingerprint_ref: str = Field(max_length=240)
    human_commanded: Literal[True] = True
    autonomous_send: Literal[False] = False

    @model_validator(mode="after")
    def validate_command(self) -> MatrixMessagingCommand:
        for name, value in self.model_dump(mode="python").items():
            if name in {
                "schema_version",
                "operation",
                "expected_outbox_state",
                "next_outbox_state",
                "outbox_message_operation",
            }:
                continue
            if isinstance(value, str):
                validate_execution_ref(value, f"matrix_messaging_{name}")
        if self.request_created_at.tzinfo is None or self.start_deadline.tzinfo is None:
            raise ValueError("MATRIX_MESSAGING_TIMEZONE_REQUIRED")
        if not self.request_created_at < self.start_deadline:
            raise ValueError("MATRIX_MESSAGING_DEADLINE_ORDER_INVALID")
        if self.start_deadline - self.request_created_at > timedelta(minutes=5):
            raise ValueError("MATRIX_MESSAGING_DEADLINE_WINDOW_EXCEEDED")
        if self.operation == MatrixMessagingOperation.desktop_notify:
            if (
                self.notification_target_ref
                != MATRIX_MESSAGING_NOTIFICATION_TARGET_REF
                or self.notification_policy_ref
                != MATRIX_MESSAGING_NOTIFICATION_POLICY_REF
                or self.notification_disclosure_ref
                != MATRIX_MESSAGING_NOTIFICATION_DISCLOSURE_REF
                or self.notification_generation_ref is None
                or self.room_ref is None
            ):
                raise ValueError("MATRIX_MESSAGING_NOTIFICATION_SCOPE_INVALID")
        elif any(
            value is not None
            for value in (
                self.notification_target_ref,
                self.notification_policy_ref,
                self.notification_disclosure_ref,
                self.notification_generation_ref,
            )
        ):
            raise ValueError("MATRIX_MESSAGING_NOTIFICATION_TARGET_FORBIDDEN")
        elif self.room_ref is None:
            raise ValueError("MATRIX_MESSAGING_ROOM_SCOPE_REQUIRED")
        outbox_scoped = self.operation in OUTBOX_SCOPED_OPERATIONS
        local_outbox_operation = self.operation in LOCAL_OUTBOX_OPERATIONS
        if local_outbox_operation:
            if self.outbox_message_operation not in TRANSACTION_SCOPED_OPERATIONS:
                raise ValueError("MATRIX_MESSAGING_OUTBOX_MESSAGE_OPERATION_REQUIRED")
            effective_operation = self.outbox_message_operation
        else:
            if self.outbox_message_operation is not None:
                raise ValueError("MATRIX_MESSAGING_OUTBOX_MESSAGE_OPERATION_FORBIDDEN")
            effective_operation = self.operation
        assert effective_operation is not None
        if (effective_operation in EVENT_SCOPED_OPERATIONS) != (
            self.event_ref is not None
        ):
            raise ValueError("MATRIX_MESSAGING_EVENT_SCOPE_INVALID")
        if (effective_operation in TRANSACTION_SCOPED_OPERATIONS) != (
            self.transaction_ref is not None
        ):
            raise ValueError("MATRIX_MESSAGING_TRANSACTION_SCOPE_INVALID")
        if (effective_operation in CONTENT_FINGERPRINT_OPERATIONS) != (
            self.content_fingerprint_ref is not None
        ):
            raise ValueError("MATRIX_MESSAGING_CONTENT_SCOPE_INVALID")
        outbox_values = (
            self.outbox_ref,
            self.outbox_generation_ref,
            self.expected_outbox_state,
        )
        if outbox_scoped:
            if any(value is None for value in outbox_values):
                raise ValueError("MATRIX_MESSAGING_OUTBOX_SCOPE_REQUIRED")
        elif any(value is not None for value in outbox_values):
            raise ValueError("MATRIX_MESSAGING_OUTBOX_SCOPE_FORBIDDEN")
        transition = self.operation == MatrixMessagingOperation.outbox_transition
        if transition != (
            self.next_outbox_state is not None
            and self.next_outbox_generation_ref is not None
        ):
            raise ValueError("MATRIX_MESSAGING_OUTBOX_TRANSITION_SCOPE_INVALID")
        if not transition and self.next_outbox_generation_ref is not None:
            raise ValueError("MATRIX_MESSAGING_NEXT_OUTBOX_GENERATION_FORBIDDEN")
        if self.rollback_ref != matrix_messaging_rollback_ref(self.operation):
            raise ValueError("MATRIX_MESSAGING_ROLLBACK_POSTURE_MISMATCH")
        expected = matrix_messaging_request_fingerprint_ref(
            **self.model_dump(mode="python", exclude={"request_fingerprint_ref"})
        )
        if self.request_fingerprint_ref != expected:
            raise ValueError("MATRIX_MESSAGING_REQUEST_FINGERPRINT_MISMATCH")
        return self


class MatrixMessagingReadiness(_MessagingModel):
    readiness_ref: str
    request_fingerprint_ref: str
    adapter_ref: str
    status: Literal["ready", "blocked", "unknown"]
    observed_at: datetime
    expires_at: datetime
    kill_switch_engaged: StrictBool
    safe_disable_active: StrictBool
    broker_integrity_verified: StrictBool
    keychain_available: StrictBool
    crypto_store_available: StrictBool
    reason_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)

    @model_validator(mode="after")
    def validate_readiness(self) -> MatrixMessagingReadiness:
        for value in (
            self.readiness_ref,
            self.request_fingerprint_ref,
            self.adapter_ref,
            *self.reason_refs,
        ):
            validate_execution_ref(value, "matrix_messaging_readiness_ref")
        if self.observed_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("MATRIX_MESSAGING_READINESS_TIMEZONE_REQUIRED")
        if not self.observed_at < self.expires_at:
            raise ValueError("MATRIX_MESSAGING_READINESS_WINDOW_INVALID")
        if self.expires_at - self.observed_at > timedelta(seconds=60):
            raise ValueError("MATRIX_MESSAGING_READINESS_WINDOW_EXCEEDED")
        ready = (
            not self.kill_switch_engaged
            and not self.safe_disable_active
            and self.broker_integrity_verified
            and self.keychain_available
            and self.crypto_store_available
        )
        if (self.status == "ready") != ready:
            raise ValueError("MATRIX_MESSAGING_READINESS_STATUS_INVALID")
        if self.status != "ready" and not self.reason_refs:
            raise ValueError("MATRIX_MESSAGING_READINESS_REASON_REQUIRED")
        return self


class MatrixMessagingDispatchMetadata(_MessagingModel):
    command: MatrixMessagingCommand
    start_deadline_ref: str

    @model_validator(mode="after")
    def validate_metadata(self) -> MatrixMessagingDispatchMetadata:
        if self.start_deadline_ref != matrix_messaging_start_deadline_ref(
            self.command.start_deadline
        ):
            raise ValueError("MATRIX_MESSAGING_START_DEADLINE_BINDING_INVALID")
        return self


class MatrixMessagingPosture(_MessagingModel):
    schema_version: Literal["uaa-matrix-messaging-posture.v1"] = (
        "uaa-matrix-messaging-posture.v1"
    )
    posture_ref: str
    runtime_status: Literal[
        "ready", "configuration_required", "blocked", "external_facility_required"
    ]
    authority_lane_refs: tuple[str, ...]
    live_executor_operation_refs: tuple[str, ...]
    blocked_operation_refs: tuple[str, ...]
    broker_ref: str
    provider_ref: Literal["provider-ref:communications:matrix"] = (
        MATRIX_MESSAGING_PROVIDER_REF
    )
    sdk_ref: Literal["sdk-ref:matrix-rust-sdk:0.18.0"] = (
        "sdk-ref:matrix-rust-sdk:0.18.0"
    )
    crypto_store_ref: str
    outbox_store_ref: str
    reason_refs: tuple[str, ...]
    element_interoperability_status: Literal[
        "passed", "failed", "external_facility_required"
    ]
    request_scoped_evaluation_required: Literal[True] = True
    approval_ref_is_authority: Literal[False] = False
    autonomous_send_enabled: Literal[False] = False
    remote_homeservers_enabled: Literal[False] = False
    desktop_only: Literal[True] = True
    raw_content_included: Literal[False] = False
    safe_summary: str = Field(min_length=1, max_length=240)


class MatrixMessagingProposal(_MessagingModel):
    schema_version: Literal["uaa-matrix-messaging-proposal.v1"] = (
        "uaa-matrix-messaging-proposal.v1"
    )
    proposal_ref: str
    operation: MatrixMessagingOperation
    request_fingerprint_ref: str
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    target_ref: str
    lease_ref: str
    idempotency_ref: str
    readiness_ref: str
    required_mode: str
    side_effect_class: str
    approval_required: Literal[True] = True
    request_scoped_evaluation_required: Literal[True] = True
    approval_ref_authorizes_execution: Literal[False] = False
    execution_permitted: Literal[False] = False
    mutation_performed: Literal[False] = False
    autonomous_send_enabled: Literal[False] = False
    raw_content_included: Literal[False] = False
    safe_summary: str = Field(min_length=1, max_length=240)


def matrix_messaging_request_fingerprint_ref(**payload: object) -> str:
    return stable_matrix_messaging_ref(
        "request-fingerprint-ref:matrix-messaging", payload
    )


def build_matrix_messaging_proposal(
    command: MatrixMessagingCommand,
) -> MatrixMessagingProposal:
    lane = matrix_messaging_lane(command.operation)
    values: dict[str, object] = {
        "operation": command.operation,
        "request_fingerprint_ref": command.request_fingerprint_ref,
        "lane_ref": lane.lane_ref,
        "capability_ref": lane.capability_ref,
        "adapter_ref": lane.adapter_ref,
        "target_ref": command.target_ref,
        "lease_ref": command.lease_ref,
        "idempotency_ref": command.idempotency_ref,
        "readiness_ref": command.readiness_ref,
        "required_mode": lane.required_mode.value,
        "side_effect_class": lane.side_effect_class,
        "safe_summary": (
            "Review one exact human-commanded Matrix operation; this proposal grants no authority and performs no mutation."
        ),
    }
    values["proposal_ref"] = stable_matrix_messaging_ref(
        "proposal-ref:matrix-messaging", values
    )
    return MatrixMessagingProposal.model_validate(values)


def build_matrix_messaging_command(**payload: object) -> MatrixMessagingCommand:
    """Normalize defaults, bind the exact fingerprint, then validate the command."""

    candidate = MatrixMessagingCommand.model_construct(
        **payload,
        request_fingerprint_ref="request-fingerprint-ref:matrix-messaging:pending",
    )
    normalized = candidate.model_dump(
        mode="python", exclude={"request_fingerprint_ref"}
    )
    normalized["request_fingerprint_ref"] = matrix_messaging_request_fingerprint_ref(
        **normalized
    )
    return MatrixMessagingCommand.model_validate(normalized)


def matrix_messaging_exact_resource_refs(
    command: MatrixMessagingCommand,
) -> tuple[str, ...]:
    lane = matrix_messaging_lane(command.operation)
    refs = [
        command.request_ref,
        command.task_ref,
        command.mission_ref,
        command.run_ref,
        command.dispatch_ref,
        command.lease_ref,
        command.account_ref,
        command.homeserver_ref,
        command.device_ref,
        command.target_ref,
        command.provider_ref,
        command.runtime_ref,
        command.outbox_schema_ref,
        command.outbox_key_item_ref,
        command.outbox_key_version_ref,
        command.request_fingerprint_ref,
        command.idempotency_ref,
        command.readiness_ref,
        command.budget_ref,
        command.safe_disable_ref,
        command.kill_switch_ref,
        command.rollback_ref,
        matrix_messaging_start_deadline_ref(command.start_deadline),
        lane.lane_ref,
        lane.capability_ref,
        lane.adapter_ref,
        lane.tool_ref,
    ]
    refs.extend(
        value
        for value in (
            command.room_ref,
            command.event_ref,
            command.transaction_ref,
            command.content_fingerprint_ref,
            command.outbox_ref,
            command.outbox_generation_ref,
            command.next_outbox_generation_ref,
            command.notification_target_ref,
            command.notification_policy_ref,
            command.notification_disclosure_ref,
            command.notification_generation_ref,
        )
        if value is not None
    )
    return tuple(dict.fromkeys(refs))


def matrix_messaging_start_deadline_ref(value: datetime) -> str:
    return stable_matrix_messaging_ref(
        "start-deadline-ref:matrix-messaging", {"value": value.isoformat()}
    )


__all__ = [
    "MatrixMessagingCommand",
    "MatrixMessagingDispatchMetadata",
    "MatrixMessagingPosture",
    "MatrixMessagingProposal",
    "MatrixMessagingReadiness",
    "MatrixOutboxState",
    "build_matrix_messaging_command",
    "build_matrix_messaging_proposal",
    "matrix_messaging_exact_resource_refs",
    "matrix_messaging_request_fingerprint_ref",
    "matrix_messaging_start_deadline_ref",
    "stable_matrix_messaging_ref",
]
