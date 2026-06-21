from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.user_workspace_identity import (
    UserWorkspaceIdentityRecord,
    validate_user_workspace_identity_record,
)


SECRETS_BOUNDARY_DOCS = [
    "docs/production/SECRETS_BOUNDARY_CREDENTIAL_VAULT_CONTRACT.md",
    "docs/production/SECRETS_BOUNDARY_POLICY.md",
    "docs/production/SECRETS_BOUNDARY_AUTHORITY_BOUNDARY.md",
    "docs/production/SECRETS_BOUNDARY_RECEIPT_PLAN.md",
    "docs/production/SECRETS_BOUNDARY_NON_GOALS.md",
    "docs/production/M113_TO_M114_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class SecretsBoundaryStatus(str, Enum):
    credential_vault_contract = "credential_vault_contract"


class _SecretsBoundaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class SecretsBoundaryPolicy(_SecretsBoundaryModel):
    policy_ref: str = "secrets-boundary-policy:m113"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_identity_model_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    credential_vault_contract_binding_required: bool = True
    secret_boundary_refs_required: bool = True
    credential_scope_refs_required: bool = True
    redaction_policy_ref_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_enabled: bool = False
    credential_storage_enabled: bool = False
    credential_read_enabled: bool = False
    credential_write_enabled: bool = False
    secret_material_access_enabled: bool = False
    secret_export_enabled: bool = False
    vault_runtime_enabled: bool = False
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


class SecretsBoundaryRecord(_SecretsBoundaryModel):
    secrets_boundary_ref: str
    source_record: UserWorkspaceIdentityRecord
    source_identity_model_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    credential_vault_contract_ref: str
    secret_boundary_refs: list[str]
    credential_scope_refs: list[str]
    redaction_policy_ref: str
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: SecretsBoundaryStatus = SecretsBoundaryStatus.credential_vault_contract
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_identity_model_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    credential_vault_contract_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_enabled: bool = False
    credential_storage_enabled: bool = False
    credential_read_enabled: bool = False
    credential_write_enabled: bool = False
    secret_material_access_enabled: bool = False
    secret_export_enabled: bool = False
    vault_runtime_enabled: bool = False
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
            (self.secrets_boundary_ref, "secrets_boundary_ref"),
            (self.source_identity_model_ref, "source_identity_model_ref"),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.credential_vault_contract_ref, "credential_vault_contract_ref"),
            (self.redaction_policy_ref, "redaction_policy_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.secret_boundary_refs:
            _validate_m61_ref(ref, "secret_boundary_ref")
        for ref in self.credential_scope_refs:
            _validate_m61_ref(ref, "credential_scope_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_secrets_boundary_record(
    *,
    source_record: UserWorkspaceIdentityRecord,
    policy: SecretsBoundaryPolicy | None = None,
) -> SecretsBoundaryRecord:
    active_policy = validate_secrets_boundary_policy(policy or SecretsBoundaryPolicy())
    validated_source = _validate_source_identity_record(source_record)
    record = SecretsBoundaryRecord(
        secrets_boundary_ref="secrets-boundary:m113",
        source_record=validated_source,
        source_identity_model_ref=validated_source.identity_model_ref,
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        credential_vault_contract_ref=(
            "credential-vault-contract:m113:no-secret-material"
        ),
        secret_boundary_refs=[
            "secret-boundary-ref:m113:no-secret-material",
            "secret-boundary-ref:m113:no-credential-runtime",
            "secret-boundary-ref:m113:no-account-connector",
        ],
        credential_scope_refs=[
            "credential-scope-ref:m113:declared-safe-refs-only",
            "credential-scope-ref:m113:no-runtime-values",
        ],
        redaction_policy_ref="redaction-policy-ref:m113:credential-safe",
        audit_ref="audit-ref:m113:secrets-boundary",
        replay_ref="replay-ref:m113:secrets-boundary",
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
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m113:secrets-boundary:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_identity_model_bound=(
            active_policy.source_identity_model_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        credential_vault_contract_bound=(
            active_policy.credential_vault_contract_binding_required
        ),
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M113_SECRETS_BOUNDARY_CREDENTIAL_VAULT_CONTRACT",
            "M113_CONTRACT_ONLY",
            "M113_REVIEW_ONLY",
            "M113_NO_SECRET_MATERIAL",
            "M114_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M113 records a contract-only and review-only boundary plus vault "
            "contract using safe refs, user refs, workspace refs, boundary "
            "refs, scope refs, a redaction policy ref, audit refs, replay "
            "refs, and a no-effect receipt plan. It grants no production "
            "authority, starts no runtime, creates no login flow, creates no "
            "session store, handles no sensitive values, stores no sensitive "
            "values, reads no sensitive values, writes no sensitive values, "
            "exports no private values, accesses no networks, calls no models, "
            "writes no memory, injects no context, executes nothing, adds no "
            "routes, adds no controls, adds no dependencies, and keeps M114 "
            "future."
        ),
    )
    return validate_secrets_boundary_record(record)


def validate_secrets_boundary_policy(
    policy: SecretsBoundaryPolicy,
) -> SecretsBoundaryPolicy:
    validated = SecretsBoundaryPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M113_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M113_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m113_metadata(validated.metadata)
    return validated


def validate_secrets_boundary_record(
    record: SecretsBoundaryRecord,
) -> SecretsBoundaryRecord:
    payload = _model_payload(record)
    for field_name, reason in _M113_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, SecretsBoundaryRecord):
        raise ValueError("SECRET_LIKE_M113_SECRETS_BOUNDARY_CONTENT_DENIED")
    if not payload.get("accepted_checkpoint_refs"):
        raise ValueError("M113_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    if not payload.get("credential_vault_contract_ref"):
        raise ValueError("M113_CREDENTIAL_VAULT_CONTRACT_REF_REQUIRED")
    if not payload.get("secret_boundary_refs"):
        raise ValueError("M113_SECRET_BOUNDARY_REF_REQUIRED")
    if not payload.get("credential_scope_refs"):
        raise ValueError("M113_CREDENTIAL_SCOPE_REF_REQUIRED")
    if not payload.get("redaction_policy_ref"):
        raise ValueError("M113_REDACTION_POLICY_REF_REQUIRED")
    source_record = _coerce_source_identity_record(payload.get("source_record"))
    validated_source = _validate_source_identity_record(source_record)
    validated = SecretsBoundaryRecord.model_validate(payload)
    for field_name, reason in _M113_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != SecretsBoundaryStatus.credential_vault_contract:
        raise ValueError("M113_SECRETS_BOUNDARY_STATUS_REQUIRED")
    for field_name, reason in _M113_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m113_bindings(validated, validated_source)
    _validate_m113_metadata(validated.metadata)
    return validated


def _coerce_source_identity_record(value: Any) -> UserWorkspaceIdentityRecord:
    if isinstance(value, UserWorkspaceIdentityRecord):
        return value
    if isinstance(value, dict):
        return UserWorkspaceIdentityRecord.model_validate(value)
    raise ValueError("M113_SOURCE_IDENTITY_RECORD_REQUIRED")


def _validate_source_identity_record(
    source_record: UserWorkspaceIdentityRecord,
) -> UserWorkspaceIdentityRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M113_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_user_workspace_identity_record(source_record)


def _validate_m113_bindings(
    record: SecretsBoundaryRecord,
    source_record: UserWorkspaceIdentityRecord,
) -> None:
    if record.source_identity_model_ref != source_record.identity_model_ref:
        raise ValueError("M113_SOURCE_IDENTITY_MODEL_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M113_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M113_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M113_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M113_WORKSPACE_BINDING_MISMATCH")
    if record.secrets_boundary_ref != "secrets-boundary:m113":
        raise ValueError("M113_SECRETS_BOUNDARY_REF_REQUIRED")
    if not record.credential_vault_contract_ref.startswith(
        "credential-vault-contract:"
    ):
        raise ValueError("M113_CREDENTIAL_VAULT_CONTRACT_REF_REQUIRED")
    for ref in record.secret_boundary_refs:
        if not ref.startswith("secret-boundary-ref:"):
            raise ValueError("M113_SECRET_BOUNDARY_REF_REQUIRED")
    for ref in record.credential_scope_refs:
        if not ref.startswith("credential-scope-ref:"):
            raise ValueError("M113_CREDENTIAL_SCOPE_REF_REQUIRED")
    if not record.redaction_policy_ref.startswith("redaction-policy-ref:"):
        raise ValueError("M113_REDACTION_POLICY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M113_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M113_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m113_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M113_SECRETS_BOUNDARY_CONTENT_DENIED") from exc


_M113_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M113_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M113_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M113_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M113_BASELINE_BINDING_REQUIRED"),
    (
        "source_identity_model_binding_required",
        "M113_SOURCE_IDENTITY_MODEL_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M113_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M113_WORKSPACE_BINDING_REQUIRED"),
    (
        "credential_vault_contract_binding_required",
        "M113_CREDENTIAL_VAULT_CONTRACT_BINDING_REQUIRED",
    ),
    ("secret_boundary_refs_required", "M113_SECRET_BOUNDARY_REF_REQUIRED"),
    ("credential_scope_refs_required", "M113_CREDENTIAL_SCOPE_REF_REQUIRED"),
    ("redaction_policy_ref_required", "M113_REDACTION_POLICY_REF_REQUIRED"),
    ("audit_required", "M113_AUDIT_REQUIRED"),
    ("replay_required", "M113_REPLAY_REQUIRED"),
]

