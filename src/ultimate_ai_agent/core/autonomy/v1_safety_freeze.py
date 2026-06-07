from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
    _ref_suffix,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


AUTONOMY_V1_SAFETY_FREEZE_DOCS = [
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE.md",
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_POLICY.md",
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_RECEIPT_PLAN.md",
    "docs/autonomy/AUTONOMY_V1_SAFETY_FREEZE_NON_GOALS.md",
    "docs/autonomy/M99_TO_M100_BOUNDARY.md",
    "docs/roadmap/M61_M100_ROADMAP.md",
]
REQUIRED_AUTONOMY_V1_ACCEPTED_MILESTONE_REFS = tuple(
    f"milestone:M{index}" for index in range(61, 99)
)


class AutonomyV1SafetyFreezeStatus(str, Enum):
    frozen_for_review = "frozen_for_review"


class _AutonomyV1SafetyFreezeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AutonomyV1SafetyFreezePolicy(_AutonomyV1SafetyFreezeModel):
    policy_ref: str = "autonomy-v1-safety-freeze-policy:m99"
    freeze_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    m61_m98_coverage_required: bool = True
    no_broad_unsandboxed_autonomy_required: bool = True
    no_production_authority_required: bool = True
    broad_autonomy_enabled: bool = False
    global_autonomy_switch_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_action_enabled: bool = False
    network_mutation_enabled: bool = False
    plugin_execution_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    mobile_sensor_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    credential_cookie_access_enabled: bool = False
    raw_prompt_payload_exposure_enabled: bool = False
    raw_file_export_enabled: bool = False
    full_file_read_enabled: bool = False
    remote_execution_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_change_enabled: bool = False
    production_authority_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        return self


