#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.verification import pytest_shard_processes as shard_processes  # noqa: E402
from scripts.verification.cpu_budget import (  # noqa: E402
    capped_worker_count,
    resolve_cpu_budget,
)
from scripts.verification.static_scan_plan import (  # noqa: E402
    STATIC_PLAN_SCHEMA,
    StaticScanSpec,
    StaticShardPlan,
    assign_static_shards,
    build_scan_specs,
    exclusive_plans,
    load_static_timings,
    plan_fingerprint,
    scan_registry_fingerprint,
)
from scripts.verification.static_scan_context import (  # noqa: E402
    StaticVerificationContext,
    resolve_repository_sha,
)
from scripts.verification.static_scan_worker import (  # noqa: E402
    PROGRESS_SCHEMA,
    RESULT_SCHEMA,
)


RUN_REPORT_SCHEMA = "uaa-static-scan-run.v1"
DEFAULT_WORKERS = 5
DEFAULT_SCAN_TIMEOUT_SECONDS = 60.0
DEFAULT_TARGET_SECONDS = 60.0
DEFAULT_HARD_TIMEOUT_SECONDS = 180.0
DEFAULT_TERMINATION_GRACE_SECONDS = 2.0


class StaticRunInterrupted(RuntimeError):
    def __init__(self, signum: int) -> None:
        super().__init__(f"static scan run interrupted by signal {signum}")
        self.signum = signum


class StaticSourceCleanupError(ValueError):
    pass


@dataclass(frozen=True)
class StaticScanOutcome:
    scan_index: int
    scan_ref: str
    name: str
    function_name: str
    status: str
    elapsed_ms: int
    failure_ref: str | None = None


@dataclass(frozen=True)
class StaticRunReport:
    passed: bool
    outcomes: tuple[StaticScanOutcome, ...]
    plan_ref: str
    registry_fingerprint: str
    repository_sha: str
    worker_count: int
    total_elapsed_seconds: float
    timed_out: bool = False

    @property
    def timing_entries(self) -> list[dict[str, Any]]:
        return [
            {
                "name": f"static_scan:{outcome.name}",
                "status": outcome.status,
                "elapsed_ms": outcome.elapsed_ms,
            }
            for outcome in self.outcomes
        ]


@dataclass
class _ActiveWorker:
    plan: StaticShardPlan
    process: subprocess.Popen[str]
    result_path: Path
    progress_path: Path
    context_ref: str
    registry_fingerprint: str
    repository_sha: str
    launched_at: float
    active_scan_index: int | None = None
    active_scan_observed_at: float | None = None
    timed_out: bool = False


def _safe_run_root(base: Path | None) -> Path:
    parent = Path(tempfile.gettempdir()) if base is None else base
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if parent.is_symlink() or not stat.S_ISDIR(parent.lstat().st_mode):
        raise ValueError("static scan basetemp must be a regular directory")
    run_root: Path | None = None
    try:
        run_root = Path(tempfile.mkdtemp(prefix="uaa-static-scan-", dir=parent))
        run_root.chmod(0o700)
        return run_root
    except BaseException:
        if run_root is not None:
            _remove_run_root(run_root)
        raise


