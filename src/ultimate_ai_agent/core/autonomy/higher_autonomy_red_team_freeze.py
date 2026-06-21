from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.autonomy.foundation_freeze import (
    _has_secret_like_extra,
    _model_payload,
    _ref_suffix,
)
from ultimate_ai_agent.core.autonomy.modes import _validate_m61_ref, _validate_safe_payload


HIGHER_AUTONOMY_RED_TEAM_FREEZE_DOCS = [
    "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE.md",
    "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_POLICY.md",
    "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_AUTHORITY_BOUNDARY.md",
    "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_RECEIPT_PLAN.md",
    "docs/autonomy/HIGHER_AUTONOMY_RED_TEAM_FREEZE_NON_GOALS.md",
    "docs/autonomy/M140_TO_M141_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(131, 140)
)


class HigherAutonomyRedTeamFreezeStatus(str, Enum):
    frozen_for_review = "frozen_for_review"


class _HigherAutonomyRedTeamFreezeModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class HigherAutonomyRedTeamFreezePolicy(_HigherAutonomyRedTeamFreezeModel):
    policy_ref: str = "higher-autonomy-red-team-freeze-policy:m140"
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    m131_m139_coverage_required: bool = True
    red_team_review_required: bool = True
    audit_replay_required: bool = True
    revocation_readiness_required: bool = True
    no_effect_receipt_required: bool = True
    no_broad_unsandboxed_autonomy_required: bool = True
    no_production_authority_required: bool = True
    m141_future_only: bool = True
    red_team_runtime_enabled: bool = False
    red_team_harness_execution_enabled: bool = False
    adversarial_test_execution_enabled: bool = False
    autonomous_execution_enabled: bool = False
    broad_autonomy_enabled: bool = False
    global_autonomy_switch_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_action_enabled: bool = False
    connector_action_enabled: bool = False
    network_access_enabled: bool = False
    plugin_execution_enabled: bool = False
    background_worker_enabled: bool = False
    scheduler_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    raw_prompt_payload_exposure_enabled: bool = False
    credential_cookie_access_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    alpha_release_enabled: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M140_SECRET_LIKE_RED_TEAM_FREEZE_CONTENT_DENIED") from exc
        return self


class HigherAutonomyRedTeamFreezeRequest(_HigherAutonomyRedTeamFreezeModel):
    request_ref: str
    freeze_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    red_team_checklist_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    safe_summary: str
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    m131_m139_coverage_required: bool = True
    red_team_review_required: bool = True
    audit_replay_required: bool = True
    revocation_readiness_required: bool = True
    no_effect_receipt_required: bool = True
    no_broad_unsandboxed_autonomy_required: bool = True
    no_production_authority_required: bool = True
    red_team_runtime_requested: bool = False
    red_team_harness_execution_requested: bool = False
    adversarial_test_execution_requested: bool = False
    autonomous_execution_requested: bool = False
    broad_autonomy_requested: bool = False
    global_autonomy_switch_requested: bool = False
    execution_requested: bool = False
    tool_execution_requested: bool = False
    shell_execution_requested: bool = False
    browser_action_requested: bool = False
    connector_action_requested: bool = False
    network_access_requested: bool = False
    plugin_execution_requested: bool = False
    background_worker_requested: bool = False
    scheduler_requested: bool = False
    mobile_sensor_requested: bool = False
    remote_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    raw_prompt_payload_exposure_requested: bool = False
    credential_cookie_access_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    alpha_release_requested: bool = False
    beta_release_requested: bool = False
    production_authority_requested: bool = False
    contains_raw_prompt: bool = False
    contains_raw_provider_payload: bool = False
    contains_cookie_or_credential: bool = False
    contains_secret: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class HigherAutonomyRedTeamFreezeReport(_HigherAutonomyRedTeamFreezeModel):
    report_ref: str
    freeze_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    red_team_checklist_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: HigherAutonomyRedTeamFreezeStatus = (
        HigherAutonomyRedTeamFreezeStatus.frozen_for_review
    )
    contract_only: bool = True
    review_only: bool = True
    freeze_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    m131_m139_covered: bool = True
    red_team_review_bound: bool = True
    audit_replay_bound: bool = True
    revocation_readiness_bound: bool = True
    no_effect_receipt_required: bool = True
    no_broad_unsandboxed_autonomy: bool = True
    no_production_authority: bool = True
    red_team_runtime_started: bool = False
    red_team_harness_execution_performed: bool = False
    adversarial_test_execution_performed: bool = False
    autonomous_execution_performed: bool = False
    broad_autonomy_granted: bool = False
    global_autonomy_switch_enabled: bool = False
    execution_performed: bool = False
    tool_execution_performed: bool = False
    shell_execution_performed: bool = False
    browser_action_performed: bool = False
    connector_action_performed: bool = False
    network_access_performed: bool = False
    plugin_execution_performed: bool = False
    background_worker_started: bool = False
    scheduler_started: bool = False
    mobile_sensor_performed: bool = False
    remote_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    raw_prompt_payload_exposed: bool = False
    credential_cookie_access_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    alpha_release_enabled: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _report_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M140_REASON_CODE_REQUIRED")
        return self


