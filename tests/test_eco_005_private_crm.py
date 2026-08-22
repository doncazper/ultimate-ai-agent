from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from ultimate_ai_agent.core.approvals.authority import LocalApprovalAuthority
from ultimate_ai_agent.core.approvals.enums import (
    ApprovalRiskLevel,
    ApprovalSubjectType,
)
from ultimate_ai_agent.core.approvals.requests import ApprovalRequest
from ultimate_ai_agent.core.crm.private_repository import (
    ECO_CRM_MUTATION_ACTION,
    CrmActivityKind,
    CrmFollowUpState,
    CrmPrivacyPolicy,
    CrmWorkspacePreset,
    PrivateCrmActivity,
    PrivateCrmConflict,
    PrivateCrmFollowUp,
    PrivateCrmPerson,
    PrivateCrmPipeline,
    PrivateCrmPipelineObject,
    PrivateCrmPortfolio,
    PrivateCrmRelationship,
    PrivateCrmRepository,
    PrivateCrmWorkspace,
    PrivateCrmWorkspaceContext,
)
from ultimate_ai_agent.core.ecosystem.boards import (
    ECO_BOARD_MUTATION_ACTION,
    Board,
    BoardLane,
    BoardRepository,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    EcosystemConflict,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    InMemoryLocalDataCryptoBackend,
    InMemoryLocalDataPathResolver,
    PutRecord,
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


WORKSPACE = "workspace-ref:crm-test"
PORTFOLIO = "crm-portfolio-ref:primary"
CRM_WORKSPACE = "crm-workspace-ref:sales"
BOARD = "board-ref:sales-pipeline"
_COUNTER = itertools.count(1)


def _approval(
    authority: LocalApprovalAuthority, *, action: str, resources: tuple[str, ...]
):
    suffix = next(_COUNTER)
    request = ApprovalRequest(
        approval_request_id=f"approval_request_eco005_{suffix}",
        run_id="run_eco_005_tests",
        subject_type=ApprovalSubjectType.kernel_task,
        subject_id=f"subject_eco005_{suffix}",
        actor_context=ActorContext(
            actor_type=ActorType.human_user,
            actor_id="actor_eco005_test",
            authority_source=AuthoritySource.foundation_test,
        ),
        requested_action=action,
        purpose="Verify one exact ECO-005 private CRM mutation.",
        risk_level=ApprovalRiskLevel.high,
        data_classification=DataClassification(
            classification=ClassificationValue.user_private,
            source="source-ref:eco-005-test",
            requires_redaction=True,
        ),
        resource_refs=list(resources),
        expires_at=utc_now() + timedelta(minutes=10),
    )
    authority.create_request(request)
    grant = authority.create_test_grant(
        request.approval_request_id, approval_ref=f"approval_eco005_{suffix}"
    )
    return request.to_validation_request(grant.approval_ref)


def _repositories(
    tmp_path: Path,
) -> tuple[PrivateCrmRepository, BoardRepository, LocalApprovalAuthority, Path]:
    authority = LocalApprovalAuthority()
    database_path = (tmp_path / "ecosystem.sqlite3").resolve()
    platform = EcosystemLocalDataPlatform(
        database_path=database_path,
        crypto_backend=InMemoryLocalDataCryptoBackend(),
        approval_authority=authority,
        path_resolver=InMemoryLocalDataPathResolver(),
    )
    key_ref = "key-version-ref:crm-v1"
    platform.create_workspace(
        workspace_ref=WORKSPACE,
        key_version_ref=key_ref,
        approval=_approval(
            authority,
            action="ecosystem.local_data.create_workspace",
            resources=(WORKSPACE, key_ref),
        ),
    )
    boards = BoardRepository(platform)
    return (
        PrivateCrmRepository(platform, board_repository=boards),
        boards,
        authority,
        database_path,
    )


def _resources(
    repository_type, *, record_ref: str, operation_ref: str, idempotency_ref: str
):
    return repository_type.mutation_resource_refs(
        workspace_ref=WORKSPACE,
        record_ref=record_ref,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
    )


def _mutate(repository, authority, method: str, *, version: int, **payload):
    operation_ref = f"operation-ref:{method}-{next(_COUNTER)}"
    idempotency_ref = f"idempotency-ref:{method}-{next(_COUNTER)}"
    return getattr(repository, method)(
        workspace_ref=WORKSPACE,
        portfolio_ref=PORTFOLIO,
        expected_version=version,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_CRM_MUTATION_ACTION,
            resources=_resources(
                PrivateCrmRepository,
                record_ref=PORTFOLIO,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
        **payload,
    )


def _create_board(boards: BoardRepository, authority: LocalApprovalAuthority) -> None:
    operation_ref = "operation-ref:create-crm-board"
    idempotency_ref = "idempotency-ref:create-crm-board"
    boards.create_board(
        board=Board(
            workspace_ref=WORKSPACE,
            board_ref=BOARD,
            name="Private sales pipeline",
            lanes=(
                BoardLane(lane_ref="lane-ref:lead", name="Lead", position=0),
                BoardLane(lane_ref="lane-ref:won", name="Won", position=1),
            ),
        ),
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_BOARD_MUTATION_ACTION,
            resources=_resources(
                BoardRepository,
                record_ref=BOARD,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )


def _create_portfolio(
    repository: PrivateCrmRepository, authority: LocalApprovalAuthority
):
    operation_ref = "operation-ref:create-crm-portfolio"
    idempotency_ref = "idempotency-ref:create-crm-portfolio"
    approval = _approval(
        authority,
        action=ECO_CRM_MUTATION_ACTION,
        resources=_resources(
            PrivateCrmRepository,
            record_ref=PORTFOLIO,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    portfolio = PrivateCrmPortfolio(
        workspace_ref=WORKSPACE,
        portfolio_ref=PORTFOLIO,
        name="Synthetic private CRM marker",
    )
    receipt = repository.create_portfolio(
        portfolio=portfolio,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=approval,
    )
    replay = repository.create_portfolio(
        portfolio=portfolio,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=approval,
    )
    assert replay.receipt_ref == receipt.receipt_ref
    return receipt


def test_private_relationship_preset_is_excluded_from_shared_surfaces() -> None:
    item = PrivateCrmWorkspace(
        crm_workspace_ref="crm-workspace-ref:private",
        name="Private relationships",
        preset=CrmWorkspacePreset.private_relationships,
    )
    assert item.privacy_policy.included_in_memory is False

    with pytest.raises(
        ValueError, match="ECO_CRM_PRIVATE_RELATIONSHIPS_ISOLATION_REQUIRED"
    ):
        PrivateCrmWorkspace(
            crm_workspace_ref="crm-workspace-ref:private",
            name="Private relationships",
            preset=CrmWorkspacePreset.private_relationships,
            privacy_policy=CrmPrivacyPolicy(included_in_today=True),
        )


def test_private_crm_builds_relationship_follow_up_and_board_owned_pipeline(
    tmp_path: Path,
) -> None:
    repository, boards, authority, database_path = _repositories(tmp_path)
    _create_board(boards, authority)
    receipt = _create_portfolio(repository, authority)
    assert receipt.replayed is False
    assert receipt.operation_receipt_refs

    version = 1
    _mutate(
        repository,
        authority,
        "add_workspace",
        version=version,
        item=PrivateCrmWorkspace(
            crm_workspace_ref=CRM_WORKSPACE,
            name="Sales",
            preset=CrmWorkspacePreset.sales,
        ),
    )
    version += 1
    for person_ref, name in (
        ("person-ref:one", "Synthetic One"),
        ("person-ref:two", "Synthetic Two"),
    ):
        _mutate(
            repository,
            authority,
            "add_person",
            version=version,
            item=PrivateCrmPerson(person_ref=person_ref, display_name=name),
        )
        version += 1
    for context_ref, person_ref in (
        ("context-ref:one", "person-ref:one"),
        ("context-ref:two", "person-ref:two"),
    ):
        _mutate(
            repository,
            authority,
            "add_context",
            version=version,
            item=PrivateCrmWorkspaceContext(
                context_ref=context_ref,
                crm_workspace_ref=CRM_WORKSPACE,
                person_ref=person_ref,
                notes="Private context marker",
            ),
        )
        version += 1
    _mutate(
        repository,
        authority,
        "add_relationship",
        version=version,
        item=PrivateCrmRelationship(
            relationship_ref="relationship-ref:one-two",
            crm_workspace_ref=CRM_WORKSPACE,
            from_context_ref="context-ref:one",
            to_context_ref="context-ref:two",
            relationship_type="Introduced by synthetic fixture",
        ),
    )
    version += 1
    _mutate(
        repository,
        authority,
        "add_activity",
        version=version,
        item=PrivateCrmActivity(
            activity_ref="activity-ref:meeting",
            crm_workspace_ref=CRM_WORKSPACE,
            context_refs=("context-ref:one", "context-ref:two"),
            kind=CrmActivityKind.meeting,
            occurred_at=datetime(2026, 8, 21, 16, tzinfo=timezone.utc),
            summary="Synthetic private meeting",
        ),
    )
    version += 1
    _mutate(
        repository,
        authority,
        "add_follow_up",
        version=version,
        item=PrivateCrmFollowUp(
            follow_up_ref="follow-up-ref:one",
            crm_workspace_ref=CRM_WORKSPACE,
            context_ref="context-ref:one",
            title="Synthetic private follow-up",
            due_at=datetime(2026, 8, 22, 16, tzinfo=timezone.utc),
        ),
    )
    version += 1
    _mutate(
        repository,
        authority,
        "add_pipeline_record",
        version=version,
        item=PrivateCrmPipeline(
            pipeline_ref="pipeline-ref:sales",
            crm_workspace_ref=CRM_WORKSPACE,
            board_ref=BOARD,
            name="Sales",
            object_kind="Opportunity",
        ),
    )
    version += 1

    operation_ref = "operation-ref:add-opportunity-card"
    idempotency_ref = "idempotency-ref:add-opportunity-card"
    boards.add_board_item(
        workspace_ref=WORKSPACE,
        board_ref=BOARD,
        card_ref="card-ref:opportunity",
        board_item_ref="pipeline-object-ref:opportunity",
        lane_ref="lane-ref:lead",
        title="Synthetic opportunity",
        expected_version=1,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_BOARD_MUTATION_ACTION,
            resources=_resources(
                BoardRepository,
                record_ref=BOARD,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )
    _mutate(
        repository,
        authority,
        "add_pipeline_object",
        version=version,
        item=PrivateCrmPipelineObject(
            pipeline_object_ref="pipeline-object-ref:opportunity",
            pipeline_ref="pipeline-ref:sales",
            context_ref="context-ref:one",
            board_ref=BOARD,
            card_ref="card-ref:opportunity",
            amount_minor=250_000,
            currency_ref="currency-ref:usd",
        ),
    )
    version += 1

    read_model = repository.workspace_read_model(
        workspace_ref=WORKSPACE,
        portfolio_ref=PORTFOLIO,
        crm_workspace_ref=CRM_WORKSPACE,
    )
    assert len(read_model.relationships) == 1
    assert len(read_model.activities) == 1
    assert read_model.pipeline_objects[0].lane_ref == "lane-ref:lead"
    first_result_ref = read_model.result_ref

    operation_ref = "operation-ref:move-opportunity"
    idempotency_ref = "idempotency-ref:move-opportunity"
    boards.move_card(
        workspace_ref=WORKSPACE,
        board_ref=BOARD,
        card_ref="card-ref:opportunity",
        lane_ref="lane-ref:won",
        position=0,
        expected_version=2,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_BOARD_MUTATION_ACTION,
            resources=_resources(
                BoardRepository,
                record_ref=BOARD,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )
    moved = repository.workspace_read_model(
        workspace_ref=WORKSPACE,
        portfolio_ref=PORTFOLIO,
        crm_workspace_ref=CRM_WORKSPACE,
    )
    assert moved.pipeline_objects[0].lane_ref == "lane-ref:won"
    assert moved.result_ref != first_result_ref

    operation_ref = "operation-ref:complete-follow-up"
    idempotency_ref = "idempotency-ref:complete-follow-up"
    approval = _approval(
        authority,
        action=ECO_CRM_MUTATION_ACTION,
        resources=_resources(
            PrivateCrmRepository,
            record_ref=PORTFOLIO,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
        ),
    )
    repository.complete_follow_up(
        workspace_ref=WORKSPACE,
        portfolio_ref=PORTFOLIO,
        expected_version=version,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=approval,
        follow_up_ref="follow-up-ref:one",
        completed_at=datetime(2026, 8, 22, 17, tzinfo=timezone.utc),
    )
    with pytest.raises(EcosystemConflict, match="ECO_IDEMPOTENCY_REPLAY_CONFLICT"):
        repository.complete_follow_up(
            workspace_ref=WORKSPACE,
            portfolio_ref=PORTFOLIO,
            expected_version=version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            follow_up_ref="follow-up-ref:one",
            completed_at=datetime(2026, 8, 22, 18, tzinfo=timezone.utc),
        )
    version += 1
    assert (
        repository.read(workspace_ref=WORKSPACE, portfolio_ref=PORTFOLIO)
        .follow_ups[0]
        .state
        == CrmFollowUpState.completed
    )

    _mutate(repository, authority, "undo", version=version)
    restored = repository.read(workspace_ref=WORKSPACE, portfolio_ref=PORTFOLIO)
    assert restored.follow_ups[0].state == CrmFollowUpState.open
    assert restored.version == version + 1
    database_bytes = database_path.read_bytes()
    assert b"Synthetic private CRM marker" not in database_bytes
    assert b"Synthetic private follow-up" not in database_bytes

    board = boards.read(workspace_ref=WORKSPACE, board_ref=BOARD)
    invalid_card = board.cards[0].model_copy(
        update={"subject_ref": "pipeline-object-ref:other"}
    )
    operation_ref = "operation-ref:invalidate-opportunity-card"
    idempotency_ref = "idempotency-ref:invalidate-opportunity-card"
    boards.save(
        board=board.model_copy(
            update={"version": board.version + 1, "cards": (invalid_card,)}
        ),
        expected_version=board.version,
        operation_ref=operation_ref,
        idempotency_ref=idempotency_ref,
        approval=_approval(
            authority,
            action=ECO_BOARD_MUTATION_ACTION,
            resources=_resources(
                BoardRepository,
                record_ref=BOARD,
                operation_ref=operation_ref,
                idempotency_ref=idempotency_ref,
            ),
        ),
    )
    with pytest.raises(
        PrivateCrmConflict,
        match="ECO_CRM_PIPELINE_OBJECT_CARD_BINDING_INVALID",
    ):
        repository.workspace_read_model(
            workspace_ref=WORKSPACE,
            portfolio_ref=PORTFOLIO,
            crm_workspace_ref=CRM_WORKSPACE,
        )


def test_pipeline_requires_existing_board_and_exact_card_binding(
    tmp_path: Path,
) -> None:
    repository, boards, authority, _database_path = _repositories(tmp_path)
    _create_portfolio(repository, authority)
    _mutate(
        repository,
        authority,
        "add_workspace",
        version=1,
        item=PrivateCrmWorkspace(
            crm_workspace_ref=CRM_WORKSPACE,
            name="Sales",
            preset=CrmWorkspacePreset.sales,
        ),
    )
    with pytest.raises(PrivateCrmConflict, match="ECO_CRM_PIPELINE_BOARD_NOT_FOUND"):
        _mutate(
            repository,
            authority,
            "add_pipeline_record",
            version=2,
            item=PrivateCrmPipeline(
                pipeline_ref="pipeline-ref:missing",
                crm_workspace_ref=CRM_WORKSPACE,
                board_ref="board-ref:missing",
                name="Missing",
                object_kind="Opportunity",
            ),
        )

    _create_board(boards, authority)
    _mutate(
        repository,
        authority,
        "add_pipeline_record",
        version=2,
        item=PrivateCrmPipeline(
            pipeline_ref="pipeline-ref:sales",
            crm_workspace_ref=CRM_WORKSPACE,
            board_ref=BOARD,
            name="Sales",
            object_kind="Opportunity",
        ),
    )


def test_generic_local_data_cannot_bypass_crm_repository(tmp_path: Path) -> None:
    repository, _boards, authority, _database_path = _repositories(tmp_path)
    portfolio = PrivateCrmPortfolio(
        workspace_ref=WORKSPACE,
        portfolio_ref=PORTFOLIO,
        name="Private",
    )
    operation_ref = "operation-ref:raw-crm"
    idempotency_ref = "idempotency-ref:raw-crm"
    with pytest.raises(
        EcosystemLocalDataError,
        match="ECO_MUTATION_REQUIRES_REPOSITORY_VALIDATION",
    ):
        repository.platform.apply(
            workspace_ref=WORKSPACE,
            idempotency_ref=idempotency_ref,
            operations=(
                PutRecord(
                    operation_ref=operation_ref,
                    module_ref="module-ref:crm",
                    record_ref=PORTFOLIO,
                    record_kind_ref="record-kind-ref:crm-private-portfolio",
                    safe_summary_ref=portfolio.safe_summary_ref,
                    private_payload=portfolio.model_dump(mode="json"),
                ),
            ),
            approval=_approval(
                authority,
                action=ECO_CRM_MUTATION_ACTION,
                resources=(WORKSPACE, idempotency_ref, operation_ref, PORTFOLIO),
            ),
            requested_action=ECO_CRM_MUTATION_ACTION,
        )
