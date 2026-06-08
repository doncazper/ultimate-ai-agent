from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


MOBILE_BACKGROUND_TASK_CONTRACT_NO_EXECUTION_DOCS = [
    "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION.md",
    "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_POLICY.md",
    "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_AUTHORITY_BOUNDARY.md",
    "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_RECEIPT_PLAN.md",
    "docs/mobile/BACKGROUND_TASK_CONTRACT_NO_EXECUTION_NON_GOALS.md",
    "docs/mobile/M105_TO_M106_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MobileBackgroundTaskChannel(str, Enum):
    local_status_placeholder = "local_status_placeholder"
    sync_candidate_placeholder = "sync_candidate_placeholder"


class MobileBackgroundTaskContractStatus(str, Enum):
    contract_only = "contract_only"


class _MobileBackgroundTaskContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobileBackgroundTaskContractPolicy(_MobileBackgroundTaskContractModel):
    policy_ref: str = "background-task-contract-no-execution-policy:m105"
    contract_only: bool = True
    planning_only_required: bool = True
    safe_refs_required: bool = True
    no_background_execution_required: bool = True
    consent_required: bool = True
    revocation_required: bool = True
    audit_required: bool = True
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    os_background_permission_prompt_enabled: bool = False
    push_trigger_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    raw_task_payload_enabled: bool = False
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


class MobileBackgroundTaskPlan(_MobileBackgroundTaskContractModel):
    background_task_plan_ref: str
    channel: MobileBackgroundTaskChannel
    actor_ref: str
    safe_device_ref: str
    safe_task_summary_ref: str
    safe_cadence_ref: str
    safe_purpose_ref: str
    consent_ref: str
    revocation_ref: str
    audit_ref: str
    planning_only: bool = True
    safe_refs_only: bool = True
    no_background_execution: bool = True
    exact_scope_required: bool = True
    consent_required: bool = True
    revocable: bool = True
    audit_required: bool = True
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    os_background_permission_prompt_enabled: bool = False
    push_trigger_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    raw_task_payload_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.background_task_plan_ref, "background_task_plan_ref"),
            (self.actor_ref, "actor_ref"),
            (self.safe_device_ref, "safe_device_ref"),
            (self.safe_task_summary_ref, "safe_task_summary_ref"),
            (self.safe_cadence_ref, "safe_cadence_ref"),
            (self.safe_purpose_ref, "safe_purpose_ref"),
            (self.consent_ref, "consent_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class MobileBackgroundTaskContractReport(_MobileBackgroundTaskContractModel):
    report_ref: str
    baseline_ref: str
    actor_ref: str
    status: MobileBackgroundTaskContractStatus = (
        MobileBackgroundTaskContractStatus.contract_only
    )
    contract_only: bool = True
    planning_only: bool = True
    safe_refs_required: bool = True
    no_background_execution: bool = True
    consent_required: bool = True
    revocation_required: bool = True
    audit_required: bool = True
    background_task_plans: list[MobileBackgroundTaskPlan]
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    daemon_enabled: bool = False
    os_background_permission_prompt_enabled: bool = False
    push_trigger_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_service_enabled: bool = False
    raw_task_payload_enabled: bool = False
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


def build_mobile_background_task_contract_report(
    policy: MobileBackgroundTaskContractPolicy | None = None,
) -> MobileBackgroundTaskContractReport:
    active_policy = validate_mobile_background_task_contract_policy(
        policy or MobileBackgroundTaskContractPolicy()
    )
    report = MobileBackgroundTaskContractReport(
        report_ref="background-task-contract-report:m105",
        baseline_ref="baseline:v1.7.2",
        actor_ref="actor:background-task-contract-reviewer",
        contract_only=active_policy.contract_only,
        background_task_plans=_default_background_task_plans(),
        side_effects_performed=[],
        reason_codes=[
            "M105_BACKGROUND_TASK_CONTRACT_NO_EXECUTION",
            "M105_SAFE_REFS_ONLY",
            "M105_NO_BACKGROUND_WORKER",
            "M105_NO_SCHEDULER",
            "M105_NO_DAEMON",
            "M106_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M105 defines mobile background task contracts for future review. "
            "It uses safe refs, safe task summaries, and safe cadence refs only. "
            "It adds no background worker, scheduler, daemon, OS background "
            "permission prompt, push trigger, device token handling, external "
            "service, raw task payload, backend routes, Control Center controls, "
            "dependencies, memory writes, context injection, execution, M106 "
            "work, or production authority."
        ),
    )
    return validate_mobile_background_task_contract_report(report)


def validate_mobile_background_task_contract_policy(
    policy: MobileBackgroundTaskContractPolicy,
) -> MobileBackgroundTaskContractPolicy:
    validated = MobileBackgroundTaskContractPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M105_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M105_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m105_metadata(validated.metadata)
    return validated


def validate_mobile_background_task_plan(
    plan: MobileBackgroundTaskPlan,
) -> MobileBackgroundTaskPlan:
    payload = _model_payload(plan)
    for field_name, reason in _M105_PLAN_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileBackgroundTaskPlan):
        raise ValueError("SECRET_LIKE_M105_BACKGROUND_TASK_CONTENT_DENIED")
    validated = MobileBackgroundTaskPlan.model_validate(payload)
    for field_name, reason in _M105_PLAN_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M105_PLAN_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m105_metadata(validated.metadata)
    return validated