def _remove_run_root(run_root: Path) -> None:
    pending_interrupt: StaticRunInterrupted | None = None
    try:
        shutil.rmtree(run_root)
    except StaticRunInterrupted as exc:
        pending_interrupt = exc
        try:
            shutil.rmtree(run_root)
        except FileNotFoundError:
            pass
    except FileNotFoundError:
        pass
    if pending_interrupt is not None:
        raise pending_interrupt


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(temp, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


@contextmanager
def _immutable_source_tree(
    root: Path,
    run_root: Path,
    repository_sha: str,
    *,
    deadline: float | None = None,
) -> Iterator[Path]:
    source_root = run_root / "source"
    try:
        checkout_command = (
            "git",
            "worktree",
            "add",
            "--detach",
            str(source_root),
            repository_sha,
        )
        checkout_timeout = 60.0
        if deadline is not None:
            remaining_seconds = deadline - time.perf_counter()
            if remaining_seconds <= 0:
                raise subprocess.TimeoutExpired(checkout_command, timeout=0)
            checkout_timeout = min(checkout_timeout, remaining_seconds)
        added = subprocess.run(
            checkout_command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=checkout_timeout,
        )
        if added.returncode != 0:
            raise ValueError("static scan immutable source checkout failed")
        source_root.chmod(0o700)
        if resolve_repository_sha(source_root) != repository_sha:
            raise ValueError("static scan immutable source identity mismatch")
        yield source_root
        if resolve_repository_sha(source_root) != repository_sha:
            raise ValueError("static scan immutable source identity changed")
    finally:
        pending_interrupt: StaticRunInterrupted | None = None
        try:
            removed = subprocess.run(
                ("git", "worktree", "remove", "--force", str(source_root)),
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except StaticRunInterrupted as exc:
            pending_interrupt = exc
            removed = subprocess.run(
                ("git", "worktree", "remove", "--force", str(source_root)),
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        if removed.returncode != 0:
            removed = subprocess.run(
                ("git", "worktree", "remove", "--force", str(source_root)),
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        if removed.returncode != 0:
            listed = subprocess.run(
                (
                    "git",
                    "-c",
                    "core.quotePath=false",
                    "worktree",
                    "list",
                    "--porcelain",
                ),
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
            registered = listed.returncode != 0 or any(
                line == f"worktree {source_root}" for line in listed.stdout.splitlines()
            )
            if source_root.exists() or registered:
                raise StaticSourceCleanupError(
                    "static scan immutable source cleanup failed"
                )
        if pending_interrupt is not None:
            raise pending_interrupt


def _write_plan(
    path: Path,
    plan: StaticShardPlan,
    *,
    repository_sha: str,
    registry_fingerprint: str,
    context_ref: str,
) -> None:
    payload = {
        "schema_version": STATIC_PLAN_SCHEMA,
        "execution_class": plan.execution_class,
        "context_ref": context_ref,
        "registry_fingerprint": registry_fingerprint,
        "repository_sha": repository_sha,
        "scan_indices": [spec.index for spec in plan.scans],
    }
    _write_private_json(path, payload)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _launch_worker(
    plan: StaticShardPlan,
    *,
    root: Path,
    run_root: Path,
    worker_ref: str,
    base_env: dict[str, str],
    repository_sha: str,
    registry_fingerprint: str,
) -> _ActiveWorker:
    worker_root = run_root / worker_ref
    worker_root.mkdir(mode=0o700)
    plan_path = worker_root / "plan.json"
    result_path = worker_root / "result.json"
    progress_path = worker_root / "progress.json"
    context = StaticVerificationContext.capture(
        root,
        tuple(spec.scan_ref for spec in plan.scans),
        repository_sha,
        registry_fingerprint,
    )
    _write_plan(
        plan_path,
        plan,
        repository_sha=repository_sha,
        registry_fingerprint=registry_fingerprint,
        context_ref=context.snapshot_ref,
    )
    command = [
        sys.executable,
        "scripts/verification/static_scan_worker.py",
        "--plan",
        str(plan_path),
        "--result",
        str(result_path),
        "--progress",
        str(progress_path),
    ]
    runtime_root = worker_root / "runtime"
    env = shard_processes.isolated_shard_environment(base_env, runtime_root)
    process = shard_processes.spawn_owned_process_group(
        command,
        cwd=root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return _ActiveWorker(
        plan=plan,
        process=process,
        result_path=result_path,
        progress_path=progress_path,
        context_ref=context.snapshot_ref,
        registry_fingerprint=registry_fingerprint,
        repository_sha=repository_sha,
        launched_at=time.perf_counter(),
    )


def _progress_scan_index(worker: _ActiveWorker) -> int | None:
    payload = _read_json(worker.progress_path)
    if payload is None or payload.get("schema_version") != PROGRESS_SCHEMA:
        return None
    index = payload.get("scan_index")
    return index if isinstance(index, int) else None


def _parse_outcomes(worker: _ActiveWorker) -> list[StaticScanOutcome]:
    payload = _read_json(worker.result_path)
    if payload is None or payload.get("schema_version") != RESULT_SCHEMA:
        return []
    if (
        payload.get("context_ref") != worker.context_ref
        or payload.get("registry_fingerprint") != worker.registry_fingerprint
        or payload.get("repository_sha") != worker.repository_sha
    ):
        first = worker.plan.scans[0]
        return [
            StaticScanOutcome(
                first.index,
                first.scan_ref,
                first.name,
                first.function_name,
                "failed",
                0,
                "identity-ref:worker-result-mismatch",
            )
        ]
    raw_outcomes = payload.get("outcomes")
    if not isinstance(raw_outcomes, list):
        return []
    parsed: list[StaticScanOutcome] = []
    for item in raw_outcomes:
        if not isinstance(item, dict):
            continue
        try:
            parsed.append(
                StaticScanOutcome(
                    scan_index=int(item["scan_index"]),
                    scan_ref=str(item["scan_ref"]),
                    name=str(item["name"]),
                    function_name=str(item["function_name"]),
                    status=str(item["status"]),
                    elapsed_ms=int(item["elapsed_ms"]),
                    failure_ref=(
                        str(item["failure_ref"])
                        if item.get("failure_ref") is not None
                        else None
                    ),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return parsed


def _run_batch(
    plans: tuple[StaticShardPlan, ...],
    *,
    root: Path,
    run_root: Path,
    base_env: dict[str, str],
    scan_timeout_seconds: float,
    deadline: float,
    safe_summary: bool,
    batch_ref: str,
    repository_sha: str,
    registry_fingerprint: str,
) -> tuple[list[StaticScanOutcome], bool]:
    active: list[_ActiveWorker] = []
    timed_out = False
    try:
        for index, plan in enumerate(plans):
            if time.perf_counter() >= deadline:
                timed_out = True
                for worker in active:
                    worker.timed_out = True
                break
            active.append(
                _launch_worker(
                    plan,
                    root=root,
                    run_root=run_root,
                    worker_ref=f"{batch_ref}-{index}",
                    base_env=base_env,
                    repository_sha=repository_sha,
                    registry_fingerprint=registry_fingerprint,
                )
            )
    except BaseException:
        shard_processes.stop_processes(
            (worker.process for worker in active),
            DEFAULT_TERMINATION_GRACE_SECONDS,
        )
        raise
    completed: list[_ActiveWorker] = []
    try:
        if timed_out and active:
            shard_processes.stop_processes(
                (worker.process for worker in active),
                DEFAULT_TERMINATION_GRACE_SECONDS,
            )
            completed.extend(active)
            active.clear()
        while active:
            now = time.perf_counter()
            if now >= deadline:
                timed_out = True
                for worker in active:
                    worker.timed_out = True
            for worker in list(active):
                scan_index = _progress_scan_index(worker)
                if scan_index is not None and scan_index != worker.active_scan_index:
                    worker.active_scan_index = scan_index
                    worker.active_scan_observed_at = now
                if (
                    worker.process.poll() is None
                    and now - (worker.active_scan_observed_at or worker.launched_at)
                    >= scan_timeout_seconds
                ):
                    worker.timed_out = True
                    timed_out = True
                if worker.process.poll() is None:
                    continue
                completed.append(worker)
                active.remove(worker)
            if timed_out and active:
                shard_processes.stop_processes(
                    (worker.process for worker in active),
                    DEFAULT_TERMINATION_GRACE_SECONDS,
                )
                for worker in list(active):
                    completed.append(worker)
                    active.remove(worker)
            elif active:
                time.sleep(0.05)
    except BaseException:
        shard_processes.stop_processes(
            (worker.process for worker in active),
            DEFAULT_TERMINATION_GRACE_SECONDS,
        )
        raise

    outcomes: list[StaticScanOutcome] = []
    for worker in completed:
        worker_outcomes = _parse_outcomes(worker)
        outcomes.extend(worker_outcomes)
        if worker.timed_out:
            reported_indices = {outcome.scan_index for outcome in worker_outcomes}
            unreported = tuple(
                spec for spec in worker.plan.scans if spec.index not in reported_indices
            )
            if unreported:
                spec = next(
                    (
                        candidate
                        for candidate in unreported
                        if candidate.index == worker.active_scan_index
                    ),
                    unreported[0],
                )
                outcomes.append(
                    StaticScanOutcome(
                        scan_index=spec.index,
                        scan_ref=spec.scan_ref,
                        name=spec.name,
                        function_name=spec.function_name,
                        status="timed_out",
                        elapsed_ms=round(scan_timeout_seconds * 1000),
                        failure_ref="timeout-ref:static-scan",
                    )
                )
        if (
            worker.process.returncode not in {0, None}
            and not worker.timed_out
            and worker_outcomes
            and all(outcome.status == "passed" for outcome in worker_outcomes)
        ):
            first = worker.plan.scans[0]
            outcomes.append(
                StaticScanOutcome(
                    scan_index=first.index,
                    scan_ref=first.scan_ref,
                    name=first.name,
                    function_name=first.function_name,
                    status="failed",
                    elapsed_ms=0,
                    failure_ref="process-ref:nonzero-exit",
                )
            )
            if not safe_summary:
                print(
                    f"FAIL: static worker {batch_ref} exited nonzero "
                    "(failure-ref:static-worker-process)"
                )
    return outcomes, timed_out


def _complete_outcomes(
    specs: tuple[StaticScanSpec, ...],
    raw_outcomes: Iterable[StaticScanOutcome],
) -> tuple[StaticScanOutcome, ...]:
    expected_indices = {spec.index for spec in specs}
    by_index: dict[int, StaticScanOutcome] = {}
    duplicate_indices: set[int] = set()
    unexpected_result = False
    for outcome in raw_outcomes:
        if outcome.scan_index not in expected_indices:
            unexpected_result = True
            continue
        if outcome.scan_index in by_index:
            duplicate_indices.add(outcome.scan_index)
            continue
        by_index[outcome.scan_index] = outcome
    completed: list[StaticScanOutcome] = []
    for spec in specs:
        outcome = by_index.get(spec.index)
        if spec.index in duplicate_indices:
            outcome = StaticScanOutcome(
                spec.index,
                spec.scan_ref,
                spec.name,
                spec.function_name,
                "failed",
                0,
                "coverage-ref:duplicate-result",
            )
        elif outcome is None:
            outcome = StaticScanOutcome(
                spec.index,
                spec.scan_ref,
                spec.name,
                spec.function_name,
                "not_run",
                0,
                "coverage-ref:missing-result",
            )
        elif (
            outcome.scan_ref != spec.scan_ref
            or outcome.name != spec.name
            or outcome.function_name != spec.function_name
        ):
            outcome = StaticScanOutcome(
                spec.index,
                spec.scan_ref,
                spec.name,
                spec.function_name,
                "failed",
                outcome.elapsed_ms,
                "coverage-ref:result-identity-mismatch",
            )
        if unexpected_result and spec.index == specs[0].index:
            outcome = StaticScanOutcome(
                spec.index,
                spec.scan_ref,
                spec.name,
                spec.function_name,
                "failed",
                outcome.elapsed_ms,
                "coverage-ref:unexpected-result",
            )
        completed.append(outcome)
    return tuple(completed)


def execute_static_scans(
    sequence: Iterable[tuple[str, str]],
    *,
    root: Path = ROOT,
    max_workers: int = DEFAULT_WORKERS,
    cpu_budget: int | str | None = None,
    timings_path: Path | None = None,
    basetemp: Path | None = None,
    scan_timeout_seconds: float = DEFAULT_SCAN_TIMEOUT_SECONDS,
    target_seconds: float = DEFAULT_TARGET_SECONDS,
    hard_timeout_seconds: float = DEFAULT_HARD_TIMEOUT_SECONDS,
    safe_summary: bool = False,
    shuffle_seed: int | None = None,
    serial_reference: bool = False,
    repository_sha: str | None = None,
) -> StaticRunReport:
    if (
        not math.isfinite(scan_timeout_seconds)
        or scan_timeout_seconds <= 0
        or not math.isfinite(target_seconds)
        or target_seconds <= 0
        or not math.isfinite(hard_timeout_seconds)
        or hard_timeout_seconds <= target_seconds
    ):
        raise ValueError(
            "static scan time budgets must be finite, positive, and ordered"
        )
    specs = build_scan_specs(sequence)
    sequence_items = tuple((spec.name, spec.function_name) for spec in specs)
    registry_fingerprint = scan_registry_fingerprint(sequence_items)
    resolved_repository_sha = resolve_repository_sha(root)
    if repository_sha is not None and repository_sha != resolved_repository_sha:
        raise ValueError("static scan repository SHA does not match HEAD")
    budget = resolve_cpu_budget(cpu_budget)
    workers = 1 if serial_reference else capped_worker_count(max_workers, budget)
    timings = load_static_timings(timings_path, specs)
    parallel_plans = (
        (
            StaticShardPlan(
                index=0,
                scans=specs,
                expected_milliseconds=sum(timings.values()),
                execution_class="serial_reference",
            ),
        )
        if serial_reference
        else assign_static_shards(
            specs,
            workers,
            timings,
            shuffle_seed=shuffle_seed,
        )
    )
    serial_plans = () if serial_reference else exclusive_plans(specs)
    all_plans = (*parallel_plans, *serial_plans)
    started = time.perf_counter()
    deadline = started + hard_timeout_seconds
    handled_signals = shard_processes.cancellation_signals()
    run_root: Path | None = None
    remove_run_root = True

    def interrupt_run(signum: int, _frame: Any) -> None:
        shard_processes.ignore_signals(handled_signals)
        raise StaticRunInterrupted(signum)

    with shard_processes.installed_signal_handlers(
        handled_signals,
        interrupt_run,
    ):
        try:
            run_root = _safe_run_root(basetemp)
            with _immutable_source_tree(
                root,
                run_root,
                resolved_repository_sha,
                deadline=deadline,
            ) as source_root:
                base_env = shard_processes.build_shard_env(source_root)
                if time.perf_counter() >= deadline:
                    raise subprocess.TimeoutExpired(
                        "static scan immutable setup",
                        timeout=hard_timeout_seconds,
                    )
                raw_outcomes, timed_out = _run_batch(
                    parallel_plans,
                    root=source_root,
                    run_root=run_root,
                    base_env=base_env,
                    scan_timeout_seconds=scan_timeout_seconds,
                    deadline=deadline,
                    safe_summary=safe_summary,
                    batch_ref="parallel",
                    repository_sha=resolved_repository_sha,
                    registry_fingerprint=registry_fingerprint,
                )
                if not timed_out:
                    for index, plan in enumerate(serial_plans):
                        batch_outcomes, batch_timed_out = _run_batch(
                            (plan,),
                            root=source_root,
                            run_root=run_root,
                            base_env=base_env,
                            scan_timeout_seconds=scan_timeout_seconds,
                            deadline=deadline,
                            safe_summary=safe_summary,
                            batch_ref=f"exclusive-{index}",
                            repository_sha=resolved_repository_sha,
                            registry_fingerprint=registry_fingerprint,
                        )
                        raw_outcomes.extend(batch_outcomes)
                        timed_out = timed_out or batch_timed_out
                        if timed_out:
                            break
        except StaticSourceCleanupError:
            remove_run_root = False
            raise
        finally:
            if run_root is not None and remove_run_root:
                _remove_run_root(run_root)
    if resolve_repository_sha(root) != resolved_repository_sha:
        raise ValueError("static scan repository identity changed during execution")
    outcomes = _complete_outcomes(specs, raw_outcomes)
    elapsed = time.perf_counter() - started
    passed = not timed_out and all(outcome.status == "passed" for outcome in outcomes)
    report = StaticRunReport(
        passed=passed,
        outcomes=outcomes,
        plan_ref=plan_fingerprint(
            all_plans,
            repository_sha=resolved_repository_sha,
            registry_fingerprint=registry_fingerprint,
        ),
        registry_fingerprint=registry_fingerprint,
        repository_sha=resolved_repository_sha,
        worker_count=max(
            len(parallel_plans),
            1 if serial_plans else 0,
        ),
        total_elapsed_seconds=elapsed,
        timed_out=timed_out,
    )
    print("\n=== Static Scan Scheduler Summary ===")
    print(f"scans: {len(specs)}")
    print(f"workers: {report.worker_count} (global CPU budget: {budget})")
    print(f"repository_sha: {report.repository_sha}")
    print(f"registry: {report.registry_fingerprint}")
    print(f"plan: {report.plan_ref}")
    print(f"elapsed_seconds: {elapsed:.2f}")
    if elapsed > target_seconds:
        print(
            "PERFORMANCE WARNING: static scan target exceeded: "
            f"elapsed_seconds={elapsed:.2f} target_seconds={target_seconds:.2f}"
        )
    for outcome in outcomes:
        if outcome.status != "passed":
            print(
                f"FAIL: {outcome.scan_ref} status={outcome.status} "
                f"failure_ref={outcome.failure_ref or 'failure-ref:unknown'}"
            )
    if passed:
        print("Static scan scheduler PASSED.")
    return report


def _write_report(path: Path, report: StaticRunReport) -> None:
    payload = {
        "schema_version": RUN_REPORT_SCHEMA,
        "passed": report.passed,
        "plan_ref": report.plan_ref,
        "registry_fingerprint": report.registry_fingerprint,
        "repository_sha": report.repository_sha,
        "worker_count": report.worker_count,
        "total_elapsed_seconds": round(report.total_elapsed_seconds, 3),
        "timed_out": report.timed_out,
        "outcomes": [
            {
                "scan_ref": outcome.scan_ref,
                "status": outcome.status,
                "elapsed_ms": outcome.elapsed_ms,
                "failure_ref": outcome.failure_ref,
            }
            for outcome in report.outcomes
        ],
    }
    _write_private_json(path, payload)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run timing-aware process-isolated static verification shards."
    )
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--cpu-budget")
    parser.add_argument("--timings-json")
    parser.add_argument("--write-report")
    parser.add_argument("--basetemp")
    parser.add_argument("--repository-sha")
    parser.add_argument(
        "--scan-timeout-seconds", type=float, default=DEFAULT_SCAN_TIMEOUT_SECONDS
    )
    parser.add_argument("--target-seconds", type=float, default=DEFAULT_TARGET_SECONDS)
    parser.add_argument(
        "--hard-timeout-seconds", type=float, default=DEFAULT_HARD_TIMEOUT_SECONDS
    )
    parser.add_argument("--safe-summary", action="store_true")
    parser.add_argument("--equivalence", action="store_true")
    parser.add_argument("--repeat", type=int, default=1)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.repeat <= 0 or args.repeat > 20:
        print("FAIL: --repeat must be between 1 and 20", file=sys.stderr)
        return 2
    from scripts.verification.run_all_legacy import SCAN_SEQUENCE

    common = {
        "root": ROOT,
        "max_workers": args.workers,
        "cpu_budget": args.cpu_budget,
        "timings_path": Path(args.timings_json) if args.timings_json else None,
        "basetemp": Path(args.basetemp) if args.basetemp else None,
        "repository_sha": args.repository_sha,
        "scan_timeout_seconds": args.scan_timeout_seconds,
        "target_seconds": args.target_seconds,
        "hard_timeout_seconds": args.hard_timeout_seconds,
        "safe_summary": args.safe_summary,
    }
    try:
        reference = (
            execute_static_scans(SCAN_SEQUENCE, serial_reference=True, **common)
            if args.equivalence
            else None
        )
        reports = [
            execute_static_scans(
                SCAN_SEQUENCE,
                shuffle_seed=index if args.equivalence else None,
                **common,
            )
            for index in range(args.repeat)
        ]
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        if not args.safe_summary:
            raise
        print(
            f"FAIL: static scheduler stopped safely (failure-ref:{type(exc).__name__})",
            file=sys.stderr,
        )
        return 1
    if args.equivalence:
        assert reference is not None
        expected = tuple((item.scan_ref, item.status) for item in reference.outcomes)
        if any(
            tuple((item.scan_ref, item.status) for item in report.outcomes) != expected
            for report in reports
        ):
            print("FAIL: static scan repeated-order equivalence drift")
            return 1
    if args.write_report:
        _write_report(Path(args.write_report), reports[-1])
    return (
        0
        if (reference is None or reference.passed)
        and all(report.passed for report in reports)
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
