from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


MOBILE_APPROVAL_RENEWAL_UX_DOCS = [
    "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX.md",
    "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_POLICY.md",
    "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_AUTHORITY_BOUNDARY.md",
    "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_RECEIPT_PLAN.md",
    "docs/mobile/MOBILE_APPROVAL_RENEWAL_UX_NON_GOALS.md",
    "docs/mobile/M107_TO_M108_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MobileApprovalRenewalUxChannel(str, Enum):
    renewal_banner_copy = "renewal_banner_copy"
    renewal_expiration_notice = "renewal_expiration_notice"


class MobileApprovalRenewalUxStatus(str, Enum):
    review_only_contract = "review_only_contract"


class _MobileApprovalRenewalUxModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobileApprovalRenewalUxPolicy(_MobileApprovalRenewalUxModel):
    policy_ref: str = "mobile-approval-renewal-ux-policy:m107"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    consent_required: bool = True
    approval_capture_enabled: bool = False
    approval_persistence_enabled: bool = False
    approval_renewal_execution_enabled: bool = False
    approval_renewal_runtime_prompt_enabled: bool = False
    native_mobile_ui_enabled: bool = False
    control_center_control_enabled: bool = False
    backend_route_enabled: bool = False
    notification_delivery_enabled: bool = False
    push_trigger_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    network_sync_enabled: bool = False
    raw_approval_payload_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    kill_switch_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MobileApprovalRenewalPrompt(_MobileApprovalRenewalUxModel):
    prompt_ref: str
    channel: MobileApprovalRenewalUxChannel
    approval_ref: str
    actor_ref: str
    safe_device_ref: str
    safe_renewal_copy_ref: str
    safe_renewal_window_ref: str
    safe_expiration_ref: str
    consent_ref: str
    revocation_ref: str
    audit_ref: str
    review_only: bool = True
    safe_refs_only: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    consent_required: bool = True
    approval_capture_enabled: bool = False
    approval_persistence_enabled: bool = False
    approval_renewal_execution_enabled: bool = False
    approval_renewal_runtime_prompt_enabled: bool = False
    native_mobile_ui_enabled: bool = False
    control_center_control_enabled: bool = False
    backend_route_enabled: bool = False
    notification_delivery_enabled: bool = False
    push_trigger_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    network_sync_enabled: bool = False
    raw_approval_payload_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    kill_switch_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.prompt_ref, "prompt_ref"),
            (self.approval_ref, "approval_ref"),
            (self.actor_ref, "actor_ref"),
            (self.safe_device_ref, "safe_device_ref"),
            (self.safe_renewal_copy_ref, "safe_renewal_copy_ref"),
            (self.safe_renewal_window_ref, "safe_renewal_window_ref"),
            (self.safe_expiration_ref, "safe_expiration_ref"),
            (self.consent_ref, "consent_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class MobileApprovalRenewalUxReport(_MobileApprovalRenewalUxModel):
    report_ref: str
    baseline_ref: str
    actor_ref: str
    status: MobileApprovalRenewalUxStatus = (
        MobileApprovalRenewalUxStatus.review_only_contract
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    audit_required: bool = True
    revocation_required: bool = True
    consent_required: bool = True
    renewal_prompts: list[MobileApprovalRenewalPrompt]
    approval_capture_enabled: bool = False
    approval_persistence_enabled: bool = False
    approval_renewal_execution_enabled: bool = False
    approval_renewal_runtime_prompt_enabled: bool = False
    native_mobile_ui_enabled: bool = False
    control_center_control_added: bool = False
    backend_route_added: bool = False
    notification_delivery_enabled: bool = False
    push_trigger_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    network_sync_enabled: bool = False
    raw_approval_payload_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    kill_switch_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
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


def build_mobile_approval_renewal_ux_report(
    policy: MobileApprovalRenewalUxPolicy | None = None,
) -> MobileApprovalRenewalUxReport:
    active_policy = validate_mobile_approval_renewal_ux_policy(
        policy or MobileApprovalRenewalUxPolicy()
    )
    report = MobileApprovalRenewalUxReport(
        report_ref="mobile-approval-renewal-ux-report:m107",
        baseline_ref="baseline:v1.7.2",
        actor_ref="actor:mobile-approval-renewal-ux-reviewer",
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        audit_required=active_policy.audit_required,
        revocation_required=active_policy.revocation_required,
        consent_required=active_policy.consent_required,
        renewal_prompts=_default_renewal_prompts(),
        side_effects_performed=[],
        reason_codes=[
            "M107_MOBILE_APPROVAL_RENEWAL_UX",
            "M107_SAFE_RENEWAL_REFS_ONLY",
            "M107_REVIEW_ONLY_UX_CONTRACT",
            "M107_NO_APPROVAL_CAPTURE",
            "M107_NO_APPROVAL_PERSISTENCE",
            "M108_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M107 defines review-only mobile approval renewal UX contracts for "
            "future inspection. It records safe renewal copy refs, safe renewal "
            "window refs, safe expiration refs, consent refs, revocation refs, "
            "and audit refs only. It adds no approval capture, approval "
            "persistence, approval renewal execution, runtime prompt, native "
            "mobile UI, backend routes, Control Center controls, notification "
            "delivery, push trigger, background worker, scheduler, daemon, "
            "device token handling, external service, network sync, raw "
            "approval payload, memory writes, context injection, execution, "
            "kill switch execution, M108 work, or production authority."
        ),
    )
    return validate_mobile_approval_renewal_ux_report(report)


def validate_mobile_approval_renewal_ux_policy(
    policy: MobileApprovalRenewalUxPolicy,
) -> MobileApprovalRenewalUxPolicy:
    validated = MobileApprovalRenewalUxPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M107_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M107_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m107_metadata(validated.metadata)
    return validated


def validate_mobile_approval_renewal_prompt(
    prompt: MobileApprovalRenewalPrompt,
) -> MobileApprovalRenewalPrompt:
    payload = _model_payload(prompt)
    for field_name, reason in _M107_PROMPT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileApprovalRenewalPrompt):
        raise ValueError("SECRET_LIKE_M107_APPROVAL_RENEWAL_CONTENT_DENIED")
    validated = MobileApprovalRenewalPrompt.model_validate(payload)
    for field_name, reason in _M107_PROMPT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M107_PROMPT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m107_metadata(validated.metadata)
    return validated


def validate_mobile_approval_renewal_ux_report(
    report: MobileApprovalRenewalUxReport,
) -> MobileApprovalRenewalUxReport:
    payload = _model_payload(report)
    for field_name, reason in _M107_REPORT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileApprovalRenewalUxReport):
        raise ValueError("SECRET_LIKE_M107_APPROVAL_RENEWAL_CONTENT_DENIED")
    validated = MobileApprovalRenewalUxReport.model_validate(payload)
    for field_name, reason in _M107_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M107_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobileApprovalRenewalUxStatus.review_only_contract:
        raise ValueError("M107_REVIEW_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_renewal_prompts(validated.renewal_prompts)
    _validate_m107_metadata(validated.metadata)
    return validated


def _default_renewal_prompts() -> list[MobileApprovalRenewalPrompt]:
    return [
        MobileApprovalRenewalPrompt(
            prompt_ref="approval-renewal-prompt:m107:banner-copy",
            channel=MobileApprovalRenewalUxChannel.renewal_banner_copy,
            approval_ref="approval-ref:m107:review-only-renewal",
            actor_ref="actor:mobile-approval-renewal-ux-reviewer",
            safe_device_ref="safe-device-ref:m107:mobile-companion",
            safe_renewal_copy_ref="safe-renewal-copy-ref:m107:banner-copy",
            safe_renewal_window_ref="safe-renewal-window-ref:m107:single-session",
            safe_expiration_ref="safe-expiration-ref:m107:approval-window",
            consent_ref="consent-ref:m107:renewal-copy",
            revocation_ref="revocation-ref:m107:renewal-copy",
            audit_ref="audit-ref:m107:banner-copy",
        ),
        MobileApprovalRenewalPrompt(
            prompt_ref="approval-renewal-prompt:m107:expiration-notice",
            channel=MobileApprovalRenewalUxChannel.renewal_expiration_notice,
            approval_ref="approval-ref:m107:expiration-review",
            actor_ref="actor:mobile-approval-renewal-ux-reviewer",
            safe_device_ref="safe-device-ref:m107:mobile-companion",
            safe_renewal_copy_ref="safe-renewal-copy-ref:m107:expiration-notice",
            safe_renewal_window_ref="safe-renewal-window-ref:m107:expiration-window",
            safe_expiration_ref="safe-expiration-ref:m107:notice-expiration",
            consent_ref="consent-ref:m107:expiration-notice",
            revocation_ref="revocation-ref:m107:expiration-notice",
            audit_ref="audit-ref:m107:expiration-notice",
        ),
    ]


def _validate_renewal_prompts(prompts: list[MobileApprovalRenewalPrompt]) -> None:
    if not prompts:
        raise ValueError("M107_RENEWAL_PROMPT_REQUIRED")
    seen_prompt_refs: set[str] = set()
    seen_channels: set[MobileApprovalRenewalUxChannel] = set()
    for prompt in prompts:
        validated = validate_mobile_approval_renewal_prompt(prompt)
        if validated.prompt_ref in seen_prompt_refs:
            raise ValueError("M107_RENEWAL_PROMPT_REF_DUPLICATE")
        seen_prompt_refs.add(validated.prompt_ref)
        seen_channels.add(validated.channel)
    if seen_channels != {
        MobileApprovalRenewalUxChannel.renewal_banner_copy,
        MobileApprovalRenewalUxChannel.renewal_expiration_notice,
    }:
        raise ValueError("M107_RENEWAL_PROMPT_CHANNELS_REQUIRED")


def _validate_m107_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M107_APPROVAL_RENEWAL_CONTENT_DENIED") from exc


_M107_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M107_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M107_SAFE_REFS_REQUIRED"),
    ("audit_required", "M107_AUDIT_REQUIRED"),
    ("revocation_required", "M107_REVOCATION_REQUIRED"),
    ("consent_required", "M107_CONSENT_REQUIRED"),
]

