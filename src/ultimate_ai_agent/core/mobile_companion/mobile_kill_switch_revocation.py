from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload
from ultimate_ai_agent.core.mobile_companion.mobile_approval_renewal_ux import (
    MobileApprovalRenewalUxReport,
    validate_mobile_approval_renewal_ux_report,
)


MOBILE_KILL_SWITCH_REVOCATION_DOCS = [
    "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION.md",
    "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_POLICY.md",
    "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_AUTHORITY_BOUNDARY.md",
    "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_RECEIPT_PLAN.md",
    "docs/mobile/MOBILE_KILL_SWITCH_REVOCATION_NON_GOALS.md",
    "docs/mobile/M108_TO_M109_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MobileKillSwitchRevocationStatus(str, Enum):
    review_only_contract = "review_only_contract"


class _MobileKillSwitchRevocationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobileKillSwitchRevocationPolicy(_MobileKillSwitchRevocationModel):
    policy_ref: str = "mobile-kill-switch-revocation-policy:m108"
    contract_only: bool = True
    review_only_required: bool = True
    safe_refs_required: bool = True
    actor_binding_required: bool = True
    device_binding_required: bool = True
    approval_binding_required: bool = True
    revocation_binding_required: bool = True
    audit_required: bool = True
    replay_required: bool = True
    revocation_execution_enabled: bool = False
    kill_switch_execution_enabled: bool = False
    approval_revocation_enabled: bool = False
    session_stop_enabled: bool = False
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
    native_mobile_ui_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MobileKillSwitchRevocationRecord(_MobileKillSwitchRevocationModel):
    record_ref: str
    source_report: MobileApprovalRenewalUxReport
    source_report_ref: str
    source_baseline_ref: str
    actor_ref: str
    safe_device_ref: str
    approval_ref: str
    safe_revocation_reason_ref: str
    safe_kill_switch_reason_ref: str
    revocation_ref: str
    audit_ref: str
    replay_ref: str
    status: MobileKillSwitchRevocationStatus = (
        MobileKillSwitchRevocationStatus.review_only_contract
    )
    contract_only: bool = True
    review_only: bool = True
    safe_refs_required: bool = True
    actor_bound: bool = True
    device_bound: bool = True
    approval_bound: bool = True
    revocation_bound: bool = True
    audit_required: bool = True
    replay_safe: bool = True
    revocation_requested: bool = True
    kill_switch_requested: bool = True
    revocation_performed: bool = False
    kill_switch_activated: bool = False
    session_stopped: bool = False
    approval_revoked: bool = False
    revocation_execution_enabled: bool = False
    kill_switch_execution_enabled: bool = False
    approval_revocation_enabled: bool = False
    session_stop_enabled: bool = False
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
    native_mobile_ui_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.record_ref, "record_ref"),
            (self.source_report_ref, "source_report_ref"),
            (self.source_baseline_ref, "source_baseline_ref"),
            (self.actor_ref, "actor_ref"),
            (self.safe_device_ref, "safe_device_ref"),
            (self.approval_ref, "approval_ref"),
            (self.safe_revocation_reason_ref, "safe_revocation_reason_ref"),
            (self.safe_kill_switch_reason_ref, "safe_kill_switch_reason_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
            (self.replay_ref, "replay_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        _validate_safe_payload(self.safe_summary)
        return self


def build_mobile_kill_switch_revocation_record(
    *,
    source_report: MobileApprovalRenewalUxReport,
    policy: MobileKillSwitchRevocationPolicy | None = None,
) -> MobileKillSwitchRevocationRecord:
    active_policy = validate_mobile_kill_switch_revocation_policy(
        policy or MobileKillSwitchRevocationPolicy()
    )
    validated_source = validate_mobile_approval_renewal_ux_report(source_report)
    record = MobileKillSwitchRevocationRecord(
        record_ref="mobile-kill-switch-revocation-record:m108",
        source_report=validated_source,
        source_report_ref=validated_source.report_ref,
        source_baseline_ref=validated_source.baseline_ref,
        actor_ref=validated_source.actor_ref,
        safe_device_ref="safe-device-ref:m108:mobile-companion",
        approval_ref="approval-ref:m108:review-only-kill-switch",
        safe_revocation_reason_ref="safe-revocation-reason-ref:m108:review-only",
        safe_kill_switch_reason_ref="safe-kill-switch-reason-ref:m108:review-only",
        revocation_ref="revocation-ref:m108:review-only",
        audit_ref="audit-ref:m108:kill-switch-revocation",
        replay_ref="replay-ref:m108:kill-switch-revocation",
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only_required,
        safe_refs_required=active_policy.safe_refs_required,
        actor_bound=active_policy.actor_binding_required,
        device_bound=active_policy.device_binding_required,
        approval_bound=active_policy.approval_binding_required,
        revocation_bound=active_policy.revocation_binding_required,
        audit_required=active_policy.audit_required,
        replay_safe=active_policy.replay_required,
        side_effects_performed=[],
        reason_codes=[
            "M108_MOBILE_KILL_SWITCH_REVOCATION",
            "M108_REVIEW_ONLY_REVOCATION_RECORD",
            "M108_SAFE_REVOCATION_REFS_ONLY",
            "M108_NO_KILL_SWITCH_EXECUTION",
            "M108_NO_REVOCATION_EXECUTION",
            "M109_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M108 records mobile kill-switch and revocation intent for review "
            "only using safe refs. It does not activate a kill switch, revoke "
            "an approval, stop a session, deliver notifications, push, run "
            "background workers, sync over a network, write memory, inject "
            "context, execute, add routes, add controls, or grant production "
            "authority."
        ),
    )
    return validate_mobile_kill_switch_revocation_record(record)


def validate_mobile_kill_switch_revocation_policy(
    policy: MobileKillSwitchRevocationPolicy,
) -> MobileKillSwitchRevocationPolicy:
    validated = MobileKillSwitchRevocationPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M108_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M108_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m108_metadata(validated.metadata)
    return validated


def validate_mobile_kill_switch_revocation_record(
    record: MobileKillSwitchRevocationRecord,
) -> MobileKillSwitchRevocationRecord:
    payload = _model_payload(record)
    for field_name, reason in _M108_RECORD_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileKillSwitchRevocationRecord):
        raise ValueError("SECRET_LIKE_M108_KILL_SWITCH_CONTENT_DENIED")
    source_payload = payload.get("source_report")
    if isinstance(source_payload, dict):
        source_payload = MobileApprovalRenewalUxReport.model_validate(source_payload)
    try:
        source_report = validate_mobile_approval_renewal_ux_report(source_payload)
    except ValueError:
        raise
    validated = MobileKillSwitchRevocationRecord.model_validate(payload)
    for field_name, reason in _M108_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M108_RECORD_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobileKillSwitchRevocationStatus.review_only_contract:
        raise ValueError("M108_REVIEW_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    if validated.approval_ref.startswith("approval_test_"):
        raise ValueError("APPROVAL_TEST_REF_DENIED")
    _validate_m108_bindings(validated, source_report)
    _validate_m108_metadata(validated.metadata)
    return validated


def _validate_m108_bindings(
    record: MobileKillSwitchRevocationRecord,
    source_report: MobileApprovalRenewalUxReport,
) -> None:
    if record.source_report_ref != source_report.report_ref:
        raise ValueError("M108_SOURCE_REPORT_BINDING_MISMATCH")
    if record.source_baseline_ref != source_report.baseline_ref:
        raise ValueError("M108_BASELINE_BINDING_MISMATCH")
    if record.actor_ref != source_report.actor_ref:
        raise ValueError("M108_ACTOR_BINDING_MISMATCH")


def _validate_m108_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M108_KILL_SWITCH_CONTENT_DENIED") from exc


_M108_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only_required", "M108_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M108_SAFE_REFS_REQUIRED"),
    ("actor_binding_required", "M108_ACTOR_BINDING_REQUIRED"),
    ("device_binding_required", "M108_DEVICE_BINDING_REQUIRED"),
    ("approval_binding_required", "M108_APPROVAL_BINDING_REQUIRED"),
    ("revocation_binding_required", "M108_REVOCATION_BINDING_REQUIRED"),
    ("audit_required", "M108_AUDIT_REQUIRED"),
    ("replay_required", "M108_REPLAY_REQUIRED"),
]

_M108_POLICY_DENIALS = [
    ("revocation_execution_enabled", "REVOCATION_EXECUTION_DENIED"),
    ("kill_switch_execution_enabled", "KILL_SWITCH_EXECUTION_DENIED"),
    ("approval_revocation_enabled", "APPROVAL_REVOCATION_DENIED"),
    ("session_stop_enabled", "SESSION_STOP_DENIED"),
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
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
]

_M108_RECORD_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M108_REVIEW_ONLY_REQUIRED"),
    ("safe_refs_required", "M108_SAFE_REFS_REQUIRED"),
    ("actor_bound", "M108_ACTOR_BINDING_REQUIRED"),
    ("device_bound", "M108_DEVICE_BINDING_REQUIRED"),
    ("approval_bound", "M108_APPROVAL_BINDING_REQUIRED"),
    ("revocation_bound", "M108_REVOCATION_BINDING_REQUIRED"),
    ("audit_required", "M108_AUDIT_REQUIRED"),
    ("replay_safe", "M108_REPLAY_REQUIRED"),
    ("revocation_requested", "M108_REVOCATION_REQUEST_REQUIRED"),
    ("kill_switch_requested", "M108_KILL_SWITCH_REQUEST_REQUIRED"),
]

_M108_RECORD_DENIALS = [
    ("revocation_performed", "REVOCATION_ACTION_DENIED"),
    ("kill_switch_activated", "KILL_SWITCH_ACTIVATION_DENIED"),
    ("session_stopped", "SESSION_STOP_DENIED"),
    ("approval_revoked", "APPROVAL_REVOCATION_DENIED"),
    ("revocation_execution_enabled", "REVOCATION_EXECUTION_DENIED"),
    ("kill_switch_execution_enabled", "KILL_SWITCH_EXECUTION_DENIED"),
    ("approval_revocation_enabled", "APPROVAL_REVOCATION_DENIED"),
    ("session_stop_enabled", "SESSION_STOP_DENIED"),
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
    ("native_mobile_ui_enabled", "NATIVE_MOBILE_UI_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
]
