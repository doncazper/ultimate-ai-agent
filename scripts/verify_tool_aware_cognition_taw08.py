from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from ultimate_ai_agent.core.evals.tool_aware_acceptance import (
    TAW08_DELTA_VERIFICATION_MISSING_REF,
    TAW08_FOUNDER_EVIDENCE_MISSING_REFS,
    TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
    TAW08AcceptanceStatus,
    TAW08AcceptanceReport,
    TAW08_REQUIRED_ACCEPTANCE_PATH_REFS,
    CandidateLockVerificationReceipt,
    EvidenceOnlyDeltaManifest,
    EvidenceOnlyDeltaVerificationReceipt,
    RevisionDeltaCensus,
    RevisionPathCensus,
    bind_revision_delta_census,
    bind_revision_path_census,
    evaluate_taw08_acceptance,
    verify_and_bind_candidate_lock,
    verify_and_bind_evidence_only_delta,
)
from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    CandidateLock,
    CandidateManifestEntry,
    SourceDependencyClosure,
    SourceDependencyEntry,
    SourceProjection,
    canonical_digest,
    derive_local_python_dependencies,
    verify_candidate_lock,
)


ROOT = Path(__file__).resolve().parents[1]
SLICE_CANDIDATE_PATHS = tuple(
    sorted(
        {
            *(ref.removeprefix("repo-path-ref:") for ref in TAW08_REQUIRED_ACCEPTANCE_PATH_REFS),
            "docs/evals/TOOL_AWARE_COGNITION_TAW08_ACCEPTANCE.md",
            "scripts/verify_tool_aware_cognition_taw08.py",
            "src/ultimate_ai_agent/core/evals/__init__.py",
            "tests/test_tool_aware_cognition_taw08.py",
        }
    )
)
EVIDENCE_ONLY_DELTA_PATHS = (
    "docs/evals/tool_aware_cognition_taw08_acceptance_report_v1.json",
    "docs/evals/tool_aware_cognition_taw08_board_reconciliation_v1.json",
    "docs/evals/tool_aware_cognition_taw08_release_truth_reconciliation_v1.json",
)


def _git(*args: str, repository_root: Path = ROOT) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repository_root,
        check=True,
        capture_output=True,
    )
    return result.stdout


def derive_revision_path_census(
    revision_ref: str, *, repository_root: Path = ROOT
) -> RevisionPathCensus:
    revision = revision_ref.removeprefix("git-sha:")
    paths = tuple(
        sorted(
            f"repo-path-ref:{path}"
            for path in _git(
                "ls-tree",
                "-r",
                "--name-only",
                revision,
                repository_root=repository_root,
            )
            .decode("utf-8")
            .splitlines()
            if path
        )
    )
    return bind_revision_path_census(
        revision_ref=revision_ref,
        path_refs=paths,
        provenance_ref="provenance-ref:git-ls-tree",
    )


def derive_revision_delta_census(
    candidate_revision_ref: str,
    delta_revision_ref: str,
    *,
    repository_root: Path = ROOT,
) -> RevisionDeltaCensus:
    candidate = candidate_revision_ref.removeprefix("git-sha:")
    delta = delta_revision_ref.removeprefix("git-sha:")
    paths = tuple(
        sorted(
            f"repo-path-ref:{path}"
            for path in _git(
                "diff",
                "--name-only",
                "--no-renames",
                candidate,
                delta,
                "--",
                repository_root=repository_root,
            )
            .decode("utf-8")
            .splitlines()
            if path
        )
    )
    return bind_revision_delta_census(
        candidate_revision_ref=candidate_revision_ref,
        delta_revision_ref=delta_revision_ref,
        path_refs=paths,
        provenance_ref="provenance-ref:git-diff-name-only",
    )


