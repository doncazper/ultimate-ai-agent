#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verification.ci_command_manifest import visual_scope_for_paths  # noqa: E402

SHA = re.compile(r"^[0-9a-f]{40}$")
MAX_DIFF_BYTES = 4 * 1024 * 1024
MAX_PATHS = 4096
MAX_GITHUB_OUTPUT_BYTES = 1024 * 1024


def resolve_visual_scope(repo: Path, base_sha: str, repository_sha: str) -> str:
    if SHA.fullmatch(base_sha) is None or SHA.fullmatch(repository_sha) is None:
        raise ValueError("exact comparison SHAs are required")
    completed = subprocess.run(
        ("git", "diff", "--no-renames", "--name-only", "-z", base_sha, repository_sha, "--"),
        cwd=repo,
        check=True,
        capture_output=True,
        timeout=30,
    )
    if len(completed.stdout) > MAX_DIFF_BYTES:
        raise ValueError("changed-path evidence exceeds its bound")
    raw_paths = completed.stdout.split(b"\0")
    if raw_paths and raw_paths[-1] == b"":
        raw_paths.pop()
    if len(raw_paths) > MAX_PATHS:
        raise ValueError("changed-path evidence exceeds its count bound")
    paths: list[str] = []
    for raw_path in raw_paths:
        try:
            path = raw_path.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ValueError("changed-path evidence is not canonical UTF-8") from exc
        if not path or "\n" in path or "\r" in path or "\0" in path:
            raise ValueError("changed-path evidence is unsafe")
        paths.append(path)
    return visual_scope_for_paths(tuple(paths))


def append_scope_output(path: Path, scope: str) -> None:
    if scope not in {"affected", "not_affected"}:
        raise ValueError("resolved visual scope must be exact")
    flags = os.O_WRONLY | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) & 0o077
            or info.st_size > MAX_GITHUB_OUTPUT_BYTES - 32
        ):
            raise ValueError("GitHub output path is unsafe")
        os.write(descriptor, f"visual_scope={scope}\n".encode("ascii"))
        os.fsync(descriptor)
        final_info = os.fstat(descriptor)
        if (
            final_info.st_dev != info.st_dev
            or final_info.st_ino != info.st_ino
            or final_info.st_uid != info.st_uid
            or final_info.st_size > MAX_GITHUB_OUTPUT_BYTES
        ):
            raise ValueError("GitHub output path changed during append")
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve exact CI visual scope")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--github-output-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        scope = resolve_visual_scope(args.repo.resolve(), args.base_sha, args.sha)
        append_scope_output(args.github_output_file, scope)
    except (OSError, subprocess.SubprocessError, ValueError):
        print("CI visual scope rejected (reason-ref:ci-evidence:visual-scope-invalid)", file=sys.stderr)
        return 1
    print(f"PASS: exact CI visual scope is {scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
