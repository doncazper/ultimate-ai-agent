"""Purpose-specific portable-evidence signing contracts and adapters."""

from .backend import (
    PortableEvidenceSigningBackendReadiness,
    PortableEvidenceSigningBackendStatus,
    PortableEvidenceSigningKeyBackend,
    UnavailablePortableEvidenceSigningBackend,
)
from .lifecycle import (
    PortableEvidenceKeyLifecycleError,
    PortableEvidenceKeyLifecycleInspection,
    PortableEvidenceKeyLifecycleLedger,
)
from .macos_keychain import (
    MacOSKeychainPortableEvidenceSigningBackend,
    MacOSKeychainSigningBackendError,
    load_installed_macos_keychain_signing_backend,
)

from .portable import (
    PortableEvidenceKeyStatus,
    PortableEvidencePublicKeyBundle,
    PortableEvidencePublicKeyRecord,
    PortableEvidenceSignedArtifact,
    PortableEvidenceSignedVerification,
    PortableEvidenceSigningAttestation,
    build_public_key_bundle,
    build_portable_evidence_signing_attestation,
    build_signed_portable_evidence_artifact,
    ed25519_public_key_fingerprint_ref,
    portable_evidence_signature_preimage,
    verify_signed_portable_evidence_artifact,
)

__all__ = [
    "MacOSKeychainPortableEvidenceSigningBackend",
    "MacOSKeychainSigningBackendError",
    "PortableEvidenceKeyLifecycleInspection",
    "PortableEvidenceKeyLifecycleError",
    "PortableEvidenceKeyLifecycleLedger",
    "PortableEvidenceKeyStatus",
    "PortableEvidencePublicKeyBundle",
    "PortableEvidencePublicKeyRecord",
    "PortableEvidenceSignedArtifact",
    "PortableEvidenceSignedVerification",
    "PortableEvidenceSigningAttestation",
    "PortableEvidenceSigningBackendReadiness",
    "PortableEvidenceSigningBackendStatus",
    "PortableEvidenceSigningKeyBackend",
    "UnavailablePortableEvidenceSigningBackend",
    "build_public_key_bundle",
    "build_portable_evidence_signing_attestation",
    "build_signed_portable_evidence_artifact",
    "ed25519_public_key_fingerprint_ref",
    "load_installed_macos_keychain_signing_backend",
    "portable_evidence_signature_preimage",
    "verify_signed_portable_evidence_artifact",
]
