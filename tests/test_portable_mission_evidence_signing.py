from __future__ import annotations

import base64
import argparse
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError
from scripts.dev.uaa_runtime_mission_completion import verify_portable

from tests.test_portable_mission_evidence import _bundle
from ultimate_ai_agent.core.evidence_signing.portable import (
    PORTABLE_EVIDENCE_SIGNING_DOMAIN,
    PortableEvidenceKeyStatus,
    PortableEvidencePublicKeyRecord,
    _stable_ref,
    build_portable_evidence_signing_attestation,
    build_public_key_bundle,
    build_signed_portable_evidence_artifact,
    ed25519_public_key_fingerprint_ref,
    portable_evidence_signature_preimage,
    verify_signed_portable_evidence_artifact,
)


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _signed_fixture(tmp_path: Path):  # type: ignore[no-untyped-def]
    unsigned = _bundle(tmp_path)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes_raw()
    record = PortableEvidencePublicKeyRecord(
        key_ref="signing-key-ref:portable-evidence:test",
        key_version_ref="signing-key-version-ref:portable-evidence:test:1",
        generation=1,
        status=PortableEvidenceKeyStatus.active,
        public_key_base64url=_b64url(public_key),
        public_key_fingerprint_ref=ed25519_public_key_fingerprint_ref(public_key),
        lifecycle_receipt_ref="receipt-ref:portable-evidence-key:create:test",
    )
    trust = build_public_key_bundle(
        [record],
        issuer_ref="issuer-ref:portable-evidence:local-operator",
        lifecycle_terminal_entry_hash_ref=(
            "portable-evidence-key-entry-hash-ref:sha256:" + "1" * 64
        ),
    )
    attestation = build_portable_evidence_signing_attestation(
        unsigned,
        key_record=record,
        signing_request_ref="signing-request-ref:portable-evidence:test",
        signing_receipt_ref="signing-receipt-ref:portable-evidence:test",
    )
    signature = private_key.sign(portable_evidence_signature_preimage(attestation))
    artifact = build_signed_portable_evidence_artifact(
        unsigned,
        key_record=record,
        signing_request_ref=attestation.signing_request_ref,
        signing_receipt_ref=attestation.signing_receipt_ref,
        signature=signature,
    )
    return private_key, record, trust, artifact


def _verify(record, trust, artifact):  # type: ignore[no-untyped-def]
    return verify_signed_portable_evidence_artifact(
        artifact,
        public_key_bundle=trust,
        expected_public_key_bundle_ref=trust.public_key_bundle_ref,
        expected_public_key_fingerprint_ref=record.public_key_fingerprint_ref,
    )


def test_real_ed25519_sign_and_offline_verify_with_pinned_trust(
    tmp_path: Path,
) -> None:
    _private, record, trust, artifact = _signed_fixture(tmp_path)

    result = _verify(record, trust, artifact)

    assert result.valid is True
    assert result.hash_chain_verified is True
    assert result.signature_verified is True
    assert result.public_key_bundle_matched is True
    assert result.trusted_fingerprint_matched is True
    assert result.cryptographic_authenticity_verified is True
    assert result.signer_identity_verified is False
    assert result.external_anchor_verified is False
    assert result.source_ledgers_verified is False
    assert result.non_repudiation_claimed is False
    assert result.execution_authority_granted is False


def test_ed25519_signature_is_deterministic_for_same_key_and_attestation(
    tmp_path: Path,
) -> None:
    private_key, _record, _trust, artifact = _signed_fixture(tmp_path)
    preimage = portable_evidence_signature_preimage(artifact.attestation)

    assert private_key.sign(preimage) == private_key.sign(preimage)


def test_artifact_builder_rejects_signature_from_another_key(tmp_path: Path) -> None:
    _private, record, _trust, artifact = _signed_fixture(tmp_path)
    attacker = Ed25519PrivateKey.generate()

    signature = attacker.sign(
        portable_evidence_signature_preimage(artifact.attestation)
    )

    try:
        build_signed_portable_evidence_artifact(
            artifact.unsigned_bundle,
            key_record=record,
            signing_request_ref=artifact.attestation.signing_request_ref,
            signing_receipt_ref=artifact.attestation.signing_receipt_ref,
            signature=signature,
        )
    except ValueError as exc:
        assert str(exc) == "PORTABLE_EVIDENCE_ED25519_SIGNATURE_INVALID"
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("mismatched signature was accepted")


