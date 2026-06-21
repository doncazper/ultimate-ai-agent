from typing import Any
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.files import (
    FileKind,
    FileOperationStatus,
    FilePatchProposal,
    FileSensitivity,
    LocalFileManager,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource


def _actor() -> Any:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def _patch(manager: LocalFileManager, target_path: str, content: str, **kwargs: Any) -> FilePatchProposal:
    return FilePatchProposal(
        proposal_id=kwargs.pop("proposal_id", "file-patch-proposal:rollback"),
        run_id="run_123",
        actor_context=_actor(),
        file_ref=kwargs.pop("file_ref", manager.build_file_ref(target_path).file_ref),
        target_path=target_path,
        purpose="rollback receipt patch",
        new_content=content,
        expected_existing_hash=kwargs.pop(
            "expected_existing_hash",
            manager.build_file_ref(target_path).content_hash,
        ),
        file_kind=kwargs.pop("file_kind", FileKind.artifact),
        sensitivity=kwargs.pop("sensitivity", FileSensitivity.project_private),
        idempotency_key=kwargs.pop("idempotency_key", "idem_patch_rollback"),
        audit_ref=kwargs.pop("audit_ref", "file-patch-audit:rollback"),
        **kwargs,
    )


def _approve(manager: LocalFileManager, proposal: FilePatchProposal) -> tuple[Any, ...]:
    authority = LocalApprovalAuthority()
    request = manager.approval_request_for_patch(proposal)
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="reviewer_123",
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref="approval:file-patch-rollback",
    )
    return authority, proposal.model_copy(update={"approval_ref": grant.approval_ref})


def _approve_rollback(manager: LocalFileManager, rollback_plan: Any, *, approval_ref: str = "approval:file-rollback-primary") -> tuple[Any, ...]:
    authority = LocalApprovalAuthority()
    request = manager.approval_request_for_rollback(
        rollback_plan,
        run_id="run_123",
        actor_context=_actor(),
    )
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="reviewer_123",
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref=approval_ref,
    )
    return authority, grant.approval_ref


