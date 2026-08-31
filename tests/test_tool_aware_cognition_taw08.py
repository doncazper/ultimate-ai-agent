from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

import ultimate_ai_agent.core.evals as evals_api
from scripts import run_foundation_gate as foundation_runner
from ultimate_ai_agent.core.evals.tool_aware_acceptance import (
    _bind_publication_history_census,
    _verify_and_bind_final_acceptance_publication,
    _verify_and_bind_foundation_gate_report,
    TAW08_FOUNDER_EVIDENCE_MISSING_REFS,
    TAW08_INDEPENDENT_PROMOTION_BLOCKER_REFS,
    TAW08_ACCEPTANCE_REPORT_PATH_REF,
    TAW08_FOUNDER_MEASUREMENT_SPECS,
    TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
    TAW08_FINAL_PUBLICATION_MISSING_REF,
    TAW08_RECONCILIATION_END,
    TAW08_RECONCILIATION_JSON,
    TAW08_RECONCILIATION_NARRATIVES,
    TAW08_RECONCILIATION_START,
    TAW08_DELTA_VERIFICATION_MISSING_REF,
    TAW08_MAX_EVIDENCE_DELTA_ARTIFACT_BYTES,
    TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
    TAW08_REQUIRED_ACCEPTANCE_PATH_REFS,
    EvidenceOnlyDeltaEntry,
    EvidenceOnlyDeltaManifest,
    EvidenceOnlyDeltaVerificationReceipt,
    FinalAcceptancePublicationArtifact,
    FinalAcceptancePublicationReceipt,
    FoundationGateReceipt,
    FounderMeasurementKind,
    FounderMeasurementObservation,
    FounderMeasurementResult,
    PublicationHistoryCensus,
    RevisionDeltaCensus,
    RevisionPathCensus,
    TAW08AcceptanceReport,
    TAW08AcceptanceStatus,
    bind_evidence_only_delta,
    build_final_acceptance_publication_artifact,
    bind_founder_private_acceptance_evidence,
    bind_revision_delta_census,
    bind_revision_path_census,
    evaluate_taw08_acceptance,
    redacted_acceptance_report_artifact,
    verify_and_bind_candidate_lock,
    verify_and_bind_evidence_only_delta,
    verify_and_bind_founder_measurement_result,
    verify_evidence_only_delta,
)
from ultimate_ai_agent.core.gate.enums import FoundationGateStatus
from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.reports import (
    FoundationGateCommandReceipt,
    FoundationGateReport,
    FoundationGateResult,
    build_foundation_gate_report,
    foundation_gate_evaluation_provenance_digest,
)
from scripts.verify_tool_aware_cognition_taw08 import (
    EVIDENCE_ONLY_DELTA_PATHS,
    derive_publication_history_census,
    derive_revision_delta_census,
    derive_revision_path_census,
    verify_repository_candidate,
    verify_repository_final_acceptance_publication,
    verify_repository_foundation_gate,
)
from scripts.run_foundation_gate import exact_repository_revision
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
PUBLICATION_REVISION_REF = "git-sha:" + "3" * 40
BOARD_PATH_REF = "repo-path-ref:docs/kanban/current_board.md"
RELEASE_PATH_REF = (
    "repo-path-ref:docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
)


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
        history_path_refs=tuple(sorted(path_refs)),
        commit_count=1,
        candidate_ancestor_verified=True,
        provenance_ref="provenance-ref:git-history-path-census",
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
            TAW08_ACCEPTANCE_REPORT_PATH_REF,
            TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
            "repo-path-ref:docs/evals/tool_aware_cognition_taw08_board_reconciliation_v1.json",
            "repo-path-ref:docs/evals/tool_aware_cognition_taw08_release_truth_reconciliation_v1.json",
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


def _candidate_verification(
    lock: CandidateLock,
    *,
    source_content_overrides: dict[str, bytes] | None = None,
    candidate_content_overrides: dict[str, bytes] | None = None,
):
    expected_refs = tuple(item.path_ref for item in lock.entries)
    content_by_ref = dict.fromkeys(expected_refs, b"")
    content_by_ref.update(candidate_content_overrides or {})
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


@lru_cache(maxsize=8)
def _unbound_foundation_gate_report():
    checked_at = datetime(2026, 8, 30, tzinfo=timezone.utc)
    return build_foundation_gate_report(
        version="0.104.0",
        results=[
            FoundationGateResult(
                criterion_id=criterion.criterion_id,
                status=FoundationGateStatus.passed,
                safe_message="Canonical Foundation criterion passed.",
                evidence_refs=["evidence-ref:taw08:foundation-census"],
                checked_at=checked_at,
            )
            for criterion in default_foundation_gate_criteria()
        ],
        command_mode="report-only",
        command_receipts=[
            FoundationGateCommandReceipt(
                command_ref="command:foundation_gate.typed_report",
                command_mode="report-only",
                status="report_only",
                satisfied_by="typed-foundation-gate-evaluator",
                safe_summary=(
                    "Evaluated canonical criteria with local read/probe code."
                ),
                return_code=0,
                checked_at=checked_at,
            )
        ],
    )


