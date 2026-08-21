from __future__ import annotations

import itertools
import sqlite3
from datetime import timedelta
from pathlib import Path
from threading import Event, Thread

import pytest

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.local_data import (
    ArchiveRecord,
    DeleteRecord,
    EcosystemConflict,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
    PutRecord,
)
from ultimate_ai_agent.core.ecosystem.tasks import (
    ECO_TASK_MUTATION_ACTION,
    CanonicalTask,
    FounderLoopLocalTaskCompatibilityReader,
    TaskConflict,
    TaskError,
    TaskMissionBinding,
    TaskPriority,
    TaskQuery,
    TaskRecurrenceCadence,
    TaskRecurrenceRule,
    TaskRepository,
    TaskStatus,
    TaskView,
)
from ultimate_ai_agent.core.hygiene.actor_context import (
    ActorContext,
    ActorType,
    AuthoritySource,
)
from ultimate_ai_agent.core.hygiene.policies import (
    ClassificationValue,
    DataClassification,
)
from ultimate_ai_agent.core.time import utc_now


WORKSPACE = "workspace-ref:tasks-test"
_COUNTER = itertools.count(1)


def _approval(
    authority: LocalApprovalAuthority,
    *,
    action: str,
    resources: tuple[str, ...],
):
    suffix = next(_COUNTER)
    request = ApprovalRequest(
        approval_request_id=f"approval_request_eco002_{suffix}",
        run_id="run_eco_002_tests",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_eco002_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco002_test",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify one exact ECO-002 local task mutation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-002-test",
            requires_redaction=True,
        ),
        resource_refs=list(resources),
        expires_at=utc_now() + timedelta(minutes=10),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id,
        approval_ref=f"approval_eco002_{suffix}",
    )
    return request.to_validation_request(grant.approval_ref)


def _repository(
    tmp_path: Path,
) -> tuple[TaskRepository, LocalApprovalAuthority, Path]:
    authority = LocalApprovalAuthority()
    database_path = (tmp_path / "ecosystem.sqlite3").resolve()
    platform = EcosystemLocalDataPlatform(
        database_path=database_path,
        crypto_backend=InMemoryLocalDataCryptoBackend(),
        approval_authority=authority,
        path_resolver=InMemoryLocalDataPathResolver(),
    )
    platform.create_workspace(
        workspace_ref=WORKSPACE,
        key_version_ref="key-version-ref:tasks-v1",
        approval=_approval(
            authority,
            action="ecosystem.local_data.create_workspace",
            resources=(WORKSPACE, "key-version-ref:tasks-v1"),
        ),
    )
    return TaskRepository(platform), authority, database_path


def _mutation_refs(
    *, task_ref: str, operation_ref: str, idempotency_ref: str
) -> tuple[str, ...]:
    return TaskRepository.mutation_resource_refs(
        workspace_ref=WORKSPACE,
        idempotency_ref=idempotency_ref,
        operation_ref=operation_ref,
        task_ref=task_ref,
    )


