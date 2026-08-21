"""Encrypted first-class local CRM foundation for ECO-005.

CRM owns private identity, relationship, activity, follow-up, and opportunity
metadata. Reusable Boards remains the sole owner of pipeline lanes, card
placement, and ordering. This module adds no route, UI, connector, model,
network, account-sync, send, or calendar-write runtime.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.ecosystem.boards import (
    BoardRepository,
    BoardSubjectKind,
)
from ultimate_ai_agent.core.ecosystem.local_data import (
    ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES,
    EcosystemConflict,
    EcosystemLocalDataError,
    EcosystemLocalDataPlatform,
    PutRecord,
    UnitOfWorkReceipt,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_CRM_SCHEMA_VERSION = "uaa-eco-005-crm-private-portfolio.v1"
ECO_CRM_MUTATION_ACTION = "ecosystem.crm.apply"
ECO_CRM_MODULE_REF = "module-ref:crm"
ECO_CRM_RECORD_KIND_REF = "record-kind-ref:crm-private-portfolio"
ECO_CRM_RETENTION_REF = "retention-ref:crm-private-operator-managed"
_ALL_CRM_PORTFOLIOS_SEARCH_TERM = "entity-kind:crm-private-portfolio"
_MAX_UNDO_DEPTH = 20
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")


class PrivateCrmError(RuntimeError):
    """Fail-closed CRM error with a stable, non-sensitive code."""


class PrivateCrmConflict(PrivateCrmError):
    pass


class CrmWorkspacePreset(str, Enum):
    personal_network = "personal_network"
    private_relationships = "private_relationships"
    sales = "sales"
    real_estate = "real_estate"
    professional_network = "professional_network"


class CrmContactPointKind(str, Enum):
    email = "email"
    phone = "phone"
    address = "address"
    handle = "handle"
    other = "other"


class CrmActivityKind(str, Enum):
    note = "note"
    call = "call"
    meeting = "meeting"
    message = "message"
    email = "email"
    task_link = "task_link"
    event_link = "event_link"


class CrmFollowUpState(str, Enum):
    open = "open"
    completed = "completed"
    cancelled = "cancelled"


class _PrivateCrmModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _validate_ref(value: str, field_name: str) -> str:
    if not _SAFE_REF_RE.fullmatch(value) or contains_obvious_secret(value):
        raise ValueError(f"ECO_CRM_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"ECO_CRM_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _validate_ref(value, field_name)
    return values


def _private_text(value: str, *, maximum: int, code: str) -> str:
    if not value or len(value.encode("utf-8")) > maximum:
        raise ValueError(code)
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise ValueError(code)
    return value


def _optional_private_text(value: str | None, *, maximum: int, code: str) -> None:
    if value is not None:
        _private_text(value, maximum=maximum, code=code)


def _aware(value: datetime, code: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(code)
    return value


def _stable_ref(prefix: str, payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return f"{prefix}:sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validation_code(exc: ValueError) -> str:
    match = re.search(r"ECO_CRM_[A-Z0-9_]+", str(exc))
    return match.group(0) if match else "ECO_CRM_MUTATION_INVARIANT_DENIED"


class CrmPrivacyPolicy(_PrivateCrmModel):
    included_in_global_search: bool = True
    included_in_today: bool = True
    included_in_briefing: bool = True
    included_in_memory: bool = True
    included_in_general_export: bool = True


class PrivateCrmWorkspace(_PrivateCrmModel):
    crm_workspace_ref: str
    name: str = Field(..., repr=False)
    preset: CrmWorkspacePreset
    privacy_policy: CrmPrivacyPolicy = CrmPrivacyPolicy()
    archived: bool = False

    @model_validator(mode="before")
    @classmethod
    def apply_private_relationship_defaults(cls, value: Any) -> Any:
        if not isinstance(value, dict) or "privacy_policy" in value:
            return value
        preset = value.get("preset")
        if preset not in (
            CrmWorkspacePreset.private_relationships,
            CrmWorkspacePreset.private_relationships.value,
        ):
            return value
        return {
            **value,
            "privacy_policy": CrmPrivacyPolicy(
                included_in_global_search=False,
                included_in_today=False,
                included_in_briefing=False,
                included_in_memory=False,
                included_in_general_export=False,
            ),
        }

    @model_validator(mode="after")
    def validate_workspace(self) -> "PrivateCrmWorkspace":
        _validate_ref(self.crm_workspace_ref, "crm_workspace_ref")
        _private_text(self.name, maximum=512, code="ECO_CRM_WORKSPACE_NAME_INVALID")
        if self.preset == CrmWorkspacePreset.private_relationships and any(
            (
                self.privacy_policy.included_in_global_search,
                self.privacy_policy.included_in_today,
                self.privacy_policy.included_in_briefing,
                self.privacy_policy.included_in_memory,
                self.privacy_policy.included_in_general_export,
            )
        ):
            raise ValueError("ECO_CRM_PRIVATE_RELATIONSHIPS_ISOLATION_REQUIRED")
        return self


class PrivateCrmContactPoint(_PrivateCrmModel):
    contact_point_ref: str
    kind: CrmContactPointKind
    value: str = Field(..., repr=False)
    label: str | None = Field(default=None, repr=False)
    preferred: bool = False

    @model_validator(mode="after")
    def validate_contact_point(self) -> "PrivateCrmContactPoint":
        _validate_ref(self.contact_point_ref, "contact_point_ref")
        _private_text(self.value, maximum=8_192, code="ECO_CRM_CONTACT_VALUE_INVALID")
        _optional_private_text(
            self.label, maximum=256, code="ECO_CRM_CONTACT_LABEL_INVALID"
        )
        return self


class PrivateCrmPerson(_PrivateCrmModel):
    person_ref: str
    display_name: str = Field(..., repr=False)
    contact_points: tuple[PrivateCrmContactPoint, ...] = Field(
        default=(), max_length=128, repr=False
    )
    aliases: tuple[str, ...] = Field(default=(), max_length=128, repr=False)
    archived: bool = False

    @model_validator(mode="after")
    def validate_person(self) -> "PrivateCrmPerson":
        _validate_ref(self.person_ref, "person_ref")
        _private_text(self.display_name, maximum=2_048, code="ECO_CRM_PERSON_NAME_INVALID")
        _validate_refs(
            tuple(item.contact_point_ref for item in self.contact_points),
            "contact_point_ref",
        )
        for alias in self.aliases:
            _private_text(alias, maximum=2_048, code="ECO_CRM_ALIAS_INVALID")
        return self


class PrivateCrmOrganization(_PrivateCrmModel):
    organization_ref: str
    name: str = Field(..., repr=False)
    website: str | None = Field(default=None, repr=False)
    archived: bool = False

    @model_validator(mode="after")
    def validate_organization(self) -> "PrivateCrmOrganization":
        _validate_ref(self.organization_ref, "organization_ref")
        _private_text(self.name, maximum=2_048, code="ECO_CRM_ORGANIZATION_NAME_INVALID")
        _optional_private_text(
            self.website, maximum=8_192, code="ECO_CRM_ORGANIZATION_WEBSITE_INVALID"
        )
        return self


class PrivateCrmWorkspaceContext(_PrivateCrmModel):
    context_ref: str
    crm_workspace_ref: str
    person_ref: str | None = None
    organization_ref: str | None = None
    role: str | None = Field(default=None, repr=False)
    notes: str | None = Field(default=None, repr=False)
    tag_refs: tuple[str, ...] = Field(default=(), max_length=128)
    important_dates: tuple[date, ...] = Field(default=(), max_length=128, repr=False)
    archived: bool = False

    @model_validator(mode="after")
    def validate_context(self) -> "PrivateCrmWorkspaceContext":
        _validate_ref(self.context_ref, "context_ref")
        _validate_ref(self.crm_workspace_ref, "crm_workspace_ref")
        if (self.person_ref is None) == (self.organization_ref is None):
            raise ValueError("ECO_CRM_CONTEXT_EXACTLY_ONE_SUBJECT_REQUIRED")
        if self.person_ref is not None:
            _validate_ref(self.person_ref, "person_ref")
        if self.organization_ref is not None:
            _validate_ref(self.organization_ref, "organization_ref")
        _optional_private_text(self.role, maximum=1_024, code="ECO_CRM_ROLE_INVALID")
        _optional_private_text(self.notes, maximum=131_072, code="ECO_CRM_NOTES_INVALID")
        _validate_refs(self.tag_refs, "tag_ref")
        return self


class PrivateCrmRelationship(_PrivateCrmModel):
    relationship_ref: str
    crm_workspace_ref: str
    from_context_ref: str
    to_context_ref: str
    relationship_type: str = Field(..., repr=False)
    state: str | None = Field(default=None, repr=False)
    notes: str | None = Field(default=None, repr=False)
    archived: bool = False

    @model_validator(mode="after")
    def validate_relationship(self) -> "PrivateCrmRelationship":
        for field_name in (
            "relationship_ref",
            "crm_workspace_ref",
            "from_context_ref",
            "to_context_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if self.from_context_ref == self.to_context_ref:
            raise ValueError("ECO_CRM_RELATIONSHIP_SELF_LINK_DENIED")
        _private_text(
            self.relationship_type,
            maximum=1_024,
            code="ECO_CRM_RELATIONSHIP_TYPE_INVALID",
        )
        _optional_private_text(self.state, maximum=1_024, code="ECO_CRM_STATE_INVALID")
        _optional_private_text(self.notes, maximum=65_536, code="ECO_CRM_NOTES_INVALID")
        return self


class PrivateCrmActivity(_PrivateCrmModel):
    activity_ref: str
    crm_workspace_ref: str
    context_refs: tuple[str, ...] = Field(..., min_length=1, max_length=256)
    kind: CrmActivityKind
    occurred_at: datetime
    summary: str = Field(..., repr=False)
    notes: str | None = Field(default=None, repr=False)
    task_ref: str | None = None
    event_ref: str | None = None
    archived: bool = False

    @model_validator(mode="after")
    def validate_activity(self) -> "PrivateCrmActivity":
        _validate_ref(self.activity_ref, "activity_ref")
        _validate_ref(self.crm_workspace_ref, "crm_workspace_ref")
        _validate_refs(self.context_refs, "context_ref")
        _aware(self.occurred_at, "ECO_CRM_ACTIVITY_TIME_INVALID")
        _private_text(self.summary, maximum=8_192, code="ECO_CRM_ACTIVITY_SUMMARY_INVALID")
        _optional_private_text(self.notes, maximum=131_072, code="ECO_CRM_NOTES_INVALID")
        if self.task_ref is not None:
            _validate_ref(self.task_ref, "task_ref")
        if self.event_ref is not None:
            _validate_ref(self.event_ref, "event_ref")
        if self.kind == CrmActivityKind.task_link and self.task_ref is None:
            raise ValueError("ECO_CRM_TASK_LINK_REF_REQUIRED")
        if self.kind == CrmActivityKind.event_link and self.event_ref is None:
            raise ValueError("ECO_CRM_EVENT_LINK_REF_REQUIRED")
        return self


class PrivateCrmFollowUp(_PrivateCrmModel):
    follow_up_ref: str
    crm_workspace_ref: str
    context_ref: str
    title: str = Field(..., repr=False)
    due_at: datetime | None = None
    state: CrmFollowUpState = CrmFollowUpState.open
    task_ref: str | None = None
    completed_at: datetime | None = None
    archived: bool = False

    @model_validator(mode="after")
    def validate_follow_up(self) -> "PrivateCrmFollowUp":
        for field_name in ("follow_up_ref", "crm_workspace_ref", "context_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        _private_text(self.title, maximum=8_192, code="ECO_CRM_FOLLOW_UP_TITLE_INVALID")
        if self.due_at is not None:
            _aware(self.due_at, "ECO_CRM_FOLLOW_UP_DUE_INVALID")
        if self.completed_at is not None:
            _aware(self.completed_at, "ECO_CRM_FOLLOW_UP_COMPLETED_INVALID")
        if self.task_ref is not None:
            _validate_ref(self.task_ref, "task_ref")
        if (self.state == CrmFollowUpState.completed) != (self.completed_at is not None):
            raise ValueError("ECO_CRM_FOLLOW_UP_COMPLETION_STATE_INVALID")
        return self


class PrivateCrmPipeline(_PrivateCrmModel):
    pipeline_ref: str
    crm_workspace_ref: str
    board_ref: str
    name: str = Field(..., repr=False)
    object_kind: str = Field(..., repr=False)
    archived: bool = False

    @model_validator(mode="after")
    def validate_record(self) -> "PrivateCrmPipeline":
        for field_name in ("pipeline_ref", "crm_workspace_ref", "board_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        _private_text(self.name, maximum=512, code="ECO_CRM_PIPELINE_NAME_INVALID")
        _private_text(self.object_kind, maximum=512, code="ECO_CRM_PIPELINE_KIND_INVALID")
        return self


class PrivateCrmPipelineObject(_PrivateCrmModel):
    pipeline_object_ref: str
    pipeline_ref: str
    context_ref: str
    board_ref: str
    card_ref: str
    amount_minor: int | None = Field(default=None, ge=0)
    currency_ref: str | None = None
    target_date: date | None = None
    notes: str | None = Field(default=None, repr=False)
    archived: bool = False

    @model_validator(mode="after")
    def validate_pipeline_object(self) -> "PrivateCrmPipelineObject":
        for field_name in (
            "pipeline_object_ref",
            "pipeline_ref",
            "context_ref",
            "board_ref",
            "card_ref",
        ):
            _validate_ref(getattr(self, field_name), field_name)
        if self.currency_ref is not None:
            _validate_ref(self.currency_ref, "currency_ref")
        _optional_private_text(self.notes, maximum=65_536, code="ECO_CRM_NOTES_INVALID")
        return self


class PrivateCrmPortfolioSnapshot(_PrivateCrmModel):
    name: str = Field(..., repr=False)
    crm_workspaces: tuple[PrivateCrmWorkspace, ...] = ()
    people: tuple[PrivateCrmPerson, ...] = ()
    organizations: tuple[PrivateCrmOrganization, ...] = ()
    contexts: tuple[PrivateCrmWorkspaceContext, ...] = ()
    relationships: tuple[PrivateCrmRelationship, ...] = ()
    activities: tuple[PrivateCrmActivity, ...] = ()
    follow_ups: tuple[PrivateCrmFollowUp, ...] = ()
    pipelines: tuple[PrivateCrmPipeline, ...] = ()
    pipeline_objects: tuple[PrivateCrmPipelineObject, ...] = ()
    archived: bool = False


class PrivateCrmPortfolio(_PrivateCrmModel):
    schema_version: Literal["uaa-eco-005-crm-private-portfolio.v1"] = ECO_CRM_SCHEMA_VERSION
    workspace_ref: str
    portfolio_ref: str
    name: str = Field(..., repr=False)
    crm_workspaces: tuple[PrivateCrmWorkspace, ...] = Field(default=(), max_length=256)
    people: tuple[PrivateCrmPerson, ...] = Field(default=(), max_length=100_000)
    organizations: tuple[PrivateCrmOrganization, ...] = Field(default=(), max_length=50_000)
    contexts: tuple[PrivateCrmWorkspaceContext, ...] = Field(default=(), max_length=250_000)
    relationships: tuple[PrivateCrmRelationship, ...] = Field(default=(), max_length=250_000)
    activities: tuple[PrivateCrmActivity, ...] = Field(default=(), max_length=500_000)
    follow_ups: tuple[PrivateCrmFollowUp, ...] = Field(default=(), max_length=250_000)
    pipelines: tuple[PrivateCrmPipeline, ...] = Field(default=(), max_length=1_000)
    pipeline_objects: tuple[PrivateCrmPipelineObject, ...] = Field(default=(), max_length=250_000)
    archived: bool = False
    version: int = Field(default=1, ge=1)
    undo_stack: tuple[PrivateCrmPortfolioSnapshot, ...] = Field(
        default=(), max_length=_MAX_UNDO_DEPTH, repr=False
    )

    @model_validator(mode="after")
    def validate_portfolio(self) -> "PrivateCrmPortfolio":
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_ref(self.portfolio_ref, "portfolio_ref")
        _private_text(self.name, maximum=512, code="ECO_CRM_PORTFOLIO_NAME_INVALID")
        groups = (
            (self.crm_workspaces, "crm_workspace_ref"),
            (self.people, "person_ref"),
            (self.organizations, "organization_ref"),
            (self.contexts, "context_ref"),
            (self.relationships, "relationship_ref"),
            (self.activities, "activity_ref"),
            (self.follow_ups, "follow_up_ref"),
            (self.pipelines, "pipeline_ref"),
            (self.pipeline_objects, "pipeline_object_ref"),
        )
        for items, field_name in groups:
            _validate_refs(tuple(getattr(item, field_name) for item in items), field_name)
        workspace_by_ref = {item.crm_workspace_ref: item for item in self.crm_workspaces}
        people = {item.person_ref: item for item in self.people}
        organizations = {item.organization_ref: item for item in self.organizations}
        context_by_ref = {item.context_ref: item for item in self.contexts}
        pipeline_by_ref = {item.pipeline_ref: item for item in self.pipelines}
        for context in self.contexts:
            if context.crm_workspace_ref not in workspace_by_ref:
                raise ValueError("ECO_CRM_CONTEXT_WORKSPACE_NOT_FOUND")
            if context.person_ref is not None and context.person_ref not in people:
                raise ValueError("ECO_CRM_CONTEXT_PERSON_NOT_FOUND")
            if context.organization_ref is not None and context.organization_ref not in organizations:
                raise ValueError("ECO_CRM_CONTEXT_ORGANIZATION_NOT_FOUND")
            if not context.archived and workspace_by_ref[context.crm_workspace_ref].archived:
                raise ValueError("ECO_CRM_ACTIVE_CONTEXT_IN_ARCHIVED_WORKSPACE")
            subject = (
                people.get(context.person_ref)
                if context.person_ref is not None
                else organizations.get(context.organization_ref)
            )
            if not context.archived and subject is not None and subject.archived:
                raise ValueError("ECO_CRM_ACTIVE_CONTEXT_SUBJECT_ARCHIVED")
        for relationship in self.relationships:
            endpoints = (context_by_ref.get(relationship.from_context_ref), context_by_ref.get(relationship.to_context_ref))
            if None in endpoints:
                raise ValueError("ECO_CRM_RELATIONSHIP_CONTEXT_NOT_FOUND")
            if any(item.crm_workspace_ref != relationship.crm_workspace_ref for item in endpoints if item is not None):
                raise ValueError("ECO_CRM_RELATIONSHIP_WORKSPACE_MISMATCH")
            if not relationship.archived and any(item.archived for item in endpoints if item is not None):
                raise ValueError("ECO_CRM_ACTIVE_RELATIONSHIP_CONTEXT_ARCHIVED")
        for item in (*self.activities, *self.follow_ups):
            refs = item.context_refs if isinstance(item, PrivateCrmActivity) else (item.context_ref,)
            contexts = [context_by_ref.get(ref) for ref in refs]
            if any(context is None for context in contexts):
                raise ValueError("ECO_CRM_WORK_ITEM_CONTEXT_NOT_FOUND")
            if any(context.crm_workspace_ref != item.crm_workspace_ref for context in contexts if context is not None):
                raise ValueError("ECO_CRM_WORK_ITEM_WORKSPACE_MISMATCH")
            if not item.archived and any(context.archived for context in contexts if context is not None):
                raise ValueError("ECO_CRM_ACTIVE_WORK_ITEM_CONTEXT_ARCHIVED")
        for pipeline in self.pipelines:
            if pipeline.crm_workspace_ref not in workspace_by_ref:
                raise ValueError("ECO_CRM_PIPELINE_WORKSPACE_NOT_FOUND")
            if not pipeline.archived and workspace_by_ref[pipeline.crm_workspace_ref].archived:
                raise ValueError("ECO_CRM_ACTIVE_PIPELINE_IN_ARCHIVED_WORKSPACE")
        for item in self.pipeline_objects:
            pipeline = pipeline_by_ref.get(item.pipeline_ref)
            context = context_by_ref.get(item.context_ref)
            if pipeline is None or context is None:
                raise ValueError("ECO_CRM_PIPELINE_OBJECT_PARENT_NOT_FOUND")
            if item.board_ref != pipeline.board_ref:
                raise ValueError("ECO_CRM_PIPELINE_OBJECT_BOARD_MISMATCH")
            if context.crm_workspace_ref != pipeline.crm_workspace_ref:
                raise ValueError("ECO_CRM_PIPELINE_OBJECT_WORKSPACE_MISMATCH")
            if not item.archived and (pipeline.archived or context.archived):
                raise ValueError("ECO_CRM_ACTIVE_PIPELINE_OBJECT_PARENT_ARCHIVED")
        return self

    @property
    def safe_summary_ref(self) -> str:
        return _stable_ref(
            "crm-private-portfolio-summary-ref",
            {
                "portfolio_ref": self.portfolio_ref,
                "version": self.version,
                "workspace_count": len(self.crm_workspaces),
                "person_count": len(self.people),
                "organization_count": len(self.organizations),
                "context_count": len(self.contexts),
                "relationship_count": len(self.relationships),
                "activity_count": len(self.activities),
                "follow_up_count": len(self.follow_ups),
                "pipeline_count": len(self.pipelines),
                "pipeline_object_count": len(self.pipeline_objects),
                "archived": self.archived,
            },
        )

    def snapshot(self) -> PrivateCrmPortfolioSnapshot:
        return PrivateCrmPortfolioSnapshot(
            **{
                field: getattr(self, field)
                for field in PrivateCrmPortfolioSnapshot.model_fields
            }
        )


class PrivateCrmWorkspaceReadModel(_PrivateCrmModel):
    crm_workspace: PrivateCrmWorkspace
    contexts: tuple[PrivateCrmWorkspaceContext, ...]
    relationships: tuple[PrivateCrmRelationship, ...]
    activities: tuple[PrivateCrmActivity, ...]
    follow_ups: tuple[PrivateCrmFollowUp, ...]
    pipelines: tuple[PrivateCrmPipeline, ...]
    pipeline_objects: tuple["PrivateCrmPipelineObjectProjection", ...]
    result_ref: str


class PrivateCrmPipelineObjectProjection(_PrivateCrmModel):
    pipeline_object: PrivateCrmPipelineObject = Field(..., repr=False)
    lane_ref: str
    position: int
    board_version: int
    canonical_owner_ref: Literal["canonical-owner-ref:boards"] = (
        "canonical-owner-ref:boards"
    )


class PrivateCrmRepository:
    """Exact governed repository for a private CRM portfolio aggregate."""

    def __init__(
        self,
        platform: EcosystemLocalDataPlatform,
        *,
        board_repository: BoardRepository,
    ) -> None:
        if board_repository.platform is not platform:
            raise ValueError("ECO_CRM_BOARD_REPOSITORY_PLATFORM_MISMATCH")
        self.platform = platform
        self.board_repository = board_repository

    @staticmethod
    def mutation_resource_refs(
        *, workspace_ref: str, idempotency_ref: str, operation_ref: str, record_ref: str
    ) -> tuple[str, ...]:
        return tuple(dict.fromkeys((workspace_ref, idempotency_ref, operation_ref, record_ref)))

    def create_portfolio(
        self,
        *,
        portfolio: PrivateCrmPortfolio,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        if portfolio.version != 1 or portfolio.undo_stack:
            raise PrivateCrmConflict("ECO_CRM_CREATE_VERSION_INVALID")
        context = self._request_context_ref(
            "create_portfolio",
            {"portfolio": portfolio.model_dump(mode="json"), "operation_ref": operation_ref},
        )
        replay = self._replay(
            workspace_ref=portfolio.workspace_ref,
            record_ref=portfolio.portfolio_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        self._ensure_missing(portfolio.workspace_ref, portfolio.portfolio_ref)
        self._validate_board_bindings(portfolio)
        return self._apply(
            workspace_ref=portfolio.workspace_ref,
            record=portfolio,
            expected_version=0,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    def read(self, *, workspace_ref: str, portfolio_ref: str) -> PrivateCrmPortfolio:
        record = self.platform.read(workspace_ref=workspace_ref, record_ref=portfolio_ref)
        try:
            portfolio = PrivateCrmPortfolio.model_validate(record.private_payload)
        except Exception as exc:
            raise PrivateCrmError("ECO_CRM_PRIVATE_PAYLOAD_INVALID") from exc
        if (
            record.module_ref != ECO_CRM_MODULE_REF
            or record.record_kind_ref != ECO_CRM_RECORD_KIND_REF
            or portfolio.workspace_ref != workspace_ref
            or portfolio.portfolio_ref != portfolio_ref
            or portfolio.version != record.version
            or portfolio.safe_summary_ref != record.safe_summary_ref
        ):
            raise PrivateCrmError("ECO_CRM_RECORD_BINDING_INVALID")
        return portfolio

    def list_portfolios(self, *, workspace_ref: str, include_archived: bool = False) -> tuple[PrivateCrmPortfolio, ...]:
        items = tuple(
            self.read(workspace_ref=workspace_ref, portfolio_ref=record_ref)
            for record_ref in self.platform.search(
                workspace_ref=workspace_ref, term=_ALL_CRM_PORTFOLIOS_SEARCH_TERM
            )
        )
        return tuple(sorted((item for item in items if include_archived or not item.archived), key=lambda item: item.portfolio_ref))

    def workspace_read_model(
        self, *, workspace_ref: str, portfolio_ref: str, crm_workspace_ref: str
    ) -> PrivateCrmWorkspaceReadModel:
        portfolio = self.read(workspace_ref=workspace_ref, portfolio_ref=portfolio_ref)
        crm_workspace = next((item for item in portfolio.crm_workspaces if item.crm_workspace_ref == crm_workspace_ref and not item.archived), None)
        if crm_workspace is None:
            raise PrivateCrmConflict("ECO_CRM_WORKSPACE_NOT_FOUND")
        contexts = tuple(item for item in portfolio.contexts if item.crm_workspace_ref == crm_workspace_ref and not item.archived)
        context_refs = {item.context_ref for item in contexts}
        pipelines = tuple(item for item in portfolio.pipelines if item.crm_workspace_ref == crm_workspace_ref and not item.archived)
        pipeline_refs = {item.pipeline_ref for item in pipelines}
        board_by_pipeline = {
            pipeline.pipeline_ref: self.board_repository.read(
                workspace_ref=workspace_ref, board_ref=pipeline.board_ref
            )
            for pipeline in pipelines
        }
        projections: list[PrivateCrmPipelineObjectProjection] = []
        for item in portfolio.pipeline_objects:
            if item.pipeline_ref not in pipeline_refs or item.context_ref not in context_refs or item.archived:
                continue
            board = board_by_pipeline[item.pipeline_ref]
            card = next(
                (
                    card
                    for card in board.cards
                    if card.card_ref == item.card_ref and not card.archived
                ),
                None,
            )
            if card is None:
                raise PrivateCrmConflict("ECO_CRM_PIPELINE_OBJECT_CARD_NOT_FOUND")
            projections.append(
                PrivateCrmPipelineObjectProjection(
                    pipeline_object=item,
                    lane_ref=card.lane_ref,
                    position=card.position,
                    board_version=board.version,
                )
            )
        return PrivateCrmWorkspaceReadModel(
            crm_workspace=crm_workspace,
            contexts=contexts,
            relationships=tuple(item for item in portfolio.relationships if item.crm_workspace_ref == crm_workspace_ref and not item.archived),
            activities=tuple(item for item in portfolio.activities if item.crm_workspace_ref == crm_workspace_ref and not item.archived),
            follow_ups=tuple(item for item in portfolio.follow_ups if item.crm_workspace_ref == crm_workspace_ref and not item.archived),
            pipelines=pipelines,
            pipeline_objects=tuple(projections),
            result_ref=_stable_ref(
                "crm-workspace-result-ref",
                {
                    "portfolio_ref": portfolio_ref,
                    "portfolio_version": portfolio.version,
                    "crm_workspace_ref": crm_workspace_ref,
                    "board_versions": sorted(
                        (board.board_ref, board.version)
                        for board in board_by_pipeline.values()
                    ),
                },
            ),
        )

    def add_workspace(self, *, item: PrivateCrmWorkspace, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._append(collection="crm_workspaces", identity_field="crm_workspace_ref", item=item, **kwargs)

    def add_person(self, *, item: PrivateCrmPerson, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._append(collection="people", identity_field="person_ref", item=item, **kwargs)

    def add_organization(self, *, item: PrivateCrmOrganization, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._append(collection="organizations", identity_field="organization_ref", item=item, **kwargs)

    def add_context(self, *, item: PrivateCrmWorkspaceContext, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._append(collection="contexts", identity_field="context_ref", item=item, **kwargs)

    def add_relationship(self, *, item: PrivateCrmRelationship, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._append(collection="relationships", identity_field="relationship_ref", item=item, **kwargs)

    def add_activity(self, *, item: PrivateCrmActivity, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._append(collection="activities", identity_field="activity_ref", item=item, **kwargs)

    def add_follow_up(self, *, item: PrivateCrmFollowUp, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._append(collection="follow_ups", identity_field="follow_up_ref", item=item, **kwargs)

    def add_pipeline_record(
        self, *, item: PrivateCrmPipeline, **kwargs: Any
    ) -> UnitOfWorkReceipt:
        return self._append(collection="pipelines", identity_field="pipeline_ref", item=item, **kwargs)

    def add_pipeline_object(self, *, item: PrivateCrmPipelineObject, **kwargs: Any) -> UnitOfWorkReceipt:
        return self._append(collection="pipeline_objects", identity_field="pipeline_object_ref", item=item, **kwargs)

    def complete_follow_up(
        self,
        *,
        follow_up_ref: str,
        completed_at: datetime,
        **kwargs: Any,
    ) -> UnitOfWorkReceipt:
        _aware(completed_at, "ECO_CRM_FOLLOW_UP_COMPLETED_INVALID")
        return self._replace_item(
            collection="follow_ups",
            identity_field="follow_up_ref",
            identity_ref=follow_up_ref,
            mutation_kind="complete_follow_up",
            update=lambda item: item.model_copy(update={"state": CrmFollowUpState.completed, "completed_at": completed_at}),
            **kwargs,
        )

    def reschedule_follow_up(
        self,
        *,
        follow_up_ref: str,
        due_at: datetime | None,
        **kwargs: Any,
    ) -> UnitOfWorkReceipt:
        if due_at is not None:
            _aware(due_at, "ECO_CRM_FOLLOW_UP_DUE_INVALID")
        return self._replace_item(
            collection="follow_ups",
            identity_field="follow_up_ref",
            identity_ref=follow_up_ref,
            mutation_kind="reschedule_follow_up",
            update=lambda item: item.model_copy(update={"due_at": due_at}),
            **kwargs,
        )

    def undo(
        self,
        *,
        workspace_ref: str,
        portfolio_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        def transform(portfolio: PrivateCrmPortfolio) -> PrivateCrmPortfolioSnapshot:
            if not portfolio.undo_stack:
                raise PrivateCrmConflict("ECO_CRM_UNDO_EMPTY")
            return portfolio.undo_stack[-1]

        return self._mutate(
            workspace_ref=workspace_ref,
            portfolio_ref=portfolio_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind="undo",
            mutation_material={},
            transform=transform,
            drop_last_undo=True,
        )

    def _append(
        self,
        *,
        collection: str,
        identity_field: str,
        item: _PrivateCrmModel,
        workspace_ref: str,
        portfolio_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        identity_ref = getattr(item, identity_field)

        def transform(portfolio: PrivateCrmPortfolio) -> PrivateCrmPortfolioSnapshot:
            current_items = getattr(portfolio, collection)
            if any(getattr(current, identity_field) == identity_ref for current in current_items):
                raise PrivateCrmConflict("ECO_CRM_ITEM_ALREADY_EXISTS")
            return self._snapshot(portfolio, **{collection: (*current_items, item)})

        return self._mutate(
            workspace_ref=workspace_ref,
            portfolio_ref=portfolio_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind=f"add_{collection}",
            mutation_material={"identity_ref": identity_ref, "item": item.model_dump(mode="json")},
            transform=transform,
        )

    def _replace_item(
        self,
        *,
        collection: str,
        identity_field: str,
        identity_ref: str,
        mutation_kind: str,
        update: Callable[[Any], Any],
        workspace_ref: str,
        portfolio_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
    ) -> UnitOfWorkReceipt:
        _validate_ref(identity_ref, identity_field)

        def transform(portfolio: PrivateCrmPortfolio) -> PrivateCrmPortfolioSnapshot:
            items = list(getattr(portfolio, collection))
            index = next((index for index, item in enumerate(items) if getattr(item, identity_field) == identity_ref), None)
            if index is None:
                raise PrivateCrmConflict("ECO_CRM_ITEM_NOT_FOUND")
            items[index] = update(items[index])
            return self._snapshot(portfolio, **{collection: tuple(items)})

        return self._mutate(
            workspace_ref=workspace_ref,
            portfolio_ref=portfolio_ref,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            mutation_kind=mutation_kind,
            mutation_material={"identity_ref": identity_ref},
            transform=transform,
        )

    def _mutate(
        self,
        *,
        workspace_ref: str,
        portfolio_ref: str,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        mutation_kind: str,
        mutation_material: dict[str, Any],
        transform: Callable[[PrivateCrmPortfolio], PrivateCrmPortfolioSnapshot],
        drop_last_undo: bool = False,
    ) -> UnitOfWorkReceipt:
        context = self._request_context_ref(
            mutation_kind,
            {"workspace_ref": workspace_ref, "portfolio_ref": portfolio_ref, "expected_version": expected_version, "operation_ref": operation_ref, "mutation": mutation_material},
        )
        replay = self._replay(
            workspace_ref=workspace_ref,
            record_ref=portfolio_ref,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )
        if replay is not None:
            return replay
        current = self.read(workspace_ref=workspace_ref, portfolio_ref=portfolio_ref)
        if current.version != expected_version:
            raise PrivateCrmConflict("ECO_CRM_STALE_VERSION")
        snapshot = transform(current)
        updated = self._with_bounded_undo(current=current, snapshot=snapshot, drop_last_undo=drop_last_undo)
        self._validate_board_bindings(updated)
        return self._apply(
            workspace_ref=workspace_ref,
            record=updated,
            expected_version=expected_version,
            operation_ref=operation_ref,
            idempotency_ref=idempotency_ref,
            approval=approval,
            request_context_ref=context,
        )

    @staticmethod
    def _snapshot(portfolio: PrivateCrmPortfolio, **updates: Any) -> PrivateCrmPortfolioSnapshot:
        material = portfolio.snapshot().model_dump(mode="json")
        material.update(updates)
        try:
            return PrivateCrmPortfolioSnapshot.model_validate(material)
        except ValueError as exc:
            raise PrivateCrmConflict(_validation_code(exc)) from exc

    @staticmethod
    def _build(
        *, current: PrivateCrmPortfolio, version: int, undo_stack: tuple[PrivateCrmPortfolioSnapshot, ...], snapshot: PrivateCrmPortfolioSnapshot
    ) -> PrivateCrmPortfolio:
        try:
            return PrivateCrmPortfolio(
                workspace_ref=current.workspace_ref,
                portfolio_ref=current.portfolio_ref,
                version=version,
                undo_stack=undo_stack,
                **snapshot.model_dump(mode="json"),
            )
        except ValueError as exc:
            raise PrivateCrmConflict(_validation_code(exc)) from exc

    def _with_bounded_undo(
        self, *, current: PrivateCrmPortfolio, snapshot: PrivateCrmPortfolioSnapshot, drop_last_undo: bool
    ) -> PrivateCrmPortfolio:
        history = list(current.undo_stack[:-1] if drop_last_undo else (*current.undo_stack, current.snapshot()))
        history = history[-_MAX_UNDO_DEPTH:]
        while True:
            updated = self._build(current=current, version=current.version + 1, undo_stack=tuple(history), snapshot=snapshot)
            size = len(json.dumps({"private_payload": updated.model_dump(mode="json"), "search_terms": [_ALL_CRM_PORTFOLIOS_SEARCH_TERM]}, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"))
            if size <= ECO_LOCAL_DATA_MAX_PRIVATE_PAYLOAD_BYTES:
                return updated
            if not history:
                raise PrivateCrmConflict("ECO_CRM_PRIVATE_PAYLOAD_LIMIT_EXCEEDED")
            history.pop(0)

    def _validate_board_bindings(self, portfolio: PrivateCrmPortfolio) -> None:
        active_pipelines = {item.pipeline_ref: item for item in portfolio.pipelines if not item.archived}
        boards: dict[str, Any] = {}
        for pipeline in active_pipelines.values():
            try:
                board = self.board_repository.read(workspace_ref=portfolio.workspace_ref, board_ref=pipeline.board_ref)
            except EcosystemLocalDataError as exc:
                if str(exc) == "ECO_RECORD_NOT_FOUND":
                    raise PrivateCrmConflict("ECO_CRM_PIPELINE_BOARD_NOT_FOUND") from exc
                raise
            if board.archived:
                raise PrivateCrmConflict("ECO_CRM_PIPELINE_BOARD_ARCHIVED")
            boards[pipeline.board_ref] = board
        for item in portfolio.pipeline_objects:
            if item.archived:
                continue
            pipeline = active_pipelines.get(item.pipeline_ref)
            if pipeline is None:
                raise PrivateCrmConflict("ECO_CRM_ACTIVE_PIPELINE_OBJECT_PARENT_ARCHIVED")
            board = boards[pipeline.board_ref]
            card = next((card for card in board.cards if card.card_ref == item.card_ref and not card.archived), None)
            if card is None:
                raise PrivateCrmConflict("ECO_CRM_PIPELINE_OBJECT_CARD_NOT_FOUND")
            if card.subject_kind != BoardSubjectKind.board_item or card.subject_ref != item.pipeline_object_ref:
                raise PrivateCrmConflict("ECO_CRM_PIPELINE_OBJECT_CARD_BINDING_INVALID")

    def _ensure_missing(self, workspace_ref: str, record_ref: str) -> None:
        try:
            self.platform.read(workspace_ref=workspace_ref, record_ref=record_ref)
        except EcosystemLocalDataError as exc:
            if str(exc) == "ECO_RECORD_NOT_FOUND":
                return
            raise
        raise PrivateCrmConflict("ECO_CRM_RECORD_ALREADY_EXISTS")

    def _apply(
        self,
        *,
        workspace_ref: str,
        record: PrivateCrmPortfolio,
        expected_version: int,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt:
        try:
            return self.platform._apply_registered_domain(
                workspace_ref=workspace_ref,
                idempotency_ref=idempotency_ref,
                operations=(PutRecord(
                    operation_ref=operation_ref,
                    module_ref=ECO_CRM_MODULE_REF,
                    record_ref=record.portfolio_ref,
                    record_kind_ref=ECO_CRM_RECORD_KIND_REF,
                    safe_summary_ref=record.safe_summary_ref,
                    private_payload=record.model_dump(mode="json"),
                    search_terms=(_ALL_CRM_PORTFOLIOS_SEARCH_TERM,),
                    expected_version=expected_version,
                    retention_ref=ECO_CRM_RETENTION_REF,
                ),),
                approval=approval,
                requested_action=ECO_CRM_MUTATION_ACTION,
                request_context_ref=request_context_ref,
            )
        except EcosystemConflict as exc:
            if str(exc) == "ECO_STALE_RECORD_VERSION":
                raise PrivateCrmConflict("ECO_CRM_STALE_VERSION") from exc
            raise
        except ValueError as exc:
            if str(exc) == "ECO_PRIVATE_PAYLOAD_LIMIT_EXCEEDED":
                raise PrivateCrmConflict("ECO_CRM_PRIVATE_PAYLOAD_LIMIT_EXCEEDED") from exc
            raise

    def _replay(
        self,
        *,
        workspace_ref: str,
        record_ref: str,
        operation_ref: str,
        idempotency_ref: str,
        approval: ApprovalValidationRequest,
        request_context_ref: str,
    ) -> UnitOfWorkReceipt | None:
        return self.platform.replay_receipt(
            workspace_ref=workspace_ref,
            idempotency_ref=idempotency_ref,
            resource_refs=self.mutation_resource_refs(workspace_ref=workspace_ref, idempotency_ref=idempotency_ref, operation_ref=operation_ref, record_ref=record_ref),
            approval=approval,
            requested_action=ECO_CRM_MUTATION_ACTION,
            request_context_ref=request_context_ref,
        )

    @staticmethod
    def _request_context_ref(kind: str, material: dict[str, Any]) -> str:
        return _stable_ref("crm-private-request-context-ref", {"kind": kind, "material": material})


__all__ = [
    "ECO_CRM_MUTATION_ACTION",
    "ECO_CRM_SCHEMA_VERSION",
    "CrmActivityKind",
    "CrmContactPointKind",
    "CrmFollowUpState",
    "CrmPrivacyPolicy",
    "CrmWorkspacePreset",
    "PrivateCrmActivity",
    "PrivateCrmConflict",
    "PrivateCrmContactPoint",
    "PrivateCrmError",
    "PrivateCrmFollowUp",
    "PrivateCrmOrganization",
    "PrivateCrmPerson",
    "PrivateCrmPipeline",
    "PrivateCrmPipelineObject",
    "PrivateCrmPipelineObjectProjection",
    "PrivateCrmPortfolio",
    "PrivateCrmPortfolioSnapshot",
    "PrivateCrmRelationship",
    "PrivateCrmRepository",
    "PrivateCrmWorkspace",
    "PrivateCrmWorkspaceContext",
    "PrivateCrmWorkspaceReadModel",
]
