from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


MOBILE_PERMISSION_MODEL_V1_DOCS = [
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_POLICY.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_CONSENT_REVOCATION.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_PRIVACY_COPY.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_AUDIT.md",
    "docs/mobile/MOBILE_PERMISSION_MODEL_V1_NON_GOALS.md",
    "docs/mobile/M100_FINAL_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]


class MobilePermissionCategory(str, Enum):
    camera = "camera"
    microphone = "microphone"
    location = "location"
    photos = "photos"
    files = "files"
    contacts = "contacts"
    calendar = "calendar"
    bluetooth = "bluetooth"
    nfc = "nfc"
    biometrics = "biometrics"
    notifications = "notifications"
    background_refresh = "background_refresh"
    clipboard = "clipboard"
    local_network = "local_network"
    motion_activity = "motion_activity"


class MobilePermissionModelV1Status(str, Enum):
    contract_only = "contract_only"


class _MobilePermissionModelV1Model(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobilePermissionModelV1Policy(_MobilePermissionModelV1Model):
    policy_ref: str = "mobile-permission-model-v1-policy:m100"
    contract_only: bool = True
    permission_taxonomy_required: bool = True
    consent_model_required: bool = True
    revocation_model_required: bool = True
    privacy_copy_required: bool = True
    permission_audit_required: bool = True
    sensors_remain_off_required: bool = True
    no_background_collection_required: bool = True
    runtime_permission_prompts_enabled: bool = False
    native_permission_requests_enabled: bool = False
    mobile_sensor_enabled: bool = False
    location_access_enabled: bool = False
    camera_access_enabled: bool = False
    photos_access_enabled: bool = False
    microphone_access_enabled: bool = False
    contacts_access_enabled: bool = False
    calendar_access_enabled: bool = False
    bluetooth_access_enabled: bool = False
    nfc_access_enabled: bool = False
    biometrics_access_enabled: bool = False
    clipboard_access_enabled: bool = False
    local_network_access_enabled: bool = False
    motion_activity_access_enabled: bool = False
    background_collection_enabled: bool = False
    push_execution_enabled: bool = False
    credential_cookie_access_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    backend_route_enabled: bool = False
    dependency_change_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MobilePermissionTaxonomyEntry(_MobilePermissionModelV1Model):
    permission_ref: str
    category: MobilePermissionCategory
    safe_label: str
    safe_privacy_copy: str
    planned_disabled: bool = True
    requires_explicit_consent: bool = True
    revocable: bool = True
    audit_required: bool = True
    runtime_prompt_enabled: bool = False
    native_permission_request_enabled: bool = False
    sensor_access_enabled: bool = False
    background_collection_enabled: bool = False
    push_execution_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.permission_ref, "permission_ref")
        _validate_safe_payload(self.safe_label)
        _validate_safe_payload(self.safe_privacy_copy)
        for field_name, reason in _M100_TAXONOMY_REQUIRED_TRUE:
            if not getattr(self, field_name):
                raise ValueError(reason)
        for field_name, reason in _M100_TAXONOMY_DENIALS:
            if getattr(self, field_name):
                raise ValueError(reason)
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED") from exc
        return self


class MobilePermissionConsentContract(_MobilePermissionModelV1Model):
    consent_ref: str
    actor_ref: str
    permission_ref: str
    device_ref: str
    scope_ref: str
    consent_capture_planned: bool = True
    runtime_consent_granted: bool = False
    exact_scope_required: bool = True
    non_transferable: bool = True
    replay_safe: bool = True
    revocable: bool = True
    renewal_required: bool = True
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.consent_ref, "consent_ref"),
            (self.actor_ref, "actor_ref"),
            (self.permission_ref, "permission_ref"),
            (self.device_ref, "device_ref"),
            (self.scope_ref, "scope_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class MobilePermissionRevocationContract(_MobilePermissionModelV1Model):
    revocation_ref: str
    consent_ref: str
    actor_ref: str
    permission_ref: str
    device_ref: str
    effective_immediately: bool = True
    future_runtime_only: bool = True
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.revocation_ref, "revocation_ref"),
            (self.consent_ref, "consent_ref"),
            (self.actor_ref, "actor_ref"),
            (self.permission_ref, "permission_ref"),
            (self.device_ref, "device_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class MobilePermissionAuditPlan(_MobilePermissionModelV1Model):
    audit_ref: str
    permission_refs: list[str]
    safe_summary: str
    redacted_receipt_required: bool = True
    no_raw_payload: bool = True
    no_sensor_payload: bool = True
    no_background_collection: bool = True
    no_production_authority: bool = True
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.audit_ref, "audit_ref")
        if not self.permission_refs:
            raise ValueError("M100_AUDIT_PERMISSION_REF_REQUIRED")
        for ref in self.permission_refs:
            _validate_m61_ref(ref, "permission_ref")
        _validate_safe_payload(self.safe_summary)
        return self


