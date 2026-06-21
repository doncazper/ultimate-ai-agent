from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.production_threat_model import (
    ProductionThreatModelRecord,
    validate_production_threat_model_record,
)


USER_WORKSPACE_IDENTITY_DOCS = [
    "docs/production/USER_WORKSPACE_IDENTITY_MODEL.md",
    "docs/production/USER_WORKSPACE_IDENTITY_POLICY.md",
    "docs/production/USER_WORKSPACE_IDENTITY_AUTHORITY_BOUNDARY.md",
    "docs/production/USER_WORKSPACE_IDENTITY_RECEIPT_PLAN.md",
    "docs/production/USER_WORKSPACE_IDENTITY_NON_GOALS.md",
    "docs/production/M112_TO_M113_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class UserWorkspaceIdentityStatus(str, Enum):
    identity_model_contract = "identity_model_contract"


class _UserWorkspaceIdentityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class UserWorkspaceIdentityPolicy(_UserWorkspaceIdentityModel):
    policy_ref: str = "user-workspace-identity-policy:m112"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_threat_model_binding_required: bool = True
    user_ref_required: bool = True
    workspace_ref_required: bool = True
    identity_boundary_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_enabled: bool = False
    persistent_identity_store_enabled: bool = False
    account_connector_enabled: bool = False
    network_access_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    background_worker_enabled: bool = False
    remote_execution_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class UserWorkspaceIdentityRecord(_UserWorkspaceIdentityModel):
    identity_model_ref: str
    source_record: ProductionThreatModelRecord
    source_threat_model_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    identity_boundary_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: UserWorkspaceIdentityStatus = (
        UserWorkspaceIdentityStatus.identity_model_contract
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_threat_model_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_enabled: bool = False
    persistent_identity_store_enabled: bool = False
    account_connector_enabled: bool = False
    network_access_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_automation_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    background_worker_enabled: bool = False
    remote_execution_enabled: bool = False
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
            (self.identity_model_ref, "identity_model_ref"),
            (self.source_threat_model_ref, "source_threat_model_ref"),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.identity_boundary_refs:
            _validate_m61_ref(ref, "identity_boundary_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_user_workspace_identity_record(
    *,
    source_record: ProductionThreatModelRecord,
    policy: UserWorkspaceIdentityPolicy | None = None,
) -> UserWorkspaceIdentityRecord:
    active_policy = validate_user_workspace_identity_policy(
        policy or UserWorkspaceIdentityPolicy()
    )
    validated_source = _validate_source_threat_model_record(source_record)
    record = UserWorkspaceIdentityRecord(
        identity_model_ref="user-workspace-identity:m112",
        source_record=validated_source,
        source_threat_model_ref=validated_source.threat_model_ref,
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref="user-ref:m112:primary-safe-user",
        workspace_ref="workspace-ref:m112:primary-safe-workspace",
        identity_boundary_refs=[
            "identity-boundary-ref:m112:user-is-not-authority",
            "identity-boundary-ref:m112:workspace-is-not-root",
            "identity-boundary-ref:m112:no-auth-runtime",
        ],
        audit_ref="audit-ref:m112:user-workspace-identity",
        replay_ref="replay-ref:m112:user-workspace-identity",
        accepted_checkpoint_refs=[
            "checkpoint:m101",
            "checkpoint:m102",
            "checkpoint:m103",
            "checkpoint:m104",
            "checkpoint:m105",
            "checkpoint:m106",
            "checkpoint:m107",
            "checkpoint:m108",
            "checkpoint:m109",
            "checkpoint:m110",
            "checkpoint:m111",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m112:user-workspace-identity:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_threat_model_bound=(
            active_policy.source_threat_model_binding_required
        ),
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M112_USER_WORKSPACE_IDENTITY_MODEL",
            "M112_CONTRACT_ONLY",
            "M112_REVIEW_ONLY",
            "M112_NO_AUTH_RUNTIME",
            "M113_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M112 records a contract-only and review-only user/workspace "
            "identity model using safe user refs, safe workspace refs, identity "
            "boundary refs, audit refs, replay refs, and a no-effect receipt "
            "plan. It grants no production authority, enables no production "
            "runtime, starts no auth runtime, creates no login flow, creates no "
            "session store, handles no credentials, persists no identity store, "
            "connects no accounts, accesses no network, calls no models, writes "
            "no memory, injects no context, executes nothing, adds no routes, "
            "adds no controls, adds no dependencies, and keeps M113 future."
        ),
    )
    return validate_user_workspace_identity_record(record)


def validate_user_workspace_identity_policy(
    policy: UserWorkspaceIdentityPolicy,
) -> UserWorkspaceIdentityPolicy:
    validated = UserWorkspaceIdentityPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M112_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M112_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m112_metadata(validated.metadata)
    return validated


def validate_user_workspace_identity_record(
    record: UserWorkspaceIdentityRecord,
) -> UserWorkspaceIdentityRecord:
    payload = _model_payload(record)
    for field_name, reason in _M112_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, UserWorkspaceIdentityRecord):
        raise ValueError("SECRET_LIKE_M112_USER_WORKSPACE_IDENTITY_CONTENT_DENIED")
    if not payload.get("accepted_checkpoint_refs"):
        raise ValueError("M112_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    if not payload.get("user_ref"):
        raise ValueError("M112_USER_REF_REQUIRED")
    if not payload.get("workspace_ref"):
        raise ValueError("M112_WORKSPACE_REF_REQUIRED")
    if not payload.get("identity_boundary_refs"):
        raise ValueError("M112_IDENTITY_BOUNDARY_REF_REQUIRED")
    source_record = _coerce_source_threat_model_record(payload.get("source_record"))
    validated_source = _validate_source_threat_model_record(source_record)
    validated = UserWorkspaceIdentityRecord.model_validate(payload)
    for field_name, reason in _M112_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != UserWorkspaceIdentityStatus.identity_model_contract:
        raise ValueError("M112_IDENTITY_MODEL_STATUS_REQUIRED")
    if not validated.accepted_checkpoint_refs:
        raise ValueError("M112_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    if not validated.user_ref:
        raise ValueError("M112_USER_REF_REQUIRED")
    if not validated.workspace_ref:
        raise ValueError("M112_WORKSPACE_REF_REQUIRED")
    if not validated.identity_boundary_refs:
        raise ValueError("M112_IDENTITY_BOUNDARY_REF_REQUIRED")
    for field_name, reason in _M112_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m112_bindings(validated, validated_source)
    _validate_m112_metadata(validated.metadata)
    return validated


def _coerce_source_threat_model_record(value: Any) -> ProductionThreatModelRecord:
    if isinstance(value, ProductionThreatModelRecord):
        return value
    if isinstance(value, dict):
        return ProductionThreatModelRecord.model_validate(value)
    raise ValueError("M112_SOURCE_THREAT_MODEL_RECORD_REQUIRED")


def _validate_source_threat_model_record(
    source_record: ProductionThreatModelRecord,
) -> ProductionThreatModelRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M112_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_production_threat_model_record(source_record)


def _validate_m112_bindings(
    record: UserWorkspaceIdentityRecord,
    source_record: ProductionThreatModelRecord,
) -> None:
    if record.source_threat_model_ref != source_record.threat_model_ref:
        raise ValueError("M112_SOURCE_THREAT_MODEL_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M112_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M112_ACTOR_BINDING_MISMATCH")
    if record.identity_model_ref != "user-workspace-identity:m112":
        raise ValueError("M112_IDENTITY_MODEL_REF_REQUIRED")
    if not record.user_ref.startswith("user-ref:"):
        raise ValueError("M112_USER_REF_REQUIRED")
    if not record.workspace_ref.startswith("workspace-ref:"):
        raise ValueError("M112_WORKSPACE_REF_REQUIRED")
    for ref in record.identity_boundary_refs:
        if not ref.startswith("identity-boundary-ref:"):
            raise ValueError("M112_IDENTITY_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M112_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M112_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m112_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError(
            "SECRET_LIKE_M112_USER_WORKSPACE_IDENTITY_CONTENT_DENIED"
        ) from exc


_M112_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M112_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M112_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M112_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M112_BASELINE_BINDING_REQUIRED"),
    (
        "source_threat_model_binding_required",
        "M112_SOURCE_THREAT_MODEL_BINDING_REQUIRED",
    ),
    ("user_ref_required", "M112_USER_REF_REQUIRED"),
    ("workspace_ref_required", "M112_WORKSPACE_REF_REQUIRED"),
    ("identity_boundary_refs_required", "M112_IDENTITY_BOUNDARY_REF_REQUIRED"),
    ("audit_required", "M112_AUDIT_REQUIRED"),
    ("replay_required", "M112_REPLAY_REQUIRED"),
]

_M112_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("persistent_identity_store_enabled", "PERSISTENT_IDENTITY_STORE_DENIED"),
    ("account_connector_enabled", "ACCOUNT_CONNECTOR_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M112_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M112_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M112_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M112_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M112_BASELINE_BINDING_REQUIRED"),
    ("source_threat_model_bound", "M112_SOURCE_THREAT_MODEL_BINDING_REQUIRED"),
    ("audit_required", "M112_AUDIT_REQUIRED"),
    ("replay_safe", "M112_REPLAY_REQUIRED"),
]

_M112_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("persistent_identity_store_enabled", "PERSISTENT_IDENTITY_STORE_DENIED"),
    ("account_connector_enabled", "ACCOUNT_CONNECTOR_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M112_SOURCE_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("deployment_enabled", "DEPLOYMENT_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_automation_enabled", "BROWSER_AUTOMATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
]
