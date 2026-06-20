from __future__ import annotations

from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret, redact_secret_value
from ultimate_ai_agent.core.time import utc_now


SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
SAFE_COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.,:/()+#;-]{0,799}$")
SAFE_ROUTE_RE = re.compile(r"^/[A-Za-z0-9_./{}:-]{0,179}$")
MAX_LOG_PREVIEW_CHARS = 400
MAX_DETAIL_PREVIEW_CHARS = 800


class MacOSSetupStepStatus(str, Enum):
    planned = "planned"
    ready = "ready"
    dry_run_only = "dry_run_only"
    approval_required = "approval_required"
    blocked = "blocked"
    manual_only = "manual_only"


class MacOSSetupStepKind(str, Enum):
    first_launch = "first_launch"
    runtime_health = "runtime_health"
    local_model_readiness = "local_model_readiness"
    model_selection = "model_selection"
    setup_question = "setup_question"
    openwebui_bridge = "openwebui_bridge"
    mattermost_bridge = "mattermost_bridge"
    approval = "approval"
    receipt_audit_latency = "receipt_audit_latency"
    rollback_uninstall = "rollback_uninstall"


class _MacOSSetupModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MacOSSetupHardwareProfile(_MacOSSetupModel):
    profile_ref: str = "macos-setup-hardware:unknown"
    chip_family_bucket: str = "apple-silicon-or-intel:unknown"
    memory_bucket: str = "ram:unknown"
    disk_budget_bucket: str = "disk:unknown"
    metal_support_bucket: str = "metal:unknown"
    local_probe_performed: bool = False
    raw_hostname_included: bool = False
    raw_serial_included: bool = False
    raw_username_included: bool = False
    raw_path_included: bool = False
    env_dump_included: bool = False
    subprocess_execution_performed: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_ref(self.profile_ref, "profile_ref")
        for field_name in [
            "chip_family_bucket",
            "memory_bucket",
            "disk_budget_bucket",
            "metal_support_bucket",
        ]:
            _validate_safe_text(getattr(self, field_name), field_name, MAX_DETAIL_PREVIEW_CHARS)
        for field_name, reason in [
            ("raw_hostname_included", "MACOS_SETUP_HOSTNAME_DENIED"),
            ("raw_serial_included", "MACOS_SETUP_SERIAL_DENIED"),
            ("raw_username_included", "MACOS_SETUP_USERNAME_DENIED"),
            ("raw_path_included", "MACOS_SETUP_RAW_PATH_DENIED"),
            ("env_dump_included", "MACOS_SETUP_ENV_DUMP_DENIED"),
            ("subprocess_execution_performed", "MACOS_SETUP_SUBPROCESS_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class MacOSSetupStep(_MacOSSetupModel):
    step_id: str
    kind: MacOSSetupStepKind
    label: str
    status: MacOSSetupStepStatus
    safe_summary: str
    route_refs: list[str] = Field(default_factory=list)
    detail_preview: list[str] = Field(default_factory=list)
    log_preview: list[str] = Field(default_factory=list)
    approval_required: bool = False
    approval_ref: str | None = None
    receipt_ref: str
    rollback_ref: str
    latency_ref: str | None = None
    state_change_allowed: bool = False
    state_change_performed: bool = False
    terminal_command_executed: bool = False
    model_download_performed: bool = False
    launch_agent_changed: bool = False
    background_service_changed: bool = False
    raw_log_stored: bool = False
    raw_prompt_stored: bool = False
    credential_material_stored: bool = False
    model_output_authoritative: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    next_safe_action: str = "inspect_setup_plan"

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_ref(self.step_id, "step_id")
        for value, field_name in [
            (self.receipt_ref, "receipt_ref"),
            (self.rollback_ref, "rollback_ref"),
            (self.next_safe_action, "next_safe_action"),
        ]:
            _validate_ref(value, field_name)
        if self.approval_ref is not None:
            _validate_ref(self.approval_ref, "approval_ref")
        if self.latency_ref is not None:
            _validate_ref(self.latency_ref, "latency_ref")
        _validate_safe_text(self.label, "label", 120)
        _validate_safe_text(self.safe_summary, "safe_summary", MAX_DETAIL_PREVIEW_CHARS)
        for ref in self.route_refs:
            _validate_route_ref(ref)
        self.detail_preview = [
            _validate_safe_text(item, "detail_preview", MAX_DETAIL_PREVIEW_CHARS)
            for item in self.detail_preview
        ]
        self.log_preview = [
            _validate_safe_text(item, "log_preview", MAX_LOG_PREVIEW_CHARS)
            for item in self.log_preview
        ]
        self.reason_codes = [_validate_ref(code, "reason_code") for code in self.reason_codes]
        if self.status == MacOSSetupStepStatus.approval_required and not self.approval_required:
            raise ValueError("MACOS_SETUP_APPROVAL_FLAG_REQUIRED")
        _deny_side_effect_flags(self)
        return self


class MacOSSetupModelRecommendation(_MacOSSetupModel):
    recommendation_ref: str
    model_ref: str
    display_name: str
    fit_summary: str
    recommended_for: str
    memory_bucket: str
    disk_bucket: str
    privacy_summary: str = "Runs through local UAA setup planning; no model call is made by this recommendation."
    approval_required_before_download: bool = True
    selected_by_default: bool = False
    model_download_performed: bool = False
    model_file_read_performed: bool = False
    model_call_performed: bool = False
    raw_model_url_included: bool = False
    raw_local_path_included: bool = False
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.recommendation_ref, "recommendation_ref"),
            (self.model_ref, "model_ref"),
        ]:
            _validate_ref(value, field_name)
        for value, field_name in [
            (self.display_name, "display_name"),
            (self.fit_summary, "fit_summary"),
            (self.recommended_for, "recommended_for"),
            (self.memory_bucket, "memory_bucket"),
            (self.disk_bucket, "disk_bucket"),
            (self.privacy_summary, "privacy_summary"),
        ]:
            _validate_safe_text(value, field_name, MAX_DETAIL_PREVIEW_CHARS)
        self.reason_codes = [_validate_ref(code, "reason_code") for code in self.reason_codes]
        for field_name, reason in [
            ("model_download_performed", "MACOS_SETUP_MODEL_DOWNLOAD_DENIED"),
            ("model_file_read_performed", "MACOS_SETUP_MODEL_FILE_READ_DENIED"),
            ("model_call_performed", "MACOS_SETUP_MODEL_CALL_DENIED"),
            ("raw_model_url_included", "MACOS_SETUP_RAW_MODEL_URL_DENIED"),
            ("raw_local_path_included", "MACOS_SETUP_RAW_LOCAL_PATH_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class MacOSSetupBridgePreview(_MacOSSetupModel):
    bridge_ref: str
    label: str
    status: MacOSSetupStepStatus
    safe_summary: str
    enablement_default: str = "disabled"
    approval_required: bool = True
    credential_material_stored: bool = False
    raw_transcript_stored: bool = False
    connector_write_performed: bool = False
    reason_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_ref(self.bridge_ref, "bridge_ref")
        _validate_safe_text(self.label, "label", 120)
        _validate_safe_text(self.safe_summary, "safe_summary", MAX_DETAIL_PREVIEW_CHARS)
        _validate_safe_text(self.enablement_default, "enablement_default", 80)
        self.reason_codes = [_validate_ref(code, "reason_code") for code in self.reason_codes]
        for field_name, reason in [
            ("credential_material_stored", "MACOS_SETUP_CREDENTIAL_STORAGE_DENIED"),
            ("raw_transcript_stored", "MACOS_SETUP_RAW_TRANSCRIPT_DENIED"),
            ("connector_write_performed", "MACOS_SETUP_CONNECTOR_WRITE_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class MacOSSetupReceiptPlan(_MacOSSetupModel):
    receipt_plan_ref: str = "macos-setup-receipt-plan:foundation"
    audit_ref: str = "macos-setup-audit:foundation"
    latency_ref: str = "macos-setup-latency:foundation"
    safe_summary: str = "Setup assistant receipt plan is preview-only; no installer side effect has occurred."
    receipt_created: bool = False
    audit_event_created: bool = False
    raw_log_stored: bool = False
    raw_prompt_stored: bool = False
    raw_provider_payload_stored: bool = False
    credential_material_stored: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.audit_ref, "audit_ref"),
            (self.latency_ref, "latency_ref"),
        ]:
            _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "safe_summary", MAX_DETAIL_PREVIEW_CHARS)
        for field_name, reason in [
            ("receipt_created", "MACOS_SETUP_RECEIPT_CREATION_DENIED_IN_PREVIEW"),
            ("audit_event_created", "MACOS_SETUP_AUDIT_CREATION_DENIED_IN_PREVIEW"),
            ("raw_log_stored", "MACOS_SETUP_RAW_LOG_DENIED"),
            ("raw_prompt_stored", "MACOS_SETUP_RAW_PROMPT_DENIED"),
            ("raw_provider_payload_stored", "MACOS_SETUP_RAW_PROVIDER_PAYLOAD_DENIED"),
            ("credential_material_stored", "MACOS_SETUP_CREDENTIAL_STORAGE_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class MacOSSetupRollbackPlan(_MacOSSetupModel):
    rollback_plan_ref: str = "macos-setup-rollback-plan:foundation"
    uninstall_ref: str = "macos-setup-uninstall:foundation"
    safe_summary: str = "Rollback is represented as planned refs only until a reviewed installer milestone exists."
    rollback_available_after_approval: bool = True
    rollback_executed: bool = False
    launch_agent_removed: bool = False
    model_files_removed: bool = False
    config_removed: bool = False

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.rollback_plan_ref, "rollback_plan_ref"),
            (self.uninstall_ref, "uninstall_ref"),
        ]:
            _validate_ref(value, field_name)
        _validate_safe_text(self.safe_summary, "safe_summary", MAX_DETAIL_PREVIEW_CHARS)
        for field_name, reason in [
            ("rollback_executed", "MACOS_SETUP_ROLLBACK_EXECUTION_DENIED"),
            ("launch_agent_removed", "MACOS_SETUP_LAUNCH_AGENT_MUTATION_DENIED"),
            ("model_files_removed", "MACOS_SETUP_MODEL_FILE_MUTATION_DENIED"),
            ("config_removed", "MACOS_SETUP_CONFIG_MUTATION_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        return self


class MacOSSetupAssistantPlan(_MacOSSetupModel):
    plan_ref: str = "macos-setup-plan:foundation"
    status: MacOSSetupStepStatus = MacOSSetupStepStatus.dry_run_only
    generated_at: str = Field(default_factory=lambda: utc_now().isoformat())
    macos_first: bool = True
    local_first: bool = True
    disabled_by_default: bool = True
    visual_shell_ref: str = "control-center:setup-assistant-preview"
    native_macos_app_ready: bool = False
    control_center_preview_ready: bool = True
    setup_question_assistant_enabled: bool = False
    model_output_authoritative: bool = False
    installer_side_effects_enabled: bool = False
    steps: list[MacOSSetupStep]
    model_recommendations: list[MacOSSetupModelRecommendation]
    bridge_previews: list[MacOSSetupBridgePreview]
    receipt_plan: MacOSSetupReceiptPlan = Field(default_factory=MacOSSetupReceiptPlan)
    rollback_plan: MacOSSetupRollbackPlan = Field(default_factory=MacOSSetupRollbackPlan)
    blocked_capabilities: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    morning_review_checklist: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_ref(self.plan_ref, "plan_ref")
        _validate_ref(self.visual_shell_ref, "visual_shell_ref")
        if not self.macos_first:
            raise ValueError("MACOS_SETUP_MACOS_FIRST_REQUIRED")
        if not self.local_first:
            raise ValueError("MACOS_SETUP_LOCAL_FIRST_REQUIRED")
        if not self.disabled_by_default:
            raise ValueError("MACOS_SETUP_DISABLED_BY_DEFAULT_REQUIRED")
        for field_name, reason in [
            ("native_macos_app_ready", "MACOS_SETUP_NATIVE_APP_READY_DENIED_IN_FOUNDATION"),
            ("setup_question_assistant_enabled", "MACOS_SETUP_ASSISTANT_QUERY_RUNTIME_DENIED"),
            ("model_output_authoritative", "MACOS_SETUP_MODEL_AUTHORITY_DENIED"),
            ("installer_side_effects_enabled", "MACOS_SETUP_INSTALLER_SIDE_EFFECTS_DENIED"),
        ]:
            if getattr(self, field_name):
                raise ValueError(reason)
        if not self.steps:
            raise ValueError("MACOS_SETUP_STEPS_REQUIRED")
        if not self.model_recommendations:
            raise ValueError("MACOS_SETUP_MODEL_RECOMMENDATIONS_REQUIRED")
        self.blocked_capabilities = [
            _validate_ref(value, "blocked_capability") for value in self.blocked_capabilities
        ]
        self.next_steps = [
            _validate_safe_text(value, "next_step", MAX_DETAIL_PREVIEW_CHARS) for value in self.next_steps
        ]
        self.morning_review_checklist = [
            _validate_safe_text(value, "morning_review_checklist", MAX_DETAIL_PREVIEW_CHARS)
            for value in self.morning_review_checklist
        ]
        _validate_safe_payload(self.metadata)
        return self


def _validate_ref(value: str, field_name: str) -> str:
    if not SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name.upper()}_UNSAFE_REF")
    if contains_obvious_secret(value):
        raise ValueError(f"{field_name.upper()}_SECRET_LIKE")
    return value


def _validate_route_ref(value: str) -> str:
    if not SAFE_ROUTE_RE.match(value):
        raise ValueError("ROUTE_REF_UNSAFE")
    if redact_secret_value(value) != value or contains_obvious_secret(value):
        raise ValueError("ROUTE_REF_SECRET_LIKE")
    return value


def _validate_safe_text(value: str, field_name: str, max_length: int) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name.upper()}_REQUIRED")
    if len(text) > max_length:
        raise ValueError(f"{field_name.upper()}_TOO_LONG")
    if not SAFE_COMPONENT_RE.match(text):
        raise ValueError(f"{field_name.upper()}_UNSAFE_TEXT")
    if redact_secret_value(text) != text or contains_obvious_secret(text):
        raise ValueError(f"{field_name.upper()}_SECRET_LIKE")
    return text


def _validate_safe_payload(payload: dict[str, Any]) -> None:
    if contains_obvious_secret(payload):
        raise ValueError("MACOS_SETUP_METADATA_SECRET_LIKE")
    for key, value in payload.items():
        _validate_safe_text(str(key), "metadata_key", 120)
        if isinstance(value, str):
            _validate_safe_text(value, "metadata_value", MAX_DETAIL_PREVIEW_CHARS)
        elif isinstance(value, bool | int | float):
            continue
        else:
            raise ValueError("MACOS_SETUP_METADATA_VALUE_UNSUPPORTED")


def _deny_side_effect_flags(step: MacOSSetupStep) -> None:
    for field_name, reason in [
        ("state_change_allowed", "MACOS_SETUP_STATE_CHANGE_DENIED_IN_FOUNDATION"),
        ("state_change_performed", "MACOS_SETUP_STATE_CHANGE_PERFORMED_DENIED"),
        ("terminal_command_executed", "MACOS_SETUP_TERMINAL_EXECUTION_DENIED"),
        ("model_download_performed", "MACOS_SETUP_MODEL_DOWNLOAD_DENIED"),
        ("launch_agent_changed", "MACOS_SETUP_LAUNCH_AGENT_MUTATION_DENIED"),
        ("background_service_changed", "MACOS_SETUP_BACKGROUND_SERVICE_MUTATION_DENIED"),
        ("raw_log_stored", "MACOS_SETUP_RAW_LOG_DENIED"),
        ("raw_prompt_stored", "MACOS_SETUP_RAW_PROMPT_DENIED"),
        ("credential_material_stored", "MACOS_SETUP_CREDENTIAL_STORAGE_DENIED"),
        ("model_output_authoritative", "MACOS_SETUP_MODEL_AUTHORITY_DENIED"),
    ]:
        if getattr(step, field_name):
            raise ValueError(reason)
