from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import tempfile
from pathlib import Path


MINIMUM_TEMP_FREE_BYTES = 1024 * 1024 * 1024
MATRIX_RUNTIME_MARKER = Path(
    "integrations/matrix-client-adapter/node_modules/matrix-js-sdk/package.json"
)
FRONTEND_RUNTIME_MARKERS = (
    Path("apps/control-center/node_modules/typescript/bin/tsc"),
    Path("apps/control-center/node_modules/vitest/vitest.mjs"),
    Path("apps/control-center/node_modules/vite/bin/vite.js"),
)
FRONTEND_RUNTIME_MARKER = FRONTEND_RUNTIME_MARKERS[0]


class VerificationEnvironmentPreflightError(RuntimeError):
    """A required runtime or local resource is unavailable before admission."""

    def __init__(self, reason_ref: str) -> None:
        self.reason_ref = reason_ref
        super().__init__(reason_ref)


def _require_regular_runtime_file(path: Path, *, reason_ref: str) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise VerificationEnvironmentPreflightError(reason_ref) from None
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or info.st_nlink != 1
    ):
        raise VerificationEnvironmentPreflightError(reason_ref)


def validate_lane_environment(
    repo: Path,
    temp_root: Path,
    *,
    lane_ref: str,
) -> tuple[str, ...]:
    """Fail before durable admission when a lane cannot actually start."""

    observations: list[str] = []
    try:
        usage = shutil.disk_usage(temp_root)
    except OSError:
        raise VerificationEnvironmentPreflightError(
            "reason-ref:verification-preflight:temp-capacity-unavailable"
        ) from None
    if usage.free < MINIMUM_TEMP_FREE_BYTES:
        raise VerificationEnvironmentPreflightError(
            "reason-ref:verification-preflight:temp-capacity-insufficient"
        )
    try:
        descriptor, probe_name = tempfile.mkstemp(
            prefix=".uaa-verification-preflight-",
            dir=temp_root,
        )
        os.fchmod(descriptor, 0o600)
        os.close(descriptor)
        Path(probe_name).unlink()
    except OSError:
        raise VerificationEnvironmentPreflightError(
            "reason-ref:verification-preflight:temp-write-unavailable"
        ) from None
    observations.append("preflight-ref:temp-capacity-and-write-ready")

    if lane_ref == "ci-pytest-shards":
        if importlib.util.find_spec("pytest") is None:
            raise VerificationEnvironmentPreflightError(
                "reason-ref:verification-preflight:pytest-runtime-unavailable"
            )
        if shutil.which("node") is None:
            raise VerificationEnvironmentPreflightError(
                "reason-ref:verification-preflight:node-runtime-unavailable"
            )
        if shutil.which("npm") is None:
            raise VerificationEnvironmentPreflightError(
                "reason-ref:verification-preflight:npm-runtime-unavailable"
            )
        _require_regular_runtime_file(
            repo / MATRIX_RUNTIME_MARKER,
            reason_ref=(
                "reason-ref:verification-preflight:matrix-runtime-unavailable"
            ),
        )
        observations.extend(
            (
                "preflight-ref:pytest-runtime-ready",
                "preflight-ref:matrix-runtime-ready",
            )
        )
    elif lane_ref == "ci-control-center-frontend":
        if shutil.which("node") is None:
            raise VerificationEnvironmentPreflightError(
                "reason-ref:verification-preflight:node-runtime-unavailable"
            )
        if shutil.which("npm") is None:
            raise VerificationEnvironmentPreflightError(
                "reason-ref:verification-preflight:npm-runtime-unavailable"
            )
        for marker in FRONTEND_RUNTIME_MARKERS:
            _require_regular_runtime_file(
                repo / marker,
                reason_ref=(
                    "reason-ref:verification-preflight:frontend-runtime-unavailable"
                ),
            )
        observations.append("preflight-ref:frontend-runtime-ready")

    return tuple(observations)