def test_direct_rollback_bypass_is_denied(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    authority, proposal = _approve(manager, _patch(manager, "note.txt", "new"))
    result = manager.apply_patch_proposal(proposal, approval_authority=authority)

    with pytest.raises(PermissionError, match="exact rollback approval"):
        manager.rollback(manager.get_rollback_plan(result.rollback_ref))

    assert target.read_text(encoding="utf-8") == "new"


def test_rollback_with_receipt_requires_exact_approval(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    authority, proposal = _approve(manager, _patch(manager, "note.txt", "new"))
    result = manager.apply_patch_proposal(proposal, approval_authority=authority)

    receipt = manager.rollback_with_receipt(
        manager.get_rollback_plan(result.rollback_ref),
        audit_ref="file-rollback-audit:missing-approval",
        idempotency_key="idem_rollback_missing_approval",
    )

    assert receipt.status == FileOperationStatus.blocked
    assert receipt.rollback_performed is False
    assert "ROLLBACK_APPROVAL_REQUIRED" in receipt.reason_codes
    assert target.read_text(encoding="utf-8") == "new"


def test_rollback_with_receipt_rejects_wrong_scope_approval(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    authority, proposal = _approve(manager, _patch(manager, "note.txt", "new"))
    result = manager.apply_patch_proposal(proposal, approval_authority=authority)

    receipt = manager.rollback_with_receipt(
        manager.get_rollback_plan(result.rollback_ref),
        audit_ref="file-rollback-audit:wrong-scope",
        idempotency_key="idem_rollback_wrong_scope",
        approval_ref=proposal.approval_ref,
        approval_authority=authority,
        run_id="run_123",
        actor_context=_actor(),
    )

    assert receipt.status == FileOperationStatus.blocked
    assert receipt.rollback_performed is False
    assert "ROLLBACK_APPROVAL_DENIED" in receipt.reason_codes
    assert "APPROVAL_SUBJECT_MISMATCH" in receipt.reason_codes
    assert target.read_text(encoding="utf-8") == "new"


def test_patch_rollback_with_receipt_restores_snapshot_without_raw_data(tmp_path: Path) -> None:
    target = tmp_path / "artifact.txt"
    target.write_text("previous-private-text", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    authority, proposal = _approve(manager, _patch(manager, "artifact.txt", "updated-private-text"))
    result = manager.apply_patch_proposal(proposal, approval_authority=authority)
    rollback_authority, rollback_approval_ref = _approve_rollback(manager, manager.get_rollback_plan(result.rollback_ref))

    receipt = manager.rollback_with_receipt(
        manager.get_rollback_plan(result.rollback_ref),
        audit_ref="file-rollback-audit:primary",
        idempotency_key="idem_rollback_receipt",
        approval_ref=rollback_approval_ref,
        approval_authority=rollback_authority,
        run_id="run_123",
        actor_context=_actor(),
    )

    assert receipt.status == FileOperationStatus.rolled_back
    assert receipt.rollback_performed is True
    assert receipt.raw_content_stored is False
    assert receipt.raw_path_stored is False
    assert receipt.preimage_ref.startswith("file_rollback_preimage_")
    assert receipt.restored_image_ref.startswith("file_rollback_restored_")
    assert "raw_content_omitted" in receipt.redactions_applied
    assert "raw_path_omitted" in receipt.redactions_applied
    assert "safe_refs_only" in receipt.redactions_applied
    assert manager.get_rollback_receipt(receipt.receipt_ref) == receipt
    assert target.read_text(encoding="utf-8") == "previous-private-text"
    receipt_json = receipt.model_dump_json()
    assert "previous-private-text" not in receipt_json
    assert "updated-private-text" not in receipt_json
    assert "artifact.txt" not in receipt_json


def test_patch_rollback_duplicate_idempotency_is_receipted_and_blocked(tmp_path: Path) -> None:
    target = tmp_path / "artifact.txt"
    target.write_text("previous-private-text", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    authority, proposal = _approve(manager, _patch(manager, "artifact.txt", "updated-private-text"))
    result = manager.apply_patch_proposal(proposal, approval_authority=authority)
    rollback_plan = manager.get_rollback_plan(result.rollback_ref)
    rollback_authority, rollback_approval_ref = _approve_rollback(manager, rollback_plan)

    first_receipt = manager.rollback_with_receipt(
        rollback_plan,
        audit_ref="file-rollback-audit:primary",
        idempotency_key="idem_rollback_duplicate",
        approval_ref=rollback_approval_ref,
        approval_authority=rollback_authority,
        run_id="run_123",
        actor_context=_actor(),
    )
    duplicate_receipt = manager.rollback_with_receipt(
        rollback_plan,
        audit_ref="file-rollback-audit:primary",
        idempotency_key="idem_rollback_duplicate",
        approval_ref=rollback_approval_ref,
        approval_authority=rollback_authority,
        run_id="run_123",
        actor_context=_actor(),
    )

    assert first_receipt.status == FileOperationStatus.rolled_back
    assert duplicate_receipt.status == FileOperationStatus.blocked
    assert duplicate_receipt.rollback_performed is False
    assert duplicate_receipt.raw_content_stored is False
    assert duplicate_receipt.raw_path_stored is False
    assert "ROLLBACK_IDEMPOTENCY_REPLAY_BLOCKED" in duplicate_receipt.reason_codes
    assert manager.get_rollback_receipt(duplicate_receipt.receipt_ref) == duplicate_receipt
    assert target.read_text(encoding="utf-8") == "previous-private-text"


def test_patch_rollback_apply_failure_returns_safe_receipt_and_preserves_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "artifact.txt"
    target.write_text("previous-private-text", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    authority, proposal = _approve(manager, _patch(manager, "artifact.txt", "updated-private-text"))
    result = manager.apply_patch_proposal(proposal, approval_authority=authority)
    rollback_authority, rollback_approval_ref = _approve_rollback(manager, manager.get_rollback_plan(result.rollback_ref))

    def fail_replace(_source: Any, _target: Any) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr("ultimate_ai_agent.core.files.manager.os.replace", fail_replace)

    receipt = manager.rollback_with_receipt(
        manager.get_rollback_plan(result.rollback_ref),
        audit_ref="file-rollback-audit:primary",
        idempotency_key="idem_rollback_failure_receipt",
        approval_ref=rollback_approval_ref,
        approval_authority=rollback_authority,
        run_id="run_123",
        actor_context=_actor(),
    )

    assert receipt.status == FileOperationStatus.failed
    assert receipt.rollback_performed is False
    assert receipt.raw_content_stored is False
    assert receipt.raw_path_stored is False
    assert "ROLLBACK_APPLY_FAILED" in receipt.reason_codes
    assert target.read_text(encoding="utf-8") == "updated-private-text"
    assert list(tmp_path.glob(".artifact.txt.*.tmp")) == []
    assert "replace failed" not in receipt.safe_message
    receipt_json = receipt.model_dump_json()
    assert "previous-private-text" not in receipt_json
    assert "updated-private-text" not in receipt_json
    assert "artifact.txt" not in receipt_json