@lru_cache(maxsize=8)
def _foundation_gate_report(revision_ref: str = CANDIDATE_REVISION_REF):
    return _bind_test_foundation_provenance(
        _unbound_foundation_gate_report(), revision_ref
    )


def _bind_test_foundation_provenance(
    report: FoundationGateReport,
    revision_ref: str,
) -> FoundationGateReport:
    """Build an internal unit fixture; production exposes no report-label binder."""

    bound = report.model_copy(update={"evaluated_revision_ref": revision_ref})
    return bound.model_copy(
        update={
            "evaluation_provenance_digest_ref": (
                foundation_gate_evaluation_provenance_digest(bound)
            )
        }
    )


def _foundation_receipt(
    *, stage: str = "exact_head", revision_ref: str = CANDIDATE_REVISION_REF
) -> FoundationGateReceipt:
    return _verify_and_bind_foundation_gate_report(
        report=_foundation_gate_report(revision_ref),
        stage=stage,
        revision_ref=revision_ref,
    )


def _measurement_receipt(
    lock: CandidateLock,
    kind: FounderMeasurementKind,
    suffix: str,
):
    specs = TAW08_FOUNDER_MEASUREMENT_SPECS[kind]
    live_identity = (
        {
            "model_profile_ref": "model-profile-ref:qwen-3.8-27b-128k",
            "model_artifact_or_configuration_ref": (
                "model-artifact-ref:qwen-3.8-27b:test-fixture"
            ),
            "context_profile_ref": "context-profile-ref:128k",
            "backend_ref": "backend-ref:test-local-runtime",
            "observed_hardware_ref": "hardware-ref:test-workstation",
        }
        if kind is FounderMeasurementKind.live_model_hardware
        else {}
    )
    result = FounderMeasurementResult(
        measurement_kind=kind,
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        evidence_ref=f"evidence-ref:taw08:{suffix}",
        observations=tuple(
            FounderMeasurementObservation(
                stratum_ref=stratum_ref,
                metric_ref=metric_ref,
                observed_value=0.99,
                observation_count=minimum_denominator,
                minimum_denominator=minimum_denominator,
                threshold_ref=threshold_ref,
                threshold_operator=operator,
                threshold_value=threshold_value,
                unit_ref=unit_ref,
            )
            for (
                stratum_ref,
                metric_ref,
                threshold_ref,
                operator,
                threshold_value,
                unit_ref,
                minimum_denominator,
            ) in specs
        ),
        observation_count=sum(item[6] for item in specs),
        threshold_decision="passed",
        **live_identity,
    )
    return verify_and_bind_founder_measurement_result(result)


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


def _pre_delta_report(lock: CandidateLock) -> TAW08AcceptanceReport:
    return evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
    )


def _safe_delta_content(lock: CandidateLock) -> bytes:
    artifact = redacted_acceptance_report_artifact(_pre_delta_report(lock))
    return json.dumps(
        artifact.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _reconciliation_content(path_ref: str, *, status: str) -> bytes:
    artifact = {
        "entries": [
            {
                "claim_ref": (
                    "claim-ref:queue-v2/Q22/taw08-current-board"
                    if path_ref == BOARD_PATH_REF
                    else "claim-ref:queue-v2/Q22/taw08-release-truth"
                ),
                "evidence_refs": (
                    ["evidence-ref:taw08:founder-private-accepted"]
                    if status == "implemented"
                    else []
                ),
                "status": status,
            }
        ],
        "raw_content_persisted": False,
        "schema_version": "uaa-taw08-claim-reconciliation.v1",
    }
    return (
        "unchanged-prefix\n"
        f"{TAW08_RECONCILIATION_START}\n"
        f"{TAW08_RECONCILIATION_NARRATIVES[path_ref][status]}\n"
        f"{TAW08_RECONCILIATION_JSON}\n"
        f"{json.dumps(artifact, sort_keys=True, separators=(',', ':'))}\n"
        f"{TAW08_RECONCILIATION_END}\n"
        "unchanged-suffix\n"
    ).encode()


def _delta_contents(
    lock: CandidateLock, acceptance_content: bytes | None = None
) -> dict[str, bytes]:
    return {
        TAW08_ACCEPTANCE_REPORT_PATH_REF: (
            _safe_delta_content(lock)
            if acceptance_content is None
            else acceptance_content
        ),
        BOARD_PATH_REF: _reconciliation_content(BOARD_PATH_REF, status="implemented"),
        RELEASE_PATH_REF: _reconciliation_content(
            RELEASE_PATH_REF, status="implemented"
        ),
    }


def _candidate_truth_contents() -> dict[str, bytes]:
    return {
        BOARD_PATH_REF: _reconciliation_content(BOARD_PATH_REF, status="blocked"),
        RELEASE_PATH_REF: _reconciliation_content(RELEASE_PATH_REF, status="blocked"),
    }


def _delta(lock: CandidateLock, content: bytes | None = None):
    contents = _delta_contents(lock, content)
    return bind_evidence_only_delta(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        delta_revision_ref=DELTA_REVISION_REF,
        entries=tuple(
            EvidenceOnlyDeltaEntry(
                path_ref=path_ref,
                artifact_kind=(
                    "acceptance_report"
                    if path_ref == TAW08_ACCEPTANCE_REPORT_PATH_REF
                    else "claim_reconciliation"
                ),
                content_digest_ref=f"sha256:{hashlib.sha256(value).hexdigest()}",
            )
            for path_ref, value in sorted(contents.items())
        ),
    )


def _delta_verification(lock: CandidateLock, delta: EvidenceOnlyDeltaManifest):
    report = _pre_delta_report(lock)
    contents = _delta_contents(lock)
    return verify_and_bind_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref=contents,
        revision_delta_census=_revision_delta_census(
            tuple(item.path_ref for item in delta.entries)
        ),
        candidate_content_by_path_ref=_candidate_truth_contents(),
        validated_acceptance_reports_by_path_ref={
            TAW08_ACCEPTANCE_REPORT_PATH_REF: report
        },
    )


