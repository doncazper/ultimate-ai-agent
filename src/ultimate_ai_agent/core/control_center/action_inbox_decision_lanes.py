from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ACTION_INBOX_DECISION_LANE_CONTRACT_REF = (
    "contract-ref:product-loop-005-action-inbox-decision-lanes:v1"
)
ACTION_INBOX_DECISION_LANE_READ_MODEL_SOURCE = (
    "python_core_action_inbox_decision_lane_read_model"
)
ACTION_INBOX_DECISION_LANE_ORDER: tuple[str, ...] = (
    "needs_approval",
    "blocked",
    "draft_only",
    "cost_blocked",
    "no_authority",
    "approved_no_execution",
    "rejected",
    "deferred",
    "receipt_recorded",
)
ACTION_INBOX_DECISION_LANE_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:action-inbox-approval-alone-does-not-execute",
    "blocked-state:action-inbox-exact-scope-required",
    "blocked-state:action-inbox-no-action-execution",
    "blocked-state:action-inbox-no-connector-write",
    "blocked-state:action-inbox-no-shell-subprocess-execution",
    "blocked-state:action-inbox-no-browser-execution",
    "blocked-state:action-inbox-no-provider-model-call",
    "blocked-state:action-inbox-no-memory-write",
    "blocked-state:action-inbox-no-context-injection",
    "blocked-state:action-inbox-no-production-authority",
    "blocked-state:action-inbox-cost-telemetry-required-for-frontier-usage",
    "blocked-state:action-inbox-safe-refs-only",
)

ActionInboxDecisionLaneId = Literal[
    "needs_approval",
    "blocked",
    "draft_only",
    "cost_blocked",
    "no_authority",
    "approved_no_execution",
    "rejected",
    "deferred",
    "receipt_recorded",
]

_LANE_DEFINITIONS: dict[str, dict[str, str]] = {
    "needs_approval": {
        "label": "Needs approval",
        "safe_summary": (
            "Items that can record a review decision receipt only after exact "
            "scope, expected receipt, cost, and authority posture are visible."
        ),
        "status": "reviewable_decision_receipt_only",
        "next_safe_action": "Review scope, cost, evidence, and expected receipt refs.",
    },
    "blocked": {
        "label": "Blocked",
        "safe_summary": (
            "Items blocked by missing envelope fields, stale state, policy, or "
            "unsupported authority posture."
        ),
        "status": "blocked_fail_closed",
        "next_safe_action": "Resolve missing refs or keep the item blocked.",
    },
    "draft_only": {
        "label": "Draft-only",
        "safe_summary": (
            "Review-only proposal items with no validated execution or mutation "
            "path."
        ),
        "status": "proposal_only_no_execution",
        "next_safe_action": "Inspect proposal refs only.",
    },
    "cost_blocked": {
        "label": "Cost blocked",
        "safe_summary": (
            "Items whose cost posture is unknown, over budget, missing receipts, "
            "or otherwise approval-bound."
        ),
        "status": "cost_blocked_or_unknown_paid_cost",
        "next_safe_action": "Resolve cost estimate, budget decision, and receipt refs.",
    },
    "no_authority": {
        "label": "No authority",
        "safe_summary": (
            "Items missing provider/model or runtime authority scope. Visibility "
            "does not make them callable."
        ),
        "status": "authority_missing",
        "next_safe_action": "Keep blocked until exact authority scope exists.",
    },
    "approved_no_execution": {
        "label": "Approved / no execution",
        "safe_summary": (
            "Items with approval posture or decision receipts where approval "
            "still does not execute work."
        ),
        "status": "approved_receipt_no_execution",
        "next_safe_action": "Inspect receipt refs; use only separately scoped commit lanes.",
    },
    "rejected": {
        "label": "Rejected",
        "safe_summary": "Items with rejected decision posture or receipts.",
        "status": "rejected_receipt_recorded",
        "next_safe_action": "Inspect rejection receipt refs.",
    },
    "deferred": {
        "label": "Deferred",
        "safe_summary": "Items deferred, expired, stale, or awaiting later review.",
        "status": "deferred_or_stale",
        "next_safe_action": "Recheck staleness and source refs before review.",
    },
    "receipt_recorded": {
        "label": "Receipt recorded",
        "safe_summary": "Items with completed decision, commit, or evidence receipts.",
        "status": "receipt_recorded",
        "next_safe_action": "Inspect receipt and evidence refs.",
    },
}

