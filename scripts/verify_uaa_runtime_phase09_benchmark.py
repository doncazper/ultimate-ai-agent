#!/usr/bin/env python3
"""Verify the finite Phase 09 scenario result artifact."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_uaa_runtime_phase09_benchmark import (  # noqa: E402
    SCENARIOS,
    scenario_execution_fingerprint,
    scenario_registry_fingerprint,
)

DEFAULT_RESULTS = (
    ROOT
    / "docs"
    / "benchmarks"
    / "runtime_capability_foundation"
    / "phase09_scenario_results.json"
)
EXPECTED_SCENARIOS = (
    ("scenario:ambiguous-intent", "reasoning_task_understanding", "passed", None),
    ("scenario:plan-revision", "reasoning_task_understanding", "passed", None),
    ("scenario:dag-replay-crash", "planning_orchestration", "passed", None),
    ("scenario:approval-expiry", "autonomy_authority", "passed", None),
    ("scenario:cancellation-race", "planning_orchestration", "passed", None),
    ("scenario:budget-exhaustion-settlement", "planning_orchestration", "passed", None),
    ("scenario:exact-tool-idempotency", "action_tool_calling", "passed", None),
    (
        "scenario:sandbox-escape-denial",
        "code_implementation_assistance",
        "blocked",
        "SANDBOX_FACILITY_NOT_PROVEN",
    ),
    ("scenario:memory-correction", "memory_context_management", "passed", None),
    ("scenario:web-citation-injection", "research_web_external", "passed", None),
    ("scenario:provider-stale-unavailable", "model_provider_management", "passed", None),
    (
        "scenario:receipt-tamper-surface-parity",
        "evidence_audit_observability",
        "passed",
        None,
    ),
)
TOP_LEVEL_KEYS = {
    "schema_version",
    "benchmark_ref",
    "status",
    "scenario_count",
    "registry_fingerprint",
    "scenarios",
    "redaction",
}
SCENARIO_KEYS = {
    "scenario_id",
    "scenario_version",
    "component_id",
    "status",
    "confidence",
    "evidence_refs",
    "test_verifier_refs",
    "duration_seconds",
    "blocker_code",
    "redaction_status",
    "execution_fingerprint",
}
REPO_REF_RE = re.compile(r"^repo-ref:uaa:([^#]+)(?:#L\d+(?:-L?\d+)?)?$")
ABSOLUTE_PATH_RE = re.compile(
    r"(?:/Users/|/home/|/private/|/var/|/tmp/|[A-Za-z]:\\)"
)
SECRET_RE = re.compile(
    r"(?:api[_-]?key|secret|password|credential|access[_-]?token)\s*[:=]",
    re.IGNORECASE,
)
FORBIDDEN_KEYS = {
    "raw_prompt",
    "raw_response",
    "raw_result",
    "raw_page",
    "raw_log",
    "provider_payload",
    "credential",
    "secret",
    "token",
    "username",
    "hostname",
    "environment_dump",
    "local_path",
}


class VerificationError(RuntimeError):
    """Raised when the Phase 09 artifact is unsafe or inconsistent."""


def _walk(value: Any, key: str | None = None) -> None:
    if key in FORBIDDEN_KEYS:
        raise VerificationError(f"unsafe durable field: {key}")
    if isinstance(value, dict):
        for child_key, child in value.items():
            _walk(child, child_key)
    elif isinstance(value, list):
        for child in value:
            _walk(child, key)
    elif isinstance(value, str):
        if ABSOLUTE_PATH_RE.search(value):
            raise VerificationError("absolute local path is forbidden")
        if SECRET_RE.search(value):
            raise VerificationError("secret-like value is forbidden")


def _require_refs(value: Any, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise VerificationError(f"{label} must be non-empty")
    for ref in value:
        if not isinstance(ref, str):
            raise VerificationError(f"{label} must contain strings")
        match = REPO_REF_RE.fullmatch(ref)
        if match is None:
            raise VerificationError(f"unsupported {label} ref")
        relative = Path(match.group(1))
        try:
            current = ROOT
            target_stat = os.lstat(current)
            for part in relative.parts:
                current /= part
                target_stat = os.lstat(current)
                if stat.S_ISLNK(target_stat.st_mode):
                    raise VerificationError(f"missing or unsafe {label} ref")
        except FileNotFoundError as exc:
            raise VerificationError(f"missing or unsafe {label} ref") from exc
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or stat.S_ISLNK(target_stat.st_mode)
            or not stat.S_ISREG(target_stat.st_mode)
        ):
            raise VerificationError(f"missing or unsafe {label} ref")


def _read_bounded_json(path: Path, *, max_bytes: int = 1_000_000) -> dict[str, Any]:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    try:
        for part in absolute.parts[1:-1]:
            current /= part
            if stat.S_ISLNK(os.lstat(current).st_mode):
                raise VerificationError(
                    "scenario artifact parent must not be a symlink"
                )
    except FileNotFoundError as exc:
        raise VerificationError("scenario artifact is missing or invalid") from exc
    try:
        path_stat = os.lstat(path)
    except FileNotFoundError as exc:
        raise VerificationError("scenario artifact is missing or invalid") from exc
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISREG(path_stat.st_mode):
        raise VerificationError("scenario artifact must be a regular non-symlink file")
    if path_stat.st_size > max_bytes:
        raise VerificationError("scenario artifact exceeds the size limit")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        opened_stat = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened_stat.st_mode)
            or opened_stat.st_dev != path_stat.st_dev
            or opened_stat.st_ino != path_stat.st_ino
            or opened_stat.st_size > max_bytes
        ):
            raise VerificationError("scenario artifact changed during bounded open")
        encoded = os.read(descriptor, max_bytes + 1)
    finally:
        os.close(descriptor)
    if len(encoded) > max_bytes:
        raise VerificationError("scenario artifact exceeds the size limit")
    try:
        data = json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("scenario artifact is missing or invalid") from exc
    if not isinstance(data, dict):
        raise VerificationError("scenario artifact must be an object")
    return data


def verify_data(data: dict[str, Any]) -> None:
    _walk(data)
    if set(data) != TOP_LEVEL_KEYS:
        raise VerificationError("top-level keys drift")
    if data["schema_version"] != "uaa_runtime_capability_phase09_scenarios.v1":
        raise VerificationError("schema version drift")
    if data["benchmark_ref"] != "benchmark-ref:runtime-capability-foundation:phase09-scenarios":
        raise VerificationError("benchmark ref drift")
    if data["status"] != "passed_with_truthful_blocked_sandbox":
        raise VerificationError("final scenario status is not accepted")
    if data["registry_fingerprint"] != scenario_registry_fingerprint():
        raise VerificationError("scenario registry fingerprint drift")
    scenarios = data["scenarios"]
    if not isinstance(scenarios, list) or len(scenarios) != len(EXPECTED_SCENARIOS):
        raise VerificationError("exactly twelve scenarios are required")
    if data["scenario_count"] != len(scenarios):
        raise VerificationError("scenario count drift")
    for scenario, expected, spec in zip(
        scenarios, EXPECTED_SCENARIOS, SCENARIOS, strict=True
    ):
        if not isinstance(scenario, dict) or set(scenario) != SCENARIO_KEYS:
            raise VerificationError("scenario keys drift")
        identity = (
            scenario["scenario_id"],
            scenario["component_id"],
            scenario["status"],
            scenario["blocker_code"],
        )
        if identity != expected:
            raise VerificationError("scenario identity, status, or blocker drift")
        if scenario["scenario_version"] != "1.0":
            raise VerificationError("scenario version drift")
        expected_confidence = (
            "medium"
            if scenario["scenario_id"] == "scenario:receipt-tamper-surface-parity"
            else "high"
        )
        if scenario["confidence"] != expected_confidence:
            raise VerificationError("scenario confidence drift")
        if scenario["redaction_status"] != "safe_refs_only":
            raise VerificationError("scenario redaction drift")
        duration = scenario["duration_seconds"]
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or not 0 < duration <= 600:
            raise VerificationError("scenario duration is invalid")
        _require_refs(scenario["evidence_refs"], "evidence")
        _require_refs(scenario["test_verifier_refs"], "test/verifier")
        if scenario["evidence_refs"] != list(spec.evidence_refs):
            raise VerificationError("scenario evidence binding drift")
        if scenario["test_verifier_refs"] != list(spec.test_verifier_refs):
            raise VerificationError("scenario test/verifier binding drift")
        if scenario["execution_fingerprint"] != scenario_execution_fingerprint(spec):
            raise VerificationError("scenario execution fingerprint drift")
    expected_redaction = {
        "safe_refs_only": True,
        "raw_content_persisted": False,
        "local_paths_persisted": False,
        "machine_identity_persisted": False,
    }
    if data["redaction"] != expected_redaction:
        raise VerificationError("redaction contract drift")


def verify(path: Path = DEFAULT_RESULTS) -> dict[str, Any]:
    data = _read_bounded_json(path)
    verify_data(data)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args(argv)
    try:
        data = verify(args.results)
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        "UAA Phase 09 benchmark verified: "
        f"{data['scenario_count']} scenarios; raw outputs omitted"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
