#!/usr/bin/env python3
"""Verify the bounded Q27 ECO-010 proposal-intelligence implementation."""

from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.ecosystem.proposals import (  # noqa: E402
    ProposalCandidateKind,
    ProposalExtractionRequest,
    ProposalFact,
    ProposalSourceRevisionBinding,
    extract_proposal_candidates,
)


REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/ecosystem/proposals.py",
    "src/ultimate_ai_agent/api/founder_loop.py",
    "scripts/inspect_eco_010_proposals.py",
    "tests/test_queue_v2_q27_proposal_intelligence.py",
    "docs/architecture/ECO_010_PROPOSAL_INTELLIGENCE.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
)
PROHIBITED_IMPORTS = {
    "browserbase",
    "firecrawl",
    "http.client",
    "httpx",
    "playwright",
    "requests",
    "selenium",
    "subprocess",
    "urllib.request",
    "urllib3",
}
REQUIRED_MARKERS = {
    "docs/architecture/ECO_010_PROPOSAL_INTELLIGENCE.md": (
        "already-normalized",
        "source-revision",
        "target record",
    ),
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": (
        "ECO-010 accepts a bounded deterministic proposal-intelligence baseline",
    ),
}
DENIED_AUTHORITY_FRAGMENTS = (
    "direct_commit_allowed: Literal[True]",
    "change_set_eligible: Literal[True]",
    "model_call_performed: Literal[True]",
    "model_output_is_authority: Literal[True]",
    "source_read_performed: Literal[True]",
    "target_write_performed: Literal[True]",
    "external_write_performed: Literal[True]",
)
DENIED_CLI_FRAGMENTS = ("--input-json", "read_text(")


def _prohibited_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    findings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [
                node.module,
                *(f"{node.module}.{item.name}" for item in node.names),
            ]
        else:
            continue
        for name in names:
            findings.update(
                item
                for item in PROHIBITED_IMPORTS
                if name == item or name.startswith(f"{item}.")
            )
    return findings


def _operational_failures() -> list[str]:
    fact = ProposalFact(
        workspace_ref="workspace-ref:eco-010:verifier",
        fact_ref="proposal-fact-ref:eco-010:verifier",
        source_artifact_ref="source-artifact-ref:eco-010:verifier",
        source_revision_ref="source-revision-ref:eco-010:verifier:v1",
        candidate_kind=ProposalCandidateKind.commitment,
        safe_summary="Synthetic cited commitment candidate for review.",
        evidence_refs=("evidence-ref:eco-010:verifier",),
        subject_ref="subject-ref:eco-010:verifier",
        confidence_percent=90,
    )
    result = extract_proposal_candidates(
        ProposalExtractionRequest(
            workspace_ref=fact.workspace_ref,
            facts=(fact,),
            source_revision_bindings=(
                ProposalSourceRevisionBinding(
                    source_artifact_ref=fact.source_artifact_ref,
                    current_source_revision_ref=fact.source_revision_ref,
                ),
            ),
            requested_at="2026-08-22T12:00:00Z",
        )
    )
    failures: list[str] = []
    candidate = result["candidates"][0]
    if candidate["candidate_kind"] != "commitment":
        failures.append("deterministic commitment candidate was not emitted")
    if candidate["review_posture"] != "ready_for_review":
        failures.append("cited current candidate was not review-ready")
    for flag in (
        "raw_source_content_included",
        "source_read_performed",
        "model_call_performed",
        "model_output_is_authority",
        "change_set_created",
        "approval_grant_created",
        "target_write_performed",
        "external_write_performed",
    ):
        if result[flag] is not False:
            failures.append(f"blocked Q27 authority flag was enabled: {flag}")
    return failures


def verify() -> list[str]:
    failures = [
        f"missing Q27 artifact: {path}"
        for path in REQUIRED_FILES
        if not (ROOT / path).is_file()
    ]
    core_path = ROOT / REQUIRED_FILES[0]
    if core_path.is_file():
        for name in sorted(_prohibited_imports(core_path)):
            failures.append(f"forbidden Q27 runtime import: {name}")
        source = core_path.read_text(encoding="utf-8")
        for fragment in DENIED_AUTHORITY_FRAGMENTS:
            if fragment in source:
                failures.append(f"denied Q27 authority fragment: {fragment}")
    cli_path = ROOT / "scripts/inspect_eco_010_proposals.py"
    if cli_path.is_file():
        cli_source = cli_path.read_text(encoding="utf-8")
        for fragment in DENIED_CLI_FRAGMENTS:
            if fragment in cli_source:
                failures.append(f"denied Q27 CLI source-read fragment: {fragment}")
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing Q27 artifact: {relative_path}")
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"missing Q27 marker in {relative_path}: {marker}")
    failures.extend(_operational_failures())
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Q27 ECO-010 proposal intelligence verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
