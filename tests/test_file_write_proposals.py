from pathlib import Path

from ultimate_ai_agent.core.files import (
    FileKind,
    FileManagerPolicy,
    FileSensitivity,
    FileWriteProposal,
    FileOperationStatus,
    LocalFileManager,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def actor():
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def proposal(path: str, content: str, **kwargs) -> FileWriteProposal:
    return FileWriteProposal(
        proposal_id=f"fwp_{path.replace('/', '_').replace('.', '_')}",
        run_id="run_123",
        actor_context=actor(),
        target_path=path,
        purpose="test write",
        new_content=content,
        file_kind=kwargs.pop("file_kind", FileKind.artifact),
        sensitivity=kwargs.pop("sensitivity", FileSensitivity.project_private),
        idempotency_key=kwargs.pop("idempotency_key", "idem_123"),
        **kwargs,
    )


def test_write_proposal_requires_idempotency_key(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)
    decision = manager.propose_write(proposal("out.txt", "hello", idempotency_key=""))

    assert decision.allowed is False
    assert decision.status == FileOperationStatus.blocked
    assert "IDEMPOTENCY_KEY_REQUIRED" in decision.reason_codes


def test_write_proposal_blocks_secret_content_and_secret_paths(tmp_path: Path):
    manager = LocalFileManager(workspace_root=tmp_path)

    secret_content = manager.propose_write(proposal("out.txt", "api_key='abcdefghijklmnop'"))
    env_file = manager.propose_write(proposal(".env", "SAFE_PLACEHOLDER=1"))

    assert secret_content.allowed is False
    assert "SECRET_CONTENT_BLOCKED" in secret_content.reason_codes
    assert env_file.allowed is False
    assert "FILE_PATH_BLOCKED" in env_file.reason_codes


def test_canonical_overwrite_requires_expected_hash(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "canonical.md").write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    decision = manager.propose_write(
        proposal("docs/canonical.md", "new", file_kind=FileKind.canonical)
    )

    assert decision.allowed is False
    assert "EXPECTED_HASH_REQUIRED" in decision.reason_codes


def test_expected_hash_mismatch_blocks_write(tmp_path: Path):
    (tmp_path / "out.txt").write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    decision = manager.propose_write(proposal("out.txt", "new", expected_existing_hash="wrong"))

    assert decision.allowed is False
    assert "EXPECTED_HASH_MISMATCH" in decision.reason_codes


def test_strict_contract_policy_blocks_unlisted_update_path(tmp_path: Path):
    manager = LocalFileManager(
        workspace_root=tmp_path,
        policy=FileManagerPolicy(strict_contract_paths=True, allowed_update_paths=["allowed.txt"]),
    )

    decision = manager.propose_write(proposal("blocked.txt", "new"))

    assert decision.allowed is False
    assert "CONTRACT_FILE_NOT_ALLOWED" in decision.reason_codes
