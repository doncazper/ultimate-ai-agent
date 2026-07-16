from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
from pathlib import Path
from typing import Any, Protocol


TIMING_SCHEMA_VERSION = "uaa_pytest_file_timings.v1"
FAILED_TEST_REFS_SCHEMA_VERSION = "uaa_pytest_failed_test_refs.v1"
DURATION_RE = re.compile(r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+\w+\s+(?P<nodeid>.+)$")
MAX_SAFE_FAILURE_REPORT_BYTES = 16_384
MAX_FAILED_TEST_REFS_PER_SHARD = 8
_SAFE_TEST_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_SAFE_TEST_REF_RE = re.compile(
    r"^pytest-test-ref:[a-z0-9_.-]{1,72}:[a-z0-9_.-]{1,72}:[a-f0-9]{12}$"
)


class ShardPlanLike(Protocol):
    index: int
    files: tuple[str, ...]
    expected_seconds: float


class ShardResultLike(Protocol):
    index: int
    file_count: int
    returncode: int
    elapsed_seconds: float
    log_path: Path
    timed_out: bool
    failure_ref_path: Path | None


def _read_bounded_regular_file(path: Path) -> bytes | None:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return None
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > MAX_SAFE_FAILURE_REPORT_BYTES
        ):
            return None
        chunks: list[bytes] = []
        remaining = MAX_SAFE_FAILURE_REPORT_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        return payload if len(payload) <= MAX_SAFE_FAILURE_REPORT_BYTES else None
    finally:
        os.close(descriptor)


def _safe_test_component(value: str, fallback: str) -> str:
    without_parameters = value.split("[", 1)[0]
    normalized = _SAFE_TEST_COMPONENT_RE.sub("-", without_parameters).strip(".-")
    return (normalized[:72] or fallback).lower()


def safe_test_ref(nodeid: str) -> str:
    # Parameter IDs are operator-provided data and may themselves contain the
    # structural ``::`` separator.  Remove the complete parameter suffix before
    # splitting the stable collection metadata so no portion can become a ref.
    parameter_free_nodeid = nodeid.split("[", 1)[0]
    parts = parameter_free_nodeid.replace("\\", "/").split("::")
    module = _safe_test_component(parts[0].rsplit("/", 1)[-1], "test-module")
    test_name = _safe_test_component(parts[-1], "test-case")
    digest = hashlib.sha256(f"{module}::{test_name}".encode("utf-8")).hexdigest()[:12]
    return f"pytest-test-ref:{module}:{test_name}:{digest}"


def is_safe_test_ref(value: object) -> bool:
    """Return true only for a canonical content-free pytest code-metadata ref."""

    if not isinstance(value, str) or _SAFE_TEST_REF_RE.fullmatch(value) is None:
        return False
    _prefix, module, test_name, _digest = value.split(":", maxsplit=3)
    return safe_test_ref(f"{module}::{test_name}") == value


def collect_failed_test_refs(
    results: list[ShardResultLike],
) -> dict[int, tuple[str, ...]]:
    """Return bounded code-metadata refs without retaining failure payloads."""

    refs_by_shard: dict[int, tuple[str, ...]] = {}
    for result in results:
        if result.returncode == 0 or result.failure_ref_path is None:
            continue
        payload = _read_bounded_regular_file(result.failure_ref_path)
        if payload is None:
            continue
        try:
            decoded = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(decoded, dict) or set(decoded) != {
            "schema_version",
            "failed_test_refs",
        }:
            continue
        raw_refs = decoded.get("failed_test_refs")
        if (
            decoded.get("schema_version") != FAILED_TEST_REFS_SCHEMA_VERSION
            or not isinstance(raw_refs, list)
            or len(raw_refs) > MAX_FAILED_TEST_REFS_PER_SHARD
            or any(not is_safe_test_ref(ref) for ref in raw_refs)
        ):
            continue
        refs = tuple(dict.fromkeys(raw_refs))
        if refs:
            refs_by_shard[result.index] = refs
    return refs_by_shard


