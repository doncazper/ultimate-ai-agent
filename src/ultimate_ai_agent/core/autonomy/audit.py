from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import (
    _ref_suffix,
    _validate_m61_ref,
    _validate_safe_payload,
)
from ultimate_ai_agent.core.autonomy.simulator import (
    AutonomousPlanSimulationResult,
)


AUTONOMY_AUDIT_REPLAY_VIEWER_DOCS = [
    "docs/autonomy/AUTONOMY_AUDIT_REPLAY_VIEWER.md",
    "docs/autonomy/AUTONOMY_AUDIT_REPLAY_CONTRACTS.md",
    "docs/autonomy/AUTONOMY_AUDIT_REPLAY_NON_GOALS.md",
    "docs/autonomy/M65_TO_M66_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class _AutonomyAuditReplayModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomyReplayStepView(_AutonomyAuditReplayModel):
    step_ref: str
    replay_outcome_ref: str
    status: str = "simulated_review_only"
    safe_summary: str = "Replay step view is deterministic, redacted, review-only, and non-authoritative."

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.step_ref, "step_ref")
        _validate_m61_ref(self.replay_outcome_ref, "replay_outcome_ref")
        _validate_safe_payload(self.safe_summary)
        if self.status != "simulated_review_only":
            raise ValueError("REPLAY_STEP_REVIEW_ONLY_REQUIRED")
        return self


