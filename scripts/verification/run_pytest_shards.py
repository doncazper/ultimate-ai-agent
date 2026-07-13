#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.verification.pytest_shard_artifacts import (
        TIMING_SCHEMA_VERSION,  # noqa: F401 - compatibility re-export
        collect_file_timings,
        load_complete_timings,  # noqa: F401 - compatibility re-export
        load_timing_profiles,
        overall_return_code,
        parse_pytest_durations,  # noqa: F401 - compatibility re-export
        print_summary,
        resolve_path,
        write_performance_report,
        write_timings_json,
    )
    from scripts.verification import pytest_shard_processes as shard_processes
except ModuleNotFoundError:  # Direct script execution from the repository root.
    from pytest_shard_artifacts import (  # type: ignore[no-redef]
        TIMING_SCHEMA_VERSION,  # noqa: F401 - compatibility re-export
        collect_file_timings,
        load_complete_timings,  # noqa: F401 - compatibility re-export
        load_timing_profiles,
        overall_return_code,
        parse_pytest_durations,  # noqa: F401 - compatibility re-export
        print_summary,
        resolve_path,
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


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASETEMP = "/tmp/uaa_pytest_shards"
DEFAULT_SHARDS = 8
DEFAULT_MAX_WORKERS = 8
DEFAULT_STRETCH_GOAL_SECONDS = 110.0
DEFAULT_TARGET_SECONDS = 125.0
DEFAULT_HARD_TIMEOUT_SECONDS = 180.0
DEFAULT_TERMINATION_GRACE_SECONDS = 2.0
DEFAULT_PERFORMANCE_REPORT = "/tmp/uaa_pytest_performance_report.json"
TIMEOUT_RETURN_CODE = 124
FOUNDATION_GATE_AFFINITY_TOKENS = ("foundation_gate_report", "foundation_gate_results")
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
SHARD_ENV_ALLOWLIST_EXACT = frozenset(
    {
        "HOME",
        "LANG",
        "PATH",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONHASHSEED",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "SHELL",
        "TEMP",
        "TERM",
        "TMP",
        "TMPDIR",
        "TZ",
        "VIRTUAL_ENV",
    }
)
SHARD_ENV_ALLOWLIST_PREFIXES = ("LC_",)


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


class ShardRunInterrupted(RuntimeError):
    def __init__(self, signum: int) -> None:
        super().__init__(f"pytest shard run interrupted by signal {signum}")
        self.signum = signum


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


def validate_runtime_budget(
    *,
    stretch_goal_seconds: float,
    target_seconds: float,
    hard_timeout_seconds: float,
    termination_grace_seconds: float,
) -> None:
    if not math.isfinite(stretch_goal_seconds) or stretch_goal_seconds <= 0:
        raise ValueError("--stretch-goal-seconds must be finite and greater than zero")
    if not math.isfinite(target_seconds) or target_seconds <= stretch_goal_seconds:
        raise ValueError(
            "--target-seconds must be finite and exceed --stretch-goal-seconds"
        )
    if (
        not math.isfinite(hard_timeout_seconds)
        or hard_timeout_seconds <= target_seconds
    ):
        raise ValueError(
            "--hard-timeout-seconds must be finite and exceed --target-seconds"
        )
    if not math.isfinite(termination_grace_seconds) or termination_grace_seconds < 0:
        raise ValueError("--termination-grace-seconds must be finite and non-negative")


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
    validate_runtime_budget(
        stretch_goal_seconds=stretch_goal_seconds,
        target_seconds=target_seconds,
        hard_timeout_seconds=hard_timeout_seconds,
        termination_grace_seconds=termination_grace_seconds,
    )
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
    handled_signals = shard_processes.cancellation_signals()
    launch_registration_active = False
    pending_signal: int | None = None

    def interrupt_run(signum: int, _frame: Any) -> None:
        nonlocal pending_signal
        if launch_registration_active:
            pending_signal = signum
            return
        shard_processes.ignore_signals(handled_signals)
        raise ShardRunInterrupted(signum)

    with shard_processes.installed_signal_handlers(handled_signals, interrupt_run):
        try:
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
                    shard_env = shard_processes.isolated_shard_environment(env, temp_dir / f"runtime-{plan.index}")
                    if not quiet:
                        print(
                            f"Starting shard {plan.index}: files={len(plan.files)} "
                            f"expected_seconds={plan.expected_seconds:.2f} log={log_path}"
                        )
                    log_handle = log_path.open("w", encoding="utf-8")
                    log_handle.write("$ " + " ".join(command) + "\n\n")
                    log_handle.flush()
                    launch_registration_active = True
                    try:
                        process = subprocess.Popen(
                            command,
                            cwd=root,
                            env=shard_env,
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
                    finally:
                        launch_registration_active = False
                        if pending_signal is not None:
                            interrupted_by = pending_signal
                            pending_signal = None
                            interrupt_run(interrupted_by, None)

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
        except BaseException:
            _stop_active_shards(active, termination_grace_seconds)
            for _index, (_process, log_handle, _started, _log_path, _plan) in list(
                active.items()
            ):
                if not log_handle.closed:
                    log_handle.write(
                        "\nPytest shard terminated because the runner was interrupted.\n"
                    )
                    log_handle.close()
            active.clear()
            raise

    return [results[index] for index in sorted(results)]


def _terminate_active_shards(
    active: dict[int, tuple[subprocess.Popen[str], Any, float, Path, ShardPlan]],
    results: dict[int, ShardResult],
    hard_timeout_seconds: float,
    termination_grace_seconds: float,
) -> None:
    _stop_active_shards(active, termination_grace_seconds)
    for index, (process, log_handle, started, log_path, plan) in list(active.items()):
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


def _stop_active_shards(
    active: dict[int, tuple[subprocess.Popen[str], Any, float, Path, ShardPlan]],
    termination_grace_seconds: float,
) -> None:
    shard_processes.stop_processes(
        (process for process, *_rest in active.values()), termination_grace_seconds
    )


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
    env = {
        name: value
        for name, value in strip_live_model_opt_in_env(base_env).items()
        if name in SHARD_ENV_ALLOWLIST_EXACT
        or any(name.startswith(prefix) for prefix in SHARD_ENV_ALLOWLIST_PREFIXES)
    }
    env["PYTHONPATH"] = _prepend_pythonpath(str(root / "src"), env.get("PYTHONPATH"))
    return env


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
        validate_shard_plans(files, plans, args.shards, affinity_groups)
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
    except ShardRunInterrupted as exc:
        print(
            "Pytest shard run interrupted; active shard process groups were terminated.",
            file=sys.stderr,
        )
        return 128 + exc.signum
    return_code = overall_return_code(results, TIMEOUT_RETURN_CODE)
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
            plan_fingerprint_ref=plan_fingerprint_ref,
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
    )
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
