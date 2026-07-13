from __future__ import annotations

from enum import Enum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.planning.validation import validate_task_ref


class PortableEvidenceSigningBackendStatus(str, Enum):
    ready = "ready"
    locked = "locked"
    helper_missing = "helper_missing"
    helper_untrusted = "helper_untrusted"
    unsupported_platform = "unsupported_platform"
    unavailable = "unavailable"
    unknown = "unknown"


class _BackendModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )


class PortableEvidenceSigningBackendReadiness(_BackendModel):
    schema_version: Literal["uaa-portable-evidence-signing-backend-readiness.v1"] = (
        "uaa-portable-evidence-signing-backend-readiness.v1"
    )
    adapter_ref: str
    status: PortableEvidenceSigningBackendStatus
    helper_version_ref: str | None = None
    helper_fingerprint_ref: str | None = None
    reason_refs: tuple[str, ...] = Field(default=(), max_length=16)
    private_key_export_supported: Literal[False] = False
    secure_enclave_claimed: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_readiness(self) -> "PortableEvidenceSigningBackendReadiness":
        _validate_refs(self.model_dump(mode="python"))
        return self


class PortableEvidenceSigningBackendPublicKey(_BackendModel):
    schema_version: Literal["uaa-portable-evidence-signing-backend-public-key.v1"] = (
        "uaa-portable-evidence-signing-backend-public-key.v1"
    )
    adapter_ref: str
    key_ref: str
    key_version_ref: str
    public_key_base64url: str = Field(..., min_length=43, max_length=43)
    public_key_fingerprint_ref: str
    helper_receipt_ref: str
    created: StrictBool
    private_key_included: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_public_key(self) -> "PortableEvidenceSigningBackendPublicKey":
        _validate_refs(self.model_dump(mode="python"))
        return self


class PortableEvidenceSigningBackendSignature(_BackendModel):
    schema_version: Literal["uaa-portable-evidence-signing-backend-signature.v1"] = (
        "uaa-portable-evidence-signing-backend-signature.v1"
    )
    adapter_ref: str
    key_ref: str
    key_version_ref: str
    request_ref: str
    signature_base64url: str = Field(..., min_length=86, max_length=86)
    signature_ref: str
    helper_receipt_ref: str
    private_key_included: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_signature(self) -> "PortableEvidenceSigningBackendSignature":
        _validate_refs(self.model_dump(mode="python"))
        return self


class PortableEvidenceSigningBackendDeletion(_BackendModel):
    schema_version: Literal["uaa-portable-evidence-signing-backend-deletion.v1"] = (
        "uaa-portable-evidence-signing-backend-deletion.v1"
    )
    adapter_ref: str
    key_ref: str
    key_version_ref: str
    helper_receipt_ref: str
    deleted_or_absent: Literal[True] = True
    private_key_included: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_deletion(self) -> "PortableEvidenceSigningBackendDeletion":
        _validate_refs(self.model_dump(mode="python"))
        return self


class PortableEvidenceSigningKeyBackend(Protocol):
    @property
    def adapter_ref(self) -> str: ...

    @property
    def binding_ref(self) -> str: ...

    def readiness(self) -> PortableEvidenceSigningBackendReadiness: ...

    def create_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendPublicKey: ...

    def probe_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendPublicKey: ...

    def sign(
        self,
        *,
        key_ref: str,
        key_version_ref: str,
        request_ref: str,
        payload: bytes,
    ) -> PortableEvidenceSigningBackendSignature: ...

    def delete_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendDeletion: ...


class UnavailablePortableEvidenceSigningBackend:
    adapter_ref = "adapter-ref:portable-evidence-signing:unavailable"
    binding_ref = "backend-binding-ref:portable-evidence-signing:unavailable"

    def readiness(self) -> PortableEvidenceSigningBackendReadiness:
        return PortableEvidenceSigningBackendReadiness(
            adapter_ref=self.adapter_ref,
            status=PortableEvidenceSigningBackendStatus.unavailable,
            reason_refs=("reason-ref:portable-evidence-signing:backend-unavailable",),
        )

    def create_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendPublicKey:
        raise RuntimeError("PORTABLE_EVIDENCE_SIGNING_BACKEND_UNAVAILABLE")

    def probe_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendPublicKey:
        raise RuntimeError("PORTABLE_EVIDENCE_SIGNING_BACKEND_UNAVAILABLE")

    def sign(
        self,
        *,
        key_ref: str,
        key_version_ref: str,
        request_ref: str,
        payload: bytes,
    ) -> PortableEvidenceSigningBackendSignature:
        raise RuntimeError("PORTABLE_EVIDENCE_SIGNING_BACKEND_UNAVAILABLE")

    def delete_key(
        self, *, key_ref: str, key_version_ref: str, request_ref: str
    ) -> PortableEvidenceSigningBackendDeletion:
        raise RuntimeError("PORTABLE_EVIDENCE_SIGNING_BACKEND_UNAVAILABLE")


def _validate_refs(value: object) -> None:
    if isinstance(value, dict):
        for name, nested in value.items():
            if name.endswith("_ref") and nested is not None:
                validate_task_ref(str(nested), f"portable_evidence_backend_{name}")
            elif name.endswith("_refs"):
                for ref in nested:
                    validate_task_ref(str(ref), f"portable_evidence_backend_{name}")
            else:
                _validate_refs(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_refs(nested)
