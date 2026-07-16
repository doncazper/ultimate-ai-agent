#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.verification.pytest_shard_plan import CANONICAL_PYTEST_SHARD_COUNT
except ModuleNotFoundError:
    from pytest_shard_plan import CANONICAL_PYTEST_SHARD_COUNT  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_ROOT = "/tmp/uaa_verify_dev_fast"
DEFAULT_TIMINGS_JSON = "/tmp/uaa_verify_dev_fast_timings.json"
DEFAULT_STATIC_TIMINGS_JSON = "/tmp/uaa_verify_all_timings.json"
DEFAULT_PYTEST_TIMINGS_JSON = "/tmp/uaa_pytest_file_timings.json"
DEFAULT_PYTEST_TIMING_SEED_JSON = "scripts/verification/pytest_file_timing_seed.json"
DEFAULT_PYTEST_BASETEMP = "/tmp/uaa_pytest_shards"
DEFAULT_JOBS = 4
DEFAULT_PYTEST_SHARDS = CANONICAL_PYTEST_SHARD_COUNT
DEFAULT_PYTEST_WORKERS = 8
LOG_TAIL_LINES = 80


@dataclass(frozen=True)
class Phase:
    name: str
    command_ref: str
    command: tuple[str, ...]
    env: dict[str, str] | None = None
    parallel: bool = True


@dataclass(frozen=True)
class PhaseResult:
    name: str
    command_ref: str
    command: tuple[str, ...]
    status: str
    elapsed_seconds: float
    returncode: int
    log_path: Path


def resolve_path(raw_path: str, root: Path = ROOT) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = root / path
    return path


def build_env(*, pythonpath_src: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    if pythonpath_src:
        src_path = str(ROOT / "src")
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            src_path if not existing else f"{src_path}{os.pathsep}{existing}"
        )
    return env


def build_parallel_phases(args: argparse.Namespace) -> list[Phase]:
    static_timings = resolve_path(args.static_timings_json)
    pytest_timings = resolve_path(args.pytest_timings_json)
    pytest_timing_seed = resolve_path(args.pytest_timing_seed_json)
    pytest_basetemp = resolve_path(args.pytest_basetemp)
    python = sys.executable
    return [
        Phase(
            name="ruff",
            command_ref="command:ruff",
            command=(python, "-m", "ruff", "check", "."),
        ),
        Phase(
            name="pytest-sharded",
            command_ref="command:pytest-sharded",
            command=(
                python,
                "scripts/verification/run_pytest_shards.py",
                "--shards",
                str(args.pytest_shards),
                "--max-workers",
                str(args.pytest_workers),
                "--timings-json",
                str(pytest_timing_seed),
                "--timings-json",
                str(pytest_timings),
                "--basetemp",
                str(pytest_basetemp),
            ),
            env=build_env(pythonpath_src=True),
        ),
        Phase(
            name="static-verification",
            command_ref="command:verify-static",
            command=(
                python,
                "scripts/verify_all.py",
                "--skip-ruff",
                "--skip-pytest",
                "--timings-json",
                str(static_timings),
            ),
        ),
        Phase(
            name="gate-architecture",
            command_ref="command:gate-architecture",
            command=(python, "scripts/verify_gate_architecture.py"),
            env=build_env(pythonpath_src=True),
        ),
    ]


def build_serial_phases() -> list[Phase]:
    python = sys.executable
    return [
        Phase(
            name="foundation-gate",
            command_ref="command:foundation-gate-report-only-no-write",
            command=(
                python,
                "scripts/run_foundation_gate.py",
                "--command-mode",
                "report-only",
                "--no-write-latest",
            ),
            parallel=False,
        )
    ]


def sanitize_ref(value: str) -> str:
    return (
        "".join(char if char.isalnum() else "_" for char in value).strip("_") or "phase"
    )


