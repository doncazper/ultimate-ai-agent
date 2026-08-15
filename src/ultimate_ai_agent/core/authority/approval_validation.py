from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import stat
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals import (
    ApprovalGrant,
    ApprovalRequest,
    ApprovalValidationDecision,
    LocalApprovalAuthority,
)
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalDecisionStatus,
    ApprovalRiskLevel,
    ApprovalStatus,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_LOCK_KEY,
    AUTHORITY_STATE_REDACTIONS,
)
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityLeaseApprovalRequirement,
    AuthorityLeaseApprovalValidator,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseReceipt,
    AuthorityLeaseStore,
    authority_state_dir,
    authority_state_lock_manager,
    build_authority_lease_approval_requirement_for_request,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_text,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now


AUTHORITY_LEASE_APPROVAL_STORE_SCHEMA_VERSION = (
    "uaa-authority-lease-approval-store.v2"
)
AUTHORITY_LEASE_APPROVAL_RECORD_SCHEMA_VERSION = (
    "uaa-authority-lease-approval-record.v2"
)
AUTHORITY_LEASE_APPROVALS_FILE = "authority_lease_approvals.json"
AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_FILE = "authority_lease_approvals.key"
AUTHORITY_LEASE_APPROVAL_RECORD_LIMIT = 512
AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_BYTES = 32


class AuthorityLeaseApprovalStateError(RuntimeError):
    """Raised when backend-owned authority approval state is not trustworthy."""


class AuthorityLeaseApprovalConflictError(RuntimeError):
    """Raised when one approval ref is rebound to different authority scope."""


class AuthorityLeaseApprovalCapacityError(RuntimeError):
    """Raised when active durable approvals exhaust the bounded store."""


