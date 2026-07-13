"""Additive ECO-000 application-ecosystem contracts.

The models in this module are planning, linking, projection, and acceptance
contracts. They deliberately contain no global callable/authorized flag and do
not grant runtime authority.
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_000_CONTRACT_VERSION = "uaa-ecosystem-contract.v1"
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
_SAFE_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,79}$")
_RAW_PATH_RE = re.compile(
    r"(?i)(^|[\\s\"'`])(~[/\\]?|/(users|home|usr|var|private|tmp|etc)(/|$)|"
    r"[a-z]:[\\/]|\\\\[^\\\s]+\\)"
)
class AppId(str, Enum):
    today = "today"
    calendar = "calendar"
    tasks = "tasks"
    boards = "boards"
    plans = "plans"
    crm = "crm"
    inbox = "inbox"
    organizer = "organizer"
    action_inbox = "action_inbox"
    evidence = "evidence"
    memory = "memory"
    trust_settings = "trust_settings"


class CanonicalOwnerId(str, Enum):
    identity = "identity"
    calendar = "calendar"
    tasks = "tasks"
    plans = "plans"
    boards = "boards"
    crm = "crm"
    inbox = "inbox"
    organizer = "organizer"
    integration_catalog = "integration_catalog"
    governance = "governance"
    memory = "memory"


class EntityKind(str, Enum):
    person = "person"
    organization = "organization"
    household = "household"
    workspace = "workspace"
    contact_point = "contact_point"
    identity_alias = "identity_alias"
    identity_match_candidate = "identity_match_candidate"
    calendar = "calendar"
    calendar_set = "calendar_set"
    event = "event"
    event_series = "event_series"
    event_occurrence = "event_occurrence"
    event_participant = "event_participant"
    availability_block = "availability_block"
    reminder = "reminder"
    task = "task"
    task_occurrence = "task_occurrence"
    subtask = "subtask"
    checklist = "checklist"
    task_dependency = "task_dependency"
    task_recurrence = "task_recurrence"
    commitment = "commitment"
    project = "project"
    plan = "plan"
    milestone = "milestone"
    plan_step = "plan_step"
    plan_dependency = "plan_dependency"
    board = "board"
    board_view = "board_view"
    lane = "lane"
    swimlane = "swimlane"
    board_membership = "board_membership"
    card_projection = "card_projection"
    card_ordering = "card_ordering"
    board_template = "board_template"
    board_item = "board_item"
    relationship = "relationship"
    workspace_context = "workspace_context"
    organization_membership = "organization_membership"
    role = "role"
    circle = "circle"
    follow_up = "follow_up"
    opportunity = "opportunity"
    pipeline = "pipeline"
    pipeline_stage = "pipeline_stage"
    property = "property"
    showing = "showing"
    offer = "offer"
    transaction = "transaction"
    closing_milestone = "closing_milestone"
    source_binding = "source_binding"
    source_artifact = "source_artifact"
    conversation_thread = "conversation_thread"
    communication_item = "communication_item"
    attachment_ref = "attachment_ref"
    communication_draft = "communication_draft"
    list_record = "list"
    list_item = "list_item"
    routine = "routine"
    routine_occurrence = "routine_occurrence"
    meal_plan = "meal_plan"
    household_responsibility = "household_responsibility"
    change_set = "change_set"
    change_operation = "change_operation"
    approval_record = "approval_record"
    policy_decision = "policy_decision"
    mutation_receipt = "mutation_receipt"
    rollback_ref = "rollback_ref"
    evidence_ref = "evidence_ref"
    memory_candidate = "memory_candidate"
    reviewed_memory = "reviewed_memory"
    memory_provenance = "memory_provenance"
    correction_record = "correction_record"


class PrivacyScope(str, Enum):
    workspace = "workspace"
    restricted_private = "restricted_private"
    governance_safe_ref = "governance_safe_ref"


class EntityLinkKind(str, Enum):
    references = "references"
    projects = "projects"
    schedules = "schedules"
    follows_up = "follows_up"
    relates_to = "relates_to"
    derived_from = "derived_from"
    supports = "supports"


class AtomicityPosture(str, Enum):
    local_atomic = "local_atomic"
    external_compensating = "external_compensating"


class OperationResultStatus(str, Enum):
    not_started = "not_started"
    applied = "applied"
    replayed = "replayed"
    skipped = "skipped"
    denied = "denied"
    conflicted = "conflicted"
    failed = "failed"
    compensated = "compensated"
    compensation_failed = "compensation_failed"


class ProductAcceptanceStatus(str, Enum):
    missing = "missing"
    draft = "draft"
    reviewed = "reviewed"
    accepted = "accepted"
    blocked = "blocked"
    superseded = "superseded"


class _EcosystemModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )

    @model_validator(mode="after")
    def reject_unsafe_content(self) -> "_EcosystemModel":
        _validate_safe_payload(self.model_dump(mode="json"))
        return self


class EntityVersion(_EcosystemModel):
    schema_version: str = ECO_000_CONTRACT_VERSION
    version: int = Field(..., ge=1)
    fingerprint_ref: str

    @field_validator("schema_version", "fingerprint_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value)


class WorkspaceScope(_EcosystemModel):
    workspace_ref: str
    privacy_scope: PrivacyScope = PrivacyScope.workspace
    allowed_workspace_refs: tuple[str, ...] = ()
    ai_use_allowed: bool = False
    cross_workspace_projection_allowed: bool = False

    @field_validator("workspace_ref")
    @classmethod
    def validate_workspace_ref(cls, value: str) -> str:
        return _validated_ref(value)

    @field_validator("allowed_workspace_refs")
    @classmethod
    def validate_allowed_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validated_unique_refs(values)

    @model_validator(mode="after")
    def validate_private_scope(self) -> "WorkspaceScope":
        if self.privacy_scope == PrivacyScope.restricted_private:
            if self.cross_workspace_projection_allowed:
                raise ValueError("ECO_PRIVATE_CROSS_WORKSPACE_PROJECTION_DENIED")
            if set(self.allowed_workspace_refs) - {self.workspace_ref}:
                raise ValueError("ECO_PRIVATE_WORKSPACE_LEAK_DENIED")
        return self


class CanonicalEntityRef(_EcosystemModel):
    entity_ref: str
    entity_kind: EntityKind
    canonical_owner: CanonicalOwnerId
    workspace: WorkspaceScope
    entity_version: EntityVersion
    canonical_truth_from_memory: bool = False
    canonical_truth_from_model_output: bool = False

    @field_validator("entity_ref")
    @classmethod
    def validate_entity_ref(cls, value: str) -> str:
        return _validated_ref(value)

    @model_validator(mode="after")
    def validate_owner_and_truth(self) -> "CanonicalEntityRef":
        from ultimate_ai_agent.core.ecosystem.ownership import canonical_owner_for

        if self.canonical_owner != canonical_owner_for(self.entity_kind):
            raise ValueError("ECO_CANONICAL_OWNER_MISMATCH")
        if self.canonical_truth_from_memory or self.canonical_truth_from_model_output:
            raise ValueError("ECO_DERIVED_OUTPUT_CANNOT_BE_CANONICAL_TRUTH")
        return self


class EntityLink(_EcosystemModel):
    link_ref: str
    link_kind: EntityLinkKind
    source: CanonicalEntityRef
    target: CanonicalEntityRef
    workspace: WorkspaceScope
    provenance_ref: str
    deletion_posture_ref: str
    hidden_context_injection: bool = False

    @field_validator("link_ref", "provenance_ref", "deletion_posture_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value)

    @model_validator(mode="after")
    def validate_link_boundary(self) -> "EntityLink":
        if self.source.entity_ref == self.target.entity_ref:
            raise ValueError("ECO_ENTITY_LINK_SELF_REFERENCE_DENIED")
        if self.hidden_context_injection:
            raise ValueError("ECO_HIDDEN_CONTEXT_INJECTION_DENIED")
        refs = {
            self.source.workspace.workspace_ref,
            self.target.workspace.workspace_ref,
        }
        if len(refs) > 1 and not self.workspace.cross_workspace_projection_allowed:
            raise ValueError("ECO_CROSS_WORKSPACE_LINK_NOT_ALLOWED")
        if (
            self.source.workspace.privacy_scope == PrivacyScope.restricted_private
            or self.target.workspace.privacy_scope == PrivacyScope.restricted_private
        ) and len(refs) > 1:
            raise ValueError("ECO_PRIVATE_ENTITY_LINK_LEAK_DENIED")
        if (
            self.workspace != self.source.workspace
            and self.workspace != self.target.workspace
        ):
            raise ValueError("ECO_ENTITY_LINK_WORKSPACE_ENVELOPE_MISMATCH")
        return self


class Projection(_EcosystemModel):
    projection_ref: str
    projection_app: AppId
    subject: CanonicalEntityRef
    projected_field_refs: tuple[str, ...]
    placement_ref: str
    claims_domain_authority: bool = False
    copies_domain_state: bool = False

    @field_validator("projection_ref", "placement_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value)

    @field_validator("projected_field_refs")
    @classmethod
    def validate_field_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError("ECO_PROJECTION_FIELD_REFS_REQUIRED")
        return _validated_unique_refs(values)

    @model_validator(mode="after")
    def validate_non_authority(self) -> "Projection":
        if self.claims_domain_authority:
            raise ValueError("ECO_PROJECTION_DOMAIN_AUTHORITY_DENIED")
        if self.copies_domain_state:
            raise ValueError("ECO_PROJECTION_DOMAIN_STATE_FORK_DENIED")
        return self


class CardSubject(_EcosystemModel):
    subject_ref: str
    canonical_subject: CanonicalEntityRef
    subject_owner: CanonicalOwnerId
    standalone_board_item: bool = False

    @field_validator("subject_ref")
    @classmethod
    def validate_subject_ref(cls, value: str) -> str:
        return _validated_ref(value)

    @model_validator(mode="after")
    def validate_subject_ownership(self) -> "CardSubject":
        if self.subject_owner != self.canonical_subject.canonical_owner:
            raise ValueError("ECO_CARD_SUBJECT_OWNER_MISMATCH")
        is_board_item = self.canonical_subject.entity_kind == EntityKind.board_item
        if self.standalone_board_item != is_board_item:
            raise ValueError("ECO_CARD_SUBJECT_STANDALONE_POSTURE_MISMATCH")
        return self


class BoardProjection(Projection):
    projection_app: Literal[AppId.boards] = AppId.boards
    card_subject: CardSubject
    board_ref: str
    lane_ref: str
    ordering_ref: str

    @field_validator("board_ref", "lane_ref", "ordering_ref")
    @classmethod
    def validate_board_refs(cls, value: str) -> str:
        return _validated_ref(value)

    @model_validator(mode="after")
    def validate_board_subject(self) -> "BoardProjection":
        if self.card_subject.canonical_subject.entity_ref != self.subject.entity_ref:
            raise ValueError("ECO_BOARD_CARD_SUBJECT_REF_MISMATCH")
        if self.subject.entity_kind not in {
            EntityKind.task,
            EntityKind.plan,
            EntityKind.plan_step,
            EntityKind.opportunity,
            EntityKind.transaction,
            EntityKind.board_item,
        }:
            raise ValueError("ECO_BOARD_SUBJECT_KIND_UNSUPPORTED")
        return self


class TimelineProjection(_EcosystemModel):
    timeline_item_ref: str
    owning_app: AppId
    source_entity: CanonicalEntityRef
    related_entity_refs: tuple[str, ...] = ()
    safe_summary_ref: str
    evidence_refs: tuple[str, ...] = ()
    raw_private_content_included: bool = False
    claims_canonical_ownership: bool = False

    @field_validator("timeline_item_ref", "safe_summary_ref")
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value)

    @field_validator("related_entity_refs", "evidence_refs")
    @classmethod
    def validate_ref_lists(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validated_unique_refs(values)

    @model_validator(mode="after")
    def validate_timeline_projection(self) -> "TimelineProjection":
        if self.raw_private_content_included or self.claims_canonical_ownership:
            raise ValueError("ECO_TIMELINE_SAFE_PROJECTION_REQUIRED")
        return self


class SourceProvenance(_EcosystemModel):
    provenance_ref: str
    source_ref: str
    source_binding_ref: str | None = None
    observed_at_ref: str
    redaction_status_ref: str
    content_untrusted: bool = True
    not_instruction_authority: bool = True
    raw_source_content_persisted: bool = False

    @field_validator(
        "provenance_ref",
        "source_ref",
        "source_binding_ref",
        "observed_at_ref",
        "redaction_status_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return None if value is None else _validated_ref(value)

    @model_validator(mode="after")
    def validate_source_posture(self) -> "SourceProvenance":
        if not self.content_untrusted or not self.not_instruction_authority:
            raise ValueError("ECO_SOURCE_MUST_REMAIN_UNTRUSTED_DATA")
        if self.raw_source_content_persisted:
            raise ValueError("ECO_RAW_SOURCE_CONTENT_PERSISTENCE_DENIED")
        return self


class ConflictPrecondition(_EcosystemModel):
    target_ref: str
    expected_version: EntityVersion
    stale_version_must_conflict: bool = True

    @field_validator("target_ref")
    @classmethod
    def validate_target_ref(cls, value: str) -> str:
        return _validated_ref(value)

    @model_validator(mode="after")
    def validate_stale_posture(self) -> "ConflictPrecondition":
        if not self.stale_version_must_conflict:
            raise ValueError("ECO_STALE_VERSION_MUST_CONFLICT")
        return self


class RollbackPlan(_EcosystemModel):
    plan_ref: str
    target_ref: str
    capability_ref: str
    plan_fingerprint_ref: str
    exact_scope_required: bool = True
    automatic_execution_allowed: bool = False

    @field_validator(
        "plan_ref", "target_ref", "capability_ref", "plan_fingerprint_ref"
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value)

    @model_validator(mode="after")
    def validate_posture(self) -> "RollbackPlan":
        if not self.exact_scope_required or self.automatic_execution_allowed:
            raise ValueError("ECO_ROLLBACK_REQUIRES_EXACT_FRESH_AUTHORITY")
        return self


class CompensationPlan(_EcosystemModel):
    plan_ref: str
    target_ref: str
    capability_ref: str
    plan_fingerprint_ref: str
    partial_completion_acknowledged: bool = True
    exact_scope_required: bool = True
    automatic_execution_allowed: bool = False

    @field_validator(
        "plan_ref", "target_ref", "capability_ref", "plan_fingerprint_ref"
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value)

    @model_validator(mode="after")
    def validate_posture(self) -> "CompensationPlan":
        if not self.partial_completion_acknowledged:
            raise ValueError("ECO_COMPENSATION_MUST_ACKNOWLEDGE_PARTIAL_COMPLETION")
        if not self.exact_scope_required or self.automatic_execution_allowed:
            raise ValueError("ECO_COMPENSATION_REQUIRES_EXACT_FRESH_AUTHORITY")
        return self


class ChangeOperation(_EcosystemModel):
    operation_ref: str
    target: CanonicalEntityRef
    capability_ref: str
    operation_fingerprint_ref: str
    depends_on: tuple[str, ...] = ()
    atomicity_posture: AtomicityPosture
    conflict_precondition: ConflictPrecondition
    rollback_plan: RollbackPlan | None = None
    compensation_plan: CompensationPlan | None = None
    claims_external_atomicity: bool = False
    planned_result: OperationResultStatus = OperationResultStatus.not_started

    @field_validator(
        "operation_ref",
        "capability_ref",
        "operation_fingerprint_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return None if value is None else _validated_ref(value)

    @field_validator("depends_on")
    @classmethod
    def validate_dependency_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validated_unique_refs(values)

    @model_validator(mode="after")
    def validate_recovery_posture(self) -> "ChangeOperation":
        if self.operation_ref in self.depends_on:
            raise ValueError("ECO_CHANGE_OPERATION_SELF_DEPENDENCY")
        if self.conflict_precondition.target_ref != self.target.entity_ref:
            raise ValueError("ECO_CONFLICT_PRECONDITION_TARGET_MISMATCH")
        if self.conflict_precondition.expected_version != self.target.entity_version:
            raise ValueError("ECO_CONFLICT_PRECONDITION_VERSION_MISMATCH")
        if self.atomicity_posture == AtomicityPosture.local_atomic:
            if self.rollback_plan is None:
                raise ValueError("ECO_LOCAL_OPERATION_ROLLBACK_PLAN_REQUIRED")
            if self.rollback_plan.target_ref != self.target.entity_ref:
                raise ValueError("ECO_ROLLBACK_TARGET_MISMATCH")
            if self.compensation_plan is not None:
                raise ValueError("ECO_LOCAL_OPERATION_COMPENSATION_PLAN_UNEXPECTED")
        else:
            if self.compensation_plan is None:
                raise ValueError("ECO_EXTERNAL_OPERATION_COMPENSATION_PLAN_REQUIRED")
            if self.compensation_plan.target_ref != self.target.entity_ref:
                raise ValueError("ECO_COMPENSATION_TARGET_MISMATCH")
            if self.rollback_plan is not None:
                raise ValueError("ECO_EXTERNAL_OPERATION_ROLLBACK_PLAN_UNEXPECTED")
            if self.claims_external_atomicity:
                raise ValueError("ECO_EXTERNAL_ATOMICITY_CLAIM_DENIED")
        return self


class ChangeSetPlan(_EcosystemModel):
    change_set_ref: str
    change_set_fingerprint_ref: str
    workspace: WorkspaceScope
    operations: tuple[ChangeOperation, ...] = Field(..., min_length=1, max_length=64)
    approval_scope_ref: str
    idempotency_ref: str
    expiry_ref: str
    predicted_result_ref: str
    execution_authorized: bool = False
    execution_performed: bool = False

    @field_validator(
        "change_set_ref",
        "change_set_fingerprint_ref",
        "approval_scope_ref",
        "idempotency_ref",
        "expiry_ref",
        "predicted_result_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validated_ref(value)

    @model_validator(mode="after")
    def validate_plan(self) -> "ChangeSetPlan":
        if self.execution_authorized or self.execution_performed:
            raise ValueError("ECO_CHANGE_SET_PLAN_CANNOT_GRANT_OR_EXECUTE_AUTHORITY")
        refs = [operation.operation_ref for operation in self.operations]
        if len(refs) != len(set(refs)):
            raise ValueError("ECO_CHANGE_OPERATION_DUPLICATE_REF")
        known = set(refs)
        for operation in self.operations:
            missing = set(operation.depends_on) - known
            if missing:
                raise ValueError("ECO_CHANGE_OPERATION_DEPENDENCY_MISSING")
            if operation.target.workspace != self.workspace:
                raise ValueError("ECO_CHANGE_SET_WORKSPACE_MISMATCH")
        _validate_acyclic_dependencies(self.operations)
        return self


class StandaloneAppMaturity(_EcosystemModel):
    app_id: AppId
    contract_ref: str
    acceptance_status: ProductAcceptanceStatus
    required_workflow_refs: tuple[str, ...]
    required_view_refs: tuple[str, ...]
    required_state_refs: tuple[str, ...]
    required_mode_refs: tuple[str, ...]
    api_cli_parity_required: bool = True
    local_manual_core_useful_without_connectors: bool = True
    integration_enhancements_optional: bool = True
    implementation_claimed: bool = False
    evidence_refs: tuple[str, ...] = ()
    blocker_refs: tuple[str, ...] = ()

    @field_validator("contract_ref")
    @classmethod
    def validate_contract_ref(cls, value: str) -> str:
        return _validated_ref(value)

    @field_validator(
        "required_workflow_refs",
        "required_view_refs",
        "required_state_refs",
        "required_mode_refs",
        "evidence_refs",
        "blocker_refs",
    )
    @classmethod
    def validate_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validated_unique_refs(values)

    @model_validator(mode="after")
    def validate_acceptance(self) -> "StandaloneAppMaturity":
        for refs in (
            self.required_workflow_refs,
            self.required_view_refs,
            self.required_state_refs,
            self.required_mode_refs,
        ):
            if not refs:
                raise ValueError("ECO_STANDALONE_ACCEPTANCE_DIMENSION_REQUIRED")
        if not self.local_manual_core_useful_without_connectors:
            raise ValueError("ECO_STANDALONE_LOCAL_MANUAL_USEFULNESS_REQUIRED")
        if self.acceptance_status != ProductAcceptanceStatus.accepted and self.implementation_claimed:
            raise ValueError("ECO_UNACCEPTED_PRODUCT_IMPLEMENTATION_CLAIM_DENIED")
        return self


class ProductRenderAcceptance(_EcosystemModel):
    surface_state_ref: str
    asset_ref: str | None = None
    acceptance_status: ProductAcceptanceStatus
    reviewed_by_ref: str | None = None
    shell_baseline_ref: str
    synthetic_dataset_ref: str
    privacy_state_visible: bool = True
    authority_state_visible: bool = True
    raw_json_primary: bool = False
    shipped_behavior_claimed: bool = False
    blocker_refs: tuple[str, ...] = ()

    @field_validator(
        "surface_state_ref",
        "asset_ref",
        "reviewed_by_ref",
        "shell_baseline_ref",
        "synthetic_dataset_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return None if value is None else _validated_ref(value)

    @field_validator("blocker_refs")
    @classmethod
    def validate_blocker_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _validated_unique_refs(values)

    @model_validator(mode="after")
    def validate_render_truth(self) -> "ProductRenderAcceptance":
        if self.raw_json_primary or self.shipped_behavior_claimed:
            raise ValueError("ECO_RENDER_PRODUCT_TRUTH_VIOLATION")
        if self.acceptance_status in {
            ProductAcceptanceStatus.reviewed,
            ProductAcceptanceStatus.accepted,
        } and (self.asset_ref is None or self.reviewed_by_ref is None):
            raise ValueError("ECO_REVIEWED_RENDER_REQUIRES_ASSET_AND_REVIEW_REF")
        return self


class CapabilityCatalogRelationship(_EcosystemModel):
    catalog_entry_ref: str
    capability_ref: str
    source_binding_ref: str | None = None
    available_in_catalog: bool
    configured_for_source: bool = False
    source_binding_reviewed: bool = False
    capability_proposed: bool = False
    authority_accepted: Literal[False] = False
    operation_executed: Literal[False] = False
    receipt_verified: Literal[False] = False
    authority_decision_ref: None = None

    @field_validator(
        "catalog_entry_ref",
        "capability_ref",
        "source_binding_ref",
        "authority_decision_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return None if value is None else _validated_ref(value)

    @model_validator(mode="after")
    def validate_monotonic_truth(self) -> "CapabilityCatalogRelationship":
        sequence = [
            self.available_in_catalog,
            self.configured_for_source,
            self.source_binding_reviewed,
            self.capability_proposed,
            self.authority_accepted,
            self.operation_executed,
            self.receipt_verified,
        ]
        for index, value in enumerate(sequence[1:], start=1):
            if value and not all(sequence[:index]):
                raise ValueError("ECO_CAPABILITY_CATALOG_STATE_GAP")
        return self


def _validated_ref(value: str) -> str:
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError("ECO_SAFE_REF_REQUIRED")
    if _RAW_PATH_RE.search(value) or contains_obvious_secret(value):
        raise ValueError("ECO_UNSAFE_REF_REJECTED")
    return value


def _validated_unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    for value in values:
        _validated_ref(value)
    if len(values) != len(set(values)):
        raise ValueError("ECO_DUPLICATE_REF_REJECTED")
    return values


def _validate_safe_payload(value: Any, *, key: str = "root") -> None:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            _validate_safe_payload(child_value, key=str(child_key))
        return
    if isinstance(value, (list, tuple)):
        for child_value in value:
            _validate_safe_payload(child_value, key=key)
        return
    if isinstance(value, str):
        if _RAW_PATH_RE.search(value) or contains_obvious_secret(value):
            raise ValueError("ECO_UNSAFE_DURABLE_VALUE_REJECTED")


def _validate_acyclic_dependencies(operations: tuple[ChangeOperation, ...]) -> None:
    dependencies = {
        operation.operation_ref: set(operation.depends_on) for operation in operations
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(operation_ref: str) -> None:
        if operation_ref in visiting:
            raise ValueError("ECO_CHANGE_OPERATION_DEPENDENCY_CYCLE")
        if operation_ref in visited:
            return
        visiting.add(operation_ref)
        for dependency_ref in dependencies[operation_ref]:
            visit(dependency_ref)
        visiting.remove(operation_ref)
        visited.add(operation_ref)

    for operation_ref in dependencies:
        visit(operation_ref)
