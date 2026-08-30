from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from ultimate_ai_agent.core.evals.tool_aware_acceptance import (
    TAW08_DELTA_VERIFICATION_MISSING_REF,
    TAW08_FOUNDER_EVIDENCE_MISSING_REFS,
    TAW08_POSTMERGE_EVIDENCE_MISSING_REF,
    TAW08AcceptanceStatus,
    evaluate_taw08_acceptance,
)
from ultimate_ai_agent.core.evals.tool_aware_baseline import (
    CandidateLock,
    CandidateManifestEntry,
    canonical_digest,
    verify_candidate_lock,
)


ROOT = Path(__file__).resolve().parents[1]
SLICE_CANDIDATE_PATHS = (
    "docs/evals/TOOL_AWARE_COGNITION_TAW08_ACCEPTANCE.md",
    "scripts/verify_tool_aware_cognition_taw08.py",
    "src/ultimate_ai_agent/core/evals/__init__.py",
    "src/ultimate_ai_agent/core/evals/tool_aware_acceptance.py",
    "tests/test_tool_aware_cognition_taw08.py",
)
EVIDENCE_ONLY_DELTA_PATHS = (
    "docs/evals/tool_aware_cognition_taw08_acceptance_report_v1.json",
    "docs/kanban/current_board.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
)


def _git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return result.stdout


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
    report = evaluate_taw08_acceptance(candidate_lock=lock)
    expected_missing = tuple(
        sorted(
            (*TAW08_FOUNDER_EVIDENCE_MISSING_REFS, TAW08_POSTMERGE_EVIDENCE_MISSING_REF)
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
