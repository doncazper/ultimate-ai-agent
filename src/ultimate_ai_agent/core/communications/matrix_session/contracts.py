from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
)

from .constants import (
    MATRIX_DISCOVERY_PENDING_FRESHNESS_REF,
    MATRIX_DISCOVERY_PENDING_OBSERVATION_REF,
    MATRIX_SESSION_BUDGET_REF,
    MATRIX_SESSION_CREDENTIAL_BACKEND_REF,
    MATRIX_SESSION_KILL_SWITCH_REF,
    MATRIX_SESSION_PROVIDER_REF,
    MATRIX_SESSION_SAFE_DISABLE_REF,
    MATRIX_SESSION_SCHEMA_VERSION,
    MATRIX_SESSION_TARGET_REF,
    MatrixSessionOperation,
    matrix_session_lane,
)


def stable_matrix_session_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class _MatrixSessionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixSessionCommand(_MatrixSessionModel):
    schema_version: Literal["uaa-matrix-session.v1"] = MATRIX_SESSION_SCHEMA_VERSION
    operation: MatrixSessionOperation
    request_ref: str = Field(..., max_length=240)
    task_ref: str = Field(..., max_length=240)
    mission_ref: str = Field(..., max_length=240)
    run_ref: str = Field(..., max_length=240)
    dispatch_ref: str = Field(..., max_length=240)
    idempotency_ref: str = Field(..., max_length=240)
    lease_ref: str = Field(..., max_length=240)
    homeserver_ref: str = Field(..., max_length=240)
    endpoint_class_ref: str = Field(..., max_length=240)
    discovery_observation_ref: str = Field(..., max_length=240)
    discovery_freshness_ref: str = Field(..., max_length=240)
    target_ref: str = MATRIX_SESSION_TARGET_REF
    account_ref: str | None = Field(default=None, max_length=240)
    device_ref: str | None = Field(default=None, max_length=240)
    session_ref: str | None = Field(default=None, max_length=240)
    session_generation_ref: str | None = Field(default=None, max_length=240)
    redirect_target_ref: str | None = Field(default=None, max_length=240)
    credential_backend_ref: str = MATRIX_SESSION_CREDENTIAL_BACKEND_REF
    credential_item_ref: str | None = Field(default=None, max_length=240)
    credential_version_ref: str | None = Field(default=None, max_length=240)
    next_credential_version_ref: str | None = Field(default=None, max_length=240)
    crypto_store_ref: str | None = Field(default=None, max_length=240)
    callback_attempt_ref: str | None = Field(default=None, max_length=240)
    budget_ref: str = MATRIX_SESSION_BUDGET_REF
    kill_switch_ref: str = MATRIX_SESSION_KILL_SWITCH_REF
    safe_disable_ref: str = MATRIX_SESSION_SAFE_DISABLE_REF
    readiness_ref: str = Field(..., max_length=240)
    target_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=16)
    request_created_at: datetime
    start_deadline: datetime
    request_fingerprint_ref: str = Field(..., max_length=240)

    @model_validator(mode="after")
    def validate_command(self) -> "MatrixSessionCommand":
        values = (
            self.request_ref,
            self.task_ref,
            self.mission_ref,
            self.run_ref,
            self.dispatch_ref,
            self.idempotency_ref,
            self.lease_ref,
            self.homeserver_ref,
            self.endpoint_class_ref,
            self.discovery_observation_ref,
            self.discovery_freshness_ref,
            self.target_ref,
            self.account_ref,
            self.device_ref,
            self.session_ref,
            self.session_generation_ref,
            self.redirect_target_ref,
            self.credential_backend_ref,
            self.credential_item_ref,
            self.credential_version_ref,
            self.next_credential_version_ref,
            self.crypto_store_ref,
            self.callback_attempt_ref,
            self.budget_ref,
            self.kill_switch_ref,
            self.safe_disable_ref,
            self.readiness_ref,
            *self.target_refs,
            self.request_fingerprint_ref,
        )
        for value in values:
            if value is not None:
                validate_execution_ref(value, "matrix_session_command_ref")
        if len(self.target_refs) != len(set(self.target_refs)):
            raise ValueError("MATRIX_SESSION_DUPLICATE_TARGET_REF")
        required_governance_refs = {
            "target_ref": MATRIX_SESSION_TARGET_REF,
            "credential_backend_ref": MATRIX_SESSION_CREDENTIAL_BACKEND_REF,
            "budget_ref": MATRIX_SESSION_BUDGET_REF,
            "kill_switch_ref": MATRIX_SESSION_KILL_SWITCH_REF,
            "safe_disable_ref": MATRIX_SESSION_SAFE_DISABLE_REF,
        }
        for name, expected_ref in required_governance_refs.items():
            if getattr(self, name) != expected_ref:
                raise ValueError(f"MATRIX_SESSION_{name.upper()}_SUBSTITUTION_DENIED")
        if (
            self.request_created_at.tzinfo is None
            or self.request_created_at.utcoffset() is None
        ):
            raise ValueError("MATRIX_SESSION_REQUEST_CREATED_AT_TIMEZONE_REQUIRED")
        if (
            self.start_deadline.tzinfo is None
            or self.start_deadline.utcoffset() is None
        ):
            raise ValueError("MATRIX_SESSION_START_DEADLINE_TIMEZONE_REQUIRED")
        if self.request_created_at >= self.start_deadline:
            raise ValueError("MATRIX_SESSION_REQUEST_DEADLINE_ORDER_INVALID")
        self._validate_operation_scope()
        expected = matrix_session_request_fingerprint_ref(
            operation=self.operation,
            request_ref=self.request_ref,
            task_ref=self.task_ref,
            mission_ref=self.mission_ref,
            run_ref=self.run_ref,
            dispatch_ref=self.dispatch_ref,
            idempotency_ref=self.idempotency_ref,
            lease_ref=self.lease_ref,
            homeserver_ref=self.homeserver_ref,
            endpoint_class_ref=self.endpoint_class_ref,
            discovery_observation_ref=self.discovery_observation_ref,
            discovery_freshness_ref=self.discovery_freshness_ref,
            target_ref=self.target_ref,
            account_ref=self.account_ref,
            device_ref=self.device_ref,
            session_ref=self.session_ref,
            session_generation_ref=self.session_generation_ref,
            redirect_target_ref=self.redirect_target_ref,
            credential_backend_ref=self.credential_backend_ref,
            credential_item_ref=self.credential_item_ref,
            credential_version_ref=self.credential_version_ref,
            next_credential_version_ref=self.next_credential_version_ref,
            crypto_store_ref=self.crypto_store_ref,
            callback_attempt_ref=self.callback_attempt_ref,
            budget_ref=self.budget_ref,
            kill_switch_ref=self.kill_switch_ref,
            safe_disable_ref=self.safe_disable_ref,
            readiness_ref=self.readiness_ref,
            target_refs=self.target_refs,
            request_created_at=self.request_created_at,
            start_deadline=self.start_deadline,
        )
        if self.request_fingerprint_ref != expected:
            raise ValueError("MATRIX_SESSION_REQUEST_FINGERPRINT_MISMATCH")
        return self

    def _validate_operation_scope(self) -> None:
        if self.operation == MatrixSessionOperation.discovery_read and (
            self.discovery_observation_ref != MATRIX_DISCOVERY_PENDING_OBSERVATION_REF
            or self.discovery_freshness_ref != MATRIX_DISCOVERY_PENDING_FRESHNESS_REF
        ):
            raise ValueError("MATRIX_DISCOVERY_PENDING_BINDING_REQUIRED")
        session_operations = {
            MatrixSessionOperation.credential_auth_create,
            MatrixSessionOperation.sso_callback_consume,
            MatrixSessionOperation.refresh,
            MatrixSessionOperation.logout,
            MatrixSessionOperation.revoke_all,
            MatrixSessionOperation.credential_store_rotate,
            MatrixSessionOperation.credential_delete,
        }
        credential_operations = {
            MatrixSessionOperation.credential_auth_create,
            MatrixSessionOperation.sso_callback_consume,
            MatrixSessionOperation.refresh,
            MatrixSessionOperation.logout,
            MatrixSessionOperation.revoke_all,
            MatrixSessionOperation.credential_store_rotate,
            MatrixSessionOperation.credential_delete,
        }
        if self.operation in session_operations and not all(
            (
                self.account_ref,
                self.device_ref,
                self.session_ref,
                self.session_generation_ref,
            )
        ):
            raise ValueError("MATRIX_SESSION_EXACT_SESSION_SCOPE_REQUIRED")
        if self.operation in credential_operations and not all(
            (self.credential_item_ref, self.credential_version_ref)
        ):
            raise ValueError("MATRIX_SESSION_EXACT_CREDENTIAL_SCOPE_REQUIRED")
        if (
            self.operation == MatrixSessionOperation.credential_auth_create
            and not self.crypto_store_ref
        ):
            raise ValueError("MATRIX_SESSION_EXACT_CRYPTO_STORE_SCOPE_REQUIRED")
        if (
            self.operation
            in {
                MatrixSessionOperation.refresh,
                MatrixSessionOperation.credential_store_rotate,
            }
            and not self.next_credential_version_ref
        ):
            raise ValueError("MATRIX_SESSION_NEXT_CREDENTIAL_SCOPE_REQUIRED")
        if (
            self.next_credential_version_ref is not None
            and self.next_credential_version_ref == self.credential_version_ref
        ):
            raise ValueError("MATRIX_SESSION_CREDENTIAL_VERSION_REUSE_DENIED")
        if (
            self.operation
            in {
                MatrixSessionOperation.sso_launch,
                MatrixSessionOperation.sso_callback_consume,
            }
            and not self.redirect_target_ref
        ):
            raise ValueError("MATRIX_SESSION_EXACT_REDIRECT_SCOPE_REQUIRED")
        if (
            self.operation
            in {
                MatrixSessionOperation.sso_launch,
                MatrixSessionOperation.sso_callback_consume,
            }
            and not self.callback_attempt_ref
        ):
            raise ValueError("MATRIX_SESSION_CALLBACK_ATTEMPT_SCOPE_REQUIRED")
        if self.operation == MatrixSessionOperation.revoke_all and not self.target_refs:
            raise ValueError("MATRIX_SESSION_DEVICE_SET_SCOPE_REQUIRED")


