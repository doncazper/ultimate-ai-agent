from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.truth.enums import ClaimVerificationStatus
from ultimate_ai_agent.core.truth.evidence import EvidenceManifest
from ultimate_ai_agent.core.truth.sources import TruthSourceManifest


def validate_no_truth_secret_payload(payload: object) -> bool:
    if scan_payload_for_secrets(payload):
        raise ValueError("Truth/evidence payload contains secret-like content.")
    return True


def validate_truth_source_manifest(source: TruthSourceManifest) -> bool:
    validate_no_truth_secret_payload(source.model_dump(mode="json"))
    return True


def validate_evidence_manifest(manifest: EvidenceManifest) -> bool:
    validate_no_truth_secret_payload(manifest.model_dump(mode="json"))

    evidence_ids = {item.evidence_id for item in manifest.evidence_items}
    unsupported_claim_ids = set(manifest.unsupported_claims)
    for claim in manifest.claims:
        if claim.verification_status == ClaimVerificationStatus.supported:
            missing_refs = [ref for ref in claim.evidence_refs if ref not in evidence_ids]
            if missing_refs:
                raise ValueError("supported claim references missing evidence.")
        if claim.verification_status == ClaimVerificationStatus.unsupported and claim.claim_id not in unsupported_claim_ids:
            raise ValueError("unsupported claims must be listed in unsupported_claims.")
    return True
