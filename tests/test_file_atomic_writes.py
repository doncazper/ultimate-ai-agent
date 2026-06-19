from pathlib import Path

import pytest

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


def test_apply_write_records_pre_write_diff_summary(tmp_path: Path):
    target = tmp_path / "out.txt"
    secret_like_old_content = "token=should-not-appear\n"
    target.write_text(secret_like_old_content, encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = FileWriteProposal(
        proposal_id="fwp_atomic_diff",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="out.txt",
        purpose="atomic write diff",
        new_content="new\n",
        expected_existing_hash=manager.build_file_ref("out.txt").content_hash,
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_atomic_diff",
    )

    change = manager.apply_write(proposal)

    assert "removed_lines=1" in change.diff_summary
    assert "added_lines=1" in change.diff_summary
    assert "raw_diff_omitted=True" in change.diff_summary
    assert "should-not-appear" not in change.diff_summary
    assert secret_like_old_content not in change.diff_summary
    assert "new" not in change.diff_summary


def test_apply_write_cleans_temp_file_when_replace_fails(tmp_path: Path, monkeypatch):
    target = tmp_path / "out.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    proposal = FileWriteProposal(
        proposal_id="fwp_atomic_failure",
        run_id="run_123",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        target_path="out.txt",
        purpose="atomic write failure",
        new_content="new",
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        idempotency_key="idem_atomic_failure",
    )

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr("ultimate_ai_agent.core.files.manager.os.replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        manager.apply_write(proposal)

    assert target.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".out.txt.*.tmp")) == []
