from __future__ import annotations

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.work_board import WorkBoardReadModel
from ultimate_ai_agent.core.crm.contracts import CrmAuthorityBoundary
from ultimate_ai_agent.core.ecosystem import (
    CANONICAL_OWNER_BY_ENTITY_KIND,
    CANONICAL_OWNERSHIP_REGISTRY,
    AppId,
    AtomicityPosture,
    BoardProjection,
    CardSubject,
    CapabilityCatalogRelationship,
    CanonicalEntityRef,
    CanonicalOwnerId,
    CanonicalOwnershipAssignment,
    CanonicalOwnershipRegistry,
    ChangeOperation,
    ChangeSetPlan,
    ConflictPrecondition,
    CompensationPlan,
    EntityKind,
    EntityLink,
    EntityLinkKind,
    EntityVersion,
    PrivacyScope,
    ProductAcceptanceStatus,
    ProductRenderAcceptance,
    Projection,
    RollbackPlan,
    SourceProvenance,
    StandaloneAppMaturity,
    WorkspaceScope,
    canonical_owner_for,
    validate_unique_canonical_ownership,
)


def _version(number: int = 1) -> EntityVersion:
    return EntityVersion(
        version=number,
        fingerprint_ref=f"fingerprint-ref:eco-test:v{number}",
    )


def _workspace(
    ref: str = "workspace-ref:eco-test:work",
    privacy: PrivacyScope = PrivacyScope.workspace,
) -> WorkspaceScope:
    allowed = (ref,) if privacy == PrivacyScope.restricted_private else ()
    return WorkspaceScope(
        workspace_ref=ref,
        privacy_scope=privacy,
        allowed_workspace_refs=allowed,
    )


def _entity(
    kind: EntityKind = EntityKind.task,
    *,
    workspace: WorkspaceScope | None = None,
) -> CanonicalEntityRef:
    return CanonicalEntityRef(
        entity_ref=f"entity-ref:eco-test:{kind.value}",
        entity_kind=kind,
        canonical_owner=canonical_owner_for(kind),
        workspace=workspace or _workspace(),
        entity_version=_version(),
    )


def _operation(
    ref: str,
    *,
    depends_on: tuple[str, ...] = (),
    posture: AtomicityPosture = AtomicityPosture.local_atomic,
) -> ChangeOperation:
    target = _entity(EntityKind.task)
    return ChangeOperation(
        operation_ref=ref,
        target=target,
        capability_ref="capability-ref:eco-test:task-write",
        operation_fingerprint_ref=f"fingerprint-ref:{ref}",
        depends_on=depends_on,
        atomicity_posture=posture,
        conflict_precondition=ConflictPrecondition(
            target_ref=target.entity_ref,
            expected_version=_version(),
        ),
        rollback_plan=(
            RollbackPlan(
                plan_ref="rollback-plan-ref:eco-test:task",
                target_ref=target.entity_ref,
                capability_ref="capability-ref:eco-test:task-rollback",
                plan_fingerprint_ref="fingerprint-ref:eco-test:task-rollback",
            )
            if posture == AtomicityPosture.local_atomic
            else None
        ),
        compensation_plan=(
            CompensationPlan(
                plan_ref="compensation-plan-ref:eco-test:external",
                target_ref=target.entity_ref,
                capability_ref="capability-ref:eco-test:external-compensate",
                plan_fingerprint_ref="fingerprint-ref:eco-test:external-compensate",
            )
            if posture == AtomicityPosture.external_compensating
            else None
        ),
    )


def _change_set(*operations: ChangeOperation) -> ChangeSetPlan:
    return ChangeSetPlan(
        change_set_ref="change-set-ref:eco-test:one",
        change_set_fingerprint_ref="fingerprint-ref:eco-test:change-set",
        workspace=_workspace(),
        operations=operations,
        approval_scope_ref="approval-scope-ref:eco-test:change-set",
        idempotency_ref="idempotency-ref:eco-test:change-set",
        expiry_ref="expiry-ref:eco-test:bounded",
        predicted_result_ref="prediction-ref:eco-test:review-only",
    )


