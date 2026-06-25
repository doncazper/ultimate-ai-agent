from __future__ import annotations

from enum import Enum
import platform
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.secrets.redaction import contains_obvious_secret
from ultimate_ai_agent.core.time import utc_now


SAFE_REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{2,190}$")
SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.,:;()+#&%-]{0,799}$")
RAW_PATH_FRAGMENT_RE = re.compile(
    r"(?i)(^|[\s\"'`])(~[/\\]?|/(Users|usr|var|private|tmp)(/|$)|[A-Z]:[\\/]|\\\\[^\\\s]+\\)"
)
MAX_SAFE_TEXT_CHARS = 800


class PlatformOSBucket(str, Enum):
    macos = "macos"
    windows = "windows"
    linux = "linux"
    wsl = "wsl"
    unknown = "unknown"


class PlatformArchitectureBucket(str, Enum):
    arm64 = "arm64"
    x86_64 = "x86_64"
    other = "other"
    unknown = "unknown"


class PlatformCapabilityState(str, Enum):
    metadata_only = "metadata_only"
    readiness_only = "readiness_only"
    not_configured = "not_configured"
    blocked = "blocked"
    unsupported = "unsupported"
    planned_disabled = "planned_disabled"


class PlatformCapabilityAuthorityState(str, Enum):
    metadata_only = "metadata_only"
    readiness_only = "readiness_only"
    proposal_only = "proposal_only"
    read_only_requires_approval = "read_only_requires_approval"
    blocked = "blocked"
    not_scoped = "not_scoped"


class PlatformCapabilityFamily(str, Enum):
    secure_credential_store = "secure_credential_store"
    notification_delivery = "notification_delivery"
    startup_item = "startup_item"
    local_calendar_metadata = "local_calendar_metadata"
    email_account_metadata = "email_account_metadata"
    conversation_source_metadata = "conversation_source_metadata"
    local_model_runtime = "local_model_runtime"
    control_center_shell = "control_center_shell"
    installer_channel = "installer_channel"


class _PlatformCapabilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class PlatformIdentity(_PlatformCapabilityModel):
    identity_ref: str = "platform-identity:detected"
    os: PlatformOSBucket
    architecture: PlatformArchitectureBucket
    detector_ref: str = "platform-detector:python-platform-safe-buckets"
    safe_summary: str = "Safe platform bucket detected for metadata readiness only."
    raw_system_value_included: bool = False
    raw_machine_value_included: bool = False
    raw_release_value_included: bool = False
    raw_hostname_included: bool = False
    raw_username_included: bool = False
    raw_path_included: bool = False
    env_dump_included: bool = False
    raw_serial_included: bool = False
    filesystem_scan_performed: bool = False
    subprocess_execution_performed: bool = False
    network_call_performed: bool = False
    credential_read_performed: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref(self.identity_ref, "identity_ref")
        _validate_ref(self.detector_ref, "detector_ref")
        _validate_safe_text(self.safe_summary, "safe_summary")
        _deny_true_flags(
            self,
            [
                ("raw_system_value_included", "PLATFORM_IDENTITY_RAW_SYSTEM_DENIED"),
                ("raw_machine_value_included", "PLATFORM_IDENTITY_RAW_MACHINE_DENIED"),
                ("raw_release_value_included", "PLATFORM_IDENTITY_RAW_RELEASE_DENIED"),
                ("raw_hostname_included", "PLATFORM_IDENTITY_HOSTNAME_DENIED"),
                ("raw_username_included", "PLATFORM_IDENTITY_USERNAME_DENIED"),
                ("raw_path_included", "PLATFORM_IDENTITY_RAW_PATH_DENIED"),
                ("env_dump_included", "PLATFORM_IDENTITY_ENV_DUMP_DENIED"),
                ("raw_serial_included", "PLATFORM_IDENTITY_SERIAL_DENIED"),
                ("filesystem_scan_performed", "PLATFORM_IDENTITY_FILESYSTEM_SCAN_DENIED"),
                ("subprocess_execution_performed", "PLATFORM_IDENTITY_SUBPROCESS_DENIED"),
                ("network_call_performed", "PLATFORM_IDENTITY_NETWORK_DENIED"),
                ("credential_read_performed", "PLATFORM_IDENTITY_CREDENTIAL_READ_DENIED"),
            ],
        )
        return self


