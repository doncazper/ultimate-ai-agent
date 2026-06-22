from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref


CUA_CONTRACT_DOC_REFS = [
    "docs/cua/COMPUTER_USE_CUA_CONTRACT.md",
    "docs/cua/cua_release_surface_manifest.json",
]


class ComputerUseCapabilityStatus(str, Enum):
    blocked = "blocked"
    experimental = "experimental"
    unavailable = "unavailable"
    observe_only_planned = "observe_only_planned"
    proposal_only_planned = "proposal_only_planned"


class ComputerUseDriverPresence(str, Enum):
    absent = "absent"
    noop = "noop"
    external_unverified = "external_unverified"
    available_untrusted = "available_untrusted"


class ComputerUseActionKind(str, Enum):
    capture = "capture"
    click = "click"
    type = "type"
    key = "key"
    scroll = "scroll"
    drag = "drag"
    focus_app = "focus_app"


class ComputerUseActionMode(str, Enum):
    observe_only = "observe_only"
    proposal_only = "proposal_only"
    blocked = "blocked"


class ComputerUseDoctorStatus(str, Enum):
    unavailable = "unavailable"
    blocked = "blocked"
    missing_permission = "missing_permission"
    degraded = "degraded"
    available_untrusted = "available_untrusted"


class ComputerUseRiskClass(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"
    forbidden = "forbidden"


class _ComputerUseContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ComputerUseCapabilityContract(_ComputerUseContractModel):
    capability_ref: str
    lane_ref: str
    status: ComputerUseCapabilityStatus = ComputerUseCapabilityStatus.blocked
    backend_ref: str
    driver_presence: ComputerUseDriverPresence = ComputerUseDriverPresence.absent
    advertised_capability_refs: list[str] = Field(default_factory=list)
    unsupported_capability_refs: list[str] = Field(default_factory=list)
    health_check_refs: list[str] = Field(default_factory=list)
    approval_requirement_refs: list[str] = Field(default_factory=list)
    blocked_action_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    safe_disable_ref: str
    release_surface_ref: str
    contract_only: bool = True
    runtime_driver_enabled: bool = False
    screenshot_capture_enabled: bool = False
    os_accessibility_probe_enabled: bool = False
    browser_automation_enabled: bool = False
    native_desktop_automation_enabled: bool = False
    action_execution_enabled: bool = False
    connector_write_enabled: bool = False
    provider_call_enabled: bool = False
    subprocess_driver_launch_enabled: bool = False
    production_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> ComputerUseCapabilityContract:
        _validate_ref_fields(
            [
                (self.capability_ref, "capability_ref"),
                (self.lane_ref, "lane_ref"),
                (self.backend_ref, "backend_ref"),
                (self.safe_disable_ref, "safe_disable_ref"),
                (self.release_surface_ref, "release_surface_ref"),
            ]
        )
        _validate_ref_list_fields(
            [
                (self.advertised_capability_refs, "advertised_capability_ref"),
                (self.unsupported_capability_refs, "unsupported_capability_ref"),
                (self.health_check_refs, "health_check_ref"),
                (self.approval_requirement_refs, "approval_requirement_ref"),
                (self.blocked_action_refs, "blocked_action_ref"),
                (self.evidence_refs, "evidence_ref"),
                (self.receipt_refs, "receipt_ref"),
            ]
        )
        _validate_safe_payload(self.model_dump(mode="python"))
        return self


class ComputerUseActionEnvelope(_ComputerUseContractModel):
    action_envelope_ref: str
    proposed_action: ComputerUseActionKind
    action_mode: ComputerUseActionMode = ComputerUseActionMode.blocked
    app_ref: str
    window_ref: str
    snapshot_ref: str
    element_token_ref: str
    element_token_validity_ref: str
    risk_class: ComputerUseRiskClass = ComputerUseRiskClass.high
    approval_scope_ref: str
    idempotency_ref: str
    rollback_ref: str
    safe_disable_ref: str
    receipt_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    blocked_state_refs: list[str] = Field(default_factory=list)
    password_entry_requested: bool = False
    credential_entry_requested: bool = False
    two_factor_handling_requested: bool = False
    permission_dialog_interaction_requested: bool = False
    security_settings_change_requested: bool = False
    account_deletion_requested: bool = False
    billing_change_requested: bool = False
    connector_write_requested: bool = False
    shell_payload_typing_requested: bool = False
    prompt_or_screenshot_instruction_authority_requested: bool = False
    automatic_execution_requested: bool = False
    action_execution_performed: bool = False
    driver_invocation_performed: bool = False
    receipt_written: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> ComputerUseActionEnvelope:
        _validate_ref_fields(
            [
                (self.action_envelope_ref, "action_envelope_ref"),
                (self.app_ref, "app_ref"),
                (self.window_ref, "window_ref"),
                (self.snapshot_ref, "snapshot_ref"),
                (self.element_token_ref, "element_token_ref"),
                (self.element_token_validity_ref, "element_token_validity_ref"),
                (self.approval_scope_ref, "approval_scope_ref"),
                (self.idempotency_ref, "idempotency_ref"),
                (self.rollback_ref, "rollback_ref"),
                (self.safe_disable_ref, "safe_disable_ref"),
                (self.receipt_ref, "receipt_ref"),
            ]
        )
        _validate_ref_list_fields(
            [
                (self.evidence_refs, "evidence_ref"),
                (self.blocked_state_refs, "blocked_state_ref"),
            ]
        )
        _validate_safe_payload(self.model_dump(mode="python"))
        return self


class ComputerUseDoctorResult(_ComputerUseContractModel):
    status: ComputerUseDoctorStatus = ComputerUseDoctorStatus.unavailable
    platform_ref: str
    permission_state_refs: list[str] = Field(default_factory=list)
    driver_version_ref: str
    capability_refs: list[str] = Field(default_factory=list)
    lifecycle_state_ref: str
    idle_behavior_ref: str
    safe_disable_ref: str
    evidence_refs: list[str] = Field(default_factory=list)
    contract_only: bool = True
    os_permission_inspection_performed: bool = False
    app_window_inspection_performed: bool = False
    display_inspection_performed: bool = False
    installed_binary_inspection_performed: bool = False
    process_inspection_performed: bool = False
    driver_launch_performed: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> ComputerUseDoctorResult:
        _validate_ref_fields(
            [
                (self.platform_ref, "platform_ref"),
                (self.driver_version_ref, "driver_version_ref"),
                (self.lifecycle_state_ref, "lifecycle_state_ref"),
                (self.idle_behavior_ref, "idle_behavior_ref"),
                (self.safe_disable_ref, "safe_disable_ref"),
            ]
        )
        _validate_ref_list_fields(
            [
                (self.permission_state_refs, "permission_state_ref"),
                (self.capability_refs, "capability_ref"),
                (self.evidence_refs, "evidence_ref"),
            ]
        )
        _validate_safe_payload(self.model_dump(mode="python"))
        return self


def build_default_computer_use_capability_contract() -> ComputerUseCapabilityContract:
    return validate_computer_use_capability_contract(
        ComputerUseCapabilityContract(
            capability_ref="cua-capability:contract-only",
            lane_ref="cua-lane:contract-only",
            status=ComputerUseCapabilityStatus.blocked,
            backend_ref="cua-backend:none",
            driver_presence=ComputerUseDriverPresence.absent,
            advertised_capability_refs=["cua-capability:future-observe-proposal"],
            unsupported_capability_refs=[
                "cua-capability:click",
                "cua-capability:type",
                "cua-capability:drag",
                "cua-capability:scroll",
                "cua-capability:browser-automation",
                "cua-capability:native-desktop-automation",
            ],
            health_check_refs=["cua-health:unavailable-contract-only"],
            approval_requirement_refs=["approval-requirement:exact-action-envelope-future"],
            blocked_action_refs=[
                "cua-action:password-entry",
                "cua-action:credential-entry",
                "cua-action:permission-dialog",
                "cua-action:shell-payload-typing",
                "cua-action:automatic-execution",
            ],
            evidence_refs=["evidence:cua-contract-lane"],
            receipt_refs=["receipt:cua-future-action-envelope"],
            safe_disable_ref="safe-disable:cua-lane-disabled",
            release_surface_ref="release-surface:cua-blocked-contract-only",
        )
    )


def build_blocked_computer_use_action_envelope(
    *,
    action_envelope_ref: str = "cua-action-envelope:blocked-proposal",
    proposed_action: ComputerUseActionKind = ComputerUseActionKind.click,
) -> ComputerUseActionEnvelope:
    return validate_computer_use_action_envelope(
        ComputerUseActionEnvelope(
            action_envelope_ref=action_envelope_ref,
            proposed_action=proposed_action,
            action_mode=ComputerUseActionMode.blocked,
            app_ref="app-ref:future-local-app",
            window_ref="window-ref:future-snapshot-window",
            snapshot_ref="snapshot-ref:future-redacted-snapshot",
            element_token_ref="element-token-ref:future-snapshot-bound-token",
            element_token_validity_ref="element-token-validity:single-snapshot-only",
            risk_class=ComputerUseRiskClass.high,
            approval_scope_ref="approval-scope:future-exact-cua-action",
            idempotency_ref="idempotency:cua-proposal-only",
            rollback_ref="rollback:cua-no-execution",
            safe_disable_ref="safe-disable:cua-lane-disabled",
            receipt_ref="receipt:cua-blocked-proposal",
            evidence_refs=["evidence:cua-proposal-only"],
            blocked_state_refs=["blocked-state:cua-action-execution-denied"],
        )
    )


def build_default_computer_use_doctor_result() -> ComputerUseDoctorResult:
    return validate_computer_use_doctor_result(
        ComputerUseDoctorResult(
            status=ComputerUseDoctorStatus.unavailable,
            platform_ref="platform-ref:not-inspected",
            permission_state_refs=["permission-state:not-inspected"],
            driver_version_ref="driver-version:not-inspected",
            capability_refs=["cua-capability:contract-only"],
            lifecycle_state_ref="driver-lifecycle:absent",
            idle_behavior_ref="idle-behavior:no-driver",
            safe_disable_ref="safe-disable:cua-lane-disabled",
            evidence_refs=["evidence:cua-doctor-contract-only"],
        )
    )


def validate_computer_use_capability_contract(
    contract: ComputerUseCapabilityContract,
) -> ComputerUseCapabilityContract:
    validated = ComputerUseCapabilityContract.model_validate(_model_payload(contract))
    if not validated.contract_only:
        raise ValueError("CUA_CONTRACT_ONLY_REQUIRED")
    if validated.status not in _ALLOWED_CAPABILITY_STATUSES:
        raise ValueError("CUA_STATUS_MUST_BE_BLOCKED_OR_PLANNED")
    for field_name, reason in _CAPABILITY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_computer_use_action_envelope(
    envelope: ComputerUseActionEnvelope,
) -> ComputerUseActionEnvelope:
    validated = ComputerUseActionEnvelope.model_validate(_model_payload(envelope))
    if (
        validated.proposed_action in _MUTATING_ACTIONS
        and validated.action_mode != ComputerUseActionMode.blocked
    ):
        raise ValueError("CUA_MUTATING_ACTIONS_DEFAULT_BLOCKED")
    if (
        validated.proposed_action == ComputerUseActionKind.capture
        and validated.action_mode == ComputerUseActionMode.observe_only
    ):
        pass
    elif validated.action_mode != ComputerUseActionMode.blocked:
        raise ValueError("CUA_ACTION_MODE_NOT_GRANTED")
    for field_name, reason in _ACTION_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


def validate_computer_use_doctor_result(result: ComputerUseDoctorResult) -> ComputerUseDoctorResult:
    validated = ComputerUseDoctorResult.model_validate(_model_payload(result))
    if not validated.contract_only:
        raise ValueError("CUA_DOCTOR_CONTRACT_ONLY_REQUIRED")
    for field_name, reason in _DOCTOR_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    return validated


_ALLOWED_CAPABILITY_STATUSES = {
    ComputerUseCapabilityStatus.blocked,
    ComputerUseCapabilityStatus.experimental,
    ComputerUseCapabilityStatus.unavailable,
    ComputerUseCapabilityStatus.observe_only_planned,
    ComputerUseCapabilityStatus.proposal_only_planned,
}

_MUTATING_ACTIONS = {
    ComputerUseActionKind.click,
    ComputerUseActionKind.type,
    ComputerUseActionKind.key,
    ComputerUseActionKind.scroll,
    ComputerUseActionKind.drag,
    ComputerUseActionKind.focus_app,
}

_CAPABILITY_DENIALS = [
    ("runtime_driver_enabled", "CUA_RUNTIME_DRIVER_DENIED"),
    ("screenshot_capture_enabled", "CUA_SCREENSHOT_CAPTURE_DENIED"),
    ("os_accessibility_probe_enabled", "CUA_OS_ACCESSIBILITY_PROBE_DENIED"),
    ("browser_automation_enabled", "CUA_BROWSER_AUTOMATION_DENIED"),
    ("native_desktop_automation_enabled", "CUA_NATIVE_DESKTOP_AUTOMATION_DENIED"),
    ("action_execution_enabled", "CUA_ACTION_EXECUTION_DENIED"),
    ("connector_write_enabled", "CUA_CONNECTOR_WRITE_DENIED"),
    ("provider_call_enabled", "CUA_PROVIDER_CALL_DENIED"),
    ("subprocess_driver_launch_enabled", "CUA_SUBPROCESS_DRIVER_LAUNCH_DENIED"),
    ("production_authority_enabled", "CUA_PRODUCTION_AUTHORITY_DENIED"),
]

_ACTION_DENIALS = [
    ("password_entry_requested", "CUA_PASSWORD_ENTRY_DENIED"),
    ("credential_entry_requested", "CUA_CREDENTIAL_ENTRY_DENIED"),
    ("two_factor_handling_requested", "CUA_2FA_HANDLING_DENIED"),
    ("permission_dialog_interaction_requested", "CUA_PERMISSION_DIALOG_DENIED"),
    ("security_settings_change_requested", "CUA_SECURITY_SETTINGS_DENIED"),
    ("account_deletion_requested", "CUA_ACCOUNT_DELETION_DENIED"),
    ("billing_change_requested", "CUA_BILLING_CHANGE_DENIED"),
    ("connector_write_requested", "CUA_CONNECTOR_WRITE_DENIED"),
    ("shell_payload_typing_requested", "CUA_SHELL_PAYLOAD_TYPING_DENIED"),
    (
        "prompt_or_screenshot_instruction_authority_requested",
        "CUA_PROMPT_SCREENSHOT_AUTHORITY_DENIED",
    ),
    ("automatic_execution_requested", "CUA_AUTOMATIC_EXECUTION_DENIED"),
    ("action_execution_performed", "CUA_ACTION_EXECUTION_DENIED"),
    ("driver_invocation_performed", "CUA_DRIVER_INVOCATION_DENIED"),
    ("receipt_written", "CUA_RECEIPT_WRITE_DENIED"),
]

_DOCTOR_DENIALS = [
    ("os_permission_inspection_performed", "CUA_OS_PERMISSION_INSPECTION_DENIED"),
    ("app_window_inspection_performed", "CUA_APP_WINDOW_INSPECTION_DENIED"),
    ("display_inspection_performed", "CUA_DISPLAY_INSPECTION_DENIED"),
    ("installed_binary_inspection_performed", "CUA_BINARY_INSPECTION_DENIED"),
    ("process_inspection_performed", "CUA_PROCESS_INSPECTION_DENIED"),
    ("driver_launch_performed", "CUA_DRIVER_LAUNCH_DENIED"),
]

_UNSAFE_VALUE_FRAGMENTS = (
    "raw screenshot",
    "raw_screenshot",
    "screenshot_bytes",
    "raw ocr",
    "raw_ocr",
    "raw accessibility",
    "accessibility-tree",
    "accessibility_tree",
    "private ui",
    "private_ui",
    "private screen",
    "provider payload",
    "provider_payload",
    "raw provider",
    "raw_prompt",
    "raw_response",
    "api_key",
    "authorization:",
    "authorization=",
    "bearer ",
    "cookie:",
    "cookie=",
    "client_secret",
    "private key",
    "-----begin",
    "credential entry",
    "password entry",
)

_RAW_PATH_FRAGMENTS = ("/users/", "/home/", "/var/", "/etc/", ":\\")


def _validate_ref_fields(refs: list[tuple[str, str]]) -> None:
    for value, field_name in refs:
        _validate_m61_ref(value, field_name)


def _validate_ref_list_fields(ref_lists: list[tuple[list[str], str]]) -> None:
    for refs, field_name in ref_lists:
        if not refs:
            raise ValueError(f"{field_name} is required")
        for ref in refs:
            _validate_m61_ref(ref, field_name)


def _validate_safe_payload(value: Any) -> None:
    _scan_for_unsafe_value_fragments(value)
    _validate_safe_values(value)


def _scan_for_unsafe_value_fragments(value: Any) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_VALUE_FRAGMENTS):
            raise ValueError("CUA_RAW_PRIVATE_CONTENT_DENIED")
        return
    if isinstance(value, list):
        for item in value:
            _scan_for_unsafe_value_fragments(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _scan_for_unsafe_value_fragments(item)


def _validate_safe_values(value: Any) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in _RAW_PATH_FRAGMENTS):
            raise ValueError("CUA_RAW_PRIVATE_CONTENT_DENIED")
        return
    if isinstance(value, list):
        for item in value:
            _validate_safe_values(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _validate_safe_values(item)


def _model_payload(model: BaseModel) -> dict[str, Any]:
    payload = model.model_dump(mode="python", round_trip=True)
    extra = getattr(model, "__pydantic_extra__", None)
    if extra:
        payload.update(extra)
    return payload
