from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_DOCS = [
    "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC.md",
    "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_POLICY.md",
    "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_AUTHORITY_BOUNDARY.md",
    "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_RECEIPT_PLAN.md",
    "docs/mobile/MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC_NON_GOALS.md",
    "docs/mobile/M106_TO_M107_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MobileBackgroundStatusSyncChannel(str, Enum):
    local_status_snapshot = "local_status_snapshot"
    sync_health_snapshot = "sync_health_snapshot"


class MobileBackgroundStatusSyncStatus(str, Enum):
    read_only_contract = "read_only_contract"


class _MobileBackgroundStatusSyncModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobileBackgroundStatusSyncPolicy(_MobileBackgroundStatusSyncModel):
    policy_ref: str = "mobile-background-read-only-status-sync-policy:m106"
    contract_only: bool = True
    read_only_required: bool = True
    safe_refs_required: bool = True
    no_background_collection_required: bool = True
    no_background_execution_required: bool = True
    audit_required: bool = True
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    os_background_fetch_enabled: bool = False
    os_background_permission_prompt_enabled: bool = False
    push_trigger_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    network_sync_enabled: bool = False
    raw_status_payload_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MobileBackgroundStatusSnapshot(_MobileBackgroundStatusSyncModel):
    status_snapshot_ref: str
    channel: MobileBackgroundStatusSyncChannel
    actor_ref: str
    background_task_plan_ref: str
    safe_device_ref: str
    safe_status_ref: str
    safe_status_summary_ref: str
    safe_observed_at_ref: str
    audit_ref: str
    read_only: bool = True
    safe_refs_only: bool = True
    no_background_collection: bool = True
    no_background_execution: bool = True
    audit_required: bool = True
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    os_background_fetch_enabled: bool = False
    os_background_permission_prompt_enabled: bool = False
    push_trigger_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    network_sync_enabled: bool = False
    raw_status_payload_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.status_snapshot_ref, "status_snapshot_ref"),
            (self.actor_ref, "actor_ref"),
            (self.background_task_plan_ref, "background_task_plan_ref"),
            (self.safe_device_ref, "safe_device_ref"),
            (self.safe_status_ref, "safe_status_ref"),
            (self.safe_status_summary_ref, "safe_status_summary_ref"),
            (self.safe_observed_at_ref, "safe_observed_at_ref"),
            (self.audit_ref, "audit_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class MobileBackgroundStatusSyncReport(_MobileBackgroundStatusSyncModel):
    report_ref: str
    baseline_ref: str
    actor_ref: str
    status: MobileBackgroundStatusSyncStatus = (
        MobileBackgroundStatusSyncStatus.read_only_contract
    )
    contract_only: bool = True
    read_only: bool = True
    safe_refs_required: bool = True
    no_background_collection: bool = True
    no_background_execution: bool = True
    audit_required: bool = True
    status_snapshots: list[MobileBackgroundStatusSnapshot]
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    os_background_fetch_enabled: bool = False
    os_background_permission_prompt_enabled: bool = False
    push_trigger_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    network_sync_enabled: bool = False
    raw_status_payload_enabled: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
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


def build_mobile_background_read_only_status_sync_report(
    policy: MobileBackgroundStatusSyncPolicy | None = None,
) -> MobileBackgroundStatusSyncReport:
    active_policy = validate_mobile_background_status_sync_policy(
        policy or MobileBackgroundStatusSyncPolicy()
    )
    report = MobileBackgroundStatusSyncReport(
        report_ref="background-status-sync-report:m106",
        baseline_ref="baseline:v1.7.2",
        actor_ref="actor:background-status-sync-reviewer",
        contract_only=active_policy.contract_only,
        status_snapshots=_default_status_snapshots(),
        side_effects_performed=[],
        reason_codes=[
            "M106_MOBILE_BACKGROUND_READ_ONLY_STATUS_SYNC",
            "M106_SAFE_STATUS_REFS_ONLY",
            "M106_READ_ONLY_CONTRACT",
            "M106_NO_BACKGROUND_WORKER",
            "M106_NO_NETWORK_SYNC",
            "M107_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M106 defines read-only mobile background status sync contracts for "
            "future review. It records safe status refs, safe status summaries, "
            "safe observed-at refs, and audit refs only. It adds no background "
            "worker, scheduler, daemon, OS background fetch, OS background "
            "permission prompt, push trigger, device token handling, external "
            "service, network sync, raw status payload, backend routes, Control "
            "Center controls, dependencies, memory writes, context injection, "
            "execution, M107 work, or production authority."
        ),
    )
    return validate_mobile_background_status_sync_report(report)


def validate_mobile_background_status_sync_policy(
    policy: MobileBackgroundStatusSyncPolicy,
) -> MobileBackgroundStatusSyncPolicy:
    validated = MobileBackgroundStatusSyncPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M106_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M106_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m106_metadata(validated.metadata)
    return validated


def validate_mobile_background_status_snapshot(
    snapshot: MobileBackgroundStatusSnapshot,
) -> MobileBackgroundStatusSnapshot:
    payload = _model_payload(snapshot)
    for field_name, reason in _M106_SNAPSHOT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileBackgroundStatusSnapshot):
        raise ValueError("SECRET_LIKE_M106_BACKGROUND_STATUS_CONTENT_DENIED")
    validated = MobileBackgroundStatusSnapshot.model_validate(payload)
    for field_name, reason in _M106_SNAPSHOT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M106_SNAPSHOT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m106_metadata(validated.metadata)
    return validated