class MatrixSessionDispatchMetadata(_MatrixSessionModel):
    command: MatrixSessionCommand
    start_deadline_ref: str
    target_ref: str = MATRIX_SESSION_TARGET_REF
    provider_ref: str = MATRIX_SESSION_PROVIDER_REF

    @model_validator(mode="after")
    def validate_metadata(self) -> "MatrixSessionDispatchMetadata":
        for value in (
            self.start_deadline_ref,
            self.target_ref,
            self.provider_ref,
        ):
            validate_execution_ref(value, "matrix_session_dispatch_metadata_ref")
        if self.start_deadline_ref != matrix_session_start_deadline_ref(
            self.command.start_deadline
        ):
            raise ValueError("MATRIX_SESSION_DISPATCH_DEADLINE_BINDING_MISMATCH")
        return self


def matrix_session_request_fingerprint_ref(**values: object) -> str:
    operation = MatrixSessionOperation(values["operation"])
    payload = {
        "request_ref": values.get("request_ref"),
        "task_ref": values.get("task_ref"),
        "mission_ref": values.get("mission_ref"),
        "run_ref": values.get("run_ref"),
        "dispatch_ref": values.get("dispatch_ref"),
        "idempotency_ref": values.get("idempotency_ref"),
        "lease_ref": values.get("lease_ref"),
        "homeserver_ref": values.get("homeserver_ref"),
        "endpoint_class_ref": values.get("endpoint_class_ref"),
        "discovery_observation_ref": values.get("discovery_observation_ref"),
        "discovery_freshness_ref": values.get("discovery_freshness_ref"),
        "target_ref": values.get("target_ref", MATRIX_SESSION_TARGET_REF),
        "account_ref": values.get("account_ref"),
        "device_ref": values.get("device_ref"),
        "session_ref": values.get("session_ref"),
        "session_generation_ref": values.get("session_generation_ref"),
        "redirect_target_ref": values.get("redirect_target_ref"),
        "credential_backend_ref": values.get(
            "credential_backend_ref", MATRIX_SESSION_CREDENTIAL_BACKEND_REF
        ),
        "credential_item_ref": values.get("credential_item_ref"),
        "credential_version_ref": values.get("credential_version_ref"),
        "next_credential_version_ref": values.get("next_credential_version_ref"),
        "crypto_store_ref": values.get("crypto_store_ref"),
        "callback_attempt_ref": values.get("callback_attempt_ref"),
        "budget_ref": values.get("budget_ref", MATRIX_SESSION_BUDGET_REF),
        "kill_switch_ref": values.get(
            "kill_switch_ref", MATRIX_SESSION_KILL_SWITCH_REF
        ),
        "safe_disable_ref": values.get(
            "safe_disable_ref", MATRIX_SESSION_SAFE_DISABLE_REF
        ),
        "readiness_ref": values.get("readiness_ref"),
        "target_refs": tuple(values.get("target_refs") or ()),
        "request_created_at": values.get("request_created_at"),
        "start_deadline": values.get("start_deadline"),
    }
    for name in ("request_created_at", "start_deadline"):
        timestamp = payload.get(name)
        if isinstance(timestamp, datetime):
            payload[name] = timestamp.isoformat()
    payload["operation"] = operation.value
    return stable_matrix_session_ref(
        "request-fingerprint-ref:matrix-session",
        payload,
    )


