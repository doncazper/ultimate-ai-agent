from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

import ultimate_ai_agent.core.ecosystem.changesets as changesets_module
from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.boards import (
    ECO_BOARD_MODULE_REF,
    ECO_BOARD_RECORD_KIND_REF,
    Board,
    BoardLane,
)
from ultimate_ai_agent.core.ecosystem.calendar import (
    ECO_CALENDAR_MODULE_REF,
    ECO_CALENDAR_RECORD_KIND_REF,
    CalendarSet,
    LocalCalendar,
)
from ultimate_ai_agent.core.ecosystem.changesets import (
    ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
    ChangeSetConflict,
    ChangeSetEngine,
    ChangeSetError,
    EntityLinkRepository,
    ExternalOutcomeObservation,
    LocalUpdateIntent,
)
from ultimate_ai_agent.core.ecosystem.contracts import (
    AtomicityPosture,
    CanonicalEntityRef,
    CanonicalOwnerId,
    ChangeOperation,
    ChangeSetPlan,
    CompensationPlan,
    ConflictPrecondition,
    EntityKind,
    EntityLink,
    EntityLinkKind,
    EntityVersion,
    OperationResultStatus,
    WorkspaceScope,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    DeleteRecord,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
    PutRecord,
)
from ultimate_ai_agent.core.ecosystem.tasks import (
    ECO_TASK_MODULE_REF,
    ECO_TASK_OCCURRENCE_RECORD_KIND_REF,
    ECO_TASK_RECORD_KIND_REF,
    CanonicalTask,
    TaskStatus,
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


WORKSPACE_REF = "workspace-ref:q19"
WORKSPACE = WorkspaceScope(workspace_ref=WORKSPACE_REF)


class ApprovalHarness:
    def __init__(self) -> None:
        self.authority = LocalApprovalAuthority()
        self.counter = 0

    def grant(self, action: str, resources: tuple[str, ...]):
        self.counter += 1
        request = ApprovalRequest(
            approval_request_id=f"approval_request_q19_{self.counter}",
            run_id="run_q19_tests",
            subject_type=ApprovalSubjectType.kernel_task,
            subject_id=f"subject_q19_{self.counter}",
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id="actor_q19_test",
                authority_source=AuthoritySource.foundation_test,
            ),
            requested_action=action,
            purpose="Verify exact ECO-008 local mutation scope.",
            risk_level=ApprovalRiskLevel.high,
            data_classification=DataClassification(
                classification=ClassificationValue.user_private,
                source="source-ref:q19-test",
                requires_redaction=True,
            ),
            resource_refs=list(resources),
            expires_at=utc_now() + timedelta(minutes=10),
        )
        self.authority.create_request(request)
        grant = self.authority.create_test_grant(
            request.approval_request_id,
            approval_ref=f"approval_q19_{self.counter}",
        )
        return request.to_validation_request(grant.approval_ref)


def _platform(
    tmp_path: Path,
    *,
    backend: InMemoryLocalDataCryptoBackend | None = None,
    fault_hook=None,
) -> tuple[EcosystemLocalDataPlatform, ApprovalHarness]:
    harness = ApprovalHarness()
    platform = EcosystemLocalDataPlatform(
        database_path=(tmp_path / "ecosystem.sqlite3").resolve(),
        crypto_backend=backend or InMemoryLocalDataCryptoBackend(),
        approval_authority=harness.authority,
        path_resolver=InMemoryLocalDataPathResolver(),
        fault_hook=fault_hook,
    )
    key_version = "key-version-ref:v1"
    platform.create_workspace(
        workspace_ref=WORKSPACE_REF,
        key_version_ref=key_version,
        approval=harness.grant(
            "ecosystem.local_data.create_workspace",
            (WORKSPACE_REF, key_version),
        ),
    )
    return platform, harness


def _seed(
    platform: EcosystemLocalDataPlatform,
    harness: ApprovalHarness,
    *,
    operation: PutRecord,
    action: str,
    idempotency_ref: str,
) -> None:
    resources = tuple(
        dict.fromkeys(
            (
                WORKSPACE_REF,
                idempotency_ref,
                operation.operation_ref,
                operation.record_ref,
            )
        )
    )
    platform._apply_registered_domain(
        workspace_ref=WORKSPACE_REF,
        idempotency_ref=idempotency_ref,
        operations=(operation,),
        approval=harness.grant(action, resources),
        requested_action=action,
        request_context_ref=f"request-context-ref:{operation.operation_ref}",
    )


def _task(
    *,
    task_ref: str = "task-ref:q19",
    title: str = "Original private task",
    status: TaskStatus = TaskStatus.inbox,
    dependency_refs: tuple[str, ...] = (),
    version: int = 1,
) -> CanonicalTask:
    return CanonicalTask(
        workspace_ref=WORKSPACE_REF,
        task_ref=task_ref,
        title=title,
        status=status,
        dependency_refs=dependency_refs,
        version=version,
    )


def _calendar(
    *, name: str = "Original private calendar", version: int = 1
) -> CalendarSet:
    return CalendarSet(
        workspace_ref=WORKSPACE_REF,
        calendar_set_ref="calendar-set-ref:q19",
        name=name,
        calendars=(LocalCalendar(calendar_ref="calendar-ref:q19", name="Primary"),),
        version=version,
    )


