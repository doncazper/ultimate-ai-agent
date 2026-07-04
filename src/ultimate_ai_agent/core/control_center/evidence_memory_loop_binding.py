from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.control_center.proof import derive_control_center_proof_ref
from ultimate_ai_agent.core.control_center.founder_loop_runs_integration import (
    FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF,
)
from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.memory import (
    MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
    MEMORY_REVIEW_WRITE_ROLLBACK_REF,
    MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
)


EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF = (
    "contract-ref:usable-authority-evidence-memory-loop-binding:v1"
)
EVIDENCE_MEMORY_LOOP_BINDING_SOURCE = (
    "python_core_evidence_memory_loop_binding_read_model"
)
EVIDENCE_MEMORY_LOOP_BINDING_CLI_REF = (
    "python scripts/dev/uaa_founder_loop.py inspect-evidence-memory-binding"
)
EVIDENCE_MEMORY_LOOP_BINDING_ROUTE_REFS: tuple[str, ...] = (
    "GET /control-center/today/summary",
    "GET /control-center/memory/review",
    "GET /control-center/evidence/timeline",
)
EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF = (
    "loop-binding-ref:evidence-memory:daily-loop-v1"
)
EVIDENCE_MEMORY_LOOP_BINDING_PROMOTION_PATH_REFS: tuple[str, ...] = (
    "promotion-path:evidence-memory:reviewed-recall-write-exact-scope",
    "promotion-path:evidence-memory:context-injection-separate-contract",
    "promotion-path:evidence-memory:delete-export-separate-contract",
    "promotion-path:evidence-memory:connector-sync-separate-contract",
)
EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-state:evidence-memory-loop:no-memory-truth-authority",
    "blocked-state:evidence-memory-loop:no-runtime-context-injection",
    "blocked-state:evidence-memory-loop:no-automatic-memory-write",
    "blocked-state:evidence-memory-loop:no-memory-delete-or-export",
    "blocked-state:evidence-memory-loop:no-action-execution",
    "blocked-state:evidence-memory-loop:no-connector-write-or-send",
    "blocked-state:evidence-memory-loop:no-provider-model-call",
    "blocked-state:evidence-memory-loop:no-shell-subprocess-execution",
    "blocked-state:evidence-memory-loop:no-browser-execution",
    "blocked-state:evidence-memory-loop:no-background-autonomy",
    "blocked-state:evidence-memory-loop:no-production-authority",
)

_DENIED_FLAGS = (
    "memory_truth_authority",
    "context_injection_authorized",
    "automatic_memory_write_authorized",
    "memory_delete_enabled",
    "memory_export_enabled",
    "action_execution_enabled",
    "connector_write_enabled",
    "connector_send_enabled",
    "provider_model_call_enabled",
    "shell_subprocess_execution_enabled",
    "browser_execution_enabled",
    "background_autonomy_enabled",
    "production_authority_enabled",
)
_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_-]+")


