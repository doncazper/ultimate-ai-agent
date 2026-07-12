#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TIMING_SCHEMA_VERSION = "uaa_pytest_file_timings.v1"
DEFAULT_BASETEMP = "/tmp/uaa_pytest_shards"
DEFAULT_SHARDS = 12
DEFAULT_MAX_WORKERS = 12
DEFAULT_STRETCH_GOAL_SECONDS = 90.0
DEFAULT_TARGET_SECONDS = 100.0
DEFAULT_HARD_TIMEOUT_SECONDS = 120.0
DEFAULT_TERMINATION_GRACE_SECONDS = 2.0
DEFAULT_PERFORMANCE_REPORT = "/tmp/uaa_pytest_performance_report.json"
TIMEOUT_RETURN_CODE = 124
FOUNDATION_GATE_AFFINITY_TOKENS = (
    "foundation_gate_report",
    "foundation_gate_results",
)
DURATION_RE = re.compile(r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+\w+\s+(?P<nodeid>.+)$")
LIVE_MODEL_ENV_DENYLIST_PREFIXES = (
    "UAA_M160_LIVE_HF_",
    "UAA_M162_LIVE_HF_",
    "UAA_M164_LLAMA_CPP_",
    "UAA_LLAMA_CPP_",
    "UAA_MODEL_ROUTER_SWEEP",
    "UAA_OPENWEBUI_TEST_",
    "UAA_TINY_LIVE_PROVIDER_",
    "UAA_WEB_HYBRID_LIVE_",
)
LIVE_MODEL_ENV_DENYLIST_EXACT = frozenset(
    {
        "UAA_FIRECRAWL_CLOUD_SECRET_FILE",
        "UAA_LOCAL_MODEL_REF",
        "UAA_LOCAL_MODEL_ROOTS",
    }
)


@dataclass(frozen=True)
class ShardPlan:
    index: int
    files: tuple[str, ...]
    expected_seconds: float


@dataclass(frozen=True)
class ShardResult:
    index: int
    file_count: int
    returncode: int
    elapsed_seconds: float
    log_path: Path
    timed_out: bool = False


def discover_test_files(root: Path = ROOT) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in (root / "tests").rglob("test_*.py")
        if path.is_file()
    )


