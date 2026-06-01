from pathlib import Path

import pytest

from ultimate_ai_agent.core.files import LocalFileManager


def test_file_manager_blocks_absolute_and_traversal_paths(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)

    with pytest.raises(ValueError, match="absolute"):
        manager.normalize_path("/tmp/outside.txt")

    with pytest.raises(ValueError, match="traversal"):
        manager.normalize_path("../outside.txt")


def test_file_manager_builds_ref_inside_workspace(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)
    path = tmp_path / "docs" / "note.md"
    path.parent.mkdir()
    path.write_text("hello", encoding="utf-8")

    ref = manager.build_file_ref("docs/note.md")

    assert ref.path == "docs/note.md"
    assert ref.size_bytes == 5
    assert ref.content_hash is not None
