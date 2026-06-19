from pathlib import Path
from types import SimpleNamespace

from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, ApprovalSubjectType, LocalApprovalAuthority
from ultimate_ai_agent.core.consent import ConsentGrant
from ultimate_ai_agent.core.consent.enums import ConsentScopeType, ConsentSubjectType, DataBoundary, PermissionAction
from ultimate_ai_agent.core.files import FileKind, FilePatchProposal, FileSensitivity, LocalFileManager
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.kernel import KernelTaskRequest, KernelTaskStatus, KernelTaskType, MinimumKernelRunner
from ultimate_ai_agent.core.memory import MemoryStore


def actor() -> ActorContext:
    return ActorContext(
        actor_type=ActorType.human_user,
        actor_id="user_123",
        authority_source=AuthoritySource.explicit_user_request,
    )


def consent() -> ConsentGrant:
    return ConsentGrant(
        consent_id="consent_file_write",
        subject_type=ConsentSubjectType.user,
        subject_id="user_123",
        granted_to_actor="user_123",
        on_behalf_of_user_id="user_123",
        scope_type=ConsentScopeType.workspace,
        scope_id="workspace_test",
        allowed_actions=[PermissionAction.create, PermissionAction.update, PermissionAction.write],
        allowed_resources=["file.write.local_dev"],
        allowed_data_boundaries=[DataBoundary.project_private],
        allowed_purposes=["create_dev_note"],
        source="test",
    )


def request(tmp_path: Path) -> KernelTaskRequest:
    return KernelTaskRequest(
        request_id="ktr_happy",
        actor_context=actor(),
        user_id="user_123",
        workspace_root=str(tmp_path),
        task_type=KernelTaskType.create_dev_file,
        user_request="Create a local dev note.",
        target_path="notes/m5.md",
        new_content="# M5\n\nLocal kernel slice.\n",
        purpose="create_dev_note",
        consent_grants=[consent()],
        approval_ref="approval_test_create",
        idempotency_key="idem_kernel_happy_123",
        data_classification=DataBoundary.project_private,
        tags=["m5", "kernel"],
    )


def grant_for_kernel_request(authority: LocalApprovalAuthority, kernel_request: KernelTaskRequest):
    approval_request = authority.create_request(
        LocalApprovalAuthority.request_for_tool_request(
            SimpleNamespace(
                request_id=f"tr_{kernel_request.request_id}",
                run_id=kernel_request.run_id,
                tool_id="file.write.local_dev",
                actor_context=kernel_request.actor_context,
                requested_action="create",
                purpose=kernel_request.purpose,
                data_classification=kernel_request.data_classification,
                consent_refs=[grant.consent_id for grant in kernel_request.consent_grants],
            ),
            subject_type=ApprovalSubjectType.tool_request,
            subject_id=f"tr_{kernel_request.request_id}",
            resource_refs=["file.write.local_dev"],
            risk_level=ApprovalRiskLevel.high,
        )
    )
    return authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")


def grant_workspace_patch_for_kernel_request(authority: LocalApprovalAuthority, kernel_request: KernelTaskRequest):
    manager = LocalFileManager(kernel_request.workspace_root)
    current_ref = manager.build_file_ref(kernel_request.target_path)
    patch = FilePatchProposal(
        proposal_id=f"file-patch-proposal:kernel:{kernel_request.request_id}",
        run_id=kernel_request.run_id,
        actor_context=kernel_request.actor_context,
        file_ref=current_ref.file_ref,
        target_path=kernel_request.target_path,
        purpose=kernel_request.purpose,
        new_content=kernel_request.new_content or "",
        expected_existing_hash=kernel_request.expected_existing_hash or current_ref.content_hash,
        file_kind=FileKind.artifact,
        sensitivity=FileSensitivity.project_private,
        risk_class=ApprovalRiskLevel.high,
        idempotency_key=kernel_request.idempotency_key,
        audit_ref=f"file-patch-audit:{kernel_request.request_id}",
    )
    approval_request = manager.approval_request_for_patch(patch)
    authority.create_request(approval_request)
    return authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="human_reviewer",
        approved_actions=[approval_request.requested_action],
        approved_resource_refs=approval_request.resource_refs,
    )


def test_minimum_lovable_kernel_happy_path_writes_receipts_and_memory(tmp_path):
    memory_store = MemoryStore()
    kernel_request = request(tmp_path).model_copy(update={"run_id": "run_kernel_happy", "approval_ref": None})
    authority = LocalApprovalAuthority()
    grant = grant_for_kernel_request(authority, kernel_request)
    workspace_grant = grant_workspace_patch_for_kernel_request(authority, kernel_request)
    runner = MinimumKernelRunner(memory_store=memory_store, approval_authority=authority)

    result = runner.run_task(
        kernel_request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "workspace_approval_ref": workspace_grant.approval_ref,
            }
        )
    )

    assert result.success is True
    assert result.status == KernelTaskStatus.completed
    assert (tmp_path / "notes/m5.md").read_text(encoding="utf-8") == "# M5\n\nLocal kernel slice.\n"
    assert result.file_change is not None
    assert result.rollback_ref
    assert result.receipt is not None
    assert result.receipt.status == "completed"
    assert "file.write.local_dev" in result.receipt.tools_called
    assert result.world_state is not None
    assert result.world_state.artifact_refs == ["notes/m5.md"]
    assert result.memory_decision is not None
    assert result.memory_decision.allowed is True
    stored = memory_store.get_memory(result.memory_decision.memory_id)
    assert stored is not None
    assert "recall only" in stored.content
    assert stored.source_refs[0].file_ref == "notes/m5.md"
