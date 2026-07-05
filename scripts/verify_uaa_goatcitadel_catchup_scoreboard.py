#!/usr/bin/env python3
"""Verify the UAA GoatCitadel catch-up scoreboard artifact."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "docs" / "control_center" / "UAA_GOATCITADEL_CATCHUP_SCOREBOARD.md"

REQUIRED_SECTIONS = (
    "# UAA GoatCitadel Catch-Up Scoreboard",
    "## Snapshot",
    "## Source Files Inspected",
    "## Component Scoreboard",
    "## Age-Adjusted Interpretation",
    "## Ranked Catch-Up Backlog",
    "## GoatCitadel Patterns Borrowed As UAA-Native Designs",
    "## GoatCitadel Patterns Not Merged",
    "## Blocked Authority Preserved",
    "## Merge-Gated Follow-Up Prompts",
    "## Phase 01 Acceptance Result",
)

REQUIRED_COMPONENTS = (
    "Reasoning and task understanding",
    "Planning and orchestration",
    "Learning and adaptation",
    "Memory and context management",
    "Communication and interaction quality",
    "Action and tool calling",
    "Autonomy and authority management",
    "Code and implementation assistance",
    "Research, web, and external information handling",
    "Model/provider management",
    "Evidence, audit, and observability",
    "Safety, security, and failure handling",
    "UX as an AI cockpit",
    "CLI/API parity",
    "Extensibility and ecosystem",
    "Productized agent loop",
)

REQUIRED_STATUS_LABELS = (
    "implemented",
    "partial",
    "planned",
    "mock-only",
    "blocked",
    "deprecated",
    "contradicted",
    "unknown",
)

REQUIRED_BLOCKED_AUTHORITY = (
    "runtime model calls",
    "provider SDK calls",
    "live web fetching",
    "browser automation",
    "connector writes",
    "unrestricted shell/subprocess execution",
    "plugin runtime import",
    "memory-write authority",
    "remote execution",
    "public release claims",
    "production authority",
    "broad autonomy",
)

REQUIRED_FOLLOW_UP_PHASES = tuple(f"Phase 0{index} Prompt" for index in range(2, 10))

REQUIRED_EVIDENCE_REFS = (
    "AGENTS.md",
    "README.md",
    "VERSION.md",
    "SECURITY.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "docs/control_center/AUTHORITY_GRADUATION_BOARD.md",
    "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
    "../GoatCitadel/README.md",
    "../GoatCitadel/docs/DURABLE_RUNS_REPLAY_FOUNDATION.md",
    "../GoatCitadel/docs/CAPABILITY_SYSTEM_V1.md",
    "../GoatCitadel/packages/contracts/src/durable.ts",
    "../GoatCitadel/packages/contracts/src/evidence.ts",
    "../GoatCitadel/packages/contracts/src/llm.ts",
)

ABSOLUTE_LOCAL_PATH_PATTERNS = (
    re.compile(r"/Users/[^\s`)]+"),
    re.compile(r"/home/[^\s`)]+"),
    re.compile(r"/var/[^\s`)]+"),
    re.compile(r"/etc/[^\s`)]+"),
)


class VerificationError(RuntimeError):
    """Raised when the scoreboard fails validation."""


def _load_report(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise VerificationError("scoreboard report is missing") from exc


def _require_all(text: str, required: tuple[str, ...], label: str) -> list[str]:
    missing = [item for item in required if item not in text]
    return [f"missing {label}: {item}" for item in missing]


def verify(report_path: Path = DEFAULT_REPORT) -> list[str]:
    text = _load_report(report_path)
    lowered = text.lower()
    failures: list[str] = []

    failures.extend(_require_all(text, REQUIRED_SECTIONS, "section"))
    failures.extend(_require_all(text, REQUIRED_COMPONENTS, "component"))
    failures.extend(_require_all(text, REQUIRED_STATUS_LABELS, "status label"))
    failures.extend(_require_all(text, REQUIRED_BLOCKED_AUTHORITY, "blocked authority"))
    failures.extend(_require_all(text, REQUIRED_FOLLOW_UP_PHASES, "follow-up phase"))
    failures.extend(_require_all(text, REQUIRED_EVIDENCE_REFS, "evidence ref"))

    for phrase in (
        "not runtime authority",
        "not copied from GoatCitadel",
        "read-only reference comparator",
        "safe refs",
        "does not change Control Center behavior",
    ):
        if phrase.lower() not in lowered:
            failures.append(f"missing required safety phrase: {phrase}")

    if "copied from goatcitadel" in lowered and "not copied from goatcitadel" not in lowered:
        failures.append("scoreboard appears to allow copying from GoatCitadel")

    for pattern in ABSOLUTE_LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            failures.append("scoreboard contains an absolute local path")
            break

    component_rows = [
        line
        for line in text.splitlines()
        if line.startswith("| ") and any(component in line for component in REQUIRED_COMPONENTS)
    ]
    if len(component_rows) < len(REQUIRED_COMPONENTS):
        failures.append("component scoreboard is missing table rows")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    failures = verify(args.report)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print("UAA GoatCitadel catch-up scoreboard verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