def test_canonical_ownership_is_total_unique_and_locked() -> None:
    validate_unique_canonical_ownership(CANONICAL_OWNER_BY_ENTITY_KIND)
    assert set(CANONICAL_OWNER_BY_ENTITY_KIND) == set(EntityKind)
    assert canonical_owner_for(EntityKind.event) == CanonicalOwnerId.calendar
    assert canonical_owner_for(EntityKind.task) == CanonicalOwnerId.tasks
    assert canonical_owner_for(EntityKind.opportunity) == CanonicalOwnerId.crm
    assert canonical_owner_for(EntityKind.reviewed_memory) == CanonicalOwnerId.memory
    assert len(CANONICAL_OWNERSHIP_REGISTRY.assignments) == len(EntityKind)


def test_duplicate_canonical_ownership_assignments_are_rejected() -> None:
    duplicate = CanonicalOwnershipAssignment(
        entity_kind=EntityKind.task,
        canonical_owner=CanonicalOwnerId.tasks,
    )
    with pytest.raises(ValidationError, match="ECO_DUPLICATE_CANONICAL_OWNERSHIP"):
        CanonicalOwnershipRegistry(assignments=(duplicate, duplicate))


def test_wrong_owner_and_crm_owned_event_or_task_are_rejected() -> None:
    for kind in (EntityKind.event, EntityKind.task):
        with pytest.raises(ValidationError, match="ECO_CANONICAL_OWNER_MISMATCH"):
            CanonicalEntityRef(
                entity_ref=f"entity-ref:eco-test:crm-duplicate-{kind.value}",
                entity_kind=kind,
                canonical_owner=CanonicalOwnerId.crm,
                workspace=_workspace(),
                entity_version=_version(),
            )


def test_memory_and_model_output_cannot_be_canonical_truth() -> None:
    for field in ("canonical_truth_from_memory", "canonical_truth_from_model_output"):
        payload = {
            "entity_ref": "entity-ref:eco-test:unsafe-derived-truth",
            "entity_kind": EntityKind.task,
            "canonical_owner": CanonicalOwnerId.tasks,
            "workspace": _workspace(),
            "entity_version": _version(),
            field: True,
        }
        with pytest.raises(
            ValidationError,
            match="ECO_DERIVED_OUTPUT_CANNOT_BE_CANONICAL_TRUTH",
        ):
            CanonicalEntityRef.model_validate(payload)


def test_projection_and_board_card_cannot_claim_or_copy_domain_authority() -> None:
    task = _entity(EntityKind.task)
    with pytest.raises(ValidationError, match="ECO_PROJECTION_DOMAIN_AUTHORITY_DENIED"):
        Projection(
            projection_ref="projection-ref:eco-test:today-task",
            projection_app=AppId.today,
            subject=task,
            projected_field_refs=("field-ref:task:status",),
            placement_ref="placement-ref:today:attention",
            claims_domain_authority=True,
        )
    with pytest.raises(ValidationError, match="ECO_PROJECTION_DOMAIN_STATE_FORK_DENIED"):
        BoardProjection(
            projection_ref="projection-ref:eco-test:board-task",
            subject=task,
            card_subject=CardSubject(
                subject_ref="card-subject-ref:eco-test:task",
                canonical_subject=task,
                subject_owner=CanonicalOwnerId.tasks,
            ),
            projected_field_refs=("field-ref:task:title",),
            placement_ref="placement-ref:board:lane",
            board_ref="board-ref:eco-test:work",
            lane_ref="lane-ref:eco-test:doing",
            ordering_ref="ordering-ref:eco-test:010",
            copies_domain_state=True,
        )


