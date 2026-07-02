from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


UNIFIED_WORK_THREAD_CONTRACT_REF = (
    "contract-ref:fcc-thread-001-unified-work-thread:v1"
)
UNIFIED_WORK_THREAD_READ_MODEL_SOURCE = (
    "python_core_unified_work_thread_read_model"
)
UNIFIED_WORK_THREAD_REF = "work-thread-ref:founder-loop:demo-safe-seeded-loop"
UNIFIED_WORK_THREAD_STEP_ORDER: tuple[str, ...] = (
    "chat_handoff",
    "plan",
    "action",
    "decision_receipt",
    "evidence",
    "memory_review",
    "weekly_review",
)
UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:unified-work-thread-no-action-execution",
    "blocked-state:unified-work-thread-no-provider-model-call",
    "blocked-state:unified-work-thread-no-a2a-mcp-runtime-dispatch",
    "blocked-state:unified-work-thread-no-browser-live-web",
    "blocked-state:unified-work-thread-no-connector-read-write",
    "blocked-state:unified-work-thread-no-email-calendar-send",
    "blocked-state:unified-work-thread-no-crm-write-or-account-sync",
    "blocked-state:unified-work-thread-no-shell-subprocess",
    "blocked-state:unified-work-thread-no-memory-write",
    "blocked-state:unified-work-thread-no-context-injection",
    "blocked-state:unified-work-thread-no-background-autonomy",
    "blocked-state:unified-work-thread-no-public-beta-claim",
    "blocked-state:unified-work-thread-no-public-release-claim",
    "blocked-state:unified-work-thread-no-production-authority",
)

UnifiedWorkThreadStepId = Literal[
    "chat_handoff",
    "plan",
    "action",
    "decision_receipt",
    "evidence",
    "memory_review",
    "weekly_review",
]

_SAFE_REF_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9:_./@#=-]{0,239}$")
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
    "api_key",
    "authorization",
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
_UNSAFE_NORMALIZED_TEXT_FRAGMENTS = (
    "raw prompt",
    "raw response",
    "provider payload",
    "provider exchange",
    "raw provider",
    "raw path",
    "raw log",
    "account identifier",
    "user name",
    "host name",
    "api key",
    "private key",
    "env dump",
    "environment dump",
    "stack trace",
)
_DENIED_FLAGS = (
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "a2a_runtime_dispatch_enabled",
    "mcp_runtime_dispatch_enabled",
    "browser_execution_enabled",
    "live_web_enabled",
    "connector_read_enabled",
    "connector_write_enabled",
    "email_calendar_send_enabled",
    "crm_write_enabled",
    "account_sync_enabled",
    "shell_subprocess_execution_enabled",
    "background_autonomy_enabled",
    "memory_write_authorized",
    "context_injection_authorized",
    "action_execution_enabled",
    "public_beta_claim_enabled",
    "public_release_claim_enabled",
    "production_authority_enabled",
)


