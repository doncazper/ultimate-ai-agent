from __future__ import annotations

import hashlib
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.action_envelopes import (
    PlanActionEnvelope,
    build_plan_action_envelope,
)
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_safe_task_text,
    validate_task_ref,
)


TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF = (
    "contract-ref:uaa-p1-090-task-decomposition-proposal-engine:v1"
)
TASK_DECOMPOSITION_PROPOSAL_REVIEW_ACTIONS = ("approve", "defer", "reject")
TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS = (
    "blocked-authority:no-runtime-model-call",
    "blocked-authority:no-provider-call",
    "blocked-authority:no-tool-execution",
    "blocked-authority:no-action-execution",
    "blocked-authority:no-workflow-execution",
    "blocked-authority:no-memory-write",
    "blocked-authority:no-context-injection",
    "blocked-authority:no-shell-subprocess",
    "blocked-authority:no-browser-network",
    "blocked-authority:no-connector-write",
    "blocked-authority:no-autonomous-planning-authority",
    "blocked-authority:no-production-authority",
)
TASK_DECOMPOSITION_PROPOSAL_AFFECTED_SURFACE_REFS = (
    "surface-ref:today",
    "surface-ref:plans",
    "surface-ref:actions",
    "surface-ref:evidence",
)
TASK_DECOMPOSITION_ACTION_KIND = "task_decomposition_proposal"
TASK_DECOMPOSITION_PROPOSAL_SOURCE = "python_core_task_decomposition_proposal_engine"

_DENIED_FLAG_FIELDS = (
    "runtime_model_call_allowed",
    "provider_call_allowed",
    "tool_execution_allowed",
    "action_execution_allowed",
    "workflow_execution_allowed",
    "memory_write_allowed",
    "context_injection_allowed",
    "shell_subprocess_allowed",
    "browser_network_allowed",
    "connector_write_allowed",
    "autonomous_planning_authority_allowed",
    "production_authority_allowed",
)
_NO_EFFECT_FALSE_FIELDS = (
    "proposal_authority_granted",
    "runtime_authority_granted",
    "autonomous_planning_authority",
    "execution_authorized",
    "execution_performed",
    "task_execution_enabled",
    "task_execution_performed",
    "workflow_execution_enabled",
    "workflow_execution_performed",
    "action_execution_enabled",
    "action_execution_performed",
    "tool_execution_enabled",
    "tool_execution_performed",
    "scheduler_registered",
    "background_worker_started",
    "approval_ref_authority",
    "approval_grant_capture_enabled",
    "local_task_commit_eligible",
    "memory_write_authorized",
    "memory_write_performed",
    "context_injection_authorized",
    "context_injection_performed",
    "connector_write_enabled",
    "connector_write_performed",
    "shell_subprocess_execution_enabled",
    "shell_subprocess_execution_performed",
    "browser_network_enabled",
    "browser_network_performed",
    "model_provider_authority_allowed",
    "model_provider_call_performed",
    "public_beta_claim_enabled",
    "public_distribution_claim_enabled",
    "production_authority_enabled",
)
_NO_EFFECT_TRUE_FIELDS = (
    "review_only",
    "proposal_only",
    "safe_refs_only",
    "no_model_call_performed",
    "no_provider_call_performed",
    "no_tool_execution_performed",
    "no_action_execution_performed",
    "no_workflow_execution_performed",
    "no_memory_write_performed",
    "no_context_injection_performed",
    "no_shell_subprocess_performed",
    "no_browser_network_performed",
    "no_connector_write_performed",
)
_SAFE_SUFFIX_RE = re.compile(r"[^a-z0-9_.@-]+")


class TaskDecompositionRiskClass(str, Enum):
    none = "none"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    blocked = "blocked"


class TaskDecompositionAmbiguityPosture(str, Enum):
    clear = "clear"
    needs_operator_clarification = "needs_operator_clarification"
    missing_evidence = "missing_evidence"
    blocked = "blocked"


class TaskDecompositionBlockedState(BaseModel):
    blocked_state_ref: str = Field(..., min_length=1)
    reason_ref: str = Field(..., min_length=1)
    blocked_authority_ref: str = Field(..., min_length=1)
    safe_summary: str = Field(..., min_length=1, max_length=400)
    affected_surface_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    next_safe_operator_action: str = Field(..., min_length=1, max_length=240)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_blocked_state(self) -> "TaskDecompositionBlockedState":
        _validate_ref_fields(
            self,
            "blocked_state_ref",
            "reason_ref",
            "blocked_authority_ref",
        )
        _validate_ref_list(self.affected_surface_refs, "affected_surface_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(
            self.next_safe_operator_action,
            "next_safe_operator_action",
        )
        return self


class TaskDecompositionRisk(BaseModel):
    risk_ref: str = Field(..., min_length=1)
    risk_class: TaskDecompositionRiskClass
    safe_summary: str = Field(..., min_length=1, max_length=400)
    mitigation_ref: str = Field(..., min_length=1)
    blocked_authority_ref: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_risk(self) -> "TaskDecompositionRisk":
        _validate_ref_fields(
            self,
            "risk_ref",
            "mitigation_ref",
            "blocked_authority_ref",
        )
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        return self


