from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)

from .constants import (
    MATRIX_HARNESS_CONFIG_REF,
    MATRIX_HARNESS_FIXTURE_PLAN_REF,
    MATRIX_HARNESS_IMAGE_REF,
    MATRIX_HARNESS_LIMITS_REF,
    MATRIX_HARNESS_PORT_REF,
    MATRIX_HARNESS_PROJECT_REF,
    MATRIX_HARNESS_PROVIDER_REF,
    MATRIX_HARNESS_SCHEMA_VERSION,
    MATRIX_HARNESS_STATE_SCOPE_REF,
    MATRIX_HARNESS_TARGET_REF,
    MatrixHarnessOperation,
    matrix_harness_lane,
)


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def stable_matrix_harness_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class MatrixHarnessRuntimeStatus(str, Enum):
    unavailable = "unavailable"
    stopped = "stopped"
    starting = "starting"
    running = "running"
    healthy = "healthy"
    degraded = "degraded"
    expired = "expired"
    cleanup_required = "cleanup_required"
    recovery_required = "recovery_required"
    unknown = "unknown"


class MatrixHarnessOperationOutcome(str, Enum):
    succeeded = "succeeded"
    blocked = "blocked"
    failed = "failed"
    recovery_required = "recovery_required"


def matrix_harness_generation_ref(generation: int) -> str:
    if generation < 0:
        raise ValueError("MATRIX_HARNESS_GENERATION_INVALID")
    return stable_matrix_harness_ref(
        "generation-ref:matrix-harness",
        {"generation": generation},
    )


def matrix_harness_state_ref(
    status: MatrixHarnessRuntimeStatus,
    generation: int,
) -> str:
    return stable_matrix_harness_ref(
        "state-ref:matrix-harness",
        {"generation": generation, "status": status.value},
    )


class _MatrixHarnessModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixHarnessCommand(_MatrixHarnessModel):
    schema_version: Literal["uaa-matrix-harness.v1"] = MATRIX_HARNESS_SCHEMA_VERSION
    operation: MatrixHarnessOperation
    request_ref: str = Field(..., max_length=240)
    task_ref: str = Field(..., max_length=240)
    mission_ref: str = Field(..., max_length=240)
    run_ref: str = Field(..., max_length=240)
    dispatch_ref: str = Field(..., max_length=240)
    idempotency_ref: str = Field(..., max_length=240)
    lease_ref: str = Field(..., max_length=240)
    lifecycle_generation_ref: str = Field(..., max_length=240)
    expected_state_ref: str = Field(..., max_length=240)
    start_deadline: datetime
    request_fingerprint_ref: str = Field(..., max_length=240)

    @model_validator(mode="after")
    def validate_command(self) -> "MatrixHarnessCommand":
        for value in (
            self.request_ref,
            self.task_ref,
            self.mission_ref,
            self.run_ref,
            self.dispatch_ref,
            self.idempotency_ref,
            self.lease_ref,
            self.lifecycle_generation_ref,
            self.expected_state_ref,
            self.request_fingerprint_ref,
        ):
            validate_execution_ref(value, "matrix_harness_command_ref")
        if self.start_deadline.tzinfo is None:
            raise ValueError("MATRIX_HARNESS_START_DEADLINE_TIMEZONE_REQUIRED")
        expected = matrix_harness_request_fingerprint_ref(
            operation=self.operation,
            request_ref=self.request_ref,
            task_ref=self.task_ref,
            mission_ref=self.mission_ref,
            run_ref=self.run_ref,
            dispatch_ref=self.dispatch_ref,
            idempotency_ref=self.idempotency_ref,
            lease_ref=self.lease_ref,
            lifecycle_generation_ref=self.lifecycle_generation_ref,
            expected_state_ref=self.expected_state_ref,
            start_deadline=self.start_deadline,
        )
        if self.request_fingerprint_ref != expected:
            raise ValueError("MATRIX_HARNESS_REQUEST_FINGERPRINT_MISMATCH")
        return self


