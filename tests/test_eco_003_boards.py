from __future__ import annotations

import itertools
from datetime import timedelta
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.ecosystem.boards import (
    ECO_BOARD_MUTATION_ACTION,
    Board,
    BoardCard,
    BoardConflict,
    BoardLane,
    BoardRepository,
    BoardSubjectKind,
    BoardTemplate,
    SavedBoardFilter,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
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
    TaskRepository,
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


WORKSPACE = "workspace-ref:boards-test"
_COUNTER = itertools.count(1)


def _approval(
    authority: LocalApprovalAuthority,
    *,
    action: str,
    resources: tuple[str, ...],
):
    suffix = next(_COUNTER)
    request = ApprovalRequest(
        approval_request_id=f"approval_request_eco003_{suffix}",
        run_id="run_eco_003_tests",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_eco003_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco003_test",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify one exact ECO-003 local Board mutation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-003-test",
            requires_redaction=True,
        ),
        resource_refs=list(resources),
        expires_at=utc_now() + timedelta(minutes=10),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id,
        approval_ref=f"approval_eco003_{suffix}",
    )
    return request.to_validation_request(grant.approval_ref)


def _repositories(
    tmp_path: Path,
) -> tuple[BoardRepository, TaskRepository, LocalApprovalAuthority, Path]:
    authority = LocalApprovalAuthority()
    database_path = (tmp_path / "ecosystem.sqlite3").resolve()
    platform = EcosystemLocalDataPlatform(
        database_path=database_path,
        crypto_backend=InMemoryLocalDataCryptoBackend(),
        approval_authority=authority,
        path_resolver=InMemoryLocalDataPathResolver(),
    )
    key_ref = "key-version-ref:boards-v1"
    platform.create_workspace(
        workspace_ref=WORKSPACE,
        key_version_ref=key_ref,
        approval=_approval(
            authority,
            action="ecosystem.local_data.create_workspace",
            resources=(WORKSPACE, key_ref),
        ),
    )
    tasks = TaskRepository(platform)
    return (
        BoardRepository(platform, task_repository=tasks),
        tasks,
        authority,
        database_path,
    )


def _board() -> Board:
    return Board(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        name="Private board name",
        description="Private board description",
        lanes=(
            BoardLane(lane_ref="lane-ref:todo", name="To do", position=0),
            BoardLane(lane_ref="lane-ref:done", name="Done", position=1),
        ),
    )


def _resources(
    *, record_ref: str, operation_ref: str, idempotency_ref: str
) -> tuple[str, ...]:
    return BoardRepository.mutation_resource_refs(
        workspace_ref=WORKSPACE,
        idempotency_ref=idempotency_ref,
        operation_ref=operation_ref,
        record_ref=record_ref,
    )


def _board_approval(
    authority: LocalApprovalAuthority,
    *,
    record_ref: str,
    operation_ref: str,
    idempotency_ref: str,
):
    return _approval(
        authority,
        action=ECO_BOARD_MUTATION_ACTION,
        resources=_resources(
            record_ref=record_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )


def _create_board(
    repository: BoardRepository,
    authority: LocalApprovalAuthority,
    board: Board | None = None,
):
    board = board or _board()
    operation_ref = "operation-ref:create-board"
    idempotency_ref = "idempotency-ref:create-board"
    return repository.create_board(
        board=board,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref=board.board_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )


def _task_approval(
    authority: LocalApprovalAuthority,
    *,
    task_ref: str,
    operation_ref: str,
    idempotency_ref: str,
):
    return _approval(
        authority,
        action=ECO_TASK_MUTATION_ACTION,
        resources=TaskRepository.mutation_resource_refs(
            workspace_ref=WORKSPACE,
            task_ref=task_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )


def test_board_core_is_encrypted_and_domain_action_bound(tmp_path: Path) -> None:
    repository, _tasks, authority, database_path = _repositories(tmp_path)
    receipt = _create_board(repository, authority)
    assert receipt.replayed is False
    assert (
        repository.read(workspace_ref=WORKSPACE, board_ref="board-ref:one") == _board()
    )
    at_rest = database_path.read_bytes()
    wal = database_path.with_name(f"{database_path.name}-wal")
    if wal.exists():
        at_rest += wal.read_bytes()
    assert b"Private board name" not in at_rest
    assert b"Private board description" not in at_rest

    board = _board().model_copy(update={"board_ref": "board-ref:bypass"})
    operation = PutRecord(
        operation_ref="operation-ref:bypass",
        module_ref="module-ref:boards",
        record_ref=board.board_ref,
        record_kind_ref="record-kind-ref:canonical-board",
        safe_summary_ref=board.safe_summary_ref,
        private_payload=board.model_dump(mode="json"),
        search_terms=("entity-kind:canonical-board",),
    )
    resources = (
        WORKSPACE,
        "idempotency-ref:bypass",
        operation.operation_ref,
        board.board_ref,
    )
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_REQUIRES_DOMAIN_ACTION"
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref="idempotency-ref:bypass",
            operations=(operation,),
            approval=_approval(
                authority,
                action="ecosystem.local_data.apply",
                resources=resources,
            ),
        )
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_REQUIRES_REPOSITORY_VALIDATION"
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref="idempotency-ref:raw-board-action",
            operations=(
                PutRecord(
                    **{
                        **vars(operation),
                        "operation_ref": "operation-ref:raw-board-action",
                    }
                ),
            ),
            approval=_approval(
                authority,
                action=ECO_BOARD_MUTATION_ACTION,
                resources=(
                    WORKSPACE,
                    "idempotency-ref:raw-board-action",
                    "operation-ref:raw-board-action",
                    board.board_ref,
                ),
            ),
            requested_action=ECO_BOARD_MUTATION_ACTION,
            request_context_ref="board-request-context-ref:raw-denied",
        )


