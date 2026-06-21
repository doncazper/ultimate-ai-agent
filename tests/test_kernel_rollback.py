from pathlib import Path
from tests.test_kernel_minimum_lovable_happy_path import (
    actor,
    consent,
    grant_for_kernel_request,
    grant_workspace_patch_for_kernel_request,
    request,
)

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.consent.enums import DataBoundary
from ultimate_ai_agent.core.kernel import KernelTaskRequest, KernelTaskStatus, KernelTaskType, MinimumKernelRunner


def test_kernel_rollback_restores_previous_content(tmp_path: Path) -> None:
    target = tmp_path / "notes/m5.md"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    authority = LocalApprovalAuthority()
    apply_request = request(tmp_path).model_copy(
        update={"run_id": "run_kernel_rollback_apply", "new_content": "after\n", "approval_ref": None}
    )
    grant = grant_for_kernel_request(authority, apply_request)
    runner = MinimumKernelRunner(approval_authority=authority)
    workspace_grant = grant_workspace_patch_for_kernel_request(authority, apply_request)

    apply_result = runner.run_task(
        apply_request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "workspace_approval_ref": workspace_grant.approval_ref,
            }
        )
    )
    rollback_request = KernelTaskRequest(
        request_id="ktr_rollback",
        run_id="run_kernel_rollback",
        actor_context=actor(),
        user_id="user_123",
        workspace_root=str(tmp_path),
        task_type=KernelTaskType.rollback_dev_file,
        user_request="Rollback the local dev note.",
        purpose="create_dev_note",
        consent_grants=[consent()],
        approval_ref=None,
        idempotency_key="idem_kernel_rollback",
        rollback_ref=apply_result.rollback_ref,
        data_classification=DataBoundary.project_private,
    )
    manager = runner._file_manager(str(tmp_path))
    approval_request = manager.approval_request_for_rollback(
        manager.get_rollback_plan(apply_result.rollback_ref),
        run_id=rollback_request.run_id,
        actor_context=rollback_request.actor_context,
        purpose=rollback_request.purpose,
    )
    authority.create_request(approval_request)
    rollback_grant = authority.grant(
        approval_request.approval_request_id,
        approved_by_actor_id="human_reviewer",
        approved_actions=[approval_request.requested_action],
        approved_resource_refs=approval_request.resource_refs,
    )

    result = runner.run_task(
        rollback_request.model_copy(update={"workspace_approval_ref": rollback_grant.approval_ref})
    )

    assert result.success is True
    assert result.status == KernelTaskStatus.completed
    assert target.read_text(encoding="utf-8") == "before\n"
    assert result.receipt is not None
    assert result.rollback_ref == apply_result.rollback_ref
