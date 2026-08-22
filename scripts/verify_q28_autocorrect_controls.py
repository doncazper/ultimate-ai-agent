#!/usr/bin/env python3
"""Verify the bounded Q28 autocorrect-control implementation."""

from __future__ import annotations

import ast
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.ecosystem.changesets import (  # noqa: E402
    FieldChangeKind,
    FieldDiff,
)
from ultimate_ai_agent.core.ecosystem.contracts import (  # noqa: E402
    CanonicalOwnerId,
    EntityKind,
)
from ultimate_ai_agent.core.ecosystem.corrections import (  # noqa: E402
    CorrectionDecision,
    CorrectionProposalRequest,
    CorrectionReviewOutcome,
    CorrectionReviewRequest,
    CorrectionReviewSession,
    build_correction_proposal,
)


REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/ecosystem/corrections.py",
    "src/ultimate_ai_agent/api/founder_loop.py",
    "scripts/inspect_autocorrect_controls.py",
    "tests/test_q28_autocorrect_controls.py",
    "docs/architecture/Q28_AUTOCORRECT_CONTROLS.md",
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
DENIED_AUTHORITY_FRAGMENTS = (
    "canonical_state_mutated: Literal[True]",
    "changeset_created: Literal[True]",
    "approval_granted: Literal[True]",
    "rollback_executed: Literal[True]",
    "model_call_performed: Literal[True]",
    "external_write_performed: Literal[True]",
)
DENIED_CLI_FRAGMENTS = ("--input-json", "read_text(")
REQUIRED_MARKERS = {
    "docs/architecture/Q28_AUTOCORRECT_CONTROLS.md": (
        "exact revision",
        "idempotency",
        "process-local",
        "no canonical mutation",
    ),
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": (
        "Q28 accepts proposal-only autocorrect controls",
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


def _synthetic_request() -> CorrectionProposalRequest:
    return CorrectionProposalRequest(
        workspace_ref="workspace-ref:q28:verifier",
        source_proposal_ref="proposal-ref:q28:verifier",
        target_kind=EntityKind.task,
        target_owner=CanonicalOwnerId.tasks,
        target_ref="task-ref:q28:verifier",
        expected_revision_ref="revision-ref:q28:verifier:1",
        current_revision_ref="revision-ref:q28:verifier:1",
        confidence_percent=90,
        field_diffs=(
            FieldDiff(
                operation_ref="operation-ref:q28:verifier",
                target_ref="task-ref:q28:verifier",
                field_ref="field-ref:title",
                change_kind=FieldChangeKind.updated,
                before_fingerprint_ref="fingerprint-ref:q28:before",
                after_fingerprint_ref="fingerprint-ref:q28:after",
            ),
        ),
        evidence_refs=("evidence-ref:q28:verifier",),
    )


def _operational_failures() -> list[str]:
    failures: list[str] = []
    proposal_request = _synthetic_request()
    proposal = build_correction_proposal(proposal_request)
    review_request = CorrectionReviewRequest(
        proposal=proposal_request,
        proposal_ref=proposal.proposal_ref,
        proposal_fingerprint_ref=proposal.proposal_fingerprint_ref,
        decision=CorrectionDecision.accept,
        reviewer_ref="reviewer-ref:q28:verifier",
        idempotency_ref="idempotency-ref:q28:verifier",
    )
    session = CorrectionReviewSession()
    receipt = session.review(review_request)
    replay = session.review(review_request)
    if receipt.outcome != CorrectionReviewOutcome.accepted_for_changeset_review:
        failures.append(
            "review-ready correction did not reach the bounded accepted outcome"
        )
    if replay.receipt_ref != receipt.receipt_ref or not replay.replayed:
        failures.append("same-payload idempotent replay was not stable")
    for name, value in {
        "proposal canonical mutation": proposal.canonical_state_mutated,
        "proposal changeset creation": proposal.changeset_created,
        "review canonical mutation": receipt.canonical_state_mutated,
        "review changeset creation": receipt.changeset_created,
        "review approval grant": receipt.approval_granted,
        "review rollback execution": receipt.rollback_executed,
        "review model call": receipt.model_call_performed,
        "review external write": receipt.external_write_performed,
    }.items():
        if value is not False:
            failures.append(f"blocked Q28 authority was enabled: {name}")
    return failures


def verify() -> list[str]:
    failures = [
        f"missing Q28 artifact: {path}"
        for path in REQUIRED_FILES
        if not (ROOT / path).is_file()
    ]
    for relative_path in REQUIRED_FILES:
        path = ROOT / relative_path
        if not path.is_file() or path.suffix != ".py":
            continue
        for name in sorted(_prohibited_imports(path)):
            failures.append(f"forbidden Q28 runtime import: {name}")
        source = path.read_text(encoding="utf-8")
        for fragment in DENIED_AUTHORITY_FRAGMENTS:
            if fragment in source:
                failures.append(
                    f"denied Q28 authority fragment in {relative_path}: {fragment}"
                )
    cli_path = ROOT / "scripts/inspect_autocorrect_controls.py"
    if cli_path.is_file():
        cli_source = cli_path.read_text(encoding="utf-8")
        for fragment in DENIED_CLI_FRAGMENTS:
            if fragment in cli_source:
                failures.append(f"denied Q28 CLI source-read fragment: {fragment}")
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"missing Q28 marker in {relative_path}: {marker}")
    failures.extend(_operational_failures())
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Q28 autocorrect controls verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
