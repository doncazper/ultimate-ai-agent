from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


FOLLOW_UP_TRACKER_CONTRACT_REF = "contract-ref:product-loop-004-follow-up-tracker:v1"
FOLLOW_UP_TRACKER_READ_MODEL_SOURCE = "python_core_follow_up_tracker_read_model"
FOLLOW_UP_TRACKER_CATEGORY_ORDER: tuple[str, ...] = (
    "relationship_follow_up",
    "promise",
    "open_loop",
    "pending_reply",
    "deferred_decision",
)
FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:follow-up-tracker-no-reminder-scheduler",
    "blocked-state:follow-up-tracker-no-message-send",
    "blocked-state:follow-up-tracker-no-email-calendar-fetch",
    "blocked-state:follow-up-tracker-no-connector-runtime",
    "blocked-state:follow-up-tracker-no-automatic-task-creation",
    "blocked-state:follow-up-tracker-no-action-execution",
    "blocked-state:follow-up-tracker-no-model-provider-call",
    "blocked-state:follow-up-tracker-no-hidden-memory-write",
    "blocked-state:follow-up-tracker-no-context-injection",
    "blocked-state:follow-up-tracker-no-production-authority",
    "blocked-state:follow-up-tracker-safe-refs-only",
)

FollowUpTrackerCategory = Literal[
    "relationship_follow_up",
    "promise",
    "open_loop",
    "pending_reply",
    "deferred_decision",
]

_SAFE_REF_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9:_./@#=-]{0,239}$")
_UNSAFE_TEXT_FRAGMENTS = (
    "raw_prompt",
    "raw prompt",
    "raw log",
    "raw logs",
    "raw_log",
    "raw path",
    "raw_path",
    "raw response",
    "raw_response",
    "provider_payload",
    "provider payload",
    "provider exchange",
    "api_key",
    "authorization",
    "cookie",
    "password",
    "private_key",
    "credential",
    "secret",
    "bearer",
    "token",
    "hostname",
    "host name",
    "username",
    "user name",
    "/users/",
    "/home/",
    "/private/",
    "/tmp/",
    "/var/",
    "/etc/",
    "\\users\\",
    "\\appdata\\",
    ":\\",
    "env dump",
    "environment dump",
    "stack trace",
    "traceback",
    "serial",
)


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe/private content")


def _validate_safe_ref(value: str, field_name: str) -> None:
    _validate_safe_text(value, field_name)
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe ref")


def _safe_ref_or_none(value: object) -> str | None:
    if value is None:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None
    try:
        _validate_safe_ref(candidate, "ref")
    except ValueError:
        return None
    return candidate


def _safe_refs(values: object) -> list[str]:
    if not isinstance(values, list | tuple | set):
        return []
    refs: list[str] = []
    for value in values:
        ref = _safe_ref_or_none(value)
        if ref and ref not in refs:
            refs.append(ref)
    return refs


def _safe_text_or_default(value: object, default: str) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        return default
    try:
        _validate_safe_text(candidate, "safe_text")
    except ValueError:
        return default
    return candidate[:500]


def _derived_ref(prefix: str, value: object) -> str:
    safe_value = _safe_ref_or_none(value) or "redacted"
    suffix = re.sub(r"[^a-zA-Z0-9_.@=-]+", "-", safe_value).strip("-") or "redacted"
    return f"{prefix}:{suffix[:160]}"


