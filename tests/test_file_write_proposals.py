from typing import Any
from pathlib import Path
from datetime import timedelta

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.files import (
    FileKind,
    FileManagerPolicy,
    FilePatchProposal,
    FileSensitivity,
    FileWriteProposal,
    FileOperationStatus,
    LocalFileManager,
)
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.time import utc_now


def actor() -> Any:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def proposal(path: str, content: str, **kwargs: Any) -> FileWriteProposal:
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


def patch_proposal(manager: LocalFileManager, path: str, content: str, **kwargs: Any) -> FilePatchProposal:
    return FilePatchProposal(
        proposal_id=kwargs.pop("proposal_id", "file-patch-proposal:primary"),
        run_id="run_123",
        actor_context=actor(),
        file_ref=kwargs.pop("file_ref", manager.build_file_ref(path).file_ref),
        target_path=path,
        purpose="test patch proposal",
        new_content=content,
        expected_existing_hash=kwargs.pop("expected_existing_hash", manager.build_file_ref(path).content_hash),
        file_kind=kwargs.pop("file_kind", FileKind.artifact),
        sensitivity=kwargs.pop("sensitivity", FileSensitivity.project_private),
        idempotency_key=kwargs.pop("idempotency_key", "idem_patch_123"),
        audit_ref=kwargs.pop("audit_ref", "file-patch-audit:primary"),
        **kwargs,
    )


def approve_patch(manager: LocalFileManager, patch: FilePatchProposal) -> tuple[Any, ...]:
    authority = LocalApprovalAuthority()
    request = manager.approval_request_for_patch(patch)
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="reviewer_123",
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref="approval:file-patch-primary",
        expires_at=utc_now() + timedelta(minutes=5),
    )
    return authority, patch.model_copy(update={"approval_ref": grant.approval_ref})


def approve_rollback(manager: LocalFileManager, rollback_plan: Any) -> tuple[Any, ...]:
    authority = LocalApprovalAuthority()
    request = manager.approval_request_for_rollback(
        rollback_plan,
        run_id="run_123",
        actor_context=actor(),
    )
    authority.create_request(request)
    grant = authority.grant(
        request.approval_request_id,
        approved_by_actor_id="reviewer_123",
        approved_actions=[request.requested_action],
        approved_resource_refs=request.resource_refs,
        approval_ref="approval:file-patch-rollback",
        expires_at=utc_now() + timedelta(minutes=5),
    )
    return authority, grant.approval_ref


def test_write_proposal_requires_idempotency_key(tmp_path: Path) -> None:
    manager = LocalFileManager(workspace_root=tmp_path)
    decision = manager.propose_write(proposal("out.txt", "hello", idempotency_key=""))

    assert decision.allowed is False
    assert decision.status == FileOperationStatus.blocked
    assert "IDEMPOTENCY_KEY_REQUIRED" in decision.reason_codes


def test_write_proposal_blocks_secret_content_and_secret_paths(tmp_path: Path) -> None:
    manager = LocalFileManager(workspace_root=tmp_path)

    secret_content = manager.propose_write(proposal("out.txt", "api_key='abcdefghijklmnop'"))
    env_file = manager.propose_write(proposal(".env", "SAFE_PLACEHOLDER=1"))

    assert secret_content.allowed is False
    assert "SECRET_CONTENT_BLOCKED" in secret_content.reason_codes
    assert env_file.allowed is False
    assert "FILE_PATH_BLOCKED" in env_file.reason_codes


def test_canonical_overwrite_requires_expected_hash(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "canonical.md").write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    decision = manager.propose_write(
        proposal("docs/canonical.md", "new", file_kind=FileKind.canonical)
    )

    assert decision.allowed is False
    assert "EXPECTED_HASH_REQUIRED" in decision.reason_codes


def test_expected_hash_mismatch_blocks_write(tmp_path: Path) -> None:
    (tmp_path / "out.txt").write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)

    decision = manager.propose_write(proposal("out.txt", "new", expected_existing_hash="wrong"))

    assert decision.allowed is False
    assert "EXPECTED_HASH_MISMATCH" in decision.reason_codes


def test_strict_contract_policy_blocks_unlisted_update_path(tmp_path: Path) -> None:
    manager = LocalFileManager(
        workspace_root=tmp_path,
        policy=FileManagerPolicy(strict_contract_paths=True, allowed_update_paths=["allowed.txt"]),
    )

    decision = manager.propose_write(proposal("blocked.txt", "new"))

    assert decision.allowed is False
    assert "CONTRACT_FILE_NOT_ALLOWED" in decision.reason_codes


