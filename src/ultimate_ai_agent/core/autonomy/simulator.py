from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import (
    AutonomyRiskClass,
    _ref_suffix,
    _validate_m61_ref,
    _validate_safe_payload,
)
from ultimate_ai_agent.core.autonomy.policies import AutonomyPolicyDecision


AUTONOMOUS_PLAN_SIMULATOR_DOCS = [
    "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR.md",
    "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_CONTRACTS.md",
    "docs/autonomy/AUTONOMOUS_PLAN_SIMULATOR_NON_GOALS.md",
    "docs/autonomy/M64_TO_M65_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class _AutonomousPlanSimulatorModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomousPlanSimulationStep(_AutonomousPlanSimulatorModel):
    step_ref: str
    intent_ref: str
    capability_ref: str
    resource_ref: str
    simulated_outcome_ref: str
    risk_class: AutonomyRiskClass = AutonomyRiskClass.low
    depends_on_step_refs: list[str] = Field(default_factory=list)
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    execution_requested: bool = False
    execution_performed: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    background_worker_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.step_ref, "step_ref"),
            (self.intent_ref, "intent_ref"),
            (self.capability_ref, "capability_ref"),
            (self.resource_ref, "resource_ref"),
            (self.simulated_outcome_ref, "simulated_outcome_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.depends_on_step_refs:
            _validate_m61_ref(ref, "depends_on_step_ref")
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        return self


class AutonomousPlanSimulationRequest(_AutonomousPlanSimulatorModel):
    simulation_request_ref: str
    policy_decision: AutonomyPolicyDecision
    steps: list[AutonomousPlanSimulationStep]
    actor_ref: str
    resource_refs: list[str]
    capability_refs: list[str]
    allowlist_refs: list[str]
    audit_ref: str
    replay_ref: str
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    review_only: bool = True
    dry_run_only: bool = True
    deterministic: bool = True
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    execution_requested: bool = False
    execution_performed: bool = False
    autonomous_actions_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    background_worker_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.simulation_request_ref, "simulation_request_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for refs, field_name, reason in [
            (self.resource_refs, "resource_ref", "RESOURCE_BINDING_REQUIRED"),
            (self.capability_refs, "capability_ref", "CAPABILITY_BINDING_REQUIRED"),
            (self.allowlist_refs, "allowlist_ref", "ALLOWLIST_REQUIRED"),
        ]:
            if not refs:
                raise ValueError(reason)
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        if not self.steps:
            raise ValueError("SIMULATION_STEP_REQUIRED")
        return self


class AutonomousPlanSimulationResult(_AutonomousPlanSimulatorModel):
    simulation_result_ref: str
    simulation_request_ref: str
    policy_decision: AutonomyPolicyDecision
    policy_decision_ref: str
    simulated_step_refs: list[str]
    contract_valid_for_review: bool = True
    review_only: bool = True
    dry_run_only: bool = True
    deterministic: bool = True
    simulation_performed: bool = True
    authority_granted: bool = False
    session_started: bool = False
    execution_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str

    @model_validator(mode="after")
    def validate_result(self) -> Any:
        _validate_m61_ref(self.simulation_result_ref, "simulation_result_ref")
        _validate_m61_ref(self.simulation_request_ref, "simulation_request_ref")
        _validate_m61_ref(self.policy_decision_ref, "policy_decision_ref")
        for ref in self.simulated_step_refs:
            _validate_m61_ref(ref, "simulated_step_ref")
        if not self.contract_valid_for_review or not self.review_only:
            raise ValueError("REVIEW_ONLY_REQUIRED")
        if not self.dry_run_only:
            raise ValueError("DRY_RUN_FIRST_REQUIRED")
        if not self.deterministic:
            raise ValueError("DETERMINISTIC_SIMULATION_REQUIRED")
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