class PlatformCapabilityAuthority(_PlatformCapabilityModel):
    authority_ref: str
    state: PlatformCapabilityAuthorityState = PlatformCapabilityAuthorityState.metadata_only
    runtime_authority_granted: bool = False
    install_authority_granted: bool = False
    read_authority_granted: bool = False
    write_authority_granted: bool = False
    credential_authority_granted: bool = False
    provider_authority_granted: bool = False
    service_authority_granted: bool = False
    permission_grant_captured: bool = False
    approval_ref_as_authority: bool = False
    production_authority_granted: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref(self.authority_ref, "authority_ref")
        _deny_true_flags(
            self,
            [
                ("runtime_authority_granted", "PLATFORM_AUTHORITY_RUNTIME_DENIED"),
                ("install_authority_granted", "PLATFORM_AUTHORITY_INSTALL_DENIED"),
                ("read_authority_granted", "PLATFORM_AUTHORITY_READ_DENIED"),
                ("write_authority_granted", "PLATFORM_AUTHORITY_WRITE_DENIED"),
                ("credential_authority_granted", "PLATFORM_AUTHORITY_CREDENTIAL_DENIED"),
                ("provider_authority_granted", "PLATFORM_AUTHORITY_PROVIDER_DENIED"),
                ("service_authority_granted", "PLATFORM_AUTHORITY_SERVICE_DENIED"),
                ("permission_grant_captured", "PLATFORM_AUTHORITY_PERMISSION_CAPTURE_DENIED"),
                ("approval_ref_as_authority", "PLATFORM_AUTHORITY_APPROVAL_REF_DENIED"),
                ("production_authority_granted", "PLATFORM_AUTHORITY_PRODUCTION_DENIED"),
            ],
        )
        return self


class PlatformInstallerPosture(_PlatformCapabilityModel):
    posture_ref: str
    state: PlatformCapabilityState = PlatformCapabilityState.metadata_only
    channel_ref: str
    safe_summary: str
    metadata_only: bool = True
    side_effects_enabled: bool = False
    installer_executed: bool = False
    file_write_performed: bool = False
    service_changed: bool = False
    startup_item_changed: bool = False
    subprocess_execution_performed: bool = False
    provider_call_performed: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref(self.posture_ref, "posture_ref")
        _validate_ref(self.channel_ref, "channel_ref")
        _validate_safe_text(self.safe_summary, "safe_summary")
        if not self.metadata_only:
            raise ValueError("PLATFORM_INSTALLER_METADATA_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("side_effects_enabled", "PLATFORM_INSTALLER_SIDE_EFFECTS_DENIED"),
                ("installer_executed", "PLATFORM_INSTALLER_EXECUTION_DENIED"),
                ("file_write_performed", "PLATFORM_INSTALLER_FILE_WRITE_DENIED"),
                ("service_changed", "PLATFORM_INSTALLER_SERVICE_CHANGE_DENIED"),
                ("startup_item_changed", "PLATFORM_INSTALLER_STARTUP_CHANGE_DENIED"),
                ("subprocess_execution_performed", "PLATFORM_INSTALLER_SUBPROCESS_DENIED"),
                ("provider_call_performed", "PLATFORM_INSTALLER_PROVIDER_CALL_DENIED"),
            ],
        )
        return self


