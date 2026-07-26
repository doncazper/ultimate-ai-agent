from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from ultimate_ai_agent.core.build_identity import (
    build_identity,
)
from scripts.dev.source_revision import verified_clean_source_commit


def test_build_identity_prefers_explicit_release_binding(tmp_path: Path) -> None:
    commit = "a" * 40
    identity = build_identity(
        env={
            "UAA_BUILD_ID": "build-ref:uaa:release:sample",
            "UAA_BUILD_COMMIT": commit,
        },
        repo_root=tmp_path,
    )

    assert identity.build_id == "build-ref:uaa:release:sample"
    assert identity.commit_ref == f"commit-ref:git:{commit}"
    assert identity.source_revision_bound is True
    assert identity.upgrade_compatibility.automatic_unknown_schema_upgrade is False


def test_build_identity_rejects_unsafe_environment_values(tmp_path: Path) -> None:
    identity = build_identity(
        env={
            "UAA_BUILD_ID": "/private/raw/path",
            "UAA_BUILD_COMMIT": "not-a-commit",
        },
        repo_root=tmp_path,
    )

    assert identity.build_id.endswith(":source-unbound")
    assert identity.commit_ref == "commit-ref:git:unbound"
    assert identity.source_revision_bound is False


def test_build_identity_rejects_unscoped_safe_shaped_identifier(tmp_path: Path) -> None:
    identity = build_identity(
        env={"UAA_BUILD_ID": "plausible-but-unscoped"},
        repo_root=tmp_path,
    )

    assert identity.build_id.endswith(":source-unbound")


def test_build_identity_does_not_trust_mutable_checkout_head(
    tmp_path: Path,
) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("a" * 40 + "\n", encoding="utf-8")

    identity = build_identity(env={}, repo_root=tmp_path)

    assert identity.commit_ref == "commit-ref:git:unbound"
    assert identity.source_revision_bound is False


def test_verified_clean_source_commit_accepts_only_exact_clean_git_root(
    tmp_path: Path,
) -> None:
    subprocess.run(("git", "init"), cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ("git", "config", "user.email", "uaa-test@example.invalid"),
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ("git", "config", "user.name", "UAA Test"),
        cwd=tmp_path,
        check=True,
    )
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("bound\n", encoding="utf-8")
    subprocess.run(("git", "add", "tracked.txt"), cwd=tmp_path, check=True)
    subprocess.run(
        ("git", "commit", "-m", "test: bind clean source"),
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    expected = subprocess.run(
        ("git", "rev-parse", "--verify", "HEAD"),
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert verified_clean_source_commit(tmp_path) == expected

    tracked.write_text("dirty\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="clean exact checkout"):
        verified_clean_source_commit(tmp_path)