class UnifiedWorkThreadStep(BaseModel):
    step_id: UnifiedWorkThreadStepId
    surface: str = Field(..., min_length=1, max_length=80)
    frontend_route_ref: str = Field(..., min_length=1, max_length=80)
    backend_route_ref: str = Field(..., min_length=1, max_length=160)
    status: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    source_refs: list[str] = Field(default_factory=list)
    proposal_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_step(self) -> "UnifiedWorkThreadStep":
        for field_name in (
            "surface",
            "frontend_route_ref",
            "backend_route_ref",
            "status",
            "safe_summary",
            "next_safe_action",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "source_refs",
            "proposal_refs",
            "receipt_refs",
            "evidence_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


class UnifiedWorkThreadReadModel(BaseModel):
    schema_version: str = "fcc-thread-001-unified-work-thread.v1"
    contract_ref: str = UNIFIED_WORK_THREAD_CONTRACT_REF
    status: str = "implemented_backend_owned_read_model_safe_refs_only"
    source: str = UNIFIED_WORK_THREAD_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    seeded_demo_safe: bool = True
    safe_refs_only: bool = True
    safe_summary_only: bool = True
    raw_content_included: bool = False
    thread_ref: str = UNIFIED_WORK_THREAD_REF
    thread_title: str = "Unified Founder Loop work thread"
    step_order: list[UnifiedWorkThreadStepId] = Field(
        default_factory=lambda: list(UNIFIED_WORK_THREAD_STEP_ORDER)
    )
    steps: list[UnifiedWorkThreadStep] = Field(default_factory=list)
    chat_turn_receipt_refs: list[str] = Field(default_factory=list)
    chat_handoff_receipt_refs: list[str] = Field(default_factory=list)
    plan_refs: list[str] = Field(default_factory=list)
    plan_proposal_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    action_decision_receipt_refs: list[str] = Field(default_factory=list)
    evidence_timeline_refs: list[str] = Field(default_factory=list)
    evidence_event_refs: list[str] = Field(default_factory=list)
    memory_review_candidate_refs: list[str] = Field(default_factory=list)
    memory_review_receipt_refs: list[str] = Field(default_factory=list)
    weekly_review_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    safe_summary: str = (
        "Unified Work Thread links Chat handoff, Plan, Action, receipt, "
        "Evidence, Memory Review, and Weekly Review refs into one backend-owned "
        "read model."
    )
    next_safe_action: str = (
        "Inspect the safe refs across the thread before promoting any new "
        "authority or product-readiness claim."
    )
    authority_boundary: str = (
        "Unified Work Thread is read-only local Founder Loop state. It does not "
        "execute actions, call providers or models, dispatch A2A or MCP runtimes, "
        "fetch live web, automate browsers, read or write connectors, send "
        "email/calendar, write CRM, sync accounts, run shell/subprocess work, "
        "write memory, inject context, run background autonomy, claim public "
        "distribution, claim external release, or grant production authority."
    )
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    a2a_runtime_dispatch_enabled: bool = False
    mcp_runtime_dispatch_enabled: bool = False
    browser_execution_enabled: bool = False
    live_web_enabled: bool = False
    connector_read_enabled: bool = False
    connector_write_enabled: bool = False
    email_calendar_send_enabled: bool = False
    crm_write_enabled: bool = False
    account_sync_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    action_execution_enabled: bool = False
    public_beta_claim_enabled: bool = False
    public_release_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "UnifiedWorkThreadReadModel":
        if self.schema_version != "fcc-thread-001-unified-work-thread.v1":
            raise ValueError("unexpected Unified Work Thread schema version")
        if self.contract_ref != UNIFIED_WORK_THREAD_CONTRACT_REF:
            raise ValueError("unexpected Unified Work Thread contract ref")
        if self.source != UNIFIED_WORK_THREAD_READ_MODEL_SOURCE:
            raise ValueError("unexpected Unified Work Thread source")
        for field_name in (
            "backend_owned",
            "local_read_model_only",
            "seeded_demo_safe",
            "safe_refs_only",
            "safe_summary_only",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        if self.raw_content_included:
            raise ValueError("Unified Work Thread must not include raw content")
        if self.step_order != list(UNIFIED_WORK_THREAD_STEP_ORDER):
            raise ValueError("Unified Work Thread step order drifted")
        if [step.step_id for step in self.steps] != self.step_order:
            raise ValueError("Unified Work Thread steps must match step order")
        missing_blockers = set(UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_authority_refs
        )
        if missing_blockers:
            raise ValueError("Unified Work Thread missing blocked refs")
        for field_name in _DENIED_FLAGS:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must remain false")
        for field_name in (
            "contract_ref",
            "thread_ref",
        ):
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        for field_name in (
            "status",
            "source",
            "thread_title",
            "safe_summary",
            "next_safe_action",
            "authority_boundary",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "chat_turn_receipt_refs",
            "chat_handoff_receipt_refs",
            "plan_refs",
            "plan_proposal_refs",
            "action_refs",
            "action_decision_receipt_refs",
            "evidence_timeline_refs",
            "evidence_event_refs",
            "memory_review_candidate_refs",
            "memory_review_receipt_refs",
            "weekly_review_refs",
            "receipt_refs",
            "evidence_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


def build_unified_work_thread_read_model(
    *,
    actions: list[dict[str, Any]],
    plans: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    memory_review_decisions: list[dict[str, Any]],
    evidence_timeline: list[dict[str, Any]],
    chat_to_loop_handoff_read_model: dict[str, Any],
    plans_to_actions_bridge_read_model: dict[str, Any],
    weekly_ceo_review_v1_read_model: dict[str, Any],
    founder_loop_product_proof_read_model: dict[str, Any],
    evidence_event_refs: list[str],
) -> dict[str, Any]:
    chat_turn_receipt_refs = _refs(
        chat_to_loop_handoff_read_model.get("turn_receipt_refs", [])
    )
    chat_handoff_receipt_refs = _refs(
        chat_to_loop_handoff_read_model.get("handoff_receipt_refs", [])
    )
    chat_outcome_refs = _refs(chat_to_loop_handoff_read_model.get("outcome_refs", []))
    chat_evidence_refs = _refs(chat_to_loop_handoff_read_model.get("evidence_refs", []))
    chat_blocked_refs = _refs(
        chat_to_loop_handoff_read_model.get("blocked_state_refs", [])
    )
    plan_refs = _dedupe(
        [
            *[plan.get("plan_ref") for plan in plans],
            *plans_to_actions_bridge_read_model.get("plan_refs", []),
        ]
    )
    plan_proposal_refs = _refs(
        [
            item.get("item_ref")
            for item in plans_to_actions_bridge_read_model.get("items", [])
            if isinstance(item, dict)
        ]
    )
    plan_receipt_refs = _refs(
        [
            ref
            for item in plans_to_actions_bridge_read_model.get("items", [])
            if isinstance(item, dict)
            for ref in item.get("receipt_refs", [])
        ]
    )
    plan_evidence_refs = _refs(plans_to_actions_bridge_read_model.get("evidence_refs", []))
    plan_blocked_refs = _refs(
        plans_to_actions_bridge_read_model.get("blocked_authority_refs", [])
    )
    action_refs = _refs(action.get("item_ref") for action in actions)
    action_receipt_refs = _refs(
        ref
        for action in actions
        for ref in action.get("receipt_refs", [])
    )
    action_evidence_refs = _refs(
        ref for action in actions for ref in action.get("evidence_refs", [])
    )
    action_blocked_refs = _refs(
        ref
        for action in actions
        for ref in action.get("action_blocked_state_refs", [])
    )
    evidence_timeline_refs = _refs(
        item.get("timeline_item_ref") for item in evidence_timeline
    )
    bounded_event_refs = _refs(evidence_event_refs)[:12]
    evidence_refs = _dedupe(
        [
            "evidence-ref:fcc-thread-001-unified-work-thread",
            *chat_evidence_refs,
            *plan_evidence_refs,
            *action_evidence_refs,
            *[
                ref
                for item in evidence_timeline
                for ref in item.get("evidence_refs", [])
            ],
            *founder_loop_product_proof_read_model.get("evidence_refs", []),
            *weekly_ceo_review_v1_read_model.get("evidence_refs", []),
        ]
    )
    memory_candidate_refs = _refs(
        item.get("business_memory_candidate_ref") or item.get("review_ref")
        for item in memory_items
    )
    memory_receipt_refs = _refs(
        receipt.get("receipt_ref") for receipt in memory_review_decisions
    )
    weekly_review_refs = _dedupe(
        [
            weekly_ceo_review_v1_read_model.get("review_period_ref"),
            *weekly_ceo_review_v1_read_model.get("carry_forward_refs", []),
            *weekly_ceo_review_v1_read_model.get("next_week_priority_refs", []),
            *weekly_ceo_review_v1_read_model.get("unresolved_refs", []),
        ]
    )
    receipt_refs = _dedupe(
        [
            *chat_turn_receipt_refs,
            *chat_handoff_receipt_refs,
            *plan_receipt_refs,
            *action_receipt_refs,
            *memory_receipt_refs,
            *weekly_ceo_review_v1_read_model.get("receipt_refs", []),
        ]
    )
    blocked_refs = _dedupe(
        [
            *UNIFIED_WORK_THREAD_REQUIRED_BLOCKED_REFS,
            *chat_blocked_refs,
            *plan_blocked_refs,
            *action_blocked_refs,
            *founder_loop_product_proof_read_model.get("blocked_authority_refs", []),
            *weekly_ceo_review_v1_read_model.get("blocked_authority_refs", []),
        ]
    )

    steps = [
        UnifiedWorkThreadStep(
            step_id="chat_handoff",
            surface="Chat",
            frontend_route_ref="/chat",
            backend_route_ref="GET /control-center/today/summary",
            status=(
                "handoff_receipts_visible"
                if chat_handoff_receipt_refs
                else "reviewable_handoff_proposals_visible"
            ),
            safe_summary=(
                "Chat contributes receipt and handoff refs for review; model "
                "output is not truth or execution authority."
            ),
            source_refs=chat_turn_receipt_refs,
            proposal_refs=chat_outcome_refs,
            receipt_refs=[*chat_turn_receipt_refs, *chat_handoff_receipt_refs],
            evidence_refs=chat_evidence_refs[:8],
            blocked_authority_refs=chat_blocked_refs[:12],
            next_safe_action=(
                "Review Chat handoff refs before creating plans, actions, or "
                "memory candidates."
            ),
        ),
        UnifiedWorkThreadStep(
            step_id="plan",
            surface="Plans",
            frontend_route_ref="/plans",
            backend_route_ref="GET /control-center/today/summary",
            status=(
                "plan_proposals_visible"
                if plan_proposal_refs
                else "plan_bridge_ready_no_proposal_recorded"
            ),
            safe_summary=(
                "Plans show review-only proposal refs and expected receipts "
                "without workflow execution."
            ),
            source_refs=plan_refs,
            proposal_refs=plan_proposal_refs,
            receipt_refs=plan_receipt_refs,
            evidence_refs=plan_evidence_refs[:8],
            blocked_authority_refs=plan_blocked_refs[:12],
            next_safe_action="Inspect plan proposal refs before opening Action Inbox.",
        ),
        UnifiedWorkThreadStep(
            step_id="action",
            surface="Action Inbox",
            frontend_route_ref="/actions",
            backend_route_ref="GET /control-center/actions/inbox",
            status=(
                "action_refs_visible"
                if action_refs
                else "action_inbox_ready_no_item_recorded"
            ),
            safe_summary=(
                "Action Inbox shows backend-owned action refs and decision "
                "posture; execution remains blocked."
            ),
            source_refs=action_refs,
            proposal_refs=_refs(action.get("action_envelope_ref") for action in actions),
            receipt_refs=action_receipt_refs,
            evidence_refs=action_evidence_refs[:8],
            blocked_authority_refs=action_blocked_refs[:12],
            next_safe_action="Record only supported decision receipts; do not execute.",
        ),
        UnifiedWorkThreadStep(
            step_id="decision_receipt",
            surface="Receipt",
            frontend_route_ref="/actions",
            backend_route_ref="POST /control-center/actions/{action_id}/{decision}",
            status=(
                "decision_receipts_visible"
                if action_receipt_refs
                else "decision_receipt_route_ready_no_receipt_recorded"
            ),
            safe_summary=(
                "Decision changes are visible as receipt refs and evidence refs, "
                "not hidden side effects."
            ),
            source_refs=action_refs,
            receipt_refs=action_receipt_refs,
            evidence_refs=action_evidence_refs[:8],
            blocked_authority_refs=[
                "blocked-state:unified-work-thread-no-action-execution",
                "blocked-state:unified-work-thread-no-connector-read-write",
            ],
            next_safe_action="Inspect receipt refs before claiming state changed.",
        ),
        UnifiedWorkThreadStep(
            step_id="evidence",
            surface="Evidence",
            frontend_route_ref="/evidence",
            backend_route_ref="GET /control-center/evidence/timeline",
            status=(
                "evidence_timeline_visible"
                if evidence_timeline_refs
                else "evidence_timeline_ready_no_event_recorded"
            ),
            safe_summary=(
                "Evidence groups the thread path with safe refs, redacted "
                "summaries, receipt refs, and blockers."
            ),
            source_refs=evidence_timeline_refs,
            receipt_refs=receipt_refs,
            evidence_refs=[*bounded_event_refs, *evidence_refs[:8]],
            blocked_authority_refs=[
                "blocked-state:unified-work-thread-no-context-injection",
                "blocked-state:unified-work-thread-no-production-authority",
            ],
            next_safe_action="Use Evidence refs to inspect the thread before promotion.",
        ),
        UnifiedWorkThreadStep(
            step_id="memory_review",
            surface="Memory Review",
            frontend_route_ref="/memory",
            backend_route_ref="GET /control-center/memory/review",
            status=(
                "memory_candidate_visible"
                if memory_candidate_refs
                else "memory_review_none_visible"
            ),
            safe_summary=(
                "Memory Review is related review metadata only; recall is not "
                "truth and writes/context injection remain blocked."
            ),
            source_refs=memory_candidate_refs,
            receipt_refs=memory_receipt_refs,
            evidence_refs=evidence_refs[:8],
            blocked_authority_refs=[
                "blocked-state:unified-work-thread-no-memory-write",
                "blocked-state:unified-work-thread-no-context-injection",
            ],
            next_safe_action="Review candidate refs or explicit none posture.",
        ),
        UnifiedWorkThreadStep(
            step_id="weekly_review",
            surface="Weekly Review",
            frontend_route_ref="/today",
            backend_route_ref="GET /control-center/today/summary",
            status=str(
                weekly_ceo_review_v1_read_model.get(
                    "status", "review_artifact_available"
                )
            ),
            safe_summary=str(
                weekly_ceo_review_v1_read_model.get(
                    "safe_summary",
                    "Weekly Review summarizes the thread outcome from safe refs.",
                )
            ),
            source_refs=weekly_review_refs,
            receipt_refs=_refs(weekly_ceo_review_v1_read_model.get("receipt_refs", [])),
            evidence_refs=_refs(weekly_ceo_review_v1_read_model.get("evidence_refs", [])),
            blocked_authority_refs=_refs(
                weekly_ceo_review_v1_read_model.get("blocked_authority_refs", [])
            ),
            next_safe_action=str(
                weekly_ceo_review_v1_read_model.get(
                    "next_safe_action",
                    "Review carry-forward refs before selecting the next priority.",
                )
            ),
        ),
    ]

    model = UnifiedWorkThreadReadModel(
        steps=steps,
        chat_turn_receipt_refs=chat_turn_receipt_refs,
        chat_handoff_receipt_refs=chat_handoff_receipt_refs,
        plan_refs=plan_refs,
        plan_proposal_refs=plan_proposal_refs,
        action_refs=action_refs,
        action_decision_receipt_refs=action_receipt_refs,
        evidence_timeline_refs=evidence_timeline_refs,
        evidence_event_refs=bounded_event_refs,
        memory_review_candidate_refs=memory_candidate_refs,
        memory_review_receipt_refs=memory_receipt_refs,
        weekly_review_refs=weekly_review_refs,
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_refs,
    )
    return model.model_dump(mode="json")


def _refs(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    else:
        try:
            values = list(values)
        except TypeError:
            values = [values]
    refs: list[str] = []
    for value in values:
        ref = _safe_ref_or_none(value)
        if ref and ref not in refs:
            refs.append(ref)
    return refs


def _dedupe(values: list[Any]) -> list[str]:
    refs: list[str] = []
    for value in values:
        ref = _safe_ref_or_none(value)
        if ref and ref not in refs:
            refs.append(ref)
    return refs


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


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        _validate_safe_ref(str(ref), field_name)


def _validate_safe_ref(value: str, field_name: str) -> None:
    _validate_safe_text(value, field_name)
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} contains unsafe ref")


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    normalized = re.sub(r"[-_.]+", " ", lowered)
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS) or any(
        fragment in normalized for fragment in _UNSAFE_NORMALIZED_TEXT_FRAGMENTS
    ):
        raise ValueError(f"{field_name} contains unsafe text")
