from pathlib import Path
from ultimate_ai_agent.core.consent.enums import DataBoundary
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.kernel import KernelTaskRequest, KernelTaskStatus, KernelTaskType, MinimumKernelRunner


def test_kernel_denies_without_consent_before_file_write(tmp_path: Path) -> None:
    request = KernelTaskRequest(
        request_id="ktr_no_consent",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="user_123",
            authority_source=AuthoritySource.explicit_user_request,
        ),
        user_id="user_123",
        workspace_root=str(tmp_path),
        task_type=KernelTaskType.create_dev_file,
        user_request="Create a local dev note.",
        target_path="notes/m5.md",
        new_content="M5 note",
        purpose="create_dev_note",
        consent_grants=[],
        approval_ref="approval_test_create",
        idempotency_key="idem_kernel_no_consent",
        data_classification=DataBoundary.project_private,
    )

    result = MinimumKernelRunner().run_task(request)

    assert result.success is False
    assert result.status == KernelTaskStatus.denied
    assert "NO_MATCHING_GRANT" in result.errors
    assert not (tmp_path / "notes/m5.md").exists()
    assert result.receipt is not None
    assert result.receipt.status == "failed"
