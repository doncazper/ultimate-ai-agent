from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from ultimate_ai_agent.core.crm.private_repository import (
    CrmPrivacyPolicy,
    CrmWorkspacePreset,
    PrivateCrmFollowUp,
    PrivateCrmWorkspace,
    PrivateCrmWorkspaceReadModel,
)
from ultimate_ai_agent.core.ecosystem.calendar import (
    CalendarEvent,
    CalendarEventProjection,
    CalendarOccurrence,
    CalendarView,
    CalendarViewResult,
)
from ultimate_ai_agent.core.ecosystem.contracts import CanonicalOwnerId
from ultimate_ai_agent.core.ecosystem.tasks import (
    CanonicalTask,
    TaskListResult,
    TaskPriority,
    TaskQuery,
    TaskView,
)
from ultimate_ai_agent.core.ecosystem.today import (
    CalendarTodaySource,
    CrmTodaySource,
    TaskTodaySource,
    TodayFreshness,
    TodayItemKind,
    TodayProjectionError,
    TodayProjectionRequest,
    TodaySourceStatus,
    TodaySupplementalCandidate,
    TodaySurface,
    build_today_and_morning_briefing,
)


WORKSPACE = "workspace-ref:eco-006"
AS_OF = datetime(2026, 8, 22, 10, tzinfo=timezone.utc)


def _request() -> TodayProjectionRequest:
    return TodayProjectionRequest(
        workspace_ref=WORKSPACE,
        as_of=AS_OF,
        timezone_name="UTC",
    )


def _tasks() -> TaskTodaySource:
    query = TaskQuery(
        workspace_ref=WORKSPACE,
        view=TaskView.today,
        as_of=AS_OF.isoformat(),
    )
    return TaskTodaySource(
        result=TaskListResult(
            query=query,
            tasks=(
                CanonicalTask(
                    workspace_ref=WORKSPACE,
                    task_ref="task-ref:overdue",
                    title="Private overdue task marker",
                    due_at="2026-08-21T12:00:00Z",
                    evidence_refs=("evidence-ref:task-overdue",),
                ),
                CanonicalTask(
                    workspace_ref=WORKSPACE,
                    task_ref="task-ref:priority",
                    title="Private priority task marker",
                    priority=TaskPriority.high,
                ),
            ),
            result_ref="task-result-ref:today",
        )
    )


def _calendar() -> CalendarTodaySource:
    event = CalendarEvent(
        event_ref="event-ref:today",
        calendar_ref="calendar-ref:primary",
        title="Private calendar marker",
        starts_at=datetime(2026, 8, 22, 11, tzinfo=timezone.utc),
        ends_at=datetime(2026, 8, 22, 12, tzinfo=timezone.utc),
        timezone="UTC",
    )
    occurrence = CalendarOccurrence(
        occurrence_ref="occurrence-ref:today",
        event_ref=event.event_ref,
        calendar_ref=event.calendar_ref,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        timezone="UTC",
    )
    return CalendarTodaySource(
        workspace_ref=WORKSPACE,
        result=CalendarViewResult(
            view=CalendarView.day,
            timezone="UTC",
            range_starts_at=datetime(2026, 8, 22, tzinfo=timezone.utc),
            range_ends_at=datetime(2026, 8, 23, tzinfo=timezone.utc),
            occurrence_items=(
                CalendarEventProjection(
                    event=event,
                    occurrence=occurrence,
                    canonical_owner_ref="canonical-owner-ref:calendar",
                    field_provenance_refs=("evidence-ref:calendar-today",),
                ),
            ),
            conflict_items=(),
            result_ref="calendar-result-ref:today",
        ),
    )


