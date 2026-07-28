#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_fallback_storage import (  # noqa: E402
    FullSuiteAttemptAlreadyRecordedError,
    FullSuiteLockUnavailableError,
)
from scripts.verification.pytest_shard_artifacts import (  # noqa: E402
    TIMING_SCHEMA_VERSION,
    is_safe_test_ref,
)
from scripts.verification.pytest_shard_plan import (  # noqa: E402
    CANONICAL_PYTEST_SHARD_COUNT,
)
from scripts.verification.run_ci_lane import (  # noqa: E402
    PYTEST_FILE_TIMINGS_NAME,
    PytestRuntimeUnavailableError,
    run_lane,
)
from scripts.verification.verification_execution_identity import (  # noqa: E402
    VerificationExecutionFenceError,
)
from scripts.verification.verification_environment_preflight import (  # noqa: E402
    VerificationEnvironmentPreflightError,
)


DEFAULT_FENCE_ROOT = Path(
    f"/private/tmp/uaa-verification-execution-fence-v2-{os.getuid()}"
)
ALLOWED_LANES = {
    "ci-pytest-shards",
    "ci-control-center-frontend",
}
MAX_TIMING_PROFILE_BYTES = 4 * 1024 * 1024
DEFAULT_DIAGNOSTIC_ROOT = Path(
    f"/private/tmp/uaa-verification-diagnostics-v1-{os.getuid()}"
)
MAX_RETAINED_DIAGNOSTIC_RUNS = 5
MAX_DIAGNOSTIC_OUTPUT_BYTE_COUNT = 64 * 1024 * 1024
SAFE_COMMAND_REF_PATTERN = re.compile(r"^command:[a-z0-9][a-z0-9._:-]{0,127}$")


class LocalVerificationLaneError(RuntimeError):
    """A local exclusive lane could not execute or publish safe evidence."""


def _prepare_diagnostic_root(path: Path) -> Path:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
        or stat.S_IMODE(info.st_mode) & 0o700 != 0o700
    ):
        raise LocalVerificationLaneError(
            "local verification diagnostic boundary is unsafe"
        )
    return path


