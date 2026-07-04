from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
)


FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF = (
    "contract-ref:founder-loop-v1-product-proof:v1"
)
FOUNDER_LOOP_PRODUCT_PROOF_READ_MODEL_SOURCE = (
    "python_core_founder_loop_v1_product_proof_read_model"
)
FOUNDER_LOOP_PRODUCT_PROOF_SCENARIO_REF = (
    "scenario-ref:founder-loop-v1-demo-safe-seeded-loop"
)
FOUNDER_LOOP_PRODUCT_PROOF_SHARED_STATE_REF = (
    "founder-loop-state-ref:demo-safe-seeded-loop"
)
FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER: tuple[str, ...] = (
    "morning_briefing",
    "today",
    "action_inbox",
    "decision_receipt",
    "evidence_timeline",
    "memory_review",
    "weekly_review",
)
FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER: tuple[str, ...] = (
    "start_here",
    "today",
    "action_inbox",
    "proof",
    "evidence",
    "memory",
    "trust",
    "settings",
)
FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:founder-loop-proof-no-provider-model-call",
    "blocked-state:founder-loop-proof-no-a2a-mcp-runtime-dispatch",
    "blocked-state:founder-loop-proof-no-browser-or-live-web",
    "blocked-state:founder-loop-proof-no-connector-write",
    "blocked-state:founder-loop-proof-no-email-calendar-send",
    "blocked-state:founder-loop-proof-no-crm-write-or-account-sync",
    "blocked-state:founder-loop-proof-no-shell-execution",
    "blocked-state:founder-loop-proof-no-background-autonomy",
    "blocked-state:founder-loop-proof-no-ui-only-authority",
    "blocked-state:founder-loop-proof-no-public-release-claim",
    "blocked-state:founder-loop-proof-no-production-authority",
)
FOUNDER_LOOP_PRODUCT_PROOF_DECISION_ACTIONS: tuple[str, ...] = (
    "approve",
    "edit",
    "reject",
    "defer",
)