class AuthorityLeaseApprovalRecord(BaseModel):
    schema_version: Literal["uaa-authority-lease-approval-record.v2"] = (
        AUTHORITY_LEASE_APPROVAL_RECORD_SCHEMA_VERSION
    )
    record_ref: str = Field(..., min_length=1)
    audit_ref: str = Field(..., min_length=1)
    approval_ref: str = Field(..., min_length=1)
    approval_scope_ref: str = Field(..., min_length=1)
    idempotency_ref: str = Field(..., min_length=1)
    requirement: AuthorityLeaseApprovalRequirement
    grant: ApprovalGrant
    backend_owned: Literal[True] = True
    caller_payload_accepted: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=360)
    record_authenticator_ref: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=utc_now)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(AUTHORITY_STATE_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_record(self) -> "AuthorityLeaseApprovalRecord":
        for value, field_name in [
            (self.record_ref, "authority_lease_approval_record_ref"),
            (self.audit_ref, "authority_lease_approval_audit_ref"),
            (self.approval_ref, "authority_lease_approval_ref"),
            (self.approval_scope_ref, "authority_lease_approval_scope_ref"),
            (self.idempotency_ref, "authority_lease_approval_idempotency_ref"),
            (
                self.record_authenticator_ref,
                "authority_lease_approval_record_authenticator_ref",
            ),
        ]:
            validate_task_ref(value, field_name)
        validate_safe_task_text(
            self.safe_summary,
            "authority_lease_approval_record_summary",
        )
        if any(
            [
                self.approval_ref != self.grant.approval_ref,
                self.approval_scope_ref != self.requirement.approval_scope_ref,
                self.grant.approval_request_id
                != self.requirement.approval_request_ref,
                self.grant.run_id != self.requirement.run_ref,
                self.grant.subject_type != ApprovalSubjectType.external_action.value,
                self.grant.subject_id != self.requirement.subject_ref,
                self.grant.granted_to_actor_id != self.requirement.operator_ref,
                self.grant.approved_actions
                != [self.requirement.requested_action],
                self.grant.approved_resource_refs
                != self.requirement.resource_refs,
                self.grant.risk_level != self.requirement.risk_level,
                self.grant.event_ref != self.requirement.approval_scope_ref,
                self.grant.trace_id != self.requirement.approval_scope_ref,
                self.created_at != self.grant.created_at,
            ]
        ):
            raise ValueError("AUTHORITY_LEASE_APPROVAL_RECORD_SCOPE_INVALID")
        if not self.record_authenticator_ref.startswith(
            "authority-lease-approval-record-authenticator-ref:hmac-sha256:"
        ):
            raise ValueError("AUTHORITY_LEASE_APPROVAL_RECORD_AUTHENTICATOR_INVALID")
        return self


def _stable_approval_ref(prefix: str, payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"{prefix}:sha256:{digest}"


def _approval_authenticator_ref(
    prefix: str,
    signing_key: bytes,
    payload: dict[str, Any],
) -> str:
    digest = hmac.new(
        signing_key,
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{prefix}:hmac-sha256:{digest}"


def _approval_record_authenticator_ref(
    signing_key: bytes,
    payload: dict[str, Any],
) -> str:
    return _approval_authenticator_ref(
        "authority-lease-approval-record-authenticator-ref",
        signing_key,
        payload,
    )


def _approval_store_authenticator_ref(
    signing_key: bytes,
    payload: dict[str, Any],
) -> str:
    return _approval_authenticator_ref(
        "authority-lease-approval-store-authenticator-ref",
        signing_key,
        payload,
    )


def _build_authority_lease_approval_record(
    requirement: AuthorityLeaseApprovalRequirement,
    grant: ApprovalGrant,
    *,
    idempotency_ref: str,
    signing_key: bytes,
) -> AuthorityLeaseApprovalRecord:
    created_at = grant.created_at
    payload: dict[str, Any] = {
        "schema_version": AUTHORITY_LEASE_APPROVAL_RECORD_SCHEMA_VERSION,
        "record_ref": _stable_approval_ref(
            "authority-lease-approval-record-ref",
            {
                "approval_ref": grant.approval_ref,
                "approval_scope_ref": requirement.approval_scope_ref,
            },
        ),
        "audit_ref": _stable_approval_ref(
            "audit-ref:authority-lease-approval",
            {
                "approval_ref": grant.approval_ref,
                "idempotency_ref": idempotency_ref,
            },
        ),
        "approval_ref": grant.approval_ref,
        "approval_scope_ref": requirement.approval_scope_ref,
        "idempotency_ref": idempotency_ref,
        "requirement": requirement.model_dump(mode="json"),
        "grant": grant.model_dump(mode="json"),
        "backend_owned": True,
        "caller_payload_accepted": False,
        "safe_summary": (
            "Backend-owned exact approval state for one AuthorityLease issue scope."
        ),
        "created_at": created_at,
        "redactions_applied": list(AUTHORITY_STATE_REDACTIONS),
    }
    record = AuthorityLeaseApprovalRecord.model_construct(
        **{
            **payload,
            "requirement": requirement,
            "grant": grant,
        },
        record_authenticator_ref=(
            "authority-lease-approval-record-authenticator-ref:hmac-sha256:pending"
        ),
    )
    payload["record_authenticator_ref"] = _approval_record_authenticator_ref(
        signing_key,
        record.model_dump(
            mode="json",
            exclude={"record_authenticator_ref"},
        ),
    )
    return AuthorityLeaseApprovalRecord.model_validate(payload)


def _approval_record_is_current(
    record: AuthorityLeaseApprovalRecord,
    *,
    now: datetime,
) -> bool:
    grant = record.grant
    return (
        grant.status == ApprovalStatus.granted.value
        and grant.revoked_at is None
        and (grant.expires_at is None or grant.expires_at > now)
    )


class AuthorityLeaseApprovalStore:
    """Durable backend-owned resolver for AuthorityLease approval refs."""

    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = state_dir or authority_state_dir()
        self.records_path = self.state_dir / AUTHORITY_LEASE_APPROVALS_FILE
        self.signing_key_path = (
            self.state_dir / AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_FILE
        )
        self.lock_manager = authority_state_lock_manager(str(self.state_dir.resolve()))

    def capture(
        self,
        requirement: AuthorityLeaseApprovalRequirement,
        *,
        idempotency_ref: str,
        approval_ref: str,
        approved_by_actor_id: str,
    ) -> ApprovalGrant:
        validate_task_ref(idempotency_ref, "authority_lease_approval_idempotency_ref")
        validate_task_ref(approval_ref, "authority_lease_approval_ref")
        validate_task_ref(
            approved_by_actor_id,
            "authority_lease_approval_actor_ref",
        )
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            generation, records = self._read_state_unlocked()
            existing_match = next(
                (
                    (index, record)
                    for index, record in enumerate(records)
                    if record.approval_ref == approval_ref
                ),
                None,
            )
            if existing_match is not None:
                existing_index, existing = existing_match
                if (
                    existing.requirement != requirement
                    or existing.idempotency_ref != idempotency_ref
                    or existing.grant.approved_by_actor_id != approved_by_actor_id
                ):
                    raise AuthorityLeaseApprovalConflictError(
                        "AUTHORITY_LEASE_APPROVAL_REF_CONFLICT"
                    )
                if _approval_record_is_current(existing, now=utc_now()):
                    return existing.grant.model_copy(deep=True)
            else:
                existing_index = None
            signing_key = self._read_signing_key_unlocked(create=True)
            authority = LocalApprovalAuthority()
            approval_request = authority.create_request(
                build_authority_lease_approval_request(requirement)
            )
            grant = authority.grant(
                approval_request.approval_request_id,
                approved_by_actor_id=approved_by_actor_id,
                approval_ref=approval_ref,
            )
            if (
                existing_index is None
                and len(records) >= AUTHORITY_LEASE_APPROVAL_RECORD_LIMIT
            ):
                records = [
                    record
                    for record in records
                    if _approval_record_is_current(record, now=utc_now())
                ]
            if (
                existing_index is None
                and len(records) >= AUTHORITY_LEASE_APPROVAL_RECORD_LIMIT
            ):
                raise AuthorityLeaseApprovalCapacityError(
                    "AUTHORITY_LEASE_APPROVAL_CAPACITY_EXHAUSTED"
                )
            replacement = _build_authority_lease_approval_record(
                requirement,
                grant,
                idempotency_ref=idempotency_ref,
                signing_key=signing_key,
            )
            if existing_index is None:
                records.append(replacement)
            else:
                records[existing_index] = replacement
            self._write_state_unlocked(
                generation + 1,
                records,
                signing_key=signing_key,
            )
            return grant.model_copy(deep=True)

    def resolve(
        self,
        approval_ref: str,
    ) -> AuthorityLeaseApprovalRecord | None:
        validate_task_ref(approval_ref, "authority_lease_approval_ref")
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            _generation, records = self._read_state_unlocked()
            record = next(
                (item for item in records if item.approval_ref == approval_ref),
                None,
            )
            return record.model_copy(deep=True) if record is not None else None

    def list_records(self) -> list[AuthorityLeaseApprovalRecord]:
        if not self.records_path.exists():
            return []
        with self.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
            _generation, records = self._read_state_unlocked()
            return [record.model_copy(deep=True) for record in records]

    def validate(
        self,
        request: AuthorityLeaseIssueRequest,
        requirement: AuthorityLeaseApprovalRequirement,
    ) -> ApprovalValidationDecision | None:
        if not requirement.approval_required or request.approval_ref is None:
            return None
        authority = LocalApprovalAuthority()
        approval_request = authority.create_request(
            build_authority_lease_approval_request(requirement)
        )
        try:
            record = self.resolve(request.approval_ref)
        except (OSError, ValueError, AuthorityLeaseApprovalStateError):
            return _approval_state_denial(
                approval_request,
                request.approval_ref,
                reason_code="APPROVAL_BACKEND_STATE_INVALID",
                safe_message=(
                    "Backend-owned approval state is unavailable or invalid."
                ),
            )
        if record is None:
            return authority.validate_for_request(
                approval_request,
                request.approval_ref,
            )
        if record.requirement != requirement:
            return _approval_state_denial(
                approval_request,
                request.approval_ref,
                reason_code="APPROVAL_BACKEND_SCOPE_MISMATCH",
                safe_message=(
                    "Backend-owned approval state does not match the exact lease scope."
                ),
                status=ApprovalDecisionStatus.out_of_scope,
            )
        authority.load_grant_for_validation(record.grant)
        return authority.validate_for_request(
            approval_request,
            request.approval_ref,
        )

    def _read_state_unlocked(
        self,
    ) -> tuple[int, list[AuthorityLeaseApprovalRecord]]:
        if not self.records_path.exists():
            return 0, []
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(
            os,
            "O_NOFOLLOW",
            0,
        )
        try:
            descriptor = os.open(self.records_path, flags)
        except OSError as exc:
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_STATE_OPEN_FAILED"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            linked_metadata = os.lstat(self.records_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (linked_metadata.st_dev, linked_metadata.st_ino)
                or stat.S_IMODE(metadata.st_mode) & 0o077
            ):
                raise AuthorityLeaseApprovalStateError(
                    "AUTHORITY_LEASE_APPROVAL_STATE_FILE_INVALID"
                )
            with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
                descriptor = -1
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            if isinstance(exc, AuthorityLeaseApprovalStateError):
                raise
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_STATE_INVALID"
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if not isinstance(payload, dict):
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_STATE_INVALID"
            )
        if set(payload) != {
            "schema_version",
            "generation",
            "records",
            "store_authenticator_ref",
        }:
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_STATE_INVALID"
            )
        if payload.get("schema_version") != AUTHORITY_LEASE_APPROVAL_STORE_SCHEMA_VERSION:
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_STATE_SCHEMA_INVALID"
            )
        generation = payload.get("generation")
        record_payloads = payload.get("records")
        store_authenticator_ref = payload.get("store_authenticator_ref")
        if (
            not isinstance(generation, int)
            or generation < 0
            or not isinstance(record_payloads, list)
            or not isinstance(store_authenticator_ref, str)
            or len(record_payloads) > AUTHORITY_LEASE_APPROVAL_RECORD_LIMIT
            or generation < len(record_payloads)
        ):
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_STATE_INVALID"
            )
        signing_key = self._read_signing_key_unlocked(create=False)
        expected_store_authenticator_ref = _approval_store_authenticator_ref(
            signing_key,
            {
                "schema_version": payload["schema_version"],
                "generation": generation,
                "records": record_payloads,
            },
        )
        if not hmac.compare_digest(
            store_authenticator_ref,
            expected_store_authenticator_ref,
        ):
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_STATE_AUTHENTICATOR_INVALID"
            )
        try:
            records = [
                AuthorityLeaseApprovalRecord.model_validate(item)
                for item in record_payloads
            ]
        except (TypeError, ValueError) as exc:
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_RECORD_INVALID"
            ) from exc
        for record in records:
            expected_record_authenticator_ref = _approval_record_authenticator_ref(
                signing_key,
                record.model_dump(
                    mode="json",
                    exclude={"record_authenticator_ref"},
                ),
            )
            if not hmac.compare_digest(
                record.record_authenticator_ref,
                expected_record_authenticator_ref,
            ):
                raise AuthorityLeaseApprovalStateError(
                    "AUTHORITY_LEASE_APPROVAL_RECORD_AUTHENTICATOR_INVALID"
                )
        refs = [record.approval_ref for record in records]
        record_refs = [record.record_ref for record in records]
        audit_refs = [record.audit_ref for record in records]
        if any(
            len(values) != len(set(values))
            for values in (refs, record_refs, audit_refs)
        ):
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_DUPLICATE_REF"
            )
        return generation, records

    def _write_state_unlocked(
        self,
        generation: int,
        records: list[AuthorityLeaseApprovalRecord],
        *,
        signing_key: bytes,
    ) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": AUTHORITY_LEASE_APPROVAL_STORE_SCHEMA_VERSION,
            "generation": generation,
            "records": [record.model_dump(mode="json") for record in records],
        }
        payload["store_authenticator_ref"] = _approval_store_authenticator_ref(
            signing_key,
            payload,
        )
        temp_path = self.records_path.with_name(
            f".{self.records_path.name}.{uuid.uuid4().hex}.tmp"
        )
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor = -1
        try:
            descriptor = os.open(temp_path, flags, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                descriptor = -1
                os.fchmod(handle.fileno(), 0o600)
                handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.records_path)
            directory_descriptor = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
        except OSError as exc:
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_STATE_WRITE_FAILED"
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

    def _read_signing_key_unlocked(self, *, create: bool) -> bytes:
        if not self.signing_key_path.exists():
            if not create:
                raise AuthorityLeaseApprovalStateError(
                    "AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_MISSING"
                )
            return self._create_signing_key_unlocked()
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(
                os,
                "O_NOFOLLOW",
                0,
            )
        )
        descriptor = -1
        try:
            descriptor = os.open(self.signing_key_path, flags)
            metadata = os.fstat(descriptor)
            linked_metadata = os.lstat(self.signing_key_path)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or (metadata.st_dev, metadata.st_ino)
                != (linked_metadata.st_dev, linked_metadata.st_ino)
                or stat.S_IMODE(metadata.st_mode) & 0o077
                or metadata.st_size != AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_BYTES
            ):
                raise AuthorityLeaseApprovalStateError(
                    "AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_INVALID"
                )
            signing_key = os.read(
                descriptor,
                AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_BYTES + 1,
            )
            closed_over = os.fstat(descriptor)
            if len(signing_key) != AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_BYTES or (
                closed_over.st_size,
                closed_over.st_mtime_ns,
                closed_over.st_ctime_ns,
            ) != (
                metadata.st_size,
                metadata.st_mtime_ns,
                metadata.st_ctime_ns,
            ):
                raise AuthorityLeaseApprovalStateError(
                    "AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_INVALID"
                )
            return signing_key
        except AuthorityLeaseApprovalStateError:
            raise
        except OSError as exc:
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_INVALID"
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def _create_signing_key_unlocked(self) -> bytes:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        signing_key = secrets.token_bytes(AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_BYTES)
        temp_path = self.signing_key_path.with_name(
            f".{self.signing_key_path.name}.{uuid.uuid4().hex}.tmp"
        )
        descriptor = -1
        try:
            descriptor = os.open(
                temp_path,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                os.fchmod(handle.fileno(), 0o600)
                handle.write(signing_key)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temp_path, self.signing_key_path)
            except FileExistsError:
                return self._read_signing_key_unlocked(create=False)
            directory_descriptor = os.open(self.state_dir, os.O_RDONLY)
            try:
                os.fsync(directory_descriptor)
            finally:
                os.close(directory_descriptor)
            return signing_key
        except AuthorityLeaseApprovalStateError:
            raise
        except OSError as exc:
            raise AuthorityLeaseApprovalStateError(
                "AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_WRITE_FAILED"
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def _approval_state_denial(
    approval_request: ApprovalRequest,
    approval_ref: str,
    *,
    reason_code: str,
    safe_message: str,
    status: ApprovalDecisionStatus = ApprovalDecisionStatus.invalid,
) -> ApprovalValidationDecision:
    return ApprovalValidationDecision(
        approval_ref=approval_ref,
        allowed=False,
        status=status,
        reason_codes=[reason_code],
        safe_message=safe_message,
        required_next_action="request_valid_local_dev_approval",
        event_ref=approval_request.event_ref,
    )


def build_authority_lease_approval_request(
    requirement: AuthorityLeaseApprovalRequirement,
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_request_id=requirement.approval_request_ref,
        run_id=requirement.run_ref,
        subject_type=ApprovalSubjectType.external_action,
        subject_id=requirement.subject_ref,
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id=requirement.operator_ref,
            authority_source=AuthoritySource.explicit_user_request,
        ),
        requested_action=requirement.requested_action,
        purpose=requirement.purpose,
        risk_level=ApprovalRiskLevel(requirement.risk_level),
        data_classification=DataClassification(
            classification=ClassificationValue.system_internal,
            source="authority_lease_approval",
            requires_redaction=True,
        ),
        resource_refs=list(requirement.resource_refs),
        event_ref=requirement.approval_scope_ref,
        trace_id=requirement.approval_scope_ref,
        expires_at=utc_now() + timedelta(hours=1),
        metadata={
            "approval_scope_ref": requirement.approval_scope_ref,
            "authority_lease_approval_required": requirement.approval_required,
        },
    )