class PlatformIntegrationPosture(_PlatformCapabilityModel):
    integration_ref: str
    state: PlatformCapabilityState = PlatformCapabilityState.metadata_only
    adapter_ref: str
    safe_summary: str
    metadata_only: bool = True
    configured: bool = False
    permission_prompted: bool = False
    os_data_read_performed: bool = False
    credential_read_performed: bool = False
    provider_call_performed: bool = False
    network_call_performed: bool = False
    service_check_performed: bool = False
    raw_payload_included: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref(self.integration_ref, "integration_ref")
        _validate_ref(self.adapter_ref, "adapter_ref")
        _validate_safe_text(self.safe_summary, "safe_summary")
        if not self.metadata_only:
            raise ValueError("PLATFORM_INTEGRATION_METADATA_ONLY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("configured", "PLATFORM_INTEGRATION_CONFIGURED_CLAIM_DENIED"),
                ("permission_prompted", "PLATFORM_INTEGRATION_PERMISSION_PROMPT_DENIED"),
                ("os_data_read_performed", "PLATFORM_INTEGRATION_OS_DATA_READ_DENIED"),
                ("credential_read_performed", "PLATFORM_INTEGRATION_CREDENTIAL_READ_DENIED"),
                ("provider_call_performed", "PLATFORM_INTEGRATION_PROVIDER_CALL_DENIED"),
                ("network_call_performed", "PLATFORM_INTEGRATION_NETWORK_DENIED"),
                ("service_check_performed", "PLATFORM_INTEGRATION_SERVICE_CHECK_DENIED"),
                ("raw_payload_included", "PLATFORM_INTEGRATION_RAW_PAYLOAD_DENIED"),
            ],
        )
        return self


class PlatformCapabilityRecord(_PlatformCapabilityModel):
    record_ref: str
    family: PlatformCapabilityFamily
    platform_os: PlatformOSBucket
    state: PlatformCapabilityState
    safe_label: str
    safe_summary: str
    authority: PlatformCapabilityAuthority
    integration_posture: PlatformIntegrationPosture
    installer_posture: PlatformInstallerPosture | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    metadata_only: bool = True
    runtime_action_performed: bool = False
    install_action_performed: bool = False
    filesystem_scan_performed: bool = False
    subprocess_execution_performed: bool = False
    network_call_performed: bool = False
    credential_read_performed: bool = False
    calendar_read_performed: bool = False
    email_read_performed: bool = False
    message_read_performed: bool = False
    service_started: bool = False
    provider_call_performed: bool = False
    file_write_performed: bool = False
    permission_prompted: bool = False
    authentication_performed: bool = False
    raw_username_included: bool = False
    raw_hostname_included: bool = False
    raw_path_included: bool = False
    env_dump_included: bool = False
    raw_log_included: bool = False
    credential_material_included: bool = False
    raw_prompt_included: bool = False
    raw_response_included: bool = False
    raw_provider_payload_included: bool = False
    production_authority_granted: bool = False

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref(self.record_ref, "record_ref")
        _validate_safe_text(self.safe_label, "safe_label", max_chars=120)
        _validate_safe_text(self.safe_summary, "safe_summary")
        self.evidence_refs = [_validate_ref(ref, "evidence_ref") for ref in self.evidence_refs]
        self.reason_codes = [_validate_ref(code, "reason_code") for code in self.reason_codes]
        _validate_safe_metadata(self.metadata, "metadata")
        if not self.metadata_only:
            raise ValueError("PLATFORM_CAPABILITY_METADATA_ONLY_REQUIRED")
        if self.authority.runtime_authority_granted or self.authority.install_authority_granted:
            raise ValueError("PLATFORM_CAPABILITY_AUTHORITY_DENIED")
        _deny_true_flags(
            self,
            [
                ("runtime_action_performed", "PLATFORM_CAPABILITY_RUNTIME_ACTION_DENIED"),
                ("install_action_performed", "PLATFORM_CAPABILITY_INSTALL_ACTION_DENIED"),
                ("filesystem_scan_performed", "PLATFORM_CAPABILITY_FILESYSTEM_SCAN_DENIED"),
                ("subprocess_execution_performed", "PLATFORM_CAPABILITY_SUBPROCESS_DENIED"),
                ("network_call_performed", "PLATFORM_CAPABILITY_NETWORK_DENIED"),
                ("credential_read_performed", "PLATFORM_CAPABILITY_CREDENTIAL_READ_DENIED"),
                ("calendar_read_performed", "PLATFORM_CAPABILITY_CALENDAR_READ_DENIED"),
                ("email_read_performed", "PLATFORM_CAPABILITY_EMAIL_READ_DENIED"),
                ("message_read_performed", "PLATFORM_CAPABILITY_MESSAGE_READ_DENIED"),
                ("service_started", "PLATFORM_CAPABILITY_SERVICE_START_DENIED"),
                ("provider_call_performed", "PLATFORM_CAPABILITY_PROVIDER_CALL_DENIED"),
                ("file_write_performed", "PLATFORM_CAPABILITY_FILE_WRITE_DENIED"),
                ("permission_prompted", "PLATFORM_CAPABILITY_PERMISSION_PROMPT_DENIED"),
                ("authentication_performed", "PLATFORM_CAPABILITY_AUTH_DENIED"),
                ("raw_username_included", "PLATFORM_CAPABILITY_USERNAME_DENIED"),
                ("raw_hostname_included", "PLATFORM_CAPABILITY_HOSTNAME_DENIED"),
                ("raw_path_included", "PLATFORM_CAPABILITY_RAW_PATH_DENIED"),
                ("env_dump_included", "PLATFORM_CAPABILITY_ENV_DUMP_DENIED"),
                ("raw_log_included", "PLATFORM_CAPABILITY_RAW_LOG_DENIED"),
                ("credential_material_included", "PLATFORM_CAPABILITY_CREDENTIAL_MATERIAL_DENIED"),
                ("raw_prompt_included", "PLATFORM_CAPABILITY_RAW_PROMPT_DENIED"),
                ("raw_response_included", "PLATFORM_CAPABILITY_RAW_RESPONSE_DENIED"),
                ("raw_provider_payload_included", "PLATFORM_CAPABILITY_RAW_PROVIDER_PAYLOAD_DENIED"),
                ("production_authority_granted", "PLATFORM_CAPABILITY_PRODUCTION_AUTHORITY_DENIED"),
            ],
        )
        return self


