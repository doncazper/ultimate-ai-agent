"""ECO-008 typed EntityLink persistence and governed local ChangeSets.

The engine deliberately executes only exact, existing-record updates across the
Tasks, Boards, and Calendar aggregates that already share the ECO-001 local
database.  External operations remain outcome/compensation contracts only.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.ecosystem.boards import (
    ECO_BOARD_MODULE_REF,
    ECO_BOARD_RECORD_KIND_REF,
    ECO_BOARD_TEMPLATE_RECORD_KIND_REF,
    Board,
    BoardRepository,
    BoardTemplate,
)
from ultimate_ai_agent.core.ecosystem.calendar import (
    ECO_CALENDAR_MODULE_REF,
    ECO_CALENDAR_RECORD_KIND_REF,
    CalendarSet,
    CalendarRepository,
)
from ultimate_ai_agent.core.ecosystem.contracts import (
    AtomicityPosture,
    CanonicalEntityRef,
    ChangeOperation,
    ChangeSetPlan,
    ConflictPrecondition,
    EntityKind,
    EntityLink,
    EntityVersion,
    OperationResultStatus,
    RollbackPlan,
    WorkspaceScope,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    DeleteRecord,
    EcosystemConflict,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    LocalRecord,
    PutRecord,
    UnitOfWorkReceipt,
)
from ultimate_ai_agent.core.ecosystem.ownership import canonical_owner_for
from ultimate_ai_agent.core.ecosystem.tasks import (
    ECO_TASK_MODULE_REF,
    ECO_TASK_OCCURRENCE_RECORD_KIND_REF,
    ECO_TASK_RECORD_KIND_REF,
    CanonicalTask,
    TaskRepository,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_CHANGESET_SCHEMA_VERSION = "uaa-eco-008-changeset.v1"
ECO_CHANGESET_MODULE_REF = "module-ref:changesets"
ECO_CHANGESET_MUTATION_ACTION = "ecosystem.changesets.apply"
ECO_CHANGESET_LOCAL_ATOMIC_ACTION = "ecosystem.changesets.local_atomic.apply"
ECO_ENTITY_LINK_RECORD_KIND_REF = "record-kind-ref:entity-link"
ECO_CHANGESET_EXECUTION_RECORD_KIND_REF = "record-kind-ref:change-set-execution"
ECO_CHANGESET_RETENTION_REF = "retention-ref:changesets-operator-managed"
_ALL_ENTITY_LINKS_TERM = "entity-kind:entity-link"
_ALL_CHANGESETS_TERM = "entity-kind:change-set"
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")


class ChangeSetError(RuntimeError):
    """Fail-closed ECO-008 error with a stable content-free code."""


class ChangeSetConflict(ChangeSetError):
    pass


class ChangeSetExecutionState(str, Enum):
    applied = "applied"
    rolled_back = "rolled_back"


class FieldChangeKind(str, Enum):
    added = "added"
    removed = "removed"
    updated = "updated"


def _validate_ref(value: str, field_name: str = "ref") -> str:
    if not _SAFE_REF_RE.fullmatch(value) or contains_obvious_secret(value):
        raise ValueError(f"ECO_CHANGESET_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("ECO_CHANGESET_JSON_VALUE_REQUIRED") from exc


def _stable_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


class _ChangeSetModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


class FieldDiff(_ChangeSetModel):
    operation_ref: str
    target_ref: str
    field_ref: str
    change_kind: FieldChangeKind
    before_fingerprint_ref: str | None = None
    after_fingerprint_ref: str | None = None
    raw_value_included: Literal[False] = False

    @field_validator(
        "operation_ref",
        "target_ref",
        "field_ref",
        "before_fingerprint_ref",
        "after_fingerprint_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return None if value is None else _validate_ref(value)

    @model_validator(mode="after")
    def validate_change(self) -> "FieldDiff":
        if self.change_kind == FieldChangeKind.added:
            if (
                self.before_fingerprint_ref is not None
                or self.after_fingerprint_ref is None
            ):
                raise ValueError("ECO_CHANGESET_ADDED_DIFF_BINDING_INVALID")
        elif self.change_kind == FieldChangeKind.removed:
            if (
                self.before_fingerprint_ref is None
                or self.after_fingerprint_ref is not None
            ):
                raise ValueError("ECO_CHANGESET_REMOVED_DIFF_BINDING_INVALID")
        elif self.before_fingerprint_ref is None or self.after_fingerprint_ref is None:
            raise ValueError("ECO_CHANGESET_UPDATED_DIFF_BINDING_INVALID")
        return self


class EntityLinkRecord(_ChangeSetModel):
    schema_version: Literal["uaa-eco-008-changeset.v1"] = ECO_CHANGESET_SCHEMA_VERSION
    link: EntityLink
    version: int = Field(default=1, ge=1)

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "entity-link-summary-ref",
            {
                "link_ref": self.link.link_ref,
                "link_kind": self.link.link_kind.value,
                "source_ref": self.link.source.entity_ref,
                "target_ref": self.link.target.entity_ref,
                "version": self.version,
            },
        )


class ChangeSetOperationResult(_ChangeSetModel):
    operation_ref: str
    target_ref: str
    status: OperationResultStatus
    operation_receipt_ref: str | None = None

    @field_validator("operation_ref", "target_ref", "operation_receipt_ref")
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return None if value is None else _validate_ref(value)


class ChangeSetExecutionReceipt(_ChangeSetModel):
    schema_version: Literal["uaa-eco-008-changeset.v1"] = ECO_CHANGESET_SCHEMA_VERSION
    change_set_ref: str
    change_set_fingerprint_ref: str
    state: ChangeSetExecutionState
    uow_receipt_ref: str
    rollback_ref: str
    operation_results: tuple[ChangeSetOperationResult, ...]
    replayed: bool = False
    external_write_performed: Literal[False] = False
    unscoped_atomicity_claimed: Literal[False] = False

    @field_validator(
        "change_set_ref",
        "change_set_fingerprint_ref",
        "uow_receipt_ref",
        "rollback_ref",
    )
    @classmethod
    def validate_refs(cls, value: str) -> str:
        return _validate_ref(value)


class ExternalOutcomeObservation(_ChangeSetModel):
    operation_ref: str
    status: OperationResultStatus
    observed_receipt_ref: str | None = None

    @field_validator("operation_ref", "observed_receipt_ref")
    @classmethod
    def validate_refs(cls, value: str | None) -> str | None:
        return None if value is None else _validate_ref(value)

    @model_validator(mode="after")
    def validate_receipt(self) -> "ExternalOutcomeObservation":
        if (
            self.status
            in {
                OperationResultStatus.applied,
                OperationResultStatus.replayed,
                OperationResultStatus.compensated,
                OperationResultStatus.compensation_failed,
            }
            and self.observed_receipt_ref is None
        ):
            raise ValueError("ECO_CHANGESET_EXTERNAL_OUTCOME_RECEIPT_REQUIRED")
        return self


class ExternalOutcomeProjection(_ChangeSetModel):
    change_set_ref: str
    outcomes: tuple[ExternalOutcomeObservation, ...]
    partial_completion: bool
    compensation_plan_refs: tuple[str, ...]
    projection_ref: str
    next_safe_action_ref: str
    external_execution_performed: Literal[False] = False
    local_mutation_performed: Literal[False] = False

    @field_validator(
        "change_set_ref",
        "compensation_plan_refs",
        "projection_ref",
        "next_safe_action_ref",
    )
    @classmethod
    def validate_refs(cls, value: str | tuple[str, ...]) -> str | tuple[str, ...]:
        if isinstance(value, tuple):
            return tuple(_validate_ref(item) for item in value)
        return _validate_ref(value)


@dataclass(frozen=True)
class LocalUpdateIntent:
    operation_ref: str
    record_ref: str
    entity_kind: EntityKind
    module_ref: str
    record_kind_ref: str
    capability_ref: str
    replacement_payload: dict[str, Any] = field(repr=False)
    search_terms: tuple[str, ...] = field(default=(), repr=False)
    retention_ref: str = ECO_CHANGESET_RETENTION_REF
    expires_at: str | None = None
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class _PreparedMutation:
    operation: ChangeOperation
    module_ref: str
    record_kind_ref: str
    safe_summary_ref: str
    replacement_json: bytes = field(repr=False)
    replacement_fingerprint_ref: str
    previous_json: bytes = field(repr=False)
    previous_fingerprint_ref: str
    previous_safe_summary_ref: str
    search_terms: tuple[str, ...] = field(repr=False)
    retention_ref: str
    expires_at: str | None
    field_diffs: tuple[FieldDiff, ...]


@dataclass(frozen=True)
class PreparedLocalChangeSet:
    plan: ChangeSetPlan
    field_diffs: tuple[FieldDiff, ...]
    scope_fingerprint_ref: str
    request_context_ref: str
    approval_resource_refs: tuple[str, ...]
    _mutations: tuple[_PreparedMutation, ...] = field(repr=False)


@dataclass(frozen=True)
class PreparedChangeSetRollback:
    change_set_ref: str
    change_set_fingerprint_ref: str
    rollback_ref: str
    scope_fingerprint_ref: str
    request_context_ref: str
    approval_resource_refs: tuple[str, ...]
    _operations: tuple[PutRecord, ...] = field(repr=False)
    _operation_refs: tuple[str, ...]
    _target_refs: tuple[str, ...]


@dataclass(frozen=True)
class _DomainSpec:
    model_type: type[BaseModel]
    entity_kind: EntityKind
    ref_field: str
    required_search_term: str
    version_field: str | None = "version"


_DOMAIN_SPECS: dict[tuple[str, str], _DomainSpec] = {
    (ECO_TASK_MODULE_REF, ECO_TASK_RECORD_KIND_REF): _DomainSpec(
        CanonicalTask,
        EntityKind.task,
        "task_ref",
        "entity-kind:canonical-task",
    ),
    (ECO_TASK_MODULE_REF, ECO_TASK_OCCURRENCE_RECORD_KIND_REF): _DomainSpec(
        CanonicalTask,
        EntityKind.task_occurrence,
        "task_ref",
        "entity-kind:canonical-task",
    ),
    (ECO_BOARD_MODULE_REF, ECO_BOARD_RECORD_KIND_REF): _DomainSpec(
        Board,
        EntityKind.board,
        "board_ref",
        "entity-kind:canonical-board",
    ),
    (ECO_BOARD_MODULE_REF, ECO_BOARD_TEMPLATE_RECORD_KIND_REF): _DomainSpec(
        BoardTemplate,
        EntityKind.board_template,
        "template_ref",
        "entity-kind:board-template",
    ),
    (ECO_CALENDAR_MODULE_REF, ECO_CALENDAR_RECORD_KIND_REF): _DomainSpec(
        CalendarSet,
        EntityKind.calendar_set,
        "calendar_set_ref",
        "entity-kind:calendar-set",
    ),
}


class EntityLinkRepository:
    """Persist typed links without changing either canonical endpoint."""

    def __init__(self, platform: EcosystemLocalDataPlatform) -> None:
        self.platform = platform

    @staticmethod
    def _extra_refs(link: EntityLink) -> tuple[str, ...]:
        return (
            link.source.entity_ref,
            link.target.entity_ref,
            link.provenance_ref,
            link.deletion_posture_ref,
        )

    @classmethod
    def mutation_resource_refs(
        cls,
        *,
        workspace_ref: str,
        idempotency_ref: str,
        operation_ref: str,
        link: EntityLink,
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (workspace_ref, idempotency_ref, operation_ref, link.link_ref)
                + cls._extra_refs(link)
            )
        )

    def create(
        self,
        *,
        link: EntityLink,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        workspace_ref = link.workspace.workspace_ref
        if workspace_ref not in {
            link.source.workspace.workspace_ref,
            link.target.workspace.workspace_ref,
        }:
            raise ChangeSetConflict("ECO_ENTITY_LINK_WORKSPACE_BINDING_INVALID")
        record = EntityLinkRecord(link=link)
        context = _stable_ref(
            "entity-link-request-context-ref",
            {"kind": "create", "record": record.model_dump(mode="json")},
        )
        resources = self.mutation_resource_refs(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            operation_ref=operation_ref,
            link=link,
        )
        replay = self.platform.replay_receipt(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            resource_refs=resources,
            approval=approval,
            requested_action=ECO_CHANGESET_MUTATION_ACTION,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        try:
            self.platform.read(workspace_ref=workspace_ref, record_ref=link.link_ref)
        except EcosystemLocalDataError as exc:
            if str(exc) != "ECO_RECORD_NOT_FOUND":
                raise
        else:
            raise ChangeSetConflict("ECO_ENTITY_LINK_ALREADY_EXISTS")
        return self.platform._apply_registered_domain(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            operations=(
                PutRecord(
                    operation_ref=operation_ref,
                    module_ref=ECO_CHANGESET_MODULE_REF,
                    record_ref=link.link_ref,
                    record_kind_ref=ECO_ENTITY_LINK_RECORD_KIND_REF,
                    safe_summary_ref=record.safe_summary_ref,
                    private_payload=record.model_dump(mode="json"),
                    search_terms=(_ALL_ENTITY_LINKS_TERM,),
                    expected_version=0,
                    retention_ref=ECO_CHANGESET_RETENTION_REF,
                ),
            ),
            approval=approval,
            requested_action=ECO_CHANGESET_MUTATION_ACTION,
            request_context_ref=context,
            approval_resource_refs=self._extra_refs(link),
        )

    def read(self, *, workspace_ref: str, link_ref: str) -> EntityLinkRecord:
        local = self.platform.read(workspace_ref=workspace_ref, record_ref=link_ref)
        try:
            record = EntityLinkRecord.model_validate(local.private_payload)
        except Exception as exc:
            raise ChangeSetError("ECO_ENTITY_LINK_PAYLOAD_INVALID") from exc
        if (
            local.module_ref != ECO_CHANGESET_MODULE_REF
            or local.record_kind_ref != ECO_ENTITY_LINK_RECORD_KIND_REF
            or local.version != record.version
            or local.safe_summary_ref != record.safe_summary_ref
            or record.link.link_ref != link_ref
            or record.link.workspace.workspace_ref != workspace_ref
        ):
            raise ChangeSetError("ECO_ENTITY_LINK_RECORD_BINDING_INVALID")
        return record

    def list(self, *, workspace_ref: str) -> tuple[EntityLinkRecord, ...]:
        return tuple(
            self.read(workspace_ref=workspace_ref, link_ref=link_ref)
            for link_ref in self.platform.search(
                workspace_ref=workspace_ref, term=_ALL_ENTITY_LINKS_TERM
            )
        )

    def remove(
        self,
        *,
        link: EntityLink,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        workspace_ref = link.workspace.workspace_ref
        link_ref = link.link_ref
        context = _stable_ref(
            "entity-link-request-context-ref",
            {
                "kind": "remove",
                "link_ref": link_ref,
                "expected_version": expected_version,
                "deletion_posture_ref": link.deletion_posture_ref,
            },
        )
        resources = self.mutation_resource_refs(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            operation_ref=operation_ref,
            link=link,
        )
        replay = self.platform.replay_receipt(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            resource_refs=resources,
            approval=approval,
            requested_action=ECO_CHANGESET_MUTATION_ACTION,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        current = self.read(workspace_ref=workspace_ref, link_ref=link_ref)
        if current.link != link:
            raise ChangeSetConflict("ECO_ENTITY_LINK_REMOVE_BINDING_INVALID")
        if current.version != expected_version:
            raise ChangeSetConflict("ECO_ENTITY_LINK_STALE_VERSION")
        return self.platform._apply_registered_domain(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            operations=(
                DeleteRecord(
                    operation_ref=operation_ref,
                    record_ref=link_ref,
                    expected_version=expected_version,
                ),
            ),
            approval=approval,
            requested_action=ECO_CHANGESET_MUTATION_ACTION,
            request_context_ref=context,
            approval_resource_refs=self._extra_refs(link),
        )


class ChangeSetEngine:
    """Prepare and execute exact local multi-app updates with durable rollback."""

    def __init__(self, platform: EcosystemLocalDataPlatform) -> None:
        self.platform = platform

    def _keyed_fingerprint(self, workspace_ref: str, value: Any) -> str:
        connection = self.platform._connect()
        try:
            key_item_ref, key_version_ref = self.platform._workspace_key(
                connection, workspace_ref
            )
            digest = hashlib.sha256(_canonical_json(value)).hexdigest()
            keyed = self.platform.crypto_backend.blind_index(
                key_item_ref=key_item_ref,
                key_version_ref=key_version_ref,
                normalized_term=f"changeset-private-v1:{digest}",
            )
            return f"private-fingerprint-ref:ecosystem-keyed:{keyed}"
        finally:
            connection.close()

    def _persistence_scope_binding(
        self,
        *,
        workspace_ref: str,
        operation_ref: str,
        target_ref: str,
        module_ref: str,
        record_kind_ref: str,
        safe_summary_ref: str,
        previous_safe_summary_ref: str,
        replacement_fingerprint_ref: str,
        previous_fingerprint_ref: str,
        search_terms: tuple[str, ...],
        retention_ref: str,
        expires_at: str | None,
    ) -> dict[str, Any]:
        """Bind every persistence-relevant value without exposing search terms."""

        return {
            "operation_ref": operation_ref,
            "target_ref": target_ref,
            "module_ref": module_ref,
            "record_kind_ref": record_kind_ref,
            "safe_summary_ref": safe_summary_ref,
            "previous_safe_summary_ref": previous_safe_summary_ref,
            "replacement_fingerprint_ref": replacement_fingerprint_ref,
            "previous_fingerprint_ref": previous_fingerprint_ref,
            "search_terms_fingerprint_ref": self._keyed_fingerprint(
                workspace_ref, search_terms
            ),
            "retention_ref": retention_ref,
            "expires_at": expires_at,
        }

    def _prepared_scope_material(
        self,
        *,
        workspace_ref: str,
        plan: ChangeSetPlan,
        mutations: tuple[_PreparedMutation, ...] | list[_PreparedMutation],
    ) -> dict[str, Any]:
        return {
            "plan": plan.model_dump(mode="json"),
            "persistence_bindings": [
                self._persistence_scope_binding(
                    workspace_ref=workspace_ref,
                    operation_ref=item.operation.operation_ref,
                    target_ref=item.operation.target.entity_ref,
                    module_ref=item.module_ref,
                    record_kind_ref=item.record_kind_ref,
                    safe_summary_ref=item.safe_summary_ref,
                    previous_safe_summary_ref=item.previous_safe_summary_ref,
                    replacement_fingerprint_ref=item.replacement_fingerprint_ref,
                    previous_fingerprint_ref=item.previous_fingerprint_ref,
                    search_terms=item.search_terms,
                    retention_ref=item.retention_ref,
                    expires_at=item.expires_at,
                )
                for item in mutations
            ],
        }

    def _rollback_scope_material(
        self,
        *,
        workspace_ref: str,
        rollback_ref: str,
        operations: tuple[PutRecord, ...] | list[PutRecord],
    ) -> dict[str, Any]:
        return {
            "rollback_ref": rollback_ref,
            "operations": [
                {
                    "operation_ref": operation.operation_ref,
                    "record_ref": operation.record_ref,
                    "module_ref": operation.module_ref,
                    "record_kind_ref": operation.record_kind_ref,
                    "safe_summary_ref": operation.safe_summary_ref,
                    "expected_version": operation.expected_version,
                    "private_payload_fingerprint_ref": self._keyed_fingerprint(
                        workspace_ref, operation.private_payload
                    ),
                    "search_terms_fingerprint_ref": self._keyed_fingerprint(
                        workspace_ref, operation.search_terms
                    ),
                    "retention_ref": operation.retention_ref,
                    "expires_at": operation.expires_at,
                }
                for operation in operations
            ],
        }

    def _validate_replacement(
        self,
        *,
        workspace_ref: str,
        intent: LocalUpdateIntent,
        current: LocalRecord,
    ) -> tuple[dict[str, Any], str]:
        spec = _DOMAIN_SPECS.get((intent.module_ref, intent.record_kind_ref))
        if spec is None:
            raise ChangeSetError("ECO_CHANGESET_DOMAIN_ADAPTER_NOT_REGISTERED")
        if intent.entity_kind != spec.entity_kind:
            raise ChangeSetError("ECO_CHANGESET_ENTITY_KIND_MISMATCH")
        if (
            current.module_ref != intent.module_ref
            or current.record_kind_ref != intent.record_kind_ref
            or current.record_ref != intent.record_ref
        ):
            raise ChangeSetError("ECO_CHANGESET_RECORD_BINDING_INVALID")
        if (
            current.retention_ref != intent.retention_ref
            or current.expires_at != intent.expires_at
        ):
            raise ChangeSetError("ECO_CHANGESET_LIFECYCLE_SCOPE_CHANGE_DENIED")
        try:
            current_model = spec.model_type.model_validate(current.private_payload)
            requested_model = spec.model_type.model_validate(intent.replacement_payload)
        except Exception as exc:
            raise ChangeSetError("ECO_CHANGESET_REPLACEMENT_PAYLOAD_INVALID") from exc
        if (
            getattr(current_model, "workspace_ref") != workspace_ref
            or getattr(current_model, spec.ref_field) != intent.record_ref
            or getattr(requested_model, "workspace_ref") != workspace_ref
            or getattr(requested_model, spec.ref_field) != intent.record_ref
        ):
            raise ChangeSetError("ECO_CHANGESET_REPLACEMENT_BINDING_INVALID")
        if (
            spec.version_field is not None
            and getattr(requested_model, spec.version_field) != current.version + 1
        ):
            raise ChangeSetError("ECO_CHANGESET_REPLACEMENT_VERSION_INVALID")
        try:
            model = self._apply_domain_invariants(
                current=current_model,
                requested=requested_model,
            )
        except Exception as exc:
            raise ChangeSetError("ECO_CHANGESET_DOMAIN_INVARIANT_FAILED") from exc
        if tuple(intent.search_terms) != self._canonical_search_terms(model, spec):
            raise ChangeSetError("ECO_CHANGESET_SEARCH_SCOPE_INVALID")
        safe_summary_ref = getattr(model, "safe_summary_ref")
        return model.model_dump(mode="json"), safe_summary_ref

    def _apply_domain_invariants(
        self, *, current: BaseModel, requested: BaseModel
    ) -> BaseModel:
        task_repository = TaskRepository(self.platform)
        if isinstance(requested, CanonicalTask):
            assert isinstance(current, CanonicalTask)
            if current.archived != requested.archived:
                raise ChangeSetConflict("ECO_CHANGESET_TASK_LIFECYCLE_CHANGE_DENIED")
            task_repository._validate_candidate(
                requested, replacing_ref=requested.task_ref
            )
            return requested
        if isinstance(requested, Board):
            assert isinstance(current, Board)
            repository = BoardRepository(self.platform, task_repository=task_repository)
            normalized = repository._with_bounded_undo(
                current=current, snapshot=requested.snapshot()
            )
            repository._validate_new_task_refs(current=current, updated=normalized)
            return normalized
        if isinstance(requested, CalendarSet):
            assert isinstance(current, CalendarSet)
            repository = CalendarRepository(
                self.platform, task_repository=task_repository
            )
            snapshot = requested.snapshot()
            repository._validate_save_lifecycle(current=current, desired=snapshot)
            normalized = repository._with_bounded_undo(
                current=current, snapshot=snapshot
            )
            repository._validate_new_task_refs(current=current, updated=normalized)
            return normalized
        return requested

    @staticmethod
    def _canonical_search_terms(model: BaseModel, spec: _DomainSpec) -> tuple[str, ...]:
        if isinstance(model, CanonicalTask):
            terms = [
                "entity-kind:canonical-task",
                f"task-status:{model.status.value}",
            ]
            if model.project_ref:
                terms.append(
                    "task-project:"
                    f"{hashlib.sha256(model.project_ref.encode()).hexdigest()}"
                )
            if model.mission_binding:
                terms.append(
                    "task-mission:"
                    f"{hashlib.sha256(model.mission_binding.mission_ref.encode()).hexdigest()}"
                )
            terms.extend(
                f"task-tag:{hashlib.sha256(ref.encode()).hexdigest()}"
                for ref in model.tag_refs
            )
            return tuple(terms)
        return (spec.required_search_term,)

    def _field_diffs(
        self,
        *,
        workspace_ref: str,
        operation_ref: str,
        target_ref: str,
        record_kind_ref: str,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> tuple[FieldDiff, ...]:
        diffs: list[FieldDiff] = []
        meaningful_change = False
        for name in sorted(set(before) | set(after)):
            old_present = name in before
            new_present = name in after
            if old_present and new_present and before[name] == after[name]:
                continue
            old_ref = (
                self._keyed_fingerprint(workspace_ref, before[name])
                if old_present
                else None
            )
            new_ref = (
                self._keyed_fingerprint(workspace_ref, after[name])
                if new_present
                else None
            )
            kind = (
                FieldChangeKind.added
                if not old_present
                else FieldChangeKind.removed
                if not new_present
                else FieldChangeKind.updated
            )
            if name != "version":
                meaningful_change = True
            diffs.append(
                FieldDiff(
                    operation_ref=operation_ref,
                    target_ref=target_ref,
                    field_ref=f"field-ref:{record_kind_ref.removeprefix('record-kind-ref:')}:{name}",
                    change_kind=kind,
                    before_fingerprint_ref=old_ref,
                    after_fingerprint_ref=new_ref,
                )
            )
        if not diffs or not meaningful_change:
            raise ChangeSetConflict("ECO_CHANGESET_NO_EFFECT_OPERATION_DENIED")
        return tuple(diffs)

    def prepare_local(
        self,
        *,
        workspace: WorkspaceScope,
        change_set_ref: str,
        intents: tuple[LocalUpdateIntent, ...],
        approval_scope_ref: str,
        idempotency_ref: str,
        expiry_ref: str,
        predicted_result_ref: str,
    ) -> PreparedLocalChangeSet:
        for value in (
            change_set_ref,
            approval_scope_ref,
            idempotency_ref,
            expiry_ref,
            predicted_result_ref,
        ):
            _validate_ref(value)
        if not intents or len(intents) > 63:
            raise ChangeSetError("ECO_CHANGESET_LOCAL_OPERATION_COUNT_INVALID")
        refs = [intent.operation_ref for intent in intents]
        if len(refs) != len(set(refs)):
            raise ChangeSetError("ECO_CHANGESET_DUPLICATE_OPERATION_REF")
        prepared: list[_PreparedMutation] = []
        operations: list[ChangeOperation] = []
        all_diffs: list[FieldDiff] = []
        workspace_ref = workspace.workspace_ref
        seen_operation_refs: set[str] = set()
        for intent in intents:
            for value in (
                intent.operation_ref,
                intent.record_ref,
                intent.module_ref,
                intent.record_kind_ref,
                intent.capability_ref,
                intent.retention_ref,
                *intent.depends_on,
            ):
                _validate_ref(value)
            if not set(intent.depends_on).issubset(seen_operation_refs):
                raise ChangeSetError("ECO_CHANGESET_OPERATION_ORDER_INVALID")
            current = self.platform.read(
                workspace_ref=workspace_ref, record_ref=intent.record_ref
            )
            replacement, safe_summary_ref = self._validate_replacement(
                workspace_ref=workspace_ref, intent=intent, current=current
            )
            current_fingerprint = self._keyed_fingerprint(
                workspace_ref, current.private_payload
            )
            replacement_fingerprint = self._keyed_fingerprint(
                workspace_ref, replacement
            )
            entity_version = EntityVersion(
                version=current.version,
                fingerprint_ref=current_fingerprint,
            )
            target = CanonicalEntityRef(
                entity_ref=intent.record_ref,
                entity_kind=intent.entity_kind,
                canonical_owner=canonical_owner_for(intent.entity_kind),
                workspace=workspace,
                entity_version=entity_version,
            )
            diffs = self._field_diffs(
                workspace_ref=workspace_ref,
                operation_ref=intent.operation_ref,
                target_ref=intent.record_ref,
                record_kind_ref=intent.record_kind_ref,
                before=current.private_payload,
                after=replacement,
            )
            rollback_fingerprint = _stable_ref(
                "rollback-plan-fingerprint-ref",
                {
                    "target_ref": intent.record_ref,
                    "before": current_fingerprint,
                    "after": replacement_fingerprint,
                },
            )
            operation_material = {
                "operation_ref": intent.operation_ref,
                "target": target.model_dump(mode="json"),
                "capability_ref": intent.capability_ref,
                "depends_on": intent.depends_on,
                "replacement_fingerprint_ref": replacement_fingerprint,
                "field_diffs": [item.model_dump(mode="json") for item in diffs],
            }
            operation = ChangeOperation(
                operation_ref=intent.operation_ref,
                target=target,
                capability_ref=intent.capability_ref,
                operation_fingerprint_ref=_stable_ref(
                    "change-operation-fingerprint-ref", operation_material
                ),
                depends_on=intent.depends_on,
                atomicity_posture=AtomicityPosture.local_atomic,
                conflict_precondition=ConflictPrecondition(
                    target_ref=intent.record_ref,
                    expected_version=entity_version,
                ),
                rollback_plan=RollbackPlan(
                    plan_ref=_stable_ref(
                        "rollback-plan-ref",
                        {
                            "change_set_ref": change_set_ref,
                            "operation_ref": intent.operation_ref,
                        },
                    ),
                    target_ref=intent.record_ref,
                    capability_ref=intent.capability_ref,
                    plan_fingerprint_ref=rollback_fingerprint,
                ),
            )
            operations.append(operation)
            all_diffs.extend(diffs)
            prepared.append(
                _PreparedMutation(
                    operation=operation,
                    module_ref=intent.module_ref,
                    record_kind_ref=intent.record_kind_ref,
                    safe_summary_ref=safe_summary_ref,
                    replacement_json=_canonical_json(replacement),
                    replacement_fingerprint_ref=replacement_fingerprint,
                    previous_json=_canonical_json(current.private_payload),
                    previous_fingerprint_ref=current_fingerprint,
                    previous_safe_summary_ref=current.safe_summary_ref,
                    search_terms=tuple(intent.search_terms),
                    retention_ref=intent.retention_ref,
                    expires_at=intent.expires_at,
                    field_diffs=diffs,
                )
            )
            seen_operation_refs.add(intent.operation_ref)
        plan_material = {
            "change_set_ref": change_set_ref,
            "workspace": workspace.model_dump(mode="json"),
            "operations": [item.model_dump(mode="json") for item in operations],
            "approval_scope_ref": approval_scope_ref,
            "idempotency_ref": idempotency_ref,
            "expiry_ref": expiry_ref,
            "predicted_result_ref": predicted_result_ref,
            "field_diffs": [item.model_dump(mode="json") for item in all_diffs],
        }
        plan = ChangeSetPlan(
            change_set_ref=change_set_ref,
            change_set_fingerprint_ref=_stable_ref(
                "change-set-fingerprint-ref", plan_material
            ),
            workspace=workspace,
            operations=tuple(operations),
            approval_scope_ref=approval_scope_ref,
            idempotency_ref=idempotency_ref,
            expiry_ref=expiry_ref,
            predicted_result_ref=predicted_result_ref,
        )
        scope_material = self._prepared_scope_material(
            workspace_ref=workspace_ref,
            plan=plan,
            mutations=prepared,
        )
        scope_ref = _stable_ref("change-set-scope-ref", scope_material)
        context = _stable_ref(
            "change-set-request-context-ref",
            {"kind": "apply", "scope_fingerprint_ref": scope_ref},
        )
        extras = tuple(
            dict.fromkeys(
                (
                    plan.change_set_fingerprint_ref,
                    plan.approval_scope_ref,
                    scope_ref,
                    *(operation.capability_ref for operation in operations),
                    *(
                        operation.rollback_plan.plan_ref
                        for operation in operations
                        if operation.rollback_plan is not None
                    ),
                )
            )
        )
        return PreparedLocalChangeSet(
            plan=plan,
            field_diffs=tuple(all_diffs),
            scope_fingerprint_ref=scope_ref,
            request_context_ref=context,
            approval_resource_refs=extras,
            _mutations=tuple(prepared),
        )

    @staticmethod
    def mutation_resource_refs(
        prepared: PreparedLocalChangeSet | PreparedChangeSetRollback,
        *,
        idempotency_ref: str,
    ) -> tuple[str, ...]:
        if isinstance(prepared, PreparedLocalChangeSet):
            operation_refs = tuple(
                item.operation.operation_ref for item in prepared._mutations
            ) + (f"operation-ref:{prepared.plan.change_set_ref}:ledger",)
            target_refs = tuple(
                item.operation.target.entity_ref for item in prepared._mutations
            ) + (prepared.plan.change_set_ref,)
            workspace_ref = prepared.plan.workspace.workspace_ref
            extras = prepared.approval_resource_refs
        else:
            operation_refs = prepared._operation_refs
            target_refs = prepared._target_refs
            workspace_ref = prepared.approval_resource_refs[0]
            extras = prepared.approval_resource_refs[1:]
        return tuple(
            dict.fromkeys(
                (workspace_ref, idempotency_ref) + operation_refs + target_refs + extras
            )
        )

    def _assert_prepared_current(self, prepared: PreparedLocalChangeSet) -> None:
        for item in prepared._mutations:
            current = self.platform.read(
                workspace_ref=prepared.plan.workspace.workspace_ref,
                record_ref=item.operation.target.entity_ref,
            )
            expected = item.operation.conflict_precondition.expected_version
            if (
                current.version != expected.version
                or current.module_ref != item.module_ref
                or current.record_kind_ref != item.record_kind_ref
                or current.safe_summary_ref != item.previous_safe_summary_ref
                or current.retention_ref != item.retention_ref
                or current.expires_at != item.expires_at
                or self._keyed_fingerprint(
                    prepared.plan.workspace.workspace_ref, current.private_payload
                )
                != expected.fingerprint_ref
            ):
                raise ChangeSetConflict("ECO_CHANGESET_CONFLICT_PRECONDITION_FAILED")
            spec = _DOMAIN_SPECS.get((item.module_ref, item.record_kind_ref))
            if spec is None:
                raise ChangeSetError("ECO_CHANGESET_DOMAIN_ADAPTER_NOT_REGISTERED")
            try:
                current_model = spec.model_type.model_validate(current.private_payload)
                requested_model = spec.model_type.model_validate(
                    json.loads(item.replacement_json)
                )
                normalized = self._apply_domain_invariants(
                    current=current_model,
                    requested=requested_model,
                )
            except Exception as exc:
                raise ChangeSetConflict(
                    "ECO_CHANGESET_DOMAIN_PRECONDITION_FAILED"
                ) from exc
            if normalized.model_dump(mode="json") != json.loads(item.replacement_json):
                raise ChangeSetConflict("ECO_CHANGESET_DOMAIN_PRECONDITION_FAILED")
            if tuple(item.search_terms) != self._canonical_search_terms(
                normalized, spec
            ):
                raise ChangeSetConflict("ECO_CHANGESET_DOMAIN_PRECONDITION_FAILED")

    def _assert_prepared_integrity(self, prepared: PreparedLocalChangeSet) -> None:
        if (
            tuple(item.operation for item in prepared._mutations)
            != prepared.plan.operations
        ):
            raise ChangeSetConflict("ECO_CHANGESET_PREPARED_OPERATION_BINDING_INVALID")
        flattened_diffs = tuple(
            diff for item in prepared._mutations for diff in item.field_diffs
        )
        if flattened_diffs != prepared.field_diffs:
            raise ChangeSetConflict("ECO_CHANGESET_PREPARED_DIFF_BINDING_INVALID")
        for item in prepared._mutations:
            replacement = json.loads(item.replacement_json)
            previous = json.loads(item.previous_json)
            if (
                self._keyed_fingerprint(
                    prepared.plan.workspace.workspace_ref, replacement
                )
                != item.replacement_fingerprint_ref
                or self._keyed_fingerprint(
                    prepared.plan.workspace.workspace_ref, previous
                )
                != item.previous_fingerprint_ref
            ):
                raise ChangeSetConflict(
                    "ECO_CHANGESET_PREPARED_PRIVATE_FINGERPRINT_INVALID"
                )
            spec = _DOMAIN_SPECS.get((item.module_ref, item.record_kind_ref))
            if spec is None:
                raise ChangeSetError("ECO_CHANGESET_DOMAIN_ADAPTER_NOT_REGISTERED")
            try:
                model = spec.model_type.model_validate(replacement)
                previous_model = spec.model_type.model_validate(previous)
            except Exception as exc:
                raise ChangeSetConflict(
                    "ECO_CHANGESET_PREPARED_REPLACEMENT_INVALID"
                ) from exc
            target = item.operation.target
            if (
                getattr(model, "workspace_ref") != prepared.plan.workspace.workspace_ref
                or getattr(model, spec.ref_field) != target.entity_ref
                or target.workspace != prepared.plan.workspace
                or target.entity_kind != spec.entity_kind
                or target.canonical_owner != canonical_owner_for(spec.entity_kind)
            ):
                raise ChangeSetConflict(
                    "ECO_CHANGESET_PREPARED_REPLACEMENT_BINDING_INVALID"
                )
            if getattr(model, "safe_summary_ref") != item.safe_summary_ref:
                raise ChangeSetConflict(
                    "ECO_CHANGESET_PREPARED_SUMMARY_BINDING_INVALID"
                )
            if (
                getattr(previous_model, "workspace_ref")
                != prepared.plan.workspace.workspace_ref
                or getattr(previous_model, spec.ref_field) != target.entity_ref
                or getattr(previous_model, "safe_summary_ref")
                != item.previous_safe_summary_ref
            ):
                raise ChangeSetConflict(
                    "ECO_CHANGESET_PREPARED_PREVIOUS_BINDING_INVALID"
                )
            if tuple(item.search_terms) != self._canonical_search_terms(model, spec):
                raise ChangeSetConflict("ECO_CHANGESET_PREPARED_SEARCH_SCOPE_INVALID")
        plan_material = {
            "change_set_ref": prepared.plan.change_set_ref,
            "workspace": prepared.plan.workspace.model_dump(mode="json"),
            "operations": [
                item.model_dump(mode="json") for item in prepared.plan.operations
            ],
            "approval_scope_ref": prepared.plan.approval_scope_ref,
            "idempotency_ref": prepared.plan.idempotency_ref,
            "expiry_ref": prepared.plan.expiry_ref,
            "predicted_result_ref": prepared.plan.predicted_result_ref,
            "field_diffs": [
                item.model_dump(mode="json") for item in prepared.field_diffs
            ],
        }
        expected_plan_ref = _stable_ref("change-set-fingerprint-ref", plan_material)
        scope_material = self._prepared_scope_material(
            workspace_ref=prepared.plan.workspace.workspace_ref,
            plan=prepared.plan,
            mutations=prepared._mutations,
        )
        expected_scope_ref = _stable_ref("change-set-scope-ref", scope_material)
        expected_context_ref = _stable_ref(
            "change-set-request-context-ref",
            {"kind": "apply", "scope_fingerprint_ref": expected_scope_ref},
        )
        expected_extras = tuple(
            dict.fromkeys(
                (
                    expected_plan_ref,
                    prepared.plan.approval_scope_ref,
                    expected_scope_ref,
                    *(
                        operation.capability_ref
                        for operation in prepared.plan.operations
                    ),
                    *(
                        operation.rollback_plan.plan_ref
                        for operation in prepared.plan.operations
                        if operation.rollback_plan is not None
                    ),
                )
            )
        )
        if (
            prepared.plan.change_set_fingerprint_ref != expected_plan_ref
            or prepared.scope_fingerprint_ref != expected_scope_ref
            or prepared.request_context_ref != expected_context_ref
            or prepared.approval_resource_refs != expected_extras
        ):
            raise ChangeSetConflict("ECO_CHANGESET_PREPARED_SCOPE_INVALID")

    def _ledger_payload(self, prepared: PreparedLocalChangeSet) -> dict[str, Any]:
        return {
            "schema_version": ECO_CHANGESET_SCHEMA_VERSION,
            "change_set_ref": prepared.plan.change_set_ref,
            "change_set_fingerprint_ref": prepared.plan.change_set_fingerprint_ref,
            "scope_fingerprint_ref": prepared.scope_fingerprint_ref,
            "state": ChangeSetExecutionState.applied.value,
            "version": 1,
            "plan": prepared.plan.model_dump(mode="json"),
            "field_diffs": [
                item.model_dump(mode="json") for item in prepared.field_diffs
            ],
            "rollback_mutations": [
                {
                    "operation_ref": item.operation.operation_ref,
                    "target_ref": item.operation.target.entity_ref,
                    "module_ref": item.module_ref,
                    "record_kind_ref": item.record_kind_ref,
                    "applied_safe_summary_ref": item.safe_summary_ref,
                    "previous_safe_summary_ref": item.previous_safe_summary_ref,
                    "private_payload": json.loads(item.previous_json),
                    "search_terms": list(item.search_terms),
                    "retention_ref": item.retention_ref,
                    "expires_at": item.expires_at,
                    "previous_payload_fingerprint_ref": item.previous_fingerprint_ref,
                    "applied_payload_fingerprint_ref": item.replacement_fingerprint_ref,
                }
                for item in prepared._mutations
            ],
        }

    def apply_local(
        self,
        prepared: PreparedLocalChangeSet,
        *,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> ChangeSetExecutionReceipt:
        self._assert_prepared_integrity(prepared)
        if idempotency_ref != prepared.plan.idempotency_ref:
            raise ChangeSetConflict("ECO_CHANGESET_IDEMPOTENCY_BINDING_INVALID")
        workspace_ref = prepared.plan.workspace.workspace_ref
        resources = self.mutation_resource_refs(
            prepared, idempotency_ref=idempotency_ref
        )
        replay = self.platform.replay_receipt(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            resource_refs=resources,
            approval=approval,
            requested_action=ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
            request_context_ref=prepared.request_context_ref,
        )
        if replay is not None:
            return self._execution_receipt(prepared, replay, replayed=True)
        self._assert_prepared_current(prepared)
        ledger_operation_ref = f"operation-ref:{prepared.plan.change_set_ref}:ledger"
        ledger_payload = self._ledger_payload(prepared)
        operations = tuple(
            PutRecord(
                operation_ref=item.operation.operation_ref,
                module_ref=item.module_ref,
                record_ref=item.operation.target.entity_ref,
                record_kind_ref=item.record_kind_ref,
                safe_summary_ref=item.safe_summary_ref,
                private_payload=json.loads(item.replacement_json),
                search_terms=item.search_terms,
                expected_version=item.operation.target.entity_version.version,
                retention_ref=item.retention_ref,
                expires_at=item.expires_at,
            )
            for item in prepared._mutations
        ) + (
            PutRecord(
                operation_ref=ledger_operation_ref,
                module_ref=ECO_CHANGESET_MODULE_REF,
                record_ref=prepared.plan.change_set_ref,
                record_kind_ref=ECO_CHANGESET_EXECUTION_RECORD_KIND_REF,
                safe_summary_ref=self._ledger_summary(ledger_payload),
                private_payload=ledger_payload,
                search_terms=(_ALL_CHANGESETS_TERM,),
                expected_version=0,
                retention_ref=ECO_CHANGESET_RETENTION_REF,
            ),
        )
        try:
            receipt = self.platform._apply_registered_domain(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=operations,
                approval=approval,
                requested_action=ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
                request_context_ref=prepared.request_context_ref,
                approval_resource_refs=prepared.approval_resource_refs,
            )
        except EcosystemConflict as exc:
            raise ChangeSetConflict("ECO_CHANGESET_ATOMIC_CONFLICT") from exc
        return self._execution_receipt(prepared, receipt, replayed=False)

    @staticmethod
    def _ledger_summary(payload: dict[str, Any]) -> str:
        return _stable_ref(
            "change-set-execution-summary-ref",
            {
                "change_set_ref": payload["change_set_ref"],
                "change_set_fingerprint_ref": payload["change_set_fingerprint_ref"],
                "state": payload["state"],
                "version": payload["version"],
            },
        )

    @staticmethod
    def _execution_receipt(
        prepared: PreparedLocalChangeSet,
        receipt: UnitOfWorkReceipt,
        *,
        replayed: bool,
    ) -> ChangeSetExecutionReceipt:
        operation_receipts = receipt.operation_receipt_refs[:-1]
        status = (
            OperationResultStatus.replayed
            if replayed
            else OperationResultStatus.applied
        )
        return ChangeSetExecutionReceipt(
            change_set_ref=prepared.plan.change_set_ref,
            change_set_fingerprint_ref=prepared.plan.change_set_fingerprint_ref,
            state=ChangeSetExecutionState.applied,
            uow_receipt_ref=receipt.receipt_ref,
            rollback_ref=_stable_ref(
                "rollback-ref",
                {
                    "change_set_ref": prepared.plan.change_set_ref,
                    "change_set_fingerprint_ref": prepared.plan.change_set_fingerprint_ref,
                },
            ),
            operation_results=tuple(
                ChangeSetOperationResult(
                    operation_ref=item.operation.operation_ref,
                    target_ref=item.operation.target.entity_ref,
                    status=status,
                    operation_receipt_ref=operation_receipts[index],
                )
                for index, item in enumerate(prepared._mutations)
            ),
            replayed=replayed,
        )

    def prepare_undo(
        self, *, workspace_ref: str, change_set_ref: str
    ) -> PreparedChangeSetRollback:
        record = self.platform.read(
            workspace_ref=workspace_ref, record_ref=change_set_ref
        )
        payload = record.private_payload
        if (
            record.module_ref != ECO_CHANGESET_MODULE_REF
            or record.record_kind_ref != ECO_CHANGESET_EXECUTION_RECORD_KIND_REF
            or payload.get("schema_version") != ECO_CHANGESET_SCHEMA_VERSION
            or payload.get("change_set_ref") != change_set_ref
            or payload.get("state") != ChangeSetExecutionState.applied.value
            or payload.get("version") != record.version
            or not isinstance(payload.get("rollback_mutations"), list)
            or record.safe_summary_ref != self._ledger_summary(payload)
            or record.retention_ref != ECO_CHANGESET_RETENTION_REF
            or record.expires_at is not None
            or record.archived
        ):
            raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_LEDGER_INVALID")
        try:
            plan = ChangeSetPlan.model_validate(payload["plan"])
            field_diffs = tuple(
                FieldDiff.model_validate(item) for item in payload["field_diffs"]
            )
        except Exception as exc:
            raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_LEDGER_INVALID") from exc
        plan_material = {
            "change_set_ref": plan.change_set_ref,
            "workspace": plan.workspace.model_dump(mode="json"),
            "operations": [item.model_dump(mode="json") for item in plan.operations],
            "approval_scope_ref": plan.approval_scope_ref,
            "idempotency_ref": plan.idempotency_ref,
            "expiry_ref": plan.expiry_ref,
            "predicted_result_ref": plan.predicted_result_ref,
            "field_diffs": [item.model_dump(mode="json") for item in field_diffs],
        }
        if (
            plan.change_set_ref != change_set_ref
            or plan.workspace.workspace_ref != workspace_ref
            or plan.change_set_fingerprint_ref
            != _stable_ref("change-set-fingerprint-ref", plan_material)
            or plan.change_set_fingerprint_ref != payload["change_set_fingerprint_ref"]
        ):
            raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_LEDGER_INVALID")
        rollback_mutations = payload["rollback_mutations"]
        if len(rollback_mutations) != len(plan.operations):
            raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_LEDGER_INVALID")
        try:
            persistence_bindings = []
            for index, item in enumerate(rollback_mutations):
                if not isinstance(item, dict):
                    raise ValueError("rollback mutation must be an object")
                operation = plan.operations[index]
                if (
                    item["operation_ref"] != operation.operation_ref
                    or item["target_ref"] != operation.target.entity_ref
                ):
                    raise ValueError("rollback mutation plan binding mismatch")
                persistence_bindings.append(
                    self._persistence_scope_binding(
                        workspace_ref=workspace_ref,
                        operation_ref=item["operation_ref"],
                        target_ref=item["target_ref"],
                        module_ref=item["module_ref"],
                        record_kind_ref=item["record_kind_ref"],
                        safe_summary_ref=item["applied_safe_summary_ref"],
                        previous_safe_summary_ref=item["previous_safe_summary_ref"],
                        replacement_fingerprint_ref=item[
                            "applied_payload_fingerprint_ref"
                        ],
                        previous_fingerprint_ref=item[
                            "previous_payload_fingerprint_ref"
                        ],
                        search_terms=tuple(item["search_terms"]),
                        retention_ref=item["retention_ref"],
                        expires_at=item["expires_at"],
                    )
                )
        except (KeyError, TypeError, ValueError) as exc:
            raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_LEDGER_INVALID") from exc
        expected_apply_scope = _stable_ref(
            "change-set-scope-ref",
            {
                "plan": plan.model_dump(mode="json"),
                "persistence_bindings": persistence_bindings,
            },
        )
        if expected_apply_scope != payload["scope_fingerprint_ref"]:
            raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_LEDGER_INVALID")
        operations: list[PutRecord] = []
        operation_refs: list[str] = []
        target_refs: list[str] = []
        for index, item in enumerate(rollback_mutations):
            target_ref = item["target_ref"]
            current = self.platform.read(
                workspace_ref=workspace_ref, record_ref=target_ref
            )
            if (
                current.module_ref != item["module_ref"]
                or current.record_kind_ref != item["record_kind_ref"]
                or current.safe_summary_ref != item["applied_safe_summary_ref"]
                or current.retention_ref != item["retention_ref"]
                or current.expires_at != item["expires_at"]
                or self._keyed_fingerprint(workspace_ref, current.private_payload)
                != item["applied_payload_fingerprint_ref"]
                or self._keyed_fingerprint(workspace_ref, item["private_payload"])
                != item["previous_payload_fingerprint_ref"]
            ):
                raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_TARGET_CHANGED")
            restored = dict(item["private_payload"])
            spec = _DOMAIN_SPECS.get((item["module_ref"], item["record_kind_ref"]))
            if spec is None:
                raise ChangeSetError("ECO_CHANGESET_DOMAIN_ADAPTER_NOT_REGISTERED")
            if spec.version_field is not None:
                restored[spec.version_field] = current.version + 1
            try:
                current_model = spec.model_type.model_validate(current.private_payload)
                requested_model = spec.model_type.model_validate(restored)
                model = self._apply_domain_invariants(
                    current=current_model,
                    requested=requested_model,
                )
            except Exception as exc:
                raise ChangeSetError("ECO_CHANGESET_ROLLBACK_PAYLOAD_INVALID") from exc
            if tuple(item["search_terms"]) != self._canonical_search_terms(model, spec):
                raise ChangeSetError("ECO_CHANGESET_ROLLBACK_PAYLOAD_INVALID")
            rollback_operation_ref = f"operation-ref:{change_set_ref}:rollback:{index}"
            operations.append(
                PutRecord(
                    operation_ref=rollback_operation_ref,
                    module_ref=item["module_ref"],
                    record_ref=target_ref,
                    record_kind_ref=item["record_kind_ref"],
                    safe_summary_ref=getattr(model, "safe_summary_ref"),
                    private_payload=model.model_dump(mode="json"),
                    search_terms=tuple(item["search_terms"]),
                    expected_version=current.version,
                    retention_ref=item["retention_ref"],
                    expires_at=item["expires_at"],
                )
            )
            operation_refs.append(rollback_operation_ref)
            target_refs.append(target_ref)
        rolled_back_payload = {
            **payload,
            "state": ChangeSetExecutionState.rolled_back.value,
            "version": record.version + 1,
        }
        ledger_operation_ref = f"operation-ref:{change_set_ref}:rollback:ledger"
        operations.append(
            PutRecord(
                operation_ref=ledger_operation_ref,
                module_ref=ECO_CHANGESET_MODULE_REF,
                record_ref=change_set_ref,
                record_kind_ref=ECO_CHANGESET_EXECUTION_RECORD_KIND_REF,
                safe_summary_ref=self._ledger_summary(rolled_back_payload),
                private_payload=rolled_back_payload,
                search_terms=(_ALL_CHANGESETS_TERM,),
                expected_version=record.version,
                retention_ref=ECO_CHANGESET_RETENTION_REF,
            )
        )
        operation_refs.append(ledger_operation_ref)
        target_refs.append(change_set_ref)
        rollback_ref = _stable_ref(
            "rollback-ref",
            {
                "change_set_ref": change_set_ref,
                "change_set_fingerprint_ref": payload["change_set_fingerprint_ref"],
            },
        )
        scope = _stable_ref(
            "change-set-rollback-scope-ref",
            self._rollback_scope_material(
                workspace_ref=workspace_ref,
                rollback_ref=rollback_ref,
                operations=operations,
            ),
        )
        context = _stable_ref(
            "change-set-request-context-ref",
            {"kind": "rollback", "scope_fingerprint_ref": scope},
        )
        extras = (
            workspace_ref,
            payload["change_set_fingerprint_ref"],
            rollback_ref,
            scope,
        )
        return PreparedChangeSetRollback(
            change_set_ref=change_set_ref,
            change_set_fingerprint_ref=payload["change_set_fingerprint_ref"],
            rollback_ref=rollback_ref,
            scope_fingerprint_ref=scope,
            request_context_ref=context,
            approval_resource_refs=extras,
            _operations=tuple(operations),
            _operation_refs=tuple(operation_refs),
            _target_refs=tuple(target_refs),
        )

    prepare_rollback = prepare_undo

    def rollback(
        self,
        prepared: PreparedChangeSetRollback,
        *,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> ChangeSetExecutionReceipt:
        if not prepared.approval_resource_refs:
            raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_SCOPE_INVALID")
        workspace_ref = prepared.approval_resource_refs[0]
        expected_rollback_ref = _stable_ref(
            "rollback-ref",
            {
                "change_set_ref": prepared.change_set_ref,
                "change_set_fingerprint_ref": prepared.change_set_fingerprint_ref,
            },
        )
        expected_scope = _stable_ref(
            "change-set-rollback-scope-ref",
            self._rollback_scope_material(
                workspace_ref=workspace_ref,
                rollback_ref=expected_rollback_ref,
                operations=prepared._operations,
            ),
        )
        expected_context = _stable_ref(
            "change-set-request-context-ref",
            {"kind": "rollback", "scope_fingerprint_ref": expected_scope},
        )
        if (
            prepared.rollback_ref != expected_rollback_ref
            or prepared.scope_fingerprint_ref != expected_scope
            or prepared.request_context_ref != expected_context
            or prepared.approval_resource_refs
            != (
                workspace_ref,
                prepared.change_set_fingerprint_ref,
                prepared.rollback_ref,
                expected_scope,
            )
            or prepared._operation_refs
            != tuple(item.operation_ref for item in prepared._operations)
            or prepared._target_refs
            != tuple(item.record_ref for item in prepared._operations)
        ):
            raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_SCOPE_INVALID")
        resources = self.mutation_resource_refs(
            prepared, idempotency_ref=idempotency_ref
        )
        replay = self.platform.replay_receipt(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            resource_refs=resources,
            approval=approval,
            requested_action=ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
            request_context_ref=prepared.request_context_ref,
        )
        if replay is None:
            try:
                replay = self.platform._apply_registered_domain(
                    workspace_ref=workspace_ref,
                    idempotency_ref=idempotency_ref,
                    operations=prepared._operations,
                    approval=approval,
                    requested_action=ECO_CHANGESET_LOCAL_ATOMIC_ACTION,
                    request_context_ref=prepared.request_context_ref,
                    approval_resource_refs=prepared.approval_resource_refs[1:],
                )
            except EcosystemConflict as exc:
                raise ChangeSetConflict("ECO_CHANGESET_ROLLBACK_CONFLICT") from exc
            replayed = False
        else:
            replayed = True
        operation_receipts = replay.operation_receipt_refs[:-1]
        return ChangeSetExecutionReceipt(
            change_set_ref=prepared.change_set_ref,
            change_set_fingerprint_ref=prepared.change_set_fingerprint_ref,
            state=ChangeSetExecutionState.rolled_back,
            uow_receipt_ref=replay.receipt_ref,
            rollback_ref=prepared.rollback_ref,
            operation_results=tuple(
                ChangeSetOperationResult(
                    operation_ref=operation_ref,
                    target_ref=prepared._target_refs[index],
                    status=(
                        OperationResultStatus.replayed
                        if replayed
                        else OperationResultStatus.applied
                    ),
                    operation_receipt_ref=operation_receipts[index],
                )
                for index, operation_ref in enumerate(prepared._operation_refs[:-1])
            ),
            replayed=replayed,
        )

    @staticmethod
    def project_external_outcomes(
        plan: ChangeSetPlan,
        outcomes: tuple[ExternalOutcomeObservation, ...],
    ) -> ExternalOutcomeProjection:
        external = {
            item.operation_ref: item
            for item in plan.operations
            if item.atomicity_posture == AtomicityPosture.external_compensating
        }
        if not external or set(external) != {item.operation_ref for item in outcomes}:
            raise ChangeSetError("ECO_CHANGESET_EXTERNAL_OUTCOME_MEMBERSHIP_INVALID")
        if tuple(external) != tuple(item.operation_ref for item in outcomes):
            raise ChangeSetError("ECO_CHANGESET_EXTERNAL_OUTCOME_ORDER_INVALID")
        by_ref = {item.operation_ref: item for item in outcomes}
        if len(by_ref) != len(outcomes):
            raise ChangeSetError("ECO_CHANGESET_EXTERNAL_OUTCOME_DUPLICATE_REF")
        terminal = {
            OperationResultStatus.applied,
            OperationResultStatus.replayed,
            OperationResultStatus.skipped,
            OperationResultStatus.denied,
            OperationResultStatus.conflicted,
            OperationResultStatus.failed,
            OperationResultStatus.compensated,
            OperationResultStatus.compensation_failed,
        }
        if any(item.status not in terminal for item in outcomes):
            raise ChangeSetError("ECO_CHANGESET_EXTERNAL_OUTCOME_NOT_TERMINAL")
        for operation_ref, operation in external.items():
            if by_ref[operation_ref].status in {
                OperationResultStatus.applied,
                OperationResultStatus.replayed,
            }:
                for dependency_ref in operation.depends_on:
                    dependency = by_ref.get(dependency_ref)
                    if dependency is None or dependency.status not in {
                        OperationResultStatus.applied,
                        OperationResultStatus.replayed,
                    }:
                        raise ChangeSetError(
                            "ECO_CHANGESET_EXTERNAL_DEPENDENCY_OUTCOME_INVALID"
                        )
        compensation_refs = tuple(
            operation.compensation_plan.plan_ref
            for operation in external.values()
            if operation.compensation_plan is not None
            and by_ref[operation.operation_ref].status
            in {
                OperationResultStatus.failed,
                OperationResultStatus.compensation_failed,
            }
        )
        distinct = {item.status for item in outcomes}
        material = {
            "change_set_ref": plan.change_set_ref,
            "outcomes": [item.model_dump(mode="json") for item in outcomes],
            "compensation_plan_refs": compensation_refs,
        }
        return ExternalOutcomeProjection(
            change_set_ref=plan.change_set_ref,
            outcomes=outcomes,
            partial_completion=len(distinct) > 1
            or any(
                item.status
                not in {OperationResultStatus.applied, OperationResultStatus.replayed}
                for item in outcomes
            ),
            compensation_plan_refs=compensation_refs,
            projection_ref=_stable_ref("external-outcome-projection-ref", material),
            next_safe_action_ref=(
                "next-safe-action-ref:review-compensation"
                if compensation_refs
                else "next-safe-action-ref:reconcile-external-outcomes"
            ),
        )


__all__ = [
    "ECO_CHANGESET_EXECUTION_RECORD_KIND_REF",
    "ECO_CHANGESET_LOCAL_ATOMIC_ACTION",
    "ECO_CHANGESET_MODULE_REF",
    "ECO_CHANGESET_MUTATION_ACTION",
    "ECO_CHANGESET_SCHEMA_VERSION",
    "ECO_ENTITY_LINK_RECORD_KIND_REF",
    "ChangeSetConflict",
    "ChangeSetEngine",
    "ChangeSetError",
    "ChangeSetExecutionReceipt",
    "ChangeSetExecutionState",
    "ChangeSetOperationResult",
    "EntityLinkRecord",
    "EntityLinkRepository",
    "ExternalOutcomeObservation",
    "ExternalOutcomeProjection",
    "FieldChangeKind",
    "FieldDiff",
    "LocalUpdateIntent",
    "PreparedChangeSetRollback",
    "PreparedLocalChangeSet",
]