class FollowUpTrackerItem(BaseModel):
    item_ref: str = Field(..., min_length=1, max_length=240)
    category: FollowUpTrackerCategory
    title: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=120)
    source_state: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    why_shown: str = Field(..., min_length=1, max_length=500)
    relationship_ref: str | None = Field(default=None, max_length=240)
    promise_ref: str | None = Field(default=None, max_length=240)
    opportunity_ref: str | None = Field(default=None, max_length=240)
    action_ref: str | None = Field(default=None, max_length=240)
    memory_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    stale_state: str | None = Field(default=None, max_length=160)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    authority_boundary: str = Field(..., min_length=1, max_length=500)
    review_required: bool = True
    local_review_only: bool = True
    safe_refs_only: bool = True
    no_source_state: bool = False
    reminder_scheduler_enabled: bool = False
    message_send_enabled: bool = False
    connector_read_enabled: bool = False
    connector_write_enabled: bool = False
    email_calendar_fetch_enabled: bool = False
    automatic_task_creation_enabled: bool = False
    action_execution_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    context_injection_authorized: bool = False
    hidden_memory_write_authorized: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_tracker_item(self) -> "FollowUpTrackerItem":
        _validate_safe_ref(self.item_ref, "item_ref")
        for maybe_ref_name in [
            "relationship_ref",
            "promise_ref",
            "opportunity_ref",
            "action_ref",
        ]:
            value = getattr(self, maybe_ref_name)
            if value is not None:
                _validate_safe_ref(value, maybe_ref_name)
        for field_name in [
            "title",
            "status",
            "source_state",
            "safe_summary",
            "why_shown",
            "next_safe_action",
            "authority_boundary",
        ]:
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        if self.stale_state is not None:
            _validate_safe_text(self.stale_state, "stale_state")
        for field_name in [
            "memory_refs",
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "blocked_state_refs",
        ]:
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        if (
            not self.review_required
            or not self.local_review_only
            or not self.safe_refs_only
        ):
            raise ValueError(
                "follow-up tracker items must remain review-only safe refs"
            )
        for field_name in _DENIED_ITEM_FLAGS:
            if bool(getattr(self, field_name)):
                raise ValueError(f"{field_name} must remain false")
        return self


_DENIED_ITEM_FLAGS = (
    "reminder_scheduler_enabled",
    "message_send_enabled",
    "connector_read_enabled",
    "connector_write_enabled",
    "email_calendar_fetch_enabled",
    "automatic_task_creation_enabled",
    "action_execution_enabled",
    "runtime_model_calls_enabled",
    "context_injection_authorized",
    "hidden_memory_write_authorized",
    "production_authority_enabled",
)


class FollowUpTrackerReadModel(BaseModel):
    contract_ref: str = FOLLOW_UP_TRACKER_CONTRACT_REF
    status: str = "backend_owned_review_only_follow_up_tracker"
    source: str = FOLLOW_UP_TRACKER_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    category_order: list[FollowUpTrackerCategory] = Field(
        default_factory=lambda: list(FOLLOW_UP_TRACKER_CATEGORY_ORDER)
    )
    items: list[FollowUpTrackerItem] = Field(default_factory=list)
    relationship_follow_up_refs: list[str] = Field(default_factory=list)
    promise_refs: list[str] = Field(default_factory=list)
    open_loop_refs: list[str] = Field(default_factory=list)
    pending_reply_refs: list[str] = Field(default_factory=list)
    deferred_decision_refs: list[str] = Field(default_factory=list)
    stale_refs: list[str] = Field(default_factory=list)
    no_source_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS)
    )
    evidence_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = (
        "Review follow-up refs before drafting any proposal; no reminders, "
        "messages, connector reads, task creation, or execution are authorized."
    )
    authority_boundary: str = (
        "Follow-up tracker is a backend-owned local read model over reviewed "
        "safe refs. It does not fetch email/calendar data, send messages, create "
        "tasks, schedule reminders, call providers, write memory, inject context, "
        "or execute actions."
    )
    reminder_scheduler_enabled: bool = False
    message_send_enabled: bool = False
    connector_read_enabled: bool = False
    connector_write_enabled: bool = False
    email_calendar_fetch_enabled: bool = False
    automatic_task_creation_enabled: bool = False
    action_execution_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    context_injection_authorized: bool = False
    hidden_memory_write_authorized: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_tracker(self) -> "FollowUpTrackerReadModel":
        if self.contract_ref != FOLLOW_UP_TRACKER_CONTRACT_REF:
            raise ValueError("follow-up tracker contract ref drifted")
        if self.source != FOLLOW_UP_TRACKER_READ_MODEL_SOURCE:
            raise ValueError("follow-up tracker source drifted")
        if self.category_order != list(FOLLOW_UP_TRACKER_CATEGORY_ORDER):
            raise ValueError("follow-up tracker category order drifted")
        for field_name in [
            "backend_owned",
            "local_read_model_only",
            "safe_refs_only",
        ]:
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        if self.raw_content_included:
            raise ValueError("follow-up tracker cannot include raw content")
        for field_name in _DENIED_ITEM_FLAGS:
            if bool(getattr(self, field_name)):
                raise ValueError(f"{field_name} must remain false")
        for blocked_ref in FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS:
            if blocked_ref not in self.blocked_state_refs:
                raise ValueError("follow-up tracker missing blocked authority ref")
        for field_name in [
            "relationship_follow_up_refs",
            "promise_refs",
            "open_loop_refs",
            "pending_reply_refs",
            "deferred_decision_refs",
            "stale_refs",
            "no_source_refs",
            "blocked_state_refs",
            "evidence_refs",
        ]:
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        _validate_safe_text(self.next_safe_action, "next_safe_action")
        _validate_safe_text(self.authority_boundary, "authority_boundary")
        return self