def _read_timing_profile(timings_json: Path) -> tuple[dict[str, float], str]:
    if not timings_json.exists():
        return {}, "missing"
    try:
        payload = json.loads(timings_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, "unreadable"

    if not isinstance(payload, dict):
        return {}, "unsupported-schema"
    schema_version = payload.get("schema_version")
    if schema_version not in (None, TIMING_SCHEMA_VERSION):
        return {}, "unsupported-schema"
    raw_timings = payload.get("timings")
    timings: dict[str, float] = {}
    if isinstance(raw_timings, dict):
        entries = raw_timings.items()
    elif isinstance(raw_timings, list):
        entries = (
            (entry.get("path"), entry.get("seconds"))
            for entry in raw_timings
            if isinstance(entry, dict)
        )
    else:
        return {}, "unsupported-schema"
    for file_path, seconds in entries:
        if (
            isinstance(file_path, str)
            and isinstance(seconds, (int, float))
            and not isinstance(seconds, bool)
            and math.isfinite(float(seconds))
            and 0.0 < float(seconds) <= 3_600.0
        ):
            timings[file_path] = float(seconds)
    return timings, "loaded" if timings else "empty"


def _complete_timings(
    raw_timings: dict[str, float], files: list[str]
) -> tuple[dict[str, float] | None, str]:
    known = {
        file_path: raw_timings[file_path]
        for file_path in files
        if raw_timings.get(file_path, 0.0) > 0.0
    }
    if not known:
        return None, "no-current-file-timings"
    missing = [file_path for file_path in files if file_path not in known]
    if not missing:
        return known, "complete"
    ordered = sorted(known.values())
    fallback_index = max(0, math.ceil(len(ordered) * 0.90) - 1)
    fallback = max(ordered[fallback_index], 0.001)
    completed = {file_path: known.get(file_path, fallback) for file_path in files}
    return completed, f"partial:{len(missing)}:fallback={fallback:.3f}s"


def load_complete_timings(
    timings_json: Path | None, files: list[str]
) -> tuple[dict[str, float] | None, str]:
    if timings_json is None:
        return None, "not-requested"
    raw_timings, source = _read_timing_profile(timings_json)
    if not raw_timings:
        return None, source
    return _complete_timings(raw_timings, files)


def load_timing_profiles(
    timing_paths: list[Path], files: list[str]
) -> tuple[dict[str, float] | None, str]:
    merged: dict[str, float] = {}
    loaded_count = 0
    statuses: list[str] = []
    for timing_path in timing_paths:
        timings, status = _read_timing_profile(timing_path)
        statuses.append(status)
        if timings:
            merged.update(timings)
            loaded_count += 1
    if not merged:
        return None, "+".join(statuses) if statuses else "not-requested"
    completed, completeness = _complete_timings(merged, files)
    return completed, f"profiles={loaded_count}:{completeness}"


def parse_pytest_durations(log_text: str, allowed_files: set[str]) -> dict[str, float]:
    durations: dict[str, float] = {}
    for line in log_text.splitlines():
        match = DURATION_RE.match(line)
        if not match:
            continue
        nodeid = match.group("nodeid").strip()
        file_path = nodeid.split("::", 1)[0].replace("\\", "/")
        if file_path not in allowed_files:
            continue
        durations[file_path] = durations.get(file_path, 0.0) + float(
            match.group("seconds")
        )
    return durations


def resolve_path(path: str | None, root: Path) -> Path | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = root / resolved
    return resolved


def collect_file_timings(
    plans: list[ShardPlanLike],
    results: list[ShardResultLike],
    allowed_files: set[str],
) -> list[dict[str, Any]]:
    result_by_index = {result.index: result for result in results}
    timing_by_file: dict[str, tuple[float, str]] = {}
    for plan in plans:
        result = result_by_index[plan.index]
        log_text = result.log_path.read_text(encoding="utf-8", errors="replace")
        parsed = parse_pytest_durations(log_text, set(plan.files))
        missing_files = [
            file_path for file_path in plan.files if parsed.get(file_path, 0.0) <= 0.0
        ]
        attributed_seconds = sum(seconds for seconds in parsed.values() if seconds > 0)
        residual_seconds = max(result.elapsed_seconds - attributed_seconds, 0.0)
        fallback_seconds = max(
            residual_seconds / len(missing_files) if missing_files else 0.0,
            0.001,
        )
        for file_path in plan.files:
            if file_path in parsed and parsed[file_path] > 0:
                timing_by_file[file_path] = (
                    parsed[file_path],
                    "pytest-duration-summary",
                )
            else:
                timing_by_file[file_path] = (
                    fallback_seconds,
                    "shard-elapsed-fallback",
                )

    return [
        {
            "path": file_path,
            "seconds": round(timing_by_file[file_path][0], 6),
            "source": timing_by_file[file_path][1],
        }
        for file_path in sorted(allowed_files)
        if file_path in timing_by_file
    ]


def write_timings_json(path: Path, timing_entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "advisory_only": True,
        "declared_source_run_status": "green",
        "schema_version": TIMING_SCHEMA_VERSION,
        "source_run_status_attestation": "operator_supplied_advisory",
        "timed_file_count": len(timing_entries),
        "timings": timing_entries,
        "verification_evidence": False,
    }
    temp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temp_path.replace(path)


def write_performance_report(
    path: Path,
    *,
    plans: list[ShardPlanLike],
    results: list[ShardResultLike],
    target_seconds: float,
    stretch_goal_seconds: float,
    hard_timeout_seconds: float,
    total_elapsed_seconds: float,
    estimated_timings: dict[str, float] | None,
    plan_fingerprint_ref: str = "pytest-shard-plan-ref:not-recorded",
    failed_test_refs: dict[int, tuple[str, ...]] | None = None,
) -> None:
    result_by_index = {result.index: result for result in results}
    status = "within_stretch_goal"
    run_status = "green"
    if any(result.timed_out for result in results):
        status = "hard_limit_exceeded"
        run_status = "timeout"
    elif any(result.returncode != 0 for result in results):
        status = "test_failed"
        run_status = "failed"
    elif total_elapsed_seconds > target_seconds:
        status = "target_exceeded"
    elif total_elapsed_seconds > stretch_goal_seconds:
        status = "within_target"
    candidates = sorted(
        (
            {
                "test_ref": file_path,
                "estimated_seconds": round(
                    (estimated_timings or {}).get(
                        file_path,
                        plan.expected_seconds / max(len(plan.files), 1),
                    ),
                    6,
                ),
                "shard_index": plan.index,
            }
            for plan in plans
            for file_path in plan.files
        ),
        key=lambda item: (-item["estimated_seconds"], item["test_ref"]),
    )[:25]
    shard_rows = []
    for plan in plans:
        result = result_by_index.get(plan.index)
        shard_rows.append(
            {
                "shard_index": plan.index,
                "file_count": len(plan.files),
                "expected_seconds": plan.expected_seconds,
                "elapsed_seconds": (
                    round(result.elapsed_seconds, 6) if result else 0.0
                ),
                "return_code": result.returncode if result else 1,
                "timed_out": result.timed_out if result else True,
                "failed_test_refs": list((failed_test_refs or {}).get(plan.index, ())),
            }
        )
    payload = {
        "advisory_only": True,
        "schema_version": "uaa_pytest_performance_report.v1",
        "status": status,
        "run_status": run_status,
        "stretch_goal_seconds": stretch_goal_seconds,
        "target_seconds": target_seconds,
        "hard_timeout_seconds": hard_timeout_seconds,
        "total_elapsed_seconds": round(total_elapsed_seconds, 6),
        "refactor_required": status in {"target_exceeded", "hard_limit_exceeded"},
        "stretch_goal_met": run_status == "green" and status == "within_stretch_goal",
        "shards": shard_rows,
        "refactor_candidates": candidates,
        "verification_evidence": False,
        "plan_fingerprint_ref": plan_fingerprint_ref,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temp_path.replace(path)


def print_summary(
    results: list[ShardResultLike],
    *,
    assignment_method: str,
    timing_source: str,
    timing_output: Path | None,
    performance_output: Path | None,
    stretch_goal_seconds: float,
    target_seconds: float,
    hard_timeout_seconds: float,
    total_elapsed_seconds: float,
    safe_summary: bool,
    plan_fingerprint_ref: str = "pytest-shard-plan-ref:not-recorded",
    failed_test_refs: dict[int, tuple[str, ...]] | None = None,
) -> None:
    print("\n=== Pytest Shard Summary ===")
    print(f"Assignment: {assignment_method}")
    print(f"Timing source: {timing_source}")
    print(f"Plan fingerprint: {plan_fingerprint_ref}")
    print(
        "Runtime budget: "
        f"stretch_goal_seconds={stretch_goal_seconds:.2f} "
        f"target_seconds={target_seconds:.2f} "
        f"hard_timeout_seconds={hard_timeout_seconds:.2f} "
        f"total_elapsed_seconds={total_elapsed_seconds:.2f}"
    )
    for result in results:
        log_ref = (
            f"pytest-shard-log:{result.index}" if safe_summary else str(result.log_path)
        )
        print(
            "shard "
            f"{result.index}: files={result.file_count} "
            f"return_code={result.returncode} "
            f"elapsed_seconds={result.elapsed_seconds:.2f} log_ref={log_ref}"
        )
        if safe_summary and result.returncode != 0:
            refs = (failed_test_refs or {}).get(result.index, ())
            print(
                f"shard {result.index} failed_test_refs="
                f"{','.join(refs) if refs else 'unavailable'}"
            )
    if timing_output is not None:
        output_ref = (
            "pytest-timing-output:local" if safe_summary else str(timing_output)
        )
        print(f"Timing output ref: {output_ref}")
    if performance_output is not None:
        output_ref = (
            "pytest-performance-report:local"
            if safe_summary
            else str(performance_output)
        )
        print(f"Performance report ref: {output_ref}")


def overall_return_code(results: list[ShardResultLike], timeout_code: int = 124) -> int:
    if any(result.timed_out for result in results):
        return timeout_code
    return 1 if any(result.returncode != 0 for result in results) else 0
