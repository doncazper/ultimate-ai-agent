from pathlib import Path

from ultimate_ai_agent.core.files import FileKind, FileSensitivity, FileWriteProposal, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def test_private_key_write_is_blocked(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = FileWriteProposal(
        proposal_id="fwp_private_key",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="id_rsa",
        purpose="blocked",
        new_content="-----BEGIN OPENSSH PRIVATE KEY-----",
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.credential_secret,
        idempotency_key="idem_key",
    )

    decision = manager.propose_write(proposal)

    assert decision.allowed is False
    assert "FILE_PATH_BLOCKED" in decision.reason_codes or "SECRET_CONTENT_BLOCKED" in decision.reason_codes
