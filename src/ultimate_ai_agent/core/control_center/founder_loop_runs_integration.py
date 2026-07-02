from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)


FOUNDER_LOOP_RUNS_INTEGRATION_CONTRACT_REF = (
    "contract-ref:founder-loop-runs-integration:v1"
)
FOUNDER_LOOP_RUNS_INTEGRATION_READ_MODEL_SOURCE = (
    "python_core_founder_loop_runs_integration_read_model"
)
FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF = (
    "run-ref:founder-loop-v1:governed-local-loop"
)
FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF = (
    "proof-ref:founder-loop-v1:governed-local-loop"
)
FOUNDER_LOOP_RUNS_INTEGRATION_SURFACE_ORDER: tuple[str, ...] = (
    "morning_briefing",
    "today",
    "action_inbox",
    "decision_receipt",
    "evidence_timeline",
    "memory_review",
    "weekly_review",
)
FOUNDER_LOOP_RUNS_INTEGRATION_REQUIRED_BLOCKED_REFS: tuple[str, ...] = (
    "blocked-state:founder-loop-runs-no-provider-model-call",
    "blocked-state:founder-loop-runs-no-connector-write",
    "blocked-state:founder-loop-runs-no-browser-or-live-web",
    "blocked-state:founder-loop-runs-no-shell-execution",
    "blocked-state:founder-loop-runs-no-background-autonomy",
    "blocked-state:founder-loop-runs-no-ui-only-truth",
    "blocked-state:founder-loop-runs-no-memory-write-authority",
    "blocked-state:founder-loop-runs-no-context-injection",
    "blocked-state:founder-loop-runs-no-production-authority",
)

FounderLoopRunsIntegrationSurfaceId = Literal[
    "morning_briefing",
    "today",
    "action_inbox",
    "decision_receipt",
    "evidence_timeline",
    "memory_review",
    "weekly_review",
]

_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_-]+")
_DENIED_FLAGS = (
    "provider_model_call_enabled",
    "runtime_model_call_enabled",
    "connector_write_enabled",
    "connector_send_enabled",
    "browser_execution_enabled",
    "live_web_enabled",
    "shell_subprocess_execution_enabled",
    "scheduler_enabled",
    "background_autonomy_enabled",
    "action_execution_enabled",
    "approval_authority_enabled",
    "memory_write_authorized",
    "context_injection_authorized",
    "ui_mutation_authority_enabled",
    "production_authority_enabled",
)


