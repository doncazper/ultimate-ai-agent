from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import (
    AutonomyAuthorityMode,
    AutonomyRiskClass,
    _ref_suffix,
    _validate_m61_ref,
    _validate_safe_payload,
)
from ultimate_ai_agent.core.autonomy.sessions import (
    ScopedAutonomySessionRequest,
    validate_scoped_autonomy_session_scope,
)


AUTONOMY_POLICY_ENGINE_DOCS = [
    "docs/autonomy/AUTONOMY_POLICY_ENGINE_V1.md",
    "docs/autonomy/AUTONOMY_POLICY_RULE_CONTRACTS.md",
    "docs/autonomy/AUTONOMY_POLICY_ENGINE_NON_GOALS.md",
    "docs/autonomy/M63_TO_M64_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class _AutonomyPolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomyPolicyRule(_AutonomyPolicyModel):
    rule_ref: str
    allowed_actor_refs: list[str]
    allowed_resource_refs: list[str]
    allowed_capability_refs: list[str]
    required_allowlist_refs: list[str]
    max_mode: AutonomyAuthorityMode = AutonomyAuthorityMode.dry_run_plan
    max_risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    max_duration_seconds: int = Field(gt=0)
    revocation_required: bool = True
    audit_replay_required: bool = True
    dry_run_only: bool = True
    policy_activation_enabled: bool = False
    session_start_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    background_worker_enabled: bool = False
    production_authority_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.rule_ref, "rule_ref")
        for refs, field_name, reason in [
            (self.allowed_actor_refs, "actor_ref", "POLICY_ACTOR_BINDING_REQUIRED"),
            (self.allowed_resource_refs, "resource_ref", "POLICY_RESOURCE_BINDING_REQUIRED"),
            (self.allowed_capability_refs, "capability_ref", "POLICY_CAPABILITY_BINDING_REQUIRED"),
            (self.required_allowlist_refs, "allowlist_ref", "POLICY_ALLOWLIST_REQUIRED"),
        ]:
            if not refs:
                raise ValueError(reason)
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        return self


class AutonomyPolicyEnginePolicy(_AutonomyPolicyModel):
    policy_ref: str
    policy_version_ref: str
    rules: list[AutonomyPolicyRule]
    disabled_by_default: bool = True
    review_only: bool = True
    policy_activation_enabled: bool = False
    backend_routes_enabled: bool = False
    dependencies_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        _validate_m61_ref(self.policy_version_ref, "policy_version_ref")
        if not self.rules:
            raise ValueError("POLICY_RULE_REQUIRED")
        return self


class AutonomyPolicyEvaluationRequest(_AutonomyPolicyModel):
    evaluation_request_ref: str
    policy: AutonomyPolicyEnginePolicy
    session_request: ScopedAutonomySessionRequest
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    execution_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.evaluation_request_ref, "evaluation_request_ref")
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        return self


class AutonomyPolicyDecision(_AutonomyPolicyModel):
    decision_ref: str
    evaluation_request_ref: str
    policy_ref: str
    session_request_ref: str
    matched_rule_ref: str | None = None
    contract_valid_for_review: bool = True
    policy_matched: bool = False
    policy_allows_review: bool = False
    authority_granted: bool = False
    session_started: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_decision(self):
        _validate_m61_ref(self.decision_ref, "decision_ref")
        _validate_m61_ref(self.evaluation_request_ref, "evaluation_request_ref")
        _validate_m61_ref(self.policy_ref, "policy_ref")
        _validate_m61_ref(self.session_request_ref, "session_request_ref")
        if self.matched_rule_ref is not None:
            _validate_m61_ref(self.matched_rule_ref, "matched_rule_ref")
        if self.authority_granted:
            raise ValueError("AUTONOMY_POLICY_AUTHORITY_DENIED")
        if self.session_started:
            raise ValueError("AUTONOMY_SESSION_START_DENIED")
        if self.execution_performed:
            raise ValueError("EXECUTION_DENIED")
        if self.side_effects_performed:
            raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
        _validate_safe_payload(self.safe_summary)
        return self


