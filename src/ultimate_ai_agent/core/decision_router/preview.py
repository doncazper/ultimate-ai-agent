from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.decision_router.parallel_preflight import (
    TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS,
    run_parallel_turn_preflight,
)
from ultimate_ai_agent.core.model_runtime.redaction import contains_secret_like
from ultimate_ai_agent.core.planning.validation import validate_safe_task_text, validate_task_ref


TURN_ROUTER_PREVIEW_CONTRACT_REF = "contract-ref:turn-router-preview:v1"
TURN_ROUTER_PREVIEW_SOURCE_REF = "source-ref:turn-router-preview:no-effect"
TURN_ROUTER_PREVIEW_ROUTE_REF = "/control-center/turn-router/preview"

TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS: dict[str, str] = {
    "diy-desk": "How do I build a DIY desk?",
    "office-memory": "Design one for my office using what you know.",
    "shopping-list": "Make me a shopping list for this desk.",
    "current-lumber-prices": "Find current lumber prices near me.",
    "order-materials": "Order the materials.",
    "card-pickup": "Use my card and book pickup at Home Depot.",
    "base-answer-bypass": "Ask the base answer path: use my card and order this.",
}
_SECRET_SURROGATE_TEXT = "private credential boundary"


class TurnRouterPreviewRequest(BaseModel):
    sample_id: str | None = Field(default=None, min_length=1, max_length=80)
    text: str | None = Field(default=None, min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_request(self) -> "TurnRouterPreviewRequest":
        if bool(self.sample_id) == bool(self.text):
            raise ValueError("provide exactly one of sample_id or text")
        if self.sample_id is not None and self.sample_id not in TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS:
            raise ValueError("unknown turn router preview sample")
        return self


class TurnRouterPolicySummary(BaseModel):
    turn_contract: str
    memory_scope: str
    memory_read_allowed: bool
    memory_write_allowed: bool
    tool_policy: str
    tool_choice: str
    tool_execution_allowed: bool
    action_execution_allowed: bool
    workflow_execution_allowed: bool
    context_injection_allowed: bool
    approval_policy: str
    approval_required: bool
    planner: bool
    durable_state: bool
    state_policy: str
    prompt_profile: str
    output_contract: str
    runtime_model_call_allowed: bool
    provider_call_allowed: bool
    shell_subprocess_allowed: bool
    browser_network_allowed: bool
    connector_write_allowed: bool
    side_effects_allowed: bool
    execution_ready: bool

    model_config = ConfigDict(extra="forbid")


class TurnRouterNoEffectProof(BaseModel):
    authority_granted: bool = False
    execution_permitted: bool = False
    no_runtime_model_call_performed: bool = True
    no_provider_call_performed: bool = True
    no_tool_execution_performed: bool = True
    no_action_execution_performed: bool = True
    no_workflow_execution_performed: bool = True
    no_context_injection_performed: bool = True
    no_memory_content_retrieved: bool = True
    no_memory_write_performed: bool = True
    no_durable_state_write_performed: bool = True
    no_shell_subprocess_performed: bool = True
    no_browser_network_performed: bool = True
    no_connector_write_performed: bool = True
    invocation_policy_compiled_only: bool = True
    raw_request_text_persisted: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_no_effect_proof(self) -> "TurnRouterNoEffectProof":
        if self.authority_granted or self.execution_permitted:
            raise ValueError("turn router preview cannot grant authority or execution")
        for field_name in (
            "no_runtime_model_call_performed",
            "no_provider_call_performed",
            "no_tool_execution_performed",
            "no_action_execution_performed",
            "no_workflow_execution_performed",
            "no_context_injection_performed",
            "no_memory_content_retrieved",
            "no_memory_write_performed",
            "no_durable_state_write_performed",
            "no_shell_subprocess_performed",
            "no_browser_network_performed",
            "no_connector_write_performed",
            "invocation_policy_compiled_only",
        ):
            if not getattr(self, field_name):
                raise ValueError("turn router preview proof flag must remain no-effect")
        if self.raw_request_text_persisted:
            raise ValueError("turn router preview cannot persist raw request text")
        return self


class TurnRouterPreviewReadModel(BaseModel):
    contract_ref: str = TURN_ROUTER_PREVIEW_CONTRACT_REF
    preview_ref: str
    request_ref: str
    request_kind: Literal["sample", "ephemeral_text"]
    sample_id: str | None = None
    selected_turn_contract: str
    confidence: float
    reason_refs: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    policy_summary: TurnRouterPolicySummary
    no_effect_proof: TurnRouterNoEffectProof
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(TURN_PREFLIGHT_REQUIRED_BLOCKED_AUTHORITY_REFS)
    )
    lane_result_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=lambda: [TURN_ROUTER_PREVIEW_SOURCE_REF])
    evidence_refs: list[str] = Field(default_factory=list)
    route_refs: list[str] = Field(default_factory=lambda: [TURN_ROUTER_PREVIEW_ROUTE_REF])
    redactions_applied: list[str] = Field(default_factory=list)
    safe_summary: str = "Turn router preview produced a no-effect diagnostic read model."
    raw_content_included: bool = False
    ephemeral_request_text_omitted: bool = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_preview(self) -> "TurnRouterPreviewReadModel":
        validate_task_ref(self.contract_ref, "contract_ref")
        validate_task_ref(self.preview_ref, "preview_ref")
        validate_task_ref(self.request_ref, "request_ref")
        validate_safe_task_text(self.safe_summary, "safe_summary")
        for field_name in ("reason_refs", "blocked_authority_refs", "lane_result_refs", "source_refs", "evidence_refs"):
            for value in getattr(self, field_name):
                validate_task_ref(value, field_name)
        if self.raw_content_included:
            raise ValueError("turn router preview cannot include raw content")
        if not self.ephemeral_request_text_omitted:
            raise ValueError("turn router preview must omit ephemeral request text")
        return self


