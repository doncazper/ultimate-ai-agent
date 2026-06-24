#!/usr/bin/env python3
"""Validate FCC-REVIEW-001 Evidence narrative and Weekly Review truth."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-REVIEW-001"
DOC = ROOT / "docs/control_center/FCC_REVIEW_001_EVIDENCE_NARRATIVE_WEEKLY_REVIEW.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
MATURITY_MANIFEST = ROOT / "docs/control_center/operational_maturity_manifest.json"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API_TYPES = ROOT / "apps/control-center/src/api/types.ts"
FOUNDER_LOOP_PANELS = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
CONTROL_CENTER_ROUTE_TEST = ROOT / "tests/test_control_center_api_routes.py"
EVIDENCE_TEST = ROOT / "tests/test_fcc_v1_006_evidence_timeline_productization.py"

DOC_REF = "docs/control_center/FCC_REVIEW_001_EVIDENCE_NARRATIVE_WEEKLY_REVIEW.md"
VERIFIER_REF = "scripts/verify_fcc_review_001_evidence_narrative_weekly_review.py"


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_text(root: Path, path: Path, failures: list[str]) -> str:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _require_fragments(
    rel_path: str,
    text: str,
    fragments: list[str],
    failures: list[str],
) -> None:
    compact = " ".join(text.lower().split())
    lowered = text.lower()
    for fragment in fragments:
        needle = fragment.lower()
        if needle not in lowered and needle not in compact:
            failures.append(f"{rel_path} missing FCC-REVIEW-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented",
            "Primary surfaces: `/evidence`, `/today`, `/briefing`, and `/actions`",
            "GET /control-center/evidence/timeline",
            "FounderLoopWeeklyReviewNarrative",
            "WeeklyReviewNarrativeCard",
            "completed_refs",
            "deferred_refs",
            "rejected_refs",
            "blocked_refs",
            "stale_refs",
            "planned_refs",
            "missing_source_refs",
            "memory_change_refs",
            "crm_movement_refs",
            "draft_refs",
            "next_week_priority_refs",
            "review_answer_refs",
            "reversible_safe_disabled",
            "does not add automatic weekly generation by model/provider",
            VERIFIER_REF,
        ],
        failures,
    )


def _validate_backend_and_frontend(root: Path, failures: list[str]) -> None:
    requirements = {
        STORAGE: [
            "def _weekly_review_narrative(",
            "completed_refs",
            "deferred_refs",
            "rejected_refs",
            "blocked_refs",
            "stale_refs",
            "planned_refs",
            "memory_change_refs",
            "crm_movement_refs",
            "draft_refs",
            "next_week_priority_refs",
            "missing_source_refs",
            "safe_ref_history_ready",
            "review_answer_refs",
            "does not invent truth",
            "sync accounts, execute actions",
        ],
        API_TYPES: [
            "FounderLoopWeeklyReviewNarrative",
            "completed_refs",
            "deferred_refs",
            "rejected_refs",
            "planned_refs",
            "blocked_refs",
            "stale_refs",
            "missing_source_refs",
        ],
        FOUNDER_LOOP_PANELS: [
            "WeeklyReviewNarrativeCard",
            "Completed refs",
            "Deferred refs",
            "Rejected refs",
            "Planned refs",
            "Memory change refs",
            "CRM movement refs",
            "Draft refs",
            "Next-week priority refs",
            "Blocked refs",
            "Stale refs",
            "Missing source refs",
            "Review answers",
        ],
        APP_TEST: [
            "Weekly Review narrative",
            "Evidence Timeline is safe-ref",
            "raw prompt",
            "provider_payload",
        ],
        CONTROL_CENTER_ROUTE_TEST: [
            "weekly_review_narrative",
            "safe_ref_history_ready",
        ],
        EVIDENCE_TEST: [
            "control_center_evidence_timeline",
            "safe_refs_only",
            "raw_content_stored",
            "rollback_execution_enabled",
            "context_injection_authorized",
            "production_authority_enabled",
            "local_task_created",
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-REVIEW-001 Evidence Narrative And Weekly CEO Review",
            DOC_REF,
            "FCC-HEALTH-001 Self-Healing Recommendations To Inbox",
        ],
        FCC_BOARD: [
            "FCC-REVIEW-001",
            "Evidence Narrative And Weekly CEO Review",
            DOC_REF,
        ],
        PRODUCT_TRUTH: [
            "FCC-REVIEW-001",
            DOC_REF,
            "Evidence Narrative and Weekly Review are implemented",
        ],
        GAP_MAP: [
            "Evidence Timeline",
            "Weekly Review",
            "safe-ref",
        ],
        DOCS_README: [DOC_REF],
        DOCS_INDEX: [DOC_REF],
        MATURITY_MANIFEST: [
            DOC_REF,
            VERIFIER_REF,
            "support_indexes_receipt_backed_events",
        ],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_review_001_evidence_narrative_weekly_review(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_backend_and_frontend(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FCC-REVIEW-001 Evidence narrative and Weekly Review truth."
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to inspect.")
    args = parser.parse_args(argv)

    failures = validate_fcc_review_001_evidence_narrative_weekly_review(
        Path(args.root).resolve()
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(f"{TASK_REF} Evidence narrative and Weekly Review verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