def test_signature_without_domain_separator_is_rejected(tmp_path: Path) -> None:
    private_key, record, _trust, artifact = _signed_fixture(tmp_path)
    preimage = portable_evidence_signature_preimage(artifact.attestation)
    signature = private_key.sign(preimage[len(PORTABLE_EVIDENCE_SIGNING_DOMAIN) :])

    with pytest.raises(
        ValueError,
        match="PORTABLE_EVIDENCE_ED25519_SIGNATURE_INVALID",
    ):
        build_signed_portable_evidence_artifact(
            artifact.unsigned_bundle,
            key_record=record,
            signing_request_ref=artifact.attestation.signing_request_ref,
            signing_receipt_ref=artifact.attestation.signing_receipt_ref,
            signature=signature,
        )


def test_signature_covers_attestation_and_rehashed_bundle_tamper(
    tmp_path: Path,
) -> None:
    _private, record, trust, artifact = _signed_fixture(tmp_path)
    payload = artifact.model_dump(mode="json")
    payload["attestation"]["signing_request_ref"] = (
        "signing-request-ref:portable-evidence:substituted"
    )
    payload["artifact_ref"] = _stable_ref(
        "portable-mission-evidence-signed-artifact-ref",
        {key: value for key, value in payload.items() if key != "artifact_ref"},
    )

    result = _verify(record, trust, payload)

    assert result.valid is False
    assert result.signature_verified is False
    assert result.cryptographic_authenticity_verified is False

    bundle_tamper = artifact.model_dump(mode="json")
    bundle_tamper["unsigned_bundle"]["envelopes"][0]["target_binding_ref"] = (
        "target-binding-ref:substituted"
    )
    assert _verify(record, trust, bundle_tamper).valid is False


def test_attacker_resigning_with_untrusted_key_is_rejected(tmp_path: Path) -> None:
    _private, record, trust, artifact = _signed_fixture(tmp_path)
    attacker = Ed25519PrivateKey.generate()
    attacker_public = attacker.public_key().public_bytes_raw()
    attacker_record = record.model_copy(
        update={
            "key_ref": "signing-key-ref:portable-evidence:attacker",
            "key_version_ref": "signing-key-version-ref:portable-evidence:attacker:1",
            "public_key_base64url": _b64url(attacker_public),
            "public_key_fingerprint_ref": ed25519_public_key_fingerprint_ref(
                attacker_public
            ),
        }
    )
    attacker_trust = build_public_key_bundle(
        [attacker_record],
        issuer_ref="issuer-ref:portable-evidence:untrusted",
        lifecycle_terminal_entry_hash_ref=(
            "portable-evidence-key-entry-hash-ref:sha256:" + "2" * 64
        ),
    )

    result = verify_signed_portable_evidence_artifact(
        artifact,
        public_key_bundle=attacker_trust,
        expected_public_key_bundle_ref=trust.public_key_bundle_ref,
        expected_public_key_fingerprint_ref=record.public_key_fingerprint_ref,
    )

    assert result.valid is False
    assert result.cryptographic_authenticity_verified is False


def test_revoked_key_is_policy_invalid_even_when_signature_math_is_valid(
    tmp_path: Path,
) -> None:
    _private, record, _trust, artifact = _signed_fixture(tmp_path)
    revoked = record.model_copy(
        update={
            "status": PortableEvidenceKeyStatus.revoked,
            "revocation_ref": "revocation-ref:portable-evidence:test",
        }
    )
    revoked_trust = build_public_key_bundle(
        [revoked],
        issuer_ref="issuer-ref:portable-evidence:local-operator",
        lifecycle_terminal_entry_hash_ref=(
            "portable-evidence-key-entry-hash-ref:sha256:" + "3" * 64
        ),
    )

    result = verify_signed_portable_evidence_artifact(
        artifact,
        public_key_bundle=revoked_trust,
        expected_public_key_bundle_ref=revoked_trust.public_key_bundle_ref,
        expected_public_key_fingerprint_ref=revoked.public_key_fingerprint_ref,
    )

    assert result.signature_verified is True
    assert result.signing_key_acceptable is False
    assert result.valid is False


def test_lost_key_fails_current_snapshot_but_preserved_active_snapshot_verifies(
    tmp_path: Path,
) -> None:
    _private, record, original_trust, artifact = _signed_fixture(tmp_path)
    lost = record.model_copy(update={"status": PortableEvidenceKeyStatus.lost})
    lost_trust = build_public_key_bundle(
        [lost],
        issuer_ref="issuer-ref:portable-evidence:local-operator",
        lifecycle_terminal_entry_hash_ref=(
            "portable-evidence-key-entry-hash-ref:sha256:" + "4" * 64
        ),
    )

    result = verify_signed_portable_evidence_artifact(
        artifact,
        public_key_bundle=lost_trust,
        expected_public_key_bundle_ref=lost_trust.public_key_bundle_ref,
        expected_public_key_fingerprint_ref=lost.public_key_fingerprint_ref,
    )

    assert result.valid is False
    assert result.key_lifecycle_status == "lost"
    assert _verify(record, original_trust, artifact).valid is True


