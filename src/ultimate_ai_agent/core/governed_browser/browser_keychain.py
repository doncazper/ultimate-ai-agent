"""Pinned macOS Keychain adapter for exact governed-browser opaque handles."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)

from .contracts import stable_governed_browser_ref


GOVERNED_BROWSER_KEYCHAIN_ADAPTER_REF = (
    "adapter-ref:governed-browser-keychain:macos:v1"
)
GOVERNED_BROWSER_KEYCHAIN_HELPER_VERSION_REF = (
    "helper-version-ref:governed-browser-keychain:v1"
)
GOVERNED_BROWSER_KEYCHAIN_HELPER_NAME = "uaa-governed-browser-keychain-helper"
GOVERNED_BROWSER_KEYCHAIN_HELPER_METADATA_NAME = (
    "governed-browser-keychain-helper.json"
)
GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_INPUT_BYTES = 16 * 1024
GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES = 32 * 1024
GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_EXECUTABLE_BYTES = 32 * 1024 * 1024
GOVERNED_BROWSER_CREDENTIAL_MIN_BYTES = 16
GOVERNED_BROWSER_CREDENTIAL_MAX_BYTES = 4 * 1024


class GovernedBrowserKeychainError(RuntimeError):
    """Content-free failure at the pinned helper boundary."""


class GovernedBrowserKeychainStatus(str, Enum):
    ready = "ready"
    unsupported_platform = "unsupported_platform"
    helper_missing = "helper_missing"
    helper_untrusted = "helper_untrusted"


class GovernedBrowserKeychainOperation(str, Enum):
    store = "store"
    probe = "probe"
    delete = "delete"


def governed_browser_keychain_item_ref(
    *,
    origin_ref: str,
    credential_handle_ref: str,
    credential_generation_ref: str,
) -> str:
    """Derive the opaque Keychain item ref shared with the native helper."""

    for value, label in (
        (origin_ref, "origin_ref"),
        (credential_handle_ref, "credential_handle_ref"),
        (credential_generation_ref, "credential_generation_ref"),
    ):
        validate_task_ref(value, label)
    scope = "\0".join(
        (origin_ref, credential_handle_ref, credential_generation_ref)
    ).encode("utf-8")
    return (
        "keychain-item-ref:governed-browser:sha256:"
        f"{hashlib.sha256(scope).hexdigest()}"
    )


class GovernedBrowserCredentialRegistration(BaseModel):
    """Safe-ref-only binding for one exact per-origin credential handle."""

    schema_version: Literal[
        "uaa-governed-browser-credential-registration.v1"
    ] = "uaa-governed-browser-credential-registration.v1"
    registration_ref: str = Field(..., min_length=1, max_length=240)
    origin_ref: str = Field(..., min_length=1, max_length=240)
    credential_handle_ref: str = Field(..., min_length=1, max_length=240)
    credential_generation_ref: str = Field(..., min_length=1, max_length=240)
    keychain_item_ref: str = Field(..., min_length=1, max_length=240)
    keychain_adapter_ref: Literal[
        "adapter-ref:governed-browser-keychain:macos:v1"
    ] = GOVERNED_BROWSER_KEYCHAIN_ADAPTER_REF
    macos_keychain_required: Literal[True] = True
    exact_origin_required: Literal[True] = True
    opaque_handle_only: Literal[True] = True
    credential_material_durable_in_python: Literal[False] = False
    credential_material_returned: Literal[False] = False
    browser_session_authority_granted: Literal[False] = False
    live_network_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_registration(self) -> "GovernedBrowserCredentialRegistration":
        for value, label in (
            (self.registration_ref, "registration_ref"),
            (self.origin_ref, "origin_ref"),
            (self.credential_handle_ref, "credential_handle_ref"),
            (self.credential_generation_ref, "credential_generation_ref"),
            (self.keychain_item_ref, "keychain_item_ref"),
            (self.keychain_adapter_ref, "keychain_adapter_ref"),
        ):
            validate_task_ref(value, label)
        if not self.origin_ref.startswith("origin-ref:governed-browser:"):
            raise ValueError("GOVERNED_BROWSER_KEYCHAIN_ORIGIN_REF_REQUIRED")
        if not self.credential_handle_ref.startswith(
            "credential-handle-ref:governed-browser:"
        ):
            raise ValueError("GOVERNED_BROWSER_CREDENTIAL_HANDLE_REF_REQUIRED")
        if not self.credential_generation_ref.startswith(
            "credential-generation-ref:governed-browser:"
        ):
            raise ValueError("GOVERNED_BROWSER_CREDENTIAL_GENERATION_REF_REQUIRED")
        expected_item_ref = governed_browser_keychain_item_ref(
            origin_ref=self.origin_ref,
            credential_handle_ref=self.credential_handle_ref,
            credential_generation_ref=self.credential_generation_ref,
        )
        if self.keychain_item_ref != expected_item_ref:
            raise ValueError("GOVERNED_BROWSER_KEYCHAIN_ITEM_REF_MISMATCH")
        expected_registration_ref = stable_governed_browser_ref(
            "credential-registration-ref:governed-browser",
            self.model_dump(mode="json", exclude={"registration_ref"}),
        )
        if self.registration_ref != expected_registration_ref:
            raise ValueError("GOVERNED_BROWSER_CREDENTIAL_REGISTRATION_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json"),
            "governed_browser_credential_registration",
        )
        return self


def build_governed_browser_credential_registration(
    *,
    origin_ref: str,
    credential_handle_ref: str,
    credential_generation_ref: str,
) -> GovernedBrowserCredentialRegistration:
    """Build a content-derived registration without accepting credential data."""

    keychain_item_ref = governed_browser_keychain_item_ref(
        origin_ref=origin_ref,
        credential_handle_ref=credential_handle_ref,
        credential_generation_ref=credential_generation_ref,
    )
    payload = {
        "origin_ref": origin_ref,
        "credential_handle_ref": credential_handle_ref,
        "credential_generation_ref": credential_generation_ref,
        "keychain_item_ref": keychain_item_ref,
    }
    provisional = GovernedBrowserCredentialRegistration.model_construct(
        registration_ref="credential-registration-ref:governed-browser:pending",
        **payload,
    )
    registration_ref = stable_governed_browser_ref(
        "credential-registration-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"registration_ref"}),
    )
    return GovernedBrowserCredentialRegistration(
        registration_ref=registration_ref,
        **payload,
    )


class GovernedBrowserKeychainReadiness(BaseModel):
    adapter_ref: Literal[
        "adapter-ref:governed-browser-keychain:macos:v1"
    ] = GOVERNED_BROWSER_KEYCHAIN_ADAPTER_REF
    status: GovernedBrowserKeychainStatus
    helper_version_ref: str | None = None
    helper_fingerprint_ref: str | None = None
    reason_refs: tuple[str, ...] = ()
    credential_material_included: Literal[False] = False
    browser_session_authority_granted: Literal[False] = False
    live_network_enabled: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_readiness(self) -> "GovernedBrowserKeychainReadiness":
        for value in (
            self.adapter_ref,
            self.helper_version_ref,
            self.helper_fingerprint_ref,
            *self.reason_refs,
        ):
            if value is not None:
                validate_task_ref(value, "governed_browser_keychain_readiness_ref")
        if self.status == GovernedBrowserKeychainStatus.ready.value and not all(
            (self.helper_version_ref, self.helper_fingerprint_ref)
        ):
            raise ValueError("GOVERNED_BROWSER_KEYCHAIN_READY_PROOF_REQUIRED")
        return self


class GovernedBrowserKeychainOperationReceipt(BaseModel):
    """Safe-ref-only result; credential material can never enter this model."""

    schema_version: Literal[
        "uaa-governed-browser-keychain-operation-receipt.v1"
    ] = "uaa-governed-browser-keychain-operation-receipt.v1"
    adapter_ref: Literal[
        "adapter-ref:governed-browser-keychain:macos:v1"
    ] = GOVERNED_BROWSER_KEYCHAIN_ADAPTER_REF
    operation: GovernedBrowserKeychainOperation
    registration_ref: str
    origin_ref: str
    credential_handle_ref: str
    credential_generation_ref: str
    keychain_item_ref: str
    helper_receipt_ref: str
    created: StrictBool | None = None
    present: StrictBool
    deleted_or_absent: StrictBool | None = None
    content_free: Literal[True] = True
    credential_material_included: Literal[False] = False
    credential_material_returned: Literal[False] = False
    browser_session_started: Literal[False] = False
    authentication_performed: Literal[False] = False
    cookies_used: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_receipt(self) -> "GovernedBrowserKeychainOperationReceipt":
        for value, label in (
            (self.adapter_ref, "adapter_ref"),
            (self.registration_ref, "registration_ref"),
            (self.origin_ref, "origin_ref"),
            (self.credential_handle_ref, "credential_handle_ref"),
            (self.credential_generation_ref, "credential_generation_ref"),
            (self.keychain_item_ref, "keychain_item_ref"),
            (self.helper_receipt_ref, "helper_receipt_ref"),
        ):
            validate_task_ref(value, label)
        if self.operation == GovernedBrowserKeychainOperation.store.value:
            if self.created is None or self.present is not True:
                raise ValueError("GOVERNED_BROWSER_KEYCHAIN_STORE_RECEIPT_INVALID")
        elif self.operation == GovernedBrowserKeychainOperation.probe.value:
            if self.created is not None or self.present is not True:
                raise ValueError("GOVERNED_BROWSER_KEYCHAIN_PROBE_RECEIPT_INVALID")
        elif (
            self.created is not None
            or self.present is not False
            or self.deleted_or_absent is not True
        ):
            raise ValueError("GOVERNED_BROWSER_KEYCHAIN_DELETE_RECEIPT_INVALID")
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_used"}),
            "governed_browser_keychain_operation_receipt",
        )
        return self


class _HelperResponse(BaseModel):
    schema_version: Literal[
        "uaa-governed-browser-keychain-helper-response.v1"
    ] = "uaa-governed-browser-keychain-helper-response.v1"
    ok: StrictBool
    operation: Literal["version", "store", "probe", "delete", "unknown"]
    adapter_ref: Literal[
        "adapter-ref:governed-browser-keychain:macos:v1"
    ] = GOVERNED_BROWSER_KEYCHAIN_ADAPTER_REF
    helper_version: str = Field(..., min_length=1, max_length=32)
    helper_version_ref: Literal[
        "helper-version-ref:governed-browser-keychain:v1"
    ] = GOVERNED_BROWSER_KEYCHAIN_HELPER_VERSION_REF
    origin_ref: str | None = None
    credential_handle_ref: str | None = None
    credential_generation_ref: str | None = None
    keychain_item_ref: str | None = None
    helper_receipt_ref: str
    created: StrictBool | None = None
    present: StrictBool | None = None
    deleted_or_absent: StrictBool | None = None
    credential_material_included: Literal[False] = False
    credential_material_returned: Literal[False] = False
    browser_session_started: Literal[False] = False
    authentication_performed: Literal[False] = False
    cookies_used: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    execution_authority_granted: Literal[False] = False
    error_code: str | None = Field(default=None, max_length=80)

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_response(self) -> "_HelperResponse":
        for name, value in self.model_dump(mode="python").items():
            if name.endswith("_ref") and value is not None:
                validate_task_ref(str(value), f"governed_browser_helper_{name}")
        if self.ok and self.error_code is not None:
            raise ValueError("GOVERNED_BROWSER_KEYCHAIN_HELPER_ERROR_CODE_DENIED")
        if not self.ok and not self.error_code:
            raise ValueError("GOVERNED_BROWSER_KEYCHAIN_HELPER_ERROR_CODE_REQUIRED")
        if self.ok and self.operation != "version":
            if not all(
                (
                    self.origin_ref,
                    self.credential_handle_ref,
                    self.credential_generation_ref,
                    self.keychain_item_ref,
                )
            ):
                raise ValueError("GOVERNED_BROWSER_KEYCHAIN_HELPER_SCOPE_REQUIRED")
            if self.operation == "store" and (
                self.created is None or self.present is not True
            ):
                raise ValueError("GOVERNED_BROWSER_KEYCHAIN_HELPER_STORE_INVALID")
            if self.operation == "probe" and self.present is not True:
                raise ValueError("GOVERNED_BROWSER_KEYCHAIN_HELPER_PROBE_INVALID")
            if self.operation == "delete" and (
                self.present is not False or self.deleted_or_absent is not True
            ):
                raise ValueError("GOVERNED_BROWSER_KEYCHAIN_HELPER_DELETE_INVALID")
        return self


class MacOSGovernedBrowserKeychainAdapter:
    """Invoke one exact, hash-pinned native helper with bounded local I/O."""

    adapter_ref = GOVERNED_BROWSER_KEYCHAIN_ADAPTER_REF

    def __init__(
        self,
        *,
        helper_path: str | Path,
        expected_helper_sha256: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._helper_path = Path(helper_path)
        if not self._helper_path.is_absolute():
            raise ValueError("GOVERNED_BROWSER_KEYCHAIN_HELPER_ABSOLUTE_PATH_REQUIRED")
        if len(expected_helper_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in expected_helper_sha256
        ):
            raise ValueError("GOVERNED_BROWSER_KEYCHAIN_HELPER_SHA256_INVALID")
        self._expected_helper_sha256 = expected_helper_sha256
        self._timeout_seconds = max(1.0, min(float(timeout_seconds), 60.0))

    def readiness(self) -> GovernedBrowserKeychainReadiness:
        if sys.platform != "darwin":
            return GovernedBrowserKeychainReadiness(
                status=GovernedBrowserKeychainStatus.unsupported_platform,
                reason_refs=(
                    "reason-ref:governed-browser-keychain:macos-required",
                ),
            )
        try:
            helper_hash = self._validate_helper()
            response = self._invoke({"operation": "version"})
        except FileNotFoundError:
            return GovernedBrowserKeychainReadiness(
                status=GovernedBrowserKeychainStatus.helper_missing,
                reason_refs=(
                    "reason-ref:governed-browser-keychain:helper-missing",
                ),
            )
        except GovernedBrowserKeychainError:
            return GovernedBrowserKeychainReadiness(
                status=GovernedBrowserKeychainStatus.helper_untrusted,
                reason_refs=(
                    "reason-ref:governed-browser-keychain:helper-untrusted",
                ),
            )
        if response.operation != "version":
            return GovernedBrowserKeychainReadiness(
                status=GovernedBrowserKeychainStatus.helper_untrusted,
                reason_refs=(
                    "reason-ref:governed-browser-keychain:protocol-mismatch",
                ),
            )
        return GovernedBrowserKeychainReadiness(
            status=GovernedBrowserKeychainStatus.ready,
            helper_version_ref=response.helper_version_ref,
            helper_fingerprint_ref=f"helper-fingerprint-ref:sha256:{helper_hash}",
            reason_refs=("reason-ref:governed-browser-keychain:helper-ready",),
        )

    def store(
        self,
        registration: GovernedBrowserCredentialRegistration,
        *,
        request_ref: str,
        credential_material: bytearray,
    ) -> GovernedBrowserKeychainOperationReceipt:
        registration = GovernedBrowserCredentialRegistration.model_validate(
            registration.model_dump(mode="json")
        )
        validate_task_ref(request_ref, "request_ref")
        if not isinstance(credential_material, bytearray):
            raise TypeError("GOVERNED_BROWSER_CREDENTIAL_MUTABLE_BUFFER_REQUIRED")
        if not (
            GOVERNED_BROWSER_CREDENTIAL_MIN_BYTES
            <= len(credential_material)
            <= GOVERNED_BROWSER_CREDENTIAL_MAX_BYTES
        ):
            _zeroize(credential_material)
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_CREDENTIAL_LENGTH_INVALID"
            )
        try:
            encoded_material = (
                base64.urlsafe_b64encode(bytes(credential_material))
                .rstrip(b"=")
                .decode("ascii")
            )
            response = self._invoke(
                {
                    "operation": "store",
                    **_registration_scope(registration),
                    "request_ref": request_ref,
                    "credential_material_base64url": encoded_material,
                }
            )
        finally:
            _zeroize(credential_material)
        return self._operation_receipt(
            response,
            registration,
            GovernedBrowserKeychainOperation.store,
        )

    def probe(
        self,
        registration: GovernedBrowserCredentialRegistration,
        *,
        request_ref: str,
    ) -> GovernedBrowserKeychainOperationReceipt:
        registration = GovernedBrowserCredentialRegistration.model_validate(
            registration.model_dump(mode="json")
        )
        validate_task_ref(request_ref, "request_ref")
        response = self._invoke(
            {
                "operation": "probe",
                **_registration_scope(registration),
                "request_ref": request_ref,
            }
        )
        return self._operation_receipt(
            response,
            registration,
            GovernedBrowserKeychainOperation.probe,
        )

    def delete(
        self,
        registration: GovernedBrowserCredentialRegistration,
        *,
        request_ref: str,
    ) -> GovernedBrowserKeychainOperationReceipt:
        registration = GovernedBrowserCredentialRegistration.model_validate(
            registration.model_dump(mode="json")
        )
        validate_task_ref(request_ref, "request_ref")
        response = self._invoke(
            {
                "operation": "delete",
                **_registration_scope(registration),
                "request_ref": request_ref,
            }
        )
        return self._operation_receipt(
            response,
            registration,
            GovernedBrowserKeychainOperation.delete,
        )

    def _operation_receipt(
        self,
        response: _HelperResponse,
        registration: GovernedBrowserCredentialRegistration,
        operation: GovernedBrowserKeychainOperation,
    ) -> GovernedBrowserKeychainOperationReceipt:
        if response.operation != operation.value or not response.ok:
            self._raise_helper_failure(response)
        observed_scope = (
            response.origin_ref,
            response.credential_handle_ref,
            response.credential_generation_ref,
            response.keychain_item_ref,
        )
        expected_scope = (
            registration.origin_ref,
            registration.credential_handle_ref,
            registration.credential_generation_ref,
            registration.keychain_item_ref,
        )
        if observed_scope != expected_scope:
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_BINDING_MISMATCH"
            )
        assert response.present is not None
        return GovernedBrowserKeychainOperationReceipt(
            operation=operation,
            registration_ref=registration.registration_ref,
            origin_ref=registration.origin_ref,
            credential_handle_ref=registration.credential_handle_ref,
            credential_generation_ref=registration.credential_generation_ref,
            keychain_item_ref=registration.keychain_item_ref,
            helper_receipt_ref=response.helper_receipt_ref,
            created=response.created,
            present=response.present,
            deleted_or_absent=response.deleted_or_absent,
        )

    def _invoke(self, payload: dict[str, Any]) -> _HelperResponse:
        self._require_darwin()
        request = {
            "schema_version": (
                "uaa-governed-browser-keychain-helper-request.v1"
            ),
            **payload,
        }
        encoded = json.dumps(
            request,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        if len(encoded) > GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_INPUT_BYTES:
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_REQUEST_TOO_LARGE"
            )
        descriptor, expected_digest = self._open_validated_helper()
        try:
            with tempfile.TemporaryDirectory(
                prefix="uaa-browser-keychain-exec-",
                dir="/tmp",
            ) as temporary_dir:
                os.chmod(temporary_dir, 0o700)
                executable = (
                    Path(temporary_dir) / GOVERNED_BROWSER_KEYCHAIN_HELPER_NAME
                )
                copy_descriptor = os.open(
                    executable,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o700,
                )
                copied_digest = hashlib.sha256()
                try:
                    while True:
                        chunk = os.read(descriptor, 65_536)
                        if not chunk:
                            break
                        copied_digest.update(chunk)
                        if os.write(copy_descriptor, chunk) != len(chunk):
                            raise GovernedBrowserKeychainError(
                                "GOVERNED_BROWSER_KEYCHAIN_HELPER_COPY_SHORT_WRITE"
                            )
                    os.fsync(copy_descriptor)
                finally:
                    os.close(copy_descriptor)
                if copied_digest.hexdigest() != expected_digest:
                    raise GovernedBrowserKeychainError(
                        "GOVERNED_BROWSER_KEYCHAIN_HELPER_COPY_FINGERPRINT_MISMATCH"
                    )
                try:
                    completed = subprocess.run(
                        [os.fspath(executable)],
                        input=encoded,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=temporary_dir,
                        env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"},
                        timeout=self._timeout_seconds,
                        check=False,
                        shell=False,
                        start_new_session=True,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise GovernedBrowserKeychainError(
                        "GOVERNED_BROWSER_KEYCHAIN_HELPER_EXECUTION_FAILED"
                    ) from exc
        finally:
            os.close(descriptor)
        if (
            len(completed.stdout)
            > GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES
            or len(completed.stderr)
            > GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES
        ):
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_OUTPUT_TOO_LARGE"
            )
        try:
            response = _HelperResponse.model_validate_json(completed.stdout)
        except ValueError as exc:
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_RESPONSE_INVALID"
            ) from exc
        if completed.returncode != 0 or not response.ok:
            self._raise_helper_failure(response)
        return response

    def _validate_helper(self) -> str:
        descriptor, digest = self._open_validated_helper()
        os.close(descriptor)
        return digest

    def _open_validated_helper(self) -> tuple[int, str]:
        metadata = os.lstat(self._helper_path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size < 1
            or metadata.st_size
            > GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_EXECUTABLE_BYTES
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o022
            or not metadata.st_mode & stat.S_IXUSR
        ):
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_FILE_UNTRUSTED"
            )
        descriptor = os.open(
            self._helper_path,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or opened.st_size < 1
                or opened.st_size
                > GOVERNED_BROWSER_KEYCHAIN_HELPER_MAX_EXECUTABLE_BYTES
                or (opened.st_dev, opened.st_ino)
                != (metadata.st_dev, metadata.st_ino)
            ):
                raise GovernedBrowserKeychainError(
                    "GOVERNED_BROWSER_KEYCHAIN_HELPER_FILE_CHANGED"
                )
            digest = hashlib.sha256()
            while True:
                chunk = os.read(descriptor, 65_536)
                if not chunk:
                    break
                digest.update(chunk)
        except Exception:
            os.close(descriptor)
            raise
        actual = digest.hexdigest()
        if actual != self._expected_helper_sha256:
            os.close(descriptor)
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_HELPER_FINGERPRINT_MISMATCH"
            )
        os.lseek(descriptor, 0, os.SEEK_SET)
        return descriptor, actual

    @staticmethod
    def _raise_helper_failure(response: _HelperResponse) -> None:
        if response.error_code == "HELPER_KEYCHAIN_LOCKED":
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_LOCKED"
            )
        if response.error_code == "HELPER_KEY_NOT_FOUND":
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_ITEM_NOT_FOUND"
            )
        raise GovernedBrowserKeychainError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_OPERATION_FAILED"
        )

    @staticmethod
    def _require_darwin() -> None:
        if sys.platform != "darwin":
            raise GovernedBrowserKeychainError(
                "GOVERNED_BROWSER_KEYCHAIN_UNSUPPORTED_PLATFORM"
            )


def _registration_scope(
    registration: GovernedBrowserCredentialRegistration,
) -> dict[str, str]:
    return {
        "origin_ref": registration.origin_ref,
        "credential_handle_ref": registration.credential_handle_ref,
        "credential_generation_ref": registration.credential_generation_ref,
        "keychain_item_ref": registration.keychain_item_ref,
    }


def _zeroize(value: bytearray) -> None:
    for index in range(len(value)):
        value[index] = 0
