from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.autonomy.tool_autonomy_single_session import (
    validate_low_risk_tool_autonomy_single_session_decision,
)


MULTI_TOOL_DRY_RUN_PROMOTION_DOCS = [
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION.md",
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_POLICY.md",
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_RECEIPT_PLAN.md",
    "docs/autonomy/MULTI_TOOL_DRY_RUN_PROMOTION_NON_GOALS.md",
    "docs/autonomy/M93_TO_M94_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_M93_PRIOR_MILESTONE_REFS = ("milestone:M69", "milestone:M91", "milestone:M92")


class MultiToolDryRunPromotionStatus(str, Enum):
    promotion_ready_for_review = "promotion_ready_for_review"


class _MultiToolDryRunPromotionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MultiToolDryRunPromotionPolicy(_MultiToolDryRunPromotionModel):
    policy_ref: str = "multi-tool-dry-run-promotion-policy:m93"
    enabled_for_review: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    exact_m92_single_session_binding_required: bool = True
    exact_dry_run_plan_binding_required: bool = True
    exact_real_run_plan_binding_required: bool = True
    dry_run_real_run_equivalence_required: bool = True
    exact_promotion_approval_required: bool = True
    wildcard_approval_denied: bool = True
    approval_refs_are_identifiers_only: bool = True
    m94_future_only: bool = True
    real_run_promotion_enabled: bool = False
    real_run_execution_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    session_start_enabled: bool = False
    background_worker_enabled: bool = False
    command_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    subprocess_execution_enabled: bool = False
    filesystem_mutation_enabled: bool = False
    network_access_enabled: bool = False
    browser_click_enabled: bool = False
    browser_form_enabled: bool = False
    plugin_execution_enabled: bool = False
    remote_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MultiToolDryRunPromotionRequest(_MultiToolDryRunPromotionModel):
    request_ref: str
    promotion_ref: str
    m92_single_session_decision_ref: str
    m92_single_session_decision: Any
    actor_ref: str
    promotion_approval_ref: str
    dry_run_plan_ref: str
    dry_run_plan_hash_ref: str
    dry_run_plan_hash: str
    real_run_plan_ref: str
    real_run_plan_hash_ref: str
    real_run_plan_hash: str
    safe_execution_scope_ref: str
    audit_ref: str
    replay_ref: str
    safe_tool_refs: list[str]
    prior_milestone_refs: list[str]
    safe_promotion_summary: str
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    execution_requested: bool = False
    real_run_execution_requested: bool = False
    tool_execution_requested: bool = False
    autonomous_execution_requested: bool = False
    session_start_requested: bool = False
    background_worker_requested: bool = False
    command_execution_requested: bool = False
    shell_execution_requested: bool = False
    subprocess_execution_requested: bool = False
    filesystem_mutation_requested: bool = False
    network_access_requested: bool = False
    browser_click_requested: bool = False
    browser_form_requested: bool = False
    plugin_execution_requested: bool = False
    remote_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    contains_raw_tool_payload: bool = False
    contains_raw_provider_payload: bool = False
    contains_raw_prompt: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.promotion_ref, "promotion_ref"),
            (self.m92_single_session_decision_ref, "m92_single_session_decision_ref"),
            (self.actor_ref, "actor_ref"),
            (self.promotion_approval_ref, "promotion_approval_ref"),
            (self.dry_run_plan_ref, "dry_run_plan_ref"),
            (self.dry_run_plan_hash_ref, "dry_run_plan_hash_ref"),
            (self.real_run_plan_ref, "real_run_plan_ref"),
            (self.real_run_plan_hash_ref, "real_run_plan_hash_ref"),
            (self.safe_execution_scope_ref, "safe_execution_scope_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_tool_refs:
            _validate_m61_ref(ref, "safe_tool_ref")
        _validate_plan_hash(self.dry_run_plan_hash, "dry_run_plan_hash")
        _validate_plan_hash(self.real_run_plan_hash, "real_run_plan_hash")
        _validate_safe_payload(self.safe_promotion_summary)
        return self


class MultiToolDryRunPromotionReceiptPlan(_MultiToolDryRunPromotionModel):
    receipt_plan_ref: str
    promotion_ref: str
    m92_single_session_decision_ref: str
    promotion_approval_ref: str
    dry_run_plan_ref: str
    dry_run_plan_hash_ref: str
    real_run_plan_ref: str
    real_run_plan_hash_ref: str
    safe_tool_refs: list[str]
    store_safe_summary_only: bool = True
    store_safe_refs_only: bool = True
    store_plan_hash_refs_only: bool = True
    store_raw_tool_payload: bool = False
    store_raw_provider_payload: bool = False
    store_raw_prompt: bool = False
    store_secret: bool = False
    execution_performed: bool = False
    real_run_execution_performed: bool = False
    tool_execution_performed: bool = False
    autonomous_execution_performed: bool = False
    session_start_performed: bool = False
    background_worker_started: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M93 promotion receipt stores safe refs and plan hash refs only."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.promotion_ref, "promotion_ref"),
            (self.m92_single_session_decision_ref, "m92_single_session_decision_ref"),
            (self.promotion_approval_ref, "promotion_approval_ref"),
            (self.dry_run_plan_ref, "dry_run_plan_ref"),
            (self.dry_run_plan_hash_ref, "dry_run_plan_hash_ref"),
            (self.real_run_plan_ref, "real_run_plan_ref"),
            (self.real_run_plan_hash_ref, "real_run_plan_hash_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_tool_refs:
            _validate_m61_ref(ref, "safe_tool_ref")
        _validate_safe_payload(self.safe_summary)
        return self


class MultiToolDryRunPromotionDecision(_MultiToolDryRunPromotionModel):
    decision_ref: str
    request_ref: str
    promotion_ref: str
    m92_single_session_decision_ref: str
    actor_ref: str
    promotion_approval_ref: str
    dry_run_plan_ref: str
    dry_run_plan_hash_ref: str
    real_run_plan_ref: str
    real_run_plan_hash_ref: str
    safe_execution_scope_ref: str
    audit_ref: str
    replay_ref: str
    safe_tool_refs: list[str]
    status: MultiToolDryRunPromotionStatus = MultiToolDryRunPromotionStatus.promotion_ready_for_review
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    approval_refs_are_identifiers_only: bool = True
    m92_single_session_revalidated: bool = True
    dry_run_plan_bound: bool = True
    real_run_plan_bound: bool = True
    dry_run_real_run_equivalent: bool = True
    exact_promotion_approval_bound: bool = True
    wildcard_approval_denied: bool = True
    promotion_allowed_for_review: bool = True
    execution_authorized: bool = False
    real_run_execution_authorized: bool = False
    tool_execution_authorized: bool = False
    autonomous_execution_authorized: bool = False
    session_start_authorized: bool = False
    background_worker_authorized: bool = False
    execution_performed: bool = False
    real_run_execution_performed: bool = False
    tool_execution_performed: bool = False
    autonomous_execution_performed: bool = False
    session_start_performed: bool = False
    background_worker_started: bool = False
    command_execution_performed: bool = False
    shell_execution_performed: bool = False
    subprocess_execution_performed: bool = False
    filesystem_mutation_performed: bool = False
    network_access_performed: bool = False
    browser_click_performed: bool = False
    browser_form_performed: bool = False
    plugin_execution_performed: bool = False
    remote_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    receipt_plan: MultiToolDryRunPromotionReceiptPlan
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.decision_ref, "decision_ref"),
            (self.request_ref, "request_ref"),
            (self.promotion_ref, "promotion_ref"),
            (self.m92_single_session_decision_ref, "m92_single_session_decision_ref"),
            (self.actor_ref, "actor_ref"),
            (self.promotion_approval_ref, "promotion_approval_ref"),
            (self.dry_run_plan_ref, "dry_run_plan_ref"),
            (self.dry_run_plan_hash_ref, "dry_run_plan_hash_ref"),
            (self.real_run_plan_ref, "real_run_plan_ref"),
            (self.real_run_plan_hash_ref, "real_run_plan_hash_ref"),
            (self.safe_execution_scope_ref, "safe_execution_scope_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.safe_tool_refs:
            _validate_m61_ref(ref, "safe_tool_ref")
        if not self.reason_codes:
            raise ValueError("M93_REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_multi_tool_dry_run_promotion_decision(
    request: MultiToolDryRunPromotionRequest,
    policy: MultiToolDryRunPromotionPolicy | None = None,
) -> MultiToolDryRunPromotionDecision:
    active_policy = validate_multi_tool_dry_run_promotion_policy(
        policy or MultiToolDryRunPromotionPolicy()
    )
    validated_request = validate_multi_tool_dry_run_promotion_request(request)
    decision = MultiToolDryRunPromotionDecision(
        decision_ref=f"multi-tool-dry-run-promotion-decision:{_ref_suffix(validated_request.promotion_ref)}",
        request_ref=validated_request.request_ref,
        promotion_ref=validated_request.promotion_ref,
        m92_single_session_decision_ref=validated_request.m92_single_session_decision_ref,
        actor_ref=validated_request.actor_ref,
        promotion_approval_ref=validated_request.promotion_approval_ref,
        dry_run_plan_ref=validated_request.dry_run_plan_ref,
        dry_run_plan_hash_ref=validated_request.dry_run_plan_hash_ref,
        real_run_plan_ref=validated_request.real_run_plan_ref,
        real_run_plan_hash_ref=validated_request.real_run_plan_hash_ref,
        safe_execution_scope_ref=validated_request.safe_execution_scope_ref,
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        safe_tool_refs=list(validated_request.safe_tool_refs),
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        approval_refs_are_identifiers_only=active_policy.approval_refs_are_identifiers_only,
        reason_codes=[
            "M93_MULTI_TOOL_DRY_RUN_REAL_RUN_PROMOTION_REVIEW_ONLY",
            "M93_DRY_RUN_REAL_RUN_EQUIVALENCE_REQUIRED",
            "M93_EXACT_PROMOTION_APPROVAL_REQUIRED",
            "M93_PLAN_HASH_BINDING_REQUIRED",
            "M93_NO_UNAPPROVED_REAL_EXECUTION",
            "M94_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M93 defines review-only promotion policy between a dry-run plan and a proposed "
            "real-run plan. Matching plan refs and hashes plus exact non-wildcard promotion "
            "approval are required before any future milestone may consider execution; M93 "
            "performs no real run, tool execution, session start, background work, shell, "
            "network, browser, plugin, model, memory, context, route, dependency, or production action."
        ),
        receipt_plan=MultiToolDryRunPromotionReceiptPlan(
            receipt_plan_ref=f"multi-tool-dry-run-promotion-receipt-plan:{_ref_suffix(validated_request.promotion_ref)}",
            promotion_ref=validated_request.promotion_ref,
            m92_single_session_decision_ref=validated_request.m92_single_session_decision_ref,
            promotion_approval_ref=validated_request.promotion_approval_ref,
            dry_run_plan_ref=validated_request.dry_run_plan_ref,
            dry_run_plan_hash_ref=validated_request.dry_run_plan_hash_ref,
            real_run_plan_ref=validated_request.real_run_plan_ref,
            real_run_plan_hash_ref=validated_request.real_run_plan_hash_ref,
            safe_tool_refs=list(validated_request.safe_tool_refs),
        ),
    )
    return validate_multi_tool_dry_run_promotion_decision(decision)


def validate_multi_tool_dry_run_promotion_policy(
    policy: MultiToolDryRunPromotionPolicy,
) -> MultiToolDryRunPromotionPolicy:
    validated = MultiToolDryRunPromotionPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M93_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M93_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_DRY_RUN_PROMOTION_CONTENT_DENIED") from exc
    return validated


def validate_multi_tool_dry_run_promotion_request(
    request: MultiToolDryRunPromotionRequest,
) -> MultiToolDryRunPromotionRequest:
    payload = _model_payload(request)
    for field_name, reason in _M93_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    validated = MultiToolDryRunPromotionRequest.model_validate(payload)
    for field_name, reason in _M93_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M93_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_prior_milestone_refs(validated.prior_milestone_refs)
    _validate_safe_tool_refs(validated.safe_tool_refs)
    _validate_approval_ref(validated.promotion_approval_ref)
    if validated.dry_run_plan_hash != validated.real_run_plan_hash:
        raise ValueError("M93_DRY_RUN_REAL_RUN_PLAN_HASH_MISMATCH")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_DRY_RUN_PROMOTION_CONTENT_DENIED") from exc
    m92_decision = validate_low_risk_tool_autonomy_single_session_decision(
        validated.m92_single_session_decision
    )
    _validate_exact_m92_binding(validated, m92_decision)
    return validated


def validate_multi_tool_dry_run_promotion_decision(
    decision: MultiToolDryRunPromotionDecision,
) -> MultiToolDryRunPromotionDecision:
    validated = MultiToolDryRunPromotionDecision.model_validate(_model_payload(decision))
    for field_name, reason in _M93_DECISION_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MultiToolDryRunPromotionStatus.promotion_ready_for_review:
        raise ValueError("M93_PROMOTION_READY_STATUS_REQUIRED")
    for field_name, reason in _M93_DECISION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    if "M93_MULTI_TOOL_DRY_RUN_REAL_RUN_PROMOTION_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M93_REASON_CODE_REQUIRED")
    _validate_receipt_plan(validated.receipt_plan)
    _validate_receipt_binding(validated)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_DRY_RUN_PROMOTION_CONTENT_DENIED") from exc
    return validated


def _validate_receipt_plan(
    receipt_plan: MultiToolDryRunPromotionReceiptPlan,
) -> MultiToolDryRunPromotionReceiptPlan:
    validated = MultiToolDryRunPromotionReceiptPlan.model_validate(_model_payload(receipt_plan))
    for field_name, reason in _M93_RECEIPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M93_RECEIPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    return validated


def _validate_exact_m92_binding(request: MultiToolDryRunPromotionRequest, decision: Any) -> None:
    for request_value, decision_value, reason in [
        (
            request.m92_single_session_decision_ref,
            decision.decision_ref,
            "M93_M92_SINGLE_SESSION_BINDING_MISMATCH",
        ),
        (request.actor_ref, decision.actor_ref, "M93_ACTOR_BINDING_MISMATCH"),
        (
            request.safe_execution_scope_ref,
            decision.safe_execution_scope_ref,
            "M93_SAFE_EXECUTION_SCOPE_BINDING_MISMATCH",
        ),
        (request.audit_ref, decision.audit_ref, "M93_AUDIT_BINDING_MISMATCH"),
        (request.replay_ref, decision.replay_ref, "M93_REPLAY_BINDING_MISMATCH"),
    ]:
        if request_value != decision_value:
            raise ValueError(reason)
    if decision.safe_tool_ref not in request.safe_tool_refs:
        raise ValueError("M93_SAFE_TOOL_BINDING_MISMATCH")


def _validate_receipt_binding(decision: MultiToolDryRunPromotionDecision) -> None:
    receipt = decision.receipt_plan
    for receipt_value, decision_value in [
        (receipt.promotion_ref, decision.promotion_ref),
        (receipt.m92_single_session_decision_ref, decision.m92_single_session_decision_ref),
        (receipt.promotion_approval_ref, decision.promotion_approval_ref),
        (receipt.dry_run_plan_ref, decision.dry_run_plan_ref),
        (receipt.dry_run_plan_hash_ref, decision.dry_run_plan_hash_ref),
        (receipt.real_run_plan_ref, decision.real_run_plan_ref),
        (receipt.real_run_plan_hash_ref, decision.real_run_plan_hash_ref),
        (receipt.safe_tool_refs, decision.safe_tool_refs),
    ]:
        if receipt_value != decision_value:
            raise ValueError("M93_RECEIPT_BINDING_MISMATCH")


def _validate_prior_milestone_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M93_PRIOR_MILESTONE_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M93_PRIOR_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "prior_milestone_ref")
    missing = [ref for ref in REQUIRED_M93_PRIOR_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M93_PRIOR_MILESTONE_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M93_PRIOR_MILESTONE_REFS]
    if unexpected:
        raise ValueError("M93_PRIOR_MILESTONE_REF_UNEXPECTED")