def build_higher_autonomy_red_team_freeze_report(
    request: HigherAutonomyRedTeamFreezeRequest,
    policy: HigherAutonomyRedTeamFreezePolicy | None = None,
) -> HigherAutonomyRedTeamFreezeReport:
    active_policy = validate_higher_autonomy_red_team_freeze_policy(
        policy or HigherAutonomyRedTeamFreezePolicy()
    )
    validated_request = validate_higher_autonomy_red_team_freeze_request(request)
    report = HigherAutonomyRedTeamFreezeReport(
        report_ref=(
            "higher-autonomy-red-team-freeze-report:"
            f"{_ref_suffix(validated_request.freeze_ref)}"
        ),
        freeze_ref=validated_request.freeze_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        red_team_checklist_refs=list(validated_request.red_team_checklist_refs),
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        no_effect_receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        freeze_only=active_policy.freeze_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        m131_m139_covered=active_policy.m131_m139_coverage_required,
        red_team_review_bound=active_policy.red_team_review_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_readiness_bound=active_policy.revocation_readiness_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_broad_unsandboxed_autonomy=(
            active_policy.no_broad_unsandboxed_autonomy_required
        ),
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M140_HIGHER_AUTONOMY_RED_TEAM_FREEZE_REVIEW_ONLY",
            "M140_M131_M139_COVERED",
            "M140_NO_RED_TEAM_RUNTIME",
            "M140_NO_BROAD_UNSANDBOXED_AUTONOMY",
            "M140_NO_PRODUCTION_AUTHORITY",
            "M141_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M140 freezes the accepted M131-M139 higher-autonomy surface for "
            "review using safe refs, red-team checklist refs, audit refs, "
            "replay refs, revocation refs, kill-switch refs, and a no-effect "
            "receipt plan. It grants no red-team runtime, harness execution, "
            "adversarial test execution, autonomous execution, broad autonomy, "
            "global autonomy switch, browser action, connector action, tool "
            "execution, shell execution, network access, plugin execution, "
            "model call, memory write, context injection, backend route, "
            "Control Center control, dependency, alpha or beta release, or "
            "production authority."
        ),
    )
    return validate_higher_autonomy_red_team_freeze_report(report)


def validate_higher_autonomy_red_team_freeze_policy(
    policy: HigherAutonomyRedTeamFreezePolicy,
) -> HigherAutonomyRedTeamFreezePolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, HigherAutonomyRedTeamFreezePolicy):
        raise ValueError("M140_SECRET_LIKE_RED_TEAM_FREEZE_CONTENT_DENIED")
    validated = HigherAutonomyRedTeamFreezePolicy.model_validate(payload)
    for field_name, reason in _M140_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M140_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M140_SECRET_LIKE_RED_TEAM_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_higher_autonomy_red_team_freeze_request(
    request: HigherAutonomyRedTeamFreezeRequest,
) -> HigherAutonomyRedTeamFreezeRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, HigherAutonomyRedTeamFreezeRequest):
        raise ValueError("M140_SECRET_LIKE_RED_TEAM_FREEZE_CONTENT_DENIED")
    _deny_enabled(_M140_REQUEST_DENIALS, payload)
    validated = HigherAutonomyRedTeamFreezeRequest.model_validate(payload)
    for field_name, reason in _M140_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M140_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M140_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    _validate_ref_list(
        validated.red_team_checklist_refs,
        "red_team_checklist_ref",
        "M140_RED_TEAM_CHECKLIST_REF_REQUIRED",
    )
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M140_SECRET_LIKE_RED_TEAM_FREEZE_CONTENT_DENIED") from exc
    return validated


