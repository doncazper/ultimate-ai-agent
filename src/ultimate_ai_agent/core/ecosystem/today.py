"""Deterministic projection-only Today and Morning Briefing core for ECO-006.

This module composes accepted canonical read models. It owns no domain records,
performs no source refresh, and grants no mutation, ranking, connector, model,
browser, background, or notification authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ultimate_ai_agent.core.crm.private_repository import (
    CrmFollowUpState,
    PrivateCrmWorkspaceReadModel,
)
from ultimate_ai_agent.core.ecosystem.calendar import CalendarViewResult
from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId
from ultimate_ai_agent.core.ecosystem.tasks import (
    TaskListResult,
    TaskPriority,
    TaskStatus,
    TaskView,
)
from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret


ECO_TODAY_SCHEMA_VERSION = "uaa-eco-006-today-briefing.v1"
ECO_TODAY_ORDERING_CONTRACT_REF = "contract-ref:eco-006-visible-ordering:v1"
_SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/-]{2,190}$")


class TodayProjectionError(RuntimeError):
    """Fail-closed projection error with a stable, non-sensitive code."""


class TodayItemKind(str, Enum):
    event = "event"
    task = "task"
    plan_milestone = "plan_milestone"
    crm_follow_up = "crm_follow_up"
    source_proposal = "source_proposal"
    blocker = "blocker"
    recent_receipt = "recent_receipt"


class TodayLane(str, Enum):
    attention = "attention"
    agenda = "agenda"
    focus = "focus"
    follow_up = "follow_up"
    recent_proof = "recent_proof"


class TodayFreshness(str, Enum):
    current = "current"
    stale = "stale"
    missing = "missing"
    blocked = "blocked"


class TodayEvidenceState(str, Enum):
    present = "present"
    missing = "missing"
    not_applicable = "not_applicable"


class TodayProposalKind(str, Enum):
    carry_forward = "carry_forward"


class TodaySurface(str, Enum):
    today = "today"
    briefing = "briefing"


class _TodayModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        use_enum_values=False,
    )


def _validate_ref(value: str, field_name: str) -> str:
    if not _SAFE_REF_RE.fullmatch(value) or contains_obvious_secret(value):
        raise ValueError(f"ECO_TODAY_{field_name.upper()}_SAFE_REF_REQUIRED")
    return value


def _validate_refs(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(values) != len(set(values)):
        raise ValueError(f"ECO_TODAY_{field_name.upper()}_DUPLICATE_REF")
    for value in values:
        _validate_ref(value, field_name)
    return values


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


def _timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _aware(parsed, "ECO_TODAY_SOURCE_TIMESTAMP_INVALID")


class TodayProjectionRequest(_TodayModel):
    workspace_ref: str
    as_of: datetime
    timezone_name: str = "UTC"

    @model_validator(mode="after")
    def validate_request(self) -> "TodayProjectionRequest":
        _validate_ref(self.workspace_ref, "workspace_ref")
        _aware(self.as_of, "ECO_TODAY_AS_OF_TIMEZONE_REQUIRED")
        try:
            ZoneInfo(self.timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("ECO_TODAY_TIMEZONE_INVALID") from exc
        return self


class TaskTodaySource(_TodayModel):
    result: TaskListResult = Field(..., repr=False)

    @property
    def workspace_ref(self) -> str:
        return self.result.query.workspace_ref


class CalendarTodaySource(_TodayModel):
    workspace_ref: str
    result: CalendarViewResult = Field(..., repr=False)

    @field_validator("workspace_ref")
    @classmethod
    def validate_workspace_ref(cls, value: str) -> str:
        return _validate_ref(value, "workspace_ref")


class CrmTodaySource(_TodayModel):
    workspace_ref: str
    result: PrivateCrmWorkspaceReadModel = Field(..., repr=False)

    @field_validator("workspace_ref")
    @classmethod
    def validate_workspace_ref(cls, value: str) -> str:
        return _validate_ref(value, "workspace_ref")


class TodaySourceStatus(_TodayModel):
    owner_app: CanonicalOwnerId
    workspace_ref: str
    source_ref: str
    result_ref: str | None = None
    freshness: TodayFreshness
    why_status_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=32)
    surfaces: tuple[TodaySurface, ...] = (
        TodaySurface.today,
        TodaySurface.briefing,
    )

    @model_validator(mode="after")
    def validate_status(self) -> "TodaySourceStatus":
        _validate_ref(self.workspace_ref, "workspace_ref")
        _validate_ref(self.source_ref, "source_ref")
        if self.result_ref is not None:
            _validate_ref(self.result_ref, "result_ref")
        _validate_refs(self.why_status_refs, "why_status_ref")
        _validate_refs(self.evidence_refs, "evidence_ref")
        if len(self.surfaces) != len(set(self.surfaces)) or not self.surfaces:
            raise ValueError("ECO_TODAY_SOURCE_SURFACES_INVALID")
        if self.freshness == TodayFreshness.current and self.result_ref is None:
            raise ValueError("ECO_TODAY_CURRENT_SOURCE_RESULT_REQUIRED")
        return self

    @property
    def status_ref(self) -> str:
        return _stable_ref("today-source-status-ref", self.model_dump(mode="json"))


class TodaySupplementalCandidate(_TodayModel):
    owner_app: CanonicalOwnerId
    canonical_ref: str
    workspace_ref: str
    item_kind: Literal[
        TodayItemKind.plan_milestone,
        TodayItemKind.source_proposal,
        TodayItemKind.blocker,
        TodayItemKind.recent_receipt,
    ]
    source_result_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    why_shown_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=32)
    receipt_refs: tuple[str, ...] = Field(default=(), max_length=32)
    due_at: datetime | None = None
    scheduled_at: datetime | None = None
    freshness: TodayFreshness = TodayFreshness.current
    surfaces: tuple[TodaySurface, ...] = (
        TodaySurface.today,
        TodaySurface.briefing,
    )

    @model_validator(mode="after")
    def validate_candidate(self) -> "TodaySupplementalCandidate":
        for field_name in ("canonical_ref", "workspace_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        for field_name in (
            "source_result_refs",
            "why_shown_refs",
            "evidence_refs",
            "receipt_refs",
        ):
            _validate_refs(getattr(self, field_name), field_name)
        if self.due_at is not None:
            _aware(self.due_at, "ECO_TODAY_CANDIDATE_DUE_INVALID")
        if self.scheduled_at is not None:
            _aware(self.scheduled_at, "ECO_TODAY_CANDIDATE_SCHEDULE_INVALID")
        if len(self.surfaces) != len(set(self.surfaces)) or not self.surfaces:
            raise ValueError("ECO_TODAY_CANDIDATE_SURFACES_INVALID")
        expected_owner = {
            TodayItemKind.plan_milestone: CanonicalOwnerId.plans,
            TodayItemKind.source_proposal: CanonicalOwnerId.inbox,
            TodayItemKind.blocker: CanonicalOwnerId.governance,
            TodayItemKind.recent_receipt: CanonicalOwnerId.governance,
        }[self.item_kind]
        if self.owner_app != expected_owner:
            raise ValueError("ECO_TODAY_CANDIDATE_CANONICAL_OWNER_MISMATCH")
        return self


class TodayOrderingFactors(_TodayModel):
    lane_ordinal: int = Field(..., ge=0, le=4)
    urgency_ordinal: int = Field(..., ge=0, le=9)
    time_ordinal: datetime | None = None
    canonical_ref: str
    ordering_contract_ref: Literal["contract-ref:eco-006-visible-ordering:v1"] = (
        ECO_TODAY_ORDERING_CONTRACT_REF
    )

    @model_validator(mode="after")
    def validate_factors(self) -> "TodayOrderingFactors":
        _validate_ref(self.canonical_ref, "canonical_ref")
        if self.time_ordinal is not None:
            _aware(self.time_ordinal, "ECO_TODAY_ORDERING_TIME_INVALID")
        return self


class TodayProjectionItem(_TodayModel):
    owner_app: CanonicalOwnerId
    canonical_ref: str
    workspace_ref: str
    item_kind: TodayItemKind
    lane: TodayLane
    source_result_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    why_shown_refs: tuple[str, ...] = Field(..., min_length=1, max_length=16)
    evidence_refs: tuple[str, ...] = Field(default=(), max_length=32)
    receipt_refs: tuple[str, ...] = Field(default=(), max_length=32)
    evidence_state: TodayEvidenceState
    freshness: TodayFreshness
    due_at: datetime | None = None
    scheduled_at: datetime | None = None
    ordering_factors: TodayOrderingFactors
    ranking_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_item(self) -> "TodayProjectionItem":
        for field_name in ("canonical_ref", "workspace_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        for field_name in (
            "source_result_refs",
            "why_shown_refs",
            "evidence_refs",
            "receipt_refs",
        ):
            _validate_refs(getattr(self, field_name), field_name)
        if self.ordering_factors.canonical_ref != self.canonical_ref:
            raise ValueError("ECO_TODAY_ORDERING_CANONICAL_REF_MISMATCH")
        if self.evidence_state == TodayEvidenceState.present and not (
            self.evidence_refs or self.receipt_refs
        ):
            raise ValueError("ECO_TODAY_PRESENT_EVIDENCE_REF_REQUIRED")
        if self.evidence_state == TodayEvidenceState.missing and (
            self.evidence_refs or self.receipt_refs
        ):
            raise ValueError("ECO_TODAY_MISSING_EVIDENCE_REFS_CONFLICT")
        return self

    @property
    def item_ref(self) -> str:
        return _stable_ref("today-item-ref", self.model_dump(mode="json"))


class TodayCarryForwardProposal(_TodayModel):
    proposal_kind: Literal[TodayProposalKind.carry_forward] = (
        TodayProposalKind.carry_forward
    )
    owner_app: CanonicalOwnerId
    canonical_ref: str
    workspace_ref: str
    original_due_at: datetime
    proposed_local_date: date
    why_proposed_refs: tuple[str, ...] = ("why-proposed-ref:eco-006/overdue-open-item",)
    mutation_authorized: Literal[False] = False
    background_work_started: Literal[False] = False

    @model_validator(mode="after")
    def validate_proposal(self) -> "TodayCarryForwardProposal":
        for field_name in ("canonical_ref", "workspace_ref"):
            _validate_ref(getattr(self, field_name), field_name)
        _aware(self.original_due_at, "ECO_TODAY_CARRY_FORWARD_DUE_INVALID")
        _validate_refs(self.why_proposed_refs, "why_proposed_ref")
        return self

    @property
    def proposal_ref(self) -> str:
        return _stable_ref(
            "today-carry-forward-proposal-ref", self.model_dump(mode="json")
        )


class TodayProjection(_TodayModel):
    request: TodayProjectionRequest
    items: tuple[TodayProjectionItem, ...]
    source_statuses: tuple[TodaySourceStatus, ...]
    carry_forward_proposals: tuple[TodayCarryForwardProposal, ...]
    result_ref: str
    projection_only: Literal[True] = True
    ranking_performed: Literal[False] = False
    mutation_authorized: Literal[False] = False

    @field_validator("result_ref")
    @classmethod
    def validate_result_ref(cls, value: str) -> str:
        return _validate_ref(value, "result_ref")


class MorningBriefingProjection(_TodayModel):
    request: TodayProjectionRequest
    items: tuple[TodayProjectionItem, ...]
    source_statuses: tuple[TodaySourceStatus, ...]
    carry_forward_proposal_refs: tuple[str, ...]
    section_refs: tuple[str, ...]
    result_ref: str
    projection_only: Literal[True] = True
    source_refresh_performed: Literal[False] = False
    notification_sent: Literal[False] = False

    @model_validator(mode="after")
    def validate_briefing(self) -> "MorningBriefingProjection":
        _validate_refs(self.carry_forward_proposal_refs, "carry_forward_proposal_ref")
        _validate_refs(self.section_refs, "section_ref")
        _validate_ref(self.result_ref, "result_ref")
        return self


class TodayAndBriefingResult(_TodayModel):
    schema_version: Literal["uaa-eco-006-today-briefing.v1"] = ECO_TODAY_SCHEMA_VERSION
    today: TodayProjection
    morning_briefing: MorningBriefingProjection
    result_ref: str
    raw_content_included: Literal[False] = False
    external_read_performed: Literal[False] = False
    background_work_started: Literal[False] = False

    @field_validator("result_ref")
    @classmethod
    def validate_result_ref(cls, value: str) -> str:
        return _validate_ref(value, "result_ref")


def _lane_for_supplemental(kind: TodayItemKind) -> tuple[TodayLane, int, int]:
    return {
        TodayItemKind.blocker: (TodayLane.attention, 0, 0),
        TodayItemKind.plan_milestone: (TodayLane.focus, 2, 3),
        TodayItemKind.source_proposal: (TodayLane.follow_up, 3, 4),
        TodayItemKind.recent_receipt: (TodayLane.recent_proof, 4, 5),
    }[kind]


def _evidence_state(
    evidence_refs: tuple[str, ...], receipt_refs: tuple[str, ...] = ()
) -> TodayEvidenceState:
    return (
        TodayEvidenceState.present
        if evidence_refs or receipt_refs
        else TodayEvidenceState.missing
    )


def _ordering_key(item: TodayProjectionItem) -> tuple[Any, ...]:
    factors = item.ordering_factors
    time_value = factors.time_ordinal or datetime.max.replace(tzinfo=timezone.utc)
    return (
        factors.lane_ordinal,
        factors.urgency_ordinal,
        time_value.astimezone(timezone.utc),
        factors.canonical_ref,
    )


def _ensure_unique_items(
    items: tuple[TodayProjectionItem, ...], *, surface: str
) -> None:
    keys = tuple((item.owner_app, item.canonical_ref) for item in items)
    if len(keys) != len(set(keys)):
        raise TodayProjectionError(f"ECO_TODAY_DUPLICATE_{surface.upper()}_ITEM")


def _ensure_unique_statuses(
    statuses: tuple[TodaySourceStatus, ...], *, surface: str
) -> None:
    keys = tuple((item.owner_app, item.source_ref) for item in statuses)
    if len(keys) != len(set(keys)):
        raise TodayProjectionError(f"ECO_TODAY_DUPLICATE_{surface.upper()}_SOURCE")


def build_today_and_morning_briefing(
    *,
    request: TodayProjectionRequest,
    task_sources: tuple[TaskTodaySource, ...] = (),
    calendar_sources: tuple[CalendarTodaySource, ...] = (),
    crm_sources: tuple[CrmTodaySource, ...] = (),
    supplemental_candidates: tuple[TodaySupplementalCandidate, ...] = (),
    supplemental_source_statuses: tuple[TodaySourceStatus, ...] = (),
) -> TodayAndBriefingResult:
    """Compose canonical source results without owning or mutating their truth."""

    zone = ZoneInfo(request.timezone_name)
    local_day = request.as_of.astimezone(zone).date()
    local_start = datetime.combine(local_day, time.min, tzinfo=zone)
    local_end = local_start + timedelta(days=1)
    today_items: list[TodayProjectionItem] = []
    briefing_items: list[TodayProjectionItem] = []
    today_carry_forward: list[TodayCarryForwardProposal] = []
    briefing_carry_forward: list[TodayCarryForwardProposal] = []
    today_statuses: list[TodaySourceStatus] = []
    briefing_statuses: list[TodaySourceStatus] = []

    def add_item(item: TodayProjectionItem, surfaces: tuple[TodaySurface, ...]) -> None:
        if TodaySurface.today in surfaces:
            today_items.append(item)
        if TodaySurface.briefing in surfaces:
            briefing_items.append(item)

    def add_status(status: TodaySourceStatus) -> None:
        if status.workspace_ref != request.workspace_ref:
            raise TodayProjectionError("ECO_TODAY_SOURCE_STATUS_WORKSPACE_MISMATCH")
        if TodaySurface.today in status.surfaces:
            today_statuses.append(status)
        if TodaySurface.briefing in status.surfaces:
            briefing_statuses.append(status)

    for source in task_sources:
        if source.workspace_ref != request.workspace_ref:
            raise TodayProjectionError("ECO_TODAY_TASK_WORKSPACE_MISMATCH")
        task_as_of = _timestamp(source.result.query.as_of)
        assert task_as_of is not None
        task_freshness = (
            TodayFreshness.current
            if task_as_of >= request.as_of
            else TodayFreshness.stale
        )
        status = TodaySourceStatus(
            owner_app=CanonicalOwnerId.tasks,
            workspace_ref=request.workspace_ref,
            source_ref=_stable_ref(
                "today-source-ref",
                {"owner": "tasks", "result": source.result.result_ref},
            ),
            result_ref=source.result.result_ref,
            freshness=task_freshness,
            why_status_refs=(
                "why-source-status-ref:eco-006/canonical-task-result"
                if task_freshness == TodayFreshness.current
                else "why-source-status-ref:eco-006/task-result-stale",
            ),
        )
        add_status(status)
        for task in source.result.tasks:
            if task.archived or task.status == TaskStatus.completed:
                continue
            due_at = _timestamp(task.due_at)
            start_at = _timestamp(task.start_at)
            why: list[str] = []
            lane = TodayLane.focus
            lane_ordinal = 2
            urgency = 5
            if due_at is not None and due_at < request.as_of:
                lane = TodayLane.attention
                lane_ordinal = 0
                urgency = 0
                why.append("why-shown-ref:eco-006/task-overdue")
                if due_at.astimezone(zone).date() < local_day:
                    proposal = TodayCarryForwardProposal(
                        owner_app=CanonicalOwnerId.tasks,
                        canonical_ref=task.task_ref,
                        workspace_ref=request.workspace_ref,
                        original_due_at=due_at,
                        proposed_local_date=local_day,
                    )
                    today_carry_forward.append(proposal)
                    briefing_carry_forward.append(proposal)
            elif task.status == TaskStatus.waiting:
                lane = TodayLane.attention
                lane_ordinal = 0
                urgency = 1
                why.append("why-shown-ref:eco-006/task-waiting")
            elif start_at is not None and start_at.astimezone(zone).date() == local_day:
                lane = TodayLane.agenda
                lane_ordinal = 1
                urgency = 2
                why.append("why-shown-ref:eco-006/task-starts-today")
            elif due_at is not None and due_at.astimezone(zone).date() == local_day:
                urgency = 2
                why.append("why-shown-ref:eco-006/task-due-today")
            elif task.flagged or task.priority == TaskPriority.high:
                urgency = 3
                why.append("why-shown-ref:eco-006/task-explicit-priority")
            elif source.result.query.view in {
                TaskView.today,
                TaskView.overdue,
                TaskView.waiting,
                TaskView.flagged,
            }:
                why.append("why-shown-ref:eco-006/task-source-view")
            else:
                continue
            evidence_refs = tuple(task.evidence_refs)
            add_item(
                TodayProjectionItem(
                    owner_app=CanonicalOwnerId.tasks,
                    canonical_ref=task.task_ref,
                    workspace_ref=request.workspace_ref,
                    item_kind=TodayItemKind.task,
                    lane=lane,
                    source_result_refs=(source.result.result_ref,),
                    why_shown_refs=tuple(why),
                    evidence_refs=evidence_refs,
                    evidence_state=_evidence_state(evidence_refs),
                    freshness=task_freshness,
                    due_at=due_at,
                    scheduled_at=start_at,
                    ordering_factors=TodayOrderingFactors(
                        lane_ordinal=lane_ordinal,
                        urgency_ordinal=urgency,
                        time_ordinal=due_at or start_at,
                        canonical_ref=task.task_ref,
                    ),
                ),
                (TodaySurface.today, TodaySurface.briefing),
            )

    for source in calendar_sources:
        if source.workspace_ref != request.workspace_ref:
            raise TodayProjectionError("ECO_TODAY_CALENDAR_WORKSPACE_MISMATCH")
        calendar_freshness = (
            TodayFreshness.current
            if source.result.range_starts_at <= local_start
            and source.result.range_ends_at >= local_end
            else TodayFreshness.stale
        )
        status = TodaySourceStatus(
            owner_app=CanonicalOwnerId.calendar,
            workspace_ref=request.workspace_ref,
            source_ref=_stable_ref(
                "today-source-ref",
                {"owner": "calendar", "result": source.result.result_ref},
            ),
            result_ref=source.result.result_ref,
            freshness=calendar_freshness,
            why_status_refs=(
                "why-source-status-ref:eco-006/canonical-calendar-result"
                if calendar_freshness == TodayFreshness.current
                else "why-source-status-ref:eco-006/calendar-range-stale",
            ),
        )
        add_status(status)
        for projection in source.result.occurrence_items:
            occurrence = projection.occurrence
            if not (
                occurrence.starts_at < local_end and occurrence.ends_at > local_start
            ):
                continue
            evidence_refs = tuple(projection.field_provenance_refs)
            add_item(
                TodayProjectionItem(
                    owner_app=CanonicalOwnerId.calendar,
                    canonical_ref=occurrence.occurrence_ref,
                    workspace_ref=request.workspace_ref,
                    item_kind=TodayItemKind.event,
                    lane=TodayLane.agenda,
                    source_result_refs=(source.result.result_ref,),
                    why_shown_refs=("why-shown-ref:eco-006/calendar-occurs-today",),
                    evidence_refs=evidence_refs,
                    evidence_state=_evidence_state(evidence_refs),
                    freshness=calendar_freshness,
                    scheduled_at=occurrence.starts_at,
                    ordering_factors=TodayOrderingFactors(
                        lane_ordinal=1,
                        urgency_ordinal=1,
                        time_ordinal=occurrence.starts_at,
                        canonical_ref=occurrence.occurrence_ref,
                    ),
                ),
                (TodaySurface.today, TodaySurface.briefing),
            )

    for source in crm_sources:
        if source.workspace_ref != request.workspace_ref:
            raise TodayProjectionError("ECO_TODAY_CRM_WORKSPACE_MISMATCH")
        policy = source.result.crm_workspace.privacy_policy
        today_allowed = policy.included_in_today
        briefing_allowed = policy.included_in_briefing
        if not today_allowed and not briefing_allowed:
            continue
        surfaces = tuple(
            surface
            for surface, allowed in (
                (TodaySurface.today, today_allowed),
                (TodaySurface.briefing, briefing_allowed),
            )
            if allowed
        )
        status = TodaySourceStatus(
            owner_app=CanonicalOwnerId.crm,
            workspace_ref=request.workspace_ref,
            source_ref=_stable_ref(
                "today-source-ref", {"owner": "crm", "result": source.result.result_ref}
            ),
            result_ref=source.result.result_ref,
            freshness=TodayFreshness.current,
            why_status_refs=("why-source-status-ref:eco-006/private-crm-result",),
            surfaces=surfaces,
        )
        add_status(status)
        for follow_up in source.result.follow_ups:
            if follow_up.archived or follow_up.state != CrmFollowUpState.open:
                continue
            due_at = follow_up.due_at
            why = ["why-shown-ref:eco-006/crm-follow-up-open"]
            lane = TodayLane.follow_up
            lane_ordinal = 3
            urgency = 4
            if due_at is not None and due_at < request.as_of:
                lane = TodayLane.attention
                lane_ordinal = 0
                urgency = 0
                why.append("why-shown-ref:eco-006/crm-follow-up-overdue")
                if due_at.astimezone(zone).date() < local_day:
                    proposal = TodayCarryForwardProposal(
                        owner_app=CanonicalOwnerId.crm,
                        canonical_ref=follow_up.follow_up_ref,
                        workspace_ref=request.workspace_ref,
                        original_due_at=due_at,
                        proposed_local_date=local_day,
                    )
                    if today_allowed:
                        today_carry_forward.append(proposal)
                    if briefing_allowed:
                        briefing_carry_forward.append(proposal)
            add_item(
                TodayProjectionItem(
                    owner_app=CanonicalOwnerId.crm,
                    canonical_ref=follow_up.follow_up_ref,
                    workspace_ref=request.workspace_ref,
                    item_kind=TodayItemKind.crm_follow_up,
                    lane=lane,
                    source_result_refs=(source.result.result_ref,),
                    why_shown_refs=tuple(why),
                    evidence_state=TodayEvidenceState.missing,
                    freshness=TodayFreshness.current,
                    due_at=due_at,
                    ordering_factors=TodayOrderingFactors(
                        lane_ordinal=lane_ordinal,
                        urgency_ordinal=urgency,
                        time_ordinal=due_at,
                        canonical_ref=follow_up.follow_up_ref,
                    ),
                ),
                surfaces,
            )

    for candidate in supplemental_candidates:
        if candidate.workspace_ref != request.workspace_ref:
            raise TodayProjectionError("ECO_TODAY_CANDIDATE_WORKSPACE_MISMATCH")
        lane, lane_ordinal, urgency = _lane_for_supplemental(candidate.item_kind)
        add_item(
            TodayProjectionItem(
                owner_app=candidate.owner_app,
                canonical_ref=candidate.canonical_ref,
                workspace_ref=candidate.workspace_ref,
                item_kind=candidate.item_kind,
                lane=lane,
                source_result_refs=candidate.source_result_refs,
                why_shown_refs=candidate.why_shown_refs,
                evidence_refs=candidate.evidence_refs,
                receipt_refs=candidate.receipt_refs,
                evidence_state=_evidence_state(
                    candidate.evidence_refs, candidate.receipt_refs
                ),
                freshness=candidate.freshness,
                due_at=candidate.due_at,
                scheduled_at=candidate.scheduled_at,
                ordering_factors=TodayOrderingFactors(
                    lane_ordinal=lane_ordinal,
                    urgency_ordinal=urgency,
                    time_ordinal=candidate.scheduled_at or candidate.due_at,
                    canonical_ref=candidate.canonical_ref,
                ),
            ),
            candidate.surfaces,
        )

    for status in supplemental_source_statuses:
        add_status(status)

    today_items_tuple = tuple(sorted(today_items, key=_ordering_key))
    briefing_items_tuple = tuple(sorted(briefing_items, key=_ordering_key))
    today_proposals_tuple = tuple(
        sorted(
            today_carry_forward,
            key=lambda item: (item.owner_app.value, item.canonical_ref),
        )
    )
    briefing_proposals_tuple = tuple(
        sorted(
            briefing_carry_forward,
            key=lambda item: (item.owner_app.value, item.canonical_ref),
        )
    )
    today_statuses_tuple = tuple(
        sorted(today_statuses, key=lambda item: item.status_ref)
    )
    briefing_statuses_tuple = tuple(
        sorted(briefing_statuses, key=lambda item: item.status_ref)
    )
    _ensure_unique_items(today_items_tuple, surface="today")
    _ensure_unique_items(briefing_items_tuple, surface="briefing")
    _ensure_unique_statuses(today_statuses_tuple, surface="today")
    _ensure_unique_statuses(briefing_statuses_tuple, surface="briefing")
    today_result_ref = _stable_ref(
        "today-projection-result-ref",
        {
            "request": request.model_dump(mode="json"),
            "item_refs": [item.item_ref for item in today_items_tuple],
            "source_status_refs": [item.status_ref for item in today_statuses_tuple],
            "proposal_refs": [item.proposal_ref for item in today_proposals_tuple],
        },
    )
    briefing_result_ref = _stable_ref(
        "morning-briefing-result-ref",
        {
            "request": request.model_dump(mode="json"),
            "item_refs": [item.item_ref for item in briefing_items_tuple],
            "source_status_refs": [item.status_ref for item in briefing_statuses_tuple],
            "proposal_refs": [item.proposal_ref for item in briefing_proposals_tuple],
        },
    )
    today = TodayProjection(
        request=request,
        items=today_items_tuple,
        source_statuses=today_statuses_tuple,
        carry_forward_proposals=today_proposals_tuple,
        result_ref=today_result_ref,
    )
    briefing = MorningBriefingProjection(
        request=request,
        items=briefing_items_tuple,
        source_statuses=briefing_statuses_tuple,
        carry_forward_proposal_refs=tuple(
            item.proposal_ref for item in briefing_proposals_tuple
        ),
        section_refs=tuple(
            f"briefing-section-ref:eco-006/{lane.value}"
            for lane in TodayLane
            if any(item.lane == lane for item in briefing_items_tuple)
        ),
        result_ref=briefing_result_ref,
    )
    return TodayAndBriefingResult(
        today=today,
        morning_briefing=briefing,
        result_ref=_stable_ref(
            "today-briefing-result-ref",
            {"today": today_result_ref, "briefing": briefing_result_ref},
        ),
    )


__all__ = [
    "ECO_TODAY_ORDERING_CONTRACT_REF",
    "ECO_TODAY_SCHEMA_VERSION",
    "CalendarTodaySource",
    "CrmTodaySource",
    "MorningBriefingProjection",
    "TaskTodaySource",
    "TodayAndBriefingResult",
    "TodayCarryForwardProposal",
    "TodayEvidenceState",
    "TodayFreshness",
    "TodayItemKind",
    "TodayLane",
    "TodayOrderingFactors",
    "TodayProjection",
    "TodayProjectionError",
    "TodayProjectionItem",
    "TodayProjectionRequest",
    "TodayProposalKind",
    "TodaySourceStatus",
    "TodaySupplementalCandidate",
    "TodaySurface",
    "build_today_and_morning_briefing",
]