def test_noncanonical_signature_base64url_is_rejected(tmp_path: Path) -> None:
    _private, record, trust, artifact = _signed_fixture(tmp_path)
    payload = artifact.model_dump(mode="json")
    final = payload["signature_base64url"][-1]
    payload["signature_base64url"] = payload["signature_base64url"][:-1] + (
        "R" if final == "Q" else "B"
    )

    assert _verify(record, trust, payload).valid is False


def test_malformed_signature_and_unknown_private_fields_fail_closed(
    tmp_path: Path,
) -> None:
    _private, record, trust, artifact = _signed_fixture(tmp_path)
    malformed = artifact.model_dump(mode="json")
    malformed["signature_base64url"] = "bad"
    assert _verify(record, trust, malformed).valid is False

    unsafe = artifact.model_dump(mode="json")
    unsafe["private_key"] = "not-accepted"
    assert _verify(record, trust, unsafe).valid is False


def test_direct_validation_hides_unknown_private_input(tmp_path: Path) -> None:
    _private, _record, _trust, artifact = _signed_fixture(tmp_path)
    unsafe = artifact.model_dump(mode="json")
    unsafe["private_key"] = "private-input-sentinel"

    with pytest.raises(ValidationError) as raised:
        type(artifact).model_validate(unsafe)

    assert "private-input-sentinel" not in str(raised.value)


def test_public_bundle_rejects_broken_rotation_continuity(tmp_path: Path) -> None:
    _private, record, _trust, _artifact = _signed_fixture(tmp_path)
    second_private = Ed25519PrivateKey.generate()
    second_public = second_private.public_key().public_bytes_raw()
    retired = record.model_copy(update={"status": PortableEvidenceKeyStatus.retired})
    wrong_chain = record.model_copy(
        update={
            "key_ref": record.key_ref,
            "key_version_ref": "signing-key-version-ref:portable-evidence:test:2",
            "generation": 2,
            "status": PortableEvidenceKeyStatus.active,
            "predecessor_key_version_ref": "signing-key-version-ref:wrong",
            "public_key_base64url": _b64url(second_public),
            "public_key_fingerprint_ref": ed25519_public_key_fingerprint_ref(
                second_public
            ),
        }
    )

    with pytest.raises(ValueError, match="CONTINUITY_INVALID"):
        build_public_key_bundle(
            [retired, wrong_chain],
            issuer_ref="issuer-ref:portable-evidence:local-operator",
            lifecycle_terminal_entry_hash_ref=(
                "portable-evidence-key-entry-hash-ref:sha256:" + "5" * 64
            ),
        )


def test_signed_cli_verification_requires_independently_pinned_trust(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _private, record, trust, artifact = _signed_fixture(tmp_path)
    artifact_path = tmp_path / "artifact.json"
    trust_path = tmp_path / "public-keys.json"
    artifact_path.write_text(artifact.model_dump_json(), encoding="utf-8")
    trust_path.write_text(trust.model_dump_json(), encoding="utf-8")
    args = argparse.Namespace(
        input=str(artifact_path),
        expected_bundle_ref=None,
        expected_envelope_count=None,
        public_key_bundle=str(trust_path),
        expected_public_key_bundle_ref=trust.public_key_bundle_ref,
        expected_public_key_fingerprint_ref=record.public_key_fingerprint_ref,
        require_signature=True,
        json=True,
    )

    assert verify_portable(args) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["signature_verified"] is True
    assert output["signer_identity_verified"] is False

    args.expected_bundle_ref = artifact.unsigned_bundle.bundle_ref
    args.expected_envelope_count = artifact.unsigned_bundle.envelope_count
    assert verify_portable(args) == 0
    capsys.readouterr()

    args.expected_bundle_ref = (
        "portable-mission-evidence-bundle-ref:sha256:" + "0" * 64
    )
    assert verify_portable(args) == 1
    assert "could not be safely read" not in capsys.readouterr().err
    args.expected_bundle_ref = None
    args.expected_envelope_count = None

    args.expected_public_key_bundle_ref = (
        "portable-evidence-public-key-bundle-ref:sha256:" + "0" * 64
    )
    assert verify_portable(args) == 1

    artifact_path.write_text("[]", encoding="utf-8")
    assert verify_portable(args) == 1
    assert "could not be safely read" in capsys.readouterr().err
