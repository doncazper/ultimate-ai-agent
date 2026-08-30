from __future__ import annotations

import hashlib
import json

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.evals.tool_aware_acceptance import (
    TAW08_FOUNDER_EVIDENCE_MISSING_REFS,
    TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS,
    TAW08_DELTA_VERIFICATION_MISSING_REF,
    TAW08_MAX_EVIDENCE_DELTA_ARTIFACT_BYTES,
    TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
    TAW08_REQUIRED_ACCEPTANCE_PATH_REFS,
    EvidenceOnlyDeltaEntry,
    EvidenceOnlyDeltaManifest,
    FoundationGateReceipt,
    TAW08AcceptanceReport,
    TAW08AcceptanceStatus,
    bind_evidence_only_delta,
    bind_foundation_gate_receipt,
    bind_founder_private_acceptance_evidence,
    evaluate_taw08_acceptance,
    verify_and_bind_candidate_lock,
    verify_and_bind_evidence_only_delta,
    verify_evidence_only_delta,
)
from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    CandidateLock,
    CandidateManifestEntry,
    SourceDependencyClosure,
    SourceDependencyEntry,
    SourceProjection,
    canonical_digest,
)


CANDIDATE_REVISION_REF = "git-sha:" + "1" * 40
DELTA_REVISION_REF = "git-sha:" + "2" * 40