def _postmerge_receipt() -> FoundationGateReceipt:
    return _foundation_receipt(stage="postmerge", revision_ref=DELTA_REVISION_REF)


def _publication_history_census(
    *,
    delta_revision_ref: str = DELTA_REVISION_REF,
    publication_revision_ref: str = PUBLICATION_REVISION_REF,
) -> PublicationHistoryCensus:
    return _bind_publication_history_census(
        delta_revision_ref=delta_revision_ref,
        publication_revision_ref=publication_revision_ref,
        path_refs=(TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,),
        history_path_refs=(TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,),
        commit_count=1,
        delta_ancestor_verified=True,
        provenance_ref="provenance-ref:git-history-path-census",
    )


def _final_publication(
    lock: CandidateLock, delta: EvidenceOnlyDeltaManifest
) -> FinalAcceptancePublicationReceipt:
    verification = _delta_verification(lock, delta)
    artifact = build_final_acceptance_publication_artifact(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        founder_evidence_digest_ref=_founder_evidence(lock).evidence_digest_ref,
        delta=delta,
        delta_verification_receipt=verification,
        postmerge_foundation_receipt=_postmerge_receipt(),
    )
    content = json.dumps(
        artifact.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return _verify_and_bind_final_acceptance_publication(
        publication_revision_ref=PUBLICATION_REVISION_REF,
        publication_path_ref=TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
        publication_content=content,
        publication_history_census=_publication_history_census(),
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        founder_evidence_digest_ref=_founder_evidence(lock).evidence_digest_ref,
        delta=delta,
        delta_verification_receipt=verification,
        postmerge_foundation_receipt=_postmerge_receipt(),
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
                TAW08_FINAL_PUBLICATION_MISSING_REF,
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
    assert report.founder_evidence_missing_refs == tuple(
        sorted(
            (
                TAW08_FINAL_PUBLICATION_MISSING_REF,
                TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
            )
        )
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
        postmerge_foundation_receipt=_postmerge_receipt(),
    )

    assert report.status == (
        TAW08AcceptanceStatus.founder_private_accepted_final_publication_pending
    )
    assert report.founder_private_accepted
    assert report.founder_evidence_missing_refs == (
        TAW08_FINAL_PUBLICATION_MISSING_REF,
    )
    assert not report.independent_promotion_ready


def test_final_publication_advances_only_founder_private_status() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        evidence_only_delta_verification_receipt=_delta_verification(lock, delta),
        postmerge_foundation_receipt=_postmerge_receipt(),
        final_acceptance_publication_receipt=_final_publication(lock, delta),
    )

    assert report.status == (
        TAW08AcceptanceStatus.founder_private_accepted_promotion_blocked
    )
    assert report.founder_evidence_missing_refs == ()
    assert not report.independent_promotion_ready


def test_final_publication_requires_exact_durable_artifact_bytes() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    verification = _delta_verification(lock, delta)
    artifact = build_final_acceptance_publication_artifact(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        founder_evidence_digest_ref=_founder_evidence(lock).evidence_digest_ref,
        delta=delta,
        delta_verification_receipt=verification,
        postmerge_foundation_receipt=_postmerge_receipt(),
    )
    assert isinstance(artifact, FinalAcceptancePublicationArtifact)
    substituted = artifact.model_dump(mode="json")
    substituted["delta_manifest_digest_ref"] = "sha256:" + "f" * 64
    content = json.dumps(substituted, sort_keys=True, separators=(",", ":")).encode()

    with pytest.raises(ValueError, match="artifact binding drift"):
        _verify_and_bind_final_acceptance_publication(
            publication_revision_ref=PUBLICATION_REVISION_REF,
            publication_path_ref=TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,
            publication_content=content,
            publication_history_census=_publication_history_census(),
            candidate_revision_ref=lock.git_revision_ref,
            candidate_manifest_digest_ref=lock.manifest_digest_ref,
            founder_evidence_digest_ref=_founder_evidence(lock).evidence_digest_ref,
            delta=delta,
            delta_verification_receipt=verification,
            postmerge_foundation_receipt=_postmerge_receipt(),
        )

    with pytest.raises(ValueError, match="path is not canonical"):
        _verify_and_bind_final_acceptance_publication(
            publication_revision_ref=PUBLICATION_REVISION_REF,
            publication_path_ref="repo-path-ref:docs/evals/substituted.json",
            publication_content=b"{}",
            publication_history_census=_publication_history_census(),
            candidate_revision_ref=lock.git_revision_ref,
            candidate_manifest_digest_ref=lock.manifest_digest_ref,
            founder_evidence_digest_ref=_founder_evidence(lock).evidence_digest_ref,
            delta=delta,
            delta_verification_receipt=verification,
            postmerge_foundation_receipt=_postmerge_receipt(),
        )


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


def test_final_acceptance_rejects_substituted_published_report() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    values = _delta_verification(lock, delta).model_dump(
        mode="json", exclude={"receipt_digest_ref"}
    )
    values["published_acceptance_report_fingerprint_ref"] = (
        evaluate_taw08_acceptance(candidate_lock=lock).report_fingerprint_ref
    )
    receipt = EvidenceOnlyDeltaVerificationReceipt.model_validate(
        {**values, "receipt_digest_ref": canonical_digest(values)}
    )

    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=_candidate_verification(lock),
        founder_evidence=_founder_evidence(lock),
        evidence_only_delta=delta,
        evidence_only_delta_verification_receipt=receipt,
        postmerge_foundation_receipt=_foundation_receipt(
            stage="postmerge", revision_ref=DELTA_REVISION_REF
        ),
    )

    assert report.status is TAW08AcceptanceStatus.failed
    assert report.failure_refs == (
        "failure-ref:taw08:published-acceptance-report-binding-drift",
    )


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
    content = _safe_delta_content(lock)
    delta = _delta(lock, content)
    contents = _delta_contents(lock, content)

    assert (
        verify_evidence_only_delta(
            candidate_lock=lock,
            delta=delta,
            changed_content_by_path_ref=contents,
            revision_delta_census=_revision_delta_census(
                tuple(sorted(contents))
            ),
            candidate_content_by_path_ref=_candidate_truth_contents(),
            validated_acceptance_reports_by_path_ref={
                TAW08_ACCEPTANCE_REPORT_PATH_REF: _pre_delta_report(lock)
            },
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
        "failure-ref:taw08:revision-history-unapproved-path",
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
    content = _safe_delta_content(lock)
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
        "failure-ref:taw08:active-truth-reconciliation-missing",
        "failure-ref:taw08:evidence-delta-acceptance-path-overlap",
        "failure-ref:taw08:evidence-delta-acceptance-report-missing",
        "failure-ref:taw08:evidence-delta-artifact-schema-invalid",
        "failure-ref:taw08:evidence-delta-unapproved-path",
        "failure-ref:taw08:revision-history-unapproved-path",
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
    with pytest.raises(ValueError, match="exact Git revision"):
        _verify_and_bind_foundation_gate_report(
            report=_foundation_gate_report(),
            stage="exact_head",
            revision_ref="git-sha:short",
        )


def test_foundation_receipt_requires_validated_gate_output() -> None:
    with pytest.raises(ValueError, match="typed gate report"):
        _verify_and_bind_foundation_gate_report(
            report=object(),
            stage="exact_head",
            revision_ref=CANDIDATE_REVISION_REF,
        )


def test_foundation_provenance_and_receipt_issuance_are_runner_scoped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    assert "evaluated_revision_ref" not in inspect.signature(
        build_foundation_gate_report
    ).parameters
    assert not hasattr(evals_api, "verify_and_bind_foundation_gate_report")
    assert not hasattr(evals_api, "verify_and_bind_final_acceptance_publication")
    assert not hasattr(
        foundation_runner, "bind_foundation_gate_execution_report"
    )

    observed_roots: list[Path] = []

    def exact_revision(repository_root: Path) -> str:
        observed_roots.append(repository_root)
        return CANDIDATE_REVISION_REF

    class FakeEvaluator:
        def __init__(self, repository_root: Path) -> None:
            assert repository_root == tmp_path

        def evaluate(self):
            return _unbound_foundation_gate_report()

    monkeypatch.setattr(foundation_runner, "exact_repository_revision", exact_revision)
    monkeypatch.setattr(foundation_runner, "FoundationGateEvaluator", FakeEvaluator)

    receipt = verify_repository_foundation_gate(
        stage="exact_head",
        repository_root=tmp_path,
    )
    assert receipt.revision_ref == CANDIDATE_REVISION_REF
    assert receipt.stage == "exact_head"
    assert observed_roots == [tmp_path, tmp_path]


def test_foundation_receipt_requires_complete_canonical_census() -> None:
    incomplete = _bind_test_foundation_provenance(
        build_foundation_gate_report(
            version="0.104.0",
            results=[
                FoundationGateResult(
                    criterion_id="taw08-invented-criterion",
                    status=FoundationGateStatus.passed,
                    safe_message="Invented criterion passed.",
                    evidence_refs=["evidence-ref:taw08:invented"],
                    checked_at=datetime(2026, 8, 30, tzinfo=timezone.utc),
                )
            ],
            command_mode="report-only",
            command_receipts=_foundation_gate_report().command_receipts,
        ),
        CANDIDATE_REVISION_REF,
    )
    with pytest.raises(ValueError, match="passing report-only gate"):
        _verify_and_bind_foundation_gate_report(
            report=incomplete,
            stage="exact_head",
            revision_ref=CANDIDATE_REVISION_REF,
        )

    lookalike_type = type(
        "FoundationGateReport",
        (),
        {
            "__module__": "ultimate_ai_agent.core.gate.reports",
            "model_dump": lambda self, **_: {},
        },
    )
    with pytest.raises(ValueError, match="typed gate report"):
        _verify_and_bind_foundation_gate_report(
            report=lookalike_type(),
            stage="exact_head",
            revision_ref=CANDIDATE_REVISION_REF,
        )

    empty_report = _bind_test_foundation_provenance(
        build_foundation_gate_report(
            version="0.104.0",
            results=[],
            command_mode="report-only",
        ),
        CANDIDATE_REVISION_REF,
    )
    with pytest.raises(ValueError, match="passing report-only gate"):
        _verify_and_bind_foundation_gate_report(
            report=empty_report,
            stage="exact_head",
            revision_ref=CANDIDATE_REVISION_REF,
        )


def test_foundation_receipt_rejects_report_from_another_revision() -> None:
    with pytest.raises(ValueError, match="revision provenance drift"):
        _verify_and_bind_foundation_gate_report(
            report=_foundation_gate_report("git-sha:" + "9" * 40),
            stage="exact_head",
            revision_ref=CANDIDATE_REVISION_REF,
        )


def test_foundation_revision_provenance_is_immutable_and_digest_bound() -> None:
    report = _foundation_gate_report()
    with pytest.raises(ValidationError, match="frozen"):
        report.evaluated_revision_ref = "git-sha:" + "8" * 40

    rebound = report.model_copy(
        update={"evaluated_revision_ref": "git-sha:" + "8" * 40}
    )
    with pytest.raises(ValueError, match="revision provenance drift"):
        _verify_and_bind_foundation_gate_report(
            report=rebound,
            stage="exact_head",
            revision_ref="git-sha:" + "8" * 40,
        )


def test_foundation_revision_provenance_requires_clean_worktree(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "foundation-revision"
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
    tracked = repository / "tracked.txt"
    tracked.write_text("clean\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "candidate")
    assert exact_repository_revision(repository) == (
        f"git-sha:{git('rev-parse', 'HEAD')}"
    )

    tracked.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="requires a clean worktree"):
        exact_repository_revision(repository)


def test_foundation_exact_revision_mode_rejects_non_repository_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(RuntimeError, match="requires the repository root"):
        exact_repository_revision(tmp_path)


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

    contents = _delta_contents(lock, malformed)
    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref=contents,
        candidate_content_by_path_ref=_candidate_truth_contents(),
        revision_delta_census=_revision_delta_census(tuple(sorted(contents))),
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


def test_candidate_verifier_locks_resolved_evaluator_environment() -> None:
    lock = _candidate_lock()
    environment_ref = "repo-path-ref:pyproject.toml"
    environment_content = b"[project]\nrequires-python = '>=3.10'\n"
    entries = tuple(
        item.model_copy(
            update={
                "content_digest_ref": (
                    f"sha256:{hashlib.sha256(environment_content).hexdigest()}"
                )
            }
        )
        if item.path_ref == environment_ref
        else item
        for item in lock.entries
    )
    values = {
        "candidate_ref": lock.candidate_ref,
        "git_revision_ref": lock.git_revision_ref,
        "entries": [item.model_dump(mode="json") for item in entries],
        "evidence_only_delta_path_refs": lock.evidence_only_delta_path_refs,
    }
    changed_lock = CandidateLock(
        **values,
        manifest_digest_ref=canonical_digest(values),
    )

    baseline = _candidate_verification(lock)
    changed = _candidate_verification(
        changed_lock,
        candidate_content_overrides={environment_ref: environment_content},
    )
    assert changed.evaluator_environment_digest_ref != (
        baseline.evaluator_environment_digest_ref
    )


def test_delta_verifier_requires_revision_derived_path_census() -> None:
    lock = _candidate_lock()
    delta = _delta(lock)
    omitted_revision_change = "repo-path-ref:src/ultimate_ai_agent/core/runtime.py"

    contents = _delta_contents(lock)
    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref=contents,
        candidate_content_by_path_ref=_candidate_truth_contents(),
        revision_delta_census=_revision_delta_census(
            tuple(sorted((*contents, omitted_revision_change)))
        ),
        validated_acceptance_reports_by_path_ref={
            TAW08_ACCEPTANCE_REPORT_PATH_REF: _pre_delta_report(lock)
        },
    ) == (
        "failure-ref:taw08:revision-delta-path-census-drift",
        "failure-ref:taw08:revision-history-unapproved-path",
    )


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
    transient = repository / "src/ultimate_ai_agent/core/transient.py"
    transient.write_text("FORBIDDEN = True\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "transient forbidden change")
    transient.unlink()
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
    assert delta_census.history_path_refs == (
        "repo-path-ref:docs/evals/evidence.json",
        "repo-path-ref:src/ultimate_ai_agent/core/root.py",
        "repo-path-ref:src/ultimate_ai_agent/core/transient.py",
    )
    assert delta_census.commit_count == 2
    assert delta_census.candidate_ancestor_verified


def test_schema_valid_secret_like_evidence_is_rejected() -> None:
    lock = _candidate_lock()
    artifact = redacted_acceptance_report_artifact(_pre_delta_report(lock)).model_dump(
        mode="json"
    )
    artifact["report_fingerprint_ref"] = (
        "taw08-acceptance-report-ref:sk_live_abcdefghijklmnopqrstuv"
    )
    content = json.dumps(artifact).encode()
    delta = _delta(lock, content)

    contents = _delta_contents(lock, content)
    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref=contents,
        candidate_content_by_path_ref=_candidate_truth_contents(),
        revision_delta_census=_revision_delta_census(tuple(sorted(contents))),
    ) == ("failure-ref:taw08:evidence-delta-artifact-schema-invalid",)


def test_founder_measurement_recomputes_threshold_decision() -> None:
    lock = _candidate_lock()
    payload = _measurement_receipt(
        lock, FounderMeasurementKind.routing_confidence, "failed-routing"
    ).result.model_dump(mode="json")
    payload["observations"][0]["observed_value"] = 0.70
    payload["threshold_decision"] = "passed"
    with pytest.raises(ValidationError, match="threshold decision drift"):
        FounderMeasurementResult.model_validate(payload)


def test_founder_measurement_rejects_substituted_threshold_spec() -> None:
    lock = _candidate_lock()
    payload = _measurement_receipt(
        lock, FounderMeasurementKind.routing_confidence, "substituted-threshold"
    ).result.model_dump(mode="json")
    payload["observations"][0]["threshold_ref"] = (
        "threshold-ref:taw08:substituted:v1"
    )
    payload["observations"][0]["threshold_value"] = 0.50
    with pytest.raises(ValidationError, match="metric threshold census drift"):
        FounderMeasurementResult.model_validate(payload)


def test_founder_measurement_requires_complete_powered_stratum_census() -> None:
    lock = _candidate_lock()
    payload = _measurement_receipt(
        lock, FounderMeasurementKind.end_to_end_journey, "incomplete-census"
    ).result.model_dump(mode="json")
    payload["observations"].pop()
    payload["observation_count"] = sum(
        item["observation_count"] for item in payload["observations"]
    )
    with pytest.raises(ValidationError, match="metric threshold census drift"):
        FounderMeasurementResult.model_validate(payload)


def test_live_measurement_requires_exact_runtime_identity() -> None:
    lock = _candidate_lock()
    payload = _measurement_receipt(
        lock, FounderMeasurementKind.live_model_hardware, "identity-drift"
    ).result.model_dump(mode="json")
    payload["model_profile_ref"] = None
    with pytest.raises(ValidationError, match="identity census is incomplete"):
        FounderMeasurementResult.model_validate(payload)


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
    report = _pre_delta_report(lock)
    contents = _delta_contents(lock)
    delta = _delta(lock)
    census = _revision_delta_census(tuple(sorted(contents)))

    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref=contents,
        candidate_content_by_path_ref=_candidate_truth_contents(),
        revision_delta_census=census,
        validated_acceptance_reports_by_path_ref={
            TAW08_ACCEPTANCE_REPORT_PATH_REF: report
        },
    ) == ()
    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref=contents,
        candidate_content_by_path_ref=_candidate_truth_contents(),
        revision_delta_census=census,
    ) == (
        "failure-ref:taw08:evidence-delta-acceptance-report-binding-drift",
    )