def run_phase(phase: Phase, log_dir: Path) -> PhaseResult:
    log_path = log_dir / f"{sanitize_ref(phase.command_ref)}.log"
    started = time.perf_counter()
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("$ " + " ".join(phase.command) + "\n\n")
        log_file.flush()
        process = subprocess.run(
            phase.command,
            cwd=ROOT,
            env=phase.env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    elapsed_seconds = time.perf_counter() - started
    return PhaseResult(
        name=phase.name,
        command_ref=phase.command_ref,
        command=phase.command,
        status="passed" if process.returncode == 0 else "failed",
        elapsed_seconds=elapsed_seconds,
        returncode=process.returncode,
        log_path=log_path,
    )


def run_parallel_phases(
    phases: list[Phase], log_dir: Path, jobs: int
) -> list[PhaseResult]:
    pending = list(phases)
    active: dict[int, tuple[Phase, subprocess.Popen[str], Any, float, Path]] = {}
    results: list[PhaseResult] = []
    max_jobs = max(1, jobs)

    while pending or active:
        while pending and len(active) < max_jobs:
            phase = pending.pop(0)
            log_path = log_dir / f"{sanitize_ref(phase.command_ref)}.log"
            log_file = log_path.open("w", encoding="utf-8")
            log_file.write("$ " + " ".join(phase.command) + "\n\n")
            log_file.flush()
            process = subprocess.Popen(
                phase.command,
                cwd=ROOT,
                env=phase.env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
            )
            active[id(process)] = (
                phase,
                process,
                log_file,
                time.perf_counter(),
                log_path,
            )

        for key, (phase, process, log_file, started, log_path) in list(active.items()):
            returncode = process.poll()
            if returncode is None:
                continue
            log_file.close()
            elapsed_seconds = time.perf_counter() - started
            results.append(
                PhaseResult(
                    name=phase.name,
                    command_ref=phase.command_ref,
                    command=phase.command,
                    status="passed" if returncode == 0 else "failed",
                    elapsed_seconds=elapsed_seconds,
                    returncode=returncode,
                    log_path=log_path,
                )
            )
            del active[key]
        if pending or active:
            time.sleep(0.2)

    result_by_name = {result.name: result for result in results}
    return [result_by_name[phase.name] for phase in phases]


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def static_timing_count(path: Path) -> int | None:
    payload = read_json(path)
    if not payload:
        return None
    timings = payload.get("timings")
    if not isinstance(timings, list):
        return None
    return len([item for item in timings if isinstance(item, dict)])


def write_timing_summary(
    path: Path, results: list[PhaseResult], total_elapsed_seconds: float
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "uaa_verify_dev_fast_gate_timings.v1",
        "generated_unix_seconds": time.time(),
        "release_gate": False,
        "summary": {
            "overall_status": "passed"
            if all(result.status == "passed" for result in results)
            else "failed",
            "total_elapsed_seconds": round(total_elapsed_seconds, 3),
            "phase_elapsed_seconds_sum": round(
                sum(result.elapsed_seconds for result in results), 3
            ),
        },
        "phases": [
            {
                "name": result.name,
                "command_ref": result.command_ref,
                "status": result.status,
                "elapsed_seconds": round(result.elapsed_seconds, 3),
                "returncode": result.returncode,
                "log_path": str(result.log_path),
            }
            for result in results
        ],
    }
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temp_path.replace(path)


def format_seconds(value: float) -> str:
    return f"{value:.2f}s"


def tail_text(path: Path, line_count: int = LOG_TAIL_LINES) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"<unable to read log: {exc}>"
    return "\n".join(lines[-line_count:])


def print_success_summary(
    results: list[PhaseResult],
    static_timings_path: Path,
    timings_path: Path,
    total_elapsed_seconds: float,
) -> None:
    print("\n=== Fast Local Verification Summary ===")
    for result in results:
        print(
            f"{result.name}: {result.status} in {format_seconds(result.elapsed_seconds)} "
            f"({result.command_ref}; log={result.log_path})"
        )
    static_count = static_timing_count(static_timings_path)
    if static_count is not None:
        print(f"static verifier tail: {static_count} timed checks")
    print(f"total wall time: {format_seconds(total_elapsed_seconds)}")
    print("docs/product language: represented by verify-static")
    print(
        "OpenAPI/route classification/redaction/authority-boundary: represented by verify-static"
    )
    print("Foundation Gate: passed")
    print(f"Timing summary: {timings_path}")
    print("\nFull release proof remains: make verify")


def print_failure_summary(
    results: list[PhaseResult], timings_path: Path, total_elapsed_seconds: float
) -> None:
    print("\n=== Fast Local Verification Failed ===")
    for result in results:
        print(
            f"{result.name}: {result.status} in {format_seconds(result.elapsed_seconds)} "
            f"return_code={result.returncode} log={result.log_path}"
        )
    print(f"total wall time: {format_seconds(total_elapsed_seconds)}")
    print(f"Timing summary: {timings_path}")
    for result in results:
        if result.status != "failed":
            continue
        print(f"\n--- tail: {result.name} ({result.log_path}) ---")
        print(tail_text(result.log_path))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local/dev verification gate with concise phase summaries."
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=int(os.environ.get("VERIFY_DEV_FAST_JOBS", DEFAULT_JOBS)),
    )
    parser.add_argument(
        "--pytest-shards",
        type=int,
        default=int(os.environ.get("PYTEST_SHARDS", DEFAULT_PYTEST_SHARDS)),
    )
    parser.add_argument(
        "--pytest-workers",
        type=int,
        default=int(
            os.environ.get("PYTEST_SHARD_WORKERS", DEFAULT_PYTEST_WORKERS)
        ),
    )
    parser.add_argument(
        "--pytest-timings-json",
        default=os.environ.get(
            "PYTEST_SHARD_TIMINGS_JSON", DEFAULT_PYTEST_TIMINGS_JSON
        ),
    )
    parser.add_argument(
        "--pytest-timing-seed-json",
        default=os.environ.get(
            "PYTEST_SHARD_TIMING_SEED_JSON",
            DEFAULT_PYTEST_TIMING_SEED_JSON,
        ),
    )
    parser.add_argument(
        "--pytest-basetemp",
        default=os.environ.get("PYTEST_SHARD_BASETEMP", DEFAULT_PYTEST_BASETEMP),
    )
    parser.add_argument(
        "--static-timings-json",
        default=os.environ.get("VERIFY_TIMINGS_JSON", DEFAULT_STATIC_TIMINGS_JSON),
    )
    parser.add_argument("--timings-json", default=DEFAULT_TIMINGS_JSON)
    parser.add_argument("--log-root", default=DEFAULT_LOG_ROOT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.jobs <= 0:
        print("FAIL: --jobs must be greater than zero", file=sys.stderr)
        return 2
    if args.pytest_shards <= 0:
        print("FAIL: --pytest-shards must be greater than zero", file=sys.stderr)
        return 2
    if args.pytest_workers <= 0:
        print("FAIL: --pytest-workers must be greater than zero", file=sys.stderr)
        return 2

    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
    log_dir = resolve_path(args.log_root) / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    timings_path = resolve_path(args.timings_json)
    static_timings_path = resolve_path(args.static_timings_json)

    print("=== Fast Local Verification Gate ===")
    print("Mode: local/dev only")
    print("Release gate unchanged: make verify")
    print(f"Logs: {log_dir}")

    started = time.perf_counter()
    results = run_parallel_phases(build_parallel_phases(args), log_dir, args.jobs)
    if all(result.status == "passed" for result in results):
        for phase in build_serial_phases():
            results.append(run_phase(phase, log_dir))
            if results[-1].status != "passed":
                break

    total_elapsed_seconds = time.perf_counter() - started
    write_timing_summary(timings_path, results, total_elapsed_seconds)
    if all(result.status == "passed" for result in results):
        print_success_summary(
            results, static_timings_path, timings_path, total_elapsed_seconds
        )
        return 0

    print_failure_summary(results, timings_path, total_elapsed_seconds)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
