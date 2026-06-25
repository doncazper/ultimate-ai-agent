from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


TODAY_LOOP_TIGHTENING_CONTRACT_REF = (
    "contract-ref:product-loop-003-today-loop-tightening:v1"
)
TODAY_LOOP_READ_MODEL_SOURCE = "python_core_today_loop_read_model"
TODAY_LOOP_LANE_ORDER = (
    "needs_review",
    "blocked_now",
    "changed",
    "follow_up",
    "stale_or_deferred",
)
TODAY_LOOP_REQUIRED_BLOCKED_REFS = (
    "blocked-state:today-loop-no-action-execution",
    "blocked-state:today-loop-no-connector-runtime",
    "blocked-state:today-loop-no-runtime-model-call",
    "blocked-state:today-loop-no-automatic-memory-write",
    "blocked-state:today-loop-no-context-injection",
    "blocked-state:today-loop-safe-refs-only",
)
TODAY_LOOP_LANE_LABELS = {
    "needs_review": "Needs review",
    "blocked_now": "Blocked now",
    "changed": "Changed",
    "follow_up": "Follow-ups",
    "stale_or_deferred": "Stale or deferred",
}

_SAFE_SUFFIX_CHARS = re.compile(r"[^a-z0-9_.@-]+")
_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw provider",
    "raw_provider",
    "raw path",
    "raw_path",
    "raw log",
    "raw_log",
    "account identifier",
    "account_identifier",
    "account id",
    "account_id",
    "raw private content",
    "raw_private_content",
    "environment dump",
    "environment_dump",
    "credential material",
    "credential_material",
    "unredacted transcript",
    "full transcript",
    "username",
    "user name",
    "hostname",
    "host name",
    "serial",
)


TodayLoopLaneId = Literal[
    "needs_review",
    "blocked_now",
    "changed",
    "follow_up",
    "stale_or_deferred",
]


class TodayLoopDigestItem(BaseModel):
    item_ref: str = Field(..., min_length=1, max_length=220)
    lane_id: TodayLoopLaneId
    surface: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=160)
    state_label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=120)
    priority: str = Field(default="medium", min_length=1, max_length=40)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    reason: str = Field(..., min_length=1, max_length=300)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    stale_state: str | None = Field(default=None, max_length=160)
    review_required: bool = True
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    authority_boundary: str = Field(..., min_length=1, max_length=500)
    safe_refs_only: bool = True
    content_untrusted: bool = False
    action_execution_enabled: bool = False
    connector_runtime_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "TodayLoopDigestItem":
        _validate_safe_ref(self.item_ref, "item_ref")
        for field_name in [
            "surface",
            "title",
            "state_label",
            "status",
            "priority",
            "safe_summary",
            "reason",
            "next_safe_action",
            "authority_boundary",
        ]:
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        if self.stale_state is not None:
            _validate_safe_text(self.stale_state, "stale_state")
        for field_name in [
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "blocked_state_refs",
        ]:
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        if not self.safe_refs_only:
            raise ValueError("today digest items must be safe-ref only")
        for field_name in [
            "action_execution_enabled",
            "connector_runtime_enabled",
            "runtime_model_calls_enabled",
            "automatic_memory_write_authorized",
            "context_injection_authorized",
            "production_authority_enabled",
        ]:
            if bool(getattr(self, field_name)):
                raise ValueError(f"{field_name} must remain false")
        return self


class TodayLoopLane(BaseModel):
    lane_id: TodayLoopLaneId
    label: str = Field(..., min_length=1, max_length=80)
    status: str = Field(..., min_length=1, max_length=120)
    count: int = Field(default=0, ge=0)
    item_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    review_only: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "TodayLoopLane":
        _validate_safe_text(self.label, "label")
        _validate_safe_text(self.status, "status")
        _validate_safe_text(self.next_safe_action, "next_safe_action")
        for field_name in [
            "item_refs",
            "evidence_refs",
            "receipt_refs",
            "blocked_state_refs",
        ]:
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        if not self.review_only:
            raise ValueError("today loop lanes must remain review-only")
        return self