class EvidenceMemoryEvidenceBinding(BaseModel):
    binding_ref: str = Field(..., min_length=1)
    timeline_item_ref: str = Field(..., min_length=1)
    event_ref: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1, max_length=120)
    group_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=180)
    why_recorded: str = Field(..., min_length=1, max_length=600)
    source_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    shared_loop_refs: list[str] = Field(default_factory=list)
    shared_run_refs: list[str] = Field(default_factory=list)
    shared_action_refs: list[str] = Field(default_factory=list)
    shared_proof_refs: list[str] = Field(default_factory=list)
    approval_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    next_safe_action: str = Field(..., min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "EvidenceMemoryEvidenceBinding":
        for field_name in (
            "binding_ref",
            "timeline_item_ref",
            "event_ref",
            "group_ref",
        ):
            validate_execution_ref(str(getattr(self, field_name)), field_name)
        for field_name in ("event_type", "title", "why_recorded", "next_safe_action"):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "source_refs",
            "action_refs",
            "run_refs",
            "proof_refs",
            "shared_loop_refs",
            "shared_run_refs",
            "shared_action_refs",
            "shared_proof_refs",
            "approval_refs",
            "receipt_refs",
            "evidence_refs",
            "memory_candidate_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        return self


class EvidenceMemoryMemoryBinding(BaseModel):
    binding_ref: str = Field(..., min_length=1)
    memory_candidate_ref: str = Field(..., min_length=1)
    review_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=180)
    why_shown: str = Field(..., min_length=1, max_length=600)
    source_refs: list[str] = Field(default_factory=list)
    why_shown_refs: list[str] = Field(default_factory=list)
    related_action_refs: list[str] = Field(default_factory=list)
    related_run_refs: list[str] = Field(default_factory=list)
    related_proof_refs: list[str] = Field(default_factory=list)
    shared_loop_refs: list[str] = Field(default_factory=list)
    shared_run_refs: list[str] = Field(default_factory=list)
    shared_action_refs: list[str] = Field(default_factory=list)
    shared_proof_refs: list[str] = Field(default_factory=list)
    related_evidence_refs: list[str] = Field(default_factory=list)
    decision_receipt_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    reviewed_recall_only: bool = True
    write_posture: str = "reviewed_recall_write_accept_correct_only"
    reviewed_memory_write_scope_ref: str = MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
    reviewed_memory_write_authorized: bool = False
    broad_memory_write_blocked: bool = True
    memory_write_safe_disable_ref: str = MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF
    memory_write_rollback_ref: str = MEMORY_REVIEW_WRITE_ROLLBACK_REF
    context_posture: str = "runtime_context_injection_blocked"
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    memory_truth_authority: bool = False
    context_injection_authorized: bool = False
    automatic_memory_write_authorized: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_binding(self) -> "EvidenceMemoryMemoryBinding":
        for field_name in ("binding_ref", "memory_candidate_ref", "review_ref"):
            validate_execution_ref(str(getattr(self, field_name)), field_name)
        for field_name in (
            "title",
            "why_shown",
            "write_posture",
            "context_posture",
            "next_safe_action",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        for field_name in (
            "source_refs",
            "why_shown_refs",
            "related_action_refs",
            "related_run_refs",
            "related_proof_refs",
            "shared_loop_refs",
            "shared_run_refs",
            "shared_action_refs",
            "shared_proof_refs",
            "related_evidence_refs",
            "decision_receipt_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        for field_name in (
            "reviewed_memory_write_scope_ref",
            "memory_write_safe_disable_ref",
            "memory_write_rollback_ref",
        ):
            validate_execution_ref(str(getattr(self, field_name)), field_name)
        if not self.reviewed_recall_only:
            raise ValueError("Memory binding must remain reviewed recall only")
        if not self.broad_memory_write_blocked:
            raise ValueError("Memory binding must keep broad memory writes blocked")
        if (
            self.reviewed_memory_write_authorized
            and self.write_posture != "accept_correct_reviewed_recall_write_only"
        ):
            raise ValueError("Reviewed memory write authority must stay exact scoped")
        if (
            self.memory_truth_authority
            or self.context_injection_authorized
            or self.automatic_memory_write_authorized
        ):
            raise ValueError("Memory binding must not grant memory/context authority")
        return self


class EvidenceMemoryLoopBindingReadModel(BaseModel):
    schema_version: str = "evidence-memory-loop-binding.v1"
    contract_ref: str = EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF
    source: str = EVIDENCE_MEMORY_LOOP_BINDING_SOURCE
    status: str = "implemented_backend_owned_evidence_memory_loop_binding"
    backend_owned: bool = True
    local_read_model_only: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False
    route_refs: list[str] = Field(
        default_factory=lambda: list(EVIDENCE_MEMORY_LOOP_BINDING_ROUTE_REFS)
    )
    cli_ref: str = EVIDENCE_MEMORY_LOOP_BINDING_CLI_REF
    evidence_binding_count: int = Field(ge=0)
    memory_binding_count: int = Field(ge=0)
    evidence_bindings: list[EvidenceMemoryEvidenceBinding] = Field(default_factory=list)
    memory_bindings: list[EvidenceMemoryMemoryBinding] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_candidate_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    shared_loop_ref: str = EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF
    shared_run_refs: list[str] = Field(default_factory=list)
    shared_action_refs: list[str] = Field(default_factory=list)
    shared_proof_refs: list[str] = Field(default_factory=list)
    reviewed_memory_write_scope_ref: str = MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF
    reviewed_memory_write_authorized_decisions: list[str] = Field(
        default_factory=lambda: ["accept", "correct"]
    )
    reviewed_memory_write_authorized: bool = False
    broad_memory_write_blocked: bool = True
    memory_write_safe_disable_ref: str = MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF
    memory_write_rollback_ref: str = MEMORY_REVIEW_WRITE_ROLLBACK_REF
    promotion_path_refs: list[str] = Field(
        default_factory=lambda: list(EVIDENCE_MEMORY_LOOP_BINDING_PROMOTION_PATH_REFS)
    )
    blocked_authority_refs: list[str] = Field(default_factory=list, min_length=1)
    operator_summary: str = Field(..., min_length=1, max_length=700)
    next_safe_action: str = Field(..., min_length=1, max_length=500)
    authority_boundary: str = Field(..., min_length=1, max_length=900)
    memory_truth_authority: bool = False
    context_injection_authorized: bool = False
    automatic_memory_write_authorized: bool = False
    memory_delete_enabled: bool = False
    memory_export_enabled: bool = False
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    provider_model_call_enabled: bool = False
    shell_subprocess_execution_enabled: bool = False
    browser_execution_enabled: bool = False
    background_autonomy_enabled: bool = False
    production_authority_enabled: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "EvidenceMemoryLoopBindingReadModel":
        if self.schema_version != "evidence-memory-loop-binding.v1":
            raise ValueError("Evidence/Memory binding schema drift")
        if self.contract_ref != EVIDENCE_MEMORY_LOOP_BINDING_CONTRACT_REF:
            raise ValueError("Evidence/Memory binding contract drift")
        if self.source != EVIDENCE_MEMORY_LOOP_BINDING_SOURCE:
            raise ValueError("Evidence/Memory binding source drift")
        if self.evidence_binding_count != len(self.evidence_bindings):
            raise ValueError("Evidence binding count drift")
        if self.memory_binding_count != len(self.memory_bindings):
            raise ValueError("Memory binding count drift")
        if not self.backend_owned or not self.local_read_model_only:
            raise ValueError("Evidence/Memory binding must stay backend-owned")
        if not self.safe_refs_only or self.raw_content_included:
            raise ValueError("Evidence/Memory binding must stay safe-ref only")
        for field_name in (
            "cli_ref",
            "operator_summary",
            "next_safe_action",
            "authority_boundary",
        ):
            validate_safe_execution_text(str(getattr(self, field_name)), field_name)
        _validate_text_list(self.route_refs, "route_refs")
        for field_name in (
            "evidence_refs",
            "memory_candidate_refs",
            "action_refs",
            "run_refs",
            "proof_refs",
            "receipt_refs",
            "shared_run_refs",
            "shared_action_refs",
            "shared_proof_refs",
            "promotion_path_refs",
            "blocked_authority_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        for field_name in (
            "shared_loop_ref",
            "reviewed_memory_write_scope_ref",
            "memory_write_safe_disable_ref",
            "memory_write_rollback_ref",
        ):
            validate_execution_ref(str(getattr(self, field_name)), field_name)
        _validate_text_list(
            self.reviewed_memory_write_authorized_decisions,
            "reviewed_memory_write_authorized_decisions",
        )
        if self.reviewed_memory_write_authorized_decisions != ["accept", "correct"]:
            raise ValueError("Reviewed memory write decisions must stay narrow")
        if not self.broad_memory_write_blocked:
            raise ValueError("Broad memory writes must remain blocked")
        expected_action_refs = _shared_action_refs(
            self.evidence_bindings,
            self.memory_bindings,
        )
        expected_proof_refs = _shared_proof_refs(
            self.evidence_bindings,
            self.memory_bindings,
        )
        if self.action_refs != expected_action_refs:
            raise ValueError("Evidence/Memory action refs drift from shared refs")
        if self.proof_refs != expected_proof_refs:
            raise ValueError("Evidence/Memory proof refs drift from shared refs")
        if self.shared_run_refs != self.run_refs:
            raise ValueError("Evidence/Memory shared run refs drift")
        if self.shared_action_refs != expected_action_refs:
            raise ValueError("Evidence/Memory shared action refs drift")
        if self.shared_proof_refs != expected_proof_refs:
            raise ValueError("Evidence/Memory shared proof refs drift")
        for binding in [*self.evidence_bindings, *self.memory_bindings]:
            if binding.shared_loop_refs != [self.shared_loop_ref]:
                raise ValueError("Evidence/Memory binding shared loop ref drift")
            if binding.shared_run_refs != self.shared_run_refs:
                raise ValueError("Evidence/Memory binding shared run refs drift")
            if binding.shared_action_refs != self.shared_action_refs:
                raise ValueError("Evidence/Memory binding shared action refs drift")
            if binding.shared_proof_refs != self.shared_proof_refs:
                raise ValueError("Evidence/Memory binding shared proof refs drift")
        for flag in _DENIED_FLAGS:
            if getattr(self, flag):
                raise ValueError(f"Evidence/Memory binding must not enable {flag}")
        return self


def build_evidence_memory_loop_binding_read_model(
    *,
    memory_items: list[dict[str, Any]],
    memory_why_shown_items: list[dict[str, Any]],
    memory_to_loop_items: list[dict[str, Any]],
    memory_review_decisions: list[dict[str, Any]],
    evidence_timeline: list[dict[str, Any]],
    evidence_events: list[dict[str, Any]],
    founder_loop_product_proof_read_model: dict[str, Any] | None = None,
    unified_work_thread_read_model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_refs = _run_refs(
        founder_loop_product_proof_read_model,
        unified_work_thread_read_model,
    )
    shared_loop_refs = [EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF]
    memory_bindings = [
        _memory_binding(
            item=item,
            memory_why_shown_items=memory_why_shown_items,
            memory_to_loop_items=memory_to_loop_items,
            memory_review_decisions=memory_review_decisions,
            evidence_timeline=evidence_timeline,
            evidence_events=evidence_events,
            run_refs=run_refs,
            shared_loop_refs=shared_loop_refs,
        )
        for item in memory_items[:8]
    ]
    evidence_bindings = [
        _evidence_binding(
            event=event,
            memory_bindings=memory_bindings,
            run_refs=run_refs,
            shared_loop_refs=shared_loop_refs,
        )
        for event in evidence_events[:12]
    ]
    if not evidence_bindings:
        evidence_bindings = [
            _evidence_binding_from_timeline_item(
                item=item,
                memory_bindings=memory_bindings,
                run_refs=run_refs,
                shared_loop_refs=shared_loop_refs,
            )
            for item in evidence_timeline[:12]
        ]
    shared_action_refs = _shared_action_refs(evidence_bindings, memory_bindings)
    shared_proof_refs = _shared_proof_refs(evidence_bindings, memory_bindings)
    reviewed_memory_write_authorized = any(
        binding.reviewed_memory_write_authorized for binding in memory_bindings
    )
    for binding in memory_bindings:
        binding.shared_action_refs = list(shared_action_refs)
        binding.shared_proof_refs = list(shared_proof_refs)
    for binding in evidence_bindings:
        binding.shared_action_refs = list(shared_action_refs)
        binding.shared_proof_refs = list(shared_proof_refs)
    model = EvidenceMemoryLoopBindingReadModel(
        evidence_binding_count=len(evidence_bindings),
        memory_binding_count=len(memory_bindings),
        evidence_bindings=evidence_bindings,
        memory_bindings=memory_bindings,
        evidence_refs=_merge_refs(
            binding.evidence_refs for binding in evidence_bindings
        ),
        memory_candidate_refs=_merge_refs(
            binding.memory_candidate_ref for binding in memory_bindings
        ),
        action_refs=shared_action_refs,
        run_refs=run_refs,
        proof_refs=shared_proof_refs,
        receipt_refs=_merge_refs(
            [binding.receipt_refs for binding in evidence_bindings],
            [binding.decision_receipt_refs for binding in memory_bindings],
        ),
        shared_loop_ref=EVIDENCE_MEMORY_LOOP_BINDING_SHARED_REF,
        shared_run_refs=run_refs,
        shared_action_refs=shared_action_refs,
        shared_proof_refs=shared_proof_refs,
        reviewed_memory_write_scope_ref=MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
        reviewed_memory_write_authorized_decisions=["accept", "correct"],
        reviewed_memory_write_authorized=reviewed_memory_write_authorized,
        broad_memory_write_blocked=True,
        memory_write_safe_disable_ref=MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
        memory_write_rollback_ref=MEMORY_REVIEW_WRITE_ROLLBACK_REF,
        promotion_path_refs=list(EVIDENCE_MEMORY_LOOP_BINDING_PROMOTION_PATH_REFS),
        blocked_authority_refs=list(EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS),
        operator_summary=(
            f"{len(evidence_bindings)} evidence bindings and {len(memory_bindings)} "
            "memory bindings explain why loop items appear using safe refs only."
        ),
        next_safe_action=(
            "Inspect linked evidence, memory, action, run, and proof refs before "
            "recording a decision or promoting new authority."
        ),
        authority_boundary=(
            "Evidence/Memory loop binding is a backend-owned local read model. "
            "It explains why items appear and how refs connect; it does not make "
            "memory truth, inject context, write memory automatically, delete or "
            "export memory, execute actions, write connectors, call providers or "
            "models, run shell/browser work, start background autonomy, or grant "
            "production authority."
        ),
    )
    return model.model_dump(mode="json")


def _memory_binding(
    *,
    item: dict[str, Any],
    memory_why_shown_items: list[dict[str, Any]],
    memory_to_loop_items: list[dict[str, Any]],
    memory_review_decisions: list[dict[str, Any]],
    evidence_timeline: list[dict[str, Any]],
    evidence_events: list[dict[str, Any]],
    run_refs: list[str],
    shared_loop_refs: list[str],
) -> EvidenceMemoryMemoryBinding:
    candidate_ref = _first_ref(
        item.get("business_memory_candidate_ref"),
        item.get("memory_candidate_ref"),
        item.get("review_ref"),
        fallback="memory-review:unknown",
    )
    review_ref = _first_ref(item.get("review_ref"), fallback=candidate_ref)
    why_items = [
        why
        for why in memory_why_shown_items
        if why.get("memory_ref") == candidate_ref
        or why.get("review_ref") == review_ref
        or why.get("loop_item_ref") in _refs(item.get("business_memory_surface_refs"))
    ]
    loop_items = [
        loop
        for loop in memory_to_loop_items
        if loop.get("memory_candidate_ref") == candidate_ref
        or loop.get("review_ref") == review_ref
    ]
    decisions = [
        receipt
        for receipt in memory_review_decisions
        if receipt.get("candidate_ref") == review_ref
        or receipt.get("review_ref") == review_ref
        or receipt.get("memory_candidate_ref") == candidate_ref
    ]
    related_evidence_refs = _merge_refs(
        item.get("evidence_refs"),
        [why.get("evidence_refs") for why in why_items],
        [loop.get("evidence_refs") for loop in loop_items],
        [
            event.get("event_ref")
            for event in evidence_events
            if candidate_ref in _refs(event.get("source_refs"))
            or review_ref in _refs(event.get("source_refs"))
            or candidate_ref == event.get("group_ref")
            or review_ref == event.get("group_ref")
        ],
        [
            timeline.get("timeline_item_ref")
            for timeline in evidence_timeline
            if candidate_ref in _refs(timeline.get("source_refs"))
            or review_ref in _refs(timeline.get("source_refs"))
        ],
    )
    source_refs = _merge_refs(
        item.get("source_refs"),
        item.get("provenance_refs"),
        [why.get("source_refs") for why in why_items],
        [loop.get("source_refs") for loop in loop_items],
    )
    blocked_refs = _merge_refs(
        item.get("blocked_states"),
        item.get("decision_blocked_state_refs"),
        item.get("business_memory_blocker_refs"),
        [why.get("missing_evidence_refs") for why in why_items],
        [loop.get("blocked_state_refs") for loop in loop_items],
        EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS,
    )
    receipt_refs = _merge_refs(
        item.get("decision_receipt_refs"),
        [receipt.get("receipt_ref") for receipt in decisions],
    )
    related_action_refs = _merge_refs(
        loop.get("follow_up_commitment_refs") for loop in loop_items
    )
    related_proof_refs = [derive_control_center_proof_ref("memory-decision", candidate_ref)]
    reviewed_write_authorized = bool(item.get("memory_write_authorized"))
    why_text = (
        str(why_items[0].get("why_shown"))
        if why_items
        else "Memory appears because reviewed source and evidence refs are in the loop."
    )
    return EvidenceMemoryMemoryBinding(
        binding_ref=f"evidence-memory-binding:memory:{_safe_suffix(candidate_ref)}",
        memory_candidate_ref=candidate_ref,
        review_ref=review_ref,
        title=str(item.get("title") or "Memory Review item"),
        why_shown=why_text,
        source_refs=source_refs,
        why_shown_refs=_merge_refs(
            [why.get("loop_item_ref") for why in why_items],
            [loop.get("loop_item_ref") for loop in loop_items],
        ),
        related_action_refs=related_action_refs,
        related_run_refs=run_refs,
        related_proof_refs=related_proof_refs,
        shared_loop_refs=shared_loop_refs,
        shared_run_refs=run_refs,
        shared_action_refs=related_action_refs,
        shared_proof_refs=related_proof_refs,
        related_evidence_refs=related_evidence_refs,
        decision_receipt_refs=receipt_refs,
        blocked_authority_refs=blocked_refs,
        reviewed_recall_only=True,
        write_posture=(
            "accept_correct_reviewed_recall_write_only"
            if reviewed_write_authorized
            else "general_memory_write_blocked"
        ),
        reviewed_memory_write_scope_ref=MEMORY_REVIEW_EXACT_WRITE_SCOPE_REF,
        reviewed_memory_write_authorized=reviewed_write_authorized,
        broad_memory_write_blocked=True,
        memory_write_safe_disable_ref=MEMORY_REVIEW_WRITE_SAFE_DISABLE_REF,
        memory_write_rollback_ref=MEMORY_REVIEW_WRITE_ROLLBACK_REF,
        context_posture="runtime_context_injection_blocked",
        next_safe_action=str(
            item.get("next_safe_action")
            or "Review memory source, evidence, stale-state, and approval posture."
        ),
    )


def _evidence_binding(
    *,
    event: dict[str, Any],
    memory_bindings: list[EvidenceMemoryMemoryBinding],
    run_refs: list[str],
    shared_loop_refs: list[str],
) -> EvidenceMemoryEvidenceBinding:
    event_ref = str(event.get("event_ref") or "evidence-event:unknown")
    timeline_item_ref = str(
        event.get("timeline_item_ref") or f"evidence-timeline:unknown:{_safe_suffix(event_ref)}"
    )
    source_refs = _merge_refs(event.get("source_refs"), event.get("status_refs"))
    memory_refs = _related_memory_refs(source_refs, memory_bindings)
    action_refs = _filter_prefixes(source_refs, ("founder-action:", "action:"))
    proof_refs = [derive_control_center_proof_ref("evidence-event", event_ref)]
    evidence_refs = _merge_refs(
        event_ref,
        timeline_item_ref,
        event.get("event_type_ref"),
        event.get("source_refs"),
        event.get("status_refs"),
    )
    why_recorded = _history_answer(event, "proposed") or str(
        event.get("safe_summary") or "Evidence event explains a loop state with safe refs."
    )
    return EvidenceMemoryEvidenceBinding(
        binding_ref=f"evidence-memory-binding:evidence:{_safe_suffix(event_ref)}",
        timeline_item_ref=timeline_item_ref,
        event_ref=event_ref,
        event_type=str(event.get("event_type") or event.get("item_kind") or "evidence"),
        group_ref=str(event.get("group_ref") or timeline_item_ref),
        title=str(event.get("title") or "Evidence Timeline item"),
        why_recorded=why_recorded,
        source_refs=source_refs,
        action_refs=action_refs,
        run_refs=run_refs,
        proof_refs=proof_refs,
        shared_loop_refs=shared_loop_refs,
        shared_run_refs=run_refs,
        shared_action_refs=action_refs,
        shared_proof_refs=proof_refs,
        approval_refs=_refs(event.get("approval_refs")),
        receipt_refs=_refs(event.get("receipt_refs")),
        evidence_refs=evidence_refs,
        memory_candidate_refs=memory_refs,
        blocked_authority_refs=_merge_refs(
            event.get("blocked_states"),
            EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS,
        ),
        next_safe_action=str(
            event.get("next_safe_action")
            or "Inspect linked refs; do not execute from evidence."
        ),
    )


def _evidence_binding_from_timeline_item(
    *,
    item: dict[str, Any],
    memory_bindings: list[EvidenceMemoryMemoryBinding],
    run_refs: list[str],
    shared_loop_refs: list[str],
) -> EvidenceMemoryEvidenceBinding:
    timeline_item_ref = str(item.get("timeline_item_ref") or "evidence-timeline:unknown")
    event_ref = f"evidence-event:timeline:{_safe_suffix(timeline_item_ref)}"
    source_refs = _merge_refs(item.get("source_refs"), item.get("status_refs"))
    memory_refs = _related_memory_refs(source_refs, memory_bindings)
    action_refs = _filter_prefixes(source_refs, ("founder-action:", "action:"))
    proof_refs = [derive_control_center_proof_ref("evidence-event", event_ref)]
    why_recorded = _history_answer(item, "proposed") or str(
        item.get("safe_summary") or "Evidence timeline item explains loop state."
    )
    return EvidenceMemoryEvidenceBinding(
        binding_ref=f"evidence-memory-binding:evidence:{_safe_suffix(timeline_item_ref)}",
        timeline_item_ref=timeline_item_ref,
        event_ref=event_ref,
        event_type=str(item.get("item_kind") or "timeline_item"),
        group_ref=timeline_item_ref,
        title=str(item.get("title") or "Evidence Timeline item"),
        why_recorded=why_recorded,
        source_refs=source_refs,
        action_refs=action_refs,
        run_refs=run_refs,
        proof_refs=proof_refs,
        shared_loop_refs=shared_loop_refs,
        shared_run_refs=run_refs,
        shared_action_refs=action_refs,
        shared_proof_refs=proof_refs,
        approval_refs=_merge_refs(
            item.get("history_answers", {}).get("approved", {}).get("refs", [])
            if isinstance(item.get("history_answers"), dict)
            else []
        ),
        receipt_refs=_refs(item.get("receipt_refs")),
        evidence_refs=_merge_refs(event_ref, timeline_item_ref, source_refs),
        memory_candidate_refs=memory_refs,
        blocked_authority_refs=_merge_refs(
            item.get("blocked_states"),
            EVIDENCE_MEMORY_LOOP_BINDING_BLOCKED_AUTHORITY_REFS,
        ),
        next_safe_action=str(
            item.get("next_safe_action")
            or "Inspect linked refs; do not execute from evidence."
        ),
    )


def _related_memory_refs(
    source_refs: list[str],
    memory_bindings: list[EvidenceMemoryMemoryBinding],
) -> list[str]:
    source_set = set(source_refs)
    refs: list[str] = []
    for binding in memory_bindings:
        if (
            binding.memory_candidate_ref in source_set
            or binding.review_ref in source_set
            or source_set.intersection(binding.related_evidence_refs)
        ):
            refs.append(binding.memory_candidate_ref)
    return _merge_refs(refs)


def _run_refs(
    founder_loop_product_proof_read_model: dict[str, Any] | None,
    unified_work_thread_read_model: dict[str, Any] | None,
) -> list[str]:
    return _merge_refs(
        _refs((founder_loop_product_proof_read_model or {}).get("run_refs")),
        _refs((unified_work_thread_read_model or {}).get("run_refs")),
        [FOUNDER_LOOP_RUNS_INTEGRATION_PRIMARY_RUN_REF],
    )


def _shared_action_refs(
    evidence_bindings: list[EvidenceMemoryEvidenceBinding],
    memory_bindings: list[EvidenceMemoryMemoryBinding],
) -> list[str]:
    return _merge_refs(
        [binding.action_refs for binding in evidence_bindings],
        [binding.related_action_refs for binding in memory_bindings],
    )


def _shared_proof_refs(
    evidence_bindings: list[EvidenceMemoryEvidenceBinding],
    memory_bindings: list[EvidenceMemoryMemoryBinding],
) -> list[str]:
    return _merge_refs(
        [binding.proof_refs for binding in evidence_bindings],
        [binding.related_proof_refs for binding in memory_bindings],
    )


def _history_answer(item: dict[str, Any], key: str) -> str | None:
    answers = item.get("history_answers")
    if not isinstance(answers, dict):
        return None
    answer = answers.get(key)
    if not isinstance(answer, dict):
        return None
    value = answer.get("answer")
    if not isinstance(value, str) or not value:
        return None
    return value


def _filter_prefixes(values: list[str], prefixes: tuple[str, ...]) -> list[str]:
    return _merge_refs(value for value in values if value.startswith(prefixes))


def _first_ref(*values: Any, fallback: str) -> str:
    for value in values:
        refs = _refs(value if isinstance(value, list | tuple | set) else [value])
        if refs:
            return refs[0]
    validate_execution_ref(fallback, "fallback_ref")
    return fallback


def _safe_suffix(value: str) -> str:
    suffix = _SAFE_SUFFIX_RE.sub("-", value.lower()).strip("-_")[:96]
    return suffix or "unknown"


def _refs(values: Any) -> list[str]:
    if isinstance(values, str):
        iterable: list[Any] = [values]
    elif isinstance(values, list | tuple | set):
        iterable = list(values)
    elif hasattr(values, "__iter__") and not isinstance(values, bytes | dict):
        iterable = list(values)
    else:
        iterable = []
    refs: list[str] = []
    for value in iterable:
        if isinstance(value, list | tuple | set):
            nested = _refs(value)
            for ref in nested:
                if ref not in refs:
                    refs.append(ref)
            continue
        if not isinstance(value, str) or not value:
            continue
        try:
            validate_execution_ref(value, "ref")
        except ValueError:
            continue
        if value not in refs:
            refs.append(value)
    return refs


def _merge_refs(*groups: Any) -> list[str]:
    refs: list[str] = []
    for group in groups:
        for ref in _refs(group):
            if ref not in refs:
                refs.append(ref)
    return refs


def _validate_ref_list(refs: list[str], field_name: str) -> None:
    for ref in refs:
        validate_execution_ref(ref, field_name)


def _validate_text_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_safe_execution_text(value, field_name)