def discover_affinity_groups(
    files: list[str], root: Path = ROOT
) -> list[tuple[str, ...]]:
    foundation_consumers: list[str] = []
    for file_path in files:
        try:
            source = (root / file_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if any(token in source for token in FOUNDATION_GATE_AFFINITY_TOKENS):
            foundation_consumers.append(file_path)
    return (
        [tuple(sorted(foundation_consumers))] if len(foundation_consumers) > 1 else []
    )


def _assignment_items(
    files: list[str], affinity_groups: list[tuple[str, ...]] | None
) -> list[tuple[str, ...]]:
    known_files = set(files)
    grouped_files: set[str] = set()
    groups: list[tuple[str, ...]] = []
    for group in affinity_groups or []:
        normalized = tuple(sorted(set(group)))
        if (
            len(normalized) < 2
            or any(file_path not in known_files for file_path in normalized)
            or grouped_files.intersection(normalized)
        ):
            raise ValueError(
                "pytest shard affinity groups must be disjoint known files"
            )
        grouped_files.update(normalized)
        groups.append(normalized)
    groups.extend((file_path,) for file_path in sorted(known_files - grouped_files))
    return groups


def deterministic_file_count_shards(
    files: list[str],
    shard_count: int,
    affinity_groups: list[tuple[str, ...]] | None = None,
) -> list[ShardPlan]:
    if not affinity_groups:
        shards = [[] for _ in range(shard_count)]
        for index, file_path in enumerate(sorted(files)):
            shards[index % shard_count].append(file_path)
        return [
            ShardPlan(index=index, files=tuple(shard_files), expected_seconds=0.0)
            for index, shard_files in enumerate(shards)
        ]
    shards = [[] for _ in range(shard_count)]
    for item in sorted(
        _assignment_items(files, affinity_groups),
        key=lambda group: (-len(group), group[0]),
    ):
        index = min(
            range(shard_count),
            key=lambda shard_index: (len(shards[shard_index]), shard_index),
        )
        shards[index].extend(item)
    return [
        ShardPlan(index=index, files=tuple(sorted(shard_files)), expected_seconds=0.0)
        for index, shard_files in enumerate(shards)
    ]


def timing_aware_shards(
    files: list[str],
    shard_count: int,
    timings: dict[str, float],
    affinity_groups: list[tuple[str, ...]] | None = None,
) -> list[ShardPlan]:
    shard_files: list[list[str]] = [[] for _ in range(shard_count)]
    shard_totals = [0.0 for _ in range(shard_count)]
    items = _assignment_items(files, affinity_groups)
    for item in sorted(
        items,
        key=lambda group: (-sum(timings[path] for path in group), group[0]),
    ):
        index = min(
            range(shard_count),
            key=lambda shard_index: (
                shard_totals[shard_index],
                len(shard_files[shard_index]),
                shard_index,
            ),
        )
        shard_files[index].extend(item)
        shard_totals[index] += sum(timings[path] for path in item)
    return [
        ShardPlan(
            index=index,
            files=tuple(sorted(shard_files[index])),
            expected_seconds=round(shard_totals[index], 6),
        )
        for index in range(shard_count)
    ]


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


def assign_shards(
    files: list[str],
    shard_count: int,
    timings: dict[str, float] | None,
    affinity_groups: list[tuple[str, ...]] | None = None,
) -> tuple[list[ShardPlan], str]:
    if shard_count <= 0:
        raise ValueError("--shards must be greater than zero")
    if timings:
        plans = timing_aware_shards(files, shard_count, timings, affinity_groups)
        method = "timing-aware"
    else:
        plans = deterministic_file_count_shards(files, shard_count, affinity_groups)
        method = "deterministic-file-count"
    if affinity_groups:
        method += "+fixture-affinity"
    return plans, method


def select_shard(plans: list[ShardPlan], shard_index: int | None) -> list[ShardPlan]:
    if shard_index is None:
        return plans
    if shard_index < 0 or shard_index >= len(plans):
        raise ValueError("--shard-index must identify one configured shard")
    return [plans[shard_index]]


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


def resolve_path(path: str | None, root: Path = ROOT) -> Path | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = root / resolved
    return resolved


def build_pytest_command(
    plan: ShardPlan,
    shard_basetemp: Path,
    *,
    write_timings: bool,
    junit_dir: Path | None,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        str(shard_basetemp),
    ]
    if write_timings:
        command.extend(["--durations=0", "--durations-min=0"])
    if junit_dir is not None:
        command.append(f"--junitxml={junit_dir / f'pytest-shard-{plan.index}.xml'}")
    command.extend(plan.files)
    return command


def run_shards(
    plans: list[ShardPlan],
    *,
    root: Path,
    basetemp: Path,
    junit_dir: Path | None,
    write_timings: bool,
    quiet: bool,
    max_workers: int | None = None,
    stretch_goal_seconds: float = DEFAULT_STRETCH_GOAL_SECONDS,
    target_seconds: float = DEFAULT_TARGET_SECONDS,
    hard_timeout_seconds: float = DEFAULT_HARD_TIMEOUT_SECONDS,
    termination_grace_seconds: float = DEFAULT_TERMINATION_GRACE_SECONDS,
    overall_started: float | None = None,
) -> list[ShardResult]:
    worker_limit = len(plans) if max_workers is None else max_workers
    if worker_limit <= 0:
        raise ValueError("pytest shard max workers must be greater than zero")
    if stretch_goal_seconds <= 0:
        raise ValueError("pytest shard stretch goal seconds must be greater than zero")
    if target_seconds <= stretch_goal_seconds:
        raise ValueError("pytest shard target must exceed the stretch goal")
    if target_seconds <= 0:
        raise ValueError("pytest shard target seconds must be greater than zero")
    if hard_timeout_seconds <= target_seconds:
        raise ValueError("pytest shard hard timeout must exceed the target")
    if termination_grace_seconds < 0:
        raise ValueError("pytest shard termination grace must not be negative")
    run_started = time.perf_counter() if overall_started is None else overall_started
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
    run_root = basetemp / run_id
    log_dir = run_root / "logs"
    temp_dir = run_root / "tmp"
    log_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    if junit_dir is not None:
        junit_dir.mkdir(parents=True, exist_ok=True)

    env = build_shard_env(root)

    pending = list(plans)
    active: dict[int, tuple[subprocess.Popen[str], Any, float, Path, ShardPlan]] = {}
    results: dict[int, ShardResult] = {}
    stretch_reported = False
    target_reported = False
    while pending or active:
        overall_elapsed = time.perf_counter() - run_started
        if not stretch_reported and overall_elapsed >= stretch_goal_seconds:
            stretch_reported = True
            if not quiet:
                print(
                    "PERFORMANCE NOTICE: pytest shard stretch goal exceeded: "
                    f"elapsed_seconds={overall_elapsed:.2f} "
                    f"stretch_goal_seconds={stretch_goal_seconds:.2f}"
                )
        if not target_reported and overall_elapsed >= target_seconds:
            target_reported = True
            if not quiet:
                print(
                    "PERFORMANCE WARNING: pytest shard target exceeded: "
                    f"elapsed_seconds={overall_elapsed:.2f} target_seconds={target_seconds:.2f}"
                )
        if overall_elapsed >= hard_timeout_seconds:
            if not quiet:
                print(
                    "PERFORMANCE FAILURE: pytest shard hard timeout exceeded; "
                    f"terminating active shards at {overall_elapsed:.2f}s"
                )
            _terminate_active_shards(
                active,
                results,
                hard_timeout_seconds,
                termination_grace_seconds,
            )
            for plan in pending:
                log_path = log_dir / f"pytest-shard-{plan.index}.log"
                log_path.write_text(
                    "Shard did not start because the overall pytest runtime budget expired.\n",
                    encoding="utf-8",
                )
                results[plan.index] = ShardResult(
                    index=plan.index,
                    file_count=len(plan.files),
                    returncode=TIMEOUT_RETURN_CODE,
                    elapsed_seconds=0.0,
                    log_path=log_path,
                    timed_out=True,
                )
            pending.clear()
            break
        while pending and len(active) < worker_limit:
            plan = pending.pop(0)
            log_path = log_dir / f"pytest-shard-{plan.index}.log"
            if not plan.files:
                log_path.write_text(
                    "No test files assigned to this shard.\n", encoding="utf-8"
                )
                results[plan.index] = ShardResult(
                    index=plan.index,
                    file_count=0,
                    returncode=0,
                    elapsed_seconds=0.0,
                    log_path=log_path,
                )
                continue
            command = build_pytest_command(
                plan,
                temp_dir / f"shard-{plan.index}",
                write_timings=write_timings,
                junit_dir=junit_dir,
            )
            if not quiet:
                print(
                    f"Starting shard {plan.index}: files={len(plan.files)} "
                    f"expected_seconds={plan.expected_seconds:.2f} log={log_path}"
                )
            log_handle = log_path.open("w", encoding="utf-8")
            log_handle.write("$ " + " ".join(command) + "\n\n")
            log_handle.flush()
            process = subprocess.Popen(
                command,
                cwd=root,
                env=env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=os.name == "posix",
            )
            active[plan.index] = (
                process,
                log_handle,
                time.perf_counter(),
                log_path,
                plan,
            )

        for index, (process, log_handle, started, log_path, plan) in list(
            active.items()
        ):
            returncode = process.poll()
            if returncode is None:
                continue
            elapsed = time.perf_counter() - started
            log_handle.close()
            results[index] = ShardResult(
                index=index,
                file_count=len(plan.files),
                returncode=returncode,
                elapsed_seconds=elapsed,
                log_path=log_path,
            )
            del active[index]
        if active:
            time.sleep(0.2)

    return [results[index] for index in sorted(results)]


def _signal_process(process: subprocess.Popen[str], sig: signal.Signals) -> None:
    if os.name == "posix" and isinstance(getattr(process, "pid", None), int):
        try:
            os.killpg(process.pid, sig)
            return
        except ProcessLookupError:
            return
    action = process.terminate if sig == signal.SIGTERM else process.kill
    try:
        action()
    except ProcessLookupError:
        return


def _terminate_active_shards(
    active: dict[int, tuple[subprocess.Popen[str], Any, float, Path, ShardPlan]],
    results: dict[int, ShardResult],
    hard_timeout_seconds: float,
    termination_grace_seconds: float,
) -> None:
    for process, _handle, _started, _path, _plan in active.values():
        _signal_process(process, signal.SIGTERM)
    grace_deadline = time.perf_counter() + termination_grace_seconds
    while active and time.perf_counter() < grace_deadline:
        if all(process.poll() is not None for process, *_rest in active.values()):
            break
        time.sleep(0.05)
    for process, _handle, _started, _path, _plan in active.values():
        if process.poll() is None:
            _signal_process(process, signal.SIGKILL)
    for index, (process, log_handle, started, log_path, plan) in list(active.items()):
        try:
            process.wait(timeout=max(termination_grace_seconds, 0.1))
        except subprocess.TimeoutExpired:
            pass
        elapsed = min(time.perf_counter() - started, hard_timeout_seconds)
        log_handle.write(
            "\nPytest shard terminated because the overall runtime budget expired.\n"
        )
        log_handle.close()
        results[index] = ShardResult(
            index=index,
            file_count=len(plan.files),
            returncode=TIMEOUT_RETURN_CODE,
            elapsed_seconds=elapsed,
            log_path=log_path,
            timed_out=True,
        )
        del active[index]


def _prepend_pythonpath(src_path: str, existing: str | None) -> str:
    if not existing:
        return src_path
    return f"{src_path}{os.pathsep}{existing}"


def is_live_model_opt_in_env_var(name: str) -> bool:
    if name in LIVE_MODEL_ENV_DENYLIST_EXACT:
        return True
    return any(name.startswith(prefix) for prefix in LIVE_MODEL_ENV_DENYLIST_PREFIXES)


def strip_live_model_opt_in_env(env: dict[str, str]) -> dict[str, str]:
    return {
        name: value
        for name, value in env.items()
        if not is_live_model_opt_in_env_var(name)
    }


def build_shard_env(
    root: Path, inherited: dict[str, str] | None = None
) -> dict[str, str]:
    base_env = dict(os.environ if inherited is None else inherited)
    env = strip_live_model_opt_in_env(base_env)
    env["PYTHONPATH"] = _prepend_pythonpath(str(root / "src"), env.get("PYTHONPATH"))
    return env


def collect_file_timings(
    plans: list[ShardPlan], results: list[ShardResult], allowed_files: set[str]
) -> list[dict[str, Any]]:
    result_by_index = {result.index: result for result in results}
    timing_by_file: dict[str, tuple[float, str]] = {}
    for plan in plans:
        result = result_by_index[plan.index]
        log_text = result.log_path.read_text(encoding="utf-8", errors="replace")
        parsed = parse_pytest_durations(log_text, set(plan.files))
        fallback_seconds = (
            result.elapsed_seconds / len(plan.files)
            if plan.files and result.elapsed_seconds > 0
            else 0.001
        )
        for file_path in plan.files:
            if file_path in parsed and parsed[file_path] > 0:
                timing_by_file[file_path] = (
                    parsed[file_path],
                    "pytest-duration-summary",
                )
            else:
                timing_by_file[file_path] = (fallback_seconds, "shard-elapsed-fallback")

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
        "schema_version": TIMING_SCHEMA_VERSION,
        "generated_unix_seconds": time.time(),
        "timings": timing_entries,
    }
    temp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temp_path.replace(path)