def validate_autonomous_plan_simulation_step(
    step: AutonomousPlanSimulationStep,
) -> AutonomousPlanSimulationStep:
    validated = AutonomousPlanSimulationStep.model_validate(step.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMOUS_PLAN_SIMULATION_CONTENT_DENIED") from exc
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _STEP_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_autonomous_plan_simulation_request(
    request: AutonomousPlanSimulationRequest,
) -> AutonomousPlanSimulationRequest:
    validated = AutonomousPlanSimulationRequest.model_validate(request.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMOUS_PLAN_SIMULATION_CONTENT_DENIED") from exc
    _validate_policy_decision_for_simulation(validated.policy_decision)
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _REQUEST_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    steps = [validate_autonomous_plan_simulation_step(step) for step in validated.steps]
    _validate_step_graph(steps)
    return validated


def build_autonomous_plan_simulation_result(
    request: AutonomousPlanSimulationRequest,
) -> AutonomousPlanSimulationResult:
    validated = validate_autonomous_plan_simulation_request(request)
    ordered_step_refs = _topological_step_refs(validated.steps)
    reason_codes = ["M64_AUTONOMOUS_PLAN_SIMULATION_REVIEW_ONLY"]
    if validated.approval_ref:
        reason_codes.append("APPROVAL_REF_IDENTIFIER_ONLY")
    return AutonomousPlanSimulationResult(
        simulation_result_ref=f"autonomy-plan-simulation-result:{_ref_suffix(validated.simulation_request_ref)}",
        simulation_request_ref=validated.simulation_request_ref,
        policy_decision=validated.policy_decision,
        policy_decision_ref=validated.policy_decision.decision_ref,
        simulated_step_refs=ordered_step_refs,
        contract_valid_for_review=True,
        review_only=True,
        dry_run_only=True,
        deterministic=True,
        simulation_performed=True,
        authority_granted=False,
        session_started=False,
        execution_performed=False,
        side_effects_performed=[],
        reason_codes=reason_codes,
        safe_summary=(
            "M64 deterministically simulates already-reviewed autonomous plan contracts; "
            "no authority, session start, execution, context injection, memory write, "
            "background worker, or side effect is performed."
        ),
    )


_STEP_DENIALS = [
    ("execution_requested", "EXECUTION_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
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

_REQUEST_REQUIRED_TRUE = [
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("dry_run_only", "DRY_RUN_FIRST_REQUIRED"),
    ("deterministic", "DETERMINISTIC_SIMULATION_REQUIRED"),
]

_REQUEST_DENIALS = [
    ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
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


def _validate_policy_decision_for_simulation(decision: AutonomyPolicyDecision) -> None:
    validated = AutonomyPolicyDecision.model_validate(decision.model_dump())
    if not validated.contract_valid_for_review:
        raise ValueError("POLICY_REVIEW_ALLOWANCE_REQUIRED")
    if not validated.policy_matched or not validated.policy_allows_review:
        raise ValueError("POLICY_REVIEW_ALLOWANCE_REQUIRED")
    if validated.authority_granted:
        raise ValueError("AUTONOMY_POLICY_AUTHORITY_DENIED")
    if validated.session_started:
        raise ValueError("AUTONOMY_SESSION_START_DENIED")
    if validated.execution_performed:
        raise ValueError("EXECUTION_DENIED")
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")


def _validate_step_graph(steps: list[AutonomousPlanSimulationStep]) -> None:
    refs = [step.step_ref for step in steps]
    if len(refs) != len(set(refs)):
        raise ValueError("SIMULATION_STEP_DUPLICATE_REF_DENIED")
    ref_set = set(refs)
    for step in steps:
        for dep_ref in step.depends_on_step_refs:
            if dep_ref == step.step_ref:
                raise ValueError("SIMULATION_STEP_SELF_DEPENDENCY_DENIED")
            if dep_ref not in ref_set:
                raise ValueError("SIMULATION_STEP_MISSING_DEPENDENCY_DENIED")
    _topological_step_refs(steps)


def _topological_step_refs(steps: list[AutonomousPlanSimulationStep]) -> list[str]:
    by_ref = {step.step_ref: step for step in steps}
    permanent: set[str] = set()
    temporary: set[str] = set()
    ordered: list[str] = []

    def visit(step_ref: str) -> None:
        if step_ref in permanent:
            return
        if step_ref in temporary:
            raise ValueError("SIMULATION_STEP_CYCLE_DENIED")
        temporary.add(step_ref)
        for dep_ref in sorted(by_ref[step_ref].depends_on_step_refs):
            visit(dep_ref)
        temporary.remove(step_ref)
        permanent.add(step_ref)
        ordered.append(step_ref)

    for step_ref in sorted(by_ref):
        visit(step_ref)
    return ordered