def test_private_entity_links_cannot_cross_workspace_or_hide_context() -> None:
    source = _entity(
        EntityKind.relationship,
        workspace=_workspace(
            "workspace-ref:eco-test:private",
            PrivacyScope.restricted_private,
        ),
    )
    target = _entity(
        EntityKind.task,
        workspace=_workspace("workspace-ref:eco-test:work"),
    )
    with pytest.raises(ValidationError, match="ECO_PRIVATE_ENTITY_LINK_LEAK_DENIED"):
        EntityLink(
            link_ref="link-ref:eco-test:private-leak",
            link_kind=EntityLinkKind.follows_up,
            source=source,
            target=target,
            workspace=WorkspaceScope(
                workspace_ref="workspace-ref:eco-test:private",
                cross_workspace_projection_allowed=True,
            ),
            provenance_ref="provenance-ref:eco-test:operator",
            deletion_posture_ref="deletion-posture-ref:eco-test:linked",
        )


def test_entity_link_workspace_must_match_an_exact_endpoint_envelope() -> None:
    source = _entity(
        EntityKind.relationship,
        workspace=_workspace("workspace-ref:eco-test:source"),
    )
    target = _entity(
        EntityKind.task,
        workspace=_workspace("workspace-ref:eco-test:target"),
    )
    with pytest.raises(
        ValidationError,
        match="ECO_ENTITY_LINK_WORKSPACE_ENVELOPE_MISMATCH",
    ):
        EntityLink(
            link_ref="link-ref:eco-test:third-workspace",
            link_kind=EntityLinkKind.follows_up,
            source=source,
            target=target,
            workspace=WorkspaceScope(
                workspace_ref="workspace-ref:eco-test:unrelated",
                cross_workspace_projection_allowed=True,
            ),
            provenance_ref="provenance-ref:eco-test:operator",
            deletion_posture_ref="deletion-posture-ref:eco-test:linked",
        )


def test_source_provenance_requires_untrusted_content_and_no_raw_persistence() -> None:
    with pytest.raises(ValidationError, match="ECO_SOURCE_MUST_REMAIN_UNTRUSTED_DATA"):
        SourceProvenance(
            provenance_ref="provenance-ref:eco-test:source",
            source_ref="source-ref:eco-test:item",
            observed_at_ref="timestamp-ref:eco-test:observed",
            redaction_status_ref="redaction-status-ref:eco-test:safe",
            content_untrusted=False,
        )


def test_change_set_validates_dependencies_cycles_and_non_authority() -> None:
    first = _operation("operation-ref:eco-test:first")
    second = _operation(
        "operation-ref:eco-test:second",
        depends_on=(first.operation_ref,),
    )
    plan = _change_set(first, second)
    assert plan.execution_authorized is False
    assert plan.execution_performed is False

    with pytest.raises(ValidationError, match="ECO_CHANGE_OPERATION_DEPENDENCY_MISSING"):
        _change_set(
            _operation(
                "operation-ref:eco-test:missing",
                depends_on=("operation-ref:eco-test:not-present",),
            )
        )
    cycle_a = _operation(
        "operation-ref:eco-test:cycle-a",
        depends_on=("operation-ref:eco-test:cycle-b",),
    )
    cycle_b = _operation(
        "operation-ref:eco-test:cycle-b",
        depends_on=("operation-ref:eco-test:cycle-a",),
    )
    with pytest.raises(ValidationError, match="ECO_CHANGE_OPERATION_DEPENDENCY_CYCLE"):
        _change_set(cycle_a, cycle_b)


def test_change_operation_binds_conflict_target_and_version_exactly() -> None:
    operation = _operation("operation-ref:eco-test:conflict-binding")
    payload = operation.model_dump(mode="python")
    payload["conflict_precondition"] = ConflictPrecondition(
        target_ref="entity-ref:eco-test:other-target",
        expected_version=operation.target.entity_version,
    )
    with pytest.raises(
        ValidationError,
        match="ECO_CONFLICT_PRECONDITION_TARGET_MISMATCH",
    ):
        ChangeOperation.model_validate(payload)

    payload["conflict_precondition"] = ConflictPrecondition(
        target_ref=operation.target.entity_ref,
        expected_version=_version(2),
    )
    with pytest.raises(
        ValidationError,
        match="ECO_CONFLICT_PRECONDITION_VERSION_MISMATCH",
    ):
        ChangeOperation.model_validate(payload)


