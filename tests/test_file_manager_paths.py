from pathlib import Path

import pytest

from ultimate_ai_agent.core.files import LocalFileManager


def test_file_manager_blocks_absolute_and_traversal_paths(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)

    with pytest.raises(ValueError, match="absolute"):
        manager.normalize_path("/tmp/outside.txt")

    with pytest.raises(ValueError, match="traversal"):
        manager.normalize_path("../outside.txt")


@pytest.mark.parametrize(
    "path,reason",
    [
        ("docs/%2e%2e/outside.txt", "Encoded unsafe"),
        ("C:/Users/secret.txt", "Drive-qualified"),
        ("~/secret.txt", "Home-relative"),
        ("docs/*.txt", "Glob-style"),
        ("docs/.git/config", "hidden"),
        ("docs/api_key='abcdefghijklmnop'.txt", "Secret-like"),
        ("docs\\note.txt", "Backslash"),
    ],
)
def test_file_manager_blocks_ambiguous_and_secret_like_paths(tmp_path: Path, path: str, reason: str):
    manager = LocalFileManager(workspace_root=tmp_path)

    with pytest.raises(ValueError, match=reason):
        manager.normalize_path(path)


def test_file_manager_constructor_does_not_create_workspace_root(tmp_path: Path):
    workspace = tmp_path / "not-created-by-constructor"

    LocalFileManager(workspace_root=workspace)

    assert not workspace.exists()


def test_file_manager_builds_ref_inside_workspace(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)
    path = tmp_path / "docs" / "note.md"
    path.parent.mkdir()
    path.write_text("hello", encoding="utf-8")

    ref = manager.build_file_ref("docs/note.md")

    assert ref.path == "docs/note.md"
    assert ref.size_bytes == 5
    assert ref.content_hash is not None
