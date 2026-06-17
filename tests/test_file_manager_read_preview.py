import hashlib
from pathlib import Path

from ultimate_ai_agent.core.files import FileReadRequest, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.memory import MemorySourceRef


def actor():
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def test_read_preview_truncates_and_redacts_secret_like_content(tmp_path: Path):
    (tmp_path / "notes.txt").write_text("prefix api_key='abcdefghijklmnop' suffix", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    preview = manager.read_preview(
        FileReadRequest(
            request_id="frr_123",
            run_id="run_123",
            actor_context=actor(),
            path="notes.txt",
            purpose="preview",
            max_bytes=18,
        )
    )

    assert preview.truncated is True
    assert "abcdefghijklmnop" not in preview.text_preview
    assert "secret_value" in preview.redactions_applied


def test_read_preview_path_can_be_used_as_memory_source_locator(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text("hello", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    preview = manager.read_preview(
        FileReadRequest(
            request_id="frr_source",
            run_id="run_123",
            actor_context=actor(),
            path="docs/note.md",
            purpose="source link",
            max_bytes=100,
        )
    )
    source = MemorySourceRef(
        source_id=preview.preview_id,
        source_type="file_preview",
        file_ref=preview.path,
        locator=f"path:{preview.path}",
    )

    assert source.file_ref == "docs/note.md"
    assert source.locator == "path:docs/note.md"


def test_read_preview_reports_full_metadata_with_bounded_preview(tmp_path: Path):
    content = "first line\n" + ("x" * 9000)
    (tmp_path / "large.txt").write_text(content, encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    preview = manager.read_preview(
        FileReadRequest(
            request_id="frr_large",
            run_id="run_123",
            actor_context=actor(),
            path="large.txt",
            purpose="large preview",
            max_bytes=12,
        )
    )

    assert preview.truncated is True
    assert preview.size_bytes == len(content.encode("utf-8"))
    assert preview.content_hash == hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert preview.text_preview == content.encode("utf-8")[:12].decode("utf-8")
