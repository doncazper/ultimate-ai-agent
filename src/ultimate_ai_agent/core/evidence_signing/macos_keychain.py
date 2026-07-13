from __future__ import annotations

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

from ultimate_ai_agent.core.evidence_signing.backend import (
    PortableEvidenceSigningBackendDeletion,
    PortableEvidenceSigningBackendPublicKey,
    PortableEvidenceSigningBackendReadiness,
    PortableEvidenceSigningBackendSignature,
    PortableEvidenceSigningBackendStatus,
)
from ultimate_ai_agent.core.evidence_signing.portable import (
    PORTABLE_EVIDENCE_SIGNING_DOMAIN,
    _decode_base64url,
    _encode_base64url,
    _stable_ref,
    ed25519_public_key_fingerprint_ref,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref


MACOS_KEYCHAIN_ADAPTER_REF = "adapter-ref:portable-evidence-signing:macos-keychain:v1"
MACOS_KEYCHAIN_HELPER_VERSION_REF = "helper-version-ref:portable-evidence-keychain:v1"
MACOS_KEYCHAIN_HELPER_MAX_INPUT_BYTES = 8 * 1024 * 1024
MACOS_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES = 32 * 1024
MACOS_KEYCHAIN_HELPER_MAX_EXECUTABLE_BYTES = 32 * 1024 * 1024
MACOS_KEYCHAIN_HELPER_INSTALL_METADATA_MAX_BYTES = 16 * 1024
MACOS_KEYCHAIN_HELPER_NAME = "uaa-portable-evidence-keychain-helper"
MACOS_KEYCHAIN_HELPER_METADATA_NAME = "portable-evidence-keychain-helper.json"


class MacOSKeychainSigningBackendError(RuntimeError):
    pass


class _HelperResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["uaa-portable-evidence-keychain-helper-response.v1"] = (
        "uaa-portable-evidence-keychain-helper-response.v1"
    )
    ok: StrictBool
    operation: Literal["version", "create", "probe", "sign", "delete", "unknown"]
    adapter_ref: Literal["adapter-ref:portable-evidence-signing:macos-keychain:v1"] = (
        MACOS_KEYCHAIN_ADAPTER_REF
    )
    helper_version: str = Field(..., min_length=1, max_length=32)
    helper_version_ref: Literal["helper-version-ref:portable-evidence-keychain:v1"] = (
        MACOS_KEYCHAIN_HELPER_VERSION_REF
    )
    key_ref: str | None = None
    key_version_ref: str | None = None
    public_key_base64url: str | None = None
    public_key_fingerprint_ref: str | None = None
    signature_base64url: str | None = None
    signature_ref: str | None = None
    helper_receipt_ref: str
    created: StrictBool | None = None
    deleted_or_absent: StrictBool | None = None
    error_code: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validate_response(self) -> "_HelperResponse":
        for name, value in self.model_dump(mode="python").items():
            if name.endswith("_ref") and value is not None:
                validate_task_ref(str(value), f"portable_evidence_helper_{name}")
        if self.ok and self.error_code is not None:
            raise ValueError("PORTABLE_EVIDENCE_HELPER_ERROR_CODE_DENIED")
        if not self.ok and not self.error_code:
            raise ValueError("PORTABLE_EVIDENCE_HELPER_ERROR_CODE_REQUIRED")
        if self.operation in {"create", "probe"} and self.ok:
            if not all(
                (
                    self.key_ref,
                    self.key_version_ref,
                    self.public_key_base64url,
                    self.public_key_fingerprint_ref,
                    self.created is not None,
                )
            ):
                raise ValueError("PORTABLE_EVIDENCE_HELPER_CREATE_RESPONSE_INVALID")
        if self.operation == "sign" and self.ok:
            if not all(
                (
                    self.key_ref,
                    self.key_version_ref,
                    self.signature_base64url,
                    self.signature_ref,
                )
            ):
                raise ValueError("PORTABLE_EVIDENCE_HELPER_SIGN_RESPONSE_INVALID")
        if self.operation == "delete" and self.ok:
            if self.deleted_or_absent is not True:
                raise ValueError("PORTABLE_EVIDENCE_HELPER_DELETE_RESPONSE_INVALID")
        return self


class MacOSKeychainPortableEvidenceSigningBackend:
    adapter_ref = MACOS_KEYCHAIN_ADAPTER_REF

    def __init__(
        self,
        *,
        helper_path: str | Path,
        expected_helper_sha256: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._helper_path = Path(helper_path)
        if len(expected_helper_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in expected_helper_sha256
        ):
            raise ValueError("PORTABLE_EVIDENCE_HELPER_SHA256_INVALID")
        self._expected_helper_sha256 = expected_helper_sha256
        self.binding_ref = _stable_ref(
            "backend-binding-ref:portable-evidence-signing:macos-keychain",
            {
                "adapter_ref": self.adapter_ref,
                "expected_helper_sha256": expected_helper_sha256,
                "helper_version_ref": MACOS_KEYCHAIN_HELPER_VERSION_REF,
            },
        )
        self._timeout_seconds = max(1.0, min(float(timeout_seconds), 60.0))

    def readiness(self) -> PortableEvidenceSigningBackendReadiness:
        if sys.platform != "darwin":
            return PortableEvidenceSigningBackendReadiness(
                adapter_ref=self.adapter_ref,
                status=PortableEvidenceSigningBackendStatus.unsupported_platform,
                reason_refs=("reason-ref:portable-evidence-signing:macos-required",),
            )
        try:
            helper_hash = self._validate_helper()
            response = self._invoke({"operation": "version"})
        except FileNotFoundError:
            return PortableEvidenceSigningBackendReadiness(
                adapter_ref=self.adapter_ref,
                status=PortableEvidenceSigningBackendStatus.helper_missing,
                reason_refs=("reason-ref:portable-evidence-signing:helper-missing",),
            )
        except MacOSKeychainSigningBackendError:
            return PortableEvidenceSigningBackendReadiness(
                adapter_ref=self.adapter_ref,
                status=PortableEvidenceSigningBackendStatus.helper_untrusted,
                reason_refs=("reason-ref:portable-evidence-signing:helper-untrusted",),
            )
        if response.operation != "version":
            return PortableEvidenceSigningBackendReadiness(
                adapter_ref=self.adapter_ref,
                status=PortableEvidenceSigningBackendStatus.helper_untrusted,
                reason_refs=(
                    "reason-ref:portable-evidence-signing:helper-protocol-mismatch",
                ),
            )
        return PortableEvidenceSigningBackendReadiness(
            adapter_ref=self.adapter_ref,
            status=PortableEvidenceSigningBackendStatus.ready,
            helper_version_ref=response.helper_version_ref,
            helper_fingerprint_ref=(f"helper-fingerprint-ref:sha256:{helper_hash}"),
            reason_refs=("reason-ref:portable-evidence-signing:helper-ready",),
        )

    def create_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendPublicKey:
        self._require_darwin()
        response = self._invoke(
            {
                "operation": "create",
                "key_ref": key_ref,
                "key_version_ref": key_version_ref,
                "request_ref": request_ref,
            }
        )
        if response.operation != "create" or not response.ok:
            self._raise_helper_failure(response)
        assert response.public_key_base64url is not None
        assert response.public_key_fingerprint_ref is not None
        assert response.key_ref is not None
        assert response.key_version_ref is not None
        assert response.created is not None
        public_key = _decode_base64url(
            response.public_key_base64url,
            expected_bytes=32,
        )
        if response.public_key_fingerprint_ref != ed25519_public_key_fingerprint_ref(
            public_key
        ):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_PUBLIC_KEY_FINGERPRINT_INVALID"
            )
        if (response.key_ref, response.key_version_ref) != (key_ref, key_version_ref):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_KEY_BINDING_MISMATCH"
            )
        return PortableEvidenceSigningBackendPublicKey(
            adapter_ref=self.adapter_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            public_key_base64url=response.public_key_base64url,
            public_key_fingerprint_ref=response.public_key_fingerprint_ref,
            helper_receipt_ref=response.helper_receipt_ref,
            created=response.created,
        )

    def probe_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendPublicKey:
        self._require_darwin()
        response = self._invoke(
            {
                "operation": "probe",
                "key_ref": key_ref,
                "key_version_ref": key_version_ref,
                "request_ref": request_ref,
            }
        )
        if response.operation != "probe" or not response.ok:
            self._raise_helper_failure(response)
        assert response.public_key_base64url is not None
        assert response.public_key_fingerprint_ref is not None
        assert response.key_ref is not None
        assert response.key_version_ref is not None
        if (response.key_ref, response.key_version_ref) != (key_ref, key_version_ref):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_KEY_BINDING_MISMATCH"
            )
        public_key = _decode_base64url(
            response.public_key_base64url,
            expected_bytes=32,
        )
        if response.public_key_fingerprint_ref != ed25519_public_key_fingerprint_ref(
            public_key
        ):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_PUBLIC_KEY_FINGERPRINT_INVALID"
            )
        return PortableEvidenceSigningBackendPublicKey(
            adapter_ref=self.adapter_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            public_key_base64url=response.public_key_base64url,
            public_key_fingerprint_ref=response.public_key_fingerprint_ref,
            helper_receipt_ref=response.helper_receipt_ref,
            created=False,
        )

    def sign(
        self,
        *,
        key_ref: str,
        key_version_ref: str,
        request_ref: str,
        payload: bytes,
    ) -> PortableEvidenceSigningBackendSignature:
        self._require_darwin()
        if len(payload) > MACOS_KEYCHAIN_HELPER_MAX_INPUT_BYTES:
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_PAYLOAD_TOO_LARGE"
            )
        if not payload.startswith(PORTABLE_EVIDENCE_SIGNING_DOMAIN):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_SIGNING_DOMAIN_REQUIRED"
            )
        response = self._invoke(
            {
                "operation": "sign",
                "key_ref": key_ref,
                "key_version_ref": key_version_ref,
                "request_ref": request_ref,
                "payload_base64url": _encode_base64url(payload),
            }
        )
        if response.operation != "sign" or not response.ok:
            self._raise_helper_failure(response)
        assert response.signature_base64url is not None
        assert response.key_ref is not None
        assert response.key_version_ref is not None
        if (response.key_ref, response.key_version_ref) != (key_ref, key_version_ref):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_KEY_BINDING_MISMATCH"
            )
        signature = _decode_base64url(
            response.signature_base64url,
            expected_bytes=64,
        )
        signature_ref = _stable_ref("portable-evidence-signature-ref", signature.hex())
        if response.signature_ref != signature_ref:
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_SIGNATURE_REF_INVALID"
            )
        return PortableEvidenceSigningBackendSignature(
            adapter_ref=self.adapter_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            request_ref=request_ref,
            signature_base64url=response.signature_base64url,
            signature_ref=signature_ref,
            helper_receipt_ref=response.helper_receipt_ref,
        )

    def delete_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendDeletion:
        self._require_darwin()
        response = self._invoke(
            {
                "operation": "delete",
                "key_ref": key_ref,
                "key_version_ref": key_version_ref,
                "request_ref": request_ref,
            }
        )
        if response.operation != "delete" or not response.ok:
            self._raise_helper_failure(response)
        if (response.key_ref, response.key_version_ref) != (key_ref, key_version_ref):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_KEY_BINDING_MISMATCH"
            )
        return PortableEvidenceSigningBackendDeletion(
            adapter_ref=self.adapter_ref,
            key_ref=key_ref,
            key_version_ref=key_version_ref,
            helper_receipt_ref=response.helper_receipt_ref,
        )

    def _invoke(self, payload: dict[str, Any]) -> _HelperResponse:
        self._require_darwin()
        request = {
            "schema_version": "uaa-portable-evidence-keychain-helper-request.v1",
            **payload,
        }
        encoded = json.dumps(
            request, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        if len(encoded) > MACOS_KEYCHAIN_HELPER_MAX_INPUT_BYTES:
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_REQUEST_TOO_LARGE"
            )
        descriptor, expected_digest = self._open_validated_helper()
        try:
            with tempfile.TemporaryDirectory(
                prefix="uaa-evidence-helper-exec-",
                dir="/tmp",
            ) as temporary_dir:
                os.chmod(temporary_dir, 0o700)
                executable = Path(temporary_dir) / MACOS_KEYCHAIN_HELPER_NAME
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
                            raise MacOSKeychainSigningBackendError(
                                "PORTABLE_EVIDENCE_HELPER_COPY_SHORT_WRITE"
                            )
                    os.fsync(copy_descriptor)
                finally:
                    os.close(copy_descriptor)
                if copied_digest.hexdigest() != expected_digest:
                    raise MacOSKeychainSigningBackendError(
                        "PORTABLE_EVIDENCE_HELPER_COPY_FINGERPRINT_MISMATCH"
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
                    raise MacOSKeychainSigningBackendError(
                        "PORTABLE_EVIDENCE_HELPER_EXECUTION_FAILED"
                    ) from exc
        finally:
            os.close(descriptor)
        if (
            len(completed.stdout) > MACOS_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES
            or len(completed.stderr) > MACOS_KEYCHAIN_HELPER_MAX_OUTPUT_BYTES
        ):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_OUTPUT_TOO_LARGE"
            )
        try:
            response = _HelperResponse.model_validate_json(completed.stdout)
        except ValueError as exc:
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_RESPONSE_INVALID"
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
            or metadata.st_size > MACOS_KEYCHAIN_HELPER_MAX_EXECUTABLE_BYTES
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o022
            or not metadata.st_mode & stat.S_IXUSR
        ):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_FILE_UNTRUSTED"
            )
        descriptor = os.open(
            self._helper_path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or opened.st_size < 1
                or opened.st_size > MACOS_KEYCHAIN_HELPER_MAX_EXECUTABLE_BYTES
                or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
            ):
                raise MacOSKeychainSigningBackendError(
                    "PORTABLE_EVIDENCE_HELPER_FILE_CHANGED"
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
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_FINGERPRINT_MISMATCH"
            )
        os.lseek(descriptor, 0, os.SEEK_SET)
        return descriptor, actual

    @staticmethod
    def _raise_helper_failure(response: _HelperResponse) -> None:
        if response.error_code == "HELPER_KEYCHAIN_LOCKED":
            raise MacOSKeychainSigningBackendError("PORTABLE_EVIDENCE_KEYCHAIN_LOCKED")
        if response.error_code == "HELPER_KEY_NOT_FOUND":
            raise MacOSKeychainSigningBackendError("PORTABLE_EVIDENCE_KEY_NOT_FOUND")
        raise MacOSKeychainSigningBackendError(
            "PORTABLE_EVIDENCE_HELPER_OPERATION_FAILED"
        )

    @staticmethod
    def _require_darwin() -> None:
        if sys.platform != "darwin":
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_SIGNING_UNSUPPORTED_PLATFORM"
            )


