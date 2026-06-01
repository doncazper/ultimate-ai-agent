from pathlib import Path

from ultimate_ai_agent.core.consent import ConsentGrant
from ultimate_ai_agent.core.consent.enums import ConsentScopeType, ConsentSubjectType, DataBoundary, PermissionAction
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


def test_minimum_lovable_kernel_happy_path_writes_receipts_and_memory(tmp_path):
    memory_store = MemoryStore()
    runner = MinimumKernelRunner(memory_store=memory_store)

    result = runner.run_task(request(tmp_path))

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
