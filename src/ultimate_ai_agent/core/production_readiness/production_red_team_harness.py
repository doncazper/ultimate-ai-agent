from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.deployment_mode_matrix import (
    DeploymentModeMatrixRecord,
    validate_deployment_mode_matrix_record,
)


PRODUCTION_RED_TEAM_HARNESS_DOCS = [
    "docs/production/PRODUCTION_RED_TEAM_HARNESS.md",
    "docs/production/PRODUCTION_RED_TEAM_HARNESS_BOUNDARY.md",
    "docs/production/PRODUCTION_RED_TEAM_HARNESS_RECEIPT_PLAN.md",
    "docs/production/PRODUCTION_RED_TEAM_HARNESS_NON_GOALS.md",
    "docs/production/M119_TO_M120_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ProductionRedTeamHarnessStatus(str, Enum):
    production_red_team_harness = "production_red_team_harness"


class _ProductionRedTeamHarness(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ProductionRedTeamHarnessPolicy(_ProductionRedTeamHarness):
    policy_ref: str = "production-red-team-harness-policy:m119"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_deployment_mode_matrix_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    deployment_mode_binding_required: bool = True
    environment_binding_required: bool = True
    authority_tier_binding_required: bool = True
    red_team_scenario_binding_required: bool = True
    abuse_case_binding_required: bool = True
    threat_model_binding_required: bool = True
    safety_control_binding_required: bool = True
    mitigation_plan_binding_required: bool = True
    red_team_scenario_refs_required: bool = True
    abuse_case_refs_required: bool = True
    threat_model_refs_required: bool = True
    safety_control_refs_required: bool = True
    mitigation_plan_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    red_team_execution_enabled: bool = False
    attack_automation_enabled: bool = False
    external_probe_enabled: bool = False
    exploit_generation_enabled: bool = False
    security_scan_runtime_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    account_action_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class ProductionRedTeamHarnessRecord(_ProductionRedTeamHarness):
    production_red_team_harness_ref: str
    source_record: DeploymentModeMatrixRecord
    source_deployment_mode_matrix_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    deployment_mode_refs: list[str]
    environment_refs: list[str]
    authority_tier_refs: list[str]
    red_team_scenario_refs: list[str]
    abuse_case_refs: list[str]
    threat_model_refs: list[str]
    safety_control_refs: list[str]
    mitigation_plan_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: ProductionRedTeamHarnessStatus = (
        ProductionRedTeamHarnessStatus.production_red_team_harness
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_deployment_mode_matrix_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    deployment_mode_bound: bool = True
    environment_bound: bool = True
    authority_tier_bound: bool = True
    red_team_scenario_bound: bool = True
    abuse_case_bound: bool = True
    threat_model_bound: bool = True
    safety_control_bound: bool = True
    mitigation_plan_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    red_team_execution_enabled: bool = False
    attack_automation_enabled: bool = False
    external_probe_enabled: bool = False
    exploit_generation_enabled: bool = False
    security_scan_runtime_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    account_action_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.production_red_team_harness_ref, "production_red_team_harness_ref"),
            (
                self.source_deployment_mode_matrix_ref,
                "source_deployment_mode_matrix_ref",
            ),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.deployment_mode_refs:
            _validate_m61_ref(ref, "deployment_mode_ref")
        for ref in self.environment_refs:
            _validate_m61_ref(ref, "environment_ref")
        for ref in self.authority_tier_refs:
            _validate_m61_ref(ref, "authority_tier_ref")
        for ref in self.red_team_scenario_refs:
            _validate_m61_ref(ref, "red_team_scenario_ref")
        for ref in self.abuse_case_refs:
            _validate_m61_ref(ref, "abuse_case_ref")
        for ref in self.threat_model_refs:
            _validate_m61_ref(ref, "threat_model_ref")
        for ref in self.safety_control_refs:
            _validate_m61_ref(ref, "safety_control_ref")
        for ref in self.mitigation_plan_refs:
            _validate_m61_ref(ref, "mitigation_plan_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_production_red_team_harness_record(
    *,
    source_record: DeploymentModeMatrixRecord,
    policy: ProductionRedTeamHarnessPolicy | None = None,
) -> ProductionRedTeamHarnessRecord:
    active_policy = validate_production_red_team_harness_policy(
        policy or ProductionRedTeamHarnessPolicy()
    )
    validated_source = _validate_source_deployment_mode_matrix_record(
        _coerce_source_deployment_mode_matrix_record(source_record)
    )
    record = ProductionRedTeamHarnessRecord(
        production_red_team_harness_ref="production-red-team-harness:m119",
        source_record=validated_source,
        source_deployment_mode_matrix_ref=validated_source.deployment_mode_matrix_ref,
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        deployment_mode_refs=validated_source.deployment_mode_refs,
        environment_refs=validated_source.environment_refs,
        authority_tier_refs=validated_source.authority_tier_refs,
        red_team_scenario_refs=[
            "red-team-scenario-ref:m119:authority-boundary-review",
            "red-team-scenario-ref:m119:credential-boundary-review",
            "red-team-scenario-ref:m119:connector-abuse-review",
        ],
        abuse_case_refs=[
            "abuse-case-ref:m119:approval-replay",
            "abuse-case-ref:m119:credential-exfiltration-attempt",
            "abuse-case-ref:m119:production-authority-escalation",
        ],
        threat_model_refs=[
            "threat-model-ref:m119:m111-production-threat-model",
            "threat-model-ref:m119:m118-deployment-mode-matrix",
        ],
        safety_control_refs=[
            "safety-control-ref:m119:no-execution",
            "safety-control-ref:m119:no-external-probing",
            "safety-control-ref:m119:no-credential-handling",
        ],
        mitigation_plan_refs=[
            "mitigation-plan-ref:m119:authority-boundary-hardening",
            "mitigation-plan-ref:m119:connector-boundary-hardening",
        ],
        audit_ref="audit-ref:m119:production-red-team-harness",
        replay_ref="replay-ref:m119:production-red-team-harness",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m118",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m119:production-red-team-harness:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_deployment_mode_matrix_bound=(
            active_policy.source_deployment_mode_matrix_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        deployment_mode_bound=active_policy.deployment_mode_binding_required,
        environment_bound=active_policy.environment_binding_required,
        authority_tier_bound=active_policy.authority_tier_binding_required,
        red_team_scenario_bound=active_policy.red_team_scenario_binding_required,
        abuse_case_bound=active_policy.abuse_case_binding_required,
        threat_model_bound=active_policy.threat_model_binding_required,
        safety_control_bound=active_policy.safety_control_binding_required,
        mitigation_plan_bound=active_policy.mitigation_plan_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M119_PRODUCTION_RED_TEAM_HARNESS",
            "M119_CONTRACT_ONLY",
            "M119_REVIEW_ONLY",
            "M119_NO_RED_TEAM_EXECUTION_OR_SCANNER_RUNTIME",
            "M120_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M119 records a contract-only and review-only production "
            "red-team harness using safe refs for scenarios, abuse cases, "
            "threat models, safety controls, mitigation plans, audit, replay, "
            "and a no-effect receipt plan. It runs no red-team execution, "
            "starts no scanner runtime, performs no external probing, "
            "generates no exploit details, handles no credentials, adds no "
            "routes, adds no controls, adds no dependencies, and keeps M120 "
            "future."
        ),
    )
    return validate_production_red_team_harness_record(record)


def validate_production_red_team_harness_policy(
    policy: ProductionRedTeamHarnessPolicy,
) -> ProductionRedTeamHarnessPolicy:
    validated = ProductionRedTeamHarnessPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M119_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M119_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m119_metadata(validated.metadata)
    return validated


def validate_production_red_team_harness_record(
    record: ProductionRedTeamHarnessRecord,
) -> ProductionRedTeamHarnessRecord:
    payload = _model_payload(record)
    for field_name, reason in _M119_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, ProductionRedTeamHarnessRecord):
        raise ValueError("SECRET_LIKE_M119_PRODUCTION_RED_TEAM_HARNESS_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M119_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("red_team_scenario_refs", "M119_RED_TEAM_SCENARIO_REF_REQUIRED"),
        ("abuse_case_refs", "M119_ABUSE_CASE_REF_REQUIRED"),
        ("threat_model_refs", "M119_THREAT_MODEL_REF_REQUIRED"),
        ("safety_control_refs", "M119_SAFETY_CONTROL_REF_REQUIRED"),
        ("mitigation_plan_refs", "M119_MITIGATION_PLAN_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_deployment_mode_matrix_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_deployment_mode_matrix_record(source_record)
    validated = ProductionRedTeamHarnessRecord.model_validate(payload)
    for field_name, reason in _M119_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != ProductionRedTeamHarnessStatus.production_red_team_harness:
        raise ValueError("M119_PRODUCTION_RED_TEAM_HARNESS_STATUS_REQUIRED")
    for field_name, reason in _M119_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m119_bindings(validated, validated_source)
    _validate_m119_metadata(validated.metadata)
    return validated


def _coerce_source_deployment_mode_matrix_record(
    value: Any,
) -> DeploymentModeMatrixRecord:
    if isinstance(value, DeploymentModeMatrixRecord):
        return value
    if isinstance(value, dict):
        return DeploymentModeMatrixRecord.model_validate(value)
    raise ValueError("M119_SOURCE_RECORD_REQUIRED")


def _validate_source_deployment_mode_matrix_record(
    source_record: DeploymentModeMatrixRecord,
) -> DeploymentModeMatrixRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M119_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_deployment_mode_matrix_record(source_record)


def _validate_m119_bindings(
    record: ProductionRedTeamHarnessRecord,
    source_record: DeploymentModeMatrixRecord,
) -> None:
    if record.source_deployment_mode_matrix_ref != source_record.deployment_mode_matrix_ref:
        raise ValueError("M119_SOURCE_DEPLOYMENT_MODE_MATRIX_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M119_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M119_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M119_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M119_WORKSPACE_BINDING_MISMATCH")
    if record.deployment_mode_refs != source_record.deployment_mode_refs:
        raise ValueError("M119_DEPLOYMENT_MODE_BINDING_MISMATCH")
    if record.environment_refs != source_record.environment_refs:
        raise ValueError("M119_ENVIRONMENT_BINDING_MISMATCH")
    if record.authority_tier_refs != source_record.authority_tier_refs:
        raise ValueError("M119_AUTHORITY_TIER_BINDING_MISMATCH")
    if record.production_red_team_harness_ref != "production-red-team-harness:m119":
        raise ValueError("M119_PRODUCTION_RED_TEAM_HARNESS_REF_REQUIRED")
    for ref in record.red_team_scenario_refs:
        if not ref.startswith("red-team-scenario-ref:"):
            raise ValueError("M119_RED_TEAM_SCENARIO_REF_REQUIRED")
    for ref in record.abuse_case_refs:
        if not ref.startswith("abuse-case-ref:"):
            raise ValueError("M119_ABUSE_CASE_REF_REQUIRED")
    for ref in record.threat_model_refs:
        if not ref.startswith("threat-model-ref:"):
            raise ValueError("M119_THREAT_MODEL_REF_REQUIRED")
    for ref in record.safety_control_refs:
        if not ref.startswith("safety-control-ref:"):
            raise ValueError("M119_SAFETY_CONTROL_REF_REQUIRED")
    for ref in record.mitigation_plan_refs:
        if not ref.startswith("mitigation-plan-ref:"):
            raise ValueError("M119_MITIGATION_PLAN_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M119_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m118" not in record.accepted_checkpoint_refs:
        raise ValueError("M119_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M119_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m119_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError(
            "SECRET_LIKE_M119_PRODUCTION_RED_TEAM_HARNESS_CONTENT_DENIED"
        ) from exc


_M119_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M119_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M119_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M119_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M119_BASELINE_BINDING_REQUIRED"),
    (
        "source_deployment_mode_matrix_binding_required",
        "M119_SOURCE_DEPLOYMENT_MODE_MATRIX_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M119_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M119_WORKSPACE_BINDING_REQUIRED"),
    ("deployment_mode_binding_required", "M119_DEPLOYMENT_MODE_BINDING_REQUIRED"),
    ("environment_binding_required", "M119_ENVIRONMENT_BINDING_REQUIRED"),
    ("authority_tier_binding_required", "M119_AUTHORITY_TIER_BINDING_REQUIRED"),
    (
        "red_team_scenario_binding_required",
        "M119_RED_TEAM_SCENARIO_BINDING_REQUIRED",
    ),
    ("abuse_case_binding_required", "M119_ABUSE_CASE_BINDING_REQUIRED"),
    ("threat_model_binding_required", "M119_THREAT_MODEL_BINDING_REQUIRED"),
    ("safety_control_binding_required", "M119_SAFETY_CONTROL_BINDING_REQUIRED"),
    ("mitigation_plan_binding_required", "M119_MITIGATION_PLAN_BINDING_REQUIRED"),
    ("red_team_scenario_refs_required", "M119_RED_TEAM_SCENARIO_REF_REQUIRED"),
    ("abuse_case_refs_required", "M119_ABUSE_CASE_REF_REQUIRED"),
    ("threat_model_refs_required", "M119_THREAT_MODEL_REF_REQUIRED"),
    ("safety_control_refs_required", "M119_SAFETY_CONTROL_REF_REQUIRED"),
    ("mitigation_plan_refs_required", "M119_MITIGATION_PLAN_REF_REQUIRED"),
    ("audit_required", "M119_AUDIT_REQUIRED"),
    ("replay_required", "M119_REPLAY_REQUIRED"),
]

_M119_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("red_team_execution_enabled", "RED_TEAM_EXECUTION_DENIED"),
    ("attack_automation_enabled", "ATTACK_AUTOMATION_DENIED"),
    ("external_probe_enabled", "EXTERNAL_PROBE_DENIED"),
    ("exploit_generation_enabled", "EXPLOIT_GENERATION_DENIED"),
    ("security_scan_runtime_enabled", "SECURITY_SCAN_RUNTIME_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M119_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M119_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M119_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M119_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M119_BASELINE_BINDING_REQUIRED"),
    (
        "source_deployment_mode_matrix_bound",
        "M119_SOURCE_DEPLOYMENT_MODE_MATRIX_BINDING_REQUIRED",
    ),
    ("user_bound", "M119_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M119_WORKSPACE_BINDING_REQUIRED"),
    ("deployment_mode_bound", "M119_DEPLOYMENT_MODE_BINDING_REQUIRED"),
    ("environment_bound", "M119_ENVIRONMENT_BINDING_REQUIRED"),
    ("authority_tier_bound", "M119_AUTHORITY_TIER_BINDING_REQUIRED"),
    ("red_team_scenario_bound", "M119_RED_TEAM_SCENARIO_BINDING_REQUIRED"),
    ("abuse_case_bound", "M119_ABUSE_CASE_BINDING_REQUIRED"),
    ("threat_model_bound", "M119_THREAT_MODEL_BINDING_REQUIRED"),
    ("safety_control_bound", "M119_SAFETY_CONTROL_BINDING_REQUIRED"),
    ("mitigation_plan_bound", "M119_MITIGATION_PLAN_BINDING_REQUIRED"),
    ("audit_required", "M119_AUDIT_REQUIRED"),
    ("replay_safe", "M119_REPLAY_REQUIRED"),
]

_M119_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("red_team_execution_enabled", "RED_TEAM_EXECUTION_DENIED"),
    ("attack_automation_enabled", "ATTACK_AUTOMATION_DENIED"),
    ("external_probe_enabled", "EXTERNAL_PROBE_DENIED"),
    ("exploit_generation_enabled", "EXPLOIT_GENERATION_DENIED"),
    ("security_scan_runtime_enabled", "SECURITY_SCAN_RUNTIME_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M119_SOURCE_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("deployment_runtime_enabled", "RED_TEAM_EXECUTION_DENIED"),
    ("deployment_execution_enabled", "RED_TEAM_EXECUTION_DENIED"),
    ("release_automation_enabled", "RED_TEAM_EXECUTION_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_PROBE_DENIED"),
    ("infrastructure_provisioning_enabled", "EXTERNAL_PROBE_DENIED"),
    ("ci_cd_execution_enabled", "SECURITY_SCAN_RUNTIME_DENIED"),
    ("signing_or_notarization_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("remote_agent_runtime_enabled", "RED_TEAM_EXECUTION_DENIED"),
    ("remote_dispatch_enabled", "RED_TEAM_EXECUTION_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]