def _create(
    repository: TaskRepository,
    authority: LocalApprovalAuthority,
    task: CanonicalTask,
    suffix: str,
):
    operation_ref = f"operation-ref:{suffix}"
    idempotency_ref = f"idempotency-ref:{suffix}"
    return repository.create(
        task=task,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_TASK_MUTATION_ACTION,
            resources=_mutation_refs(
                task_ref=task.task_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )


def _save(
    repository: TaskRepository,
    authority: LocalApprovalAuthority,
    task: CanonicalTask,
    suffix: str,
):
    operation_ref = f"operation-ref:{suffix}"
    idempotency_ref = f"idempotency-ref:{suffix}"
    return repository.save(
        task=task,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        expected_version=task.version - 1,
        approval=_approval(
            authority,
            action=ECO_TASK_MUTATION_ACTION,
            resources=_mutation_refs(
                task_ref=task.task_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )


def _task(task_ref: str = "task-ref:one", **updates) -> CanonicalTask:
    return CanonicalTask(
        workspace_ref=WORKSPACE,
        task_ref=task_ref,
        title="Private task title",
        **updates,
    )


def test_task_create_is_encrypted_and_exact_action_bound(tmp_path: Path) -> None:
    repository, authority, database_path = _repository(tmp_path)
    task = _task(notes="private notes")
    receipt = _create(repository, authority, task, "create-one")
    assert receipt.replayed is False
    assert repository.read(workspace_ref=WORKSPACE, task_ref=task.task_ref) == task
    at_rest = database_path.read_bytes()
    wal = database_path.with_name(f"{database_path.name}-wal")
    if wal.exists():
        at_rest += wal.read_bytes()
    assert b"Private task title" not in at_rest
    assert b"private notes" not in at_rest

    operation = repository._put(task, "operation-ref:create-one", expected_version=0)
    resources = _mutation_refs(
        task_ref=task.task_ref,
        operation_ref=operation.operation_ref,
        idempotency_ref="idempotency-ref:create-one",
    )
    with pytest.raises(EcosystemConflict, match="ECO_IDEMPOTENCY_REPLAY_CONFLICT"):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref="idempotency-ref:create-one",
            operations=(operation,),
            approval=_approval(
                authority,
                action="ecosystem.local_data.apply",
                resources=resources,
            ),
        )


def test_wrong_task_action_cannot_mutate(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task()
    operation_ref = "operation-ref:wrong-action"
    idempotency_ref = "idempotency-ref:wrong-action"
    with pytest.raises(EcosystemLocalDataError, match="ECO_APPROVAL_SCOPE_INVALID"):
        repository.create(
            task=task,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=_approval(
                authority,
                action="ecosystem.local_data.apply",
                resources=_mutation_refs(
                    task_ref=task.task_ref,
                    operation_ref=operation_ref,
                    idempotency_ref=idempotency_ref,
                ),
            ),
        )
    with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
        repository.read(workspace_ref=WORKSPACE, task_ref=task.task_ref)


def test_task_action_cannot_mutate_another_domain(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task("task-ref:generic-action-denied")
    task_operation = repository._put(
        task, "operation-ref:generic-action-denied", expected_version=0
    )
    task_idempotency_ref = "idempotency-ref:generic-action-denied"
    task_resources = (
        WORKSPACE,
        task_idempotency_ref,
        task_operation.operation_ref,
        task_operation.record_ref,
    )
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_REQUIRES_DOMAIN_ACTION"
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=task_idempotency_ref,
            operations=(task_operation,),
            approval=_approval(
                authority,
                action="ecosystem.local_data.apply",
                resources=task_resources,
            ),
        )

    operation = PutRecord(
        operation_ref="operation-ref:foreign-domain",
        module_ref="module-ref:foreign",
        record_ref="record-ref:foreign",
        record_kind_ref="record-kind-ref:foreign",
        safe_summary_ref="summary-ref:foreign",
        private_payload={"value": "private"},
    )
    idempotency_ref = "idempotency-ref:foreign-domain"
    resources = (
        WORKSPACE,
        idempotency_ref,
        operation.operation_ref,
        operation.record_ref,
    )

    with pytest.raises(
        EcosystemLocalDataError,
        match="ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID",
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=idempotency_ref,
            operations=(operation,),
            approval=_approval(
                authority,
                action=ECO_TASK_MUTATION_ACTION,
                resources=resources,
            ),
            requested_action=ECO_TASK_MUTATION_ACTION,
        )

    create_idempotency_ref = "idempotency-ref:foreign-domain-create"
    create_resources = (
        WORKSPACE,
        create_idempotency_ref,
        operation.operation_ref,
        operation.record_ref,
    )
    repository.platform.apply(
        workspace_ref=WORKSPACE,
        idempotency_ref=create_idempotency_ref,
        operations=(operation,),
        approval=_approval(
            authority,
            action="ecosystem.local_data.apply",
            resources=create_resources,
        ),
    )
    delete = DeleteRecord(
        operation_ref="operation-ref:foreign-domain-delete",
        record_ref=operation.record_ref,
        expected_version=1,
    )
    delete_idempotency_ref = "idempotency-ref:foreign-domain-delete"
    delete_resources = (
        WORKSPACE,
        delete_idempotency_ref,
        delete.operation_ref,
        delete.record_ref,
    )
    with pytest.raises(
        EcosystemLocalDataError,
        match="ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID",
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=delete_idempotency_ref,
            operations=(delete,),
            approval=_approval(
                authority,
                action=ECO_TASK_MUTATION_ACTION,
                resources=delete_resources,
            ),
            requested_action=ECO_TASK_MUTATION_ACTION,
        )


def test_task_read_rejects_another_module_owner(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task("task-ref:foreign-owner")
    operation = repository._put(task, "operation-ref:foreign-owner", expected_version=0)
    foreign = PutRecord(
        **{
            **vars(operation),
            "module_ref": "module-ref:foreign",
        }
    )
    idempotency_ref = "idempotency-ref:foreign-owner"
    resources = (
        WORKSPACE,
        idempotency_ref,
        foreign.operation_ref,
        foreign.record_ref,
    )
    repository.platform.apply(
        workspace_ref=WORKSPACE,
        idempotency_ref=idempotency_ref,
        operations=(foreign,),
        approval=_approval(
            authority,
            action="ecosystem.local_data.apply",
            resources=resources,
        ),
    )

    with pytest.raises(TaskError, match="ECO_TASK_RECORD_BINDING_INVALID"):
        repository.read(workspace_ref=WORKSPACE, task_ref=task.task_ref)


def test_put_cannot_reassign_existing_record_domain_ownership(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    foreign_ref = "record-ref:foreign-owned"
    foreign_create = PutRecord(
        operation_ref="operation-ref:foreign-owned-create",
        module_ref="module-ref:foreign",
        record_ref=foreign_ref,
        record_kind_ref="record-kind-ref:foreign",
        safe_summary_ref="summary-ref:foreign",
        private_payload={"value": "private"},
    )
    foreign_create_idempotency = "idempotency-ref:foreign-owned-create"
    repository.platform.apply(
        workspace_ref=WORKSPACE,
        idempotency_ref=foreign_create_idempotency,
        operations=(foreign_create,),
        approval=_approval(
            authority,
            action="ecosystem.local_data.apply",
            resources=(
                WORKSPACE,
                foreign_create_idempotency,
                foreign_create.operation_ref,
                foreign_ref,
            ),
        ),
    )
    claimed_task = _task(foreign_ref)
    claimed_put = repository._put(
        claimed_task, "operation-ref:foreign-owned-claim", expected_version=1
    )
    claimed_idempotency = "idempotency-ref:foreign-owned-claim"
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID"
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=claimed_idempotency,
            operations=(claimed_put,),
            approval=_approval(
                authority,
                action=ECO_TASK_MUTATION_ACTION,
                resources=_mutation_refs(
                    task_ref=foreign_ref,
                    operation_ref=claimed_put.operation_ref,
                    idempotency_ref=claimed_idempotency,
                ),
            ),
            requested_action=ECO_TASK_MUTATION_ACTION,
        )

    task = _task("task-ref:task-owned")
    _create(repository, authority, task, "task-owned-create")
    foreign_claim = PutRecord(
        operation_ref="operation-ref:task-owned-claim",
        module_ref="module-ref:foreign",
        record_ref=task.task_ref,
        record_kind_ref="record-kind-ref:foreign",
        safe_summary_ref="summary-ref:foreign",
        private_payload={"value": "private"},
        expected_version=1,
    )
    foreign_claim_idempotency = "idempotency-ref:task-owned-claim"
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_REQUIRES_DOMAIN_ACTION"
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=foreign_claim_idempotency,
            operations=(foreign_claim,),
            approval=_approval(
                authority,
                action="ecosystem.local_data.apply",
                resources=(
                    WORKSPACE,
                    foreign_claim_idempotency,
                    foreign_claim.operation_ref,
                    task.task_ref,
                ),
            ),
        )


def test_legacy_task_module_records_have_an_exact_maintenance_lane(
    tmp_path: Path,
) -> None:
    repository, authority, _ = _repository(tmp_path)
    action = "ecosystem.tasks.legacy_local_data.apply"
    record_ref = "record-ref:legacy-task"

    def apply_legacy(operation, suffix: str):
        idempotency_ref = f"idempotency-ref:{suffix}"
        return repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=idempotency_ref,
            operations=(operation,),
            approval=_approval(
                authority,
                action=action,
                resources=(
                    WORKSPACE,
                    idempotency_ref,
                    operation.operation_ref,
                    record_ref,
                ),
            ),
            requested_action=action,
        )

    apply_legacy(
        PutRecord(
            operation_ref="operation-ref:legacy-task-create",
            module_ref="module-ref:tasks",
            record_ref=record_ref,
            record_kind_ref="record-kind-ref:task",
            safe_summary_ref="summary-ref:legacy-task",
            private_payload={"title": "private legacy task"},
        ),
        "legacy-task-create",
    )
    apply_legacy(
        PutRecord(
            operation_ref="operation-ref:legacy-task-update",
            module_ref="module-ref:tasks",
            record_ref=record_ref,
            record_kind_ref="record-kind-ref:task",
            safe_summary_ref="summary-ref:legacy-task",
            private_payload={"title": "private updated legacy task"},
            expected_version=1,
        ),
        "legacy-task-update",
    )
    apply_legacy(
        ArchiveRecord(
            operation_ref="operation-ref:legacy-task-archive",
            record_ref=record_ref,
            expected_version=2,
        ),
        "legacy-task-archive",
    )
    apply_legacy(
        DeleteRecord(
            operation_ref="operation-ref:legacy-task-delete",
            record_ref=record_ref,
            expected_version=3,
        ),
        "legacy-task-delete",
    )
    with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
        repository.platform.read(workspace_ref=WORKSPACE, record_ref=record_ref)


def test_lifecycle_replay_survives_later_task_mutations(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task("task-ref:durable-lifecycle-replay")
    _create(repository, authority, task, "durable-lifecycle-create")
    complete_operation = "operation-ref:durable-complete"
    complete_idempotency = "idempotency-ref:durable-complete"
    complete_approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=_mutation_refs(
            task_ref=task.task_ref,
            operation_ref=complete_operation,
            idempotency_ref=complete_idempotency,
        ),
    )
    complete_receipt = repository.complete(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        completed_at="2026-08-20T19:00:00Z",
        operation_ref=complete_operation,
        idempotency_ref=complete_idempotency,
        approval=complete_approval,
    )
    reopen_operation = "operation-ref:durable-reopen"
    reopen_idempotency = "idempotency-ref:durable-reopen"
    repository.reopen(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        operation_ref=reopen_operation,
        idempotency_ref=reopen_idempotency,
        approval=_approval(
            authority,
            action=ECO_TASK_MUTATION_ACTION,
            resources=_mutation_refs(
                task_ref=task.task_ref,
                operation_ref=reopen_operation,
                idempotency_ref=reopen_idempotency,
            ),
        ),
    )

    replay = repository.complete(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        completed_at="2026-08-20T12:00:00-07:00",
        operation_ref=complete_operation,
        idempotency_ref=complete_idempotency,
        approval=complete_approval,
    )
    assert replay.replayed is True
    assert replay.receipt_ref == complete_receipt.receipt_ref
    current = repository.read(workspace_ref=WORKSPACE, task_ref=task.task_ref)
    assert current.status == TaskStatus.ready
    assert current.version == 3


def test_lifecycle_replay_is_bound_to_the_public_operation(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task("task-ref:lifecycle-binding")
    operation_ref = "operation-ref:lifecycle-binding"
    idempotency_ref = "idempotency-ref:lifecycle-binding"
    approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=_mutation_refs(
            task_ref=task.task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    repository.create(
        task=task,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=approval,
    )
    with pytest.raises(EcosystemConflict, match="ECO_IDEMPOTENCY_REPLAY_CONFLICT"):
        repository.reopen(
            workspace_ref=WORKSPACE,
            task_ref=task.task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
        )


def test_raw_task_action_cannot_bypass_repository_lifecycle_validation(
    tmp_path: Path,
) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task("task-ref:repository-only")
    _create(repository, authority, task, "repository-only-create")
    operations = (
        repository._put(
            CanonicalTask.model_validate(
                {
                    **task.model_dump(mode="json"),
                    "title": "Private bypass attempt",
                    "version": 2,
                }
            ),
            "operation-ref:repository-only-put",
            expected_version=1,
        ),
        ArchiveRecord(
            operation_ref="operation-ref:repository-only-archive",
            record_ref=task.task_ref,
            expected_version=1,
        ),
        DeleteRecord(
            operation_ref="operation-ref:repository-only-delete",
            record_ref=task.task_ref,
            expected_version=1,
        ),
    )
    for index, operation in enumerate(operations):
        idempotency_ref = f"idempotency-ref:repository-only-{index}"
        with pytest.raises(
            EcosystemLocalDataError,
            match="ECO_MUTATION_REQUIRES_REPOSITORY_VALIDATION",
        ):
            repository.platform.apply(
                workspace_ref=WORKSPACE,
                idempotency_ref=idempotency_ref,
                operations=(operation,),
                approval=_approval(
                    authority,
                    action=ECO_TASK_MUTATION_ACTION,
                    resources=_mutation_refs(
                        task_ref=task.task_ref,
                        operation_ref=operation.operation_ref,
                        idempotency_ref=idempotency_ref,
                    ),
                ),
                requested_action=ECO_TASK_MUTATION_ACTION,
            )
    current = repository.read(workspace_ref=WORKSPACE, task_ref=task.task_ref)
    assert current == task


def test_already_current_task_rejects_at_the_task_boundary(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task("task-ref:already-current")
    _create(repository, authority, task, "already-current-create")
    updated = CanonicalTask.model_validate(
        {
            **task.model_dump(mode="json"),
            "title": "Private updated title",
            "version": 2,
        }
    )
    _save(repository, authority, updated, "already-current-save")

    with pytest.raises(TaskConflict, match="ECO_TASK_STALE_VERSION"):
        _save(repository, authority, updated, "already-current-save-new-key")

    ready_task = _task("task-ref:already-ready")
    _create(repository, authority, ready_task, "already-ready-create")
    operation_ref = "operation-ref:already-ready-reopen"
    idempotency_ref = "idempotency-ref:already-ready-reopen"
    with pytest.raises(TaskConflict, match="ECO_TASK_STALE_VERSION"):
        repository.reopen(
            workspace_ref=WORKSPACE,
            task_ref=ready_task.task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=_approval(
                authority,
                action=ECO_TASK_MUTATION_ACTION,
                resources=_mutation_refs(
                    task_ref=ready_task.task_ref,
                    operation_ref=operation_ref,
                    idempotency_ref=idempotency_ref,
                ),
            ),
        )


def test_quick_capture_complete_reopen_and_exact_replay(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task_ref = "task-ref:captured"
    operation_ref = "operation-ref:capture"
    idempotency_ref = "idempotency-ref:capture"
    approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=_mutation_refs(
            task_ref=task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    first = repository.capture(
        workspace_ref=WORKSPACE,
        task_ref=task_ref,
        title="Captured privately",
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=approval,
    )
    replay = repository.capture(
        workspace_ref=WORKSPACE,
        task_ref=task_ref,
        title="Captured privately",
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=approval,
    )
    assert replay.replayed is True
    assert replay.receipt_ref == first.receipt_ref

    complete_operation = "operation-ref:complete"
    complete_idempotency = "idempotency-ref:complete"
    complete_approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=_mutation_refs(
            task_ref=task_ref,
            operation_ref=complete_operation,
            idempotency_ref=complete_idempotency,
        ),
    )
    completed_receipt = repository.complete(
        workspace_ref=WORKSPACE,
        task_ref=task_ref,
        completed_at="2026-08-20T12:00:00-07:00",
        operation_ref=complete_operation,
        idempotency_ref=complete_idempotency,
        approval=complete_approval,
    )
    completed_replay = repository.complete(
        workspace_ref=WORKSPACE,
        task_ref=task_ref,
        completed_at="2026-08-20T19:00:00Z",
        operation_ref=complete_operation,
        idempotency_ref=complete_idempotency,
        approval=complete_approval,
    )
    assert completed_replay.replayed is True
    assert completed_replay.receipt_ref == completed_receipt.receipt_ref
    completed = repository.read(workspace_ref=WORKSPACE, task_ref=task_ref)
    assert completed.status == TaskStatus.completed
    assert completed.completed_at == "2026-08-20T19:00:00Z"

    reopen_operation = "operation-ref:reopen"
    reopen_idempotency = "idempotency-ref:reopen"
    reopen_approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=_mutation_refs(
            task_ref=task_ref,
            operation_ref=reopen_operation,
            idempotency_ref=reopen_idempotency,
        ),
    )
    reopen_receipt = repository.reopen(
        workspace_ref=WORKSPACE,
        task_ref=task_ref,
        operation_ref=reopen_operation,
        idempotency_ref=reopen_idempotency,
        approval=reopen_approval,
    )
    reopen_replay = repository.reopen(
        workspace_ref=WORKSPACE,
        task_ref=task_ref,
        operation_ref=reopen_operation,
        idempotency_ref=reopen_idempotency,
        approval=reopen_approval,
    )
    assert reopen_replay.replayed is True
    assert reopen_replay.receipt_ref == reopen_receipt.receipt_ref
    reopened = repository.read(workspace_ref=WORKSPACE, task_ref=task_ref)
    assert reopened.status == TaskStatus.ready
    assert reopened.completed_at is None
    assert reopened.version == 3


def test_views_are_backend_owned_and_deterministic(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    tasks = (
        _task("task-ref:inbox"),
        _task(
            "task-ref:today",
            status=TaskStatus.ready,
            priority=TaskPriority.high,
            flagged=True,
            project_ref="project-ref:alpha",
            tag_refs=("tag-ref:focus",),
            due_at="2026-08-20T09:00:00Z",
        ),
        _task(
            "task-ref:upcoming",
            status=TaskStatus.ready,
            due_at="2026-08-22T09:00:00Z",
        ),
        _task(
            "task-ref:waiting",
            status=TaskStatus.waiting,
            waiting_on_ref="person-ref:reviewer",
        ),
        _task(
            "task-ref:completed",
            status=TaskStatus.completed,
            completed_at="2026-08-19T09:00:00Z",
        ),
    )
    for index, task in enumerate(tasks):
        _create(repository, authority, task, f"view-{index}")
    as_of = "2026-08-20T12:00:00Z"
    today = repository.query(
        TaskQuery(workspace_ref=WORKSPACE, view=TaskView.today, as_of=as_of)
    )
    assert [task.task_ref for task in today.tasks] == ["task-ref:today"]
    upcoming = repository.query(
        TaskQuery(workspace_ref=WORKSPACE, view=TaskView.upcoming, as_of=as_of)
    )
    assert [task.task_ref for task in upcoming.tasks] == ["task-ref:upcoming"]
    waiting = repository.query(
        TaskQuery(workspace_ref=WORKSPACE, view=TaskView.waiting, as_of=as_of)
    )
    assert [task.task_ref for task in waiting.tasks] == ["task-ref:waiting"]
    filtered = repository.query(
        TaskQuery(
            workspace_ref=WORKSPACE,
            view=TaskView.flagged,
            as_of=as_of,
            project_ref="project-ref:alpha",
            tag_ref="tag-ref:focus",
        )
    )
    assert [task.task_ref for task in filtered.tasks] == ["task-ref:today"]
    assert filtered.background_work_started is False
    assert filtered.external_read_performed is False


def test_today_view_uses_explicit_operator_timezone(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task(
        "task-ref:local-evening",
        status=TaskStatus.ready,
        due_at="2026-08-21T20:00:00Z",
    )
    _create(repository, authority, task, "local-evening")

    local_today = repository.query(
        TaskQuery(
            workspace_ref=WORKSPACE,
            view=TaskView.today,
            as_of="2026-08-20T19:00:00-07:00",
            timezone_name="America/Los_Angeles",
        )
    )
    utc_today = repository.query(
        TaskQuery(
            workspace_ref=WORKSPACE,
            view=TaskView.today,
            as_of="2026-08-21T02:00:00Z",
        )
    )

    assert local_today.tasks == ()
    assert [item.task_ref for item in utc_today.tasks] == [task.task_ref]


def test_dependency_graph_rejects_missing_and_cycles(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    first = _task("task-ref:first")
    _create(repository, authority, first, "dependency-first")
    with pytest.raises(TaskConflict, match="ECO_TASK_RELATED_TASK_NOT_FOUND"):
        _create(
            repository,
            authority,
            _task("task-ref:missing", dependency_refs=("task-ref:not-found",)),
            "dependency-missing",
        )
    second = _task("task-ref:second", dependency_refs=(first.task_ref,))
    _create(repository, authority, second, "dependency-second")
    cyclic_first = CanonicalTask.model_validate(
        {
            **first.model_dump(mode="json"),
            "dependency_refs": [second.task_ref],
            "version": 2,
        }
    )
    with pytest.raises(TaskConflict, match="ECO_TASK_DEPENDENCY_CYCLE_DENIED"):
        _save(repository, authority, cyclic_first, "dependency-cycle")
    assert (
        repository.read(workspace_ref=WORKSPACE, task_ref=first.task_ref).version == 1
    )

    parent = _task("task-ref:parent")
    child = _task("task-ref:child", parent_task_ref=parent.task_ref)
    _create(repository, authority, parent, "parent-cycle-parent")
    _create(repository, authority, child, "parent-cycle-child")
    cyclic_parent = CanonicalTask.model_validate(
        {
            **parent.model_dump(mode="json"),
            "parent_task_ref": child.task_ref,
            "version": 2,
        }
    )
    with pytest.raises(TaskConflict, match="ECO_TASK_PARENT_CYCLE_DENIED"):
        _save(repository, authority, cyclic_parent, "parent-cycle")


def test_hierarchy_cycle_detection_includes_occurrence_links(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    parent = _task("task-ref:occurrence-cycle-parent")
    occurrence = _task(
        "task-ref:occurrence-cycle-child", occurrence_of_ref=parent.task_ref
    )
    _create(repository, authority, parent, "occurrence-cycle-parent")
    _create(repository, authority, occurrence, "occurrence-cycle-child")
    cyclic_parent = CanonicalTask.model_validate(
        {
            **parent.model_dump(mode="json"),
            "parent_task_ref": occurrence.task_ref,
            "version": 2,
        }
    )
    with pytest.raises(TaskConflict, match="ECO_TASK_PARENT_CYCLE_DENIED"):
        _save(repository, authority, cyclic_parent, "occurrence-cycle-save")


def test_one_task_owns_each_mission_without_copying_execution_state(
    tmp_path: Path,
) -> None:
    repository, authority, _ = _repository(tmp_path)
    binding = TaskMissionBinding(
        mission_ref="mission-ref:one",
        run_ref="run-ref:one",
        plan_ref="plan-ref:one",
        owner_ref="owner-ref:operator",
        binding_evidence_ref="evidence-ref:mission-binding",
        handoff_ref="handoff-ref:reviewed",
        recovery_ref="recovery-ref:checkpoint",
    )
    assert binding.mission_execution_state_owned_by_tasks is False
    _create(
        repository,
        authority,
        _task("task-ref:mission-owner", mission_binding=binding),
        "mission-owner",
    )
    with pytest.raises(TaskConflict, match="ECO_TASK_MISSION_ALREADY_OWNED"):
        _create(
            repository,
            authority,
            _task("task-ref:mission-duplicate", mission_binding=binding),
            "mission-duplicate",
        )


def test_archived_task_releases_active_mission_ownership(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    binding = TaskMissionBinding(
        mission_ref="mission-ref:reassignable",
        run_ref="run-ref:reassignable",
        plan_ref="plan-ref:reassignable",
        owner_ref="owner-ref:operator",
        binding_evidence_ref="evidence-ref:reassignable",
    )
    first = _task("task-ref:former-mission-owner", mission_binding=binding)
    _create(repository, authority, first, "former-mission-owner")
    operation_ref = "operation-ref:archive-mission-owner"
    idempotency_ref = "idempotency-ref:archive-mission-owner"
    repository.archive(
        workspace_ref=WORKSPACE,
        task_ref=first.task_ref,
        expected_version=1,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_TASK_MUTATION_ACTION,
            resources=_mutation_refs(
                task_ref=first.task_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )

    second = _task("task-ref:new-mission-owner", mission_binding=binding)
    _create(repository, authority, second, "new-mission-owner")
    assert repository.read(workspace_ref=WORKSPACE, task_ref=second.task_ref) == second


def test_recurrence_is_explicit_and_materializes_distinct_occurrence(
    tmp_path: Path,
) -> None:
    repository, authority, _ = _repository(tmp_path)
    parent = _task(
        "task-ref:recurring",
        status=TaskStatus.ready,
        due_at="2026-01-31T17:00:00Z",
        recurrence=TaskRecurrenceRule(
            cadence=TaskRecurrenceCadence.monthly,
            anchor_at="2026-01-31T09:00:00-08:00",
            timezone_name="America/Los_Angeles",
            day_of_month=31,
        ),
    )
    _create(repository, authority, parent, "recurrence-parent")
    plan = repository.plan_next_occurrence(
        workspace_ref=WORKSPACE,
        parent_task_ref=parent.task_ref,
        after="2026-01-31T17:00:00Z",
        idempotency_ref="idempotency-ref:recurrence-february",
    )
    assert plan.scheduler_started is False
    assert plan.background_work_started is False
    assert plan.occurrence.due_at == "2026-02-28T17:00:00Z"
    approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=plan.resource_refs,
    )
    first = repository.materialize_occurrence(plan=plan, approval=approval)
    replay = repository.materialize_occurrence(plan=plan, approval=approval)
    assert first.receipt_ref == replay.receipt_ref
    assert replay.replayed is True
    occurrence = repository.read(
        workspace_ref=WORKSPACE, task_ref=plan.occurrence.task_ref
    )
    assert occurrence.occurrence_of_ref == parent.task_ref
    assert occurrence.recurrence is None
    assert occurrence.mission_binding is None


def test_occurrence_replay_survives_later_parent_mutation(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    parent = _task(
        "task-ref:recurrence-replay-parent",
        recurrence=TaskRecurrenceRule(
            cadence=TaskRecurrenceCadence.daily,
            anchor_at="2026-08-20T12:00:00Z",
            timezone_name="UTC",
        ),
    )
    _create(repository, authority, parent, "recurrence-replay-parent")
    plan = repository.plan_next_occurrence(
        workspace_ref=WORKSPACE,
        parent_task_ref=parent.task_ref,
        after="2026-08-20T12:00:00Z",
        idempotency_ref="idempotency-ref:recurrence-replay-occurrence",
    )
    approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=plan.resource_refs,
    )
    first = repository.materialize_occurrence(plan=plan, approval=approval)
    updated_parent = CanonicalTask.model_validate(
        {
            **parent.model_dump(mode="json"),
            "title": "Private changed recurring title",
            "version": 2,
        }
    )
    _save(repository, authority, updated_parent, "recurrence-replay-parent-save")

    replay = repository.materialize_occurrence(plan=plan, approval=approval)
    assert replay.replayed is True
    assert replay.receipt_ref == first.receipt_ref


def test_materialization_replay_cannot_reuse_a_direct_create_receipt(
    tmp_path: Path,
) -> None:
    repository, authority, _ = _repository(tmp_path)
    parent = _task(
        "task-ref:materialization-context-parent",
        recurrence=TaskRecurrenceRule(
            cadence=TaskRecurrenceCadence.daily,
            anchor_at="2026-08-20T12:00:00Z",
            timezone_name="UTC",
        ),
    )
    _create(repository, authority, parent, "materialization-context-parent")
    plan = repository.plan_next_occurrence(
        workspace_ref=WORKSPACE,
        parent_task_ref=parent.task_ref,
        after="2026-08-20T12:00:00Z",
        idempotency_ref="idempotency-ref:materialization-context",
    )
    approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=plan.resource_refs,
    )
    repository.create(
        task=plan.occurrence,
        operation_ref=plan.operation_ref,
        idempotency_ref=plan.idempotency_ref,
        approval=approval,
    )
    updated_parent = CanonicalTask.model_validate(
        {
            **parent.model_dump(mode="json"),
            "title": "Private stale parent",
            "version": 2,
        }
    )
    _save(repository, authority, updated_parent, "materialization-context-save")

    with pytest.raises(EcosystemConflict, match="ECO_IDEMPOTENCY_REPLAY_CONFLICT"):
        repository.materialize_occurrence(plan=plan, approval=approval)


def test_recurrence_end_boundary_compares_instants_not_strings() -> None:
    rule = TaskRecurrenceRule(
        cadence=TaskRecurrenceCadence.daily,
        anchor_at="2026-01-01T00:00:00.500Z",
        timezone_name="UTC",
        end_at="2026-01-02T00:00:00Z",
    )

    with pytest.raises(TaskConflict, match="ECO_TASK_RECURRENCE_ENDED"):
        TaskRepository._next_occurrence(rule, "2026-01-01T00:00:00.500Z")


def test_materialization_holds_parent_validation_lock(
    tmp_path: Path, monkeypatch
) -> None:
    repository, authority, _ = _repository(tmp_path)
    parent = _task(
        "task-ref:locked-recurring",
        recurrence=TaskRecurrenceRule(
            cadence=TaskRecurrenceCadence.daily,
            anchor_at="2026-08-20T12:00:00Z",
            timezone_name="UTC",
        ),
    )
    _create(repository, authority, parent, "locked-recurring")
    plan = repository.plan_next_occurrence(
        workspace_ref=WORKSPACE,
        parent_task_ref=parent.task_ref,
        after="2026-08-20T12:00:00Z",
        idempotency_ref="idempotency-ref:locked-materialize",
    )
    entered = Event()
    worker: list[Thread] = []

    def probe_lock() -> None:
        with authority.hold_validation_lock():
            entered.set()

    def guarded_create(**_kwargs):
        thread = Thread(target=probe_lock)
        worker.append(thread)
        thread.start()
        assert entered.wait(0.05) is False
        return "receipt-sentinel"

    monkeypatch.setattr(repository, "create", guarded_create)
    result = repository.materialize_occurrence(
        plan=plan,
        approval=_approval(
            authority,
            action=ECO_TASK_MUTATION_ACTION,
            resources=plan.resource_refs,
        ),
    )

    assert result == "receipt-sentinel"
    assert entered.wait(1)
    worker[0].join(timeout=1)


def test_archive_restore_delete_and_active_reference_safety(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    parent = _task("task-ref:archive-parent")
    child = _task("task-ref:archive-child", parent_task_ref=parent.task_ref)
    _create(repository, authority, parent, "archive-parent")
    _create(repository, authority, child, "archive-child")
    archive_operation = "operation-ref:archive-blocked"
    archive_idempotency = "idempotency-ref:archive-blocked"
    with pytest.raises(TaskConflict, match="ECO_TASK_ACTIVE_REFERENCE_BLOCKS_REMOVAL"):
        repository.archive(
            workspace_ref=WORKSPACE,
            task_ref=parent.task_ref,
            expected_version=1,
            operation_ref=archive_operation,
            idempotency_ref=archive_idempotency,
            approval=_approval(
                authority,
                action=ECO_TASK_MUTATION_ACTION,
                resources=_mutation_refs(
                    task_ref=parent.task_ref,
                    operation_ref=archive_operation,
                    idempotency_ref=archive_idempotency,
                ),
            ),
        )
    detached = CanonicalTask.model_validate(
        {
            **child.model_dump(mode="json"),
            "parent_task_ref": None,
            "version": 2,
        }
    )
    _save(repository, authority, detached, "archive-detach")
    archive_operation = "operation-ref:archive"
    archive_idempotency = "idempotency-ref:archive"
    repository.archive(
        workspace_ref=WORKSPACE,
        task_ref=parent.task_ref,
        expected_version=1,
        operation_ref=archive_operation,
        idempotency_ref=archive_idempotency,
        approval=_approval(
            authority,
            action=ECO_TASK_MUTATION_ACTION,
            resources=_mutation_refs(
                task_ref=parent.task_ref,
                operation_ref=archive_operation,
                idempotency_ref=archive_idempotency,
            ),
        ),
    )
    assert repository.read(workspace_ref=WORKSPACE, task_ref=parent.task_ref).archived
    assert parent.task_ref not in {
        task.task_ref
        for task in repository.query(
            TaskQuery(
                workspace_ref=WORKSPACE,
                view=TaskView.all,
                as_of="2026-08-20T12:00:00Z",
            )
        ).tasks
    }
    restore_operation = "operation-ref:restore"
    restore_idempotency = "idempotency-ref:restore"
    repository.restore(
        workspace_ref=WORKSPACE,
        task_ref=parent.task_ref,
        expected_version=2,
        operation_ref=restore_operation,
        idempotency_ref=restore_idempotency,
        approval=_approval(
            authority,
            action=ECO_TASK_MUTATION_ACTION,
            resources=_mutation_refs(
                task_ref=parent.task_ref,
                operation_ref=restore_operation,
                idempotency_ref=restore_idempotency,
            ),
        ),
    )
    restored = repository.read(workspace_ref=WORKSPACE, task_ref=parent.task_ref)
    assert restored.archived is False
    assert restored.version == 3


def test_archive_restore_replay_and_direct_save_guard(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task("task-ref:archive-replay")
    _create(repository, authority, task, "archive-replay-create")
    direct_archive = CanonicalTask.model_validate(
        {
            **task.model_dump(mode="json"),
            "archived": True,
            "version": 2,
        }
    )
    with pytest.raises(
        TaskConflict, match="ECO_TASK_ARCHIVE_TRANSITION_REQUIRES_LIFECYCLE"
    ):
        _save(repository, authority, direct_archive, "archive-direct-save")

    archive_operation = "operation-ref:archive-replay"
    archive_idempotency = "idempotency-ref:archive-replay"
    archive_approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=_mutation_refs(
            task_ref=task.task_ref,
            operation_ref=archive_operation,
            idempotency_ref=archive_idempotency,
        ),
    )
    archive_receipt = repository.archive(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=1,
        operation_ref=archive_operation,
        idempotency_ref=archive_idempotency,
        approval=archive_approval,
    )
    archive_replay = repository.archive(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=1,
        operation_ref=archive_operation,
        idempotency_ref=archive_idempotency,
        approval=archive_approval,
    )
    assert archive_replay.replayed is True
    assert archive_replay.receipt_ref == archive_receipt.receipt_ref

    restore_operation = "operation-ref:restore-replay"
    restore_idempotency = "idempotency-ref:restore-replay"
    restore_approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=_mutation_refs(
            task_ref=task.task_ref,
            operation_ref=restore_operation,
            idempotency_ref=restore_idempotency,
        ),
    )
    restore_receipt = repository.restore(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=2,
        operation_ref=restore_operation,
        idempotency_ref=restore_idempotency,
        approval=restore_approval,
    )
    restore_replay = repository.restore(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=2,
        operation_ref=restore_operation,
        idempotency_ref=restore_idempotency,
        approval=restore_approval,
    )
    assert restore_replay.replayed is True
    assert restore_replay.receipt_ref == restore_receipt.receipt_ref


def test_delete_requires_archived_task(tmp_path: Path) -> None:
    repository, authority, _ = _repository(tmp_path)
    task = _task("task-ref:delete")
    _create(repository, authority, task, "delete-create")
    delete_operation = "operation-ref:delete-unarchived"
    delete_idempotency = "idempotency-ref:delete-unarchived"
    with pytest.raises(TaskConflict, match="ECO_TASK_DELETE_REQUIRES_ARCHIVE"):
        repository.delete(
            workspace_ref=WORKSPACE,
            task_ref=task.task_ref,
            expected_version=1,
            operation_ref=delete_operation,
            idempotency_ref=delete_idempotency,
            approval=_approval(
                authority,
                action=ECO_TASK_MUTATION_ACTION,
                resources=_mutation_refs(
                    task_ref=task.task_ref,
                    operation_ref=delete_operation,
                    idempotency_ref=delete_idempotency,
                ),
            ),
        )

    archive_operation = "operation-ref:delete-archive"
    archive_idempotency = "idempotency-ref:delete-archive"
    repository.archive(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=1,
        operation_ref=archive_operation,
        idempotency_ref=archive_idempotency,
        approval=_approval(
            authority,
            action=ECO_TASK_MUTATION_ACTION,
            resources=_mutation_refs(
                task_ref=task.task_ref,
                operation_ref=archive_operation,
                idempotency_ref=archive_idempotency,
            ),
        ),
    )
    operation_ref = "operation-ref:delete"
    idempotency_ref = "idempotency-ref:delete"
    approval = _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=_mutation_refs(
            task_ref=task.task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    receipt = repository.delete(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=2,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=approval,
    )
    replay = repository.delete(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=2,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=approval,
    )
    assert replay.replayed is True
    assert replay.receipt_ref == receipt.receipt_ref


def test_legacy_local_task_preview_is_read_only_and_requires_private_title(
    tmp_path: Path,
) -> None:
    special_directory = tmp_path / "folder?#%encoded"
    special_directory.mkdir()
    source = (special_directory / "founder-loop.sqlite3").resolve()
    connection = sqlite3.connect(source)
    connection.execute(
        "CREATE TABLE local_tasks (local_task_ref TEXT PRIMARY KEY, item_ref TEXT, "
        "status TEXT, receipt_ref TEXT)"
    )
    connection.execute(
        "INSERT INTO local_tasks VALUES (?, ?, ?, ?)",
        (
            "local-task-ref:one",
            "item-ref:one",
            "local_task_created",
            "receipt-ref:one",
        ),
    )
    connection.commit()
    connection.close()
    before = source.read_bytes()
    reader = FounderLoopLocalTaskCompatibilityReader()
    first = reader.preview(source)
    second = reader.preview(source)
    assert first == second
    assert first.writes_performed is False
    assert first.private_task_content_recovered is False
    assert source.read_bytes() == before
    candidate = reader.prepare_candidate(
        candidate=first.candidates[0],
        workspace_ref=WORKSPACE,
        task_ref="task-ref:imported",
        title="Operator supplied private title",
    )
    assert candidate.title == "Operator supplied private title"
    assert candidate.provenance_refs == (
        "local-task-ref:one",
        "item-ref:one",
        "receipt-ref:one",
    )


def test_legacy_preview_redacts_filesystem_errors(tmp_path: Path, monkeypatch) -> None:
    source = (tmp_path / "founder-loop.sqlite3").resolve()
    source.touch()
    reader = FounderLoopLocalTaskCompatibilityReader()

    def unavailable(*_args, **_kwargs):
        raise OSError(f"sensitive path: {source}")

    monkeypatch.setattr(Path, "open", unavailable)
    with pytest.raises(TaskError) as error:
        reader.preview(source)

    assert str(error.value) == "ECO_TASK_MIGRATION_SOURCE_UNAVAILABLE"
    assert error.value.__cause__ is None
    assert str(source) not in str(error.value)
