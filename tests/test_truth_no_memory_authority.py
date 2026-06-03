import pytest

from ultimate_ai_agent.core.truth import (
    Claim,
    ClaimRiskLevel,
    ClaimStatus,
    EvidenceChain,
    EvidenceRef,
    EvidenceStrength,
    TruthSourceKind,
    VerificationRequest,
    assert_memory_not_truth,
    verify_claim_against_evidence_chain,
)


def memory_request(kind: TruthSourceKind) -> VerificationRequest:
    return VerificationRequest(
        request_id=f"verify:{kind.value}",
        claim=Claim(
            claim_id="claim:memory",
            safe_claim_summary="Memory cannot verify truth alone.",
            claim_text_hash="sha256:memory",
            claim_status=ClaimStatus.unverified,
            claim_risk=ClaimRiskLevel.low,
            data_classification="public",
        ),
        evidence_chain=EvidenceChain(
            chain_id="chain:memory",
            claim_ref="claim:memory",
            source_refs=[f"memory:{kind.value}"],
            evidence_refs=[f"evidence:memory:{kind.value}"],
            memory_refs=[f"memory:{kind.value}"],
            evidence_strength=EvidenceStrength.source_linked,
            source_priority_summary="memory",
            safe_summary="Memory-only chain.",
        ),
        evidence_refs=[
            EvidenceRef(
                evidence_ref=f"evidence:memory:{kind.value}",
                source_ref=f"memory:{kind.value}",
                source_kind=kind,
                evidence_strength=EvidenceStrength.source_linked,
                data_classification="public",
                redaction_status="redacted",
                safe_summary="Memory summary.",
            )
        ],
        requested_status=ClaimStatus.verified_by_primary_source,
    )


def test_memory_kinds_cannot_verify_truth_alone():
    for kind in [
        TruthSourceKind.source_linked_memory,
        TruthSourceKind.reviewed_memory,
        TruthSourceKind.unreviewed_memory,
    ]:
        decision = verify_claim_against_evidence_chain(memory_request(kind))
        assert decision.allowed is False
        with pytest.raises(ValueError, match="Memory refs cannot verify truth"):
            assert_memory_not_truth(memory_request(kind).evidence_chain)