def _board(*, name: str = "Original private board", version: int = 1) -> Board:
    return Board(
        workspace_ref=WORKSPACE_REF,
        board_ref="board-ref:q19",
        name=name,
        lanes=(BoardLane(lane_ref="lane-ref:q19", name="Ready", position=0),),
        version=version,
    )


def _seed_core_records(
    platform: EcosystemLocalDataPlatform, harness: ApprovalHarness
) -> None:
    task = _task()
    calendar = _calendar()
    board = _board()
    _seed(
        platform,
        harness,
        operation=PutRecord(
            operation_ref="operation-ref:seed-task",
            module_ref=ECO_TASK_MODULE_REF,
            record_ref=task.task_ref,
            record_kind_ref=ECO_TASK_RECORD_KIND_REF,
            safe_summary_ref=task.safe_summary_ref,
            private_payload=task.model_dump(mode="json"),
            search_terms=("entity-kind:canonical-task", "task-status:inbox"),
            retention_ref="retention-ref:tasks-operator-managed",
        ),
        action="ecosystem.tasks.apply",
        idempotency_ref="idempotency-ref:seed-task",
    )
    _seed(
        platform,
        harness,
        operation=PutRecord(
            operation_ref="operation-ref:seed-calendar",
            module_ref=ECO_CALENDAR_MODULE_REF,
            record_ref=calendar.calendar_set_ref,
            record_kind_ref=ECO_CALENDAR_RECORD_KIND_REF,
            safe_summary_ref=calendar.safe_summary_ref,
            private_payload=calendar.model_dump(mode="json"),
            search_terms=("entity-kind:calendar-set",),
            retention_ref="retention-ref:calendar-operator-managed",
        ),
        action="ecosystem.calendar.apply",
        idempotency_ref="idempotency-ref:seed-calendar",
    )
    _seed(
        platform,
        harness,
        operation=PutRecord(
            operation_ref="operation-ref:seed-board",
            module_ref=ECO_BOARD_MODULE_REF,
            record_ref=board.board_ref,
            record_kind_ref=ECO_BOARD_RECORD_KIND_REF,
            safe_summary_ref=board.safe_summary_ref,
            private_payload=board.model_dump(mode="json"),
            search_terms=("entity-kind:canonical-board",),
            retention_ref="retention-ref:boards-operator-managed",
        ),
        action="ecosystem.boards.apply",
        idempotency_ref="idempotency-ref:seed-board",
    )


def _prepared(engine: ChangeSetEngine):
    updated_task = _task(title="Updated private task", version=2)
    updated_calendar = _calendar(name="Updated private calendar", version=2)
    updated_board = _board(name="Updated private board", version=2)
    return engine.prepare_local(
        workspace=WORKSPACE,
        change_set_ref="change-set-ref:q19-golden",
        intents=(
            LocalUpdateIntent(
                operation_ref="operation-ref:q19-update-task",
                record_ref=updated_task.task_ref,
                entity_kind=EntityKind.task,
                module_ref=ECO_TASK_MODULE_REF,
                record_kind_ref=ECO_TASK_RECORD_KIND_REF,
                capability_ref="capability-ref:q19-task-update",
                replacement_payload=updated_task.model_dump(mode="json"),
                search_terms=("entity-kind:canonical-task", "task-status:inbox"),
                retention_ref="retention-ref:tasks-operator-managed",
            ),
            LocalUpdateIntent(
                operation_ref="operation-ref:q19-update-calendar",
                record_ref=updated_calendar.calendar_set_ref,
                entity_kind=EntityKind.calendar_set,
                module_ref=ECO_CALENDAR_MODULE_REF,
                record_kind_ref=ECO_CALENDAR_RECORD_KIND_REF,
                capability_ref="capability-ref:q19-calendar-update",
                replacement_payload=updated_calendar.model_dump(mode="json"),
                search_terms=("entity-kind:calendar-set",),
                retention_ref="retention-ref:calendar-operator-managed",
                depends_on=("operation-ref:q19-update-task",),
            ),
            LocalUpdateIntent(
                operation_ref="operation-ref:q19-update-board",
                record_ref=updated_board.board_ref,
                entity_kind=EntityKind.board,
                module_ref=ECO_BOARD_MODULE_REF,
                record_kind_ref=ECO_BOARD_RECORD_KIND_REF,
                capability_ref="capability-ref:q19-board-update",
                replacement_payload=updated_board.model_dump(mode="json"),
                search_terms=("entity-kind:canonical-board",),
                retention_ref="retention-ref:boards-operator-managed",
                depends_on=("operation-ref:q19-update-calendar",),
            ),
        ),
        approval_scope_ref="approval-scope-ref:q19-golden",
        idempotency_ref="idempotency-ref:q19-golden",
        expiry_ref="expiry-ref:q19-reviewed",
        predicted_result_ref="predicted-result-ref:q19-two-updates",
    )


