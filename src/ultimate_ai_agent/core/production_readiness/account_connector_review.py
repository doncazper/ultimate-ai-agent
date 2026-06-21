from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.secrets_boundary import (
    SecretsBoundaryRecord,
    validate_secrets_boundary_record,
)


ACCOUNT_CONNECTOR_REVIEW_DOCS = [
    "docs/production/ACCOUNT_CONNECTOR_CONTRACT_REVIEW.md",
    "docs/production/ACCOUNT_CONNECTOR_POLICY.md",
    "docs/production/ACCOUNT_CONNECTOR_AUTHORITY_BOUNDARY.md",
    "docs/production/ACCOUNT_CONNECTOR_RECEIPT_PLAN.md",
    "docs/production/ACCOUNT_CONNECTOR_NON_GOALS.md",
    "docs/production/M114_TO_M115_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class AccountConnectorContractReviewStatus(str, Enum):
    contract_review = "contract_review"


class _AccountConnectorReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AccountConnectorContractReviewPolicy(_AccountConnectorReviewModel):
    policy_ref: str = "account-connector-policy:m114"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_secrets_boundary_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    credential_boundary_binding_required: bool = True
    auth_boundary_binding_required: bool = True
    connector_contract_refs_required: bool = True
    connector_scope_refs_required: bool = True
    data_access_boundary_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    oauth_flow_enabled: bool = False
    token_exchange_enabled: bool = False
    credential_handling_enabled: bool = False
    credential_storage_enabled: bool = False
    credential_read_enabled: bool = False
    credential_write_enabled: bool = False
    secret_material_access_enabled: bool = False
    secret_export_enabled: bool = False
    vault_runtime_enabled: bool = False
    account_connector_runtime_enabled: bool = False
    account_connector_enabled: bool = False
    network_access_enabled: bool = False
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


class AccountConnectorContractReviewRecord(_AccountConnectorReviewModel):
    account_connector_review_ref: str
    source_record: SecretsBoundaryRecord
    source_secrets_boundary_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    connector_contract_refs: list[str]
    connector_scope_refs: list[str]
    credential_boundary_ref: str
    auth_boundary_ref: str
    data_access_boundary_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: AccountConnectorContractReviewStatus = (
        AccountConnectorContractReviewStatus.contract_review
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_secrets_boundary_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    credential_boundary_bound: bool = True
    auth_boundary_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    oauth_flow_enabled: bool = False
    token_exchange_enabled: bool = False
    credential_handling_enabled: bool = False
    credential_storage_enabled: bool = False
    credential_read_enabled: bool = False
    credential_write_enabled: bool = False
    secret_material_access_enabled: bool = False
    secret_export_enabled: bool = False
    vault_runtime_enabled: bool = False
    account_connector_runtime_enabled: bool = False
    account_connector_enabled: bool = False
    network_access_enabled: bool = False
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
            (self.account_connector_review_ref, "account_connector_review_ref"),
            (self.source_secrets_boundary_ref, "source_secrets_boundary_ref"),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.credential_boundary_ref, "credential_boundary_ref"),
            (self.auth_boundary_ref, "auth_boundary_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.connector_contract_refs:
            _validate_m61_ref(ref, "connector_contract_ref")
        for ref in self.connector_scope_refs:
            _validate_m61_ref(ref, "connector_scope_ref")
        for ref in self.data_access_boundary_refs:
            _validate_m61_ref(ref, "data_access_boundary_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_account_connector_contract_review_record(
    *,
    source_record: SecretsBoundaryRecord,
    policy: AccountConnectorContractReviewPolicy | None = None,
) -> AccountConnectorContractReviewRecord:
    active_policy = validate_account_connector_contract_review_policy(
        policy or AccountConnectorContractReviewPolicy()
    )
    validated_source = _validate_source_secrets_boundary_record(source_record)
    record = AccountConnectorContractReviewRecord(
        account_connector_review_ref="account-connector-review:m114",
        source_record=validated_source,
        source_secrets_boundary_ref=validated_source.secrets_boundary_ref,
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        connector_contract_refs=[
            "connector-contract-ref:m114:read-only-candidate",
            "connector-contract-ref:m114:no-runtime-auth",
            "connector-contract-ref:m114:no-account-action",
        ],
        connector_scope_refs=[
            "connector-scope-ref:m114:declared-safe-refs-only",
            "connector-scope-ref:m114:no-live-account-data",
        ],
        credential_boundary_ref="credential-boundary-ref:m114:no-sensitive-material",
        auth_boundary_ref="auth-boundary-ref:m114:no-auth-runtime",
        data_access_boundary_refs=[
            "data-access-boundary-ref:m114:no-live-account-read",
            "data-access-boundary-ref:m114:no-account-write",
        ],
        audit_ref="audit-ref:m114:account-connector-contract-review",
        replay_ref="replay-ref:m114:account-connector-contract-review",
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
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m114:account-connector-contract-review:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_secrets_boundary_bound=(
            active_policy.source_secrets_boundary_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        credential_boundary_bound=active_policy.credential_boundary_binding_required,
        auth_boundary_bound=active_policy.auth_boundary_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M114_ACCOUNT_CONNECTOR_CONTRACT_REVIEW",
            "M114_CONTRACT_ONLY",
            "M114_REVIEW_ONLY",
            "M114_NO_AUTH_OR_CONNECTOR_RUNTIME",
            "M115_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M114 records a contract-only and review-only account connector "
            "contract review using safe refs, user refs, workspace refs, "
            "connector contract refs, connector scope refs, boundary refs, "
            "audit refs, replay refs, and a no-effect receipt plan. It grants "
            "no production authority, starts no runtime, creates no login "
            "flow, creates no session store, handles no sensitive values, "
            "stores no sensitive values, reads no sensitive values, writes no "
            "sensitive values, performs no account actions, accesses no "
            "networks, calls no models, writes no memory, injects no context, "
            "executes nothing, adds no routes, adds no controls, adds no "
            "dependencies, and keeps M115 future."
        ),
    )
    return validate_account_connector_contract_review_record(record)


def validate_account_connector_contract_review_policy(
    policy: AccountConnectorContractReviewPolicy,
) -> AccountConnectorContractReviewPolicy:
    validated = AccountConnectorContractReviewPolicy.model_validate(
        _model_payload(policy)
    )
    for field_name, reason in _M114_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M114_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m114_metadata(validated.metadata)
    return validated


def validate_account_connector_contract_review_record(
    record: AccountConnectorContractReviewRecord,
) -> AccountConnectorContractReviewRecord:
    payload = _model_payload(record)
    for field_name, reason in _M114_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, AccountConnectorContractReviewRecord):
        raise ValueError("SECRET_LIKE_M114_ACCOUNT_CONNECTOR_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M114_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("connector_contract_refs", "M114_CONNECTOR_CONTRACT_REF_REQUIRED"),
        ("connector_scope_refs", "M114_CONNECTOR_SCOPE_REF_REQUIRED"),
        ("credential_boundary_ref", "M114_CREDENTIAL_BOUNDARY_REF_REQUIRED"),
        ("auth_boundary_ref", "M114_AUTH_BOUNDARY_REF_REQUIRED"),
        ("data_access_boundary_refs", "M114_DATA_ACCESS_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_secrets_boundary_record(payload.get("source_record"))
    validated_source = _validate_source_secrets_boundary_record(source_record)
    validated = AccountConnectorContractReviewRecord.model_validate(payload)
    for field_name, reason in _M114_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != AccountConnectorContractReviewStatus.contract_review:
        raise ValueError("M114_ACCOUNT_CONNECTOR_REVIEW_STATUS_REQUIRED")
    for field_name, reason in _M114_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m114_bindings(validated, validated_source)
    _validate_m114_metadata(validated.metadata)
    return validated


def _coerce_source_secrets_boundary_record(value: Any) -> SecretsBoundaryRecord:
    if isinstance(value, SecretsBoundaryRecord):
        return value
    if isinstance(value, dict):
        return SecretsBoundaryRecord.model_validate(value)
    raise ValueError("M114_SOURCE_SECRETS_BOUNDARY_RECORD_REQUIRED")


def _validate_source_secrets_boundary_record(
    source_record: SecretsBoundaryRecord,
) -> SecretsBoundaryRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M114_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_secrets_boundary_record(source_record)


def _validate_m114_bindings(
    record: AccountConnectorContractReviewRecord,
    source_record: SecretsBoundaryRecord,
) -> None:
    if record.source_secrets_boundary_ref != source_record.secrets_boundary_ref:
        raise ValueError("M114_SOURCE_SECRETS_BOUNDARY_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M114_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M114_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M114_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M114_WORKSPACE_BINDING_MISMATCH")
    if record.account_connector_review_ref != "account-connector-review:m114":
        raise ValueError("M114_ACCOUNT_CONNECTOR_REVIEW_REF_REQUIRED")
    for ref in record.connector_contract_refs:
        if not ref.startswith("connector-contract-ref:"):
            raise ValueError("M114_CONNECTOR_CONTRACT_REF_REQUIRED")
    for ref in record.connector_scope_refs:
        if not ref.startswith("connector-scope-ref:"):
            raise ValueError("M114_CONNECTOR_SCOPE_REF_REQUIRED")
    if not record.credential_boundary_ref.startswith("credential-boundary-ref:"):
        raise ValueError("M114_CREDENTIAL_BOUNDARY_REF_REQUIRED")
    if not record.auth_boundary_ref.startswith("auth-boundary-ref:"):
        raise ValueError("M114_AUTH_BOUNDARY_REF_REQUIRED")
    for ref in record.data_access_boundary_refs:
        if not ref.startswith("data-access-boundary-ref:"):
            raise ValueError("M114_DATA_ACCESS_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M114_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M114_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m114_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M114_ACCOUNT_CONNECTOR_CONTENT_DENIED") from exc


_M114_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M114_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M114_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M114_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M114_BASELINE_BINDING_REQUIRED"),
    (
        "source_secrets_boundary_binding_required",
        "M114_SOURCE_SECRETS_BOUNDARY_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M114_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M114_WORKSPACE_BINDING_REQUIRED"),
    (
        "credential_boundary_binding_required",
        "M114_CREDENTIAL_BOUNDARY_BINDING_REQUIRED",
    ),
    ("auth_boundary_binding_required", "M114_AUTH_BOUNDARY_BINDING_REQUIRED"),
    ("connector_contract_refs_required", "M114_CONNECTOR_CONTRACT_REF_REQUIRED"),
    ("connector_scope_refs_required", "M114_CONNECTOR_SCOPE_REF_REQUIRED"),
    (
        "data_access_boundary_refs_required",
        "M114_DATA_ACCESS_BOUNDARY_REF_REQUIRED",
    ),
    ("audit_required", "M114_AUDIT_REQUIRED"),
    ("replay_required", "M114_REPLAY_REQUIRED"),
]

_M114_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
    ("oauth_flow_enabled", "OAUTH_FLOW_DENIED"),
    ("token_exchange_enabled", "TOKEN_EXCHANGE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("credential_storage_enabled", "CREDENTIAL_STORAGE_DENIED"),
    ("credential_read_enabled", "CREDENTIAL_READ_DENIED"),
    ("credential_write_enabled", "CREDENTIAL_WRITE_DENIED"),
    ("secret_material_access_enabled", "SECRET_MATERIAL_ACCESS_DENIED"),
    ("secret_export_enabled", "SECRET_EXPORT_DENIED"),
    ("vault_runtime_enabled", "VAULT_RUNTIME_DENIED"),
    ("account_connector_runtime_enabled", "ACCOUNT_CONNECTOR_RUNTIME_DENIED"),
    ("account_connector_enabled", "ACCOUNT_CONNECTOR_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
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
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M114_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M114_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M114_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M114_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M114_BASELINE_BINDING_REQUIRED"),
    (
        "source_secrets_boundary_bound",
        "M114_SOURCE_SECRETS_BOUNDARY_BINDING_REQUIRED",
    ),
    ("user_bound", "M114_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M114_WORKSPACE_BINDING_REQUIRED"),
    ("credential_boundary_bound", "M114_CREDENTIAL_BOUNDARY_BINDING_REQUIRED"),
    ("auth_boundary_bound", "M114_AUTH_BOUNDARY_BINDING_REQUIRED"),
    ("audit_required", "M114_AUDIT_REQUIRED"),
    ("replay_safe", "M114_REPLAY_REQUIRED"),
]

_M114_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("auth_runtime_enabled", "AUTH_RUNTIME_DENIED"),
    ("login_enabled", "LOGIN_DENIED"),
    ("session_cookie_enabled", "SESSION_COOKIE_DENIED"),
    ("oauth_flow_enabled", "OAUTH_FLOW_DENIED"),
    ("token_exchange_enabled", "TOKEN_EXCHANGE_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("credential_storage_enabled", "CREDENTIAL_STORAGE_DENIED"),
    ("credential_read_enabled", "CREDENTIAL_READ_DENIED"),
    ("credential_write_enabled", "CREDENTIAL_WRITE_DENIED"),
    ("secret_material_access_enabled", "SECRET_MATERIAL_ACCESS_DENIED"),
    ("secret_export_enabled", "SECRET_EXPORT_DENIED"),
    ("vault_runtime_enabled", "VAULT_RUNTIME_DENIED"),
    ("account_connector_runtime_enabled", "ACCOUNT_CONNECTOR_RUNTIME_DENIED"),
    ("account_connector_enabled", "ACCOUNT_CONNECTOR_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
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
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M114_SOURCE_DENIALS = [
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
]