def test_active_truth_reconciliation_is_bounded_to_machine_block() -> None:
    lock = _candidate_lock()
    report = _pre_delta_report(lock)
    delta = _delta(lock)
    contents = _delta_contents(lock)
    candidate_contents = _candidate_truth_contents()
    census = _revision_delta_census(tuple(sorted(contents)))
    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref=contents,
        candidate_content_by_path_ref=candidate_contents,
        revision_delta_census=census,
        validated_acceptance_reports_by_path_ref={
            TAW08_ACCEPTANCE_REPORT_PATH_REF: report
        },
    ) == ()
    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={
            **contents,
            BOARD_PATH_REF: contents[BOARD_PATH_REF].replace(
                b"unchanged-prefix", b"substituted-prefix"
            ),
        },
        candidate_content_by_path_ref=candidate_contents,
        revision_delta_census=census,
        validated_acceptance_reports_by_path_ref={
            TAW08_ACCEPTANCE_REPORT_PATH_REF: report
        },
    ) == (
        "failure-ref:taw08:evidence-delta-artifact-schema-invalid",
    )


def test_active_truth_reconciliation_must_publish_accepted_status() -> None:
    lock = _candidate_lock()
    contents = _delta_contents(lock)
    contents[BOARD_PATH_REF] = _reconciliation_content(
        BOARD_PATH_REF, status="blocked"
    )
    delta = bind_evidence_only_delta(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        delta_revision_ref=DELTA_REVISION_REF,
        entries=tuple(
            EvidenceOnlyDeltaEntry(
                path_ref=path_ref,
                artifact_kind=(
                    "acceptance_report"
                    if path_ref == TAW08_ACCEPTANCE_REPORT_PATH_REF
                    else "claim_reconciliation"
                ),
                content_digest_ref=f"sha256:{hashlib.sha256(value).hexdigest()}",
            )
            for path_ref, value in sorted(contents.items())
        ),
    )
    assert "failure-ref:taw08:active-truth-status-not-implemented" in (
        verify_evidence_only_delta(
            candidate_lock=lock,
            delta=delta,
            changed_content_by_path_ref=contents,
            candidate_content_by_path_ref=_candidate_truth_contents(),
            revision_delta_census=_revision_delta_census(tuple(sorted(contents))),
            validated_acceptance_reports_by_path_ref={
                TAW08_ACCEPTANCE_REPORT_PATH_REF: _pre_delta_report(lock)
            },
        )
    )