def test_local_changeset_applies_replays_and_rolls_back_exactly(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    prepared = _prepared(engine)

    assert len(prepared.plan.operations) == 3
    assert {item.field_ref for item in prepared.field_diffs} >= {
        "field-ref:canonical-task:title",
        "field-ref:calendar-set:name",
        "field-ref:canonical-board:name",
    }
    prepared_repr = repr(prepared)
    plan_json = prepared.plan.model_dump_json()
    for private_fragment in ("Original private", "Updated private"):
        assert private_fragment not in prepared_repr
        assert private_fragment not in plan_json
    assert all(not item.raw_value_included for item in prepared.field_diffs)

    resources = engine.mutation_resource_refs(
        prepared, idempotency_ref=prepared.plan.idempotency_ref
    )
    receipt = engine.apply_local(
        prepared,
        idempotency_ref=prepared.plan.idempotency_ref,
        approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
    )
    assert receipt.replayed is False
    assert [item.status for item in receipt.operation_results] == [
        OperationResultStatus.applied,
        OperationResultStatus.applied,
        OperationResultStatus.applied,
    ]
    assert _task_record(platform).title == "Updated private task"
    assert _calendar_record(platform).name == "Updated private calendar"
    assert _board_record(platform).name == "Updated private board"

    replay = engine.apply_local(
        prepared,
        idempotency_ref=prepared.plan.idempotency_ref,
        approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
    )
    assert replay.replayed is True
    assert replay.uow_receipt_ref == receipt.uow_receipt_ref
    assert all(
        item.status == OperationResultStatus.replayed
        for item in replay.operation_results
    )

    undo = engine.prepare_undo(
        workspace_ref=WORKSPACE_REF,
        change_set_ref=prepared.plan.change_set_ref,
    )
    undo_idempotency = "idempotency-ref:q19-golden-rollback"
    undo_resources = engine.mutation_resource_refs(
        undo, idempotency_ref=undo_idempotency
    )
    forged_undo_operation = replace(
        undo._operations[0], expires_at="2030-01-01T00:00:00Z"
    )
    forged_undo = replace(
        undo,
        _operations=(forged_undo_operation, *undo._operations[1:]),
    )
    with pytest.raises(ChangeSetConflict, match="ECO_CHANGESET_ROLLBACK_SCOPE_INVALID"):
        engine.rollback(
            forged_undo,
            idempotency_ref=undo_idempotency,
            approval=harness.grant(
                ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
                engine.mutation_resource_refs(
                    forged_undo, idempotency_ref=undo_idempotency
                ),
            ),
        )
    rolled_back = engine.rollback(
        undo,
        idempotency_ref=undo_idempotency,
        approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, undo_resources),
    )
    assert rolled_back.state.value == "rolled_back"
    assert _task_record(platform).title == "Original private task"
    assert _task_record(platform).version == 3
    assert _calendar_record(platform).name == "Original private calendar"
    assert _calendar_record(platform).version == 3
    assert _board_record(platform).name == "Original private board"
    assert _board_record(platform).version == 3

    rollback_replay = engine.rollback(
        undo,
        idempotency_ref=undo_idempotency,
        approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, undo_resources),
    )
    assert rollback_replay.replayed is True
    with pytest.raises(
        ChangeSetConflict, match="ECO_CHANGESET_ROLLBACK_LEDGER_INVALID"
    ):
        engine.prepare_undo(
            workspace_ref=WORKSPACE_REF,
            change_set_ref=prepared.plan.change_set_ref,
        )


def _task_record(platform: EcosystemLocalDataPlatform) -> CanonicalTask:
    return CanonicalTask.model_validate(
        platform.read(
            workspace_ref=WORKSPACE_REF, record_ref="task-ref:q19"
        ).private_payload
    )


def _calendar_record(platform: EcosystemLocalDataPlatform) -> CalendarSet:
    return CalendarSet.model_validate(
        platform.read(
            workspace_ref=WORKSPACE_REF, record_ref="calendar-set-ref:q19"
        ).private_payload
    )


def _board_record(platform: EcosystemLocalDataPlatform) -> Board:
    return Board.model_validate(
        platform.read(
            workspace_ref=WORKSPACE_REF, record_ref="board-ref:q19"
        ).private_payload
    )