def matrix_session_start_deadline_ref(start_deadline: datetime) -> str:
    return stable_matrix_session_ref(
        "start-deadline-ref:matrix-session",
        {"start_deadline": start_deadline.isoformat()},
    )


def matrix_session_rollback_ref(operation: MatrixSessionOperation) -> str:
    posture = (
        "not-applicable-read"
        if operation
        in {
            MatrixSessionOperation.discovery_read,
            MatrixSessionOperation.auth_methods_read,
        }
        else "blocked-unimplemented"
    )
    return f"rollback-readiness-ref:matrix-session:{operation.value}:{posture}"


def matrix_session_exact_resource_refs(
    command: MatrixSessionCommand,
) -> tuple[str, ...]:
    lane = matrix_session_lane(command.operation)
    values = (
        command.request_ref,
        command.task_ref,
        command.mission_ref,
        command.run_ref,
        command.dispatch_ref,
        command.idempotency_ref,
        command.lease_ref,
        command.request_fingerprint_ref,
        command.homeserver_ref,
        command.endpoint_class_ref,
        command.discovery_observation_ref,
        command.discovery_freshness_ref,
        command.target_ref,
        command.account_ref,
        command.device_ref,
        command.session_ref,
        command.session_generation_ref,
        command.redirect_target_ref,
        command.credential_backend_ref,
        command.credential_item_ref,
        command.credential_version_ref,
        command.next_credential_version_ref,
        command.crypto_store_ref,
        command.callback_attempt_ref,
        command.budget_ref,
        command.kill_switch_ref,
        command.safe_disable_ref,
        command.readiness_ref,
        *command.target_refs,
        matrix_session_start_deadline_ref(command.start_deadline),
        matrix_session_rollback_ref(command.operation),
        lane.lane_ref,
        lane.capability_ref,
        lane.adapter_ref,
        lane.tool_ref,
        MATRIX_SESSION_PROVIDER_REF,
    )
    return tuple(dict.fromkeys(value for value in values if value is not None))
