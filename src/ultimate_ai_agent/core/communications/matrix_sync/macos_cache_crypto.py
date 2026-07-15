from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.execution.validation import validate_execution_ref

from .cache import MatrixCacheKeyUnavailable, MatrixProtectedCacheError


MACOS_MATRIX_CACHE_ADAPTER_REF = "adapter-ref:matrix-protected-cache:macos-keychain:v1"
MACOS_MATRIX_CACHE_HELPER_VERSION_REF = "helper-version-ref:matrix-protected-cache:v1"
MACOS_MATRIX_CACHE_HELPER_NAME = "uaa-matrix-protected-cache-helper"
MACOS_MATRIX_CACHE_HELPER_MAX_INPUT_BYTES = 24 * 1024 * 1024
MACOS_MATRIX_CACHE_HELPER_MAX_OUTPUT_BYTES = 24 * 1024 * 1024
MACOS_MATRIX_CACHE_HELPER_MAX_EXECUTABLE_BYTES = 32 * 1024 * 1024


class MacOSMatrixCacheCryptoError(MatrixProtectedCacheError):
    pass


class _HelperResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["uaa-matrix-protected-cache-helper-response.v1"]
    ok: StrictBool
    operation: Literal["version", "create", "probe", "encrypt", "decrypt", "delete", "unknown"]
    adapter_ref: Literal["adapter-ref:matrix-protected-cache:macos-keychain:v1"]
    helper_version: str = Field(..., min_length=1, max_length=32)
    helper_version_ref: Literal["helper-version-ref:matrix-protected-cache:v1"]
    key_item_ref: str | None = None
    key_version_ref: str | None = None
    payload_base64url: str | None = Field(default=None, repr=False)
    payload_fingerprint_ref: str | None = None
    helper_receipt_ref: str
    created: StrictBool | None = None
    deleted_or_absent: StrictBool | None = None
    error_code: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def validate_response(self) -> "_HelperResponse":
        for value in (
            self.key_item_ref,
            self.key_version_ref,
            self.payload_fingerprint_ref,
            self.helper_receipt_ref,
        ):
            if value is not None:
                validate_execution_ref(value, "matrix_cache_helper_ref")
        if self.ok == (self.error_code is not None):
            raise ValueError("MATRIX_CACHE_HELPER_ERROR_POSTURE_INVALID")
        if self.ok and self.operation in {"encrypt", "decrypt"}:
            if not self.payload_base64url or not self.payload_fingerprint_ref:
                raise ValueError("MATRIX_CACHE_HELPER_PAYLOAD_RESPONSE_INVALID")
        elif self.payload_base64url is not None or self.payload_fingerprint_ref is not None:
            raise ValueError("MATRIX_CACHE_HELPER_PAYLOAD_RESPONSE_FORBIDDEN")
        return self


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_base64url(value: str, *, maximum: int) -> bytes:
    if not value or any(
        char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        for char in value
    ):
        raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_PAYLOAD_INVALID")
    padding = "=" * ((4 - len(value) % 4) % 4)
    decoded = base64.urlsafe_b64decode(value + padding)
    if len(decoded) > maximum or _encode_base64url(decoded) != value:
        raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_PAYLOAD_INVALID")
    return decoded