def test_stale_precondition_blocks_the_entire_changeset(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    prepared = _prepared(engine)

    independently_updated = _task(title="Independent private update", version=2)
    _seed(
        platform,
        harness,
        operation=PutRecord(
            operation_ref="operation-ref:independent-task-update",
            module_ref=ECO_TASK_MODULE_REF,
            record_ref=independently_updated.task_ref,
            record_kind_ref=ECO_TASK_RECORD_KIND_REF,
            safe_summary_ref=independently_updated.safe_summary_ref,
            private_payload=independently_updated.model_dump(mode="json"),
            search_terms=("entity-kind:canonical-task", "task-status:inbox"),
            expected_version=1,
        ),
        action="ecosystem.tasks.apply",
        idempotency_ref="idempotency-ref:independent-task-update",
    )
    resources = engine.mutation_resource_refs(
        prepared, idempotency_ref=prepared.plan.idempotency_ref
    )
    with pytest.raises(
        ChangeSetConflict, match="ECO_CHANGESET_CONFLICT_PRECONDITION_FAILED"
    ):
        engine.apply_local(
            prepared,
            idempotency_ref=prepared.plan.idempotency_ref,
            approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
        )
    assert _task_record(platform).title == "Independent private update"
    assert _calendar_record(platform).version == 1
    with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
        platform.read(
            workspace_ref=WORKSPACE_REF,
            record_ref=prepared.plan.change_set_ref,
        )


def test_injected_failure_rolls_back_every_domain_and_ledger_write(
    tmp_path: Path,
) -> None:
    enabled = False
    applied = 0

    def fault_hook(stage: str) -> None:
        nonlocal applied
        if enabled and stage.startswith("operation-applied"):
            applied += 1
            if applied == 2:
                raise RuntimeError("synthetic-q19-fault")

    platform, harness = _platform(tmp_path, fault_hook=fault_hook)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    prepared = _prepared(engine)
    resources = engine.mutation_resource_refs(
        prepared, idempotency_ref=prepared.plan.idempotency_ref
    )
    enabled = True
    with pytest.raises(RuntimeError, match="synthetic-q19-fault"):
        engine.apply_local(
            prepared,
            idempotency_ref=prepared.plan.idempotency_ref,
            approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
        )
    assert _task_record(platform).version == 1
    assert _calendar_record(platform).version == 1
    with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
        platform.read(
            workspace_ref=WORKSPACE_REF,
            record_ref=prepared.plan.change_set_ref,
        )


def _entity_ref(
    *, entity_ref: str, kind: EntityKind, owner: CanonicalOwnerId
) -> CanonicalEntityRef:
    return CanonicalEntityRef(
        entity_ref=entity_ref,
        entity_kind=kind,
        canonical_owner=owner,
        workspace=WORKSPACE,
        entity_version=EntityVersion(
            version=1,
            fingerprint_ref=f"fingerprint-ref:{entity_ref}",
        ),
    )


def test_entity_links_are_typed_removable_and_do_not_mutate_endpoints(
    tmp_path: Path,
) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    repository = EntityLinkRepository(platform)
    link = EntityLink(
        link_ref="entity-link-ref:q19-task-board",
        link_kind=EntityLinkKind.projects,
        source=_entity_ref(
            entity_ref="task-ref:q19",
            kind=EntityKind.task,
            owner=CanonicalOwnerId.tasks,
        ),
        target=_entity_ref(
            entity_ref="board-ref:q19",
            kind=EntityKind.board,
            owner=CanonicalOwnerId.boards,
        ),
        workspace=WORKSPACE,
        provenance_ref="provenance-ref:q19-operator-reviewed",
        deletion_posture_ref="deletion-posture-ref:q19-link-only",
    )
    create_idempotency = "idempotency-ref:q19-link-create"
    create_resources = repository.mutation_resource_refs(
        workspace_ref=WORKSPACE_REF,
        idempotency_ref=create_idempotency,
        operation_ref="operation-ref:q19-link-create",
        link=link,
    )
    altered_link = link.model_copy(update={"link_kind": EntityLinkKind.relates_to})
    with pytest.raises(EcosystemLocalDataError, match="ECO_APPROVAL_SCOPE_INVALID"):
        repository.create(
            link=altered_link,
            operation_ref="operation-ref:q19-link-create",
            idempotency_ref=create_idempotency,
            approval=harness.grant("ecosystem.changesets.apply", create_resources),
        )
    repository.create(
        link=link,
        operation_ref="operation-ref:q19-link-create",
        idempotency_ref=create_idempotency,
        approval=harness.grant("ecosystem.changesets.apply", create_resources),
    )
    assert repository.list(workspace_ref=WORKSPACE_REF)[0].link == link

    remove_idempotency = "idempotency-ref:q19-link-remove"
    remove_resources = repository.mutation_resource_refs(
        workspace_ref=WORKSPACE_REF,
        idempotency_ref=remove_idempotency,
        operation_ref="operation-ref:q19-link-remove",
        link=link,
    )
    removed = repository.remove(
        link=link,
        expected_version=1,
        operation_ref="operation-ref:q19-link-remove",
        idempotency_ref=remove_idempotency,
        approval=harness.grant("ecosystem.changesets.apply", remove_resources),
    )
    replay = repository.remove(
        link=link,
        expected_version=1,
        operation_ref="operation-ref:q19-link-remove",
        idempotency_ref=remove_idempotency,
        approval=harness.grant("ecosystem.changesets.apply", remove_resources),
    )
    assert removed.replayed is False
    assert replay.replayed is True
    assert _task_record(platform).version == 1
    assert (
        Board.model_validate(
            platform.read(
                workspace_ref=WORKSPACE_REF, record_ref="board-ref:q19"
            ).private_payload
        ).version
        == 1
    )
    with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
        repository.read(workspace_ref=WORKSPACE_REF, link_ref=link.link_ref)


def test_prepared_scope_and_domain_boundary_fail_closed(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    prepared = _prepared(engine)
    forged = replace(prepared, scope_fingerprint_ref="change-set-scope-ref:forged")
    resources = engine.mutation_resource_refs(
        forged, idempotency_ref=forged.plan.idempotency_ref
    )
    with pytest.raises(ChangeSetConflict, match="ECO_CHANGESET_PREPARED_SCOPE_INVALID"):
        engine.apply_local(
            forged,
            idempotency_ref=forged.plan.idempotency_ref,
            approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
        )

    forged_mutation = replace(prepared._mutations[0], expires_at="2030-01-01T00:00:00Z")
    forged_persistence = replace(
        prepared,
        _mutations=(forged_mutation, *prepared._mutations[1:]),
    )
    forged_resources = engine.mutation_resource_refs(
        forged_persistence,
        idempotency_ref=forged_persistence.plan.idempotency_ref,
    )
    with pytest.raises(ChangeSetConflict, match="ECO_CHANGESET_PREPARED_SCOPE_INVALID"):
        engine.apply_local(
            forged_persistence,
            idempotency_ref=forged_persistence.plan.idempotency_ref,
            approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, forged_resources),
        )

    unsupported = PutRecord(
        operation_ref="operation-ref:q19-unsupported",
        module_ref="module-ref:crm",
        record_ref="portfolio-ref:q19",
        record_kind_ref="record-kind-ref:crm-private-portfolio",
        safe_summary_ref="summary-ref:q19-unsupported",
        private_payload={"unsafe": "domain bypass"},
    )
    unsupported_idempotency = "idempotency-ref:q19-unsupported"
    unsupported_resources = (
        WORKSPACE_REF,
        unsupported_idempotency,
        unsupported.operation_ref,
        unsupported.record_ref,
    )
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID"
    ):
        platform._apply_registered_domain(
            workspace_ref=WORKSPACE_REF,
            idempotency_ref=unsupported_idempotency,
            operations=(unsupported,),
            approval=harness.grant(
                ECO_CHANGESET_LOCAL_ATOMIC_ACTION, unsupported_resources
            ),
            requested_action=ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
            request_context_ref="request-context-ref:q19-unsupported",
        )

    new_task = CanonicalTask(
        workspace_ref=WORKSPACE_REF,
        task_ref="task-ref:q19-unscoped-create",
        title="Private create must stay denied",
    )
    unscoped_create = PutRecord(
        operation_ref="operation-ref:q19-unscoped-create",
        module_ref=ECO_TASK_MODULE_REF,
        record_ref=new_task.task_ref,
        record_kind_ref=ECO_TASK_RECORD_KIND_REF,
        safe_summary_ref=new_task.safe_summary_ref,
        private_payload=new_task.model_dump(mode="json"),
        search_terms=("entity-kind:canonical-task", "task-status:inbox"),
        retention_ref="retention-ref:tasks-operator-managed",
    )
    create_idempotency = "idempotency-ref:q19-unscoped-create"
    create_resources = (
        WORKSPACE_REF,
        create_idempotency,
        unscoped_create.operation_ref,
        unscoped_create.record_ref,
    )
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID"
    ):
        platform._apply_registered_domain(
            workspace_ref=WORKSPACE_REF,
            idempotency_ref=create_idempotency,
            operations=(unscoped_create,),
            approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, create_resources),
            requested_action=ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
            request_context_ref="request-context-ref:q19-unscoped-create",
        )

    unscoped_delete = DeleteRecord(
        operation_ref="operation-ref:q19-unscoped-delete",
        record_ref="task-ref:q19",
        expected_version=1,
    )
    delete_idempotency = "idempotency-ref:q19-unscoped-delete"
    delete_resources = (
        WORKSPACE_REF,
        delete_idempotency,
        unscoped_delete.operation_ref,
        unscoped_delete.record_ref,
    )
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_CHANGESET_LOCAL_ATOMIC_PUT_REQUIRED"
    ):
        platform._apply_registered_domain(
            workspace_ref=WORKSPACE_REF,
            idempotency_ref=delete_idempotency,
            operations=(unscoped_delete,),
            approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, delete_resources),
            requested_action=ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
            request_context_ref="request-context-ref:q19-unscoped-delete",
        )

    kind_swap = PutRecord(
        operation_ref="operation-ref:q19-kind-swap",
        module_ref=ECO_TASK_MODULE_REF,
        record_ref="task-ref:q19",
        record_kind_ref=ECO_TASK_OCCURRENCE_RECORD_KIND_REF,
        safe_summary_ref=_task().safe_summary_ref,
        private_payload=_task().model_dump(mode="json"),
        search_terms=("entity-kind:canonical-task", "task-status:inbox"),
        expected_version=1,
        retention_ref="retention-ref:tasks-operator-managed",
    )
    kind_swap_idempotency = "idempotency-ref:q19-kind-swap"
    kind_swap_resources = (
        WORKSPACE_REF,
        kind_swap_idempotency,
        kind_swap.operation_ref,
        kind_swap.record_ref,
    )
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID"
    ):
        platform._apply_registered_domain(
            workspace_ref=WORKSPACE_REF,
            idempotency_ref=kind_swap_idempotency,
            operations=(kind_swap,),
            approval=harness.grant(
                ECO_CHANGESET_LOCAL_ATOMIC_ACTION, kind_swap_resources
            ),
            requested_action=ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
            request_context_ref="request-context-ref:q19-kind-swap",
        )