class PlatformCapabilitySnapshot(_PlatformCapabilityModel):
    snapshot_ref: str = "platform-capability-snapshot:metadata-readiness"
    generated_at: str = Field(default_factory=lambda: utc_now().isoformat())
    platform_identity: PlatformIdentity
    capabilities: list[PlatformCapabilityRecord]
    blocked_by_default: bool = True
    metadata_only: bool = True
    no_authority_granted: bool = True
    installer_side_effects_enabled: bool = False
    platform_probe_performed: bool = False
    summary: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_ref(self.snapshot_ref, "snapshot_ref")
        _validate_safe_text(self.generated_at, "generated_at", max_chars=80)
        _validate_safe_metadata(self.summary, "summary")
        if not self.blocked_by_default:
            raise ValueError("PLATFORM_SNAPSHOT_BLOCKED_BY_DEFAULT_REQUIRED")
        if not self.metadata_only:
            raise ValueError("PLATFORM_SNAPSHOT_METADATA_ONLY_REQUIRED")
        if not self.no_authority_granted:
            raise ValueError("PLATFORM_SNAPSHOT_NO_AUTHORITY_REQUIRED")
        _deny_true_flags(
            self,
            [
                ("installer_side_effects_enabled", "PLATFORM_SNAPSHOT_INSTALLER_SIDE_EFFECTS_DENIED"),
                ("platform_probe_performed", "PLATFORM_SNAPSHOT_PLATFORM_PROBE_DENIED"),
            ],
        )
        families = [record.family for record in self.capabilities]
        if set(families) != set(PlatformCapabilityFamily):
            raise ValueError("PLATFORM_SNAPSHOT_CANONICAL_FAMILIES_REQUIRED")
        if len(families) != len(set(families)):
            raise ValueError("PLATFORM_SNAPSHOT_DUPLICATE_FAMILIES_DENIED")
        if any(record.platform_os != self.platform_identity.os for record in self.capabilities):
            raise ValueError("PLATFORM_SNAPSHOT_OS_MISMATCH_DENIED")
        if any(not record.metadata_only for record in self.capabilities):
            raise ValueError("PLATFORM_SNAPSHOT_CAPABILITY_AUTHORITY_DENIED")
        return self


