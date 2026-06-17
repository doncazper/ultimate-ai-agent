from pydantic import ValidationError

from ultimate_ai_agent.core.gate import FoundationGateStatus
from ultimate_ai_agent.core.truth import EvidenceManifest
from ultimate_ai_agent.core.truth.claims import ClaimEvidence
from ultimate_ai_agent.core.truth.enums import ClaimVerificationStatus, SourceFreshnessStatus


def test_truth_evidence_gate_criteria_passes_contract_checks(foundation_gate_results):
    result = foundation_gate_results["truth_evidence_contracts_valid"]

    assert result.status == FoundationGateStatus.passed
    assert result.evidence_refs


def test_supported_claim_requires_evidence_reference():
    try:
        ClaimEvidence(
            claim_id="claim_missing_evidence",
            claim_text="M6 is verification only.",
            verification_status=ClaimVerificationStatus.supported,
            freshness_status=SourceFreshnessStatus.current,
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("supported claims must require evidence references")


def test_evidence_manifest_rejects_unknown_fields():
    try:
        EvidenceManifest(manifest_id="evm_gate", run_id="run_gate", unexpected=True)
    except ValidationError:
        pass
    else:
        raise AssertionError("EvidenceManifest accepted an unknown field")