def validate_mobile_background_status_sync_report(
    report: MobileBackgroundStatusSyncReport,
) -> MobileBackgroundStatusSyncReport:
    payload = _model_payload(report)
    for field_name, reason in _M106_REPORT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileBackgroundStatusSyncReport):
        raise ValueError("SECRET_LIKE_M106_BACKGROUND_STATUS_CONTENT_DENIED")
    validated = MobileBackgroundStatusSyncReport.model_validate(payload)
    for field_name, reason in _M106_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M106_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobileBackgroundStatusSyncStatus.read_only_contract:
        raise ValueError("M106_READ_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_status_snapshots(validated.status_snapshots)
    _validate_m106_metadata(validated.metadata)
    return validated


def _default_status_snapshots() -> list[MobileBackgroundStatusSnapshot]:
    return [
        MobileBackgroundStatusSnapshot(
            status_snapshot_ref="background-status-snapshot:m106:local-status",
            channel=MobileBackgroundStatusSyncChannel.local_status_snapshot,
            actor_ref="actor:background-status-sync-reviewer",
            background_task_plan_ref="background-task-plan:m105:local-status-placeholder",
            safe_device_ref="safe-device-ref:m106:mobile-companion",
            safe_status_ref="safe-background-status-ref:m106:local-status",
            safe_status_summary_ref="safe-background-status-summary:m106:local-status",
            safe_observed_at_ref="safe-observed-at-ref:m106:manual-review",
            audit_ref="audit-ref:m106:local-status",
        ),
        MobileBackgroundStatusSnapshot(
            status_snapshot_ref="background-status-snapshot:m106:sync-health",
            channel=MobileBackgroundStatusSyncChannel.sync_health_snapshot,
            actor_ref="actor:background-status-sync-reviewer",
            background_task_plan_ref="background-task-plan:m105:sync-candidate-placeholder",
            safe_device_ref="safe-device-ref:m106:sync-candidate",
            safe_status_ref="safe-background-status-ref:m106:sync-health",
            safe_status_summary_ref="safe-background-status-summary:m106:sync-health",
            safe_observed_at_ref="safe-observed-at-ref:m106:manual-review",
            audit_ref="audit-ref:m106:sync-health",
        ),
    ]


def _validate_status_snapshots(snapshots: list[MobileBackgroundStatusSnapshot]) -> None:
    if not snapshots:
        raise ValueError("M106_STATUS_SNAPSHOT_REQUIRED")
    seen_snapshot_refs: set[str] = set()
    seen_channels: set[MobileBackgroundStatusSyncChannel] = set()
    for snapshot in snapshots:
        validated = validate_mobile_background_status_snapshot(snapshot)
        if validated.status_snapshot_ref in seen_snapshot_refs:
            raise ValueError("M106_STATUS_SNAPSHOT_REF_DUPLICATE")
        seen_snapshot_refs.add(validated.status_snapshot_ref)
        seen_channels.add(validated.channel)
    if seen_channels != {
        MobileBackgroundStatusSyncChannel.local_status_snapshot,
        MobileBackgroundStatusSyncChannel.sync_health_snapshot,
    }:
        raise ValueError("M106_STATUS_SNAPSHOT_CHANNELS_REQUIRED")


def _validate_m106_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M106_BACKGROUND_STATUS_CONTENT_DENIED") from exc


_M106_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("read_only_required", "M106_READ_ONLY_REQUIRED"),
    ("safe_refs_required", "M106_SAFE_REFS_REQUIRED"),
    ("no_background_collection_required", "M106_NO_BACKGROUND_COLLECTION_REQUIRED"),
    ("no_background_execution_required", "M106_NO_BACKGROUND_EXECUTION_REQUIRED"),
    ("audit_required", "M106_AUDIT_REQUIRED"),
]

_M106_DENIALS = [
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("os_background_fetch_enabled", "OS_BACKGROUND_FETCH_DENIED"),
    ("os_background_permission_prompt_enabled", "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
    ("raw_status_payload_enabled", "RAW_STATUS_PAYLOAD_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M106_SNAPSHOT_REQUIRED_TRUE = [
    ("read_only", "M106_READ_ONLY_REQUIRED"),
    ("safe_refs_only", "M106_SAFE_REFS_REQUIRED"),
    ("no_background_collection", "M106_NO_BACKGROUND_COLLECTION_REQUIRED"),
    ("no_background_execution", "M106_NO_BACKGROUND_EXECUTION_REQUIRED"),
    ("audit_required", "M106_AUDIT_REQUIRED"),
]

_M106_SNAPSHOT_DENIALS = [
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("os_background_fetch_enabled", "OS_BACKGROUND_FETCH_DENIED"),
    ("os_background_permission_prompt_enabled", "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
    ("raw_status_payload_enabled", "RAW_STATUS_PAYLOAD_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M106_REPORT_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("read_only", "M106_READ_ONLY_REQUIRED"),
    ("safe_refs_required", "M106_SAFE_REFS_REQUIRED"),
    ("no_background_collection", "M106_NO_BACKGROUND_COLLECTION_REQUIRED"),
    ("no_background_execution", "M106_NO_BACKGROUND_EXECUTION_REQUIRED"),
    ("audit_required", "M106_AUDIT_REQUIRED"),
]

_M106_REPORT_DENIALS = [
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("os_background_fetch_enabled", "OS_BACKGROUND_FETCH_DENIED"),
    ("os_background_permission_prompt_enabled", "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("network_sync_enabled", "NETWORK_SYNC_DENIED"),
    ("raw_status_payload_enabled", "RAW_STATUS_PAYLOAD_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
