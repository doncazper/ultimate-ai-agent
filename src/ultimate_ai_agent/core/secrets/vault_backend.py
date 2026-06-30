from __future__ import annotations

import json
import os
import uuid
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import ApprovalRiskLevel, ApprovalSubjectType
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification
from ultimate_ai_agent.core.secrets.vault_contracts import (
    ProviderCredentialVaultPosture,
    _reject_unsafe_payload,
    _require_safe_ref,
)
from ultimate_ai_agent.core.time import utc_now


LOCAL_CREDENTIAL_VAULT_BACKEND_REF = "credential-vault-backend-ref:local-secret-ref:v1"
LOCAL_CREDENTIAL_VAULT_STORAGE_REF = "credential-vault-storage-ref:local-secret-ref-ledger:v1"
LOCAL_CREDENTIAL_VAULT_CLI_REF = "cli-inspection-ref:provider-credential-vault-backend-v1"
UAA_CREDENTIAL_VAULT_STATE_DIR_ENV = "UAA_CREDENTIAL_VAULT_STATE_DIR"
LOCAL_CREDENTIAL_VAULT_ACTION_ENROLL = "credential_vault_enroll_secret_ref"
LOCAL_CREDENTIAL_VAULT_ACTION_REVOKE = "credential_vault_revoke_secret_ref"
LOCAL_CREDENTIAL_VAULT_ACTION_MARK_ROTATION = "credential_vault_mark_rotation_required"

_BACKEND_BLOCKER_CODES = {
    "RAW_SECRET_MATERIAL_NOT_PERSISTED",
    "SECRET_RESOLUTION_NOT_EXPOSED",
    "PROVIDER_VALIDATION_BLOCKED",
    "PROVIDER_INVOCATION_BLOCKED",
    "PROVIDER_SDK_CALL_BLOCKED",
    "MODEL_INVOCATION_BLOCKED",
    "BILLING_AUTHORITY_BLOCKED",
}
_DENIED_AUTHORITY_FLAGS = (
    "raw_secret_material_persisted",
    "raw_secret_material_returned",
    "recoverable_secret_material_available",
    "secret_resolution_enabled",
    "credential_validation_enabled",
    "provider_sdk_call_enabled",
    "model_invocation_enabled",
    "provider_invocation_enabled",
    "billing_authority_granted",
    "vault_presence_authorizes_validation",
    "vault_presence_authorizes_invocation",
)
_RECORD_REF_FIELDS = (
    "backend_ref",
    "storage_ref",
    "record_ref",
    "run_id",
    "provider_ref",
    "model_ref",
    "credential_ref",
    "secret_ref",
    "policy_ref",
    "approval_ref",
    "approval_scope_ref",
    "budget_decision_ref",
    "expected_receipt_ref",
    "revocation_ref",
    "rotation_required_ref",
    "enrollment_receipt_ref",
    "last_operation_receipt_ref",
)
_REQUEST_REF_FIELDS = (
    "provider_ref",
    "model_ref",
    "credential_ref",
    "policy_ref",
    "approval_scope_ref",
    "budget_decision_ref",
    "expected_receipt_ref",
    "idempotency_ref",
)


class LocalCredentialVaultOperation(str, Enum):
    enroll = "enroll"
    revoke = "revoke"
    mark_rotation_required = "mark_rotation_required"


class _LocalCredentialVaultModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    def model_copy(self, *, update: Any | None = None, deep: bool = False) -> Any:
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


def _require_safe_refs(instance: Any, fields: tuple[str, ...]) -> None:
    for field_name in fields:
        value = getattr(instance, field_name)
        if value is None:
            continue
        _require_safe_ref(str(value), field_name)


def _suffix(ref: str) -> str:
    return ref.split(":")[-1].replace("_", "-")


def _new_safe_ref(prefix: str, scope_ref: str) -> str:
    return f"{prefix}:{_suffix(scope_ref)}:{uuid.uuid4().hex[:12]}"


def _utc_timestamp() -> str:
    return utc_now().replace(microsecond=0).isoformat()


def _default_actor_context() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="operator:local",
        authority_source=AuthoritySource.manual_operator_action,
    )


def _default_data_classification() -> DataClassification:
    return DataClassification(
        classification=ClassificationValue.project_private,
        source="credential_vault_backend_v1",
        requires_redaction=True,
        requires_consent=True,
    )


