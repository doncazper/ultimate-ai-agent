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
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import (  # noqa: E402
    DECLARED_RUNNER_PROFILE_ENV,
    DECLARED_RUNNER_PROFILE_PATTERN,
    GITHUB_FULL_SUITE_LOCK_WAIT_SECONDS,
    CI_JOB_GRAPH,
    VERIFICATION_DAG,
    PLAYWRIGHT_BROWSER_DIRNAME,
    PROFILE_REF,
    CommandSpec,
    build_plan,
    command_registry,
    lane_registry,
    observed_platform_fingerprint,
    optional_nonexecution_reason_ref,
    optional_nonexecution_result_ref,
)
from scripts.verification.pytest_collection_evidence import (  # noqa: E402
    CollectionEvidenceError,
    collection_evidence_reason_ref,
    load_aggregate_evidence,
)
from scripts.verification.pytest_shard_plan import (  # noqa: E402
    CANONICAL_PYTEST_SHARD_COUNT,
)
from scripts.verification.pytest_shard_artifacts import (  # noqa: E402
    MAX_FAILED_TEST_REFS_PER_SHARD,
    is_safe_test_ref,
)
from scripts.verification.ci_fallback_storage import (  # noqa: E402
    FullSuiteAttemptAlreadyRecordedError,
    FullSuiteLock,
    FullSuiteLockUnavailableError,
)
from scripts.verification.frontend_collection_evidence import (  # noqa: E402
    FrontendCollectionEvidenceError,
    consume_frontend_collection_evidence,
)
from scripts.verification.pytest_shard_processes import (  # noqa: E402
    build_shard_env,
    cancellation_signals,
    installed_signal_handlers,
    process_group_leader_is_terminal_without_reaping,
    spawn_owned_process_group,
    stop_processes,
)
from scripts.verification.run_pytest_shards import (  # noqa: E402
    MatrixLoopbackTestResourceUnavailableError,
    assert_matrix_loopback_test_resource_available,
    current_shard_plan_fingerprint,
)
from scripts.verification.typescript_binding import (  # noqa: E402
    build_declared_typescript_binding,
    resolve_typescript_runtime_binding,
)
from scripts.verification.verification_contracts import (  # noqa: E402
    TEST_EXECUTION_COMMAND_REFS,
    VerificationReceipt,
    VerificationRunManifest,
    VerificationTerminalStatus,
    VerificationUnitKind,
    dependency_lock_set_fingerprint,
    dependency_state_fingerprint,
    verification_receipt_fingerprint,
    verification_receipt_payload,
    verification_run_manifest_fingerprint,
    verification_run_manifest_payload,
)
from scripts.verification.verification_execution_identity import (  # noqa: E402
    VerificationExecutionFence,
    VerificationExecutionFenceDisposition,
    VerificationExecutionFenceError,
    build_verification_execution_identity,
    build_verification_execution_terminal_proof,
    verification_exclusive_resource_attempt_fingerprint,
)
from scripts.verification.verification_environment_preflight import (  # noqa: E402
    VerificationEnvironmentPreflightError,
    validate_lane_environment,
)
from scripts.verification.verification_github_transport import (  # noqa: E402
    build_github_job_output_envelope,
    decode_github_job_output,
    encode_github_job_output,
    validate_github_job_output_against_plan,
)
from scripts.verification.verification_github_prerequisites import (  # noqa: E402
    append_github_output,
)
from scripts.verification.verification_run_aggregator import (  # noqa: E402
    aggregate_verification_run,
    validate_receipt_for_plan_unit,
)
from scripts.verification.verification_receipt_store import (  # noqa: E402
    VerificationReceiptStore,
)


TERMINATION_GRACE_SECONDS = 10.0
MAX_TRANSIENT_OUTPUT_BYTES = 32 * 1024 * 1024
MAX_RECEIPT_BYTES = 1024 * 1024
MAX_PYTEST_PERFORMANCE_REPORT_BYTES = 256 * 1024
PYTEST_PERFORMANCE_REPORT_NAME = "uaa_pytest_performance_report.json"
PYTEST_FILE_TIMINGS_NAME = "uaa_pytest_file_timings.json"
PYTEST_COLLECTION_EVIDENCE_NAME = "uaa_pytest_collection_evidence.json"
FRONTEND_COLLECTION_EVIDENCE_DIRNAME = "uaa_frontend_collection_evidence"
FRONTEND_COLLECTION_EVIDENCE_NAME = "aggregate.json"
PYTEST_PERFORMANCE_SCHEMA_VERSION = "uaa_pytest_performance_report.v1"
PYTEST_PLAN_REF_RE = re.compile(r"^pytest-shard-plan-ref:sha256:[0-9a-f]{64}$")
PYTEST_REPRODUCTION_LANE_RE = re.compile(
    rf"^ci-pytest-shard-[0-{CANONICAL_PYTEST_SHARD_COUNT - 1}]-reproduce$"
)
PYTEST_DIAGNOSTIC_LOCK_PATH = Path("/tmp/uaa-ci-pytest-diagnostic.lock")
PYTEST_RUNTIME_UNAVAILABLE_REASON_REF = "reason-ref:ci:pytest-runtime-unavailable"
PYTEST_LOOPBACK_RESOURCE_UNAVAILABLE_REASON_REF = (
    "reason-ref:ci:pytest-loopback-resource-unavailable"
)
FULL_SUITE_LOCK_UNAVAILABLE_REASON_REF = "reason-ref:ci:full-suite-capacity-unavailable"
FULL_SUITE_ATTEMPT_RECORDED_REASON_REF = "reason-ref:ci:full-suite-attempt-recorded"
VERIFICATION_EXECUTION_FENCE_REASON_REF = (
    "reason-ref:ci:verification-execution-fence-blocked"
)
PRIVATE_NON_DIAGNOSTIC_REASON_REF = (
    "reason-ref:ci:private-nondiagnostic-execution-denied"
)
CI_LANE_EXECUTION_ERROR_REASON_REF = "reason-ref:ci:lane-execution-failed"
GITHUB_OUTPUT_KEY = "verification_envelope"
TYPED_EVIDENCE_REDACTION_STATUS = "content_free_refs_hashes_counts_and_durations_only"


class PytestRuntimeUnavailableError(RuntimeError):
    """Raised before a full-suite attempt when pytest cannot be imported."""


