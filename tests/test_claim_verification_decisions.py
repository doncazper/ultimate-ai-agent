from ultimate_ai_agent.core.truth import (
    Claim,
    ClaimRiskLevel,
    ClaimStatus,
    EvidenceChain,
    EvidenceRef,
    EvidenceStrength,
    TruthSourceKind,
    VerificationDecisionStatus,
    VerificationRequest,
    verify_claim_against_evidence_chain,
)


def claim() -> Claim:
    return Claim(
        claim_id="claim:release",
        safe_claim_summary="The active baseline is v0.28.2.",
        claim_text_hash="sha256:release",
        claim_status=ClaimStatus.unverified,
        claim_risk=ClaimRiskLevel.low,
        data_classification="public",
    )


def evidence(ref: str, kind: TruthSourceKind, strength: EvidenceStrength) -> EvidenceRef:
    return EvidenceRef(
        evidence_ref=f"evidence:{ref}",
        source_ref=ref,
        source_kind=kind,
        evidence_strength=strength,
        data_classification="public",
        redaction_status="redacted",
        safe_summary="Safe source-linked summary.",
    )


def test_primary_source_backed_evidence_can_support_claim():
    chain = EvidenceChain(
        chain_id="chain:release",
        claim_ref="claim:release",
        source_refs=["canonical:version"],
        evidence_refs=["evidence:canonical:version"],
        evidence_strength=EvidenceStrength.evidence_supported,
        source_priority_summary="canonical source",
        safe_summary="Canonical version file supports the claim.",
    )
    request = VerificationRequest(
        request_id="verify:1",
        claim=claim(),
        evidence_chain=chain,
        evidence_refs=[evidence("canonical:version", TruthSourceKind.canonical_document, EvidenceStrength.evidence_supported)],
        requested_status=ClaimStatus.verified_by_primary_source,
    )

    decision = verify_claim_against_evidence_chain(request)

    assert decision.allowed is True
    assert decision.status == VerificationDecisionStatus.allowed
    assert decision.claim_status == ClaimStatus.verified_by_primary_source


def test_memory_only_evidence_is_denied_for_verified_status():
    chain = EvidenceChain(
        chain_id="chain:memory",
        claim_ref="claim:release",
        source_refs=["memory:release"],
        evidence_refs=["evidence:memory:release"],
        memory_refs=["memory:release"],
        evidence_strength=EvidenceStrength.source_linked,
        source_priority_summary="memory only",
        safe_summary="Memory-only support.",
    )
    request = VerificationRequest(
        request_id="verify:memory",
        claim=claim(),
        evidence_chain=chain,
        evidence_refs=[evidence("memory:release", TruthSourceKind.reviewed_memory, EvidenceStrength.source_linked)],
        requested_status=ClaimStatus.verified_by_primary_source,
    )

    decision = verify_claim_against_evidence_chain(request)

    assert decision.allowed is False
    assert decision.status == VerificationDecisionStatus.denied
    assert "MEMORY_ONLY_CANNOT_VERIFY_TRUTH" in decision.reason_codes