def _tracker_item(**kwargs: Any) -> FollowUpTrackerItem:
    blocked_state_refs = _safe_refs(kwargs.pop("blocked_state_refs", []))
    blocked_state_refs = [
        *FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS,
        *[
            ref
            for ref in blocked_state_refs
            if ref not in FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS
        ],
    ]
    return FollowUpTrackerItem(blocked_state_refs=blocked_state_refs, **kwargs)


def _relationship_follow_up_items(
    crm_lite_followups: list[dict[str, Any]],
) -> list[FollowUpTrackerItem]:
    items: list[FollowUpTrackerItem] = []
    for followup in crm_lite_followups[:5]:
        follow_up_ref = _safe_ref_or_none(followup.get("follow_up_ref"))
        if not follow_up_ref:
            continue
        relationship_ref = _safe_ref_or_none(followup.get("relationship_ref"))
        promise_ref = _safe_ref_or_none(followup.get("promise_ref"))
        opportunity_ref = _safe_ref_or_none(followup.get("opportunity_ref"))
        memory_refs = _safe_refs(followup.get("memory_refs", []))
        source_refs = _safe_refs(followup.get("source_refs", []))
        evidence_refs = _safe_refs(followup.get("evidence_refs", []))
        items.append(
            _tracker_item(
                item_ref=follow_up_ref,
                category="relationship_follow_up",
                title="Relationship follow-up",
                status=_safe_text_or_default(followup.get("status"), "review_only"),
                source_state="reviewed_memory_ref",
                safe_summary=_safe_text_or_default(
                    followup.get("safe_summary"),
                    "Reviewed memory produced a relationship follow-up ref.",
                ),
                why_shown=_safe_text_or_default(
                    followup.get("why_now"),
                    "Relationship follow-up is visible from reviewed memory.",
                ),
                relationship_ref=relationship_ref,
                promise_ref=promise_ref,
                opportunity_ref=opportunity_ref,
                memory_refs=memory_refs,
                source_refs=source_refs,
                evidence_refs=evidence_refs,
                stale_state="recheck_required_before_message_or_task",
                next_safe_action=_safe_text_or_default(
                    followup.get("next_safe_action"),
                    "Review memory and evidence refs before drafting a follow-up.",
                ),
                authority_boundary=_safe_text_or_default(
                    followup.get("authority_boundary"),
                    "Relationship follow-up is local reviewed recall only.",
                ),
                blocked_state_refs=_safe_refs(followup.get("blocked_state_refs", [])),
            )
        )
        if promise_ref:
            items.append(
                _tracker_item(
                    item_ref=promise_ref,
                    category="promise",
                    title="Promise or commitment",
                    status="review_only_stale_check_required",
                    source_state="reviewed_memory_ref",
                    safe_summary="Promise ref is visible as local reviewed recall.",
                    why_shown="The promise is linked to a relationship follow-up ref.",
                    relationship_ref=relationship_ref,
                    promise_ref=promise_ref,
                    opportunity_ref=opportunity_ref,
                    memory_refs=memory_refs,
                    source_refs=[follow_up_ref, *source_refs],
                    evidence_refs=evidence_refs,
                    stale_state="recheck_required_before_relying_on_promise",
                    next_safe_action="Review evidence refs before drafting a promise follow-up.",
                    authority_boundary="Promise tracking is recall-only and grants no message or task authority.",
                    blocked_state_refs=_safe_refs(
                        followup.get("blocked_state_refs", [])
                    ),
                )
            )
    return items


