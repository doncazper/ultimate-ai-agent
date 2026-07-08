#!/usr/bin/env python3
"""Verify the UAA runtime parity scorecard artifact."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "docs" / "runtime" / "UAA_RUNTIME_PARITY_SCORECARD.md"

REQUIRED_SECTIONS = (
    "# UAA Runtime Parity Scorecard",
    "## Status Labels",
    "## Parity Target",
    "## Source Files Inspected",
    "## Component Scoreboard",
    "## Phase Lane Map",
    "## External Runtime Patterns Borrowed As UAA-Native Designs",
    "## External Runtime Patterns Not Merged",
    "## Blocked Authority Preserved",
    "## Evidence Rules",
    "## Phase 01 Acceptance Result",
)

REQUIRED_DIMENSIONS = (
    "Turn-contract clarity",
    "Authority/safety boundary",
    "Execution readiness",
    "Durable runtime integration",
    "Model/provider routing",
    "Operator inspectability",
    "Product usefulness today",
    "Long-term safe foundation",
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
    "remote execution",
    "public release claims",
    "production authority",
    "broad autonomy",
    "raw prompt persistence",
    "raw response persistence",
    "raw provider payload persistence",
)

REQUIRED_EVIDENCE_REFS = (
    "AGENTS.md",
    "README.md",
    "VERSION.md",
    "SECURITY.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "docs/control_center/AUTHORITY_GRADUATION_BOARD.md",
    "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
    "docs/architecture/TURN_CONTRACT_ROUTER.md",
    "src/ultimate_ai_agent/core/decision_router/",
    "src/ultimate_ai_agent/core/runtime_gateway/contracts.py",
    "src/ultimate_ai_agent/core/orchestration_efficiency/",
    "src/ultimate_ai_agent/core/providers/control_plane.py",
    "tests/test_turn_contract_router_harness_binding.py",
    "tests/test_governed_runtime_contracts.py",
    "tests/test_model_provider_control_plane.py",
    "external-runtime-ref:gateway-chat-messages",
    "external-runtime-ref:orchestration-engine",
    "external-runtime-ref:model-selector",
    "external-runtime-ref:chat-turn-prep-service",
    "external-runtime-ref:canonical-runtime-state-model",
)

REQUIRED_PHASES = tuple(f"Phase 0{index} Prompt" for index in range(2, 9))

REQUIRED_SAFETY_PHRASES = (
    "not runtime authority",
    "not copied from external runtime references",
    "read-only reference comparator",
    "does not change Control Center behavior",
    "safe refs",
    "Control Center may display and initiate backend-owned envelopes, but it must not mint authority",
)

ABSOLUTE_LOCAL_PATH_PATTERNS = (
    re.compile(r"/Users/[^\s`)]+"),
    re.compile(r"/home/[^\s`)]+"),
    re.compile(r"/var/[^\s`)]+"),
    re.compile(r"/etc/[^\s`)]+"),
)

FORBIDDEN_CLAIMS = (
    "runtime model calls are enabled",
    "provider sdk calls are enabled",
    "live web fetching is enabled",
    "browser automation is enabled",
    "connector writes are enabled",
    "unrestricted shell/subprocess execution is enabled",
    "plugin runtime import is enabled",
    "remote execution is enabled",
    "production authority is enabled",
    "broad autonomy is enabled",
    "external runtime code copied",
)


class VerificationError(RuntimeError):
    """Raised when the scorecard cannot be loaded."""


def _load_report(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise VerificationError("runtime parity scorecard is missing") from exc


def _require_all(text: str, required: tuple[str, ...], label: str) -> list[str]:
    missing = [item for item in required if item not in text]
    return [f"missing {label}: {item}" for item in missing]


def verify(report_path: Path = DEFAULT_REPORT) -> list[str]:
    text = _load_report(report_path)
    lowered = text.lower()
    failures: list[str] = []

    failures.extend(_require_all(text, REQUIRED_SECTIONS, "section"))
    failures.extend(_require_all(text, REQUIRED_DIMENSIONS, "runtime dimension"))
    failures.extend(_require_all(text, REQUIRED_STATUS_LABELS, "status label"))
    failures.extend(_require_all(text, REQUIRED_BLOCKED_AUTHORITY, "blocked authority"))
    failures.extend(_require_all(text, REQUIRED_EVIDENCE_REFS, "evidence ref"))
    failures.extend(_require_all(text, REQUIRED_PHASES, "phase lane"))

    for phrase in REQUIRED_SAFETY_PHRASES:
        if phrase.lower() not in lowered:
            failures.append(f"missing required safety phrase: {phrase}")

    for forbidden in FORBIDDEN_CLAIMS:
        if forbidden in lowered:
            failures.append(f"forbidden overclaim present: {forbidden}")

    for pattern in ABSOLUTE_LOCAL_PATH_PATTERNS:
        if pattern.search(text):
            failures.append("scorecard contains an absolute local path")
            break

    scoreboard_rows = [
        line
        for line in text.splitlines()
        if line.startswith("| ") and any(dimension in line for dimension in REQUIRED_DIMENSIONS)
    ]
    if len(scoreboard_rows) < len(REQUIRED_DIMENSIONS):
        failures.append("component scoreboard is missing one or more runtime dimension rows")

    if "| Runtime parity dimension | Current Score | Target Score |" not in text:
        failures.append("component scoreboard header does not expose current and target scores")

    if "external runtime refs are architectural evidence only" not in text:
        failures.append("external runtime reference posture is not explicit")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)

    try:
        failures = verify(args.report)
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print("UAA runtime parity scorecard verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
