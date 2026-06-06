import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.ledger import EventLedgerEvent
from ultimate_ai_agent.core.tools.v2.validation import validate_safe_tool_payload


M55_DOC_REFS = [
    "docs/observability/REDACTED_OBSERVABILITY_EXPORT.md",
    "docs/observability/REDACTED_OBSERVABILITY_EXPORT_POLICY.md",
    "docs/observability/REDACTED_OBSERVABILITY_EXPORT_AUTHORITY_BOUNDARY.md",
    "docs/observability/M55_TO_M56_BOUNDARY.md",
]
M55_SAFE_REF_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.-]*:[a-zA-Z0-9][a-zA-Z0-9_.:/@-]*$")


class ObservabilityExportFormat(str, Enum):
    internal_redacted_json = "internal_redacted_json"
    otel_redacted_mapping = "otel_redacted_mapping"
    cloudevents_redacted_mapping = "cloudevents_redacted_mapping"


class RedactedObservabilityExportStatus(str, Enum):
    ready = "ready"
    denied = "denied"


class _M55ObservabilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class RedactedObservabilityExportPolicy(_M55ObservabilityModel):
    policy_ref: str = "redacted-observability-export-policy:m55"
    baseline_version: str = "0.59.0"
    redacted_only: bool = True
    contract_only: bool = True
    external_saas_sdk_enabled: bool = False
    network_delivery_enabled: bool = False
    raw_prompt_export_enabled: bool = False
    raw_provider_payload_export_enabled: bool = False
    raw_private_content_export_enabled: bool = False
    secret_export_enabled: bool = False
    forensic_trace_export_enabled: bool = False
    memory_write_enabled: bool = False
    model_call_enabled: bool = False
    context_injection_enabled: bool = False
    backend_routes_enabled: bool = False
    control_center_controls_enabled: bool = False
    dependencies_added: bool = False
    production_authority_enabled: bool = False
    m56_implemented: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M55_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M55", "version:v0.59.0"])
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy_shape(self):
        _validate_m55_ref(self.policy_ref, "policy_ref")
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m55_ref(ref, "metadata_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        return self


class RedactedObservabilityExportRequest(_M55ObservabilityModel):
    request_ref: str
    run_ref: str
    export_ref: str
    requested_formats: list[ObservabilityExportFormat]
    source_event_refs: list[str]
    redaction_policy_ref: str
    raw_prompt_export_requested: bool = False
    raw_provider_payload_export_requested: bool = False
    raw_private_content_export_requested: bool = False
    secret_export_requested: bool = False
    external_saas_export_requested: bool = False
    network_export_requested: bool = False
    memory_write_requested: bool = False
    model_call_requested: bool = False
    context_injection_requested: bool = False
    metadata_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request_shape(self):
        _validate_m55_ref(self.request_ref, "request_ref")
        _validate_m55_ref(self.run_ref, "run_ref")
        _validate_m55_ref(self.export_ref, "export_ref")
        _validate_m55_ref(self.redaction_policy_ref, "redaction_policy_ref")
        if not self.requested_formats:
            raise ValueError("OBSERVABILITY_EXPORT_FORMAT_REQUIRED")
        if not self.source_event_refs:
            raise ValueError("OBSERVABILITY_EXPORT_EVENT_REFS_REQUIRED")
        for ref in self.source_event_refs:
            _validate_m55_ref(ref, "source_event_ref")
        for ref in self.metadata_refs:
            _validate_m55_ref(ref, "metadata_ref")
        validate_safe_tool_payload(self.metadata, "metadata")
        return self


class RedactedObservabilityExportItem(_M55ObservabilityModel):
    event_ref: str
    run_ref: str
    trace_ref: str
    span_ref: str
    event_name: str
    event_type: str
    status: str
    severity: str
    safe_summary: str
    redaction_summary_ref: str
    evidence_refs: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_item_shape(self):
        for value, field_name in [
            (self.event_ref, "event_ref"),
            (self.run_ref, "run_ref"),
            (self.trace_ref, "trace_ref"),
            (self.span_ref, "span_ref"),
            (self.redaction_summary_ref, "redaction_summary_ref"),
        ]:
            _validate_m55_ref(value, field_name)
        for value, field_name in [
            (self.event_name, "event_name"),
            (self.event_type, "event_type"),
            (self.status, "status"),
            (self.severity, "severity"),
            (self.safe_summary, "safe_summary"),
        ]:
            _require_nonempty(value, field_name)
            validate_safe_tool_payload(value, field_name)
        for ref in self.evidence_refs:
            _validate_m55_ref(ref, "evidence_ref")
        return self


class RedactedObservabilityExportReceiptPlan(_M55ObservabilityModel):
    receipt_plan_ref: str
    export_ref: str
    redacted_only: bool = True
    export_performed: bool = False
    external_delivery_performed: bool = False
    raw_prompt_exported: bool = False
    raw_provider_payload_exported: bool = False
    raw_private_content_exported: bool = False
    secret_exported: bool = False
    network_call_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    safe_summary: str = "M55 redacted observability export receipt plan."

    @model_validator(mode="after")
    def validate_receipt_plan(self):
        _validate_m55_ref(self.receipt_plan_ref, "receipt_plan_ref")
        _validate_m55_ref(self.export_ref, "export_ref")
        if not self.redacted_only:
            raise ValueError("REDACTED_OBSERVABILITY_EXPORT_REQUIRED")
        for field_name, reason in [
            ("export_performed", "EXPORT_PERFORMED_DENIED"),
            ("external_delivery_performed", "EXTERNAL_DELIVERY_DENIED"),
            ("raw_prompt_exported", "RAW_PROMPT_EXPORT_DENIED"),
            ("raw_provider_payload_exported", "RAW_PROVIDER_PAYLOAD_EXPORT_DENIED"),
            ("raw_private_content_exported", "RAW_PRIVATE_CONTENT_EXPORT_DENIED"),
            ("secret_exported", "SECRET_EXPORT_DENIED"),
            ("network_call_performed", "NETWORK_EXPORT_DENIED"),
            ("model_call_performed", "MODEL_CALL_DENIED"),
            ("memory_write_performed", "MEMORY_WRITE_DENIED"),
            ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        if self.side_effects_performed:
            raise ValueError("SIDE_EFFECTS_DENIED")
        validate_safe_tool_payload(self.safe_summary, "safe_summary")
        return self


class RedactedObservabilityExportBundle(_M55ObservabilityModel):
    bundle_ref: str
    request_ref: str
    export_ref: str
    status: RedactedObservabilityExportStatus
    requested_formats: list[ObservabilityExportFormat]
    items: list[RedactedObservabilityExportItem]
    receipt_plan: RedactedObservabilityExportReceiptPlan | None = None
    reason_codes: list[str] = Field(default_factory=list)
    redacted_only: bool = True
    export_performed: bool = False
    external_delivery_performed: bool = False
    raw_prompt_exported: bool = False
    raw_provider_payload_exported: bool = False
    raw_private_content_exported: bool = False
    secret_exported: bool = False
    saas_sdk_enabled: bool = False
    network_call_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    docs_refs: list[str] = Field(default_factory=lambda: list(M55_DOC_REFS))
    metadata_refs: list[str] = Field(default_factory=lambda: ["milestone:M55", "version:v0.59.0"])

    @model_validator(mode="after")
    def validate_bundle(self):
        _validate_m55_ref(self.bundle_ref, "bundle_ref")
        _validate_m55_ref(self.request_ref, "request_ref")
        _validate_m55_ref(self.export_ref, "export_ref")
        if not self.redacted_only:
            raise ValueError("REDACTED_OBSERVABILITY_EXPORT_REQUIRED")
        if self.status == RedactedObservabilityExportStatus.ready and not self.items:
            raise ValueError("OBSERVABILITY_EXPORT_ITEMS_REQUIRED")
        for field_name, reason in [
            ("export_performed", "EXPORT_PERFORMED_DENIED"),
            ("external_delivery_performed", "EXTERNAL_DELIVERY_DENIED"),
            ("raw_prompt_exported", "RAW_PROMPT_EXPORT_DENIED"),
            ("raw_provider_payload_exported", "RAW_PROVIDER_PAYLOAD_EXPORT_DENIED"),
            ("raw_private_content_exported", "RAW_PRIVATE_CONTENT_EXPORT_DENIED"),
            ("secret_exported", "SECRET_EXPORT_DENIED"),
            ("saas_sdk_enabled", "EXTERNAL_SAAS_SDK_DENIED"),
            ("network_call_performed", "NETWORK_EXPORT_DENIED"),
            ("model_call_performed", "MODEL_CALL_DENIED"),
            ("memory_write_performed", "MEMORY_WRITE_DENIED"),
            ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        for ref in self.docs_refs:
            _require_nonempty(ref, "docs_ref")
        for ref in self.metadata_refs:
            _validate_m55_ref(ref, "metadata_ref")
        for reason in self.reason_codes:
            _require_nonempty(reason, "reason_code")
        return self


def validate_redacted_observability_export_policy(
    policy: RedactedObservabilityExportPolicy,
) -> RedactedObservabilityExportPolicy:
    validated = RedactedObservabilityExportPolicy.model_validate(policy.model_dump())
    if not validated.redacted_only or not validated.contract_only:
        raise ValueError("REDACTED_OBSERVABILITY_EXPORT_REQUIRED")
    for field_name, reason in [
        ("external_saas_sdk_enabled", "EXTERNAL_SAAS_SDK_DENIED"),
        ("network_delivery_enabled", "NETWORK_EXPORT_DENIED"),
        ("raw_prompt_export_enabled", "RAW_PROMPT_EXPORT_DENIED"),
        ("raw_provider_payload_export_enabled", "RAW_PROVIDER_PAYLOAD_EXPORT_DENIED"),
        ("raw_private_content_export_enabled", "RAW_PRIVATE_CONTENT_EXPORT_DENIED"),
        ("secret_export_enabled", "SECRET_EXPORT_DENIED"),
        ("forensic_trace_export_enabled", "FORENSIC_TRACE_EXPORT_DENIED"),
        ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
        ("model_call_enabled", "MODEL_CALL_DENIED"),
        ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
        ("backend_routes_enabled", "BACKEND_ROUTE_DENIED"),
        ("control_center_controls_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
        ("dependencies_added", "DEPENDENCY_ADDITION_DENIED"),
        ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
        ("m56_implemented", "M56_IMPLEMENTATION_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_redacted_observability_export_request(
    request: RedactedObservabilityExportRequest,
) -> RedactedObservabilityExportRequest:
    validated = RedactedObservabilityExportRequest.model_validate(request.model_dump())
    for field_name, reason in [
        ("raw_prompt_export_requested", "RAW_PROMPT_EXPORT_DENIED"),
        ("raw_provider_payload_export_requested", "RAW_PROVIDER_PAYLOAD_EXPORT_DENIED"),
        ("raw_private_content_export_requested", "RAW_PRIVATE_CONTENT_EXPORT_DENIED"),
        ("secret_export_requested", "SECRET_EXPORT_DENIED"),
        ("external_saas_export_requested", "EXTERNAL_SAAS_EXPORT_DENIED"),
        ("network_export_requested", "NETWORK_EXPORT_DENIED"),
        ("memory_write_requested", "MEMORY_WRITE_DENIED"),
        ("model_call_requested", "MODEL_CALL_DENIED"),
        ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ]:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def build_redacted_observability_export(
    request: RedactedObservabilityExportRequest,
    events: list[EventLedgerEvent],
    policy: RedactedObservabilityExportPolicy | None = None,
) -> RedactedObservabilityExportBundle:
    active_policy = validate_redacted_observability_export_policy(
        policy or RedactedObservabilityExportPolicy()
    )
    active_request = validate_redacted_observability_export_request(request)
    event_by_ref = {f"event:{event.event_id}": event for event in events}
    missing_refs = [ref for ref in active_request.source_event_refs if ref not in event_by_ref]
    if missing_refs:
        raise ValueError("OBSERVABILITY_EXPORT_EVENT_REF_MISMATCH")

    items = [_redacted_item_from_event(event_by_ref[ref]) for ref in active_request.source_event_refs]
    return RedactedObservabilityExportBundle(
        bundle_ref=f"observability-export-bundle:{_ref_suffix(active_request.export_ref)}",
        request_ref=active_request.request_ref,
        export_ref=active_request.export_ref,
        status=RedactedObservabilityExportStatus.ready,
        requested_formats=active_request.requested_formats,
        items=items,
        receipt_plan=RedactedObservabilityExportReceiptPlan(
            receipt_plan_ref=f"observability-export-receipt:{_ref_suffix(active_request.export_ref)}",
            export_ref=active_request.export_ref,
            safe_summary="M55 plans redacted observability export only; no delivery is performed.",
        ),
        reason_codes=["M55_REDACTED_EXPORT_CONTRACT_ONLY"],
        metadata_refs=[
            *active_policy.metadata_refs,
            active_request.request_ref,
            active_request.export_ref,
        ],
    )


def _redacted_item_from_event(event: EventLedgerEvent) -> RedactedObservabilityExportItem:
    _assert_event_redacted_safe(event)
    safe_summary = str(event.metadata.get("safe_summary") or event.subject)
    return RedactedObservabilityExportItem(
        event_ref=f"event:{event.event_id}",
        run_ref=f"run:{event.run_id}",
        trace_ref=f"trace:{event.trace_id}",
        span_ref=f"span:{event.span_id}",
        event_name=str(event.event_name),
        event_type=event.event_type,
        status=event.status,
        severity=event.severity,
        safe_summary=safe_summary,
        redaction_summary_ref=f"redaction-summary:{event.event_id}",
        evidence_refs=list(event.evidence_refs),
    )


def _assert_event_redacted_safe(event: EventLedgerEvent) -> None:
    for field_name, value in [
        ("subject", event.subject),
        ("action", event.action),
        ("outcome", event.outcome),
        ("status", event.status),
        ("severity", event.severity),
        ("metadata", event.metadata),
        ("redaction_summary", event.redaction_summary),
        ("evidence_refs", event.evidence_refs),
    ]:
        try:
            validate_safe_tool_payload(value, field_name)
        except ValueError as exc:
            raise ValueError("SECRET_LIKE_OBSERVABILITY_CONTENT_DENIED") from exc


def _require_nonempty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_m55_ref(value: str, field_name: str) -> None:
    _require_nonempty(value, field_name)
    if not M55_SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name} must be a structured safe ref")


def _ref_suffix(value: str) -> str:
    return value.split(":", 1)[1].replace("/", "-").replace("@", "-")
