from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.fusion_routing import (
    CacheContextEconomics,
    DelegationProposalEnvelope,
    WorkClassification,
    WorkClassificationValue,
    build_cache_context_economics,
    build_delegation_proposal,
    build_work_classification,
)


PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF = (
    "contract-ref:product-loop-006-plans-to-reviewable-action-envelopes:v1"
)
PLANS_TO_ACTIONS_BRIDGE_READ_MODEL_SOURCE = (
    "python_core_plans_to_actions_bridge_read_model"
)
PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:plans-to-actions-proposal-only",
    "blocked-state:plans-to-actions-approval-refs-identifiers-only",
    "blocked-state:plans-to-actions-no-action-execution",
    "blocked-state:plans-to-actions-no-tool-execution",
    "blocked-state:plans-to-actions-no-workflow-execution",
    "blocked-state:plans-to-actions-no-model-provider-call",
    "blocked-state:plans-to-actions-no-shell-subprocess",
    "blocked-state:plans-to-actions-no-browser-execution",
    "blocked-state:plans-to-actions-no-connector-runtime",
    "blocked-state:plans-to-actions-no-connector-write",
    "blocked-state:plans-to-actions-no-memory-write",
    "blocked-state:plans-to-actions-no-context-injection",
    "blocked-state:plans-to-actions-no-production-authority",
)
PLANS_TO_ACTIONS_REVIEW_RECEIPT_LABELS: tuple[str, ...] = (
    "approve",
    "edit",
    "reject",
    "defer",
)

_SAFE_REF_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9:_./@#=-]{0,239}$")
_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_.@-]+")
_UNSAFE_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "provider exchange",
    "raw provider",
    "raw_provider",
    "raw path",
    "raw_path",
    "raw log",
    "raw_log",
    "account identifier",
    "account_identifier",
    "username",
    "user name",
    "hostname",
    "host name",
    "credential",
    "secret",
    "bearer",
    "token",
    "cookie",
    "password",
    "private_key",
    "env dump",
    "environment dump",
    "stack trace",
    "traceback",
    "serial",
    "/users/",
    "/home/",
    "/private/",
    "/tmp/",
    "/var/",
    "/etc/",
    "\\users\\",
    "\\appdata\\",
    ":\\",
)
_DENIED_FLAGS = (
    "approval_ref_authority",
    "approval_grant_capture_enabled",
    "approval_alone_executes",
    "execution_authorized",
    "execution_performed",
    "action_execution_enabled",
    "action_execution_performed",
    "tool_execution_enabled",
    "tool_execution_performed",
    "workflow_execution_enabled",
    "workflow_execution_performed",
    "model_provider_call_enabled",
    "model_provider_authority_allowed",
    "provider_model_call_enabled",
    "shell_subprocess_execution_enabled",
    "shell_subprocess_execution_performed",
    "browser_execution_enabled",
    "browser_execution_performed",
    "connector_runtime_enabled",
    "connector_write_enabled",
    "connector_write_performed",
    "memory_write_authorized",
    "memory_write_performed",
    "context_injection_authorized",
    "context_injection_performed",
    "automatic_planning_authority_enabled",
    "production_authority_enabled",
)


