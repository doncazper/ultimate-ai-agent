from pathlib import Path

from ultimate_ai_agent.core.files import FileKind, FileSensitivity, FileWriteProposal, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def test_rollback_restores_snapshot(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    old_hash = manager.build_file_ref("note.txt").content_hash
    proposal = FileWriteProposal(
        proposal_id="fwp_rollback",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="note.txt",
        purpose="rollback",
        new_content="new",
        expected_existing_hash=old_hash,
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_rollback",
    )

    change = manager.apply_write(proposal)
    rollback_change = manager.rollback(manager.get_rollback_plan(change.rollback_ref))

    assert target.read_text(encoding="utf-8") == "old"
    assert rollback_change.after_hash == old_hash
