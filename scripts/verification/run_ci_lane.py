#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    GITHUB_FULL_SUITE_LOCK_WAIT_SECONDS,
    PLAYWRIGHT_BROWSER_DIRNAME,
    PROFILE_REF,
    CommandSpec,
    build_plan,
    command_registry,
    lane_registry,
)
from scripts.verification.ci_fallback_storage import (  # noqa: E402
    FullSuiteLock,
    FullSuiteLockUnavailableError,
)
from scripts.verification.pytest_shard_processes import (  # noqa: E402
    build_shard_env,
    cancellation_signals,
    installed_signal_handlers,
    stop_processes,
)


TERMINATION_GRACE_SECONDS = 10.0
MAX_TRANSIENT_OUTPUT_BYTES = 32 * 1024 * 1024
MAX_RECEIPT_BYTES = 1024 * 1024
MAX_PYTEST_PERFORMANCE_REPORT_BYTES = 256 * 1024
PYTEST_PERFORMANCE_REPORT_NAME = "uaa_pytest_performance_report.json"
PYTEST_PERFORMANCE_SCHEMA_VERSION = "uaa_pytest_performance_report.v1"
PYTEST_PLAN_REF_RE = re.compile(r"^pytest-shard-plan-ref:sha256:[0-9a-f]{64}$")
PYTEST_RUNTIME_UNAVAILABLE_REASON_REF = "reason-ref:ci:pytest-runtime-unavailable"
FULL_SUITE_LOCK_UNAVAILABLE_REASON_REF = (
    "reason-ref:ci:full-suite-capacity-unavailable"
)