class MobilePermissionModelV1Report(_MobilePermissionModelV1Model):
    report_ref: str
    baseline_ref: str
    actor_ref: str
    status: MobilePermissionModelV1Status = MobilePermissionModelV1Status.contract_only
    contract_only: bool = True
    permission_taxonomy_defined: bool = True
    consent_model_defined: bool = True
    revocation_model_defined: bool = True
    privacy_copy_defined: bool = True
    permission_audit_defined: bool = True
    sensors_remain_off: bool = True
    no_background_collection: bool = True
    taxonomy: list[MobilePermissionTaxonomyEntry]
    consent_contracts: list[MobilePermissionConsentContract]
    revocation_contracts: list[MobilePermissionRevocationContract]
    audit_plan: MobilePermissionAuditPlan
    runtime_permission_prompts_enabled: bool = False
    native_permission_requests_enabled: bool = False
    mobile_sensor_enabled: bool = False
    location_access_enabled: bool = False
    camera_access_enabled: bool = False
    photos_access_enabled: bool = False
    microphone_access_enabled: bool = False
    contacts_access_enabled: bool = False
    calendar_access_enabled: bool = False
    bluetooth_access_enabled: bool = False
    nfc_access_enabled: bool = False
    biometrics_access_enabled: bool = False
    clipboard_access_enabled: bool = False
    local_network_access_enabled: bool = False
    motion_activity_access_enabled: bool = False
    background_collection_enabled: bool = False
    push_execution_enabled: bool = False
    credential_cookie_access_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    backend_route_added: bool = False
    dependency_added: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_mobile_permission_model_v1_report(
    policy: MobilePermissionModelV1Policy | None = None,
) -> MobilePermissionModelV1Report:
    active_policy = validate_mobile_permission_model_v1_policy(
        policy or MobilePermissionModelV1Policy()
    )
    taxonomy = _default_taxonomy()
    consent_contracts = [
        MobilePermissionConsentContract(
            consent_ref=f"mobile-permission-consent-v1:{entry.category.value}",
            actor_ref="actor:mobile-permission-reviewer",
            permission_ref=entry.permission_ref,
            device_ref="device:mobile-companion-contract",
            scope_ref=f"mobile-permission-scope:{entry.category.value}",
        )
        for entry in taxonomy
    ]
    revocation_contracts = [
        MobilePermissionRevocationContract(
            revocation_ref=f"mobile-permission-revocation-v1:{entry.category.value}",
            consent_ref=f"mobile-permission-consent-v1:{entry.category.value}",
            actor_ref="actor:mobile-permission-reviewer",
            permission_ref=entry.permission_ref,
            device_ref="device:mobile-companion-contract",
        )
        for entry in taxonomy
    ]
    audit_plan = MobilePermissionAuditPlan(
        audit_ref="mobile-permission-audit-v1:m100",
        permission_refs=[entry.permission_ref for entry in taxonomy],
        safe_summary=(
            "M100 audits mobile permission taxonomy, consent, revocation, and privacy copy "
            "without collecting sensor data or requesting runtime OS permissions."
        ),
    )
    report = MobilePermissionModelV1Report(
        report_ref="mobile-permission-model-v1-report:m100",
        baseline_ref="baseline:v1.3.0",
        actor_ref="actor:mobile-permission-reviewer",
        contract_only=active_policy.contract_only,
        taxonomy=taxonomy,
        consent_contracts=consent_contracts,
        revocation_contracts=revocation_contracts,
        audit_plan=audit_plan,
        side_effects_performed=[],
        reason_codes=[
            "M100_MOBILE_PERMISSION_MODEL_V1_CONTRACT_ONLY",
            "M100_PERMISSION_TAXONOMY_DEFINED",
            "M100_CONSENT_REVOCATION_REQUIRED",
            "M100_SENSORS_REMAIN_OFF",
            "M100_NO_BACKGROUND_COLLECTION",
            "POST_M100_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M100 defines Mobile Permission Model v1 as a contract-only taxonomy, consent, "
            "revocation, privacy-copy, and audit boundary. It adds no mobile sensors, "
            "runtime permission prompts, native OS permission requests, background collection, "
            "push execution, backend route, dependency, M101 work, or production authority."
        ),
    )
    return validate_mobile_permission_model_v1_report(report)