def _posture_from_records(
    records: list["LocalCredentialVaultRecord"],
) -> ProviderCredentialVaultPosture:
    if not records:
        return ProviderCredentialVaultPosture.vault_not_configured
    if any(record.posture == ProviderCredentialVaultPosture.rotation_required for record in records):
        return ProviderCredentialVaultPosture.rotation_required
    if any(record.posture == ProviderCredentialVaultPosture.secret_ref_available for record in records):
        return ProviderCredentialVaultPosture.secret_ref_available
    if all(record.posture == ProviderCredentialVaultPosture.secret_ref_revoked for record in records):
        return ProviderCredentialVaultPosture.secret_ref_revoked
    return ProviderCredentialVaultPosture.vault_blocked


def _require_approval(
    approval_authority: LocalApprovalAuthority | None,
    approval_request: ApprovalRequest,
    approval_ref: str,
) -> None:
    if approval_authority is None:
        raise ValueError("LOCAL_CREDENTIAL_VAULT_APPROVAL_REQUIRED")
    decision = approval_authority.validate_for_request(approval_request, approval_ref)
    if not decision.allowed:
        raise ValueError("LOCAL_CREDENTIAL_VAULT_APPROVAL_DENIED")


def enrollment_resource_refs(request: "LocalCredentialVaultEnrollmentRequest") -> list[str]:
    return [
        request.provider_ref,
        request.model_ref,
        request.credential_ref,
        request.policy_ref,
        request.approval_scope_ref,
        request.budget_decision_ref,
        request.expected_receipt_ref,
        request.idempotency_ref,
        request.revocation_ref,
        request.rotation_required_ref,
    ]


def revoke_resource_refs(request: "LocalCredentialVaultRevokeRequest") -> list[str]:
    return [
        request.secret_ref,
        request.provider_ref,
        request.model_ref,
        request.credential_ref,
        request.revocation_ref,
        request.policy_ref,
        request.approval_scope_ref,
        request.budget_decision_ref,
        request.expected_receipt_ref,
        request.idempotency_ref,
    ]


def rotation_resource_refs(request: "LocalCredentialVaultRotationRequiredRequest") -> list[str]:
    return [
        request.secret_ref,
        request.provider_ref,
        request.model_ref,
        request.credential_ref,
        request.rotation_required_ref,
        request.policy_ref,
        request.approval_scope_ref,
        request.budget_decision_ref,
        request.expected_receipt_ref,
        request.idempotency_ref,
    ]


def build_local_credential_vault_enrollment_approval_request(
    request: "LocalCredentialVaultEnrollmentRequest",
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=f"approval-request:{request.idempotency_ref}",
        run_id=request.run_id,
        subject_type=ApprovalSubjectType.credential_access,
        subject_id=request.credential_ref,
        actor_context=request.actor_context,
        requested_action=LOCAL_CREDENTIAL_VAULT_ACTION_ENROLL,
        purpose="Approve one exact-scoped local credential vault safe-ref enrollment.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=request.data_classification,
        resource_refs=enrollment_resource_refs(request),
        provider_id=request.provider_ref,
        event_ref=request.expected_receipt_ref,
        trace_id=request.idempotency_ref,
    )


def build_local_credential_vault_revoke_approval_request(
    request: "LocalCredentialVaultRevokeRequest",
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=f"approval-request:{request.idempotency_ref}",
        run_id=request.run_id,
        subject_type=ApprovalSubjectType.credential_access,
        subject_id=request.secret_ref,
        actor_context=request.actor_context,
        requested_action=LOCAL_CREDENTIAL_VAULT_ACTION_REVOKE,
        purpose="Approve one exact-scoped local credential vault safe-ref revocation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=request.data_classification,
        resource_refs=revoke_resource_refs(request),
        event_ref=request.expected_receipt_ref,
        trace_id=request.idempotency_ref,
    )


def build_local_credential_vault_rotation_approval_request(
    request: "LocalCredentialVaultRotationRequiredRequest",
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=f"approval-request:{request.idempotency_ref}",
        run_id=request.run_id,
        subject_type=ApprovalSubjectType.credential_access,
        subject_id=request.secret_ref,
        actor_context=request.actor_context,
        requested_action=LOCAL_CREDENTIAL_VAULT_ACTION_MARK_ROTATION,
        purpose="Approve one exact-scoped local credential vault rotation-required posture update.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=request.data_classification,
        resource_refs=rotation_resource_refs(request),
        event_ref=request.expected_receipt_ref,
        trace_id=request.idempotency_ref,
    )