def detect_platform_identity() -> PlatformIdentity:
    system_value = platform.system()
    machine_value = platform.machine()
    release_value = platform.release()

    os_bucket = _bucket_system(system_value, release_value)
    architecture_bucket = _bucket_machine(machine_value)
    return PlatformIdentity(
        os=os_bucket,
        architecture=architecture_bucket,
        safe_summary="Safe platform bucket detected for metadata readiness only.",
    )


def build_platform_capability_snapshot(
    identity: PlatformIdentity | None = None,
) -> PlatformCapabilitySnapshot:
    platform_identity = identity or detect_platform_identity()
    capabilities = [
        _record(platform_identity.os, family)
        for family in PlatformCapabilityFamily
    ]
    return PlatformCapabilitySnapshot(
        platform_identity=platform_identity,
        capabilities=capabilities,
        summary={
            "platform_os": platform_identity.os.value,
            "architecture": platform_identity.architecture.value,
            "capability_count": len(capabilities),
            "metadata_only": True,
            "authority_granted": False,
            "installer_side_effects_enabled": False,
            "windows_first_class_posture": True,
            "macos_lead_dogfood_platform": True,
        },
    )


def _bucket_system(system_value: str, release_value: str) -> PlatformOSBucket:
    normalized = (system_value or "").strip().lower()
    release_normalized = (release_value or "").strip().lower()
    if normalized == "darwin":
        return PlatformOSBucket.macos
    if normalized == "windows":
        return PlatformOSBucket.windows
    if normalized == "linux" and ("microsoft" in release_normalized or "wsl" in release_normalized):
        return PlatformOSBucket.wsl
    if normalized == "linux":
        return PlatformOSBucket.linux
    return PlatformOSBucket.unknown


def _bucket_machine(machine_value: str) -> PlatformArchitectureBucket:
    normalized = (machine_value or "").strip().lower()
    if normalized in {"arm64", "aarch64"}:
        return PlatformArchitectureBucket.arm64
    if normalized in {"x86_64", "amd64"}:
        return PlatformArchitectureBucket.x86_64
    if normalized:
        return PlatformArchitectureBucket.other
    return PlatformArchitectureBucket.unknown


def _record(
    os_bucket: PlatformOSBucket,
    family: PlatformCapabilityFamily,
) -> PlatformCapabilityRecord:
    details = _capability_details(os_bucket, family)
    family_ref = family.value.replace("_", "-")
    os_ref = os_bucket.value
    authority_state = details["authority_state"]
    state = details["state"]
    return PlatformCapabilityRecord(
        record_ref=f"platform-capability:{os_ref}:{family_ref}",
        family=family,
        platform_os=os_bucket,
        state=state,
        safe_label=details["label"],
        safe_summary=details["summary"],
        authority=PlatformCapabilityAuthority(
            authority_ref=f"platform-authority:{os_ref}:{family_ref}",
            state=authority_state,
        ),
        integration_posture=PlatformIntegrationPosture(
            integration_ref=f"platform-integration:{os_ref}:{family_ref}",
            state=state,
            adapter_ref=details["adapter_ref"],
            safe_summary=details["integration_summary"],
        ),
        installer_posture=_installer_posture(os_bucket, family, state, details),
        evidence_refs=[
            "docs-ref:platform-capability-registry-contract",
            "test-ref:platform-capabilities-contracts",
        ],
        reason_codes=details["reason_codes"],
        metadata={
            "metadata_visibility_only": True,
            "callable_runtime": False,
            "platform_probe": False,
            "os_data_read": False,
            "provider_call": False,
        },
    )


