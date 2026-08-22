#!/usr/bin/env python3
"""Verify the bounded ECO-006 Today and Morning Briefing projection core."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId
from ultimate_ai_agent.core.ecosystem.today import (
    TodayFreshness,
    TodayProjectionRequest,
    TodaySourceStatus,
    build_today_and_morning_briefing,
)


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/ecosystem/today.py",
    "tests/test_eco_006_today.py",
    "docs/architecture/ECO_006_TODAY_AND_MORNING_BRIEFING.md",
    "docs/decisions/ADR-0068-today-and-morning-briefing-projection.md",
)
PROHIBITED_RUNTIME_IMPORTS = (
    "http.client",
    "httpx",
    "requests",
    "subprocess",
    "urllib.request",
    "urllib3",
)
DENIED_SOURCE_FRAGMENTS = (
    "background_work_started=True",
    "external_read_performed=True",
    "mutation_authorized=True",
    "ranking_performed=True",
)


def _qualified_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = _qualified_name(node.value, aliases)
        return None if parent is None else f"{parent}.{node.attr}"
    return None


def _forbidden_runtime_refs(source: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ("invalid-python-source",)
    aliases: dict[str, str] = {}
    findings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name.split(".", 1)[0]] = item.name
                if item.name in PROHIBITED_RUNTIME_IMPORTS:
                    findings.add(item.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
            if node.module in PROHIBITED_RUNTIME_IMPORTS:
                findings.add(node.module)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Call, ast.Attribute)):
            continue
        target = node.func if isinstance(node, ast.Call) else node
        qualified = _qualified_name(target, aliases)
        if qualified is None:
            continue
        for prohibited in PROHIBITED_RUNTIME_IMPORTS:
            if qualified == prohibited or qualified.startswith(f"{prohibited}."):
                findings.add(prohibited)
    return tuple(sorted(findings))


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing ECO-006 artifact: {relative}")
    source_path = ROOT / REQUIRED_FILES[0]
    if not source_path.is_file():
        return failures
    source = source_path.read_text(encoding="utf-8")
    for runtime_ref in _forbidden_runtime_refs(source):
        failures.append(f"forbidden ECO-006 runtime ref: {runtime_ref}")
    for fragment in DENIED_SOURCE_FRAGMENTS:
        if fragment in source:
            failures.append(f"denied ECO-006 authority fragment: {fragment}")

    try:
        request = TodayProjectionRequest(
            workspace_ref="workspace-ref:eco-006-verifier",
            as_of=datetime(2026, 8, 22, 10, tzinfo=timezone.utc),
        )
        result = build_today_and_morning_briefing(
            request=request,
            supplemental_source_statuses=(
                TodaySourceStatus(
                    owner_app=CanonicalOwnerId.inbox,
                    workspace_ref=request.workspace_ref,
                    source_ref="source-ref:manual-inbox",
                    freshness=TodayFreshness.missing,
                    why_status_refs=(
                        "why-source-status-ref:eco-006/manual-input-missing",
                    ),
                ),
            ),
        )
        payload = result.model_dump(mode="json")
        if result.today.ranking_performed or result.today.mutation_authorized:
            failures.append("ECO-006 projection granted ranking or mutation authority")
        if result.external_read_performed or result.background_work_started:
            failures.append("ECO-006 projection performed runtime work")
        if payload["today"]["source_statuses"][0]["freshness"] != "missing":
            failures.append("ECO-006 missing-source posture was not preserved")
        if "raw-content-marker" in json.dumps(payload, sort_keys=True):
            failures.append("ECO-006 raw content marker leaked")
    except Exception as exc:  # pragma: no cover - surfaced as verifier output
        failures.append(
            f"ECO-006 operational verification failed: {type(exc).__name__}"
        )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("ECO-006 Today and Morning Briefing verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