def validate_mobile_background_task_contract_report(
    report: MobileBackgroundTaskContractReport,
) -> MobileBackgroundTaskContractReport:
    payload = _model_payload(report)
    for field_name, reason in _M105_REPORT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileBackgroundTaskContractReport):
        raise ValueError("SECRET_LIKE_M105_BACKGROUND_TASK_CONTENT_DENIED")
    validated = MobileBackgroundTaskContractReport.model_validate(payload)
    for field_name, reason in _M105_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M105_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobileBackgroundTaskContractStatus.contract_only:
        raise ValueError("M105_CONTRACT_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_background_task_plans(validated.background_task_plans)
    _validate_m105_metadata(validated.metadata)
    return validated


def _default_background_task_plans() -> list[MobileBackgroundTaskPlan]:
    return [
        MobileBackgroundTaskPlan(
            background_task_plan_ref="background-task-plan:m105:local-status-placeholder",
            channel=MobileBackgroundTaskChannel.local_status_placeholder,
            actor_ref="actor:background-task-contract-reviewer",
            safe_device_ref="safe-device-ref:m105:mobile-companion",
            safe_task_summary_ref="safe-background-task-summary:m105:local-status",
            safe_cadence_ref="safe-cadence-ref:m105:manual-review-only",
            safe_purpose_ref="safe-purpose-ref:m105:local-status",
            consent_ref="consent-ref:m105:future-review",
            revocation_ref="revocation-ref:m105:future-review",
            audit_ref="audit-ref:m105:local-status",
        ),
        MobileBackgroundTaskPlan(
            background_task_plan_ref="background-task-plan:m105:sync-candidate-placeholder",
            channel=MobileBackgroundTaskChannel.sync_candidate_placeholder,
            actor_ref="actor:background-task-contract-reviewer",
            safe_device_ref="safe-device-ref:m105:sync-candidate",
            safe_task_summary_ref="safe-background-task-summary:m105:sync-candidate",
            safe_cadence_ref="safe-cadence-ref:m105:future-review-only",
            safe_purpose_ref="safe-purpose-ref:m105:sync-candidate",
            consent_ref="consent-ref:m105:sync-candidate",
            revocation_ref="revocation-ref:m105:sync-candidate",
            audit_ref="audit-ref:m105:sync-candidate",
        ),
    ]


def _validate_background_task_plans(plans: list[MobileBackgroundTaskPlan]) -> None:
    if not plans:
        raise ValueError("M105_BACKGROUND_TASK_PLAN_REQUIRED")
    seen_plan_refs: set[str] = set()
    seen_channels: set[MobileBackgroundTaskChannel] = set()
    for plan in plans:
        validated = validate_mobile_background_task_plan(plan)
        if validated.background_task_plan_ref in seen_plan_refs:
            raise ValueError("M105_BACKGROUND_TASK_PLAN_REF_DUPLICATE")
        seen_plan_refs.add(validated.background_task_plan_ref)
        seen_channels.add(validated.channel)
    if seen_channels != {
        MobileBackgroundTaskChannel.local_status_placeholder,
        MobileBackgroundTaskChannel.sync_candidate_placeholder,
    }:
        raise ValueError("M105_BACKGROUND_TASK_PLAN_CHANNELS_REQUIRED")


def _validate_m105_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M105_BACKGROUND_TASK_CONTENT_DENIED") from exc


_M105_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("planning_only_required", "M105_PLANNING_ONLY_REQUIRED"),
    ("safe_refs_required", "M105_SAFE_REFS_REQUIRED"),
    ("no_background_execution_required", "M105_NO_BACKGROUND_EXECUTION_REQUIRED"),
    ("consent_required", "M105_CONSENT_REQUIRED"),
    ("revocation_required", "M105_REVOCATION_REQUIRED"),
    ("audit_required", "M105_AUDIT_REQUIRED"),
]

_M105_DENIALS = [
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("os_background_permission_prompt_enabled", "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("raw_task_payload_enabled", "RAW_TASK_PAYLOAD_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M105_PLAN_REQUIRED_TRUE = [
    ("planning_only", "M105_PLANNING_ONLY_REQUIRED"),
    ("safe_refs_only", "M105_SAFE_REFS_REQUIRED"),
    ("no_background_execution", "M105_NO_BACKGROUND_EXECUTION_REQUIRED"),
    ("exact_scope_required", "M105_EXACT_SCOPE_REQUIRED"),
    ("consent_required", "M105_CONSENT_REQUIRED"),
    ("revocable", "M105_REVOCATION_REQUIRED"),
    ("audit_required", "M105_AUDIT_REQUIRED"),
]

_M105_PLAN_DENIALS = [
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("os_background_permission_prompt_enabled", "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("raw_task_payload_enabled", "RAW_TASK_PAYLOAD_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M105_REPORT_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("planning_only", "M105_PLANNING_ONLY_REQUIRED"),
    ("safe_refs_required", "M105_SAFE_REFS_REQUIRED"),
    ("no_background_execution", "M105_NO_BACKGROUND_EXECUTION_REQUIRED"),
    ("consent_required", "M105_CONSENT_REQUIRED"),
    ("revocation_required", "M105_REVOCATION_REQUIRED"),
    ("audit_required", "M105_AUDIT_REQUIRED"),
]

_M105_REPORT_DENIALS = [
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("daemon_enabled", "DAEMON_DENIED"),
    ("os_background_permission_prompt_enabled", "OS_BACKGROUND_PERMISSION_PROMPT_DENIED"),
    ("push_trigger_enabled", "PUSH_TRIGGER_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_service_enabled", "EXTERNAL_SERVICE_DENIED"),
    ("raw_task_payload_enabled", "RAW_TASK_PAYLOAD_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