def _validate_safe_tool_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M93_SAFE_TOOL_REFS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M93_SAFE_TOOL_REF_DUPLICATE")
    if len(refs) < 2:
        raise ValueError("M93_MULTI_TOOL_PLAN_REQUIRED")
    for ref in refs:
        _validate_m61_ref(ref, "safe_tool_ref")


def _validate_approval_ref(ref: str) -> None:
    lower = ref.lower()
    if "approval_test_" in lower:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    if "*" in ref or "wildcard" in lower or lower.endswith(":all"):
        raise ValueError("M93_WILDCARD_APPROVAL_DENIED")
    if "promotion" not in lower:
        raise ValueError("M93_EXACT_PROMOTION_APPROVAL_REQUIRED")
    _validate_m61_ref(ref, "promotion_approval_ref")


def _validate_plan_hash(value: str, field_name: str) -> None:
    if not value or len(value) < 16:
        raise ValueError(f"{field_name.upper()}_REQUIRED")
    lowered = value.lower()
    if "raw" in lowered or "secret" in lowered or "prompt" in lowered:
        raise ValueError("M93_UNSAFE_PLAN_HASH_DENIED")


def _model_payload(model: Any) -> dict[str, Any]:
    if isinstance(model, BaseModel):
        payload = dict(model.__dict__)
        payload.update(getattr(model, "__pydantic_extra__", None) or {})
        return payload
    if isinstance(model, dict):
        return dict(model)
    raise TypeError(f"unsupported model payload type: {type(model)!r}")