def _installer_posture(
    os_bucket: PlatformOSBucket,
    family: PlatformCapabilityFamily,
    state: PlatformCapabilityState,
    details: dict[str, Any],
) -> PlatformInstallerPosture | None:
    if family != PlatformCapabilityFamily.installer_channel:
        return None
    family_ref = family.value.replace("_", "-")
    os_ref = os_bucket.value
    return PlatformInstallerPosture(
        posture_ref=f"platform-installer-posture:{os_ref}:{family_ref}",
        state=state,
        channel_ref=details["channel_ref"],
        safe_summary=details["installer_summary"],
    )


def _capability_details(
    os_bucket: PlatformOSBucket,
    family: PlatformCapabilityFamily,
) -> dict[str, Any]:
    matrix = _details_matrix()
    return matrix.get(os_bucket, matrix[PlatformOSBucket.unknown])[family]


def _details_matrix() -> dict[PlatformOSBucket, dict[PlatformCapabilityFamily, dict[str, Any]]]:
    return {
        PlatformOSBucket.macos: _platform_details(
            os_name="macOS",
            credential="Keychain",
            notification="user notifications",
            startup="LaunchAgent startup item",
            calendar="EventKit calendar metadata",
            email="Apple Mail or IMAP account metadata",
            conversation="iMessage conversation source metadata",
            installer_channel="macos-bootstrap-channel",
            installer_summary="macOS installer channel is metadata only and performs no bootstrap or file mutation.",
            startup_state=PlatformCapabilityState.planned_disabled,
            integration_state=PlatformCapabilityState.planned_disabled,
            installer_state=PlatformCapabilityState.metadata_only,
        ),
        PlatformOSBucket.windows: _platform_details(
            os_name="Windows",
            credential="Credential Manager and DPAPI",
            notification="toast notifications",
            startup="Task Scheduler or service startup item",
            calendar="Outlook or Microsoft Graph calendar metadata",
            email="Outlook or Microsoft Graph email account metadata",
            conversation="Teams Phone Link or Graph style conversation source metadata",
            installer_channel="windows-bootstrap-channel",
            installer_summary="Windows installer channel is planned disabled and performs no PowerShell MSIX winget or service mutation.",
            startup_state=PlatformCapabilityState.planned_disabled,
            integration_state=PlatformCapabilityState.planned_disabled,
            installer_state=PlatformCapabilityState.planned_disabled,
        ),
        PlatformOSBucket.linux: _platform_details(
            os_name="Linux",
            credential="desktop secret store potential",
            notification="desktop notification potential",
            startup="systemd user service potential",
            calendar="calendar metadata adapter potential",
            email="email account metadata adapter potential",
            conversation="conversation source metadata adapter potential",
            installer_channel="linux-installer-channel",
            installer_summary="Linux installer channel is unsupported in this contract slice and performs no mutation.",
            startup_state=PlatformCapabilityState.unsupported,
            integration_state=PlatformCapabilityState.unsupported,
            installer_state=PlatformCapabilityState.unsupported,
        ),
        PlatformOSBucket.wsl: _platform_details(
            os_name="WSL",
            credential="host credential store metadata potential",
            notification="host notification bridge metadata potential",
            startup="host startup item metadata potential",
            calendar="host calendar metadata adapter potential",
            email="host email metadata adapter potential",
            conversation="host conversation source metadata adapter potential",
            installer_channel="wsl-installer-channel",
            installer_summary="WSL installer channel is unsupported in this contract slice and performs no mutation.",
            startup_state=PlatformCapabilityState.unsupported,
            integration_state=PlatformCapabilityState.unsupported,
            installer_state=PlatformCapabilityState.unsupported,
        ),
        PlatformOSBucket.unknown: _platform_details(
            os_name="Unknown platform",
            credential="credential store metadata potential",
            notification="notification metadata potential",
            startup="startup item metadata potential",
            calendar="calendar metadata adapter potential",
            email="email metadata adapter potential",
            conversation="conversation source metadata adapter potential",
            installer_channel="unknown-installer-channel",
            installer_summary="Unknown installer channel is unsupported and performs no mutation.",
            startup_state=PlatformCapabilityState.unsupported,
            integration_state=PlatformCapabilityState.unsupported,
            installer_state=PlatformCapabilityState.unsupported,
        ),
    }