def _candidate_lock() -> CandidateLock:
    empty_digest = f"sha256:{hashlib.sha256(b'').hexdigest()}"
    entries = tuple(
        CandidateManifestEntry(path_ref=path_ref, content_digest_ref=empty_digest)
        for path_ref in TAW08_REQUIRED_ACCEPTANCE_PATH_REFS
    )
    values = {
        "candidate_ref": "candidate-ref:taw08:founder-private:v1",
        "git_revision_ref": CANDIDATE_REVISION_REF,
        "entries": [item.model_dump(mode="json") for item in entries],
        "evidence_only_delta_path_refs": (
            "repo-path-ref:docs/evals/taw08_acceptance_report.json",
            "repo-path-ref:docs/evals/taw08_evidence_refs.json",
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


def _candidate_verification(lock: CandidateLock):
    expected_refs = tuple(item.path_ref for item in lock.entries)
    content_by_ref = dict.fromkeys(expected_refs, b"")
    source_entries = tuple(
        item
        for item in lock.entries
        if item.path_ref.startswith("repo-path-ref:src/")
        and item.path_ref.endswith(".py")
    )
    projection_payload = {
        "schema_version": "uaa-taw00-source-projection.v1",
        "projection_ref": "source-projection-ref:taw08:test",
        "source_revision_ref": lock.git_revision_ref,
        "status": "transitive_dependency_closed",
        "entries": [item.model_dump(mode="json") for item in source_entries],
        "routing_changes_added": False,
        "prompt_changes_added": False,
        "runtime_model_calls_added": False,
        "authority_added": False,
    }
    projection = SourceProjection(
        **projection_payload,
        projection_digest_ref=canonical_digest(projection_payload),
    )
    closure_entries = tuple(
        SourceDependencyEntry(
            path_ref=item.path_ref,
            content_digest_ref=item.content_digest_ref,
            dependency_path_refs=(),
        )
        for item in source_entries
    )
    closure_payload = {
        "schema_version": "uaa-taw00-source-dependency-closure.v1",
        "source_revision_ref": lock.git_revision_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "root_path_refs": tuple(item.path_ref for item in source_entries),
        "entries": [item.model_dump(mode="json") for item in closure_entries],
    }
    closure = SourceDependencyClosure(
        **closure_payload,
        closure_digest_ref=canonical_digest(closure_payload),
    )
    source_content = {item.path_ref: b"" for item in source_entries}
    return verify_and_bind_candidate_lock(
        candidate_lock=lock,
        expected_path_refs=expected_refs,
        revision_content_by_path_ref=content_by_ref,
        source_projection=projection,
        source_closure=closure,
        closure_content_by_path_ref=source_content,
        available_path_refs=set(source_content),
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
        founder_decision_outcome="accepted",
        exact_head_foundation_receipt=_foundation_receipt(),
    )


def _safe_delta_content() -> bytes:
    return json.dumps(
        {
            "schema_version": "uaa-taw08-immutable-evidence-refs.v1",
            "evidence_refs": ["evidence-ref:taw08:redacted-acceptance"],
            "raw_content_persisted": False,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _delta(lock: CandidateLock, content: bytes | None = None):
    content = _safe_delta_content() if content is None else content
    return bind_evidence_only_delta(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        delta_revision_ref=DELTA_REVISION_REF,
        entries=(
            EvidenceOnlyDeltaEntry(
                path_ref="repo-path-ref:docs/evals/taw08_evidence_refs.json",
                artifact_kind="immutable_evidence_refs",
                content_digest_ref=(f"sha256:{hashlib.sha256(content).hexdigest()}"),
            ),
        ),
    )


def _delta_verification(lock: CandidateLock, delta: EvidenceOnlyDeltaManifest):
    return verify_and_bind_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={delta.entries[0].path_ref: _safe_delta_content()},
    )


def test_missing_evidence_remains_blocked_and_explicit() -> None:
    report = evaluate_taw08_acceptance(candidate_lock=_candidate_lock())

    assert report.status == TAW08AcceptanceStatus.blocked_missing_founder_evidence
    assert not report.founder_private_accepted
    assert report.founder_evidence_missing_refs == tuple(
        sorted(
            (
                *TAW08_FOUNDER_EVIDENCE_MISSING_REFS,
                TAW08_DELTA_VERIFICATION_MISSING_REF,
                TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
            )
        )
    )
    assert report.independent_promotion_blocker_refs == (
        TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS
    )
    assert not report.independent_promotion_ready
    assert not report.public_quality_claims_allowed


def test_founder_private_acceptance_does_not_claim_independent_promotion() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        evidence_only_delta_verification_receipt=_delta_verification(lock, delta),
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
    delta = _delta(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        evidence_only_delta_verification_receipt=_delta_verification(lock, delta),
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
    delta = _delta(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        evidence_only_delta_verification_receipt=_delta_verification(lock, delta),
        postmerge_foundation_receipt=_foundation_receipt(
            stage="postmerge", revision_ref="git-sha:" + "5" * 40
        ),
    )
    assert report.status is TAW08AcceptanceStatus.failed
    assert report.failure_refs == ("failure-ref:taw08:postmerge-delta-revision-drift",)


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
            founder_decision_outcome="accepted",
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
            founder_decision_outcome="accepted",
            exact_head_foundation_receipt=_foundation_receipt(),
        )


def test_evidence_only_delta_verifies_exact_allowed_content() -> None:
    lock = _candidate_lock()
    content = _safe_delta_content()
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


def test_evidence_only_delta_bounds_paths_and_content_before_hashing() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    too_many_paths = {
        f"repo-path-ref:docs/evals/report-{index}.json": b"safe" for index in range(33)
    }

    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref=too_many_paths,
    ) == ("failure-ref:taw08:evidence-delta-path-bound-exceeded",)

    assert "failure-ref:taw08:evidence-delta-content-bound-exceeded" in (
        verify_evidence_only_delta(
            candidate_lock=lock,
            delta=delta,
            changed_content_by_path_ref={
                delta.entries[0].path_ref: (
                    b"x" * (TAW08_MAX_EVIDENCE_DELTA_ARTIFACT_BYTES + 1)
                )
            },
        )
    )


def test_evidence_only_delta_cannot_overlap_candidate_artifact() -> None:
    lock = _candidate_lock()
    candidate_path = lock.entries[0].path_ref
    content = _safe_delta_content()
    values = {
        "candidate_revision_ref": lock.git_revision_ref,
        "candidate_manifest_digest_ref": lock.manifest_digest_ref,
        "delta_revision_ref": DELTA_REVISION_REF,
        "entries": [
            {
                "path_ref": candidate_path,
                "artifact_kind": "immutable_evidence_refs",
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


def test_serialized_report_cannot_replace_validated_evidence_with_digest_refs() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        evidence_only_delta_verification_receipt=_delta_verification(lock, delta),
        postmerge_foundation_receipt=_foundation_receipt(
            stage="postmerge", revision_ref=DELTA_REVISION_REF
        ),
    )
    payload = report.model_dump(mode="json")
    payload["founder_evidence"] = None

    with pytest.raises(ValidationError, match="embedded evidence"):
        TAW08AcceptanceReport.model_validate(payload)

    payload = report.model_dump(mode="json")
    payload["postmerge_foundation_receipt"] = None
    with pytest.raises(ValidationError, match="embedded Foundation receipt"):
        TAW08AcceptanceReport.model_validate(payload)

    payload = report.model_dump(mode="json")
    payload["candidate_verification_receipt"] = None
    with pytest.raises(ValidationError, match="embedded receipt"):
        TAW08AcceptanceReport.model_validate(payload)

    payload = report.model_dump(mode="json")
    payload["evidence_only_delta_verification_receipt"] = None
    with pytest.raises(ValidationError, match="embedded receipt"):
        TAW08AcceptanceReport.model_validate(payload)


def test_postmerge_acceptance_requires_verified_evidence_delta() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        postmerge_foundation_receipt=_foundation_receipt(
            stage="postmerge", revision_ref=DELTA_REVISION_REF
        ),
    )

    assert report.status is TAW08AcceptanceStatus.failed
    assert not report.founder_private_accepted
    assert report.failure_refs == (
        "failure-ref:taw08:postmerge-delta-verification-missing",
    )


def test_founder_private_evidence_requires_explicit_accepted_outcome() -> None:
    lock = _candidate_lock()
    values = _founder_evidence(lock).model_dump(
        mode="json", exclude={"evidence_digest_ref"}
    )
    values["live_model_hardware_receipt_refs"] = tuple(
        values["live_model_hardware_receipt_refs"]
    )
    values["founder_decision_outcome"] = "rejected"

    with pytest.raises(ValidationError, match="founder_decision_outcome"):
        bind_founder_private_acceptance_evidence(**values)


def test_evidence_delta_rejects_malformed_or_unredacted_payloads() -> None:
    lock = _candidate_lock()
    malformed = b'{"raw_prompt":"secret"}'
    delta = _delta(lock, malformed)

    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={delta.entries[0].path_ref: malformed},
    ) == ("failure-ref:taw08:evidence-delta-artifact-schema-invalid",)


def test_candidate_binding_drift_returns_auditable_failed_report() -> None:
    lock = _candidate_lock()
    other_payload = {
        "candidate_ref": "candidate-ref:taw08:other:v1",
        "git_revision_ref": lock.git_revision_ref,
        "entries": [item.model_dump(mode="json") for item in lock.entries],
        "evidence_only_delta_path_refs": lock.evidence_only_delta_path_refs,
    }
    other_lock = CandidateLock(
        **other_payload,
        manifest_digest_ref=canonical_digest(other_payload),
    )

    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(other_lock),
    )

    assert report.status is TAW08AcceptanceStatus.failed
    assert report.failure_refs == (
        "failure-ref:taw08:founder-evidence-candidate-binding-drift",
    )


def test_candidate_verifier_rejects_incomplete_acceptance_path_census() -> None:
    lock = _candidate_lock()
    one_entry = (
        next(
            item
            for item in lock.entries
            if item.path_ref.startswith("repo-path-ref:src/")
        ),
    )
    values = {
        "candidate_ref": "candidate-ref:taw08:incomplete:v1",
        "git_revision_ref": lock.git_revision_ref,
        "entries": [item.model_dump(mode="json") for item in one_entry],
        "evidence_only_delta_path_refs": lock.evidence_only_delta_path_refs,
    }
    incomplete_lock = CandidateLock(
        **values,
        manifest_digest_ref=canonical_digest(values),
    )

    with pytest.raises(ValueError, match="path census is incomplete"):
        _candidate_verification(incomplete_lock)


def test_receipt_binders_reject_unknown_fields_before_model_construct() -> None:
    lock = _candidate_lock()
    with pytest.raises(ValueError, match="unknown builder fields"):
        bind_foundation_gate_receipt(
            stage="exact_head",
            revision_ref=lock.git_revision_ref,
            report_digest_ref="sha256:" + "3" * 64,
            report_ref="foundation-report-ref:taw08:exact-head",
            passsed=True,
        )

    with pytest.raises(ValueError, match="unknown builder fields"):
        bind_evidence_only_delta(
            candidate_revision_ref=lock.git_revision_ref,
            candidate_manifest_digest_ref=lock.manifest_digest_ref,
            delta_revision_ref=DELTA_REVISION_REF,
            entries=_delta(lock).entries,
            raw_report="not allowed",
        )

    founder_values = _founder_evidence(lock).model_dump(
        mode="json", exclude={"evidence_digest_ref"}
    )
    founder_values["live_model_hardware_receipt_refs"] = tuple(
        founder_values["live_model_hardware_receipt_refs"]
    )
    founder_values["raw_prompt"] = "not allowed"
    with pytest.raises(ValueError, match="unknown builder fields"):
        bind_founder_private_acceptance_evidence(**founder_values)


def test_python_310_compatible_string_enums_are_used() -> None:
    assert issubclass(TAW08AcceptanceStatus, str)
    assert TAW08AcceptanceStatus.blocked_missing_founder_evidence.value == (
        "blocked_missing_founder_evidence"
    )
