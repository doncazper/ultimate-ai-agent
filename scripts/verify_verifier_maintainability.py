#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.verification.repo import load_json, read_text, repo_path  # noqa: E402
from scripts.verification.test_corpus_guard import (  # noqa: E402
    TestCorpusGuardError,
    verify_test_corpus_guard,
)


POLICY_PATH = "docs/verification/verification_maintainability_policy.json"
MILESTONE_PATTERN = re.compile(r"UAA-P1-(\d{3})")
LINE_BUDGET_ENFORCEMENTS = frozenset({"hard", "advisory"})


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _iter_policy_paths(globs: Iterable[str]) -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in globs:
        for path in ROOT.glob(pattern):
            if path in seen or not path.is_file() or "__pycache__" in path.parts:
                continue
            seen.add(path)
            yield path


def _append_line_budget_findings(
    failures: list[str],
    warnings: list[str],
    label: str,
    section: dict[str, Any],
) -> None:
    enforcement = section.get("enforcement", "hard")
    if not isinstance(enforcement, str) or enforcement not in LINE_BUDGET_ENFORCEMENTS:
        failures.append(
            f"{label} has unsupported line budget enforcement {enforcement!r}"
        )
        return
    max_lines = int(section["max_lines"])
    allowlist = section.get("allowlist", {})
    paths = [repo_path(path) for path in section.get("paths", [])]
    paths.extend(_iter_policy_paths(section.get("globs", [])))

    for path in sorted(set(paths)):
        rel = _relative(path)
        allowed = allowlist.get(rel)
        effective_max = (
            int(allowed.get("max_lines", max_lines)) if allowed else max_lines
        )
        line_count = _line_count(path)
        if line_count > effective_max:
            finding = (
                f"{label} line "
                f"{'review threshold' if enforcement == 'advisory' else 'budget'} "
                f"exceeded for {rel}: {line_count} > {effective_max}"
            )
            (warnings if enforcement == "advisory" else failures).append(finding)


def _append_future_milestone_failures(
    failures: list[str], policy: dict[str, Any]
) -> None:
    for rel_path in policy.get("milestone_future_reference_check", {}).get("paths", []):
        path = repo_path(rel_path)
        if not path.exists():
            failures.append(
                f"future milestone reference check missing path: {rel_path}"
            )
            continue
        own_match = MILESTONE_PATTERN.search(path.name.replace("_", "-").upper())
        if own_match is None:
            failures.append(f"could not infer milestone id from {rel_path}")
            continue
        own_id = int(own_match.group(1))
        for found in MILESTONE_PATTERN.finditer(read_text(path)):
            referenced = int(found.group(1))
            if referenced > own_id:
                failures.append(
                    f"{rel_path} references future milestone UAA-P1-{referenced:03d}"
                )


def _append_duplicate_helper_failures(
    failures: list[str], policy: dict[str, Any]
) -> None:
    for rule in policy.get("banned_duplicate_helpers", []):
        pattern = rule["pattern"]
        allowed_paths = set(rule.get("allowed_paths", []))
        for path in _iter_policy_paths(["scripts/**/*.py", "tests/**/*.py"]):
            rel = _relative(path)
            if rel in allowed_paths:
                continue
            if pattern in read_text(path):
                failures.append(f"{rel} duplicates banned helper pattern {pattern!r}")


def _append_shared_api_lane_failures(
    failures: list[str], policy: dict[str, Any]
) -> None:
    section = policy.get("shared_api_lane_setup", {})
    forbidden_patterns = section.get("forbidden_patterns", [])
    for rel_path in section.get("paths", []):
        path = repo_path(rel_path)
        if not path.exists():
            failures.append(f"shared API lane setup check missing path: {rel_path}")
            continue
        text = read_text(path)
        for pattern in forbidden_patterns:
            if pattern in text:
                failures.append(
                    f"{rel_path} duplicates API lane setup pattern {pattern!r}"
                )


def _append_test_corpus_guard_failures(
    failures: list[str], policy: dict[str, Any]
) -> None:
    if "test_corpus_guard" not in policy:
        return
    try:
        verify_test_corpus_guard(ROOT)
    except TestCorpusGuardError as exc:
        failures.append(f"test corpus guard failed: {exc}")


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    policy = load_json(POLICY_PATH)

    for label, section in policy.get("line_budgets", {}).items():
        _append_line_budget_findings(failures, warnings, label, section)
    _append_future_milestone_failures(failures, policy)
    _append_duplicate_helper_failures(failures, policy)
    _append_shared_api_lane_failures(failures, policy)
    _append_test_corpus_guard_failures(failures, policy)

    for warning in warnings:
        print(f"WARNING: {warning}")
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1
    print("Verifier maintainability verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
