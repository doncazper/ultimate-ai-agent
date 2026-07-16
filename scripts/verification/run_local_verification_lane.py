#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import stat
import subprocess
import tempfile
from pathlib import Path

from scripts.verification.ci_fallback_storage import (
    FullSuiteAttemptAlreadyRecordedError,
    FullSuiteLockUnavailableError,
)
from scripts.verification.pytest_shard_artifacts import TIMING_SCHEMA_VERSION
from scripts.verification.run_ci_lane import (
    PYTEST_FILE_TIMINGS_NAME,
    PytestRuntimeUnavailableError,
    run_lane,
)
from scripts.verification.verification_execution_identity import (
    VerificationExecutionFenceError,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FENCE_ROOT = Path("/private/tmp/uaa-verification-execution-fence-v2")
ALLOWED_LANES = {
    "ci-pytest-shards",
    "ci-control-center-frontend",
}
MAX_TIMING_PROFILE_BYTES = 4 * 1024 * 1024


class LocalVerificationLaneError(RuntimeError):
    """A local exclusive lane could not execute or publish safe evidence."""


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
    with tempfile.TemporaryDirectory(
        prefix="uaa-local-verification-",
        dir=parent,
    ) as rendered:
        temp_root = Path(rendered)
        temp_root.chmod(0o700)
        receipt = run_lane(
            lane_ref,
            repository_sha=repository_sha,
            temp_root=temp_root,
            verification_execution_fence_root=fence_root,
            full_suite_lock_mode="local",
        )
        if receipt.get("status") != "pass":
            return 1
        if profile_output is not None:
            _publish_timing_profile(
                temp_root / PYTEST_FILE_TIMINGS_NAME,
                profile_output,
            )
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