def validate_authority_lease_approval(
    request: AuthorityLeaseIssueRequest,
    requirement: AuthorityLeaseApprovalRequirement,
) -> ApprovalValidationDecision | None:
    return AuthorityLeaseApprovalStore().validate(request, requirement)


def authority_lease_approval_validator(
    state_dir: Path,
) -> AuthorityLeaseApprovalValidator:
    approval_store = AuthorityLeaseApprovalStore(state_dir)
    return approval_store.validate


def _build_authority_lease_test_grant(
    requirement: AuthorityLeaseApprovalRequirement,
    *,
    approval_ref: str,
    approved_by_actor_id: str,
) -> ApprovalGrant:
    authority = LocalApprovalAuthority()
    approval_request = authority.create_request(
        build_authority_lease_approval_request(requirement)
    )
    return authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id=approved_by_actor_id,
        approval_ref=approval_ref,
    )


def build_authority_lease_backend_approval_ref(
    requirement: AuthorityLeaseApprovalRequirement,
    *,
    idempotency_ref: str,
) -> str:
    payload = {
        "approval_scope_ref": requirement.approval_scope_ref,
        "idempotency_ref": idempotency_ref,
        "requested_action": requirement.requested_action,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return f"approval-ref:authority-lease:{digest}"


def capture_authority_lease_backend_approval(
    store: AuthorityLeaseStore,
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
    approved_by_actor_id: str,
    approval_ref: str | None = None,
) -> tuple[AuthorityLeaseApprovalRequirement, ApprovalGrant | None]:
    requirement = build_authority_lease_approval_requirement_for_request(
        request,
        idempotency_ref=idempotency_ref,
    )
    if not requirement.approval_required:
        return requirement, None
    if request.approval_ref is not None:
        raise ValueError("AUTHORITY_LEASE_BACKEND_CAPTURE_REQUIRES_REF_FREE_REQUEST")
    resolved_ref = approval_ref or build_authority_lease_backend_approval_ref(
        requirement,
        idempotency_ref=idempotency_ref,
    )
    grant = AuthorityLeaseApprovalStore(store.state_dir).capture(
        requirement,
        idempotency_ref=idempotency_ref,
        approval_ref=resolved_ref,
        approved_by_actor_id=approved_by_actor_id,
    )
    return requirement, grant


def issue_authority_lease_from_backend_state(
    store: AuthorityLeaseStore,
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
) -> tuple[AuthorityLease | None, AuthorityLeaseReceipt]:
    return store.issue_lease(
        request,
        idempotency_ref=idempotency_ref,
        approval_validator=authority_lease_approval_validator(store.state_dir),
    )


def issue_authority_lease_with_backend_approval(
    store: AuthorityLeaseStore,
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
    approved_by_actor_id: str,
    approval_ref: str | None = None,
) -> tuple[
    AuthorityLeaseApprovalRequirement,
    ApprovalGrant | None,
    AuthorityLease | None,
    AuthorityLeaseReceipt,
]:
    with store.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY):
        try:
            requirement, grant = capture_authority_lease_backend_approval(
                store,
                request,
                idempotency_ref=idempotency_ref,
                approved_by_actor_id=approved_by_actor_id,
                approval_ref=approval_ref,
            )
        except (
            AuthorityLeaseApprovalCapacityError,
            AuthorityLeaseApprovalStateError,
        ) as exc:
            requirement = build_authority_lease_approval_requirement_for_request(
                request,
                idempotency_ref=idempotency_ref,
            )
            failed_approval_ref = (
                approval_ref
                or build_authority_lease_backend_approval_ref(
                    requirement,
                    idempotency_ref=idempotency_ref,
                )
            )
            approval_request = build_authority_lease_approval_request(requirement)
            reason_code = (
                "APPROVAL_BACKEND_CAPACITY_EXHAUSTED"
                if isinstance(exc, AuthorityLeaseApprovalCapacityError)
                else "APPROVAL_BACKEND_STATE_INVALID"
            )
            decision = _approval_state_denial(
                approval_request,
                failed_approval_ref,
                reason_code=reason_code,
                safe_message=(
                    "Backend-owned approval state could not safely capture "
                    "the exact lease approval."
                ),
            )
            failed_request = request.model_copy(
                update={"approval_ref": failed_approval_ref}
            )
            lease, receipt = store.issue_lease(
                failed_request,
                idempotency_ref=idempotency_ref,
                approval_validator=lambda _request, _requirement: decision,
            )
            return requirement, None, lease, receipt
        approved_request = (
            request.model_copy(update={"approval_ref": grant.approval_ref})
            if grant is not None
            else request
        )
        lease, receipt = issue_authority_lease_from_backend_state(
            store,
            approved_request,
            idempotency_ref=idempotency_ref,
        )
        return requirement, grant, lease, receipt


def build_authority_lease_test_grant(
    requirement: AuthorityLeaseApprovalRequirement,
    *,
    approval_ref: str,
    approved_by_actor_id: str = "operator-ref:test-approver",
) -> ApprovalGrant:
    return _build_authority_lease_test_grant(
        requirement,
        approval_ref=approval_ref,
        approved_by_actor_id=approved_by_actor_id,
    )


def issue_authority_lease_with_test_approval(
    store: AuthorityLeaseStore,
    request: AuthorityLeaseIssueRequest,
    *,
    idempotency_ref: str,
    approval_ref: str | None = None,
) -> tuple[AuthorityLease | None, AuthorityLeaseReceipt]:
    _requirement, _grant, lease, receipt = issue_authority_lease_with_backend_approval(
        store,
        request,
        idempotency_ref=idempotency_ref,
        approved_by_actor_id="operator-ref:test-approver",
        approval_ref=(
            approval_ref
            or f"approval-ref:test-authority-lease:{idempotency_ref.rsplit(':', 1)[-1]}"
        ),
    )
    return lease, receipt
