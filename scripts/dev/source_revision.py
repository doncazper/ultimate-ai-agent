from __future__ import annotations

import re
import subprocess
from pathlib import Path


_GIT_SHA = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


def verified_clean_source_commit(repo_root: Path) -> str:
    """Return HEAD only when the exact repo-local tooling worktree is clean."""
    try:
        top_level = subprocess.run(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        head = subprocess.run(
            ("git", "rev-parse", "--verify", "HEAD"),
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = subprocess.run(
            ("git", "status", "--porcelain", "--untracked-files=all"),
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        resolved_top_level = Path(top_level.stdout.strip()).resolve()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise RuntimeError(
            "source revision could not be verified; use a clean exact checkout"
        ) from exc
    commit = head.stdout.strip().lower()
    if (
        top_level.returncode != 0
        or head.returncode != 0
        or status.returncode != 0
        or resolved_top_level != repo_root.resolve()
        or status.stdout.strip()
        or _GIT_SHA.fullmatch(commit) is None
    ):
        raise RuntimeError(
            "source revision could not be verified; use a clean exact checkout"
        )
    return commit