def _platform_details(
    *,
    os_name: str,
    credential: str,
    notification: str,
    startup: str,
    calendar: str,
    email: str,
    conversation: str,
    installer_channel: str,
    installer_summary: str,
    startup_state: PlatformCapabilityState,
    integration_state: PlatformCapabilityState,
    installer_state: PlatformCapabilityState,
) -> dict[PlatformCapabilityFamily, dict[str, Any]]:
    return {
        PlatformCapabilityFamily.secure_credential_store: _detail(
            state=PlatformCapabilityState.metadata_only,
            authority_state=PlatformCapabilityAuthorityState.metadata_only,
            label=f"{os_name} secure credential store",
            summary=f"{os_name} {credential} potential is visible as metadata only and no credential read occurs.",
            adapter_ref="platform-adapter:secure-credential-store",
            integration_summary=f"{os_name} credential integration is metadata only and not configured.",
            reason_codes=["platform-capability:metadata-only", "platform-capability:credential-read-blocked"],
        ),
        PlatformCapabilityFamily.notification_delivery: _detail(
            state=PlatformCapabilityState.metadata_only,
            authority_state=PlatformCapabilityAuthorityState.metadata_only,
            label=f"{os_name} notification delivery",
            summary=f"{os_name} {notification} potential is visible as metadata only and no notification is sent.",
            adapter_ref="platform-adapter:notification-delivery",
            integration_summary=f"{os_name} notification integration is metadata only and not configured.",
            reason_codes=["platform-capability:metadata-only", "platform-capability:notification-send-blocked"],
        ),
        PlatformCapabilityFamily.startup_item: _detail(
            state=startup_state,
            authority_state=PlatformCapabilityAuthorityState.blocked,
            label=f"{os_name} startup item",
            summary=f"{os_name} {startup} remains blocked or planned disabled and no startup item is created.",
            adapter_ref="platform-adapter:startup-item",
            integration_summary=f"{os_name} startup integration is metadata only and not configured.",
            reason_codes=["platform-capability:startup-change-blocked"],
        ),
        PlatformCapabilityFamily.local_calendar_metadata: _detail(
            state=integration_state,
            authority_state=PlatformCapabilityAuthorityState.blocked,
            label=f"{os_name} calendar metadata",
            summary=f"{os_name} {calendar} remains metadata only and no calendar data is read.",
            adapter_ref="platform-adapter:local-calendar-metadata",
            integration_summary=f"{os_name} calendar integration is metadata only and not configured.",
            reason_codes=["platform-capability:calendar-read-blocked"],
        ),
        PlatformCapabilityFamily.email_account_metadata: _detail(
            state=integration_state,
            authority_state=PlatformCapabilityAuthorityState.blocked,
            label=f"{os_name} email account metadata",
            summary=f"{os_name} {email} remains metadata only and no email account data is read.",
            adapter_ref="platform-adapter:email-account-metadata",
            integration_summary=f"{os_name} email integration is metadata only and not configured.",
            reason_codes=["platform-capability:email-read-blocked"],
        ),
        PlatformCapabilityFamily.conversation_source_metadata: _detail(
            state=integration_state,
            authority_state=PlatformCapabilityAuthorityState.blocked,
            label=f"{os_name} conversation source metadata",
            summary=f"{os_name} {conversation} remains metadata only and no message data is read.",
            adapter_ref="platform-adapter:conversation-source-metadata",
            integration_summary=f"{os_name} conversation source integration is metadata only and not configured.",
            reason_codes=["platform-capability:message-read-blocked"],
        ),
        PlatformCapabilityFamily.local_model_runtime: _detail(
            state=PlatformCapabilityState.readiness_only,
            authority_state=PlatformCapabilityAuthorityState.readiness_only,
            label=f"{os_name} local model runtime",
            summary=f"{os_name} local model runtime posture is readiness only and no model call or service check occurs.",
            adapter_ref="platform-adapter:local-model-runtime",
            integration_summary=f"{os_name} local model runtime integration is readiness only and not configured.",
            reason_codes=["platform-capability:readiness-only", "platform-capability:model-call-blocked"],
        ),
        PlatformCapabilityFamily.control_center_shell: _detail(
            state=PlatformCapabilityState.metadata_only,
            authority_state=PlatformCapabilityAuthorityState.metadata_only,
            label=f"{os_name} Control Center shell",
            summary=f"{os_name} Control Center shell posture is metadata only and grants no runtime authority.",
            adapter_ref="platform-adapter:control-center-shell",
            integration_summary=f"{os_name} Control Center shell integration is metadata only.",
            reason_codes=["platform-capability:metadata-only", "platform-capability:ui-authority-blocked"],
        ),
        PlatformCapabilityFamily.installer_channel: _detail(
            state=installer_state,
            authority_state=PlatformCapabilityAuthorityState.blocked,
            label=f"{os_name} installer channel",
            summary=installer_summary,
            adapter_ref="platform-adapter:installer-channel",
            integration_summary=f"{os_name} installer channel integration is metadata only.",
            channel_ref=f"platform-installer-channel:{installer_channel}",
            installer_summary=installer_summary,
            reason_codes=["platform-capability:installer-execution-blocked"],
        ),
    }