def test_exact_approval_order_and_no_effect_guards(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    prepared = _prepared(engine)
    resources = engine.mutation_resource_refs(
        prepared, idempotency_ref=prepared.plan.idempotency_ref
    )
    with pytest.raises(EcosystemLocalDataError, match="ECO_APPROVAL_SCOPE_INVALID"):
        engine.apply_local(
            prepared,
            idempotency_ref=prepared.plan.idempotency_ref,
            approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources[:-1]),
        )

    version_only = _task(version=2)
    with pytest.raises(
        ChangeSetConflict, match="ECO_CHANGESET_NO_EFFECT_OPERATION_DENIED"
    ):
        engine.prepare_local(
            workspace=WORKSPACE,
            change_set_ref="change-set-ref:q19-no-effect",
            intents=(
                LocalUpdateIntent(
                    operation_ref="operation-ref:q19-no-effect",
                    record_ref=version_only.task_ref,
                    entity_kind=EntityKind.task,
                    module_ref=ECO_TASK_MODULE_REF,
                    record_kind_ref=ECO_TASK_RECORD_KIND_REF,
                    capability_ref="capability-ref:q19-task-update",
                    replacement_payload=version_only.model_dump(mode="json"),
                    search_terms=(
                        "entity-kind:canonical-task",
                        "task-status:inbox",
                    ),
                    retention_ref="retention-ref:tasks-operator-managed",
                ),
            ),
            approval_scope_ref="approval-scope-ref:q19-no-effect",
            idempotency_ref="idempotency-ref:q19-no-effect",
            expiry_ref="expiry-ref:q19-no-effect",
            predicted_result_ref="predicted-result-ref:q19-no-effect",
        )

    updated_calendar = _calendar(name="Out of order", version=2)
    with pytest.raises(ChangeSetError, match="ECO_CHANGESET_OPERATION_ORDER_INVALID"):
        engine.prepare_local(
            workspace=WORKSPACE,
            change_set_ref="change-set-ref:q19-order",
            intents=(
                LocalUpdateIntent(
                    operation_ref="operation-ref:q19-order-calendar",
                    record_ref=updated_calendar.calendar_set_ref,
                    entity_kind=EntityKind.calendar_set,
                    module_ref=ECO_CALENDAR_MODULE_REF,
                    record_kind_ref=ECO_CALENDAR_RECORD_KIND_REF,
                    capability_ref="capability-ref:q19-calendar-update",
                    replacement_payload=updated_calendar.model_dump(mode="json"),
                    search_terms=("entity-kind:calendar-set",),
                    retention_ref="retention-ref:calendar-operator-managed",
                    depends_on=("operation-ref:q19-order-task",),
                ),
            ),
            approval_scope_ref="approval-scope-ref:q19-order",
            idempotency_ref="idempotency-ref:q19-order",
            expiry_ref="expiry-ref:q19-order",
            predicted_result_ref="predicted-result-ref:q19-order",
        )


