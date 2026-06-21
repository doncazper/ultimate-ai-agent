from pathlib import Path

from ultimate_ai_agent.core.files import FileKind, FileSensitivity, FileWriteProposal, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def test_diff_preview_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("old\n", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = FileWriteProposal(
        proposal_id="fwp_diff",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="note.txt",
        purpose="diff",
        new_content="new\n",
        expected_existing_hash=manager.build_file_ref("note.txt").content_hash,
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_diff",
    )

    diff = manager.diff_preview(proposal)

    assert "--- note.txt" in diff
    assert "+++ note.txt" in diff
    assert "-old" in diff
    assert "+new" in diff
