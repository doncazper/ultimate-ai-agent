from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

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
    FounderMeasurementKind,
    RevisionDeltaCensus,
    RevisionPathCensus,
    TAW08AcceptanceReport,
    TAW08AcceptanceStatus,
    bind_evidence_only_delta,
    bind_foundation_gate_receipt,
    bind_founder_measurement_receipt,
    bind_founder_private_acceptance_evidence,
    bind_revision_delta_census,
    bind_revision_path_census,
    evaluate_taw08_acceptance,
    redacted_acceptance_report_artifact,
    verify_and_bind_candidate_lock,
    verify_and_bind_evidence_only_delta,
    verify_evidence_only_delta,
)
from scripts.verify_tool_aware_cognition_taw08 import (
    EVIDENCE_ONLY_DELTA_PATHS,
    derive_revision_delta_census,
    derive_revision_path_census,
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


def _revision_path_census(path_refs: set[str]) -> RevisionPathCensus:
    return bind_revision_path_census(
        revision_ref=CANDIDATE_REVISION_REF,
        path_refs=tuple(sorted(path_refs)),
        provenance_ref="provenance-ref:git-ls-tree",
    )


def _revision_delta_census(path_refs: tuple[str, ...]) -> RevisionDeltaCensus:
    return bind_revision_delta_census(
        candidate_revision_ref=CANDIDATE_REVISION_REF,
        delta_revision_ref=DELTA_REVISION_REF,
        path_refs=tuple(sorted(path_refs)),
        provenance_ref="provenance-ref:git-diff-name-only",
    )


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
            "repo-path-ref:docs/evals/taw08_board_reconciliation.json",
            "repo-path-ref:docs/evals/taw08_release_truth_reconciliation.json",
        ),
    }
    return CandidateLock(
        candidate_ref=values["candidate_ref"],
        git_revision_ref=values["git_revision_ref"],
        entries=entries,
        evidence_only_delta_path_refs=values["evidence_only_delta_path_refs"],
        manifest_digest_ref=canonical_digest(values),
    )