def test_duplicate_targets_are_rejected_before_prepare(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    updated = _task(title="Updated private task", version=2)

    with pytest.raises(ChangeSetError, match="ECO_CHANGESET_DUPLICATE_TARGET_REF"):
        engine.prepare_local(
            workspace=WORKSPACE,
            change_set_ref="change-set-ref:q19-duplicate-target",
            intents=(
                LocalUpdateIntent(
                    operation_ref="operation-ref:q19-duplicate-one",
                    record_ref=updated.task_ref,
                    entity_kind=EntityKind.task,
                    module_ref=ECO_TASK_MODULE_REF,
                    record_kind_ref=ECO_TASK_RECORD_KIND_REF,
                    capability_ref="capability-ref:q19-task-update",
                    replacement_payload=updated.model_dump(mode="json"),
                    search_terms=("entity-kind:canonical-task", "task-status:inbox"),
                    retention_ref="retention-ref:tasks-operator-managed",
                ),
                LocalUpdateIntent(
                    operation_ref="operation-ref:q19-duplicate-two",
                    record_ref=updated.task_ref,
                    entity_kind=EntityKind.task,
                    module_ref=ECO_TASK_MODULE_REF,
                    record_kind_ref=ECO_TASK_RECORD_KIND_REF,
                    capability_ref="capability-ref:q19-task-update",
                    replacement_payload=updated.model_dump(mode="json"),
                    search_terms=("entity-kind:canonical-task", "task-status:inbox"),
                    retention_ref="retention-ref:tasks-operator-managed",
                ),
            ),
            approval_scope_ref="approval-scope-ref:q19-duplicate-target",
            idempotency_ref="idempotency-ref:q19-duplicate-target",
            expiry_ref="expiry-ref:q19-duplicate-target",
            predicted_result_ref="predicted-result-ref:q19-duplicate-target",
        )


def test_combined_task_updates_reject_a_cycle(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    second = _task(task_ref="task-ref:q19-second", title="Second private task")
    _seed(
        platform,
        harness,
        operation=PutRecord(
            operation_ref="operation-ref:seed-second-task",
            module_ref=ECO_TASK_MODULE_REF,
            record_ref=second.task_ref,
            record_kind_ref=ECO_TASK_RECORD_KIND_REF,
            safe_summary_ref=second.safe_summary_ref,
            private_payload=second.model_dump(mode="json"),
            search_terms=("entity-kind:canonical-task", "task-status:inbox"),
            retention_ref="retention-ref:tasks-operator-managed",
        ),
        action="ecosystem.tasks.apply",
        idempotency_ref="idempotency-ref:seed-second-task",
    )
    first_update = _task(
        dependency_refs=(second.task_ref,),
        title="First updated private task",
        version=2,
    )
    second_update = _task(
        task_ref=second.task_ref,
        dependency_refs=(first_update.task_ref,),
        title="Second updated private task",
        version=2,
    )

    with pytest.raises(ChangeSetConflict, match="ECO_CHANGESET_TASK_GRAPH_INVALID"):
        ChangeSetEngine(platform).prepare_local(
            workspace=WORKSPACE,
            change_set_ref="change-set-ref:q19-cycle",
            intents=tuple(
                LocalUpdateIntent(
                    operation_ref=f"operation-ref:q19-cycle-{index}",
                    record_ref=task.task_ref,
                    entity_kind=EntityKind.task,
                    module_ref=ECO_TASK_MODULE_REF,
                    record_kind_ref=ECO_TASK_RECORD_KIND_REF,
                    capability_ref="capability-ref:q19-task-update",
                    replacement_payload=task.model_dump(mode="json"),
                    search_terms=("entity-kind:canonical-task", "task-status:inbox"),
                    retention_ref="retention-ref:tasks-operator-managed",
                )
                for index, task in enumerate((first_update, second_update), start=1)
            ),
            approval_scope_ref="approval-scope-ref:q19-cycle",
            idempotency_ref="idempotency-ref:q19-cycle",
            expiry_ref="expiry-ref:q19-cycle",
            predicted_result_ref="predicted-result-ref:q19-cycle",
        )


def test_rollback_restores_prior_search_terms(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    updated = _task(status=TaskStatus.ready, version=2)
    prepared = engine.prepare_local(
        workspace=WORKSPACE,
        change_set_ref="change-set-ref:q19-search-rollback",
        intents=(
            LocalUpdateIntent(
                operation_ref="operation-ref:q19-search-rollback",
                record_ref=updated.task_ref,
                entity_kind=EntityKind.task,
                module_ref=ECO_TASK_MODULE_REF,
                record_kind_ref=ECO_TASK_RECORD_KIND_REF,
                capability_ref="capability-ref:q19-task-update",
                replacement_payload=updated.model_dump(mode="json"),
                search_terms=("entity-kind:canonical-task", "task-status:ready"),
                retention_ref="retention-ref:tasks-operator-managed",
            ),
        ),
        approval_scope_ref="approval-scope-ref:q19-search-rollback",
        idempotency_ref="idempotency-ref:q19-search-rollback",
        expiry_ref="expiry-ref:q19-search-rollback",
        predicted_result_ref="predicted-result-ref:q19-search-rollback",
    )
    resources = engine.mutation_resource_refs(
        prepared, idempotency_ref=prepared.plan.idempotency_ref
    )
    engine.apply_local(
        prepared,
        idempotency_ref=prepared.plan.idempotency_ref,
        approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
    )
    assert platform.search(workspace_ref=WORKSPACE_REF, term="task-status:ready") == (
        updated.task_ref,
    )
    undo = engine.prepare_undo(
        workspace_ref=WORKSPACE_REF,
        change_set_ref=prepared.plan.change_set_ref,
    )
    rollback_idempotency = "idempotency-ref:q19-search-rollback-undo"
    rollback_resources = engine.mutation_resource_refs(
        undo, idempotency_ref=rollback_idempotency
    )
    engine.rollback(
        undo,
        idempotency_ref=rollback_idempotency,
        approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, rollback_resources),
    )
    assert platform.search(workspace_ref=WORKSPACE_REF, term="task-status:inbox") == (
        updated.task_ref,
    )
    assert platform.search(workspace_ref=WORKSPACE_REF, term="task-status:ready") == ()


def test_prepare_rejects_oversized_rollback_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    monkeypatch.setattr(
        changesets_module, "ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES", 1
    )

    with pytest.raises(
        ChangeSetError, match="ECO_CHANGESET_ROLLBACK_LEDGER_SIZE_LIMIT_EXCEEDED"
    ):
        _prepared(ChangeSetEngine(platform))


def test_restart_replays_apply_and_retains_exact_rollback(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    prepared = _prepared(engine)
    resources = engine.mutation_resource_refs(
        prepared, idempotency_ref=prepared.plan.idempotency_ref
    )
    engine.apply_local(
        prepared,
        idempotency_ref=prepared.plan.idempotency_ref,
        approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
    )
    new_key_version_ref = "key-version-ref:q19-rotated"
    platform.rotate_workspace_key(
        workspace_ref=WORKSPACE_REF,
        new_key_version_ref=new_key_version_ref,
        approval=harness.grant(
            "ecosystem.local_data.rotate_workspace_key",
            (WORKSPACE_REF, new_key_version_ref),
        ),
    )

    reopened_harness = ApprovalHarness()
    reopened = EcosystemLocalDataPlatform(
        database_path=platform.database_path,
        crypto_backend=platform.crypto_backend,
        approval_authority=reopened_harness.authority,
        path_resolver=InMemoryLocalDataPathResolver(),
    )
    reopened_engine = ChangeSetEngine(reopened)
    replay = reopened_engine.apply_local(
        prepared,
        idempotency_ref=prepared.plan.idempotency_ref,
        approval=reopened_harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
    )
    assert replay.replayed is True
    undo = reopened_engine.prepare_undo(
        workspace_ref=WORKSPACE_REF,
        change_set_ref=prepared.plan.change_set_ref,
    )
    rollback_idempotency = "idempotency-ref:q19-restart-rollback"
    rollback_resources = reopened_engine.mutation_resource_refs(
        undo, idempotency_ref=rollback_idempotency
    )
    reopened_engine.rollback(
        undo,
        idempotency_ref=rollback_idempotency,
        approval=reopened_harness.grant(
            ECO_CHANGESET_LOCAL_ATOMIC_ACTION, rollback_resources
        ),
    )
    assert _task_record(reopened).title == "Original private task"
    assert _calendar_record(reopened).name == "Original private calendar"
    assert _board_record(reopened).name == "Original private board"


def test_external_outcomes_are_projection_only_with_compensation_refs(
    tmp_path: Path,
) -> None:
    platform, _harness = _platform(tmp_path)
    before = platform.integrity_check().record_count
    target = _entity_ref(
        entity_ref="task-ref:q19-external",
        kind=EntityKind.task,
        owner=CanonicalOwnerId.tasks,
    )
    first = ChangeOperation(
        operation_ref="operation-ref:q19-external-one",
        target=target,
        capability_ref="capability-ref:q19-external-one",
        operation_fingerprint_ref="operation-fingerprint-ref:q19-external-one",
        atomicity_posture=AtomicityPosture.external_compensating,
        conflict_precondition=ConflictPrecondition(
            target_ref=target.entity_ref,
            expected_version=target.entity_version,
        ),
        compensation_plan=CompensationPlan(
            plan_ref="compensation-plan-ref:q19-external-one",
            target_ref=target.entity_ref,
            capability_ref="capability-ref:q19-external-one-compensate",
            plan_fingerprint_ref="compensation-fingerprint-ref:q19-external-one",
        ),
    )
    second = ChangeOperation(
        operation_ref="operation-ref:q19-external-two",
        target=target.model_copy(update={"entity_ref": "task-ref:q19-external-two"}),
        capability_ref="capability-ref:q19-external-two",
        operation_fingerprint_ref="operation-fingerprint-ref:q19-external-two",
        depends_on=(first.operation_ref,),
        atomicity_posture=AtomicityPosture.external_compensating,
        conflict_precondition=ConflictPrecondition(
            target_ref="task-ref:q19-external-two",
            expected_version=target.entity_version,
        ),
        compensation_plan=CompensationPlan(
            plan_ref="compensation-plan-ref:q19-external-two",
            target_ref="task-ref:q19-external-two",
            capability_ref="capability-ref:q19-external-two-compensate",
            plan_fingerprint_ref="compensation-fingerprint-ref:q19-external-two",
        ),
    )
    plan = ChangeSetPlan(
        change_set_ref="change-set-ref:q19-external",
        change_set_fingerprint_ref="change-set-fingerprint-ref:q19-external",
        workspace=WORKSPACE,
        operations=(first, second),
        approval_scope_ref="approval-scope-ref:q19-external",
        idempotency_ref="idempotency-ref:q19-external",
        expiry_ref="expiry-ref:q19-external",
        predicted_result_ref="predicted-result-ref:q19-external",
    )
    projection = ChangeSetEngine.project_external_outcomes(
        plan,
        (
            ExternalOutcomeObservation(
                operation_ref=first.operation_ref,
                status=OperationResultStatus.applied,
                observed_receipt_ref="receipt-ref:q19-external-one",
            ),
            ExternalOutcomeObservation(
                operation_ref=second.operation_ref,
                status=OperationResultStatus.failed,
            ),
        ),
    )
    assert projection.partial_completion is True
    assert projection.compensation_plan_refs == (
        "compensation-plan-ref:q19-external-one",
    )
    assert projection.external_execution_performed is False
    assert projection.local_mutation_performed is False
    assert platform.integrity_check().record_count == before


def test_private_changeset_payloads_remain_encrypted_at_rest(tmp_path: Path) -> None:
    platform, harness = _platform(tmp_path)
    _seed_core_records(platform, harness)
    engine = ChangeSetEngine(platform)
    prepared = _prepared(engine)
    resources = engine.mutation_resource_refs(
        prepared, idempotency_ref=prepared.plan.idempotency_ref
    )
    engine.apply_local(
        prepared,
        idempotency_ref=prepared.plan.idempotency_ref,
        approval=harness.grant(ECO_CHANGESET_LOCAL_ATOMIC_ACTION, resources),
    )
    database = (tmp_path / "ecosystem.sqlite3").read_bytes()
    wal_path = tmp_path / "ecosystem.sqlite3-wal"
    wal = wal_path.read_bytes() if wal_path.exists() else b""
    assert b"Original private task" not in database + wal
    assert b"Updated private calendar" not in database + wal
