#!/usr/bin/env python3
"""Validate FCC-BRIEFING-001 Morning Briefing and Today Plan truth."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "FCC-BRIEFING-001"
DOC = ROOT / "docs/control_center/FCC_BRIEFING_001_MORNING_BRIEFING_TODAY_PLAN.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
STORAGE = ROOT / "src/ultimate_ai_agent/core/storage/founder_loop.py"
API_ROUTE = ROOT / "src/ultimate_ai_agent/api/founder_loop.py"
CONTROL_CENTER_MANIFEST = ROOT / "src/ultimate_ai_agent/core/control_center/manifest.py"
API_TYPES = ROOT / "apps/control-center/src/api/types.ts"
ROUTES = ROOT / "apps/control-center/src/routes.tsx"
FOUNDER_LOOP_PANELS = ROOT / "apps/control-center/src/components/FounderLoopPanels.tsx"
APP_TEST = ROOT / "apps/control-center/src/App.test.tsx"
STORAGE_BRIEFING_TEST = ROOT / "tests/test_founder_loop_storage_briefing.py"
CONTROL_CENTER_ROUTE_TEST = ROOT / "tests/test_control_center_api_routes.py"

DOC_REF = "docs/control_center/FCC_BRIEFING_001_MORNING_BRIEFING_TODAY_PLAN.md"
VERIFIER_REF = "scripts/verify_fcc_briefing_001_morning_briefing_today_plan.py"
BRIEFING_ROUTE = "GET /control-center/morning-briefing/summary"
SOURCE_READINESS_ROUTE = "GET /control-center/sources/readiness"


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
            failures.append(f"{rel_path} missing FCC-BRIEFING-001 fragment: {fragment}")


def _validate_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(DOC),
        text,
        [
            "Status: Implemented",
            "Primary surfaces: `/briefing` and `/today`",
            BRIEFING_ROUTE,
            SOURCE_READINESS_ROUTE,
            "FounderLoopMorningBriefing",
            "MorningBriefingPanel",
            "daily_loop_summary",
            "source_readiness_posture",
            "review_queue_groups",
            "crm_lite_followups",
            "memory_why_shown_items",
            "weekly_review_narrative",
            "dogfood_capture",
            "does not add email or calendar fetch",
            VERIFIER_REF,
        ],
        failures,
    )


def _validate_backend_and_frontend(root: Path, failures: list[str]) -> None:
    requirements = {
        STORAGE: [
            "def morning_briefing",
            "daily_loop_summary",
            "home_surface",
            "Morning Briefing",
            "decision_surface",
            "Today",
            "source_readiness_posture",
            "source_readiness_items",
            "review_queue_groups",
            "crm_lite_followups",
            "memory_why_shown_items",
            "weekly_review_narrative",
            "dogfood_capture",
            "refresh_enabled",
            "notification_delivery_enabled",
            "no_background_refresh",
            "no_notification_delivery",
        ],
        API_ROUTE: [
            '@router.get("/morning-briefing/summary"',
            "control_center_morning_briefing_summary",
            "morning_briefing_summary",
        ],
        CONTROL_CENTER_MANIFEST: [
            "CONTROL_CENTER_ROUTES",
            '"/control-center/morning-briefing/summary"',
        ],
        API_TYPES: [
            "FounderLoopMorningBriefing",
            "daily_loop_summary",
            "source_readiness_posture",
            "daily_loop_sections",
            "review_queue_groups",
            "dogfood_capture",
            "refresh_enabled",
            "notification_delivery_enabled",
        ],
        ROUTES: [
            '{ path: "/briefing", label: "Briefing"',
            "founderMorningBriefing",
            "MorningBriefingPanel",
        ],
        FOUNDER_LOOP_PANELS: [
            "export function MorningBriefingPanel",
            "Read-only source readiness metadata",
            "BriefingDailyLoopPanel",
            "DailyLoopSummaryCard",
            "SourceReadinessCards",
            "ReviewQueueGroupCards",
            "CrmLiteFollowUpCards",
            "MemoryWhyShownCards",
            "DogfoodCaptureCard",
            "WeeklyReviewNarrativeCard",
            "refresh, notification delivery, model/provider authority",
        ],
        APP_TEST: [
            "renders Morning Briefing source-readiness posture without source controls",
            "/control-center/morning-briefing/summary",
            "no_background_refresh",
            "no_notification_delivery",
            "queryByRole(\"button\", { name: label })",
        ],
        STORAGE_BRIEFING_TEST: [
            "test_founder_loop_briefing_defaults_are_blocked_and_read_only",
            "daily_loop_summary",
            "source_readiness_posture",
            "dogfood_capture",
            "public_beta_claim_enabled",
            "action_execution_enabled",
        ],
        CONTROL_CENTER_ROUTE_TEST: [
            "/control-center/morning-briefing/summary",
            "daily_loop_summary",
            "source_readiness_posture",
            "source_readiness_items",
            "public_distribution_enabled",
        ],
    }
    for path, fragments in requirements.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "FCC-BRIEFING-001 Morning Briefing And Today Plan V1",
            DOC_REF,
            "FCC-SOURCES-001 Source Readiness And Draft-only Inputs",
        ],
        FCC_BOARD: [
            "FCC-BRIEFING-001",
            "Morning Briefing And Today Plan V1",
            DOC_REF,
        ],
        PRODUCT_TRUTH: [
            "FCC-BRIEFING-001",
            DOC_REF,
            "Morning Briefing is implemented as a read-only daily-loop surface",
        ],
        GAP_MAP: [
            "`/briefing` renders bounded local briefing summaries",
            "no email/calendar access",
        ],
        DOCS_README: [DOC_REF],
        DOCS_INDEX: [DOC_REF],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if text:
            _require_fragments(_rel(path), text, fragments, failures)


def validate_fcc_briefing_001_morning_briefing_today_plan(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_doc(root, failures)
    _validate_backend_and_frontend(root, failures)
    _validate_active_docs(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate FCC-BRIEFING-001 Morning Briefing and Today Plan truth."
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to inspect.")
    args = parser.parse_args(argv)

    failures = validate_fcc_briefing_001_morning_briefing_today_plan(
        Path(args.root).resolve()
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(f"{TASK_REF} Morning Briefing verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