def _memory_follow_up_items(
    memory_items: list[dict[str, Any]],
) -> list[FollowUpTrackerItem]:
    items: list[FollowUpTrackerItem] = []
    for memory in memory_items[:6]:
        review_ref = _safe_ref_or_none(memory.get("review_ref"))
        if not review_ref:
            continue
        candidate_kind = _safe_text_or_default(
            memory.get("business_memory_candidate_kind") or memory.get("candidate_kind"),
            "",
        )
        if candidate_kind not in {
            "promise",
            "commitment",
            "follow_up",
            "opportunity",
            "deal",
            "project",
        }:
            continue
        candidate_ref = _safe_ref_or_none(
            memory.get("business_memory_candidate_ref")
            or memory.get("candidate_ref")
            or review_ref
        )
        item_ref = candidate_ref or _derived_ref("memory-follow-up-ref", review_ref)
        category: FollowUpTrackerCategory = (
            "promise"
            if candidate_kind in {"promise", "commitment"}
            else "relationship_follow_up"
            if candidate_kind == "follow_up"
            else "open_loop"
        )
        items.append(
            _tracker_item(
                item_ref=item_ref,
                category=category,
                title=(
                    "Promise or commitment"
                    if category == "promise"
                    else "Memory follow-up"
                    if category == "relationship_follow_up"
                    else "Open loop"
                ),
                status=_safe_text_or_default(
                    memory.get("review_state") or memory.get("status"),
                    "review_required",
                ),
                source_state="reviewed_memory_queue_ref",
                safe_summary=_safe_text_or_default(
                    memory.get("safe_summary"),
                    "Reviewed memory produced a follow-up candidate ref.",
                ),
                why_shown=(
                    "Reviewed memory candidate kind can create a local follow-up "
                    "loop, but remains recall-only."
                ),
                promise_ref=item_ref if category == "promise" else None,
                opportunity_ref=item_ref if candidate_kind in {"opportunity", "deal"} else None,
                memory_refs=[review_ref, *([candidate_ref] if candidate_ref else [])],
                source_refs=_safe_refs(memory.get("source_refs", [])),
                evidence_refs=_safe_refs(memory.get("evidence_refs", [])),
                receipt_refs=_safe_refs(memory.get("receipt_refs", [])),
                stale_state=_safe_text_or_default(
                    memory.get("business_memory_stale_state")
                    or memory.get("stale_state"),
                    "recheck_required_before_follow_up",
                ),
                next_safe_action=_safe_text_or_default(
                    memory.get("business_memory_next_safe_action")
                    or memory.get("next_safe_action"),
                    "Review memory evidence refs before drafting any follow-up.",
                ),
                authority_boundary=(
                    "Memory-derived follow-up tracking is recall-only and grants "
                    "no memory write, context injection, task creation, message, "
                    "connector, or action authority."
                ),
                blocked_state_refs=_safe_refs(
                    [
                        *list(memory.get("business_memory_blocker_refs") or []),
                        *list(memory.get("blocked_states") or []),
                    ]
                ),
            )
        )
    return items