class TaskDecompositionStep(BaseModel):
    step_ref: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=120)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    depends_on: list[str] = Field(default_factory=list)
    dependency_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list, min_length=1)
    ambiguity_refs: list[str] = Field(default_factory=list)
    missing_evidence_refs: list[str] = Field(default_factory=list)
    suggested_action_inbox_proposal_ref: str | None = Field(default=None)
    required_approval_refs: list[str] = Field(default_factory=list)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(
            TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS
        )
    )
    risk_class: TaskDecompositionRiskClass = TaskDecompositionRiskClass.low
    why_proposed: str = Field(..., min_length=1, max_length=360)
    what_this_affects: list[str] = Field(default_factory=list, min_length=1)
    review_only: bool = True
    proposal_only: bool = True
    execution_performed: bool = False
    safe_refs_only: bool = True

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_step(self) -> "TaskDecompositionStep":
        _validate_ref_fields(self, "step_ref")
        _validate_ref_list(self.depends_on, "depends_on")
        _validate_ref_list(self.dependency_refs, "dependency_refs")
        _validate_ref_list(self.evidence_refs, "evidence_refs")
        _validate_ref_list(self.ambiguity_refs, "ambiguity_refs")
        _validate_ref_list(self.missing_evidence_refs, "missing_evidence_refs")
        _validate_ref_list(self.required_approval_refs, "required_approval_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_ref_list(self.what_this_affects, "what_this_affects")
        if self.suggested_action_inbox_proposal_ref is not None:
            validate_task_ref(
                self.suggested_action_inbox_proposal_ref,
                "suggested_action_inbox_proposal_ref",
            )
        validate_safe_task_text(self.title, "title")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(self.why_proposed, "why_proposed")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "step")
        _validate_step_no_effect_flags(self)
        return self


