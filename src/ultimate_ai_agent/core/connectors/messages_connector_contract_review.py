from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.connectors.contacts_connector_contract_refresh import (
    ContactsConnectorContractRefreshRecord,
    validate_contacts_connector_contract_refresh_record,
)


MESSAGES_CONNECTOR_CONTRACT_REVIEW_DOCS = [
    "docs/connectors/MESSAGES_CONNECTOR_CONTRACT_REVIEW.md",
    "docs/connectors/MESSAGES_CONNECTOR_AUTHORITY_BOUNDARY.md",
    "docs/connectors/MESSAGES_CONNECTOR_RECEIPT_PLAN.md",
    "docs/connectors/MESSAGES_CONNECTOR_NON_GOALS.md",
    "docs/connectors/M124_TO_M125_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MessagesConnectorContractReviewStatus(str, Enum):
    messages_connector_contract_review = "messages_connector_contract_review"


class _MessagesConnectorContractReview(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MessagesConnectorContractReviewPolicy(_MessagesConnectorContractReview):
    policy_ref: str = "messages-connector-contract-review-policy:m124"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_contacts_connector_contract_refresh_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    messages_scope_binding_required: bool = True
    messages_boundary_binding_required: bool = True
    message_thread_boundary_binding_required: bool = True
    consent_boundary_binding_required: bool = True
    data_classification_binding_required: bool = True
    retention_boundary_binding_required: bool = True
    messages_scope_refs_required: bool = True
    messages_boundary_refs_required: bool = True
    message_thread_boundary_refs_required: bool = True
    consent_boundary_refs_required: bool = True
    data_classification_refs_required: bool = True
    retention_boundary_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    messages_connector_runtime_enabled: bool = False
    messages_account_auth_enabled: bool = False
    messages_read_enabled: bool = False
    messages_search_enabled: bool = False
    messages_lookup_enabled: bool = False
    messages_send_enabled: bool = False
    message_thread_access_enabled: bool = False
    messages_create_enabled: bool = False
    messages_update_enabled: bool = False
    messages_delete_enabled: bool = False
    messages_export_enabled: bool = False
    messages_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
    raw_messages_content_enabled: bool = False
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
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MessagesConnectorContractReviewRecord(_MessagesConnectorContractReview):
    messages_connector_contract_review_ref: str
    source_record: ContactsConnectorContractRefreshRecord
    source_contacts_connector_contract_refresh_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    messages_scope_refs: list[str]
    messages_boundary_refs: list[str]
    message_thread_boundary_refs: list[str]
    consent_boundary_refs: list[str]
    data_classification_refs: list[str]
    retention_boundary_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: MessagesConnectorContractReviewStatus = (
        MessagesConnectorContractReviewStatus.messages_connector_contract_review
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_contacts_connector_contract_refresh_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    messages_scope_bound: bool = True
    messages_boundary_bound: bool = True
    message_thread_boundary_bound: bool = True
    consent_boundary_bound: bool = True
    data_classification_bound: bool = True
    retention_boundary_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    messages_connector_runtime_enabled: bool = False
    messages_account_auth_enabled: bool = False
    messages_read_enabled: bool = False
    messages_search_enabled: bool = False
    messages_lookup_enabled: bool = False
    messages_send_enabled: bool = False
    message_thread_access_enabled: bool = False
    messages_create_enabled: bool = False
    messages_update_enabled: bool = False
    messages_delete_enabled: bool = False
    messages_export_enabled: bool = False
    messages_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
    raw_messages_content_enabled: bool = False
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
    def validate_shape(self) -> Any:
        for value, field_name in [
            (
                self.messages_connector_contract_review_ref,
                "messages_connector_contract_review_ref",
            ),
            (
                self.source_contacts_connector_contract_refresh_ref,
                "source_contacts_connector_contract_refresh_ref",
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
            ("messages_scope_ref", self.messages_scope_refs),
            ("messages_boundary_ref", self.messages_boundary_refs),
            ("message_thread_boundary_ref", self.message_thread_boundary_refs),
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


def build_messages_connector_contract_review_record(
    *,
    source_record: ContactsConnectorContractRefreshRecord,
    policy: MessagesConnectorContractReviewPolicy | None = None,
) -> MessagesConnectorContractReviewRecord:
    active_policy = validate_messages_connector_contract_review_policy(
        policy or MessagesConnectorContractReviewPolicy()
    )
    validated_source = _validate_source_contacts_connector_contract_refresh_record(
        _coerce_source_contacts_connector_contract_refresh_record(source_record)
    )
    record = MessagesConnectorContractReviewRecord(
        messages_connector_contract_review_ref="messages-connector-contract-review:m124",
        source_record=validated_source,
        source_contacts_connector_contract_refresh_ref=(
            validated_source.contacts_connector_contract_refresh_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        messages_scope_refs=[
            "messages-scope-ref:m124:declared-messages-boundary",
            "messages-scope-ref:m124:metadata-preview-only",
            "messages-scope-ref:m124:no-account-action",
        ],
        messages_boundary_refs=[
            "messages-boundary-ref:m124:declared-only",
            "messages-boundary-ref:m124:no-messages-access",
        ],
        message_thread_boundary_refs=[
            "message-thread-boundary-ref:m124:metadata-summary-only",
            "message-thread-boundary-ref:m124:no-message-thread-or-message-body-data",
        ],
        consent_boundary_refs=[
            "consent-boundary-ref:m124:future-exact-actor-resource",
            "consent-boundary-ref:m124:no-account-connection",
        ],
        data_classification_refs=[
            "data-classification-ref:m124:metadata-summary-only",
            "data-classification-ref:m124:no-message-body",
        ],
        retention_boundary_refs=[
            "retention-boundary-ref:m124:no-messages-storage",
            "retention-boundary-ref:m124:no-message-storage",
        ],
        audit_ref="audit-ref:m124:messages-connector-contract-review",
        replay_ref="replay-ref:m124:messages-connector-contract-review",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m123",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m124:messages-connector-contract-review:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_contacts_connector_contract_refresh_bound=(
            active_policy.source_contacts_connector_contract_refresh_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        messages_scope_bound=active_policy.messages_scope_binding_required,
        messages_boundary_bound=active_policy.messages_boundary_binding_required,
        message_thread_boundary_bound=active_policy.message_thread_boundary_binding_required,
        consent_boundary_bound=active_policy.consent_boundary_binding_required,
        data_classification_bound=active_policy.data_classification_binding_required,
        retention_boundary_bound=active_policy.retention_boundary_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M124_MESSAGES_CONNECTOR_CONTRACT_REVIEW",
            "M124_CONTRACT_ONLY",
            "M124_REVIEW_ONLY",
            "M124_NO_MESSAGES_RUNTIME_ACCOUNT_AUTH_OR_SEND",
            "M125_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M124 records a contract-only and review-only messages connector "
            "contract refresh using safe refs for messages scope, messages "
            "boundaries, message thread boundaries, consent boundaries, data "
            "classification, retention, audit, replay, and a no-effect receipt "
            "plan. It grants no messages runtime, no account connection, no "
            "messages data access, no message lookup, no send, no thread "
            "access, no message update/delete, no message export, no attachment "
            "retrieval, no network access, no credentials, no routes, no "
            "controls, no dependencies, and keeps M125 future."
        ),
    )
    return validate_messages_connector_contract_review_record(record)


def validate_messages_connector_contract_review_policy(
    policy: MessagesConnectorContractReviewPolicy,
) -> MessagesConnectorContractReviewPolicy:
    validated = MessagesConnectorContractReviewPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M124_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M124_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m124_metadata(validated.metadata)
    return validated


def validate_messages_connector_contract_review_record(
    record: MessagesConnectorContractReviewRecord,
) -> MessagesConnectorContractReviewRecord:
    payload = _model_payload(record)
    for field_name, reason in _M124_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MessagesConnectorContractReviewRecord):
        raise ValueError("SECRET_LIKE_M124_MESSAGES_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M124_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("messages_scope_refs", "M124_MESSAGES_SCOPE_REF_REQUIRED"),
        ("messages_boundary_refs", "M124_MESSAGES_BOUNDARY_REF_REQUIRED"),
        ("message_thread_boundary_refs", "M124_MESSAGE_THREAD_BOUNDARY_REF_REQUIRED"),
        ("consent_boundary_refs", "M124_CONSENT_BOUNDARY_REF_REQUIRED"),
        ("data_classification_refs", "M124_DATA_CLASSIFICATION_REF_REQUIRED"),
        ("retention_boundary_refs", "M124_RETENTION_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_contacts_connector_contract_refresh_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_contacts_connector_contract_refresh_record(
        source_record
    )
    validated = MessagesConnectorContractReviewRecord.model_validate(payload)
    for field_name, reason in _M124_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != MessagesConnectorContractReviewStatus.messages_connector_contract_review
    ):
        raise ValueError("M124_MESSAGES_CONNECTOR_CONTRACT_REVIEW_STATUS_REQUIRED")
    for field_name, reason in _M124_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m124_bindings(validated, validated_source)
    _validate_m124_metadata(validated.metadata)
    return validated


def _coerce_source_contacts_connector_contract_refresh_record(
    value: Any,
) -> ContactsConnectorContractRefreshRecord:
    if isinstance(value, ContactsConnectorContractRefreshRecord):
        return value
    if isinstance(value, dict):
        return ContactsConnectorContractRefreshRecord.model_validate(value)
    raise ValueError("M124_SOURCE_RECORD_REQUIRED")


def _validate_source_contacts_connector_contract_refresh_record(
    source_record: ContactsConnectorContractRefreshRecord,
) -> ContactsConnectorContractRefreshRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M124_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_contacts_connector_contract_refresh_record(source_record)


def _validate_m124_bindings(
    record: MessagesConnectorContractReviewRecord,
    source_record: ContactsConnectorContractRefreshRecord,
) -> None:
    if (
        record.source_contacts_connector_contract_refresh_ref
        != source_record.contacts_connector_contract_refresh_ref
    ):
        raise ValueError(
            "M124_SOURCE_CONTACTS_CONNECTOR_CONTRACT_REFRESH_BINDING_MISMATCH"
        )
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M124_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M124_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M124_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M124_WORKSPACE_BINDING_MISMATCH")
    if (
        record.messages_connector_contract_review_ref
        != "messages-connector-contract-review:m124"
    ):
        raise ValueError("M124_MESSAGES_CONNECTOR_CONTRACT_REVIEW_REF_REQUIRED")
    for ref in record.messages_scope_refs:
        if not ref.startswith("messages-scope-ref:"):
            raise ValueError("M124_MESSAGES_SCOPE_REF_REQUIRED")
    for ref in record.messages_boundary_refs:
        if not ref.startswith("messages-boundary-ref:"):
            raise ValueError("M124_MESSAGES_BOUNDARY_REF_REQUIRED")
    for ref in record.message_thread_boundary_refs:
        if not ref.startswith("message-thread-boundary-ref:"):
            raise ValueError("M124_MESSAGE_THREAD_BOUNDARY_REF_REQUIRED")
    for ref in record.consent_boundary_refs:
        if not ref.startswith("consent-boundary-ref:"):
            raise ValueError("M124_CONSENT_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M124_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m123" not in record.accepted_checkpoint_refs:
        raise ValueError("M124_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M124_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m124_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M124_MESSAGES_CONTENT_DENIED") from exc


_M124_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M124_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M124_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M124_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M124_BASELINE_BINDING_REQUIRED"),
    (
        "source_contacts_connector_contract_refresh_binding_required",
        "M124_SOURCE_CONTACTS_CONNECTOR_CONTRACT_REFRESH_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M124_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M124_WORKSPACE_BINDING_REQUIRED"),
    ("messages_scope_binding_required", "M124_MESSAGES_SCOPE_BINDING_REQUIRED"),
    ("messages_boundary_binding_required", "M124_MESSAGES_BOUNDARY_BINDING_REQUIRED"),
    ("message_thread_boundary_binding_required", "M124_MESSAGE_THREAD_BOUNDARY_BINDING_REQUIRED"),
    ("consent_boundary_binding_required", "M124_CONSENT_BOUNDARY_BINDING_REQUIRED"),
    (
        "data_classification_binding_required",
        "M124_DATA_CLASSIFICATION_BINDING_REQUIRED",
    ),
    ("retention_boundary_binding_required", "M124_RETENTION_BOUNDARY_BINDING_REQUIRED"),
    ("messages_scope_refs_required", "M124_MESSAGES_SCOPE_REF_REQUIRED"),
    ("messages_boundary_refs_required", "M124_MESSAGES_BOUNDARY_REF_REQUIRED"),
    ("message_thread_boundary_refs_required", "M124_MESSAGE_THREAD_BOUNDARY_REF_REQUIRED"),
    ("consent_boundary_refs_required", "M124_CONSENT_BOUNDARY_REF_REQUIRED"),
    ("data_classification_refs_required", "M124_DATA_CLASSIFICATION_REF_REQUIRED"),
    ("retention_boundary_refs_required", "M124_RETENTION_BOUNDARY_REF_REQUIRED"),
    ("audit_required", "M124_AUDIT_REQUIRED"),
    ("replay_required", "M124_REPLAY_REQUIRED"),
]

_M124_POLICY_DENIALS = [
    ("messages_connector_runtime_enabled", "MESSAGES_CONNECTOR_RUNTIME_DENIED"),
    ("messages_account_auth_enabled", "MESSAGES_ACCOUNT_AUTH_DENIED"),
    ("messages_read_enabled", "MESSAGES_READ_DENIED"),
    ("messages_search_enabled", "MESSAGES_SEARCH_DENIED"),
    ("messages_lookup_enabled", "MESSAGES_LOOKUP_DENIED"),
    ("messages_send_enabled", "MESSAGES_SEND_DENIED"),
    ("message_thread_access_enabled", "MESSAGE_THREAD_ACCESS_DENIED"),
    ("messages_create_enabled", "MESSAGES_CREATE_DENIED"),
    ("messages_update_enabled", "MESSAGES_UPDATE_DENIED"),
    ("messages_delete_enabled", "MESSAGES_DELETE_DENIED"),
    ("messages_export_enabled", "MESSAGES_EXPORT_DENIED"),
    ("messages_bulk_export_enabled", "MESSAGES_BULK_EXPORT_DENIED"),
    ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
    ("raw_messages_content_enabled", "RAW_MESSAGES_CONTENT_DENIED"),
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

_M124_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M124_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M124_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M124_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M124_BASELINE_BINDING_REQUIRED"),
    (
        "source_contacts_connector_contract_refresh_bound",
        "M124_SOURCE_CONTACTS_CONNECTOR_CONTRACT_REFRESH_BINDING_REQUIRED",
    ),
    ("user_bound", "M124_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M124_WORKSPACE_BINDING_REQUIRED"),
    ("messages_scope_bound", "M124_MESSAGES_SCOPE_BINDING_REQUIRED"),
    ("messages_boundary_bound", "M124_MESSAGES_BOUNDARY_BINDING_REQUIRED"),
    ("message_thread_boundary_bound", "M124_MESSAGE_THREAD_BOUNDARY_BINDING_REQUIRED"),
    ("consent_boundary_bound", "M124_CONSENT_BOUNDARY_BINDING_REQUIRED"),
    ("data_classification_bound", "M124_DATA_CLASSIFICATION_BINDING_REQUIRED"),
    ("retention_boundary_bound", "M124_RETENTION_BOUNDARY_BINDING_REQUIRED"),
    ("audit_required", "M124_AUDIT_REQUIRED"),
    ("replay_safe", "M124_REPLAY_REQUIRED"),
]

_M124_RECORD_DENIALS = [
    ("messages_connector_runtime_enabled", "MESSAGES_CONNECTOR_RUNTIME_DENIED"),
    ("messages_account_auth_enabled", "MESSAGES_ACCOUNT_AUTH_DENIED"),
    ("messages_read_enabled", "MESSAGES_READ_DENIED"),
    ("messages_search_enabled", "MESSAGES_SEARCH_DENIED"),
    ("messages_lookup_enabled", "MESSAGES_LOOKUP_DENIED"),
    ("messages_send_enabled", "MESSAGES_SEND_DENIED"),
    ("message_thread_access_enabled", "MESSAGE_THREAD_ACCESS_DENIED"),
    ("messages_create_enabled", "MESSAGES_CREATE_DENIED"),
    ("messages_update_enabled", "MESSAGES_UPDATE_DENIED"),
    ("messages_delete_enabled", "MESSAGES_DELETE_DENIED"),
    ("messages_export_enabled", "MESSAGES_EXPORT_DENIED"),
    ("messages_bulk_export_enabled", "MESSAGES_BULK_EXPORT_DENIED"),
    ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
    ("raw_messages_content_enabled", "RAW_MESSAGES_CONTENT_DENIED"),
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

_M124_SOURCE_DENIALS = [
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
