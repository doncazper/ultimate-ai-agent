from __future__ import annotations

from ultimate_ai_agent.core.code import (
    build_coding_patch_proposal_preview,
    verify_coding_patch_proposal_signed_evidence,
)


def test_coding_evidence_is_hash_only_and_rejects_unsafe_claims() -> None:
    envelope = build_coding_patch_proposal_preview().signed_evidence

    assert envelope.integrity_posture == "sha256_hash_only_not_a_cryptographic_signature"
    assert envelope.cryptographic_signature_present is False
    assert envelope.external_anchor_verified is False

    payload = envelope.model_dump(mode="json")
    for unsafe in (
        payload | {"raw_prompt": "unsafe"},
        payload | {"cryptographic_signature_present": True},
        payload | {"envelope_ref": "/Users/private"},
    ):
        rejected = verify_coding_patch_proposal_signed_evidence(unsafe)
        assert rejected.verification_status == "failed"
        assert rejected.tamper_detected is True