def _enrollment_idempotency_scope(request: "LocalCredentialVaultEnrollmentRequest") -> dict[str, str]:
    return {
        "run_id": request.run_id,
        "provider_ref": request.provider_ref,
        "model_ref": request.model_ref,
        "credential_ref": request.credential_ref,
        "policy_ref": request.policy_ref,
        "approval_ref": request.approval_ref,
        "approval_scope_ref": request.approval_scope_ref,
        "budget_decision_ref": request.budget_decision_ref,
        "expected_receipt_ref": request.expected_receipt_ref,
        "idempotency_ref": request.idempotency_ref,
        "revocation_ref": request.revocation_ref,
        "rotation_required_ref": request.rotation_required_ref,
    }


def _revoke_idempotency_scope(request: "LocalCredentialVaultRevokeRequest") -> dict[str, str]:
    return {
        "run_id": request.run_id,
        "secret_ref": request.secret_ref,
        "provider_ref": request.provider_ref,
        "model_ref": request.model_ref,
        "credential_ref": request.credential_ref,
        "revocation_ref": request.revocation_ref,
        "policy_ref": request.policy_ref,
        "approval_ref": request.approval_ref,
        "approval_scope_ref": request.approval_scope_ref,
        "budget_decision_ref": request.budget_decision_ref,
        "expected_receipt_ref": request.expected_receipt_ref,
        "idempotency_ref": request.idempotency_ref,
    }


def _rotation_idempotency_scope(
    request: "LocalCredentialVaultRotationRequiredRequest",
) -> dict[str, str]:
    return {
        "run_id": request.run_id,
        "secret_ref": request.secret_ref,
        "provider_ref": request.provider_ref,
        "model_ref": request.model_ref,
        "credential_ref": request.credential_ref,
        "rotation_required_ref": request.rotation_required_ref,
        "policy_ref": request.policy_ref,
        "approval_ref": request.approval_ref,
        "approval_scope_ref": request.approval_scope_ref,
        "budget_decision_ref": request.budget_decision_ref,
        "expected_receipt_ref": request.expected_receipt_ref,
        "idempotency_ref": request.idempotency_ref,
    }


def _receipt_idempotency_scope(receipt: "LocalCredentialVaultOperationReceipt") -> dict[str, str]:
    base = {
        "run_id": receipt.run_id,
        "policy_ref": receipt.policy_ref,
        "approval_ref": receipt.approval_ref,
        "approval_scope_ref": receipt.approval_scope_ref,
        "expected_receipt_ref": receipt.expected_receipt_ref,
        "idempotency_ref": receipt.idempotency_ref,
    }
    if receipt.operation == LocalCredentialVaultOperation.enroll:
        return {
            **base,
            "provider_ref": receipt.provider_ref,
            "model_ref": receipt.model_ref,
            "credential_ref": receipt.credential_ref,
            "budget_decision_ref": receipt.budget_decision_ref,
            "revocation_ref": receipt.revocation_ref,
            "rotation_required_ref": receipt.rotation_required_ref,
        }
    if receipt.operation == LocalCredentialVaultOperation.revoke:
        return {
            **base,
            "secret_ref": receipt.secret_ref,
            "provider_ref": receipt.provider_ref,
            "model_ref": receipt.model_ref,
            "credential_ref": receipt.credential_ref,
            "budget_decision_ref": receipt.budget_decision_ref,
            "revocation_ref": receipt.revocation_ref,
        }
    return {
        **base,
        "secret_ref": receipt.secret_ref,
        "provider_ref": receipt.provider_ref,
        "model_ref": receipt.model_ref,
        "credential_ref": receipt.credential_ref,
        "budget_decision_ref": receipt.budget_decision_ref,
        "rotation_required_ref": receipt.rotation_required_ref,
    }


def _require_record_scope_for_request(
    record: "LocalCredentialVaultRecord",
    request: "LocalCredentialVaultRevokeRequest | LocalCredentialVaultRotationRequiredRequest",
) -> None:
    immutable_fields = (
        "run_id",
        "secret_ref",
        "provider_ref",
        "model_ref",
        "credential_ref",
        "budget_decision_ref",
    )
    if any(getattr(record, field) != getattr(request, field) for field in immutable_fields):
        raise ValueError("LOCAL_CREDENTIAL_VAULT_RECORD_SCOPE_MISMATCH")


