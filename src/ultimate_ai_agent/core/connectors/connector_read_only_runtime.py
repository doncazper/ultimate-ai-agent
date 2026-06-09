from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.connectors.messages_connector_contract_review import (
    MessagesConnectorContractReviewRecord,
    validate_messages_connector_contract_review_record,
)


CONNECTOR_READ_ONLY_RUNTIME_DOCS = [
    "docs/connectors/CONNECTOR_READ_ONLY_RUNTIME.md",
    "docs/connectors/CONNECTOR_READ_ONLY_RUNTIME_AUTHORITY_BOUNDARY.md",
    "docs/connectors/CONNECTOR_READ_ONLY_RUNTIME_RECEIPT_PLAN.md",
    "docs/connectors/CONNECTOR_READ_ONLY_RUNTIME_NON_GOALS.md",
    "docs/connectors/M125_TO_M126_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ConnectorReadOnlyRuntimeStatus(str, Enum):
    connector_read_only_runtime_reviewed = "connector_read_only_runtime_reviewed"


class _ConnectorReadOnlyRuntime(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ConnectorReadOnlyRuntimePolicy(_ConnectorReadOnlyRuntime):
    policy_ref: str = "connector-read-only-runtime-policy:m125"
    read_only_runtime_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_messages_connector_contract_review_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    connector_scope_binding_required: bool = True
    connector_allowlist_binding_required: bool = True
    operation_allowlist_binding_required: bool = True
    data_minimization_binding_required: bool = True
    redaction_binding_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    live_connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    raw_connector_content_enabled: bool = False
    full_content_read_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_export_enabled: bool = False
    connector_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
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


class ConnectorReadOnlyRuntimeRecord(_ConnectorReadOnlyRuntime):
    connector_read_only_runtime_ref: str
    source_record: MessagesConnectorContractReviewRecord
    source_messages_connector_contract_review_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    connector_scope_refs: list[str]
    connector_allowlist_refs: list[str]
    operation_allowlist_refs: list[str]
    data_minimization_refs: list[str]
    redaction_refs: list[str]
    redacted_metadata_preview_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: ConnectorReadOnlyRuntimeStatus = (
        ConnectorReadOnlyRuntimeStatus.connector_read_only_runtime_reviewed
    )
    read_only_runtime: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_messages_connector_contract_review_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    connector_scope_bound: bool = True
    connector_allowlist_bound: bool = True
    operation_allowlist_bound: bool = True
    data_minimization_bound: bool = True
    redaction_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    live_connector_runtime_enabled: bool = False
    account_auth_enabled: bool = False
    network_access_enabled: bool = False
    credential_handling_enabled: bool = False
    raw_connector_content_enabled: bool = False
    full_content_read_enabled: bool = False
    connector_write_enabled: bool = False
    connector_send_enabled: bool = False
    connector_delete_enabled: bool = False
    connector_export_enabled: bool = False
    connector_bulk_export_enabled: bool = False
    attachment_download_enabled: bool = False
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
            (self.connector_read_only_runtime_ref, "connector_read_only_runtime_ref"),
            (
                self.source_messages_connector_contract_review_ref,
                "source_messages_connector_contract_review_ref",
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
            ("connector_scope_ref", self.connector_scope_refs),
            ("connector_allowlist_ref", self.connector_allowlist_refs),
            ("connector_operation_ref", self.operation_allowlist_refs),
            ("data_minimization_ref", self.data_minimization_refs),
            ("redaction_ref", self.redaction_refs),
            ("metadata_preview_ref", self.redacted_metadata_preview_refs),
            ("accepted_checkpoint_ref", self.accepted_checkpoint_refs),
        ]:
            for ref in refs:
                _validate_m61_ref(ref, field_name)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_connector_read_only_runtime_record(
    *,
    source_record: MessagesConnectorContractReviewRecord,
    policy: ConnectorReadOnlyRuntimePolicy | None = None,
) -> ConnectorReadOnlyRuntimeRecord:
    active_policy = validate_connector_read_only_runtime_policy(
        policy or ConnectorReadOnlyRuntimePolicy()
    )
    validated_source = _validate_source_messages_connector_contract_review_record(
        _coerce_source_messages_connector_contract_review_record(source_record)
    )
    record = ConnectorReadOnlyRuntimeRecord(
        connector_read_only_runtime_ref="connector-read-only-runtime:m125",
        source_record=validated_source,
        source_messages_connector_contract_review_ref=(
            validated_source.messages_connector_contract_review_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        connector_scope_refs=[
            "connector-scope-ref:m125:read-only-safe-metadata",
            "connector-scope-ref:m125:explicit-reviewed-connector-refs",
            "connector-scope-ref:m125:no-account-or-live-provider-access",
        ],
        connector_allowlist_refs=[
            "connector-allowlist-ref:m125:email-metadata-only",
            "connector-allowlist-ref:m125:calendar-metadata-only",
            "connector-allowlist-ref:m125:contacts-metadata-only",
            "connector-allowlist-ref:m125:messages-metadata-only",
        ],
        operation_allowlist_refs=[
            "connector-operation-ref:m125:list-safe-metadata",
            "connector-operation-ref:m125:get-safe-summary-by-ref",
        ],
        data_minimization_refs=[
            "data-minimization-ref:m125:metadata-summary-only",
            "data-minimization-ref:m125:no-body-content",
        ],
        redaction_refs=[
            "redaction-ref:m125:subject-and-body-omitted",
            "redaction-ref:m125:addresses-and-identifiers-safe-ref-only",
        ],
        redacted_metadata_preview_refs=[
            "metadata-preview-ref:m125:email-safe-summary",
            "metadata-preview-ref:m125:calendar-safe-summary",
            "metadata-preview-ref:m125:contacts-safe-summary",
            "metadata-preview-ref:m125:messages-safe-summary",
        ],
        audit_ref="audit-ref:m125:connector-read-only-runtime",
        replay_ref="replay-ref:m125:connector-read-only-runtime",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m124",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m125:connector-read-only-runtime:no-effect"
        ),
        read_only_runtime=active_policy.read_only_runtime_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_messages_connector_contract_review_bound=(
            active_policy.source_messages_connector_contract_review_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        connector_scope_bound=active_policy.connector_scope_binding_required,
        connector_allowlist_bound=active_policy.connector_allowlist_binding_required,
        operation_allowlist_bound=active_policy.operation_allowlist_binding_required,
        data_minimization_bound=active_policy.data_minimization_binding_required,
        redaction_bound=active_policy.redaction_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M125_CONNECTOR_READ_ONLY_RUNTIME",
            "M125_SAFE_METADATA_ONLY",
            "M125_NO_AUTH_NETWORK_RAW_CONTENT_OR_WRITES",
            "M126_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M125 records a deterministic read-only connector runtime contract "
            "over reviewed connector refs. It returns safe metadata preview refs "
            "and summaries only. It grants no live connector runtime, no account "
            "connection, no network access, no credentials, no connector content, "
            "no full content read, no write, no send, no delete, no export, no "
            "attachment retrieval, no routes, no controls, no dependencies, and "
            "keeps M126 future."
        ),
    )
    return validate_connector_read_only_runtime_record(record)


def validate_connector_read_only_runtime_policy(
    policy: ConnectorReadOnlyRuntimePolicy,
) -> ConnectorReadOnlyRuntimePolicy:
    validated = ConnectorReadOnlyRuntimePolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M125_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M125_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m125_metadata(validated.metadata)
    return validated


def validate_connector_read_only_runtime_record(
    record: ConnectorReadOnlyRuntimeRecord,
) -> ConnectorReadOnlyRuntimeRecord:
    payload = _model_payload(record)
    for field_name, reason in _M125_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, ConnectorReadOnlyRuntimeRecord):
        raise ValueError("SECRET_LIKE_M125_CONNECTOR_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M125_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("connector_scope_refs", "M125_CONNECTOR_SCOPE_REF_REQUIRED"),
        ("connector_allowlist_refs", "M125_CONNECTOR_ALLOWLIST_REF_REQUIRED"),
        ("operation_allowlist_refs", "M125_OPERATION_ALLOWLIST_REF_REQUIRED"),
        ("data_minimization_refs", "M125_DATA_MINIMIZATION_REF_REQUIRED"),
        ("redaction_refs", "M125_REDACTION_REF_REQUIRED"),
        ("redacted_metadata_preview_refs", "M125_METADATA_PREVIEW_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_messages_connector_contract_review_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_messages_connector_contract_review_record(
        source_record
    )
    validated = ConnectorReadOnlyRuntimeRecord.model_validate(payload)
    for field_name, reason in _M125_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != ConnectorReadOnlyRuntimeStatus.connector_read_only_runtime_reviewed
    ):
        raise ValueError("M125_CONNECTOR_READ_ONLY_RUNTIME_STATUS_REQUIRED")
    for field_name, reason in _M125_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m125_safe_summary(validated.safe_summary)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m125_bindings(validated, validated_source)
    _validate_m125_metadata(validated.metadata)
    return validated


def _coerce_source_messages_connector_contract_review_record(
    value: Any,
) -> MessagesConnectorContractReviewRecord:
    if isinstance(value, MessagesConnectorContractReviewRecord):
        return value
    if isinstance(value, dict):
        return MessagesConnectorContractReviewRecord.model_validate(value)
    raise ValueError("M125_SOURCE_RECORD_REQUIRED")


def _validate_source_messages_connector_contract_review_record(
    source_record: MessagesConnectorContractReviewRecord,
) -> MessagesConnectorContractReviewRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M125_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_messages_connector_contract_review_record(source_record)


def _validate_m125_bindings(
    record: ConnectorReadOnlyRuntimeRecord,
    source_record: MessagesConnectorContractReviewRecord,
) -> None:
    if (
        record.source_messages_connector_contract_review_ref
        != source_record.messages_connector_contract_review_ref
    ):
        raise ValueError(
            "M125_SOURCE_MESSAGES_CONNECTOR_CONTRACT_REVIEW_REF_MISMATCH"
        )
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M125_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M125_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M125_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M125_WORKSPACE_BINDING_MISMATCH")
    if record.connector_read_only_runtime_ref != "connector-read-only-runtime:m125":
        raise ValueError("M125_CONNECTOR_READ_ONLY_RUNTIME_REF_REQUIRED")
    for ref in record.connector_scope_refs:
        if not ref.startswith("connector-scope-ref:"):
            raise ValueError("M125_CONNECTOR_SCOPE_REF_REQUIRED")
    for ref in record.connector_allowlist_refs:
        if not ref.startswith("connector-allowlist-ref:"):
            raise ValueError("M125_CONNECTOR_ALLOWLIST_REF_REQUIRED")
    for ref in record.operation_allowlist_refs:
        if not ref.startswith("connector-operation-ref:"):
            raise ValueError("M125_OPERATION_ALLOWLIST_REF_REQUIRED")
    for ref in record.data_minimization_refs:
        if not ref.startswith("data-minimization-ref:"):
            raise ValueError("M125_DATA_MINIMIZATION_REF_REQUIRED")
    for ref in record.redaction_refs:
        if not ref.startswith("redaction-ref:"):
            raise ValueError("M125_REDACTION_REF_REQUIRED")
    for ref in record.redacted_metadata_preview_refs:
        if not ref.startswith("metadata-preview-ref:m125:"):
            raise ValueError("M125_METADATA_PREVIEW_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M125_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m124" not in record.accepted_checkpoint_refs:
        raise ValueError("M125_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M125_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m125_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M125_CONNECTOR_CONTENT_DENIED") from exc


def _validate_m125_safe_summary(summary: str) -> None:
    lowered = summary.lower()
    for fragment in [
        "raw email",
        "raw calendar",
        "raw contact",
        "raw message",
        "message body",
        "email body",
        "calendar body",
        "contact body",
        "download attachment",
        "bulk export",
    ]:
        if fragment in lowered:
            raise ValueError("SAFE_PAYLOAD_UNSAFE")


_M125_POLICY_REQUIRED_TRUE = [
    ("read_only_runtime_required", "M125_READ_ONLY_RUNTIME_REQUIRED"),
    ("safe_refs_required", "M125_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M125_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M125_BASELINE_BINDING_REQUIRED"),
    (
        "source_messages_connector_contract_review_binding_required",
        "M125_SOURCE_MESSAGES_CONNECTOR_CONTRACT_REVIEW_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M125_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M125_WORKSPACE_BINDING_REQUIRED"),
    ("connector_scope_binding_required", "M125_CONNECTOR_SCOPE_BINDING_REQUIRED"),
    (
        "connector_allowlist_binding_required",
        "M125_CONNECTOR_ALLOWLIST_BINDING_REQUIRED",
    ),
    (
        "operation_allowlist_binding_required",
        "M125_OPERATION_ALLOWLIST_BINDING_REQUIRED",
    ),
    ("data_minimization_binding_required", "M125_DATA_MINIMIZATION_BINDING_REQUIRED"),
    ("redaction_binding_required", "M125_REDACTION_BINDING_REQUIRED"),
    ("audit_required", "M125_AUDIT_REQUIRED"),
    ("replay_required", "M125_REPLAY_REQUIRED"),
]

_M125_POLICY_DENIALS = [
    ("live_connector_runtime_enabled", "LIVE_CONNECTOR_RUNTIME_DENIED"),
    ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("raw_connector_content_enabled", "RAW_CONNECTOR_CONTENT_DENIED"),
    ("full_content_read_enabled", "FULL_CONTENT_READ_DENIED"),
    ("connector_write_enabled", "CONNECTOR_WRITE_DENIED"),
    ("connector_send_enabled", "CONNECTOR_SEND_DENIED"),
    ("connector_delete_enabled", "CONNECTOR_DELETE_DENIED"),
    ("connector_export_enabled", "CONNECTOR_EXPORT_DENIED"),
    ("connector_bulk_export_enabled", "CONNECTOR_BULK_EXPORT_DENIED"),
    ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M125_RECORD_REQUIRED_TRUE = [
    ("read_only_runtime", "M125_READ_ONLY_RUNTIME_REQUIRED"),
    ("safe_refs_required", "M125_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M125_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M125_BASELINE_BINDING_REQUIRED"),
    (
        "source_messages_connector_contract_review_bound",
        "M125_SOURCE_MESSAGES_CONNECTOR_CONTRACT_REVIEW_BINDING_REQUIRED",
    ),
    ("user_bound", "M125_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M125_WORKSPACE_BINDING_REQUIRED"),
    ("connector_scope_bound", "M125_CONNECTOR_SCOPE_BINDING_REQUIRED"),
    ("connector_allowlist_bound", "M125_CONNECTOR_ALLOWLIST_BINDING_REQUIRED"),
    ("operation_allowlist_bound", "M125_OPERATION_ALLOWLIST_BINDING_REQUIRED"),
    ("data_minimization_bound", "M125_DATA_MINIMIZATION_BINDING_REQUIRED"),
    ("redaction_bound", "M125_REDACTION_BINDING_REQUIRED"),
    ("audit_required", "M125_AUDIT_REQUIRED"),
    ("replay_safe", "M125_REPLAY_REQUIRED"),
]

_M125_RECORD_DENIALS = [
    ("live_connector_runtime_enabled", "LIVE_CONNECTOR_RUNTIME_DENIED"),
    ("account_auth_enabled", "ACCOUNT_AUTH_DENIED"),
    ("network_access_enabled", "NETWORK_ACCESS_DENIED"),
    ("credential_handling_enabled", "CREDENTIAL_HANDLING_DENIED"),
    ("raw_connector_content_enabled", "RAW_CONNECTOR_CONTENT_DENIED"),
    ("full_content_read_enabled", "FULL_CONTENT_READ_DENIED"),
    ("connector_write_enabled", "CONNECTOR_WRITE_DENIED"),
    ("connector_send_enabled", "CONNECTOR_SEND_DENIED"),
    ("connector_delete_enabled", "CONNECTOR_DELETE_DENIED"),
    ("connector_export_enabled", "CONNECTOR_EXPORT_DENIED"),
    ("connector_bulk_export_enabled", "CONNECTOR_BULK_EXPORT_DENIED"),
    ("attachment_download_enabled", "ATTACHMENT_DOWNLOAD_DENIED"),
    ("model_call_enabled", "MODEL_CALL_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_DENIED"),
]

_M125_SOURCE_DENIALS = [
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
