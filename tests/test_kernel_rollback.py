from tests.test_kernel_minimum_lovable_happy_path import actor, consent, request

from ultimate_ai_agent.core.consent.enums import DataBoundary
from ultimate_ai_agent.core.kernel import KernelTaskRequest, KernelTaskStatus, KernelTaskType, MinimumKernelRunner


def test_kernel_rollback_restores_previous_content(tmp_path):
    target = tmp_path / "notes/m5.md"
    target.parent.mkdir(parents=True)
    target.write_text("before\n", encoding="utf-8")
    runner = MinimumKernelRunner()

    apply_result = runner.run_task(request(tmp_path).model_copy(update={"new_content": "after\n"}))
    rollback_request = KernelTaskRequest(
        request_id="ktr_rollback",
        actor_context=actor(),
        user_id="user_123",
        workspace_root=str(tmp_path),
        task_type=KernelTaskType.rollback_dev_file,
        user_request="Rollback the local dev note.",
        purpose="create_dev_note",
        consent_grants=[consent()],
        approval_ref="approval_test_rollback",
        idempotency_key="idem_kernel_rollback",
        rollback_ref=apply_result.rollback_ref,
        data_classification=DataBoundary.project_private,
    )

    result = runner.run_task(rollback_request)

    assert result.success is True
    assert result.status == KernelTaskStatus.completed
    assert target.read_text(encoding="utf-8") == "before\n"
    assert result.receipt is not None
    assert result.rollback_ref == apply_result.rollback_ref
