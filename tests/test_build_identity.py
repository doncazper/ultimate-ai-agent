from __future__ import annotations

from pathlib import Path

from ultimate_ai_agent.core.build_identity import build_identity


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
