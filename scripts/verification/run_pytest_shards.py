#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TIMING_SCHEMA_VERSION = "uaa_pytest_file_timings.v1"
DEFAULT_BASETEMP = "/tmp/uaa_pytest_shards"
DEFAULT_SHARDS = 4
DURATION_RE = re.compile(r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+\w+\s+(?P<nodeid>.+)$")
LIVE_MODEL_ENV_DENYLIST_PREFIXES = (
    "UAA_M160_LIVE_HF_",
    "UAA_M162_LIVE_HF_",
    "UAA_M164_LLAMA_CPP_",
    "UAA_LLAMA_CPP_",
    "UAA_MODEL_ROUTER_SWEEP",
    "UAA_OPENWEBUI_TEST_",
    "UAA_TINY_LIVE_PROVIDER_",
)
LIVE_MODEL_ENV_DENYLIST_EXACT = frozenset(
    {
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


def discover_test_files(root: Path = ROOT) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in (root / "tests").rglob("test_*.py")
        if path.is_file()
    )


def deterministic_file_count_shards(files: list[str], shard_count: int) -> list[ShardPlan]:
    shards = [[] for _ in range(shard_count)]
    for index, file_path in enumerate(sorted(files)):
        shards[index % shard_count].append(file_path)
    return [
        ShardPlan(index=index, files=tuple(shard_files), expected_seconds=0.0)
        for index, shard_files in enumerate(shards)
    ]


def timing_aware_shards(
    files: list[str], shard_count: int, timings: dict[str, float]
) -> list[ShardPlan]:
    shard_files: list[list[str]] = [[] for _ in range(shard_count)]
    shard_totals = [0.0 for _ in range(shard_count)]
    for file_path in sorted(files, key=lambda path: (-timings[path], path)):
        index = min(
            range(shard_count),
            key=lambda shard_index: (
                shard_totals[shard_index],
                len(shard_files[shard_index]),
                shard_index,
            ),
        )
        shard_files[index].append(file_path)
        shard_totals[index] += timings[file_path]
    return [
        ShardPlan(
            index=index,
            files=tuple(sorted(shard_files[index])),
            expected_seconds=round(shard_totals[index], 6),
        )
        for index in range(shard_count)
    ]


def load_complete_timings(
    timings_json: Path | None, files: list[str]
) -> tuple[dict[str, float] | None, str]:
    if timings_json is None:
        return None, "not-requested"
    if not timings_json.exists():
        return None, "missing"
    try:
        payload = json.loads(timings_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "unreadable"

    raw_timings = payload.get("timings")
    timings: dict[str, float] = {}
    if isinstance(raw_timings, dict):
        for file_path, seconds in raw_timings.items():
            if isinstance(file_path, str) and isinstance(seconds, (int, float)):
                timings[file_path] = float(seconds)
    elif isinstance(raw_timings, list):
        for entry in raw_timings:
            if not isinstance(entry, dict):
                continue
            file_path = entry.get("path")
            seconds = entry.get("seconds")
            if isinstance(file_path, str) and isinstance(seconds, (int, float)):
                timings[file_path] = float(seconds)
    else:
        return None, "unsupported-schema"

    missing = [file_path for file_path in files if timings.get(file_path, 0.0) <= 0.0]
    if missing:
        return None, f"incomplete:{len(missing)}"
    return {file_path: timings[file_path] for file_path in files}, "complete"


def assign_shards(
    files: list[str], shard_count: int, timings: dict[str, float] | None
) -> tuple[list[ShardPlan], str]:
    if shard_count <= 0:
        raise ValueError("--shards must be greater than zero")
    if timings:
        return timing_aware_shards(files, shard_count, timings), "timing-aware"
    return deterministic_file_count_shards(files, shard_count), "deterministic-file-count"


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
        durations[file_path] = durations.get(file_path, 0.0) + float(match.group("seconds"))
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
) -> list[ShardResult]:
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
    run_root = basetemp / run_id
    log_dir = run_root / "logs"
    temp_dir = run_root / "tmp"
    log_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    if junit_dir is not None:
        junit_dir.mkdir(parents=True, exist_ok=True)

    env = build_shard_env(root)

    active: dict[int, tuple[subprocess.Popen[str], Any, float, Path, ShardPlan]] = {}
    results: dict[int, ShardResult] = {}
    for plan in plans:
        log_path = log_dir / f"pytest-shard-{plan.index}.log"
        if not plan.files:
            log_path.write_text("No test files assigned to this shard.\n", encoding="utf-8")
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
        )
        active[plan.index] = (process, log_handle, time.perf_counter(), log_path, plan)

    while active:
        for index, (process, log_handle, started, log_path, plan) in list(active.items()):
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


def build_shard_env(root: Path, inherited: dict[str, str] | None = None) -> dict[str, str]:
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
                timing_by_file[file_path] = (parsed[file_path], "pytest-duration-summary")
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
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(path)


def overall_return_code(results: list[ShardResult]) -> int:
    return 1 if any(result.returncode != 0 for result in results) else 0


def print_summary(
    results: list[ShardResult],
    *,
    assignment_method: str,
    timing_source: str,
    timing_output: Path | None,
    safe_summary: bool,
) -> None:
    print("\n=== Pytest Shard Summary ===")
    print(f"Assignment: {assignment_method}")
    print(f"Timing source: {timing_source}")
    for result in results:
        log_ref = (
            f"pytest-shard-log:{result.index}"
            if safe_summary
            else str(result.log_path)
        )
        print(
            "shard "
            f"{result.index}: files={result.file_count} return_code={result.returncode} "
            f"elapsed_seconds={result.elapsed_seconds:.2f} log_ref={log_ref}"
        )
    if timing_output is not None:
        output_ref = (
            "pytest-timing-output:local"
            if safe_summary
            else str(timing_output)
        )
        print(f"Timing output ref: {output_ref}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pytest test files in deterministic local shards."
    )
    parser.add_argument("--shards", type=int, default=DEFAULT_SHARDS)
    parser.add_argument("--shard-index", type=int)
    parser.add_argument("--timings-json")
    parser.add_argument("--write-timings-json")
    parser.add_argument("--basetemp", default=DEFAULT_BASETEMP)
    parser.add_argument("--junit-dir")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--safe-summary", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.shards <= 0:
        print("FAIL: --shards must be greater than zero", file=sys.stderr)
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

    timings_path = resolve_path(args.timings_json, ROOT)
    write_timings_path = resolve_path(args.write_timings_json, ROOT)
    basetemp = resolve_path(args.basetemp, ROOT)
    junit_dir = resolve_path(args.junit_dir, ROOT)
    assert basetemp is not None

    timings, timing_source = load_complete_timings(timings_path, files)
    plans, assignment_method = assign_shards(files, args.shards, timings)
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
    )
    return_code = overall_return_code(results)

    if write_timings_path is not None and return_code == 0:
        timing_entries = collect_file_timings(plans, results, set(files))
        write_timings_json(write_timings_path, timing_entries)
    elif write_timings_path is not None:
        print("Timing output skipped because at least one shard failed.")

    print_summary(
        results,
        assignment_method=assignment_method,
        timing_source=timing_source,
        timing_output=write_timings_path if return_code == 0 else None,
        safe_summary=args.safe_summary,
    )
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