class TaskDecompositionRequest(BaseModel):
    contract_ref: str = TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF
    request_ref: str = Field(..., min_length=1)
    original_request_ref: str = Field(..., min_length=1)
    original_request_safe_summary: str = Field(..., min_length=1, max_length=600)
    source_refs: list[str] = Field(default_factory=list, min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    ambiguity_refs: list[str] = Field(default_factory=list)
    missing_evidence_refs: list[str] = Field(default_factory=list)
    operator_goal_refs: list[str] = Field(default_factory=list)
    requested_surface_refs: list[str] = Field(
        default_factory=lambda: list(TASK_DECOMPOSITION_PROPOSAL_AFFECTED_SURFACE_REFS)
    )
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    runtime_model_call_allowed: bool = False
    provider_call_allowed: bool = False
    tool_execution_allowed: bool = False
    action_execution_allowed: bool = False
    workflow_execution_allowed: bool = False
    memory_write_allowed: bool = False
    context_injection_allowed: bool = False
    shell_subprocess_allowed: bool = False
    browser_network_allowed: bool = False
    connector_write_allowed: bool = False
    autonomous_planning_authority_allowed: bool = False
    production_authority_allowed: bool = False
    safe_refs_only: bool = True
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "TaskDecompositionRequest":
        if self.contract_ref != TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF:
            raise ValueError("unexpected task decomposition proposal contract ref")
        _validate_ref_fields(self, "contract_ref", "request_ref", "original_request_ref")
        for field_name in (
            "source_refs",
            "evidence_refs",
            "ambiguity_refs",
            "missing_evidence_refs",
            "operator_goal_refs",
            "requested_surface_refs",
            "metadata_refs",
        ):
            _validate_ref_list(getattr(self, field_name), field_name)
        validate_safe_task_text(
            self.original_request_safe_summary,
            "original_request_safe_summary",
        )
        _validate_denied_flags(self, "request")
        if not self.safe_refs_only:
            raise ValueError("task decomposition request must be safe-ref only")
        if self.raw_content_included:
            raise ValueError("task decomposition request must not include raw content")
        validate_safe_task_payload(self.metadata, "metadata")
        return self


class TaskDecompositionProposal(BaseModel):
    contract_ref: str = TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF
    proposal_ref: str = Field(..., min_length=1)
    request_ref: str = Field(..., min_length=1)
    original_request_ref: str = Field(..., min_length=1)
    original_request_safe_summary: str = Field(..., min_length=1, max_length=600)
    safe_summary: str = Field(..., min_length=1, max_length=600)
    proposed_steps: list[TaskDecompositionStep] = Field(default_factory=list, min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    ambiguity_refs: list[str] = Field(default_factory=list)
    missing_evidence_refs: list[str] = Field(default_factory=list)
    risks: list[TaskDecompositionRisk] = Field(default_factory=list, min_length=1)
    risk_class: TaskDecompositionRiskClass = TaskDecompositionRiskClass.low
    suggested_action_inbox_proposal_refs: list[str] = Field(default_factory=list, min_length=1)
    required_approvals: list[str] = Field(default_factory=list, min_length=1)
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(
            TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS
        )
    )
    why_proposed: str = Field(..., min_length=1, max_length=500)
    what_this_affects: list[str] = Field(default_factory=list, min_length=1)
    plans_bridge_ref: str = Field(..., min_length=1)
    action_inbox_bridge_ref: str = Field(..., min_length=1)
    review_envelope_ref: str = Field(..., min_length=1)
    blocked_states: list[TaskDecompositionBlockedState] = Field(default_factory=list, min_length=1)
    review_only: bool = True
    proposal_only: bool = True
    proposal_authority_granted: bool = False
    runtime_authority_granted: bool = False
    autonomous_planning_authority: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    task_execution_enabled: bool = False
    task_execution_performed: bool = False
    workflow_execution_enabled: bool = False
    workflow_execution_performed: bool = False
    action_execution_enabled: bool = False
    action_execution_performed: bool = False
    tool_execution_enabled: bool = False
    tool_execution_performed: bool = False
    scheduler_registered: bool = False
    background_worker_started: bool = False
    approval_ref_authority: bool = False
    approval_grant_capture_enabled: bool = False
    local_task_commit_eligible: bool = False
    memory_write_authorized: bool = False
    memory_write_performed: bool = False
    context_injection_authorized: bool = False
    context_injection_performed: bool = False
    connector_write_enabled: bool = False
    connector_write_performed: bool = False
    shell_subprocess_execution_enabled: bool = False
    shell_subprocess_execution_performed: bool = False
    browser_network_enabled: bool = False
    browser_network_performed: bool = False
    model_provider_authority_allowed: bool = False
    model_provider_call_performed: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    no_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_memory_write_performed: bool = True
    no_context_injection_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_proposal(self) -> "TaskDecompositionProposal":
        if self.contract_ref != TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF:
            raise ValueError("unexpected task decomposition proposal contract ref")
        _validate_ref_fields(
            self,
            "contract_ref",
            "proposal_ref",
            "request_ref",
            "original_request_ref",
            "plans_bridge_ref",
            "action_inbox_bridge_ref",
            "review_envelope_ref",
        )
        _validate_ref_list(self.dependencies, "dependencies")
        _validate_ref_list(self.ambiguity_refs, "ambiguity_refs")
        _validate_ref_list(self.missing_evidence_refs, "missing_evidence_refs")
        _validate_ref_list(
            self.suggested_action_inbox_proposal_refs,
            "suggested_action_inbox_proposal_refs",
        )
        _validate_ref_list(self.required_approvals, "required_approvals")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        _validate_ref_list(self.what_this_affects, "what_this_affects")
        validate_safe_task_text(
            self.original_request_safe_summary,
            "original_request_safe_summary",
        )
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(self.why_proposed, "why_proposed")
        _validate_required_blocked_authorities(self.blocked_authority_refs, "proposal")
        _validate_no_effect_flags(self, "proposal")
        if self.raw_content_included:
            raise ValueError("task decomposition proposal must not include raw content")
        return self


class TaskDecompositionReviewEnvelope(BaseModel):
    contract_ref: str = TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF
    review_envelope_ref: str = Field(..., min_length=1)
    request_ref: str = Field(..., min_length=1)
    proposal_refs: list[str] = Field(default_factory=list, min_length=1)
    proposals: list[TaskDecompositionProposal] = Field(default_factory=list, min_length=1)
    plans_bridge_refs: list[str] = Field(default_factory=list, min_length=1)
    action_inbox_proposal_refs: list[str] = Field(default_factory=list, min_length=1)
    review_actions: list[str] = Field(
        default_factory=lambda: list(TASK_DECOMPOSITION_PROPOSAL_REVIEW_ACTIONS)
    )
    decision_receipt_only: bool = True
    separate_approval_required: bool = True
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(
            TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS
        )
    )
    safe_summary: str = Field(..., min_length=1, max_length=600)
    next_safe_operator_action: str = Field(..., min_length=1, max_length=260)
    review_only: bool = True
    proposal_only: bool = True
    proposal_authority_granted: bool = False
    runtime_authority_granted: bool = False
    autonomous_planning_authority: bool = False
    execution_authorized: bool = False
    execution_performed: bool = False
    task_execution_enabled: bool = False
    task_execution_performed: bool = False
    workflow_execution_enabled: bool = False
    workflow_execution_performed: bool = False
    action_execution_enabled: bool = False
    action_execution_performed: bool = False
    tool_execution_enabled: bool = False
    tool_execution_performed: bool = False
    scheduler_registered: bool = False
    background_worker_started: bool = False
    approval_ref_authority: bool = False
    approval_grant_capture_enabled: bool = False
    local_task_commit_eligible: bool = False
    memory_write_authorized: bool = False
    memory_write_performed: bool = False
    context_injection_authorized: bool = False
    context_injection_performed: bool = False
    connector_write_enabled: bool = False
    connector_write_performed: bool = False
    shell_subprocess_execution_enabled: bool = False
    shell_subprocess_execution_performed: bool = False
    browser_network_enabled: bool = False
    browser_network_performed: bool = False
    model_provider_authority_allowed: bool = False
    model_provider_call_performed: bool = False
    public_beta_claim_enabled: bool = False
    public_distribution_claim_enabled: bool = False
    production_authority_enabled: bool = False
    no_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_memory_write_performed: bool = True
    no_context_injection_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True
    safe_refs_only: bool = True
    raw_content_included: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_review_envelope(self) -> "TaskDecompositionReviewEnvelope":
        if self.contract_ref != TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF:
            raise ValueError("unexpected task decomposition proposal contract ref")
        _validate_ref_fields(self, "contract_ref", "review_envelope_ref", "request_ref")
        _validate_ref_list(self.proposal_refs, "proposal_refs")
        _validate_ref_list(self.plans_bridge_refs, "plans_bridge_refs")
        _validate_ref_list(self.action_inbox_proposal_refs, "action_inbox_proposal_refs")
        _validate_ref_list(self.blocked_authority_refs, "blocked_authority_refs")
        if set(TASK_DECOMPOSITION_PROPOSAL_REVIEW_ACTIONS) - set(self.review_actions):
            raise ValueError("review envelope must include approve, defer, and reject")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        validate_safe_task_text(
            self.next_safe_operator_action,
            "next_safe_operator_action",
        )
        _validate_required_blocked_authorities(self.blocked_authority_refs, "review envelope")
        _validate_no_effect_flags(self, "review envelope")
        if not self.decision_receipt_only:
            raise ValueError("review envelope decisions must be receipt-only")
        if not self.separate_approval_required:
            raise ValueError("review envelope must require separate approval")
        if self.raw_content_included:
            raise ValueError("review envelope must not include raw content")
        return self