class LocalCredentialVaultRecord(_LocalCredentialVaultModel):
    backend_ref: str = LOCAL_CREDENTIAL_VAULT_BACKEND_REF
    storage_ref: str = LOCAL_CREDENTIAL_VAULT_STORAGE_REF
    record_ref: str
    run_id: str
    posture: ProviderCredentialVaultPosture
    provider_ref: str
    model_ref: str
    credential_ref: str
    secret_ref: str
    policy_ref: str
    approval_ref: str
    approval_scope_ref: str
    budget_decision_ref: str
    expected_receipt_ref: str
    revocation_ref: str = "revocation-ref:provider-runtime:not-active"
    rotation_required_ref: str = "rotation-ref:provider-runtime:not-required"
    enrollment_receipt_ref: str
    last_operation_receipt_ref: str
    safe_refs_only: bool = True
    durable_ref_record: bool = True
    transient_secret_discarded: bool = True
    raw_secret_material_persisted: bool = False
    raw_secret_material_returned: bool = False
    recoverable_secret_material_available: bool = False
    secret_resolution_enabled: bool = False
    credential_validation_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    provider_invocation_enabled: bool = False
    billing_authority_granted: bool = False
    vault_presence_authorizes_validation: bool = False
    vault_presence_authorizes_invocation: bool = False
    blocker_codes: list[str] = Field(default_factory=lambda: sorted(_BACKEND_BLOCKER_CODES))
    created_at: str = Field(default_factory=_utc_timestamp)
    updated_at: str = Field(default_factory=_utc_timestamp)
    safe_summary: str = (
        "Local credential vault backend V1 stores durable safe refs and operation posture only; "
        "transient secret material is discarded and provider validation or invocation remains blocked."
    )

    @model_validator(mode="after")
    def record_must_remain_safe_ref_only(self) -> Any:
        payload = self.model_dump(mode="json")
        _reject_unsafe_payload(
            payload,
            "LOCAL_CREDENTIAL_VAULT_RECORD_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        _require_safe_refs(self, _RECORD_REF_FIELDS)
        if not self.safe_refs_only or not self.durable_ref_record or not self.transient_secret_discarded:
            raise ValueError("LOCAL_CREDENTIAL_VAULT_RECORD_SAFE_LEDGER_REQUIRED")
        if any(getattr(self, flag) for flag in _DENIED_AUTHORITY_FLAGS):
            raise ValueError("LOCAL_CREDENTIAL_VAULT_RECORD_AUTHORITY_DENIED")
        if not _BACKEND_BLOCKER_CODES.issubset(set(self.blocker_codes)):
            raise ValueError("LOCAL_CREDENTIAL_VAULT_RECORD_BLOCKER_CODES_REQUIRED")
        if self.posture not in {
            ProviderCredentialVaultPosture.secret_ref_available,
            ProviderCredentialVaultPosture.secret_ref_revoked,
            ProviderCredentialVaultPosture.rotation_required,
            ProviderCredentialVaultPosture.vault_blocked,
        }:
            raise ValueError("LOCAL_CREDENTIAL_VAULT_RECORD_POSTURE_DENIED")
        return self


class LocalCredentialVaultEnrollmentRequest(_LocalCredentialVaultModel):
    run_id: str
    provider_ref: str
    model_ref: str
    credential_ref: str
    policy_ref: str
    approval_ref: str
    approval_scope_ref: str
    budget_decision_ref: str
    expected_receipt_ref: str
    idempotency_ref: str
    actor_context: ActorContext = Field(default_factory=_default_actor_context)
    data_classification: DataClassification = Field(default_factory=_default_data_classification)
    revocation_ref: str = "revocation-ref:provider-runtime:not-active"
    rotation_required_ref: str = "rotation-ref:provider-runtime:not-required"
    secret_value: SecretStr = Field(..., exclude=True, repr=False)

    @model_validator(mode="after")
    def enrollment_request_must_keep_secret_transient(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "LOCAL_CREDENTIAL_VAULT_ENROLLMENT_REQUEST_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        _require_safe_refs(
            self,
            (
                "run_id",
                *_REQUEST_REF_FIELDS,
                "approval_ref",
                "revocation_ref",
                "rotation_required_ref",
            ),
        )
        if not self.secret_value.get_secret_value().strip():
            raise ValueError("LOCAL_CREDENTIAL_VAULT_ENROLLMENT_SECRET_VALUE_REQUIRED")
        return self


class LocalCredentialVaultRevokeRequest(_LocalCredentialVaultModel):
    run_id: str
    secret_ref: str
    provider_ref: str
    model_ref: str
    credential_ref: str
    revocation_ref: str
    policy_ref: str
    approval_ref: str
    approval_scope_ref: str
    budget_decision_ref: str
    expected_receipt_ref: str
    idempotency_ref: str
    actor_context: ActorContext = Field(default_factory=_default_actor_context)
    data_classification: DataClassification = Field(default_factory=_default_data_classification)

    @model_validator(mode="after")
    def revoke_request_must_use_safe_refs(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "LOCAL_CREDENTIAL_VAULT_REVOKE_REQUEST_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        _require_safe_refs(
            self,
            (
                "run_id",
                "secret_ref",
                "provider_ref",
                "model_ref",
                "credential_ref",
                "revocation_ref",
                "policy_ref",
                "approval_ref",
                "approval_scope_ref",
                "budget_decision_ref",
                "expected_receipt_ref",
                "idempotency_ref",
            ),
        )
        return self


class LocalCredentialVaultRotationRequiredRequest(_LocalCredentialVaultModel):
    run_id: str
    secret_ref: str
    provider_ref: str
    model_ref: str
    credential_ref: str
    rotation_required_ref: str
    policy_ref: str
    approval_ref: str
    approval_scope_ref: str
    budget_decision_ref: str
    expected_receipt_ref: str
    idempotency_ref: str
    actor_context: ActorContext = Field(default_factory=_default_actor_context)
    data_classification: DataClassification = Field(default_factory=_default_data_classification)

    @model_validator(mode="after")
    def rotation_request_must_use_safe_refs(self) -> Any:
        _reject_unsafe_payload(
            self.model_dump(mode="json"),
            "LOCAL_CREDENTIAL_VAULT_ROTATION_REQUEST_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        _require_safe_refs(
            self,
            (
                "run_id",
                "secret_ref",
                "provider_ref",
                "model_ref",
                "credential_ref",
                "rotation_required_ref",
                "policy_ref",
                "approval_ref",
                "approval_scope_ref",
                "budget_decision_ref",
                "expected_receipt_ref",
                "idempotency_ref",
            ),
        )
        return self


class LocalCredentialVaultOperationReceipt(_LocalCredentialVaultModel):
    receipt_ref: str
    run_id: str
    operation: LocalCredentialVaultOperation
    allowed: bool
    posture: ProviderCredentialVaultPosture
    backend_ref: str = LOCAL_CREDENTIAL_VAULT_BACKEND_REF
    storage_ref: str = LOCAL_CREDENTIAL_VAULT_STORAGE_REF
    record_ref: str
    secret_ref: str
    provider_ref: str
    model_ref: str
    credential_ref: str
    policy_ref: str
    approval_ref: str
    approval_scope_ref: str
    budget_decision_ref: str
    expected_receipt_ref: str
    revocation_ref: str
    rotation_required_ref: str
    idempotency_ref: str
    safe_refs_only: bool = True
    transient_secret_discarded: bool = True
    raw_secret_material_persisted: bool = False
    raw_secret_material_returned: bool = False
    recoverable_secret_material_available: bool = False
    secret_resolution_enabled: bool = False
    credential_validation_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    provider_invocation_enabled: bool = False
    billing_authority_granted: bool = False
    vault_presence_authorizes_validation: bool = False
    vault_presence_authorizes_invocation: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utc_timestamp)
    safe_summary: str = (
        "Credential vault backend operation recorded safe refs only; no provider validation, "
        "provider invocation, billing authority, or secret material return is enabled."
    )

    @model_validator(mode="after")
    def receipt_must_be_safe_ref_only(self) -> Any:
        payload = self.model_dump(mode="json")
        _reject_unsafe_payload(
            payload,
            "LOCAL_CREDENTIAL_VAULT_RECEIPT_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        _require_safe_refs(
            self,
            (
                "receipt_ref",
                "run_id",
                "backend_ref",
                "storage_ref",
                "record_ref",
                "secret_ref",
                "provider_ref",
                "model_ref",
                "credential_ref",
                "policy_ref",
                "approval_ref",
                "approval_scope_ref",
                "budget_decision_ref",
                "expected_receipt_ref",
                "revocation_ref",
                "rotation_required_ref",
                "idempotency_ref",
            ),
        )
        if not self.safe_refs_only or not self.transient_secret_discarded:
            raise ValueError("LOCAL_CREDENTIAL_VAULT_RECEIPT_SAFE_LEDGER_REQUIRED")
        if any(getattr(self, flag) for flag in _DENIED_AUTHORITY_FLAGS):
            raise ValueError("LOCAL_CREDENTIAL_VAULT_RECEIPT_AUTHORITY_DENIED")
        if self.allowed and self.receipt_ref != self.expected_receipt_ref:
            raise ValueError("LOCAL_CREDENTIAL_VAULT_RECEIPT_EXPECTED_REF_MISMATCH")
        return self