def _ref_suffix(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


_M93_REQUIRED_TRUE = [
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
    ("local_only", "M93_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M93_SAFE_REFS_ONLY_REQUIRED"),
    ("approval_refs_are_identifiers_only", "APPROVAL_REF_IDENTIFIER_ONLY"),
]
_M93_POLICY_REQUIRED_TRUE = [
    ("enabled_for_review", "M93_REVIEW_ENABLED_REQUIRED"),
    ("exact_m92_single_session_binding_required", "M93_EXACT_M92_BINDING_REQUIRED"),
    ("exact_dry_run_plan_binding_required", "M93_EXACT_DRY_RUN_PLAN_BINDING_REQUIRED"),
    ("exact_real_run_plan_binding_required", "M93_EXACT_REAL_RUN_PLAN_BINDING_REQUIRED"),
    ("dry_run_real_run_equivalence_required", "M93_DRY_RUN_REAL_RUN_EQUIVALENCE_REQUIRED"),
    ("exact_promotion_approval_required", "M93_EXACT_PROMOTION_APPROVAL_REQUIRED"),
    ("wildcard_approval_denied", "M93_WILDCARD_APPROVAL_DENIAL_REQUIRED"),
    ("m94_future_only", "M94_FUTURE_ONLY_REQUIRED"),
    *_M93_REQUIRED_TRUE,
]
_M93_DECISION_REQUIRED_TRUE = [
    *_M93_REQUIRED_TRUE,
    ("m92_single_session_revalidated", "M93_M92_REVALIDATION_REQUIRED"),
    ("dry_run_plan_bound", "M93_DRY_RUN_PLAN_BINDING_REQUIRED"),
    ("real_run_plan_bound", "M93_REAL_RUN_PLAN_BINDING_REQUIRED"),
    ("dry_run_real_run_equivalent", "M93_DRY_RUN_REAL_RUN_EQUIVALENCE_REQUIRED"),
    ("exact_promotion_approval_bound", "M93_EXACT_PROMOTION_APPROVAL_REQUIRED"),
    ("wildcard_approval_denied", "M93_WILDCARD_APPROVAL_DENIAL_REQUIRED"),
    ("promotion_allowed_for_review", "M93_PROMOTION_REVIEW_REQUIRED"),
]
_M93_RECEIPT_REQUIRED_TRUE = [
    ("store_safe_summary_only", "M93_SAFE_SUMMARY_ONLY_REQUIRED"),
    ("store_safe_refs_only", "M93_SAFE_REFS_ONLY_REQUIRED"),
    ("store_plan_hash_refs_only", "M93_PLAN_HASH_REFS_ONLY_REQUIRED"),
]
_M93_DENIALS = [
    ("execution", "EXECUTION_DENIED"),
    ("real_run_execution", "M93_REAL_RUN_EXECUTION_DENIED"),
    ("tool_execution", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start", "SESSION_START_DENIED"),
    ("background_worker", "BACKGROUND_WORKER_DENIED"),
    ("command_execution", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution", "SUBPROCESS_EXECUTION_DENIED"),
    ("filesystem_mutation", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access", "NETWORK_ACCESS_DENIED"),
    ("browser_click", "BROWSER_CLICK_DENIED"),
    ("browser_form", "BROWSER_FORM_DENIED"),
    ("plugin_execution", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution", "REMOTE_EXECUTION_DENIED"),
    ("model_call", "MODEL_CALL_DENIED"),
    ("memory_write", "MEMORY_WRITE_DENIED"),
    ("context_injection", "CONTEXT_INJECTION_DENIED"),
    ("backend_route", "BACKEND_ROUTE_DENIED"),
    ("control_center_control", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority", "PRODUCTION_AUTHORITY_DENIED"),
]
_M93_POLICY_DENIALS = [
    ("real_run_promotion_enabled", "M93_REAL_RUN_PROMOTION_ENABLEMENT_DENIED"),
    ("real_run_execution_enabled", "M93_REAL_RUN_EXECUTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_enabled", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_enabled", "SESSION_START_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("command_execution_enabled", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_enabled", "SUBPROCESS_EXECUTION_DENIED"),
    ("filesystem_mutation_enabled", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("browser_click_enabled", "BROWSER_CLICK_DENIED"),
    ("browser_form_enabled", "BROWSER_FORM_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
_M93_REQUEST_DENIALS = [
    *[(f"{field}_requested", reason) for field, reason in _M93_DENIALS],
    ("contains_raw_tool_payload", "M93_RAW_TOOL_PAYLOAD_DENIED"),
    ("contains_raw_provider_payload", "M93_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("contains_raw_prompt", "RAW_PROMPT_DENIED"),
    ("contains_secret", "SECRET_LIKE_DRY_RUN_PROMOTION_CONTENT_DENIED"),
]
_M93_DECISION_DENIALS = [
    *[(f"{field}_authorized", reason) for field, reason in _M93_DENIALS[:6]],
    ("execution_performed", "EXECUTION_DENIED"),
    ("real_run_execution_performed", "M93_REAL_RUN_EXECUTION_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_performed", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_performed", "SESSION_START_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
    ("command_execution_performed", "COMMAND_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("subprocess_execution_performed", "SUBPROCESS_EXECUTION_DENIED"),
    ("filesystem_mutation_performed", "FILESYSTEM_MUTATION_DENIED"),
    ("network_access_performed", "NETWORK_ACCESS_DENIED"),
    ("browser_click_performed", "BROWSER_CLICK_DENIED"),
    ("browser_form_performed", "BROWSER_FORM_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("remote_execution_performed", "REMOTE_EXECUTION_DENIED"),
    ("model_call_performed", "MODEL_CALL_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
_M93_RECEIPT_DENIALS = [
    ("store_raw_tool_payload", "M93_RAW_TOOL_PAYLOAD_DENIED"),
    ("store_raw_provider_payload", "M93_RAW_PROVIDER_PAYLOAD_DENIED"),
    ("store_raw_prompt", "RAW_PROMPT_DENIED"),
    ("store_secret", "SECRET_LIKE_DRY_RUN_PROMOTION_CONTENT_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("real_run_execution_performed", "M93_REAL_RUN_EXECUTION_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("autonomous_execution_performed", "AUTONOMOUS_EXECUTION_DENIED"),
    ("session_start_performed", "SESSION_START_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
]
