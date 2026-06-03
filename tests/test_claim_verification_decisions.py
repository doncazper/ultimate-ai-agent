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


def test_inferred_unknown_ref_is_denied_for_evidence_supported():
    chain = EvidenceChain(
        chain_id="chain:random",
        claim_ref="claim:release",
        source_refs=["random:source"],
        evidence_refs=["evidence:random:source"],
        evidence_strength=EvidenceStrength.evidence_supported,
        source_priority_summary="unknown source",
        safe_summary="Unknown source support.",
    )
    request = VerificationRequest(
        request_id="verify:random",
        claim=claim(),
        evidence_chain=chain,
        requested_status=ClaimStatus.evidence_supported,
    )

    decision = verify_claim_against_evidence_chain(request)

    assert decision.allowed is False
    assert decision.claim_status != ClaimStatus.evidence_supported
    assert "UNKNOWN_SOURCE_KIND_DENIED" in decision.reason_codes
    assert "ARBITRARY_SOURCE_REF_DENIED" in decision.reason_codes


def test_explicit_unknown_source_kind_is_denied_for_evidence_supported():
    chain = EvidenceChain(
        chain_id="chain:unknown",
        claim_ref="claim:release",
        source_refs=["unknown:source"],
        evidence_refs=["evidence:unknown:source"],
        evidence_strength=EvidenceStrength.evidence_supported,
        source_priority_summary="unknown source kind",
        safe_summary="Unknown source kind support.",
    )
    request = VerificationRequest(
        request_id="verify:unknown-kind",
        claim=claim(),
        evidence_chain=chain,
        evidence_refs=[evidence("unknown:source", TruthSourceKind.unknown, EvidenceStrength.evidence_supported)],
        requested_status=ClaimStatus.evidence_supported,
    )

    decision = verify_claim_against_evidence_chain(request)

    assert decision.allowed is False
    assert decision.claim_status != ClaimStatus.evidence_supported
    assert "UNKNOWN_SOURCE_KIND_DENIED" in decision.reason_codes


def test_unknown_ref_is_denied_for_verified_by_primary_source():
    chain = EvidenceChain(
        chain_id="chain:random-primary",
        claim_ref="claim:release",
        source_refs=["madeup:thing"],
        evidence_refs=["evidence:madeup:thing"],
        evidence_strength=EvidenceStrength.evidence_supported,
        source_priority_summary="made up source",
        safe_summary="Made up source support.",
    )
    request = VerificationRequest(
        request_id="verify:random-primary",
        claim=claim(),
        evidence_chain=chain,
        requested_status=ClaimStatus.verified_by_primary_source,
    )

    decision = verify_claim_against_evidence_chain(request)

    assert decision.allowed is False
    assert decision.claim_status != ClaimStatus.verified_by_primary_source
    assert "PRIMARY_SOURCE_EVIDENCE_REQUIRED" in decision.reason_codes
    assert "ARBITRARY_SOURCE_REF_DENIED" in decision.reason_codes


def test_unknown_ref_is_denied_for_source_linked_status():
    chain = EvidenceChain(
        chain_id="chain:random-source-linked",
        claim_ref="claim:release",
        source_refs=["random:source-linked"],
        evidence_refs=["evidence:random:source-linked"],
        evidence_strength=EvidenceStrength.source_linked,
        source_priority_summary="random source-linked",
        safe_summary="Random source-linked support.",
    )
    request = VerificationRequest(
        request_id="verify:random-source-linked",
        claim=claim(),
        evidence_chain=chain,
        requested_status=ClaimStatus.source_linked,
    )

    decision = verify_claim_against_evidence_chain(request)

    assert decision.allowed is False
    assert decision.claim_status != ClaimStatus.source_linked
    assert "ARBITRARY_SOURCE_REF_DENIED" in decision.reason_codes