def build_task_decomposition_review_envelope(
    request: TaskDecompositionRequest | dict[str, Any],
) -> TaskDecompositionReviewEnvelope:
    parsed = request if isinstance(request, TaskDecompositionRequest) else TaskDecompositionRequest(**request)
    suffix = _safe_suffix(parsed.request_ref)
    risk_class = _risk_class_for_summary(parsed.original_request_safe_summary)
    ambiguity_posture = _ambiguity_posture(parsed)
    step_specs = _step_specs(parsed, ambiguity_posture)
    steps: list[TaskDecompositionStep] = []
    for index, spec in enumerate(step_specs, start=1):
        step_ref = f"task-decomposition-step:{suffix}-{index}"
        action_ref = f"action-proposal:task-decomposition:{suffix}-{index}"
        depends_on = [steps[-1].step_ref] if steps else []
        step_risk = risk_class if spec["kind"] == "action_proposal" else TaskDecompositionRiskClass.low
        steps.append(
            TaskDecompositionStep(
                step_ref=step_ref,
                title=spec["title"],
                safe_summary=spec["safe_summary"],
                depends_on=depends_on,
                dependency_refs=[
                    f"dependency-ref:task-decomposition:{suffix}-{index}"
                ]
                if depends_on
                else [],
                evidence_refs=_dedupe(
                    parsed.evidence_refs
                    or [f"evidence-ref:task-decomposition:{suffix}"]
                ),
                ambiguity_refs=parsed.ambiguity_refs,
                missing_evidence_refs=parsed.missing_evidence_refs,
                suggested_action_inbox_proposal_ref=action_ref,
                required_approval_refs=[
                    f"approval-requirement:task-decomposition:{suffix}-{index}"
                ],
                risk_class=step_risk,
                why_proposed=spec["why_proposed"],
                what_this_affects=spec["what_this_affects"],
            )
        )
    proposal_ref = f"task-decomposition-proposal:{suffix}"
    review_envelope_ref = f"review-envelope:task-decomposition:{suffix}"
    action_refs = [step.suggested_action_inbox_proposal_ref for step in steps if step.suggested_action_inbox_proposal_ref]
    blocked_states = _blocked_states(parsed, suffix, ambiguity_posture, risk_class)
    proposal = TaskDecompositionProposal(
        proposal_ref=proposal_ref,
        request_ref=parsed.request_ref,
        original_request_ref=parsed.original_request_ref,
        original_request_safe_summary=parsed.original_request_safe_summary,
        safe_summary=(
            "Review-only decomposition proposal with bounded steps, evidence "
            "refs, Action Inbox proposal refs, and blocked authority refs."
        ),
        proposed_steps=steps,
        dependencies=[ref for step in steps for ref in step.dependency_refs],
        ambiguity_refs=parsed.ambiguity_refs,
        missing_evidence_refs=parsed.missing_evidence_refs,
        risks=_risks_for_request(parsed, suffix, risk_class),
        risk_class=risk_class,
        suggested_action_inbox_proposal_refs=action_refs,
        required_approvals=[
            f"approval-requirement:task-decomposition:{suffix}:operator-review"
        ],
        why_proposed=_why_proposed(parsed, ambiguity_posture),
        what_this_affects=_dedupe(list(parsed.requested_surface_refs)),
        plans_bridge_ref=f"plan-proposal:task-decomposition:{suffix}",
        action_inbox_bridge_ref=f"action-inbox-proposal:task-decomposition:{suffix}",
        review_envelope_ref=review_envelope_ref,
        blocked_states=blocked_states,
    )
    return TaskDecompositionReviewEnvelope(
        review_envelope_ref=review_envelope_ref,
        request_ref=parsed.request_ref,
        proposal_refs=[proposal.proposal_ref],
        proposals=[proposal],
        plans_bridge_refs=[proposal.plans_bridge_ref],
        action_inbox_proposal_refs=proposal.suggested_action_inbox_proposal_refs,
        safe_summary=(
            "Task decomposition proposal envelope for operator review only; "
            "decisions record posture and do not perform work."
        ),
        next_safe_operator_action=(
            "Review, defer, or reject the proposal; create any executable work "
            "only through a separate exact-scoped approval lane."
        ),
    )