def _crm(
    *,
    crm_workspace_ref: str = "crm-workspace-ref:sales",
    preset: CrmWorkspacePreset = CrmWorkspacePreset.sales,
    privacy_policy: CrmPrivacyPolicy | None = None,
    result_ref: str = "crm-result-ref:sales",
) -> CrmTodaySource:
    workspace_payload = {
        "crm_workspace_ref": crm_workspace_ref,
        "name": "Private CRM workspace marker",
        "preset": preset,
    }
    if privacy_policy is not None:
        workspace_payload["privacy_policy"] = privacy_policy
    return CrmTodaySource(
        workspace_ref=WORKSPACE,
        result=PrivateCrmWorkspaceReadModel(
            crm_workspace=PrivateCrmWorkspace.model_validate(workspace_payload),
            contexts=(),
            relationships=(),
            activities=(),
            follow_ups=(
                PrivateCrmFollowUp(
                    follow_up_ref=f"follow-up-ref:{preset.value}",
                    crm_workspace_ref=crm_workspace_ref,
                    context_ref=f"context-ref:{preset.value}",
                    title="Private CRM follow-up marker",
                    due_at=datetime(2026, 8, 20, 9, tzinfo=timezone.utc),
                ),
            ),
            pipelines=(),
            pipeline_objects=(),
            result_ref=result_ref,
        ),
    )


def test_today_projection_is_deterministic_explainable_and_proposal_only() -> None:
    missing_source = TodaySourceStatus(
        owner_app=CanonicalOwnerId.inbox,
        workspace_ref=WORKSPACE,
        source_ref="source-ref:inbox-manual-import",
        freshness=TodayFreshness.missing,
        why_status_refs=("why-source-status-ref:eco-006/manual-source-missing",),
    )
    plan = TodaySupplementalCandidate(
        owner_app=CanonicalOwnerId.plans,
        canonical_ref="milestone-ref:today",
        workspace_ref=WORKSPACE,
        item_kind=TodayItemKind.plan_milestone,
        source_result_refs=("plan-result-ref:today",),
        why_shown_refs=("why-shown-ref:eco-006/current-plan-milestone",),
    )
    first = build_today_and_morning_briefing(
        request=_request(),
        task_sources=(_tasks(),),
        calendar_sources=(_calendar(),),
        crm_sources=(_crm(),),
        supplemental_candidates=(plan,),
        supplemental_source_statuses=(missing_source,),
    )
    second = build_today_and_morning_briefing(
        request=_request(),
        task_sources=(_tasks(),),
        calendar_sources=(_calendar(),),
        crm_sources=(_crm(),),
        supplemental_candidates=(plan,),
        supplemental_source_statuses=(missing_source,),
    )

    assert first == second
    assert first.today.result_ref == second.today.result_ref
    assert all(item.why_shown_refs for item in first.today.items)
    assert all(item.ranking_performed is False for item in first.today.items)
    assert [item.ordering_factors for item in first.today.items] == sorted(
        (item.ordering_factors for item in first.today.items),
        key=lambda factors: (
            factors.lane_ordinal,
            factors.urgency_ordinal,
            factors.time_ordinal or datetime.max.replace(tzinfo=timezone.utc),
            factors.canonical_ref,
        ),
    )
    assert {item.canonical_ref for item in first.today.items} == {
        "follow-up-ref:sales",
        "task-ref:overdue",
        "occurrence-ref:today",
        "task-ref:priority",
        "milestone-ref:today",
    }
    assert len(first.today.carry_forward_proposals) == 2
    assert all(
        proposal.mutation_authorized is False
        and proposal.background_work_started is False
        for proposal in first.today.carry_forward_proposals
    )
    assert any(
        status.freshness == TodayFreshness.missing
        for status in first.today.source_statuses
    )
    serialized = json.dumps(first.model_dump(mode="json"), sort_keys=True)
    assert "Private overdue task marker" not in serialized
    assert "Private calendar marker" not in serialized
    assert "Private CRM follow-up marker" not in serialized