def _open_loop_items(actions: list[dict[str, Any]]) -> list[FollowUpTrackerItem]:
    items: list[FollowUpTrackerItem] = []
    for action in actions[:6]:
        action_ref = _safe_ref_or_none(action.get("item_ref"))
        if not action_ref:
            continue
        status = _safe_text_or_default(action.get("status"), "review_required")
        action_group = _safe_text_or_default(action.get("action_group_id"), "review")
        if status in {"receipt_recorded", "rejected"}:
            continue
        category: FollowUpTrackerCategory = (
            "deferred_decision" if status in {"deferred", "snoozed"} else "open_loop"
        )
        items.append(
            _tracker_item(
                item_ref=(
                    _derived_ref("deferred-decision-ref", action_ref)
                    if category == "deferred_decision"
                    else _derived_ref("open-loop-ref", action_ref)
                ),
                category=category,
                title="Deferred decision"
                if category == "deferred_decision"
                else "Open loop",
                status=status,
                source_state=action_group,
                safe_summary=_safe_text_or_default(
                    action.get("safe_summary"),
                    "Action Inbox item remains reviewable local state.",
                ),
                why_shown="Action Inbox item has not produced a final safe receipt.",
                action_ref=action_ref,
                source_refs=[action_ref],
                evidence_refs=_safe_refs(action.get("evidence_refs", [])),
                receipt_refs=_safe_refs(action.get("receipt_refs", [])),
                stale_state=_safe_text_or_default(
                    action.get("stale_state"),
                    "recheck_required_before_follow_up",
                ),
                next_safe_action="Review exact scope before recording any supported receipt.",
                authority_boundary="Open loops are review-only and do not authorize action execution.",
                blocked_state_refs=_safe_refs(action.get("blocked_state_refs", [])),
            )
        )
    return items


def _pending_reply_items(
    source_readiness_items: list[dict[str, Any]],
) -> list[FollowUpTrackerItem]:
    items: list[FollowUpTrackerItem] = []
    for source in source_readiness_items:
        source_kind = _safe_text_or_default(source.get("source_kind"), "")
        if source_kind not in {"inbox", "email", "calendar"}:
            continue
        source_ref = _safe_ref_or_none(source.get("source_ref"))
        if not source_ref:
            continue
        status = _safe_text_or_default(source.get("status"), "not_configured")
        items.append(
            _tracker_item(
                item_ref=_derived_ref("pending-reply-ref", source_ref),
                category="pending_reply",
                title="Pending replies",
                status="blocked_no_source" if status != "ready" else "review_only",
                source_state=status,
                safe_summary=(
                    "Pending replies are visible only as source-readiness posture; "
                    "no inbox or calendar content is fetched."
                ),
                why_shown="A source could contain pending replies, but runtime source access is blocked.",
                source_refs=[source_ref],
                evidence_refs=_safe_refs(source.get("evidence_refs", [])),
                no_source_state=status != "ready",
                next_safe_action="Add a scoped read-only source contract before pending replies can be grounded.",
                authority_boundary="Pending reply posture is metadata only and grants no source or message authority.",
                blocked_state_refs=_safe_refs(source.get("blocked_state_refs", [])),
            )
        )
    return items[:3]


