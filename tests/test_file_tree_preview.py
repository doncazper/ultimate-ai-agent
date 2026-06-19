from pathlib import Path

from ultimate_ai_agent.core.files import FileTreePreviewRequest, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def actor():
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def tree_request(**kwargs) -> FileTreePreviewRequest:
    return FileTreePreviewRequest(
        request_id="ftp_req",
        run_id="run_123",
        actor_context=actor(),
        purpose="safe workspace tree preview",
        **kwargs,
    )


def test_file_tree_preview_returns_safe_refs_without_raw_paths(tmp_path: Path):
    (tmp_path / "docs" / "nested").mkdir(parents=True)
    (tmp_path / "docs" / "visible.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "docs" / "nested" / "child.md").write_text("child", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    preview = manager.preview_tree(tree_request(root_path="docs", max_depth=2, max_entries=10))
    payload = preview.model_dump_json()

    assert preview.root_ref.startswith("file_tree_")
    assert len(preview.entries) == 3
    assert {entry.entry_type for entry in preview.entries} == {"directory", "file"}
    assert all(entry.entry_ref.startswith("file_tree_") for entry in preview.entries)
    assert all(entry.parent_ref for entry in preview.entries)
    assert "raw_paths_omitted" in preview.redactions_applied
    assert "safe_refs_only" in preview.redactions_applied
    for raw_fragment in ["docs", "visible.txt", "nested", "child.md"]:
        assert raw_fragment not in payload


def test_file_tree_preview_bounds_entries_and_marks_truncated(tmp_path: Path):
    for index in range(5):
        (tmp_path / f"file_{index}.txt").write_text("hello", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    preview = manager.preview_tree(tree_request(max_depth=1, max_entries=2))

    assert len(preview.entries) == 2
    assert preview.truncated is True


def test_file_tree_preview_blocks_unsafe_entries_without_disclosing_names(tmp_path: Path):
    (tmp_path / "safe.txt").write_text("safe", encoding="utf-8")
    (tmp_path / ".env").write_text("SAFE_PLACEHOLDER=1", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    preview = manager.preview_tree(tree_request(max_depth=1, max_entries=10))
    payload = preview.model_dump_json()

    assert len(preview.entries) == 1
    assert preview.blocked_entry_count == 1
    assert "blocked_unsafe_entries" in preview.redactions_applied
    assert ".env" not in payload
    assert "safe.txt" not in payload


def test_file_tree_preview_denies_unsafe_root(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)

    try:
        manager.preview_tree(tree_request(root_path="../outside", max_depth=1))
    except ValueError as exc:
        assert "Path traversal" in str(exc)
    else:
        raise AssertionError("unsafe root path was not denied")