def test_private_relationships_leave_no_today_or_briefing_projection_trace() -> None:
    request = _request()
    without_private = build_today_and_morning_briefing(request=request)
    with_private = build_today_and_morning_briefing(
        request=request,
        crm_sources=(
            _crm(
                crm_workspace_ref="crm-workspace-ref:private",
                preset=CrmWorkspacePreset.private_relationships,
                result_ref="crm-result-ref:private-one",
            ),
        ),
    )
    changed_private = build_today_and_morning_briefing(
        request=request,
        crm_sources=(
            _crm(
                crm_workspace_ref="crm-workspace-ref:private",
                preset=CrmWorkspacePreset.private_relationships,
                result_ref="crm-result-ref:private-two",
            ),
        ),
    )

    assert with_private == without_private
    assert changed_private == without_private
    assert not with_private.today.items
    assert not with_private.today.source_statuses
    assert not with_private.today.carry_forward_proposals
    assert not with_private.morning_briefing.items


def test_surface_specific_privacy_and_workspace_scoping_fail_closed() -> None:
    briefing_only = _crm(
        privacy_policy=CrmPrivacyPolicy(
            included_in_today=False,
            included_in_briefing=True,
        )
    )
    result = build_today_and_morning_briefing(
        request=_request(), crm_sources=(briefing_only,)
    )
    assert not result.today.items
    assert not result.today.source_statuses
    assert not result.today.carry_forward_proposals
    assert len(result.morning_briefing.items) == 1
    assert len(result.morning_briefing.source_statuses) == 1
    assert len(result.morning_briefing.carry_forward_proposals) == 1
    proposal = result.morning_briefing.carry_forward_proposals[0]
    assert proposal.proposal_ref in result.morning_briefing.carry_forward_proposal_refs
    assert proposal.mutation_authorized is False

    with pytest.raises(TodayProjectionError, match="ECO_TODAY_CRM_WORKSPACE_MISMATCH"):
        build_today_and_morning_briefing(
            request=_request(),
            crm_sources=(
                briefing_only.model_copy(
                    update={"workspace_ref": "workspace-ref:other"}
                ),
            ),
        )


def test_source_result_and_freshness_changes_are_bound_into_result_refs() -> None:
    current = TodaySourceStatus(
        owner_app=CanonicalOwnerId.inbox,
        workspace_ref=WORKSPACE,
        source_ref="source-ref:inbox",
        result_ref="source-result-ref:one",
        freshness=TodayFreshness.current,
        why_status_refs=("why-source-status-ref:eco-006/current",),
        surfaces=(TodaySurface.today,),
    )
    stale = current.model_copy(
        update={
            "freshness": TodayFreshness.stale,
            "why_status_refs": ("why-source-status-ref:eco-006/stale",),
        }
    )
    first = build_today_and_morning_briefing(
        request=_request(), supplemental_source_statuses=(current,)
    )
    second = build_today_and_morning_briefing(
        request=_request(), supplemental_source_statuses=(stale,)
    )
    assert first.today.result_ref != second.today.result_ref
    assert not first.morning_briefing.source_statuses


def test_duplicate_items_and_wrong_canonical_owners_fail_closed() -> None:
    duplicate_task_source = _tasks()
    with pytest.raises(TodayProjectionError, match="ECO_TODAY_DUPLICATE_TODAY_ITEM"):
        build_today_and_morning_briefing(
            request=_request(),
            task_sources=(duplicate_task_source, duplicate_task_source),
        )

    with pytest.raises(
        ValueError, match="ECO_TODAY_CANDIDATE_CANONICAL_OWNER_MISMATCH"
    ):
        TodaySupplementalCandidate(
            owner_app=CanonicalOwnerId.crm,
            canonical_ref="milestone-ref:wrong-owner",
            workspace_ref=WORKSPACE,
            item_kind=TodayItemKind.plan_milestone,
            source_result_refs=("plan-result-ref:wrong-owner",),
            why_shown_refs=("why-shown-ref:eco-006/wrong-owner",),
        )


