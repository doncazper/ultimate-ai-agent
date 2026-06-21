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
    assert_model_output_not_truth,
    verify_claim_against_evidence_chain,
)


def test_model_runtime_and_openwebui_output_cannot_verify_truth() -> None:
    for kind in [
        TruthSourceKind.model_output,
        TruthSourceKind.runtime_output,
        TruthSourceKind.openwebui_output,
    ]:
        request = VerificationRequest(
            request_id=f"verify:{kind.value}",
            claim=Claim(
                claim_id="claim:model",
                safe_claim_summary="Model output cannot verify truth.",
                claim_text_hash="sha256:model",
                claim_status=ClaimStatus.unverified,
                claim_risk=ClaimRiskLevel.low,
                data_classification="public",
            ),
            evidence_chain=EvidenceChain(
                chain_id="chain:model",
                claim_ref="claim:model",
                source_refs=[f"{kind.value}:blocked"],
                evidence_refs=[f"evidence:{kind.value}"],
                evidence_strength=EvidenceStrength.blocked,
                source_priority_summary="blocked output",
                safe_summary="Blocked output.",
            ),
            evidence_refs=[
                EvidenceRef(
                    evidence_ref=f"evidence:{kind.value}",
                    source_ref=f"{kind.value}:blocked",
                    source_kind=kind,
                    evidence_strength=EvidenceStrength.blocked,
                    data_classification="public",
                    redaction_status="redacted",
                    safe_summary="Blocked output summary.",
                )
            ],
            requested_status=ClaimStatus.verified_by_primary_source,
        )

        decision = verify_claim_against_evidence_chain(request)
        assert decision.allowed is False
        with pytest.raises(ValueError, match="Model/runtime/OpenWebUI output refs cannot verify truth"):
            assert_model_output_not_truth(request.evidence_chain)
