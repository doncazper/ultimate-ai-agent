#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import os
import socket
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.verification import pytest_collection_evidence
    from scripts.verification.pytest_shard_artifacts import (
        FAILED_TEST_REFS_SCHEMA_VERSION,  # noqa: F401 - compatibility re-export
        MAX_FAILED_TEST_REFS_PER_SHARD,  # noqa: F401 - compatibility re-export
        MAX_SAFE_FAILURE_REPORT_BYTES,  # noqa: F401 - compatibility re-export
        TIMING_SCHEMA_VERSION,  # noqa: F401 - compatibility re-export
        collect_file_timings,
        collect_failed_test_refs,
        is_safe_test_ref,  # noqa: F401 - compatibility re-export
        load_complete_timings,  # noqa: F401 - compatibility re-export
        load_timing_profiles,
        overall_return_code,
        parse_pytest_durations,  # noqa: F401 - compatibility re-export
        print_summary,
        resolve_path,
        safe_test_ref,  # noqa: F401 - compatibility re-export
        write_performance_report,
        write_timings_json,
    )
    from scripts.verification import pytest_shard_processes as shard_processes
except ModuleNotFoundError:  # Direct script execution from the repository root.
    import pytest_collection_evidence  # type: ignore[no-redef]
    from pytest_shard_artifacts import (  # type: ignore[no-redef]
        FAILED_TEST_REFS_SCHEMA_VERSION,  # noqa: F401 - compatibility re-export
        MAX_FAILED_TEST_REFS_PER_SHARD,  # noqa: F401 - compatibility re-export
        MAX_SAFE_FAILURE_REPORT_BYTES,  # noqa: F401 - compatibility re-export
        TIMING_SCHEMA_VERSION,  # noqa: F401 - compatibility re-export
        collect_file_timings,
        collect_failed_test_refs,
        is_safe_test_ref,  # noqa: F401 - compatibility re-export
        load_complete_timings,  # noqa: F401 - compatibility re-export
        load_timing_profiles,
        overall_return_code,
        parse_pytest_durations,  # noqa: F401 - compatibility re-export
        print_summary,
        resolve_path,
        safe_test_ref,  # noqa: F401 - compatibility re-export
        write_performance_report,
        write_timings_json,
    )
    import pytest_shard_processes as shard_processes  # type: ignore[no-redef]

try:
    from scripts.verification import pytest_shard_plan
except ModuleNotFoundError:  # Direct script execution from the repository root.
    import pytest_shard_plan  # type: ignore[no-redef]

shard_plan_fingerprint = pytest_shard_plan.shard_plan_fingerprint
validate_shard_plans = pytest_shard_plan.validate_shard_plans
CANONICAL_PYTEST_SHARD_COUNT = pytest_shard_plan.CANONICAL_PYTEST_SHARD_COUNT
build_shard_env = shard_processes.build_shard_env
is_live_model_opt_in_env_var = shard_processes.is_live_model_opt_in_env_var
validate_runtime_budget = shard_processes.validate_runtime_budget


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASETEMP = "/tmp/uaa_pytest_shards"
DEFAULT_SHARDS = CANONICAL_PYTEST_SHARD_COUNT
DEFAULT_MAX_WORKERS = 8
DEFAULT_STRETCH_GOAL_SECONDS = 110.0
DEFAULT_TARGET_SECONDS = 125.0
DEFAULT_HARD_TIMEOUT_SECONDS = 180.0
DEFAULT_TERMINATION_GRACE_SECONDS = 2.0
DEFAULT_PERFORMANCE_REPORT = "/tmp/uaa_pytest_performance_report.json"
TIMEOUT_RETURN_CODE = 124
FOUNDATION_GATE_AFFINITY_TOKENS = ("foundation_gate_report", "foundation_gate_results")
MATRIX_LOOPBACK_PORT_AFFINITY_TOKEN = (
    "PYTEST_EXCLUSIVE_RESOURCE_MATRIX_LOOPBACK = True"
)
MATRIX_LOOPBACK_TEST_HOST = "127.0.0.1"
MATRIX_LOOPBACK_TEST_PORT = 18008