def validate_higher_autonomy_red_team_freeze_report(
    report: HigherAutonomyRedTeamFreezeReport,
) -> HigherAutonomyRedTeamFreezeReport:
    payload = _model_payload(report)
    if _has_secret_like_extra(payload, HigherAutonomyRedTeamFreezeReport):
        raise ValueError("M140_SECRET_LIKE_RED_TEAM_FREEZE_CONTENT_DENIED")
    _deny_enabled(_M140_REPORT_DENIALS, payload)
    validated = HigherAutonomyRedTeamFreezeReport.model_validate(payload)
    for field_name, reason in _M140_REPORT_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M140_REPORT_DENIALS, _model_payload(validated))
    if validated.status != HigherAutonomyRedTeamFreezeStatus.frozen_for_review:
        raise ValueError("M140_FREEZE_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M140_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    _validate_ref_list(
        validated.red_team_checklist_refs,
        "red_team_checklist_ref",
        "M140_RED_TEAM_CHECKLIST_REF_REQUIRED",
    )
    if "M140_HIGHER_AUTONOMY_RED_TEAM_FREEZE_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M140_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M140_SECRET_LIKE_RED_TEAM_FREEZE_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: HigherAutonomyRedTeamFreezeRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.freeze_ref, "freeze_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _report_ref_pairs(report: HigherAutonomyRedTeamFreezeReport) -> list[Any]:
    return [
        (report.report_ref, "report_ref"),
        (report.freeze_ref, "freeze_ref"),
        (report.request_ref, "request_ref"),
        (report.baseline_ref, "baseline_ref"),
        (report.actor_ref, "actor_ref"),
        (report.audit_ref, "audit_ref"),
        (report.replay_ref, "replay_ref"),
        (report.revocation_ref, "revocation_ref"),
        (report.kill_switch_ref, "kill_switch_ref"),
        (report.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _validate_accepted_checkpoints(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M140_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M140_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M140_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M140_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M140_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M140_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M140_REQUIRED_TRUE = [
    ("contract_only", "M140_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M140_REVIEW_ONLY_REQUIRED"),
    ("freeze_only", "M140_FREEZE_ONLY_REQUIRED"),
    ("deterministic", "M140_DETERMINISTIC_REQUIRED"),
    ("local_only", "M140_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M140_SAFE_REFS_ONLY_REQUIRED"),
    ("m131_m139_coverage_required", "M140_M131_M139_COVERAGE_REQUIRED"),
    ("red_team_review_required", "M140_RED_TEAM_REVIEW_REQUIRED"),
    ("audit_replay_required", "M140_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_required", "M140_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M140_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_broad_unsandboxed_autonomy_required", "M140_BROAD_AUTONOMY_DENIED"),
    ("no_production_authority_required", "M140_PRODUCTION_AUTHORITY_DENIED"),
]

_M140_REPORT_REQUIRED_TRUE = [
    ("contract_only", "M140_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M140_REVIEW_ONLY_REQUIRED"),
    ("freeze_only", "M140_FREEZE_ONLY_REQUIRED"),
    ("deterministic", "M140_DETERMINISTIC_REQUIRED"),
    ("local_only", "M140_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M140_SAFE_REFS_ONLY_REQUIRED"),
    ("m131_m139_covered", "M140_M131_M139_COVERAGE_REQUIRED"),
    ("red_team_review_bound", "M140_RED_TEAM_REVIEW_REQUIRED"),
    ("audit_replay_bound", "M140_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_bound", "M140_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M140_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_broad_unsandboxed_autonomy", "M140_BROAD_AUTONOMY_DENIED"),
    ("no_production_authority", "M140_PRODUCTION_AUTHORITY_DENIED"),
]

_M140_POLICY_DENIALS = {
    "red_team_runtime_enabled": "M140_RED_TEAM_RUNTIME_DENIED",
    "red_team_harness_execution_enabled": "M140_RED_TEAM_HARNESS_EXECUTION_DENIED",
    "adversarial_test_execution_enabled": "M140_ADVERSARIAL_TEST_EXECUTION_DENIED",
    "autonomous_execution_enabled": "M140_AUTONOMOUS_EXECUTION_DENIED",
    "broad_autonomy_enabled": "M140_BROAD_AUTONOMY_DENIED",
    "global_autonomy_switch_enabled": "M140_GLOBAL_AUTONOMY_SWITCH_DENIED",
    "execution_enabled": "M140_EXECUTION_DENIED",
    "tool_execution_enabled": "M140_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M140_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M140_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M140_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M140_NETWORK_ACCESS_DENIED",
    "plugin_execution_enabled": "M140_PLUGIN_EXECUTION_DENIED",
    "background_worker_enabled": "M140_BACKGROUND_WORKER_DENIED",
    "scheduler_enabled": "M140_SCHEDULER_DENIED",
    "mobile_sensor_enabled": "M140_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M140_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M140_MODEL_CALL_DENIED",
    "memory_write_enabled": "M140_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M140_CONTEXT_INJECTION_DENIED",
    "raw_prompt_payload_exposure_enabled": "M140_RAW_PROMPT_PAYLOAD_DENIED",
    "credential_cookie_access_enabled": "M140_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "backend_route_enabled": "M140_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M140_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M140_DEPENDENCY_DENIED",
    "alpha_release_enabled": "M140_ALPHA_RELEASE_DENIED",
    "beta_release_enabled": "M140_BETA_RELEASE_DENIED",
    "production_authority_granted": "M140_PRODUCTION_AUTHORITY_DENIED",
}

_M140_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M140_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "red_team_harness_execution_requested": "M140_RED_TEAM_HARNESS_EXECUTION_DENIED",
    "adversarial_test_execution_requested": "M140_ADVERSARIAL_TEST_EXECUTION_DENIED",
    "autonomous_execution_requested": "M140_AUTONOMOUS_EXECUTION_DENIED",
    "dependency_requested": "M140_DEPENDENCY_DENIED",
    "alpha_release_requested": "M140_ALPHA_RELEASE_DENIED",
    "beta_release_requested": "M140_BETA_RELEASE_DENIED",
    "production_authority_requested": "M140_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_prompt": "M140_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M140_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M140_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M140_SECRET_DENIED",
}

_M140_REPORT_DENIALS = {
    "red_team_runtime_started": "M140_RED_TEAM_RUNTIME_DENIED",
    "red_team_harness_execution_performed": "M140_RED_TEAM_HARNESS_EXECUTION_DENIED",
    "adversarial_test_execution_performed": "M140_ADVERSARIAL_TEST_EXECUTION_DENIED",
    "autonomous_execution_performed": "M140_AUTONOMOUS_EXECUTION_DENIED",
    "broad_autonomy_granted": "M140_BROAD_AUTONOMY_DENIED",
    "global_autonomy_switch_enabled": "M140_GLOBAL_AUTONOMY_SWITCH_DENIED",
    "execution_performed": "M140_EXECUTION_DENIED",
    "tool_execution_performed": "M140_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M140_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M140_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M140_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M140_NETWORK_ACCESS_DENIED",
    "plugin_execution_performed": "M140_PLUGIN_EXECUTION_DENIED",
    "background_worker_started": "M140_BACKGROUND_WORKER_DENIED",
    "scheduler_started": "M140_SCHEDULER_DENIED",
    "mobile_sensor_performed": "M140_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M140_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M140_MODEL_CALL_DENIED",
    "memory_write_performed": "M140_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M140_CONTEXT_INJECTION_DENIED",
    "raw_prompt_payload_exposed": "M140_RAW_PROMPT_PAYLOAD_DENIED",
    "credential_cookie_access_performed": "M140_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "backend_route_added": "M140_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M140_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M140_DEPENDENCY_DENIED",
    "alpha_release_enabled": "M140_ALPHA_RELEASE_DENIED",
    "beta_release_enabled": "M140_BETA_RELEASE_DENIED",
    "production_authority_granted": "M140_PRODUCTION_AUTHORITY_DENIED",
}
