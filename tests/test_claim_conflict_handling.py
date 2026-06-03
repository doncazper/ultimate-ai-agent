from ultimate_ai_agent.core.truth import (
    Claim,
    ClaimRiskLevel,
    ClaimStatus,
    EvidenceChain,
    EvidenceStrength,
    SourceRevocation,
    SourceStaleness,
    VerificationDecisionStatus,
    VerificationRequest,
    verify_claim_against_evidence_chain,
)


def request_with_chain(**chain_updates) -> VerificationRequest:
    chain_payload = {
        "chain_id": "chain:safety",
        "claim_ref": "claim:safety",
        "source_refs": ["canonical:safety"],
        "evidence_refs": ["evidence:safety"],
        "evidence_strength": EvidenceStrength.evidence_supported,
        "source_priority_summary": "canonical source",
        "safe_summary": "Safe summary.",
    }
    chain_payload.update(chain_updates)
    return VerificationRequest(
        request_id="verify:safety",
        claim=Claim(
            claim_id="claim:safety",
            safe_claim_summary="Safety claim.",
            claim_text_hash="sha256:safety",
            claim_status=ClaimStatus.unverified,
            claim_risk=ClaimRiskLevel.low,
            data_classification="public",
        ),
        evidence_chain=EvidenceChain(**chain_payload),
        requested_status=ClaimStatus.verified_by_primary_source,
    )


def test_stale_conflicted_or_revoked_sources_are_denied():
    cases = [
        ({"stale_refs": ["canonical:safety"], "source_staleness": SourceStaleness.stale}, "STALE_SOURCE_CANNOT_VERIFY_TRUTH"),
        ({"conflict_refs": ["conflict:safety"]}, "CONFLICTED_SOURCE_CANNOT_VERIFY_TRUTH"),
        ({"revoked_refs": ["canonical:safety"], "source_revocation": SourceRevocation.revoked}, "REVOKED_SOURCE_CANNOT_VERIFY_TRUTH"),
    ]

    for updates, reason in cases:
        decision = verify_claim_against_evidence_chain(request_with_chain(**updates))
        assert decision.allowed is False
        assert decision.status == VerificationDecisionStatus.denied
        assert reason in decision.reason_codes