class PytestRuntimeUnavailableError(RuntimeError):
    """Raised before a full-suite attempt when pytest cannot be imported."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _git_head(repo: Path) -> str:
    completed = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return completed.stdout.strip()


def _safe_temp_root(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("CI temp root must be a real directory")
    return path.resolve()


def _resolved_argv(
    command: CommandSpec,
    temp_root: Path,
    repository_sha: str,
) -> tuple[str, ...]:
    return tuple(
        token.replace("{temp_root}", str(temp_root)).replace(
            "{repository_sha}", repository_sha
        )
        for token in command.argv
    )


def _safe_env(command: CommandSpec, temp_root: Path) -> dict[str, str]:
    env = build_shard_env(ROOT)
    isolated_home = temp_root / "runtime-home"
    isolated_tmp = temp_root / "runtime-tmp"
    playwright_browsers = temp_root / PLAYWRIGHT_BROWSER_DIRNAME
    isolated_home.mkdir(parents=True, exist_ok=True)
    isolated_tmp.mkdir(parents=True, exist_ok=True)
    playwright_browsers.mkdir(parents=True, exist_ok=True)
    env.update(
        {
            "CI": "true",
            "HOME": str(isolated_home),
            "TEMP": str(isolated_tmp),
            "TMP": str(isolated_tmp),
            "TMPDIR": str(isolated_tmp),
            "PLAYWRIGHT_BROWSERS_PATH": str(playwright_browsers),
        }
    )
    env.update(dict(command.env))
    return env


def _result_ref(
    command_ref: str,
    repository_sha: str,
    returncode: int,
    output_digest: str,
    duration_ms: int,
) -> str:
    payload = "|".join(
        (command_ref, repository_sha, str(returncode), output_digest, str(duration_ms))
    )
    return f"result-ref:ci:{hashlib.sha256(payload.encode()).hexdigest()}"


def _pytest_shard_evidence(temp_root: Path) -> dict[str, Any]:
    path = temp_root / PYTEST_PERFORMANCE_REPORT_NAME
    try:
        path_info = path.lstat()
    except FileNotFoundError:
        return {
            "pytest_shard_evidence_status": "unavailable",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-unavailable"
            ),
        }
    if not stat.S_ISREG(path_info.st_mode):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-unsafe"
            ),
        }
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-unsafe"
            ),
        }
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.getuid()
            or info.st_mode & 0o022
            or info.st_size <= 0
            or info.st_size > MAX_PYTEST_PERFORMANCE_REPORT_BYTES
        ):
            raise ValueError("unsafe pytest performance report")
        encoded = os.read(descriptor, MAX_PYTEST_PERFORMANCE_REPORT_BYTES + 1)
    except (OSError, ValueError):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-unsafe"
            ),
        }
    finally:
        os.close(descriptor)
    try:
        payload = json.loads(encoded)
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = None
    if not isinstance(payload, dict):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-invalid"
            ),
        }
    plan_ref = payload.get("plan_fingerprint_ref")
    rows = payload.get("shards")
    if (
        payload.get("schema_version") != PYTEST_PERFORMANCE_SCHEMA_VERSION
        or not isinstance(plan_ref, str)
        or PYTEST_PLAN_REF_RE.fullmatch(plan_ref) is None
        or not isinstance(rows, list)
        or len(rows) != 8
    ):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-invalid"
            ),
        }
    normalized: list[tuple[int, int, bool]] = []
    for row in rows:
        if not isinstance(row, dict):
            break
        shard_index = row.get("shard_index")
        return_code = row.get("return_code")
        timed_out = row.get("timed_out")
        if (
            not isinstance(shard_index, int)
            or isinstance(shard_index, bool)
            or not isinstance(return_code, int)
            or isinstance(return_code, bool)
            or not isinstance(timed_out, bool)
        ):
            break
        normalized.append((shard_index, return_code, timed_out))
    if len(normalized) != 8 or sorted(index for index, _, _ in normalized) != list(range(8)):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-invalid"
            ),
        }
    failed_refs = tuple(
        f"pytest-shard-ref:{index}:{'timed-out' if timed_out else 'failed'}"
        for index, return_code, timed_out in sorted(normalized)
        if timed_out or return_code != 0
    )
    return {
        "pytest_shard_evidence_status": "available",
        "pytest_shard_plan_fingerprint_ref": plan_ref,
        "pytest_shard_count": 8,
        "failed_shard_count": len(failed_refs),
        "failed_shard_refs": failed_refs,
    }


def _run_command(
    command: CommandSpec,
    *,
    repository_sha: str,
    temp_root: Path,
    validate_start: Callable[[], None] | None = None,
    before_start: Callable[[], None] | None = None,
) -> dict[str, Any]:
    started_at = _utc_now()
    started = time.perf_counter()
    output_path: Path | None = None
    process: subprocess.Popen[bytes] | None = None
    timed_out = False
    interrupted = False

    def handle_signal(signum: int, _frame: object) -> None:
        nonlocal interrupted
        interrupted = True
        if process is not None:
            stop_processes((process,), TERMINATION_GRACE_SECONDS)
        raise KeyboardInterrupt(f"CI lane interrupted by signal {signum}")

    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix="uaa-ci-transient-",
            dir=temp_root,
            delete=False,
        ) as output:
            output_path = Path(output.name)
            with installed_signal_handlers(cancellation_signals(), handle_signal):
                if validate_start is not None:
                    validate_start()
                if before_start is not None:
                    before_start()
                process = subprocess.Popen(
                    _resolved_argv(command, temp_root, repository_sha),
                    cwd=ROOT,
                    env=_safe_env(command, temp_root),
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    start_new_session=os.name == "posix",
                )
                deadline = time.monotonic() + command.timeout_seconds
                returncode: int | None = None
                while returncode is None:
                    returncode = process.poll()
                    output.flush()
                    if output.tell() > MAX_TRANSIENT_OUTPUT_BYTES:
                        stop_processes((process,), TERMINATION_GRACE_SECONDS)
                        returncode = 125
                        break
                    if time.monotonic() >= deadline:
                        timed_out = True
                        stop_processes((process,), TERMINATION_GRACE_SECONDS)
                        returncode = 124
                        break
                    time.sleep(0.05)
            output.flush()
            output.seek(0, os.SEEK_END)
            output_bytes = output.tell()
            if output_bytes > MAX_TRANSIENT_OUTPUT_BYTES:
                returncode = 125
            output.seek(0)
            digest = hashlib.sha256()
            while chunk := output.read(1024 * 1024):
                digest.update(chunk)
            output_digest = digest.hexdigest()
    except KeyboardInterrupt:
        returncode = 130
        output_bytes = 0
        output_digest = hashlib.sha256(b"").hexdigest()
    finally:
        if process is not None and process.poll() is None:
            stop_processes((process,), TERMINATION_GRACE_SECONDS)
        if output_path is not None:
            output_path.unlink(missing_ok=True)

    duration_ms = max(0, int((time.perf_counter() - started) * 1000))
    status_value = "pass" if returncode == 0 else "fail"
    if timed_out:
        status_value = "timed_out"
    elif interrupted:
        status_value = "cancelled"
    return {
        "command_ref": command.command_ref,
        "category": command.category,
        "status": status_value,
        "started_at": started_at,
        "completed_at": _utc_now(),
        "duration_ms": duration_ms,
        "output_byte_count": output_bytes,
        "output_digest": output_digest,
        "result_ref": _result_ref(
            command.command_ref,
            repository_sha,
            returncode,
            output_digest,
            duration_ms,
        ),
        "redaction_status": "content_free_output_metadata_only",
    }


def _append_summary(path: Path | None, lines: list[str]) -> None:
    if path is None:
        return
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise ValueError("CI summary target must be a regular non-symlink file")
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.getuid()
            or info.st_mode & 0o022
        ):
            raise ValueError("CI summary target must remain regular")
        os.write(descriptor, ("\n".join(lines) + "\n").encode())
    finally:
        os.close(descriptor)


def _write_receipt(path: Path | None, receipt: dict[str, Any], temp_root: Path) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise ValueError("CI receipt target must remain inside the temp root")
    parent = path.parent.resolve()
    if not parent.is_dir() or not parent.is_relative_to(temp_root):
        raise ValueError("CI receipt target must remain inside the temp root")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
        ):
            raise ValueError("CI receipt target is unsafe")
        encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        if len(encoded) > MAX_RECEIPT_BYTES:
            raise ValueError("CI receipt exceeds its byte bound")
        os.write(descriptor, encoded)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run_lane(
    lane_ref: str,
    *,
    repository_sha: str,
    temp_root: Path,
    visual_scope: str = "unknown_fail_closed",
    docker_available: str = "unknown_fail_closed",
    summary_file: Path | None = None,
    receipt_file: Path | None = None,
    full_suite_lock_mode: str = "github",
) -> dict[str, Any]:
    if _git_head(ROOT) != repository_sha:
        raise ValueError("CI lane SHA does not match the checked-out repository")
    lanes = lane_registry()
    if lane_ref not in lanes:
        raise ValueError("unknown canonical CI lane ref")
    lane = lanes[lane_ref]
    temp_root = _safe_temp_root(temp_root)
    plan = build_plan(
        ROOT,
        repository_sha,
        lane_refs=(lane_ref,),
        frontend_visual_scope=visual_scope,
    )
    commands = command_registry()
    if lane_ref == "ci-pytest-shards" and importlib.util.find_spec("pytest") is None:
        raise PytestRuntimeUnavailableError(
            "canonical pytest runtime is unavailable before suite start"
        )
    started_at = _utc_now()
    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    if full_suite_lock_mode not in {"github", "private"}:
        raise ValueError("unknown full-suite lock mode")
    lock = (
        FullSuiteLock(
            wait_seconds=(
                GITHUB_FULL_SUITE_LOCK_WAIT_SECONDS
                if full_suite_lock_mode == "github"
                else 0
            ),
            repository_sha=repository_sha,
            attempt_scope=full_suite_lock_mode,
        )
        if lane_ref == "ci-pytest-shards"
        else nullcontext()
    )
    with lock as full_suite_lock:
        for command_ref in lane.command_refs:
            if command_ref in lane.satisfied_command_refs:
                results.append(
                    {
                        "command_ref": command_ref,
                        "category": commands[command_ref].category,
                        "status": "satisfied_by_required_dependency",
                        "duration_ms": 0,
                        "result_ref": f"result-ref:ci:{hashlib.sha256((repository_sha + command_ref + lane_ref).encode()).hexdigest()}",
                        "redaction_status": "content_free_output_metadata_only",
                    }
                )
                continue
            skip_reason: str | None = None
            if command_ref == "command:frontend.visual-regression" and visual_scope == "not_affected":
                skip_reason = "reason-ref:visual-regression:not-affected"
            if command_ref == "command:desktop-packaging.proof" and docker_available == "unavailable":
                skip_reason = "reason-ref:self-hosted-runner-docker-unavailable"
            if skip_reason is not None:
                results.append(
                    {
                        "command_ref": command_ref,
                        "category": commands[command_ref].category,
                        "status": "not_applicable" if "not-affected" in skip_reason else "skipped",
                        "duration_ms": 0,
                        "reason_ref": skip_reason,
                        "result_ref": f"result-ref:ci:{hashlib.sha256((repository_sha + command_ref + skip_reason).encode()).hexdigest()}",
                        "redaction_status": "content_free_output_metadata_only",
                    }
                )
                continue
            result = _run_command(
                commands[command_ref],
                repository_sha=repository_sha,
                temp_root=temp_root,
                validate_start=(
                    full_suite_lock.ensure_start_available
                    if lane_ref == "ci-pytest-shards"
                    else None
                ),
                before_start=(
                    full_suite_lock.record_start
                    if lane_ref == "ci-pytest-shards"
                    else None
                ),
            )
            if lane_ref == "ci-pytest-shards":
                result.update(_pytest_shard_evidence(temp_root))
            results.append(result)
            if result["status"] != "pass":
                break

    terminal_ok = all(
        result["status"]
        in {"pass", "skipped", "not_applicable", "satisfied_by_required_dependency"}
        for result in results
    ) and len(results) == len(lane.command_refs)
    receipt = {
        "schema_version": "uaa_ci_lane_receipt.v1",
        "profile_ref": PROFILE_REF,
        "repository_sha": repository_sha,
        "lane_ref": lane_ref,
        "plan": asdict(plan),
        "started_at": started_at,
        "completed_at": _utc_now(),
        "duration_ms": max(0, int((time.perf_counter() - started) * 1000)),
        "status": "pass" if terminal_ok else "fail",
        "command_results": results,
        "github_gate_satisfied": False,
        "merge_gate_satisfied": False,
        "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
    }
    receipt["receipt_ref"] = (
        "receipt-ref:ci-lane:"
        + hashlib.sha256(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    summary = [
        f"## {lane.name}",
        "",
        f"- Lane ref: {lane_ref}",
        f"- Manifest version: {plan.schema_version}",
        f"- Manifest fingerprint: {plan.definition_fingerprint}",
        "- Report mode: safe-summary-only",
        "- Raw command output: transient and not persisted or uploaded",
    ]
    summary.extend(
        f"- {result['command_ref']}: {result['status']}" for result in results
    )
    for result in results:
        if result.get("pytest_shard_evidence_status") is None:
            continue
        summary.append(
            "- Pytest shard evidence: "
            + str(result["pytest_shard_evidence_status"])
        )
        for failed_ref in result.get("failed_shard_refs", ()):
            shard_index = failed_ref.split(":", maxsplit=2)[1]
            summary.append(
                f"- Failed shard: {failed_ref} "
                f"(reproduce with make ci-reproduce-shard CI_SHARD_INDEX={shard_index})"
            )
    _append_summary(summary_file, summary)
    _write_receipt(receipt_file, receipt, temp_root)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one canonical UAA CI lane.")
    parser.add_argument("--lane", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--profile", default=PROFILE_REF)
    parser.add_argument("--temp-root", required=True)
    parser.add_argument(
        "--visual-scope",
        choices=("affected", "not_affected", "unknown_fail_closed"),
        default="unknown_fail_closed",
    )
    parser.add_argument(
        "--docker-available",
        choices=("available", "unavailable", "unknown_fail_closed"),
        default="unknown_fail_closed",
    )
    parser.add_argument("--summary-file")
    parser.add_argument("--receipt-file")
    parser.add_argument(
        "--full-suite-lock-mode",
        choices=("github", "private"),
        default="github",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.profile != PROFILE_REF:
        parser.error("unknown CI profile")
    try:
        receipt = run_lane(
            args.lane,
            repository_sha=args.sha,
            temp_root=Path(args.temp_root),
            visual_scope=args.visual_scope,
            docker_available=args.docker_available,
            summary_file=Path(args.summary_file) if args.summary_file else None,
            receipt_file=Path(args.receipt_file) if args.receipt_file else None,
            full_suite_lock_mode=args.full_suite_lock_mode,
        )
    except PytestRuntimeUnavailableError:
        print(
            "UAA CI lane blocked: " + PYTEST_RUNTIME_UNAVAILABLE_REASON_REF,
            file=sys.stderr,
        )
        return 1
    except FullSuiteLockUnavailableError:
        print(
            "UAA CI lane blocked: " + FULL_SUITE_LOCK_UNAVAILABLE_REASON_REF,
            file=sys.stderr,
        )
        return 1
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        print(f"UAA CI lane: {receipt['lane_ref']}")
        print(f"Status: {receipt['status']}")
        print(f"Exact SHA: {receipt['repository_sha']}")
        print(f"Manifest: {receipt['plan']['definition_fingerprint']}")
        for result in receipt["command_results"]:
            print(f"- {result['command_ref']}: {result['status']}")
        print("GitHub merge gate satisfied: no")
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