def test_nested_task_and_crm_workspace_membership_fails_closed() -> None:
    tasks = _tasks()
    mismatched_task = tasks.result.tasks[0].model_copy(
        update={"workspace_ref": "workspace-ref:other"}
    )
    mismatched_tasks = tasks.model_copy(
        update={"result": tasks.result.model_copy(update={"tasks": (mismatched_task,)})}
    )
    with pytest.raises(
        TodayProjectionError, match="ECO_TODAY_TASK_RECORD_WORKSPACE_MISMATCH"
    ):
        build_today_and_morning_briefing(
            request=_request(), task_sources=(mismatched_tasks,)
        )

    crm = _crm()
    mismatched_follow_up = crm.result.follow_ups[0].model_copy(
        update={"crm_workspace_ref": "crm-workspace-ref:private"}
    )
    mismatched_crm = crm.model_copy(
        update={
            "result": crm.result.model_copy(
                update={"follow_ups": (mismatched_follow_up,)}
            )
        }
    )
    with pytest.raises(
        TodayProjectionError, match="ECO_TODAY_CRM_FOLLOW_UP_WORKSPACE_MISMATCH"
    ):
        build_today_and_morning_briefing(
            request=_request(), crm_sources=(mismatched_crm,)
        )


def test_calendar_non_current_projections_are_not_daily_commitments() -> None:
    calendar = _calendar()
    archived_projection = calendar.result.occurrence_items[0].model_copy(
        update={"projection_state": "archived"}
    )
    archived_calendar = calendar.model_copy(
        update={
            "result": calendar.result.model_copy(
                update={"occurrence_items": (archived_projection,)}
            )
        }
    )

    result = build_today_and_morning_briefing(
        request=_request(), calendar_sources=(archived_calendar,)
    )

    assert not result.today.items
    assert not result.morning_briefing.items
    assert len(result.today.source_statuses) == 1


def test_scheduled_tasks_order_by_start_and_accept_canonical_evidence_limit() -> None:
    evidence_refs = tuple(f"evidence-ref:task-{index}" for index in range(64))
    scheduled = CanonicalTask(
        workspace_ref=WORKSPACE,
        task_ref="task-ref:scheduled",
        title="Private scheduled task marker",
        start_at="2026-08-22T09:00:00Z",
        due_at="2026-08-22T18:00:00Z",
        evidence_refs=evidence_refs,
    )
    source = TaskTodaySource(
        result=TaskListResult(
            query=TaskQuery(
                workspace_ref=WORKSPACE,
                view=TaskView.today,
                as_of=(AS_OF - timedelta(seconds=1)).isoformat(),
            ),
            tasks=(scheduled,),
            result_ref="task-result-ref:scheduled",
        )
    )

    result = build_today_and_morning_briefing(
        request=_request(), task_sources=(source,), calendar_sources=(_calendar(),)
    )

    assert [item.canonical_ref for item in result.today.items] == [
        "task-ref:scheduled",
        "occurrence-ref:today",
    ]
    task_item = result.today.items[0]
    assert task_item.ordering_factors.time_ordinal == datetime(
        2026, 8, 22, 9, tzinfo=timezone.utc
    )
    assert task_item.evidence_refs == evidence_refs
    task_status = next(
        status
        for status in result.today.source_statuses
        if status.owner_app == CanonicalOwnerId.tasks
    )
    assert task_status.freshness == TodayFreshness.current
    crm_result = build_today_and_morning_briefing(
        request=_request(), crm_sources=(_crm(),)
    )
    assert crm_result.today.source_statuses[0].freshness == TodayFreshness.stale
    assert crm_result.today.items[0].freshness == TodayFreshness.stale


@pytest.mark.parametrize(
    "raw_path_ref", ("C:/Users/alice/project", "path:/home/alice/project")
)
def test_path_shaped_values_are_not_safe_refs(raw_path_ref: str) -> None:
    with pytest.raises(ValueError, match="ECO_TODAY_WORKSPACE_REF_SAFE_REF_REQUIRED"):
        TodayProjectionRequest(
            workspace_ref=raw_path_ref,
            as_of=AS_OF,
        )
