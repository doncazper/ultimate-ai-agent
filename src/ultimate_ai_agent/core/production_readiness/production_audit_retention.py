from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.account_connector_review import (
    AccountConnectorContractReviewRecord,
    validate_account_connector_contract_review_record,
)


PRODUCTION_AUDIT_RETENTION_DOCS = [
    "docs/production/PRODUCTION_AUDIT_RETENTION_POLICY.md",
    "docs/production/PRODUCTION_AUDIT_RETENTION_AUTHORITY_BOUNDARY.md",
    "docs/production/PRODUCTION_AUDIT_RETENTION_RECEIPT_PLAN.md",
    "docs/production/PRODUCTION_AUDIT_RETENTION_NON_GOALS.md",
    "docs/production/M115_TO_M116_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ProductionAuditRetentionPolicyStatus(str, Enum):
    retention_policy = "retention_policy"


class _ProductionAuditRetentionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ProductionAuditRetentionPolicy(_ProductionAuditRetentionModel):
    policy_ref: str = "production-audit-retention-policy:m115"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_account_connector_review_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    retention_schedule_binding_required: bool = True
    redaction_boundary_binding_required: bool = True
    deletion_window_binding_required: bool = True
    retention_policy_refs_required: bool = True
    retention_schedule_refs_required: bool = True
    audit_data_class_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    audit_runtime_enabled: bool = False
    audit_store_enabled: bool = False
    audit_export_enabled: bool = False
    raw_log_storage_enabled: bool = False
    raw_prompt_storage_enabled: bool = False
    raw_provider_payload_storage_enabled: bool = False
    secret_storage_enabled: bool = False
    external_saas_export_enabled: bool = False
    network_delivery_enabled: bool = False
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


class ProductionAuditRetentionPolicyRecord(_ProductionAuditRetentionModel):
    audit_retention_policy_ref: str
    source_record: AccountConnectorContractReviewRecord
    source_account_connector_review_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    retention_policy_refs: list[str]
    retention_schedule_refs: list[str]
    audit_data_class_refs: list[str]
    redaction_policy_ref: str
    deletion_window_ref: str
    legal_hold_boundary_ref: str
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: ProductionAuditRetentionPolicyStatus = (
        ProductionAuditRetentionPolicyStatus.retention_policy
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_account_connector_review_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    retention_schedule_bound: bool = True
    redaction_boundary_bound: bool = True
    deletion_window_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    production_authority_enabled: bool = False
    production_runtime_enabled: bool = False
    audit_runtime_enabled: bool = False
    audit_store_enabled: bool = False
    audit_export_enabled: bool = False
    raw_log_storage_enabled: bool = False
    raw_prompt_storage_enabled: bool = False
    raw_provider_payload_storage_enabled: bool = False
    secret_storage_enabled: bool = False
    external_saas_export_enabled: bool = False
    network_delivery_enabled: bool = False
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
            (self.audit_retention_policy_ref, "audit_retention_policy_ref"),
            (
                self.source_account_connector_review_ref,
                "source_account_connector_review_ref",
            ),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.user_ref, "user_ref"),
            (self.workspace_ref, "workspace_ref"),
            (self.redaction_policy_ref, "redaction_policy_ref"),
            (self.deletion_window_ref, "deletion_window_ref"),
            (self.legal_hold_boundary_ref, "legal_hold_boundary_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
            (self.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        for ref in self.retention_policy_refs:
            _validate_m61_ref(ref, "retention_policy_ref")
        for ref in self.retention_schedule_refs:
            _validate_m61_ref(ref, "retention_schedule_ref")
        for ref in self.audit_data_class_refs:
            _validate_m61_ref(ref, "audit_data_class_ref")
        for ref in self.accepted_checkpoint_refs:
            _validate_m61_ref(ref, "accepted_checkpoint_ref")
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_production_audit_retention_policy_record(
    *,
    source_record: AccountConnectorContractReviewRecord,
    policy: ProductionAuditRetentionPolicy | None = None,
) -> ProductionAuditRetentionPolicyRecord:
    active_policy = validate_production_audit_retention_policy(
        policy or ProductionAuditRetentionPolicy()
    )
    validated_source = _validate_source_account_connector_record(source_record)
    record = ProductionAuditRetentionPolicyRecord(
        audit_retention_policy_ref="audit-retention-policy:m115",
        source_record=validated_source,
        source_account_connector_review_ref=(
            validated_source.account_connector_review_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        retention_policy_refs=[
            "retention-policy-ref:m115:redacted-audit-minimum",
            "retention-policy-ref:m115:no-raw-log-retention",
            "retention-policy-ref:m115:no-external-delivery",
        ],
        retention_schedule_refs=[
            "retention-schedule-ref:m115:declared-safe-metadata-only",
            "retention-schedule-ref:m115:review-required-before-runtime",
        ],
        audit_data_class_refs=[
            "audit-data-class-ref:m115:safe-event-metadata",
            "audit-data-class-ref:m115:redacted-receipt-summary",
        ],
        redaction_policy_ref="redaction-policy-ref:m115:retention-safe-summary-only",
        deletion_window_ref="deletion-window-ref:m115:declared-no-runtime-window",
        legal_hold_boundary_ref="legal-hold-boundary-ref:m115:review-only-no-hold",
        audit_ref="audit-ref:m115:production-audit-retention-policy",
        replay_ref="replay-ref:m115:production-audit-retention-policy",
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
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m115:production-audit-retention-policy:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_account_connector_review_bound=(
            active_policy.source_account_connector_review_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        retention_schedule_bound=active_policy.retention_schedule_binding_required,
        redaction_boundary_bound=active_policy.redaction_boundary_binding_required,
        deletion_window_bound=active_policy.deletion_window_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M115_PRODUCTION_AUDIT_RETENTION_POLICY",
            "M115_CONTRACT_ONLY",
            "M115_REVIEW_ONLY",
            "M115_NO_AUDIT_RUNTIME_OR_EXPORT",
            "M116_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M115 records a contract-only and review-only production audit "
            "retention policy using safe refs, user refs, workspace refs, "
            "retention policy refs, retention schedule refs, audit data class "
            "refs, redaction policy refs, deletion window refs, legal hold "
            "boundary refs, audit refs, replay refs, and a no-effect receipt "
            "plan. It grants no production authority, starts no production "
            "runtime, starts no audit runtime, creates no audit store, exports "
            "nothing, retains no raw logs, retains no prompt bodies, retains "
            "no provider payload bodies, stores no sensitive values, sends no "
            "external SaaS data, delivers no network data, calls no models, "
            "writes no memory, injects no context, executes nothing, adds no "
            "routes, adds no controls, adds no dependencies, and keeps M116 "
            "future."
        ),
    )
    return validate_production_audit_retention_policy_record(record)


def validate_production_audit_retention_policy(
    policy: ProductionAuditRetentionPolicy,
) -> ProductionAuditRetentionPolicy:
    validated = ProductionAuditRetentionPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M115_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M115_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m115_metadata(validated.metadata)
    return validated


def validate_production_audit_retention_policy_record(
    record: ProductionAuditRetentionPolicyRecord,
) -> ProductionAuditRetentionPolicyRecord:
    payload = _model_payload(record)
    for field_name, reason in _M115_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, ProductionAuditRetentionPolicyRecord):
        raise ValueError("SECRET_LIKE_M115_AUDIT_RETENTION_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M115_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("retention_policy_refs", "M115_RETENTION_POLICY_REF_REQUIRED"),
        ("retention_schedule_refs", "M115_RETENTION_SCHEDULE_REF_REQUIRED"),
        ("audit_data_class_refs", "M115_AUDIT_DATA_CLASS_REF_REQUIRED"),
        ("redaction_policy_ref", "M115_REDACTION_POLICY_REF_REQUIRED"),
        ("deletion_window_ref", "M115_DELETION_WINDOW_REF_REQUIRED"),
        ("legal_hold_boundary_ref", "M115_LEGAL_HOLD_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_account_connector_record(payload.get("source_record"))
    validated_source = _validate_source_account_connector_record(source_record)
    validated = ProductionAuditRetentionPolicyRecord.model_validate(payload)
    for field_name, reason in _M115_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != ProductionAuditRetentionPolicyStatus.retention_policy:
        raise ValueError("M115_AUDIT_RETENTION_POLICY_STATUS_REQUIRED")
    for field_name, reason in _M115_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m115_bindings(validated, validated_source)
    _validate_m115_metadata(validated.metadata)
    return validated


def _coerce_source_account_connector_record(
    value: Any,
) -> AccountConnectorContractReviewRecord:
    if isinstance(value, AccountConnectorContractReviewRecord):
        return value
    if isinstance(value, dict):
        return AccountConnectorContractReviewRecord.model_validate(value)
    raise ValueError("M115_SOURCE_ACCOUNT_CONNECTOR_REVIEW_RECORD_REQUIRED")


def _validate_source_account_connector_record(
    source_record: AccountConnectorContractReviewRecord,
) -> AccountConnectorContractReviewRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M115_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_account_connector_contract_review_record(source_record)


def _validate_m115_bindings(
    record: ProductionAuditRetentionPolicyRecord,
    source_record: AccountConnectorContractReviewRecord,
) -> None:
    if record.source_account_connector_review_ref != (
        source_record.account_connector_review_ref
    ):
        raise ValueError("M115_SOURCE_ACCOUNT_CONNECTOR_REVIEW_BINDING_MISMATCH")
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M115_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M115_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M115_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M115_WORKSPACE_BINDING_MISMATCH")
    if record.audit_retention_policy_ref != "audit-retention-policy:m115":
        raise ValueError("M115_AUDIT_RETENTION_POLICY_REF_REQUIRED")
    for ref in record.retention_policy_refs:
        if not ref.startswith("retention-policy-ref:"):
            raise ValueError("M115_RETENTION_POLICY_REF_REQUIRED")
    for ref in record.retention_schedule_refs:
        if not ref.startswith("retention-schedule-ref:"):
            raise ValueError("M115_RETENTION_SCHEDULE_REF_REQUIRED")
    for ref in record.audit_data_class_refs:
        if not ref.startswith("audit-data-class-ref:"):
            raise ValueError("M115_AUDIT_DATA_CLASS_REF_REQUIRED")
    if not record.redaction_policy_ref.startswith("redaction-policy-ref:"):
        raise ValueError("M115_REDACTION_POLICY_REF_REQUIRED")
    if not record.deletion_window_ref.startswith("deletion-window-ref:"):
        raise ValueError("M115_DELETION_WINDOW_REF_REQUIRED")
    if not record.legal_hold_boundary_ref.startswith("legal-hold-boundary-ref:"):
        raise ValueError("M115_LEGAL_HOLD_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M115_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M115_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m115_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M115_AUDIT_RETENTION_CONTENT_DENIED") from exc


_M115_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M115_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M115_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M115_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M115_BASELINE_BINDING_REQUIRED"),
    (
        "source_account_connector_review_binding_required",
        "M115_SOURCE_ACCOUNT_CONNECTOR_REVIEW_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M115_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M115_WORKSPACE_BINDING_REQUIRED"),
    (
        "retention_schedule_binding_required",
        "M115_RETENTION_SCHEDULE_BINDING_REQUIRED",
    ),
    (
        "redaction_boundary_binding_required",
        "M115_REDACTION_BOUNDARY_BINDING_REQUIRED",
    ),
    ("deletion_window_binding_required", "M115_DELETION_WINDOW_BINDING_REQUIRED"),
    ("retention_policy_refs_required", "M115_RETENTION_POLICY_REF_REQUIRED"),
    ("retention_schedule_refs_required", "M115_RETENTION_SCHEDULE_REF_REQUIRED"),
    ("audit_data_class_refs_required", "M115_AUDIT_DATA_CLASS_REF_REQUIRED"),
    ("audit_required", "M115_AUDIT_REQUIRED"),
    ("replay_required", "M115_REPLAY_REQUIRED"),
]

_M115_POLICY_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("audit_runtime_enabled", "AUDIT_RUNTIME_DENIED"),
    ("audit_store_enabled", "AUDIT_STORE_DENIED"),
    ("audit_export_enabled", "AUDIT_EXPORT_DENIED"),
    ("raw_log_storage_enabled", "RAW_LOG_STORAGE_DENIED"),
    ("raw_prompt_storage_enabled", "RAW_PROMPT_STORAGE_DENIED"),
    (
        "raw_provider_payload_storage_enabled",
        "RAW_PROVIDER_PAYLOAD_STORAGE_DENIED",
    ),
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
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M115_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M115_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M115_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M115_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M115_BASELINE_BINDING_REQUIRED"),
    (
        "source_account_connector_review_bound",
        "M115_SOURCE_ACCOUNT_CONNECTOR_REVIEW_BINDING_REQUIRED",
    ),
    ("user_bound", "M115_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M115_WORKSPACE_BINDING_REQUIRED"),
    ("retention_schedule_bound", "M115_RETENTION_SCHEDULE_BINDING_REQUIRED"),
    ("redaction_boundary_bound", "M115_REDACTION_BOUNDARY_BINDING_REQUIRED"),
    ("deletion_window_bound", "M115_DELETION_WINDOW_BINDING_REQUIRED"),
    ("audit_required", "M115_AUDIT_REQUIRED"),
    ("replay_safe", "M115_REPLAY_REQUIRED"),
]

_M115_RECORD_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("audit_runtime_enabled", "AUDIT_RUNTIME_DENIED"),
    ("audit_store_enabled", "AUDIT_STORE_DENIED"),
    ("audit_export_enabled", "AUDIT_EXPORT_DENIED"),
    ("raw_log_storage_enabled", "RAW_LOG_STORAGE_DENIED"),
    ("raw_prompt_storage_enabled", "RAW_PROMPT_STORAGE_DENIED"),
    (
        "raw_provider_payload_storage_enabled",
        "RAW_PROVIDER_PAYLOAD_STORAGE_DENIED",
    ),
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

_M115_SOURCE_DENIALS = [
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
