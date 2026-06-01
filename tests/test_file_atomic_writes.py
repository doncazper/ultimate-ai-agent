from pathlib import Path

from ultimate_ai_agent.core.files import FileKind, FileSensitivity, FileWriteProposal, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def test_apply_write_uses_proposal_and_changes_file_content(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = FileWriteProposal(
        proposal_id="fwp_atomic",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="nested/out.txt",
        purpose="atomic write",
        new_content="hello",
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_atomic",
    )

    decision = manager.propose_write(proposal)
    change = manager.apply_write(proposal)

    assert decision.allowed is True
    assert (tmp_path / "nested" / "out.txt").read_text(encoding="utf-8") == "hello"
    assert change.before_hash is None
    assert change.after_hash is not None
    assert change.rollback_ref is not None