class MatrixHarnessDispatchMetadata(_MatrixHarnessModel):
    operation: MatrixHarnessOperation
    provider_ref: Literal["provider-ref:communications:matrix-local-synapse"] = (
        MATRIX_HARNESS_PROVIDER_REF
    )
    target_ref: Literal["target-ref:communications:matrix-harness-loopback"] = (
        MATRIX_HARNESS_TARGET_REF
    )
    project_ref: Literal["project-ref:communications:matrix-harness-v1"] = (
        MATRIX_HARNESS_PROJECT_REF
    )
    port_ref: Literal["port-ref:communications:matrix-harness-18008"] = (
        MATRIX_HARNESS_PORT_REF
    )
    image_ref: Literal[
        "matrixdotorg/synapse@sha256:d2215c4a0e0bbd304489af228345b31d6857c1a228175471358d3fda187c0d91"
    ] = MATRIX_HARNESS_IMAGE_REF
    config_ref: Literal[
        "config-ref:communications:matrix-harness-loopback-sqlite-no-federation-v1"
    ] = MATRIX_HARNESS_CONFIG_REF
    limits_ref: Literal[
        "limits-ref:communications:matrix-harness-30m-1cpu-1g-128pids"
    ] = MATRIX_HARNESS_LIMITS_REF
    request_ref: str = Field(..., max_length=240)
    task_ref: str = Field(..., max_length=240)
    mission_ref: str = Field(..., max_length=240)
    run_ref: str = Field(..., max_length=240)
    request_fingerprint_ref: str = Field(..., max_length=240)
    lifecycle_generation_ref: str = Field(..., max_length=240)
    expected_state_ref: str = Field(..., max_length=240)
    start_deadline_ref: str = Field(..., max_length=240)
    fixture_plan_ref: str | None = Field(default=None, max_length=240)
    state_scope_ref: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def validate_metadata(self) -> "MatrixHarnessDispatchMetadata":
        lane = matrix_harness_lane(self.operation)
        for value in (
            self.request_ref,
            self.task_ref,
            self.mission_ref,
            self.run_ref,
            self.request_fingerprint_ref,
            self.lifecycle_generation_ref,
            self.expected_state_ref,
            self.start_deadline_ref,
            self.provider_ref,
            self.target_ref,
            self.project_ref,
            self.port_ref,
            self.config_ref,
            self.limits_ref,
            lane.lane_ref,
            lane.capability_ref,
            lane.adapter_ref,
            lane.tool_ref,
        ):
            validate_execution_ref(value, "matrix_harness_dispatch_ref")
        if self.operation == MatrixHarnessOperation.fixture_seed:
            if self.fixture_plan_ref != MATRIX_HARNESS_FIXTURE_PLAN_REF:
                raise ValueError("MATRIX_HARNESS_FIXTURE_PLAN_BINDING_REQUIRED")
        elif self.fixture_plan_ref is not None:
            raise ValueError("MATRIX_HARNESS_FIXTURE_PLAN_FORBIDDEN")
        if self.operation == MatrixHarnessOperation.reset:
            if self.state_scope_ref != MATRIX_HARNESS_STATE_SCOPE_REF:
                raise ValueError("MATRIX_HARNESS_STATE_SCOPE_BINDING_REQUIRED")
        elif self.state_scope_ref is not None:
            raise ValueError("MATRIX_HARNESS_STATE_SCOPE_FORBIDDEN")
        return self


class MatrixHarnessBackendResult(_MatrixHarnessModel):
    execution_ref: str
    operation: MatrixHarnessOperation
    outcome: MatrixHarnessOperationOutcome
    runtime_status: MatrixHarnessRuntimeStatus
    reason_codes: list[str] = Field(default_factory=list, max_length=24)
    warning_reason_refs: list[str] = Field(default_factory=list, max_length=24)
    evidence_refs: list[str] = Field(..., min_length=1, max_length=24)
    lifecycle_generation_ref: str | None = Field(default=None, max_length=240)
    lifecycle_state_ref: str | None = Field(default=None, max_length=240)
    container_count: int = Field(default=0, ge=0, le=4)
    network_count: int = Field(default=0, ge=0, le=4)
    volume_count: int = Field(default=0, ge=0, le=4)
    fixture_account_count: int = Field(default=0, ge=0, le=8)
    fixture_room_count: int = Field(default=0, ge=0, le=16)
    fixture_event_count: int = Field(default=0, ge=0, le=64)
    residual_resource_count: int = Field(default=0, ge=0, le=32)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    raw_output_persisted: Literal[False] = False
    raw_paths_persisted: Literal[False] = False
    credentials_persisted_in_receipt: Literal[False] = False
    fixture_content_persisted_in_receipt: Literal[False] = False
    encryption_fixture_posture: Literal["placeholder_only"] = "placeholder_only"

    @model_validator(mode="after")
    def validate_result(self) -> "MatrixHarnessBackendResult":
        validate_execution_ref(self.execution_ref, "matrix_harness_execution_ref")
        for ref in (
            *self.evidence_refs,
            *self.warning_reason_refs,
            self.lifecycle_generation_ref,
            self.lifecycle_state_ref,
        ):
            if ref is None:
                continue
            validate_execution_ref(ref, "matrix_harness_evidence_ref")
        for reason in self.reason_codes:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", reason):
                raise ValueError("MATRIX_HARNESS_REASON_CODE_INVALID")
        validate_safe_execution_text(self.safe_summary, "matrix_harness_safe_summary")
        if self.outcome == MatrixHarnessOperationOutcome.succeeded and self.reason_codes:
            raise ValueError("MATRIX_HARNESS_SUCCESS_REASON_CODES_FORBIDDEN")
        if self.outcome != MatrixHarnessOperationOutcome.succeeded and not self.reason_codes:
            raise ValueError("MATRIX_HARNESS_FAILURE_REASON_CODE_REQUIRED")
        return self