@contextmanager
def _locked_diagnostic_root(root: Path):
    lock_path = root / ".uaa-diagnostic-retention.lock"
    descriptor = os.open(
        lock_path,
        os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise LocalVerificationLaneError(
                "local verification diagnostic lock is unsafe"
            )
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _retained_diagnostic_directories(root: Path) -> tuple[Path, ...]:
    retained: list[tuple[int, Path]] = []
    try:
        candidates = tuple(root.iterdir())
    except OSError as exc:
        raise LocalVerificationLaneError(
            "local verification diagnostics cannot be bounded"
        ) from exc
    for path in candidates:
        if (
            len(path.name) != 64
            or any(character not in "0123456789abcdef" for character in path.name)
        ):
            continue
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise LocalVerificationLaneError(
                "local verification diagnostics cannot be bounded"
            ) from exc
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            continue
        retained.append((metadata.st_mtime_ns, path))
    return tuple(
        path
        for _mtime_ns, path in sorted(
            retained,
            key=lambda item: item[0],
            reverse=True,
        )
    )


def _remove_diagnostic_directory(path: Path) -> None:
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise LocalVerificationLaneError(
            "local verification diagnostics cannot be bounded"
        ) from exc
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LocalVerificationLaneError(
            "local verification diagnostics cannot be bounded"
        ) from exc
    raise LocalVerificationLaneError(
        "local verification diagnostics cannot be bounded"
    )


def _retain_diagnostics(
    receipt: dict[str, object] | None,
    *,
    diagnostic_root: Path,
    lane_ref: str,
    repository_sha: str,
) -> str:
    root = _prepare_diagnostic_root(diagnostic_root)
    token = hashlib.sha256(
        os.urandom(32)
        + lane_ref.encode("utf-8")
        + repository_sha.encode("ascii")
    ).hexdigest()
    destination = root / token
    with _locked_diagnostic_root(root):
        destination.mkdir(mode=0o700)
        receipt_status = None if receipt is None else receipt.get("status")
        safe_status = (
            receipt_status
            if receipt_status in {"fail", "timed_out", "cancelled", "blocked"}
            else "blocked"
        )
        payload: dict[str, object] = {
            "schema_version": "uaa_local_verification_diagnostic.v1",
            "lane_ref": lane_ref,
            "repository_sha": repository_sha,
            "status": safe_status,
            "command_results": [],
            "redaction_status": "content_free_failure_metadata_only",
        }
        if receipt is not None:
            safe_results: list[dict[str, object]] = []
            results = receipt.get("command_results")
            if isinstance(results, list):
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    command_ref = result.get("command_ref")
                    status_value = result.get("status")
                    output_byte_count = result.get("output_byte_count")
                    output_digest = result.get("output_digest")
                    if (
                        not isinstance(command_ref, str)
                        or SAFE_COMMAND_REF_PATTERN.fullmatch(command_ref) is None
                        or not isinstance(status_value, str)
                        or status_value
                        not in {"pass", "fail", "timed_out", "cancelled"}
                        or not isinstance(output_byte_count, int)
                        or isinstance(output_byte_count, bool)
                        or output_byte_count < 0
                        or output_byte_count > MAX_DIAGNOSTIC_OUTPUT_BYTE_COUNT
                        or not isinstance(output_digest, str)
                        or len(output_digest) != 64
                        or any(
                            character not in "0123456789abcdef"
                            for character in output_digest
                        )
                    ):
                        continue
                    safe_result: dict[str, object] = {
                        "command_ref": command_ref,
                        "status": status_value,
                        "output_byte_count": output_byte_count,
                        "output_digest": output_digest,
                    }
                    failed_shard_refs = result.get("failed_shard_refs")
                    if isinstance(failed_shard_refs, (list, tuple)):
                        safe_shard_refs = tuple(
                            value
                            for value in failed_shard_refs
                            if _safe_failed_shard_ref(value) is not None
                        )
                        if safe_shard_refs:
                            safe_result["failed_shard_refs"] = safe_shard_refs
                    failed_test_refs = result.get("failed_test_refs")
                    if isinstance(failed_test_refs, (list, tuple)):
                        safe_test_refs = tuple(
                            value
                            for value in failed_test_refs
                            if isinstance(value, str) and is_safe_test_ref(value)
                        )
                        if safe_test_refs:
                            safe_result["failed_test_refs"] = safe_test_refs
                    safe_results.append(safe_result)
            payload["command_results"] = safe_results
        diagnostic_path = destination / "diagnostic.json"
        try:
            descriptor = os.open(
                diagnostic_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
            try:
                encoded = (
                    json.dumps(payload, sort_keys=True, separators=(",", ":"))
                    + "\n"
                ).encode("utf-8")
                remaining = memoryview(encoded)
                while remaining:
                    written = os.write(descriptor, remaining)
                    if written <= 0:
                        raise OSError("diagnostic write did not make progress")
                    remaining = remaining[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError as exc:
            _remove_diagnostic_directory(destination)
            raise LocalVerificationLaneError(
                "local verification diagnostics could not be retained"
            ) from exc
        try:
            retained = _retained_diagnostic_directories(root)
            if destination not in retained:
                raise LocalVerificationLaneError(
                    "local verification diagnostics cannot be bounded"
                )
            for stale in retained[MAX_RETAINED_DIAGNOSTIC_RUNS:]:
                _remove_diagnostic_directory(stale)
            retained = _retained_diagnostic_directories(root)
            if (
                destination not in retained
                or len(retained) > MAX_RETAINED_DIAGNOSTIC_RUNS
            ):
                raise LocalVerificationLaneError(
                    "local verification diagnostics cannot be bounded"
                )
        except LocalVerificationLaneError:
            _remove_diagnostic_directory(destination)
            raise
    return f"diagnostic-ref:local-verification:{token}"


def _safe_failed_shard_ref(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    parts = value.split(":")
    if len(parts) != 3 or parts[0] != "pytest-shard-ref":
        return None
    try:
        shard_index = int(parts[1])
    except ValueError:
        return None
    if (
        not 0 <= shard_index < CANONICAL_PYTEST_SHARD_COUNT
        or parts[2] not in {"failed", "timed-out"}
    ):
        return None
    return value


def _print_safe_pytest_failure_refs(receipt: dict[str, object]) -> None:
    results = receipt.get("command_results")
    if not isinstance(results, list):
        return
    for result in results:
        if not isinstance(result, dict):
            continue
        failed_shard_refs = result.get("failed_shard_refs")
        if isinstance(failed_shard_refs, (list, tuple)):
            for value in failed_shard_refs:
                failed_shard_ref = _safe_failed_shard_ref(value)
                if failed_shard_ref is not None:
                    shard_index = failed_shard_ref.split(":")[1]
                    print(
                        f"Failed shard: {failed_shard_ref} "
                        "(reproduce with make ci-reproduce-shard "
                        f"CI_SHARD_INDEX={shard_index})"
                    )
        failed_test_refs = result.get("failed_test_refs")
        if isinstance(failed_test_refs, (list, tuple)):
            for value in failed_test_refs:
                if isinstance(value, str) and is_safe_test_ref(value):
                    print(f"Diagnostic test ref: {value}")


def _repository_sha() -> str:
    try:
        value = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise LocalVerificationLaneError(
            "local verification repository state is unavailable"
        ) from exc
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise LocalVerificationLaneError(
            "local verification requires an exact repository SHA"
        )
    return value


def _validated_timing_profile(path: Path) -> bytes:
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as exc:
        raise LocalVerificationLaneError(
            "local pytest timing profile is unavailable"
        ) from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_size > MAX_TIMING_PROFILE_BYTES
        or len(payload) > MAX_TIMING_PROFILE_BYTES
    ):
        raise LocalVerificationLaneError("local pytest timing profile is unsafe")
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocalVerificationLaneError(
            "local pytest timing profile is malformed"
        ) from exc
    if not isinstance(decoded, dict):
        raise LocalVerificationLaneError(
            "local pytest timing profile schema is invalid"
        )
    timings = decoded.get("timings")
    if decoded.get("schema_version") != TIMING_SCHEMA_VERSION or not isinstance(
        timings, (dict, list)
    ):
        raise LocalVerificationLaneError(
            "local pytest timing profile schema is invalid"
        )
    entries = (
        timings.items()
        if isinstance(timings, dict)
        else (
            (entry.get("path"), entry.get("seconds"))
            for entry in timings
            if isinstance(entry, dict)
        )
    )
    observed = 0
    for path_ref, seconds in entries:
        if (
            not isinstance(path_ref, str)
            or not path_ref.startswith("tests/")
            or Path(path_ref).is_absolute()
            or ".." in Path(path_ref).parts
            or not isinstance(seconds, (int, float))
            or isinstance(seconds, bool)
            or not math.isfinite(float(seconds))
            or not 0.0 < float(seconds) <= 3_600.0
        ):
            raise LocalVerificationLaneError(
                "local pytest timing profile contains unsafe entries"
            )
        observed += 1
    if observed == 0:
        raise LocalVerificationLaneError("local pytest timing profile is empty")
    return payload


def _publish_timing_profile(source: Path, target: Path) -> None:
    if not target.is_absolute() or target.name in {"", ".", ".."}:
        raise LocalVerificationLaneError(
            "local pytest timing target must be an absolute file"
        )
    payload = _validated_timing_profile(source)
    try:
        parent = target.parent.resolve(strict=True)
        parent_metadata = parent.lstat()
    except OSError as exc:
        raise LocalVerificationLaneError(
            "local pytest timing target parent is unavailable"
        ) from exc
    if not stat.S_ISDIR(parent_metadata.st_mode):
        raise LocalVerificationLaneError(
            "local pytest timing target parent is unsafe"
        )
    resolved_target = parent / target.name
    try:
        current = resolved_target.lstat()
    except FileNotFoundError:
        current = None
    if current is not None and (
        resolved_target.is_symlink()
        or not stat.S_ISREG(current.st_mode)
        or current.st_nlink != 1
        or current.st_uid != os.getuid()
    ):
        raise LocalVerificationLaneError("local pytest timing target is unsafe")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        os.write(descriptor, payload)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, resolved_target)
        directory_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def run_local_lane(
    lane_ref: str,
    *,
    fence_root: Path = DEFAULT_FENCE_ROOT,
    profile_output: Path | None = None,
    diagnostic_root: Path | None = None,
) -> int:
    if lane_ref not in ALLOWED_LANES:
        raise LocalVerificationLaneError("local verification lane is not allowlisted")
    if profile_output is not None and lane_ref != "ci-pytest-shards":
        raise LocalVerificationLaneError(
            "local timing publication is limited to complete pytest"
        )
    repository_sha = _repository_sha()
    parent = Path("/private/tmp")
    if parent.is_symlink() or not parent.is_dir():
        raise LocalVerificationLaneError(
            "local verification temporary boundary is unavailable"
        )
    temp_root = Path(
        tempfile.mkdtemp(
            prefix="uaa-local-verification-",
            dir=parent,
        )
    )
    temp_root.chmod(0o700)
    retained = False
    resolved_diagnostic_root = diagnostic_root or DEFAULT_DIAGNOSTIC_ROOT
    try:
        receipt = run_lane(
            lane_ref,
            repository_sha=repository_sha,
            temp_root=temp_root,
            verification_execution_fence_root=fence_root,
            full_suite_lock_mode="local",
            emit_failure_diagnostic_ref=True,
        )
        if receipt.get("status") != "pass":
            _print_safe_pytest_failure_refs(receipt)
            diagnostic_ref = _retain_diagnostics(
                receipt,
                diagnostic_root=resolved_diagnostic_root,
                lane_ref=lane_ref,
                repository_sha=repository_sha,
            )
            retained = True
            print(f"Retained local diagnostics: {diagnostic_ref}")
            return 1
        if profile_output is not None:
            _publish_timing_profile(
                temp_root / PYTEST_FILE_TIMINGS_NAME,
                profile_output,
            )
    except BaseException:
        if temp_root.exists() and not retained:
            diagnostic_ref = _retain_diagnostics(
                None,
                diagnostic_root=resolved_diagnostic_root,
                lane_ref=lane_ref,
                repository_sha=repository_sha,
            )
            retained = True
            print(f"Retained local diagnostics: {diagnostic_ref}")
        raise
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run one clean exact-SHA local lane through the canonical exclusive "
            "resource fence."
        )
    )
    parser.add_argument("--lane", choices=sorted(ALLOWED_LANES), required=True)
    parser.add_argument("--fence-root", type=Path, default=DEFAULT_FENCE_ROOT)
    parser.add_argument("--profile-output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_local_lane(
            args.lane,
            fence_root=args.fence_root,
            profile_output=args.profile_output,
        )
    except (
        FullSuiteAttemptAlreadyRecordedError,
        FullSuiteLockUnavailableError,
        LocalVerificationLaneError,
        PytestRuntimeUnavailableError,
        VerificationExecutionFenceError,
        VerificationEnvironmentPreflightError,
        OSError,
        ValueError,
    ):
        print(
            "Local verification blocked "
            "(reason-ref:verification:exclusive-resource-unavailable)"
        )
        return 1
    if result == 0:
        print(
            "Local verification passed "
            "(evidence-ref:verification:exact-resource-terminal)"
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