class AutonomyV1SafetyFreezeRequest(_AutonomyV1SafetyFreezeModel):
    request_ref: str
    freeze_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_milestone_refs: list[str]
    checklist_refs: list[str]
    safe_summary: str
    freeze_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    m61_m98_coverage_required: bool = True
    no_broad_unsandboxed_autonomy_required: bool = True
    no_production_authority_required: bool = True
    broad_autonomy_requested: bool = False
    global_autonomy_switch_requested: bool = False
    execution_requested: bool = False
    tool_execution_requested: bool = False
    shell_execution_requested: bool = False
    browser_action_requested: bool = False
    network_mutation_requested: bool = False
    plugin_execution_requested: bool = False
    background_worker_requested: bool = False
    scheduler_requested: bool = False
    mobile_sensor_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    credential_cookie_access_requested: bool = False
    raw_prompt_payload_exposure_requested: bool = False
    raw_file_export_requested: bool = False
    full_file_read_requested: bool = False
    remote_execution_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    production_authority_requested: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.request_ref, "request_ref"),
            (self.freeze_ref, "freeze_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class AutonomyV1SafetyFreezeReport(_AutonomyV1SafetyFreezeModel):
    report_ref: str
    freeze_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_milestone_refs: list[str]
    checklist_refs: list[str]
    status: AutonomyV1SafetyFreezeStatus = AutonomyV1SafetyFreezeStatus.frozen_for_review
    freeze_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    m61_m98_covered: bool = True
    no_broad_unsandboxed_autonomy: bool = True
    no_production_authority: bool = True
    broad_autonomy_granted: bool = False
    global_autonomy_switch_enabled: bool = False
    execution_performed: bool = False
    tool_execution_performed: bool = False
    shell_execution_performed: bool = False
    browser_action_performed: bool = False
    network_mutation_performed: bool = False
    plugin_execution_performed: bool = False
    background_worker_started: bool = False
    scheduler_started: bool = False
    mobile_sensor_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    credential_cookie_access_performed: bool = False
    raw_prompt_payload_exposed: bool = False
    raw_file_export_performed: bool = False
    full_file_read_performed: bool = False
    remote_execution_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        for value, field_name in [
            (self.report_ref, "report_ref"),
            (self.freeze_ref, "freeze_ref"),
            (self.request_ref, "request_ref"),
            (self.baseline_ref, "baseline_ref"),
            (self.actor_ref, "actor_ref"),
        ]:
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("REASON_CODE_REQUIRED")
        return self


def build_autonomy_v1_safety_freeze_report(
    request: AutonomyV1SafetyFreezeRequest,
    policy: AutonomyV1SafetyFreezePolicy | None = None,
) -> AutonomyV1SafetyFreezeReport:
    active_policy = validate_autonomy_v1_safety_freeze_policy(
        policy or AutonomyV1SafetyFreezePolicy()
    )
    validated_request = validate_autonomy_v1_safety_freeze_request(request)
    report = AutonomyV1SafetyFreezeReport(
        report_ref=f"autonomy-v1-safety-freeze-report:{_ref_suffix(validated_request.freeze_ref)}",
        freeze_ref=validated_request.freeze_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_milestone_refs=list(validated_request.accepted_milestone_refs),
        checklist_refs=list(validated_request.checklist_refs),
        freeze_only=active_policy.freeze_only,
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        side_effects_performed=[],
        reason_codes=[
            "M99_AUTONOMY_V1_SAFETY_FREEZE_REVIEW_ONLY",
            "M99_M61_M98_COVERED",
            "M99_NO_BROAD_UNSANDBOXED_AUTONOMY",
            "M99_NO_PRODUCTION_AUTHORITY",
            "M100_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M99 freezes the accepted M61-M98 autonomy v1 surface for review only. "
            "It adds no broad unsandboxed autonomy, global autonomy switch, execution, "
            "shell execution, browser action, network mutation, plugin execution, "
            "scheduler, background worker, mobile sensor, memory write, context "
            "injection, sensitive account material access, raw prompt/provider payload exposure, "
            "raw file export, full-file read, remote execution, route, dependency, "
            "M100 work, or production authority."
        ),
    )
    return validate_autonomy_v1_safety_freeze_report(report)


def validate_autonomy_v1_safety_freeze_policy(
    policy: AutonomyV1SafetyFreezePolicy,
) -> AutonomyV1SafetyFreezePolicy:
    validated = AutonomyV1SafetyFreezePolicy.model_validate(_model_payload(policy))
    for field_name, reason in _M99_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M99_POLICY_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M99_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_autonomy_v1_safety_freeze_request(
    request: AutonomyV1SafetyFreezeRequest,
) -> AutonomyV1SafetyFreezeRequest:
    payload = _model_payload(request)
    for field_name, reason in _M99_REQUEST_DENIALS:
        if payload.get(field_name):
            raise ValueError(reason)
    if _has_secret_like_extra(payload, AutonomyV1SafetyFreezeRequest):
        raise ValueError("SECRET_LIKE_M99_FREEZE_CONTENT_DENIED")
    validated = AutonomyV1SafetyFreezeRequest.model_validate(payload)
    for field_name, reason in _M99_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M99_REQUEST_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_accepted_milestones(validated.accepted_milestone_refs)
    _validate_checklist_refs(validated.checklist_refs)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M99_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_autonomy_v1_safety_freeze_report(
    report: AutonomyV1SafetyFreezeReport,
) -> AutonomyV1SafetyFreezeReport:
    validated = AutonomyV1SafetyFreezeReport.model_validate(_model_payload(report))
    for field_name, reason in _M99_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    for field_name, reason in _M99_REPORT_DENIALS:
        if getattr(validated, field_name):
            raise ValueError(reason)
    if validated.status != AutonomyV1SafetyFreezeStatus.frozen_for_review:
        raise ValueError("M99_FREEZE_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("SIDE_EFFECTS_DENIED")
    _validate_accepted_milestones(validated.accepted_milestone_refs)
    _validate_checklist_refs(validated.checklist_refs)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("SECRET_LIKE_M99_FREEZE_CONTENT_DENIED") from exc
    return validated


def _validate_accepted_milestones(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M99_ACCEPTED_MILESTONES_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M99_MILESTONE_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_milestone_ref")
    missing = [ref for ref in REQUIRED_AUTONOMY_V1_ACCEPTED_MILESTONE_REFS if ref not in refs]
    if missing:
        raise ValueError("M99_MILESTONE_REF_REQUIRED")
    unexpected = [
        ref for ref in refs if ref not in REQUIRED_AUTONOMY_V1_ACCEPTED_MILESTONE_REFS
    ]
    if unexpected:
        raise ValueError("M99_MILESTONE_REF_UNEXPECTED")


def _validate_checklist_refs(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M99_CHECKLIST_REF_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M99_CHECKLIST_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "checklist_ref")


_M99_REQUIRED_TRUE = [
    ("freeze_only", "FREEZE_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REVIEW_REQUIRED"),
    ("m61_m98_coverage_required", "M61_M98_COVERAGE_REQUIRED"),
    ("no_broad_unsandboxed_autonomy_required", "BROAD_AUTONOMY_DENIED"),
    ("no_production_authority_required", "PRODUCTION_AUTHORITY_DENIED"),
]

_M99_POLICY_DENIALS = [
    ("broad_autonomy_enabled", "BROAD_AUTONOMY_DENIED"),
    ("global_autonomy_switch_enabled", "GLOBAL_AUTONOMY_SWITCH_DENIED"),
    ("execution_enabled", "EXECUTION_DENIED"),
    ("tool_execution_enabled", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_enabled", "SHELL_EXECUTION_DENIED"),
    ("browser_action_enabled", "BROWSER_ACTION_DENIED"),
    ("network_mutation_enabled", "NETWORK_MUTATION_DENIED"),
    ("plugin_execution_enabled", "PLUGIN_EXECUTION_DENIED"),
    ("background_worker_enabled", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_enabled", "SCHEDULER_DENIED"),
    ("mobile_sensor_enabled", "MOBILE_SENSOR_DENIED"),
    ("memory_write_enabled", "MEMORY_WRITE_DENIED"),
    ("context_injection_enabled", "CONTEXT_INJECTION_DENIED"),
    ("credential_cookie_access_enabled", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
    ("raw_prompt_payload_exposure_enabled", "RAW_PROMPT_PAYLOAD_EXPOSURE_DENIED"),
    ("raw_file_export_enabled", "RAW_FILE_EXPORT_DENIED"),
    ("full_file_read_enabled", "FULL_FILE_READ_DENIED"),
    ("remote_execution_enabled", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_enabled", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_enabled", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_change_enabled", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_enabled", "PRODUCTION_AUTHORITY_DENIED"),
]

_M99_REQUEST_DENIALS = [
    ("broad_autonomy_requested", "BROAD_AUTONOMY_DENIED"),
    ("global_autonomy_switch_requested", "GLOBAL_AUTONOMY_SWITCH_DENIED"),
    ("execution_requested", "EXECUTION_DENIED"),
    ("tool_execution_requested", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_requested", "SHELL_EXECUTION_DENIED"),
    ("browser_action_requested", "BROWSER_ACTION_DENIED"),
    ("network_mutation_requested", "NETWORK_MUTATION_DENIED"),
    ("plugin_execution_requested", "PLUGIN_EXECUTION_DENIED"),
    ("background_worker_requested", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_requested", "SCHEDULER_DENIED"),
    ("mobile_sensor_requested", "MOBILE_SENSOR_DENIED"),
    ("memory_write_requested", "MEMORY_WRITE_DENIED"),
    ("context_injection_requested", "CONTEXT_INJECTION_DENIED"),
    ("credential_cookie_access_requested", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
    ("raw_prompt_payload_exposure_requested", "RAW_PROMPT_PAYLOAD_EXPOSURE_DENIED"),
    ("raw_file_export_requested", "RAW_FILE_EXPORT_DENIED"),
    ("full_file_read_requested", "FULL_FILE_READ_DENIED"),
    ("remote_execution_requested", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_requested", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_requested", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_requested", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_requested", "PRODUCTION_AUTHORITY_DENIED"),
]

_M99_REPORT_REQUIRED_TRUE = [
    ("freeze_only", "FREEZE_ONLY_REQUIRED"),
    ("review_only", "REVIEW_ONLY_REQUIRED"),
    ("deterministic", "DETERMINISTIC_REVIEW_REQUIRED"),
    ("m61_m98_covered", "M61_M98_COVERAGE_REQUIRED"),
    ("no_broad_unsandboxed_autonomy", "BROAD_AUTONOMY_DENIED"),
    ("no_production_authority", "PRODUCTION_AUTHORITY_DENIED"),
]

_M99_REPORT_DENIALS = [
    ("broad_autonomy_granted", "BROAD_AUTONOMY_DENIED"),
    ("global_autonomy_switch_enabled", "GLOBAL_AUTONOMY_SWITCH_DENIED"),
    ("execution_performed", "EXECUTION_DENIED"),
    ("tool_execution_performed", "TOOL_EXECUTION_DENIED"),
    ("shell_execution_performed", "SHELL_EXECUTION_DENIED"),
    ("browser_action_performed", "BROWSER_ACTION_DENIED"),
    ("network_mutation_performed", "NETWORK_MUTATION_DENIED"),
    ("plugin_execution_performed", "PLUGIN_EXECUTION_DENIED"),
    ("background_worker_started", "BACKGROUND_WORKER_DENIED"),
    ("scheduler_started", "SCHEDULER_DENIED"),
    ("mobile_sensor_performed", "MOBILE_SENSOR_DENIED"),
    ("memory_write_performed", "MEMORY_WRITE_DENIED"),
    ("context_injection_performed", "CONTEXT_INJECTION_DENIED"),
    ("credential_cookie_access_performed", "CREDENTIAL_COOKIE_ACCESS_DENIED"),
    ("raw_prompt_payload_exposed", "RAW_PROMPT_PAYLOAD_EXPOSURE_DENIED"),
    ("raw_file_export_performed", "RAW_FILE_EXPORT_DENIED"),
    ("full_file_read_performed", "FULL_FILE_READ_DENIED"),
    ("remote_execution_performed", "REMOTE_EXECUTION_DENIED"),
    ("backend_route_added", "BACKEND_ROUTE_DENIED"),
    ("control_center_control_added", "CONTROL_CENTER_CONTROL_DENIED"),
    ("dependency_added", "DEPENDENCY_CHANGE_DENIED"),
    ("production_authority_granted", "PRODUCTION_AUTHORITY_DENIED"),
]
