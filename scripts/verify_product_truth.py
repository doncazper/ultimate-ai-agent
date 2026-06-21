#!/usr/bin/env python3
"""Verify docs, UI, and reports do not describe blocked/pending/mock/planned/partial/not-scoped
work as complete, production-ready, publicly released, signed, audited, or broadly autonomous.

This verifier is repo-local and deterministic. It scans scoped docs and optional frontend
source/build output for product-truth overclaims without echoing the offending content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_TRUTH_SCHEMA_VERSION = "uaa_product_truth_regression.v1"
PRODUCT_TRUTH_TASK_REF = "UAA-P1-057"
DEFAULT_SCOPES = (
    "README.md",
    "docs/kanban/current_board.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "docs/control_center/ROUTE_STATUS_MANIFEST.md",
    "docs/control_center/route_status_manifest.json",
    "docs/control_center/PRODUCT_LANGUAGE_RULES.md",
    "docs/production/RELEASE_VERIFICATION_LANES.md",
    "docs/production/RELEASE_EVIDENCE_PACKET.md",
    "apps/control-center/src",
    "apps/control-center/dist",
)
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
SKIPPED_PATH_FRAGMENTS = (
    "/.git/",
    "/__pycache__/",
    "/node_modules/",
)

# Completion-claim words used in overclaim detection.
_COMPLETION_WORDS = (
    r"(?:complete|done|shipped|released|live|production[- ]ready"
    r"|publicly\s+released|audited|signed)"
)


@dataclass(frozen=True)
class ProductTruthFinding:
    rel_path: str
    line: int
    category: str
    evidence_hash: str
    safe_message: str


# ---------------------------------------------------------------------------
# Patterns
# Each tuple is (category_name, compiled_pattern).
# Patterns must NOT echo or reproduce the offending text in any finding field.
# ---------------------------------------------------------------------------

# -- Incomplete-status subject with completion claim -------------------------
# Structure matched: [STATUS_WORD] [0-5 words] [COPULA] [COMPLETION_WORD]
# Negative lookaheads on common preposition/conjunction bridges prevent
# flagging correct disclaimer language ("blocked for X", "planned for Y", etc.).

_OVERCLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "blocked_work_claimed_complete",
        re.compile(
            r"(?i)\bblocked\s+"
            r"(?!for\b|by\b|from\b|until\b|unless\b|because\b|due\b|as\b)"
            r"(?:[\w-]+\s+){0,5}"
            r"\b(?:is|are|was|has been)\s+" + _COMPLETION_WORDS + r"\b"
        ),
    ),
    (
        "mock_only_work_claimed_complete",
        re.compile(
            r"(?i)\bmock[- ]only\s+"
            r"(?:[\w-]+\s+){0,5}"
            r"\b(?:is|are|was|has been)\s+" + _COMPLETION_WORDS + r"\b"
        ),
    ),
    (
        "not_scoped_work_claimed_complete",
        re.compile(
            r"(?i)\bnot[- ]scoped\s+"
            r"(?:[\w-]+\s+){0,5}"
            r"\b(?:is|are|was|has been)\s+" + _COMPLETION_WORDS + r"\b"
        ),
    ),
    (
        "planned_work_claimed_released",
        re.compile(
            r"(?i)\bplanned\s+"
            r"(?!for\b|as\b|by\b|in\b|during\b|after\b|before\b|until\b|when\b|at\b)"
            r"(?:[\w-]+\s+){0,5}"
            r"\b(?:is|are|was|has been)\s+"
            r"(?:released|shipped|live|production[- ]ready|publicly\s+released|audited|signed)\b"
        ),
    ),
    (
        "pending_work_claimed_complete",
        re.compile(
            r"(?i)\bpending\s+"
            r"(?:[\w-]+\s+){0,5}"
            r"\b(?:is|are|was|has been)\s+" + _COMPLETION_WORDS + r"\b"
        ),
    ),
    (
        "partial_work_claimed_complete",
        re.compile(
            r"(?i)\bpartial\s+"
            r"(?!list\b|view\b|match\b|overlap\b)"
            r"(?:[\w-]+\s+){0,5}"
            r"\b(?:is|are|was|has been)\s+" + _COMPLETION_WORDS + r"\b"
        ),
    ),
    (
        "skipped_work_claimed_passing",
        re.compile(
            r"(?i)\bskipped\s+"
            r"(?:[\w-]+\s+){0,5}"
            r"\b(?:is|are|was|has been)\s+"
            r"(?:passing|complete|done|shipped|released|live)\b"
        ),
    ),
)

# -- Autonomy overclaims ------------------------------------------------------

_AUTONOMY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "broad_autonomy_claim",
        re.compile(r"(?i)\b(?:fully|broadly)\s+autonomous\b"),
    ),
    (
        "autonomous_without_oversight_claim",
        re.compile(r"(?i)\bautonomo\w+\s+(?:without|with no)\s+human\b"),
    ),
    (
        "autonomous_execution_enabled_claim",
        re.compile(
            r"(?i)\bautonomous\s+(?:background\s+)?execution\s+is\s+"
            r"(?:enabled|active|available|live)\b"
        ),
    ),
)

ALL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    *_OVERCLAIM_PATTERNS,
    *_AUTONOMY_PATTERNS,
)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def _safe_hash(rel_path: str, line_number: int, category: str, line: str) -> str:
    digest = hashlib.sha256(
        f"{rel_path}:{line_number}:{category}:{line}".encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest[:16]}"


def _finding(
    *,
    rel_path: str,
    line_number: int,
    category: str,
    line: str,
) -> ProductTruthFinding:
    return ProductTruthFinding(
        rel_path=rel_path,
        line=line_number,
        category=category,
        evidence_hash=_safe_hash(rel_path, line_number, category, line),
        safe_message=(
            f"{rel_path}:{line_number} contains {category}; "
            "offending content redacted"
        ),
    )


def _is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def _iter_scope_files(root: Path, scopes: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for scope in scopes:
        candidate = root / scope
        if not candidate.exists():
            continue
        if candidate.is_file():
            files.append(candidate)
            continue
        for path in candidate.rglob("*"):
            rel = path.relative_to(root).as_posix()
            rel_with_slashes = f"/{rel}/" if path.is_dir() else f"/{rel}"
            if any(
                fragment in rel_with_slashes for fragment in SKIPPED_PATH_FRAGMENTS
            ):
                continue
            if path.is_file() and _is_text_file(path):
                files.append(path)
    return sorted(set(files), key=lambda p: p.relative_to(root).as_posix())


def scan_text(rel_path: str, text: str) -> list[ProductTruthFinding]:
    findings: list[ProductTruthFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for category, pattern in ALL_PATTERNS:
            if pattern.search(line):
                findings.append(
                    _finding(
                        rel_path=rel_path,
                        line_number=line_number,
                        category=category,
                        line=line,
                    )
                )
    return findings


def scan_file(root: Path, path: Path) -> list[ProductTruthFinding]:
    rel_path = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    return scan_text(rel_path, text)


def validate_product_truth(
    root: Path = ROOT,
    scopes: Iterable[str] = DEFAULT_SCOPES,
) -> list[ProductTruthFinding]:
    root = root.resolve()
    findings: list[ProductTruthFinding] = []
    for path in _iter_scope_files(root, scopes):
        findings.extend(scan_file(root, path))
    return findings


def build_scan_report(
    *,
    root: Path = ROOT,
    scopes: Iterable[str] = DEFAULT_SCOPES,
) -> dict[str, object]:
    scanned_files = _iter_scope_files(root.resolve(), scopes)
    findings = validate_product_truth(root=root, scopes=scopes)
    categories = sorted({f.category for f in findings})
    return {
        "schema_version": PRODUCT_TRUTH_SCHEMA_VERSION,
        "task_ref": PRODUCT_TRUTH_TASK_REF,
        "status": "failed" if findings else "passed",
        "scope_refs": list(scopes),
        "scanned_file_count": len(scanned_files),
        "finding_count": len(findings),
        "finding_categories": categories,
        "findings": [asdict(f) for f in findings],
        "report_safety": {
            "raw_prompt_included": False,
            "raw_response_included": False,
            "offending_content_echoed": False,
        },
        "non_goals": [
            "does not execute release lane commands",
            "does not add backend routes or runtime authority",
            "does not add operation IDs or side-effect class changes",
            "does not add model, provider, connector, browser, or shell expansion",
            "does not claim public distribution, signed release, or production readiness",
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify docs/UI/reports do not describe blocked/pending/mock/planned/"
            "partial/not-scoped work as complete, production-ready, or autonomous."
        ),
    )
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Repository root to scan. Default: current repository.",
    )
    parser.add_argument(
        "--scope",
        action="append",
        dest="scopes",
        help="Repo-relative file or directory scope. May be repeated.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = Path(args.root)
    scopes = tuple(args.scopes) if args.scopes else DEFAULT_SCOPES
    report = build_scan_report(root=root, scopes=scopes)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Ultimate AI Agent product-truth regression scan")
        print(f"Schema: {report['schema_version']}")
        print(f"Task: {report['task_ref']}")
        print(f"Status: {report['status']}")
        print(f"Scanned files: {report['scanned_file_count']}")
        print(f"Findings: {report['finding_count']}")
        for finding in report["findings"]:  # type: ignore[index]
            print(
                "- {safe_message} [{evidence_hash}]".format(
                    safe_message=finding["safe_message"],
                    evidence_hash=finding["evidence_hash"],
                )
            )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
