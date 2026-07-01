#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DOC_PATH = ROOT / "docs/control_center/BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md"
PRODUCT_LANGUAGE_PATH = ROOT / "docs/control_center/PRODUCT_LANGUAGE_RULES.md"
CURRENT_BOARD_PATH = ROOT / "docs/kanban/current_board.md"
DOC_INDEX_PATH = ROOT / "docs/DOCUMENTATION_INDEX.md"
README_PATH = ROOT / "docs/README.md"
CANONICAL_MAP_PATH = ROOT / "docs/canonical/CANONICAL_DOC_MAP.md"
TRUTH_PACKET_PATH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
ROADMAP_PATH = ROOT / "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"

REQUIRED_DOC_FRAGMENTS = {
    "Status: planning-only promotion requirements; background and autonomous",
    "provider calls remain blocked.",
    "Python Agent Core remains the authority boundary.",
    "Scoped autonomy window",
    "exact allowed provider/model refs",
    "exact allowed credential refs",
    "max spend per window",
    "per-request and per-session cost estimate refs",
    "CostGovernor must run before enqueue, before dispatch, and before every fallback attempt.",
    "There must be no hidden queue.",
    "kill switch",
    "Revocation must invalidate the window",
    "Replay is inspection-only, not re-execution.",
    "prompt injection",
    "UI/CLI parity",
    "No hidden prompt injection",
    "No raw payload persistence",
    "Incomplete cost is a stop condition.",
    "explicit human approval",
    "safe-disable behavior",
    "queued_no_authority",
    "incomplete_cost_requires_review",
    "No background execution.",
    "No scheduler.",
    "No autonomous model calls.",
    "No provider calls.",
    "No runtime activation.",
    "No billing authority.",
    "No broad provider router.",
    "No new API runtime route.",
}

REQUIRED_SUPPORTING_FRAGMENTS = {
    PRODUCT_LANGUAGE_PATH: "No background/autonomous provider-call promotion authority drift",
    CURRENT_BOARD_PATH: "Background and Autonomous Provider Calls Promotion Plan",
    DOC_INDEX_PATH: "BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md",
    README_PATH: "BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md",
    CANONICAL_MAP_PATH: "BACKGROUND_AUTONOMOUS_PROVIDER_CALLS_PROMOTION_PLAN.md",
    TRUTH_PACKET_PATH: "Background and Autonomous Provider Calls Promotion Plan",
    ROADMAP_PATH: "Background/autonomous provider calls remain blocked.",
}

FORBIDDEN_DOC_FRAGMENTS = {
    "background provider calls are enabled",
    "background provider calls are implemented",
    "autonomous provider calls are enabled",
    "autonomous provider calls are implemented",
    "scheduler is available",
    "scheduler is enabled",
    "provider calls are enabled in background",
    "billing authority is granted",
    "broad provider router is available",
    "background queue dispatch is available",
    "autonomous model calls are available",
    "new api runtime route is available",
}

FORBIDDEN_DOC_PATTERNS = {
    "background_provider_calls_enabled": re.compile(
        r"\bbackground provider calls?\s+(?:is|are)\s+"
        r"(?:enabled|implemented|available|live|callable)\b"
    ),
    "autonomous_provider_calls_enabled": re.compile(
        r"\bautonomous provider calls?\s+(?:is|are)\s+"
        r"(?:enabled|implemented|available|live|callable)\b"
    ),
    "scheduler_enabled": re.compile(
        r"\bscheduler\s+(?:is\s+)?(?:enabled|implemented|available|live|callable)\b"
    ),
    "billing_authority_granted": re.compile(
        r"\bbilling authority\s+(?:is\s+)?(?:granted|enabled|available)\b"
    ),
    "broad_provider_router_available": re.compile(
        r"\bbroad provider router\s+(?:is\s+)?"
        r"(?:available|enabled|implemented|live|callable)\b"
    ),
    "background_dispatch_available": re.compile(
        r"\bbackground (?:queue )?dispatch\s+(?:is\s+)?"
        r"(?:available|enabled|implemented|live|callable)\b"
    ),
    "new_api_runtime_route_available": re.compile(
        r"\bnew api runtime route\s+(?:is\s+)?"
        r"(?:available|enabled|implemented|live|callable)\b"
    ),
}

FORBIDDEN_API_ROUTE_FRAGMENTS = {
    "/background-provider",
    "/autonomous-provider",
    "/providers/background",
    "/providers/autonomous",
    "background_autonomous_provider",
}


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read(path: Path, failures: list[str]) -> str:
    if not path.exists():
        failures.append(f"missing required file: {_display_path(path)}")
        return ""
    return path.read_text(encoding="utf-8")


def _append_authority_drift_failures(
    failures: list[str],
    *,
    label: str,
    text: str,
) -> None:
    lowered = text.lower()
    for fragment in FORBIDDEN_DOC_FRAGMENTS:
        if fragment in lowered:
            failures.append(f"{label} contains authority drift: {fragment}")
    for drift_label, pattern in FORBIDDEN_DOC_PATTERNS.items():
        if pattern.search(lowered):
            failures.append(f"{label} contains authority drift: {drift_label}")


def _append_api_route_failures(failures: list[str]) -> None:
    api_root = ROOT / "src/ultimate_ai_agent/api"
    for path in api_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for fragment in FORBIDDEN_API_ROUTE_FRAGMENTS:
            if fragment in lowered:
                failures.append(
                    f"{_display_path(path)} contains forbidden runtime route fragment: {fragment}"
                )


def validate_background_autonomous_provider_plan() -> list[str]:
    failures: list[str] = []
    doc_text = _read(DOC_PATH, failures)

    for fragment in REQUIRED_DOC_FRAGMENTS:
        if fragment not in doc_text:
            failures.append(
                f"background/autonomous provider plan missing fragment: {fragment}"
            )

    _append_authority_drift_failures(
        failures,
        label="background/autonomous provider plan",
        text=doc_text,
    )

    for path, fragment in REQUIRED_SUPPORTING_FRAGMENTS.items():
        text = _read(path, failures)
        if fragment not in text:
            failures.append(
                f"{_display_path(path)} missing background/autonomous provider plan fragment: {fragment}"
            )
        _append_authority_drift_failures(
            failures,
            label=_display_path(path),
            text=text,
        )

    _append_api_route_failures(failures)
    return failures


def main() -> int:
    failures = validate_background_autonomous_provider_plan()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("background/autonomous provider promotion plan verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
