from __future__ import annotations

import base64
import hashlib
import json
import re
from enum import Enum
from typing import Any, Literal, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from ultimate_ai_agent.core.execution.portable_mission_evidence import (
    PortableMissionEvidenceBundle,
    verify_portable_mission_evidence_bundle,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref


PORTABLE_EVIDENCE_SIGNING_DOMAIN = b"uaa:portable-mission-evidence:ed25519:v1\x00"
PORTABLE_EVIDENCE_CANONICALIZATION_REF = "canonicalization-ref:uaa-sorted-json:v1"
PORTABLE_EVIDENCE_SIGNING_ALGORITHM_REF = "signature-algorithm-ref:ed25519:rfc8032"
PORTABLE_EVIDENCE_SIGNED_MAX_BYTES = 5 * 1024 * 1024
_BASE64URL_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class PortableEvidenceKeyStatus(str, Enum):
    active = "active"
    retired = "retired"
    revoked = "revoked"
    lost = "lost"


class _SigningModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=True,
    )

    def model_copy(
        self,
        *,
        update: dict[str, Any] | None = None,
        deep: bool = False,
    ) -> "_SigningModel":
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class PortableEvidencePublicKeyRecord(_SigningModel):
    schema_version: Literal["uaa-portable-evidence-public-key.v1"] = (
        "uaa-portable-evidence-public-key.v1"
    )
    key_ref: str
    key_version_ref: str
    generation: StrictInt = Field(..., ge=1, le=1_000_000)
    status: PortableEvidenceKeyStatus
    public_key_base64url: str = Field(..., min_length=43, max_length=43)
    public_key_fingerprint_ref: str
    predecessor_key_version_ref: str | None = None
    lifecycle_receipt_ref: str
    revocation_ref: str | None = None
    private_key_included: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_record(self) -> "PortableEvidencePublicKeyRecord":
        _validate_refs(self.model_dump(mode="python"))
        public_key = _decode_base64url(self.public_key_base64url, expected_bytes=32)
        if self.public_key_fingerprint_ref != ed25519_public_key_fingerprint_ref(
            public_key
        ):
            raise ValueError("PORTABLE_EVIDENCE_PUBLIC_KEY_FINGERPRINT_INVALID")
        if self.generation == 1 and self.predecessor_key_version_ref is not None:
            raise ValueError("PORTABLE_EVIDENCE_FIRST_KEY_PREDECESSOR_DENIED")
        if self.generation > 1 and self.predecessor_key_version_ref is None:
            raise ValueError("PORTABLE_EVIDENCE_KEY_PREDECESSOR_REQUIRED")
        if self.status == PortableEvidenceKeyStatus.revoked.value:
            if self.revocation_ref is None:
                raise ValueError("PORTABLE_EVIDENCE_KEY_REVOCATION_REF_REQUIRED")
        elif self.revocation_ref is not None:
            raise ValueError("PORTABLE_EVIDENCE_KEY_REVOCATION_REF_DENIED")
        return self