class TodayLoopReadModel(BaseModel):
    schema_version: str = "product-loop-003-today-loop-tightening.v1"
    contract_ref: str = TODAY_LOOP_TIGHTENING_CONTRACT_REF
    status: str = "implemented_backend_owned_review_digest"
    source: str = TODAY_LOOP_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    lane_order: list[TodayLoopLaneId] = Field(
        default_factory=lambda: list(TODAY_LOOP_LANE_ORDER)
    )
    lanes: list[TodayLoopLane] = Field(default_factory=list)
    digest_items: list[TodayLoopDigestItem] = Field(default_factory=list)
    what_matters_now_refs: list[str] = Field(default_factory=list)
    what_changed_refs: list[str] = Field(default_factory=list)
    blocked_now_refs: list[str] = Field(default_factory=list)
    needs_review_refs: list[str] = Field(default_factory=list)
    follow_up_refs: list[str] = Field(default_factory=list)
    stale_or_deferred_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = (
        "Review needs-review, blocked, changed, follow-up, and stale refs before "
        "opening deeper surfaces."
    )
    authority_boundary: str = (
        "Today Loop digest is a backend-owned read model over local safe refs. "
        "It does not execute actions, call providers, fetch connectors, write "
        "memory, inject context, or grant production authority."
    )
    action_execution_enabled: bool = False
    connector_runtime_enabled: bool = False
    source_refresh_enabled: bool = False
    runtime_model_calls_enabled: bool = False
    automatic_memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    production_authority_enabled: bool = False
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(TODAY_LOOP_REQUIRED_BLOCKED_REFS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "TodayLoopReadModel":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_text(self.status, "status")
        _validate_safe_text(self.source, "source")
        _validate_safe_text(self.next_safe_action, "next_safe_action")
        _validate_safe_text(self.authority_boundary, "authority_boundary")
        if not self.backend_owned:
            raise ValueError("today loop digest must be backend-owned")
        if not self.local_read_model_only:
            raise ValueError("today loop digest must remain a local read model")
        if not self.safe_refs_only or self.raw_content_included:
            raise ValueError("today loop digest must be safe-ref only")
        for field_name in [
            "action_execution_enabled",
            "connector_runtime_enabled",
            "source_refresh_enabled",
            "runtime_model_calls_enabled",
            "automatic_memory_write_authorized",
            "context_injection_authorized",
            "production_authority_enabled",
        ]:
            if bool(getattr(self, field_name)):
                raise ValueError(f"{field_name} must remain false")
        for field_name in [
            "what_matters_now_refs",
            "what_changed_refs",
            "blocked_now_refs",
            "needs_review_refs",
            "follow_up_refs",
            "stale_or_deferred_refs",
            "evidence_refs",
            "blocked_state_refs",
        ]:
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        return self


def build_today_loop_read_model(
    *,
    actions: list[dict[str, Any]],
    plans: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    briefing_items: list[dict[str, Any]],
    evidence_timeline: list[dict[str, Any]],
    chat_turn_receipts: list[dict[str, Any]],
    chat_handoff_receipts: list[dict[str, Any]],
    memory_review_decisions: list[dict[str, Any]],
    crm_lite_followups: list[dict[str, Any]],
    source_readiness_items: list[dict[str, Any]],
    limit_per_lane: int = 5,
) -> dict[str, Any]:
    items: list[TodayLoopDigestItem] = []
    limit = max(1, min(int(limit_per_lane), 8))

    for action in actions:
        action_ref = _safe_ref_or_none(action.get("item_ref"))
        if not action_ref:
            continue
        title = _safe_text_or_default(action.get("title"), "Action review")
        action_status = _safe_text_or_default(action.get("status"), "review_ready")
        action_priority = _safe_text_or_default(action.get("priority"), "medium")
        base_refs = _safe_refs(
            [
                action.get("item_ref"),
                action.get("action_envelope_ref"),
                action.get("approval_envelope_ref"),
                action.get("local_task_ref"),
            ]
        )
        evidence_refs = _safe_refs(action.get("evidence_refs", []))
        receipt_refs = _safe_refs(action.get("receipt_refs", []))
        blocked_refs = [
            *_safe_refs(
                [
                    action.get("local_task_safe_disable_ref"),
                    action.get("local_task_safe_disable_posture_ref"),
                ]
            ),
            *_generated_action_blockers(action),
        ]
        next_safe_action = _safe_text_or_default(
            action.get("next_safe_action"),
            "Review exact scope and receipt posture before any later action.",
        )
        if _is_reviewable_action(action):
            items.append(
                _digest_item(
                    item_ref=action_ref,
                    lane_id="needs_review",
                    surface="Actions",
                    title=title,
                    state_label="Needs review",
                    status=action_status,
                    priority=action_priority,
                    safe_summary=_safe_text_or_default(
                        action.get("safe_summary"),
                        "Action Inbox item needs local operator review.",
                    ),
                    reason="Action Inbox item is reviewable and approval-bound.",
                    source_refs=base_refs,
                    evidence_refs=evidence_refs,
                    receipt_refs=receipt_refs,
                    blocked_state_refs=blocked_refs,
                    stale_state=action.get("stale_state"),
                    next_safe_action=next_safe_action,
                )
            )
        if _is_blocked(action):
            items.append(
                _digest_item(
                    item_ref=_derived_ref("today-loop-blocked", action_ref),
                    lane_id="blocked_now",
                    surface="Actions",
                    title=title,
                    state_label="Cost or authority blocked"
                    if _has_cost_blocker(action)
                    else "Blocked",
                    status=_safe_text_or_default(
                        action.get("state_change_readiness"), "blocked"
                    ),
                    priority=action_priority,
                    safe_summary="Action cannot proceed until blockers and exact scope are resolved.",
                    reason="Action carries blocked authority or state-change posture.",
                    source_refs=base_refs,
                    evidence_refs=evidence_refs,
                    receipt_refs=receipt_refs,
                    blocked_state_refs=blocked_refs
                    or ["blocked-state:today-loop-action-blocked"],
                    stale_state=action.get("stale_state"),
                    next_safe_action=next_safe_action,
                )
            )
        if receipt_refs:
            items.append(
                _digest_item(
                    item_ref=_derived_ref("today-loop-changed", action_ref),
                    lane_id="changed",
                    surface="Actions",
                    title=title,
                    state_label="Receipt recorded",
                    status="changed_receipt_recorded",
                    priority=action_priority,
                    safe_summary="Action Inbox item has receipt refs for operator history.",
                    reason="Receipt refs changed the local action history.",
                    source_refs=base_refs,
                    evidence_refs=evidence_refs,
                    receipt_refs=receipt_refs,
                    blocked_state_refs=blocked_refs,
                    stale_state=action.get("stale_state"),
                    next_safe_action="Inspect receipt refs before further review.",
                )
            )
        if action.get("stale_state"):
            items.append(
                _stale_item(
                    source_ref=action_ref,
                    surface="Actions",
                    title=title,
                    status=action.get("stale_state"),
                    source_refs=base_refs,
                    evidence_refs=evidence_refs,
                    receipt_refs=receipt_refs,
                    blocked_state_refs=blocked_refs,
                    next_safe_action=next_safe_action,
                )
            )

    for plan in plans:
        plan_ref = _safe_ref_or_none(plan.get("plan_ref"))
        if not plan_ref:
            continue
        plan_refs = _safe_refs(
            [
                plan.get("plan_ref"),
                plan.get("task_decomposition_proposal_ref"),
                plan.get("task_decomposition_review_envelope_ref"),
                *(plan.get("task_decomposition_suggested_action_inbox_proposal_refs") or []),
            ]
        )
        blocked_refs = _safe_refs(plan.get("task_decomposition_blocked_authority_refs", []))
        items.append(
            _digest_item(
                item_ref=plan_ref,
                lane_id="needs_review",
                surface="Plans",
                title=_safe_text_or_default(plan.get("title"), "Plan review"),
                state_label="Plan proposal",
                status=_safe_text_or_default(
                    plan.get("task_decomposition_status"), plan.get("status", "proposal")
                ),
                priority="medium",
                safe_summary=_safe_text_or_default(
                    plan.get("safe_summary"),
                    "Plan proposal is review-only.",
                ),
                reason="Plans stay proposal-only until converted into reviewed Action envelopes.",
                source_refs=plan_refs,
                evidence_refs=_safe_refs(plan.get("evidence_refs", [])),
                receipt_refs=[],
                blocked_state_refs=blocked_refs
                or ["blocked-state:today-loop-plan-execution-blocked"],
                stale_state=plan.get("stale_state"),
                next_safe_action=_safe_text_or_default(
                    plan.get("next_step_summary"),
                    "Review plan refs before creating any action envelope.",
                ),
            )
        )

    for item in memory_items:
        review_ref = _safe_ref_or_none(item.get("review_ref"))
        if not review_ref:
            continue
        source_refs = _safe_refs(
            [
                item.get("review_ref"),
                *(item.get("source_refs") or []),
                *(item.get("provenance_refs") or []),
            ]
        )
        blocked_refs = _memory_blockers(item)
        items.append(
            _digest_item(
                item_ref=review_ref,
                lane_id="needs_review",
                surface="Memory",
                title=_safe_text_or_default(item.get("title"), "Memory review"),
                state_label="Memory review",
                status=_safe_text_or_default(item.get("review_state"), "review_needed"),
                priority=_safe_text_or_default(item.get("priority"), "medium"),
                safe_summary=_safe_text_or_default(
                    item.get("safe_summary"),
                    "Memory candidate needs review.",
                ),
                reason="Memory recall is visible for review, not truth or context authority.",
                source_refs=source_refs,
                evidence_refs=_safe_refs(item.get("evidence_refs", [])),
                receipt_refs=_safe_refs(item.get("receipt_refs", [])),
                blocked_state_refs=blocked_refs,
                stale_state=item.get("stale_state"),
                next_safe_action=_safe_text_or_default(
                    item.get("next_safe_action"),
                    "Review memory provenance and evidence refs.",
                ),
            )
        )
        if item.get("stale_state"):
            items.append(
                _stale_item(
                    source_ref=review_ref,
                    surface="Memory",
                    title=_safe_text_or_default(item.get("title"), "Memory review"),
                    status=item.get("stale_state"),
                    source_refs=source_refs,
                    evidence_refs=_safe_refs(item.get("evidence_refs", [])),
                    receipt_refs=_safe_refs(item.get("receipt_refs", [])),
                    blocked_state_refs=blocked_refs,
                    next_safe_action=_safe_text_or_default(
                        item.get("next_safe_action"),
                        "Review memory stale refs before recall use.",
                    ),
                )
            )

    for receipt in memory_review_decisions:
        receipt_ref = _safe_ref_or_none(receipt.get("receipt_ref"))
        if not receipt_ref:
            continue
        items.append(
            _digest_item(
                item_ref=receipt_ref,
                lane_id="changed",
                surface="Memory",
                title="Memory review receipt",
                state_label="Memory receipt",
                status=_safe_text_or_default(receipt.get("decision"), "receipt_recorded"),
                priority="medium",
                safe_summary="Memory Review decision receipt changed local review posture.",
                reason="A memory review decision receipt is available for inspection.",
                source_refs=_safe_refs([receipt.get("candidate_ref")]),
                evidence_refs=_safe_refs(receipt.get("evidence_refs", [])),
                receipt_refs=[receipt_ref],
                blocked_state_refs=["blocked-state:today-loop-memory-recall-not-truth"],
                next_safe_action="Inspect receipt refs before relying on memory posture.",
            )
        )

    for followup in crm_lite_followups:
        follow_ref = _safe_ref_or_none(followup.get("follow_up_ref"))
        if not follow_ref:
            continue
        items.append(
            _digest_item(
                item_ref=follow_ref,
                lane_id="follow_up",
                surface="Memory",
                title="Relationship follow-up",
                state_label="Follow-up review",
                status=_safe_text_or_default(followup.get("status"), "review_only"),
                priority="medium",
                safe_summary=_safe_text_or_default(
                    followup.get("safe_summary"),
                    "Reviewed relationship follow-up is visible.",
                ),
                reason=_safe_text_or_default(
                    followup.get("why_now"),
                    "Reviewed memory produced a local follow-up ref.",
                ),
                source_refs=_safe_refs(
                    [
                        followup.get("relationship_ref"),
                        followup.get("review_envelope_ref"),
                        *(followup.get("memory_refs") or []),
                        *(followup.get("source_refs") or []),
                    ]
                ),
                evidence_refs=_safe_refs(followup.get("evidence_refs", [])),
                receipt_refs=[],
                blocked_state_refs=_safe_refs(followup.get("blocked_state_refs", []))
                or ["blocked-state:today-loop-no-external-crm-write"],
                next_safe_action=_safe_text_or_default(
                    followup.get("next_safe_action"),
                    "Review follow-up refs before drafting any action.",
                ),
            )
        )

    for source in source_readiness_items:
        source_ref = _safe_ref_or_none(source.get("source_ref"))
        if not source_ref:
            continue
        status = _safe_text_or_default(source.get("status"), "metadata_only")
        if status in {"blocked", "missing", "unavailable", "not_configured"}:
            items.append(
                _digest_item(
                    item_ref=source_ref,
                    lane_id="blocked_now",
                    surface="Sources",
                    title=f"{_safe_text_or_default(source.get('source_kind'), 'source')} source",
                    state_label="No source authority",
                    status=status,
                    priority="high" if status == "blocked" else "medium",
                    safe_summary=_safe_text_or_default(
                        source.get("safe_summary"),
                        "Source readiness is blocked or not configured.",
                    ),
                    reason="Missing source authority affects Today inputs.",
                    source_refs=_safe_refs(source.get("source_refs", [])),
                    evidence_refs=_safe_refs(source.get("evidence_refs", [])),
                    receipt_refs=[],
                    blocked_state_refs=_safe_refs(source.get("blocked_state_refs", []))
                    or ["blocked-state:today-loop-source-readiness-blocked"],
                    next_safe_action=_safe_text_or_default(
                        source.get("next_safe_action"),
                        "Keep source-derived items blocked until scoped contracts exist.",
                    ),
                )
            )

    for receipt in [*chat_turn_receipts, *chat_handoff_receipts]:
        receipt_ref = _safe_ref_or_none(receipt.get("receipt_ref"))
        if not receipt_ref:
            continue
        created_ref = _safe_ref_or_none(receipt.get("created_ref"))
        lane_id: TodayLoopLaneId = "needs_review" if created_ref else "changed"
        items.append(
            _digest_item(
                item_ref=created_ref or receipt_ref,
                lane_id=lane_id,
                surface="Chat",
                title="Chat handoff" if created_ref else "Chat receipt",
                state_label="Reviewable handoff" if created_ref else "Receipt recorded",
                status=_safe_text_or_default(receipt.get("status"), "receipt_recorded"),
                priority="medium",
                safe_summary="Chat produced local receipt or handoff refs for review.",
                reason="Chat output remains proposal and receipt posture only.",
                source_refs=_safe_refs([receipt.get("turn_ref"), receipt.get("handoff_ref")]),
                evidence_refs=_safe_refs(receipt.get("evidence_refs", [])),
                receipt_refs=[receipt_ref],
                blocked_state_refs=["blocked-state:today-loop-chat-output-not-authority"],
                next_safe_action="Review handoff refs before creating memory, plan, or action proposals.",
            )
        )

    for evidence_item in evidence_timeline[:limit]:
        timeline_ref = _safe_ref_or_none(evidence_item.get("timeline_item_ref"))
        if not timeline_ref:
            continue
        items.append(
            _digest_item(
                item_ref=timeline_ref,
                lane_id="changed",
                surface="Evidence",
                title=_safe_text_or_default(evidence_item.get("title"), "Evidence event"),
                state_label="Evidence update",
                status=_safe_text_or_default(evidence_item.get("item_kind"), "evidence"),
                priority="medium",
                safe_summary="Evidence Timeline has safe refs for recent operator history.",
                reason="Evidence changed or explains the current local loop state.",
                source_refs=[timeline_ref],
                evidence_refs=_safe_refs(evidence_item.get("evidence_refs", [])),
                receipt_refs=_safe_refs(evidence_item.get("receipt_refs", [])),
                blocked_state_refs=_safe_refs(
                    [
                        *(evidence_item.get("blocked_state_refs") or []),
                        *(evidence_item.get("blocked_states") or []),
                    ]
                ),
                next_safe_action="Inspect evidence refs outside the UI before relying on a claim.",
            )
        )

    for briefing in briefing_items:
        briefing_ref = _safe_ref_or_none(briefing.get("briefing_ref"))
        if not briefing_ref:
            continue
        if briefing.get("stale_state"):
            items.append(
                _stale_item(
                    source_ref=briefing_ref,
                    surface="Today",
                    title=_safe_text_or_default(briefing.get("title"), "Briefing item"),
                    status=briefing.get("stale_state"),
                    source_refs=_safe_refs(
                        [briefing.get("briefing_ref"), *(briefing.get("source_refs") or [])]
                    ),
                    evidence_refs=_safe_refs(briefing.get("evidence_refs", [])),
                    receipt_refs=[],
                    blocked_state_refs=_safe_refs(briefing.get("blocked_states", [])),
                    next_safe_action=_safe_text_or_default(
                        briefing.get("next_safe_action"),
                        "Recheck briefing source refs before use.",
                    ),
                )
            )

    deduped = _dedupe_items(items)
    lane_rows: list[TodayLoopLane] = []
    for lane_id in TODAY_LOOP_LANE_ORDER:
        lane_items = [item for item in deduped if item.lane_id == lane_id][:limit]
        lane_rows.append(
            TodayLoopLane(
                lane_id=lane_id,
                label=TODAY_LOOP_LANE_LABELS[lane_id],
                status="ready_for_review" if lane_items else "empty",
                count=len([item for item in deduped if item.lane_id == lane_id]),
                item_refs=[item.item_ref for item in lane_items],
                evidence_refs=_unique_refs(
                    ref for item in lane_items for ref in item.evidence_refs
                ),
                receipt_refs=_unique_refs(
                    ref for item in lane_items for ref in item.receipt_refs
                ),
                blocked_state_refs=_unique_refs(
                    [
                        *TODAY_LOOP_REQUIRED_BLOCKED_REFS,
                        *[
                            ref
                            for item in lane_items
                            for ref in item.blocked_state_refs
                        ],
                    ]
                )[:12],
                next_safe_action=_lane_next_safe_action(lane_id),
            )
        )

    lane_items_by_id = {
        lane_id: [item for item in deduped if item.lane_id == lane_id][:limit]
        for lane_id in TODAY_LOOP_LANE_ORDER
    }
    what_matters_now = _unique_refs(
        item.item_ref
        for lane_id in ("needs_review", "blocked_now", "follow_up")
        for item in lane_items_by_id[lane_id][:3]
    )
    read_model = TodayLoopReadModel(
        lanes=lane_rows,
        digest_items=[
            item
            for lane_id in TODAY_LOOP_LANE_ORDER
            for item in lane_items_by_id[lane_id]
        ][: max(limit * len(TODAY_LOOP_LANE_ORDER), 1)],
        what_matters_now_refs=what_matters_now,
        what_changed_refs=[item.item_ref for item in lane_items_by_id["changed"]],
        blocked_now_refs=[item.item_ref for item in lane_items_by_id["blocked_now"]],
        needs_review_refs=[item.item_ref for item in lane_items_by_id["needs_review"]],
        follow_up_refs=[item.item_ref for item in lane_items_by_id["follow_up"]],
        stale_or_deferred_refs=[
            item.item_ref for item in lane_items_by_id["stale_or_deferred"]
        ],
        evidence_refs=_unique_refs(
            [
                "evidence-ref:founder-loop:today-summary",
                *[ref for item in deduped for ref in item.evidence_refs],
            ]
        )[:20],
    )
    return read_model.model_dump(mode="json")


def _digest_item(
    *,
    item_ref: str,
    lane_id: TodayLoopLaneId,
    surface: str,
    title: str,
    state_label: str,
    status: str,
    priority: str,
    safe_summary: str,
    reason: str,
    source_refs: list[str],
    evidence_refs: list[str],
    receipt_refs: list[str],
    blocked_state_refs: list[str],
    next_safe_action: str,
    stale_state: Any | None = None,
) -> TodayLoopDigestItem:
    return TodayLoopDigestItem(
        item_ref=item_ref,
        lane_id=lane_id,
        surface=surface,
        title=title,
        state_label=state_label,
        status=status,
        priority=priority,
        safe_summary=safe_summary,
        reason=reason,
        source_refs=_unique_refs(source_refs),
        evidence_refs=_unique_refs(evidence_refs),
        receipt_refs=_unique_refs(receipt_refs),
        blocked_state_refs=_unique_refs(
            [*blocked_state_refs, *TODAY_LOOP_REQUIRED_BLOCKED_REFS]
        )[:12],
        stale_state=_safe_text_or_none(stale_state),
        next_safe_action=next_safe_action,
        authority_boundary=(
            "Today digest row is review-only safe-ref posture; it does not "
            "authorize action execution, connector runtime, provider calls, "
            "memory writes, context injection, or production authority."
        ),
    )


def _stale_item(
    *,
    source_ref: str,
    surface: str,
    title: str,
    status: Any,
    source_refs: list[str],
    evidence_refs: list[str],
    receipt_refs: list[str],
    blocked_state_refs: list[str],
    next_safe_action: str,
) -> TodayLoopDigestItem:
    return _digest_item(
        item_ref=_derived_ref("today-loop-stale", source_ref),
        lane_id="stale_or_deferred",
        surface=surface,
        title=title,
        state_label="Stale or deferred",
        status=_safe_text_or_default(status, "recheck_required"),
        priority="medium",
        safe_summary="This local ref needs freshness review before use.",
        reason="Stale or deferred posture is visible before any deeper review.",
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        receipt_refs=receipt_refs,
        blocked_state_refs=blocked_state_refs
        or ["blocked-state:today-loop-stale-recheck-required"],
        stale_state=status,
        next_safe_action=next_safe_action,
    )


def _is_reviewable_action(action: dict[str, Any]) -> bool:
    status = str(action.get("status", "")).lower()
    readiness = str(action.get("state_change_readiness", "")).lower()
    return (
        status in {"review_ready", "proposed", "approved"}
        or bool(action.get("approval_required"))
        or "review" in readiness
    )


def _is_blocked(item: dict[str, Any]) -> bool:
    status_text = " ".join(
        str(item.get(key, ""))
        for key in [
            "status",
            "blocked_state",
            "state_change_readiness",
            "approval_envelope_status",
            "local_task_commit_approval_status",
            "cost_state_label",
            "provider_authority_state_label",
        ]
    ).lower()
    return any(token in status_text for token in ["blocked", "missing", "no authority"])


def _has_cost_blocker(item: dict[str, Any]) -> bool:
    status_text = " ".join(
        str(item.get(key, ""))
        for key in [
            "cost_state_label",
            "provider_authority_state_label",
            "cost_blocked_state_refs",
        ]
    ).lower()
    return "cost" in status_text or "provider" in status_text


def _generated_action_blockers(action: dict[str, Any]) -> list[str]:
    refs = [
        "blocked-state:today-loop-action-execution-blocked",
        "blocked-state:today-loop-approval-scope-required",
    ]
    if action.get("blocked_state"):
        refs.append(
            _derived_ref("blocked-state:today-loop-action", str(action["item_ref"]))
        )
    for ref in _safe_refs(action.get("cost_blocked_state_refs", [])):
        refs.append(ref)
    for ref in _safe_refs(action.get("local_task_commit_blocked_reasons", [])):
        refs.append(_derived_ref("blocked-state:today-loop-local-task", ref))
    return _unique_refs(refs)


def _memory_blockers(item: dict[str, Any]) -> list[str]:
    refs = [
        _derived_ref("blocked-state:today-loop-memory", str(value))
        for value in item.get("blocked_states", [])
    ]
    if not refs:
        refs = [
            "blocked-state:today-loop-memory-recall-not-truth",
            "blocked-state:today-loop-no-context-injection",
        ]
    return _unique_refs(refs)


def _lane_next_safe_action(lane_id: str) -> str:
    return {
        "needs_review": "Review exact scope, evidence, and receipt posture before recording any supported decision.",
        "blocked_now": "Inspect blockers and keep unavailable authority disabled.",
        "changed": "Inspect receipts and evidence refs before carrying changes forward.",
        "follow_up": "Review relationship and memory refs before drafting any follow-up action.",
        "stale_or_deferred": "Recheck source freshness before relying on these refs.",
    }[lane_id]


def _dedupe_items(items: list[TodayLoopDigestItem]) -> list[TodayLoopDigestItem]:
    seen: set[tuple[str, str]] = set()
    deduped: list[TodayLoopDigestItem] = []
    for item in items:
        key = (item.lane_id, item.item_ref)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _safe_ref_or_none(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        _validate_safe_ref(value, "ref")
    except ValueError:
        return None
    return value


def _safe_refs(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        candidates = [values]
    else:
        candidates = [str(value) for value in values if value is not None]
    return _unique_refs(ref for ref in candidates if _safe_ref_or_none(ref))


def _unique_refs(values: Any) -> list[str]:
    refs: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        if value and value not in refs:
            refs.append(value)
    return refs


def _safe_text_or_default(value: Any, default: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return default
    candidate = value.strip()
    try:
        _validate_safe_text(candidate, "text")
    except ValueError:
        return default
    return candidate


def _safe_text_or_none(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return _safe_text_or_default(value, "recheck_required")


def _derived_ref(prefix: str, value: str) -> str:
    try:
        _validate_safe_text(value, "ref_suffix")
    except ValueError:
        value = "redacted"
    suffix = _SAFE_SUFFIX_CHARS.sub("-", value.lower()).strip("-")
    return f"{prefix}:{suffix or 'missing'}"


def _validate_safe_ref(value: str, field_name: str) -> None:
    validate_execution_ref(value, field_name)


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe raw/private content")
    validate_safe_execution_text(value, field_name)


__all__ = [
    "TODAY_LOOP_LANE_ORDER",
    "TODAY_LOOP_READ_MODEL_SOURCE",
    "TODAY_LOOP_REQUIRED_BLOCKED_REFS",
    "TODAY_LOOP_TIGHTENING_CONTRACT_REF",
    "TodayLoopDigestItem",
    "TodayLoopLane",
    "TodayLoopReadModel",
    "build_today_loop_read_model",
]