class MatrixHarnessLifecycleRecord(_MatrixHarnessModel):
    schema_version: Literal["uaa-matrix-harness.v1"] = MATRIX_HARNESS_SCHEMA_VERSION
    generation: int = Field(ge=0)
    generation_ref: str
    state: MatrixHarnessRuntimeStatus
    state_ref: str
    ownership_ref: str
    operation_ref: str | None = None
    updated_at: datetime

    @model_validator(mode="after")
    def validate_record(self) -> "MatrixHarnessLifecycleRecord":
        if self.generation_ref != matrix_harness_generation_ref(self.generation):
            raise ValueError("MATRIX_HARNESS_GENERATION_REF_MISMATCH")
        if self.state_ref != matrix_harness_state_ref(self.state, self.generation):
            raise ValueError("MATRIX_HARNESS_STATE_REF_MISMATCH")
        for ref in (
            self.generation_ref,
            self.state_ref,
            self.ownership_ref,
            self.operation_ref,
        ):
            if ref is not None:
                validate_execution_ref(ref, "matrix_harness_lifecycle_ref")
        if self.updated_at.tzinfo is None:
            raise ValueError("MATRIX_HARNESS_LIFECYCLE_TIMEZONE_REQUIRED")
        return self


class MatrixHarnessPosture(_MatrixHarnessModel):
    schema_version: Literal["uaa-matrix-harness.v1"] = MATRIX_HARNESS_SCHEMA_VERSION
    provider_ref: Literal["provider-ref:communications:matrix-local-synapse"] = (
        MATRIX_HARNESS_PROVIDER_REF
    )
    image_ref: str = MATRIX_HARNESS_IMAGE_REF
    target_ref: str = MATRIX_HARNESS_TARGET_REF
    runtime_status: MatrixHarnessRuntimeStatus
    lifecycle_generation_ref: str
    state_ref: str
    image_present: bool
    safe_disable_engaged: bool
    kill_switch_engaged: bool
    configuration_valid: bool
    authority_granted: Literal[False] = False
    globally_enabled: Literal[False] = False
    production_ready: Literal[False] = False
    reason_codes: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=240)

    @model_validator(mode="after")
    def validate_posture(self) -> "MatrixHarnessPosture":
        for ref in (
            self.provider_ref,
            self.target_ref,
            self.lifecycle_generation_ref,
            self.state_ref,
            *self.evidence_refs,
        ):
            validate_execution_ref(ref, "matrix_harness_posture_ref")
        if not _SHA256_RE.fullmatch(self.image_ref.rsplit("sha256:", 1)[-1]):
            raise ValueError("MATRIX_HARNESS_IMAGE_DIGEST_REQUIRED")
        validate_safe_execution_text(self.safe_summary, "matrix_harness_safe_summary")
        return self


def matrix_harness_request_fingerprint_ref(
    *,
    operation: MatrixHarnessOperation,
    request_ref: str,
    task_ref: str,
    mission_ref: str,
    run_ref: str,
    dispatch_ref: str,
    idempotency_ref: str,
    lease_ref: str,
    lifecycle_generation_ref: str,
    expected_state_ref: str,
    start_deadline: datetime,
) -> str:
    return stable_matrix_harness_ref(
        "request-fingerprint-ref:matrix-harness",
        {
            "operation": operation.value,
            "request_ref": request_ref,
            "task_ref": task_ref,
            "mission_ref": mission_ref,
            "run_ref": run_ref,
            "dispatch_ref": dispatch_ref,
            "idempotency_ref": idempotency_ref,
            "lease_ref": lease_ref,
            "lifecycle_generation_ref": lifecycle_generation_ref,
            "expected_state_ref": expected_state_ref,
            "start_deadline": start_deadline.isoformat(),
        },
    )


def matrix_harness_start_deadline_ref(start_deadline: datetime) -> str:
    return stable_matrix_harness_ref(
        "start-deadline-ref:matrix-harness",
        {"start_deadline": start_deadline.isoformat()},
    )


def matrix_harness_exact_resource_refs(
    command: MatrixHarnessCommand,
) -> tuple[str, ...]:
    lane = matrix_harness_lane(command.operation)
    refs = [
        command.request_ref,
        command.task_ref,
        command.mission_ref,
        command.run_ref,
        command.dispatch_ref,
        command.idempotency_ref,
        command.lease_ref,
        command.request_fingerprint_ref,
        command.lifecycle_generation_ref,
        command.expected_state_ref,
        matrix_harness_start_deadline_ref(command.start_deadline),
        lane.lane_ref,
        lane.capability_ref,
        lane.adapter_ref,
        lane.tool_ref,
        MATRIX_HARNESS_PROVIDER_REF,
        MATRIX_HARNESS_TARGET_REF,
        MATRIX_HARNESS_PROJECT_REF,
        MATRIX_HARNESS_PORT_REF,
        MATRIX_HARNESS_CONFIG_REF,
        MATRIX_HARNESS_LIMITS_REF,
        stable_matrix_harness_ref(
            "image-ref:matrix-harness", {"image": MATRIX_HARNESS_IMAGE_REF}
        ),
    ]
    if command.operation == MatrixHarnessOperation.fixture_seed:
        refs.append(MATRIX_HARNESS_FIXTURE_PLAN_REF)
    if command.operation == MatrixHarnessOperation.reset:
        refs.append(MATRIX_HARNESS_STATE_SCOPE_REF)
    return tuple(refs)
