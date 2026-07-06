from __future__ import annotations

import hashlib
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


ACTION_INBOX_WORK_QUEUE_CONTRACT_REF = (
    "contract-ref:usable-authority-action-inbox-work-queue:v1"
)
ACTION_INBOX_WORK_QUEUE_SOURCE = "python_core_action_inbox_work_queue_read_model"
ACTION_INBOX_WORK_QUEUE_CLI_REF = (
    "python scripts/dev/uaa_founder_loop.py inspect-action-work-queue"
)
ACTION_INBOX_WORK_QUEUE_ROUTE_REF = "GET /control-center/actions/inbox"
ACTION_INBOX_WORK_QUEUE_PROOF_ROUTE_REF = "GET /control-center/proof/{proof_ref}"
ACTION_INBOX_WORK_QUEUE_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-state:action-inbox-work-queue:no-broad-action-execution",
    "blocked-state:action-inbox-work-queue:no-connector-write-or-send",
    "blocked-state:action-inbox-work-queue:no-provider-model-call",
    "blocked-state:action-inbox-work-queue:no-shell-subprocess-execution",
    "blocked-state:action-inbox-work-queue:no-browser-execution",
    "blocked-state:action-inbox-work-queue:no-memory-write",
    "blocked-state:action-inbox-work-queue:no-context-injection",
    "blocked-state:action-inbox-work-queue:no-background-autonomy",
    "blocked-state:action-inbox-work-queue:no-production-authority",
)
ACTION_INBOX_WORK_QUEUE_UNSAFE_REF_OMITTED_REF = (
    "blocked-state:action-inbox-work-queue:unsafe-ref-omitted"
)

_NEXT_ITEM_GROUP_ORDER = (
    "approved_local_task_lane",
    "ready_for_decision",
    "proposal_only_no_execution_path",
    "blocked_by_authority",
    "expired_stale",
    "receipt_recorded",
)
_PROOF_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_-]+")
_DENIED_FLAGS = (
    "action_execution_enabled",
    "connector_write_enabled",
    "connector_send_enabled",
    "provider_model_call_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "memory_write_enabled",
    "context_injection_authorized",
    "background_autonomy_enabled",
    "production_authority_enabled",
)


