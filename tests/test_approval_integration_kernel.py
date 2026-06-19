from types import SimpleNamespace

from tests.test_kernel_minimum_lovable_happy_path import grant_workspace_patch_for_kernel_request, request
from ultimate_ai_agent.core.approvals import ApprovalRiskLevel, ApprovalSubjectType, LocalApprovalAuthority
from ultimate_ai_agent.core.kernel import KernelTaskStatus, MinimumKernelRunner


def test_kernel_accepts_valid_local_dev_approval_grant(tmp_path):
    kernel_request = request(tmp_path).model_copy(update={"run_id": "run_kernel_m85", "approval_ref": None})
    authority = LocalApprovalAuthority()
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
    grant = authority.grant(approval_request.approval_request_id, approved_by_actor_id="human_reviewer")
    workspace_grant = grant_workspace_patch_for_kernel_request(authority, kernel_request)

    result = MinimumKernelRunner(approval_authority=authority).run_task(
        kernel_request.model_copy(
            update={
                "approval_ref": grant.approval_ref,
                "workspace_approval_ref": workspace_grant.approval_ref,
            }
        )
    )

    assert result.success is True
    assert result.status == KernelTaskStatus.completed
    assert (tmp_path / "notes/m5.md").exists()


def test_kernel_rejects_arbitrary_approval_even_with_authority(tmp_path):
    kernel_request = request(tmp_path).model_copy(update={"run_id": "run_kernel_m85", "approval_ref": "human_approved_ref_123"})

    result = MinimumKernelRunner(approval_authority=LocalApprovalAuthority()).run_task(kernel_request)

    assert result.success is False
    assert result.status == KernelTaskStatus.approval_required
    assert "APPROVAL_REF_UNKNOWN" in result.errors
    assert not (tmp_path / "notes/m5.md").exists()