class MacOSMatrixCacheCryptoBackend:
    backend_ref = MACOS_MATRIX_CACHE_ADAPTER_REF

    def __init__(
        self,
        *,
        helper_path: Path,
        expected_helper_sha256: str,
        timeout_seconds: float = 30,
    ) -> None:
        self._helper_path = helper_path
        if len(expected_helper_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in expected_helper_sha256
        ):
            raise ValueError("MATRIX_CACHE_HELPER_SHA256_INVALID")
        self._expected_helper_sha256 = expected_helper_sha256
        self._timeout_seconds = max(1.0, min(float(timeout_seconds), 60.0))

    def create(self, *, key_item_ref: str, key_version_ref: str) -> str:
        response = self._invoke(
            "create", key_item_ref=key_item_ref, key_version_ref=key_version_ref
        )
        return response.helper_receipt_ref

    def probe(self, *, key_item_ref: str, key_version_ref: str) -> str:
        response = self._invoke(
            "probe", key_item_ref=key_item_ref, key_version_ref=key_version_ref
        )
        return response.helper_receipt_ref

    def encrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        plaintext: bytes,
        aad: bytes,
    ) -> bytes:
        return self._crypto(
            "encrypt",
            key_item_ref=key_item_ref,
            key_version_ref=key_version_ref,
            payload=plaintext,
            aad=aad,
        )

    def decrypt(
        self,
        *,
        key_item_ref: str,
        key_version_ref: str,
        ciphertext: bytes,
        aad: bytes,
    ) -> bytes:
        return self._crypto(
            "decrypt",
            key_item_ref=key_item_ref,
            key_version_ref=key_version_ref,
            payload=ciphertext,
            aad=aad,
        )

    def delete(self, *, key_item_ref: str, key_version_ref: str) -> str:
        response = self._invoke(
            "delete", key_item_ref=key_item_ref, key_version_ref=key_version_ref
        )
        return response.helper_receipt_ref

    def readiness(self) -> tuple[str, tuple[str, ...]]:
        if sys.platform != "darwin":
            return "unsupported", ("reason-ref:matrix-cache:macos-required",)
        try:
            response = self._invoke("version")
        except (FileNotFoundError, MacOSMatrixCacheCryptoError):
            return "blocked", ("reason-ref:matrix-cache:helper-unavailable",)
        if response.operation != "version":
            return "blocked", ("reason-ref:matrix-cache:helper-protocol-invalid",)
        return "ready", ("reason-ref:matrix-cache:helper-ready",)

    def _crypto(
        self,
        operation: Literal["encrypt", "decrypt"],
        *,
        key_item_ref: str,
        key_version_ref: str,
        payload: bytes,
        aad: bytes,
    ) -> bytes:
        response = self._invoke(
            operation,
            key_item_ref=key_item_ref,
            key_version_ref=key_version_ref,
            payload_base64url=_encode_base64url(payload),
            aad_base64url=_encode_base64url(aad),
        )
        assert response.payload_base64url is not None
        output = _decode_base64url(
            response.payload_base64url,
            maximum=17 * 1024 * 1024,
        )
        expected = f"matrix-cache-helper-payload-fingerprint-ref:sha256:{hashlib.sha256(output).hexdigest()}"
        if response.payload_fingerprint_ref != expected:
            raise MacOSMatrixCacheCryptoError(
                "MATRIX_CACHE_HELPER_PAYLOAD_FINGERPRINT_INVALID"
            )
        return output

    def _invoke(self, operation: str, **payload: Any) -> _HelperResponse:
        self._require_darwin()
        request = {
            "schema_version": "uaa-matrix-protected-cache-helper-request.v1",
            "operation": operation,
            **payload,
        }
        if operation != "version":
            request["request_ref"] = (
                f"request-ref:matrix-cache-helper:{hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()}"
            )
        encoded = json.dumps(
            request, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        if len(encoded) > MACOS_MATRIX_CACHE_HELPER_MAX_INPUT_BYTES:
            raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_REQUEST_TOO_LARGE")
        descriptor, digest = self._open_validated_helper()
        try:
            with tempfile.TemporaryDirectory(prefix="uaa-matrix-cache-helper-", dir="/tmp") as temporary:
                os.chmod(temporary, 0o700)
                executable = Path(temporary) / MACOS_MATRIX_CACHE_HELPER_NAME
                target_fd = os.open(
                    executable,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL
                    | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                    0o700,
                )
                copied = hashlib.sha256()
                try:
                    while True:
                        chunk = os.read(descriptor, 65_536)
                        if not chunk:
                            break
                        copied.update(chunk)
                        if os.write(target_fd, chunk) != len(chunk):
                            raise MacOSMatrixCacheCryptoError(
                                "MATRIX_CACHE_HELPER_COPY_FAILED"
                            )
                    os.fsync(target_fd)
                finally:
                    os.close(target_fd)
                if copied.hexdigest() != digest:
                    raise MacOSMatrixCacheCryptoError(
                        "MATRIX_CACHE_HELPER_COPY_FINGERPRINT_MISMATCH"
                    )
                try:
                    completed = subprocess.run(
                        [os.fspath(executable)],
                        input=encoded,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=temporary,
                        env={"PATH": "/usr/bin:/bin", "TMPDIR": "/tmp"},
                        timeout=self._timeout_seconds,
                        check=False,
                        shell=False,
                        start_new_session=True,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise MacOSMatrixCacheCryptoError(
                        "MATRIX_CACHE_HELPER_EXECUTION_FAILED"
                    ) from exc
        finally:
            os.close(descriptor)
        if (
            len(completed.stdout) > MACOS_MATRIX_CACHE_HELPER_MAX_OUTPUT_BYTES
            or len(completed.stderr) > 4096
        ):
            raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_OUTPUT_TOO_LARGE")
        try:
            response = _HelperResponse.model_validate_json(completed.stdout)
        except ValueError as exc:
            raise MacOSMatrixCacheCryptoError(
                "MATRIX_CACHE_HELPER_RESPONSE_INVALID"
            ) from exc
        if completed.returncode != 0 or not response.ok:
            if response.error_code == "MATRIX_CACHE_HELPER_KEYCHAIN_LOCKED":
                raise MatrixCacheKeyUnavailable("MATRIX_CACHE_KEY_BACKEND_LOCKED")
            if response.error_code == "MATRIX_CACHE_HELPER_KEY_NOT_FOUND":
                raise MatrixCacheKeyUnavailable("MATRIX_CACHE_KEY_NOT_FOUND")
            raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_OPERATION_FAILED")
        if response.operation != operation:
            raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_OPERATION_MISMATCH")
        return response

    def _open_validated_helper(self) -> tuple[int, str]:
        metadata = os.lstat(self._helper_path)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size < 1
            or metadata.st_size > MACOS_MATRIX_CACHE_HELPER_MAX_EXECUTABLE_BYTES
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o022
            or not metadata.st_mode & stat.S_IXUSR
        ):
            raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_FILE_UNTRUSTED")
        descriptor = os.open(
            self._helper_path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
            ):
                raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_FILE_CHANGED")
            hasher = hashlib.sha256()
            while chunk := os.read(descriptor, 65_536):
                hasher.update(chunk)
        except Exception:
            os.close(descriptor)
            raise
        actual = hasher.hexdigest()
        if actual != self._expected_helper_sha256:
            os.close(descriptor)
            raise MacOSMatrixCacheCryptoError(
                "MATRIX_CACHE_HELPER_FINGERPRINT_MISMATCH"
            )
        os.lseek(descriptor, 0, os.SEEK_SET)
        return descriptor, actual

    @staticmethod
    def _require_darwin() -> None:
        if sys.platform != "darwin":
            raise MacOSMatrixCacheCryptoError("MATRIX_CACHE_HELPER_MACOS_REQUIRED")