def _candidate_lock(revision: str) -> tuple[CandidateLock, dict[str, bytes]]:
    entries: list[CandidateManifestEntry] = []
    content_by_ref: dict[str, bytes] = {}
    for path in SLICE_CANDIDATE_PATHS:
        comparison = subprocess.run(
            ["git", "diff", "--quiet", revision, "--", path],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if comparison.returncode == 1:
            raise RuntimeError(f"TAW-08 contract path is dirty at {revision}: {path}")
        if comparison.returncode != 0:
            raise RuntimeError(f"TAW-08 contract path comparison failed: {path}")
        content = _git("show", f"{revision}:{path}")
        path_ref = f"repo-path-ref:{path}"
        content_by_ref[path_ref] = content
        entries.append(
            CandidateManifestEntry(
                path_ref=path_ref,
                content_digest_ref=f"sha256:{hashlib.sha256(content).hexdigest()}",
            )
        )
    candidate_ref = "candidate-ref:taw08:contract-slice:v1"
    git_revision_ref = f"git-sha:{revision}"
    evidence_only_delta_path_refs = tuple(
        f"repo-path-ref:{path}" for path in EVIDENCE_ONLY_DELTA_PATHS
    )
    digest_payload = {
        "candidate_ref": candidate_ref,
        "git_revision_ref": git_revision_ref,
        "entries": [entry.model_dump(mode="json") for entry in entries],
        "evidence_only_delta_path_refs": evidence_only_delta_path_refs,
    }
    return (
        CandidateLock(
            candidate_ref=candidate_ref,
            git_revision_ref=git_revision_ref,
            entries=tuple(entries),
            manifest_digest_ref=canonical_digest(digest_payload),
            evidence_only_delta_path_refs=evidence_only_delta_path_refs,
        ),
        content_by_ref,
    )


def _source_evidence_from_git(
    lock: CandidateLock,
    revision_path_census: RevisionPathCensus,
    *,
    repository_root: Path = ROOT,
) -> tuple[SourceProjection, SourceDependencyClosure, dict[str, bytes]]:
    root_entries = tuple(
        item
        for item in lock.entries
        if item.path_ref.startswith("repo-path-ref:src/")
        and item.path_ref.endswith(".py")
    )
    projection_payload = {
        "schema_version": "uaa-taw00-source-projection.v1",
        "projection_ref": "source-projection-ref:taw08:repository-derived",
        "source_revision_ref": lock.git_revision_ref,
        "status": "transitive_dependency_closed",
        "entries": [item.model_dump(mode="json") for item in root_entries],
        "routing_changes_added": False,
        "prompt_changes_added": False,
        "runtime_model_calls_added": False,
        "authority_added": False,
    }
    projection = SourceProjection(
        **projection_payload,
        projection_digest_ref=canonical_digest(projection_payload),
    )
    revision = lock.git_revision_ref.removeprefix("git-sha:")
    available = set(revision_path_census.path_refs)
    content_by_ref: dict[str, bytes] = {}
    dependencies_by_ref: dict[str, tuple[str, ...]] = {}
    frontier = [item.path_ref for item in root_entries]
    while frontier:
        path_ref = frontier.pop()
        if path_ref in content_by_ref:
            continue
        path = path_ref.removeprefix("repo-path-ref:")
        content = _git(
            "show",
            f"{revision}:{path}",
            repository_root=repository_root,
        )
        content_by_ref[path_ref] = content
        dependencies = derive_local_python_dependencies(
            path_ref,
            content,
            available_path_refs=available,
        )
        dependencies_by_ref[path_ref] = dependencies
        frontier.extend(ref for ref in dependencies if ref not in content_by_ref)
    closure_entries = tuple(
        SourceDependencyEntry(
            path_ref=path_ref,
            content_digest_ref=(
                f"sha256:{hashlib.sha256(content_by_ref[path_ref]).hexdigest()}"
            ),
            dependency_path_refs=dependencies_by_ref[path_ref],
        )
        for path_ref in sorted(content_by_ref)
    )
    closure_payload = {
        "schema_version": "uaa-taw00-source-dependency-closure.v1",
        "source_revision_ref": lock.git_revision_ref,
        "source_projection_digest_ref": projection.projection_digest_ref,
        "root_path_refs": tuple(item.path_ref for item in root_entries),
        "entries": [item.model_dump(mode="json") for item in closure_entries],
    }
    closure = SourceDependencyClosure(
        **closure_payload,
        closure_digest_ref=canonical_digest(closure_payload),
    )
    return projection, closure, content_by_ref


def verify_repository_candidate(
    lock: CandidateLock,
    content_by_ref: dict[str, bytes],
    *,
    repository_root: Path = ROOT,
) -> CandidateLockVerificationReceipt:
    revision_path_census = derive_revision_path_census(
        lock.git_revision_ref,
        repository_root=repository_root,
    )
    projection, closure, closure_content = _source_evidence_from_git(
        lock,
        revision_path_census,
        repository_root=repository_root,
    )
    return verify_and_bind_candidate_lock(
        candidate_lock=lock,
        expected_path_refs=tuple(item.path_ref for item in lock.entries),
        revision_content_by_path_ref=content_by_ref,
        source_projection=projection,
        source_closure=closure,
        closure_content_by_path_ref=closure_content,
        revision_path_census=revision_path_census,
    )


def verify_repository_evidence_delta(
    *,
    candidate_lock: CandidateLock,
    delta: EvidenceOnlyDeltaManifest,
    validated_acceptance_reports_by_path_ref: dict[str, TAW08AcceptanceReport]
    | None = None,
    repository_root: Path = ROOT,
) -> EvidenceOnlyDeltaVerificationReceipt:
    census = derive_revision_delta_census(
        candidate_lock.git_revision_ref,
        delta.delta_revision_ref,
        repository_root=repository_root,
    )
    delta_revision = delta.delta_revision_ref.removeprefix("git-sha:")
    content_by_ref = {
        path_ref: _git(
            "show",
            f"{delta_revision}:{path_ref.removeprefix('repo-path-ref:')}",
            repository_root=repository_root,
        )
        for path_ref in census.path_refs
    }
    return verify_and_bind_evidence_only_delta(
        candidate_lock=candidate_lock,
        delta=delta,
        changed_content_by_path_ref=content_by_ref,
        revision_delta_census=census,
        validated_acceptance_reports_by_path_ref=(
            validated_acceptance_reports_by_path_ref
        ),
    )


def verify() -> None:
    revision = _git("rev-parse", "HEAD").decode("ascii").strip()
    lock, content_by_ref = _candidate_lock(revision)
    expected_refs = tuple(f"repo-path-ref:{path}" for path in SLICE_CANDIDATE_PATHS)
    failures = verify_candidate_lock(
        lock,
        expected_path_refs=expected_refs,
        revision_content_by_path_ref=content_by_ref,
    )
    if failures:
        raise RuntimeError(f"TAW-08 contract candidate lock failed: {failures}")
    candidate_receipt = verify_repository_candidate(lock, content_by_ref)
    report = evaluate_taw08_acceptance(
        candidate_lock=lock,
        candidate_verification_receipt=candidate_receipt,
    )
    expected_missing = tuple(
        sorted(
            (
                *(
                    ref
                    for ref in TAW08_FOUNDER_EVIDENCE_MISSING_REFS
                    if ref
                    != "evidence-missing-ref:taw08:candidate-lock-verification-receipt"
                ),
                TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
            )
            + (TAW08_DELTA_VERIFICATION_MISSING_REF,)
        )
    )
    if (
        report.status != TAW08AcceptanceStatus.blocked_missing_founder_evidence
        or report.founder_private_accepted
        or report.founder_evidence_missing_refs != expected_missing
        or report.independent_promotion_ready
        or report.sealed_holdout_evidence_verified
        or report.public_quality_claims_allowed
    ):
        raise RuntimeError(
            "TAW-08 acceptance contract failed closed-state verification"
        )
    if any(
        (
            report.production_authority_added,
            report.runtime_model_calls_added,
            report.provider_calls_added,
            report.execution_authority_added,
            report.raw_content_persisted,
        )
    ):
        raise RuntimeError("TAW-08 verifier detected authority or content expansion")


def main() -> int:
    verify()
    print(
        "Tool-aware cognition TAW-08 acceptance contract verified; founder-private "
        "acceptance remains blocked on exact measured evidence."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