def test_evidence_delta_requires_canonical_acceptance_report() -> None:
    lock = _candidate_lock()
    content = json.dumps(
        {
            "schema_version": "uaa-taw08-immutable-evidence-refs.v1",
            "evidence_refs": ["evidence-ref:taw08:one"],
            "raw_content_persisted": False,
        }
    ).encode()
    path_ref = (
        "repo-path-ref:docs/evals/"
        "tool_aware_cognition_taw08_board_reconciliation_v1.json"
    )
    delta = bind_evidence_only_delta(
        candidate_revision_ref=lock.git_revision_ref,
        candidate_manifest_digest_ref=lock.manifest_digest_ref,
        delta_revision_ref=DELTA_REVISION_REF,
        entries=(
            EvidenceOnlyDeltaEntry(
                path_ref=path_ref,
                artifact_kind="immutable_evidence_refs",
                content_digest_ref=f"sha256:{hashlib.sha256(content).hexdigest()}",
            ),
        ),
    )
    assert verify_evidence_only_delta(
        candidate_lock=lock,
        delta=delta,
        changed_content_by_path_ref={path_ref: content},
        revision_delta_census=_revision_delta_census((path_ref,)),
    ) == (
        "failure-ref:taw08:active-truth-reconciliation-missing",
        "failure-ref:taw08:evidence-delta-acceptance-report-missing",
    )


