from __future__ import annotations

import os
import stat
import subprocess
import time
from pathlib import Path

from scripts.verification.pytest_shard_processes import (
    ProcessCleanupError,
    cancellation_signals,
    installed_signal_handlers,
    process_group_leader_is_terminal_without_reaping,
    spawn_owned_process_group,
    stop_processes,
)


POLL_SECONDS = 0.05
TERMINATION_GRACE_SECONDS = 2.0


class FrontendCommandProcessError(RuntimeError):
    """A frontend command process tree did not settle safely."""


def resolve_installed_frontend_tool(app_root: Path, tool_name: str) -> Path:
    """Resolve one pinned npm-installed executable without package acquisition."""

    if tool_name not in {"playwright", "vite"}:
        raise FrontendCommandProcessError("frontend tool ref is not allowlisted")
    try:
        app = Path(os.path.abspath(app_root)).resolve(strict=True)
        modules = app / "node_modules"
        modules_metadata = modules.lstat()
        bin_directory = modules / ".bin"
        bin_metadata = bin_directory.lstat()
        launcher = bin_directory / tool_name
        launcher_metadata = launcher.lstat()
        resolved = launcher.resolve(strict=True)
        resolved_metadata = resolved.stat()
        if (
            stat.S_ISLNK(modules_metadata.st_mode)
            or not stat.S_ISDIR(modules_metadata.st_mode)
            or stat.S_ISLNK(bin_metadata.st_mode)
            or not stat.S_ISDIR(bin_metadata.st_mode)
            or not stat.S_ISLNK(launcher_metadata.st_mode)
            or not stat.S_ISREG(resolved_metadata.st_mode)
            or launcher_metadata.st_uid != os.geteuid()
            or any(
                metadata.st_uid != os.geteuid() or metadata.st_mode & 0o022
                for metadata in (
                    modules_metadata,
                    bin_metadata,
                    resolved_metadata,
                )
            )
            or os.path.commonpath(
                (os.fspath(resolved), os.fspath(modules))
            )
            != os.fspath(modules)
            or not os.access(resolved, os.X_OK)
        ):
            raise FrontendCommandProcessError(
                "frontend installed tool boundary is unsafe"
            )
    except (OSError, ValueError):
        raise FrontendCommandProcessError(
            "frontend installed tool is unavailable"
        ) from None
    return resolved


def run_frontend_command(
    argv: tuple[str, ...],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> int:
    """Run one frontend command without retaining output or orphaning children."""

    if (
        not argv
        or not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
    ):
        raise FrontendCommandProcessError("frontend command declaration is invalid")
    process: subprocess.Popen[bytes] | None = None
    cleanup_complete = False

    def handle_signal(signum: int, _frame: object) -> None:
        raise KeyboardInterrupt(f"frontend command interrupted by signal {signum}")

    try:
        with installed_signal_handlers(cancellation_signals(), handle_signal):
            process = spawn_owned_process_group(
                argv,
                cwd=cwd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            deadline = time.monotonic() + timeout_seconds
            while True:
                if process_group_leader_is_terminal_without_reaping(process):
                    stop_processes((process,), TERMINATION_GRACE_SECONDS)
                    cleanup_complete = True
                    if not isinstance(process.returncode, int):
                        raise FrontendCommandProcessError(
                            "frontend command terminal status is unavailable"
                        )
                    return process.returncode
                if time.monotonic() >= deadline:
                    raise FrontendCommandProcessError(
                        "frontend command exceeded its bounded timeout"
                    )
                time.sleep(POLL_SECONDS)
    except BaseException as exc:
        if process is not None and not cleanup_complete:
            try:
                stop_processes((process,), TERMINATION_GRACE_SECONDS)
            except ProcessCleanupError as cleanup_exc:
                raise FrontendCommandProcessError(
                    "frontend command cleanup could not be proven"
                ) from cleanup_exc
        if isinstance(exc, (FrontendCommandProcessError, KeyboardInterrupt)):
            raise
        if isinstance(exc, (OSError, ProcessCleanupError)):
            raise FrontendCommandProcessError(
                "frontend command process could not be proven"
            ) from exc
        raise