def validate_autonomy_policy_rule(rule: AutonomyPolicyRule) -> AutonomyPolicyRule:
    validated = AutonomyPolicyRule.model_validate(rule.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_POLICY_CONTENT_DENIED") from exc
    for field_name, reason in _RULE_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _RULE_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_autonomy_policy_engine_policy(
    policy: AutonomyPolicyEnginePolicy,
) -> AutonomyPolicyEnginePolicy:
    validated = AutonomyPolicyEnginePolicy.model_validate(policy.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_POLICY_CONTENT_DENIED") from exc
    if not validated.disabled_by_default:
        raise ValueError("DISABLED_BY_DEFAULT_REQUIRED")
    if not validated.review_only:
        raise ValueError("REVIEW_ONLY_REQUIRED")
    for field_name, reason in _POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    for rule in validated.rules:
        validate_autonomy_policy_rule(rule)
    return validated


def validate_autonomy_policy_evaluation_request(
    request: AutonomyPolicyEvaluationRequest,
) -> AutonomyPolicyEvaluationRequest:
    validated = AutonomyPolicyEvaluationRequest.model_validate(request.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_POLICY_CONTENT_DENIED") from exc
    validate_autonomy_policy_engine_policy(validated.policy)
    _validate_session_request_for_policy(validated.session_request)
    if validated.approval_test_ref or validated.session_request.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def build_autonomy_policy_decision(
    request: AutonomyPolicyEvaluationRequest,
) -> AutonomyPolicyDecision:
    validated = validate_autonomy_policy_evaluation_request(request)
    reason_codes: list[str] = []
    matched_rule_ref: str | None = None
    for rule in validated.policy.rules:
        rule_result = _evaluate_rule(rule, validated.session_request)
        if rule_result is None:
            matched_rule_ref = rule.rule_ref
            reason_codes.append("M63_AUTONOMY_POLICY_MATCH_REVIEW_ONLY")
            break
        reason_codes.extend(rule_result)
    if validated.approval_ref or validated.session_request.approval_ref:
        reason_codes.append("APPROVAL_REF_IDENTIFIER_ONLY")
    policy_matched = matched_rule_ref is not None
    return AutonomyPolicyDecision(
        decision_ref=f"autonomy-policy-decision:{_ref_suffix(validated.evaluation_request_ref)}",
        evaluation_request_ref=validated.evaluation_request_ref,
        policy_ref=validated.policy.policy_ref,
        session_request_ref=validated.session_request.session_request_ref,
        matched_rule_ref=matched_rule_ref,
        contract_valid_for_review=True,
        policy_matched=policy_matched,
        policy_allows_review=policy_matched,
        authority_granted=False,
        session_started=False,
        execution_performed=False,
        side_effects_performed=[],
        reason_codes=reason_codes or ["M63_AUTONOMY_POLICY_NO_MATCH"],
        safe_summary="M63 evaluates autonomy policy contracts for review only; no authority is granted.",
    )


_RISK_ORDER = {
    AutonomyRiskClass.low: 0,
    AutonomyRiskClass.medium: 1,
    AutonomyRiskClass.high: 2,
    AutonomyRiskClass.critical: 3,
}
_MODE_ORDER = {
    AutonomyAuthorityMode.off: 0,
    AutonomyAuthorityMode.observe_only: 1,
    AutonomyAuthorityMode.dry_run_plan: 2,
    AutonomyAuthorityMode.ask_before_every_action: 3,
    AutonomyAuthorityMode.scoped_autonomy_window: 4,
    AutonomyAuthorityMode.trusted_recurring_automation: 5,
    AutonomyAuthorityMode.production_authority_later: 6,
}

_RULE_REQUIRED_TRUE = [
    ("revocation_required", "REVOCATION_REQUIRED"),
    ("audit_replay_required", "AUDIT_REPLAY_REQUIRED"),
    ("dry_run_only", "DRY_RUN_FIRST_REQUIRED"),
]

_RULE_DENIALS = [
    ("policy_activation_enabled", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_enabled", "AUTONOMY_SESSION_START_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_POLICY_DENIALS = [
    ("policy_activation_enabled", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
    ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
]

_REQUEST_DENIALS = [
    ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
]


def _validate_session_request_for_policy(request: ScopedAutonomySessionRequest) -> None:
    validated = ScopedAutonomySessionRequest.model_validate(request.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_POLICY_CONTENT_DENIED") from exc
    validate_scoped_autonomy_session_scope(validated.scope)
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in [
        ("start_requested", "AUTONOMY_SESSION_START_DENIED"),
        ("session_active", "AUTONOMY_SESSION_ACTIVATION_DENIED"),
        ("execution_requested", "EXECUTION_DENIED"),
        ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
        ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)


def _evaluate_rule(
    rule: AutonomyPolicyRule, session_request: ScopedAutonomySessionRequest
) -> list[str] | None:
    failures: list[str] = []
    scope = session_request.scope
    if _MODE_ORDER[session_request.requested_mode] > _MODE_ORDER[rule.max_mode]:
        failures.append("POLICY_MODE_EXCEEDS_RULE")
    if scope.actor_ref not in set(rule.allowed_actor_refs):
        failures.append("POLICY_ACTOR_NOT_ALLOWED")
    if not set(scope.resource_refs).issubset(set(rule.allowed_resource_refs)):
        failures.append("POLICY_RESOURCE_NOT_ALLOWED")
    if not set(scope.capability_refs).issubset(set(rule.allowed_capability_refs)):
        failures.append("POLICY_CAPABILITY_NOT_ALLOWED")
    if not set(rule.required_allowlist_refs).issubset(set(scope.allowlist_refs)):
        failures.append("POLICY_ALLOWLIST_NOT_SATISFIED")
    if scope.max_duration_seconds > rule.max_duration_seconds:
        failures.append("POLICY_DURATION_EXCEEDED")
    if _RISK_ORDER[scope.risk_class] > _RISK_ORDER[rule.max_risk_class]:
        failures.append("POLICY_RISK_EXCEEDED")
    return failures or None