class AutonomyAuditReplayView(_AutonomyAuditReplayModel):
    audit_view_ref: str
    simulation_result: AutonomousPlanSimulationResult
    simulation_result_ref: str
    simulation_request_ref: str
    policy_decision_ref: str
    actor_ref: str
    audit_ref: str
    replay_ref: str
    simulated_step_refs: list[str]
    replay_steps: list[AutonomyReplayStepView]
    contract_valid_for_review: bool = True
    review_only: bool = True
    replay_view_only: bool = True
    deterministic: bool = True
    authority_granted: bool = False
    session_started: bool = False
    policy_activation_requested: bool = False
    session_start_requested: bool = False
    autonomous_actions_enabled: bool = False
    background_worker_enabled: bool = False
    execution_requested: bool = False
    execution_performed: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    network_tool_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    model_provider_call_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    approval_ref: str | None = None
    approval_test_ref: str | None = None
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.audit_view_ref, "audit_view_ref"),
            (self.simulation_result_ref, "simulation_result_ref"),
            (self.simulation_request_ref, "simulation_request_ref"),
            (self.policy_decision_ref, "policy_decision_ref"),
            (self.actor_ref, "actor_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.simulated_step_refs:
            _validate_m61_ref(ref, "simulated_step_ref")
        if self.approval_ref is not None:
            _validate_m61_ref(self.approval_ref, "approval_ref")
        if self.approval_test_ref is not None:
            _validate_m61_ref(self.approval_test_ref, "approval_test_ref")
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_autonomy_audit_replay_view(
    *,
    audit_view_ref: str,
    simulation_result: AutonomousPlanSimulationResult,
    actor_ref: str,
    audit_ref: str,
    replay_ref: str,
    approval_ref: str | None = None,
    approval_test_ref: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AutonomyAuditReplayView:
    validated_result = AutonomousPlanSimulationResult.model_validate(simulation_result.model_dump())
    replay_steps = [
        AutonomyReplayStepView(
            step_ref=step_ref,
            replay_outcome_ref=f"autonomy-replay-outcome:{_ref_suffix(step_ref)}",
        )
        for step_ref in validated_result.simulated_step_refs
    ]
    return validate_autonomy_audit_replay_view(
        AutonomyAuditReplayView(
            audit_view_ref=audit_view_ref,
            simulation_result=validated_result,
            simulation_result_ref=validated_result.simulation_result_ref,
            simulation_request_ref=validated_result.simulation_request_ref,
            policy_decision_ref=validated_result.policy_decision_ref,
            actor_ref=actor_ref,
            audit_ref=audit_ref,
            replay_ref=replay_ref,
            simulated_step_refs=list(validated_result.simulated_step_refs),
            replay_steps=replay_steps,
            contract_valid_for_review=True,
            review_only=True,
            replay_view_only=True,
            deterministic=True,
            authority_granted=False,
            session_started=False,
            execution_performed=False,
            side_effects_performed=[],
            approval_ref=approval_ref,
            approval_test_ref=approval_test_ref,
            reason_codes=["M65_AUTONOMY_AUDIT_REPLAY_VIEW_REVIEW_ONLY"],
            safe_summary=(
                "M65 displays deterministic audit and replay references for an M64 simulation result; "
                "it grants no authority, starts no session, executes nothing, writes no memory, "
                "injects no context, exports nothing, and performs no side effect."
            ),
            metadata={} if metadata is None else metadata,
        )
    )


def validate_autonomy_audit_replay_view(view: AutonomyAuditReplayView) -> AutonomyAuditReplayView:
    validated = AutonomyAuditReplayView.model_validate(view.model_dump())
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_AUTONOMY_AUDIT_REPLAY_CONTENT_DENIED") from exc
    _validate_simulation_result_for_audit_replay(validated.simulation_result)
    if validated.approval_test_ref:
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    for field_name, reason in _AUDIT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _AUDIT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")
    expected_step_refs = list(validated.simulation_result.simulated_step_refs)
    replay_step_refs = [step.step_ref for step in validated.replay_steps]
    if validated.simulated_step_refs != expected_step_refs or replay_step_refs != expected_step_refs:
        raise ValueError("REPLAY_STEP_SEQUENCE_MISMATCH_DENIED")
    if validated.simulation_result_ref != validated.simulation_result.simulation_result_ref:
        raise ValueError("SIMULATION_RESULT_BINDING_MISMATCH_DENIED")
    if validated.simulation_request_ref != validated.simulation_result.simulation_request_ref:
        raise ValueError("SIMULATION_REQUEST_BINDING_MISMATCH_DENIED")
    if validated.policy_decision_ref != validated.simulation_result.policy_decision_ref:
        raise ValueError("POLICY_DECISION_BINDING_MISMATCH_DENIED")
    return validated


def _validate_simulation_result_for_audit_replay(result: AutonomousPlanSimulationResult) -> None:
    validated = AutonomousPlanSimulationResult.model_validate(result.model_dump())
    if validated.policy_decision is None:
        raise ValueError("POLICY_DECISION_BINDING_REQUIRED")
    if not validated.contract_valid_for_review or not validated.review_only:
        raise ValueError("REVIEW_ONLY_REQUIRED")
    if not validated.dry_run_only:
        raise ValueError("DRY_RUN_FIRST_REQUIRED")
    if not validated.deterministic:
        raise ValueError("DETERMINISTIC_REPLAY_REQUIRED")
    if validated.authority_granted:
        raise ValueError("AUTONOMY_POLICY_AUTHORITY_DENIED")
    if validated.session_started:
        raise ValueError("AUTONOMY_SESSION_START_DENIED")
    if validated.execution_performed:
        raise ValueError("EXECUTION_DENIED")
    if validated.side_effects_performed:
        raise ValueError("AUTONOMY_SIDE_EFFECTS_DENIED")


_AUDIT_REQUIRED_TRUE = [
    ("contract_valid_for_review", "REVIEW_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("replay_view_only", "REPLAY_VIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REPLAY_REQUIRED"),
]

_AUDIT_DENIALS = [
    ("authority_granted", "AUTONOMY_POLICY_AUTHORITY_DENIED"),
    ("session_started", "AUTONOMY_SESSION_START_DENIED"),
    ("policy_activation_requested", "AUTONOMY_POLICY_ACTIVATION_DENIED"),
    ("session_start_requested", "AUTONOMY_SESSION_START_DENIED"),
    ("autonomous_actions_enabled", "AUTONOMOUS_ACTIONS_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("network_tool_enabled", "NETWORK_TOOL_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("model_provider_call_enabled", "MODEL_PROVIDER_CALL_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
