from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.evals.tool_aware_acceptance import (
    TAW08_FOUNDER_EVIDENCE_MISSING_REFS,
    TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS,
    TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
    EvidenceOnlyDeltaEntry,
    EvidenceOnlyDeltaManifest,
    FoundationGateReceipt,
    TAW08AcceptanceReport,
    TAW08AcceptanceStatus,
    bind_evidence_only_delta,
    bind_foundation_gate_receipt,
    bind_founder_private_acceptance_evidence,
    evaluate_taw08_acceptance,
    verify_evidence_only_delta,
)
from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    CandidateLock,
    CandidateManifestEntry,
    canonical_digest,
)


CANDIDATE_REVISION_REF = "git-sha:" + "1" * 40
DELTA_REVISION_REF = "git-sha:" + "2" * 40


def _candidate_lock() -> CandidateLock:
    entries = (
        CandidateManifestEntry(
            path_ref="repo-path-ref:src/ultimate_ai_agent/core/candidate.py",
            content_digest_ref="sha256:" + "a" * 64,
        ),
    )
    values = {
        "candidate_ref": "candidate-ref:taw08:founder-private:v1",
        "git_revision_ref": CANDIDATE_REVISION_REF,
        "entries": [item.model_dump(mode="json") for item in entries],
        "evidence_only_delta_path_refs": (
            "repo-path-ref:docs/evals/taw08_acceptance_report.json",
            "repo-path-ref:docs/kanban/current_board.md",
            "repo-path-ref:docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
        ),
    }
    return CandidateLock(
        candidate_ref=values["candidate_ref"],
        git_revision_ref=values["git_revision_ref"],
        entries=entries,
        evidence_only_delta_path_refs=values["evidence_only_delta_path_refs"],
        manifest_digest_ref=canonical_digest(values),
    )


def _foundation_receipt(
    *, stage: str = "exact_head", revision_ref: str = CANDIDATE_REVISION_REF
) -> FoundationGateReceipt:
    return bind_foundation_gate_receipt(
        stage=stage,
        revision_ref=revision_ref,
        report_digest_ref="sha256:" + "3" * 64,
        report_ref=f"foundation-report-ref:taw08:{stage}",
    )


def _founder_evidence(lock: CandidateLock):
    return bind_founder_private_acceptance_evidence(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        stale_cache_recovery_receipt_ref="receipt-ref:taw08:stale-recovery",
        routing_confidence_receipt_ref="receipt-ref:taw08:routing-confidence",
        response_scoring_receipt_ref="receipt-ref:taw08:response-scoring",
        live_model_hardware_receipt_refs=("receipt-ref:taw08:qwen-mac-run-1",),
        end_to_end_journey_receipt_ref="receipt-ref:taw08:end-to-end-journeys",
        founder_decision_ref="decision-ref:taw08:founder-private:accepted",
        exact_head_foundation_receipt=_foundation_receipt(),
    )


def _delta(lock: CandidateLock, content: bytes = b"redacted acceptance report"):
    return bind_evidence_only_delta(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        delta_revision_ref=DELTA_REVISION_REF,
        entries=(
            EvidenceOnlyDeltaEntry(
                path_ref="repo-path-ref:docs/evals/taw08_acceptance_report.json",
                artifact_kind="acceptance_report",
                content_digest_ref=(f"sha256:{hashlib.sha256(content).hexdigest()}"),
            ),
        ),
    )


def test_missing_evidence_remains_blocked_and_explicit() -> None:
    report = evaluate_taw08_acceptance(candidate_lock=_candidate_lock())

    assert report.status == TAW08AcceptanceStatus.blocked_missing_founder_evidence
    assert not report.founder_private_accepted
    assert report.founder_evidence_missing_refs == tuple(
        sorted(
            (*TAW08_FOUNDER_EVIDENCE_MISSING_REFS, TAW08_POSTMERGE_EVIDENCE_MISSING_REF)
        )
    )
    assert report.independent_promotion_blocker_refs == (
        TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS
    )
    assert not report.independent_promotion_ready
    assert not report.public_quality_claims_allowed