class PrivateNonDiagnosticExecutionError(RuntimeError):
    """Raised when private CI tries to execute a non-diagnostic canonical lane."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _wall_duration_ms(started_at: str, completed_at: str) -> int:
    """Bind receipt duration to the same suspend-aware clock as its timestamps."""

    started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    duration_ms = int((completed - started).total_seconds() * 1_000)
    if duration_ms < 0:
        raise ValueError("verification receipt completion precedes its start")
    return duration_ms


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
    base_sha: str,
) -> tuple[str, ...]:
    resolved = tuple(
        token.replace("{temp_root}", str(temp_root))
        .replace("{repository_sha}", repository_sha)
        .replace("{base_sha}", base_sha)
        for token in command.argv
    )
    if resolved and resolved[0] == ".venv/bin/python":
        return (sys.executable, *resolved[1:])
    return resolved


def _safe_env(
    command: CommandSpec,
    temp_root: Path,
    base_sha: str | None = None,
    visual_scope: str | None = None,
) -> dict[str, str]:
    env = build_shard_env(ROOT)
    isolated_home = temp_root / "runtime-home"
    isolated_tmp = temp_root / "runtime-tmp"
    playwright_browsers = temp_root / PLAYWRIGHT_BROWSER_DIRNAME
    frontend_evidence_directory = temp_root / FRONTEND_COLLECTION_EVIDENCE_DIRNAME
    isolated_home.mkdir(parents=True, exist_ok=True)
    isolated_tmp.mkdir(parents=True, exist_ok=True)
    playwright_browsers.mkdir(parents=True, exist_ok=True)
    frontend_evidence_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    frontend_evidence_directory.chmod(0o700)
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
    if base_sha is not None:
        env["UAA_VERIFICATION_BASE_SHA"] = base_sha
    if visual_scope is not None:
        env["UAA_VERIFICATION_VISUAL_SCOPE"] = visual_scope
    if any(key == DECLARED_RUNNER_PROFILE_ENV for key, _value in command.env):
        raise ValueError("command environment cannot override declared runner profile")
    declared_runner_profile = os.environ.get(DECLARED_RUNNER_PROFILE_ENV)
    if declared_runner_profile is not None:
        if DECLARED_RUNNER_PROFILE_PATTERN.fullmatch(declared_runner_profile) is None:
            raise ValueError("declared runner profile is invalid")
        env[DECLARED_RUNNER_PROFILE_ENV] = declared_runner_profile
    if command.command_ref in {
        "command:frontend.check",
        "command:frontend.visual-regression",
    }:
        env["UAA_FRONTEND_COLLECTION_EVIDENCE_PATH"] = str(
            frontend_evidence_directory / FRONTEND_COLLECTION_EVIDENCE_NAME
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


def _transient_output_metadata(path: Path) -> tuple[int, str]:
    """Read exact metadata from the internally-created transient output file."""

    metadata = path.lstat()
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != os.getuid()
    ):
        raise RuntimeError("CI transient output boundary is unsafe")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if (
            opened.st_dev != metadata.st_dev
            or opened.st_ino != metadata.st_ino
            or opened.st_mode != metadata.st_mode
            or opened.st_nlink != metadata.st_nlink
            or opened.st_uid != metadata.st_uid
        ):
            raise RuntimeError("CI transient output changed before hashing")
        return _transient_output_metadata_from_descriptor(descriptor)
    finally:
        os.close(descriptor)


def _transient_output_metadata_from_descriptor(
    descriptor: int,
) -> tuple[int, str]:
    """Hash the exact internally-created transient output inode."""

    opened = os.fstat(descriptor)
    if (
        not stat.S_ISREG(opened.st_mode)
        or opened.st_nlink != 1
        or opened.st_uid != os.getuid()
    ):
        raise RuntimeError("CI transient output boundary is unsafe")
    if opened.st_size > MAX_TRANSIENT_OUTPUT_BYTES:
        raise RuntimeError("CI transient output exceeds the bounded byte limit")
    os.lseek(descriptor, 0, os.SEEK_SET)
    output_bytes = 0
    digest = hashlib.sha256()
    while output_bytes < opened.st_size:
        remaining_bytes = min(
            opened.st_size - output_bytes,
            MAX_TRANSIENT_OUTPUT_BYTES - output_bytes,
        )
        chunk = os.read(descriptor, min(1024 * 1024, remaining_bytes))
        if not chunk:
            break
        output_bytes += len(chunk)
        digest.update(chunk)
    final = os.fstat(descriptor)
    if (
        final.st_dev != opened.st_dev
        or final.st_ino != opened.st_ino
        or final.st_mode != opened.st_mode
        or final.st_nlink != opened.st_nlink
        or final.st_uid != opened.st_uid
        or final.st_size != opened.st_size
        or output_bytes != opened.st_size
    ):
        raise RuntimeError("CI transient output changed while hashing")
    return output_bytes, digest.hexdigest()


def _cleanup_transient_output_inode(
    descriptor: int,
    *,
    temp_root: Path,
) -> None:
    """Erase the bound output inode without acting on a mutable pathname."""

    del temp_root
    os.ftruncate(descriptor, 0)
    os.fsync(descriptor)
    bound = os.fstat(descriptor)
    if (
        not stat.S_ISREG(bound.st_mode)
        or bound.st_uid != os.getuid()
        or bound.st_size != 0
    ):
        raise RuntimeError("CI transient output cleanup is unproven")


def expected_pytest_shard_plan_ref() -> str:
    return current_shard_plan_fingerprint(
        ROOT,
        CANONICAL_PYTEST_SHARD_COUNT,
        ROOT / "scripts/verification/pytest_file_timing_seed.json",
    )


def _assert_pytest_report_absent(temp_root: Path) -> None:
    path = temp_root / PYTEST_PERFORMANCE_REPORT_NAME
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError("pytest performance report must not predate the current attempt")


def _pytest_shard_evidence(
    temp_root: Path,
    *,
    expected_plan_ref: str,
    command_status: str,
) -> dict[str, Any]:
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
    run_status = payload.get("run_status")
    rows = payload.get("shards")
    if (
        payload.get("schema_version") != PYTEST_PERFORMANCE_SCHEMA_VERSION
        or not isinstance(plan_ref, str)
        or PYTEST_PLAN_REF_RE.fullmatch(plan_ref) is None
        or plan_ref != expected_plan_ref
        or run_status not in {"green", "failed", "timeout"}
        or not isinstance(rows, list)
        or len(rows) != CANONICAL_PYTEST_SHARD_COUNT
    ):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-invalid"
            ),
        }
    normalized: list[tuple[int, int, bool, tuple[str, ...]]] = []
    for row in rows:
        if not isinstance(row, dict):
            break
        shard_index = row.get("shard_index")
        return_code = row.get("return_code")
        timed_out = row.get("timed_out")
        raw_failed_test_refs = row.get("failed_test_refs", [])
        if (
            not isinstance(shard_index, int)
            or isinstance(shard_index, bool)
            or not isinstance(return_code, int)
            or isinstance(return_code, bool)
            or not -255 <= return_code <= 255
            or not isinstance(timed_out, bool)
            or not isinstance(raw_failed_test_refs, list)
            or len(raw_failed_test_refs) > MAX_FAILED_TEST_REFS_PER_SHARD
            or any(not is_safe_test_ref(ref) for ref in raw_failed_test_refs)
            or len(raw_failed_test_refs) != len(set(raw_failed_test_refs))
            or (return_code == 0 and raw_failed_test_refs)
            or (timed_out and return_code == 0)
        ):
            break
        normalized.append(
            (shard_index, return_code, timed_out, tuple(raw_failed_test_refs))
        )
    shard_indices = sorted(index for index, _, _, _ in normalized)
    if (
        len(normalized) != CANONICAL_PYTEST_SHARD_COUNT
        or shard_indices != list(range(CANONICAL_PYTEST_SHARD_COUNT))
    ):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-invalid"
            ),
        }
    failed_refs = tuple(
        f"pytest-shard-ref:{index}:{'timed-out' if timed_out else 'failed'}"
        for index, return_code, timed_out, _failed_test_refs in sorted(normalized)
        if timed_out or return_code != 0
    )
    failed_test_refs = tuple(
        failed_test_ref
        for _index, return_code, _timed_out, shard_failed_test_refs in sorted(
            normalized
        )
        if return_code != 0
        for failed_test_ref in shard_failed_test_refs
    )
    if len(failed_test_refs) != len(set(failed_test_refs)):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-invalid"
            ),
        }
    derived_run_status = (
        "timeout"
        if any(timed_out for _, _, timed_out, _ in normalized)
        else "failed"
        if failed_refs
        else "green"
    )
    if run_status != derived_run_status or (command_status == "pass") != (
        derived_run_status == "green"
    ):
        return {
            "pytest_shard_evidence_status": "rejected",
            "pytest_shard_evidence_reason_ref": (
                "reason-ref:ci:pytest-performance-report-inconsistent"
            ),
        }
    evidence: dict[str, Any] = {
        "pytest_shard_evidence_status": "available",
        "pytest_shard_plan_fingerprint_ref": plan_ref,
        "pytest_shard_count": CANONICAL_PYTEST_SHARD_COUNT,
        "failed_shard_count": len(failed_refs),
        "failed_shard_refs": failed_refs,
    }
    if failed_test_refs:
        evidence.update(
            {
                "failed_test_refs": failed_test_refs,
                "failed_test_ref_posture": ("diagnostic_untrusted_code_metadata_only"),
            }
        )
    return evidence


def _run_command(
    command: CommandSpec,
    *,
    repository_sha: str,
    base_sha: str | None = None,
    visual_scope: str | None = None,
    temp_root: Path,
    validate_start: Callable[[], None] | None = None,
    before_start: Callable[[], None] | None = None,
    after_spawn: Callable[[], None] | None = None,
    on_spawn_failure: Callable[[], None] | None = None,
    emit_failure_diagnostic_ref: bool = False,
) -> dict[str, Any]:
    resolved_base_sha = base_sha or repository_sha
    started_at = _utc_now()
    started = time.perf_counter()
    output_path: Path | None = None
    output_descriptor: int | None = None
    process: subprocess.Popen[bytes] | None = None
    timed_out = False
    interrupted = False
    registration_active = False
    pending_signal: int | None = None
    cleanup_attempted = False
    returncode: int | None = None
    signal_handling = False
    unspawned_reservation_active = False

    def settle_process() -> None:
        nonlocal cleanup_attempted
        if process is None or cleanup_attempted:
            return
        cleanup_attempted = True
        stop_processes((process,), TERMINATION_GRACE_SECONDS)

    def handle_signal(signum: int, _frame: object) -> None:
        nonlocal interrupted, pending_signal, signal_handling
        interrupted = True
        if signal_handling:
            return
        signal_handling = True
        if registration_active:
            pending_signal = signum
            return
        if cleanup_attempted:
            return
        raise KeyboardInterrupt(f"CI lane interrupted by signal {signum}")

    def release_unspawned_reservation() -> None:
        nonlocal unspawned_reservation_active
        if not unspawned_reservation_active:
            return
        unspawned_reservation_active = False
        if on_spawn_failure is not None:
            on_spawn_failure()

    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix="uaa-ci-transient-",
            dir=temp_root,
            delete=False,
        ) as output:
            output_path = Path(output.name)
            output_descriptor = os.dup(output.fileno())
            with installed_signal_handlers(cancellation_signals(), handle_signal):
                try:
                    if validate_start is not None:
                        validate_start()
                    registration_active = True
                    if before_start is not None:
                        unspawned_reservation_active = True
                        before_start()
                    if pending_signal is not None:
                        interrupted_by = pending_signal
                        pending_signal = None
                        registration_active = False
                        release_unspawned_reservation()
                        raise KeyboardInterrupt(
                            f"CI lane interrupted by signal {interrupted_by}"
                        )
                    try:
                        process = spawn_owned_process_group(
                            _resolved_argv(
                                command,
                                temp_root,
                                repository_sha,
                                resolved_base_sha,
                            ),
                            cwd=ROOT,
                            env=_safe_env(
                                command,
                                temp_root,
                                resolved_base_sha,
                                visual_scope,
                            ),
                            stdout=output,
                            stderr=subprocess.STDOUT,
                        )
                    except BaseException:
                        registration_active = False
                        release_unspawned_reservation()
                        raise
                    else:
                        unspawned_reservation_active = False
                        if after_spawn is not None:
                            try:
                                after_spawn()
                            except BaseException:
                                settle_process()
                                raise
                        registration_active = False
                        if pending_signal is not None:
                            interrupted_by = pending_signal
                            pending_signal = None
                            raise KeyboardInterrupt(
                                f"CI lane interrupted by signal {interrupted_by}"
                            )
                    deadline = time.monotonic() + command.timeout_seconds
                    while returncode is None:
                        if process_group_leader_is_terminal_without_reaping(process):
                            settle_process()
                            if not isinstance(process.returncode, int):
                                raise RuntimeError(
                                    "CI lane terminal status is unavailable"
                                )
                            returncode = process.returncode
                            break
                        output.flush()
                        if output.tell() > MAX_TRANSIENT_OUTPUT_BYTES:
                            settle_process()
                            returncode = 125
                            break
                        if time.monotonic() >= deadline:
                            timed_out = True
                            settle_process()
                            returncode = 124
                            break
                        time.sleep(0.05)
                except BaseException:
                    registration_active = False
                    if process is None:
                        release_unspawned_reservation()
                    raise
                finally:
                    settle_process()
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
        if output_path is None:
            output_bytes = 0
            output_digest = hashlib.sha256(b"").hexdigest()
        else:
            if output_descriptor is None:
                raise RuntimeError(
                    "CI transient output descriptor is unavailable"
                ) from None
            output_bytes, output_digest = (
                _transient_output_metadata_from_descriptor(output_descriptor)
            )
    finally:
        if output_descriptor is not None:
            try:
                _cleanup_transient_output_inode(
                    output_descriptor,
                    temp_root=temp_root,
                )
            finally:
                os.close(output_descriptor)

    duration_ms = max(0, int((time.perf_counter() - started) * 1000))
    status_value = "pass" if returncode == 0 else "fail"
    if timed_out:
        status_value = "timed_out"
    elif interrupted:
        status_value = "cancelled"
    result = {
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
    if emit_failure_diagnostic_ref and returncode != 0:
        result["diagnostic_digest_ref"] = (
            f"diagnostic-output-ref:sha256:{output_digest}"
        )
    return result


def _append_summary(path: Path | None, lines: list[str]) -> None:
    if path is None:
        return
    if path.name in {"", ".", ".."}:
        raise ValueError("CI receipt target name is invalid")
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
    if path.name in {"", ".", ".."} or len(os.fsencode(path.name)) > 255:
        raise ValueError("CI receipt target name is invalid")
    lexical_parent = Path(os.path.abspath(path.parent))
    if not lexical_parent.is_relative_to(temp_root):
        raise ValueError("CI receipt target must remain inside the temp root")
    relative_parts = lexical_parent.relative_to(temp_root).parts
    if any(part in {"", ".", ".."} for part in relative_parts):
        raise ValueError("CI receipt target must remain inside the temp root")
    parent_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        parent_descriptor = os.open(temp_root, parent_flags)
    except OSError as exc:
        raise ValueError("CI receipt temp root is unsafe") from exc
    try:
        root_info = os.fstat(parent_descriptor)
        if (
            not stat.S_ISDIR(root_info.st_mode)
            or root_info.st_uid != os.getuid()
            or root_info.st_mode & 0o022
        ):
            raise ValueError("CI receipt temp root is unsafe")
        for component in relative_parts:
            try:
                child_descriptor = os.open(
                    component,
                    parent_flags,
                    dir_fd=parent_descriptor,
                )
            except FileNotFoundError:
                try:
                    os.mkdir(component, 0o700, dir_fd=parent_descriptor)
                    os.fsync(parent_descriptor)
                except FileExistsError:
                    pass
                child_descriptor = os.open(
                    component,
                    parent_flags,
                    dir_fd=parent_descriptor,
                )
            child_info = os.fstat(child_descriptor)
            if (
                not stat.S_ISDIR(child_info.st_mode)
                or child_info.st_uid != os.getuid()
                or child_info.st_mode & 0o022
            ):
                os.close(child_descriptor)
                raise ValueError("CI receipt parent is unsafe")
            os.close(parent_descriptor)
            parent_descriptor = child_descriptor
    except OSError as exc:
        os.close(parent_descriptor)
        raise ValueError("CI receipt target must remain inside the temp root") from exc
    except Exception:
        os.close(parent_descriptor)
        raise
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= (
        getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor: int | None = None
    try:
        descriptor = os.open(path.name, flags, 0o600, dir_fd=parent_descriptor)
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
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise ValueError("CI receipt write did not complete")
            view = view[written:]
        os.fsync(descriptor)
        os.fsync(parent_descriptor)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent_descriptor)


def _assert_pytest_collection_absent(temp_root: Path) -> None:
    path = temp_root / PYTEST_COLLECTION_EVIDENCE_NAME
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError("pytest collection evidence must not predate the current attempt")


def _frontend_collection_evidence_path(temp_root: Path) -> Path:
    return (
        temp_root
        / FRONTEND_COLLECTION_EVIDENCE_DIRNAME
        / FRONTEND_COLLECTION_EVIDENCE_NAME
    )


def _assert_frontend_collection_absent(temp_root: Path) -> None:
    path = _frontend_collection_evidence_path(temp_root)
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError("frontend collection evidence must not predate the current attempt")


def _typed_output_digest(results: list[dict[str, Any]]) -> str:
    safe_results = tuple(
        {
            "command_ref": result["command_ref"],
            "status": result["status"],
            "result_ref": result["result_ref"],
            "duration_ms": result["duration_ms"],
            "output_byte_count": result.get("output_byte_count", 0),
            "output_digest": result.get("output_digest"),
        }
        for result in results
    )
    return hashlib.sha256(
        json.dumps(safe_results, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _execution_failure_reason_ref(results: list[dict[str, Any]]) -> str:
    """Keep explicitly observed infrastructure outcomes non-deterministic."""

    if any(result.get("status") == "timed_out" for result in results):
        return "reason-ref:verification:infrastructure-failure"
    return "reason-ref:verification:deterministic-code-failure"


def _build_typed_lane_evidence(
    *,
    lane_ref: str,
    legacy_receipt: dict[str, Any],
    full_plan: Any,
    results: list[dict[str, Any]],
    execution_surface_ref: str,
    pytest_collection: dict[str, Any] | None,
    frontend_collection: dict[str, Any] | None = None,
    reused_receipts_by_command: dict[str, VerificationReceipt] | None = None,
    pre_typescript_runtime: Any | None = None,
    pre_execution_identity_ref: str | None = None,
) -> tuple[VerificationReceipt, VerificationRunManifest]:
    reused_receipts_by_command = reused_receipts_by_command or {}
    matching_units = tuple(unit for unit in CI_JOB_GRAPH if unit.lane_ref == lane_ref)
    if len(matching_units) != 1:
        raise ValueError("typed CI evidence requires one exact canonical unit")
    unit = matching_units[0]
    lane = lane_registry()[lane_ref]
    result_command_refs = tuple(str(result["command_ref"]) for result in results)
    if (
        not result_command_refs
        or result_command_refs != unit.command_refs[: len(result_command_refs)]
    ):
        raise ValueError("typed CI evidence command membership is not canonical")
    terminal_status = (
        VerificationTerminalStatus.CANCELLED
        if any(result["status"] == "cancelled" for result in results)
        else VerificationTerminalStatus.PASSED
        if legacy_receipt["status"] == "pass"
        else VerificationTerminalStatus.FAILED
    )
    if terminal_status is VerificationTerminalStatus.PASSED and any(
        result["status"]
        in {"skipped", "not_applicable", "satisfied_by_required_dependency"}
        for result in results
    ):
        terminal_status = VerificationTerminalStatus.BLOCKED
    if (
        terminal_status is VerificationTerminalStatus.PASSED
        and result_command_refs != unit.command_refs
    ):
        raise ValueError(
            "passed typed CI evidence requires complete command membership"
        )

    test_collection_posture = "not_applicable"
    observed_collection_fingerprint: str | None = None
    observed_test_count = 0
    if lane_ref == "ci-pytest-shards":
        if pytest_collection is None:
            test_collection_posture = "unavailable"
            terminal_status = VerificationTerminalStatus.FAILED
        else:
            test_collection_posture = "collected"
            observed_collection_fingerprint = str(
                pytest_collection["collection_digest_ref"]
            ).removeprefix("sha256:")
            observed_test_count = int(pytest_collection["collected_test_count"])
    elif any(
        result["command_ref"] in {
            "command:frontend.check",
            "command:frontend.visual-regression",
        }
        and result["status"]
        not in {"skipped", "not_applicable", "satisfied_by_required_dependency"}
        for result in results
    ):
        frontend_is_reused = any(
            result["command_ref"] == "command:frontend.check"
            and result["status"] == "reused_exact_receipt"
            for result in results
        )
        if frontend_collection is None and not frontend_is_reused:
            test_collection_posture = "unavailable"
            if terminal_status is VerificationTerminalStatus.PASSED:
                terminal_status = VerificationTerminalStatus.FAILED
        elif frontend_collection is not None:
            test_collection_posture = "collected"
            observed_collection_fingerprint = str(
                frontend_collection["collection_digest_ref"]
            ).removeprefix("sha256:")
            observed_test_count = int(frontend_collection["collected_test_count"])

    declared_typescript = None
    runtime_typescript = None
    typescript_project_fingerprint: str | None = None
    typescript_runtime_fingerprint: str | None = None
    typescript_version_ref: str | None = None
    typescript_binding_posture = "not_applicable"
    if "command:frontend.check" in result_command_refs:
        frontend_result = next(
            result
            for result in results
            if result["command_ref"] == "command:frontend.check"
        )
        if frontend_result["status"] == "reused_exact_receipt":
            source_receipt = reused_receipts_by_command.get("command:frontend.check")
            if (
                source_receipt is None
                or source_receipt.status is not VerificationTerminalStatus.PASSED
                or source_receipt.test_collection_posture != "collected"
                or source_receipt.typescript_binding_posture != "resolved"
                or source_receipt.typescript_project_fingerprint
                != full_plan.typescript_project_fingerprint
                or source_receipt.typescript_runtime_fingerprint is None
                or source_receipt.typescript_version_ref is None
            ):
                raise ValueError("frontend reuse lacks exact dependency proof")
            typescript_project_fingerprint = (
                source_receipt.typescript_project_fingerprint
            )
            typescript_runtime_fingerprint = (
                source_receipt.typescript_runtime_fingerprint
            )
            typescript_version_ref = source_receipt.typescript_version_ref
            typescript_binding_posture = "resolved"
            if frontend_collection is None:
                test_collection_posture = "collected"
                observed_collection_fingerprint = (
                    source_receipt.observed_test_collection_fingerprint
                )
                observed_test_count = source_receipt.observed_test_count
        elif frontend_result["status"] not in {
            "skipped",
            "not_applicable",
            "satisfied_by_required_dependency",
        }:
            declared_typescript = build_declared_typescript_binding(
                ROOT / "apps/control-center"
            )
            if (
                declared_typescript.declared_project_fingerprint
                != full_plan.typescript_project_fingerprint
            ):
                raise ValueError(
                    "TypeScript declaration changed after plan construction"
                )
            runtime_typescript = resolve_typescript_runtime_binding(
                ROOT / "apps/control-center", declared_typescript
            )
            if (
                pre_typescript_runtime is None
                or runtime_typescript != pre_typescript_runtime
            ):
                raise ValueError("TypeScript runtime changed during verification")
            typescript_project_fingerprint = (
                declared_typescript.declared_project_fingerprint
            )
            typescript_runtime_fingerprint = (
                runtime_typescript.resolved_runtime_fingerprint
            )
            typescript_version_ref = (
                f"typescript-version:{runtime_typescript.typescript_version}"
            )
            typescript_binding_posture = "resolved"
    nonexecution_results = tuple(
        result
        for result in results
        if result["status"]
        in {"skipped", "not_applicable", "satisfied_by_required_dependency"}
    )
    nonexecution_unbound = bool(nonexecution_results)
    declared_optional_nonexecution = bool(nonexecution_results) and (
        result_command_refs == unit.command_refs
        and {str(result["command_ref"]) for result in nonexecution_results}
        <= set(lane.optional_command_refs)
    )
    if nonexecution_unbound and not declared_optional_nonexecution:
        receipt_schema_version = "uaa_verification_receipt.v2"
    else:
        receipt_schema_version = "uaa_verification_receipt.v4"
    executed_command_result_bindings = tuple(
        (str(result["command_ref"]), str(result["result_ref"]))
        for result in results
        if result["status"]
        not in {
            "reused_exact_receipt",
            "skipped",
            "not_applicable",
            "satisfied_by_required_dependency",
        }
    )
    nonexecuted_command_result_bindings = tuple(
        (
            str(result["command_ref"]),
            str(result["result_ref"]),
            str(result["reason_ref"]),
        )
        for result in nonexecution_results
    )
    reused_command_receipt_bindings = tuple(
        (str(result["command_ref"]), str(result["result_ref"]))
        for result in results
        if result["status"] == "reused_exact_receipt"
    )
    if (
        terminal_status is VerificationTerminalStatus.PASSED
        and any(
            command_ref.startswith("command:pytest.")
            or command_ref in TEST_EXECUTION_COMMAND_REFS
            for command_ref in result_command_refs
        )
        and test_collection_posture != "collected"
    ):
        terminal_status = VerificationTerminalStatus.BLOCKED
    execution_identity_ref = None
    if receipt_schema_version == "uaa_verification_receipt.v4":
        if pre_execution_identity_ref is None:
            raise ValueError("v4 verification evidence requires a pre-start identity")
        execution_identity_ref = build_verification_execution_identity(
            full_plan,
            unit,
            execution_surface_ref=execution_surface_ref,
            typescript_runtime_fingerprint=typescript_runtime_fingerprint,
            typescript_version_ref=typescript_version_ref,
        ).identity_ref
        if execution_identity_ref != pre_execution_identity_ref:
            raise ValueError("verification execution identity changed after start")

    receipt = VerificationReceipt(
        schema_version=receipt_schema_version,
        receipt_ref=f"receipt:verification:{'0' * 64}",
        plan_fingerprint=full_plan.plan_fingerprint,
        unit_ref=unit.unit_ref,
        repository_sha=full_plan.repository_sha,
        dependency_state_fingerprint=dependency_state_fingerprint(full_plan),
        platform_fingerprint=full_plan.platform_fingerprint,
        command_manifest_fingerprint=full_plan.command_manifest_fingerprint,
        verifier_definition_fingerprint=full_plan.verifier_definition_fingerprint,
        test_collection_fingerprint=full_plan.test_collection_fingerprint,
        status=terminal_status,
        started_at=str(legacy_receipt["started_at"]),
        completed_at=str(legacy_receipt["completed_at"]),
        duration_ms=int(legacy_receipt["duration_ms"]),
        result_refs=tuple(str(result["result_ref"]) for result in results),
        output_byte_count=sum(
            int(result.get("output_byte_count", 0)) for result in results
        ),
        output_digest=_typed_output_digest(results),
        equivalent_receipt_ref=str(legacy_receipt["receipt_ref"]),
        command_refs=result_command_refs,
        command_result_bindings=executed_command_result_bindings,
        execution_surface_ref=execution_surface_ref,
        proof_equivalence_ref=unit.proof_equivalence_ref,
        test_collection_posture=test_collection_posture,
        observed_test_collection_fingerprint=observed_collection_fingerprint,
        observed_test_count=observed_test_count,
        typescript_binding_posture=typescript_binding_posture,
        typescript_project_fingerprint=typescript_project_fingerprint,
        typescript_runtime_fingerprint=typescript_runtime_fingerprint,
        typescript_version_ref=typescript_version_ref,
        receipt_fingerprint="0" * 64,
        dependency_lock_set_fingerprint=(
            dependency_lock_set_fingerprint(full_plan)
            if receipt_schema_version == "uaa_verification_receipt.v4"
            else None
        ),
        pytest_shard_plan_fingerprint=(
            full_plan.pytest_shard_plan_fingerprint
            if receipt_schema_version == "uaa_verification_receipt.v4"
            else None
        ),
        execution_identity_ref=execution_identity_ref,
        executed_command_result_bindings=(
            executed_command_result_bindings
            if receipt_schema_version == "uaa_verification_receipt.v4"
            else ()
        ),
        nonexecuted_command_result_bindings=(
            nonexecuted_command_result_bindings
            if receipt_schema_version == "uaa_verification_receipt.v4"
            else ()
        ),
        reused_command_receipt_bindings=(
            reused_command_receipt_bindings
            if receipt_schema_version == "uaa_verification_receipt.v4"
            else ()
        ),
        observed_platform_fingerprint=(
            observed_platform_fingerprint()
            if receipt_schema_version == "uaa_verification_receipt.v4"
            else None
        ),
    )
    receipt_fingerprint = verification_receipt_fingerprint(receipt)
    receipt = replace(
        receipt,
        receipt_ref=f"receipt:verification:{receipt_fingerprint}",
        receipt_fingerprint=receipt_fingerprint,
    )
    receipt.validate()

    run_schema_version = (
        "uaa_verification_run.v2"
        if receipt.schema_version == "uaa_verification_receipt.v2"
        else "uaa_verification_run.v3"
    )
    missing_unit_refs = tuple(
        unit_ref
        for unit_ref in full_plan.selected_unit_refs
        if unit_ref != receipt.unit_ref
    )
    run_status = (
        VerificationTerminalStatus.FAILED
        if receipt.status is VerificationTerminalStatus.FAILED
        else VerificationTerminalStatus.BLOCKED
    )
    run = VerificationRunManifest(
        schema_version=run_schema_version,
        run_ref=f"run:verification:{'0' * 64}",
        plan_fingerprint=full_plan.plan_fingerprint,
        repository_sha=full_plan.repository_sha,
        receipt_refs=(receipt.receipt_ref,),
        started_at=receipt.started_at,
        completed_at=receipt.completed_at,
        status=run_status,
        run_fingerprint="0" * 64,
        dependency_state_fingerprint=dependency_state_fingerprint(full_plan),
        command_manifest_fingerprint=full_plan.command_manifest_fingerprint,
        execution_surface_ref=execution_surface_ref,
        unit_receipt_bindings=((receipt.unit_ref, receipt.receipt_ref),),
        dependency_lock_set_fingerprint=(
            dependency_lock_set_fingerprint(full_plan)
            if run_schema_version == "uaa_verification_run.v3"
            else None
        ),
        platform_fingerprint=(
            full_plan.platform_fingerprint
            if run_schema_version == "uaa_verification_run.v3"
            else None
        ),
        verifier_definition_fingerprint=(
            full_plan.verifier_definition_fingerprint
            if run_schema_version == "uaa_verification_run.v3"
            else None
        ),
        test_collection_fingerprint=(
            full_plan.test_collection_fingerprint
            if run_schema_version == "uaa_verification_run.v3"
            else None
        ),
        pytest_shard_plan_fingerprint=(
            full_plan.pytest_shard_plan_fingerprint
            if run_schema_version == "uaa_verification_run.v3"
            else None
        ),
        typescript_project_fingerprint=(
            full_plan.typescript_project_fingerprint
            if run_schema_version == "uaa_verification_run.v3"
            else None
        ),
        required_unit_refs=(
            full_plan.selected_unit_refs
            if run_schema_version == "uaa_verification_run.v3"
            else ()
        ),
        missing_unit_refs=(
            missing_unit_refs if run_schema_version == "uaa_verification_run.v3" else ()
        ),
        failed_unit_refs=(
            (receipt.unit_ref,)
            if run_schema_version == "uaa_verification_run.v3"
            and receipt.status is VerificationTerminalStatus.FAILED
            else ()
        ),
        reason_refs=(
            (
                ("reason-ref:verification:unit-failed",)
                if receipt.status is VerificationTerminalStatus.FAILED
                else ("reason-ref:verification:whole-run-incomplete",)
            )
            if run_schema_version == "uaa_verification_run.v3"
            else ()
        ),
        observed_test_collection_bindings=(
            ((receipt.unit_ref, receipt.observed_test_collection_fingerprint),)
            if run_schema_version == "uaa_verification_run.v3"
            and receipt.observed_test_collection_fingerprint is not None
            else ()
        ),
    )
    run_fingerprint = verification_run_manifest_fingerprint(run)
    run = replace(
        run,
        run_ref=f"run:verification:{run_fingerprint}",
        run_fingerprint=run_fingerprint,
    )
    run.validate()
    return receipt, run


def _canonicalize_terminal_dependency_receipts(
    required_unit_refs: tuple[str, ...],
    dependency_receipts_by_unit: dict[str, VerificationReceipt],
) -> dict[str, VerificationReceipt]:
    if (
        len(dependency_receipts_by_unit) != len(required_unit_refs)
        or set(dependency_receipts_by_unit) != set(required_unit_refs)
    ):
        raise ValueError("terminal dependency evidence is incomplete")
    return {
        unit_ref: dependency_receipts_by_unit[unit_ref]
        for unit_ref in required_unit_refs
    }


def _build_terminal_foundation_run(
    full_plan: Any,
    dependency_receipts_by_unit: dict[str, VerificationReceipt],
    foundation_receipt: VerificationReceipt,
    *,
    execution_surface_ref: str,
) -> VerificationRunManifest:
    foundation_unit = next(
        unit for unit in CI_JOB_GRAPH if unit.unit_ref == "foundation-gate-report"
    )
    if foundation_receipt.unit_ref != foundation_unit.unit_ref:
        raise ValueError("terminal dependency evidence is incomplete")
    dependency_receipts_by_unit = _canonicalize_terminal_dependency_receipts(
        foundation_unit.needs,
        dependency_receipts_by_unit,
    )
    aggregate_result = aggregate_verification_run(
        full_plan,
        VERIFICATION_DAG,
        (
            *(
                dependency_receipts_by_unit[dependency_ref]
                for dependency_ref in foundation_unit.needs
                if next(
                    unit
                    for unit in CI_JOB_GRAPH
                    if unit.unit_ref == dependency_ref
                ).unit_kind
                is not VerificationUnitKind.AGGREGATE
            ),
            foundation_receipt,
        ),
        execution_surface_ref=execution_surface_ref,
    )
    incoming_aggregate = dependency_receipts_by_unit.get("pytest")
    derived_aggregate = next(
        (
            receipt
            for receipt in aggregate_result.derived_receipts
            if receipt.unit_ref == "pytest"
        ),
        None,
    )
    if (
        incoming_aggregate is None
        or derived_aggregate != incoming_aggregate
        or aggregate_result.run_manifest.status
        is not VerificationTerminalStatus.PASSED
        or aggregate_result.run_manifest.missing_unit_refs
        or aggregate_result.run_manifest.failed_unit_refs
    ):
        raise ValueError("terminal verification run proof is incomplete")
    return aggregate_result.run_manifest


def _pytest_shard_summary_lines(result: dict[str, Any]) -> list[str]:
    status = result.get("pytest_shard_evidence_status")
    if status is None:
        return []
    lines = ["Pytest shard evidence: " + str(status)]
    for failed_ref in result.get("failed_shard_refs", ()):
        shard_index = failed_ref.split(":", maxsplit=2)[1]
        lines.append(
            f"Failed shard: {failed_ref} "
            f"(reproduce with make ci-reproduce-shard CI_SHARD_INDEX={shard_index})"
        )
    for failed_test_ref in result.get("failed_test_refs", ()):
        lines.append(f"Diagnostic test ref: {failed_test_ref}")
    collection_status = result.get("pytest_collection_evidence_status")
    if collection_status is not None:
        lines.append("Pytest collection evidence: " + str(collection_status))
    collection_reason_ref = result.get("pytest_collection_evidence_reason_ref")
    if collection_reason_ref is not None:
        lines.append("Pytest collection evidence reason: " + str(collection_reason_ref))
    if collected_count := result.get("pytest_collected_test_count"):
        lines.append(f"Observed pytest tests: {collected_count}")
    frontend_status = result.get("frontend_collection_evidence_status")
    if frontend_status is not None:
        lines.append("Frontend collection evidence: " + str(frontend_status))
    if frontend_count := result.get("frontend_collected_test_count"):
        lines.append(f"Observed frontend tests: {frontend_count}")
    return lines


def run_lane(
    lane_ref: str,
    *,
    repository_sha: str,
    base_sha: str | None = None,
    temp_root: Path,
    visual_scope: str = "unknown_fail_closed",
    docker_available: str = "unknown_fail_closed",
    summary_file: Path | None = None,
    receipt_file: Path | None = None,
    verification_receipt_file: Path | None = None,
    verification_run_manifest_file: Path | None = None,
    verification_store_root: Path | None = None,
    github_output_file: Path | None = None,
    verification_execution_fence_root: Path | None = None,
    dependency_envelopes: tuple[str, ...] = (),
    full_suite_lock_mode: str = "github",
    execution_surface: str | None = None,
    emit_failure_diagnostic_ref: bool = False,
) -> dict[str, Any]:
    if _git_head(ROOT) != repository_sha:
        raise ValueError("CI lane SHA does not match the checked-out repository")
    resolved_base_sha = base_sha or repository_sha
    if re.fullmatch(r"[0-9a-f]{40}", resolved_base_sha) is None:
        raise ValueError("CI lane base SHA must be an exact lowercase ref")
    lanes = lane_registry()
    if lane_ref not in lanes:
        raise ValueError("unknown canonical CI lane ref")
    lane = lanes[lane_ref]
    if (
        lane_ref == "ci-control-center-frontend"
        and verification_execution_fence_root is None
    ):
        raise ValueError(
            "canonical frontend verification requires a durable execution fence"
        )
    diagnostic_reproduction = (
        PYTEST_REPRODUCTION_LANE_RE.fullmatch(lane_ref) is not None
    )
    resolved_execution_surface = execution_surface or (
        "local" if diagnostic_reproduction else full_suite_lock_mode
    )
    if resolved_execution_surface not in {"github", "local", "private"}:
        raise ValueError("unknown verification execution surface")
    if not diagnostic_reproduction and execution_surface is not None:
        raise ValueError(
            "execution surface override is limited to diagnostic reproduction"
        )
    if diagnostic_reproduction and resolved_execution_surface not in {
        "local",
        "private",
    }:
        raise ValueError("diagnostic shard reproduction is local/private only")
    if not diagnostic_reproduction and resolved_execution_surface == "private":
        raise PrivateNonDiagnosticExecutionError(
            "private execution is limited to exact diagnostic shard reproduction"
        )
    if diagnostic_reproduction and (
        verification_receipt_file is not None
        or verification_run_manifest_file is not None
        or verification_store_root is not None
        or github_output_file is not None
        or verification_execution_fence_root is not None
    ):
        raise ValueError(
            "diagnostic shard reproduction cannot emit typed gating evidence"
        )
    temp_root = _safe_temp_root(temp_root)
    plan = build_plan(
        ROOT,
        repository_sha,
        base_sha=resolved_base_sha,
        lane_refs=(lane_ref,),
        frontend_visual_scope=visual_scope,
    )
    pytest_resource_attempt_fingerprint = (
        verification_exclusive_resource_attempt_fingerprint(
            repository_sha=repository_sha,
            dependency_state_ref=dependency_state_fingerprint(plan),
            exclusive_resource_ref="resource-ref:complete-pytest",
            typescript_runtime_fingerprint=None,
            typescript_version_ref=None,
        )
        if lane_ref == "ci-pytest-shards"
        else None
    )
    commands = command_registry()
    if lane_ref == "ci-pytest-shards" and importlib.util.find_spec("pytest") is None:
        raise PytestRuntimeUnavailableError(
            "canonical pytest runtime is unavailable before suite start"
        )
    validate_lane_environment(ROOT, temp_root, lane_ref=lane_ref)
    typed_evidence_requested = verification_execution_fence_root is not None or any(
        value is not None
        for value in (
            verification_receipt_file,
            verification_run_manifest_file,
            verification_store_root,
            github_output_file,
        )
    ) or bool(dependency_envelopes)
    full_plan_before = (
        build_plan(
            ROOT,
            repository_sha,
            base_sha=resolved_base_sha,
            frontend_visual_scope=visual_scope,
        )
        if typed_evidence_requested
        else None
    )
    pre_typescript_runtime = None
    if (
        "command:frontend.check" in lane.command_refs
        and "command:frontend.check" not in lane.satisfied_command_refs
    ):
        declared_typescript = build_declared_typescript_binding(
            ROOT / "apps/control-center"
        )
        if (
            declared_typescript.declared_project_fingerprint
            != plan.typescript_project_fingerprint
        ):
            raise ValueError("TypeScript declaration does not match the CI plan")
        pre_typescript_runtime = resolve_typescript_runtime_binding(
            ROOT / "apps/control-center", declared_typescript
        )
    pre_execution_identity = None
    pre_execution_identity_ref: str | None = None
    identity_typescript_runtime_fingerprint: str | None = None
    identity_typescript_version_ref: str | None = None
    typed_unit = None
    reused_receipts_by_command: dict[str, VerificationReceipt] = {}
    dependency_receipts_by_unit: dict[str, VerificationReceipt] = {}
    if full_plan_before is not None:
        matching_units = tuple(
            unit for unit in CI_JOB_GRAPH if unit.lane_ref == lane_ref
        )
        if len(matching_units) != 1:
            raise ValueError("typed CI evidence requires one exact canonical unit")
        typed_unit = matching_units[0]
        if dependency_envelopes:
            terminal_foundation = typed_unit.unit_ref == "foundation-gate-report"
            if not lane.satisfied_command_refs and not terminal_foundation:
                raise ValueError(
                    "verification dependency envelopes are not declared for this lane"
                )
            direct_dependencies = tuple(typed_unit.needs)
            direct_dependency_set = set(direct_dependencies)
            source_receipt_refs: set[str] = set()
            for encoded_envelope in dependency_envelopes:
                envelope = decode_github_job_output(encoded_envelope)
                validate_github_job_output_against_plan(
                    envelope,
                    full_plan_before,
                )
                source_receipt = envelope.receipt
                source_unit = next(
                    (
                        unit
                        for unit in CI_JOB_GRAPH
                        if unit.unit_ref == source_receipt.unit_ref
                    ),
                    None,
                )
                if (
                    (
                        envelope.final_run_manifest is not None
                        and source_unit is not None
                        and source_unit.unit_kind is not VerificationUnitKind.AGGREGATE
                    )
                    or source_receipt.unit_ref not in direct_dependency_set
                    or source_unit is None
                    or source_receipt.receipt_ref in source_receipt_refs
                    or source_receipt.unit_ref in dependency_receipts_by_unit
                ):
                    raise ValueError("verification dependency envelope is invalid")
                validate_receipt_for_plan_unit(
                    source_receipt,
                    plan=full_plan_before,
                    unit=source_unit,
                    execution_surface_ref="surface-ref:github",
                )
                if not (
                    source_receipt.status is VerificationTerminalStatus.PASSED
                    or (
                        source_unit.evidence_posture == "typed_optional"
                        and source_receipt.status
                        in {
                            VerificationTerminalStatus.BLOCKED,
                            VerificationTerminalStatus.SKIPPED,
                        }
                    )
                ):
                    raise ValueError("verification dependency evidence did not pass")
                source_receipt_refs.add(source_receipt.receipt_ref)
                dependency_receipts_by_unit[source_receipt.unit_ref] = source_receipt
                if lane.satisfied_command_refs:
                    executed_commands = dict(
                        source_receipt.executed_command_result_bindings
                    )
                    source_matched = False
                    for satisfied_command_ref in lane.satisfied_command_refs:
                        if satisfied_command_ref in executed_commands:
                            source_matched = True
                            if satisfied_command_ref in reused_receipts_by_command:
                                raise ValueError(
                                    "verification dependency command proof is ambiguous"
                                )
                            reused_receipts_by_command[satisfied_command_ref] = (
                                source_receipt
                            )
                    if not source_matched:
                        raise ValueError(
                            "verification dependency envelope proves no reused command"
                        )
            if terminal_foundation:
                dependency_receipts_by_unit = (
                    _canonicalize_terminal_dependency_receipts(
                        direct_dependencies,
                        dependency_receipts_by_unit,
                    )
                )
            if lane.satisfied_command_refs and set(reused_receipts_by_command) != set(
                lane.satisfied_command_refs
            ):
                raise ValueError("verification dependency command proof is incomplete")
        elif lane.satisfied_command_refs or typed_unit.unit_ref == "foundation-gate-report":
            raise ValueError("synthetic dependency satisfaction is forbidden")
        if not lane.satisfied_command_refs:
            identity_typescript_runtime_fingerprint = (
                pre_typescript_runtime.resolved_runtime_fingerprint
                if pre_typescript_runtime is not None
                else None
            )
            identity_typescript_version_ref = (
                f"typescript-version:{pre_typescript_runtime.typescript_version}"
                if pre_typescript_runtime is not None
                else None
            )
            pre_execution_identity = build_verification_execution_identity(
                full_plan_before,
                typed_unit,
                execution_surface_ref=f"surface-ref:{resolved_execution_surface}",
                typescript_runtime_fingerprint=identity_typescript_runtime_fingerprint,
                typescript_version_ref=identity_typescript_version_ref,
            )
            pre_execution_identity_ref = pre_execution_identity.identity_ref
            if (
                lane_ref == "ci-pytest-shards"
                and pre_execution_identity.exclusive_resource_attempt_fingerprint
                != pytest_resource_attempt_fingerprint
            ):
                raise ValueError(
                    "complete pytest resource attempt binding changed"
                )
        else:
            reused_typescript_receipt = reused_receipts_by_command.get(
                "command:frontend.check"
            )
            identity_typescript_runtime_fingerprint = (
                reused_typescript_receipt.typescript_runtime_fingerprint
                if reused_typescript_receipt is not None
                else None
            )
            identity_typescript_version_ref = (
                reused_typescript_receipt.typescript_version_ref
                if reused_typescript_receipt is not None
                else None
            )
            pre_execution_identity = build_verification_execution_identity(
                full_plan_before,
                typed_unit,
                execution_surface_ref=f"surface-ref:{resolved_execution_surface}",
                typescript_runtime_fingerprint=identity_typescript_runtime_fingerprint,
                typescript_version_ref=identity_typescript_version_ref,
            )
            pre_execution_identity_ref = pre_execution_identity.identity_ref

    requires_durable_execution_fence = bool(
        typed_evidence_requested
        and typed_unit is not None
        and {
            "resource-ref:complete-pytest",
            "resource-ref:typescript-typecheck",
        }
        & set(typed_unit.exclusive_resource_refs)
    )
    if requires_durable_execution_fence and verification_execution_fence_root is None:
        raise ValueError(
            "exclusive typed verification requires a durable execution fence"
        )
    if requires_durable_execution_fence and len(typed_unit.command_refs) != 1:
        raise ValueError(
            "exclusive typed verification requires one atomic command boundary"
        )
    if verification_execution_fence_root is not None and not (
        requires_durable_execution_fence
    ):
        raise ValueError("execution fence is limited to exclusive typed verification")
    execution_fence = (
        VerificationExecutionFence(verification_execution_fence_root)
        if requires_durable_execution_fence
        and verification_execution_fence_root is not None
        else None
    )
    execution_fence_owner_token: str | None = None
    exclusive_resource_attempt_fingerprint = (
        pre_execution_identity.exclusive_resource_attempt_fingerprint
        if pre_execution_identity is not None
        else pytest_resource_attempt_fingerprint
    )
    exclusive_resource_ref: str | None = None
    if pre_execution_identity is not None:
        exclusive_resource_ref = pre_execution_identity.exclusive_resource_ref
    elif lane_ref == "ci-pytest-shards":
        exclusive_resource_ref = "resource-ref:complete-pytest"
    if (exclusive_resource_attempt_fingerprint is None) != (
        exclusive_resource_ref is None
    ):
        raise ValueError("exclusive resource execution binding is incomplete")

    def validate_typed_prestart() -> None:
        if full_plan_before is None:
            return
        assert typed_unit is not None
        observed_plan = build_plan(
            ROOT,
            repository_sha,
            base_sha=resolved_base_sha,
            frontend_visual_scope=visual_scope,
        )
        if observed_plan != full_plan_before:
            raise ValueError("verification plan changed before command start")
        observed_typescript_runtime = None
        if pre_typescript_runtime is not None:
            observed_declaration = build_declared_typescript_binding(
                ROOT / "apps/control-center"
            )
            if (
                observed_declaration.declared_project_fingerprint
                != observed_plan.typescript_project_fingerprint
            ):
                raise ValueError("TypeScript declaration changed before command start")
            observed_typescript_runtime = resolve_typescript_runtime_binding(
                ROOT / "apps/control-center",
                observed_declaration,
            )
            if observed_typescript_runtime != pre_typescript_runtime:
                raise ValueError("TypeScript runtime changed before command start")
        if pre_execution_identity_ref is None:
            return
        observed_identity_ref = build_verification_execution_identity(
            observed_plan,
            typed_unit,
            execution_surface_ref=f"surface-ref:{resolved_execution_surface}",
            typescript_runtime_fingerprint=(
                observed_typescript_runtime.resolved_runtime_fingerprint
                if observed_typescript_runtime is not None
                else identity_typescript_runtime_fingerprint
            ),
            typescript_version_ref=(
                f"typescript-version:{observed_typescript_runtime.typescript_version}"
                if observed_typescript_runtime is not None
                else identity_typescript_version_ref
            ),
        ).identity_ref
        if observed_identity_ref != pre_execution_identity_ref:
            raise ValueError("verification execution identity changed before start")

    started_at = _utc_now()
    results: list[dict[str, Any]] = []
    pytest_collection_payload: dict[str, Any] | None = None
    frontend_collection_payload: dict[str, Any] | None = None
    if full_suite_lock_mode not in {"github", "local", "private"}:
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
            resource_attempt_fingerprint=exclusive_resource_attempt_fingerprint,
            resource_ref=exclusive_resource_ref,
        )
        if exclusive_resource_attempt_fingerprint is not None
        else FullSuiteLock(
            path=PYTEST_DIAGNOSTIC_LOCK_PATH,
            wait_seconds=0,
            shared_across_accounts=False,
        )
        if diagnostic_reproduction
        else nullcontext()
    )
    with lock as full_suite_lock:
        expected_pytest_plan_ref: str | None = None
        if lane_ref == "ci-pytest-shards":
            _assert_pytest_report_absent(temp_root)
            _assert_pytest_collection_absent(temp_root)
            expected_pytest_plan_ref = expected_pytest_shard_plan_ref()
        if any(
            command_ref in {
                "command:frontend.check",
                "command:frontend.visual-regression",
            }
            and command_ref not in lane.satisfied_command_refs
            for command_ref in lane.command_refs
        ):
            _assert_frontend_collection_absent(temp_root)
        for command_ref in lane.command_refs:
            if command_ref in lane.satisfied_command_refs:
                source_receipt = reused_receipts_by_command.get(command_ref)
                if source_receipt is None:
                    raise ValueError("exact dependency receipt is required")
                results.append(
                    {
                        "command_ref": command_ref,
                        "category": commands[command_ref].category,
                        "status": "reused_exact_receipt",
                        "duration_ms": 0,
                        "result_ref": source_receipt.receipt_ref,
                        "redaction_status": "content_free_output_metadata_only",
                    }
                )
                continue
            skip_reason = optional_nonexecution_reason_ref(
                command_ref,
                frontend_visual_scope=visual_scope,
            )
            if (
                command_ref == "command:desktop-packaging.proof"
                and docker_available != "unavailable"
            ):
                skip_reason = None
            if skip_reason is not None:
                skip_status = (
                    "not_applicable" if "not-affected" in skip_reason else "skipped"
                )
                results.append(
                    {
                        "command_ref": command_ref,
                        "category": commands[command_ref].category,
                        "status": skip_status,
                        "duration_ms": 0,
                        "reason_ref": skip_reason,
                        "result_ref": optional_nonexecution_result_ref(
                            repository_sha,
                            command_ref,
                            skip_reason,
                        ),
                        "redaction_status": "content_free_output_metadata_only",
                    }
                )
                continue

            def validate_command_start() -> None:
                if exclusive_resource_attempt_fingerprint is not None:
                    full_suite_lock.ensure_start_available()
                validate_typed_prestart()
                if lane_ref == "ci-pytest-shards":
                    assert_matrix_loopback_test_resource_available()

            def begin_durable_command_start() -> None:
                nonlocal execution_fence_owner_token
                if execution_fence is not None:
                    assert pre_execution_identity is not None
                    decision = execution_fence.begin(pre_execution_identity)
                    if (
                        decision.disposition
                        is not VerificationExecutionFenceDisposition.START_GRANTED
                        or decision.owner_token is None
                    ):
                        raise VerificationExecutionFenceError(
                            "exact verification execution is not startable"
                        )
                    execution_fence_owner_token = decision.owner_token

            def record_spawned_command_start() -> None:
                if exclusive_resource_attempt_fingerprint is not None:
                    full_suite_lock.record_start()

            def abort_unspawned_command_start() -> None:
                nonlocal execution_fence_owner_token
                if (
                    execution_fence is None
                    or pre_execution_identity is None
                    or execution_fence_owner_token is None
                ):
                    return
                owner_token = execution_fence_owner_token
                try:
                    execution_fence.abort_prestart(
                        pre_execution_identity,
                        owner_token=owner_token,
                    )
                except BaseException as cleanup_error:
                    raise VerificationExecutionFenceError(
                        "verification pre-start recovery is required"
                    ) from cleanup_error
                execution_fence_owner_token = None

            result = _run_command(
                commands[command_ref],
                repository_sha=repository_sha,
                base_sha=resolved_base_sha,
                visual_scope=visual_scope,
                temp_root=temp_root,
                validate_start=(
                    validate_command_start
                    if lane_ref == "ci-pytest-shards" or typed_evidence_requested
                    else None
                ),
                before_start=(
                    begin_durable_command_start
                    if execution_fence is not None
                    else None
                ),
                after_spawn=(
                    record_spawned_command_start
                    if exclusive_resource_attempt_fingerprint is not None
                    else None
                ),
                on_spawn_failure=(
                    abort_unspawned_command_start
                    if execution_fence is not None
                    else None
                ),
                emit_failure_diagnostic_ref=emit_failure_diagnostic_ref,
            )
            if lane_ref == "ci-pytest-shards":
                assert expected_pytest_plan_ref is not None
                result.update(
                    _pytest_shard_evidence(
                        temp_root,
                        expected_plan_ref=expected_pytest_plan_ref,
                        command_status=str(result["status"]),
                    )
                )
            if (
                lane_ref == "ci-pytest-shards"
                and command_ref == "command:pytest.sharded-suite"
            ):
                try:
                    pytest_collection_payload = load_aggregate_evidence(
                        temp_root / PYTEST_COLLECTION_EVIDENCE_NAME,
                        expected_shard_count=CANONICAL_PYTEST_SHARD_COUNT,
                        expected_plan_fingerprint_ref=expected_pytest_plan_ref,
                    )
                except CollectionEvidenceError as exc:
                    result.update(
                        {
                            "pytest_collection_evidence_status": "rejected",
                            "pytest_collection_evidence_reason_ref": (
                                collection_evidence_reason_ref(exc)
                            ),
                        }
                    )
                    if result["status"] == "pass":
                        result["status"] = "fail"
                else:
                    result.update(
                        {
                            "pytest_collection_evidence_status": "collected",
                            "pytest_collection_digest_ref": (
                                pytest_collection_payload["collection_digest_ref"]
                            ),
                            "pytest_collected_test_count": (
                                pytest_collection_payload["collected_test_count"]
                            ),
                        }
                    )
            if command_ref in {
                "command:frontend.check",
                "command:frontend.visual-regression",
            }:
                try:
                    frontend_collection_payload = consume_frontend_collection_evidence(
                        _frontend_collection_evidence_path(temp_root)
                    )
                except FrontendCollectionEvidenceError:
                    result.update(
                        {
                            "frontend_collection_evidence_status": "rejected",
                            "frontend_collection_evidence_reason_ref": (
                                "reason-ref:ci:frontend-collection-evidence-rejected"
                            ),
                        }
                    )
                    if result["status"] == "pass":
                        result["status"] = "fail"
                else:
                    evidence_passed = (
                        frontend_collection_payload["result_status"] == "passed"
                    )
                    terminal_process_status = result["status"] in {
                        "timed_out",
                        "cancelled",
                    }
                    if (
                        not terminal_process_status
                        and (result["status"] == "pass") != evidence_passed
                    ):
                        result["status"] = "fail"
                        result.update(
                            {
                                "frontend_collection_evidence_status": "rejected",
                                "frontend_collection_evidence_reason_ref": (
                                    "reason-ref:ci:frontend-collection-status-mismatch"
                                ),
                            }
                        )
                    else:
                        result.update(
                            {
                                "frontend_collection_evidence_status": "collected",
                                "frontend_collection_digest_ref": (
                                    frontend_collection_payload[
                                        "collection_digest_ref"
                                    ]
                                ),
                                "frontend_collected_test_count": (
                                    frontend_collection_payload[
                                        "collected_test_count"
                                    ]
                                ),
                            }
                        )
            results.append(result)
            if result["status"] != "pass":
                break

    terminal_ok = all(
        result["status"]
        in {
            "pass",
            "skipped",
            "not_applicable",
            "satisfied_by_required_dependency",
            "reused_exact_receipt",
        }
        for result in results
    ) and len(results) == len(lane.command_refs)
    legacy_status = "pass" if terminal_ok else "fail"
    if any(result.get("status") == "cancelled" for result in results):
        legacy_status = "cancelled"
    elif any(result.get("status") == "timed_out" for result in results):
        legacy_status = "timed_out"
    completed_at = _utc_now()
    receipt = {
        "schema_version": "uaa_ci_lane_receipt.v1",
        "profile_ref": PROFILE_REF,
        "repository_sha": repository_sha,
        "lane_ref": lane_ref,
        "plan": asdict(plan),
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": _wall_duration_ms(started_at, completed_at),
        "status": legacy_status,
        "command_results": results,
        "github_gate_satisfied": False,
        "merge_gate_satisfied": False,
        "redaction_status": "content_free_refs_hashes_counts_and_durations_only",
    }
    if diagnostic_reproduction:
        receipt["execution_surface_ref"] = f"surface-ref:{resolved_execution_surface}"
    receipt["receipt_ref"] = (
        "receipt-ref:ci-lane:"
        + hashlib.sha256(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    typed_artifact_refs: tuple[str, ...] = ()
    typed_receipt: VerificationReceipt | None = None
    run_manifest: VerificationRunManifest | None = None
    if typed_evidence_requested:
        assert full_plan_before is not None
        full_plan = build_plan(
            ROOT,
            repository_sha,
            base_sha=resolved_base_sha,
            frontend_visual_scope=visual_scope,
        )
        if full_plan != full_plan_before:
            raise ValueError("verification plan changed during command execution")
        typed_receipt, run_manifest = _build_typed_lane_evidence(
            lane_ref=lane_ref,
            legacy_receipt=receipt,
            full_plan=full_plan,
            results=results,
            execution_surface_ref=f"surface-ref:{resolved_execution_surface}",
            pytest_collection=pytest_collection_payload,
            frontend_collection=frontend_collection_payload,
            reused_receipts_by_command=reused_receipts_by_command,
            pre_typescript_runtime=pre_typescript_runtime,
            pre_execution_identity_ref=pre_execution_identity_ref,
        )
        if typed_unit is not None and typed_unit.unit_ref == "foundation-gate-report":
            run_manifest = _build_terminal_foundation_run(
                full_plan,
                dependency_receipts_by_unit,
                typed_receipt,
                execution_surface_ref=f"surface-ref:{resolved_execution_surface}",
            )
        _write_receipt(
            verification_receipt_file,
            verification_receipt_payload(typed_receipt),
            temp_root,
        )
        _write_receipt(
            verification_run_manifest_file,
            verification_run_manifest_payload(run_manifest),
            temp_root,
        )
        if verification_store_root is not None:
            store = VerificationReceiptStore(verification_store_root)
            stored_receipt = store.put_receipt(typed_receipt)
            stored_run = store.put_run_manifest(run_manifest)
            typed_artifact_refs = (
                stored_receipt.artifact_ref,
                stored_run.artifact_ref,
            )
        if execution_fence is not None:
            assert pre_execution_identity is not None
            assert execution_fence_owner_token is not None
            failure_reason_ref = "reason-ref:verification:not-applicable"
            failure_evidence_ref = None
            if typed_receipt.status is VerificationTerminalStatus.FAILED:
                failure_reason_ref = _execution_failure_reason_ref(results)
                failure_evidence_ref = typed_receipt.result_refs[0]
            elif typed_receipt.status is VerificationTerminalStatus.BLOCKED:
                failure_reason_ref = "reason-ref:verification:execution-blocked"
                failure_evidence_ref = typed_receipt.result_refs[0]
            elif typed_receipt.status is VerificationTerminalStatus.CANCELLED:
                failure_reason_ref = "reason-ref:verification:execution-cancelled"
                failure_evidence_ref = typed_receipt.result_refs[0]
            terminal_proof = build_verification_execution_terminal_proof(
                pre_execution_identity,
                status=typed_receipt.status,
                receipt_ref=typed_receipt.receipt_ref,
                result_refs=typed_receipt.result_refs,
                output_digest=typed_receipt.output_digest,
                completed_at=typed_receipt.completed_at,
                failure_reason_ref=failure_reason_ref,
                failure_evidence_ref=failure_evidence_ref,
            )
            execution_fence.complete(
                pre_execution_identity,
                owner_token=execution_fence_owner_token,
                terminal_proof=terminal_proof,
            )
        if github_output_file is not None:
            if resolved_execution_surface != "github":
                raise ValueError("GitHub output requires the GitHub execution surface")
            envelope = build_github_job_output_envelope(
                full_plan,
                typed_receipt,
                final_run_manifest=(
                    run_manifest
                    if typed_unit is not None
                    and typed_unit.unit_ref == "foundation-gate-report"
                    else None
                ),
            )
            append_github_output(
                github_output_file,
                GITHUB_OUTPUT_KEY,
                encode_github_job_output(envelope),
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
        summary.extend(f"- {line}" for line in _pytest_shard_summary_lines(result))
    summary.extend(f"- Stored typed proof: {ref}" for ref in typed_artifact_refs)
    _append_summary(summary_file, summary)
    _write_receipt(receipt_file, receipt, temp_root)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one canonical UAA CI lane.")
    parser.add_argument("--lane", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--base-sha")
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
    parser.add_argument("--verification-receipt-file")
    parser.add_argument("--verification-run-manifest-file")
    parser.add_argument("--verification-store-root")
    parser.add_argument("--github-output-file")
    parser.add_argument("--verification-execution-fence-root")
    parser.add_argument("--dependency-envelope", action="append", default=[])
    parser.add_argument(
        "--full-suite-lock-mode",
        choices=("github", "local", "private"),
        default="github",
    )
    parser.add_argument(
        "--execution-surface",
        choices=("github", "local", "private"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.profile != PROFILE_REF:
        parser.error("unknown CI profile")
    try:
        receipt = run_lane(
            args.lane,
            repository_sha=args.sha,
            base_sha=args.base_sha,
            temp_root=Path(args.temp_root),
            visual_scope=args.visual_scope,
            docker_available=args.docker_available,
            summary_file=Path(args.summary_file) if args.summary_file else None,
            receipt_file=Path(args.receipt_file) if args.receipt_file else None,
            verification_receipt_file=(
                Path(args.verification_receipt_file)
                if args.verification_receipt_file
                else None
            ),
            verification_run_manifest_file=(
                Path(args.verification_run_manifest_file)
                if args.verification_run_manifest_file
                else None
            ),
            verification_store_root=(
                Path(args.verification_store_root)
                if args.verification_store_root
                else None
            ),
            github_output_file=(
                Path(args.github_output_file) if args.github_output_file else None
            ),
            verification_execution_fence_root=(
                Path(args.verification_execution_fence_root)
                if args.verification_execution_fence_root
                else None
            ),
            dependency_envelopes=tuple(args.dependency_envelope),
            full_suite_lock_mode=args.full_suite_lock_mode,
            execution_surface=args.execution_surface,
        )
    except PytestRuntimeUnavailableError:
        print(
            "UAA CI lane blocked: " + PYTEST_RUNTIME_UNAVAILABLE_REASON_REF,
            file=sys.stderr,
        )
        return 1
    except MatrixLoopbackTestResourceUnavailableError:
        print(
            "UAA CI lane blocked: "
            + PYTEST_LOOPBACK_RESOURCE_UNAVAILABLE_REASON_REF,
            file=sys.stderr,
        )
        return 1
    except FullSuiteLockUnavailableError:
        print(
            "UAA CI lane blocked: " + FULL_SUITE_LOCK_UNAVAILABLE_REASON_REF,
            file=sys.stderr,
        )
        return 1
    except VerificationEnvironmentPreflightError as exc:
        print(
            f"UAA CI lane blocked: {exc.reason_ref}",
            file=sys.stderr,
        )
        return 1
    except FullSuiteAttemptAlreadyRecordedError:
        print(
            "UAA CI lane blocked: " + FULL_SUITE_ATTEMPT_RECORDED_REASON_REF,
            file=sys.stderr,
        )
        return 1
    except VerificationExecutionFenceError:
        print(
            "UAA CI lane blocked: " + VERIFICATION_EXECUTION_FENCE_REASON_REF,
            file=sys.stderr,
        )
        return 1
    except PrivateNonDiagnosticExecutionError:
        print(
            "UAA CI lane blocked: " + PRIVATE_NON_DIAGNOSTIC_REASON_REF,
            file=sys.stderr,
        )
        return 1
    except (Exception, KeyboardInterrupt):
        print(
            "UAA CI lane blocked: " + CI_LANE_EXECUTION_ERROR_REASON_REF,
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
            for line in _pytest_shard_summary_lines(result):
                print(f"- {line}")
        print("GitHub merge gate satisfied: no")
    return 0 if receipt["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