def test_repository_candidate_wrapper_has_no_caller_content_override() -> None:
    parameters = inspect.signature(verify_repository_candidate).parameters
    assert "content_by_ref" not in parameters
    source = inspect.getsource(verify_repository_candidate)
    assert '"show"' in source
    assert "for item in lock.entries" in source
    publication_parameters = inspect.signature(
        verify_repository_final_acceptance_publication
    ).parameters
    assert "publication_content" not in publication_parameters
    publication_source = inspect.getsource(
        verify_repository_final_acceptance_publication
    )
    assert '"show"' in publication_source
    assert "TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF" in publication_source
    assert "derive_publication_history_census" in publication_source


def test_publication_history_requires_descendant_and_final_report_only(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "publication-history"
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
    baseline = repository / "baseline.txt"
    baseline.write_text("baseline\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "baseline")
    baseline_revision = git("rev-parse", "HEAD")

    delta_file = repository / "delta.txt"
    delta_file.write_text("delta\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "evidence delta")
    delta_revision = git("rev-parse", "HEAD")

    final_path = repository / TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF.removeprefix(
        "repo-path-ref:"
    )
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text("{}\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "final publication")
    publication_revision = git("rev-parse", "HEAD")

    census = derive_publication_history_census(
        f"git-sha:{delta_revision}",
        f"git-sha:{publication_revision}",
        repository_root=repository,
    )
    assert census.path_refs == (TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,)
    assert census.history_path_refs == (TAW08_FINAL_ACCEPTANCE_REPORT_PATH_REF,)

    git("checkout", "-b", "invalid-history", delta_revision)
    unrelated = repository / "unrelated.txt"
    unrelated.write_text("not publication\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "intervening unrelated change")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text("{}\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "final publication after unrelated change")
    invalid_publication_revision = git("rev-parse", "HEAD")
    with pytest.raises(ValidationError, match="at most 1 item"):
        derive_publication_history_census(
            f"git-sha:{delta_revision}",
            f"git-sha:{invalid_publication_revision}",
            repository_root=repository,
        )

    git("checkout", "-b", "non-descendant", baseline_revision)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text("{}\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "unrelated final publication")
    non_descendant_revision = git("rev-parse", "HEAD")
    with pytest.raises(ValueError, match="must descend"):
        derive_publication_history_census(
            f"git-sha:{delta_revision}",
            f"git-sha:{non_descendant_revision}",
            repository_root=repository,
        )


def test_repository_candidate_wrapper_derives_locked_bytes_from_git(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "locked-repo"
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
    for path_ref in TAW08_REQUIRED_ACCEPTANCE_PATH_REFS:
        path = repository / path_ref.removeprefix("repo-path-ref:")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    git("add", ".")
    git("commit", "-m", "locked candidate")
    revision_ref = f"git-sha:{git('rev-parse', 'HEAD')}"
    empty_digest = f"sha256:{hashlib.sha256(b'').hexdigest()}"
    entries = tuple(
        CandidateManifestEntry(path_ref=path_ref, content_digest_ref=empty_digest)
        for path_ref in TAW08_REQUIRED_ACCEPTANCE_PATH_REFS
    )
    values = {
        "candidate_ref": "candidate-ref:taw08:repository-byte-test:v1",
        "git_revision_ref": revision_ref,
        "entries": [item.model_dump(mode="json") for item in entries],
        "evidence_only_delta_path_refs": _candidate_lock().evidence_only_delta_path_refs,
    }
    lock = CandidateLock(
        **values,
        manifest_digest_ref=canonical_digest(values),
    )
    assert verify_repository_candidate(
        lock, repository_root=repository
    ).candidate_revision_ref == revision_ref

    substituted_entries = list(entries)
    substituted_entries[0] = substituted_entries[0].model_copy(
        update={"content_digest_ref": "sha256:" + "f" * 64}
    )
    substituted_values = {
        **values,
        "entries": [item.model_dump(mode="json") for item in substituted_entries],
    }
    substituted_lock = CandidateLock(
        **substituted_values,
        manifest_digest_ref=canonical_digest(substituted_values),
    )
    with pytest.raises(ValueError, match="candidate lock verification failed"):
        verify_repository_candidate(
            substituted_lock,
            repository_root=repository,
        )


def test_active_truth_paths_are_explicit_evidence_delta_surfaces() -> None:
    assert "docs/kanban/current_board.md" in EVIDENCE_ONLY_DELTA_PATHS
    assert "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md" in (
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
    assert report.founder_evidence_missing_refs == (
        TAW08_FINAL_PUBLICATION_MISSING_REF,
    )
    assert report.failure_refs == (
        "failure-ref:taw08:postmerge-delta-revision-drift",
        "failure-ref:taw08:postmerge-foundation-stage-drift",
    )


def test_python_310_compatible_string_enums_are_used() -> None:
    assert issubclass(TAW08AcceptanceStatus, str)
    assert TAW08AcceptanceStatus.blocked_missing_founder_evidence.value == (
        "blocked_missing_founder_evidence"
    )
