from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from ultimate_ai_agent.core.evals.tool_aware_corpus import DevelopmentCorpusManifest
from ultimate_ai_agent.core.evals.tool_aware_hardening import (
    HardeningStatus,
    TAW07_CATALOG_STATES,
    TAW07_REPLAY_MODES,
    TAW07HardeningPolicy,
    build_taw07_founder_development_evidence,
    evaluate_taw07_hardening,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "docs/evals/tool_aware_cognition_taw07_development_corpus_v1.json"
CANDIDATE_PATHS = (
    "docs/DOCUMENTATION_INDEX.md",
    "docs/evals/TOOL_AWARE_COGNITION_TAW06_DIAGNOSTICS.md",
    "docs/evals/TOOL_AWARE_COGNITION_TAW07_HARDENING.md",
    "docs/evals/tool_aware_cognition_taw07_development_corpus_v1.json",
    "docs/kanban/current_board.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "scripts/verify_tool_aware_cognition_taw07.py",
    "src/ultimate_ai_agent/core/capabilities/__init__.py",
    "src/ultimate_ai_agent/core/capabilities/chat_shadow.py",
    "src/ultimate_ai_agent/core/capabilities/familiarity.py",
    "src/ultimate_ai_agent/core/evals/tool_aware_hardening.py",
    "src/ultimate_ai_agent/core/system_map/catalog.py",
    "tests/test_tool_aware_cognition_taw07.py",
)


def _candidate_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _candidate_manifest_digest_ref(revision: str) -> str:
    digest = hashlib.sha256()
    for relative_path in CANDIDATE_PATHS:
        result = subprocess.run(
            ["git", "show", f"{revision}:{relative_path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        committed = result.stdout
        comparison = subprocess.run(
            ["git", "diff", "--quiet", revision, "--", relative_path],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        if comparison.returncode == 1:
            raise RuntimeError(
                f"TAW-07 candidate path is dirty relative to {revision}: {relative_path}"
            )
        if comparison.returncode != 0:
            raise RuntimeError(
                f"TAW-07 candidate path comparison failed: {relative_path}"
            )
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(committed)
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def verify() -> None:
    candidate_revision = _candidate_revision()
    corpus = DevelopmentCorpusManifest.model_validate(
        json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    )
    policy = TAW07HardeningPolicy(
        candidate_revision_ref=f"git-sha:{candidate_revision}",
        candidate_manifest_digest_ref=_candidate_manifest_digest_ref(
            candidate_revision
        ),
        development_corpus_digest_ref=corpus.corpus_digest,
    )
    bindings, observations, quality = build_taw07_founder_development_evidence(
        policy=policy,
        corpus=corpus,
    )
    report = evaluate_taw07_hardening(
        policy=policy,
        corpus=corpus,
        legacy_bindings=bindings,
        observations=observations,
        quality_observations=quality,
    )
    if (
        report.status != HardeningStatus.blocked_missing_holdout_commitment
        or report.case_count != 24
        or report.observation_count
        != report.case_count * len(TAW07_CATALOG_STATES) * len(TAW07_REPLAY_MODES)
        or report.quality_observation_count != 2
        or not report.safe_disable_equivalence_proven
        or not report.exact_matrix_coverage_proven
        or any(not item.passed for item in report.metric_results)
    ):
        raise RuntimeError("TAW-07 deterministic development evidence drifted")
    if any(
        (
            report.holdout_material_accessed,
            report.raw_content_persisted,
            report.runtime_model_calls_added,
            report.provider_calls_added,
            report.execution_authority_added,
            report.public_quality_claims_allowed,
            report.independent_promotion_ready,
        )
    ):
        raise RuntimeError("TAW-07 verifier detected authority or claim expansion")


def main() -> int:
    verify()
    print(
        "Tool-aware cognition TAW-07 development contract verified; "
        "qualification remains blocked on the holdout commitment."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
