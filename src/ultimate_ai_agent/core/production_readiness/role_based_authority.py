from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.production_audit_retention import (
    ProductionAuditRetentionPolicyRecord,
    validate_production_audit_retention_policy_record,
)


ROLE_BASED_AUTHORITY_DOCS = [
    "docs/production/ROLE_BASED_AUTHORITY_MODEL.md",
    "docs/production/ROLE_BASED_AUTHORITY_BOUNDARY.md",
    "docs/production/ROLE_BASED_AUTHORITY_RECEIPT_PLAN.md",
    "docs/production/ROLE_BASED_AUTHORITY_NON_GOALS.md",
    "docs/production/M116_TO_M117_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class RoleBasedAuthorityModelStatus(str, Enum):
    authority_model = "authority_model"


class _RoleBasedAuthorityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class RoleBasedAuthorityModelPolicy(_RoleBasedAuthorityModel):
    policy_ref: str = "role-based-authority-policy:m116"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_production_audit_retention_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    role_binding_required: bool = True
    authority_scope_binding_required: bool = True
    permission_boundary_binding_required: bool = True
    separation_of_duty_binding_required: bool = True
    role_refs_required: bool = True
    authority_scope_refs_required: bool = True
    permission_boundary_refs_required: bool = True
    separation_of_duty_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    authority_runtime_enabled: bool = False
    role_enforcement_enabled: bool = False
    permission_enforcement_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_handling_enabled: bool = False
    oauth_flow_enabled: bool = False
    token_exchange_enabled: bool = False
    credential_handling_enabled: bool = False
    account_action_enabled: bool = False
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
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class RoleBasedAuthorityModelRecord(_RoleBasedAuthorityModel):
    role_authority_model_ref: str
    source_record: ProductionAuditRetentionPolicyRecord
    source_production_audit_retention_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    role_refs: list[str]
    authority_scope_refs: list[str]
    permission_boundary_refs: list[str]
    separation_of_duty_refs: list[str]
    reviewer_role_ref: str
    operator_role_ref: str
    admin_role_ref: str
    break_glass_boundary_ref: str
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: RoleBasedAuthorityModelStatus = (
        RoleBasedAuthorityModelStatus.authority_model
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_production_audit_retention_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    role_bound: bool = True
    authority_scope_bound: bool = True
    permission_boundary_bound: bool = True
    separation_of_duty_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    authority_runtime_enabled: bool = False
    role_enforcement_enabled: bool = False
    permission_enforcement_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_handling_enabled: bool = False
    oauth_flow_enabled: bool = False
    token_exchange_enabled: bool = False
    credential_handling_enabled: bool = False
    account_action_enabled: bool = False
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
    def validate_shape(self):
        for value, field_name in [
            (self.role_authority_model_ref, "role_authority_model_ref"),
            (
                self.source_production_audit_retention_ref,
                "source_production_audit_retention_ref",
            ),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.reviewer_role_ref, "reviewer_role_ref"),
            (self.operator_role_ref, "operator_role_ref"),
            (self.admin_role_ref, "admin_role_ref"),
            (self.break_glass_boundary_ref, "break_glass_boundary_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.role_refs:
            _validate_m61_ref(ref, "role_ref")
        for ref in self.authority_scope_refs:
            _validate_m61_ref(ref, "authority_scope_ref")
        for ref in self.permission_boundary_refs:
            _validate_m61_ref(ref, "permission_boundary_ref")
        for ref in self.separation_of_duty_refs:
            _validate_m61_ref(ref, "separation_of_duty_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_role_based_authority_model_record(
    *,
    source_record: ProductionAuditRetentionPolicyRecord,
    policy: RoleBasedAuthorityModelPolicy | None = None,
) -> RoleBasedAuthorityModelRecord:
    active_policy = validate_role_based_authority_model_policy(
        policy or RoleBasedAuthorityModelPolicy()
    )
    validated_source = _validate_source_production_audit_retention_record(source_record)
    record = RoleBasedAuthorityModelRecord(
        role_authority_model_ref="role-authority-model:m116",
        source_record=validated_source,
        source_production_audit_retention_ref=(
            validated_source.audit_retention_policy_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        role_refs=[
            "role-ref:m116:reviewer",
            "role-ref:m116:operator",
            "role-ref:m116:admin-review-only",
        ],
        authority_scope_refs=[
            "authority-scope-ref:m116:review-only",
            "authority-scope-ref:m116:no-runtime-enforcement",
        ],
        permission_boundary_refs=[
            "permission-boundary-ref:m116:no-production-authority",
            "permission-boundary-ref:m116:no-account-actions",
            "permission-boundary-ref:m116:no-credential-handling",
        ],
        separation_of_duty_refs=[
            "separation-of-duty-ref:m116:reviewer-not-operator",
            "separation-of-duty-ref:m116:admin-review-only",
        ],
        reviewer_role_ref="role-ref:m116:reviewer",
        operator_role_ref="role-ref:m116:operator",
        admin_role_ref="role-ref:m116:admin-review-only",
        break_glass_boundary_ref="break-glass-boundary-ref:m116:review-only-no-runtime",
        audit_ref="audit-ref:m116:role-based-authority-model",
        replay_ref="replay-ref:m116:role-based-authority-model",
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
            "checkpoint:m112",
            "checkpoint:m113",
            "checkpoint:m114",
            "checkpoint:m115",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m116:role-based-authority-model:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_production_audit_retention_bound=(
            active_policy.source_production_audit_retention_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        role_bound=active_policy.role_binding_required,
        authority_scope_bound=active_policy.authority_scope_binding_required,
        permission_boundary_bound=active_policy.permission_boundary_binding_required,
        separation_of_duty_bound=active_policy.separation_of_duty_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M116_ROLE_BASED_AUTHORITY_MODEL",
            "M116_CONTRACT_ONLY",
            "M116_REVIEW_ONLY",
            "M116_NO_AUTHORITY_RUNTIME_OR_ENFORCEMENT",
            "M117_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M116 records a contract-only and review-only role-based "
            "authority model using safe refs, role refs, authority scope refs, "
            "permission boundary refs, separation-of-duty refs, audit refs, "
            "replay refs, and a no-effect receipt plan. It grants no "
            "production authority, starts no production runtime, starts no "
            "authority runtime, enforces no roles or permissions, starts no "
            "auth runtime, creates no login or session capability, performs no "
            "OAuth flow or token exchange, handles no credentials, performs no "
            "account actions, uses no network, calls no models, writes no "
            "memory, injects no context, executes nothing, adds no routes, "
            "adds no controls, adds no dependencies, and keeps M117 future."
        ),
    )
    return validate_role_based_authority_model_record(record)


def validate_role_based_authority_model_policy(
    policy: RoleBasedAuthorityModelPolicy,
) -> RoleBasedAuthorityModelPolicy:
    validated = RoleBasedAuthorityModelPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M116_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M116_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m116_metadata(validated.metadata)
    return validated


def validate_role_based_authority_model_record(
    record: RoleBasedAuthorityModelRecord,
) -> RoleBasedAuthorityModelRecord:
    payload = _model_payload(record)
    for field_name, reason in _M116_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, RoleBasedAuthorityModelRecord):
        raise ValueError("SECRET_LIKE_M116_ROLE_AUTHORITY_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M116_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("role_refs", "M116_ROLE_REF_REQUIRED"),
        ("authority_scope_refs", "M116_AUTHORITY_SCOPE_REF_REQUIRED"),
        ("permission_boundary_refs", "M116_PERMISSION_BOUNDARY_REF_REQUIRED"),
        ("separation_of_duty_refs", "M116_SEPARATION_OF_DUTY_REF_REQUIRED"),
        ("reviewer_role_ref", "M116_ROLE_REF_REQUIRED"),
        ("operator_role_ref", "M116_ROLE_REF_REQUIRED"),
        ("admin_role_ref", "M116_ROLE_REF_REQUIRED"),
        ("break_glass_boundary_ref", "M116_BREAK_GLASS_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_production_audit_retention_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_production_audit_retention_record(
        source_record
    )
    validated = RoleBasedAuthorityModelRecord.model_validate(payload)
    for field_name, reason in _M116_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != RoleBasedAuthorityModelStatus.authority_model:
        raise ValueError("M116_ROLE_BASED_AUTHORITY_MODEL_STATUS_REQUIRED")
    for field_name, reason in _M116_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m116_bindings(validated, validated_source)
    _validate_m116_metadata(validated.metadata)
    return validated


def _coerce_source_production_audit_retention_record(
    value: Any,
) -> ProductionAuditRetentionPolicyRecord:
    if isinstance(value, ProductionAuditRetentionPolicyRecord):
        return value
    if isinstance(value, dict):
        return ProductionAuditRetentionPolicyRecord.model_validate(value)
    raise ValueError("M116_SOURCE_PRODUCTION_AUDIT_RETENTION_RECORD_REQUIRED")


def _validate_source_production_audit_retention_record(
    source_record: ProductionAuditRetentionPolicyRecord,
) -> ProductionAuditRetentionPolicyRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M116_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_production_audit_retention_policy_record(source_record)


def _validate_m116_bindings(
    record: RoleBasedAuthorityModelRecord,
    source_record: ProductionAuditRetentionPolicyRecord,
) -> None:
    if record.source_production_audit_retention_ref != (
        source_record.audit_retention_policy_ref
    ):
        raise ValueError("M116_SOURCE_PRODUCTION_AUDIT_RETENTION_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M116_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M116_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M116_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M116_WORKSPACE_BINDING_MISMATCH")
    if record.role_authority_model_ref != "role-authority-model:m116":
        raise ValueError("M116_ROLE_AUTHORITY_MODEL_REF_REQUIRED")
    for ref in record.role_refs:
        if not ref.startswith("role-ref:"):
            raise ValueError("M116_ROLE_REF_REQUIRED")
    for ref in [
        record.reviewer_role_ref,
        record.operator_role_ref,
        record.admin_role_ref,
    ]:
        if not ref.startswith("role-ref:"):
            raise ValueError("M116_ROLE_REF_REQUIRED")
    for ref in record.authority_scope_refs:
        if not ref.startswith("authority-scope-ref:"):
            raise ValueError("M116_AUTHORITY_SCOPE_REF_REQUIRED")
    for ref in record.permission_boundary_refs:
        if not ref.startswith("permission-boundary-ref:"):
            raise ValueError("M116_PERMISSION_BOUNDARY_REF_REQUIRED")
    for ref in record.separation_of_duty_refs:
        if not ref.startswith("separation-of-duty-ref:"):
            raise ValueError("M116_SEPARATION_OF_DUTY_REF_REQUIRED")
    if not record.break_glass_boundary_ref.startswith("break-glass-boundary-ref:"):
        raise ValueError("M116_BREAK_GLASS_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M116_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M116_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m116_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M116_ROLE_AUTHORITY_CONTENT_DENIED") from exc


_M116_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M116_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M116_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M116_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M116_BASELINE_BINDING_REQUIRED"),
    (
        "source_production_audit_retention_binding_required",
        "M116_SOURCE_PRODUCTION_AUDIT_RETENTION_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M116_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M116_WORKSPACE_BINDING_REQUIRED"),
    ("role_binding_required", "M116_ROLE_BINDING_REQUIRED"),
    ("authority_scope_binding_required", "M116_AUTHORITY_SCOPE_BINDING_REQUIRED"),
    (
        "permission_boundary_binding_required",
        "M116_PERMISSION_BOUNDARY_BINDING_REQUIRED",
    ),
    (
        "separation_of_duty_binding_required",
        "M116_SEPARATION_OF_DUTY_BINDING_REQUIRED",
    ),
    ("role_refs_required", "M116_ROLE_REF_REQUIRED"),
    ("authority_scope_refs_required", "M116_AUTHORITY_SCOPE_REF_REQUIRED"),
    ("permission_boundary_refs_required", "M116_PERMISSION_BOUNDARY_REF_REQUIRED"),
    ("separation_of_duty_refs_required", "M116_SEPARATION_OF_DUTY_REF_REQUIRED"),
    ("audit_required", "M116_AUDIT_REQUIRED"),
    ("replay_required", "M116_REPLAY_REQUIRED"),
]

_M116_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("authority_runtime_enabled", "AUTHORITY_RUNTIME_DENIED"),
    ("role_enforcement_enabled", "ROLE_ENFORCEMENT_DENIED"),
    ("permission_enforcement_enabled", "PERMISSION_ENFORCEMENT_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_handling_enabled", "SESSION_COOKIE_HANDLING_DENIED"),
    ("oauth_flow_enabled", "OAUTH_FLOW_DENIED"),
    ("token_exchange_enabled", "TOKEN_EXCHANGE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
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

_M116_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M116_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M116_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M116_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M116_BASELINE_BINDING_REQUIRED"),
    (
        "source_production_audit_retention_bound",
        "M116_SOURCE_PRODUCTION_AUDIT_RETENTION_BINDING_REQUIRED",
    ),
    ("user_bound", "M116_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M116_WORKSPACE_BINDING_REQUIRED"),
    ("role_bound", "M116_ROLE_BINDING_REQUIRED"),
    ("authority_scope_bound", "M116_AUTHORITY_SCOPE_BINDING_REQUIRED"),
    ("permission_boundary_bound", "M116_PERMISSION_BOUNDARY_BINDING_REQUIRED"),
    ("separation_of_duty_bound", "M116_SEPARATION_OF_DUTY_BINDING_REQUIRED"),
    ("audit_required", "M116_AUDIT_REQUIRED"),
    ("replay_safe", "M116_REPLAY_REQUIRED"),
]

_M116_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("authority_runtime_enabled", "AUTHORITY_RUNTIME_DENIED"),
    ("role_enforcement_enabled", "ROLE_ENFORCEMENT_DENIED"),
    ("permission_enforcement_enabled", "PERMISSION_ENFORCEMENT_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_handling_enabled", "SESSION_COOKIE_HANDLING_DENIED"),
    ("oauth_flow_enabled", "OAUTH_FLOW_DENIED"),
    ("token_exchange_enabled", "TOKEN_EXCHANGE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
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

_M116_SOURCE_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("audit_runtime_enabled", "AUDIT_RUNTIME_DENIED"),
    ("audit_store_enabled", "AUDIT_STORE_DENIED"),
    ("audit_export_enabled", "AUDIT_EXPORT_DENIED"),
    ("raw_log_storage_enabled", "RAW_LOG_STORAGE_DENIED"),
    ("raw_prompt_storage_enabled", "RAW_PROMPT_STORAGE_DENIED"),
    ("raw_provider_payload_storage_enabled", "RAW_PROVIDER_PAYLOAD_STORAGE_DENIED"),
    ("secret_storage_enabled", "SECRET_STORAGE_DENIED"),
    ("external_saas_export_enabled", "EXTERNAL_SAAS_EXPORT_DENIED"),
    ("network_delivery_enabled", "NETWORK_DELIVERY_DENIED"),
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
