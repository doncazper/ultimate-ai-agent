from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.remote_agent_coordination import (
    RemoteAgentCoordinationContractRecord,
    validate_remote_agent_coordination_contract_record,
)


DEPLOYMENT_MODE_MATRIX_DOCS = [
    "docs/production/DEPLOYMENT_MODE_MATRIX.md",
    "docs/production/DEPLOYMENT_MODE_MATRIX_BOUNDARY.md",
    "docs/production/DEPLOYMENT_MODE_MATRIX_RECEIPT_PLAN.md",
    "docs/production/DEPLOYMENT_MODE_MATRIX_NON_GOALS.md",
    "docs/production/M118_TO_M119_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class DeploymentModeMatrixStatus(str, Enum):
    deployment_mode_matrix = "deployment_mode_matrix"


class _DeploymentModeMatrix(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class DeploymentModeMatrixPolicy(_DeploymentModeMatrix):
    policy_ref: str = "deployment-mode-matrix-policy:m118"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_remote_agent_coordination_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    deployment_mode_binding_required: bool = True
    environment_binding_required: bool = True
    authority_tier_binding_required: bool = True
    rollout_stage_binding_required: bool = True
    rollback_boundary_binding_required: bool = True
    deployment_mode_refs_required: bool = True
    environment_refs_required: bool = True
    authority_tier_refs_required: bool = True
    rollout_stage_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    deployment_runtime_enabled: bool = False
    deployment_execution_enabled: bool = False
    release_automation_enabled: bool = False
    external_distribution_enabled: bool = False
    infrastructure_provisioning_enabled: bool = False
    ci_cd_execution_enabled: bool = False
    signing_or_notarization_enabled: bool = False
    remote_agent_runtime_enabled: bool = False
    remote_dispatch_enabled: bool = False
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
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class DeploymentModeMatrixRecord(_DeploymentModeMatrix):
    deployment_mode_matrix_ref: str
    source_record: RemoteAgentCoordinationContractRecord
    source_remote_agent_coordination_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    deployment_mode_refs: list[str]
    environment_refs: list[str]
    authority_tier_refs: list[str]
    rollout_stage_refs: list[str]
    rollback_boundary_ref: str
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: DeploymentModeMatrixStatus = DeploymentModeMatrixStatus.deployment_mode_matrix
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_remote_agent_coordination_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    deployment_mode_bound: bool = True
    environment_bound: bool = True
    authority_tier_bound: bool = True
    rollout_stage_bound: bool = True
    rollback_boundary_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    deployment_runtime_enabled: bool = False
    deployment_execution_enabled: bool = False
    release_automation_enabled: bool = False
    external_distribution_enabled: bool = False
    infrastructure_provisioning_enabled: bool = False
    ci_cd_execution_enabled: bool = False
    signing_or_notarization_enabled: bool = False
    remote_agent_runtime_enabled: bool = False
    remote_dispatch_enabled: bool = False
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
    def validate_shape(self):
        for value, field_name in [
            (self.deployment_mode_matrix_ref, "deployment_mode_matrix_ref"),
            (
                self.source_remote_agent_coordination_ref,
                "source_remote_agent_coordination_ref",
            ),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.rollback_boundary_ref, "rollback_boundary_ref"),
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
        for ref in self.rollout_stage_refs:
            _validate_m61_ref(ref, "rollout_stage_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_deployment_mode_matrix_record(
    *,
    source_record: RemoteAgentCoordinationContractRecord,
    policy: DeploymentModeMatrixPolicy | None = None,
) -> DeploymentModeMatrixRecord:
    active_policy = validate_deployment_mode_matrix_policy(
        policy or DeploymentModeMatrixPolicy()
    )
    validated_source = _validate_source_remote_agent_coordination_record(
        _coerce_source_remote_agent_coordination_record(source_record)
    )
    record = DeploymentModeMatrixRecord(
        deployment_mode_matrix_ref="deployment-mode-matrix:m118",
        source_record=validated_source,
        source_remote_agent_coordination_ref=(
            validated_source.remote_coordination_contract_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        deployment_mode_refs=[
            "deployment-mode-ref:m118:local-dev",
            "deployment-mode-ref:m118:internal-alpha",
            "deployment-mode-ref:m118:future-beta-candidate",
        ],
        environment_refs=[
            "environment-ref:m118:local-only",
            "environment-ref:m118:internal-review-only",
        ],
        authority_tier_refs=[
            "authority-tier-ref:m118:no-production-authority",
            "authority-tier-ref:m118:review-only",
        ],
        rollout_stage_refs=[
            "rollout-stage-ref:m118:pre-alpha-checkpoint",
            "rollout-stage-ref:m118:no-release-automation",
        ],
        rollback_boundary_ref="rollback-boundary-ref:m118:planning-only",
        audit_ref="audit-ref:m118:deployment-mode-matrix",
        replay_ref="replay-ref:m118:deployment-mode-matrix",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m117",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m118:deployment-mode-matrix:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_remote_agent_coordination_bound=(
            active_policy.source_remote_agent_coordination_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        deployment_mode_bound=active_policy.deployment_mode_binding_required,
        environment_bound=active_policy.environment_binding_required,
        authority_tier_bound=active_policy.authority_tier_binding_required,
        rollout_stage_bound=active_policy.rollout_stage_binding_required,
        rollback_boundary_bound=active_policy.rollback_boundary_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M118_DEPLOYMENT_MODE_MATRIX",
            "M118_CONTRACT_ONLY",
            "M118_REVIEW_ONLY",
            "M118_NO_DEPLOYMENT_RUNTIME_OR_RELEASE_AUTOMATION",
            "M119_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M118 records a contract-only and review-only deployment mode "
            "matrix using safe refs for deployment modes, environments, "
            "authority tiers, rollout stages, rollback boundary, audit, replay, "
            "and a no-effect receipt plan. It starts no deployment runtime, "
            "runs no release automation, performs no external distribution, "
            "provisions no infrastructure, executes no CI or CD workflow, uses "
            "no signing flow, handles no credentials, adds no routes, adds no "
            "controls, adds no dependencies, and keeps M119 future."
        ),
    )
    return validate_deployment_mode_matrix_record(record)


def validate_deployment_mode_matrix_policy(
    policy: DeploymentModeMatrixPolicy,
) -> DeploymentModeMatrixPolicy:
    validated = DeploymentModeMatrixPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M118_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M118_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m118_metadata(validated.metadata)
    return validated


def validate_deployment_mode_matrix_record(
    record: DeploymentModeMatrixRecord,
) -> DeploymentModeMatrixRecord:
    payload = _model_payload(record)
    for field_name, reason in _M118_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, DeploymentModeMatrixRecord):
        raise ValueError("SECRET_LIKE_M118_DEPLOYMENT_MODE_MATRIX_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M118_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("deployment_mode_refs", "M118_DEPLOYMENT_MODE_REF_REQUIRED"),
        ("environment_refs", "M118_ENVIRONMENT_REF_REQUIRED"),
        ("authority_tier_refs", "M118_AUTHORITY_TIER_REF_REQUIRED"),
        ("rollout_stage_refs", "M118_ROLLOUT_STAGE_REF_REQUIRED"),
        ("rollback_boundary_ref", "M118_ROLLBACK_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_remote_agent_coordination_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_remote_agent_coordination_record(source_record)
    validated = DeploymentModeMatrixRecord.model_validate(payload)
    for field_name, reason in _M118_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != DeploymentModeMatrixStatus.deployment_mode_matrix:
        raise ValueError("M118_DEPLOYMENT_MODE_MATRIX_STATUS_REQUIRED")
    for field_name, reason in _M118_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m118_bindings(validated, validated_source)
    _validate_m118_metadata(validated.metadata)
    return validated


def _coerce_source_remote_agent_coordination_record(
    value: Any,
) -> RemoteAgentCoordinationContractRecord:
    if isinstance(value, RemoteAgentCoordinationContractRecord):
        return value
    if isinstance(value, dict):
        return RemoteAgentCoordinationContractRecord.model_validate(value)
    raise ValueError("M118_SOURCE_RECORD_REQUIRED")


def _validate_source_remote_agent_coordination_record(
    source_record: RemoteAgentCoordinationContractRecord,
) -> RemoteAgentCoordinationContractRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M118_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_remote_agent_coordination_contract_record(source_record)


def _validate_m118_bindings(
    record: DeploymentModeMatrixRecord,
    source_record: RemoteAgentCoordinationContractRecord,
) -> None:
    if (
        record.source_remote_agent_coordination_ref
        != source_record.remote_coordination_contract_ref
    ):
        raise ValueError("M118_SOURCE_REMOTE_AGENT_COORDINATION_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M118_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M118_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M118_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M118_WORKSPACE_BINDING_MISMATCH")
    if record.deployment_mode_matrix_ref != "deployment-mode-matrix:m118":
        raise ValueError("M118_DEPLOYMENT_MODE_MATRIX_REF_REQUIRED")
    for ref in record.deployment_mode_refs:
        if not ref.startswith("deployment-mode-ref:"):
            raise ValueError("M118_DEPLOYMENT_MODE_REF_REQUIRED")
    for ref in record.environment_refs:
        if not ref.startswith("environment-ref:"):
            raise ValueError("M118_ENVIRONMENT_REF_REQUIRED")
    for ref in record.authority_tier_refs:
        if not ref.startswith("authority-tier-ref:"):
            raise ValueError("M118_AUTHORITY_TIER_REF_REQUIRED")
    for ref in record.rollout_stage_refs:
        if not ref.startswith("rollout-stage-ref:"):
            raise ValueError("M118_ROLLOUT_STAGE_REF_REQUIRED")
    if not record.rollback_boundary_ref.startswith("rollback-boundary-ref:"):
        raise ValueError("M118_ROLLBACK_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M118_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m117" not in record.accepted_checkpoint_refs:
        raise ValueError("M118_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M118_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m118_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError(
            "SECRET_LIKE_M118_DEPLOYMENT_MODE_MATRIX_CONTENT_DENIED"
        ) from exc


_M118_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M118_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M118_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M118_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M118_BASELINE_BINDING_REQUIRED"),
    (
        "source_remote_agent_coordination_binding_required",
        "M118_SOURCE_REMOTE_AGENT_COORDINATION_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M118_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M118_WORKSPACE_BINDING_REQUIRED"),
    ("deployment_mode_binding_required", "M118_DEPLOYMENT_MODE_BINDING_REQUIRED"),
    ("environment_binding_required", "M118_ENVIRONMENT_BINDING_REQUIRED"),
    ("authority_tier_binding_required", "M118_AUTHORITY_TIER_BINDING_REQUIRED"),
    ("rollout_stage_binding_required", "M118_ROLLOUT_STAGE_BINDING_REQUIRED"),
    ("rollback_boundary_binding_required", "M118_ROLLBACK_BOUNDARY_BINDING_REQUIRED"),
    ("deployment_mode_refs_required", "M118_DEPLOYMENT_MODE_REF_REQUIRED"),
    ("environment_refs_required", "M118_ENVIRONMENT_REF_REQUIRED"),
    ("authority_tier_refs_required", "M118_AUTHORITY_TIER_REF_REQUIRED"),
    ("rollout_stage_refs_required", "M118_ROLLOUT_STAGE_REF_REQUIRED"),
    ("audit_required", "M118_AUDIT_REQUIRED"),
    ("replay_required", "M118_REPLAY_REQUIRED"),
]

_M118_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("deployment_runtime_enabled", "DEPLOYMENT_RUNTIME_DENIED"),
    ("deployment_execution_enabled", "DEPLOYMENT_EXECUTION_DENIED"),
    ("release_automation_enabled", "RELEASE_AUTOMATION_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("infrastructure_provisioning_enabled", "INFRASTRUCTURE_PROVISIONING_DENIED"),
    ("ci_cd_execution_enabled", "CI_CD_EXECUTION_DENIED"),
    ("signing_or_notarization_enabled", "SIGNING_OR_NOTARIZATION_DENIED"),
    ("remote_agent_runtime_enabled", "REMOTE_AGENT_RUNTIME_DENIED"),
    ("remote_dispatch_enabled", "REMOTE_DISPATCH_DENIED"),
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

_M118_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M118_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M118_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M118_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M118_BASELINE_BINDING_REQUIRED"),
    (
        "source_remote_agent_coordination_bound",
        "M118_SOURCE_REMOTE_AGENT_COORDINATION_BINDING_REQUIRED",
    ),
    ("user_bound", "M118_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M118_WORKSPACE_BINDING_REQUIRED"),
    ("deployment_mode_bound", "M118_DEPLOYMENT_MODE_BINDING_REQUIRED"),
    ("environment_bound", "M118_ENVIRONMENT_BINDING_REQUIRED"),
    ("authority_tier_bound", "M118_AUTHORITY_TIER_BINDING_REQUIRED"),
    ("rollout_stage_bound", "M118_ROLLOUT_STAGE_BINDING_REQUIRED"),
    ("rollback_boundary_bound", "M118_ROLLBACK_BOUNDARY_BINDING_REQUIRED"),
    ("audit_required", "M118_AUDIT_REQUIRED"),
    ("replay_safe", "M118_REPLAY_REQUIRED"),
]

_M118_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("deployment_runtime_enabled", "DEPLOYMENT_RUNTIME_DENIED"),
    ("deployment_execution_enabled", "DEPLOYMENT_EXECUTION_DENIED"),
    ("release_automation_enabled", "RELEASE_AUTOMATION_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("infrastructure_provisioning_enabled", "INFRASTRUCTURE_PROVISIONING_DENIED"),
    ("ci_cd_execution_enabled", "CI_CD_EXECUTION_DENIED"),
    ("signing_or_notarization_enabled", "SIGNING_OR_NOTARIZATION_DENIED"),
    ("remote_agent_runtime_enabled", "REMOTE_AGENT_RUNTIME_DENIED"),
    ("remote_dispatch_enabled", "REMOTE_DISPATCH_DENIED"),
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

_M118_SOURCE_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("remote_agent_runtime_enabled", "REMOTE_AGENT_RUNTIME_DENIED"),
    ("remote_dispatch_enabled", "REMOTE_DISPATCH_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("live_connection_enabled", "LIVE_CONNECTION_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("agent_spawn_enabled", "AGENT_SPAWN_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
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