def _detail(
    *,
    state: PlatformCapabilityState,
    authority_state: PlatformCapabilityAuthorityState,
    label: str,
    summary: str,
    adapter_ref: str,
    integration_summary: str,
    reason_codes: list[str],
    channel_ref: str = "platform-installer-channel:not-applicable",
    installer_summary: str = "Installer posture is not applicable to this capability family.",
) -> dict[str, Any]:
    return {
        "state": state,
        "authority_state": authority_state,
        "label": label,
        "summary": summary,
        "adapter_ref": adapter_ref,
        "integration_summary": integration_summary,
        "channel_ref": channel_ref,
        "installer_summary": installer_summary,
        "reason_codes": reason_codes,
    }


def _validate_ref(value: str, field_name: str) -> str:
    _validate_no_private_or_secret_text(value, field_name)
    if not SAFE_REF_RE.match(value):
        raise ValueError(f"{field_name.upper()}_UNSAFE_REF")
    return value


def _validate_safe_text(value: str, field_name: str, max_chars: int = MAX_SAFE_TEXT_CHARS) -> str:
    _validate_no_private_or_secret_text(value, field_name)
    if len(value) > max_chars:
        raise ValueError(f"{field_name.upper()}_TOO_LONG")
    if not SAFE_TEXT_RE.match(value):
        raise ValueError(f"{field_name.upper()}_UNSAFE_TEXT")
    return value


def _validate_safe_metadata(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_safe_text(str(key), f"{field_name}_key", max_chars=120)
            _validate_safe_metadata(item, field_name)
        return
    if isinstance(value, list):
        for item in value:
            _validate_safe_metadata(item, field_name)
        return
    if isinstance(value, str):
        _validate_safe_text(value, field_name)
        return
    if isinstance(value, bool | int | float) or value is None:
        return
    raise ValueError(f"{field_name.upper()}_UNSAFE_METADATA_VALUE")


def _validate_no_private_or_secret_text(value: str, field_name: str) -> None:
    if RAW_PATH_FRAGMENT_RE.search(value):
        raise ValueError(f"{field_name.upper()}_RAW_PATH_DENIED")
    if contains_obvious_secret(value):
        raise ValueError(f"{field_name.upper()}_SECRET_LIKE")


def _deny_true_flags(model: Any, flags: list[tuple[str, str]]) -> None:
    for field_name, reason in flags:
        if getattr(model, field_name):
            raise ValueError(reason)