def load_installed_macos_keychain_signing_backend(
    install_root: str | Path | None = None,
) -> MacOSKeychainPortableEvidenceSigningBackend:
    root = (
        Path(install_root)
        if install_root is not None
        else Path.home() / ".local" / "share" / "uaa" / "helpers"
    )
    root_metadata = os.lstat(root)
    if (
        not stat.S_ISDIR(root_metadata.st_mode)
        or stat.S_ISLNK(root_metadata.st_mode)
        or root_metadata.st_uid != os.getuid()
        or root_metadata.st_mode & 0o022
    ):
        raise MacOSKeychainSigningBackendError(
            "PORTABLE_EVIDENCE_HELPER_INSTALL_ROOT_UNTRUSTED"
        )
    metadata_path = root / MACOS_KEYCHAIN_HELPER_METADATA_NAME
    descriptor = os.open(
        metadata_path,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0),
    )
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
            or metadata.st_size > MACOS_KEYCHAIN_HELPER_INSTALL_METADATA_MAX_BYTES
        ):
            raise MacOSKeychainSigningBackendError(
                "PORTABLE_EVIDENCE_HELPER_METADATA_UNTRUSTED"
            )
        raw = os.read(
            descriptor,
            MACOS_KEYCHAIN_HELPER_INSTALL_METADATA_MAX_BYTES + 1,
        )
    finally:
        os.close(descriptor)
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MacOSKeychainSigningBackendError(
            "PORTABLE_EVIDENCE_HELPER_METADATA_INVALID"
        ) from exc
    expected_keys = {
        "schema_version",
        "helper_ref",
        "helper_version_ref",
        "helper_fingerprint_ref",
        "platform_ref",
        "private_key_included",
        "absolute_path_included",
        "execution_authority_granted",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) != expected_keys
        or payload.get("schema_version")
        != "uaa-portable-evidence-keychain-helper-install.v1"
        or payload.get("helper_ref") != "helper-ref:portable-evidence-keychain:v1"
        or payload.get("helper_version_ref") != MACOS_KEYCHAIN_HELPER_VERSION_REF
        or payload.get("private_key_included") is not False
        or payload.get("absolute_path_included") is not False
        or payload.get("execution_authority_granted") is not False
    ):
        raise MacOSKeychainSigningBackendError(
            "PORTABLE_EVIDENCE_HELPER_METADATA_INVALID"
        )
    fingerprint = payload.get("helper_fingerprint_ref")
    prefix = "helper-fingerprint-ref:sha256:"
    if not isinstance(fingerprint, str) or not fingerprint.startswith(prefix):
        raise MacOSKeychainSigningBackendError(
            "PORTABLE_EVIDENCE_HELPER_METADATA_FINGERPRINT_INVALID"
        )
    return MacOSKeychainPortableEvidenceSigningBackend(
        helper_path=root / MACOS_KEYCHAIN_HELPER_NAME,
        expected_helper_sha256=fingerprint.removeprefix(prefix),
    )