class PortableEvidencePublicKeyBundle(_SigningModel):
    schema_version: Literal["uaa-portable-evidence-public-key-bundle.v1"] = (
        "uaa-portable-evidence-public-key-bundle.v1"
    )
    public_key_bundle_ref: str
    issuer_ref: str
    records: tuple[PortableEvidencePublicKeyRecord, ...] = Field(
        ..., min_length=1, max_length=1_000
    )
    previous_public_key_bundle_ref: str | None = None
    lifecycle_terminal_entry_hash_ref: str
    safe_refs_only: Literal[True] = True
    private_key_included: Literal[False] = False
    external_anchor_included: Literal[False] = False
    signer_identity_verified: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self) -> "PortableEvidencePublicKeyBundle":
        _validate_refs(self.model_dump(mode="python"))
        generations = [record.generation for record in self.records]
        if generations != list(range(1, len(generations) + 1)):
            raise ValueError("PORTABLE_EVIDENCE_PUBLIC_KEY_GENERATION_INVALID")
        versions = [record.key_version_ref for record in self.records]
        if len(versions) != len(set(versions)):
            raise ValueError("PORTABLE_EVIDENCE_PUBLIC_KEY_VERSION_DUPLICATE")
        if len({record.key_ref for record in self.records}) != 1:
            raise ValueError("PORTABLE_EVIDENCE_PUBLIC_KEY_REF_CHANGED")
        fingerprints = [record.public_key_fingerprint_ref for record in self.records]
        if len(fingerprints) != len(set(fingerprints)):
            raise ValueError("PORTABLE_EVIDENCE_PUBLIC_KEY_FINGERPRINT_DUPLICATE")
        for index, record in enumerate(self.records):
            expected_predecessor = (
                None if index == 0 else self.records[index - 1].key_version_ref
            )
            if record.predecessor_key_version_ref != expected_predecessor:
                raise ValueError("PORTABLE_EVIDENCE_PUBLIC_KEY_CONTINUITY_INVALID")
            if index < len(self.records) - 1 and record.status != "retired":
                raise ValueError("PORTABLE_EVIDENCE_PUBLIC_KEY_HISTORY_INVALID")
        active = [record for record in self.records if record.status == "active"]
        if len(active) > 1:
            raise ValueError("PORTABLE_EVIDENCE_MULTIPLE_ACTIVE_KEYS_DENIED")
        if active and active[0] != self.records[-1]:
            raise ValueError("PORTABLE_EVIDENCE_ACTIVE_KEY_MUST_BE_LATEST")
        expected = _stable_ref(
            "portable-evidence-public-key-bundle-ref",
            self.model_dump(mode="json", exclude={"public_key_bundle_ref"}),
        )
        if self.public_key_bundle_ref != expected:
            raise ValueError("PORTABLE_EVIDENCE_PUBLIC_KEY_BUNDLE_REF_INVALID")
        return self


class PortableEvidenceSigningAttestation(_SigningModel):
    schema_version: Literal["uaa-portable-evidence-signing-attestation.v1"] = (
        "uaa-portable-evidence-signing-attestation.v1"
    )
    bundle_ref: str
    bundle_digest_ref: str
    signature_algorithm_ref: Literal["signature-algorithm-ref:ed25519:rfc8032"] = (
        PORTABLE_EVIDENCE_SIGNING_ALGORITHM_REF
    )
    canonicalization_ref: Literal["canonicalization-ref:uaa-sorted-json:v1"] = (
        PORTABLE_EVIDENCE_CANONICALIZATION_REF
    )
    domain_separator_ref: Literal[
        "domain-separator-ref:uaa:portable-mission-evidence:ed25519:v1"
    ] = "domain-separator-ref:uaa:portable-mission-evidence:ed25519:v1"
    key_ref: str
    key_version_ref: str
    key_generation: StrictInt = Field(..., ge=1, le=1_000_000)
    public_key_fingerprint_ref: str
    signing_request_ref: str
    signing_receipt_ref: str
    key_management_ref: str | None = None
    managed_key_backend_attested: StrictBool = False
    source_ledgers_verified: Literal[False] = False
    signer_identity_verified: Literal[False] = False
    non_repudiation_claimed: Literal[False] = False
    execution_evidence_grants_authority: Literal[False] = False

    @model_validator(mode="after")
    def validate_attestation(self) -> "PortableEvidenceSigningAttestation":
        _validate_refs(self.model_dump(mode="python"))
        if self.managed_key_backend_attested != (self.key_management_ref is not None):
            raise ValueError("PORTABLE_EVIDENCE_KEY_MANAGEMENT_BINDING_INVALID")
        return self