def build_task_decomposition_plan_action_envelope(
    proposal: TaskDecompositionProposal,
) -> PlanActionEnvelope:
    return build_plan_action_envelope(
        source_plan_ref=proposal.plans_bridge_ref,
        source_action_ref=proposal.action_inbox_bridge_ref,
        title="Review task decomposition proposal",
        safe_summary=proposal.safe_summary,
        evidence_refs=[
            f"evidence-ref:task-decomposition:{_safe_suffix(proposal.proposal_ref)}",
            *proposal.missing_evidence_refs,
        ],
        side_effect_class="validation_only",
        risk_class=proposal.risk_class,
        approval_required=True,
        blocked_state_refs=[
            "blocked-state:task-decomposition-proposal-only",
            "blocked-state:task-decomposition-no-action-execution",
            *proposal.blocked_authority_refs,
        ],
        next_safe_action=(
            "Review, defer, or reject the decomposition proposal; do not execute "
            "steps from this envelope."
        ),
    )


def task_decomposition_action_items(
    envelope: TaskDecompositionReviewEnvelope,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for proposal in envelope.proposals:
        suffix = _safe_suffix(proposal.proposal_ref)
        evidence_refs = [
            f"evidence-ref:task-decomposition:{suffix}",
            *proposal.missing_evidence_refs,
        ]
        item = {
            "item_ref": f"action:task-decomposition:{suffix}",
            "title": "Review task decomposition proposal",
            "safe_summary": proposal.safe_summary,
            "surface": "Plans",
            "priority": "medium" if proposal.risk_class in {"none", "low"} else "high",
            "risk_class": proposal.risk_class,
            "action_kind": TASK_DECOMPOSITION_ACTION_KIND,
            "status": "proposed",
            "side_effect_class": "validation_only",
            "authority_boundary": (
                "Task decomposition Action Inbox item is review-only. It does "
                "not execute steps, mutate memory, call providers, run shell or "
                "browser actions, write connectors, or grant production authority."
            ),
            "approval_required": False,
            "approval_envelope_ref": f"approval-envelope:task-decomposition:{suffix}",
            "approval_envelope_status": "not_required_proposal_only",
            "state_change_contract_ref": None,
            "state_change_readiness": "proposal_only_no_execution_path",
            "blocked_state": (
                "Separate approval is required before any task, workflow, tool, "
                "connector, memory, browser, network, or shell path could exist."
            ),
            "evidence_refs": _dedupe(evidence_refs),
            "receipt_refs": [],
            "audit_refs": [],
            "idempotency_key_ref": None,
            "expires_at": None,
            "stale_state": "recheck_request_and_evidence_refs_before_scoping_work",
            "rollback_ref": None,
            "safe_disable_ref": None,
            "next_safe_action": (
                "Inspect the proposed steps and either keep them as planning refs "
                "or create a separate exact-scoped approved action later."
            ),
            "task_decomposition_proposal_ref": proposal.proposal_ref,
            "task_decomposition_review_envelope_ref": envelope.review_envelope_ref,
            "task_decomposition_plans_bridge_ref": proposal.plans_bridge_ref,
            "task_decomposition_action_inbox_bridge_ref": (
                proposal.action_inbox_bridge_ref
            ),
            "task_decomposition_step_refs": [
                step.step_ref for step in proposal.proposed_steps
            ],
            "task_decomposition_dependency_refs": proposal.dependencies,
            "task_decomposition_ambiguity_refs": proposal.ambiguity_refs,
            "task_decomposition_missing_evidence_refs": (
                proposal.missing_evidence_refs
            ),
            "task_decomposition_required_approvals": proposal.required_approvals,
            "task_decomposition_blocked_authority_refs": (
                proposal.blocked_authority_refs
            ),
            "task_decomposition_why_proposed": proposal.why_proposed,
            "task_decomposition_what_this_affects": proposal.what_this_affects,
            "task_decomposition_review_only": proposal.review_only,
            "task_decomposition_proposal_only": proposal.proposal_only,
            "task_decomposition_execution_performed": proposal.execution_performed,
            "task_decomposition_runtime_authority_granted": (
                proposal.runtime_authority_granted
            ),
            "task_decomposition_execution_authorized": (
                proposal.execution_authorized
            ),
            "task_decomposition_action_execution_enabled": (
                proposal.action_execution_enabled
            ),
            "task_decomposition_tool_execution_enabled": (
                proposal.tool_execution_enabled
            ),
            "task_decomposition_workflow_execution_enabled": (
                proposal.workflow_execution_enabled
            ),
            "task_decomposition_memory_write_authorized": (
                proposal.memory_write_authorized
            ),
            "task_decomposition_context_injection_authorized": (
                proposal.context_injection_authorized
            ),
            "task_decomposition_connector_write_enabled": (
                proposal.connector_write_enabled
            ),
            "task_decomposition_shell_subprocess_execution_enabled": (
                proposal.shell_subprocess_execution_enabled
            ),
            "task_decomposition_browser_network_enabled": (
                proposal.browser_network_enabled
            ),
            "task_decomposition_model_provider_authority_allowed": (
                proposal.model_provider_authority_allowed
            ),
            "task_decomposition_public_beta_claim_enabled": (
                proposal.public_beta_claim_enabled
            ),
            "task_decomposition_production_authority_enabled": (
                proposal.production_authority_enabled
            ),
        }
        validate_safe_task_payload(item, "task_decomposition_action_item")
        items.append(item)
    return items


def task_decomposition_read_model_for_plan(
    plan_ref: str,
    *,
    title: str,
    safe_summary: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    request = TaskDecompositionRequest(
        request_ref=f"task-decomposition-request:{_safe_suffix(plan_ref)}",
        original_request_ref=plan_ref,
        original_request_safe_summary=safe_summary,
        source_refs=[plan_ref],
        evidence_refs=evidence_refs or ["evidence-ref:founder-loop:plan-summary"],
        operator_goal_refs=[f"operator-goal:task-decomposition:{_stable_digest(title)}"],
    )
    envelope = build_task_decomposition_review_envelope(request)
    proposal = envelope.proposals[0]
    plan_action_envelope = build_task_decomposition_plan_action_envelope(proposal)
    return {
        "task_decomposition_contract_ref": TASK_DECOMPOSITION_PROPOSAL_CONTRACT_REF,
        "task_decomposition_request_ref": request.request_ref,
        "task_decomposition_original_request_ref": request.original_request_ref,
        "task_decomposition_review_envelope_ref": envelope.review_envelope_ref,
        "task_decomposition_proposal_ref": proposal.proposal_ref,
        "task_decomposition_status": "proposal_only_review_required",
        "task_decomposition_steps": [
            step.model_dump(mode="json") for step in proposal.proposed_steps
        ],
        "task_decomposition_step_refs": [
            step.step_ref for step in proposal.proposed_steps
        ],
        "task_decomposition_dependency_refs": proposal.dependencies,
        "task_decomposition_ambiguity_refs": proposal.ambiguity_refs,
        "task_decomposition_missing_evidence_refs": proposal.missing_evidence_refs,
        "task_decomposition_risks": [
            risk.model_dump(mode="json") for risk in proposal.risks
        ],
        "task_decomposition_risk_class": proposal.risk_class,
        "task_decomposition_suggested_action_inbox_proposal_refs": (
            proposal.suggested_action_inbox_proposal_refs
        ),
        "task_decomposition_required_approvals": proposal.required_approvals,
        "task_decomposition_blocked_authority_refs": proposal.blocked_authority_refs,
        "task_decomposition_why_proposed": proposal.why_proposed,
        "task_decomposition_what_this_affects": proposal.what_this_affects,
        "task_decomposition_plans_bridge_ref": proposal.plans_bridge_ref,
        "task_decomposition_action_inbox_bridge_ref": proposal.action_inbox_bridge_ref,
        "task_decomposition_review_only": proposal.review_only,
        "task_decomposition_proposal_only": proposal.proposal_only,
        "task_decomposition_execution_performed": proposal.execution_performed,
        "task_decomposition_runtime_authority_granted": (
            proposal.runtime_authority_granted
        ),
        "task_decomposition_execution_authorized": proposal.execution_authorized,
        "task_decomposition_action_execution_enabled": (
            proposal.action_execution_enabled
        ),
        "task_decomposition_tool_execution_enabled": proposal.tool_execution_enabled,
        "task_decomposition_workflow_execution_enabled": (
            proposal.workflow_execution_enabled
        ),
        "task_decomposition_memory_write_authorized": (
            proposal.memory_write_authorized
        ),
        "task_decomposition_context_injection_authorized": (
            proposal.context_injection_authorized
        ),
        "task_decomposition_connector_write_enabled": proposal.connector_write_enabled,
        "task_decomposition_shell_subprocess_execution_enabled": (
            proposal.shell_subprocess_execution_enabled
        ),
        "task_decomposition_browser_network_enabled": proposal.browser_network_enabled,
        "task_decomposition_model_provider_authority_allowed": (
            proposal.model_provider_authority_allowed
        ),
        "task_decomposition_public_beta_claim_enabled": (
            proposal.public_beta_claim_enabled
        ),
        "task_decomposition_production_authority_enabled": (
            proposal.production_authority_enabled
        ),
        "task_decomposition_action_envelope_ref": (
            plan_action_envelope.action_envelope_ref
        ),
    }


def _step_specs(
    request: TaskDecompositionRequest,
    ambiguity_posture: TaskDecompositionAmbiguityPosture,
) -> list[dict[str, Any]]:
    requested_surfaces = _dedupe(list(request.requested_surface_refs))
    specs = [
        {
            "kind": "review",
            "title": "Confirm requested outcome",
            "safe_summary": (
                "Review the safe request summary, source refs, and intended "
                "operator outcome before any scoped work is created."
            ),
            "why_proposed": "The request needs a bounded outcome before planning refs become useful.",
            "what_this_affects": requested_surfaces,
        },
        {
            "kind": "evidence",
            "title": "Bind evidence and blockers",
            "safe_summary": (
                "Collect reviewed evidence refs, missing-evidence refs, and "
                "blocked authority refs for the proposed work."
            ),
            "why_proposed": "Evidence and blockers make the proposal inspectable and safe to defer.",
            "what_this_affects": ["surface-ref:evidence", "surface-ref:plans"],
        },
        {
            "kind": "plan",
            "title": "Draft plan proposal",
            "safe_summary": (
                "Create a Plans-facing proposal with ordered steps, dependency "
                "refs, risk posture, and no execution path."
            ),
            "why_proposed": "The operator needs a reviewable plan before any Action Inbox item exists.",
            "what_this_affects": ["surface-ref:plans", "surface-ref:today"],
        },
    ]
    if ambiguity_posture != TaskDecompositionAmbiguityPosture.clear:
        specs.insert(
            1,
            {
                "kind": "clarify",
                "title": "Ask for clarification",
                "safe_summary": (
                    "Request the missing operator decision or reviewed evidence "
                    "before converting the proposal into scoped work."
                ),
                "why_proposed": "The request is ambiguous or lacks reviewed evidence.",
                "what_this_affects": ["surface-ref:today", "surface-ref:actions"],
            },
        )
    if _summary_suggests_action(request.original_request_safe_summary):
        specs.append(
            {
                "kind": "action_proposal",
                "title": "Prepare Action Inbox proposal refs",
                "safe_summary": (
                    "Prepare proposal-only Action Inbox refs that require a "
                    "separate exact-scoped approval lane before any work."
                ),
                "why_proposed": "The request appears to need follow-up work after plan review.",
                "what_this_affects": ["surface-ref:actions", "surface-ref:evidence"],
            }
        )
    return specs


def _risks_for_request(
    request: TaskDecompositionRequest,
    suffix: str,
    risk_class: TaskDecompositionRiskClass,
) -> list[TaskDecompositionRisk]:
    return [
        TaskDecompositionRisk(
            risk_ref=f"risk:task-decomposition:{suffix}:proposal-boundary",
            risk_class=risk_class,
            safe_summary=(
                "Proposal may imply future work, so execution, provider calls, "
                "memory writes, shell, browser, network, and connector writes stay blocked."
            ),
            mitigation_ref=f"mitigation:task-decomposition:{suffix}:separate-approval",
            blocked_authority_ref="blocked-authority:no-action-execution",
            evidence_refs=request.evidence_refs
            or [f"evidence-ref:task-decomposition:{suffix}"],
        )
    ]


def _blocked_states(
    request: TaskDecompositionRequest,
    suffix: str,
    ambiguity_posture: TaskDecompositionAmbiguityPosture,
    risk_class: TaskDecompositionRiskClass,
) -> list[TaskDecompositionBlockedState]:
    states = [
        TaskDecompositionBlockedState(
            blocked_state_ref=f"blocked-state:task-decomposition:{suffix}:proposal-only",
            reason_ref=f"reason-ref:task-decomposition:{suffix}:proposal-only",
            blocked_authority_ref="blocked-authority:no-action-execution",
            safe_summary="Task decomposition output is a proposal and cannot execute work.",
            affected_surface_refs=["surface-ref:plans", "surface-ref:actions"],
            evidence_refs=request.evidence_refs
            or [f"evidence-ref:task-decomposition:{suffix}"],
            next_safe_operator_action="Review the proposal before scoping any separate approved action.",
        )
    ]
    if ambiguity_posture != TaskDecompositionAmbiguityPosture.clear:
        states.append(
            TaskDecompositionBlockedState(
                blocked_state_ref=f"blocked-state:task-decomposition:{suffix}:clarification",
                reason_ref=f"reason-ref:task-decomposition:{suffix}:clarification",
                blocked_authority_ref="blocked-authority:no-insufficient-evidence-work",
                safe_summary="Clarification or reviewed evidence is needed before scoped work.",
                affected_surface_refs=["surface-ref:today", "surface-ref:actions"],
                evidence_refs=request.missing_evidence_refs
                or [f"evidence-ref:task-decomposition:{suffix}:missing"],
                next_safe_operator_action="Ask the operator for the missing decision or evidence ref.",
            )
        )
    if risk_class in {
        TaskDecompositionRiskClass.high,
        TaskDecompositionRiskClass.critical,
        TaskDecompositionRiskClass.blocked,
    }:
        states.append(
            TaskDecompositionBlockedState(
                blocked_state_ref=f"blocked-state:task-decomposition:{suffix}:risk",
                reason_ref=f"reason-ref:task-decomposition:{suffix}:risk",
                blocked_authority_ref="blocked-authority:no-autonomous-planning-authority",
                safe_summary="Higher-risk proposal needs explicit separate review.",
                affected_surface_refs=["surface-ref:plans", "surface-ref:evidence"],
                evidence_refs=request.evidence_refs
                or [f"evidence-ref:task-decomposition:{suffix}:risk"],
                next_safe_operator_action="Keep the proposal review-only until exact authority is scoped.",
            )
        )
    return states


def _risk_class_for_summary(summary: str) -> TaskDecompositionRiskClass:
    lowered = summary.lower()
    if any(marker in lowered for marker in ("production", "payment", "credential")):
        return TaskDecompositionRiskClass.critical
    if any(
        marker in lowered
        for marker in (
            "delete",
            "write",
            "shell",
            "subprocess",
            "browser",
            "network",
            "connector",
            "provider",
            "model call",
            "memory write",
            "context injection",
        )
    ):
        return TaskDecompositionRiskClass.high
    if any(marker in lowered for marker in ("implement", "build", "wire", "fix", "change")):
        return TaskDecompositionRiskClass.medium
    return TaskDecompositionRiskClass.low


def _ambiguity_posture(
    request: TaskDecompositionRequest,
) -> TaskDecompositionAmbiguityPosture:
    lowered = request.original_request_safe_summary.lower()
    if request.missing_evidence_refs:
        return TaskDecompositionAmbiguityPosture.missing_evidence
    if request.ambiguity_refs or any(marker in lowered for marker in ("vague", "unclear", "maybe", "not sure", "?")):
        return TaskDecompositionAmbiguityPosture.needs_operator_clarification
    return TaskDecompositionAmbiguityPosture.clear


def _summary_suggests_action(summary: str) -> bool:
    lowered = summary.lower()
    return any(
        marker in lowered
        for marker in (
            "implement",
            "build",
            "wire",
            "create",
            "fix",
            "add",
            "update",
            "review",
        )
    )


def _why_proposed(
    request: TaskDecompositionRequest,
    ambiguity_posture: TaskDecompositionAmbiguityPosture,
) -> str:
    if ambiguity_posture == TaskDecompositionAmbiguityPosture.missing_evidence:
        return "The request needs a proposal because reviewed evidence refs are missing."
    if ambiguity_posture == TaskDecompositionAmbiguityPosture.needs_operator_clarification:
        return "The request is ambiguous enough to require operator review before scoping work."
    return "The request can be decomposed into reviewable planning and Action Inbox proposal refs."


def _validate_ref_fields(model: Any, *field_names: str) -> None:
    for field_name in field_names:
        validate_task_ref(getattr(model, field_name), field_name)


def _validate_ref_list(values: list[str], field_name: str) -> None:
    for value in values:
        validate_task_ref(value, field_name)


def _validate_required_blocked_authorities(refs: list[str], owner: str) -> None:
    missing = set(TASK_DECOMPOSITION_PROPOSAL_REQUIRED_BLOCKED_AUTHORITY_REFS) - set(refs)
    if missing:
        raise ValueError(f"{owner} missing required blocked authority ref: {sorted(missing)[0]}")


def _validate_denied_flags(model: Any, owner: str) -> None:
    enabled = [field_name for field_name in _DENIED_FLAG_FIELDS if getattr(model, field_name)]
    if enabled:
        raise ValueError(f"{owner} enabled denied authority: {enabled[0]}")


def _validate_step_no_effect_flags(step: TaskDecompositionStep) -> None:
    if not step.review_only:
        raise ValueError("step must remain review-only")
    if not step.proposal_only:
        raise ValueError("step must remain proposal-only")
    if step.execution_performed:
        raise ValueError("step performed denied execution")
    if not step.safe_refs_only:
        raise ValueError("step must be safe-ref only")


def _validate_no_effect_flags(model: Any, owner: str) -> None:
    false_required = [field_name for field_name in _NO_EFFECT_FALSE_FIELDS if getattr(model, field_name)]
    if false_required:
        raise ValueError(f"{owner} granted denied authority: {false_required[0]}")
    true_required = [field_name for field_name in _NO_EFFECT_TRUE_FIELDS if not getattr(model, field_name, True)]
    if true_required:
        raise ValueError(f"{owner} failed no-effect proof flag: {true_required[0]}")


def _safe_suffix(value: str) -> str:
    suffix = _SAFE_SUFFIX_RE.sub("-", value.lower()).strip("-")
    return suffix or "missing"


def _stable_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
