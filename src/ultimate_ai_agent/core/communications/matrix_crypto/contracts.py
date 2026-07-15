from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .constants import (
    MATRIX_CRYPTO_BACKUP_BACKEND_REF,
    MATRIX_CRYPTO_BUDGET_REF,
    MATRIX_CRYPTO_KEY_BACKEND_REF,
    MATRIX_CRYPTO_KILL_SWITCH_REF,
    MATRIX_CRYPTO_LANES,
    MATRIX_CRYPTO_PROVIDER_REF,
    MATRIX_CRYPTO_RUNTIME_REF,
    MATRIX_CRYPTO_SAFE_DISABLE_REF,
    MATRIX_CRYPTO_SCHEMA_VERSION,
    MATRIX_CRYPTO_STORE_BACKEND_REF,
    MATRIX_CRYPTO_TARGET_REF,
    MatrixCryptoOperation,
    matrix_crypto_lane,
    matrix_crypto_rollback_ref,
)


def stable_matrix_crypto_ref(prefix: str, payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


class _MatrixCryptoModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MatrixCryptoRuntimeStatus(str, Enum):
    adapter_required = "adapter_required"
    configuration_required = "configuration_required"
    blocked = "blocked"
    ready = "ready"
    unknown = "unknown"


class MatrixCryptoFreshness(str, Enum):
    current = "current"
    stale = "stale"
    unknown = "unknown"


class MatrixCryptoCommand(_MatrixCryptoModel):
    schema_version: Literal["uaa-matrix-crypto.v1"] = MATRIX_CRYPTO_SCHEMA_VERSION
    operation: MatrixCryptoOperation
    request_ref: str = Field(..., max_length=240)
    task_ref: str = Field(..., max_length=240)
    mission_ref: str = Field(..., max_length=240)
    run_ref: str = Field(..., max_length=240)
    dispatch_ref: str = Field(..., max_length=240)
    idempotency_ref: str = Field(..., max_length=240)
    lease_ref: str = Field(..., max_length=240)
    account_ref: str = Field(..., max_length=240)
    device_ref: str = Field(..., max_length=240)
    peer_device_ref: str | None = Field(default=None, max_length=240)
    crypto_store_ref: str = Field(..., max_length=240)
    store_schema_ref: str = Field(..., max_length=240)
    store_generation_ref: str = Field(..., max_length=240)
    crypto_key_item_ref: str = Field(..., max_length=240)
    crypto_key_version_ref: str = Field(..., max_length=240)
    next_crypto_key_version_ref: str | None = Field(default=None, max_length=240)
    verification_transaction_ref: str | None = Field(default=None, max_length=240)
    verification_method_ref: str | None = Field(default=None, max_length=240)
    verification_generation_ref: str | None = Field(default=None, max_length=240)
    transcript_hash_ref: str | None = Field(default=None, max_length=240)
    cross_signing_generation_ref: str = Field(..., max_length=240)
    backup_ref: str = Field(..., max_length=240)
    backup_version_ref: str = Field(..., max_length=240)
    next_backup_version_ref: str | None = Field(default=None, max_length=240)
    backup_integrity_ref: str = Field(..., max_length=240)
    backup_key_item_ref: str = Field(..., max_length=240)
    backup_key_version_ref: str = Field(..., max_length=240)
    staging_store_ref: str | None = Field(default=None, max_length=240)
    recovery_target_ref: str = Field(..., max_length=240)
    recovery_attempt_ref: str = Field(..., max_length=240)
    consequence_review_ref: str | None = Field(default=None, max_length=240)
    target_ref: Literal["target-ref:communications:matrix-crypto-exact-scope"] = (
        MATRIX_CRYPTO_TARGET_REF
    )
    provider_ref: Literal["provider-ref:communications:matrix"] = (
        MATRIX_CRYPTO_PROVIDER_REF
    )
    runtime_ref: Literal["runtime-ref:matrix-rust-crypto:adapter-required-v1"] = (
        MATRIX_CRYPTO_RUNTIME_REF
    )
    store_backend_ref: Literal[
        "crypto-store-backend-ref:matrix:persistent-rust-store-required-v1"
    ] = MATRIX_CRYPTO_STORE_BACKEND_REF
    key_backend_ref: Literal[
        "credential-backend-ref:matrix:device-only-keychain-crypto-v1"
    ] = MATRIX_CRYPTO_KEY_BACKEND_REF
    backup_backend_ref: Literal[
        "backup-backend-ref:matrix:dedicated-wrapping-key-required-v1"
    ] = MATRIX_CRYPTO_BACKUP_BACKEND_REF
    budget_ref: Literal["budget-ref:communications:matrix-crypto-zero-cost"] = (
        MATRIX_CRYPTO_BUDGET_REF
    )
    kill_switch_ref: Literal["kill-switch-ref:authority-lease-local"] = (
        MATRIX_CRYPTO_KILL_SWITCH_REF
    )
    safe_disable_ref: Literal["safe-disable-ref:communications:matrix-crypto"] = (
        MATRIX_CRYPTO_SAFE_DISABLE_REF
    )
    readiness_ref: str = Field(..., max_length=240)
    rollback_ref: str = Field(..., max_length=240)
    request_created_at: datetime
    start_deadline: datetime
    max_duration_ms: int = Field(default=10_000, ge=100, le=30_000)
    max_cost_microusd: Literal[0] = 0
    request_fingerprint_ref: str = Field(..., max_length=240)

    @model_validator(mode="after")
    def validate_command(self) -> "MatrixCryptoCommand":
        for value in self.model_dump(mode="python").values():
            if isinstance(value, str) and value != self.operation.value:
                if value.startswith(("uaa-",)):
                    continue
                validate_execution_ref(value, "matrix_crypto_command_ref")
        if self.request_created_at.tzinfo is None or self.start_deadline.tzinfo is None:
            raise ValueError("MATRIX_CRYPTO_TIMEZONE_REQUIRED")
        if self.request_created_at >= self.start_deadline:
            raise ValueError("MATRIX_CRYPTO_DEADLINE_ORDER_INVALID")
        if self.start_deadline - self.request_created_at > timedelta(minutes=5):
            raise ValueError("MATRIX_CRYPTO_DEADLINE_WINDOW_EXCEEDED")
        verification = self.operation in {
            MatrixCryptoOperation.verification_request,
            MatrixCryptoOperation.verification_cancel,
            MatrixCryptoOperation.verification_confirm,
        }
        verification_refs = (
            self.peer_device_ref,
            self.verification_transaction_ref,
            self.verification_method_ref,
            self.verification_generation_ref,
        )
        if verification and any(value is None for value in verification_refs):
            raise ValueError("MATRIX_CRYPTO_EXACT_VERIFICATION_SCOPE_REQUIRED")
        if not verification and any(value is not None for value in verification_refs):
            raise ValueError("MATRIX_CRYPTO_VERIFICATION_SCOPE_FORBIDDEN")
        if self.operation == MatrixCryptoOperation.verification_confirm:
            if self.transcript_hash_ref is None:
                raise ValueError("MATRIX_CRYPTO_TRANSCRIPT_HASH_REQUIRED")
        elif self.transcript_hash_ref is not None:
            raise ValueError("MATRIX_CRYPTO_TRANSCRIPT_HASH_FORBIDDEN")
        if self.operation == MatrixCryptoOperation.crypto_store_key_rotate:
            if (
                self.next_crypto_key_version_ref is None
                or self.next_crypto_key_version_ref == self.crypto_key_version_ref
            ):
                raise ValueError("MATRIX_CRYPTO_NEXT_STORE_KEY_VERSION_REQUIRED")
        elif self.next_crypto_key_version_ref is not None:
            raise ValueError("MATRIX_CRYPTO_NEXT_STORE_KEY_VERSION_FORBIDDEN")
        if self.operation == MatrixCryptoOperation.backup_rotate:
            if (
                self.next_backup_version_ref is None
                or self.next_backup_version_ref == self.backup_version_ref
            ):
                raise ValueError("MATRIX_CRYPTO_NEXT_BACKUP_VERSION_REQUIRED")
        elif self.next_backup_version_ref is not None:
            raise ValueError("MATRIX_CRYPTO_NEXT_BACKUP_VERSION_FORBIDDEN")
        if self.operation in {
            MatrixCryptoOperation.recovery_restore,
            MatrixCryptoOperation.local_backup_restore,
        }:
            if self.staging_store_ref is None:
                raise ValueError("MATRIX_CRYPTO_STAGED_RESTORE_REQUIRED")
            if self.staging_store_ref == self.crypto_store_ref:
                raise ValueError("MATRIX_CRYPTO_IN_PLACE_RESTORE_DENIED")
        elif self.staging_store_ref is not None:
            raise ValueError("MATRIX_CRYPTO_STAGING_STORE_FORBIDDEN")
        if self.operation == MatrixCryptoOperation.identity_reset:
            if self.consequence_review_ref is None:
                raise ValueError("MATRIX_CRYPTO_CONSEQUENCE_REVIEW_REQUIRED")
        elif self.consequence_review_ref is not None:
            raise ValueError("MATRIX_CRYPTO_CONSEQUENCE_REVIEW_FORBIDDEN")
        if self.rollback_ref != matrix_crypto_rollback_ref(self.operation):
            raise ValueError("MATRIX_CRYPTO_ROLLBACK_POSTURE_MISMATCH")
        expected = matrix_crypto_request_fingerprint_ref(
            **self.model_dump(mode="python", exclude={"request_fingerprint_ref"})
        )
        if self.request_fingerprint_ref != expected:
            raise ValueError("MATRIX_CRYPTO_REQUEST_FINGERPRINT_MISMATCH")
        return self


class MatrixCryptoProposal(_MatrixCryptoModel):
    schema_version: Literal["uaa-matrix-crypto-proposal.v1"] = (
        "uaa-matrix-crypto-proposal.v1"
    )
    proposal_ref: str
    operation: MatrixCryptoOperation
    request_fingerprint_ref: str
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    required_mode: str
    target_refs: tuple[str, ...] = Field(min_length=1, max_length=64)
    approval_required: StrictBool
    lease_required: Literal[True] = True
    execution_permitted: Literal[False] = False
    mutation_performed: Literal[False] = False
    approval_ref_authorizes_execution: Literal[False] = False
    recovery_material_included: Literal[False] = False
    raw_crypto_payload_included: Literal[False] = False
    expected_receipt_ref: str
    rollback_ref: str
    safe_disable_ref: str
    reason_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    blocker_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    safe_summary: str = Field(..., min_length=1, max_length=240)
    redaction_status: Literal["safe_refs_only"] = "safe_refs_only"

    @model_validator(mode="after")
    def validate_refs(self) -> "MatrixCryptoProposal":
        for value in (
            self.proposal_ref,
            self.request_fingerprint_ref,
            self.lane_ref,
            self.capability_ref,
            self.adapter_ref,
            *self.target_refs,
            self.expected_receipt_ref,
            self.rollback_ref,
            self.safe_disable_ref,
            *self.reason_refs,
            *self.blocker_refs,
        ):
            validate_execution_ref(value, "matrix_crypto_proposal_ref")
        return self


class MatrixCryptoPosture(_MatrixCryptoModel):
    schema_version: Literal["uaa-matrix-crypto-posture.v1"] = (
        "uaa-matrix-crypto-posture.v1"
    )
    posture_ref: str
    runtime_status: MatrixCryptoRuntimeStatus
    freshness: MatrixCryptoFreshness
    authority_lane_refs: tuple[str, ...]
    accepted_authority_operation_refs: tuple[str, ...]
    live_executor_operation_refs: tuple[str, ...]
    blocked_operation_refs: tuple[str, ...]
    provider_ref: str
    runtime_ref: str
    store_backend_ref: str
    key_backend_ref: str
    backup_backend_ref: str
    reason_refs: tuple[str, ...]
    blocker_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    single_owner_required: Literal[True] = True
    request_scoped_evaluation_required: Literal[True] = True
    recovery_material_included: Literal[False] = False
    raw_crypto_payload_included: Literal[False] = False
    element_interoperability_status: Literal["external_facility_required"] = (
        "external_facility_required"
    )
    desktop_only: Literal[True] = True
    safe_summary: str = Field(..., min_length=1, max_length=240)
    redaction_status: Literal["safe_refs_only"] = "safe_refs_only"

    @model_validator(mode="after")
    def validate_posture(self) -> "MatrixCryptoPosture":
        values = (
            self.posture_ref,
            *self.authority_lane_refs,
            *self.accepted_authority_operation_refs,
            *self.live_executor_operation_refs,
            *self.blocked_operation_refs,
            self.provider_ref,
            self.runtime_ref,
            self.store_backend_ref,
            self.key_backend_ref,
            self.backup_backend_ref,
            *self.reason_refs,
            *self.blocker_refs,
            *self.evidence_refs,
        )
        for value in values:
            validate_execution_ref(value, "matrix_crypto_posture_ref")
        expected_lanes = tuple(lane.lane_ref for lane in MATRIX_CRYPTO_LANES.values())
        expected_operations = tuple(
            f"operation-ref:matrix-crypto:{operation.value.replace('_', '-')}"
            for operation in MatrixCryptoOperation
        )
        if self.runtime_status != MatrixCryptoRuntimeStatus.adapter_required:
            raise ValueError("MATRIX_CRYPTO_RUNTIME_STATUS_NOT_PROVEN")
        if self.freshness != MatrixCryptoFreshness.unknown:
            raise ValueError("MATRIX_CRYPTO_FRESHNESS_NOT_PROVEN")
        if self.authority_lane_refs != expected_lanes:
            raise ValueError("MATRIX_CRYPTO_AUTHORITY_LANE_SET_MISMATCH")
        if self.accepted_authority_operation_refs != expected_operations:
            raise ValueError("MATRIX_CRYPTO_ACCEPTED_OPERATION_SET_MISMATCH")
        if self.blocked_operation_refs != expected_operations:
            raise ValueError("MATRIX_CRYPTO_BLOCKED_OPERATION_SET_MISMATCH")
        if self.live_executor_operation_refs:
            raise ValueError("MATRIX_CRYPTO_LIVE_EXECUTOR_CLAIM_NOT_PROVEN")
        return self


def matrix_crypto_request_fingerprint_ref(**values: object) -> str:
    payload = {
        "peer_device_ref": None,
        "next_crypto_key_version_ref": None,
        "verification_transaction_ref": None,
        "verification_method_ref": None,
        "verification_generation_ref": None,
        "transcript_hash_ref": None,
        "next_backup_version_ref": None,
        "staging_store_ref": None,
        "consequence_review_ref": None,
        "target_ref": MATRIX_CRYPTO_TARGET_REF,
        "provider_ref": MATRIX_CRYPTO_PROVIDER_REF,
        "runtime_ref": MATRIX_CRYPTO_RUNTIME_REF,
        "store_backend_ref": MATRIX_CRYPTO_STORE_BACKEND_REF,
        "key_backend_ref": MATRIX_CRYPTO_KEY_BACKEND_REF,
        "backup_backend_ref": MATRIX_CRYPTO_BACKUP_BACKEND_REF,
        "budget_ref": MATRIX_CRYPTO_BUDGET_REF,
        "kill_switch_ref": MATRIX_CRYPTO_KILL_SWITCH_REF,
        "safe_disable_ref": MATRIX_CRYPTO_SAFE_DISABLE_REF,
        "max_duration_ms": 10_000,
        "max_cost_microusd": 0,
        **values,
    }
    operation = MatrixCryptoOperation(payload.pop("operation"))
    payload.pop("schema_version", None)
    return stable_matrix_crypto_ref(
        "request-fingerprint-ref:matrix-crypto",
        {"operation": operation.value, **payload},
    )


def matrix_crypto_start_deadline_ref(value: datetime) -> str:
    return stable_matrix_crypto_ref(
        "deadline-ref:matrix-crypto",
        {"start_deadline": value.isoformat()},
    )


def matrix_crypto_exact_resource_refs(command: MatrixCryptoCommand) -> tuple[str, ...]:
    lane = matrix_crypto_lane(command.operation)
    values = (
        lane.lane_ref,
        lane.capability_ref,
        lane.adapter_ref,
        lane.tool_ref,
        command.request_ref,
        command.task_ref,
        command.mission_ref,
        command.run_ref,
        command.dispatch_ref,
        command.idempotency_ref,
        command.lease_ref,
        command.account_ref,
        command.device_ref,
        command.peer_device_ref,
        command.crypto_store_ref,
        command.store_schema_ref,
        command.store_generation_ref,
        command.crypto_key_item_ref,
        command.crypto_key_version_ref,
        command.next_crypto_key_version_ref,
        command.verification_transaction_ref,
        command.verification_method_ref,
        command.verification_generation_ref,
        command.transcript_hash_ref,
        command.cross_signing_generation_ref,
        command.backup_ref,
        command.backup_version_ref,
        command.next_backup_version_ref,
        command.backup_integrity_ref,
        command.backup_key_item_ref,
        command.backup_key_version_ref,
        command.staging_store_ref,
        command.recovery_target_ref,
        command.recovery_attempt_ref,
        command.consequence_review_ref,
        command.target_ref,
        command.provider_ref,
        command.runtime_ref,
        command.store_backend_ref,
        command.key_backend_ref,
        command.backup_backend_ref,
        command.budget_ref,
        command.kill_switch_ref,
        command.safe_disable_ref,
        command.readiness_ref,
        command.rollback_ref,
        command.request_fingerprint_ref,
        matrix_crypto_start_deadline_ref(command.start_deadline),
    )
    return tuple(sorted({value for value in values if value is not None}))


def build_matrix_crypto_proposal(command: MatrixCryptoCommand) -> MatrixCryptoProposal:
    lane = matrix_crypto_lane(command.operation)
    return MatrixCryptoProposal(
        proposal_ref=stable_matrix_crypto_ref(
            "proposal-ref:matrix-crypto",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        operation=command.operation,
        request_fingerprint_ref=command.request_fingerprint_ref,
        lane_ref=lane.lane_ref,
        capability_ref=lane.capability_ref,
        adapter_ref=lane.adapter_ref,
        required_mode=lane.required_mode.value,
        target_refs=matrix_crypto_exact_resource_refs(command),
        approval_required=lane.approval_required,
        expected_receipt_ref=stable_matrix_crypto_ref(
            "receipt-ref:matrix-crypto:expected",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        rollback_ref=command.rollback_ref,
        safe_disable_ref=command.safe_disable_ref,
        reason_refs=(
            "reason-ref:matrix-crypto:exact-authority-accepted",
            "reason-ref:matrix-crypto:request-scoped-evaluation-required",
        ),
        blocker_refs=(
            "blocker-ref:matrix-crypto:persistent-rust-backend-required",
            "blocker-ref:matrix-crypto:authenticated-session-required",
            "blocker-ref:matrix-crypto:live-executor-uncomposed",
        ),
        safe_summary=(
            "Review one exact Matrix crypto request; no key, recovery material, "
            "store mutation, device trust change, backup action, or reset occurred."
        ),
    )


def build_default_matrix_crypto_posture() -> MatrixCryptoPosture:
    operations = tuple(
        f"operation-ref:matrix-crypto:{operation.value.replace('_', '-')}"
        for operation in MatrixCryptoOperation
    )
    return MatrixCryptoPosture(
        posture_ref="posture-ref:matrix-crypto:adapter-required-v1",
        runtime_status=MatrixCryptoRuntimeStatus.adapter_required,
        freshness=MatrixCryptoFreshness.unknown,
        authority_lane_refs=tuple(
            lane.lane_ref for lane in MATRIX_CRYPTO_LANES.values()
        ),
        accepted_authority_operation_refs=operations,
        live_executor_operation_refs=(),
        blocked_operation_refs=operations,
        provider_ref=MATRIX_CRYPTO_PROVIDER_REF,
        runtime_ref=MATRIX_CRYPTO_RUNTIME_REF,
        store_backend_ref=MATRIX_CRYPTO_STORE_BACKEND_REF,
        key_backend_ref=MATRIX_CRYPTO_KEY_BACKEND_REF,
        backup_backend_ref=MATRIX_CRYPTO_BACKUP_BACKEND_REF,
        reason_refs=(
            "reason-ref:matrix-crypto:exact-authority-contracts-accepted",
            "reason-ref:matrix-crypto:legacy-crypto-denied",
            "reason-ref:matrix-crypto:recovery-material-output-denied",
        ),
        blocker_refs=(
            "blocker-ref:matrix-crypto:persistent-rust-backend-required",
            "blocker-ref:matrix-crypto:authenticated-session-required",
            "blocker-ref:matrix-crypto:element-interoperability-external",
        ),
        evidence_refs=(
            "evidence-ref:matrix-crypto:authority-contract-tests",
            "evidence-ref:matrix-crypto:fail-closed-adapter-boundary",
            "evidence-ref:matrix-crypto:redaction-tests",
        ),
        safe_summary=(
            "Exact crypto authorities are declared for fresh evaluation, but live "
            "persistent Rust crypto, recovery, and device trust remain blocked."
        ),
    )
