import pytest

from ultimate_ai_agent.core.truth import (
    Claim,
    ClaimRiskLevel,
    ClaimStatus,
    EvidenceChain,
    EvidenceRef,
    EvidenceStrength,
    TruthSourceKind,
)


def test_claim_uses_hash_and_safe_summary_not_raw_text() -> None:
    claim = Claim(
        claim_id="claim:1",
        safe_claim_summary="The roadmap marks M24 implemented.",
        claim_text_hash="sha256:abc123",
        claim_status=ClaimStatus.unverified,
        claim_risk=ClaimRiskLevel.low,
        data_classification="public",
    )

    assert claim.claim_text_hash == "sha256:abc123"


def test_claim_rejects_raw_or_secret_like_summary() -> None:
    with pytest.raises(ValueError, match="raw content"):
        Claim(
            claim_id="claim:raw",
            safe_claim_summary="raw_prompt: please verify this",
            claim_text_hash="sha256:abc123",
            claim_status=ClaimStatus.unverified,
            claim_risk=ClaimRiskLevel.low,
            data_classification="public",
        )

    with pytest.raises(ValueError, match="secret-like"):
        EvidenceRef(
            evidence_ref="evidence:secret",
            source_ref="canonical:roadmap",
            source_kind=TruthSourceKind.canonical_document,
            evidence_strength=EvidenceStrength.source_linked,
            data_classification="public",
            redaction_status="redacted",
            safe_summary="token=abc123",
        )


def test_evidence_chain_rejects_claim_self_verification() -> None:
    with pytest.raises(ValueError, match="cannot self-verify"):
        EvidenceChain(
            chain_id="chain:1",
            claim_ref="claim:1",
            source_refs=["claim:1"],
            evidence_refs=["evidence:1"],
            evidence_strength=EvidenceStrength.evidence_supported,
            source_priority_summary="canonical source",
            safe_summary="Claim points at itself.",
        )
