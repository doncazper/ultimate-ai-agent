import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.truth import (
    ClaimEvidence,
    ClaimVerificationStatus,
    EvidenceItem,
    EvidenceManifest,
    SourceFreshnessStatus,
    TruthSourceType,
    validate_evidence_manifest,
)


def evidence_item(evidence_id: str = "ev_1", *, summary: str = "Source supports the claim.") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_id="src_canonical",
        source_type=TruthSourceType.canonical_file,
        locator="docs/canonical/09_roadmap.md:157",
        summary=summary,
        freshness_status=SourceFreshnessStatus.current,
        confidence=0.95,
        file_ref="docs/canonical/09_roadmap.md",
    )


def test_supported_claim_without_evidence_is_rejected() -> None:
    with pytest.raises(ValidationError, match="evidence"):
        ClaimEvidence(
            claim_id="claim_1",
            claim_text="M4.5 implements truth routing.",
            verification_status=ClaimVerificationStatus.supported,
            confidence=0.9,
        )


def test_unsupported_claim_is_accepted_with_reason() -> None:
    claim = ClaimEvidence(
        claim_id="claim_unsupported",
        claim_text="Unsupported claim.",
        verification_status=ClaimVerificationStatus.unsupported,
        confidence=0.0,
        unsupported_reason="No approved source supplied.",
    )

    assert claim.unsupported_reason == "No approved source supplied."


def test_evidence_manifest_lists_unsupported_claims() -> None:
    unsupported = ClaimEvidence(
        claim_id="claim_unsupported",
        claim_text="Unsupported claim.",
        verification_status=ClaimVerificationStatus.unsupported,
        confidence=0.0,
        unsupported_reason="No evidence.",
    )
    manifest = EvidenceManifest(
        manifest_id="em_1",
        run_id="run_123",
        claims=[unsupported],
        evidence_items=[],
        unsupported_claims=["claim_unsupported"],
    )

    assert validate_evidence_manifest(manifest) is True


def test_raw_secret_evidence_rejected() -> None:
    manifest = EvidenceManifest(
        manifest_id="em_secret",
        run_id="run_123",
        claims=[],
        evidence_items=[evidence_item(summary="api_key='abcdefghijklmnop'")],
    )

    with pytest.raises(ValueError, match="secret"):
        validate_evidence_manifest(manifest)


def test_private_evidence_citation_can_be_redacted() -> None:
    item = evidence_item()
    item.permission_ref = "consent_private"
    item.metadata["citation_display"] = "Private source available to this user"

    assert item.metadata["citation_display"] == "Private source available to this user"