_SAFE_REF_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9:_./@#=-]{0,239}$")
_UNSAFE_TEXT_FRAGMENTS = (
    "raw_prompt",
    "raw prompt",
    "raw_response",
    "raw response",
    "raw_log",
    "raw log",
    "raw path",
    "raw_path",
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
_DENIED_ITEM_FLAGS = (
    "approval_alone_executes",
    "approval_ref_authority",
    "approval_grants_runtime_authority",
    "action_execution_enabled",
    "connector_write_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "provider_model_call_enabled",
    "memory_write_enabled",
    "context_injection_authorized",
    "hidden_memory_write_authorized",
    "production_authority_enabled",
)
_DENIED_READ_MODEL_FLAGS = (
    "action_execution_enabled",
    "connector_write_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "provider_model_call_enabled",
    "memory_write_enabled",
    "context_injection_authorized",
    "hidden_memory_write_authorized",
    "production_authority_enabled",
    "approval_alone_executes",
)


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe/private content")


def _validate_safe_ref(value: str, field_name: str) -> None:
    _validate_safe_text(value, field_name)
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe ref")


def _safe_text_or_default(value: object, default: str, *, max_length: int = 500) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        return default
    try:
        _validate_safe_text(candidate, "safe_text")
    except ValueError:
        return default
    return candidate[:max_length]


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


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _envelope(action: dict[str, Any]) -> dict[str, Any]:
    value = action.get("approval_envelope")
    return value if isinstance(value, dict) else {}


def _first_safe_ref(*values: object) -> str | None:
    for value in values:
        ref = _safe_ref_or_none(value)
        if ref:
            return ref
    return None


def _expected_receipt_refs(action: dict[str, Any], envelope: dict[str, Any]) -> list[str]:
    refs = _safe_refs(action.get("action_expected_receipt_refs"))
    if not refs:
        refs = _safe_refs(envelope.get("expected_receipt_refs"))
    if not refs:
        refs = _safe_refs(action.get("receipt_refs"))
    return refs or ["missing"]


def _field_missing(ref: str | None) -> bool:
    return ref is None or ref in {"missing", "unknown", "planned", "not_applicable"}


def _missing_envelope_field_states(
    action: dict[str, Any],
    envelope: dict[str, Any],
    *,
    expected_receipts: list[str],
) -> list[str]:
    approval_required = bool(action.get("approval_required", True))
    if not approval_required:
        return []
    states: list[str] = []
    if not envelope:
        states.append("approval_envelope:missing")
    fields = {
        "approval_envelope_ref": _first_safe_ref(action.get("approval_envelope_ref")),
        "approval_scope_ref": _first_safe_ref(
            action.get("action_scope_ref"),
            envelope.get("exact_scope"),
        ),
        "approval_requirement_ref": _first_safe_ref(
            action.get("action_approval_requirement_ref"),
            envelope.get("approval_requirement"),
        ),
        "idempotency_ref": _first_safe_ref(
            action.get("action_idempotency_key_ref"),
            action.get("idempotency_key_ref"),
            envelope.get("idempotency_ref"),
        ),
        "rollback_ref": _first_safe_ref(action.get("rollback_ref")),
        "safe_disable_ref": _first_safe_ref(action.get("safe_disable_ref")),
    }
    for field_name, ref in fields.items():
        if _field_missing(ref):
            states.append(f"{field_name}:missing")
    if expected_receipts == ["missing"]:
        states.append("expected_receipt_refs:missing")
    if not _safe_refs(action.get("evidence_refs")) and not _safe_refs(
        envelope.get("evidence_refs")
    ):
        states.append("evidence_refs:missing")
    return states


def _with_required_blockers(*groups: object) -> list[str]:
    refs: list[str] = list(ACTION_INBOX_DECISION_LANE_REQUIRED_BLOCKED_REFS)
    for group in groups:
        refs.extend(_safe_refs(group))
    return list(dict.fromkeys(refs))


def _cost_receipt_refs(action: dict[str, Any], envelope: dict[str, Any]) -> list[str]:
    return _safe_refs(
        action.get("action_envelope_cost_receipt_refs")
        or action.get("cost_receipt_refs")
        or envelope.get("cost_receipt_refs")
    )


def _cost_blocked_refs(action: dict[str, Any], envelope: dict[str, Any]) -> list[str]:
    return _safe_refs(
        action.get("action_envelope_cost_blocked_state_refs")
        or action.get("cost_blocked_state_refs")
        or envelope.get("cost_blocked_state_refs")
    )


def _cost_state_label(action: dict[str, Any], envelope: dict[str, Any]) -> str:
    return _safe_text_or_default(
        action.get("action_envelope_cost_state_label")
        or action.get("cost_state_label")
        or envelope.get("cost_state_label"),
        "Cost blocked",
        max_length=80,
    )


def _provider_authority_state_label(
    action: dict[str, Any],
    envelope: dict[str, Any],
) -> str:
    return _safe_text_or_default(
        action.get("action_envelope_provider_authority_state_label")
        or action.get("provider_authority_state_label")
        or envelope.get("provider_authority_state_label"),
        "No provider authority",
        max_length=120,
    )


def _provider_ref(action: dict[str, Any], envelope: dict[str, Any]) -> str | None:
    return _first_safe_ref(
        action.get("action_envelope_provider_ref"),
        action.get("provider_ref"),
        envelope.get("provider_ref"),
    )


def _model_profile_ref(action: dict[str, Any], envelope: dict[str, Any]) -> str | None:
    return _first_safe_ref(
        action.get("action_envelope_model_profile_ref"),
        action.get("model_profile_ref"),
        envelope.get("model_profile_ref"),
    )


def _is_draft_only(action: dict[str, Any]) -> bool:
    action_kind = str(action.get("action_kind") or "review_only")
    group_id = str(action.get("action_group_id") or "")
    if action.get("approval_required") is False:
        return True
    if action_kind == "review_only":
        return not bool(action.get("state_change_contract_ref"))
    return action_kind in {
        "task_decomposition_proposal",
        "source_readiness_contract_proposal",
        "self_heal_recommendation",
    } or group_id == "proposal_only_no_execution_path"


def _has_receipt_recorded(action: dict[str, Any]) -> bool:
    status = str(action.get("status") or "").lower()
    if status in {"receipt_recorded", "edited"}:
        return True
    if _safe_ref_or_none(action.get("local_task_commit_receipt_ref")):
        return True
    visibility = action.get("receipt_visibility")
    if isinstance(visibility, dict):
        for key in [
            "decision_receipt_ref",
            "local_task_commit_receipt_ref",
            "evidence_timeline_event_ref",
        ]:
            value = str(visibility.get(key) or "")
            if value.startswith(("receipt:", "evidence-event:")):
                return True
    return any(str(ref).startswith("receipt:") for ref in action.get("receipt_refs") or [])


def _is_deferred(action: dict[str, Any]) -> bool:
    status = str(action.get("status") or "").lower()
    stale_state = str(action.get("stale_state") or action.get("action_stale_state") or "")
    return status in {"deferred", "expired", "stale", "superseded"} or any(
        marker in stale_state.lower()
        for marker in ["deferred", "expired", "stale", "superseded", "outdated"]
    )


def _is_cost_blocked(
    action: dict[str, Any],
    envelope: dict[str, Any],
    *,
    cost_blockers: list[str],
) -> bool:
    label = _cost_state_label(action, envelope).lower()
    return (
        label in {"cost blocked", "unknown paid cost"}
        or "blocked" in label
        or "unknown paid cost" in label
        or bool(cost_blockers)
        or bool(action.get("unknown_paid_cost_requires_explicit_approval", False))
        or bool(
            action.get(
                "action_envelope_unknown_paid_cost_requires_explicit_approval",
                False,
            )
        )
    )


def _is_no_authority(
    action: dict[str, Any],
    envelope: dict[str, Any],
    *,
    provider_ref: str | None,
    model_profile_ref: str | None,
) -> bool:
    label = _provider_authority_state_label(action, envelope).lower()
    return (
        "no provider authority" in label
        or "missing" in label
        or provider_ref in {None, "provider-ref:not-invoked"}
        or model_profile_ref in {None, "model-profile-ref:not-invoked"}
    )


def _has_general_blocker(action: dict[str, Any]) -> bool:
    status = str(action.get("status") or "").lower()
    group_id = str(action.get("action_group_id") or "").lower()
    blocked_state = str(action.get("blocked_state") or "").lower()
    readiness = str(action.get("state_change_readiness") or "").lower()
    return (
        status == "blocked"
        or group_id == "blocked_by_authority"
        or "not scoped" in blocked_state
        or "unscoped" in blocked_state
        or readiness.startswith("blocked")
    )


def _classify_decision_lane(
    action: dict[str, Any],
    envelope: dict[str, Any],
    *,
    missing_field_states: list[str],
    cost_blockers: list[str],
    provider_ref: str | None,
    model_profile_ref: str | None,
) -> ActionInboxDecisionLaneId:
    status = str(action.get("status") or "").lower()
    if status == "rejected":
        return "rejected"
    if _is_deferred(action):
        return "deferred"
    if status == "approved":
        return "approved_no_execution"
    if _has_receipt_recorded(action):
        return "receipt_recorded"
    if _is_draft_only(action):
        return "draft_only"
    if missing_field_states or _has_general_blocker(action):
        return "blocked"
    if _is_cost_blocked(action, envelope, cost_blockers=cost_blockers):
        return "cost_blocked"
    if _is_no_authority(
        action,
        envelope,
        provider_ref=provider_ref,
        model_profile_ref=model_profile_ref,
    ):
        return "no_authority"
    if bool(action.get("approval_required", True)):
        return "needs_approval"
    return "draft_only"


class ActionInboxDecisionLaneItem(BaseModel):
    item_ref: str = Field(..., min_length=1, max_length=240)
    lane_id: ActionInboxDecisionLaneId
    lane_label: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=160)
    status: str = Field(..., min_length=1, max_length=120)
    priority: str = Field(default="normal", min_length=1, max_length=80)
    action_kind: str = Field(default="review_only", min_length=1, max_length=120)
    side_effect_class: str = Field(default="local_dev_workspace_only", min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    why_shown: str = Field(..., min_length=1, max_length=500)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    authority_boundary: str = Field(..., min_length=1, max_length=500)
    approval_required: bool = True
    approval_envelope_ref: str | None = Field(default=None, max_length=240)
    approval_envelope_status: str = Field(default="missing", min_length=1, max_length=160)
    approval_scope_ref: str | None = Field(default=None, max_length=240)
    approval_requirement_ref: str | None = Field(default=None, max_length=240)
    expected_receipt_refs: list[str] = Field(default_factory=list)
    expected_receipt_state: str = Field(default="missing", min_length=1, max_length=120)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    expected_receipt_refs_visible: bool = True
    rollback_ref: str | None = Field(default=None, max_length=240)
    safe_disable_ref: str | None = Field(default=None, max_length=240)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    missing_envelope_field_states: list[str] = Field(default_factory=list)
    cost_state_label: str = Field(default="Cost blocked", min_length=1, max_length=80)
    provider_authority_state_label: str = Field(
        default="No provider authority",
        min_length=1,
        max_length=120,
    )
    estimated_cost_usd: float = 0.0
    max_approved_cost_usd: float = 0.0
    provider_ref: str | None = Field(default=None, max_length=240)
    model_profile_ref: str | None = Field(default=None, max_length=240)
    input_metered_units: int = 0
    output_metered_units: int = 0
    total_metered_units: int = 0
    cost_estimate_ref: str | None = Field(default=None, max_length=240)
    captured_usage_ref: str | None = Field(default=None, max_length=240)
    budget_decision_ref: str | None = Field(default=None, max_length=240)
    cost_receipt_refs: list[str] = Field(default_factory=list)
    cost_blocked_state_refs: list[str] = Field(default_factory=list)
    unknown_paid_cost_requires_explicit_approval: bool = True
    frontier_usage_claimed: bool = False
    cost_telemetry_complete: bool = False
    provider_model_refs_present: bool = False
    backend_owned: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    approval_alone_executes: bool = False
    approval_ref_authority: bool = False
    approval_grants_runtime_authority: bool = False
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    provider_model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_authorized: bool = False
    hidden_memory_write_authorized: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_decision_lane_item(self) -> "ActionInboxDecisionLaneItem":
        _validate_safe_ref(self.item_ref, "item_ref")
        for field_name in [
            "approval_envelope_ref",
            "approval_scope_ref",
            "approval_requirement_ref",
            "rollback_ref",
            "safe_disable_ref",
            "provider_ref",
            "model_profile_ref",
            "cost_estimate_ref",
            "captured_usage_ref",
            "budget_decision_ref",
        ]:
            value = getattr(self, field_name)
            if value is not None:
                _validate_safe_ref(value, field_name)
        for field_name in [
            "lane_label",
            "title",
            "status",
            "priority",
            "action_kind",
            "side_effect_class",
            "safe_summary",
            "why_shown",
            "next_safe_action",
            "authority_boundary",
            "approval_envelope_status",
            "expected_receipt_state",
            "cost_state_label",
            "provider_authority_state_label",
        ]:
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in [
            "expected_receipt_refs",
            "evidence_refs",
            "receipt_refs",
            "blocked_authority_refs",
            "missing_envelope_field_states",
            "cost_receipt_refs",
            "cost_blocked_state_refs",
        ]:
            for ref in getattr(self, field_name):
                _validate_safe_ref(ref, field_name)
        if not self.backend_owned or not self.safe_refs_only or self.raw_content_included:
            raise ValueError("decision lane items must be backend-owned safe refs only")
        for field_name in _DENIED_ITEM_FLAGS:
            if bool(getattr(self, field_name)):
                raise ValueError(f"{field_name} must remain false")
        has_missing_envelope_fields = any(
            state != "none" for state in self.missing_envelope_field_states
        )
        if self.approval_required and has_missing_envelope_fields and self.lane_id in {
            "needs_approval",
            "approved_no_execution",
        }:
            raise ValueError("missing envelope fields must fail closed")
        if self.frontier_usage_claimed and not (
            self.cost_estimate_ref
            and self.captured_usage_ref
            and self.budget_decision_ref
            and self.provider_ref
            and self.model_profile_ref
            and self.cost_receipt_refs
        ):
            raise ValueError("frontier usage claims require cost telemetry refs")
        if self.total_metered_units != self.input_metered_units + self.output_metered_units:
            raise ValueError("metered unit total must match input and output units")
        return self


class ActionInboxDecisionLane(BaseModel):
    lane_id: ActionInboxDecisionLaneId
    label: str = Field(..., min_length=1, max_length=80)
    status: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    count: int = Field(default=0, ge=0)
    item_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    approval_alone_executes: bool = False
    action_execution_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "ActionInboxDecisionLane":
        for field_name in ["label", "status", "safe_summary", "next_safe_action"]:
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for ref in self.item_refs:
            _validate_safe_ref(ref, "item_refs")
        for ref in self.blocked_state_refs:
            _validate_safe_ref(ref, "blocked_state_refs")
        if self.approval_alone_executes or self.action_execution_enabled:
            raise ValueError("decision lanes cannot execute actions")
        return self


class ActionInboxDecisionLaneReadModel(BaseModel):
    contract_ref: str = ACTION_INBOX_DECISION_LANE_CONTRACT_REF
    status: str = Field(
        default="backend_owned_decision_lane_read_model",
        min_length=1,
        max_length=120,
    )
    source: str = ACTION_INBOX_DECISION_LANE_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    lane_order: list[ActionInboxDecisionLaneId] = Field(default_factory=list)
    lanes: list[ActionInboxDecisionLane] = Field(default_factory=list)
    items: list[ActionInboxDecisionLaneItem] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    missing_envelope_fields_fail_safe: bool = True
    cost_posture_visible_before_approval: bool = True
    provider_authority_visible_before_approval: bool = True
    approval_scope_visible_before_approval: bool = True
    expected_receipts_visible_before_approval: bool = True
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    provider_model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_authorized: bool = False
    hidden_memory_write_authorized: bool = False
    production_authority_enabled: bool = False
    approval_alone_executes: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "ActionInboxDecisionLaneReadModel":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_text(self.status, "status")
        _validate_safe_text(self.source, "source")
        if (
            not self.backend_owned
            or not self.local_read_model_only
            or not self.safe_refs_only
            or self.raw_content_included
        ):
            raise ValueError("decision lane read model must be local safe refs only")
        for field_name in _DENIED_READ_MODEL_FLAGS:
            if bool(getattr(self, field_name)):
                raise ValueError(f"{field_name} must remain false")
        for ref in self.blocked_state_refs:
            _validate_safe_ref(ref, "blocked_state_refs")
        if list(self.lane_order) != list(ACTION_INBOX_DECISION_LANE_ORDER):
            raise ValueError("decision lane order must remain canonical")
        lane_ids = [lane.lane_id for lane in self.lanes]
        if lane_ids != list(ACTION_INBOX_DECISION_LANE_ORDER):
            raise ValueError("decision lanes must include every canonical lane")
        return self


def _item_from_action(action: dict[str, Any]) -> ActionInboxDecisionLaneItem:
    envelope = _envelope(action)
    expected_receipts = _expected_receipt_refs(action, envelope)
    missing_fields = _missing_envelope_field_states(
        action,
        envelope,
        expected_receipts=expected_receipts,
    )
    cost_blockers = _cost_blocked_refs(action, envelope)
    provider_ref = _provider_ref(action, envelope)
    model_profile_ref = _model_profile_ref(action, envelope)
    lane_id = _classify_decision_lane(
        action,
        envelope,
        missing_field_states=missing_fields,
        cost_blockers=cost_blockers,
        provider_ref=provider_ref,
        model_profile_ref=model_profile_ref,
    )
    definition = _LANE_DEFINITIONS[lane_id]
    evidence_refs = _safe_refs(action.get("evidence_refs")) or _safe_refs(
        envelope.get("evidence_refs")
    )
    receipt_refs = _safe_refs(action.get("receipt_refs"))
    cost_receipts = _cost_receipt_refs(action, envelope)
    blocked_authority_refs = _with_required_blockers(
        action.get("action_blocked_state_refs"),
        action.get("blocked_state_refs"),
        action.get("source_readiness_blocked_authority_refs"),
        action.get("task_decomposition_blocked_authority_refs"),
        action.get("health_recommendation_blocked_authority_refs"),
        action.get("local_task_commit_blocked_reasons"),
        action.get("local_task_commit_external_authority_blocked_refs"),
        envelope.get("blocked_authority_refs"),
        cost_blockers,
        [f"blocked-state:action-inbox-{state.replace(':', '-')}" for state in missing_fields],
    )
    input_units = _as_int(
        action.get("action_envelope_input_metered_units")
        or action.get("input_metered_units")
        or envelope.get("input_metered_units")
    )
    output_units = _as_int(
        action.get("action_envelope_output_metered_units")
        or action.get("output_metered_units")
        or envelope.get("output_metered_units")
    )
    total_units = _as_int(
        action.get("action_envelope_total_metered_units")
        or action.get("total_metered_units")
        or envelope.get("total_metered_units"),
        input_units + output_units,
    )
    cost_estimate_ref = _first_safe_ref(
        action.get("action_envelope_cost_estimate_ref"),
        action.get("cost_estimate_ref"),
        envelope.get("cost_estimate_ref"),
    )
    captured_usage_ref = _first_safe_ref(
        action.get("action_envelope_captured_usage_ref"),
        action.get("captured_usage_ref"),
        envelope.get("captured_usage_ref"),
    )
    budget_decision_ref = _first_safe_ref(
        action.get("action_envelope_budget_decision_ref"),
        action.get("budget_decision_ref"),
        envelope.get("budget_decision_ref"),
    )
    provider_model_refs_present = bool(
        provider_ref
        and model_profile_ref
        and provider_ref != "provider-ref:not-invoked"
        and model_profile_ref != "model-profile-ref:not-invoked"
    )
    cost_telemetry_complete = bool(
        cost_estimate_ref and captured_usage_ref and budget_decision_ref and cost_receipts
    )
    return ActionInboxDecisionLaneItem(
        item_ref=_safe_ref_or_none(action.get("item_ref")) or "founder-action:redacted",
        lane_id=lane_id,
        lane_label=definition["label"],
        title=_safe_text_or_default(action.get("title"), "Action item"),
        status=_safe_text_or_default(action.get("status"), "unknown", max_length=120),
        priority=_safe_text_or_default(action.get("priority"), "normal", max_length=80),
        action_kind=_safe_text_or_default(
            action.get("action_kind"),
            "review_only",
            max_length=120,
        ),
        side_effect_class=_safe_text_or_default(
            action.get("side_effect_class"),
            "local_dev_workspace_only",
            max_length=120,
        ),
        safe_summary=_safe_text_or_default(
            action.get("safe_summary"),
            "Action item summary redacted.",
        ),
        why_shown=_safe_text_or_default(
            action.get("action_group_reason"),
            definition["safe_summary"],
        ),
        next_safe_action=_safe_text_or_default(
            action.get("next_safe_action")
            or action.get("action_group_available_action"),
            definition["next_safe_action"],
        ),
        authority_boundary=_safe_text_or_default(
            action.get("authority_boundary"),
            "Action Inbox decision lanes are review posture only; approval alone does not execute work.",
        ),
        approval_required=bool(action.get("approval_required", True)),
        approval_envelope_ref=_first_safe_ref(action.get("approval_envelope_ref")),
        approval_envelope_status=_safe_text_or_default(
            action.get("approval_envelope_status"),
            "missing",
            max_length=160,
        ),
        approval_scope_ref=_first_safe_ref(
            action.get("action_scope_ref"),
            envelope.get("exact_scope"),
        ),
        approval_requirement_ref=_first_safe_ref(
            action.get("action_approval_requirement_ref"),
            envelope.get("approval_requirement"),
        ),
        expected_receipt_refs=expected_receipts,
        expected_receipt_state=(
            "visible" if expected_receipts != ["missing"] else "missing_fail_closed"
        ),
        evidence_refs=evidence_refs or ["missing"],
        receipt_refs=receipt_refs,
        rollback_ref=_first_safe_ref(action.get("rollback_ref")),
        safe_disable_ref=_first_safe_ref(action.get("safe_disable_ref")),
        blocked_authority_refs=blocked_authority_refs,
        missing_envelope_field_states=missing_fields or ["none"],
        cost_state_label=_cost_state_label(action, envelope),
        provider_authority_state_label=_provider_authority_state_label(
            action,
            envelope,
        ),
        estimated_cost_usd=_as_float(
            action.get("action_envelope_estimated_cost_usd")
            or action.get("estimated_cost_usd")
            or envelope.get("estimated_cost_usd")
        ),
        max_approved_cost_usd=_as_float(
            action.get("action_envelope_max_approved_cost_usd")
            or action.get("max_approved_cost_usd")
            or envelope.get("max_approved_cost_usd")
        ),
        provider_ref=provider_ref,
        model_profile_ref=model_profile_ref,
        input_metered_units=input_units,
        output_metered_units=output_units,
        total_metered_units=total_units,
        cost_estimate_ref=cost_estimate_ref,
        captured_usage_ref=captured_usage_ref,
        budget_decision_ref=budget_decision_ref,
        cost_receipt_refs=cost_receipts,
        cost_blocked_state_refs=cost_blockers,
        unknown_paid_cost_requires_explicit_approval=bool(
            action.get("action_envelope_unknown_paid_cost_requires_explicit_approval")
            if action.get("action_envelope_unknown_paid_cost_requires_explicit_approval")
            is not None
            else action.get(
                "unknown_paid_cost_requires_explicit_approval",
                True,
            )
        ),
        frontier_usage_claimed=bool(
            action.get("action_envelope_frontier_usage_claimed")
            or action.get("frontier_usage_claimed", False)
        ),
        cost_telemetry_complete=cost_telemetry_complete,
        provider_model_refs_present=provider_model_refs_present,
    )


def build_action_inbox_decision_lane_read_model(
    *,
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    items = [_item_from_action(action) for action in actions]
    item_refs_by_lane = {
        lane_id: [item.item_ref for item in items if item.lane_id == lane_id]
        for lane_id in ACTION_INBOX_DECISION_LANE_ORDER
    }
    lanes = [
        ActionInboxDecisionLane(
            lane_id=lane_id,  # type: ignore[arg-type]
            label=_LANE_DEFINITIONS[lane_id]["label"],
            status=_LANE_DEFINITIONS[lane_id]["status"],
            safe_summary=_LANE_DEFINITIONS[lane_id]["safe_summary"],
            count=len(item_refs_by_lane[lane_id]),
            item_refs=item_refs_by_lane[lane_id],
            blocked_state_refs=list(ACTION_INBOX_DECISION_LANE_REQUIRED_BLOCKED_REFS),
            next_safe_action=_LANE_DEFINITIONS[lane_id]["next_safe_action"],
        )
        for lane_id in ACTION_INBOX_DECISION_LANE_ORDER
    ]
    read_model = ActionInboxDecisionLaneReadModel(
        lane_order=list(ACTION_INBOX_DECISION_LANE_ORDER),  # type: ignore[list-item]
        lanes=lanes,
        items=items,
        blocked_state_refs=list(ACTION_INBOX_DECISION_LANE_REQUIRED_BLOCKED_REFS),
    )
    return read_model.model_dump(mode="json")