def _memory_deferred_items(
    memory_review_decisions: list[dict[str, Any]],
) -> list[FollowUpTrackerItem]:
    items: list[FollowUpTrackerItem] = []
    for decision in memory_review_decisions[:5]:
        decision_kind = _safe_text_or_default(
            decision.get("decision")
            or decision.get("decision_kind")
            or decision.get("status"),
            "",
        )
        if decision_kind not in {"defer", "deferred"}:
            continue
        receipt_ref = _safe_ref_or_none(decision.get("receipt_ref"))
        candidate_ref = _safe_ref_or_none(decision.get("candidate_ref"))
        item_ref = receipt_ref or _derived_ref(
            "deferred-decision-ref", candidate_ref or "memory"
        )
        items.append(
            _tracker_item(
                item_ref=item_ref,
                category="deferred_decision",
                title="Deferred memory decision",
                status="deferred_pending_operator_review",
                source_state="memory_review_receipt",
                safe_summary="Memory Review decision remains deferred and review-only.",
                why_shown="Deferred memory decisions can create open follow-up loops.",
                memory_refs=[ref for ref in [candidate_ref] if ref],
                receipt_refs=[ref for ref in [receipt_ref] if ref],
                evidence_refs=_safe_refs(decision.get("evidence_refs", [])),
                stale_state="recheck_required_before_memory_use",
                next_safe_action="Review the memory decision receipt before using it as recall.",
                authority_boundary="Deferred memory decisions do not authorize memory writes or context injection.",
                blocked_state_refs=_safe_refs(decision.get("blocked_state_refs", [])),
            )
        )
    return items


def _unique_items(
    items: list[FollowUpTrackerItem], *, limit: int
) -> list[FollowUpTrackerItem]:
    deduped: list[FollowUpTrackerItem] = []
    seen: set[str] = set()
    for item in items:
        if item.item_ref in seen:
            continue
        seen.add(item.item_ref)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def build_follow_up_tracker_read_model(
    *,
    actions: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    memory_review_decisions: list[dict[str, Any]],
    crm_lite_followups: list[dict[str, Any]],
    source_readiness_items: list[dict[str, Any]],
    evidence_timeline: list[dict[str, Any]],
    limit: int = 12,
) -> dict[str, Any]:
    del evidence_timeline
    items = _unique_items(
        [
            *_relationship_follow_up_items(crm_lite_followups),
            *_memory_follow_up_items(memory_items),
            *_open_loop_items(actions),
            *_pending_reply_items(source_readiness_items),
            *_memory_deferred_items(memory_review_decisions),
        ],
        limit=max(1, min(limit, 25)),
    )
    refs_by_category: dict[str, list[str]] = {
        category: [item.item_ref for item in items if item.category == category]
        for category in FOLLOW_UP_TRACKER_CATEGORY_ORDER
    }
    evidence_refs: list[str] = []
    blocked_state_refs = list(FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS)
    stale_refs: list[str] = []
    no_source_refs: list[str] = []
    for item in items:
        for ref in item.evidence_refs:
            if ref not in evidence_refs:
                evidence_refs.append(ref)
        for ref in item.blocked_state_refs:
            if ref not in blocked_state_refs:
                blocked_state_refs.append(ref)
        if item.stale_state:
            stale_ref = _derived_ref("stale-follow-up-ref", item.item_ref)
            if stale_ref not in stale_refs:
                stale_refs.append(stale_ref)
        if item.no_source_state and item.item_ref not in no_source_refs:
            no_source_refs.append(item.item_ref)

    return FollowUpTrackerReadModel(
        status=(
            "backend_owned_review_only_follow_up_tracker"
            if items
            else "backend_owned_no_follow_up_refs"
        ),
        items=items,
        relationship_follow_up_refs=refs_by_category["relationship_follow_up"],
        promise_refs=refs_by_category["promise"],
        open_loop_refs=refs_by_category["open_loop"],
        pending_reply_refs=refs_by_category["pending_reply"],
        deferred_decision_refs=refs_by_category["deferred_decision"],
        stale_refs=stale_refs,
        no_source_refs=no_source_refs,
        blocked_state_refs=blocked_state_refs,
        evidence_refs=evidence_refs,
    ).model_dump(mode="json")


__all__ = [
    "FOLLOW_UP_TRACKER_CATEGORY_ORDER",
    "FOLLOW_UP_TRACKER_CONTRACT_REF",
    "FOLLOW_UP_TRACKER_READ_MODEL_SOURCE",
    "FOLLOW_UP_TRACKER_REQUIRED_BLOCKED_REFS",
    "FollowUpTrackerItem",
    "FollowUpTrackerReadModel",
    "build_follow_up_tracker_read_model",
]