class PortableEvidenceSignedArtifact(_SigningModel):
    schema_version: Literal["uaa-portable-mission-evidence-signed-artifact.v1"] = (
        "uaa-portable-mission-evidence-signed-artifact.v1"
    )
    artifact_ref: str
    unsigned_bundle: PortableMissionEvidenceBundle
    attestation: PortableEvidenceSigningAttestation
    signature_base64url: str = Field(..., min_length=86, max_length=86)
    signature_ref: str
    signature_present: Literal[True] = True
    signing_status: Literal["ed25519_signature_present"] = "ed25519_signature_present"
    managed_key_backend_attested: StrictBool = False
    cryptographic_authenticity_claimed: Literal[True] = True
    signer_identity_verified: Literal[False] = False
    external_anchor_verified: Literal[False] = False
    source_ledgers_verified: Literal[False] = False
    execution_evidence_grants_authority: Literal[False] = False
    raw_content_included: Literal[False] = False

    @model_validator(mode="after")
    def validate_artifact(self) -> "PortableEvidenceSignedArtifact":
        _validate_refs(self.model_dump(mode="python"))
        signature = _decode_base64url(self.signature_base64url, expected_bytes=64)
        if self.signature_ref != _stable_ref(
            "portable-evidence-signature-ref", signature.hex()
        ):
            raise ValueError("PORTABLE_EVIDENCE_SIGNATURE_REF_INVALID")
        canonical_bundle = _canonical_json_bytes(
            self.unsigned_bundle.model_dump(mode="json")
        )
        if self.attestation.bundle_ref != self.unsigned_bundle.bundle_ref:
            raise ValueError("PORTABLE_EVIDENCE_SIGNED_BUNDLE_REF_MISMATCH")
        if self.attestation.bundle_digest_ref != _digest_ref(
            "portable-evidence-bundle-digest-ref", canonical_bundle
        ):
            raise ValueError("PORTABLE_EVIDENCE_SIGNED_BUNDLE_DIGEST_MISMATCH")
        if (
            self.managed_key_backend_attested
            != self.attestation.managed_key_backend_attested
        ):
            raise ValueError("PORTABLE_EVIDENCE_MANAGED_KEY_POSTURE_MISMATCH")
        expected_artifact_ref = _stable_ref(
            "portable-mission-evidence-signed-artifact-ref",
            self.model_dump(mode="json", exclude={"artifact_ref"}),
        )
        if self.artifact_ref != expected_artifact_ref:
            raise ValueError("PORTABLE_EVIDENCE_SIGNED_ARTIFACT_REF_INVALID")
        if (
            len(_canonical_json_bytes(self.model_dump(mode="json")))
            > PORTABLE_EVIDENCE_SIGNED_MAX_BYTES
        ):
            raise ValueError("PORTABLE_EVIDENCE_SIGNED_ARTIFACT_TOO_LARGE")
        return self


class PortableEvidenceSignedVerification(_SigningModel):
    valid: StrictBool
    artifact_ref: str | None = None
    bundle_ref: str | None = None
    hash_chain_verified: StrictBool = False
    signature_present: StrictBool = False
    signature_verified: StrictBool = False
    public_key_bundle_matched: StrictBool = False
    trusted_fingerprint_matched: StrictBool = False
    signing_key_acceptable: StrictBool = False
    key_lifecycle_status: str = "unknown"
    cryptographic_authenticity_verified: StrictBool = False
    signer_identity_verified: Literal[False] = False
    external_anchor_verified: Literal[False] = False
    source_ledgers_verified: Literal[False] = False
    non_repudiation_claimed: Literal[False] = False
    execution_authority_granted: Literal[False] = False
    reason_refs: tuple[str, ...] = ()


def ed25519_public_key_fingerprint_ref(public_key: bytes) -> str:
    if len(public_key) != 32:
        raise ValueError("PORTABLE_EVIDENCE_ED25519_PUBLIC_KEY_LENGTH_INVALID")
    return _digest_ref("portable-evidence-public-key-fingerprint-ref", public_key)


def build_public_key_bundle(
    records: Sequence[PortableEvidencePublicKeyRecord],
    *,
    issuer_ref: str,
    lifecycle_terminal_entry_hash_ref: str,
    previous_public_key_bundle_ref: str | None = None,
) -> PortableEvidencePublicKeyBundle:
    provisional = PortableEvidencePublicKeyBundle.model_construct(
        public_key_bundle_ref="portable-evidence-public-key-bundle-ref:pending",
        issuer_ref=issuer_ref,
        records=tuple(records),
        previous_public_key_bundle_ref=previous_public_key_bundle_ref,
        lifecycle_terminal_entry_hash_ref=lifecycle_terminal_entry_hash_ref,
    )
    payload = provisional.model_dump(mode="json", exclude={"public_key_bundle_ref"})
    return PortableEvidencePublicKeyBundle(
        **payload,
        public_key_bundle_ref=_stable_ref(
            "portable-evidence-public-key-bundle-ref", payload
        ),
    )