def test_change_set_requires_exact_workspace_privacy_envelope() -> None:
    operation = _operation("operation-ref:eco-test:privacy-envelope")
    with pytest.raises(ValidationError, match="ECO_CHANGE_SET_WORKSPACE_MISMATCH"):
        ChangeSetPlan(
            change_set_ref="change-set-ref:eco-test:privacy-envelope",
            change_set_fingerprint_ref="fingerprint-ref:eco-test:privacy-envelope",
            workspace=_workspace(
                operation.target.workspace.workspace_ref,
                PrivacyScope.restricted_private,
            ),
            operations=(operation,),
            approval_scope_ref="approval-scope-ref:eco-test:privacy-envelope",
            idempotency_ref="idempotency-ref:eco-test:privacy-envelope",
            expiry_ref="expiry-ref:eco-test:bounded",
            predicted_result_ref="prediction-ref:eco-test:review-only",
        )


def test_local_requires_rollback_and_external_requires_compensation_not_atomicity() -> None:
    target = _entity(EntityKind.task)
    common = {
        "operation_ref": "operation-ref:eco-test:recovery",
        "target": target,
        "capability_ref": "capability-ref:eco-test:write",
        "operation_fingerprint_ref": "fingerprint-ref:eco-test:recovery",
        "conflict_precondition": ConflictPrecondition(
            target_ref=target.entity_ref,
            expected_version=_version(),
        ),
    }
    with pytest.raises(ValidationError, match="ECO_LOCAL_OPERATION_ROLLBACK_PLAN_REQUIRED"):
        ChangeOperation(**common, atomicity_posture=AtomicityPosture.local_atomic)
    with pytest.raises(
        ValidationError,
        match="ECO_EXTERNAL_OPERATION_COMPENSATION_PLAN_REQUIRED",
    ):
        ChangeOperation(
            **common,
            atomicity_posture=AtomicityPosture.external_compensating,
        )
    with pytest.raises(ValidationError, match="ECO_EXTERNAL_ATOMICITY_CLAIM_DENIED"):
        ChangeOperation(
            **common,
            atomicity_posture=AtomicityPosture.external_compensating,
            compensation_plan=CompensationPlan(
                plan_ref="compensation-plan-ref:eco-test:required",
                target_ref=target.entity_ref,
                capability_ref="capability-ref:eco-test:compensate",
                plan_fingerprint_ref="fingerprint-ref:eco-test:compensate",
            ),
            claims_external_atomicity=True,
        )


def test_card_subject_owner_and_recovery_plans_require_exact_fresh_scope() -> None:
    task = _entity(EntityKind.task)
    with pytest.raises(ValidationError, match="ECO_CARD_SUBJECT_OWNER_MISMATCH"):
        CardSubject(
            subject_ref="card-subject-ref:eco-test:mismatch",
            canonical_subject=task,
            subject_owner=CanonicalOwnerId.crm,
        )
    with pytest.raises(
        ValidationError,
        match="ECO_ROLLBACK_REQUIRES_EXACT_FRESH_AUTHORITY",
    ):
        RollbackPlan(
            plan_ref="rollback-plan-ref:eco-test:auto",
            target_ref=task.entity_ref,
            capability_ref="capability-ref:eco-test:rollback",
            plan_fingerprint_ref="fingerprint-ref:eco-test:rollback",
            automatic_execution_allowed=True,
        )


