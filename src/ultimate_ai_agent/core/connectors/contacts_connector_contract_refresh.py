from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.connectors.calendar_connector_contract_refresh import (
    CalendarConnectorContractRefreshRecord,
    validate_calendar_connector_contract_refresh_record,
)


CONTACTS_CONNECTOR_CONTRACT_REFRESH_DOCS = [
    "docs/connectors/CONTACTS_CONNECTOR_CONTRACT_REFRESH.md",
    "docs/connectors/CONTACTS_CONNECTOR_AUTHORITY_BOUNDARY.md",
    "docs/connectors/CONTACTS_CONNECTOR_RECEIPT_PLAN.md",
    "docs/connectors/CONTACTS_CONNECTOR_NON_GOALS.md",
    "docs/connectors/M123_TO_M124_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class ContactsConnectorContractRefreshStatus(str, Enum):
    contacts_connector_contract_refresh = "contacts_connector_contract_refresh"


class _ContactsConnectorContractRefresh(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ContactsConnectorContractRefreshPolicy(_ContactsConnectorContractRefresh):
    policy_ref: str = "contacts-connector-contract-refresh-policy:m123"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    baseline_binding_required: bool = True
    source_calendar_connector_contract_refresh_binding_required: bool = True
    user_binding_required: bool = True
    workspace_binding_required: bool = True
    contacts_scope_binding_required: bool = True
    contacts_boundary_binding_required: bool = True
    contact_boundary_binding_required: bool = True
    consent_boundary_binding_required: bool = True
    data_classification_binding_required: bool = True
    retention_boundary_binding_required: bool = True
    contacts_scope_refs_required: bool = True
    contacts_boundary_refs_required: bool = True
    contact_boundary_refs_required: bool = True
    consent_boundary_refs_required: bool = True
    data_classification_refs_required: bool = True
    retention_boundary_refs_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    contacts_connector_runtime_enabled: bool = False
    contacts_account_auth_enabled: bool = False
    contacts_read_enabled: bool = False
    contacts_search_enabled: bool = False
    contacts_lookup_enabled: bool = False
    contacts_create_enabled: bool = False
    contacts_update_enabled: bool = False
    contacts_delete_enabled: bool = False
    contacts_export_enabled: bool = False
    contacts_bulk_export_enabled: bool = False
    raw_contacts_content_enabled: bool = False
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


class ContactsConnectorContractRefreshRecord(_ContactsConnectorContractRefresh):
    contacts_connector_contract_refresh_ref: str
    source_record: CalendarConnectorContractRefreshRecord
    source_calendar_connector_contract_refresh_ref: str
    source_baseline_ref: str
    actor_ref: str
    user_ref: str
    workspace_ref: str
    contacts_scope_refs: list[str]
    contacts_boundary_refs: list[str]
    contact_boundary_refs: list[str]
    consent_boundary_refs: list[str]
    data_classification_refs: list[str]
    retention_boundary_refs: list[str]
    audit_ref: str
    replay_ref: str
    accepted_checkpoint_refs: list[str]
    no_effect_receipt_plan_ref: str
    status: ContactsConnectorContractRefreshStatus = (
        ContactsConnectorContractRefreshStatus.contacts_connector_contract_refresh
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    baseline_bound: bool = True
    source_calendar_connector_contract_refresh_bound: bool = True
    user_bound: bool = True
    workspace_bound: bool = True
    contacts_scope_bound: bool = True
    contacts_boundary_bound: bool = True
    contact_boundary_bound: bool = True
    consent_boundary_bound: bool = True
    data_classification_bound: bool = True
    retention_boundary_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    contacts_connector_runtime_enabled: bool = False
    contacts_account_auth_enabled: bool = False
    contacts_read_enabled: bool = False
    contacts_search_enabled: bool = False
    contacts_lookup_enabled: bool = False
    contacts_create_enabled: bool = False
    contacts_update_enabled: bool = False
    contacts_delete_enabled: bool = False
    contacts_export_enabled: bool = False
    contacts_bulk_export_enabled: bool = False
    raw_contacts_content_enabled: bool = False
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
                self.contacts_connector_contract_refresh_ref,
                "contacts_connector_contract_refresh_ref",
            ),
            (
                self.source_calendar_connector_contract_refresh_ref,
                "source_calendar_connector_contract_refresh_ref",
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
            ("contacts_scope_ref", self.contacts_scope_refs),
            ("contacts_boundary_ref", self.contacts_boundary_refs),
            ("contact_boundary_ref", self.contact_boundary_refs),
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


def build_contacts_connector_contract_refresh_record(
    *,
    source_record: CalendarConnectorContractRefreshRecord,
    policy: ContactsConnectorContractRefreshPolicy | None = None,
) -> ContactsConnectorContractRefreshRecord:
    active_policy = validate_contacts_connector_contract_refresh_policy(
        policy or ContactsConnectorContractRefreshPolicy()
    )
    validated_source = _validate_source_calendar_connector_contract_refresh_record(
        _coerce_source_calendar_connector_contract_refresh_record(source_record)
    )
    record = ContactsConnectorContractRefreshRecord(
        contacts_connector_contract_refresh_ref="contacts-connector-contract-refresh:m123",
        source_record=validated_source,
        source_calendar_connector_contract_refresh_ref=(
            validated_source.calendar_connector_contract_refresh_ref
        ),
        source_baseline_ref=validated_source.source_baseline_ref,
        actor_ref=validated_source.actor_ref,
        user_ref=validated_source.user_ref,
        workspace_ref=validated_source.workspace_ref,
        contacts_scope_refs=[
            "contacts-scope-ref:m123:declared-contacts-boundary",
            "contacts-scope-ref:m123:metadata-preview-only",
            "contacts-scope-ref:m123:no-account-action",
        ],
        contacts_boundary_refs=[
            "contacts-boundary-ref:m123:declared-only",
            "contacts-boundary-ref:m123:no-contacts-access",
        ],
        contact_boundary_refs=[
            "contact-boundary-ref:m123:metadata-summary-only",
            "contact-boundary-ref:m123:no-contact-card-or-address-book-data",
        ],
        consent_boundary_refs=[
            "consent-boundary-ref:m123:future-exact-actor-resource",
            "consent-boundary-ref:m123:no-account-connection",
        ],
        data_classification_refs=[
            "data-classification-ref:m123:metadata-summary-only",
            "data-classification-ref:m123:no-contact-card",
        ],
        retention_boundary_refs=[
            "retention-boundary-ref:m123:no-contacts-storage",
            "retention-boundary-ref:m123:no-address-book-storage",
        ],
        audit_ref="audit-ref:m123:contacts-connector-contract-refresh",
        replay_ref="replay-ref:m123:contacts-connector-contract-refresh",
        accepted_checkpoint_refs=[
            *validated_source.accepted_checkpoint_refs,
            "checkpoint:m122",
        ],
        no_effect_receipt_plan_ref=(
            "receipt-plan-ref:m123:contacts-connector-contract-refresh:no-effect"
        ),
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        baseline_bound=active_policy.baseline_binding_required,
        source_calendar_connector_contract_refresh_bound=(
            active_policy.source_calendar_connector_contract_refresh_binding_required
        ),
        user_bound=active_policy.user_binding_required,
        workspace_bound=active_policy.workspace_binding_required,
        contacts_scope_bound=active_policy.contacts_scope_binding_required,
        contacts_boundary_bound=active_policy.contacts_boundary_binding_required,
        contact_boundary_bound=active_policy.contact_boundary_binding_required,
        consent_boundary_bound=active_policy.consent_boundary_binding_required,
        data_classification_bound=active_policy.data_classification_binding_required,
        retention_boundary_bound=active_policy.retention_boundary_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M123_CONTACTS_CONNECTOR_CONTRACT_REFRESH",
            "M123_CONTRACT_ONLY",
            "M123_REVIEW_ONLY",
            "M123_NO_CONTACTS_RUNTIME_OR_ACCOUNT_AUTH",
            "M124_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M123 records a contract-only and review-only contacts connector "
            "contract refresh using safe refs for contacts scope, contacts "
            "boundaries, contact boundaries, consent boundaries, data "
            "classification, retention, audit, replay, and a no-effect receipt "
            "plan. It grants no contacts runtime, no account connection, no "
            "contacts data access, no lookup, no create/update/delete, no "
            "address-book export, no network access, no credentials, no "
            "routes, no controls, no dependencies, and keeps M124 future."
        ),
    )
    return validate_contacts_connector_contract_refresh_record(record)


def validate_contacts_connector_contract_refresh_policy(
    policy: ContactsConnectorContractRefreshPolicy,
) -> ContactsConnectorContractRefreshPolicy:
    validated = ContactsConnectorContractRefreshPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M123_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M123_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m123_metadata(validated.metadata)
    return validated


def validate_contacts_connector_contract_refresh_record(
    record: ContactsConnectorContractRefreshRecord,
) -> ContactsConnectorContractRefreshRecord:
    payload = _model_payload(record)
    for field_name, reason in _M123_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, ContactsConnectorContractRefreshRecord):
        raise ValueError("SECRET_LIKE_M123_CONTACTS_CONTENT_DENIED")
    for field_name, reason in [
        ("accepted_checkpoint_refs", "M123_ACCEPTED_CHECKPOINT_REF_REQUIRED"),
        ("contacts_scope_refs", "M123_CONTACTS_SCOPE_REF_REQUIRED"),
        ("contacts_boundary_refs", "M123_CONTACTS_BOUNDARY_REF_REQUIRED"),
        ("contact_boundary_refs", "M123_CONTACT_BOUNDARY_REF_REQUIRED"),
        ("consent_boundary_refs", "M123_CONSENT_BOUNDARY_REF_REQUIRED"),
        ("data_classification_refs", "M123_DATA_CLASSIFICATION_REF_REQUIRED"),
        ("retention_boundary_refs", "M123_RETENTION_BOUNDARY_REF_REQUIRED"),
    ]:
        if not payload.get(field_name):
            raise ValueError(reason)
    source_record = _coerce_source_calendar_connector_contract_refresh_record(
        payload.get("source_record")
    )
    validated_source = _validate_source_calendar_connector_contract_refresh_record(
        source_record
    )
    validated = ContactsConnectorContractRefreshRecord.model_validate(payload)
    for field_name, reason in _M123_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if (
        validated.status
        != ContactsConnectorContractRefreshStatus.contacts_connector_contract_refresh
    ):
        raise ValueError("M123_CONTACTS_CONNECTOR_CONTRACT_REFRESH_STATUS_REQUIRED")
    for field_name, reason in _M123_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m123_bindings(validated, validated_source)
    _validate_m123_metadata(validated.metadata)
    return validated


def _coerce_source_calendar_connector_contract_refresh_record(
    value: Any,
) -> CalendarConnectorContractRefreshRecord:
    if isinstance(value, CalendarConnectorContractRefreshRecord):
        return value
    if isinstance(value, dict):
        return CalendarConnectorContractRefreshRecord.model_validate(value)
    raise ValueError("M123_SOURCE_RECORD_REQUIRED")


def _validate_source_calendar_connector_contract_refresh_record(
    source_record: CalendarConnectorContractRefreshRecord,
) -> CalendarConnectorContractRefreshRecord:
    source_payload = _model_payload(source_record)
    for field_name, reason in _M123_SOURCE_DENIALS:
        if source_payload.get(field_name):
            raise ValueError(reason)
    return validate_calendar_connector_contract_refresh_record(source_record)


def _validate_m123_bindings(
    record: ContactsConnectorContractRefreshRecord,
    source_record: CalendarConnectorContractRefreshRecord,
) -> None:
    if (
        record.source_calendar_connector_contract_refresh_ref
        != source_record.calendar_connector_contract_refresh_ref
    ):
        raise ValueError(
            "M123_SOURCE_CALENDAR_CONNECTOR_CONTRACT_REFRESH_BINDING_MISMATCH"
        )
    if record.source_baseline_ref != source_record.source_baseline_ref:
        raise ValueError("M123_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_record.actor_ref:
        raise ValueError("M123_ACTOR_BINDING_MISMATCH")
    if record.user_ref != source_record.user_ref:
        raise ValueError("M123_USER_BINDING_MISMATCH")
    if record.workspace_ref != source_record.workspace_ref:
        raise ValueError("M123_WORKSPACE_BINDING_MISMATCH")
    if (
        record.contacts_connector_contract_refresh_ref
        != "contacts-connector-contract-refresh:m123"
    ):
        raise ValueError("M123_CONTACTS_CONNECTOR_CONTRACT_REFRESH_REF_REQUIRED")
    for ref in record.contacts_scope_refs:
        if not ref.startswith("contacts-scope-ref:"):
            raise ValueError("M123_CONTACTS_SCOPE_REF_REQUIRED")
    for ref in record.contacts_boundary_refs:
        if not ref.startswith("contacts-boundary-ref:"):
            raise ValueError("M123_CONTACTS_BOUNDARY_REF_REQUIRED")
    for ref in record.contact_boundary_refs:
        if not ref.startswith("contact-boundary-ref:"):
            raise ValueError("M123_CONTACT_BOUNDARY_REF_REQUIRED")
    for ref in record.consent_boundary_refs:
        if not ref.startswith("consent-boundary-ref:"):
            raise ValueError("M123_CONSENT_BOUNDARY_REF_REQUIRED")
    if not record.no_effect_receipt_plan_ref.startswith("receipt-plan-ref:"):
        raise ValueError("M123_NO_EFFECT_RECEIPT_PLAN_REF_REQUIRED")
    if "checkpoint:m122" not in record.accepted_checkpoint_refs:
        raise ValueError("M123_ACCEPTED_CHECKPOINT_REF_REQUIRED")
    for checkpoint_ref in record.accepted_checkpoint_refs:
        if not checkpoint_ref.startswith("checkpoint:m"):
            raise ValueError("M123_ACCEPTED_CHECKPOINT_REF_REQUIRED")


def _validate_m123_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M123_CONTACTS_CONTENT_DENIED") from exc


_M123_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M123_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M123_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M123_ACTOR_BINDING_REQUIRED"),
    ("baseline_binding_required", "M123_BASELINE_BINDING_REQUIRED"),
    (
        "source_calendar_connector_contract_refresh_binding_required",
        "M123_SOURCE_CALENDAR_CONNECTOR_CONTRACT_REFRESH_BINDING_REQUIRED",
    ),
    ("user_binding_required", "M123_USER_BINDING_REQUIRED"),
    ("workspace_binding_required", "M123_WORKSPACE_BINDING_REQUIRED"),
    ("contacts_scope_binding_required", "M123_CONTACTS_SCOPE_BINDING_REQUIRED"),
    ("contacts_boundary_binding_required", "M123_CONTACTS_BOUNDARY_BINDING_REQUIRED"),
    ("contact_boundary_binding_required", "M123_CONTACT_BOUNDARY_BINDING_REQUIRED"),
    ("consent_boundary_binding_required", "M123_CONSENT_BOUNDARY_BINDING_REQUIRED"),
    (
        "data_classification_binding_required",
        "M123_DATA_CLASSIFICATION_BINDING_REQUIRED",
    ),
    ("retention_boundary_binding_required", "M123_RETENTION_BOUNDARY_BINDING_REQUIRED"),
    ("contacts_scope_refs_required", "M123_CONTACTS_SCOPE_REF_REQUIRED"),
    ("contacts_boundary_refs_required", "M123_CONTACTS_BOUNDARY_REF_REQUIRED"),
    ("contact_boundary_refs_required", "M123_CONTACT_BOUNDARY_REF_REQUIRED"),
    ("consent_boundary_refs_required", "M123_CONSENT_BOUNDARY_REF_REQUIRED"),
    ("data_classification_refs_required", "M123_DATA_CLASSIFICATION_REF_REQUIRED"),
    ("retention_boundary_refs_required", "M123_RETENTION_BOUNDARY_REF_REQUIRED"),
    ("audit_required", "M123_AUDIT_REQUIRED"),
    ("replay_required", "M123_REPLAY_REQUIRED"),
]

_M123_POLICY_DENIALS = [
    ("contacts_connector_runtime_enabled", "CONTACTS_CONNECTOR_RUNTIME_DENIED"),
    ("contacts_account_auth_enabled", "CONTACTS_ACCOUNT_AUTH_DENIED"),
    ("contacts_read_enabled", "CONTACTS_READ_DENIED"),
    ("contacts_search_enabled", "CONTACTS_SEARCH_DENIED"),
    ("contacts_lookup_enabled", "CONTACTS_LOOKUP_DENIED"),
    ("contacts_create_enabled", "CONTACTS_CREATE_DENIED"),
    ("contacts_update_enabled", "CONTACTS_UPDATE_DENIED"),
    ("contacts_delete_enabled", "CONTACTS_DELETE_DENIED"),
    ("contacts_export_enabled", "CONTACTS_EXPORT_DENIED"),
    ("contacts_bulk_export_enabled", "CONTACTS_BULK_EXPORT_DENIED"),
    ("raw_contacts_content_enabled", "RAW_CONTACTS_CONTENT_DENIED"),
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

_M123_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M123_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M123_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M123_ACTOR_BINDING_REQUIRED"),
    ("baseline_bound", "M123_BASELINE_BINDING_REQUIRED"),
    (
        "source_calendar_connector_contract_refresh_bound",
        "M123_SOURCE_CALENDAR_CONNECTOR_CONTRACT_REFRESH_BINDING_REQUIRED",
    ),
    ("user_bound", "M123_USER_BINDING_REQUIRED"),
    ("workspace_bound", "M123_WORKSPACE_BINDING_REQUIRED"),
    ("contacts_scope_bound", "M123_CONTACTS_SCOPE_BINDING_REQUIRED"),
    ("contacts_boundary_bound", "M123_CONTACTS_BOUNDARY_BINDING_REQUIRED"),
    ("contact_boundary_bound", "M123_CONTACT_BOUNDARY_BINDING_REQUIRED"),
    ("consent_boundary_bound", "M123_CONSENT_BOUNDARY_BINDING_REQUIRED"),
    ("data_classification_bound", "M123_DATA_CLASSIFICATION_BINDING_REQUIRED"),
    ("retention_boundary_bound", "M123_RETENTION_BOUNDARY_BINDING_REQUIRED"),
    ("audit_required", "M123_AUDIT_REQUIRED"),
    ("replay_safe", "M123_REPLAY_REQUIRED"),
]

_M123_RECORD_DENIALS = [
    ("contacts_connector_runtime_enabled", "CONTACTS_CONNECTOR_RUNTIME_DENIED"),
    ("contacts_account_auth_enabled", "CONTACTS_ACCOUNT_AUTH_DENIED"),
    ("contacts_read_enabled", "CONTACTS_READ_DENIED"),
    ("contacts_search_enabled", "CONTACTS_SEARCH_DENIED"),
    ("contacts_lookup_enabled", "CONTACTS_LOOKUP_DENIED"),
    ("contacts_create_enabled", "CONTACTS_CREATE_DENIED"),
    ("contacts_update_enabled", "CONTACTS_UPDATE_DENIED"),
    ("contacts_delete_enabled", "CONTACTS_DELETE_DENIED"),
    ("contacts_export_enabled", "CONTACTS_EXPORT_DENIED"),
    ("contacts_bulk_export_enabled", "CONTACTS_BULK_EXPORT_DENIED"),
    ("raw_contacts_content_enabled", "RAW_CONTACTS_CONTENT_DENIED"),
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

_M123_SOURCE_DENIALS = [
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