FounderLoopProductProofStepId = Literal[
    "morning_briefing",
    "today",
    "action_inbox",
    "decision_receipt",
    "evidence_timeline",
    "memory_review",
    "weekly_review",
]
FounderLoopProductizedSurfaceId = Literal[
    "start_here",
    "today",
    "action_inbox",
    "proof",
    "evidence",
    "memory",
    "trust",
    "settings",
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
_DENIED_FLAGS = (
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "a2a_runtime_dispatch_enabled",
    "mcp_runtime_dispatch_enabled",
    "browser_execution_enabled",
    "live_web_enabled",
    "connector_write_enabled",
    "email_calendar_send_enabled",
    "crm_write_enabled",
    "account_sync_enabled",
    "shell_subprocess_execution_enabled",
    "background_autonomy_enabled",
    "memory_write_authorized",
    "context_injection_authorized",
    "public_beta_claim_enabled",
    "public_release_claim_enabled",
    "production_authority_enabled",
)


class FounderLoopProductProofStep(BaseModel):
    step_id: FounderLoopProductProofStepId
    surface: str = Field(..., min_length=1, max_length=80)
    backend_route_ref: str = Field(..., min_length=1, max_length=160)
    frontend_route_ref: str = Field(..., min_length=1, max_length=80)
    status: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    source_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_step(self) -> "FounderLoopProductProofStep":
        for field_name in (
            "surface",
            "backend_route_ref",
            "frontend_route_ref",
            "status",
            "safe_summary",
            "next_safe_action",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "source_refs",
            "evidence_refs",
            "receipt_refs",
            "blocked_state_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


class FounderLoopProductizedSurfaceBinding(BaseModel):
    surface_id: FounderLoopProductizedSurfaceId
    surface: str = Field(..., min_length=1, max_length=80)
    frontend_route_ref: str = Field(..., min_length=1, max_length=80)
    backend_route_ref: str = Field(..., min_length=1, max_length=160)
    status: str = Field(..., min_length=1, max_length=120)
    product_posture: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    shared_ref: str = Field(..., min_length=1)
    primary_proof_ref: str = Field(..., min_length=1)
    source_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "FounderLoopProductizedSurfaceBinding":
        for field_name in (
            "surface",
            "frontend_route_ref",
            "backend_route_ref",
            "status",
            "product_posture",
            "safe_summary",
            "next_safe_action",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in ("shared_ref", "primary_proof_ref"):
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        for field_name in (
            "source_refs",
            "receipt_refs",
            "evidence_refs",
            "memory_candidate_refs",
            "blocked_state_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


class FounderLoopProductProofReadModel(BaseModel):
    schema_version: str = "founder-loop-v1-product-proof.v1"
    contract_ref: str = FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF
    status: str = "implemented_backend_owned_product_proof_pass_safe_refs_only"
    source: str = FOUNDER_LOOP_PRODUCT_PROOF_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    seeded_demo_safe: bool = True
    safe_refs_only: bool = True
    safe_summary_only: bool = True
    raw_content_included: bool = False
    scenario_ref: str = FOUNDER_LOOP_PRODUCT_PROOF_SCENARIO_REF
    shared_state_ref: str = FOUNDER_LOOP_PRODUCT_PROOF_SHARED_STATE_REF
    full_strength_goal: str = (
        "Start Here, Today, Action Inbox, Proof, Evidence, Memory, Trust, and "
        "Settings operate as one local first governed daily loop."
    )
    repo_safe_scope: str = (
        "Backend owned safe refs, read only route posture, visual cohesion, "
        "mock fallback labels, and CLI inspection only."
    )
    blocked_authority_summary: str = (
        "Provider and model calls, connector writes or sends, browser work, "
        "shell subprocess work, background autonomy, public beta and "
        "distribution claims, and production authority remain blocked."
    )
    exact_promotion_path_refs: list[str] = Field(
        default_factory=lambda: [
            "promotion-path-ref:daily-loop-productization:shared-backend-refs",
            "promotion-path-ref:daily-loop-productization:route-proof-cohesion",
            "promotion-path-ref:daily-loop-productization:receipt-evidence-memory-binding",
            "promotion-path-ref:daily-loop-productization:approved-mutation-lanes-only",
        ]
    )
    productized_surface_order: list[FounderLoopProductizedSurfaceId] = Field(
        default_factory=lambda: list(FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER)
    )
    productized_surface_count: int = 0
    productized_surface_bindings: list[FounderLoopProductizedSurfaceBinding] = Field(
        default_factory=list
    )
    productized_route_refs: list[str] = Field(default_factory=list)
    productized_backend_route_refs: list[str] = Field(default_factory=list)
    loop_order: list[FounderLoopProductProofStepId] = Field(
        default_factory=lambda: list(FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER)
    )
    steps: list[FounderLoopProductProofStep] = Field(default_factory=list)
    supported_decision_actions: list[str] = Field(
        default_factory=lambda: list(FOUNDER_LOOP_PRODUCT_PROOF_DECISION_ACTIONS)
    )
    morning_briefing_refs: list[str] = Field(default_factory=list)
    today_refs: list[str] = Field(default_factory=list)
    action_inbox_refs: list[str] = Field(default_factory=list)
    action_decision_receipt_refs: list[str] = Field(default_factory=list)
    evidence_timeline_refs: list[str] = Field(default_factory=list)
    evidence_event_refs: list[str] = Field(default_factory=list)
    memory_review_candidate_refs: list[str] = Field(default_factory=list)
    memory_review_receipt_refs: list[str] = Field(default_factory=list)
    weekly_review_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    memory_review_status: str = "none"
    weekly_review_status: str = "review_artifact_available"
    decision_receipt_status: str = "ready_no_receipt_recorded"
    safe_summary: str = (
        "Founder Loop V1 product proof binds Morning Briefing, Today, Action "
        "Inbox decisions, receipt refs, Evidence Timeline, Memory Review, and "
        "Weekly Review through backend-owned safe refs."
    )
    next_safe_action: str = (
        "Inspect the shared safe refs and receipt posture before claiming more "
        "authority or adding new runtime lanes."
    )
    authority_boundary: str = (
        "Founder Loop V1 product proof is a backend-owned local read model. It "
        "does not call providers or models, dispatch A2A or MCP runtimes, fetch "
        "live web, automate a browser, write connectors, send email/calendar, "
        "write CRM, sync accounts, run shell/subprocess work, grant background "
        "autonomy, write memory, inject context, claim external-release, or grant "
        "production authority."
    )
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    a2a_runtime_dispatch_enabled: bool = False
    mcp_runtime_dispatch_enabled: bool = False
    browser_execution_enabled: bool = False
    live_web_enabled: bool = False
    connector_write_enabled: bool = False
    email_calendar_send_enabled: bool = False
    crm_write_enabled: bool = False
    account_sync_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    public_beta_claim_enabled: bool = False
    public_release_claim_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "FounderLoopProductProofReadModel":
        if self.schema_version != "founder-loop-v1-product-proof.v1":
            raise ValueError("unexpected Founder Loop product proof schema version")
        if self.contract_ref != FOUNDER_LOOP_PRODUCT_PROOF_CONTRACT_REF:
            raise ValueError("unexpected Founder Loop product proof contract ref")
        if self.source != FOUNDER_LOOP_PRODUCT_PROOF_READ_MODEL_SOURCE:
            raise ValueError("unexpected Founder Loop product proof source")
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
            raise ValueError("Founder Loop product proof must not include raw content")
        if self.loop_order != list(FOUNDER_LOOP_PRODUCT_PROOF_STEP_ORDER):
            raise ValueError("Founder Loop product proof loop order drifted")
        if [step.step_id for step in self.steps] != self.loop_order:
            raise ValueError("Founder Loop product proof steps must match loop order")
        if self.productized_surface_order != list(
            FOUNDER_LOOP_PRODUCTIZATION_SURFACE_ORDER
        ):
            raise ValueError("Founder Loop productized surface order drifted")
        if self.productized_surface_count != len(self.productized_surface_bindings):
            raise ValueError("Founder Loop productized surface count drifted")
        if self.productized_surface_bindings:
            if (
                [binding.surface_id for binding in self.productized_surface_bindings]
                != self.productized_surface_order
            ):
                raise ValueError("Founder Loop productized bindings must match order")
        if self.supported_decision_actions != list(
            FOUNDER_LOOP_PRODUCT_PROOF_DECISION_ACTIONS
        ):
            raise ValueError("Founder Loop product proof decision actions drifted")
        missing_blockers = set(FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS) - set(
            self.blocked_authority_refs
        )
        if missing_blockers:
            raise ValueError("Founder Loop product proof missing blocked refs")
        if self.memory_review_status not in {"candidate_available", "none"}:
            raise ValueError("Founder Loop product proof memory status drifted")
        for field_name in _DENIED_FLAGS:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must remain false")
        for field_name in (
            "scenario_ref",
            "shared_state_ref",
            "contract_ref",
        ):
            _validate_safe_ref(str(getattr(self, field_name)), field_name)
        for field_name in (
            "status",
            "source",
            "memory_review_status",
            "weekly_review_status",
            "decision_receipt_status",
            "safe_summary",
            "next_safe_action",
            "authority_boundary",
            "full_strength_goal",
            "repo_safe_scope",
            "blocked_authority_summary",
        ):
            _validate_safe_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "exact_promotion_path_refs",
            "morning_briefing_refs",
            "today_refs",
            "action_inbox_refs",
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
        _validate_safe_text_list(self.productized_route_refs, "productized_route_refs")
        _validate_safe_text_list(
            self.productized_backend_route_refs,
            "productized_backend_route_refs",
        )
        if self.productized_route_refs != [
            binding.frontend_route_ref
            for binding in self.productized_surface_bindings
        ]:
            raise ValueError("productized route refs must mirror surface bindings")
        if self.productized_backend_route_refs != [
            binding.backend_route_ref
            for binding in self.productized_surface_bindings
        ]:
            raise ValueError(
                "productized backend route refs must mirror surface bindings"
            )
        return self


def build_founder_loop_product_proof_read_model(
    *,
    actions: list[dict[str, Any]],
    briefing_items: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    evidence_timeline: list[dict[str, Any]],
    memory_review_decisions: list[dict[str, Any]],
    today_loop_read_model: dict[str, Any],
    weekly_ceo_review_v1_read_model: dict[str, Any],
    daily_loop_summary: dict[str, Any],
    evidence_event_refs: list[str],
) -> dict[str, Any]:
    action_refs = _refs(action.get("item_ref") for action in actions)
    briefing_refs = _refs(item.get("briefing_ref") for item in briefing_items)
    memory_candidate_refs = _refs(
        item.get("business_memory_candidate_ref") or item.get("review_ref")
        for item in memory_items
    )
    memory_review_refs = _refs(item.get("review_ref") for item in memory_items)
    action_receipt_refs = _refs(
        ref
        for action in actions
        for ref in action.get("receipt_refs", [])
        if str(ref).startswith("receipt:")
    )
    memory_receipt_refs = _refs(
        receipt.get("receipt_ref") for receipt in memory_review_decisions
    )
    receipt_refs = _dedupe([*action_receipt_refs, *memory_receipt_refs])
    evidence_timeline_refs = _refs(
        item.get("timeline_item_ref") for item in evidence_timeline
    )
    bounded_event_refs = _refs(evidence_event_refs)[:12]
    evidence_refs = _dedupe(
        [
            "evidence-ref:founder-loop-v1-product-proof",
            *[
                ref
                for action in actions
                for ref in action.get("evidence_refs", [])
            ],
            *[
                ref
                for item in briefing_items
                for ref in item.get("evidence_refs", [])
            ],
            *[
                ref
                for item in memory_items
                for ref in item.get("evidence_refs", [])
            ],
            *[
                ref
                for item in evidence_timeline
                for ref in item.get("evidence_refs", [])
            ],
            *weekly_ceo_review_v1_read_model.get("evidence_refs", []),
        ]
    )
    today_refs = _dedupe(
        [
            _safe_ref_or_none(daily_loop_summary.get("loop_ref")),
            _safe_ref_or_none(today_loop_read_model.get("contract_ref")),
            *today_loop_read_model.get("what_matters_now_refs", []),
            *today_loop_read_model.get("needs_review_refs", []),
        ]
    )
    weekly_refs = _dedupe(
        [
            _safe_ref_or_none(
                weekly_ceo_review_v1_read_model.get("review_period_ref")
            ),
            *weekly_ceo_review_v1_read_model.get("carry_forward_refs", []),
            *weekly_ceo_review_v1_read_model.get("next_week_priority_refs", []),
            *weekly_ceo_review_v1_read_model.get("unresolved_refs", []),
        ]
    )
    blocked_refs = _dedupe(
        [
            *FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS,
            *today_loop_read_model.get("blocked_state_refs", []),
            *weekly_ceo_review_v1_read_model.get("blocked_authority_refs", []),
            *[
                ref
                for action in actions
                for ref in action.get("action_blocked_state_refs", [])
            ],
        ]
    )
    decision_status = (
        "receipt_backed_decision_path_visible"
        if receipt_refs
        else "ready_no_receipt_recorded"
    )
    memory_status = "candidate_available" if memory_candidate_refs else "none"

    steps = [
        FounderLoopProductProofStep(
            step_id="morning_briefing",
            surface="Morning Briefing",
            backend_route_ref="GET /control-center/morning-briefing/summary",
            frontend_route_ref="/briefing",
            status="backend_owned_read_model",
            safe_summary=(
                "Briefing starts the loop from local safe refs and missing-source "
                "blockers."
            ),
            source_refs=briefing_refs,
            evidence_refs=evidence_refs[:8],
            blocked_state_refs=[
                "blocked-state:founder-loop-proof-no-browser-or-live-web",
                "blocked-state:founder-loop-proof-no-connector-write",
            ],
            next_safe_action="Open Today or Action Inbox before recording receipts.",
        ),
        FounderLoopProductProofStep(
            step_id="today",
            surface="Today",
            backend_route_ref="GET /control-center/today/summary",
            frontend_route_ref="/today",
            status=today_loop_read_model.get("status", "backend_owned_read_model"),
            safe_summary=(
                "Today shares the same backend state and orders what matters, "
                "needs review, changed, and blocked refs."
            ),
            source_refs=today_refs,
            evidence_refs=_refs(today_loop_read_model.get("evidence_refs", [])),
            blocked_state_refs=_refs(today_loop_read_model.get("blocked_state_refs", [])),
            next_safe_action=today_loop_read_model.get(
                "next_safe_action",
                "Review Today refs before opening deeper surfaces.",
            ),
        ),
        FounderLoopProductProofStep(
            step_id="action_inbox",
            surface="Action Inbox",
            backend_route_ref="GET /control-center/actions/inbox",
            frontend_route_ref="/actions",
            status="decision_receipt_route_available",
            safe_summary=(
                "Action Inbox exposes approve, edit, reject, and defer receipt "
                "decisions without executing actions."
            ),
            source_refs=action_refs,
            evidence_refs=evidence_refs[:8],
            receipt_refs=action_receipt_refs,
            blocked_state_refs=[
                "blocked-state:founder-loop-proof-no-ui-only-authority",
                "blocked-state:founder-loop-proof-no-production-authority",
            ],
            next_safe_action=(
                "Record only backend-supported decision receipts; execution "
                "remains blocked."
            ),
        ),
        FounderLoopProductProofStep(
            step_id="decision_receipt",
            surface="Receipt",
            backend_route_ref="POST /control-center/actions/{action_id}/{decision}",
            frontend_route_ref="/actions",
            status=decision_status,
            safe_summary=(
                "Decision changes are represented by receipt refs and evidence "
                "refs, not by hidden execution."
            ),
            source_refs=action_refs,
            evidence_refs=evidence_refs[:8],
            receipt_refs=receipt_refs,
            blocked_state_refs=[
                "blocked-state:founder-loop-proof-no-shell-execution",
                "blocked-state:founder-loop-proof-no-connector-write",
            ],
            next_safe_action="Inspect receipt refs before claiming changed state.",
        ),
        FounderLoopProductProofStep(
            step_id="evidence_timeline",
            surface="Evidence Timeline",
            backend_route_ref="GET /control-center/evidence/timeline",
            frontend_route_ref="/evidence",
            status="safe_ref_decision_path_visible",
            safe_summary=(
                "Evidence Timeline shows decision, blocked, stale, receipt, and "
                "weekly-review refs as inspection evidence."
            ),
            source_refs=evidence_timeline_refs,
            evidence_refs=[*bounded_event_refs, *evidence_refs[:6]],
            receipt_refs=receipt_refs,
            blocked_state_refs=[
                "blocked-state:founder-loop-proof-no-context-injection",
                "blocked-state:founder-loop-proof-no-production-authority",
            ],
            next_safe_action="Use Evidence Timeline refs as proof before promotion.",
        ),
        FounderLoopProductProofStep(
            step_id="memory_review",
            surface="Memory Review",
            backend_route_ref="GET /control-center/memory/review",
            frontend_route_ref="/memory",
            status=memory_status,
            safe_summary=(
                "Memory Review shows a related candidate when available; recall "
                "remains review-only and not truth authority."
                if memory_candidate_refs
                else "Memory Review has no candidate in this state and says so explicitly."
            ),
            source_refs=[*memory_candidate_refs, *memory_review_refs],
            evidence_refs=evidence_refs[:8],
            receipt_refs=memory_receipt_refs,
            blocked_state_refs=[
                "blocked-state:founder-loop-proof-no-memory-write",
                "blocked-state:founder-loop-proof-no-context-injection",
            ],
            next_safe_action=(
                "Review candidate refs or explicit none posture before relying "
                "on memory."
            ),
        ),
        FounderLoopProductProofStep(
            step_id="weekly_review",
            surface="Weekly Review",
            backend_route_ref="GET /control-center/today/summary",
            frontend_route_ref="/today",
            status=weekly_ceo_review_v1_read_model.get(
                "status", "review_artifact_available"
            ),
            safe_summary=weekly_ceo_review_v1_read_model.get(
                "safe_summary",
                "Weekly Review summarizes the loop outcome from safe refs only.",
            ),
            source_refs=weekly_refs,
            evidence_refs=_refs(weekly_ceo_review_v1_read_model.get("evidence_refs", [])),
            receipt_refs=_refs(weekly_ceo_review_v1_read_model.get("receipt_refs", [])),
            blocked_state_refs=_refs(
                weekly_ceo_review_v1_read_model.get("blocked_authority_refs", [])
            ),
            next_safe_action=weekly_ceo_review_v1_read_model.get(
                "next_safe_action",
                "Review carry-forward refs before choosing next product priority.",
            ),
        ),
    ]
    productized_surface_bindings = _productized_surface_bindings(
        action_refs=action_refs,
        bounded_event_refs=bounded_event_refs,
        evidence_refs=evidence_refs,
        evidence_timeline_refs=evidence_timeline_refs,
        memory_candidate_refs=memory_candidate_refs,
        memory_receipt_refs=memory_receipt_refs,
        receipt_refs=receipt_refs,
        today_refs=today_refs,
    )

    model = FounderLoopProductProofReadModel(
        steps=steps,
        productized_surface_count=len(productized_surface_bindings),
        productized_surface_bindings=productized_surface_bindings,
        productized_route_refs=[
            binding.frontend_route_ref for binding in productized_surface_bindings
        ],
        productized_backend_route_refs=[
            binding.backend_route_ref for binding in productized_surface_bindings
        ],
        morning_briefing_refs=briefing_refs,
        today_refs=today_refs,
        action_inbox_refs=action_refs,
        action_decision_receipt_refs=action_receipt_refs,
        evidence_timeline_refs=evidence_timeline_refs,
        evidence_event_refs=bounded_event_refs,
        memory_review_candidate_refs=memory_candidate_refs,
        memory_review_receipt_refs=memory_receipt_refs,
        weekly_review_refs=weekly_refs,
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        blocked_authority_refs=blocked_refs,
        memory_review_status=memory_status,
        weekly_review_status=weekly_ceo_review_v1_read_model.get(
            "status", "review_artifact_available"
        ),
        decision_receipt_status=decision_status,
    )
    return model.model_dump(mode="json")


def _productized_surface_bindings(
    *,
    action_refs: list[str],
    bounded_event_refs: list[str],
    evidence_refs: list[str],
    evidence_timeline_refs: list[str],
    memory_candidate_refs: list[str],
    memory_receipt_refs: list[str],
    receipt_refs: list[str],
    today_refs: list[str],
) -> list[FounderLoopProductizedSurfaceBinding]:
    common_blocked = list(FOUNDER_LOOP_PRODUCT_PROOF_REQUIRED_BLOCKED_REFS)
    shared_ref = FOUNDER_LOOP_PRODUCT_PROOF_SHARED_STATE_REF
    primary_proof_ref = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
    return [
        FounderLoopProductizedSurfaceBinding(
            surface_id="start_here",
            surface="Start Here",
            frontend_route_ref="/start",
            backend_route_ref="GET /control-center/start-here/summary",
            status="backend_owned_entrypoint",
            product_posture="entrypoint",
            safe_summary=(
                "Start Here opens the local daily loop with shared run, proof, "
                "action, evidence, memory, and Trust refs."
            ),
            shared_ref=shared_ref,
            primary_proof_ref=primary_proof_ref,
            source_refs=[
                "contract-ref:control-center-start-here:v1",
                *today_refs[:3],
            ],
            evidence_refs=evidence_refs[:6],
            blocked_state_refs=common_blocked,
            next_safe_action="Open Today or Action Inbox from the shared loop refs.",
        ),
        FounderLoopProductizedSurfaceBinding(
            surface_id="today",
            surface="Today",
            frontend_route_ref="/today",
            backend_route_ref="GET /control-center/today/summary",
            status="backend_owned_home",
            product_posture="home",
            safe_summary=(
                "Today remains the local home surface for what matters, what "
                "needs review, evidence, memory, and blocked posture."
            ),
            shared_ref=shared_ref,
            primary_proof_ref=primary_proof_ref,
            source_refs=today_refs,
            evidence_refs=evidence_refs[:8],
            blocked_state_refs=common_blocked,
            next_safe_action="Review Action Inbox and Proof before claiming outcomes.",
        ),
        FounderLoopProductizedSurfaceBinding(
            surface_id="action_inbox",
            surface="Action Inbox",
            frontend_route_ref="/actions",
            backend_route_ref="GET /control-center/actions/inbox",
            status="receipt_lane_visible",
            product_posture="work_queue",
            safe_summary=(
                "Action Inbox shows exact local work, decision receipts, and "
                "approved local task posture without generic execution."
            ),
            shared_ref=shared_ref,
            primary_proof_ref=primary_proof_ref,
            source_refs=action_refs,
            receipt_refs=receipt_refs,
            evidence_refs=evidence_refs[:8],
            blocked_state_refs=common_blocked,
            next_safe_action="Record only supported receipts or exact approved local task commits.",
        ),
        FounderLoopProductizedSurfaceBinding(
            surface_id="proof",
            surface="Proof",
            frontend_route_ref="/proof",
            backend_route_ref="GET /control-center/proof/index",
            status="backend_owned_proof_index",
            product_posture="proof_spine",
            safe_summary=(
                "Proof ties the same run, receipt, evidence, memory, rollback, "
                "safe disable, and blocked authority refs into inspection detail."
            ),
            shared_ref=shared_ref,
            primary_proof_ref=primary_proof_ref,
            source_refs=[
                "contract-ref:control-center-proof-spine:v1",
                primary_proof_ref,
            ],
            receipt_refs=receipt_refs,
            evidence_refs=evidence_refs[:8],
            memory_candidate_refs=memory_candidate_refs[:6],
            blocked_state_refs=common_blocked,
            next_safe_action="Open Proof before treating a loop event as complete.",
        ),
        FounderLoopProductizedSurfaceBinding(
            surface_id="evidence",
            surface="Evidence",
            frontend_route_ref="/evidence",
            backend_route_ref="GET /control-center/evidence/timeline",
            status="storage_backed_timeline",
            product_posture="evidence_spine",
            safe_summary=(
                "Evidence shows what was proposed, approved, changed, stale, "
                "blocked, and receipt backed from safe refs only."
            ),
            shared_ref=shared_ref,
            primary_proof_ref=primary_proof_ref,
            source_refs=evidence_timeline_refs,
            receipt_refs=receipt_refs,
            evidence_refs=[*bounded_event_refs, *evidence_refs[:6]],
            blocked_state_refs=common_blocked,
            next_safe_action="Use Evidence refs to justify Memory and Action posture.",
        ),
        FounderLoopProductizedSurfaceBinding(
            surface_id="memory",
            surface="Memory",
            frontend_route_ref="/memory",
            backend_route_ref="GET /control-center/memory/review",
            status="reviewed_recall_only",
            product_posture="memory_binding",
            safe_summary=(
                "Memory remains reviewed recall only and explains which evidence "
                "and receipts make memory visible in the loop."
            ),
            shared_ref=shared_ref,
            primary_proof_ref=primary_proof_ref,
            source_refs=memory_candidate_refs,
            receipt_refs=memory_receipt_refs,
            evidence_refs=evidence_refs[:8],
            memory_candidate_refs=memory_candidate_refs,
            blocked_state_refs=common_blocked,
            next_safe_action="Review memory candidates; no hidden memory write or context injection.",
        ),
        FounderLoopProductizedSurfaceBinding(
            surface_id="trust",
            surface="Trust",
            frontend_route_ref="/trust",
            backend_route_ref="GET /control-center/trust-authority/matrix",
            status="authority_map_visible",
            product_posture="authority_map",
            safe_summary=(
                "Trust turns the loop into an operator authority map with enabled, "
                "approval required, planned, and blocked lanes."
            ),
            shared_ref=shared_ref,
            primary_proof_ref=primary_proof_ref,
            source_refs=[
                "contract-ref:usable-authority-trust-authority-map:v1",
                "trust-lane:local-read-preview",
            ],
            evidence_refs=evidence_refs[:6],
            blocked_state_refs=common_blocked,
            next_safe_action="Use Trust to pick the next exact authority promotion.",
        ),
        FounderLoopProductizedSurfaceBinding(
            surface_id="settings",
            surface="Settings",
            frontend_route_ref="/settings",
            backend_route_ref="GET /control-center/settings/status",
            status="read_only_status_backed",
            product_posture="operator_posture",
            safe_summary=(
                "Settings closes the loop with local status, kill switch posture, "
                "feature flag visibility, and product language boundaries."
            ),
            shared_ref=shared_ref,
            primary_proof_ref=primary_proof_ref,
            source_refs=[
                "settings-ref:control-center:status",
                "docs-ref:control-center-product-language-rules",
            ],
            evidence_refs=evidence_refs[:6],
            blocked_state_refs=common_blocked,
            next_safe_action="Inspect Settings posture before proposing any new authority.",
        ),
    ]


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


def _dedupe(values: list[str | None]) -> list[str]:
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


def _validate_safe_text_list(values: list[str], field_name: str) -> None:
    for value in values:
        _validate_safe_text(str(value), field_name)


def _validate_safe_ref(value: str, field_name: str) -> None:
    _validate_safe_text(value, field_name)
    if not _SAFE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} contains unsafe ref")


def _validate_safe_text(value: str, field_name: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe/private content")