def test_catalog_visibility_does_not_imply_authority() -> None:
    relationship = CapabilityCatalogRelationship(
        catalog_entry_ref="catalog-entry-ref:eco-test:calendar",
        capability_ref="capability-ref:eco-test:calendar-read",
        available_in_catalog=True,
    )
    assert relationship.authority_accepted is False
    assert relationship.operation_executed is False

    with pytest.raises(ValidationError, match="Input should be False"):
        CapabilityCatalogRelationship(
            catalog_entry_ref="catalog-entry-ref:eco-test:unsafe",
            capability_ref="capability-ref:eco-test:unsafe",
            available_in_catalog=True,
            operation_executed=True,
        )

    with pytest.raises(ValidationError):
        CapabilityCatalogRelationship(
            catalog_entry_ref="catalog-entry-ref:eco-test:authority-denied",
            capability_ref="capability-ref:eco-test:authority-denied",
            available_in_catalog=True,
            configured_for_source=True,
            source_binding_reviewed=True,
            capability_proposed=True,
            authority_accepted=True,
            authority_decision_ref="authority-decision-ref:eco-test:not-request-scoped",
        )


def test_board_projection_app_is_not_overridable() -> None:
    task = _entity(EntityKind.task)
    with pytest.raises(ValidationError):
        BoardProjection(
            projection_ref="projection-ref:eco-test:wrong-app",
            projection_app=AppId.today,
            subject=task,
            card_subject=CardSubject(
                subject_ref="card-subject-ref:eco-test:wrong-app",
                canonical_subject=task,
                subject_owner=CanonicalOwnerId.tasks,
            ),
            projected_field_refs=("field-ref:task:title",),
            placement_ref="placement-ref:board:lane",
            board_ref="board-ref:eco-test:work",
            lane_ref="lane-ref:eco-test:doing",
            ordering_ref="ordering-ref:eco-test:010",
        )


def test_standalone_and_render_acceptance_are_complete_and_truthful() -> None:
    maturity = StandaloneAppMaturity(
        app_id=AppId.tasks,
        contract_ref="contract-ref:eco-test:tasks:v1",
        acceptance_status=ProductAcceptanceStatus.draft,
        required_workflow_refs=("workflow-ref:tasks:capture-to-complete",),
        required_view_refs=("view-ref:tasks:today",),
        required_state_refs=("state-ref:tasks:empty",),
        required_mode_refs=("mode-ref:tasks:desktop",),
        blocker_refs=("blocked-state-ref:tasks:not-implemented",),
    )
    assert maturity.implementation_claimed is False

    with pytest.raises(
        ValidationError,
        match="ECO_REVIEWED_RENDER_REQUIRES_ASSET_AND_REVIEW_REF",
    ):
        ProductRenderAcceptance(
            surface_state_ref="surface-state-ref:eco-test:today-default",
            acceptance_status=ProductAcceptanceStatus.reviewed,
            shell_baseline_ref="shell-baseline-ref:control-center:v1",
            synthetic_dataset_ref="dataset-ref:eco-test:medium",
        )


def test_raw_private_secret_and_path_shaped_values_are_rejected() -> None:
    with pytest.raises(ValidationError, match="ECO_(SAFE_REF_REQUIRED|UNSAFE_REF_REJECTED)"):
        EntityVersion(
            version=1,
            fingerprint_ref="fingerprint-ref:/Users/example/private",
        )
    with pytest.raises(ValidationError):
        WorkspaceScope(
            workspace_ref="workspace-ref:ghp_AAAAAAAAAAAAAAAAAAAAAAAA",
        )
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SourceProvenance.model_validate(
            {
                "provenance_ref": "provenance-ref:eco-test:source",
                "source_ref": "source-ref:eco-test:item",
                "observed_at_ref": "timestamp-ref:eco-test:observed",
                "redaction_status_ref": "redaction-status-ref:eco-test:safe",
                "raw_prompt": "unsafe content",
            }
        )


def test_historical_contracts_remain_importable_without_runtime_changes() -> None:
    assert FounderLoopLocalTaskCommitRequest is not None
    assert WorkBoardReadModel is not None
    assert CrmAuthorityBoundary is not None
