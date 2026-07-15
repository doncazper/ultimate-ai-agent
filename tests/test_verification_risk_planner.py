from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.verification.plan_affected_verification import (
    _head_path_is_unsafe,
    _validate_comparison,
    _validate_repository,
    parse_name_status,
)
from scripts.verification.verification_risk import ChangeKind


SHA = "a" * 40


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "verification@example.invalid")
    _git(repo, "config", "user.name", "Verification Fixture")
    return repo


def test_name_status_parser_preserves_change_kinds_and_both_rename_paths() -> None:
    records = parse_name_status(
        b"M\0src/module.py\0A\0docs/new.md\0R100\0docs/old.md\0docs/moved.md\0"
    )

    assert records[0].kind is ChangeKind.MODIFIED
    assert records[1].kind is ChangeKind.ADDED
    assert records[2].kind is ChangeKind.RENAMED
    assert records[2].path_refs == ("docs/old.md", "docs/moved.md")


@pytest.mark.parametrize(
    "payload",
    (
        b"Q\0path.py\0",
        b"Rxx\0old.py\0new.py\0",
        b"R100\0old.py\0",
        b"M\0../escape.py\0",
        b"M\0bad\npath.py\0",
        b"M\0\xff\0",
    ),
)
def test_name_status_parser_rejects_unknown_malformed_or_unsafe_records(
    payload: bytes,
) -> None:
    with pytest.raises(ValueError):
        parse_name_status(payload)


def test_repository_preflight_requires_exact_clean_head(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    tracked = repo / "tracked.txt"
    tracked.write_text("safe\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "fixture")
    head = _git(repo, "rev-parse", "HEAD")

    _validate_repository(repo, head_sha=head)
    tracked.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="VERIFICATION_WORKTREE_NOT_CLEAN"):
        _validate_repository(repo, head_sha=head)
    with pytest.raises(ValueError, match="VERIFICATION_SHA_INVALID"):
        _validate_repository(repo, head_sha="HEAD")


def test_comparison_requires_a_distinct_ancestor_unless_force_full(
    tmp_path: Path,
) -> None:
    repo = _repository(tmp_path)
    tracked = repo / "tracked.txt"
    tracked.write_text("first\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "first")
    base = _git(repo, "rev-parse", "HEAD")
    tracked.write_text("second\n", encoding="utf-8")
    _git(repo, "commit", "-am", "second")
    head = _git(repo, "rev-parse", "HEAD")

    _validate_comparison(
        repo,
        base_sha=base,
        head_sha=head,
        force_full=False,
    )
    with pytest.raises(ValueError, match="VERIFICATION_BASE_EQUALS_HEAD"):
        _validate_comparison(
            repo,
            base_sha=head,
            head_sha=head,
            force_full=False,
        )
    _validate_comparison(
        repo,
        base_sha=head,
        head_sha=head,
        force_full=True,
    )
    with pytest.raises(ValueError, match="VERIFICATION_BASE_NOT_ANCESTOR"):
        _validate_comparison(
            repo,
            base_sha=head,
            head_sha=base,
            force_full=False,
        )


def test_head_tree_and_worktree_symlinks_are_unsafe(tmp_path: Path) -> None:
    repo = _repository(tmp_path)
    target = repo / "target.txt"
    target.write_text("safe\n", encoding="utf-8")
    link = repo / "linked.txt"
    link.symlink_to(target.name)
    _git(repo, "add", "target.txt", "linked.txt")
    _git(repo, "commit", "-m", "fixture")
    head = _git(repo, "rev-parse", "HEAD")

    assert (
        _head_path_is_unsafe(
            repo,
            head_sha=head,
            path_ref="target.txt",
        )
        is False
    )
    assert (
        _head_path_is_unsafe(
            repo,
            head_sha=head,
            path_ref="linked.txt",
        )
        is True
    )
    assert (
        _head_path_is_unsafe(
            repo,
            head_sha=head,
            path_ref="missing.txt",
        )
        is True
    )