class ActionInboxWorkQueueLane(BaseModel):
    lane_id: str = Field(..., min_length=1, max_length=120)
    lane_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    available_action: str = Field(..., min_length=1, max_length=300)
    count: int = Field(ge=0)
    item_refs: list[str] = Field(default_factory=list)
    tier: str = "tier_1_local_read_preview"
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "ActionInboxWorkQueueLane":
        for field_name in ("lane_id", "label", "status", "safe_summary", "available_action", "tier"):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        validate_execution_ref(self.lane_ref, "lane_ref")
        _validate_ref_list(self.item_refs, "item_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        return self


class ActionInboxWorkQueueNextItem(BaseModel):
    item_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=160)
    lane_id: str = Field(..., min_length=1, max_length=120)
    lane_label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=120)
    priority: str = Field(..., min_length=1, max_length=80)
    risk_class: str = Field(..., min_length=1, max_length=80)
    action_kind: str = Field(..., min_length=1, max_length=120)
    available_action: str = Field(..., min_length=1, max_length=300)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    approval_required: bool
    approval_envelope_ref: str | None = None
    exact_scope_ref: str | None = None
    idempotency_ref: str | None = None
    expiry_or_staleness: str = "unknown; recheck_required_before_mutation"
    expected_receipt_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    proof_ref: str = Field(..., min_length=1)
    local_task_commit_eligible: bool = False
    local_task_commit_route_ref: str | None = None
    rollback_ref: str | None = None
    safe_disable_ref: str | None = None
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_next_item(self) -> "ActionInboxWorkQueueNextItem":
        validate_execution_ref(self.item_ref, "item_ref")
        validate_execution_ref(self.proof_ref, "proof_ref")
        for field_name in (
            "title",
            "lane_id",
            "lane_label",
            "status",
            "priority",
            "risk_class",
            "action_kind",
            "available_action",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "approval_envelope_ref",
            "exact_scope_ref",
            "idempotency_ref",
            "rollback_ref",
            "safe_disable_ref",
        ):
            value = getattr(self, field_name)
            if value:
                validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.expiry_or_staleness, "expiry_or_staleness")
        if self.local_task_commit_route_ref:
            validate_safe_execution_text(
                self.local_task_commit_route_ref, "local_task_commit_route_ref"
            )
        for field_name in (
            "expected_receipt_refs",
            "receipt_refs",
            "evidence_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


class ActionInboxWorkQueueWorkItem(BaseModel):
    item_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=160)
    lane_id: str = Field(..., min_length=1, max_length=120)
    lane_label: str = Field(..., min_length=1, max_length=120)
    status: str = Field(..., min_length=1, max_length=120)
    priority: str = Field(..., min_length=1, max_length=80)
    risk_class: str = Field(..., min_length=1, max_length=80)
    action_kind: str = Field(..., min_length=1, max_length=120)
    side_effect_class: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    approval_posture: str = Field(..., min_length=1, max_length=160)
    receipt_posture: str = Field(..., min_length=1, max_length=160)
    mutation_control_posture: str = Field(..., min_length=1, max_length=200)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    approval_required: bool
    operator_actionable: bool = False
    local_task_commit_eligible: bool = False
    fake_mutation_control_exposed: bool = False
    approval_envelope_ref: str | None = None
    exact_scope_ref: str | None = None
    idempotency_ref: str | None = None
    expiry_or_staleness: str = "unknown; recheck_required_before_mutation"
    local_task_commit_route_ref: str | None = None
    proof_ref: str = Field(..., min_length=1)
    expected_receipt_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    rollback_ref: str | None = None
    safe_disable_ref: str | None = None
    blocked_authority_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_work_item(self) -> "ActionInboxWorkQueueWorkItem":
        validate_execution_ref(self.item_ref, "item_ref")
        validate_execution_ref(self.proof_ref, "proof_ref")
        for field_name in (
            "title",
            "lane_id",
            "lane_label",
            "status",
            "priority",
            "risk_class",
            "action_kind",
            "side_effect_class",
            "safe_summary",
            "approval_posture",
            "receipt_posture",
            "mutation_control_posture",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "approval_envelope_ref",
            "exact_scope_ref",
            "idempotency_ref",
            "rollback_ref",
            "safe_disable_ref",
        ):
            value = getattr(self, field_name)
            if value:
                validate_execution_ref(value, field_name)
        validate_safe_execution_text(self.expiry_or_staleness, "expiry_or_staleness")
        if self.local_task_commit_route_ref:
            validate_safe_execution_text(
                self.local_task_commit_route_ref, "local_task_commit_route_ref"
            )
        if self.fake_mutation_control_exposed:
            raise ValueError("Action Inbox work item must not expose fake controls")
        for field_name in (
            "expected_receipt_refs",
            "receipt_refs",
            "evidence_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


class ActionInboxWorkQueueReadModel(BaseModel):
    schema_version: str = "action-inbox-work-queue.v1"
    contract_ref: str = ACTION_INBOX_WORK_QUEUE_CONTRACT_REF
    source: str = ACTION_INBOX_WORK_QUEUE_SOURCE
    status: str = "implemented_backend_owned_work_queue_summary"
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    queue_ref: str = "action-work-queue:founder-loop:current"
    route_ref: str = ACTION_INBOX_WORK_QUEUE_ROUTE_REF
    cli_ref: str = ACTION_INBOX_WORK_QUEUE_CLI_REF
    proof_route_ref: str = ACTION_INBOX_WORK_QUEUE_PROOF_ROUTE_REF
    item_count: int = Field(ge=0)
    operator_actionable_count: int = Field(ge=0)
    ready_for_decision_count: int = Field(ge=0)
    approved_local_task_count: int = Field(ge=0)
    proposal_only_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    receipt_recorded_count: int = Field(ge=0)
    lane_count: int = Field(ge=0)
    lanes: list[ActionInboxWorkQueueLane] = Field(default_factory=list)
    work_item_count: int = Field(ge=0)
    work_item_refs: list[str] = Field(default_factory=list)
    work_items: list[ActionInboxWorkQueueWorkItem] = Field(default_factory=list)
    next_item: ActionInboxWorkQueueNextItem | None = None
    next_item_ref: str | None = None
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    operator_summary: str = Field(..., min_length=1, max_length=700)
    tier_posture: str = "tier_1_read_preview_with_tier_3_exact_local_task_commit_lane"
    mutating_controls_posture: str = (
        "decision_receipts_and_exact_local_task_commit_only"
    )
    tier_3_exact_local_task_commit_available: bool = False
    fake_mutation_controls_exposed: bool = False
    unsafe_ref_omitted_count: int = Field(default=0, ge=0)
    unsafe_ref_blocked_state_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    provider_model_call_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_authorized: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "ActionInboxWorkQueueReadModel":
        if self.schema_version != "action-inbox-work-queue.v1":
            raise ValueError("Action Inbox work queue schema drift")
        if self.contract_ref != ACTION_INBOX_WORK_QUEUE_CONTRACT_REF:
            raise ValueError("Action Inbox work queue contract drift")
        if self.source != ACTION_INBOX_WORK_QUEUE_SOURCE:
            raise ValueError("Action Inbox work queue source drift")
        if self.lane_count != len(self.lanes):
            raise ValueError("Action Inbox work queue lane count drift")
        if self.work_item_count != len(self.work_items):
            raise ValueError("Action Inbox work queue item count drift")
        if self.work_item_refs != [item.item_ref for item in self.work_items]:
            raise ValueError("Action Inbox work queue item ref drift")
        if self.next_item_ref != (self.next_item.item_ref if self.next_item else None):
            raise ValueError("Action Inbox work queue next item ref drift")
        validate_execution_ref(self.queue_ref, "queue_ref")
        for field_name in (
            "status",
            "route_ref",
            "cli_ref",
            "proof_route_ref",
            "next_safe_action",
            "operator_summary",
            "tier_posture",
            "mutating_controls_posture",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        if self.next_item_ref:
            validate_execution_ref(self.next_item_ref, "next_item_ref")
        _validate_ref_list(self.work_item_refs, "work_item_refs")
        _validate_ref_list(
            self.unsafe_ref_blocked_state_refs, "unsafe_ref_blocked_state_refs"
        )
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        if not self.backend_owned or not self.local_read_model_only:
            raise ValueError("Action Inbox work queue must stay backend-owned")
        if not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Action Inbox work queue must stay safe-ref only")
        if self.fake_mutation_controls_exposed:
            raise ValueError("Action Inbox work queue must not expose fake controls")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag):
                raise ValueError(f"Action Inbox work queue must not enable {flag}")
        return self


def build_action_inbox_work_queue_read_model(
    *,
    actions: list[dict[str, Any]],
    action_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    lane_by_id = {str(group.get("group_id")): group for group in action_groups}
    lanes = [
        _lane_model(group=lane_by_id[group_id], actions=actions)
        for group_id in lane_by_id
    ]
    work_items = [_work_item_model(action) for action in _actions_for_work_items(actions)]
    next_item = _next_item_model(actions)
    counts = _counts(actions)
    unsafe_ref_count = _unsafe_ref_omitted_count(actions)
    unsafe_ref_blockers = (
        [ACTION_INBOX_WORK_QUEUE_UNSAFE_REF_OMITTED_REF]
        if unsafe_ref_count
        else []
    )
    model = ActionInboxWorkQueueReadModel(
        item_count=len(actions),
        operator_actionable_count=counts["ready_for_decision"]
        + counts["approved_local_task_lane"],
        ready_for_decision_count=counts["ready_for_decision"],
        approved_local_task_count=counts["approved_local_task_lane"],
        proposal_only_count=counts["proposal_only_no_execution_path"],
        blocked_count=counts["blocked_by_authority"],
        receipt_recorded_count=counts["receipt_recorded"],
        lane_count=len(lanes),
        lanes=lanes,
        work_item_count=len(work_items),
        work_item_refs=[item.item_ref for item in work_items],
        work_items=work_items,
        next_item=next_item,
        next_item_ref=next_item.item_ref if next_item else None,
        next_safe_action=_next_safe_action(next_item),
        operator_summary=_operator_summary(counts=counts, item_count=len(actions)),
        tier_3_exact_local_task_commit_available=(
            counts["approved_local_task_lane"] > 0
        ),
        unsafe_ref_omitted_count=unsafe_ref_count,
        unsafe_ref_blocked_state_refs=unsafe_ref_blockers,
        blocked_authority_refs=[
            *unsafe_ref_blockers,
            *list(ACTION_INBOX_WORK_QUEUE_BLOCKED_AUTHORITY_REFS),
        ],
    )
    return model.model_dump(mode="json")


def _lane_model(
    *,
    group: dict[str, Any],
    actions: list[dict[str, Any]],
) -> ActionInboxWorkQueueLane:
    group_id = str(group.get("group_id") or "proposal_only_no_execution_path")
    lane_items = [
        action
        for action in actions
        if str(action.get("action_group_id") or "proposal_only_no_execution_path")
        == group_id
    ]
    return ActionInboxWorkQueueLane(
        lane_id=group_id,
        lane_ref=f"action-work-queue-lane:{group_id.replace('_', '-')}",
        label=str(group.get("label") or group_id.replace("_", " ")),
        status=_lane_status(group_id=group_id, count=len(lane_items)),
        safe_summary=str(
            group.get("safe_summary")
            or "Backend-owned Action Inbox lane with safe refs only."
        ),
        available_action=str(
            group.get("available_action") or "Inspect safe refs only."
        ),
        count=len(lane_items),
        item_refs=_refs(action.get("item_ref") for action in lane_items[:8]),
        blocked_authority_refs=list(ACTION_INBOX_WORK_QUEUE_BLOCKED_AUTHORITY_REFS),
    )


def _next_item_model(
    actions: list[dict[str, Any]],
) -> ActionInboxWorkQueueNextItem | None:
    action = _next_action(actions)
    if action is None:
        return None
    item_ref = str(action.get("item_ref") or "founder-action:missing")
    expected_receipts = _refs(
        [
            *_list(action.get("action_expected_receipt_refs")),
            *_list(action.get("receipt_refs")),
        ]
    )
    receipt_refs = _refs(action.get("receipt_refs"))
    proof_ref = _proof_ref_for_item(
        str(action.get("action_envelope_ref") or item_ref)
    )
    return ActionInboxWorkQueueNextItem(
        item_ref=item_ref,
        title=str(action.get("title") or "Action Inbox item"),
        lane_id=str(action.get("action_group_id") or "proposal_only_no_execution_path"),
        lane_label=str(action.get("action_group_label") or "Action Inbox lane"),
        status=str(action.get("status") or "review_ready"),
        priority=str(action.get("priority") or "normal"),
        risk_class=str(action.get("risk_class") or "medium"),
        action_kind=str(action.get("action_kind") or "review_only"),
        available_action=str(
            action.get("action_group_available_action")
            or "Inspect the backend-owned queue item."
        ),
        next_safe_action=str(
            action.get("local_task_commit_next_safe_action")
            or action.get("next_safe_action")
            or "Review safe refs before any decision."
        ),
        approval_required=bool(action.get("approval_required", True)),
        approval_envelope_ref=_optional_ref(action.get("approval_envelope_ref")),
        exact_scope_ref=_optional_ref(action.get("action_scope_ref")),
        idempotency_ref=_optional_ref(_idempotency_ref(action)),
        expiry_or_staleness=_expiry_or_staleness(action),
        expected_receipt_refs=expected_receipts,
        receipt_refs=receipt_refs,
        evidence_refs=_refs(action.get("evidence_refs")),
        proof_ref=proof_ref,
        local_task_commit_eligible=bool(action.get("local_task_commit_eligible")),
        local_task_commit_route_ref=_optional_safe_text(
            action.get("local_task_commit_route_ref")
        ),
        rollback_ref=_optional_ref(action.get("rollback_ref")),
        safe_disable_ref=_optional_ref(action.get("safe_disable_ref")),
        blocked_authority_refs=_merge_refs(
            action.get("action_blocked_state_refs"),
            action.get("local_task_commit_external_authority_blocked_refs"),
            ACTION_INBOX_WORK_QUEUE_BLOCKED_AUTHORITY_REFS,
        ),
    )


def _work_item_model(action: dict[str, Any]) -> ActionInboxWorkQueueWorkItem:
    item_ref = str(action.get("item_ref") or "founder-action:missing")
    expected_receipts = _refs(
        [
            *_list(action.get("action_expected_receipt_refs")),
            *_list(action.get("receipt_refs")),
        ]
    )
    receipt_refs = _refs(action.get("receipt_refs"))
    lane_id = str(action.get("action_group_id") or "proposal_only_no_execution_path")
    local_task_commit_eligible = bool(action.get("local_task_commit_eligible"))
    operator_actionable = lane_id in {
        "approved_local_task_lane",
        "ready_for_decision",
    }
    return ActionInboxWorkQueueWorkItem(
        item_ref=item_ref,
        title=str(action.get("title") or "Action Inbox item"),
        lane_id=lane_id,
        lane_label=str(action.get("action_group_label") or "Action Inbox lane"),
        status=str(action.get("status") or "review_ready"),
        priority=str(action.get("priority") or "normal"),
        risk_class=str(action.get("risk_class") or "medium"),
        action_kind=str(action.get("action_kind") or "review_only"),
        side_effect_class=str(action.get("side_effect_class") or "validation_only"),
        safe_summary=str(
            action.get("safe_summary")
            or "Backend-owned Action Inbox item with safe refs only."
        ),
        approval_posture=str(
            action.get("local_task_commit_approval_status")
            or action.get("approval_envelope_status")
            or "approval_posture_missing"
        ),
        receipt_posture=_receipt_posture(
            expected_receipts=expected_receipts,
            receipt_refs=receipt_refs,
        ),
        mutation_control_posture=_mutation_control_posture(
            lane_id=lane_id,
            local_task_commit_eligible=local_task_commit_eligible,
        ),
        next_safe_action=str(
            action.get("local_task_commit_next_safe_action")
            or action.get("next_safe_action")
            or "Inspect safe refs before any decision."
        ),
        approval_required=bool(action.get("approval_required", True)),
        operator_actionable=operator_actionable,
        local_task_commit_eligible=local_task_commit_eligible,
        approval_envelope_ref=_optional_ref(action.get("approval_envelope_ref")),
        exact_scope_ref=_optional_ref(action.get("action_scope_ref")),
        idempotency_ref=_optional_ref(_idempotency_ref(action)),
        expiry_or_staleness=_expiry_or_staleness(action),
        local_task_commit_route_ref=_optional_safe_text(
            action.get("local_task_commit_route_ref")
        ),
        proof_ref=_proof_ref_for_action(action),
        expected_receipt_refs=expected_receipts,
        receipt_refs=receipt_refs,
        evidence_refs=_refs(action.get("evidence_refs")),
        rollback_ref=_optional_ref(action.get("rollback_ref")),
        safe_disable_ref=_optional_ref(action.get("safe_disable_ref")),
        blocked_authority_refs=_merge_refs(
            action.get("action_blocked_state_refs"),
            action.get("local_task_commit_external_authority_blocked_refs"),
            ACTION_INBOX_WORK_QUEUE_BLOCKED_AUTHORITY_REFS,
        ),
    )


def _next_action(actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    for group_id in _NEXT_ITEM_GROUP_ORDER:
        for action in actions:
            if str(action.get("action_group_id") or "") == group_id:
                return action
    return actions[0] if actions else None


def _ordered_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {group_id: index for index, group_id in enumerate(_NEXT_ITEM_GROUP_ORDER)}
    return sorted(
        actions,
        key=lambda action: (
            order.get(str(action.get("action_group_id") or ""), len(order)),
            str(action.get("item_ref") or ""),
        ),
    )


def _actions_for_work_items(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = list(actions[:6])
    next_action = _next_action(actions)
    if next_action is not None and all(
        str(action.get("item_ref") or "") != str(next_action.get("item_ref") or "")
        for action in selected
    ):
        selected.append(next_action)
    return _ordered_actions(selected)


def _counts(actions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {group_id: 0 for group_id in _NEXT_ITEM_GROUP_ORDER}
    for action in actions:
        group_id = str(action.get("action_group_id") or "proposal_only_no_execution_path")
        counts[group_id] = counts.get(group_id, 0) + 1
    return counts


def _next_safe_action(next_item: ActionInboxWorkQueueNextItem | None) -> str:
    if next_item is None:
        return "No Action Inbox items need operator review right now."
    if next_item.local_task_commit_eligible:
        return "Commit the exact approved local task lane or inspect its proof refs."
    if next_item.approval_required:
        return "Review the next item scope, receipts, evidence, and proof before recording a decision."
    return "Review the next proposal without sending, executing, or applying it."


def _operator_summary(*, counts: dict[str, int], item_count: int) -> str:
    return (
        f"{item_count} Action Inbox items are grouped by backend-owned queue "
        f"posture: {counts['ready_for_decision']} ready for decision, "
        f"{counts['approved_local_task_lane']} exact local task commits, "
        f"{counts['proposal_only_no_execution_path']} proposals, and "
        f"{counts['blocked_by_authority']} blocked by authority."
    )


def _receipt_posture(
    *,
    expected_receipts: list[str],
    receipt_refs: list[str],
) -> str:
    if receipt_refs:
        return "receipt_refs_recorded"
    if expected_receipts:
        return "expected_receipt_refs_visible"
    return "expected_receipt_refs_missing"


def _mutation_control_posture(
    *,
    lane_id: str,
    local_task_commit_eligible: bool,
) -> str:
    if local_task_commit_eligible:
        return "exact_local_task_commit_route_only"
    if lane_id == "ready_for_decision":
        return "decision_receipt_only_no_execution"
    return "no_mutation_control_exposed"


def _idempotency_ref(action: dict[str, Any]) -> Any:
    return action.get("idempotency_key_ref") or action.get("action_idempotency_key_ref")


def _expiry_or_staleness(action: dict[str, Any]) -> str:
    expires_at = _optional_safe_text(
        action.get("expires_at") or action.get("action_expires_at")
    )
    stale_state = _optional_safe_text(
        action.get("stale_state") or action.get("action_stale_state")
    )
    return (
        f"{expires_at or 'unknown'}; "
        f"{stale_state or 'recheck_required_before_mutation'}"
    )


def _unsafe_ref_omitted_count(actions: list[dict[str, Any]]) -> int:
    count = 0
    list_fields = (
        "action_expected_receipt_refs",
        "receipt_refs",
        "evidence_refs",
        "action_blocked_state_refs",
        "local_task_commit_external_authority_blocked_refs",
        "proof_refs",
        "audit_refs",
    )
    scalar_fields = (
        "item_ref",
        "action_envelope_ref",
        "approval_envelope_ref",
        "action_scope_ref",
        "idempotency_key_ref",
        "action_idempotency_key_ref",
        "rollback_ref",
        "safe_disable_ref",
    )
    for action in actions:
        for field_name in list_fields:
            values = action.get(field_name)
            if not isinstance(values, list | tuple | set):
                continue
            for value in values:
                if isinstance(value, str) and not _is_valid_ref(value):
                    count += 1
        for field_name in scalar_fields:
            value = action.get(field_name)
            if isinstance(value, str) and not _is_valid_ref(value):
                count += 1
    return count


def _lane_status(*, group_id: str, count: int) -> str:
    if count == 0:
        return "empty"
    if group_id == "approved_local_task_lane":
        return "exact_local_task_commit_available"
    if group_id == "ready_for_decision":
        return "decision_receipt_available"
    if group_id == "proposal_only_no_execution_path":
        return "proposal_review_available"
    if group_id == "blocked_by_authority":
        return "blocked_authority_visible"
    if group_id == "receipt_recorded":
        return "receipt_review_available"
    return "review_available"


def _proof_ref_for_action(action: dict[str, Any]) -> str:
    proof_refs = _refs(action.get("proof_refs"))
    if proof_refs:
        return proof_refs[0]
    return _proof_ref_for_item(
        str(action.get("action_envelope_ref") or action.get("item_ref") or "missing")
    )


def _proof_ref_for_item(item_ref: str) -> str:
    slug = _PROOF_SAFE_SUFFIX_RE.sub("-", item_ref.lower()).strip("-")[:80]
    candidate = f"proof-ref:action-decision:{slug or 'missing'}"
    try:
        validate_execution_ref(candidate, "proof_ref")
        return candidate
    except ValueError:
        digest = hashlib.sha256(item_ref.encode("utf-8")).hexdigest()[:24]
        proof_ref = f"proof-ref:action-decision:sha256:{digest}"
        validate_execution_ref(proof_ref, "proof_ref")
        return proof_ref


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _optional_ref(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        validate_execution_ref(value, "ref")
    except ValueError:
        return None
    return value


def _optional_safe_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        validate_safe_execution_text(value, "safe_text")
    except ValueError:
        return None
    return value


def _is_valid_ref(value: str) -> bool:
    try:
        validate_execution_ref(value, "ref")
    except ValueError:
        return False
    return True


def _refs(values: Any) -> list[str]:
    result: list[str] = []
    if isinstance(values, list | tuple | set):
        iterable = values
    elif hasattr(values, "__iter__") and not isinstance(values, str | bytes | dict):
        iterable = list(values)
    else:
        iterable = []
    for value in iterable:
        if not isinstance(value, str) or not value:
            continue
        try:
            validate_execution_ref(value, "ref")
        except ValueError:
            continue
        if value not in result:
            result.append(value)
    return result


def _merge_refs(*groups: Any) -> list[str]:
    refs: list[str] = []
    for group in groups:
        refs.extend(_refs(group if isinstance(group, list | tuple | set) else _list(group)))
    for ref in ACTION_INBOX_WORK_QUEUE_BLOCKED_AUTHORITY_REFS:
        if ref not in refs:
            refs.append(ref)
    return refs


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        validate_execution_ref(ref, field_name)