class LocalCredentialVaultInspectionSnapshot(_LocalCredentialVaultModel):
    snapshot_ref: str = "credential-vault-snapshot-ref:local-secret-ref-backend:v1"
    backend_ref: str = LOCAL_CREDENTIAL_VAULT_BACKEND_REF
    storage_ref: str = LOCAL_CREDENTIAL_VAULT_STORAGE_REF
    cli_inspection_ref: str = LOCAL_CREDENTIAL_VAULT_CLI_REF
    backend_kind: str = "local_secret_ref_ledger"
    posture: ProviderCredentialVaultPosture = ProviderCredentialVaultPosture.vault_not_configured
    records: list[LocalCredentialVaultRecord] = Field(default_factory=list)
    record_count: int = 0
    supports_enroll: bool = True
    supports_revoke: bool = True
    supports_rotation_required: bool = True
    safe_refs_only: bool = True
    raw_secret_material_persisted: bool = False
    raw_secret_material_returned: bool = False
    recoverable_secret_material_available: bool = False
    secret_resolution_enabled: bool = False
    credential_validation_enabled: bool = False
    provider_sdk_call_enabled: bool = False
    model_invocation_enabled: bool = False
    provider_invocation_enabled: bool = False
    billing_authority_granted: bool = False
    vault_presence_authorizes_validation: bool = False
    vault_presence_authorizes_invocation: bool = False
    blocker_codes: list[str] = Field(default_factory=lambda: sorted(_BACKEND_BLOCKER_CODES))
    safe_summary: str = (
        "Credential vault backend V1 is a local safe-ref ledger for enrolled secret refs, "
        "revocation refs, and rotation posture. It does not expose or recover secret material."
    )

    @model_validator(mode="after")
    def snapshot_must_not_grant_authority(self) -> Any:
        payload = self.model_dump(mode="json")
        _reject_unsafe_payload(
            payload,
            "LOCAL_CREDENTIAL_VAULT_SNAPSHOT_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        _require_safe_refs(self, ("snapshot_ref", "backend_ref", "storage_ref", "cli_inspection_ref"))
        if self.record_count != len(self.records):
            raise ValueError("LOCAL_CREDENTIAL_VAULT_SNAPSHOT_RECORD_COUNT_MISMATCH")
        if self.posture != _posture_from_records(self.records):
            raise ValueError("LOCAL_CREDENTIAL_VAULT_SNAPSHOT_POSTURE_MISMATCH")
        if not self.supports_enroll or not self.supports_revoke or not self.supports_rotation_required:
            raise ValueError("LOCAL_CREDENTIAL_VAULT_SNAPSHOT_OPERATION_SUPPORT_REQUIRED")
        if not self.safe_refs_only:
            raise ValueError("LOCAL_CREDENTIAL_VAULT_SNAPSHOT_SAFE_REFS_REQUIRED")
        if any(getattr(self, flag) for flag in _DENIED_AUTHORITY_FLAGS):
            raise ValueError("LOCAL_CREDENTIAL_VAULT_SNAPSHOT_AUTHORITY_DENIED")
        if not _BACKEND_BLOCKER_CODES.issubset(set(self.blocker_codes)):
            raise ValueError("LOCAL_CREDENTIAL_VAULT_SNAPSHOT_BLOCKER_CODES_REQUIRED")
        return self


class LocalCredentialVaultBackend:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.ledger_path = self.state_dir / "credential_vault_backend_v1.jsonl"

    @classmethod
    def default(cls) -> "LocalCredentialVaultBackend":
        configured = os.environ.get(UAA_CREDENTIAL_VAULT_STATE_DIR_ENV)
        state_dir = Path(configured) if configured else Path(".uaa") / "credential-vault-backend-v1"
        return cls(state_dir)

    def inspect(self) -> LocalCredentialVaultInspectionSnapshot:
        records = self._latest_records()
        return LocalCredentialVaultInspectionSnapshot(
            posture=_posture_from_records(records),
            records=records,
            record_count=len(records),
        )

    def enroll_secret(
        self,
        request: LocalCredentialVaultEnrollmentRequest,
        *,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> LocalCredentialVaultOperationReceipt:
        _require_approval(
            approval_authority,
            build_local_credential_vault_enrollment_approval_request(request),
            request.approval_ref,
        )
        existing = self._receipt_for_idempotency(
            request.idempotency_ref,
            LocalCredentialVaultOperation.enroll,
            expected_scope=_enrollment_idempotency_scope(request),
        )
        if existing is not None:
            return existing
        record_ref = _new_safe_ref("credential-vault-record-ref", request.credential_ref)
        secret_ref = _new_safe_ref("secret-ref", request.credential_ref)
        receipt_ref = request.expected_receipt_ref
        record = LocalCredentialVaultRecord(
            record_ref=record_ref,
            run_id=request.run_id,
            posture=ProviderCredentialVaultPosture.secret_ref_available,
            provider_ref=request.provider_ref,
            model_ref=request.model_ref,
            credential_ref=request.credential_ref,
            secret_ref=secret_ref,
            policy_ref=request.policy_ref,
            approval_ref=request.approval_ref,
            approval_scope_ref=request.approval_scope_ref,
            budget_decision_ref=request.budget_decision_ref,
            expected_receipt_ref=request.expected_receipt_ref,
            revocation_ref=request.revocation_ref,
            rotation_required_ref=request.rotation_required_ref,
            enrollment_receipt_ref=receipt_ref,
            last_operation_receipt_ref=receipt_ref,
        )
        receipt = self._receipt_for(
            operation=LocalCredentialVaultOperation.enroll,
            allowed=True,
            record=record,
            idempotency_ref=request.idempotency_ref,
            reason_codes=[
                "LOCAL_SECRET_REF_ENROLLED",
                "TRANSIENT_SECRET_DISCARDED",
                "SECRET_RESOLUTION_NOT_EXPOSED",
                "PROVIDER_VALIDATION_BLOCKED",
                "PROVIDER_INVOCATION_BLOCKED",
            ],
        )
        self._append(record, receipt)
        return receipt

    def revoke_secret_ref(
        self,
        request: LocalCredentialVaultRevokeRequest,
        *,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> LocalCredentialVaultOperationReceipt:
        _require_approval(
            approval_authority,
            build_local_credential_vault_revoke_approval_request(request),
            request.approval_ref,
        )
        existing = self._receipt_for_idempotency(
            request.idempotency_ref,
            LocalCredentialVaultOperation.revoke,
            expected_scope=_revoke_idempotency_scope(request),
        )
        if existing is not None:
            return existing
        record = self._require_record(request.secret_ref)
        _require_record_scope_for_request(record, request)
        revoked_record = record.model_copy(
            update={
                "posture": ProviderCredentialVaultPosture.secret_ref_revoked,
                "policy_ref": request.policy_ref,
                "approval_ref": request.approval_ref,
                "approval_scope_ref": request.approval_scope_ref,
                "expected_receipt_ref": request.expected_receipt_ref,
                "revocation_ref": request.revocation_ref,
                "last_operation_receipt_ref": request.expected_receipt_ref,
                "updated_at": _utc_timestamp(),
            }
        )
        receipt = self._receipt_for(
            operation=LocalCredentialVaultOperation.revoke,
            allowed=True,
            record=revoked_record,
            idempotency_ref=request.idempotency_ref,
            reason_codes=[
                "LOCAL_SECRET_REF_REVOKED",
                "SECRET_RESOLUTION_NOT_EXPOSED",
                "PROVIDER_VALIDATION_BLOCKED",
                "PROVIDER_INVOCATION_BLOCKED",
            ],
        )
        self._append(revoked_record, receipt)
        return receipt

    def mark_rotation_required(
        self,
        request: LocalCredentialVaultRotationRequiredRequest,
        *,
        approval_authority: LocalApprovalAuthority | None = None,
    ) -> LocalCredentialVaultOperationReceipt:
        _require_approval(
            approval_authority,
            build_local_credential_vault_rotation_approval_request(request),
            request.approval_ref,
        )
        record = self._require_record(request.secret_ref)
        _require_record_scope_for_request(record, request)
        if record.posture == ProviderCredentialVaultPosture.secret_ref_revoked:
            raise ValueError("LOCAL_CREDENTIAL_VAULT_REVOKED_REF_TERMINAL")
        existing = self._receipt_for_idempotency(
            request.idempotency_ref,
            LocalCredentialVaultOperation.mark_rotation_required,
            expected_scope=_rotation_idempotency_scope(request),
        )
        if existing is not None:
            return existing
        rotation_record = record.model_copy(
            update={
                "posture": ProviderCredentialVaultPosture.rotation_required,
                "policy_ref": request.policy_ref,
                "approval_ref": request.approval_ref,
                "approval_scope_ref": request.approval_scope_ref,
                "expected_receipt_ref": request.expected_receipt_ref,
                "rotation_required_ref": request.rotation_required_ref,
                "last_operation_receipt_ref": request.expected_receipt_ref,
                "updated_at": _utc_timestamp(),
            }
        )
        receipt = self._receipt_for(
            operation=LocalCredentialVaultOperation.mark_rotation_required,
            allowed=True,
            record=rotation_record,
            idempotency_ref=request.idempotency_ref,
            reason_codes=[
                "LOCAL_SECRET_REF_ROTATION_REQUIRED",
                "SECRET_RESOLUTION_NOT_EXPOSED",
                "PROVIDER_VALIDATION_BLOCKED",
                "PROVIDER_INVOCATION_BLOCKED",
            ],
        )
        self._append(rotation_record, receipt)
        return receipt

    def _receipt_for(
        self,
        *,
        operation: LocalCredentialVaultOperation,
        allowed: bool,
        record: LocalCredentialVaultRecord,
        idempotency_ref: str,
        reason_codes: list[str],
    ) -> LocalCredentialVaultOperationReceipt:
        return LocalCredentialVaultOperationReceipt(
            receipt_ref=record.expected_receipt_ref,
            run_id=record.run_id,
            operation=operation,
            allowed=allowed,
            posture=record.posture,
            record_ref=record.record_ref,
            secret_ref=record.secret_ref,
            provider_ref=record.provider_ref,
            model_ref=record.model_ref,
            credential_ref=record.credential_ref,
            policy_ref=record.policy_ref,
            approval_ref=record.approval_ref,
            approval_scope_ref=record.approval_scope_ref,
            budget_decision_ref=record.budget_decision_ref,
            expected_receipt_ref=record.expected_receipt_ref,
            revocation_ref=record.revocation_ref,
            rotation_required_ref=record.rotation_required_ref,
            idempotency_ref=idempotency_ref,
            reason_codes=reason_codes,
        )

    def _append(
        self,
        record: LocalCredentialVaultRecord,
        receipt: LocalCredentialVaultOperationReceipt,
    ) -> None:
        payload = {
            "record": record.model_dump(mode="json"),
            "receipt": receipt.model_dump(mode="json"),
        }
        _reject_unsafe_payload(
            payload,
            "LOCAL_CREDENTIAL_VAULT_LEDGER_PRIVATE_OR_SECRET_VALUE_REJECTED",
        )
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _latest_records(self) -> list[LocalCredentialVaultRecord]:
        latest_by_secret_ref: dict[str, LocalCredentialVaultRecord] = {}
        if not self.ledger_path.exists():
            return []
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                record = LocalCredentialVaultRecord.model_validate(payload["record"])
                latest_by_secret_ref[record.secret_ref] = record
        return sorted(latest_by_secret_ref.values(), key=lambda record: record.secret_ref)

    def _receipt_for_idempotency(
        self,
        idempotency_ref: str,
        operation: LocalCredentialVaultOperation,
        *,
        expected_scope: dict[str, str],
    ) -> LocalCredentialVaultOperationReceipt | None:
        _require_safe_ref(idempotency_ref, "idempotency_ref")
        if not self.ledger_path.exists():
            return None
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                receipt = LocalCredentialVaultOperationReceipt.model_validate(payload["receipt"])
                if receipt.idempotency_ref != idempotency_ref:
                    continue
                if receipt.operation != operation:
                    raise ValueError("LOCAL_CREDENTIAL_VAULT_IDEMPOTENCY_OPERATION_CONFLICT")
                if _receipt_idempotency_scope(receipt) != expected_scope:
                    raise ValueError("LOCAL_CREDENTIAL_VAULT_IDEMPOTENCY_SCOPE_CONFLICT")
                return receipt
        return None

    def _require_record(self, secret_ref: str) -> LocalCredentialVaultRecord:
        _require_safe_ref(secret_ref, "secret_ref")
        for record in self._latest_records():
            if record.secret_ref == secret_ref:
                return record
        raise ValueError("LOCAL_CREDENTIAL_VAULT_SECRET_REF_NOT_FOUND")