_M107_POLICY_DENIALS = [
    ("approval_capture_enabled", "APPROVAL_CAPTURE_DENIED"),
    ("approval_persistence_enabled", "APPROVAL_PERSISTENCE_DENIED"),
    ("approval_renewal_execution_enabled", "APPROVAL_RENEWAL_EXECUTION_DENIED"),
    ("approval_renewal_runtime_prompt_enabled", "APPROVAL_RENEWAL_RUNTIME_PROMPT_DENIED"),
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
    ("raw_approval_payload_enabled", "RAW_APPROVAL_PAYLOAD_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("kill_switch_enabled", "KILL_SWITCH_DENIED"),
]

_M107_PROMPT_REQUIRED_TRUE = [
    ("review_only", "M107_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_only", "M107_SAFE_REFS_REQUIRED"),
    ("audit_required", "M107_AUDIT_REQUIRED"),
    ("revocation_required", "M107_REVOCATION_REQUIRED"),
    ("consent_required", "M107_CONSENT_REQUIRED"),
]

_M107_PROMPT_DENIALS = [
    ("approval_capture_enabled", "APPROVAL_CAPTURE_DENIED"),
    ("approval_persistence_enabled", "APPROVAL_PERSISTENCE_DENIED"),
    ("approval_renewal_execution_enabled", "APPROVAL_RENEWAL_EXECUTION_DENIED"),
    ("approval_renewal_runtime_prompt_enabled", "APPROVAL_RENEWAL_RUNTIME_PROMPT_DENIED"),
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
    ("raw_approval_payload_enabled", "RAW_APPROVAL_PAYLOAD_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("kill_switch_enabled", "KILL_SWITCH_DENIED"),
]

_M107_REPORT_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M107_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M107_SAFE_REFS_REQUIRED"),
    ("audit_required", "M107_AUDIT_REQUIRED"),
    ("revocation_required", "M107_REVOCATION_REQUIRED"),
    ("consent_required", "M107_CONSENT_REQUIRED"),
]

_M107_REPORT_DENIALS = [
    ("approval_capture_enabled", "APPROVAL_CAPTURE_DENIED"),
    ("approval_persistence_enabled", "APPROVAL_PERSISTENCE_DENIED"),
    ("approval_renewal_execution_enabled", "APPROVAL_RENEWAL_EXECUTION_DENIED"),
    ("approval_renewal_runtime_prompt_enabled", "APPROVAL_RENEWAL_RUNTIME_PROMPT_DENIED"),
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("notification_delivery_enabled", "NOTIFICATION_DELIVERY_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
    ("raw_approval_payload_enabled", "RAW_APPROVAL_PAYLOAD_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
    ("kill_switch_enabled", "KILL_SWITCH_DENIED"),
]
