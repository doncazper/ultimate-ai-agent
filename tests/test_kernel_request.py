import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.consent import ConsentGrant
from ultimate_ai_agent.core.consent.enums import ConsentScopeType, ConsentSubjectType, DataBoundary, PermissionAction
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource
from ultimate_ai_agent.core.kernel import KernelTaskRequest, KernelTaskType


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


def test_kernel_request_requires_idempotency_for_mutation(tmp_path):
    with pytest.raises(ValidationError, match="idempotency"):
        KernelTaskRequest(
            request_id="ktr_1",
            actor_context=actor(),
            user_id="user_123",
            workspace_root=str(tmp_path),
            task_type=KernelTaskType.create_dev_file,
            user_request="Create a local dev note.",
            target_path="notes/m5.md",
            new_content="M5 note",
            purpose="create_dev_note",
            consent_grants=[consent()],
            approval_ref="approval_test_create",
            data_classification=DataBoundary.project_private,
        )


def test_kernel_request_requires_target_and_content_for_mutation(tmp_path):
    with pytest.raises(ValidationError, match="target_path"):
        KernelTaskRequest(
            request_id="ktr_2",
            actor_context=actor(),
            user_id="user_123",
            workspace_root=str(tmp_path),
            task_type=KernelTaskType.create_dev_file,
            user_request="Create a local dev note.",
            new_content="M5 note",
            purpose="create_dev_note",
            consent_grants=[consent()],
            approval_ref="approval_test_create",
            idempotency_key="idem_kernel_123",
            data_classification=DataBoundary.project_private,
        )


def test_kernel_request_blocks_absolute_and_traversal_paths(tmp_path):
    for target_path in ["/tmp/outside.md", "../outside.md"]:
        with pytest.raises(ValidationError, match="path"):
            KernelTaskRequest(
                request_id=f"ktr_{target_path}",
                actor_context=actor(),
                user_id="user_123",
                workspace_root=str(tmp_path),
                task_type=KernelTaskType.create_dev_file,
                user_request="Create a local dev note.",
                target_path=target_path,
                new_content="M5 note",
                purpose="create_dev_note",
                consent_grants=[consent()],
                approval_ref="approval_test_create",
                idempotency_key="idem_kernel_123",
                data_classification=DataBoundary.project_private,
            )


def test_kernel_request_blocks_secret_like_inputs(tmp_path):
    with pytest.raises(ValidationError, match="secret"):
        KernelTaskRequest(
            request_id="ktr_secret",
            actor_context=actor(),
            user_id="user_123",
            workspace_root=str(tmp_path),
            task_type=KernelTaskType.create_dev_file,
            user_request="Create a local dev note.",
            target_path="notes/m5.md",
            new_content="api_key='abcdefghijklmnop'",
            purpose="create_dev_note",
            consent_grants=[consent()],
            approval_ref="approval_test_create",
            idempotency_key="idem_kernel_123",
            data_classification=DataBoundary.project_private,
        )