_M113_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("credential_storage_enabled", "CREDENTIAL_STORAGE_DENIED"),
    ("credential_read_enabled", "CREDENTIAL_READ_DENIED"),
    ("credential_write_enabled", "CREDENTIAL_WRITE_DENIED"),
    ("secret_material_access_enabled", "SECRET_MATERIAL_ACCESS_DENIED"),
    ("secret_export_enabled", "SECRET_EXPORT_DENIED"),
    ("vault_runtime_enabled", "VAULT_RUNTIME_DENIED"),
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

_M113_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M113_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M113_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M113_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M113_BASELINE_BINDING_REQUIRED"),
    ("source_identity_model_bound", "M113_SOURCE_IDENTITY_MODEL_BINDING_REQUIRED"),
    ("user_bound", "M113_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M113_WORKSPACE_BINDING_REQUIRED"),
    (
        "credential_vault_contract_bound",
        "M113_CREDENTIAL_VAULT_CONTRACT_BINDING_REQUIRED",
    ),
    ("audit_required", "M113_AUDIT_REQUIRED"),
    ("replay_safe", "M113_REPLAY_REQUIRED"),
]

_M113_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("credential_storage_enabled", "CREDENTIAL_STORAGE_DENIED"),
    ("credential_read_enabled", "CREDENTIAL_READ_DENIED"),
    ("credential_write_enabled", "CREDENTIAL_WRITE_DENIED"),
    ("secret_material_access_enabled", "SECRET_MATERIAL_ACCESS_DENIED"),
    ("secret_export_enabled", "SECRET_EXPORT_DENIED"),
    ("vault_runtime_enabled", "VAULT_RUNTIME_DENIED"),
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

_M113_SOURCE_DENIALS = [
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
]