def test_board_action_cannot_claim_task_records(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    operation = PutRecord(
        operation_ref="operation-ref:claim-task",
        module_ref="module-ref:tasks",
        record_ref="task-ref:claimed",
        record_kind_ref="record-kind-ref:canonical-task",
        safe_summary_ref="task-summary-ref:claimed",
        private_payload={"value": "private"},
    )
    idempotency_ref = "idempotency-ref:claim-task"
    with pytest.raises(
        EcosystemLocalDataError, match="ECO_MUTATION_ACTION_DOMAIN_SCOPE_INVALID"
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=idempotency_ref,
            operations=(operation,),
            approval=_approval(
                authority,
                action=ECO_BOARD_MUTATION_ACTION,
                resources=(
                    WORKSPACE,
                    idempotency_ref,
                    operation.operation_ref,
                    operation.record_ref,
                ),
            ),
            requested_action=ECO_BOARD_MUTATION_ACTION,
            request_context_ref="board-request-context-ref:foreign-denied",
        )


def test_lane_card_order_filter_and_undo_are_versioned(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_board(repository, authority)

    operation_ref = "operation-ref:add-item"
    idempotency_ref = "idempotency-ref:add-item"
    receipt = repository.add_board_item(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        card_ref="card-ref:item-one",
        board_item_ref="board-item-ref:one",
        lane_ref="lane-ref:todo",
        title="Private item title",
        description="Private item notes",
        label_refs=("label-ref:important",),
        expected_version=1,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    assert receipt.replayed is False

    operation_ref = "operation-ref:move-item"
    idempotency_ref = "idempotency-ref:move-item"
    repository.move_card(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        card_ref="card-ref:item-one",
        lane_ref="lane-ref:done",
        position=0,
        expected_version=2,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    moved = repository.read(workspace_ref=WORKSPACE, board_ref="board-ref:one")
    assert moved.version == 3
    assert moved.cards[0].lane_ref == "lane-ref:done"
    assert len(moved.undo_stack) == 2

    operation_ref = "operation-ref:undo-move"
    idempotency_ref = "idempotency-ref:undo-move"
    repository.undo(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        expected_version=3,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    restored = repository.read(workspace_ref=WORKSPACE, board_ref="board-ref:one")
    assert restored.version == 4
    assert restored.cards[0].lane_ref == "lane-ref:todo"
    assert len(restored.undo_stack) == 1

    saved_filter = SavedBoardFilter(
        filter_ref="filter-ref:important",
        name="Important",
        lane_refs=("lane-ref:todo",),
        label_refs=("label-ref:important",),
    )
    operation_ref = "operation-ref:save-filter"
    idempotency_ref = "idempotency-ref:save-filter"
    repository.save_filter(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        saved_filter=saved_filter,
        expected_version=4,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    read_model = repository.read_model(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        filter_ref=saved_filter.filter_ref,
    )
    assert tuple(item.card.card_ref for item in read_model.cards) == (
        "card-ref:item-one",
    )


def test_exact_replay_survives_later_board_mutation(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    _create_board(repository, authority)
    add_operation = "operation-ref:add-replay-item"
    add_idempotency = "idempotency-ref:add-replay-item"

    def add_item():
        return repository.add_board_item(
            workspace_ref=WORKSPACE,
            board_ref="board-ref:one",
            card_ref="card-ref:replay-item",
            board_item_ref="board-item-ref:replay-item",
            lane_ref="lane-ref:todo",
            title="Replay item",
            expected_version=1,
            operation_ref=add_operation,
            idempotency_ref=add_idempotency,
            approval=_board_approval(
                authority,
                record_ref="board-ref:one",
                operation_ref=add_operation,
                idempotency_ref=add_idempotency,
            ),
        )

    assert add_item().replayed is False
    move_operation = "operation-ref:later-move"
    move_idempotency = "idempotency-ref:later-move"
    repository.move_card(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        card_ref="card-ref:replay-item",
        lane_ref="lane-ref:done",
        position=0,
        expected_version=2,
        operation_ref=move_operation,
        idempotency_ref=move_idempotency,
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref=move_operation,
            idempotency_ref=move_idempotency,
        ),
    )
    assert add_item().replayed is True
    assert (
        repository.read(workspace_ref=WORKSPACE, board_ref="board-ref:one").version == 3
    )


def test_task_cards_resolve_live_truth_without_copying_it(tmp_path: Path) -> None:
    repository, tasks, authority, database_path = _repositories(tmp_path)
    task = CanonicalTask(
        workspace_ref=WORKSPACE,
        task_ref="task-ref:projected",
        title="Canonical private task title",
    )
    task_operation = "operation-ref:create-task"
    task_idempotency = "idempotency-ref:create-task"
    tasks.create(
        task=task,
        operation_ref=task_operation,
        idempotency_ref=task_idempotency,
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref=task_operation,
            idempotency_ref=task_idempotency,
        ),
    )
    _create_board(repository, authority)

    operation_ref = "operation-ref:add-task-card"
    idempotency_ref = "idempotency-ref:add-task-card"
    repository.add_task_projection(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        card_ref="card-ref:projected-task",
        task_ref=task.task_ref,
        lane_ref="lane-ref:todo",
        expected_version=1,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    board = repository.read(workspace_ref=WORKSPACE, board_ref="board-ref:one")
    card = board.cards[0]
    assert card.subject_kind == BoardSubjectKind.task
    assert card.title is None
    assert card.description is None
    projected = repository.read_model(
        workspace_ref=WORKSPACE, board_ref="board-ref:one"
    ).cards[0]
    assert projected.canonical_task == task
    assert projected.canonical_owner_ref == "canonical-owner-ref:tasks"
    assert projected.projection_state == "current"
    assert b"Canonical private task title" not in database_path.read_bytes()


def test_deleted_task_projection_is_explicit_and_does_not_freeze_board(
    tmp_path: Path,
) -> None:
    repository, tasks, authority, _database_path = _repositories(tmp_path)
    task = CanonicalTask(
        workspace_ref=WORKSPACE,
        task_ref="task-ref:later-deleted",
        title="Task that will be deleted",
    )
    task_operation = "operation-ref:create-later-deleted"
    task_idempotency = "idempotency-ref:create-later-deleted"
    tasks.create(
        task=task,
        operation_ref=task_operation,
        idempotency_ref=task_idempotency,
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref=task_operation,
            idempotency_ref=task_idempotency,
        ),
    )
    _create_board(repository, authority)
    operation_ref = "operation-ref:add-later-deleted"
    idempotency_ref = "idempotency-ref:add-later-deleted"
    repository.add_task_projection(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        card_ref="card-ref:later-deleted",
        task_ref=task.task_ref,
        lane_ref="lane-ref:todo",
        expected_version=1,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    archive_operation = "operation-ref:archive-later-deleted"
    archive_idempotency = "idempotency-ref:archive-later-deleted"
    tasks.archive(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=1,
        operation_ref=archive_operation,
        idempotency_ref=archive_idempotency,
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref=archive_operation,
            idempotency_ref=archive_idempotency,
        ),
    )
    archived_projection = repository.read_model(
        workspace_ref=WORKSPACE, board_ref="board-ref:one"
    ).cards[0]
    assert archived_projection.projection_state == "archived"
    delete_operation = "operation-ref:delete-later-deleted"
    delete_idempotency = "idempotency-ref:delete-later-deleted"
    tasks.delete(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=2,
        operation_ref=delete_operation,
        idempotency_ref=delete_idempotency,
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref=delete_operation,
            idempotency_ref=delete_idempotency,
        ),
    )
    missing_projection = repository.read_model(
        workspace_ref=WORKSPACE, board_ref="board-ref:one"
    ).cards[0]
    assert missing_projection.projection_state == "missing"
    assert missing_projection.canonical_task is None

    operation_ref = "operation-ref:add-lane-after-delete"
    idempotency_ref = "idempotency-ref:add-lane-after-delete"
    repository.add_lane(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        lane_ref="lane-ref:blocked",
        name="Blocked",
        expected_version=2,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    assert (
        repository.read(workspace_ref=WORKSPACE, board_ref="board-ref:one").version == 3
    )


def test_invalid_task_shadow_missing_task_and_stale_write_fail_closed(
    tmp_path: Path,
) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    with pytest.raises(
        ValueError, match="ECO_BOARD_TASK_PROJECTION_CANNOT_COPY_TASK_TRUTH"
    ):
        BoardCard(
            card_ref="card-ref:bad-task",
            subject_kind=BoardSubjectKind.task,
            subject_ref="task-ref:missing",
            lane_ref="lane-ref:todo",
            position=0,
            title="Copied task title",
        )
    _create_board(repository, authority)
    operation_ref = "operation-ref:missing-task"
    idempotency_ref = "idempotency-ref:missing-task"
    with pytest.raises(EcosystemLocalDataError, match="ECO_RECORD_NOT_FOUND"):
        repository.add_task_projection(
            workspace_ref=WORKSPACE,
            board_ref="board-ref:one",
            card_ref="card-ref:missing-task",
            task_ref="task-ref:missing",
            lane_ref="lane-ref:todo",
            expected_version=1,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=_board_approval(
                authority,
                record_ref="board-ref:one",
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        )
    with pytest.raises(BoardConflict, match="ECO_BOARD_STALE_VERSION"):
        repository.add_lane(
            workspace_ref=WORKSPACE,
            board_ref="board-ref:one",
            lane_ref="lane-ref:later",
            name="Later",
            expected_version=2,
            operation_ref="operation-ref:stale",
            idempotency_ref="idempotency-ref:stale",
            approval=_board_approval(
                authority,
                record_ref="board-ref:one",
                operation_ref="operation-ref:stale",
                idempotency_ref="idempotency-ref:stale",
            ),
        )


def test_templates_instantiate_configuration_without_live_coupling(
    tmp_path: Path,
) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    template = BoardTemplate(
        workspace_ref=WORKSPACE,
        template_ref="board-template-ref:basic",
        name="Basic board",
        lanes=(
            BoardLane(lane_ref="lane-ref:backlog", name="Backlog", position=0),
            BoardLane(lane_ref="lane-ref:doing", name="Doing", position=1),
        ),
    )
    operation_ref = "operation-ref:create-template"
    idempotency_ref = "idempotency-ref:create-template"
    repository.create_template(
        template=template,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref=template.template_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    operation_ref = "operation-ref:instantiate-template"
    idempotency_ref = "idempotency-ref:instantiate-template"
    repository.instantiate_template(
        workspace_ref=WORKSPACE,
        template_ref=template.template_ref,
        board_ref="board-ref:from-template",
        name="Private instantiated board",
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_board_approval(
            authority,
            record_ref="board-ref:from-template",
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    board = repository.read(
        workspace_ref=WORKSPACE, board_ref="board-ref:from-template"
    )
    assert board.template_ref == template.template_ref
    assert tuple(lane.lane_ref for lane in board.lanes) == (
        "lane-ref:backlog",
        "lane-ref:doing",
    )


def test_wip_and_contiguous_order_invariants_fail_closed() -> None:
    with pytest.raises(ValueError, match="ECO_BOARD_WIP_LIMIT_EXCEEDED"):
        Board(
            workspace_ref=WORKSPACE,
            board_ref="board-ref:wip",
            name="WIP",
            lanes=(
                BoardLane(
                    lane_ref="lane-ref:wip",
                    name="Doing",
                    position=0,
                    wip_limit=1,
                ),
            ),
            cards=(
                BoardCard(
                    card_ref="card-ref:one",
                    subject_kind=BoardSubjectKind.board_item,
                    subject_ref="board-item-ref:one",
                    lane_ref="lane-ref:wip",
                    position=0,
                    title="One",
                ),
                BoardCard(
                    card_ref="card-ref:two",
                    subject_kind=BoardSubjectKind.board_item,
                    subject_ref="board-item-ref:two",
                    lane_ref="lane-ref:wip",
                    position=1,
                    title="Two",
                ),
            ),
        )


def test_large_board_trims_undo_history_and_remains_mutable(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    board = Board(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:large-undo",
        name="Large undo board",
        lanes=(BoardLane(lane_ref="lane-ref:large", name="Large", position=0),),
        cards=(
            BoardCard(
                card_ref="card-ref:large",
                subject_kind=BoardSubjectKind.board_item,
                subject_ref="board-item-ref:large",
                lane_ref="lane-ref:large",
                position=0,
                title="Large item",
                description="x" * 65_536,
            ),
        ),
    )
    _create_board(repository, authority, board)

    for index in range(1, 23):
        current = repository.read(workspace_ref=WORKSPACE, board_ref=board.board_ref)
        desired = current.model_copy(
            update={"name": f"Large undo board {index}", "version": current.version + 1}
        )
        operation_ref = f"operation-ref:large-save-{index}"
        idempotency_ref = f"idempotency-ref:large-save-{index}"
        repository.save(
            board=desired,
            expected_version=current.version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=_board_approval(
                authority,
                record_ref=board.board_ref,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        )

    current = repository.read(workspace_ref=WORKSPACE, board_ref=board.board_ref)
    assert current.version == 23
    assert 0 < len(current.undo_stack) < 20


def test_undo_restores_a_task_projection_after_task_deletion(tmp_path: Path) -> None:
    repository, tasks, authority, _database_path = _repositories(tmp_path)
    task = CanonicalTask(
        workspace_ref=WORKSPACE,
        task_ref="task-ref:undo-deleted",
        title="Task deleted before undo",
    )
    tasks.create(
        task=task,
        operation_ref="operation-ref:create-undo-task",
        idempotency_ref="idempotency-ref:create-undo-task",
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref="operation-ref:create-undo-task",
            idempotency_ref="idempotency-ref:create-undo-task",
        ),
    )
    _create_board(repository, authority)
    repository.add_task_projection(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        card_ref="card-ref:undo-deleted",
        task_ref=task.task_ref,
        lane_ref="lane-ref:todo",
        expected_version=1,
        operation_ref="operation-ref:add-undo-task",
        idempotency_ref="idempotency-ref:add-undo-task",
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref="operation-ref:add-undo-task",
            idempotency_ref="idempotency-ref:add-undo-task",
        ),
    )
    current = repository.read(workspace_ref=WORKSPACE, board_ref="board-ref:one")
    repository.save(
        board=current.model_copy(update={"cards": (), "version": 3}),
        expected_version=2,
        operation_ref="operation-ref:remove-undo-task",
        idempotency_ref="idempotency-ref:remove-undo-task",
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref="operation-ref:remove-undo-task",
            idempotency_ref="idempotency-ref:remove-undo-task",
        ),
    )
    tasks.archive(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=1,
        operation_ref="operation-ref:archive-undo-task",
        idempotency_ref="idempotency-ref:archive-undo-task",
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref="operation-ref:archive-undo-task",
            idempotency_ref="idempotency-ref:archive-undo-task",
        ),
    )
    tasks.delete(
        workspace_ref=WORKSPACE,
        task_ref=task.task_ref,
        expected_version=2,
        operation_ref="operation-ref:delete-undo-task",
        idempotency_ref="idempotency-ref:delete-undo-task",
        approval=_task_approval(
            authority,
            task_ref=task.task_ref,
            operation_ref="operation-ref:delete-undo-task",
            idempotency_ref="idempotency-ref:delete-undo-task",
        ),
    )
    repository.undo(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:one",
        expected_version=3,
        operation_ref="operation-ref:undo-deleted-task",
        idempotency_ref="idempotency-ref:undo-deleted-task",
        approval=_board_approval(
            authority,
            record_ref="board-ref:one",
            operation_ref="operation-ref:undo-deleted-task",
            idempotency_ref="idempotency-ref:undo-deleted-task",
        ),
    )
    projection = repository.read_model(
        workspace_ref=WORKSPACE, board_ref="board-ref:one"
    ).cards[0]
    assert projection.card.subject_ref == task.task_ref
    assert projection.projection_state == "missing"


def test_move_preserves_declared_target_lane_order(tmp_path: Path) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    board = Board(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:unordered-tuple",
        name="Logical order",
        lanes=(
            BoardLane(lane_ref="lane-ref:source", name="Source", position=0),
            BoardLane(lane_ref="lane-ref:target", name="Target", position=1),
        ),
        cards=(
            BoardCard(
                card_ref="card-ref:moving",
                subject_kind=BoardSubjectKind.board_item,
                subject_ref="board-item-ref:moving",
                lane_ref="lane-ref:source",
                position=0,
                title="Moving",
            ),
            BoardCard(
                card_ref="card-ref:target-second",
                subject_kind=BoardSubjectKind.board_item,
                subject_ref="board-item-ref:target-second",
                lane_ref="lane-ref:target",
                position=1,
                title="Second",
            ),
            BoardCard(
                card_ref="card-ref:target-first",
                subject_kind=BoardSubjectKind.board_item,
                subject_ref="board-item-ref:target-first",
                lane_ref="lane-ref:target",
                position=0,
                title="First",
            ),
        ),
    )
    _create_board(repository, authority, board)
    repository.move_card(
        workspace_ref=WORKSPACE,
        board_ref=board.board_ref,
        card_ref="card-ref:moving",
        lane_ref="lane-ref:target",
        position=2,
        expected_version=1,
        operation_ref="operation-ref:move-logical-order",
        idempotency_ref="idempotency-ref:move-logical-order",
        approval=_board_approval(
            authority,
            record_ref=board.board_ref,
            operation_ref="operation-ref:move-logical-order",
            idempotency_ref="idempotency-ref:move-logical-order",
        ),
    )
    moved = repository.read(workspace_ref=WORKSPACE, board_ref=board.board_ref)
    assert tuple(card.card_ref for card in moved.cards) == (
        "card-ref:target-first",
        "card-ref:target-second",
        "card-ref:moving",
    )


def test_mutation_validation_and_atomic_stale_write_use_board_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _tasks, authority, _database_path = _repositories(tmp_path)
    board = Board(
        workspace_ref=WORKSPACE,
        board_ref="board-ref:wip-mutation",
        name="WIP mutation",
        lanes=(
            BoardLane(
                lane_ref="lane-ref:limited",
                name="Limited",
                position=0,
                wip_limit=1,
            ),
        ),
        cards=(
            BoardCard(
                card_ref="card-ref:existing",
                subject_kind=BoardSubjectKind.board_item,
                subject_ref="board-item-ref:existing",
                lane_ref="lane-ref:limited",
                position=0,
                title="Existing",
            ),
        ),
    )
    _create_board(repository, authority, board)
    with pytest.raises(BoardConflict, match="ECO_BOARD_WIP_LIMIT_EXCEEDED"):
        repository.add_board_item(
            workspace_ref=WORKSPACE,
            board_ref=board.board_ref,
            card_ref="card-ref:overflow",
            board_item_ref="board-item-ref:overflow",
            lane_ref="lane-ref:limited",
            title="Overflow",
            expected_version=1,
            operation_ref="operation-ref:wip-overflow",
            idempotency_ref="idempotency-ref:wip-overflow",
            approval=_board_approval(
                authority,
                record_ref=board.board_ref,
                operation_ref="operation-ref:wip-overflow",
                idempotency_ref="idempotency-ref:wip-overflow",
            ),
        )

    def reject_atomic_write(**_kwargs):
        raise EcosystemConflict("ECO_STALE_RECORD_VERSION")

    monkeypatch.setattr(
        repository.platform, "_apply_registered_domain", reject_atomic_write
    )
    with pytest.raises(BoardConflict, match="ECO_BOARD_STALE_VERSION"):
        repository.add_lane(
            workspace_ref=WORKSPACE,
            board_ref=board.board_ref,
            lane_ref="lane-ref:later",
            name="Later",
            expected_version=1,
            operation_ref="operation-ref:atomic-stale",
            idempotency_ref="idempotency-ref:atomic-stale",
            approval=_board_approval(
                authority,
                record_ref=board.board_ref,
                operation_ref="operation-ref:atomic-stale",
                idempotency_ref="idempotency-ref:atomic-stale",
            ),
        )