def test_founder_private_acceptance_does_not_claim_independent_promotion() -> None:
    lock = _candidate_lock()
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=_delta(lock),
    )

    assert report.status == (
        TAW08AcceptanceStatus.founder_private_accepted_postmerge_pending
    )
    assert report.founder_private_accepted
    assert report.founder_evidence_missing_refs == (
        TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
    )
    assert not report.independent_promotion_ready
    assert not report.sealed_holdout_evidence_verified


def test_postmerge_receipt_advances_only_founder_private_status() -> None:
    lock = _candidate_lock()
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=_delta(lock),
        postmerge_foundation_receipt=_foundation_receipt(
            stage="postmerge", revision_ref=DELTA_REVISION_REF
        ),
    )

    assert report.status == (
        TAW08AcceptanceStatus.founder_private_accepted_promotion_blocked
    )
    assert report.founder_private_accepted
    assert report.founder_evidence_missing_refs == ()
    assert not report.independent_promotion_ready


def test_postmerge_receipt_must_bind_evidence_delta_revision() -> None:
    lock = _candidate_lock()
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=_delta(lock),
        postmerge_foundation_receipt=_foundation_receipt(
            stage="postmerge", revision_ref="git-sha:" + "5" * 40
        ),
    )

    assert report.status == TAW08AcceptanceStatus.failed
    assert report.failure_refs == ("failure-ref:taw08:postmerge-delta-revision-drift",)
    assert not report.founder_private_accepted


def test_founder_evidence_rejects_candidate_revision_substitution() -> None:
    lock = _candidate_lock()
    receipt = _foundation_receipt(revision_ref="git-sha:" + "4" * 40)

    with pytest.raises(ValidationError, match="must bind the candidate revision"):
        bind_founder_private_acceptance_evidence(
            candidate_revision_ref=lock.git_revision_ref,
            candidate_manifest_digest_ref=lock.manifest_digest_ref,
            stale_cache_recovery_receipt_ref="receipt-ref:taw08:stale-recovery",
            routing_confidence_receipt_ref="receipt-ref:taw08:routing-confidence",
            response_scoring_receipt_ref="receipt-ref:taw08:response-scoring",
            live_model_hardware_receipt_refs=("receipt-ref:taw08:qwen-mac",),
            end_to_end_journey_receipt_ref="receipt-ref:taw08:journeys",
            founder_decision_ref="decision-ref:taw08:founder-private:accepted",
            exact_head_foundation_receipt=receipt,
        )


def test_founder_evidence_rejects_duplicate_measurement_receipts() -> None:
    lock = _candidate_lock()

    with pytest.raises(ValidationError, match="unique and sorted"):
        bind_founder_private_acceptance_evidence(
            candidate_revision_ref=lock.git_revision_ref,
            candidate_manifest_digest_ref=lock.manifest_digest_ref,
            stale_cache_recovery_receipt_ref="receipt-ref:taw08:stale-recovery",
            routing_confidence_receipt_ref="receipt-ref:taw08:routing-confidence",
            response_scoring_receipt_ref="receipt-ref:taw08:response-scoring",
            live_model_hardware_receipt_refs=(
                "receipt-ref:taw08:qwen-mac",
                "receipt-ref:taw08:qwen-mac",
            ),
            end_to_end_journey_receipt_ref="receipt-ref:taw08:journeys",
            founder_decision_ref="decision-ref:taw08:founder-private:accepted",
            exact_head_foundation_receipt=_foundation_receipt(),
        )


def test_evidence_only_delta_verifies_exact_allowed_content() -> None:
    lock = _candidate_lock()
    content = b"redacted acceptance report"
    delta = _delta(lock, content)

    assert (
        verify_evidence_only_delta(
            candidate_lock=lock,
            delta=delta,
            changed_content_by_path_ref={delta.entries[0].path_ref: content},
        )
        == ()
    )


