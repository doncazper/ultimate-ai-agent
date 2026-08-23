#!/usr/bin/env python3
"""Verify the bounded Q29 governed-improvement implementation."""

from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.ecosystem.improvements import (  # noqa: E402
    ImprovementDecision,
    ImprovementEvidenceKind,
    ImprovementEvidenceSource,
    ImprovementProposalRequest,
    ImprovementReviewOutcome,
    ImprovementReviewRequest,
    ImprovementRightsPosture,
    ImprovementSession,
    ImprovementTargetKind,
    build_improvement_proposal,
    build_improvement_status,
)


REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/ecosystem/improvements.py",
    "scripts/inspect_governed_improvement.py",
    "scripts/verify_q29_governed_improvement.py",
    "tests/test_q29_governed_improvement.py",
    "docs/architecture/Q29_GOVERNED_SELF_IMPROVEMENT.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
)
AUTHORITY_SURFACE_FILES = {
    "src/ultimate_ai_agent/core/ecosystem/improvements.py",
    "scripts/inspect_governed_improvement.py",
    "tests/test_q29_governed_improvement.py",
}
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
DENIED_AUTHORITY_FRAGMENTS = (
    "target_mutated: Literal[True]",
    "patch_created: Literal[True]",
    "model_trained: Literal[True]",
    "approval_granted: Literal[True]",
    "proposal_promoted: Literal[True]",
    "git_operation_performed: Literal[True]",
    "external_write_performed: Literal[True]",
    "automatic_learning_performed: Literal[True]",
)
DENIED_CLI_FRAGMENTS = ("--input-json", "read_text(")
REQUIRED_MARKERS = {
    "docs/architecture/Q29_GOVERNED_SELF_IMPROVEMENT.md": (
        "source-specific rights",
        "process-local",
        "no automatic learning occurs",
    ),
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": (
        "Q29 accepts a bounded governed self-improvement",
    ),
}


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


def _request() -> ImprovementProposalRequest:
    return ImprovementProposalRequest(
        workspace_ref="workspace-ref:q29:verifier",
        target_kind=ImprovementTargetKind.evaluation_case,
        target_ref="evaluation-case-ref:q29:verifier",
        target_revision_ref="revision-ref:q29:target:1",
        source_evidence=(
            ImprovementEvidenceSource(
                source_kind=ImprovementEvidenceKind.evaluation_gap,
                source_receipt_ref="evaluation-receipt-ref:q29:verifier",
                source_revision_ref="revision-ref:q29:source:1",
                provenance_ref="provenance-ref:q29:verifier",
                rights_posture=ImprovementRightsPosture.permitted,
                rights_evidence_ref="rights-evidence-ref:q29:verifier",
                evidence_refs=("evidence-ref:q29:verifier",),
            ),
        ),
        intended_delta_refs=("delta-ref:q29:verifier",),
        expected_regression_refs=("regression-ref:q29:verifier",),
        rollback_plan_ref="rollback-plan-ref:q29:verifier",
    )


def verify() -> list[str]:
    failures = [
        f"missing Q29 artifact: {relative_path}"
        for relative_path in REQUIRED_FILES
        if not (ROOT / relative_path).is_file()
    ]
    for relative_path in REQUIRED_FILES:
        path = ROOT / relative_path
        if not path.is_file() or path.suffix != ".py":
            continue
        for name in sorted(_prohibited_imports(path)):
            failures.append(f"forbidden Q29 runtime import in {relative_path}: {name}")
        if relative_path not in AUTHORITY_SURFACE_FILES:
            continue
        source = path.read_text(encoding="utf-8")
        for fragment in DENIED_AUTHORITY_FRAGMENTS:
            if fragment in source:
                failures.append(
                    f"denied Q29 authority fragment in {relative_path}: {fragment}"
                )
    cli_path = ROOT / "scripts/inspect_governed_improvement.py"
    if cli_path.is_file():
        cli_source = cli_path.read_text(encoding="utf-8")
        for fragment in DENIED_CLI_FRAGMENTS:
            if fragment in cli_source:
                failures.append(f"denied Q29 CLI source-read fragment: {fragment}")
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"missing Q29 marker in {relative_path}: {marker}")

    request = _request()
    proposal = build_improvement_proposal(request)
    session = ImprovementSession()
    receipt = session.review(
        ImprovementReviewRequest(
            proposal=request,
            proposal_ref=proposal.proposal_ref,
            proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
            decision=ImprovementDecision.accept,
            reviewer_ref="reviewer-ref:q29:verifier",
            independent_reviewer_ref="reviewer-ref:q29:independent-verifier",
            independent_review_evidence_ref="review-evidence-ref:q29:verifier",
            independent_review_verified=True,
            idempotency_ref="idempotency-ref:q29:verifier",
        )
    )
    if receipt.outcome != ImprovementReviewOutcome.accepted_for_separate_change_review:
        failures.append("ready proposal did not reach separate change review")
    if any(
        (
            proposal.target_mutated,
            proposal.patch_created,
            proposal.model_trained,
            proposal.approval_granted,
            proposal.proposal_promoted,
            proposal.git_operation_performed,
            proposal.external_write_performed,
            receipt.target_mutated,
            receipt.patch_created,
            receipt.model_trained,
            receipt.approval_granted,
            receipt.proposal_promoted,
            receipt.git_operation_performed,
            receipt.external_write_performed,
        )
    ):
        failures.append("Q29 enabled blocked authority")
    status = build_improvement_status()
    if any(
        status[key]
        for key in (
            "self_modifying_code_enabled",
            "automatic_training_enabled",
            "automatic_promotion_enabled",
            "automatic_git_publication_enabled",
            "automatic_merge_enabled",
        )
    ):
        failures.append("Q29 status enabled automatic authority")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Q29 governed self-improvement verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