class PlansToActionsBridgeItem(BaseModel):
    item_ref: str = Field(..., min_length=1)
    source_plan_ref: str = Field(..., min_length=1)
    linked_action_item_ref: str | None = Field(default=None)
    plan_title: str = Field(..., min_length=1, max_length=160)
    plan_status: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=600)
    why_proposed: str = Field(..., min_length=1, max_length=500)
    risk_class: str = Field(..., min_length=1, max_length=40)
    action_envelope_ref: str = Field(..., min_length=1)
    action_scope_ref: str = Field(..., min_length=1)
    approval_requirement_ref: str = Field(..., min_length=1)
    task_decomposition_proposal_ref: str | None = Field(default=None)
    task_decomposition_review_envelope_ref: str | None = Field(default=None)
    task_decomposition_action_inbox_bridge_ref: str | None = Field(default=None)
    review_receipt_labels: list[str] = Field(default_factory=list, min_length=1)
    expected_receipt_refs: list[str] = Field(default_factory=list, min_length=1)
    receipt_refs: list[str] = Field(default_factory=list)
    rollback_ref: str = Field(..., min_length=1)
    safe_disable_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    step_refs: list[str] = Field(default_factory=list)
    risk_refs: list[str] = Field(default_factory=list)
    ambiguity_refs: list[str] = Field(default_factory=list)
    missing_evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    work_classification: WorkClassification
    delegation_proposal: DelegationProposalEnvelope
    cache_context_economics: CacheContextEconomics
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    backend_owned: bool = True
    review_only: bool = True
    proposal_only: bool = True
    exact_scope_required: bool = True
    expected_receipts_required: bool = True
    rollback_required: bool = True
    safe_disable_required: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    approval_ref_authority: bool = False
    approval_grant_capture_enabled: bool = False
    approval_alone_executes: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    action_execution_enabled: bool = False
    action_execution_performed: bool = False
    tool_execution_enabled: bool = False
    tool_execution_performed: bool = False
    workflow_execution_enabled: bool = False
    workflow_execution_performed: bool = False
    model_provider_call_enabled: bool = False
    model_provider_authority_allowed: bool = False
    provider_model_call_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    shell_subprocess_execution_performed: bool = False
    browser_execution_enabled: bool = False
    browser_execution_performed: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    connector_write_performed: bool = False
    memory_write_authorized: bool = False
    memory_write_performed: bool = False
    context_injection_authorized: bool = False
    context_injection_performed: bool = False
    automatic_planning_authority_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_item(self) -> "PlansToActionsBridgeItem":
        _validate_ref_fields(
            self,
            "item_ref",
            "source_plan_ref",
            "action_envelope_ref",
            "action_scope_ref",
            "approval_requirement_ref",
            "rollback_ref",
            "safe_disable_ref",
        )
        for field_name in (
            "linked_action_item_ref",
            "task_decomposition_proposal_ref",
            "task_decomposition_review_envelope_ref",
            "task_decomposition_action_inbox_bridge_ref",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _validate_safe_ref(value, field_name)
        for field_name in (
            "plan_title",
            "plan_status",
            "safe_summary",
            "why_proposed",
            "risk_class",
            "next_safe_action",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "review_receipt_labels",
            "expected_receipt_refs",
            "receipt_refs",
            "evidence_refs",
            "step_refs",
            "risk_refs",
            "ambiguity_refs",
            "missing_evidence_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        if self.work_classification.execution_authorized:
            raise ValueError("work classification cannot authorize execution")
        if self.delegation_proposal.worker_execution_enabled:
            raise ValueError("delegation proposal cannot execute")
        if self.cache_context_economics.runtime_model_switch_performed:
            raise ValueError("cache/context economics cannot switch models")
        if set(PLANS_TO_ACTIONS_REVIEW_RECEIPT_LABELS) - set(
            self.review_receipt_labels
        ):
            raise ValueError("plans-to-actions bridge must expose all review labels")
        if set(PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("plans-to-actions bridge missing blocked authority refs")
        for field_name in (
            "backend_owned",
            "review_only",
            "proposal_only",
            "exact_scope_required",
            "expected_receipts_required",
            "rollback_required",
            "safe_disable_required",
            "safe_refs_only",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        if self.raw_content_included:
            raise ValueError("plans-to-actions bridge must not include raw content")
        _validate_denied_flags(self)
        return self


class PlansToActionsBridgeReadModel(BaseModel):
    schema_version: str = "product-loop-006-plans-to-actions.v1"
    contract_ref: str = PLANS_TO_ACTIONS_BRIDGE_CONTRACT_REF
    status: str = "implemented_backend_owned_review_envelope_bridge"
    source: str = PLANS_TO_ACTIONS_BRIDGE_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    item_count: int = Field(default=0, ge=0)
    items: list[PlansToActionsBridgeItem] = Field(default_factory=list)
    plan_refs: list[str] = Field(default_factory=list)
    action_inbox_item_refs: list[str] = Field(default_factory=list)
    task_decomposition_proposal_refs: list[str] = Field(default_factory=list)
    expected_receipt_refs: list[str] = Field(default_factory=list)
    rollback_refs: list[str] = Field(default_factory=list)
    safe_disable_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(
        default_factory=lambda: list(PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS)
    )
    next_safe_action: str = (
        "Review plan-to-action envelope refs, risks, reasons, expected receipts, "
        "rollback, and safe-disable posture before any separately scoped work."
    )
    authority_boundary: str = (
        "Plans-to-Actions is a backend-owned local read model. Plans produce "
        "reviewable envelopes only; approval refs are identifiers and decision "
        "receipts only and do not execute actions, tools, workflows, providers, "
        "shell, browser, connectors, memory writes, context injection, or "
        "production work."
    )
    approval_ref_authority: bool = False
    approval_grant_capture_enabled: bool = False
    approval_alone_executes: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    action_execution_enabled: bool = False
    action_execution_performed: bool = False
    tool_execution_enabled: bool = False
    tool_execution_performed: bool = False
    workflow_execution_enabled: bool = False
    workflow_execution_performed: bool = False
    model_provider_call_enabled: bool = False
    model_provider_authority_allowed: bool = False
    provider_model_call_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    shell_subprocess_execution_performed: bool = False
    browser_execution_enabled: bool = False
    browser_execution_performed: bool = False
    connector_runtime_enabled: bool = False
    connector_write_enabled: bool = False
    connector_write_performed: bool = False
    memory_write_authorized: bool = False
    memory_write_performed: bool = False
    context_injection_authorized: bool = False
    context_injection_performed: bool = False
    automatic_planning_authority_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "PlansToActionsBridgeReadModel":
        _validate_safe_ref(self.contract_ref, "contract_ref")
        _validate_safe_text(self.status, "status")
        _validate_safe_text(self.source, "source")
        _validate_safe_text(self.next_safe_action, "next_safe_action")
        _validate_safe_text(self.authority_boundary, "authority_boundary")
        if self.source != PLANS_TO_ACTIONS_BRIDGE_READ_MODEL_SOURCE:
            raise ValueError("unexpected plans-to-actions read-model source")
        if self.item_count != len(self.items):
            raise ValueError("item_count must match plans-to-actions items")
        for field_name in (
            "backend_owned",
            "local_read_model_only",
            "safe_refs_only",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        if self.raw_content_included:
            raise ValueError("plans-to-actions read model must not include raw content")
        for field_name in (
            "plan_refs",
            "action_inbox_item_refs",
            "task_decomposition_proposal_refs",
            "expected_receipt_refs",
            "rollback_refs",
            "safe_disable_refs",
            "blocked_state_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        if set(PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_state_refs
        ):
            raise ValueError("plans-to-actions read model missing blocked refs")
        _validate_denied_flags(self)
        return self


def build_plans_to_actions_bridge_read_model(
    *,
    plans: list[dict[str, Any]],
    action_items: list[dict[str, Any]],
) -> dict[str, Any]:
    actions_by_proposal_ref = {
        str(action["task_decomposition_proposal_ref"]): action
        for action in action_items
        if action.get("task_decomposition_proposal_ref")
    }
    actions_by_bridge_ref = {
        str(action["task_decomposition_action_inbox_bridge_ref"]): action
        for action in action_items
        if action.get("task_decomposition_action_inbox_bridge_ref")
    }

    items: list[PlansToActionsBridgeItem] = []
    for plan in plans:
        plan_ref = _safe_ref_or_none(plan.get("plan_ref"))
        if not plan_ref:
            continue
        proposal_ref = _safe_ref_or_none(plan.get("task_decomposition_proposal_ref"))
        action_bridge_ref = _safe_ref_or_none(
            plan.get("task_decomposition_action_inbox_bridge_ref")
        )
        linked_action = (
            actions_by_proposal_ref.get(proposal_ref or "")
            or actions_by_bridge_ref.get(action_bridge_ref or "")
            or {}
        )
        item = _bridge_item_for_plan(
            plan=plan,
            linked_action=linked_action,
            plan_ref=plan_ref,
            proposal_ref=proposal_ref,
            action_bridge_ref=action_bridge_ref,
        )
        items.append(item)

    read_model = PlansToActionsBridgeReadModel(
        item_count=len(items),
        items=items,
        plan_refs=_dedupe([item.source_plan_ref for item in items]),
        action_inbox_item_refs=_dedupe(
            [
                item.linked_action_item_ref
                for item in items
                if item.linked_action_item_ref
            ]
        ),
        task_decomposition_proposal_refs=_dedupe(
            [
                item.task_decomposition_proposal_ref
                for item in items
                if item.task_decomposition_proposal_ref
            ]
        ),
        expected_receipt_refs=_dedupe(
            [ref for item in items for ref in item.expected_receipt_refs]
        ),
        rollback_refs=_dedupe([item.rollback_ref for item in items]),
        safe_disable_refs=_dedupe([item.safe_disable_ref for item in items]),
    )
    return read_model.model_dump(mode="json")


def _bridge_item_for_plan(
    *,
    plan: dict[str, Any],
    linked_action: dict[str, Any],
    plan_ref: str,
    proposal_ref: str | None,
    action_bridge_ref: str | None,
) -> PlansToActionsBridgeItem:
    suffix = _safe_suffix(plan_ref)
    risk_refs = _safe_refs(
        [risk.get("risk_ref") for risk in plan.get("task_decomposition_risks", [])]
        if isinstance(plan.get("task_decomposition_risks"), list)
        else []
    )
    expected_receipts = _safe_refs(
        [
            *(plan.get("expected_receipt_refs") or []),
            *(plan.get("plan_action_expected_receipt_refs") or []),
            *(linked_action.get("action_expected_receipt_refs") or []),
        ]
    )
    expected_receipts_missing = not expected_receipts
    expected_receipts = expected_receipts or [f"receipt-plan:plans-to-actions:{suffix}"]
    rollback_ref_from_payload = (
        _safe_ref_or_none(plan.get("rollback_ref"))
        or _safe_ref_or_none(linked_action.get("action_rollback_ref"))
    )
    rollback_ref = rollback_ref_from_payload or f"rollback-plan:plans-to-actions:{suffix}"
    safe_disable_ref_from_payload = (
        _safe_ref_or_none(plan.get("safe_disable_ref"))
        or _safe_ref_or_none(linked_action.get("action_safe_disable_ref"))
    )
    safe_disable_ref = (
        safe_disable_ref_from_payload or f"safe-disable:plans-to-actions:{suffix}"
    )
    action_envelope_ref_from_payload = (
        _safe_ref_or_none(plan.get("task_decomposition_action_envelope_ref"))
        or _safe_ref_or_none(plan.get("action_envelope_ref"))
    )
    action_scope_ref_from_payload = (
        _safe_ref_or_none(plan.get("scope_ref"))
        or _safe_ref_or_none(plan.get("plan_action_scope_ref"))
    )
    approval_requirement_ref_from_payload = (
        _safe_ref_or_none(plan.get("approval_requirement_ref"))
        or _safe_ref_or_none(plan.get("plan_action_approval_requirement_ref"))
    )
    missing_field_blocked_refs = [
        *(
            ["blocked-state:plans-to-actions-expected-receipt-refs-missing"]
            if expected_receipts_missing
            else []
        ),
        *(
            ["blocked-state:plans-to-actions-rollback-ref-missing"]
            if not rollback_ref_from_payload
            else []
        ),
        *(
            ["blocked-state:plans-to-actions-safe-disable-ref-missing"]
            if not safe_disable_ref_from_payload
            else []
        ),
        *(
            ["blocked-state:plans-to-actions-action-envelope-ref-missing"]
            if not action_envelope_ref_from_payload
            else []
        ),
        *(
            ["blocked-state:plans-to-actions-action-scope-ref-missing"]
            if not action_scope_ref_from_payload
            else []
        ),
        *(
            ["blocked-state:plans-to-actions-approval-requirement-ref-missing"]
            if not approval_requirement_ref_from_payload
            else []
        ),
    ]
    blocked_refs = _dedupe(
        [
            *PLANS_TO_ACTIONS_BRIDGE_REQUIRED_BLOCKED_REFS,
            *missing_field_blocked_refs,
            *(plan.get("blocked_state_refs") or []),
            *(plan.get("plan_action_blocked_state_refs") or []),
            *(plan.get("task_decomposition_blocked_authority_refs") or []),
            *(linked_action.get("action_blocked_state_refs") or []),
            *(linked_action.get("task_decomposition_blocked_authority_refs") or []),
            *([] if linked_action else ["blocked-state:plans-to-actions-action-item-missing"]),
        ]
    )
    action_envelope_ref = (
        action_envelope_ref_from_payload or f"action-envelope:plans-to-actions:{suffix}"
    )
    work_classification = build_work_classification(
        WorkClassificationValue.judgment_required,
        suffix_ref=plan_ref,
        source_ref=plan_ref,
        evidence_ref=(expected_receipts[0] if expected_receipts else f"evidence-ref:plans-to-actions:{suffix}"),
        reason_ref=f"classification-reason-ref:plans-to-actions:{suffix}",
    )
    return PlansToActionsBridgeItem(
        item_ref=f"plans-to-actions-bridge:{suffix}",
        source_plan_ref=plan_ref,
        linked_action_item_ref=_safe_ref_or_none(linked_action.get("item_ref")),
        plan_title=_safe_text_or_default(plan.get("title"), "Plan proposal"),
        plan_status=_safe_text_or_default(
            plan.get("task_decomposition_status") or plan.get("status"),
            "proposal_only_review_required",
        ),
        safe_summary=(
            "Plan proposal maps to a reviewable Action envelope with risk, "
            "reason, expected receipt, rollback, safe-disable, and blocked "
            "authority refs; no execution authority is granted."
        ),
        why_proposed=_safe_text_or_default(
            plan.get("task_decomposition_why_proposed"),
            "Plan needs operator review before any separately scoped work.",
        ),
        risk_class=_safe_text_or_default(
            plan.get("task_decomposition_risk_class") or plan.get("risk_class"),
            "medium",
            max_length=40,
        ),
        action_envelope_ref=action_envelope_ref,
        action_scope_ref=(
            action_scope_ref_from_payload or f"scope-ref:plans-to-actions:{suffix}"
        ),
        approval_requirement_ref=(
            approval_requirement_ref_from_payload
            or f"approval-requirement:plans-to-actions:{suffix}"
        ),
        task_decomposition_proposal_ref=proposal_ref,
        task_decomposition_review_envelope_ref=_safe_ref_or_none(
            plan.get("task_decomposition_review_envelope_ref")
        ),
        task_decomposition_action_inbox_bridge_ref=action_bridge_ref,
        review_receipt_labels=list(PLANS_TO_ACTIONS_REVIEW_RECEIPT_LABELS),
        expected_receipt_refs=expected_receipts,
        receipt_refs=_safe_refs(linked_action.get("receipt_refs") or []),
        rollback_ref=rollback_ref,
        safe_disable_ref=safe_disable_ref,
        evidence_refs=_safe_refs(
            [
                *(plan.get("evidence_refs") or []),
                *(linked_action.get("evidence_refs") or []),
            ]
        )
        or [f"evidence-ref:plans-to-actions:{suffix}"],
        step_refs=_safe_refs(plan.get("task_decomposition_step_refs") or []),
        risk_refs=risk_refs,
        ambiguity_refs=_safe_refs(plan.get("task_decomposition_ambiguity_refs") or []),
        missing_evidence_refs=_safe_refs(
            plan.get("task_decomposition_missing_evidence_refs") or []
        ),
        blocked_authority_refs=blocked_refs,
        work_classification=work_classification,
        delegation_proposal=build_delegation_proposal(
            work_classification=work_classification,
            suffix_ref=plan_ref,
        ),
        cache_context_economics=build_cache_context_economics(
            suffix_ref=plan_ref,
            blocker_refs=missing_field_blocked_refs,
        ),
        next_safe_action=(
            "Review the envelope, risks, reasons, expected receipts, rollback, "
            "and safe-disable refs; create executable work only in a separate "
            "exact-scoped lane."
        ),
    )


def _validate_denied_flags(model: BaseModel) -> None:
    enabled = [field for field in _DENIED_FLAGS if bool(getattr(model, field))]
    if enabled:
        raise ValueError(f"{enabled[0]} must remain false")


def _validate_ref_fields(model: BaseModel, *field_names: str) -> None:
    for field_name in field_names:
        _validate_safe_ref(str(getattr(model, field_name)), field_name)


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        _validate_safe_ref(str(value), field_name)


def _validate_safe_ref(value: str, field_name: str) -> None:
    _validate_safe_text(value, field_name)
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe ref")


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe/private content")


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


def _safe_text_or_default(
    value: object,
    default: str,
    *,
    max_length: int = 500,
) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        return default
    try:
        _validate_safe_text(candidate, "safe_text")
    except ValueError:
        return default
    return candidate[:max_length]


def _safe_suffix(value: str) -> str:
    suffix = _SAFE_SUFFIX_RE.sub("-", value.lower()).strip("-")
    return suffix or "missing"


def _dedupe(values: list[str | None]) -> list[str]:
    refs: list[str] = []
    for value in values:
        if not value:
            continue
        ref = _safe_ref_or_none(value)
        if ref and ref not in refs:
            refs.append(ref)
    return refs