def build_turn_router_preview(
    request: TurnRouterPreviewRequest | dict[str, Any],
) -> TurnRouterPreviewReadModel:
    parsed = request if isinstance(request, TurnRouterPreviewRequest) else TurnRouterPreviewRequest(**request)
    request_text, request_kind, request_ref, sample_id = _resolve_preview_request(parsed)
    secret_like_input = contains_secret_like({"text": request_text})
    classification_text = _SECRET_SURROGATE_TEXT if secret_like_input else request_text
    suffix = sample_id or "ephemeral-text"
    preflight = run_parallel_turn_preflight(
        classification_text,
        run_ref=f"turn-preflight-run:router-preview:{suffix}",
        decision_ref=f"turn-decision:router-preview:{suffix}",
    )
    redactions = ["ephemeral_request_text_omitted"]
    if secret_like_input:
        redactions.append("secret_like_input_safely_summarized")
    return TurnRouterPreviewReadModel(
        preview_ref=f"turn-router-preview:{suffix}",
        request_ref=request_ref,
        request_kind=request_kind,
        sample_id=sample_id,
        selected_turn_contract=preflight.turn_decision.turn_contract,
        confidence=preflight.turn_decision.confidence,
        reason_refs=preflight.turn_decision.reason_refs,
        risk_flags=[str(flag) for flag in preflight.turn_decision.risk_flags],
        policy_summary=_policy_summary(preflight.invocation_policy.model_dump(mode="json")),
        no_effect_proof=TurnRouterNoEffectProof(
            authority_granted=preflight.authority_granted,
            execution_permitted=preflight.execution_permitted,
            no_runtime_model_call_performed=preflight.no_runtime_model_call_performed,
            no_provider_call_performed=preflight.no_provider_call_performed,
            no_tool_execution_performed=preflight.no_tool_execution_performed,
            no_action_execution_performed=preflight.no_action_execution_performed,
            no_workflow_execution_performed=preflight.no_workflow_execution_performed,
            no_context_injection_performed=preflight.no_context_injection_performed,
            no_memory_content_retrieved=preflight.no_memory_content_retrieved,
            no_memory_write_performed=preflight.no_memory_write_performed,
            no_durable_state_write_performed=preflight.no_durable_state_write_performed,
            no_shell_subprocess_performed=preflight.no_shell_subprocess_performed,
            no_browser_network_performed=preflight.no_browser_network_performed,
            no_connector_write_performed=preflight.no_connector_write_performed,
            invocation_policy_compiled_only=preflight.invocation_policy_compiled_only,
        ),
        blocked_authority_refs=preflight.blocked_authority_refs,
        lane_result_refs=[lane.lane_result_ref for lane in preflight.bundle.lane_results],
        evidence_refs=[
            *preflight.turn_decision.evidence_refs,
            "evidence-ref:turn-router-preview:no-effect",
        ],
        redactions_applied=redactions,
    )


def _resolve_preview_request(
    request: TurnRouterPreviewRequest,
) -> tuple[str, Literal["sample", "ephemeral_text"], str, str | None]:
    if request.sample_id is not None:
        return (
            TURN_ROUTER_PREVIEW_SAMPLE_PROMPTS[request.sample_id],
            "sample",
            f"turn-router-preview-request:sample:{request.sample_id}",
            request.sample_id,
        )
    return (
        request.text or "",
        "ephemeral_text",
        "turn-router-preview-request:ephemeral-text",
        None,
    )


def _policy_summary(policy: dict[str, Any]) -> TurnRouterPolicySummary:
    return TurnRouterPolicySummary(
        turn_contract=policy["turn_contract"],
        memory_scope=policy["memory_scope"],
        memory_read_allowed=policy["memory_read_allowed"],
        memory_write_allowed=policy["memory_write_allowed"],
        tool_policy=policy["tool_policy"],
        tool_choice=policy["tool_choice"],
        tool_execution_allowed=policy["tool_execution_allowed"],
        action_execution_allowed=policy["action_execution_allowed"],
        workflow_execution_allowed=policy["workflow_execution_allowed"],
        context_injection_allowed=policy["context_injection_allowed"],
        approval_policy=policy["approval_policy"],
        approval_required=policy["approval_required"],
        planner=policy["planner"],
        durable_state=policy["durable_state"],
        state_policy=policy["state_policy"],
        prompt_profile=policy["prompt_profile"],
        output_contract=policy["output_contract"],
        runtime_model_call_allowed=policy["runtime_model_call_allowed"],
        provider_call_allowed=policy["provider_call_allowed"],
        shell_subprocess_allowed=policy["shell_subprocess_allowed"],
        browser_network_allowed=policy["browser_network_allowed"],
        connector_write_allowed=policy["connector_write_allowed"],
        side_effects_allowed=policy["side_effects_allowed"],
        execution_ready=policy["execution_ready"],
    )