class FounderLoopRunsIntegrationSurfaceBinding(BaseModel):
    surface_id: FounderLoopRunsIntegrationSurfaceId
    surface: str = Field(..., min_length=1, max_length=80)
    status: str = Field(..., min_length=1, max_length=120)
    frontend_route_ref: str = Field(..., min_length=1, max_length=80)
    backend_route_ref: str = Field(..., min_length=1, max_length=160)
    run_ref: str = Field(..., min_length=1)
    proof_ref: str = Field(..., min_length=1)
    proof_detail_ref: str = Field(..., min_length=1)
    proof_detail_route_ref: str = Field(..., min_length=1, max_length=160)
    action_source_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_event_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    operator_run_event_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    next_safe_action: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "FounderLoopRunsIntegrationSurfaceBinding":
        if self.run_ref != FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF:
            raise ValueError("Founder Loop surface bindings must share one run ref")
        for field_name in (
            "run_ref",
            "proof_ref",
            "proof_detail_ref",
        ):
            validate_execution_ref(getattr(self, field_name), field_name)
        for field_name in (
            "surface",
            "status",
            "frontend_route_ref",
            "backend_route_ref",
            "proof_detail_route_ref",
            "safe_summary",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "action_source_refs",
            "approval_refs",
            "receipt_refs",
            "evidence_refs",
            "evidence_event_refs",
            "memory_candidate_refs",
            "operator_run_event_refs",
            "blocked_state_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


class FounderLoopRunsIntegrationReadModel(BaseModel):
    schema_version: str = "founder-loop-runs-integration.v1"
    contract_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_CONTRACT_REF
    status: str = "implemented_backend_owned_run_proof_refs_safe_refs_only"
    source: str = FOUNDER_LOOP_RUNS_INTEGRATION_READ_MODEL_SOURCE
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    redacted_summaries_only: bool = True
    raw_payloads_persisted: bool = False
    ui_truth_source: str = "python_core_read_model"
    primary_run_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF
    primary_proof_ref: str = FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF
    surface_order: list[FounderLoopRunsIntegrationSurfaceId] = Field(
        default_factory=lambda: list(FOUNDER_LOOP_RUNS_INTEGRATION_SURFACE_ORDER)
    )
    surface_count: int = Field(default=0, ge=0)
    run_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    proof_detail_refs: list[str] = Field(default_factory=list)
    action_source_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_event_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    operator_run_event_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    surface_bindings: list[FounderLoopRunsIntegrationSurfaceBinding] = Field(
        default_factory=list
    )
    action_origin_posture: str = (
        "action_refs_are_bound_to_the_shared_founder_loop_run_ref"
    )
    decision_receipt_posture: str = (
        "decisions_are_explained_by_backend_receipt_refs_or_explicit_none"
    )
    evidence_path_posture: str = (
        "state_is_supported_by_safe_evidence_refs_and_operator_run_event_refs"
    )
    proof_detail_posture: str = (
        "proof_refs_available_dedicated_universal_proof_route_not_present"
    )
    memory_candidate_posture: str = (
        "memory_candidates_are_related_by_safe_refs_or_explicit_none"
    )
    weekly_review_posture: str = (
        "weekly_review_summarizes_same_loop_state_from_safe_refs"
    )
    authority_boundary: str = (
        "Founder Loop runs integration is a backend-owned read model over local "
        "safe refs. It does not grant approval, execute actions, call providers "
        "or models, write or send connectors, browse live web, run shell work, "
        "schedule background autonomy, write memory, inject context, or confer "
        "production authority."
    )
    next_safe_action: str = (
        "Inspect run, proof, receipt, evidence, and blocker refs before claiming "
        "a Founder Loop outcome."
    )
    provider_model_call_enabled: bool = False
    runtime_model_call_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    browser_execution_enabled: bool = False
    live_web_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    scheduler_enabled: bool = False
    background_autonomy_enabled: bool = False
    action_execution_enabled: bool = False
    approval_authority_enabled: bool = False
    memory_write_authorized: bool = False
    context_injection_authorized: bool = False
    ui_mutation_authority_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "FounderLoopRunsIntegrationReadModel":
        if self.schema_version != "founder-loop-runs-integration.v1":
            raise ValueError("unexpected Founder Loop runs integration schema")
        if self.contract_ref != FOUNDER_LOOP_RUNS_INTEGRATION_CONTRACT_REF:
            raise ValueError("unexpected Founder Loop runs integration contract")
        if self.source != FOUNDER_LOOP_RUNS_INTEGRATION_READ_MODEL_SOURCE:
            raise ValueError("unexpected Founder Loop runs integration source")
        for field_name in (
            "backend_owned",
            "local_read_model_only",
            "safe_refs_only",
            "redacted_summaries_only",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"{field_name} must remain true")
        if self.raw_payloads_persisted:
            raise ValueError("Founder Loop runs integration must not persist payloads")
        if self.ui_truth_source != "python_core_read_model":
            raise ValueError(
                "Founder Loop runs integration truth must be backend-owned"
            )
        if self.surface_order != list(FOUNDER_LOOP_RUNS_INTEGRATION_SURFACE_ORDER):
            raise ValueError("Founder Loop runs integration surface order drifted")
        if self.surface_count != len(self.surface_bindings):
            raise ValueError("Founder Loop runs integration surface count mismatch")
        if [
            binding.surface_id for binding in self.surface_bindings
        ] != self.surface_order:
            raise ValueError("Founder Loop runs integration bindings must follow order")
        if self.primary_run_ref not in self.run_refs:
            raise ValueError("Founder Loop runs integration missing primary run ref")
        if self.primary_proof_ref not in self.proof_refs:
            raise ValueError("Founder Loop runs integration missing primary proof ref")
        missing_blockers = set(
            FOUNDER_LOOP_RUNS_INTEGRATION_REQUIRED_BLOCKED_REFS
        ) - set(self.blocked_authority_refs)
        if missing_blockers:
            raise ValueError("Founder Loop runs integration missing blocked refs")
        for field_name in _DENIED_FLAGS:
            if getattr(self, field_name):
                raise ValueError(f"{field_name} must remain false")
        for field_name in (
            "contract_ref",
            "primary_run_ref",
            "primary_proof_ref",
        ):
            validate_execution_ref(getattr(self, field_name), field_name)
        for field_name in (
            "status",
            "source",
            "ui_truth_source",
            "action_origin_posture",
            "decision_receipt_posture",
            "evidence_path_posture",
            "proof_detail_posture",
            "memory_candidate_posture",
            "weekly_review_posture",
            "authority_boundary",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "run_refs",
            "proof_refs",
            "proof_detail_refs",
            "action_source_refs",
            "approval_refs",
            "receipt_refs",
            "evidence_refs",
            "evidence_event_refs",
            "memory_candidate_refs",
            "operator_run_event_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


def build_founder_loop_runs_integration_read_model(
    *,
    actions: list[dict[str, Any]],
    briefing_items: list[dict[str, Any]],
    memory_items: list[dict[str, Any]],
    evidence_timeline: list[dict[str, Any]],
    memory_review_decisions: list[dict[str, Any]],
    founder_loop_product_proof_read_model: dict[str, Any],
    weekly_ceo_review_v1_read_model: dict[str, Any],
    evidence_event_refs: list[str],
) -> dict[str, Any]:
    product_steps_by_id = {
        str(step.get("step_id")): step
        for step in founder_loop_product_proof_read_model.get("steps", [])
        if isinstance(step, dict)
    }
    action_refs = _refs(action.get("item_ref") for action in actions)
    approval_refs = _refs(
        ref
        for action in actions
        for ref in (
            action.get("approval_envelope_ref"),
            action.get("local_task_commit_approval_ref"),
        )
    )
    receipt_refs = _unique_refs(
        [
            *[
                ref
                for action in actions
                for ref in _refs(action.get("receipt_refs"))
                if ref.startswith("receipt:")
            ],
            *[
                str(decision.get("receipt_ref"))
                for decision in memory_review_decisions
                if decision.get("receipt_ref")
            ],
            *_refs(founder_loop_product_proof_read_model.get("receipt_refs")),
            *_refs(weekly_ceo_review_v1_read_model.get("receipt_refs")),
        ]
    )
    evidence_refs = _unique_refs(
        [
            FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
            "evidence-ref:founder-loop-runs-integration",
            *_refs(founder_loop_product_proof_read_model.get("evidence_refs")),
            *_refs(weekly_ceo_review_v1_read_model.get("evidence_refs")),
            *[
                ref
                for item in evidence_timeline
                for ref in _refs(item.get("evidence_refs"))
            ],
        ]
    )
    memory_candidate_refs = _unique_refs(
        [
            *[
                ref
                for item in memory_items
                for ref in _refs(
                    [
                        item.get("business_memory_candidate_ref"),
                        item.get("review_ref"),
                    ]
                )
            ],
            *_refs(
                founder_loop_product_proof_read_model.get(
                    "memory_review_candidate_refs"
                )
            ),
        ]
    )
    operator_run_event_refs = _unique_refs(
        _operator_run_event_ref(event_ref) for event_ref in evidence_event_refs
    )
    blocked_refs = _unique_refs(
        [
            *FOUNDER_LOOP_RUNS_INTEGRATION_REQUIRED_BLOCKED_REFS,
            *_refs(founder_loop_product_proof_read_model.get("blocked_authority_refs")),
            *_refs(weekly_ceo_review_v1_read_model.get("blocked_authority_refs")),
            *[
                ref
                for action in actions
                for ref in _refs(action.get("action_blocked_state_refs"))
            ],
            *[
                ref
                for item in memory_items
                for ref in _refs(item.get("blocked_states"))
            ],
        ]
    )

    bindings = [
        _surface_binding(
            step_id=step_id,
            product_step=product_steps_by_id.get(step_id, {}),
            action_refs=action_refs,
            approval_refs=approval_refs,
            receipt_refs=receipt_refs,
            evidence_refs=evidence_refs,
            memory_candidate_refs=memory_candidate_refs,
            operator_run_event_refs=operator_run_event_refs,
            blocked_refs=blocked_refs,
            briefing_refs=_refs(item.get("briefing_ref") for item in briefing_items),
            weekly_refs=_refs(
                [
                    weekly_ceo_review_v1_read_model.get("review_period_ref"),
                    *weekly_ceo_review_v1_read_model.get("carry_forward_refs", []),
                    *weekly_ceo_review_v1_read_model.get("next_week_priority_refs", []),
                ]
            ),
            evidence_timeline_refs=_refs(
                item.get("timeline_item_ref") for item in evidence_timeline
            ),
        )
        for step_id in FOUNDER_LOOP_RUNS_INTEGRATION_SURFACE_ORDER
    ]
    model = FounderLoopRunsIntegrationReadModel(
        surface_count=len(bindings),
        run_refs=[FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
        proof_refs=_unique_refs(
            [
                FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_PROOF_REF,
                *[binding.proof_ref for binding in bindings],
            ]
        ),
        proof_detail_refs=_unique_refs(
            binding.proof_detail_ref for binding in bindings
        ),
        action_source_refs=action_refs,
        approval_refs=approval_refs,
        receipt_refs=receipt_refs,
        evidence_refs=evidence_refs,
        evidence_event_refs=_unique_refs(evidence_event_refs),
        memory_candidate_refs=memory_candidate_refs,
        operator_run_event_refs=operator_run_event_refs,
        blocked_authority_refs=blocked_refs,
        surface_bindings=bindings,
        memory_candidate_posture=(
            "memory_candidate_refs_visible"
            if memory_candidate_refs
            else "memory_candidate_refs_explicit_none"
        ),
    )
    return model.model_dump(mode="json")


def _surface_binding(
    *,
    step_id: str,
    product_step: dict[str, Any],
    action_refs: list[str],
    approval_refs: list[str],
    receipt_refs: list[str],
    evidence_refs: list[str],
    memory_candidate_refs: list[str],
    operator_run_event_refs: list[str],
    blocked_refs: list[str],
    briefing_refs: list[str],
    weekly_refs: list[str],
    evidence_timeline_refs: list[str],
) -> FounderLoopRunsIntegrationSurfaceBinding:
    surface = _surface_label(step_id)
    proof_ref = f"proof-ref:founder-loop-v1:{_safe_suffix(step_id)}"
    source_refs = _source_refs_for_step(
        step_id=step_id,
        product_step=product_step,
        action_refs=action_refs,
        briefing_refs=briefing_refs,
        weekly_refs=weekly_refs,
        evidence_timeline_refs=evidence_timeline_refs,
    )
    step_receipts = _step_refs(step_id, receipt_refs, product_step, "receipt_refs")
    step_evidence = _step_refs(step_id, evidence_refs, product_step, "evidence_refs")
    step_memory = memory_candidate_refs if step_id == "memory_review" else []
    step_approvals = (
        approval_refs if step_id in {"action_inbox", "decision_receipt"} else []
    )
    safe_summary = _safe_summary_for_step(
        step_id=step_id,
        product_step=product_step,
        has_memory=bool(memory_candidate_refs),
        has_receipts=bool(receipt_refs),
    )
    return FounderLoopRunsIntegrationSurfaceBinding(
        surface_id=step_id,  # type: ignore[arg-type]
        surface=surface,
        status=str(product_step.get("status") or "backend_owned_run_ref_projection"),
        frontend_route_ref=_frontend_route_ref(step_id, product_step),
        backend_route_ref=_backend_route_ref(step_id, product_step),
        run_ref=FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
        proof_ref=proof_ref,
        proof_detail_ref=f"proof-detail-ref:founder-loop-v1:{_safe_suffix(step_id)}",
        proof_detail_route_ref="proof-detail-route:planned-universal-proof",
        action_source_refs=source_refs,
        approval_refs=step_approvals,
        receipt_refs=step_receipts,
        evidence_refs=[proof_ref, *step_evidence],
        memory_candidate_refs=step_memory,
        operator_run_event_refs=operator_run_event_refs[:8],
        blocked_state_refs=_unique_refs(
            [
                *blocked_refs[:12],
                *_refs(product_step.get("blocked_state_refs")),
            ]
        ),
        safe_summary=safe_summary,
        next_safe_action=str(
            product_step.get("next_safe_action")
            or "Inspect run and proof refs before claiming this surface outcome."
        ),
    )


def _surface_label(step_id: str) -> str:
    return {
        "morning_briefing": "Morning Briefing",
        "today": "Today",
        "action_inbox": "Action Inbox",
        "decision_receipt": "Decision Receipt",
        "evidence_timeline": "Evidence Timeline",
        "memory_review": "Memory Review",
        "weekly_review": "Weekly Review",
    }[step_id]


def _frontend_route_ref(step_id: str, product_step: dict[str, Any]) -> str:
    explicit = product_step.get("frontend_route_ref")
    if isinstance(explicit, str) and explicit:
        return explicit
    return {
        "morning_briefing": "/briefing",
        "today": "/today",
        "action_inbox": "/actions",
        "decision_receipt": "/actions",
        "evidence_timeline": "/evidence",
        "memory_review": "/memory",
        "weekly_review": "/today",
    }[step_id]


def _backend_route_ref(step_id: str, product_step: dict[str, Any]) -> str:
    explicit = product_step.get("backend_route_ref")
    if isinstance(explicit, str) and explicit:
        return explicit
    return {
        "morning_briefing": "GET /control-center/morning-briefing/summary",
        "today": "GET /control-center/today/summary",
        "action_inbox": "GET /control-center/actions/inbox",
        "decision_receipt": "POST /control-center/actions/{action_id}/{decision}",
        "evidence_timeline": "GET /control-center/evidence/timeline",
        "memory_review": "GET /control-center/memory/review",
        "weekly_review": "GET /control-center/today/summary",
    }[step_id]


def _source_refs_for_step(
    *,
    step_id: str,
    product_step: dict[str, Any],
    action_refs: list[str],
    briefing_refs: list[str],
    weekly_refs: list[str],
    evidence_timeline_refs: list[str],
) -> list[str]:
    product_source_refs = _refs(product_step.get("source_refs"))
    if product_source_refs:
        return product_source_refs
    if step_id == "morning_briefing":
        return briefing_refs
    if step_id in {"action_inbox", "decision_receipt"}:
        return action_refs
    if step_id == "evidence_timeline":
        return evidence_timeline_refs
    if step_id == "weekly_review":
        return weekly_refs
    return product_source_refs


def _step_refs(
    step_id: str,
    aggregate_refs: list[str],
    product_step: dict[str, Any],
    field_name: str,
) -> list[str]:
    product_refs = _refs(product_step.get(field_name))
    if product_refs:
        return product_refs
    if step_id in {
        "decision_receipt",
        "action_inbox",
        "evidence_timeline",
        "weekly_review",
    }:
        return aggregate_refs[:12]
    return aggregate_refs[:6]


def _safe_summary_for_step(
    *,
    step_id: str,
    product_step: dict[str, Any],
    has_memory: bool,
    has_receipts: bool,
) -> str:
    explicit = product_step.get("safe_summary")
    if isinstance(explicit, str) and explicit:
        return explicit
    if step_id == "action_inbox":
        return "This action set came from the shared Founder Loop run ref."
    if step_id == "decision_receipt":
        return (
            "Decision receipt refs explain what changed."
            if has_receipts
            else "No decision receipt is recorded yet, and the model says so explicitly."
        )
    if step_id == "memory_review":
        return (
            "Memory Review has related candidate refs in the shared loop."
            if has_memory
            else "Memory Review has no related candidate refs in this loop state."
        )
    return "This surface is bound to the shared Founder Loop run and proof refs."


def _operator_run_event_ref(event_ref: object) -> str | None:
    ref = _safe_ref_or_none(event_ref)
    if not ref:
        return None
    return f"operator-run-event:{_safe_suffix(ref)}"


def _safe_suffix(value: object) -> str:
    candidate = str(value).strip().lower().replace(":", "-").replace("/", "-")
    candidate = _SAFE_SUFFIX_RE.sub("-", candidate).strip("-")
    return candidate[:80] or "unknown"


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


def _unique_refs(values: Any) -> list[str]:
    return sorted(set(_refs(values)))


def _safe_ref_or_none(value: object) -> str | None:
    if value is None:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None
    try:
        validate_execution_ref(candidate, "ref")
    except ValueError:
        return None
    return candidate


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        validate_execution_ref(str(ref), field_name)
