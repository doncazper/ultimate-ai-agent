#!/usr/bin/env python3
"""Validate the UAA-P1-065 Founder Command Center review cleanup scope."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_REF = "UAA-P1-065"
SCOPE_DOC = ROOT / "docs/control_center/UAA_P1_065_FOUNDER_COMMAND_CENTER_REVIEW_CLEANUP.md"
CURRENT_BOARD = ROOT / "docs/kanban/current_board.md"
FCC_BOARD = ROOT / "docs/kanban/founder_command_center_board.md"
ROADMAP = ROOT / "docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
GAP_MAP = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
DOCS_README = ROOT / "docs/README.md"
DOCS_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
RECOMMENDATION_LOG = ROOT / "docs/backlog/codex_recommendation_log.md"
RECONCILIATION_ARTIFACT = (
    ROOT
    / "docs/backlog/reconciliation/2026-06-21-uaa-p1-065-founder-command-center-review-cleanup.json"
)

SCOPE_REF = "docs/control_center/UAA_P1_065_FOUNDER_COMMAND_CENTER_REVIEW_CLEANUP.md"
PROMOTED_TASK = "FCC-P0-002 Follow-Up Collapse/Organize Control Center Around Core Surfaces"
NEXT_PROMPT_REF = "prompt-ref:uaa-p1-066-local-model-read-only-control-center-status"

REQUIRED_SAFETY_FLAGS = {
    "raw_prompt_included",
    "raw_response_included",
    "raw_provider_payload_included",
    "raw_path_included",
    "raw_log_included",
    "username_included",
    "hostname_included",
    "serial_included",
    "environment_dump_included",
    "credential_material_included",
    "private_content_included",
}

FORBIDDEN_PRIVATE_FRAGMENTS = {
    "/users/",
    "c:\\users\\",
    "raw prompt:",
    "raw response:",
    "raw provider payload:",
    "raw path:",
    "raw log:",
    "username:",
    "hostname:",
    "serial number:",
    "environment dump:",
    "credential:",
    "api_key",
    "secret_key",
    "password=",
    "token=",
}


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _read_text(root: Path, path: Path, failures: list[str]) -> str:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return ""
    return target.read_text(encoding="utf-8")


def _read_json(root: Path, path: Path, failures: list[str]) -> dict[str, Any]:
    rel_path = path.relative_to(ROOT)
    target = root / rel_path
    if not target.exists():
        failures.append(f"missing required file: {rel_path.as_posix()}")
        return {}
    try:
        loaded = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {rel_path.as_posix()}: {exc.msg}")
        return {}
    if not isinstance(loaded, dict):
        failures.append(f"{rel_path.as_posix()} must contain a JSON object")
        return {}
    return loaded


def _scan_text(rel_path: str, text: str) -> list[str]:
    lowered = text.lower()
    return [
        f"{rel_path} contains forbidden raw/private fragment: {fragment}"
        for fragment in sorted(FORBIDDEN_PRIVATE_FRAGMENTS)
        if fragment in lowered
    ]


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
            failures.append(f"{rel_path} missing UAA-P1-065 fragment: {fragment}")


def _validate_scope_doc(root: Path, failures: list[str]) -> None:
    text = _read_text(root, SCOPE_DOC, failures)
    if not text:
        return
    _require_fragments(
        _rel(SCOPE_DOC),
        text,
        [
            "Status: Implemented",
            "Classify Founder Command Center cards",
            "Classification Output",
            "Implemented / ready for review",
            "Candidate-next",
            "Blocked / future",
            "Promoted Next FCC Task",
            PROMOTED_TASK,
            "frontend read-only product-surface organization",
            "This task is not implemented by UAA-P1-065",
            "No backend routes",
            "No OpenAPI operation changes",
            "No Control Center implementation work",
            "No React-only product behavior",
            "No model/provider calls, web fetching",
            "scripts/verify_uaa_p1_065_founder_command_center_review_cleanup.py",
        ],
        failures,
    )
    failures.extend(_scan_text(_rel(SCOPE_DOC), text))


def _validate_active_docs(root: Path, failures: list[str]) -> None:
    required_by_doc = {
        CURRENT_BOARD: [
            "UAA-P1-065 Founder Command Center Review/Cleanup Lane",
            "UAA-P1-066 Local Model Manager Read-Only Control Center Inventory/Status",
            PROMOTED_TASK,
            "UAA-P1-067 completed",
            "UAA-P1-068 completed",
            "UAA-P1-069 completed",
            "UAA-P1-079 is complete",
            "UAA-P1-080 is complete",
            "UAA-P1-081 remains planned/queued",
            "This milestone adds no backend route",
            "UAA-P1-066 remains queued",
        ],
        FCC_BOARD: [
            "UAA-P1-065 completed",
            "Classification Summary",
            "Candidate Next",
            PROMOTED_TASK,
            "This task is not implemented by UAA-P1-065",
            "No backend route",
            "No OpenAPI change",
        ],
        ROADMAP: [
            "`UAA-P1-065` Done",
            PROMOTED_TASK,
            "without adding routes",
            "or runtime authority",
        ],
        PRODUCT_TRUTH: [
            "UAA-P1-065 completes a docs-only Founder Command Center review/cleanup pass",
            PROMOTED_TASK,
            SCOPE_REF,
        ],
        GAP_MAP: [
            "FCC-P0-002",
            "route authority",
        ],
        DOCS_README: [
            SCOPE_REF,
            "completed UAA-P1-065 Founder Command Center review cleanup",
            "completed UAA-P1-067",
            "completed UAA-P1-068",
            "completed UAA-P1-069",
            "completed UAA-P1-079",
        ],
        DOCS_INDEX: [SCOPE_REF],
        RECOMMENDATION_LOG: [
            "UAA-P1-065 Founder Command Center Review/Cleanup Completed",
            PROMOTED_TASK,
            "UAA-P1-066 Local Model Manager Read-Only Control Center",
            SCOPE_REF,
        ],
    }
    for path, fragments in required_by_doc.items():
        text = _read_text(root, path, failures)
        if not text:
            continue
        _require_fragments(_rel(path), text, fragments, failures)
        failures.extend(_scan_text(_rel(path), text))


def _validate_reconciliation_artifact(root: Path, failures: list[str]) -> None:
    artifact = _read_json(root, RECONCILIATION_ARTIFACT, failures)
    if not artifact:
        return
    if artifact.get("reconciliation_id") != (
        "reconciliation:2026-06-21-uaa-p1-065-founder-command-center-review-cleanup"
    ):
        failures.append("UAA-P1-065 reconciliation artifact id drifted")
    if artifact.get("next_prompt_ref") != NEXT_PROMPT_REF:
        failures.append("UAA-P1-065 reconciliation artifact must point to UAA-P1-066")

    safety = artifact.get("reconciliation_safety")
    if not isinstance(safety, dict) or set(safety) != REQUIRED_SAFETY_FLAGS:
        failures.append("UAA-P1-065 reconciliation safety flags are incomplete")
    elif any(safety.get(flag) is not False for flag in REQUIRED_SAFETY_FLAGS):
        failures.append("UAA-P1-065 reconciliation safety flags must all be false")

    serialized = json.dumps(artifact, sort_keys=True)
    for fragment in [
        "recommendation:uaa-p1-065-fcc-board-reconciliation",
        "recommendation:fcc-p0-002-follow-up-candidate",
        "recommendation:fcc-p0-002-follow-up-implementation",
        "recommendation:fcc-runtime-authority",
        "COMPLETED_WITH_EVIDENCE",
        "PROMOTED_FOR_LATER_EXACT_MILESTONE",
        "OUTSIDE_CURRENT_MILESTONE",
        "MISSING_SCOPED_AUTHORITY",
        SCOPE_REF,
        PROMOTED_TASK,
    ]:
        if fragment not in serialized:
            failures.append(f"UAA-P1-065 reconciliation artifact missing: {fragment}")
    failures.extend(_scan_text(_rel(RECONCILIATION_ARTIFACT), serialized))


def validate_uaa_p1_065_founder_command_center_review_cleanup(
    root: Path = ROOT,
) -> list[str]:
    failures: list[str] = []
    _validate_scope_doc(root, failures)
    _validate_active_docs(root, failures)
    _validate_reconciliation_artifact(root, failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate UAA-P1-065 Founder Command Center review cleanup."
    )
    parser.add_argument("--root", default=str(ROOT), help="Repository root to validate.")
    args = parser.parse_args(argv)
    failures = validate_uaa_p1_065_founder_command_center_review_cleanup(
        Path(args.root).resolve()
    )
    if failures:
        print("UAA-P1-065 Founder Command Center review cleanup verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("UAA-P1-065 Founder Command Center review cleanup verification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
