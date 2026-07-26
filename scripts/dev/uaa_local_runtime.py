#!/usr/bin/env python3
"""Operate the loopback-only Docker package from an exact clean source tree."""
from __future__ import annotations

import argparse
import os
import secrets
import subprocess
import sys
import urllib.parse
import webbrowser
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


def _write_private_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    path.chmod(0o600)


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
    _write_private_text(SECRET_FILE, local_bearer)
    _write_private_text(SOURCE_COMMIT_FILE, commit)
    _run_compose(["up", "--build", "--detach", "--wait"], commit=commit)
    port = _compose_env(commit)["UAA_LOCAL_RUNTIME_CONTROL_CENTER_PORT"]
    session_url = (
        f"http://127.0.0.1:{port}/today"
        f"#uaa-session-bearer={urllib.parse.quote(local_bearer, safe='')}"
    )
    browser_opened = webbrowser.open(session_url)
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