def test_patch_proposal_blocks_mismatched_file_path_binding(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text("old", encoding="utf-8")
    (tmp_path / "two.txt").write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    wrong_file_ref = manager.build_file_ref("one.txt").file_ref

    decision = manager.propose_patch(patch_proposal(manager, "two.txt", "new", file_ref=wrong_file_ref))

    assert decision.allowed is False
    assert decision.status == FileOperationStatus.blocked
    assert "FILE_REF_PATH_BINDING_MISMATCH" in decision.reason_codes
    assert decision.preview_ref is None


def test_patch_apply_requires_exact_approval(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    patch = patch_proposal(manager, "note.txt", "new")

    result = manager.apply_patch_proposal(patch)

    assert result.allowed is False
    assert result.status == FileOperationStatus.blocked
    assert "PATCH_APPROVAL_REQUIRED" in result.reason_codes
    assert target.read_text(encoding="utf-8") == "old"
    assert result.rollback_ref is None


def test_patch_apply_rejects_unvalidated_approval_ref_string(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    patch = patch_proposal(manager, "note.txt", "new").model_copy(
        update={"approval_ref": "approval:file-patch-unvalidated"}
    )

    result = manager.apply_patch_proposal(patch, approval_authority=LocalApprovalAuthority())

    assert result.allowed is False
    assert result.status == FileOperationStatus.blocked
    assert "PATCH_APPROVAL_DENIED" in result.reason_codes
    assert "APPROVAL_REF_UNKNOWN" in result.reason_codes
    assert target.read_text(encoding="utf-8") == "old"


def test_patch_apply_rejects_wrong_scope_approval(tmp_path: Path) -> None:
    (tmp_path / "first.txt").write_text("old", encoding="utf-8")
    (tmp_path / "second.txt").write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    first_patch = patch_proposal(manager, "first.txt", "new", proposal_id="file-patch-proposal:first")
    second_patch = patch_proposal(
        manager,
        "second.txt",
        "new",
        proposal_id="file-patch-proposal:second",
        idempotency_key="idem_patch_second",
    )
    authority, approved_first = approve_patch(manager, first_patch)
    wrong_scope_patch = second_patch.model_copy(update={"approval_ref": approved_first.approval_ref})

    result = manager.apply_patch_proposal(wrong_scope_patch, approval_authority=authority)

    assert result.allowed is False
    assert result.status == FileOperationStatus.blocked
    assert "PATCH_APPROVAL_DENIED" in result.reason_codes
    assert "APPROVAL_SUBJECT_MISMATCH" in result.reason_codes
    assert (tmp_path / "second.txt").read_text(encoding="utf-8") == "old"


def test_patch_proposal_blocks_expired_review_window(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    patch = patch_proposal(manager, "note.txt", "new", expires_at=utc_now() - timedelta(minutes=1))

    decision = manager.propose_patch(patch, current_time=utc_now())

    assert decision.allowed is False
    assert decision.status == FileOperationStatus.blocked
    assert "PATCH_PROPOSAL_EXPIRED" in decision.reason_codes


def test_patch_apply_blocks_stale_proposal(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    patch = patch_proposal(manager, "note.txt", "new")
    authority, approved_patch = approve_patch(manager, patch)
    target.write_text("changed-before-apply", encoding="utf-8")

    result = manager.apply_patch_proposal(approved_patch, approval_authority=authority)

    assert result.allowed is False
    assert result.status == FileOperationStatus.blocked
    assert "PATCH_PROPOSAL_STALE" in result.reason_codes
    assert target.read_text(encoding="utf-8") == "changed-before-apply"


def test_patch_apply_blocks_duplicate_idempotency_after_success(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    patch = patch_proposal(manager, "note.txt", "new")
    authority, approved_patch = approve_patch(manager, patch)

    first = manager.apply_patch_proposal(approved_patch, approval_authority=authority)
    second = manager.apply_patch_proposal(approved_patch, approval_authority=authority)

    assert first.allowed is True
    assert first.status == FileOperationStatus.applied
    assert first.rollback_ref is not None
    assert manager.get_rollback_plan(first.rollback_ref).snapshot_id is not None
    assert second.allowed is False
    assert second.status == FileOperationStatus.blocked
    assert "PATCH_IDEMPOTENCY_REPLAY_BLOCKED" in second.reason_codes
    assert target.read_text(encoding="utf-8") == "new"


def test_patch_proposal_blocks_unsafe_diff_content(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    unsafe_content = "api_" + "key='abcdefghijklmnop'"

    decision = manager.propose_patch(patch_proposal(manager, "note.txt", unsafe_content))

    assert decision.allowed is False
    assert decision.status == FileOperationStatus.blocked
    assert "PATCH_DIFF_CONTENT_BLOCKED" in decision.reason_codes
    assert "abcdefghijklmnop" not in decision.model_dump_json()


def test_patch_apply_exact_approval_captures_rollback_before_mutation(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    target.write_text("old", encoding="utf-8")
    manager = LocalFileManager(workspace_root=tmp_path)
    patch = patch_proposal(manager, "note.txt", "new")
    authority, approved_patch = approve_patch(manager, patch)

    result = manager.apply_patch_proposal(approved_patch, approval_authority=authority)
    rollback_plan = manager.get_rollback_plan(result.rollback_ref)
    rollback_authority, rollback_approval_ref = approve_rollback(manager, rollback_plan)
    rollback = manager.rollback_with_receipt(
        rollback_plan,
        audit_ref="file-rollback-audit:write-proposals",
        idempotency_key="idem_rollback_write_proposals",
        approval_ref=rollback_approval_ref,
        approval_authority=rollback_authority,
        run_id="run_123",
        actor_context=actor(),
    )

    assert result.allowed is True
    assert result.status == FileOperationStatus.applied
    assert result.audit_ref == "file-patch-audit:primary"
    assert result.target_ref.startswith("file_path_")
    assert "note.txt" not in result.model_dump_json()
    assert target.read_text(encoding="utf-8") == "old"
    assert rollback.rollback_ref == result.rollback_ref
    assert rollback.status == FileOperationStatus.rolled_back
