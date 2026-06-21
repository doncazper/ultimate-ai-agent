from ultimate_ai_agent.core.truth import ClaimEvidence, ClaimVerificationStatus, SourceFreshnessStatus


def test_supported_claim_records_claim_level_evidence() -> None:
    claim = ClaimEvidence(
        claim_id="claim_supported",
        claim_text="Canonical files outrank memory.",
        verification_status=ClaimVerificationStatus.supported,
        evidence_refs=["ev_canonical"],
        source_ids=["src_canonical"],
        confidence=0.98,
        freshness_status=SourceFreshnessStatus.current,
    )

    assert claim.evidence_refs == ["ev_canonical"]
    assert claim.source_ids == ["src_canonical"]


def test_human_review_required_claim_can_be_labeled() -> None:
    claim = ClaimEvidence(
        claim_id="claim_review",
        claim_text="Security decision requires review.",
        verification_status=ClaimVerificationStatus.requires_human_review,
        confidence=0.4,
        human_review_required=True,
        notes=["High-stakes claim."],
    )

    assert claim.human_review_required is True
