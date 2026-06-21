from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


MOBILE_NOTIFICATION_PLANNING_NO_PUSH_DOCS = [
    "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH.md",
    "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_POLICY.md",
    "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_AUTHORITY_BOUNDARY.md",
    "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_RECEIPT_PLAN.md",
    "docs/mobile/NOTIFICATION_PLANNING_NO_PUSH_NON_GOALS.md",
    "docs/mobile/M104_TO_M105_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]


class MobileNotificationChannel(str, Enum):
    local_review_placeholder = "local_review_placeholder"
    push_candidate_placeholder = "push_candidate_placeholder"


class MobileNotificationPlanningStatus(str, Enum):
    contract_only = "contract_only"


class _MobileNotificationPlanningModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MobileNotificationPlanningPolicy(_MobileNotificationPlanningModel):
    policy_ref: str = "notification-planning-no-push-policy:m104"
    contract_only: bool = True
    planning_only_required: bool = True
    safe_refs_required: bool = True
    no_push_execution_required: bool = True
    consent_required: bool = True
    revocation_required: bool = True
    audit_required: bool = True
    push_delivery_enabled: bool = False
    notification_permission_prompt_enabled: bool = False
    notification_scheduling_enabled: bool = False
    background_task_execution_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_push_provider_enabled: bool = False
    raw_notification_body_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    execution_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class MobileNotificationPlan(_MobileNotificationPlanningModel):
    notification_plan_ref: str
    channel: MobileNotificationChannel
    actor_ref: str
    safe_device_ref: str
    safe_message_summary_ref: str
    safe_purpose_ref: str
    consent_ref: str
    revocation_ref: str
    audit_ref: str
    planning_only: bool = True
    safe_refs_only: bool = True
    no_push_execution: bool = True
    exact_scope_required: bool = True
    consent_required: bool = True
    revocable: bool = True
    audit_required: bool = True
    push_delivery_enabled: bool = False
    notification_permission_prompt_enabled: bool = False
    notification_scheduling_enabled: bool = False
    background_task_execution_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_push_provider_enabled: bool = False
    raw_notification_body_enabled: bool = False
    production_authority_enabled: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in [
            (self.notification_plan_ref, "notification_plan_ref"),
            (self.actor_ref, "actor_ref"),
            (self.safe_device_ref, "safe_device_ref"),
            (self.safe_message_summary_ref, "safe_message_summary_ref"),
            (self.safe_purpose_ref, "safe_purpose_ref"),
            (self.consent_ref, "consent_ref"),
            (self.revocation_ref, "revocation_ref"),
            (self.audit_ref, "audit_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        return self


class MobileNotificationPlanningReport(_MobileNotificationPlanningModel):
    report_ref: str
    baseline_ref: str
    actor_ref: str
    status: MobileNotificationPlanningStatus = (
        MobileNotificationPlanningStatus.contract_only
    )
    contract_only: bool = True
    planning_only: bool = True
    safe_refs_required: bool = True
    no_push_execution: bool = True
    consent_required: bool = True
    revocation_required: bool = True
    audit_required: bool = True
    notification_plans: list[MobileNotificationPlan]
    push_delivery_enabled: bool = False
    notification_permission_prompt_enabled: bool = False
    notification_scheduling_enabled: bool = False
    background_task_execution_enabled: bool = False
    device_token_handling_enabled: bool = False
    external_push_provider_enabled: bool = False
    raw_notification_body_enabled: bool = False
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


def build_mobile_notification_planning_report(
    policy: MobileNotificationPlanningPolicy | None = None,
) -> MobileNotificationPlanningReport:
    active_policy = validate_mobile_notification_planning_policy(
        policy or MobileNotificationPlanningPolicy()
    )
    report = MobileNotificationPlanningReport(
        report_ref="notification-planning-report:m104",
        baseline_ref="baseline:v1.7.2",
        actor_ref="actor:notification-planning-reviewer",
        contract_only=active_policy.contract_only,
        notification_plans=_default_notification_plans(),
        side_effects_performed=[],
        reason_codes=[
            "M104_NOTIFICATION_PLANNING_NO_PUSH",
            "M104_SAFE_REFS_ONLY",
            "M104_NO_PERMISSION_PROMPT",
            "M104_NO_PUSH_DELIVERY",
            "M104_NO_BACKGROUND_TASK_EXECUTION",
            "M105_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M104 defines notification planning contracts for future review. "
            "It uses safe refs and safe message summaries only. It adds no push "
            "delivery, notification permission prompt, notification scheduling, "
            "background task execution, device token handling, external push "
            "provider, raw notification body, backend routes, Control Center "
            "controls, dependencies, memory writes, context injection, "
            "execution, M105 work, or production authority."
        ),
    )
    return validate_mobile_notification_planning_report(report)


def validate_mobile_notification_planning_policy(
    policy: MobileNotificationPlanningPolicy,
) -> MobileNotificationPlanningPolicy:
    validated = MobileNotificationPlanningPolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M104_POLICY_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M104_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    _validate_m104_metadata(validated.metadata)
    return validated


def validate_mobile_notification_plan(
    plan: MobileNotificationPlan,
) -> MobileNotificationPlan:
    payload = _model_payload(plan)
    for field_name, reason in _M104_PLAN_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileNotificationPlan):
        raise ValueError("SECRET_LIKE_M104_NOTIFICATION_CONTENT_DENIED")
    validated = MobileNotificationPlan.model_validate(payload)
    for field_name, reason in _M104_PLAN_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M104_PLAN_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_m104_metadata(validated.metadata)
    return validated


def validate_mobile_notification_planning_report(
    report: MobileNotificationPlanningReport,
) -> MobileNotificationPlanningReport:
    payload = _model_payload(report)
    for field_name, reason in _M104_REPORT_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, MobileNotificationPlanningReport):
        raise ValueError("SECRET_LIKE_M104_NOTIFICATION_CONTENT_DENIED")
    validated = MobileNotificationPlanningReport.model_validate(payload)
    for field_name, reason in _M104_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M104_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != MobileNotificationPlanningStatus.contract_only:
        raise ValueError("M104_CONTRACT_ONLY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_notification_plans(validated.notification_plans)
    _validate_m104_metadata(validated.metadata)
    return validated


def _default_notification_plans() -> list[MobileNotificationPlan]:
    return [
        MobileNotificationPlan(
            notification_plan_ref="notification-plan:m104:local-review-placeholder",
            channel=MobileNotificationChannel.local_review_placeholder,
            actor_ref="actor:notification-planning-reviewer",
            safe_device_ref="safe-device-ref:m104:mobile-companion",
            safe_message_summary_ref="safe-notification-summary:m104:local-review",
            safe_purpose_ref="safe-purpose-ref:m104:local-review",
            consent_ref="consent-ref:m104:future-review",
            revocation_ref="revocation-ref:m104:future-review",
            audit_ref="audit-ref:m104:local-review",
        ),
        MobileNotificationPlan(
            notification_plan_ref="notification-plan:m104:push-candidate-placeholder",
            channel=MobileNotificationChannel.push_candidate_placeholder,
            actor_ref="actor:notification-planning-reviewer",
            safe_device_ref="safe-device-ref:m104:push-candidate",
            safe_message_summary_ref="safe-notification-summary:m104:push-candidate",
            safe_purpose_ref="safe-purpose-ref:m104:push-candidate",
            consent_ref="consent-ref:m104:push-candidate",
            revocation_ref="revocation-ref:m104:push-candidate",
            audit_ref="audit-ref:m104:push-candidate",
        ),
    ]


def _validate_notification_plans(plans: list[MobileNotificationPlan]) -> None:
    if not plans:
        raise ValueError("M104_NOTIFICATION_PLAN_REQUIRED")
    seen_plan_refs: set[str] = set()
    seen_channels: set[MobileNotificationChannel] = set()
    for plan in plans:
        validated = validate_mobile_notification_plan(plan)
        if validated.notification_plan_ref in seen_plan_refs:
            raise ValueError("M104_NOTIFICATION_PLAN_REF_DUPLICATE")
        seen_plan_refs.add(validated.notification_plan_ref)
        seen_channels.add(validated.channel)
    if seen_channels != {
        MobileNotificationChannel.local_review_placeholder,
        MobileNotificationChannel.push_candidate_placeholder,
    }:
        raise ValueError("M104_NOTIFICATION_PLAN_CHANNELS_REQUIRED")


def _validate_m104_metadata(metadata: dict[str, Any]) -> None:
    try:
        _validate_safe_payload(metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M104_NOTIFICATION_CONTENT_DENIED") from exc


_M104_POLICY_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("planning_only_required", "M104_PLANNING_ONLY_REQUIRED"),
    ("safe_refs_required", "M104_SAFE_REFS_REQUIRED"),
    ("no_push_execution_required", "M104_NO_PUSH_EXECUTION_REQUIRED"),
    ("consent_required", "M104_CONSENT_REQUIRED"),
    ("revocation_required", "M104_REVOCATION_REQUIRED"),
    ("audit_required", "M104_AUDIT_REQUIRED"),
]

_M104_DENIALS = [
    ("push_delivery_enabled", "PUSH_DELIVERY_DENIED"),
    ("notification_permission_prompt_enabled", "NOTIFICATION_PERMISSION_PROMPT_DENIED"),
    ("notification_scheduling_enabled", "NOTIFICATION_SCHEDULING_DENIED"),
    ("background_task_execution_enabled", "BACKGROUND_TASK_EXECUTION_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_push_provider_enabled", "EXTERNAL_PUSH_PROVIDER_DENIED"),
    ("raw_notification_body_enabled", "RAW_NOTIFICATION_BODY_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M104_PLAN_REQUIRED_TRUE = [
    ("planning_only", "M104_PLANNING_ONLY_REQUIRED"),
    ("safe_refs_only", "M104_SAFE_REFS_REQUIRED"),
    ("no_push_execution", "M104_NO_PUSH_EXECUTION_REQUIRED"),
    ("exact_scope_required", "M104_EXACT_SCOPE_REQUIRED"),
    ("consent_required", "M104_CONSENT_REQUIRED"),
    ("revocable", "M104_REVOCATION_REQUIRED"),
    ("audit_required", "M104_AUDIT_REQUIRED"),
]

_M104_PLAN_DENIALS = [
    ("push_delivery_enabled", "PUSH_DELIVERY_DENIED"),
    ("notification_permission_prompt_enabled", "NOTIFICATION_PERMISSION_PROMPT_DENIED"),
    ("notification_scheduling_enabled", "NOTIFICATION_SCHEDULING_DENIED"),
    ("background_task_execution_enabled", "BACKGROUND_TASK_EXECUTION_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_push_provider_enabled", "EXTERNAL_PUSH_PROVIDER_DENIED"),
    ("raw_notification_body_enabled", "RAW_NOTIFICATION_BODY_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M104_REPORT_REQUIRED_TRUE = [
    ("contract_only", "CONTRACT_ONLY_REQUIRED"),
    ("planning_only", "M104_PLANNING_ONLY_REQUIRED"),
    ("safe_refs_required", "M104_SAFE_REFS_REQUIRED"),
    ("no_push_execution", "M104_NO_PUSH_EXECUTION_REQUIRED"),
    ("consent_required", "M104_CONSENT_REQUIRED"),
    ("revocation_required", "M104_REVOCATION_REQUIRED"),
    ("audit_required", "M104_AUDIT_REQUIRED"),
]

_M104_REPORT_DENIALS = [
    ("push_delivery_enabled", "PUSH_DELIVERY_DENIED"),
    ("notification_permission_prompt_enabled", "NOTIFICATION_PERMISSION_PROMPT_DENIED"),
    ("notification_scheduling_enabled", "NOTIFICATION_SCHEDULING_DENIED"),
    ("background_task_execution_enabled", "BACKGROUND_TASK_EXECUTION_DENIED"),
    ("device_token_handling_enabled", "DEVICE_TOKEN_HANDLING_DENIED"),
    ("external_push_provider_enabled", "EXTERNAL_PUSH_PROVIDER_DENIED"),
    ("raw_notification_body_enabled", "RAW_NOTIFICATION_BODY_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]