def write_performance_report(
    path: Path,
    *,
    plans: list[ShardPlan],
    results: list[ShardResult],
    target_seconds: float,
    stretch_goal_seconds: float,
    hard_timeout_seconds: float,
    total_elapsed_seconds: float,
    estimated_timings: dict[str, float] | None,
) -> None:
    result_by_index = {result.index: result for result in results}
    status = "within_stretch_goal"
    if any(result.timed_out for result in results):
        status = "hard_limit_exceeded"
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
                "elapsed_seconds": round(result.elapsed_seconds, 6) if result else 0.0,
                "return_code": result.returncode if result else 1,
                "timed_out": result.timed_out if result else True,
            }
        )
    payload = {
        "schema_version": "uaa_pytest_performance_report.v1",
        "status": status,
        "stretch_goal_seconds": stretch_goal_seconds,
        "target_seconds": target_seconds,
        "hard_timeout_seconds": hard_timeout_seconds,
        "total_elapsed_seconds": round(total_elapsed_seconds, 6),
        "refactor_required": status in {"target_exceeded", "hard_limit_exceeded"},
        "stretch_goal_met": status == "within_stretch_goal",
        "shards": shard_rows,
        "refactor_candidates": candidates,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temp_path.replace(path)


def overall_return_code(results: list[ShardResult]) -> int:
    if any(result.timed_out for result in results):
        return TIMEOUT_RETURN_CODE
    return 1 if any(result.returncode != 0 for result in results) else 0


def print_summary(
    results: list[ShardResult],
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
) -> None:
    print("\n=== Pytest Shard Summary ===")
    print(f"Assignment: {assignment_method}")
    print(f"Timing source: {timing_source}")
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
            f"{result.index}: files={result.file_count} return_code={result.returncode} "
            f"elapsed_seconds={result.elapsed_seconds:.2f} log_ref={log_ref}"
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pytest test files in deterministic local shards."
    )
    parser.add_argument("--shards", type=int, default=DEFAULT_SHARDS)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--timings-json", action="append", default=[])
    parser.add_argument("--write-timings-json")
    parser.add_argument("--basetemp", default=DEFAULT_BASETEMP)
    parser.add_argument("--junit-dir")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--safe-summary", action="store_true")
    parser.add_argument(
        "--stretch-goal-seconds",
        type=float,
        default=DEFAULT_STRETCH_GOAL_SECONDS,
    )
    parser.add_argument("--target-seconds", type=float, default=DEFAULT_TARGET_SECONDS)
    parser.add_argument(
        "--hard-timeout-seconds", type=float, default=DEFAULT_HARD_TIMEOUT_SECONDS
    )
    parser.add_argument(
        "--termination-grace-seconds",
        type=float,
        default=DEFAULT_TERMINATION_GRACE_SECONDS,
    )
    parser.add_argument("--performance-report", default=DEFAULT_PERFORMANCE_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    overall_started = time.perf_counter()
    args = parse_args(argv)
    if args.shards <= 0:
        print("FAIL: --shards must be greater than zero", file=sys.stderr)
        return 2
    if args.max_workers <= 0:
        print("FAIL: --max-workers must be greater than zero", file=sys.stderr)
        return 2
    if args.stretch_goal_seconds <= 0:
        print(
            "FAIL: --stretch-goal-seconds must be greater than zero",
            file=sys.stderr,
        )
        return 2
    if args.target_seconds <= args.stretch_goal_seconds:
        print(
            "FAIL: --target-seconds must exceed --stretch-goal-seconds",
            file=sys.stderr,
        )
        return 2
    if args.target_seconds <= 0:
        print("FAIL: --target-seconds must be greater than zero", file=sys.stderr)
        return 2
    if args.hard_timeout_seconds <= args.target_seconds:
        print(
            "FAIL: --hard-timeout-seconds must exceed --target-seconds",
            file=sys.stderr,
        )
        return 2
    if args.termination_grace_seconds < 0:
        print(
            "FAIL: --termination-grace-seconds must not be negative",
            file=sys.stderr,
        )
        return 2
    if args.shard_index is not None and args.write_timings_json is not None:
        print(
            "FAIL: --write-timings-json requires the complete shard set",
            file=sys.stderr,
        )
        return 2

    files = discover_test_files(ROOT)
    if not files:
        print("FAIL: no tests/test_*.py files discovered", file=sys.stderr)
        return 1

    timing_paths = [
        resolved
        for raw_path in args.timings_json
        if (resolved := resolve_path(raw_path, ROOT)) is not None
    ]
    write_timings_path = resolve_path(args.write_timings_json, ROOT)
    basetemp = resolve_path(args.basetemp, ROOT)
    junit_dir = resolve_path(args.junit_dir, ROOT)
    performance_report_path = resolve_path(args.performance_report, ROOT)
    assert basetemp is not None

    timings, timing_source = load_timing_profiles(timing_paths, files)
    affinity_groups = discover_affinity_groups(files, ROOT)
    plans, assignment_method = assign_shards(
        files,
        args.shards,
        timings,
        affinity_groups,
    )
    try:
        plans = select_shard(plans, args.shard_index)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    results = run_shards(
        plans,
        root=ROOT,
        basetemp=basetemp,
        junit_dir=junit_dir,
        write_timings=write_timings_path is not None,
        quiet=args.quiet,
        max_workers=min(args.max_workers, len(plans)),
        stretch_goal_seconds=args.stretch_goal_seconds,
        target_seconds=args.target_seconds,
        hard_timeout_seconds=args.hard_timeout_seconds,
        termination_grace_seconds=args.termination_grace_seconds,
        overall_started=overall_started,
    )
    return_code = overall_return_code(results)
    total_elapsed_seconds = time.perf_counter() - overall_started

    if write_timings_path is not None and return_code == 0:
        timing_entries = collect_file_timings(plans, results, set(files))
        write_timings_json(write_timings_path, timing_entries)
    elif write_timings_path is not None:
        print("Timing output skipped because at least one shard failed.")

    if performance_report_path is not None:
        write_performance_report(
            performance_report_path,
            plans=plans,
            results=results,
            stretch_goal_seconds=args.stretch_goal_seconds,
            target_seconds=args.target_seconds,
            hard_timeout_seconds=args.hard_timeout_seconds,
            total_elapsed_seconds=total_elapsed_seconds,
            estimated_timings=timings,
        )

    print_summary(
        results,
        assignment_method=assignment_method,
        timing_source=timing_source,
        timing_output=write_timings_path if return_code == 0 else None,
        performance_output=performance_report_path,
        stretch_goal_seconds=args.stretch_goal_seconds,
        target_seconds=args.target_seconds,
        hard_timeout_seconds=args.hard_timeout_seconds,
        total_elapsed_seconds=total_elapsed_seconds,
        safe_summary=args.safe_summary,
    )
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