def test_evidence_only_delta_rejects_unapproved_or_substituted_content() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)

    failures = verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={
            "repo-path-ref:src/ultimate_ai_agent/core/runtime.py": b"changed"
        },
    )

    assert failures == (
        "failure-ref:taw08:evidence-delta-path-census-drift",
        "failure-ref:taw08:evidence-delta-unapproved-path",
    )


def test_evidence_only_delta_cannot_overlap_candidate_artifact() -> None:
    lock = _candidate_lock()
    candidate_path = lock.entries[0].path_ref
    content = b"changed candidate"
    values = {
        "candidate_revision_ref": lock.git_revision_ref,
        "candidate_manifest_digest_ref": lock.manifest_digest_ref,
        "delta_revision_ref": DELTA_REVISION_REF,
        "entries": [
            {
                "path_ref": candidate_path,
                "artifact_kind": "acceptance_report",
                "content_digest_ref": (f"sha256:{hashlib.sha256(content).hexdigest()}"),
            }
        ],
    }
    delta = bind_evidence_only_delta(**values)

    failures = verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={candidate_path: content},
    )

    assert failures == (
        "failure-ref:taw08:evidence-delta-acceptance-path-overlap",
        "failure-ref:taw08:evidence-delta-unapproved-path",
    )


def test_delta_schema_cannot_label_executable_change_as_evidence_only() -> None:
    lock = _candidate_lock()

    with pytest.raises(ValidationError, match="artifact_kind"):
        bind_evidence_only_delta(
            candidate_revision_ref=lock.git_revision_ref,
            candidate_manifest_digest_ref=lock.manifest_digest_ref,
            delta_revision_ref=DELTA_REVISION_REF,
            entries=(
                {
                    "path_ref": "repo-path-ref:src/runtime.py",
                    "artifact_kind": "executable",
                    "content_digest_ref": "sha256:" + "a" * 64,
                },
            ),
        )


def test_delta_manifest_rejects_digest_rebinding_and_unknown_fields() -> None:
    delta = _delta(_candidate_lock())
    payload = delta.model_dump(mode="json")
    payload["manifest_digest_ref"] = "sha256:" + "f" * 64

    with pytest.raises(ValidationError, match="digest binding drift"):
        EvidenceOnlyDeltaManifest.model_validate(payload)

    payload = delta.model_dump(mode="json")
    payload["raw_report"] = "not allowed"
    with pytest.raises(ValidationError, match="extra_forbidden"):
        EvidenceOnlyDeltaManifest.model_validate(payload)


def test_foundation_receipt_rejects_non_exact_revision() -> None:
    with pytest.raises(ValidationError, match="exact Git revision"):
        bind_foundation_gate_receipt(
            stage="exact_head",
            revision_ref="git-sha:short",
            report_digest_ref="sha256:" + "3" * 64,
            report_ref="foundation-report-ref:taw08:exact-head",
        )


def test_report_rejects_status_or_fingerprint_substitution() -> None:
    report = evaluate_taw08_acceptance(candidate_lock=_candidate_lock())
    payload = report.model_dump(mode="json")
    payload["status"] = "founder_private_accepted_promotion_blocked"

    with pytest.raises(ValidationError, match="status does not match"):
        TAW08AcceptanceReport.model_validate(payload)

    payload = report.model_dump(mode="json")
    payload["report_fingerprint_ref"] = "taw08-acceptance-report-ref:sha256:" + "f" * 64
    with pytest.raises(ValidationError, match="fingerprint binding drift"):
        TAW08AcceptanceReport.model_validate(payload)


def test_python_310_compatible_string_enums_are_used() -> None:
    assert issubclass(TAW08AcceptanceStatus, str)
    assert TAW08AcceptanceStatus.blocked_missing_founder_evidence.value == (
        "blocked_missing_founder_evidence"
    )
