from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.production_readiness.production_authority_readiness import (
    ProductionAuthorityReadinessReviewRecord,
    validate_production_authority_readiness_review_record,
)


EMAIL_CONNECTOR_CONTRACT_REFRESH_DOCS = [
    "docs/connectors/EMAIL_CONNECTOR_CONTRACT_REFRESH.md",
    "docs/connectors/EMAIL_CONNECTOR_AUTHORITY_BOUNDARY.md",
    "docs/connectors/EMAIL_CONNECTOR_RECEIPT_PLAN.md",
    "docs/connectors/EMAIL_CONNECTOR_NON_GOALS.md",
    "docs/connectors/M121_TO_M122_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class EmailConnectorContractRefreshStatus(str, Enum):
    email_connector_contract_refresh = "email_connector_contract_refresh"


class _EmailConnectorContractRefresh(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class EmailConnectorContractRefreshPolicy(_EmailConnectorContractRefresh):
    policy_ref: str = "email-connector-contract-refresh-policy:m121"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_production_authority_readiness_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    email_scope_binding_required: bool = True
    mailbox_boundary_binding_required: bool = True
    consent_boundary_binding_required: bool = True
    data_classification_binding_required: bool = True
    retention_boundary_binding_required: bool = True
    email_scope_refs_required: bool = True
    mailbox_boundary_refs_required: bool = True
    consent_boundary_refs_required: bool = True
    data_classification_refs_required: bool = True
    retention_boundary_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    email_connector_runtime_enabled: bool = False
    email_account_auth_enabled: bool = False
    email_read_enabled: bool = False
    email_search_enabled: bool = False
    email_send_enabled: bool = False
    email_write_enabled: bool = False
    email_delete_enabled: bool = False
    email_attachment_download_enabled: bool = False
    raw_email_content_enabled: bool = False
    credential_handling_enabled: bool = False
    network_access_enabled: bool = False
    account_action_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class EmailConnectorContractRefreshRecord(_EmailConnectorContractRefresh):
    email_connector_contract_refresh_ref: str
    source_record: ProductionAuthorityReadinessReviewRecord
    source_production_authority_readiness_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    email_scope_refs: list[str]
    mailbox_boundary_refs: list[str]
    consent_boundary_refs: list[str]
    data_classification_refs: list[str]
    retention_boundary_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: EmailConnectorContractRefreshStatus = (
        EmailConnectorContractRefreshStatus.email_connector_contract_refresh
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_production_authority_readiness_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    email_scope_bound: bool = True
    mailbox_boundary_bound: bool = True
    consent_boundary_bound: bool = True
    data_classification_bound: bool = True
    retention_boundary_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    email_connector_runtime_enabled: bool = False
    email_account_auth_enabled: bool = False
    email_read_enabled: bool = False
    email_search_enabled: bool = False
    email_send_enabled: bool = False
    email_write_enabled: bool = False
    email_delete_enabled: bool = False
    email_attachment_download_enabled: bool = False
    raw_email_content_enabled: bool = False
    credential_handling_enabled: bool = False
    network_access_enabled: bool = False
    account_action_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
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
            (
                self.email_connector_contract_refresh_ref,
                "email_connector_contract_refresh_ref",
            ),
            (
                self.source_production_authority_readiness_ref,
                "source_production_authority_readiness_ref",
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
        for field_name, refs in [
            ("email_scope_ref", self.email_scope_refs),
            ("mailbox_boundary_ref", self.mailbox_boundary_refs),
            ("consent_boundary_ref", self.consent_boundary_refs),
            ("data_classification_ref", self.data_classification_refs),
            ("retention_boundary_ref", self.retention_boundary_refs),
            ("accepted_checkpoint_ref", self.accepted_checkpoint_refs),
        ]:
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_email_connector_contract_refresh_record(
    *,
    source_record: ProductionAuthorityReadinessReviewRecord,
    policy: EmailConnectorContractRefreshPolicy | None = None,
) -> EmailConnectorContractRefreshRecord:
    active_policy = validate_email_connector_contract_refresh_policy(
        policy or EmailConnectorContractRefreshPolicy()
    )
    validated_source = _validate_source_production_authority_readiness_record(
        _coerce_source_production_authority_readiness_record(source_record)
    )
    record = EmailConnectorContractRefreshRecord(
        email_connector_contract_refresh_ref="email-connector-contract-refresh:m121",
        source_record=validated_source,
        source_production_authority_readiness_ref=(
            validated_source.production_authority_readiness_review_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        email_scope_refs=[
            "email-scope-ref:m121:declared-mailbox-boundary",
            "email-scope-ref:m121:metadata-preview-only",
            "email-scope-ref:m121:no-account-action",
        ],
        mailbox_boundary_refs=[
            "mailbox-boundary-ref:m121:declared-only",
            "mailbox-boundary-ref:m121:no-mailbox-access",
        ],
        consent_boundary_refs=[
            "consent-boundary-ref:m121:future-exact-actor-resource",
            "consent-boundary-ref:m121:no-account-connection",
        ],
        data_classification_refs=[
            "data-classification-ref:m121:metadata-summary-only",
            "data-classification-ref:m121:no-message-body",
        ],
        retention_boundary_refs=[
            "retention-boundary-ref:m121:no-mail-storage",
            "retention-boundary-ref:m121:no-attachment-storage",
        ],
        audit_ref="audit-ref:m121:email-connector-contract-refresh",
        replay_ref="replay-ref:m121:email-connector-contract-refresh",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m120",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m121:email-connector-contract-refresh:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_production_authority_readiness_bound=(
            active_policy.source_production_authority_readiness_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        email_scope_bound=active_policy.email_scope_binding_required,
        mailbox_boundary_bound=active_policy.mailbox_boundary_binding_required,
        consent_boundary_bound=active_policy.consent_boundary_binding_required,
        data_classification_bound=active_policy.data_classification_binding_required,
        retention_boundary_bound=active_policy.retention_boundary_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M121_EMAIL_CONNECTOR_CONTRACT_REFRESH",
            "M121_CONTRACT_ONLY",
            "M121_REVIEW_ONLY",
            "M121_NO_EMAIL_RUNTIME_OR_ACCOUNT_AUTH",
            "M122_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M121 records a contract-only and review-only email connector "
            "contract refresh using safe refs for email scope, mailbox "
            "boundaries, consent boundaries, data classification, retention, "
            "audit, replay, and a no-effect receipt plan. It grants no mail "
            "runtime, no account connection, no mailbox data access, no mail "
            "delivery, no network access, no credentials, no routes, no "
            "controls, no dependencies, and keeps M122 future."
        ),
    )
    return validate_email_connector_contract_refresh_record(record)


def validate_email_connector_contract_refresh_policy(
    policy: EmailConnectorContractRefreshPolicy,
) -> EmailConnectorContractRefreshPolicy:
    validated = EmailConnectorContractRefreshPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M121_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M121_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m121_metadata(validated.metadata)
    return validated


def validate_email_connector_contract_refresh_record(
    record: EmailConnectorContractRefreshRecord,
) -> EmailConnectorContractRefreshRecord:
    payload = _model_payload(record)
    for field_name, reason in _M121_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, EmailConnectorContractRefreshRecord):
        raise ValueError("SECRET_LIKE_M121_EMAIL_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M121_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("email_scope_refs", "M121_EMAIL_SCOPE_REF_REQUIRED"),
        ("mailbox_boundary_refs", "M121_MAILBOX_BOUNDARY_REF_REQUIRED"),
        ("consent_boundary_refs", "M121_CONSENT_BOUNDARY_REF_REQUIRED"),
        ("data_classification_refs", "M121_DATA_CLASSIFICATION_REF_REQUIRED"),
        ("retention_boundary_refs", "M121_RETENTION_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_production_authority_readiness_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_production_authority_readiness_record(
        source_record
    )
    validated = EmailConnectorContractRefreshRecord.model_validate(payload)
    for field_name, reason in _M121_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != EmailConnectorContractRefreshStatus.email_connector_contract_refresh
    ):
        raise ValueError("M121_EMAIL_CONNECTOR_CONTRACT_REFRESH_STATUS_REQUIRED")
    for field_name, reason in _M121_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m121_bindings(validated, validated_source)
    _validate_m121_metadata(validated.metadata)
    return validated


def _coerce_source_production_authority_readiness_record(
    value: Any,
) -> ProductionAuthorityReadinessReviewRecord:
    if isinstance(value, ProductionAuthorityReadinessReviewRecord):
        return value
    if isinstance(value, dict):
        return ProductionAuthorityReadinessReviewRecord.model_validate(value)
    raise ValueError("M121_SOURCE_RECORD_REQUIRED")


def _validate_source_production_authority_readiness_record(
    source_record: ProductionAuthorityReadinessReviewRecord,
) -> ProductionAuthorityReadinessReviewRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M121_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_production_authority_readiness_review_record(source_record)


def _validate_m121_bindings(
    record: EmailConnectorContractRefreshRecord,
    source_record: ProductionAuthorityReadinessReviewRecord,
) -> None:
    if (
        record.source_production_authority_readiness_ref
        != source_record.production_authority_readiness_review_ref
    ):
        raise ValueError(
            "M121_SOURCE_PRODUCTION_AUTHORITY_READINESS_BINDING_MISMATCH"
        )
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M121_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M121_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M121_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M121_WORKSPACE_BINDING_MISMATCH")
    if (
        record.email_connector_contract_refresh_ref
        != "email-connector-contract-refresh:m121"
    ):
        raise ValueError("M121_EMAIL_CONNECTOR_CONTRACT_REFRESH_REF_REQUIRED")
    for ref in record.email_scope_refs:
        if not ref.startswith("email-scope-ref:"):
            raise ValueError("M121_EMAIL_SCOPE_REF_REQUIRED")
    for ref in record.mailbox_boundary_refs:
        if not ref.startswith("mailbox-boundary-ref:"):
            raise ValueError("M121_MAILBOX_BOUNDARY_REF_REQUIRED")
    for ref in record.consent_boundary_refs:
        if not ref.startswith("consent-boundary-ref:"):
            raise ValueError("M121_CONSENT_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M121_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m120" not in record.accepted_checkpoint_refs:
        raise ValueError("M121_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M121_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m121_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M121_EMAIL_CONTENT_DENIED") from exc


_M121_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M121_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M121_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M121_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M121_BASELINE_BINDING_REQUIRED"),
    (
        "source_production_authority_readiness_binding_required",
        "M121_SOURCE_PRODUCTION_AUTHORITY_READINESS_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M121_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M121_WORKSPACE_BINDING_REQUIRED"),
    ("email_scope_binding_required", "M121_EMAIL_SCOPE_BINDING_REQUIRED"),
    ("mailbox_boundary_binding_required", "M121_MAILBOX_BOUNDARY_BINDING_REQUIRED"),
    ("consent_boundary_binding_required", "M121_CONSENT_BOUNDARY_BINDING_REQUIRED"),
    (
        "data_classification_binding_required",
        "M121_DATA_CLASSIFICATION_BINDING_REQUIRED",
    ),
    ("retention_boundary_binding_required", "M121_RETENTION_BOUNDARY_BINDING_REQUIRED"),
    ("email_scope_refs_required", "M121_EMAIL_SCOPE_REF_REQUIRED"),
    ("mailbox_boundary_refs_required", "M121_MAILBOX_BOUNDARY_REF_REQUIRED"),
    ("consent_boundary_refs_required", "M121_CONSENT_BOUNDARY_REF_REQUIRED"),
    ("data_classification_refs_required", "M121_DATA_CLASSIFICATION_REF_REQUIRED"),
    ("retention_boundary_refs_required", "M121_RETENTION_BOUNDARY_REF_REQUIRED"),
    ("audit_required", "M121_AUDIT_REQUIRED"),
    ("replay_required", "M121_REPLAY_REQUIRED"),
]

_M121_POLICY_DENIALS = [
    ("email_connector_runtime_enabled", "EMAIL_CONNECTOR_RUNTIME_DENIED"),
    ("email_account_auth_enabled", "EMAIL_ACCOUNT_AUTH_DENIED"),
    ("email_read_enabled", "EMAIL_READ_DENIED"),
    ("email_search_enabled", "EMAIL_SEARCH_DENIED"),
    ("email_send_enabled", "EMAIL_SEND_DENIED"),
    ("email_write_enabled", "EMAIL_WRITE_DENIED"),
    ("email_delete_enabled", "EMAIL_DELETE_DENIED"),
    ("email_attachment_download_enabled", "EMAIL_ATTACHMENT_DOWNLOAD_DENIED"),
    ("raw_email_content_enabled", "RAW_EMAIL_CONTENT_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M121_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M121_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M121_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M121_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M121_BASELINE_BINDING_REQUIRED"),
    (
        "source_production_authority_readiness_bound",
        "M121_SOURCE_PRODUCTION_AUTHORITY_READINESS_BINDING_REQUIRED",
    ),
    ("user_bound", "M121_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M121_WORKSPACE_BINDING_REQUIRED"),
    ("email_scope_bound", "M121_EMAIL_SCOPE_BINDING_REQUIRED"),
    ("mailbox_boundary_bound", "M121_MAILBOX_BOUNDARY_BINDING_REQUIRED"),
    ("consent_boundary_bound", "M121_CONSENT_BOUNDARY_BINDING_REQUIRED"),
    ("data_classification_bound", "M121_DATA_CLASSIFICATION_BINDING_REQUIRED"),
    ("retention_boundary_bound", "M121_RETENTION_BOUNDARY_BINDING_REQUIRED"),
    ("audit_required", "M121_AUDIT_REQUIRED"),
    ("replay_safe", "M121_REPLAY_REQUIRED"),
]

_M121_RECORD_DENIALS = [
    ("email_connector_runtime_enabled", "EMAIL_CONNECTOR_RUNTIME_DENIED"),
    ("email_account_auth_enabled", "EMAIL_ACCOUNT_AUTH_DENIED"),
    ("email_read_enabled", "EMAIL_READ_DENIED"),
    ("email_search_enabled", "EMAIL_SEARCH_DENIED"),
    ("email_send_enabled", "EMAIL_SEND_DENIED"),
    ("email_write_enabled", "EMAIL_WRITE_DENIED"),
    ("email_delete_enabled", "EMAIL_DELETE_DENIED"),
    ("email_attachment_download_enabled", "EMAIL_ATTACHMENT_DOWNLOAD_DENIED"),
    ("raw_email_content_enabled", "RAW_EMAIL_CONTENT_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M121_SOURCE_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("production_runtime_enabled", "PRODUCTION_RUNTIME_DENIED"),
    ("go_live_enabled", "GO_LIVE_DENIED"),
    ("production_deployment_enabled", "PRODUCTION_DEPLOYMENT_DENIED"),
    ("external_distribution_enabled", "EXTERNAL_DISTRIBUTION_DENIED"),
    ("traffic_routing_enabled", "TRAFFIC_ROUTING_DENIED"),
    ("account_action_enabled", "ACCOUNT_ACTION_DENIED"),
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
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]
