from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.connectors.email_connector_contract_refresh import (
    EmailConnectorContractRefreshRecord,
    validate_email_connector_contract_refresh_record,
)


CALENDAR_CONNECTOR_CONTRACT_REFRESH_DOCS = [
    "docs/connectors/CALENDAR_CONNECTOR_CONTRACT_REFRESH.md",
    "docs/connectors/CALENDAR_CONNECTOR_AUTHORITY_BOUNDARY.md",
    "docs/connectors/CALENDAR_CONNECTOR_RECEIPT_PLAN.md",
    "docs/connectors/CALENDAR_CONNECTOR_NON_GOALS.md",
    "docs/connectors/M122_TO_M123_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class CalendarConnectorContractRefreshStatus(str, Enum):
    calendar_connector_contract_refresh = "calendar_connector_contract_refresh"


class _CalendarConnectorContractRefresh(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class CalendarConnectorContractRefreshPolicy(_CalendarConnectorContractRefresh):
    policy_ref: str = "calendar-connector-contract-refresh-policy:m122"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_email_connector_contract_refresh_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    calendar_scope_binding_required: bool = True
    calendar_boundary_binding_required: bool = True
    event_boundary_binding_required: bool = True
    consent_boundary_binding_required: bool = True
    data_classification_binding_required: bool = True
    retention_boundary_binding_required: bool = True
    calendar_scope_refs_required: bool = True
    calendar_boundary_refs_required: bool = True
    event_boundary_refs_required: bool = True
    consent_boundary_refs_required: bool = True
    data_classification_refs_required: bool = True
    retention_boundary_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    calendar_connector_runtime_enabled: bool = False
    calendar_account_auth_enabled: bool = False
    calendar_read_enabled: bool = False
    calendar_search_enabled: bool = False
    calendar_event_create_enabled: bool = False
    calendar_event_update_enabled: bool = False
    calendar_event_delete_enabled: bool = False
    calendar_invite_send_enabled: bool = False
    calendar_attachment_download_enabled: bool = False
    raw_calendar_content_enabled: bool = False
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


class CalendarConnectorContractRefreshRecord(_CalendarConnectorContractRefresh):
    calendar_connector_contract_refresh_ref: str
    source_record: EmailConnectorContractRefreshRecord
    source_email_connector_contract_refresh_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    calendar_scope_refs: list[str]
    calendar_boundary_refs: list[str]
    event_boundary_refs: list[str]
    consent_boundary_refs: list[str]
    data_classification_refs: list[str]
    retention_boundary_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: CalendarConnectorContractRefreshStatus = (
        CalendarConnectorContractRefreshStatus.calendar_connector_contract_refresh
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_email_connector_contract_refresh_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    calendar_scope_bound: bool = True
    calendar_boundary_bound: bool = True
    event_boundary_bound: bool = True
    consent_boundary_bound: bool = True
    data_classification_bound: bool = True
    retention_boundary_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    calendar_connector_runtime_enabled: bool = False
    calendar_account_auth_enabled: bool = False
    calendar_read_enabled: bool = False
    calendar_search_enabled: bool = False
    calendar_event_create_enabled: bool = False
    calendar_event_update_enabled: bool = False
    calendar_event_delete_enabled: bool = False
    calendar_invite_send_enabled: bool = False
    calendar_attachment_download_enabled: bool = False
    raw_calendar_content_enabled: bool = False
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
                self.calendar_connector_contract_refresh_ref,
                "calendar_connector_contract_refresh_ref",
            ),
            (
                self.source_email_connector_contract_refresh_ref,
                "source_email_connector_contract_refresh_ref",
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
            ("calendar_scope_ref", self.calendar_scope_refs),
            ("calendar_boundary_ref", self.calendar_boundary_refs),
            ("event_boundary_ref", self.event_boundary_refs),
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


def build_calendar_connector_contract_refresh_record(
    *,
    source_record: EmailConnectorContractRefreshRecord,
    policy: CalendarConnectorContractRefreshPolicy | None = None,
) -> CalendarConnectorContractRefreshRecord:
    active_policy = validate_calendar_connector_contract_refresh_policy(
        policy or CalendarConnectorContractRefreshPolicy()
    )
    validated_source = _validate_source_email_connector_contract_refresh_record(
        _coerce_source_email_connector_contract_refresh_record(source_record)
    )
    record = CalendarConnectorContractRefreshRecord(
        calendar_connector_contract_refresh_ref="calendar-connector-contract-refresh:m122",
        source_record=validated_source,
        source_email_connector_contract_refresh_ref=(
            validated_source.email_connector_contract_refresh_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        calendar_scope_refs=[
            "calendar-scope-ref:m122:declared-calendar-boundary",
            "calendar-scope-ref:m122:metadata-preview-only",
            "calendar-scope-ref:m122:no-account-action",
        ],
        calendar_boundary_refs=[
            "calendar-boundary-ref:m122:declared-only",
            "calendar-boundary-ref:m122:no-calendar-access",
        ],
        event_boundary_refs=[
            "event-boundary-ref:m122:metadata-summary-only",
            "event-boundary-ref:m122:no-event-body-or-attendee-data",
        ],
        consent_boundary_refs=[
            "consent-boundary-ref:m122:future-exact-actor-resource",
            "consent-boundary-ref:m122:no-account-connection",
        ],
        data_classification_refs=[
            "data-classification-ref:m122:metadata-summary-only",
            "data-classification-ref:m122:no-message-body",
        ],
        retention_boundary_refs=[
            "retention-boundary-ref:m122:no-calendar-storage",
            "retention-boundary-ref:m122:no-attachment-storage",
        ],
        audit_ref="audit-ref:m122:calendar-connector-contract-refresh",
        replay_ref="replay-ref:m122:calendar-connector-contract-refresh",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m121",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m122:calendar-connector-contract-refresh:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_email_connector_contract_refresh_bound=(
            active_policy.source_email_connector_contract_refresh_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        calendar_scope_bound=active_policy.calendar_scope_binding_required,
        calendar_boundary_bound=active_policy.calendar_boundary_binding_required,
        event_boundary_bound=active_policy.event_boundary_binding_required,
        consent_boundary_bound=active_policy.consent_boundary_binding_required,
        data_classification_bound=active_policy.data_classification_binding_required,
        retention_boundary_bound=active_policy.retention_boundary_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M122_CALENDAR_CONNECTOR_CONTRACT_REFRESH",
            "M122_CONTRACT_ONLY",
            "M122_REVIEW_ONLY",
            "M122_NO_CALENDAR_RUNTIME_OR_ACCOUNT_AUTH",
            "M123_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M122 records a contract-only and review-only calendar connector "
            "contract refresh using safe refs for calendar scope, calendar "
            "boundaries, event boundaries, consent boundaries, data "
            "classification, retention, audit, replay, and a no-effect receipt "
            "plan. It grants no calendar runtime, no account connection, no "
            "calendar data access, no event mutation, no invite delivery, no "
            "network access, no credentials, no routes, no controls, no "
            "dependencies, and keeps M123 future."
        ),
    )
    return validate_calendar_connector_contract_refresh_record(record)


def validate_calendar_connector_contract_refresh_policy(
    policy: CalendarConnectorContractRefreshPolicy,
) -> CalendarConnectorContractRefreshPolicy:
    validated = CalendarConnectorContractRefreshPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M122_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M122_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m122_metadata(validated.metadata)
    return validated


def validate_calendar_connector_contract_refresh_record(
    record: CalendarConnectorContractRefreshRecord,
) -> CalendarConnectorContractRefreshRecord:
    payload = _model_payload(record)
    for field_name, reason in _M122_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, CalendarConnectorContractRefreshRecord):
        raise ValueError("SECRET_LIKE_M122_CALENDAR_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M122_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("calendar_scope_refs", "M122_CALENDAR_SCOPE_REF_REQUIRED"),
        ("calendar_boundary_refs", "M122_CALENDAR_BOUNDARY_REF_REQUIRED"),
        ("event_boundary_refs", "M122_EVENT_BOUNDARY_REF_REQUIRED"),
        ("consent_boundary_refs", "M122_CONSENT_BOUNDARY_REF_REQUIRED"),
        ("data_classification_refs", "M122_DATA_CLASSIFICATION_REF_REQUIRED"),
        ("retention_boundary_refs", "M122_RETENTION_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_email_connector_contract_refresh_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_email_connector_contract_refresh_record(
        source_record
    )
    validated = CalendarConnectorContractRefreshRecord.model_validate(payload)
    for field_name, reason in _M122_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != CalendarConnectorContractRefreshStatus.calendar_connector_contract_refresh
    ):
        raise ValueError("M122_CALENDAR_CONNECTOR_CONTRACT_REFRESH_STATUS_REQUIRED")
    for field_name, reason in _M122_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m122_bindings(validated, validated_source)
    _validate_m122_metadata(validated.metadata)
    return validated


def _coerce_source_email_connector_contract_refresh_record(
    value: Any,
) -> EmailConnectorContractRefreshRecord:
    if isinstance(value, EmailConnectorContractRefreshRecord):
        return value
    if isinstance(value, dict):
        return EmailConnectorContractRefreshRecord.model_validate(value)
    raise ValueError("M122_SOURCE_RECORD_REQUIRED")


def _validate_source_email_connector_contract_refresh_record(
    source_record: EmailConnectorContractRefreshRecord,
) -> EmailConnectorContractRefreshRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M122_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_email_connector_contract_refresh_record(source_record)


def _validate_m122_bindings(
    record: CalendarConnectorContractRefreshRecord,
    source_record: EmailConnectorContractRefreshRecord,
) -> None:
    if (
        record.source_email_connector_contract_refresh_ref
        != source_record.email_connector_contract_refresh_ref
    ):
        raise ValueError(
            "M122_SOURCE_EMAIL_CONNECTOR_CONTRACT_REFRESH_BINDING_MISMATCH"
        )
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M122_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M122_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M122_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M122_WORKSPACE_BINDING_MISMATCH")
    if (
        record.calendar_connector_contract_refresh_ref
        != "calendar-connector-contract-refresh:m122"
    ):
        raise ValueError("M122_CALENDAR_CONNECTOR_CONTRACT_REFRESH_REF_REQUIRED")
    for ref in record.calendar_scope_refs:
        if not ref.startswith("calendar-scope-ref:"):
            raise ValueError("M122_CALENDAR_SCOPE_REF_REQUIRED")
    for ref in record.calendar_boundary_refs:
        if not ref.startswith("calendar-boundary-ref:"):
            raise ValueError("M122_CALENDAR_BOUNDARY_REF_REQUIRED")
    for ref in record.event_boundary_refs:
        if not ref.startswith("event-boundary-ref:"):
            raise ValueError("M122_EVENT_BOUNDARY_REF_REQUIRED")
    for ref in record.consent_boundary_refs:
        if not ref.startswith("consent-boundary-ref:"):
            raise ValueError("M122_CONSENT_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M122_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m121" not in record.accepted_checkpoint_refs:
        raise ValueError("M122_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M122_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m122_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M122_CALENDAR_CONTENT_DENIED") from exc


_M122_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M122_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M122_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M122_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M122_BASELINE_BINDING_REQUIRED"),
    (
        "source_email_connector_contract_refresh_binding_required",
        "M122_SOURCE_EMAIL_CONNECTOR_CONTRACT_REFRESH_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M122_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M122_WORKSPACE_BINDING_REQUIRED"),
    ("calendar_scope_binding_required", "M122_CALENDAR_SCOPE_BINDING_REQUIRED"),
    ("calendar_boundary_binding_required", "M122_CALENDAR_BOUNDARY_BINDING_REQUIRED"),
    ("event_boundary_binding_required", "M122_EVENT_BOUNDARY_BINDING_REQUIRED"),
    ("consent_boundary_binding_required", "M122_CONSENT_BOUNDARY_BINDING_REQUIRED"),
    (
        "data_classification_binding_required",
        "M122_DATA_CLASSIFICATION_BINDING_REQUIRED",
    ),
    ("retention_boundary_binding_required", "M122_RETENTION_BOUNDARY_BINDING_REQUIRED"),
    ("calendar_scope_refs_required", "M122_CALENDAR_SCOPE_REF_REQUIRED"),
    ("calendar_boundary_refs_required", "M122_CALENDAR_BOUNDARY_REF_REQUIRED"),
    ("event_boundary_refs_required", "M122_EVENT_BOUNDARY_REF_REQUIRED"),
    ("consent_boundary_refs_required", "M122_CONSENT_BOUNDARY_REF_REQUIRED"),
    ("data_classification_refs_required", "M122_DATA_CLASSIFICATION_REF_REQUIRED"),
    ("retention_boundary_refs_required", "M122_RETENTION_BOUNDARY_REF_REQUIRED"),
    ("audit_required", "M122_AUDIT_REQUIRED"),
    ("replay_required", "M122_REPLAY_REQUIRED"),
]

_M122_POLICY_DENIALS = [
    ("calendar_connector_runtime_enabled", "CALENDAR_CONNECTOR_RUNTIME_DENIED"),
    ("calendar_account_auth_enabled", "CALENDAR_ACCOUNT_AUTH_DENIED"),
    ("calendar_read_enabled", "CALENDAR_READ_DENIED"),
    ("calendar_search_enabled", "CALENDAR_SEARCH_DENIED"),
    ("calendar_event_create_enabled", "CALENDAR_EVENT_CREATE_DENIED"),
    ("calendar_event_update_enabled", "CALENDAR_EVENT_UPDATE_DENIED"),
    ("calendar_event_delete_enabled", "CALENDAR_EVENT_DELETE_DENIED"),
    ("calendar_invite_send_enabled", "CALENDAR_INVITE_SEND_DENIED"),
    ("calendar_attachment_download_enabled", "CALENDAR_ATTACHMENT_DOWNLOAD_DENIED"),
    ("raw_calendar_content_enabled", "RAW_CALENDAR_CONTENT_DENIED"),
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

_M122_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M122_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M122_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M122_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M122_BASELINE_BINDING_REQUIRED"),
    (
        "source_email_connector_contract_refresh_bound",
        "M122_SOURCE_EMAIL_CONNECTOR_CONTRACT_REFRESH_BINDING_REQUIRED",
    ),
    ("user_bound", "M122_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M122_WORKSPACE_BINDING_REQUIRED"),
    ("calendar_scope_bound", "M122_CALENDAR_SCOPE_BINDING_REQUIRED"),
    ("calendar_boundary_bound", "M122_CALENDAR_BOUNDARY_BINDING_REQUIRED"),
    ("event_boundary_bound", "M122_EVENT_BOUNDARY_BINDING_REQUIRED"),
    ("consent_boundary_bound", "M122_CONSENT_BOUNDARY_BINDING_REQUIRED"),
    ("data_classification_bound", "M122_DATA_CLASSIFICATION_BINDING_REQUIRED"),
    ("retention_boundary_bound", "M122_RETENTION_BOUNDARY_BINDING_REQUIRED"),
    ("audit_required", "M122_AUDIT_REQUIRED"),
    ("replay_safe", "M122_REPLAY_REQUIRED"),
]

_M122_RECORD_DENIALS = [
    ("calendar_connector_runtime_enabled", "CALENDAR_CONNECTOR_RUNTIME_DENIED"),
    ("calendar_account_auth_enabled", "CALENDAR_ACCOUNT_AUTH_DENIED"),
    ("calendar_read_enabled", "CALENDAR_READ_DENIED"),
    ("calendar_search_enabled", "CALENDAR_SEARCH_DENIED"),
    ("calendar_event_create_enabled", "CALENDAR_EVENT_CREATE_DENIED"),
    ("calendar_event_update_enabled", "CALENDAR_EVENT_UPDATE_DENIED"),
    ("calendar_event_delete_enabled", "CALENDAR_EVENT_DELETE_DENIED"),
    ("calendar_invite_send_enabled", "CALENDAR_INVITE_SEND_DENIED"),
    ("calendar_attachment_download_enabled", "CALENDAR_ATTACHMENT_DOWNLOAD_DENIED"),
    ("raw_calendar_content_enabled", "RAW_CALENDAR_CONTENT_DENIED"),
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

_M122_SOURCE_DENIALS = [
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
