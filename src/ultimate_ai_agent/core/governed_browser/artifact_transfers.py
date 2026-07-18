"""Inactive governed download quarantine and artifact-bound upload plans.

The only implemented download effect is a bounded write into an app-owned
quarantine during injected local validation. Uploads are plan-only and may
refer only to an exact fingerprinted artifact already in that quarantine.
No browser, network, upload body, external target, or ordinary user path is
opened by this module.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now

from .contracts import (
    ExternalActionDispatchOutcome,
    ExternalActionDispatchResult,
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    stable_governed_browser_ref,
)
from .transaction import GovernedExternalActionKernel


MAX_GOVERNED_ARTIFACT_BYTES = 65_536
MAX_GOVERNED_ARTIFACT_RECIPE_LIFETIME = timedelta(minutes=10)
_HASH_PINNED_SUFFIX_RE = re.compile(r"sha256:[0-9a-f]{64}")


class GovernedArtifactTransferOperation(str, Enum):
    download_quarantine = "download_quarantine"
    upload_quarantined_artifact_plan = "upload_quarantined_artifact_plan"


class GovernedArtifactMediaType(str, Enum):
    text_plain = "text/plain"
    image_png = "image/png"
    image_jpeg = "image/jpeg"


class GovernedArtifactTransferStatus(str, Enum):
    quarantined = "quarantined"
    upload_plan_ready = "upload_plan_ready"
    preflight_blocked = "preflight_blocked"
    transaction_blocked = "transaction_blocked"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"
    replayed_content_free = "replayed_content_free"


class GovernedArtifactQuarantineError(RuntimeError):
    """Quarantine storage failed before a trustworthy terminal result."""


class GovernedArtifactPayloadRejected(ValueError):
    """The transient artifact failed bounded pre-write validation."""


class GovernedArtifactQuarantinePrecondition(ValueError):
    """An existing quarantined artifact is absent, unsafe, or drifted."""


def _validate_hash_pinned_ref(
    value: str,
    *,
    label: str,
    prefix: str,
) -> None:
    validate_task_ref(value, label)
    if not value.startswith(prefix):
        raise ValueError(f"GOVERNED_ARTIFACT_{label.upper()}_REQUIRED")
    if _HASH_PINNED_SUFFIX_RE.fullmatch(value.removeprefix(prefix)) is None:
        raise ValueError("GOVERNED_ARTIFACT_HASH_PIN_REQUIRED")


def governed_artifact_ref(
    *,
    source_ref: str,
    declared_media_type: GovernedArtifactMediaType,
) -> str:
    validate_task_ref(source_ref, "source_ref")
    return stable_governed_browser_ref(
        "artifact-ref:governed-browser",
        {
            "source_ref": source_ref,
            "declared_media_type": GovernedArtifactMediaType(declared_media_type).value,
        },
    )


def governed_artifact_quarantine_ref(
    *,
    origin_ref: str,
    artifact_ref: str,
    download_transaction_ref: str,
) -> str:
    for value, label in (
        (origin_ref, "origin_ref"),
        (artifact_ref, "artifact_ref"),
        (download_transaction_ref, "download_transaction_ref"),
    ):
        validate_task_ref(value, label)
    _validate_hash_pinned_ref(
        artifact_ref,
        label="artifact_ref",
        prefix="artifact-ref:governed-browser:",
    )
    return stable_governed_browser_ref(
        "artifact-quarantine-ref:governed-browser",
        {
            "origin_ref": origin_ref,
            "artifact_ref": artifact_ref,
            "download_transaction_ref": download_transaction_ref,
        },
    )


def governed_artifact_transfer_schema_ref(
    *,
    operation: GovernedArtifactTransferOperation,
    artifact_ref: str,
    quarantine_ref: str,
    download_transaction_ref: str,
    declared_media_type: GovernedArtifactMediaType,
    max_bytes: int,
    content_fingerprint_ref: str | None,
    source_download_receipt_ref: str | None = None,
    source_download_recipe_ref: str | None = None,
) -> str:
    exact_operation = GovernedArtifactTransferOperation(operation)
    exact_media_type = GovernedArtifactMediaType(declared_media_type)
    _validate_hash_pinned_ref(
        artifact_ref,
        label="artifact_ref",
        prefix="artifact-ref:governed-browser:",
    )
    _validate_hash_pinned_ref(
        quarantine_ref,
        label="quarantine_ref",
        prefix="artifact-quarantine-ref:governed-browser:",
    )
    validate_task_ref(download_transaction_ref, "download_transaction_ref")
    if not 1 <= max_bytes <= MAX_GOVERNED_ARTIFACT_BYTES:
        raise ValueError("GOVERNED_ARTIFACT_SIZE_LIMIT_INVALID")
    if content_fingerprint_ref is not None:
        _validate_hash_pinned_ref(
            content_fingerprint_ref,
            label="content_fingerprint_ref",
            prefix="content-fingerprint-ref:governed-browser:",
        )
    if source_download_receipt_ref is not None:
        _validate_hash_pinned_ref(
            source_download_receipt_ref,
            label="source_download_receipt_ref",
            prefix="receipt-ref:governed-external-action:",
        )
    if source_download_recipe_ref is not None:
        _validate_hash_pinned_ref(
            source_download_recipe_ref,
            label="source_download_recipe_ref",
            prefix="artifact-transfer-recipe-ref:governed-browser:",
        )
    if (
        exact_operation
        == GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
    ) != (
        content_fingerprint_ref is not None
        and source_download_receipt_ref is not None
        and source_download_recipe_ref is not None
    ):
        raise ValueError("GOVERNED_ARTIFACT_FINGERPRINT_SCOPE_MISMATCH")
    return stable_governed_browser_ref(
        "artifact-transfer-schema-ref:governed-browser",
        {
            "operation": exact_operation.value,
            "artifact_ref": artifact_ref,
            "quarantine_ref": quarantine_ref,
            "download_transaction_ref": download_transaction_ref,
            "declared_media_type": exact_media_type.value,
            "max_bytes": max_bytes,
            "content_fingerprint_ref": content_fingerprint_ref,
            "source_download_receipt_ref": source_download_receipt_ref,
            "source_download_recipe_ref": source_download_recipe_ref,
        },
    )


def governed_artifact_transfer_operation_authority_ref(
    *,
    operation: GovernedArtifactTransferOperation,
    origin_ref: str,
    artifact_ref: str,
    quarantine_ref: str,
) -> str:
    for value, label in (
        (origin_ref, "origin_ref"),
        (artifact_ref, "artifact_ref"),
        (quarantine_ref, "quarantine_ref"),
    ):
        validate_task_ref(value, label)
    return stable_governed_browser_ref(
        "artifact-transfer-operation-authority-ref:governed-browser",
        {
            "operation": GovernedArtifactTransferOperation(operation).value,
            "origin_ref": origin_ref,
            "artifact_ref": artifact_ref,
            "quarantine_ref": quarantine_ref,
        },
    )


def _required_capability(
    operation: GovernedArtifactTransferOperation,
) -> AuthorityCapability:
    return {
        GovernedArtifactTransferOperation.download_quarantine: (
            AuthorityCapability.download
        ),
        GovernedArtifactTransferOperation.upload_quarantined_artifact_plan: (
            AuthorityCapability.upload
        ),
    }[GovernedArtifactTransferOperation(operation)]


@dataclass(frozen=True)
class GovernedArtifactInspection:
    declared_media_type: GovernedArtifactMediaType
    byte_count: int
    content_fingerprint_ref: str


class GovernedArtifactQuarantineStore:
    """Purpose-specific app-owned storage; paths never cross the boundary."""

    def __init__(self, root: Path) -> None:
        if not root.is_absolute() or root == Path(root.anchor):
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_ROOT_UNSAFE")
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        root_info = os.lstat(root)
        if (
            not stat.S_ISDIR(root_info.st_mode)
            or stat.S_ISLNK(root_info.st_mode)
            or root_info.st_uid != os.geteuid()
            or root_info.st_mode & 0o077
        ):
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_ROOT_UNSAFE")
        quarantine = root / "artifact-quarantine"
        quarantine.mkdir(mode=0o700, exist_ok=True)
        quarantine_info = os.lstat(quarantine)
        if (
            not stat.S_ISDIR(quarantine_info.st_mode)
            or stat.S_ISLNK(quarantine_info.st_mode)
            or quarantine_info.st_uid != os.geteuid()
            or quarantine_info.st_mode & 0o077
        ):
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_ROOT_UNSAFE")
        self._root = root
        self._quarantine = quarantine
        self._root_identity = (root_info.st_dev, root_info.st_ino)
        self._quarantine_identity = (
            quarantine_info.st_dev,
            quarantine_info.st_ino,
        )
        self.binding_ref = stable_governed_browser_ref(
            "artifact-quarantine-store-ref:governed-browser",
            {
                "root_identity": self._root_identity,
                "quarantine_identity": self._quarantine_identity,
            },
        )

    @staticmethod
    def _filename(quarantine_ref: str) -> str:
        validate_task_ref(quarantine_ref, "quarantine_ref")
        return f"{hashlib.sha256(quarantine_ref.encode()).hexdigest()}.quarantine"

    def _verify_directories(self) -> None:
        try:
            root_info = os.lstat(self._root)
            quarantine_info = os.lstat(self._quarantine)
        except OSError as exc:
            raise GovernedArtifactQuarantineError(
                "GOVERNED_ARTIFACT_QUARANTINE_SUBSTITUTION_DENIED"
            ) from exc
        if (
            not stat.S_ISDIR(root_info.st_mode)
            or stat.S_ISLNK(root_info.st_mode)
            or root_info.st_uid != os.geteuid()
            or root_info.st_mode & 0o077
            or (root_info.st_dev, root_info.st_ino) != self._root_identity
            or not stat.S_ISDIR(quarantine_info.st_mode)
            or stat.S_ISLNK(quarantine_info.st_mode)
            or quarantine_info.st_uid != os.geteuid()
            or quarantine_info.st_mode & 0o077
            or (quarantine_info.st_dev, quarantine_info.st_ino)
            != self._quarantine_identity
        ):
            raise GovernedArtifactQuarantineError(
                "GOVERNED_ARTIFACT_QUARANTINE_SUBSTITUTION_DENIED"
            )

    def _open_quarantine_directory(self) -> int:
        self._verify_directories()
        try:
            descriptor = os.open(
                self._quarantine,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
        except OSError as exc:
            raise GovernedArtifactQuarantineError(
                "GOVERNED_ARTIFACT_QUARANTINE_SUBSTITUTION_DENIED"
            ) from exc
        info = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o077
            or (info.st_dev, info.st_ino) != self._quarantine_identity
        ):
            os.close(descriptor)
            raise GovernedArtifactQuarantineError(
                "GOVERNED_ARTIFACT_QUARANTINE_SUBSTITUTION_DENIED"
            )
        return descriptor

    @staticmethod
    def validate_payload(
        *,
        payload: bytes | bytearray,
        declared_media_type: GovernedArtifactMediaType,
        max_bytes: int,
    ) -> GovernedArtifactInspection:
        exact_media_type = GovernedArtifactMediaType(declared_media_type)
        if not 1 <= max_bytes <= MAX_GOVERNED_ARTIFACT_BYTES:
            raise GovernedArtifactPayloadRejected(
                "GOVERNED_ARTIFACT_SIZE_LIMIT_INVALID"
            )
        if not payload:
            raise GovernedArtifactPayloadRejected("GOVERNED_ARTIFACT_EMPTY_DENIED")
        if len(payload) > max_bytes:
            raise GovernedArtifactPayloadRejected(
                "GOVERNED_ARTIFACT_SIZE_LIMIT_EXCEEDED"
            )
        if exact_media_type == GovernedArtifactMediaType.text_plain:
            if b"\x00" in payload or b"<script" in payload.lower():
                raise GovernedArtifactPayloadRejected(
                    "GOVERNED_ARTIFACT_CONTENT_TYPE_MISMATCH"
                )
            try:
                payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise GovernedArtifactPayloadRejected(
                    "GOVERNED_ARTIFACT_CONTENT_TYPE_MISMATCH"
                ) from exc
        elif exact_media_type == GovernedArtifactMediaType.image_png:
            if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
                raise GovernedArtifactPayloadRejected(
                    "GOVERNED_ARTIFACT_CONTENT_TYPE_MISMATCH"
                )
        elif exact_media_type == GovernedArtifactMediaType.image_jpeg:
            if not payload.startswith(b"\xff\xd8\xff"):
                raise GovernedArtifactPayloadRejected(
                    "GOVERNED_ARTIFACT_CONTENT_TYPE_MISMATCH"
                )
        return GovernedArtifactInspection(
            declared_media_type=exact_media_type,
            byte_count=len(payload),
            content_fingerprint_ref=stable_governed_browser_ref(
                "content-fingerprint-ref:governed-browser",
                {
                    "declared_media_type": exact_media_type.value,
                    "byte_count": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                },
            ),
        )

    def quarantine(
        self,
        *,
        quarantine_ref: str,
        payload: bytes | bytearray,
        declared_media_type: GovernedArtifactMediaType,
        max_bytes: int,
    ) -> GovernedArtifactInspection:
        _validate_hash_pinned_ref(
            quarantine_ref,
            label="quarantine_ref",
            prefix="artifact-quarantine-ref:governed-browser:",
        )
        payload_snapshot = bytes(payload)
        inspection = self.validate_payload(
            payload=payload_snapshot,
            declared_media_type=declared_media_type,
            max_bytes=max_bytes,
        )
        directory_fd = self._open_quarantine_directory()
        filename = self._filename(quarantine_ref)
        descriptor: int | None = None
        created = False
        try:
            try:
                descriptor = os.open(
                    filename,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=directory_fd,
                )
                created = True
                _write_all(descriptor, payload_snapshot)
                os.fsync(descriptor)
                info = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_nlink != 1
                    or info.st_uid != os.geteuid()
                    or info.st_mode & 0o077
                    or info.st_size != len(payload_snapshot)
                ):
                    raise OSError("unsafe quarantine file")
                os.fsync(directory_fd)
            except OSError as exc:
                if created:
                    try:
                        os.unlink(filename, dir_fd=directory_fd)
                        os.fsync(directory_fd)
                    except OSError:
                        pass
                raise GovernedArtifactQuarantineError(
                    "GOVERNED_ARTIFACT_QUARANTINE_WRITE_UNCERTAIN"
                ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(directory_fd)
        return inspection

    def inspect(
        self,
        *,
        quarantine_ref: str,
        declared_media_type: GovernedArtifactMediaType,
        max_bytes: int,
        expected_content_fingerprint_ref: str,
    ) -> GovernedArtifactInspection:
        _validate_hash_pinned_ref(
            quarantine_ref,
            label="quarantine_ref",
            prefix="artifact-quarantine-ref:governed-browser:",
        )
        _validate_hash_pinned_ref(
            expected_content_fingerprint_ref,
            label="content_fingerprint_ref",
            prefix="content-fingerprint-ref:governed-browser:",
        )
        directory_fd = self._open_quarantine_directory()
        filename = self._filename(quarantine_ref)
        try:
            try:
                descriptor = os.open(
                    filename,
                    os.O_RDONLY
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=directory_fd,
                )
            except OSError as exc:
                raise GovernedArtifactQuarantinePrecondition(
                    "GOVERNED_ARTIFACT_QUARANTINE_REQUIRED"
                ) from exc
            try:
                info = os.fstat(descriptor)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_nlink != 1
                    or info.st_uid != os.geteuid()
                    or info.st_mode & 0o077
                    or info.st_size > max_bytes
                ):
                    raise GovernedArtifactQuarantinePrecondition(
                        "GOVERNED_ARTIFACT_QUARANTINE_INVALID"
                    )
                payload = _read_bounded(descriptor, max_bytes=max_bytes)
            finally:
                os.close(descriptor)
        finally:
            os.close(directory_fd)
        try:
            inspection = self.validate_payload(
                payload=payload,
                declared_media_type=declared_media_type,
                max_bytes=max_bytes,
            )
        except GovernedArtifactPayloadRejected as exc:
            raise GovernedArtifactQuarantinePrecondition(
                "GOVERNED_ARTIFACT_QUARANTINE_INVALID"
            ) from exc
        if inspection.content_fingerprint_ref != expected_content_fingerprint_ref:
            raise GovernedArtifactQuarantinePrecondition(
                "GOVERNED_ARTIFACT_FINGERPRINT_MISMATCH"
            )
        return inspection


def _write_all(descriptor: int, payload: bytes | bytearray) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("short quarantine write")
        view = view[written:]


def _read_bounded(descriptor: int, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    remaining = max_bytes + 1
    while remaining > 0:
        chunk = os.read(descriptor, min(8192, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    payload = b"".join(chunks)
    if len(payload) > max_bytes:
        raise GovernedArtifactQuarantinePrecondition(
            "GOVERNED_ARTIFACT_SIZE_LIMIT_EXCEEDED"
        )
    return payload


class GovernedArtifactTransferRecipe(BaseModel):
    """One immutable exact quarantine or upload-plan operation."""

    schema_version: Literal["uaa-governed-artifact-transfer-recipe.v1"] = (
        "uaa-governed-artifact-transfer-recipe.v1"
    )
    recipe_ref: str = Field(..., max_length=240)
    operation: GovernedArtifactTransferOperation
    operation_authority_ref: str = Field(..., max_length=240)
    binding_ref: str = Field(..., max_length=240)
    transaction_ref: str = Field(..., max_length=240)
    origin_ref: str = Field(..., max_length=240)
    page_snapshot_ref: str = Field(..., max_length=240)
    artifact_ref: str = Field(..., max_length=240)
    quarantine_ref: str = Field(..., max_length=240)
    download_transaction_ref: str = Field(..., max_length=240)
    quarantine_store_ref: str = Field(..., max_length=240)
    transfer_schema_ref: str = Field(..., max_length=240)
    transfer_surface_ref: str = Field(..., max_length=240)
    visibility_proof_ref: str = Field(..., max_length=240)
    declared_media_type: GovernedArtifactMediaType
    content_fingerprint_ref: str | None = Field(default=None, max_length=240)
    source_download_receipt_ref: str | None = Field(default=None, max_length=240)
    source_download_recipe_ref: str | None = Field(default=None, max_length=240)
    max_bytes: int = Field(ge=1, le=MAX_GOVERNED_ARTIFACT_BYTES)
    created_at: datetime
    expires_at: datetime
    exact_capability: AuthorityCapability
    registered_recipe_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    approval_revalidation_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    readiness_revalidation_required: Literal[True] = True
    human_presence_required: Literal[True] = True
    app_owned_quarantine_required: Literal[True] = True
    content_fingerprint_required_for_upload: Literal[True] = True
    quarantine_before_upload_required: Literal[True] = True
    live_download_allowed: Literal[False] = False
    live_upload_allowed: Literal[False] = False
    upload_body_materialization_allowed: Literal[False] = False
    browser_session_allowed: Literal[False] = False
    authentication_allowed: Literal[False] = False
    cookies_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    external_mutation_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_recipe(self) -> "GovernedArtifactTransferRecipe":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.operation_authority_ref, "operation_authority_ref"),
            (self.binding_ref, "binding_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.artifact_ref, "artifact_ref"),
            (self.quarantine_ref, "quarantine_ref"),
            (self.download_transaction_ref, "download_transaction_ref"),
            (self.quarantine_store_ref, "quarantine_store_ref"),
            (self.transfer_schema_ref, "transfer_schema_ref"),
            (self.transfer_surface_ref, "transfer_surface_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
            (self.content_fingerprint_ref, "content_fingerprint_ref"),
            (self.source_download_receipt_ref, "source_download_receipt_ref"),
            (self.source_download_recipe_ref, "source_download_recipe_ref"),
        ):
            if value is not None:
                validate_task_ref(value, label)
        operation = GovernedArtifactTransferOperation(self.operation)
        media_type = GovernedArtifactMediaType(self.declared_media_type)
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_ARTIFACT_TIMEZONE_REQUIRED")
        if (
            self.expires_at <= self.created_at
            or self.expires_at - self.created_at > MAX_GOVERNED_ARTIFACT_RECIPE_LIFETIME
        ):
            raise ValueError("GOVERNED_ARTIFACT_RECIPE_LIFETIME_INVALID")
        if self.exact_capability != _required_capability(operation).value:
            raise ValueError("GOVERNED_ARTIFACT_EXACT_CAPABILITY_MISMATCH")
        expected_quarantine_ref = governed_artifact_quarantine_ref(
            origin_ref=self.origin_ref,
            artifact_ref=self.artifact_ref,
            download_transaction_ref=self.download_transaction_ref,
        )
        if self.quarantine_ref != expected_quarantine_ref:
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_SCOPE_MISMATCH")
        if (
            operation == GovernedArtifactTransferOperation.download_quarantine
            and self.download_transaction_ref != self.transaction_ref
        ):
            raise ValueError("GOVERNED_ARTIFACT_DOWNLOAD_TRANSACTION_MISMATCH")
        if (
            operation
            == GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
            and self.download_transaction_ref == self.transaction_ref
        ):
            raise ValueError("GOVERNED_ARTIFACT_SOURCE_TRANSACTION_MUST_BE_DISTINCT")
        expected_schema_ref = governed_artifact_transfer_schema_ref(
            operation=operation,
            artifact_ref=self.artifact_ref,
            quarantine_ref=self.quarantine_ref,
            download_transaction_ref=self.download_transaction_ref,
            declared_media_type=media_type,
            max_bytes=self.max_bytes,
            content_fingerprint_ref=self.content_fingerprint_ref,
            source_download_receipt_ref=self.source_download_receipt_ref,
            source_download_recipe_ref=self.source_download_recipe_ref,
        )
        if self.transfer_schema_ref != expected_schema_ref:
            raise ValueError("GOVERNED_ARTIFACT_TRANSFER_SCHEMA_REF_MISMATCH")
        expected_authority_ref = governed_artifact_transfer_operation_authority_ref(
            operation=operation,
            origin_ref=self.origin_ref,
            artifact_ref=self.artifact_ref,
            quarantine_ref=self.quarantine_ref,
        )
        if self.operation_authority_ref != expected_authority_ref:
            raise ValueError("GOVERNED_ARTIFACT_OPERATION_AUTHORITY_REF_MISMATCH")
        _validate_hash_pinned_ref(
            self.transfer_surface_ref,
            label="transfer_surface_ref",
            prefix="artifact-transfer-surface-ref:governed-browser:",
        )
        _validate_hash_pinned_ref(
            self.visibility_proof_ref,
            label="visibility_proof_ref",
            prefix="visibility-proof-ref:governed-browser:",
        )
        expected_recipe_ref = stable_governed_browser_ref(
            "artifact-transfer-recipe-ref:governed-browser",
            self.model_dump(mode="json", exclude={"recipe_ref"}),
        )
        if self.recipe_ref != expected_recipe_ref:
            raise ValueError("GOVERNED_ARTIFACT_RECIPE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_allowed"}),
            "governed_artifact_transfer_recipe",
        )
        return self


def build_governed_artifact_transfer_recipe(
    request: ExternalActionExecutionRequest,
    *,
    operation: GovernedArtifactTransferOperation,
    artifact_ref: str,
    quarantine_ref: str,
    download_transaction_ref: str,
    quarantine_store_ref: str,
    transfer_surface_ref: str,
    visibility_proof_ref: str,
    declared_media_type: GovernedArtifactMediaType,
    max_bytes: int,
    content_fingerprint_ref: str | None,
    created_at: datetime,
    expires_at: datetime,
    source_download_receipt_ref: str | None = None,
    source_download_recipe_ref: str | None = None,
) -> GovernedArtifactTransferRecipe:
    execution = ExternalActionExecutionRequest.model_validate(
        request.model_dump(mode="json")
    )
    binding = execution.binding
    exact_operation = GovernedArtifactTransferOperation(operation)
    exact_media_type = GovernedArtifactMediaType(declared_media_type)
    required_capability = _required_capability(exact_operation)
    if binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_ARTIFACT_REAL_TARGETS_INACTIVE")
    if binding.authority_capability != required_capability.value:
        raise ValueError("GOVERNED_ARTIFACT_EXACT_CAPABILITY_MISMATCH")
    if not binding.human_present:
        raise ValueError("GOVERNED_ARTIFACT_HUMAN_PRESENCE_REQUIRED")
    if created_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("GOVERNED_ARTIFACT_TIMEZONE_REQUIRED")
    if created_at > binding.start_deadline or expires_at > binding.start_deadline:
        raise ValueError("GOVERNED_ARTIFACT_DEADLINE_EXCEEDED")
    if binding.artifact_refs != [artifact_ref]:
        raise ValueError("GOVERNED_ARTIFACT_EXACT_ARTIFACT_SCOPE_REQUIRED")
    expected_quarantine_ref = governed_artifact_quarantine_ref(
        origin_ref=binding.origin_ref,
        artifact_ref=artifact_ref,
        download_transaction_ref=download_transaction_ref,
    )
    if quarantine_ref != expected_quarantine_ref:
        raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_SCOPE_MISMATCH")
    if (
        exact_operation == GovernedArtifactTransferOperation.download_quarantine
        and download_transaction_ref != binding.transaction_ref
    ):
        raise ValueError("GOVERNED_ARTIFACT_DOWNLOAD_TRANSACTION_MISMATCH")
    if (
        exact_operation
        == GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
        and download_transaction_ref == binding.transaction_ref
    ):
        raise ValueError("GOVERNED_ARTIFACT_SOURCE_TRANSACTION_MUST_BE_DISTINCT")
    operation_authority_ref = governed_artifact_transfer_operation_authority_ref(
        operation=exact_operation,
        origin_ref=binding.origin_ref,
        artifact_ref=artifact_ref,
        quarantine_ref=quarantine_ref,
    )
    schema_ref = governed_artifact_transfer_schema_ref(
        operation=exact_operation,
        artifact_ref=artifact_ref,
        quarantine_ref=quarantine_ref,
        download_transaction_ref=download_transaction_ref,
        declared_media_type=exact_media_type,
        max_bytes=max_bytes,
        content_fingerprint_ref=content_fingerprint_ref,
        source_download_receipt_ref=source_download_receipt_ref,
        source_download_recipe_ref=source_download_recipe_ref,
    )
    if binding.field_schema_ref != schema_ref:
        raise ValueError("GOVERNED_ARTIFACT_SCHEMA_NOT_AUTHORITY_BOUND")
    bound_operation_refs = tuple(
        ref
        for ref in binding.resource_refs
        if ref.startswith("artifact-transfer-operation-authority-ref:governed-browser:")
    )
    if bound_operation_refs != (operation_authority_ref,):
        raise ValueError("GOVERNED_ARTIFACT_OPERATION_AUTHORITY_MISMATCH")
    required_resources = {
        operation_authority_ref,
        quarantine_ref,
        download_transaction_ref,
        quarantine_store_ref,
        transfer_surface_ref,
        visibility_proof_ref,
    }
    if content_fingerprint_ref is not None:
        required_resources.add(content_fingerprint_ref)
    if source_download_receipt_ref is not None:
        required_resources.add(source_download_receipt_ref)
    if source_download_recipe_ref is not None:
        required_resources.add(source_download_recipe_ref)
    if not required_resources.issubset(set(binding.exact_resource_refs())):
        raise ValueError("GOVERNED_ARTIFACT_RESOURCE_NOT_AUTHORITY_BOUND")
    payload = {
        "operation": exact_operation,
        "operation_authority_ref": operation_authority_ref,
        "binding_ref": binding.binding_ref,
        "transaction_ref": binding.transaction_ref,
        "origin_ref": binding.origin_ref,
        "page_snapshot_ref": binding.page_snapshot_ref,
        "artifact_ref": artifact_ref,
        "quarantine_ref": quarantine_ref,
        "download_transaction_ref": download_transaction_ref,
        "quarantine_store_ref": quarantine_store_ref,
        "transfer_schema_ref": schema_ref,
        "transfer_surface_ref": transfer_surface_ref,
        "visibility_proof_ref": visibility_proof_ref,
        "declared_media_type": exact_media_type,
        "content_fingerprint_ref": content_fingerprint_ref,
        "source_download_receipt_ref": source_download_receipt_ref,
        "source_download_recipe_ref": source_download_recipe_ref,
        "max_bytes": max_bytes,
        "created_at": created_at,
        "expires_at": expires_at,
        "exact_capability": required_capability,
    }
    provisional = GovernedArtifactTransferRecipe.model_construct(
        recipe_ref="artifact-transfer-recipe-ref:governed-browser:pending",
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "artifact-transfer-recipe-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    return GovernedArtifactTransferRecipe(recipe_ref=recipe_ref, **payload)


class GovernedArtifactTransferRecipeRegistry:
    def __init__(self, recipes: Sequence[GovernedArtifactTransferRecipe]) -> None:
        validated = tuple(
            GovernedArtifactTransferRecipe.model_validate(
                recipe.model_dump(mode="json")
            )
            for recipe in recipes
        )
        if not validated:
            raise ValueError("GOVERNED_ARTIFACT_RECIPE_REGISTRY_EMPTY")
        if len(validated) > 128:
            raise ValueError("GOVERNED_ARTIFACT_RECIPE_REGISTRY_TOO_LARGE")
        self._recipes = {recipe.recipe_ref: recipe for recipe in validated}
        if len(self._recipes) != len(validated):
            raise ValueError("GOVERNED_ARTIFACT_RECIPE_REF_DUPLICATE")
        operation_scopes = {
            (recipe.operation, recipe.operation_authority_ref) for recipe in validated
        }
        if len(operation_scopes) != len(validated):
            raise ValueError("GOVERNED_ARTIFACT_OPERATION_SCOPE_DUPLICATE")

    def resolve(self, recipe_ref: str) -> GovernedArtifactTransferRecipe | None:
        return self._recipes.get(recipe_ref)


class ExactGovernedArtifactTransferRequest(BaseModel):
    execution_request: ExternalActionExecutionRequest
    recipe_ref: str
    operation: GovernedArtifactTransferOperation
    artifact_ref: str
    quarantine_ref: str
    download_transaction_ref: str

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_request(self) -> "ExactGovernedArtifactTransferRequest":
        validate_task_ref(self.recipe_ref, "recipe_ref")
        _validate_hash_pinned_ref(
            self.artifact_ref,
            label="artifact_ref",
            prefix="artifact-ref:governed-browser:",
        )
        _validate_hash_pinned_ref(
            self.quarantine_ref,
            label="quarantine_ref",
            prefix="artifact-quarantine-ref:governed-browser:",
        )
        validate_task_ref(
            self.download_transaction_ref,
            "download_transaction_ref",
        )
        binding = self.execution_request.binding
        operation = GovernedArtifactTransferOperation(self.operation)
        if binding.authority_capability != _required_capability(operation).value:
            raise ValueError("GOVERNED_ARTIFACT_EXACT_CAPABILITY_MISMATCH")
        if binding.artifact_refs != [self.artifact_ref]:
            raise ValueError("GOVERNED_ARTIFACT_EXACT_ARTIFACT_SCOPE_REQUIRED")
        expected_quarantine_ref = governed_artifact_quarantine_ref(
            origin_ref=binding.origin_ref,
            artifact_ref=self.artifact_ref,
            download_transaction_ref=self.download_transaction_ref,
        )
        if self.quarantine_ref != expected_quarantine_ref:
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_SCOPE_MISMATCH")
        if (
            operation == GovernedArtifactTransferOperation.download_quarantine
            and self.download_transaction_ref != binding.transaction_ref
        ):
            raise ValueError("GOVERNED_ARTIFACT_DOWNLOAD_TRANSACTION_MISMATCH")
        if (
            operation
            == GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
            and self.download_transaction_ref == binding.transaction_ref
        ):
            raise ValueError("GOVERNED_ARTIFACT_SOURCE_TRANSACTION_MUST_BE_DISTINCT")
        required_refs = {
            self.artifact_ref,
            self.quarantine_ref,
            self.download_transaction_ref,
        }
        if not required_refs.issubset(set(binding.exact_resource_refs())):
            raise ValueError("GOVERNED_ARTIFACT_RESOURCE_NOT_AUTHORITY_BOUND")
        return self


class ExactGovernedArtifactQuarantine(BaseModel):
    schema_version: Literal["uaa-governed-artifact-quarantine.v1"] = (
        "uaa-governed-artifact-quarantine.v1"
    )
    quarantine_projection_ref: str
    recipe_ref: str
    artifact_ref: str
    quarantine_ref: str
    download_transaction_ref: str
    origin_ref: str
    quarantine_store_ref: str
    content_fingerprint_ref: str
    declared_media_type: GovernedArtifactMediaType
    byte_count: int = Field(ge=1, le=MAX_GOVERNED_ARTIFACT_BYTES)
    expires_at: datetime
    quarantined: Literal[True] = True
    trusted_for_use: Literal[False] = False
    raw_artifact_returned: Literal[False] = False
    artifact_opened: Literal[False] = False
    materialized_outside_quarantine: Literal[False] = False
    browser_opened: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    real_external_target: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_quarantine(self) -> "ExactGovernedArtifactQuarantine":
        for value, label in (
            (self.quarantine_projection_ref, "quarantine_projection_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.artifact_ref, "artifact_ref"),
            (self.quarantine_ref, "quarantine_ref"),
            (self.download_transaction_ref, "download_transaction_ref"),
            (self.origin_ref, "origin_ref"),
            (self.quarantine_store_ref, "quarantine_store_ref"),
            (self.content_fingerprint_ref, "content_fingerprint_ref"),
        ):
            validate_task_ref(value, label)
        if self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_ARTIFACT_TIMEZONE_REQUIRED")
        expected_quarantine_ref = governed_artifact_quarantine_ref(
            origin_ref=self.origin_ref,
            artifact_ref=self.artifact_ref,
            download_transaction_ref=self.download_transaction_ref,
        )
        if self.quarantine_ref != expected_quarantine_ref:
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_SCOPE_MISMATCH")
        expected_projection_ref = stable_governed_browser_ref(
            "artifact-quarantine-projection-ref:governed-browser",
            self.model_dump(
                mode="json",
                exclude={"quarantine_projection_ref"},
            ),
        )
        if self.quarantine_projection_ref != expected_projection_ref:
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_PROJECTION_REF_MISMATCH")
        return self


class ExactGovernedArtifactUploadPlan(BaseModel):
    schema_version: Literal["uaa-governed-artifact-upload-plan.v1"] = (
        "uaa-governed-artifact-upload-plan.v1"
    )
    plan_ref: str
    recipe_ref: str
    artifact_ref: str
    quarantine_ref: str
    download_transaction_ref: str
    source_download_receipt_ref: str
    source_download_recipe_ref: str
    quarantine_store_ref: str
    content_fingerprint_ref: str
    transfer_surface_ref: str
    visibility_proof_ref: str
    origin_ref: str
    page_snapshot_ref: str
    declared_media_type: GovernedArtifactMediaType
    byte_count: int = Field(ge=1, le=MAX_GOVERNED_ARTIFACT_BYTES)
    expires_at: datetime
    artifact_fingerprint_verified: Literal[True] = True
    quarantined_source_required: Literal[True] = True
    upload_plan_only: Literal[True] = True
    raw_artifact_returned: Literal[False] = False
    upload_body_materialized: Literal[False] = False
    upload_performed: Literal[False] = False
    browser_opened: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    real_external_target: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_plan(self) -> "ExactGovernedArtifactUploadPlan":
        for value, label in (
            (self.plan_ref, "plan_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.artifact_ref, "artifact_ref"),
            (self.quarantine_ref, "quarantine_ref"),
            (self.download_transaction_ref, "download_transaction_ref"),
            (self.source_download_receipt_ref, "source_download_receipt_ref"),
            (self.source_download_recipe_ref, "source_download_recipe_ref"),
            (self.quarantine_store_ref, "quarantine_store_ref"),
            (self.content_fingerprint_ref, "content_fingerprint_ref"),
            (self.transfer_surface_ref, "transfer_surface_ref"),
            (self.visibility_proof_ref, "visibility_proof_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
        ):
            validate_task_ref(value, label)
        if self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_ARTIFACT_TIMEZONE_REQUIRED")
        expected_quarantine_ref = governed_artifact_quarantine_ref(
            origin_ref=self.origin_ref,
            artifact_ref=self.artifact_ref,
            download_transaction_ref=self.download_transaction_ref,
        )
        if self.quarantine_ref != expected_quarantine_ref:
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_SCOPE_MISMATCH")
        _validate_hash_pinned_ref(
            self.source_download_receipt_ref,
            label="source_download_receipt_ref",
            prefix="receipt-ref:governed-external-action:",
        )
        _validate_hash_pinned_ref(
            self.source_download_recipe_ref,
            label="source_download_recipe_ref",
            prefix="artifact-transfer-recipe-ref:governed-browser:",
        )
        expected_plan_ref = stable_governed_browser_ref(
            "artifact-upload-plan-ref:governed-browser",
            self.model_dump(mode="json", exclude={"plan_ref"}),
        )
        if self.plan_ref != expected_plan_ref:
            raise ValueError("GOVERNED_ARTIFACT_UPLOAD_PLAN_REF_MISMATCH")
        return self


class GovernedArtifactTransferReceipt(BaseModel):
    schema_version: Literal["uaa-governed-artifact-transfer-receipt.v1"] = (
        "uaa-governed-artifact-transfer-receipt.v1"
    )
    receipt_ref: str
    recipe_ref: str
    operation: GovernedArtifactTransferOperation
    artifact_ref: str
    quarantine_ref: str
    download_transaction_ref: str
    origin_ref: str
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    status: GovernedArtifactTransferStatus
    external_action_state: ExternalActionState
    external_action_receipt_ref: str | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_settlement_ref: str | None = None
    content_fingerprint_ref: str | None = None
    source_download_receipt_ref: str | None = None
    source_download_recipe_ref: str | None = None
    quarantine_projection_ref: str | None = None
    upload_plan_ref: str | None = None
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    reason_refs: list[str] = Field(default_factory=list, max_length=16)
    replayed: StrictBool = False
    content_free: Literal[True] = True
    raw_path_recorded: Literal[False] = False
    raw_artifact_recorded: Literal[False] = False
    live_download_performed: Literal[False] = False
    upload_performed: Literal[False] = False
    upload_body_materialized: Literal[False] = False
    browser_action_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    automatic_retry_allowed: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_receipt(self) -> "GovernedArtifactTransferReceipt":
        for value, label in (
            (self.receipt_ref, "receipt_ref"),
            (self.recipe_ref, "recipe_ref"),
            (self.artifact_ref, "artifact_ref"),
            (self.quarantine_ref, "quarantine_ref"),
            (self.download_transaction_ref, "download_transaction_ref"),
            (self.origin_ref, "origin_ref"),
            (self.transaction_ref, "transaction_ref"),
            (self.intent_ref, "intent_ref"),
            (self.binding_ref, "binding_ref"),
            (self.external_action_receipt_ref, "external_action_receipt_ref"),
            (self.approval_validation_ref, "approval_validation_ref"),
            (self.authority_decision_ref, "authority_decision_ref"),
            (self.budget_reservation_ref, "budget_reservation_ref"),
            (self.budget_settlement_ref, "budget_settlement_ref"),
            (self.content_fingerprint_ref, "content_fingerprint_ref"),
            (self.source_download_receipt_ref, "source_download_receipt_ref"),
            (self.source_download_recipe_ref, "source_download_recipe_ref"),
            (self.quarantine_projection_ref, "quarantine_projection_ref"),
            (self.upload_plan_ref, "upload_plan_ref"),
            *[(ref, "evidence_ref") for ref in self.evidence_refs],
            *[(ref, "reason_ref") for ref in self.reason_refs],
        ):
            if value is not None:
                validate_task_ref(value, label)
        _validate_hash_pinned_ref(
            self.artifact_ref,
            label="artifact_ref",
            prefix="artifact-ref:governed-browser:",
        )
        _validate_hash_pinned_ref(
            self.quarantine_ref,
            label="quarantine_ref",
            prefix="artifact-quarantine-ref:governed-browser:",
        )
        expected_quarantine_ref = governed_artifact_quarantine_ref(
            origin_ref=self.origin_ref,
            artifact_ref=self.artifact_ref,
            download_transaction_ref=self.download_transaction_ref,
        )
        if self.quarantine_ref != expected_quarantine_ref:
            raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_SCOPE_MISMATCH")
        ready_statuses = {
            GovernedArtifactTransferStatus.quarantined.value,
            GovernedArtifactTransferStatus.upload_plan_ready.value,
        }
        operation = GovernedArtifactTransferOperation(self.operation)
        status = GovernedArtifactTransferStatus(self.status)
        if (
            status == GovernedArtifactTransferStatus.quarantined
            and operation != GovernedArtifactTransferOperation.download_quarantine
        ) or (
            status == GovernedArtifactTransferStatus.upload_plan_ready
            and operation
            != GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
        ):
            raise ValueError("GOVERNED_ARTIFACT_OPERATION_STATUS_MISMATCH")
        if (
            operation == GovernedArtifactTransferOperation.download_quarantine
            and self.download_transaction_ref != self.transaction_ref
        ):
            raise ValueError("GOVERNED_ARTIFACT_DOWNLOAD_TRANSACTION_MISMATCH")
        if (
            operation
            == GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
            and self.download_transaction_ref == self.transaction_ref
        ):
            raise ValueError("GOVERNED_ARTIFACT_SOURCE_TRANSACTION_MUST_BE_DISTINCT")
        if (
            self.status in ready_statuses
            and self.external_action_state != ExternalActionState.succeeded.value
        ):
            raise ValueError("GOVERNED_ARTIFACT_READY_STATE_MISMATCH")
        if self.status in ready_statuses:
            kernel_proof_refs = (
                self.external_action_receipt_ref,
                self.approval_validation_ref,
                self.authority_decision_ref,
                self.budget_reservation_ref,
                self.budget_settlement_ref,
            )
            if self.replayed or any(ref is None for ref in kernel_proof_refs):
                raise ValueError("GOVERNED_ARTIFACT_READY_KERNEL_PROOF_REQUIRED")
            if self.content_fingerprint_ref is None:
                raise ValueError("GOVERNED_ARTIFACT_READY_FINGERPRINT_REQUIRED")
            _validate_hash_pinned_ref(
                self.content_fingerprint_ref,
                label="content_fingerprint_ref",
                prefix="content-fingerprint-ref:governed-browser:",
            )
            if status == GovernedArtifactTransferStatus.quarantined:
                if (
                    self.quarantine_projection_ref is None
                    or self.source_download_receipt_ref is not None
                    or self.source_download_recipe_ref is not None
                    or self.upload_plan_ref is not None
                ):
                    raise ValueError(
                        "GOVERNED_ARTIFACT_QUARANTINE_PROJECTION_PROOF_REQUIRED"
                    )
                _validate_hash_pinned_ref(
                    self.quarantine_projection_ref,
                    label="quarantine_projection_ref",
                    prefix="artifact-quarantine-projection-ref:governed-browser:",
                )
                expected_evidence_refs = [
                    self.artifact_ref,
                    self.quarantine_ref,
                    self.content_fingerprint_ref,
                    self.quarantine_projection_ref,
                ]
            else:
                if (
                    self.upload_plan_ref is None
                    or self.source_download_receipt_ref is None
                    or self.source_download_recipe_ref is None
                    or self.quarantine_projection_ref is not None
                ):
                    raise ValueError("GOVERNED_ARTIFACT_UPLOAD_PLAN_PROOF_REQUIRED")
                _validate_hash_pinned_ref(
                    self.source_download_receipt_ref,
                    label="source_download_receipt_ref",
                    prefix="receipt-ref:governed-external-action:",
                )
                _validate_hash_pinned_ref(
                    self.source_download_recipe_ref,
                    label="source_download_recipe_ref",
                    prefix="artifact-transfer-recipe-ref:governed-browser:",
                )
                _validate_hash_pinned_ref(
                    self.upload_plan_ref,
                    label="upload_plan_ref",
                    prefix="artifact-upload-plan-ref:governed-browser:",
                )
                expected_evidence_refs = [
                    self.artifact_ref,
                    self.quarantine_ref,
                    self.content_fingerprint_ref,
                    self.source_download_receipt_ref,
                    self.source_download_recipe_ref,
                    self.upload_plan_ref,
                ]
            if self.evidence_refs != expected_evidence_refs:
                raise ValueError("GOVERNED_ARTIFACT_READY_EVIDENCE_MISMATCH")
        elif any(
            ref is not None
            for ref in (
                self.content_fingerprint_ref,
                self.source_download_receipt_ref,
                self.source_download_recipe_ref,
                self.quarantine_projection_ref,
                self.upload_plan_ref,
            )
        ):
            raise ValueError("GOVERNED_ARTIFACT_NON_READY_PROJECTION_PROOF_DENIED")
        if (
            self.status == GovernedArtifactTransferStatus.replayed_content_free.value
            and not self.replayed
        ):
            raise ValueError("GOVERNED_ARTIFACT_REPLAY_FLAG_REQUIRED")
        expected_receipt_ref = stable_governed_browser_ref(
            "receipt-ref:governed-artifact-transfer",
            self.model_dump(mode="json", exclude={"receipt_ref"}),
        )
        if self.receipt_ref != expected_receipt_ref:
            raise ValueError("GOVERNED_ARTIFACT_RECEIPT_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_artifact_transfer_receipt",
        )
        return self


class ExactGovernedArtifactTransferResult(BaseModel):
    receipt: GovernedArtifactTransferReceipt
    quarantine: ExactGovernedArtifactQuarantine | None = None
    upload_plan: ExactGovernedArtifactUploadPlan | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_result(self) -> "ExactGovernedArtifactTransferResult":
        if self.receipt.status == GovernedArtifactTransferStatus.quarantined.value:
            if self.quarantine is None or self.upload_plan is not None:
                raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_RESULT_MISMATCH")
            if (
                self.quarantine.recipe_ref,
                self.quarantine.artifact_ref,
                self.quarantine.quarantine_ref,
                self.quarantine.download_transaction_ref,
                self.quarantine.origin_ref,
            ) != (
                self.receipt.recipe_ref,
                self.receipt.artifact_ref,
                self.receipt.quarantine_ref,
                self.receipt.download_transaction_ref,
                self.receipt.origin_ref,
            ):
                raise ValueError("GOVERNED_ARTIFACT_QUARANTINE_RESULT_SCOPE_MISMATCH")
            if (
                self.quarantine.content_fingerprint_ref
                != self.receipt.content_fingerprint_ref
                or self.quarantine.quarantine_projection_ref
                != self.receipt.quarantine_projection_ref
            ):
                raise ValueError(
                    "GOVERNED_ARTIFACT_QUARANTINE_RESULT_EVIDENCE_MISMATCH"
                )
        elif (
            self.receipt.status
            == GovernedArtifactTransferStatus.upload_plan_ready.value
        ):
            if self.upload_plan is None or self.quarantine is not None:
                raise ValueError("GOVERNED_ARTIFACT_UPLOAD_PLAN_RESULT_MISMATCH")
            if (
                self.upload_plan.recipe_ref,
                self.upload_plan.artifact_ref,
                self.upload_plan.quarantine_ref,
                self.upload_plan.download_transaction_ref,
                self.upload_plan.origin_ref,
            ) != (
                self.receipt.recipe_ref,
                self.receipt.artifact_ref,
                self.receipt.quarantine_ref,
                self.receipt.download_transaction_ref,
                self.receipt.origin_ref,
            ):
                raise ValueError("GOVERNED_ARTIFACT_UPLOAD_PLAN_RESULT_SCOPE_MISMATCH")
            if (
                self.upload_plan.content_fingerprint_ref
                != self.receipt.content_fingerprint_ref
                or self.upload_plan.source_download_receipt_ref
                != self.receipt.source_download_receipt_ref
                or self.upload_plan.source_download_recipe_ref
                != self.receipt.source_download_recipe_ref
                or self.upload_plan.plan_ref != self.receipt.upload_plan_ref
            ):
                raise ValueError(
                    "GOVERNED_ARTIFACT_UPLOAD_PLAN_RESULT_EVIDENCE_MISMATCH"
                )
        elif self.quarantine is not None or self.upload_plan is not None:
            raise ValueError("GOVERNED_ARTIFACT_NON_SUCCESS_PROJECTION_DENIED")
        return self


class ExactGovernedArtifactTransferService:
    """Run one registered inactive transfer through every shared gate."""

    def __init__(
        self,
        *,
        registry: GovernedArtifactTransferRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        quarantine_store: GovernedArtifactQuarantineStore,
        source_download_kernel: GovernedExternalActionKernel | None = None,
        source_download_registry: GovernedArtifactTransferRecipeRegistry | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._registry = registry
        self._kernel = kernel
        self._store = quarantine_store
        self._source_download_kernel = source_download_kernel
        self._source_download_registry = source_download_registry
        self._clock = clock

    def execute(
        self,
        transfer_request: ExactGovernedArtifactTransferRequest,
        *,
        injected_download_payload: bytearray | None = None,
    ) -> ExactGovernedArtifactTransferResult:
        if injected_download_payload is not None and not isinstance(
            injected_download_payload, bytearray
        ):
            raise TypeError("GOVERNED_ARTIFACT_MUTABLE_PAYLOAD_REQUIRED")
        try:
            return self._execute(
                transfer_request,
                injected_download_payload=injected_download_payload,
            )
        finally:
            if injected_download_payload is not None:
                injected_download_payload[:] = b"\x00" * len(injected_download_payload)

    def _execute(
        self,
        transfer_request: ExactGovernedArtifactTransferRequest,
        *,
        injected_download_payload: bytearray | None,
    ) -> ExactGovernedArtifactTransferResult:
        request = ExactGovernedArtifactTransferRequest.model_validate(
            transfer_request.model_dump(mode="json")
        )
        execution = request.execution_request
        recipe = self._registry.resolve(request.recipe_ref)
        requested_operation = GovernedArtifactTransferOperation(request.operation)
        if recipe is None:
            return _preflight_blocked(
                request,
                operation=requested_operation,
                reason_ref="reason-ref:governed-artifact:recipe-unregistered",
            )
        operation = GovernedArtifactTransferOperation(recipe.operation)
        if operation != requested_operation:
            return _preflight_blocked(
                request,
                operation=requested_operation,
                reason_ref="reason-ref:governed-artifact:operation-mismatch",
            )
        if (
            recipe.artifact_ref,
            recipe.quarantine_ref,
            recipe.download_transaction_ref,
            recipe.transaction_ref,
        ) != (
            request.artifact_ref,
            request.quarantine_ref,
            request.download_transaction_ref,
            execution.binding.transaction_ref,
        ):
            return _preflight_blocked(
                request,
                operation=operation,
                reason_ref="reason-ref:governed-artifact:request-scope-mismatch",
            )
        if recipe.quarantine_store_ref != self._store.binding_ref:
            return _preflight_blocked(
                request,
                operation=operation,
                reason_ref="reason-ref:governed-artifact:store-binding-mismatch",
            )
        scope_reason = _recipe_scope_reason(recipe, execution)
        if scope_reason is not None:
            return _preflight_blocked(
                request,
                operation=operation,
                reason_ref=scope_reason,
            )
        kernel_execution = ExternalActionExecutionRequest.model_validate(
            {
                **execution.model_dump(mode="json"),
                "idempotency_ref": stable_governed_browser_ref(
                    "idempotency-ref:governed-artifact-transfer",
                    {
                        "source_idempotency_ref": execution.idempotency_ref,
                        "recipe_ref": recipe.recipe_ref,
                    },
                ),
            }
        )
        replay = self._kernel.replay_if_terminal(kernel_execution)
        if replay is not None:
            return _result_from_external_receipt(
                request=request,
                recipe=recipe,
                external_receipt=replay,
                quarantine=None,
                upload_plan=None,
            )
        current_time, clock_reason = _read_transfer_clock(self._clock)
        if clock_reason is not None:
            return _preflight_blocked(
                request,
                operation=operation,
                reason_ref=clock_reason,
            )
        if (
            operation == GovernedArtifactTransferOperation.download_quarantine
            and injected_download_payload is None
        ):
            return _preflight_blocked(
                request,
                operation=operation,
                reason_ref="reason-ref:governed-artifact:injected-payload-required",
            )
        if (
            operation
            == GovernedArtifactTransferOperation.upload_quarantined_artifact_plan
            and injected_download_payload is not None
        ):
            return _preflight_blocked(
                request,
                operation=operation,
                reason_ref="reason-ref:governed-artifact:raw-upload-payload-denied",
            )
        assert current_time is not None
        if current_time < recipe.created_at:
            return _preflight_blocked(
                request,
                operation=operation,
                reason_ref="reason-ref:governed-artifact:recipe-not-yet-valid",
            )
        captured_quarantine: ExactGovernedArtifactQuarantine | None = None
        captured_plan: ExactGovernedArtifactUploadPlan | None = None

        def dispatch(
            dispatched_request: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            nonlocal captured_quarantine, captured_plan
            current_time, dispatch_clock_reason = _read_transfer_clock(self._clock)
            if dispatch_clock_reason is not None:
                return _failed_dispatch(
                    dispatched_request,
                    "transfer-clock-invalid",
                )
            assert current_time is not None
            if (
                dispatched_request.binding.binding_ref != recipe.binding_ref
                or not recipe.created_at <= current_time < recipe.expires_at
            ):
                return _failed_dispatch(
                    dispatched_request,
                    "transfer-revalidation-failed",
                )
            if operation == GovernedArtifactTransferOperation.download_quarantine:
                assert injected_download_payload is not None
                try:
                    inspection = self._store.quarantine(
                        quarantine_ref=recipe.quarantine_ref,
                        payload=injected_download_payload,
                        declared_media_type=GovernedArtifactMediaType(
                            recipe.declared_media_type
                        ),
                        max_bytes=recipe.max_bytes,
                    )
                except GovernedArtifactPayloadRejected:
                    return _failed_dispatch(
                        dispatched_request,
                        "download-payload-rejected",
                    )
                quarantine_payload = {
                    "recipe_ref": recipe.recipe_ref,
                    "artifact_ref": recipe.artifact_ref,
                    "quarantine_ref": recipe.quarantine_ref,
                    "download_transaction_ref": recipe.download_transaction_ref,
                    "origin_ref": recipe.origin_ref,
                    "quarantine_store_ref": recipe.quarantine_store_ref,
                    "content_fingerprint_ref": inspection.content_fingerprint_ref,
                    "declared_media_type": inspection.declared_media_type,
                    "byte_count": inspection.byte_count,
                    "expires_at": recipe.expires_at,
                }
                provisional_quarantine = (
                    ExactGovernedArtifactQuarantine.model_construct(
                        quarantine_projection_ref=(
                            "artifact-quarantine-projection-ref:"
                            "governed-browser:pending"
                        ),
                        **quarantine_payload,
                    )
                )
                quarantine_projection_ref = stable_governed_browser_ref(
                    "artifact-quarantine-projection-ref:governed-browser",
                    provisional_quarantine.model_dump(
                        mode="json",
                        exclude={"quarantine_projection_ref"},
                    ),
                )
                captured_quarantine = ExactGovernedArtifactQuarantine(
                    quarantine_projection_ref=quarantine_projection_ref,
                    **quarantine_payload,
                )
                evidence_refs = [
                    recipe.artifact_ref,
                    recipe.quarantine_ref,
                    inspection.content_fingerprint_ref,
                    quarantine_projection_ref,
                ]
            else:
                assert recipe.content_fingerprint_ref is not None
                assert recipe.source_download_receipt_ref is not None
                assert recipe.source_download_recipe_ref is not None
                if not self._source_download_receipt_is_valid(recipe):
                    return _failed_dispatch(
                        dispatched_request,
                        "source-download-receipt-required",
                    )
                try:
                    inspection = self._store.inspect(
                        quarantine_ref=recipe.quarantine_ref,
                        declared_media_type=GovernedArtifactMediaType(
                            recipe.declared_media_type
                        ),
                        max_bytes=recipe.max_bytes,
                        expected_content_fingerprint_ref=(
                            recipe.content_fingerprint_ref
                        ),
                    )
                except GovernedArtifactQuarantinePrecondition:
                    return _failed_dispatch(
                        dispatched_request,
                        "upload-artifact-precondition-failed",
                    )
                plan_payload = {
                    "recipe_ref": recipe.recipe_ref,
                    "artifact_ref": recipe.artifact_ref,
                    "quarantine_ref": recipe.quarantine_ref,
                    "download_transaction_ref": recipe.download_transaction_ref,
                    "source_download_receipt_ref": (recipe.source_download_receipt_ref),
                    "source_download_recipe_ref": recipe.source_download_recipe_ref,
                    "quarantine_store_ref": recipe.quarantine_store_ref,
                    "content_fingerprint_ref": inspection.content_fingerprint_ref,
                    "transfer_surface_ref": recipe.transfer_surface_ref,
                    "visibility_proof_ref": recipe.visibility_proof_ref,
                    "origin_ref": recipe.origin_ref,
                    "page_snapshot_ref": recipe.page_snapshot_ref,
                    "declared_media_type": inspection.declared_media_type,
                    "byte_count": inspection.byte_count,
                    "expires_at": recipe.expires_at,
                }
                provisional = ExactGovernedArtifactUploadPlan.model_construct(
                    plan_ref="artifact-upload-plan-ref:governed-browser:pending",
                    **plan_payload,
                )
                plan_ref = stable_governed_browser_ref(
                    "artifact-upload-plan-ref:governed-browser",
                    provisional.model_dump(mode="json", exclude={"plan_ref"}),
                )
                captured_plan = ExactGovernedArtifactUploadPlan(
                    plan_ref=plan_ref,
                    **plan_payload,
                )
                evidence_refs = [
                    recipe.artifact_ref,
                    recipe.quarantine_ref,
                    inspection.content_fingerprint_ref,
                    recipe.source_download_receipt_ref,
                    recipe.source_download_recipe_ref,
                    plan_ref,
                ]
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=evidence_refs,
                verified=True,
            )

        external_receipt = self._kernel.execute(kernel_execution, dispatch=dispatch)
        if (
            external_receipt.replayed
            or external_receipt.state != ExternalActionState.succeeded.value
        ):
            captured_quarantine = None
            captured_plan = None
        return _result_from_external_receipt(
            request=request,
            recipe=recipe,
            external_receipt=external_receipt,
            quarantine=captured_quarantine,
            upload_plan=captured_plan,
        )

    def _source_download_receipt_is_valid(
        self,
        recipe: GovernedArtifactTransferRecipe,
    ) -> bool:
        receipt_ref = recipe.source_download_receipt_ref
        source_recipe_ref = recipe.source_download_recipe_ref
        kernel = self._source_download_kernel
        source_registry = self._source_download_registry
        if (
            receipt_ref is None
            or source_recipe_ref is None
            or kernel is None
            or source_registry is None
        ):
            return False
        source_recipe = source_registry.resolve(source_recipe_ref)
        if (
            source_recipe is None
            or GovernedArtifactTransferOperation(source_recipe.operation)
            != GovernedArtifactTransferOperation.download_quarantine
            or source_recipe.recipe_ref != source_recipe_ref
            or source_recipe.transaction_ref != recipe.download_transaction_ref
            or source_recipe.download_transaction_ref != recipe.download_transaction_ref
            or source_recipe.artifact_ref != recipe.artifact_ref
            or source_recipe.quarantine_ref != recipe.quarantine_ref
            or source_recipe.origin_ref != recipe.origin_ref
            or source_recipe.quarantine_store_ref != recipe.quarantine_store_ref
            or source_recipe.declared_media_type != recipe.declared_media_type
            or source_recipe.max_bytes != recipe.max_bytes
            or source_recipe.content_fingerprint_ref is not None
            or source_recipe.source_download_receipt_ref is not None
            or source_recipe.source_download_recipe_ref is not None
        ):
            return False
        try:
            receipt = kernel.terminal_receipt_by_ref(
                transaction_ref=recipe.download_transaction_ref,
                receipt_ref=receipt_ref,
            )
        except Exception:
            return False
        if (
            receipt is None
            or receipt.replayed
            or receipt.state != ExternalActionState.succeeded.value
            or receipt.transaction_ref != recipe.download_transaction_ref
            or receipt.receipt_ref != receipt_ref
            or receipt.binding_ref != source_recipe.binding_ref
            or any(
                ref is None
                for ref in (
                    receipt.approval_validation_ref,
                    receipt.authority_decision_ref,
                    receipt.budget_reservation_ref,
                    receipt.budget_settlement_ref,
                )
            )
            or recipe.content_fingerprint_ref is None
            or len(receipt.evidence_refs) != 4
            or receipt.evidence_refs[:3]
            != [
                recipe.artifact_ref,
                recipe.quarantine_ref,
                recipe.content_fingerprint_ref,
            ]
            or not receipt.evidence_refs[3].startswith(
                "artifact-quarantine-projection-ref:governed-browser:"
            )
        ):
            return False
        return True


def _recipe_scope_reason(
    recipe: GovernedArtifactTransferRecipe,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    operation = GovernedArtifactTransferOperation(recipe.operation)
    required_resources = {
        recipe.operation_authority_ref,
        recipe.quarantine_ref,
        recipe.download_transaction_ref,
        recipe.quarantine_store_ref,
        recipe.transfer_surface_ref,
        recipe.visibility_proof_ref,
    }
    if recipe.content_fingerprint_ref is not None:
        required_resources.add(recipe.content_fingerprint_ref)
    if recipe.source_download_receipt_ref is not None:
        required_resources.add(recipe.source_download_receipt_ref)
    if recipe.source_download_recipe_ref is not None:
        required_resources.add(recipe.source_download_recipe_ref)
    checks = (
        (
            recipe.binding_ref == binding.binding_ref,
            "reason-ref:governed-artifact:binding-mismatch",
        ),
        (
            recipe.transaction_ref == binding.transaction_ref,
            "reason-ref:governed-artifact:transaction-mismatch",
        ),
        (
            recipe.origin_ref == binding.origin_ref,
            "reason-ref:governed-artifact:origin-mismatch",
        ),
        (
            recipe.page_snapshot_ref == binding.page_snapshot_ref,
            "reason-ref:governed-artifact:snapshot-mismatch",
        ),
        (
            recipe.transfer_schema_ref == binding.field_schema_ref,
            "reason-ref:governed-artifact:schema-mismatch",
        ),
        (
            binding.artifact_refs == [recipe.artifact_ref],
            "reason-ref:governed-artifact:artifact-mismatch",
        ),
        (
            binding.authority_capability == _required_capability(operation).value,
            "reason-ref:governed-artifact:capability-mismatch",
        ),
        (
            binding.human_present,
            "reason-ref:governed-artifact:human-presence-required",
        ),
        (
            required_resources.issubset(set(binding.exact_resource_refs())),
            "reason-ref:governed-artifact:resource-not-authority-bound",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-artifact:real-targets-inactive",
        ),
        (
            recipe.expires_at <= binding.start_deadline,
            "reason-ref:governed-artifact:recipe-outlives-deadline",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _failed_dispatch(
    request: ExternalActionExecutionRequest,
    suffix: str,
) -> ExternalActionDispatchResult:
    return ExternalActionDispatchResult(
        outcome=ExternalActionDispatchOutcome.failed,
        evidence_refs=[
            stable_governed_browser_ref(
                f"evidence-ref:governed-artifact:{suffix}",
                {"intent_ref": request.intent_ref},
            )
        ],
        verified=False,
    )


def _read_transfer_clock(
    clock: Callable[[], datetime],
) -> tuple[datetime | None, str | None]:
    try:
        current_time = clock()
    except Exception:
        return None, "reason-ref:governed-artifact:trusted-clock-failed"
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        return None, "reason-ref:governed-artifact:trusted-clock-invalid"
    try:
        return current_time.astimezone(timezone.utc), None
    except Exception:
        return None, "reason-ref:governed-artifact:trusted-clock-invalid"


def _preflight_blocked(
    request: ExactGovernedArtifactTransferRequest,
    *,
    operation: GovernedArtifactTransferOperation,
    reason_ref: str,
) -> ExactGovernedArtifactTransferResult:
    execution = request.execution_request
    payload = {
        "recipe_ref": request.recipe_ref,
        "operation": operation,
        "artifact_ref": request.artifact_ref,
        "quarantine_ref": request.quarantine_ref,
        "download_transaction_ref": request.download_transaction_ref,
        "origin_ref": execution.binding.origin_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "binding_ref": execution.binding.binding_ref,
        "status": GovernedArtifactTransferStatus.preflight_blocked,
        "external_action_state": ExternalActionState.blocked,
        "reason_refs": [reason_ref],
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        GovernedArtifactTransferReceipt.model_construct(
            receipt_ref="receipt-ref:governed-artifact-transfer:pending",
            **payload,
        ).model_dump(mode="json", exclude={"receipt_ref"}),
    )
    return ExactGovernedArtifactTransferResult(
        receipt=GovernedArtifactTransferReceipt(
            receipt_ref=receipt_ref,
            **payload,
        )
    )


def _result_from_external_receipt(
    *,
    request: ExactGovernedArtifactTransferRequest,
    recipe: GovernedArtifactTransferRecipe,
    external_receipt: ExternalActionReceipt,
    quarantine: ExactGovernedArtifactQuarantine | None,
    upload_plan: ExactGovernedArtifactUploadPlan | None,
) -> ExactGovernedArtifactTransferResult:
    state = ExternalActionState(external_receipt.state)
    operation = GovernedArtifactTransferOperation(recipe.operation)
    if external_receipt.replayed:
        status = GovernedArtifactTransferStatus.replayed_content_free
    elif state == ExternalActionState.succeeded:
        status = {
            GovernedArtifactTransferOperation.download_quarantine: (
                GovernedArtifactTransferStatus.quarantined
            ),
            GovernedArtifactTransferOperation.upload_quarantined_artifact_plan: (
                GovernedArtifactTransferStatus.upload_plan_ready
            ),
        }[operation]
    else:
        status = {
            ExternalActionState.blocked: (
                GovernedArtifactTransferStatus.transaction_blocked
            ),
            ExternalActionState.failed: GovernedArtifactTransferStatus.failed,
            ExternalActionState.outcome_ambiguous: (
                GovernedArtifactTransferStatus.outcome_ambiguous
            ),
            ExternalActionState.started: (
                GovernedArtifactTransferStatus.outcome_ambiguous
            ),
            ExternalActionState.prepared: (
                GovernedArtifactTransferStatus.outcome_ambiguous
            ),
        }[state]
    reason_refs = list(external_receipt.reason_refs)
    if state == ExternalActionState.failed and not reason_refs:
        reason_refs = ["reason-ref:governed-artifact:transfer-preparation-failed"]
    payload = {
        "recipe_ref": recipe.recipe_ref,
        "operation": operation,
        "artifact_ref": recipe.artifact_ref,
        "quarantine_ref": recipe.quarantine_ref,
        "download_transaction_ref": recipe.download_transaction_ref,
        "origin_ref": recipe.origin_ref,
        "transaction_ref": external_receipt.transaction_ref,
        "intent_ref": external_receipt.intent_ref,
        "binding_ref": external_receipt.binding_ref,
        "status": status,
        "external_action_state": state,
        "external_action_receipt_ref": external_receipt.receipt_ref,
        "approval_validation_ref": external_receipt.approval_validation_ref,
        "authority_decision_ref": external_receipt.authority_decision_ref,
        "budget_reservation_ref": external_receipt.budget_reservation_ref,
        "budget_settlement_ref": external_receipt.budget_settlement_ref,
        "content_fingerprint_ref": (
            quarantine.content_fingerprint_ref
            if quarantine is not None
            else upload_plan.content_fingerprint_ref
            if upload_plan is not None
            else None
        ),
        "source_download_receipt_ref": (
            upload_plan.source_download_receipt_ref if upload_plan is not None else None
        ),
        "source_download_recipe_ref": (
            upload_plan.source_download_recipe_ref if upload_plan is not None else None
        ),
        "quarantine_projection_ref": (
            quarantine.quarantine_projection_ref if quarantine is not None else None
        ),
        "upload_plan_ref": upload_plan.plan_ref if upload_plan is not None else None,
        "evidence_refs": list(external_receipt.evidence_refs),
        "reason_refs": reason_refs,
        "replayed": external_receipt.replayed,
    }
    receipt_ref = stable_governed_browser_ref(
        "receipt-ref:governed-artifact-transfer",
        GovernedArtifactTransferReceipt.model_construct(
            receipt_ref="receipt-ref:governed-artifact-transfer:pending",
            **payload,
        ).model_dump(mode="json", exclude={"receipt_ref"}),
    )
    return ExactGovernedArtifactTransferResult(
        receipt=GovernedArtifactTransferReceipt(
            receipt_ref=receipt_ref,
            **payload,
        ),
        quarantine=quarantine,
        upload_plan=upload_plan,
    )