@dataclass(frozen=True)
class ShardPlan:
    index: int
    files: tuple[str, ...]
    expected_seconds: float
    serialized_preflight: bool = False


@dataclass(frozen=True)
class ShardResult:
    index: int
    file_count: int
    returncode: int
    elapsed_seconds: float
    log_path: Path
    timed_out: bool = False
    failure_ref_path: Path | None = None
    collection_evidence_path: Path | None = None


class ShardRunInterrupted(RuntimeError):
    def __init__(self, signum: int) -> None:
        super().__init__(f"pytest shard run interrupted by signal {signum}")
        self.signum = signum


class MatrixLoopbackTestResourceUnavailableError(RuntimeError):
    """Raised before pytest starts when its exact loopback fixture is occupied."""


def assert_matrix_loopback_test_resource_available() -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # ThreadingHTTPServer enables address reuse. Mirror that exact bind
        # posture so a recently closed fixture in TIME_WAIT is not mistaken for
        # a live competing listener.
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind((MATRIX_LOOPBACK_TEST_HOST, MATRIX_LOOPBACK_TEST_PORT))
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise
        raise MatrixLoopbackTestResourceUnavailableError(
            "exact Matrix loopback test resource is unavailable"
        ) from exc
    finally:
        probe.close()


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
    matrix_loopback_port_consumers: list[str] = []
    for file_path in files:
        try:
            source = (root / file_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if any(token in source for token in FOUNDATION_GATE_AFFINITY_TOKENS):
            foundation_consumers.append(file_path)
        if MATRIX_LOOPBACK_PORT_AFFINITY_TOKEN in source:
            matrix_loopback_port_consumers.append(file_path)
    groups: list[tuple[str, ...]] = []
    for consumers in (foundation_consumers, matrix_loopback_port_consumers):
        if len(consumers) > 1:
            groups.append(tuple(sorted(consumers)))
    return groups


def discover_serialized_preflight_groups(
    files: list[str],
    root: Path = ROOT,
) -> list[tuple[str, ...]]:
    consumers: list[str] = []
    for file_path in files:
        try:
            source = (root / file_path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(
                "serialized preflight resource scan could not read a test file"
            ) from exc
        if MATRIX_LOOPBACK_PORT_AFFINITY_TOKEN in source:
            consumers.append(file_path)
    return [tuple(sorted(consumers))] if consumers else []


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


def current_shard_plan_fingerprint(
    root: Path, shard_count: int, timings_path: Path
) -> str:
    files = discover_test_files(root)
    timings, _source = load_timing_profiles([timings_path], files)
    affinity_groups = discover_affinity_groups(files, root)
    serialized_groups = discover_serialized_preflight_groups(files, root)
    plans, _method = assign_shards(
        files,
        shard_count,
        timings,
        affinity_groups,
        exclusive_affinity_groups=serialized_groups,
    )
    validate_shard_plans(
        files,
        plans,
        shard_count,
        affinity_groups,
        serialized_groups,
    )
    return shard_plan_fingerprint(plans)


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


def assign_shards(
    files: list[str],
    shard_count: int,
    timings: dict[str, float] | None,
    affinity_groups: list[tuple[str, ...]] | None = None,
    *,
    exclusive_affinity_groups: list[tuple[str, ...]] | None = None,
) -> tuple[list[ShardPlan], str]:
    if shard_count <= 0:
        raise ValueError("--shards must be greater than zero")
    normalized_affinity = {
        tuple(sorted(set(group))) for group in (affinity_groups or [])
    }
    exclusive_groups = [
        tuple(sorted(set(group))) for group in (exclusive_affinity_groups or [])
    ]
    if any(group not in normalized_affinity for group in exclusive_groups):
        raise ValueError("exclusive preflight group must be an affinity group")
    if exclusive_groups and len(exclusive_groups) >= shard_count:
        raise ValueError("exclusive preflight groups exhaust configured shards")
    exclusive_files = {
        file_path for group in exclusive_groups for file_path in group
    }
    remaining_files = [
        file_path for file_path in files if file_path not in exclusive_files
    ]
    remaining_affinity = [
        group
        for group in (affinity_groups or [])
        if tuple(sorted(set(group))) not in set(exclusive_groups)
    ]
    assign_count = shard_count - len(exclusive_groups)
    if timings:
        assigned = timing_aware_shards(
            remaining_files,
            assign_count,
            timings,
            remaining_affinity,
        )
        method = "timing-aware"
    else:
        assigned = deterministic_file_count_shards(
            remaining_files,
            assign_count,
            remaining_affinity,
        )
        method = "deterministic-file-count"
    plans = [
        *(
            ShardPlan(
                index=index,
                files=group,
                expected_seconds=(
                    round(sum(timings[path] for path in group), 6)
                    if timings
                    else 0.0
                ),
                serialized_preflight=True,
            )
            for index, group in enumerate(exclusive_groups)
        ),
        *(
            ShardPlan(
                index=plan.index + len(exclusive_groups),
                files=plan.files,
                expected_seconds=plan.expected_seconds,
                serialized_preflight=False,
            )
            for plan in assigned
        ),
    ]
    if affinity_groups:
        method += "+fixture-affinity"
    if exclusive_groups:
        method += "+exclusive-resource-preflight"
    return plans, method


def select_shard(plans: list[ShardPlan], shard_index: int | None) -> list[ShardPlan]:
    if shard_index is None:
        return plans
    if shard_index < 0 or shard_index >= len(plans):
        raise ValueError("--shard-index must identify one configured shard")
    return [plans[shard_index]]


def build_pytest_command(
    plan: ShardPlan,
    shard_basetemp: Path,
    *,
    write_timings: bool,
    failure_ref_dir: Path | None,
    collection_evidence_dir: Path | None = None,
    collection_shard_count: int | None = None,
    collection_plan_fingerprint_ref: str | None = None,
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
    if failure_ref_dir is not None:
        command.extend(
            [
                "-p",
                "scripts.verification.pytest_safe_failure_plugin",
                "--uaa-safe-failure-report",
                str(failure_ref_dir / f"pytest-shard-{plan.index}.json"),
            ]
        )
    if collection_evidence_dir is not None:
        if collection_shard_count is None or collection_plan_fingerprint_ref is None:
            raise ValueError("pytest collection evidence requires exact plan bindings")
        command.extend(
            [
                "-p",
                "scripts.verification.pytest_collection_evidence",
                "--uaa-collection-evidence-sidecar",
                str(collection_evidence_dir / f"pytest-shard-{plan.index}.json"),
                "--uaa-collection-shard-index",
                str(plan.index),
                "--uaa-collection-shard-count",
                str(collection_shard_count),
                "--uaa-collection-plan-fingerprint",
                collection_plan_fingerprint_ref,
            ]
        )
    command.extend(plan.files)
    return command


def _prepare_failure_ref_run_dir(base: Path | None, run_id: str) -> Path | None:
    if base is None:
        return None
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    metadata = base.lstat()
    if not base.is_dir() or base.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("pytest failure-ref root must be a regular directory")
    base.chmod(0o700)
    run_dir = base / run_id
    run_dir.mkdir(mode=0o700, exist_ok=False)
    if run_dir.is_symlink() or not stat.S_ISDIR(run_dir.lstat().st_mode):
        raise ValueError("pytest failure-ref run directory must be a regular directory")
    return run_dir


def run_shards(
    plans: list[ShardPlan],
    *,
    root: Path,
    basetemp: Path,
    failure_ref_dir: Path | None,
    write_timings: bool,
    quiet: bool,
    collection_evidence_output: Path | None = None,
    collection_plan_fingerprint_ref: str | None = None,
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
    validate_runtime_budget(
        stretch_goal_seconds=stretch_goal_seconds,
        target_seconds=target_seconds,
        hard_timeout_seconds=hard_timeout_seconds,
        termination_grace_seconds=termination_grace_seconds,
    )
    run_started = time.perf_counter() if overall_started is None else overall_started
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}-{time.monotonic_ns()}"
    run_root = basetemp / run_id
    log_dir = run_root / "logs"
    temp_dir = run_root / "tmp"
    log_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    run_failure_ref_dir = _prepare_failure_ref_run_dir(failure_ref_dir, run_id)
    collection_evidence_dir: Path | None = None
    if collection_evidence_output is not None:
        if collection_plan_fingerprint_ref is None:
            raise pytest_collection_evidence.CollectionEvidenceError(
                "collection evidence requires the shard-plan fingerprint"
            )
        if [plan.index for plan in plans] != list(range(len(plans))):
            raise pytest_collection_evidence.CollectionEvidenceError(
                "collection evidence requires the complete contiguous shard set"
            )
        assigned_files = [file_path for plan in plans for file_path in plan.files]
        if len(assigned_files) != len(set(assigned_files)):
            raise pytest_collection_evidence.CollectionEvidenceError(
                "collection evidence requires unique shard file ownership"
            )
        if len(plans) > pytest_collection_evidence.MAX_SHARDS:
            raise pytest_collection_evidence.CollectionEvidenceError(
                "collection evidence shard count exceeds the bound"
            )
        if any(not plan.files for plan in plans):
            raise pytest_collection_evidence.CollectionEvidenceError(
                "collection evidence does not permit empty shard invocations"
            )
        pytest_collection_evidence.validate_new_evidence_target(
            collection_evidence_output
        )
        collection_evidence_dir = run_root / "collection-evidence"
        pytest_collection_evidence.prepare_private_directory(collection_evidence_dir)

    env = build_shard_env(root)

    serialized_preflight = tuple(
        plan.index for plan in plans if plan.serialized_preflight
    )
    serialized_preflight_set = set(serialized_preflight)
    pending = [
        *(plan for index in serialized_preflight for plan in plans if plan.index == index),
        *(plan for plan in plans if plan.index not in serialized_preflight_set),
    ]
    serialized_preflight_remaining = set(serialized_preflight)
    active: dict[int, tuple[subprocess.Popen[str], Any, float, Path, ShardPlan]] = {}
    results: dict[int, ShardResult] = {}
    stretch_reported = False
    target_reported = False
    handled_signals = shard_processes.cancellation_signals()
    pending_signal: int | None = None

    def interrupt_run(signum: int, _frame: Any) -> None:
        nonlocal pending_signal
        if pending_signal is None:
            pending_signal = signum

    def raise_pending_signal() -> None:
        nonlocal pending_signal
        if pending_signal is None:
            return
        interrupted_by = pending_signal
        pending_signal = None
        shard_processes.ignore_signals(handled_signals)
        raise ShardRunInterrupted(interrupted_by)

    with shard_processes.installed_signal_handlers(handled_signals, interrupt_run):
        try:
            while pending or active:
                raise_pending_signal()
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
                    raise_pending_signal()
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
                            failure_ref_path=(
                                run_failure_ref_dir / f"pytest-shard-{plan.index}.json"
                                if run_failure_ref_dir is not None
                                else None
                            ),
                            timed_out=True,
                        )
                    pending.clear()
                    break
                active_worker_limit = (
                    1 if serialized_preflight_remaining else worker_limit
                )
                while pending and len(active) < active_worker_limit:
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
                        serialized_preflight_remaining.discard(plan.index)
                        continue
                    command = build_pytest_command(
                        plan,
                        temp_dir / f"shard-{plan.index}",
                        write_timings=write_timings,
                        failure_ref_dir=run_failure_ref_dir,
                        collection_evidence_dir=collection_evidence_dir,
                        collection_shard_count=len(plans),
                        collection_plan_fingerprint_ref=(
                            collection_plan_fingerprint_ref
                        ),
                    )
                    shard_env = shard_processes.isolated_shard_environment(
                        env, temp_dir / f"runtime-{plan.index}"
                    )
                    if not quiet:
                        print(
                            f"Starting shard {plan.index}: files={len(plan.files)} "
                            f"expected_seconds={plan.expected_seconds:.2f} log={log_path}"
                        )
                    log_handle = log_path.open("w", encoding="utf-8")
                    log_handle.write("$ " + " ".join(command) + "\n\n")
                    log_handle.flush()
                    process: subprocess.Popen[str] | None = None
                    try:
                        process = shard_processes.spawn_owned_process_group(
                            command,
                            cwd=root,
                            env=shard_env,
                            stdout=log_handle,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                        active[plan.index] = (
                            process,
                            log_handle,
                            time.perf_counter(),
                            log_path,
                            plan,
                        )
                    except BaseException:
                        if process is not None:
                            try:
                                shard_processes.stop_processes(
                                    (process,),
                                    termination_grace_seconds,
                                )
                            finally:
                                log_handle.close()
                        else:
                            log_handle.close()
                        raise
                    else:
                        raise_pending_signal()

                for index, (process, log_handle, started, log_path, plan) in list(
                    active.items()
                ):
                    if not shard_processes.process_group_leader_is_terminal_without_reaping(
                        process
                    ):
                        continue
                    try:
                        shard_processes.stop_processes(
                            (process,),
                            termination_grace_seconds,
                        )
                        if not isinstance(process.returncode, int):
                            raise RuntimeError(
                                "pytest shard terminal status is unavailable"
                            )
                        returncode = process.returncode
                        elapsed = time.perf_counter() - started
                        log_handle.close()
                        results[index] = ShardResult(
                            index=index,
                            file_count=len(plan.files),
                            returncode=returncode,
                            elapsed_seconds=elapsed,
                            log_path=log_path,
                            failure_ref_path=(
                                run_failure_ref_dir / f"pytest-shard-{plan.index}.json"
                                if run_failure_ref_dir is not None
                                else None
                            ),
                            collection_evidence_path=(
                                collection_evidence_dir
                                / f"pytest-shard-{plan.index}.json"
                                if collection_evidence_dir is not None
                                else None
                            ),
                        )
                        serialized_preflight_remaining.discard(index)
                        del active[index]
                    except BaseException:
                        if not log_handle.closed:
                            log_handle.write(
                                "\nPytest shard process-group cleanup could not be proven.\n"
                            )
                            log_handle.close()
                        raise
                    else:
                        raise_pending_signal()
                if active:
                    time.sleep(0.2)
            raise_pending_signal()
        except BaseException:
            _stop_active_shards(active, termination_grace_seconds)
            for (
                _index,
                (_process, log_handle, _started, _log_path, _plan),
            ) in list(active.items()):
                if not log_handle.closed:
                    log_handle.write(
                        "\nPytest shard terminated because the runner was interrupted.\n"
                    )
                    log_handle.close()
            active.clear()
            raise

    ordered_results = [results[index] for index in sorted(results)]
    if collection_evidence_output is not None:
        assert collection_evidence_dir is not None
        assert collection_plan_fingerprint_ref is not None
        pytest_collection_evidence.publish_aggregate_evidence(
            (
                collection_evidence_dir / f"pytest-shard-{plan.index}.json"
                for plan in plans
            ),
            output_path=collection_evidence_output,
            expected_shard_count=len(plans),
            expected_plan_fingerprint_ref=collection_plan_fingerprint_ref,
        )
    return ordered_results


def _terminate_active_shards(
    active: dict[int, tuple[subprocess.Popen[str], Any, float, Path, ShardPlan]],
    results: dict[int, ShardResult],
    hard_timeout_seconds: float,
    termination_grace_seconds: float,
) -> None:
    terminating = dict(active)
    try:
        _stop_active_shards(terminating, termination_grace_seconds)
    except BaseException:
        for _process, log_handle, _started, _log_path, _plan in terminating.values():
            if not log_handle.closed:
                log_handle.write(
                    "\nPytest shard process-group cleanup could not be proven.\n"
                )
                log_handle.close()
        raise
    active.clear()
    for index, (process, log_handle, started, log_path, plan) in terminating.items():
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


def _stop_active_shards(
    active: dict[int, tuple[subprocess.Popen[str], Any, float, Path, ShardPlan]],
    termination_grace_seconds: float,
) -> None:
    shard_processes.stop_processes(
        (process for process, *_rest in active.values()), termination_grace_seconds
    )


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
    parser.add_argument("--failure-ref-dir")
    parser.add_argument(
        "--collection-evidence",
        help=(
            "Write one content-free collection proof from the tests observed by "
            "the complete real shard run."
        ),
    )
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
    raw_args = sys.argv[1:] if argv is None else argv
    if any(
        argument == "--junit-dir" or argument.startswith("--junit-dir=")
        for argument in raw_args
    ):
        parser.error(
            "--junit-dir was removed because raw JUnit artifacts are not retained; "
            "use --failure-ref-dir for bounded content-free failure refs"
        )
    return parser.parse_args(raw_args)


def main(argv: list[str] | None = None) -> int:
    overall_started = time.perf_counter()
    args = parse_args(argv)
    if args.shards <= 0:
        print("FAIL: --shards must be greater than zero", file=sys.stderr)
        return 2
    if args.max_workers <= 0:
        print("FAIL: --max-workers must be greater than zero", file=sys.stderr)
        return 2
    try:
        validate_runtime_budget(
            stretch_goal_seconds=args.stretch_goal_seconds,
            target_seconds=args.target_seconds,
            hard_timeout_seconds=args.hard_timeout_seconds,
            termination_grace_seconds=args.termination_grace_seconds,
        )
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    if args.shard_index is not None and args.write_timings_json is not None:
        print(
            "FAIL: --write-timings-json requires the complete shard set",
            file=sys.stderr,
        )
        return 2
    if args.shard_index is not None and args.collection_evidence is not None:
        print(
            "FAIL: --collection-evidence requires the complete shard set",
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
    failure_ref_dir = resolve_path(args.failure_ref_dir, ROOT)
    collection_evidence_output = resolve_path(args.collection_evidence, ROOT)
    performance_report_path = resolve_path(args.performance_report, ROOT)
    assert basetemp is not None

    timings, timing_source = load_timing_profiles(timing_paths, files)
    affinity_groups = discover_affinity_groups(files, ROOT)
    serialized_groups = discover_serialized_preflight_groups(files, ROOT)
    plans, assignment_method = assign_shards(
        files,
        args.shards,
        timings,
        affinity_groups,
        exclusive_affinity_groups=serialized_groups,
    )
    try:
        validate_shard_plans(
            files,
            plans,
            args.shards,
            affinity_groups,
            serialized_groups,
        )
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    plan_fingerprint_ref = shard_plan_fingerprint(plans)
    try:
        plans = select_shard(plans, args.shard_index)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    try:
        results = run_shards(
            plans,
            root=ROOT,
            basetemp=basetemp,
            failure_ref_dir=failure_ref_dir,
            write_timings=write_timings_path is not None,
            quiet=args.quiet,
            collection_evidence_output=collection_evidence_output,
            collection_plan_fingerprint_ref=plan_fingerprint_ref,
            max_workers=min(args.max_workers, len(plans)),
            stretch_goal_seconds=args.stretch_goal_seconds,
            target_seconds=args.target_seconds,
            hard_timeout_seconds=args.hard_timeout_seconds,
            termination_grace_seconds=args.termination_grace_seconds,
            overall_started=overall_started,
        )
    except ShardRunInterrupted as exc:
        print(
            "Pytest shard run interrupted; active shard process groups were terminated.",
            file=sys.stderr,
        )
        return 128 + exc.signum
    except pytest_collection_evidence.CollectionEvidenceError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    return_code = overall_return_code(results, TIMEOUT_RETURN_CODE)
    total_elapsed_seconds = time.perf_counter() - overall_started
    failed_test_refs = collect_failed_test_refs(results)

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
            plan_fingerprint_ref=plan_fingerprint_ref,
            failed_test_refs=failed_test_refs,
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
        plan_fingerprint_ref=plan_fingerprint_ref,
        failed_test_refs=failed_test_refs,
    )
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
