#!/usr/bin/env python3
"""Verify the tool-aware cognition plan and ordered queue insertion."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "strategy" / "UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md"
QUEUE = ROOT / "docs" / "roadmap" / "UAA_TOOL_AWARE_COGNITION_QUEUE_INSERTION.md"
BOARD = ROOT / "docs" / "kanban" / "current_board.md"
ROADMAP = ROOT / "docs" / "roadmap" / "OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"

PLAN_REQUIRED = (
    "This program extends the accepted Turn Contract Router",
    "The configured local model remains responsible for language understanding",
    "zero additional model calls to the direct-chat path",
    "`familiar_supported`",
    "`familiar_input_required`",
    "`familiar_unavailable`",
    "`familiar_requires_approval`",
    "`familiar_authority_blocked`",
    "`ambiguous`",
    "`novel_unsupported`",
    "`outcome_uncertain`",
    "approval cannot mint or broaden authority",
    "do not request an approval that cannot authorize it",
    "direct-chat false-positive tool selection at or below 2%",
    "recall of an applicable capability at or above 95%",
    "blind paired scoring on the accepted ordinary-chat corpus",
    "same frozen local model",
    "report point estimates plus 95% confidence intervals",
    "Human blind scoring with a versioned rubric is the default quality judge",
    "A model-as-judge call is neither implicitly authorized",
    "written to repository reports, receipts, test",
    "number of repeated paired samples",
    "Retrieval must not add a per-turn model or provider call",
    "TAW-00",
    "TAW-08",
    "final GoatCitadel comparison may start only after",
    "No raw conversation is added to a training or evaluation corpus automatically",
    "receipt- and attempt-keyed",
    "fully redacted transformation",
    "Those matches remain classification",
    "excluded only from proposal or execution",
    "evidence-only shadow mode",
    "explicit safe-disable boundary",
    "ordinary chat unavailable",
    "fails closed as unsupported or unavailable",
    "corrupt-index fallback",
)
QUEUE_REQUIRED = (
    "Run the final GoatCitadel comparison only after",
    "The local model remains UAA's language and reasoning engine",
    "The queue item is not complete when these documents merge",
)
BOARD_REQUIRED = (
    "Tool-Aware Cognition And Chat Quality",
    "before the final GoatCitadel comparison",
    "docs/strategy/UAA_TOOL_AWARE_COGNITION_AND_CHAT_QUALITY_PLAN.md",
)
ROADMAP_REQUIRED = (
    "Ordered queue insertion: the Tool-Aware Cognition And Chat Quality program",
    "must reach its TAW-08 acceptance gate before",
    "does not replace the configured local model",
)
FORBIDDEN = (
    "this plan authorizes runtime model calls",
    "this plan grants browser authority",
    "automatic skill activation is allowed",
)
AUTHORITY_DENIALS = (
    "## 12. Explicit Non-Goals",
    "- new runtime model/provider calls;",
    "- web fetching or browser automation;",
    "- connector writes;",
    "- unrestricted shell or subprocess execution;",
    "- automatic skill/plugin import or execution;",
    "- automatic PR submission or merging;",
    "- standing or cross-request approval;",
    "- billing/account changes or credential creation;",
    "- policy, approval, route, OpenAPI, redaction, or Foundation Gate bypass;",
    "- raw prompt, response, provider payload, or local-path persistence; or",
    "- public release, production authority, or claims of human-like",
)
PHASE_HEADINGS = (
    "### TAW-00 — Convergence ledger and evaluation baseline",
    "### TAW-01 — Capability evidence envelope",
    "### TAW-02 — Familiarity and uncertainty assessor",
    "### TAW-03 — Progressive capability retrieval",
    "### TAW-04 — Chat integration and clarification behavior",
    "### TAW-05 — Outcome evidence and governed improvement",
    "### TAW-06 — Operator diagnostics",
    "### TAW-07 — Quality, latency, and adversarial hardening",
    "### TAW-08 — Acceptance and GoatCitadel precondition",
)
QUEUE_ORDERED_STEPS = (
    "1. Finish the currently admitted PR or verification atomic unit",
    "2. Continue already-started prerequisite parity work",
    "3. Execute TAW-00 through TAW-08",
    "4. Run the final GoatCitadel comparison only after",
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        try:
            safe_ref = path.relative_to(ROOT).as_posix()
        except ValueError:
            safe_ref = "required-ref:outside-repository"
        raise RuntimeError(f"missing or unreadable required file: {safe_ref}") from exc


def _require(label: str, text: str, fragments: tuple[str, ...]) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise RuntimeError(f"{label} is missing required fragments: {missing}")


def _require_ordered(label: str, text: str, fragments: tuple[str, ...]) -> None:
    _require(label, text, fragments)
    positions = [text.index(fragment) for fragment in fragments]
    if positions != sorted(positions):
        raise RuntimeError(f"{label} is not in required order")


def verify() -> dict[str, object]:
    plan = _read(PLAN)
    queue = _read(QUEUE)
    board = _read(BOARD)
    roadmap = _read(ROADMAP)
    _require("plan", plan, PLAN_REQUIRED)
    _require("plan authority boundary", plan, AUTHORITY_DENIALS)
    _require("queue insertion", queue, QUEUE_REQUIRED)
    _require_ordered("ordered queue insertion", queue, QUEUE_ORDERED_STEPS)
    _require("current board", board, BOARD_REQUIRED)
    _require("canonical roadmap", roadmap, ROADMAP_REQUIRED)

    combined = "\n".join((plan, queue, board, roadmap)).lower()
    present = [phrase for phrase in FORBIDDEN if phrase in combined]
    if present:
        raise RuntimeError(f"self-authorizing language found: {present}")

    _require_ordered("plan phase headings", plan, PHASE_HEADINGS)

    return {
        "status": "passed",
        "phase_count": len(PHASE_HEADINGS),
        "normal_chat_fast_path": True,
        "direct_chat_quality_non_inferiority": True,
        "local_model_preserved": True,
        "familiarity_states": 8,
        "goat_comparison_gate": True,
        "evaluation_governance": True,
        "reversible_rollout": True,
        "runtime_authority_added": False,
    }


def main() -> int:
    try:
        result = verify()
    except RuntimeError as exc:
        print(f"tool-aware cognition plan verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