def portable_evidence_signature_preimage(
    attestation: PortableEvidenceSigningAttestation,
) -> bytes:
    return PORTABLE_EVIDENCE_SIGNING_DOMAIN + _canonical_json_bytes(
        attestation.model_dump(mode="json")
    )


def build_portable_evidence_signing_attestation(
    unsigned_bundle: PortableMissionEvidenceBundle,
    *,
    key_record: PortableEvidencePublicKeyRecord,
    signing_request_ref: str,
    signing_receipt_ref: str,
    key_management_ref: str | None = None,
    managed_key_backend_attested: bool = False,
) -> PortableEvidenceSigningAttestation:
    verification = verify_portable_mission_evidence_bundle(unsigned_bundle)
    if not verification.valid or not verification.chain_verified:
        raise ValueError("PORTABLE_EVIDENCE_UNSIGNED_BUNDLE_INVALID")
    if key_record.status != PortableEvidenceKeyStatus.active.value:
        raise ValueError("PORTABLE_EVIDENCE_ACTIVE_SIGNING_KEY_REQUIRED")
    canonical_bundle = _canonical_json_bytes(unsigned_bundle.model_dump(mode="json"))
    return PortableEvidenceSigningAttestation(
        bundle_ref=unsigned_bundle.bundle_ref,
        bundle_digest_ref=_digest_ref(
            "portable-evidence-bundle-digest-ref", canonical_bundle
        ),
        key_ref=key_record.key_ref,
        key_version_ref=key_record.key_version_ref,
        key_generation=key_record.generation,
        public_key_fingerprint_ref=key_record.public_key_fingerprint_ref,
        signing_request_ref=signing_request_ref,
        signing_receipt_ref=signing_receipt_ref,
        key_management_ref=key_management_ref,
        managed_key_backend_attested=managed_key_backend_attested,
    )


def build_signed_portable_evidence_artifact(
    unsigned_bundle: PortableMissionEvidenceBundle,
    *,
    key_record: PortableEvidencePublicKeyRecord,
    signing_request_ref: str,
    signing_receipt_ref: str,
    signature: bytes,
    key_management_ref: str | None = None,
    managed_key_backend_attested: bool = False,
) -> PortableEvidenceSignedArtifact:
    attestation = build_portable_evidence_signing_attestation(
        unsigned_bundle,
        key_record=key_record,
        signing_request_ref=signing_request_ref,
        signing_receipt_ref=signing_receipt_ref,
        key_management_ref=key_management_ref,
        managed_key_backend_attested=managed_key_backend_attested,
    )
    if len(signature) != 64:
        raise ValueError("PORTABLE_EVIDENCE_ED25519_SIGNATURE_LENGTH_INVALID")
    public_key = _decode_base64url(
        key_record.public_key_base64url,
        expected_bytes=32,
    )
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(
            signature,
            portable_evidence_signature_preimage(attestation),
        )
    except InvalidSignature as exc:
        raise ValueError("PORTABLE_EVIDENCE_ED25519_SIGNATURE_INVALID") from exc
    signature_base64url = _encode_base64url(signature)
    signature_ref = _stable_ref("portable-evidence-signature-ref", signature.hex())
    provisional = PortableEvidenceSignedArtifact.model_construct(
        artifact_ref="portable-mission-evidence-signed-artifact-ref:pending",
        unsigned_bundle=unsigned_bundle,
        attestation=attestation,
        signature_base64url=signature_base64url,
        signature_ref=signature_ref,
        managed_key_backend_attested=managed_key_backend_attested,
    )
    payload = provisional.model_dump(mode="json", exclude={"artifact_ref"})
    return PortableEvidenceSignedArtifact(
        **payload,
        artifact_ref=_stable_ref(
            "portable-mission-evidence-signed-artifact-ref", payload
        ),
    )


