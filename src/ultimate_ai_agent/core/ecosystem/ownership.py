"""Canonical object ownership for ECO-000."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId, EntityKind


CANONICAL_OWNER_BY_ENTITY_KIND: Mapping[EntityKind, CanonicalOwnerId] = {
    EntityKind.person: CanonicalOwnerId.identity,
    EntityKind.organization: CanonicalOwnerId.identity,
    EntityKind.household: CanonicalOwnerId.identity,
    EntityKind.workspace: CanonicalOwnerId.identity,
    EntityKind.contact_point: CanonicalOwnerId.identity,
    EntityKind.identity_alias: CanonicalOwnerId.identity,
    EntityKind.identity_match_candidate: CanonicalOwnerId.identity,
    EntityKind.calendar: CanonicalOwnerId.calendar,
    EntityKind.calendar_set: CanonicalOwnerId.calendar,
    EntityKind.event: CanonicalOwnerId.calendar,
    EntityKind.event_series: CanonicalOwnerId.calendar,
    EntityKind.event_occurrence: CanonicalOwnerId.calendar,
    EntityKind.event_participant: CanonicalOwnerId.calendar,
    EntityKind.availability_block: CanonicalOwnerId.calendar,
    EntityKind.reminder: CanonicalOwnerId.calendar,
    EntityKind.task: CanonicalOwnerId.tasks,
    EntityKind.task_occurrence: CanonicalOwnerId.tasks,
    EntityKind.subtask: CanonicalOwnerId.tasks,
    EntityKind.checklist: CanonicalOwnerId.tasks,
    EntityKind.task_dependency: CanonicalOwnerId.tasks,
    EntityKind.task_recurrence: CanonicalOwnerId.tasks,
    EntityKind.commitment: CanonicalOwnerId.tasks,
    EntityKind.project: CanonicalOwnerId.plans,
    EntityKind.plan: CanonicalOwnerId.plans,
    EntityKind.milestone: CanonicalOwnerId.plans,
    EntityKind.plan_step: CanonicalOwnerId.plans,
    EntityKind.plan_dependency: CanonicalOwnerId.plans,
    EntityKind.board: CanonicalOwnerId.boards,
    EntityKind.board_view: CanonicalOwnerId.boards,
    EntityKind.lane: CanonicalOwnerId.boards,
    EntityKind.swimlane: CanonicalOwnerId.boards,
    EntityKind.board_membership: CanonicalOwnerId.boards,
    EntityKind.card_projection: CanonicalOwnerId.boards,
    EntityKind.card_ordering: CanonicalOwnerId.boards,
    EntityKind.board_template: CanonicalOwnerId.boards,
    EntityKind.board_item: CanonicalOwnerId.boards,
    EntityKind.relationship: CanonicalOwnerId.crm,
    EntityKind.workspace_context: CanonicalOwnerId.crm,
    EntityKind.organization_membership: CanonicalOwnerId.crm,
    EntityKind.role: CanonicalOwnerId.crm,
    EntityKind.circle: CanonicalOwnerId.crm,
    EntityKind.follow_up: CanonicalOwnerId.crm,
    EntityKind.opportunity: CanonicalOwnerId.crm,
    EntityKind.pipeline: CanonicalOwnerId.crm,
    EntityKind.pipeline_stage: CanonicalOwnerId.crm,
    EntityKind.property: CanonicalOwnerId.crm,
    EntityKind.showing: CanonicalOwnerId.crm,
    EntityKind.offer: CanonicalOwnerId.crm,
    EntityKind.transaction: CanonicalOwnerId.crm,
    EntityKind.closing_milestone: CanonicalOwnerId.crm,
    EntityKind.source_binding: CanonicalOwnerId.inbox,
    EntityKind.source_artifact: CanonicalOwnerId.inbox,
    EntityKind.conversation_thread: CanonicalOwnerId.inbox,
    EntityKind.communication_item: CanonicalOwnerId.inbox,
    EntityKind.attachment_ref: CanonicalOwnerId.inbox,
    EntityKind.communication_draft: CanonicalOwnerId.inbox,
    EntityKind.list_record: CanonicalOwnerId.organizer,
    EntityKind.list_item: CanonicalOwnerId.organizer,
    EntityKind.routine: CanonicalOwnerId.organizer,
    EntityKind.routine_occurrence: CanonicalOwnerId.organizer,
    EntityKind.meal_plan: CanonicalOwnerId.organizer,
    EntityKind.household_responsibility: CanonicalOwnerId.organizer,
    EntityKind.change_set: CanonicalOwnerId.governance,
    EntityKind.change_operation: CanonicalOwnerId.governance,
    EntityKind.approval_record: CanonicalOwnerId.governance,
    EntityKind.policy_decision: CanonicalOwnerId.governance,
    EntityKind.mutation_receipt: CanonicalOwnerId.governance,
    EntityKind.rollback_ref: CanonicalOwnerId.governance,
    EntityKind.evidence_ref: CanonicalOwnerId.governance,
    EntityKind.memory_candidate: CanonicalOwnerId.memory,
    EntityKind.reviewed_memory: CanonicalOwnerId.memory,
    EntityKind.memory_provenance: CanonicalOwnerId.memory,
    EntityKind.correction_record: CanonicalOwnerId.memory,
}


class CanonicalOwnershipAssignment(BaseModel):
    entity_kind: EntityKind
    canonical_owner: CanonicalOwnerId

    model_config = ConfigDict(extra="forbid", frozen=True)


class CanonicalOwnershipRegistry(BaseModel):
    schema_version: str = "uaa-eco-000-canonical-ownership.v1"
    assignments: tuple[CanonicalOwnershipAssignment, ...] = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def validate_registry(self) -> "CanonicalOwnershipRegistry":
        entity_kinds = [assignment.entity_kind for assignment in self.assignments]
        if len(entity_kinds) != len(set(entity_kinds)):
            raise ValueError("ECO_DUPLICATE_CANONICAL_OWNERSHIP")
        mapping = {
            assignment.entity_kind: assignment.canonical_owner
            for assignment in self.assignments
        }
        validate_unique_canonical_ownership(mapping)
        for entity_kind, owner in mapping.items():
            if owner != CANONICAL_OWNER_BY_ENTITY_KIND[entity_kind]:
                raise ValueError("ECO_CANONICAL_OWNERSHIP_LOCK_MISMATCH")
        return self


def validate_unique_canonical_ownership(
    ownership: Mapping[EntityKind, CanonicalOwnerId],
) -> None:
    """Reject missing, duplicate-key-shaped, or non-enum ownership records."""

    if set(ownership) != set(EntityKind):
        missing = sorted(kind.value for kind in set(EntityKind) - set(ownership))
        unexpected = sorted(str(kind) for kind in set(ownership) - set(EntityKind))
        raise ValueError(
            "ECO_CANONICAL_OWNERSHIP_INCOMPLETE:"
            f"missing={','.join(missing)};unexpected={','.join(unexpected)}"
        )
    for entity_kind, owner in ownership.items():
        if not isinstance(entity_kind, EntityKind) or not isinstance(
            owner, CanonicalOwnerId
        ):
            raise ValueError("ECO_CANONICAL_OWNERSHIP_ENUMS_REQUIRED")


def canonical_owner_for(entity_kind: EntityKind) -> CanonicalOwnerId:
    return CANONICAL_OWNER_BY_ENTITY_KIND[entity_kind]


validate_unique_canonical_ownership(CANONICAL_OWNER_BY_ENTITY_KIND)

CANONICAL_OWNERSHIP_REGISTRY = CanonicalOwnershipRegistry(
    assignments=tuple(
        CanonicalOwnershipAssignment(
            entity_kind=entity_kind,
            canonical_owner=canonical_owner,
        )
        for entity_kind, canonical_owner in CANONICAL_OWNER_BY_ENTITY_KIND.items()
    )
)
