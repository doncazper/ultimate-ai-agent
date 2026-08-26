"""Opaque-key encryption boundary for FIN-001 protected local repositories."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from enum import Enum
from pathlib import Path
from typing import Literal, Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.communications.matrix_sync.macos_cache_crypto import (
    MACOS_MATRIX_CACHE_HELPER_VERSION_REF,
    MacOSMatrixCacheCryptoBackend,
)


FINANCE_CRYPTO_DOMAIN = b"uaa:finance-protected-repository:aes256gcm:v1\x00"
FINANCE_CRYPTO_ADAPTER_REF = "adapter-ref:finance-protected-crypto:v1"
FINANCE_KEYCHAIN_ADAPTER_REF = "adapter-ref:finance-keychain:macos:v1"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode_b64url(value: str) -> bytes:
    if not value or any(
        character
        not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
        for character in value
    ):
        raise ValueError("FINANCE_CRYPTO_BASE64URL_INVALID")
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


def finance_crypto_aad(*, key_handle_ref: str, context_ref: str) -> bytes:
    validate_task_ref(key_handle_ref, "finance_key_handle_ref")
    validate_task_ref(context_ref, "finance_crypto_context_ref")
    return FINANCE_CRYPTO_DOMAIN + json.dumps(
        {"context_ref": context_ref, "key_handle_ref": key_handle_ref},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class FinanceCryptoStatus(str, Enum):
    ready = "ready"
    unavailable = "unavailable"
    key_unavailable = "key_unavailable"
    helper_missing = "helper_missing"
    helper_untrusted = "helper_untrusted"
    unsupported_platform = "unsupported_platform"


class FinanceCryptoReadiness(BaseModel):
    schema_version: Literal["uaa-finance-crypto-readiness.v1"] = (
        "uaa-finance-crypto-readiness.v1"
    )
    adapter_ref: str
    status: FinanceCryptoStatus
    reason_refs: tuple[str, ...] = Field(default=(), max_length=16)
    helper_version_ref: str | None = None
    helper_fingerprint_ref: str | None = None
    key_material_included: Literal[False] = False
    persistent_plaintext_allowed: Literal[False] = False
    synchronizing_keychain_allowed: Literal[False] = False
    production_authority_granted: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=True)

    @model_validator(mode="after")
    def validate_readiness(self) -> "FinanceCryptoReadiness":
        for value in (
            self.adapter_ref,
            *self.reason_refs,
            self.helper_version_ref,
            self.helper_fingerprint_ref,
        ):
            if value is not None:
                validate_task_ref(value, "finance_crypto_readiness_ref")
        return self


class FinanceKeyReceipt(BaseModel):
    schema_version: Literal["uaa-finance-key-receipt.v1"] = "uaa-finance-key-receipt.v1"
    operation: Literal["create", "probe", "delete"]
    key_handle_ref: str
    key_version_ref: str
    receipt_ref: str
    present: bool
    created: bool | None = None
    deleted_or_absent: bool | None = None
    key_material_included: Literal[False] = False
    key_material_returned: Literal[False] = False
    synchronizing_keychain_used: Literal[False] = False

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_receipt(self) -> "FinanceKeyReceipt":
        for value in (self.key_handle_ref, self.key_version_ref, self.receipt_ref):
            validate_task_ref(value, "finance_key_receipt_ref")
        if self.operation == "create" and not (self.created and self.present):
            raise ValueError("FINANCE_KEY_CREATE_RECEIPT_INVALID")
        if self.operation == "probe" and (self.created is not None or not self.present):
            raise ValueError("FINANCE_KEY_PROBE_RECEIPT_INVALID")
        if self.operation == "delete" and not (
            self.deleted_or_absent and not self.present and self.created is None
        ):
            raise ValueError("FINANCE_KEY_DELETE_RECEIPT_INVALID")
        return self


class FinanceCryptoBackend(Protocol):
    adapter_ref: str

    def readiness(self) -> FinanceCryptoReadiness: ...

    def create_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt: ...

    def probe_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt: ...

    def seal(
        self,
        *,
        key_handle_ref: str,
        key_version_ref: str,
        context_ref: str,
        request_ref: str,
        plaintext: bytes,
    ) -> bytes: ...

    def open(
        self,
        *,
        key_handle_ref: str,
        key_version_ref: str,
        context_ref: str,
        request_ref: str,
        ciphertext: bytes,
    ) -> bytes: ...

    def delete_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt: ...


class InMemoryFinanceCryptoBackend:
    """Test-only opaque-key backend; secrets never enter models or receipts."""

    adapter_ref = "adapter-ref:finance-protected-crypto:memory-test-only:v1"

    def __init__(self) -> None:
        self._keys: dict[tuple[str, str], bytes] = {}

    def readiness(self) -> FinanceCryptoReadiness:
        return FinanceCryptoReadiness(
            adapter_ref=self.adapter_ref,
            status=FinanceCryptoStatus.ready,
            reason_refs=("reason-ref:finance-crypto:test-only-ready",),
        )

    def create_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        key = (key_handle_ref, key_version_ref)
        if key in self._keys:
            raise RuntimeError("FINANCE_KEY_ALREADY_EXISTS")
        self._keys[key] = AESGCM.generate_key(bit_length=256)
        return self._receipt(
            "create",
            key_handle_ref,
            key_version_ref,
            request_ref,
            present=True,
            created=True,
        )

    def probe_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        if (key_handle_ref, key_version_ref) not in self._keys:
            raise RuntimeError("FINANCE_KEY_UNAVAILABLE")
        return self._receipt(
            "probe",
            key_handle_ref,
            key_version_ref,
            request_ref,
            present=True,
        )

    def seal(
        self,
        *,
        key_handle_ref: str,
        key_version_ref: str,
        context_ref: str,
        request_ref: str,
        plaintext: bytes,
    ) -> bytes:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        key = self._require_key(key_handle_ref, key_version_ref)
        nonce = os.urandom(12)
        encrypted = AESGCM(key).encrypt(
            nonce,
            plaintext,
            finance_crypto_aad(
                key_handle_ref=key_handle_ref,
                context_ref=context_ref,
            ),
        )
        return b"UAAFIN1\x00" + nonce + encrypted

    def open(
        self,
        *,
        key_handle_ref: str,
        key_version_ref: str,
        context_ref: str,
        request_ref: str,
        ciphertext: bytes,
    ) -> bytes:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        if not ciphertext.startswith(b"UAAFIN1\x00") or len(ciphertext) < 36:
            raise RuntimeError("FINANCE_CIPHERTEXT_INVALID")
        key = self._require_key(key_handle_ref, key_version_ref)
        nonce = ciphertext[8:20]
        return AESGCM(key).decrypt(
            nonce,
            ciphertext[20:],
            finance_crypto_aad(
                key_handle_ref=key_handle_ref,
                context_ref=context_ref,
            ),
        )

    def delete_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        self._keys.pop((key_handle_ref, key_version_ref), None)
        return self._receipt(
            "delete",
            key_handle_ref,
            key_version_ref,
            request_ref,
            present=False,
            deleted_or_absent=True,
        )

    def _require_key(self, key_handle_ref: str, key_version_ref: str) -> bytes:
        try:
            return self._keys[(key_handle_ref, key_version_ref)]
        except KeyError:
            raise RuntimeError("FINANCE_KEY_UNAVAILABLE") from None

    @staticmethod
    def _validate_scope(
        key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> None:
        validate_task_ref(key_handle_ref, "finance_key_handle_ref")
        validate_task_ref(key_version_ref, "finance_key_version_ref")
        validate_task_ref(request_ref, "finance_crypto_request_ref")

    @staticmethod
    def _receipt(
        operation: Literal["create", "probe", "delete"],
        key_handle_ref: str,
        key_version_ref: str,
        request_ref: str,
        *,
        present: bool,
        created: bool | None = None,
        deleted_or_absent: bool | None = None,
    ) -> FinanceKeyReceipt:
        digest = hashlib.sha256(
            "\0".join((operation, key_handle_ref, key_version_ref, request_ref)).encode(
                "utf-8"
            )
        ).hexdigest()
        return FinanceKeyReceipt(
            operation=operation,
            key_handle_ref=key_handle_ref,
            key_version_ref=key_version_ref,
            receipt_ref=f"key-receipt-ref:finance:sha256:{digest}",
            present=present,
            created=created,
            deleted_or_absent=deleted_or_absent,
        )


class MacOSFinanceCryptoBackend:
    """Finance-scoped facade over the pinned opaque macOS Keychain crypto helper.

    The shared native helper never returns key material. Finance uses dedicated
    content-derived key handles and Finance-specific AAD, so its items and
    ciphertexts cannot be substituted into the Matrix protected-cache lane.
    """

    adapter_ref = FINANCE_KEYCHAIN_ADAPTER_REF

    def __init__(
        self,
        *,
        helper_path: Path,
        expected_helper_sha256: str,
        timeout_seconds: float = 30,
    ) -> None:
        self._expected_helper_sha256 = expected_helper_sha256
        self._delegate = MacOSMatrixCacheCryptoBackend(
            helper_path=helper_path,
            expected_helper_sha256=expected_helper_sha256,
            timeout_seconds=timeout_seconds,
        )

    def readiness(self) -> FinanceCryptoReadiness:
        status, _reasons = self._delegate.readiness()
        if status == "ready":
            return FinanceCryptoReadiness(
                adapter_ref=self.adapter_ref,
                status=FinanceCryptoStatus.ready,
                reason_refs=("reason-ref:finance-crypto:keychain-helper-ready",),
                helper_version_ref=MACOS_MATRIX_CACHE_HELPER_VERSION_REF,
                helper_fingerprint_ref=(
                    "helper-fingerprint-ref:finance-keychain:sha256:"
                    f"{self._expected_helper_sha256}"
                ),
            )
        mapped = (
            FinanceCryptoStatus.unsupported_platform
            if status == "unsupported"
            else FinanceCryptoStatus.helper_untrusted
        )
        return FinanceCryptoReadiness(
            adapter_ref=self.adapter_ref,
            status=mapped,
            reason_refs=("reason-ref:finance-crypto:keychain-helper-unavailable",),
        )

    def create_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        helper_receipt_ref = self._delegate.create(
            key_item_ref=key_handle_ref,
            key_version_ref=key_version_ref,
        )
        return self._receipt(
            operation="create",
            key_handle_ref=key_handle_ref,
            key_version_ref=key_version_ref,
            request_ref=request_ref,
            helper_receipt_ref=helper_receipt_ref,
            present=True,
            created=True,
        )

    def probe_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        helper_receipt_ref = self._delegate.probe(
            key_item_ref=key_handle_ref,
            key_version_ref=key_version_ref,
        )
        return self._receipt(
            operation="probe",
            key_handle_ref=key_handle_ref,
            key_version_ref=key_version_ref,
            request_ref=request_ref,
            helper_receipt_ref=helper_receipt_ref,
            present=True,
        )

    def seal(
        self,
        *,
        key_handle_ref: str,
        key_version_ref: str,
        context_ref: str,
        request_ref: str,
        plaintext: bytes,
    ) -> bytes:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        return self._delegate.encrypt(
            key_item_ref=key_handle_ref,
            key_version_ref=key_version_ref,
            plaintext=plaintext,
            aad=finance_crypto_aad(
                key_handle_ref=key_handle_ref,
                context_ref=context_ref,
            ),
        )

    def open(
        self,
        *,
        key_handle_ref: str,
        key_version_ref: str,
        context_ref: str,
        request_ref: str,
        ciphertext: bytes,
    ) -> bytes:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        return self._delegate.decrypt(
            key_item_ref=key_handle_ref,
            key_version_ref=key_version_ref,
            ciphertext=ciphertext,
            aad=finance_crypto_aad(
                key_handle_ref=key_handle_ref,
                context_ref=context_ref,
            ),
        )

    def delete_key(
        self, *, key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> FinanceKeyReceipt:
        self._validate_scope(key_handle_ref, key_version_ref, request_ref)
        helper_receipt_ref = self._delegate.delete(
            key_item_ref=key_handle_ref,
            key_version_ref=key_version_ref,
        )
        return self._receipt(
            operation="delete",
            key_handle_ref=key_handle_ref,
            key_version_ref=key_version_ref,
            request_ref=request_ref,
            helper_receipt_ref=helper_receipt_ref,
            present=False,
            deleted_or_absent=True,
        )

    @staticmethod
    def _validate_scope(
        key_handle_ref: str, key_version_ref: str, request_ref: str
    ) -> None:
        for value, label in (
            (key_handle_ref, "finance_key_handle_ref"),
            (key_version_ref, "finance_key_version_ref"),
            (request_ref, "finance_crypto_request_ref"),
        ):
            validate_task_ref(value, label)

    @staticmethod
    def _receipt(
        *,
        operation: Literal["create", "probe", "delete"],
        key_handle_ref: str,
        key_version_ref: str,
        request_ref: str,
        helper_receipt_ref: str,
        present: bool,
        created: bool | None = None,
        deleted_or_absent: bool | None = None,
    ) -> FinanceKeyReceipt:
        payload = "\0".join(
            (
                operation,
                key_handle_ref,
                key_version_ref,
                request_ref,
                helper_receipt_ref,
            )
        ).encode("utf-8")
        return FinanceKeyReceipt(
            operation=operation,
            key_handle_ref=key_handle_ref,
            key_version_ref=key_version_ref,
            receipt_ref=(
                "key-receipt-ref:finance-keychain:sha256:"
                f"{hashlib.sha256(payload).hexdigest()}"
            ),
            present=present,
            created=created,
            deleted_or_absent=deleted_or_absent,
        )


class UnavailableFinanceCryptoBackend:
    adapter_ref = "adapter-ref:finance-protected-crypto:unavailable:v1"

    def readiness(self) -> FinanceCryptoReadiness:
        return FinanceCryptoReadiness(
            adapter_ref=self.adapter_ref,
            status=FinanceCryptoStatus.unavailable,
            reason_refs=("reason-ref:finance-crypto:backend-unavailable",),
        )

    def __getattr__(self, _name: str) -> object:
        raise RuntimeError("FINANCE_CRYPTO_BACKEND_UNAVAILABLE")


def ciphertext_ref(ciphertext: bytes) -> str:
    return f"ciphertext-ref:finance:sha256:{hashlib.sha256(ciphertext).hexdigest()}"


def encode_crypto_payload(payload: bytes) -> str:
    return _b64url(payload)


def decode_crypto_payload(payload: str) -> bytes:
    return _decode_b64url(payload)