def verify_signed_portable_evidence_artifact(
    value: PortableEvidenceSignedArtifact | dict[str, Any],
    *,
    public_key_bundle: PortableEvidencePublicKeyBundle | dict[str, Any],
    expected_public_key_bundle_ref: str,
    expected_public_key_fingerprint_ref: str,
) -> PortableEvidenceSignedVerification:
    try:
        artifact = PortableEvidenceSignedArtifact.model_validate(value)
        trust = PortableEvidencePublicKeyBundle.model_validate(public_key_bundle)
        chain = verify_portable_mission_evidence_bundle(artifact.unsigned_bundle)
        if not chain.valid or not chain.chain_verified:
            raise ValueError("PORTABLE_EVIDENCE_SIGNED_CHAIN_INVALID")
        bundle_matched = trust.public_key_bundle_ref == expected_public_key_bundle_ref
        record = next(
            (
                item
                for item in trust.records
                if item.key_ref == artifact.attestation.key_ref
                and item.key_version_ref == artifact.attestation.key_version_ref
                and item.generation == artifact.attestation.key_generation
            ),
            None,
        )
        if record is None:
            raise ValueError("PORTABLE_EVIDENCE_SIGNING_KEY_UNKNOWN")
        fingerprint_matched = bool(
            record.public_key_fingerprint_ref
            == artifact.attestation.public_key_fingerprint_ref
            == expected_public_key_fingerprint_ref
        )
        public_key = _decode_base64url(record.public_key_base64url, expected_bytes=32)
        signature = _decode_base64url(artifact.signature_base64url, expected_bytes=64)
        signature_verified = False
        try:
            Ed25519PublicKey.from_public_bytes(public_key).verify(
                signature,
                portable_evidence_signature_preimage(artifact.attestation),
            )
            signature_verified = True
        except InvalidSignature:
            signature_verified = False
        acceptable = record.status == PortableEvidenceKeyStatus.active.value
        valid = bool(
            bundle_matched and fingerprint_matched and signature_verified and acceptable
        )
        reasons = ["reason-ref:portable-evidence:hash-chain-verified"]
        reasons.append(
            "reason-ref:portable-evidence:signature-verified"
            if signature_verified
            else "reason-ref:portable-evidence:signature-invalid"
        )
        if not bundle_matched:
            reasons.append("reason-ref:portable-evidence:public-key-bundle-mismatch")
        if not fingerprint_matched:
            reasons.append("reason-ref:portable-evidence:key-fingerprint-mismatch")
        if not acceptable:
            reasons.append("reason-ref:portable-evidence:key-not-active")
        return PortableEvidenceSignedVerification(
            valid=valid,
            artifact_ref=artifact.artifact_ref,
            bundle_ref=artifact.unsigned_bundle.bundle_ref,
            hash_chain_verified=True,
            signature_present=True,
            signature_verified=signature_verified,
            public_key_bundle_matched=bundle_matched,
            trusted_fingerprint_matched=fingerprint_matched,
            signing_key_acceptable=acceptable,
            key_lifecycle_status=str(record.status),
            cryptographic_authenticity_verified=valid,
            reason_refs=tuple(reasons),
        )
    except (TypeError, ValueError):
        return PortableEvidenceSignedVerification(
            valid=False,
            reason_refs=("reason-ref:portable-evidence:signed-artifact-invalid",),
        )


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _digest_ref(prefix: str, value: bytes) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(value).hexdigest()}"


def _stable_ref(prefix: str, value: Any) -> str:
    return _digest_ref(prefix, _canonical_json_bytes(value))


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_base64url(value: str, *, expected_bytes: int) -> bytes:
    if not _BASE64URL_RE.fullmatch(value) or "=" in value:
        raise ValueError("PORTABLE_EVIDENCE_BASE64URL_INVALID")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError("PORTABLE_EVIDENCE_BASE64URL_INVALID") from exc
    if len(decoded) != expected_bytes:
        raise ValueError("PORTABLE_EVIDENCE_BASE64URL_LENGTH_INVALID")
    if _encode_base64url(decoded) != value:
        raise ValueError("PORTABLE_EVIDENCE_BASE64URL_NONCANONICAL")
    return decoded


def _validate_refs(value: Any) -> None:
    if isinstance(value, dict):
        for name, nested in value.items():
            if name.endswith("_ref") and nested is not None:
                validate_task_ref(str(nested), f"portable_evidence_signing_{name}")
            elif name.endswith("_refs"):
                for ref in nested:
                    validate_task_ref(str(ref), f"portable_evidence_signing_{name}")
            else:
                _validate_refs(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _validate_refs(nested)