def _candidate_verification(
    lock: CandidateLock, *, source_content_overrides: dict[str, bytes] | None = None
):
    expected_refs = tuple(item.path_ref for item in lock.entries)
    content_by_ref = dict.fromkeys(expected_refs, b"")
    locked_source_entries = tuple(
        item
        for item in lock.entries
        if item.path_ref.startswith("repo-path-ref:src/")
        and item.path_ref.endswith(".py")
    )
    source_content_overrides = source_content_overrides or {}
    source_content = {
        item.path_ref: source_content_overrides.get(item.path_ref, b"")
        for item in locked_source_entries
    }
    source_entries = tuple(
        CandidateManifestEntry(
            path_ref=item.path_ref,
            content_digest_ref=(
                f"sha256:{hashlib.sha256(source_content[item.path_ref]).hexdigest()}"
            ),
        )
        for item in locked_source_entries
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
    return verify_and_bind_candidate_lock(
        candidate_lock=lock,
        expected_path_refs=expected_refs,
        revision_content_by_path_ref=content_by_ref,
        source_projection=projection,
        source_closure=closure,
        closure_content_by_path_ref=source_content,
        revision_path_census=_revision_path_census(set(source_content)),
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


def _measurement_receipt(
    lock: CandidateLock,
    kind: FounderMeasurementKind,
    suffix: str,
):
    return bind_founder_measurement_receipt(
        measurement_kind=kind,
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        evidence_ref=f"evidence-ref:taw08:{suffix}",
        evidence_digest_ref="sha256:" + hashlib.sha256(suffix.encode()).hexdigest(),
    )


def _founder_evidence(lock: CandidateLock):
    return bind_founder_private_acceptance_evidence(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        stale_cache_recovery_receipt=_measurement_receipt(
            lock, FounderMeasurementKind.stale_cache_recovery, "stale-recovery"
        ),
        routing_confidence_receipt=_measurement_receipt(
            lock, FounderMeasurementKind.routing_confidence, "routing-confidence"
        ),
        response_scoring_receipt=_measurement_receipt(
            lock, FounderMeasurementKind.response_scoring, "response-scoring"
        ),
        live_model_hardware_receipts=(
            _measurement_receipt(
                lock, FounderMeasurementKind.live_model_hardware, "qwen-mac-run-1"
            ),
        ),
        end_to_end_journey_receipt=_measurement_receipt(
            lock, FounderMeasurementKind.end_to_end_journey, "end-to-end-journeys"
        ),
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
        revision_delta_census=_revision_delta_census(
            tuple(item.path_ref for item in delta.entries)
        ),
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
    values = _founder_evidence(lock).model_dump(
        mode="json", exclude={"evidence_digest_ref"}
    )
    values["exact_head_foundation_receipt"] = receipt

    with pytest.raises(ValidationError, match="must bind the candidate revision"):
        bind_founder_private_acceptance_evidence(**values)


def test_founder_evidence_rejects_duplicate_measurement_receipts() -> None:
    lock = _candidate_lock()
    values = _founder_evidence(lock).model_dump(
        mode="json", exclude={"evidence_digest_ref"}
    )
    measurement = values["live_model_hardware_receipts"][0]
    values["live_model_hardware_receipts"] = (measurement, measurement)

    with pytest.raises(ValidationError, match="must be unique"):
        bind_founder_private_acceptance_evidence(**values)


def test_evidence_only_delta_verifies_exact_allowed_content() -> None:
    lock = _candidate_lock()
    content = _safe_delta_content()
    delta = _delta(lock, content)

    assert (
        verify_evidence_only_delta(
            candidate_lock=lock,
            delta=delta,
            changed_content_by_path_ref={delta.entries[0].path_ref: content},
            revision_delta_census=_revision_delta_census(
                (delta.entries[0].path_ref,)
            ),
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
        revision_delta_census=_revision_delta_census(
            ("repo-path-ref:src/ultimate_ai_agent/core/runtime.py",)
        ),
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
        revision_delta_census=_revision_delta_census((delta.entries[0].path_ref,)),
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
            revision_delta_census=_revision_delta_census(
                (delta.entries[0].path_ref,)
            ),
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
        revision_delta_census=_revision_delta_census((candidate_path,)),
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
    values["live_model_hardware_receipts"] = tuple(
        values["live_model_hardware_receipts"]
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
        revision_delta_census=_revision_delta_census(
            (delta.entries[0].path_ref,)
        ),
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


def test_candidate_verifier_rejects_source_content_substitution() -> None:
    lock = _candidate_lock()
    source_ref = next(
        item.path_ref
        for item in lock.entries
        if item.path_ref.startswith("repo-path-ref:src/")
    )

    with pytest.raises(
        ValueError, match="candidate-source-(projection|closure)-content-drift"
    ):
        _candidate_verification(
            lock,
            source_content_overrides={source_ref: b"substituted = True\n"},
        )


def test_delta_verifier_requires_revision_derived_path_census() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    omitted_revision_change = "repo-path-ref:src/ultimate_ai_agent/core/runtime.py"

    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={delta.entries[0].path_ref: _safe_delta_content()},
        revision_delta_census=_revision_delta_census(
            (delta.entries[0].path_ref, omitted_revision_change)
        ),
    ) == ("failure-ref:taw08:revision-delta-path-census-drift",)


def test_delta_verification_receipt_binds_revision_path_census() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    receipt = _delta_verification(lock, delta)
    receipt_payload = receipt.model_dump(mode="json", exclude={"receipt_digest_ref"})
    receipt_payload["revision_delta_path_census_digest_ref"] = "sha256:" + "f" * 64
    substituted_receipt = type(receipt).model_validate(
        {
            **receipt_payload,
            "receipt_digest_ref": canonical_digest(receipt_payload),
        }
    )

    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        evidence_only_delta_verification_receipt=substituted_receipt,
    )

    assert report.status is TAW08AcceptanceStatus.failed
    assert report.failure_refs == (
        "failure-ref:taw08:delta-verification-binding-drift",
    )


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
    founder_values["live_model_hardware_receipts"] = tuple(
        founder_values["live_model_hardware_receipts"]
    )
    founder_values["raw_prompt"] = "not allowed"
    with pytest.raises(ValueError, match="unknown builder fields"):
        bind_founder_private_acceptance_evidence(**founder_values)


def test_repository_censuses_are_derived_from_named_git_revisions(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git("init")
    git("config", "user.name", "TAW-08 Test")
    git("config", "user.email", "taw08@example.invalid")
    source = repository / "src/ultimate_ai_agent/core"
    source.mkdir(parents=True)
    (source / "dependency.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / "root.py").write_text(
        "from ultimate_ai_agent.core import dependency\n",
        encoding="utf-8",
    )
    git("add", ".")
    git("commit", "-m", "candidate")
    candidate = git("rev-parse", "HEAD")
    evidence = repository / "docs/evals/evidence.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("{}\n", encoding="utf-8")
    (source / "root.py").write_text(
        "from ultimate_ai_agent.core import dependency\nCHANGED = True\n",
        encoding="utf-8",
    )
    git("add", ".")
    git("commit", "-m", "delta")
    delta = git("rev-parse", "HEAD")

    path_census = derive_revision_path_census(
        f"git-sha:{candidate}", repository_root=repository
    )
    assert "repo-path-ref:src/ultimate_ai_agent/core/dependency.py" in (
        path_census.path_refs
    )
    delta_census = derive_revision_delta_census(
        f"git-sha:{candidate}",
        f"git-sha:{delta}",
        repository_root=repository,
    )
    assert delta_census.path_refs == (
        "repo-path-ref:docs/evals/evidence.json",
        "repo-path-ref:src/ultimate_ai_agent/core/root.py",
    )


def test_schema_valid_secret_like_evidence_is_rejected() -> None:
    lock = _candidate_lock()
    content = json.dumps(
        {
            "schema_version": "uaa-taw08-immutable-evidence-refs.v1",
            "evidence_refs": [
                "evidence-ref:ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
            ],
            "raw_content_persisted": False,
        }
    ).encode()
    delta = _delta(lock, content)

    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={delta.entries[0].path_ref: content},
        revision_delta_census=_revision_delta_census(
            (delta.entries[0].path_ref,)
        ),
    ) == ("failure-ref:taw08:evidence-delta-artifact-schema-invalid",)


def test_founder_measurement_receipts_bind_the_candidate() -> None:
    lock = _candidate_lock()
    other_values = {
        "candidate_ref": "candidate-ref:taw08:other-measurements:v1",
        "git_revision_ref": lock.git_revision_ref,
        "entries": [item.model_dump(mode="json") for item in lock.entries],
        "evidence_only_delta_path_refs": lock.evidence_only_delta_path_refs,
    }
    other_lock = CandidateLock(
        **other_values,
        manifest_digest_ref=canonical_digest(other_values),
    )
    values = _founder_evidence(lock).model_dump(
        mode="json", exclude={"evidence_digest_ref"}
    )
    values["routing_confidence_receipt"] = _measurement_receipt(
        other_lock,
        FounderMeasurementKind.routing_confidence,
        "other-routing-confidence",
    )

    with pytest.raises(ValidationError, match="candidate binding drift"):
        bind_founder_private_acceptance_evidence(**values)


def test_redacted_acceptance_artifact_binds_a_validated_report() -> None:
    lock = _candidate_lock()
    report = evaluate_taw08_acceptance(candidate_lock=lock)
    artifact = redacted_acceptance_report_artifact(report)
    content = json.dumps(
        artifact.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode()
    path_ref = "repo-path-ref:docs/evals/taw08_acceptance_report.json"
    delta = bind_evidence_only_delta(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        delta_revision_ref=DELTA_REVISION_REF,
        entries=(
            EvidenceOnlyDeltaEntry(
                path_ref=path_ref,
                artifact_kind="acceptance_report",
                content_digest_ref=f"sha256:{hashlib.sha256(content).hexdigest()}",
            ),
        ),
    )
    census = _revision_delta_census((path_ref,))

    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={path_ref: content},
        revision_delta_census=census,
        validated_acceptance_reports_by_path_ref={path_ref: report},
    ) == ()
    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={path_ref: content},
        revision_delta_census=census,
    ) == (
        "failure-ref:taw08:evidence-delta-acceptance-report-binding-drift",
    )


def test_reconciliation_paths_are_structured_json_not_markdown() -> None:
    assert all(path.endswith(".json") for path in EVIDENCE_ONLY_DELTA_PATHS)
    assert "docs/kanban/current_board.md" not in EVIDENCE_ONLY_DELTA_PATHS
    assert "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md" not in (
        EVIDENCE_ONLY_DELTA_PATHS
    )


def test_wrong_postmerge_stage_returns_a_failed_report() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        evidence_only_delta_verification_receipt=_delta_verification(lock, delta),
        postmerge_foundation_receipt=_foundation_receipt(stage="exact_head"),
    )

    assert report.status is TAW08AcceptanceStatus.failed
    assert report.founder_evidence_missing_refs == ()
    assert report.failure_refs == (
        "failure-ref:taw08:postmerge-delta-revision-drift",
        "failure-ref:taw08:postmerge-foundation-stage-drift",
    )


def test_python_310_compatible_string_enums_are_used() -> None:
    assert issubclass(TAW08AcceptanceStatus, str)
    assert TAW08AcceptanceStatus.blocked_missing_founder_evidence.value == (
        "blocked_missing_founder_evidence"
    )