def validate_mobile_permission_model_v1_policy(
    policy: MobilePermissionModelV1Policy,
) -> MobilePermissionModelV1Policy:
    validated = MobilePermissionModelV1Policy.model_validate(_model_payload(policy))
    for field_name, reason in _M100_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M100_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED") from exc
    return validated


def validate_mobile_permission_taxonomy_entry(
    entry: MobilePermissionTaxonomyEntry,
) -> MobilePermissionTaxonomyEntry:
    payload = _model_payload(entry)
    for field_name, reason in _M100_TAXONOMY_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobilePermissionTaxonomyEntry):
        raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED")
    validated = MobilePermissionTaxonomyEntry.model_validate(payload)
    for field_name, reason in _M100_TAXONOMY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED") from exc
    return validated


def validate_mobile_permission_model_v1_report(
    report: MobilePermissionModelV1Report,
) -> MobilePermissionModelV1Report:
    payload = _model_payload(report)
    for field_name, reason in _M100_REPORT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobilePermissionModelV1Report):
        raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED")
    validated = MobilePermissionModelV1Report.model_validate(payload)
    for field_name, reason in _M100_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M100_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobilePermissionModelV1Status.contract_only:
        raise ValueError("M100_CONTRACT_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_taxonomy(validated.taxonomy)
    _validate_consent_revocation(validated.consent_contracts, validated.revocation_contracts)
    _validate_audit_plan(validated.audit_plan, [entry.permission_ref for entry in validated.taxonomy])
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED") from exc
    return validated


def _default_taxonomy() -> list[MobilePermissionTaxonomyEntry]:
    entries = []
    for category in MobilePermissionCategory:
        label = category.value.replace("_", " ").title()
        entries.append(
            MobilePermissionTaxonomyEntry(
                permission_ref=f"mobile-permission-v1:{category.value}",
                category=category,
                safe_label=label,
                safe_privacy_copy=(
                    f"{label} permission is defined for future consent review only; "
                    "M100 does not request runtime access or collect data."
                ),
            )
        )
    return entries


def _validate_taxonomy(entries: list[MobilePermissionTaxonomyEntry]) -> None:
    if not entries:
        raise ValueError("M100_PERMISSION_TAXONOMY_REQUIRED")
    seen_refs: set[str] = set()
    seen_categories: set[MobilePermissionCategory] = set()
    for entry in entries:
        validated = validate_mobile_permission_taxonomy_entry(entry)
        if validated.permission_ref in seen_refs:
            raise ValueError("M100_PERMISSION_REF_DUPLICATE")
        if validated.category in seen_categories:
            raise ValueError("M100_PERMISSION_CATEGORY_DUPLICATE")
        seen_refs.add(validated.permission_ref)
        seen_categories.add(validated.category)
    missing = [category for category in MobilePermissionCategory if category not in seen_categories]
    if missing:
        raise ValueError("M100_PERMISSION_CATEGORY_REQUIRED")


def _validate_consent_revocation(
    consents: list[MobilePermissionConsentContract],
    revocations: list[MobilePermissionRevocationContract],
) -> None:
    if not consents:
        raise ValueError("M100_CONSENT_CONTRACT_REQUIRED")
    consent_refs = set()
    for consent in consents:
        payload = _model_payload(consent)
        for field_name, reason in _M100_CONSENT_DENIALS:
            if payload.get(field_name):
                raise ValueError(reason)
        if _has_secret_like_extra(payload, MobilePermissionConsentContract):
            raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED")
        validated = MobilePermissionConsentContract.model_validate(payload)
        for field_name, reason in _M100_CONSENT_REQUIRED_TRUE:
            if not getattr(validated, field_name):
                raise ValueError(reason)
        if validated.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        try:
            _validate_safe_payload(validated.metadata)
        except ValueError as exc:
            raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED") from exc
        consent_refs.add(validated.consent_ref)
    revoked_refs = set()
    for revocation in revocations:
        payload = _model_payload(revocation)
        for field_name, reason in _M100_REVOCATION_DENIALS:
            if payload.get(field_name):
                raise ValueError(reason)
        if _has_secret_like_extra(payload, MobilePermissionRevocationContract):
            raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED")
        validated = MobilePermissionRevocationContract.model_validate(payload)
        for field_name, reason in _M100_REVOCATION_REQUIRED_TRUE:
            if not getattr(validated, field_name):
                raise ValueError(reason)
        if validated.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        try:
            _validate_safe_payload(validated.metadata)
        except ValueError as exc:
            raise ValueError("SECRET_LIKE_M100_PERMISSION_CONTENT_DENIED") from exc
        revoked_refs.add(validated.consent_ref)
    if consent_refs != revoked_refs:
        raise ValueError("M100_CONSENT_REVOCATION_BINDING_REQUIRED")


def _validate_audit_plan(audit_plan: MobilePermissionAuditPlan, permission_refs: list[str]) -> None:
    payload = _model_payload(audit_plan)
    validated = MobilePermissionAuditPlan.model_validate(payload)
    for field_name, reason in _M100_AUDIT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    if set(validated.permission_refs) != set(permission_refs):
        raise ValueError("M100_AUDIT_PERMISSION_BINDING_REQUIRED")


_M100_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("permission_taxonomy_required", "M100_PERMISSION_TAXONOMY_REQUIRED"),
    ("consent_model_required", "M100_CONSENT_MODEL_REQUIRED"),
    ("revocation_model_required", "M100_REVOCATION_MODEL_REQUIRED"),
    ("privacy_copy_required", "M100_PRIVACY_COPY_REQUIRED"),
    ("permission_audit_required", "M100_PERMISSION_AUDIT_REQUIRED"),
    ("sensors_remain_off_required", "MOBILE_SENSOR_DENIED"),
    ("no_background_collection_required", "BACKGROUND_COLLECTION_DENIED"),
]

