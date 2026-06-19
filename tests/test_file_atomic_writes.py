from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.files import (
    FileKind,
    FileOperationStatus,
    FilePatchProposal,
    FileSensitivity,
    FileWriteProposal,
    LocalFileManager,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.time import utc_now


def _actor():
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _patch(manager: LocalFileManager, path: str, content: str, **kwargs) -> FilePatchProposal:
    return FilePatchProposal(
        proposal_id=kwargs.pop("proposal_id", "file-patch-proposal:atomic"),
        run_id="run_123",
        actor_context=_actor(),
        file_ref=kwargs.pop("file_ref", manager.build_file_ref(path).file_ref),
        target_path=path,
        purpose="atomic patch",
        new_content=content,
        expected_existing_hash=kwargs.pop("expected_existing_hash", manager.build_file_ref(path).content_hash),
        file_kind=kwargs.pop("file_kind", FileKind.artifact),
        sensitivity=kwargs.pop("sensitivity", FileSensitivity.project_private),
        idempotency_key=kwargs.pop("idempotency_key", "idem_patch_atomic"),
        audit_ref=kwargs.pop("audit_ref", "file-patch-audit:atomic"),
        **kwargs,
    )


def _approve(manager: LocalFileManager, proposal: FilePatchProposal):
    authority = LocalApprovalAuthority()
    request = manager.approval_request_for_patch(proposal)
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="reviewer_123",
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref="approval:file-patch-atomic",
    )
    return authority, proposal.model_copy(update={"approval_ref": grant.approval_ref})


def test_direct_apply_write_bypass_is_denied(tmp_path: Path):
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

    with pytest.raises(PermissionError, match="exact patch proposal approval"):
        manager.apply_write(proposal)

    assert decision.allowed is True
    assert not (tmp_path / "nested" / "out.txt").exists()


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

    diff_summary = manager.redacted_diff_summary(proposal)

    assert "removed_lines=1" in diff_summary
    assert "added_lines=1" in diff_summary
    assert "raw_diff_omitted=True" in diff_summary
    assert "should-not-appear" not in diff_summary
    assert secret_like_old_content not in diff_summary
    assert "new" not in diff_summary


def test_direct_apply_write_denial_has_no_temp_file(tmp_path: Path):
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

    with pytest.raises(PermissionError, match="shell and subprocess"):
        manager.apply_write(proposal)

    assert target.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".out.txt.*.tmp")) == []


def test_patch_apply_emits_redacted_receipt_with_preimage_and_postimage_refs(tmp_path: Path):
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    authority, proposal = _approve(manager, _patch(manager, "note.txt", "new"))

    result = manager.apply_patch_proposal(proposal, approval_authority=authority)

    assert result.allowed is True
    assert result.status == FileOperationStatus.applied
    assert result.receipt_ref is not None
    assert result.receipt is not None
    assert result.receipt.mutation_performed is True
    assert result.receipt.raw_content_stored is False
    assert result.receipt.raw_path_stored is False
    assert result.preimage_ref.startswith("file_preimage_")
    assert result.postimage_ref.startswith("file_postimage_")
    assert result.receipt.preimage_ref == result.preimage_ref
    assert result.receipt.postimage_ref == result.postimage_ref
    assert "raw_content_omitted" in result.receipt.redactions_applied
    assert "raw_path_omitted" in result.receipt.redactions_applied
    assert "old" not in result.receipt.model_dump_json()
    assert "new" not in result.receipt.model_dump_json()
    assert "note.txt" not in result.receipt.model_dump_json()


def test_patch_apply_failure_returns_safe_receipt_and_preserves_existing_file(
    tmp_path: Path,
    monkeypatch,
):
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    authority, proposal = _approve(manager, _patch(manager, "note.txt", "new"))

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr("ultimate_ai_agent.core.files.manager.os.replace", fail_replace)

    result = manager.apply_patch_proposal(
        proposal,
        approval_authority=authority,
        current_time=utc_now(),
    )

    assert result.allowed is False
    assert result.status == FileOperationStatus.failed
    assert "PATCH_APPLY_FAILED" in result.reason_codes
    assert result.receipt_ref is not None
    assert result.receipt is not None
    assert result.receipt.mutation_performed is False
    assert result.receipt.raw_content_stored is False
    assert result.receipt.raw_path_stored is False
    assert result.preimage_ref.startswith("file_preimage_")
    assert result.postimage_ref.startswith("file_postimage_")
    assert result.preimage_ref.rsplit("_", maxsplit=1)[-1] == result.postimage_ref.rsplit("_", maxsplit=1)[-1]
    assert manager.get_patch_apply_receipt(result.receipt_ref) == result.receipt
    assert target.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".note.txt.*.tmp")) == []
    assert "replace failed" not in result.safe_message
    assert "note.txt" not in result.receipt.model_dump_json()
