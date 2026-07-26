#!/usr/bin/env python3
"""Operate the loopback-only Docker package from an exact clean source tree."""
from __future__ import annotations

import argparse
import os
import secrets
import stat
import subprocess
import sys
import urllib.parse
import webbrowser
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.dev.source_revision import verified_clean_source_commit  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "packaging" / "local-runtime" / "compose.yaml"
STATE_DIR = ROOT / ".uaa" / "local-runtime"
SECRET_FILE = STATE_DIR / "uaa_local_runtime_secret"
SOURCE_COMMIT_FILE = STATE_DIR / "verified_source_commit"
DEFAULT_API_PORT = "8000"
DEFAULT_CONTROL_CENTER_PORT = "5173"


@dataclass(frozen=True)
class _PrivateFileSnapshot:
    existed: bool
    content: bytes = b""
    mode: int = 0o600


def _open_private_parent(path: Path, *, create: bool) -> int:
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    try:
        parent_stat = path.parent.lstat()
    except FileNotFoundError:
        raise
    if not stat.S_ISDIR(parent_stat.st_mode):
        raise OSError("local runtime state parent is not a directory")
    flags = os.O_RDONLY
    flags |= getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    return os.open(path.parent, flags)


def _write_private_bytes(path: Path, content: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing_stat = path.lstat()
    except FileNotFoundError:
        existing_stat = None
    if existing_stat is not None and not stat.S_ISREG(existing_stat.st_mode):
        raise OSError("local runtime state path is not a regular file")

    parent_fd = _open_private_parent(path, create=False)
    file_fd = -1
    try:
        flags = os.O_WRONLY | os.O_CREAT
        flags |= getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        file_fd = os.open(path.name, flags, mode, dir_fd=parent_fd)
        opened_stat = os.fstat(file_fd)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise OSError("local runtime state path is not a regular file")
        if existing_stat is not None and (
            opened_stat.st_dev,
            opened_stat.st_ino,
        ) != (
            existing_stat.st_dev,
            existing_stat.st_ino,
        ):
            raise OSError("local runtime state path changed during access")
        os.ftruncate(file_fd, 0)
        os.fchmod(file_fd, mode)
        view = memoryview(content)
        while view:
            written = os.write(file_fd, view)
            if written <= 0:
                raise OSError("local runtime state write failed")
            view = view[written:]
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        os.close(parent_fd)


def _write_private_text(path: Path, value: str) -> None:
    _write_private_bytes(path, (value + "\n").encode(), mode=0o600)


def _snapshot_private_file(path: Path) -> _PrivateFileSnapshot:
    try:
        file_stat = path.lstat()
    except FileNotFoundError:
        return _PrivateFileSnapshot(existed=False)
    if not stat.S_ISREG(file_stat.st_mode):
        raise OSError("local runtime state path is not a regular file")

    parent_fd = _open_private_parent(path, create=False)
    file_fd = -1
    try:
        flags = os.O_RDONLY
        flags |= getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        file_fd = os.open(path.name, flags, dir_fd=parent_fd)
        opened_stat = os.fstat(file_fd)
        if not stat.S_ISREG(opened_stat.st_mode) or (
            opened_stat.st_dev,
            opened_stat.st_ino,
        ) != (
            file_stat.st_dev,
            file_stat.st_ino,
        ):
            raise OSError("local runtime state path changed during access")
        with os.fdopen(file_fd, "rb", closefd=False) as handle:
            content = handle.read()
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        os.close(parent_fd)
    return _PrivateFileSnapshot(
        existed=True,
        content=content,
        mode=file_stat.st_mode & 0o777,
    )


def _unlink_private_path(path: Path) -> None:
    try:
        parent_fd = _open_private_parent(path, create=False)
    except FileNotFoundError:
        return
    try:
        try:
            os.unlink(path.name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
    finally:
        os.close(parent_fd)


def _restore_private_files(
    snapshots: tuple[tuple[Path, _PrivateFileSnapshot], ...],
) -> None:
    restore_failed = False
    for path, snapshot in snapshots:
        try:
            if not snapshot.existed:
                _unlink_private_path(path)
                continue
            _write_private_bytes(path, snapshot.content, mode=snapshot.mode)
        except OSError:
            restore_failed = True
    if restore_failed:
        raise RuntimeError("local runtime state restoration failed")


def _compose_env(commit: str) -> dict[str, str]:
    return {
        **os.environ,
        "UAA_BUILD_COMMIT": commit,
        "UAA_LOCAL_RUNTIME_VERIFIED_SOURCE": "verified-clean-source:v1",
        "UAA_LOCAL_RUNTIME_API_PORT": os.environ.get(
            "UAA_LOCAL_RUNTIME_API_PORT", DEFAULT_API_PORT
        ),
        "UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT": os.environ.get(
            "UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT",
            DEFAULT_CONTROL_CENTER_PORT,
        ),
    }


def _run_compose(arguments: list[str], *, commit: str) -> None:
    completed = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), *arguments],
        cwd=ROOT,
        env=_compose_env(commit),
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if completed.returncode != 0:
        raise RuntimeError("local runtime compose command failed")


def _verified_up() -> None:
    commit = verified_clean_source_commit(ROOT)
    local_bearer = secrets.token_urlsafe(48)
    snapshots = tuple(
        (path, _snapshot_private_file(path))
        for path in (SECRET_FILE, SOURCE_COMMIT_FILE)
    )
    compose_attempted = False
    try:
        _write_private_text(SECRET_FILE, local_bearer)
        _write_private_text(SOURCE_COMMIT_FILE, commit)
        compose_attempted = True
        _run_compose(["up", "--build", "--detach", "--wait"], commit=commit)
    except BaseException as startup_error:
        cleanup_failed = False
        if compose_attempted:
            try:
                _run_compose(["down", "--remove-orphans"], commit=commit)
            except BaseException:
                cleanup_failed = True
        try:
            _restore_private_files(snapshots)
        except RuntimeError as restore_error:
            raise restore_error from startup_error
        if cleanup_failed:
            raise RuntimeError("local runtime partial startup cleanup failed") from (
                startup_error
            )
        raise
    port = _compose_env(commit)["UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT"]
    session_url = (
        f"http://127.0.0.1:{port}/today"
        f"#uaa-session-bearer={urllib.parse.quote(local_bearer, safe='')}"
    )
    try:
        browser_opened = webbrowser.open(session_url)
    except (OSError, webbrowser.Error):
        browser_opened = False
    print("OK: local runtime started from a verified clean source revision")
    if not browser_opened:
        print(
            "WARNING: local runtime is healthy but the browser handoff was unavailable",
            file=sys.stderr,
        )


def _down() -> None:
    try:
        commit = SOURCE_COMMIT_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        commit = "0" * 40
    if len(commit) != 40 or any(value not in "0123456789abcdef" for value in commit):
        commit = "0" * 40
    _run_compose(["down", "--remove-orphans"], commit=commit)
    print("OK: local runtime stopped")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("up")
    subparsers.add_parser("down")
    args = parser.parse_args(argv)
    try:
        if args.command == "up":
            _verified_up()
        else:
            _down()
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print("ERROR: local runtime operation failed closed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