_M100_POLICY_DENIALS = [
    ("runtime_permission_prompts_enabled", "RUNTIME_PERMISSION_PROMPT_DENIED"),
    ("native_permission_requests_enabled", "NATIVE_PERMISSION_REQUEST_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("location_access_enabled", "LOCATION_ACCESS_DENIED"),
    ("camera_access_enabled", "CAMERA_ACCESS_DENIED"),
    ("photos_access_enabled", "PHOTOS_ACCESS_DENIED"),
    ("microphone_access_enabled", "MICROPHONE_ACCESS_DENIED"),
    ("contacts_access_enabled", "CONTACTS_ACCESS_DENIED"),
    ("calendar_access_enabled", "CALENDAR_ACCESS_DENIED"),
    ("bluetooth_access_enabled", "BLUETOOTH_ACCESS_DENIED"),
    ("nfc_access_enabled", "NFC_ACCESS_DENIED"),
    ("biometrics_access_enabled", "BIOMETRICS_ACCESS_DENIED"),
    ("clipboard_access_enabled", "CLIPBOARD_ACCESS_DENIED"),
    ("local_network_access_enabled", "LOCAL_NETWORK_ACCESS_DENIED"),
    ("motion_activity_access_enabled", "MOTION_ACTIVITY_ACCESS_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("push_execution_enabled", "PUSH_EXECUTION_DENIED"),
    ("credential_cookie_access_enabled", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M100_TAXONOMY_REQUIRED_TRUE = [
    ("planned_disabled", "M100_PERMISSION_DISABLED_BY_DEFAULT_REQUIRED"),
    ("requires_explicit_consent", "M100_EXPLICIT_CONSENT_REQUIRED"),
    ("revocable", "M100_REVOCATION_REQUIRED"),
    ("audit_required", "M100_PERMISSION_AUDIT_REQUIRED"),
]

_M100_TAXONOMY_DENIALS = [
    ("runtime_prompt_enabled", "RUNTIME_PERMISSION_PROMPT_DENIED"),
    ("native_permission_request_enabled", "NATIVE_PERMISSION_REQUEST_DENIED"),
    ("sensor_access_enabled", "MOBILE_SENSOR_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("push_execution_enabled", "PUSH_EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M100_REPORT_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("permission_taxonomy_defined", "M100_PERMISSION_TAXONOMY_REQUIRED"),
    ("consent_model_defined", "M100_CONSENT_MODEL_REQUIRED"),
    ("revocation_model_defined", "M100_REVOCATION_MODEL_REQUIRED"),
    ("privacy_copy_defined", "M100_PRIVACY_COPY_REQUIRED"),
    ("permission_audit_defined", "M100_PERMISSION_AUDIT_REQUIRED"),
    ("sensors_remain_off", "MOBILE_SENSOR_DENIED"),
    ("no_background_collection", "BACKGROUND_COLLECTION_DENIED"),
]

_M100_REPORT_DENIALS = [
    ("runtime_permission_prompts_enabled", "RUNTIME_PERMISSION_PROMPT_DENIED"),
    ("native_permission_requests_enabled", "NATIVE_PERMISSION_REQUEST_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("location_access_enabled", "LOCATION_ACCESS_DENIED"),
    ("camera_access_enabled", "CAMERA_ACCESS_DENIED"),
    ("photos_access_enabled", "PHOTOS_ACCESS_DENIED"),
    ("microphone_access_enabled", "MICROPHONE_ACCESS_DENIED"),
    ("contacts_access_enabled", "CONTACTS_ACCESS_DENIED"),
    ("calendar_access_enabled", "CALENDAR_ACCESS_DENIED"),
    ("bluetooth_access_enabled", "BLUETOOTH_ACCESS_DENIED"),
    ("nfc_access_enabled", "NFC_ACCESS_DENIED"),
    ("biometrics_access_enabled", "BIOMETRICS_ACCESS_DENIED"),
    ("clipboard_access_enabled", "CLIPBOARD_ACCESS_DENIED"),
    ("local_network_access_enabled", "LOCAL_NETWORK_ACCESS_DENIED"),
    ("motion_activity_access_enabled", "MOTION_ACTIVITY_ACCESS_DENIED"),
    ("background_collection_enabled", "BACKGROUND_COLLECTION_DENIED"),
    ("push_execution_enabled", "PUSH_EXECUTION_DENIED"),
    ("credential_cookie_access_enabled", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M100_CONSENT_REQUIRED_TRUE = [
    ("consent_capture_planned", "M100_CONSENT_MODEL_REQUIRED"),
    ("exact_scope_required", "M100_EXACT_SCOPE_REQUIRED"),
    ("non_transferable", "M100_NON_TRANSFERABLE_CONSENT_REQUIRED"),
    ("replay_safe", "M100_REPLAY_SAFE_CONSENT_REQUIRED"),
    ("revocable", "M100_REVOCATION_REQUIRED"),
    ("renewal_required", "M100_RENEWAL_REQUIRED"),
]

_M100_CONSENT_DENIALS = [
    ("runtime_consent_granted", "RUNTIME_PERMISSION_GRANT_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M100_REVOCATION_REQUIRED_TRUE = [
    ("effective_immediately", "M100_REVOCATION_REQUIRED"),
    ("future_runtime_only", "M100_FUTURE_RUNTIME_ONLY_REQUIRED"),
]

_M100_REVOCATION_DENIALS = [
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M100_AUDIT_REQUIRED_TRUE = [
    ("redacted_receipt_required", "M100_REDACTED_RECEIPT_REQUIRED"),
    ("no_raw_payload", "RAW_PAYLOAD_DENIED"),
    ("no_sensor_payload", "MOBILE_SENSOR_DENIED"),
    ("no_background_collection", "BACKGROUND_COLLECTION_DENIED"),
    ("no_production_authority", "PRODUCTION_AUTHORITY_DENIED"),
]
