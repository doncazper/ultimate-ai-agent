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


ENTERPRISE_PRO_SAFETY_MODES_DOCS = [
    "docs/productization/ENTERPRISE_PRO_SAFETY_MODES.md",
    "docs/productization/ENTERPRISE_PRO_SAFETY_MODES_POLICY.md",
    "docs/productization/ENTERPRISE_PRO_SAFETY_MODES_AUTHORITY_BOUNDARY.md",
    "docs/productization/ENTERPRISE_PRO_SAFETY_MODES_RECEIPT_PLAN.md",
    "docs/productization/ENTERPRISE_PRO_SAFETY_MODES_NON_GOALS.md",
    "docs/productization/M145_TO_M146_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M145_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 145)
)


class EnterpriseProSafetyModesStatus(str, Enum):
    safety_modes_recorded = "safety_modes_recorded"


class _EnterpriseProSafetyModesModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class EnterpriseProSafetyModesPolicy(_EnterpriseProSafetyModesModel):
    policy_ref: str = "enterprise-pro-safety-modes-policy:m145"
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    safety_modes_only: bool = True
    disabled_by_default_required: bool = True
    m101_m144_coverage_required: bool = True
    enterprise_safety_mode_refs_required: bool = True
    pro_safety_mode_refs_required: bool = True
    workspace_boundary_refs_required: bool = True
    role_policy_refs_required: bool = True
    authority_ceiling_refs_required: bool = True
    feature_availability_refs_required: bool = True
    escalation_policy_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_enterprise_runtime_required: bool = True
    no_pro_runtime_required: bool = True
    no_plan_enforcement_required: bool = True
    no_billing_runtime_required: bool = True
    no_account_tenant_runtime_required: bool = True
    no_role_runtime_required: bool = True
    no_auth_runtime_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    m146_future_only: bool = True
    enterprise_runtime_enabled: bool = False
    pro_runtime_enabled: bool = False
    safety_mode_runtime_enabled: bool = False
    plan_enforcement_enabled: bool = False
    billing_runtime_enabled: bool = False
    billing_plan_boundary_enabled: bool = False
    account_tenant_runtime_enabled: bool = False
    role_runtime_enabled: bool = False
    workspace_sharing_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_enabled: bool = False
    connector_runtime_enabled: bool = False
    plugin_marketplace_runtime_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_action_enabled: bool = False
    connector_action_enabled: bool = False
    network_access_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M145_SECRET_LIKE_SAFETY_MODE_CONTENT_DENIED") from exc
        return self


class EnterpriseProSafetyModesRequest(_EnterpriseProSafetyModesModel):
    request_ref: str
    safety_modes_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    enterprise_safety_mode_refs: list[str]
    pro_safety_mode_refs: list[str]
    workspace_boundary_refs: list[str]
    role_policy_refs: list[str]
    authority_ceiling_refs: list[str]
    feature_availability_refs: list[str]
    escalation_policy_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    safe_summary: str
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    safety_modes_only: bool = True
    disabled_by_default_required: bool = True
    m101_m144_coverage_required: bool = True
    enterprise_safety_mode_refs_required: bool = True
    pro_safety_mode_refs_required: bool = True
    workspace_boundary_refs_required: bool = True
    role_policy_refs_required: bool = True
    authority_ceiling_refs_required: bool = True
    feature_availability_refs_required: bool = True
    escalation_policy_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_enterprise_runtime_required: bool = True
    no_pro_runtime_required: bool = True
    no_plan_enforcement_required: bool = True
    no_billing_runtime_required: bool = True
    no_account_tenant_runtime_required: bool = True
    no_role_runtime_required: bool = True
    no_auth_runtime_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    enterprise_runtime_requested: bool = False
    pro_runtime_requested: bool = False
    safety_mode_runtime_requested: bool = False
    plan_enforcement_requested: bool = False
    billing_runtime_requested: bool = False
    billing_plan_boundary_requested: bool = False
    account_tenant_runtime_requested: bool = False
    role_runtime_requested: bool = False
    workspace_sharing_requested: bool = False
    auth_runtime_requested: bool = False
    login_requested: bool = False
    session_cookie_requested: bool = False
    credential_handling_requested: bool = False
    connector_runtime_requested: bool = False
    plugin_marketplace_runtime_requested: bool = False
    execution_requested: bool = False
    tool_execution_requested: bool = False
    shell_execution_requested: bool = False
    browser_action_requested: bool = False
    connector_action_requested: bool = False
    network_access_requested: bool = False
    mobile_sensor_requested: bool = False
    remote_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
    beta_release_requested: bool = False
    production_authority_requested: bool = False
    contains_raw_private_content: bool = False
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


class EnterpriseProSafetyModesRecord(_EnterpriseProSafetyModesModel):
    record_ref: str
    safety_modes_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    enterprise_safety_mode_refs: list[str]
    pro_safety_mode_refs: list[str]
    workspace_boundary_refs: list[str]
    role_policy_refs: list[str]
    authority_ceiling_refs: list[str]
    feature_availability_refs: list[str]
    escalation_policy_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: EnterpriseProSafetyModesStatus = (
        EnterpriseProSafetyModesStatus.safety_modes_recorded
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    safety_modes_only: bool = True
    disabled_by_default: bool = True
    m101_m144_covered: bool = True
    enterprise_safety_modes_bound: bool = True
    pro_safety_modes_bound: bool = True
    workspace_boundaries_bound: bool = True
    role_policies_bound: bool = True
    authority_ceilings_bound: bool = True
    feature_availability_bound: bool = True
    escalation_policies_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    no_effect_receipt_required: bool = True
    no_enterprise_runtime: bool = True
    no_pro_runtime: bool = True
    no_plan_enforcement: bool = True
    no_billing_runtime: bool = True
    no_account_tenant_runtime: bool = True
    no_role_runtime: bool = True
    no_auth_runtime: bool = True
    no_backend_route: bool = True
    no_control_center_control: bool = True
    no_dependency: bool = True
    no_production_authority: bool = True
    enterprise_runtime_started: bool = False
    pro_runtime_started: bool = False
    safety_mode_runtime_started: bool = False
    plan_enforcement_performed: bool = False
    billing_runtime_started: bool = False
    billing_plan_boundary_performed: bool = False
    account_tenant_runtime_started: bool = False
    role_runtime_started: bool = False
    workspace_sharing_performed: bool = False
    auth_runtime_started: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_performed: bool = False
    connector_runtime_started: bool = False
    plugin_marketplace_runtime_started: bool = False
    execution_performed: bool = False
    tool_execution_performed: bool = False
    shell_execution_performed: bool = False
    browser_action_performed: bool = False
    connector_action_performed: bool = False
    network_access_performed: bool = False
    mobile_sensor_performed: bool = False
    remote_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    side_effects_performed: list[str] = Field(default_factory=list)
    reason_codes: list[str]
    safe_summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        for value, field_name in _record_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M145_REASON_CODE_REQUIRED")
        return self


def build_enterprise_pro_safety_modes_record(
    request: EnterpriseProSafetyModesRequest,
    policy: EnterpriseProSafetyModesPolicy | None = None,
) -> EnterpriseProSafetyModesRecord:
    active_policy = validate_enterprise_pro_safety_modes_policy(
        policy or EnterpriseProSafetyModesPolicy()
    )
    validated_request = validate_enterprise_pro_safety_modes_request(request)
    record = EnterpriseProSafetyModesRecord(
        record_ref=f"enterprise-pro-safety-modes-record:{_ref_suffix(validated_request.safety_modes_ref)}",
        safety_modes_ref=validated_request.safety_modes_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        enterprise_safety_mode_refs=list(
            validated_request.enterprise_safety_mode_refs
        ),
        pro_safety_mode_refs=list(validated_request.pro_safety_mode_refs),
        workspace_boundary_refs=list(validated_request.workspace_boundary_refs),
        role_policy_refs=list(validated_request.role_policy_refs),
        authority_ceiling_refs=list(validated_request.authority_ceiling_refs),
        feature_availability_refs=list(validated_request.feature_availability_refs),
        escalation_policy_refs=list(validated_request.escalation_policy_refs),
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        no_effect_receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        safety_modes_only=active_policy.safety_modes_only,
        disabled_by_default=active_policy.disabled_by_default_required,
        m101_m144_covered=active_policy.m101_m144_coverage_required,
        enterprise_safety_modes_bound=(
            active_policy.enterprise_safety_mode_refs_required
        ),
        pro_safety_modes_bound=active_policy.pro_safety_mode_refs_required,
        workspace_boundaries_bound=active_policy.workspace_boundary_refs_required,
        role_policies_bound=active_policy.role_policy_refs_required,
        authority_ceilings_bound=active_policy.authority_ceiling_refs_required,
        feature_availability_bound=active_policy.feature_availability_refs_required,
        escalation_policies_bound=active_policy.escalation_policy_refs_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_enterprise_runtime=active_policy.no_enterprise_runtime_required,
        no_pro_runtime=active_policy.no_pro_runtime_required,
        no_plan_enforcement=active_policy.no_plan_enforcement_required,
        no_billing_runtime=active_policy.no_billing_runtime_required,
        no_account_tenant_runtime=(
            active_policy.no_account_tenant_runtime_required
        ),
        no_role_runtime=active_policy.no_role_runtime_required,
        no_auth_runtime=active_policy.no_auth_runtime_required,
        no_backend_route=active_policy.no_backend_route_required,
        no_control_center_control=active_policy.no_control_center_control_required,
        no_dependency=active_policy.no_dependency_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M145_ENTERPRISE_PRO_SAFETY_MODES_REVIEW_ONLY",
            "M145_M101_M144_COVERED",
            "M145_DISABLED_BY_DEFAULT",
            "M145_NO_ENTERPRISE_RUNTIME",
            "M145_NO_PRO_RUNTIME",
            "M145_NO_PLAN_ENFORCEMENT",
            "M145_NO_BILLING_RUNTIME",
            "M145_NO_ACCOUNT_TENANT_RUNTIME",
            "M145_NO_AUTH_RUNTIME",
            "M145_NO_BACKEND_ROUTE",
            "M145_NO_PRODUCTION_AUTHORITY",
            "M146_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M145 records contract-only Enterprise/Pro safety mode refs using "
            "safe enterprise safety mode, pro safety mode, workspace boundary, "
            "role policy, authority ceiling, feature availability, escalation, "
            "audit, replay, revocation, kill-switch, and no-effect receipt refs. "
            "It grants no enterprise runtime, pro runtime, plan enforcement, "
            "billing runtime, account or tenant runtime, auth runtime, backend "
            "route, Control Center control, dependency, beta release, or "
            "production authority."
        ),
    )
    return validate_enterprise_pro_safety_modes_record(record)


def validate_enterprise_pro_safety_modes_policy(
    policy: EnterpriseProSafetyModesPolicy,
) -> EnterpriseProSafetyModesPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, EnterpriseProSafetyModesPolicy):
        raise ValueError("M145_SECRET_LIKE_SAFETY_MODE_CONTENT_DENIED")
    validated = EnterpriseProSafetyModesPolicy.model_validate(payload)
    for field_name, reason in _M145_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M145_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M145_SECRET_LIKE_SAFETY_MODE_CONTENT_DENIED") from exc
    return validated


def validate_enterprise_pro_safety_modes_request(
    request: EnterpriseProSafetyModesRequest,
) -> EnterpriseProSafetyModesRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, EnterpriseProSafetyModesRequest):
        raise ValueError("M145_SECRET_LIKE_SAFETY_MODE_CONTENT_DENIED")
    _deny_enabled(_M145_REQUEST_DENIALS, payload)
    validated = EnterpriseProSafetyModesRequest.model_validate(payload)
    for field_name, reason in _M145_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M145_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M145_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _request_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M145_SECRET_LIKE_SAFETY_MODE_CONTENT_DENIED") from exc
    return validated


def validate_enterprise_pro_safety_modes_record(
    record: EnterpriseProSafetyModesRecord,
) -> EnterpriseProSafetyModesRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, EnterpriseProSafetyModesRecord):
        raise ValueError("M145_SECRET_LIKE_SAFETY_MODE_CONTENT_DENIED")
    _deny_enabled(_M145_RECORD_DENIALS, payload)
    validated = EnterpriseProSafetyModesRecord.model_validate(payload)
    for field_name, reason in _M145_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M145_RECORD_DENIALS, _model_payload(validated))
    if validated.status != EnterpriseProSafetyModesStatus.safety_modes_recorded:
        raise ValueError("M145_SAFETY_MODES_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M145_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _record_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    if "M145_ENTERPRISE_PRO_SAFETY_MODES_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M145_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M145_SECRET_LIKE_SAFETY_MODE_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: EnterpriseProSafetyModesRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.safety_modes_ref, "safety_modes_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: EnterpriseProSafetyModesRecord) -> list[Any]:
    return [
        (record.record_ref, "record_ref"),
        (record.safety_modes_ref, "safety_modes_ref"),
        (record.request_ref, "request_ref"),
        (record.baseline_ref, "baseline_ref"),
        (record.actor_ref, "actor_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _request_ref_lists(request: EnterpriseProSafetyModesRequest) -> list[Any]:
    return [
        (
            request.enterprise_safety_mode_refs,
            "enterprise_safety_mode_ref",
            "M145_ENTERPRISE_SAFETY_MODE_REF_REQUIRED",
        ),
        (
            request.pro_safety_mode_refs,
            "pro_safety_mode_ref",
            "M145_PRO_SAFETY_MODE_REF_REQUIRED",
        ),
        (
            request.workspace_boundary_refs,
            "workspace_boundary_ref",
            "M145_WORKSPACE_BOUNDARY_REF_REQUIRED",
        ),
        (
            request.role_policy_refs,
            "role_policy_ref",
            "M145_ROLE_POLICY_REF_REQUIRED",
        ),
        (
            request.authority_ceiling_refs,
            "authority_ceiling_ref",
            "M145_AUTHORITY_CEILING_REF_REQUIRED",
        ),
        (
            request.feature_availability_refs,
            "feature_availability_ref",
            "M145_FEATURE_AVAILABILITY_REF_REQUIRED",
        ),
        (
            request.escalation_policy_refs,
            "escalation_policy_ref",
            "M145_ESCALATION_POLICY_REF_REQUIRED",
        ),
    ]


def _record_ref_lists(record: EnterpriseProSafetyModesRecord) -> list[Any]:
    return [
        (
            record.enterprise_safety_mode_refs,
            "enterprise_safety_mode_ref",
            "M145_ENTERPRISE_SAFETY_MODE_REF_REQUIRED",
        ),
        (
            record.pro_safety_mode_refs,
            "pro_safety_mode_ref",
            "M145_PRO_SAFETY_MODE_REF_REQUIRED",
        ),
        (
            record.workspace_boundary_refs,
            "workspace_boundary_ref",
            "M145_WORKSPACE_BOUNDARY_REF_REQUIRED",
        ),
        (record.role_policy_refs, "role_policy_ref", "M145_ROLE_POLICY_REF_REQUIRED"),
        (
            record.authority_ceiling_refs,
            "authority_ceiling_ref",
            "M145_AUTHORITY_CEILING_REF_REQUIRED",
        ),
        (
            record.feature_availability_refs,
            "feature_availability_ref",
            "M145_FEATURE_AVAILABILITY_REF_REQUIRED",
        ),
        (
            record.escalation_policy_refs,
            "escalation_policy_ref",
            "M145_ESCALATION_POLICY_REF_REQUIRED",
        ),
    ]


def _validate_accepted_checkpoints(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M145_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M145_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M145_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M145_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M145_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M145_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M145_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M145_REQUIRED_TRUE = [
    ("contract_only", "M145_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M145_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M145_DETERMINISTIC_REQUIRED"),
    ("local_only", "M145_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M145_SAFE_REFS_ONLY_REQUIRED"),
    ("safety_modes_only", "M145_SAFETY_MODES_ONLY_REQUIRED"),
    ("disabled_by_default_required", "M145_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m144_coverage_required", "M145_M101_M144_COVERAGE_REQUIRED"),
    (
        "enterprise_safety_mode_refs_required",
        "M145_ENTERPRISE_SAFETY_MODE_REF_REQUIRED",
    ),
    ("pro_safety_mode_refs_required", "M145_PRO_SAFETY_MODE_REF_REQUIRED"),
    ("workspace_boundary_refs_required", "M145_WORKSPACE_BOUNDARY_REF_REQUIRED"),
    ("role_policy_refs_required", "M145_ROLE_POLICY_REF_REQUIRED"),
    ("authority_ceiling_refs_required", "M145_AUTHORITY_CEILING_REF_REQUIRED"),
    (
        "feature_availability_refs_required",
        "M145_FEATURE_AVAILABILITY_REF_REQUIRED",
    ),
    ("escalation_policy_refs_required", "M145_ESCALATION_POLICY_REF_REQUIRED"),
    ("audit_replay_required", "M145_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M145_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M145_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_enterprise_runtime_required", "M145_ENTERPRISE_RUNTIME_DENIED"),
    ("no_pro_runtime_required", "M145_PRO_RUNTIME_DENIED"),
    ("no_plan_enforcement_required", "M145_PLAN_ENFORCEMENT_DENIED"),
    ("no_billing_runtime_required", "M145_BILLING_RUNTIME_DENIED"),
    ("no_account_tenant_runtime_required", "M145_ACCOUNT_TENANT_RUNTIME_DENIED"),
    ("no_role_runtime_required", "M145_ROLE_RUNTIME_DENIED"),
    ("no_auth_runtime_required", "M145_AUTH_RUNTIME_DENIED"),
    ("no_backend_route_required", "M145_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control_required", "M145_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency_required", "M145_DEPENDENCY_DENIED"),
    ("no_production_authority_required", "M145_PRODUCTION_AUTHORITY_DENIED"),
]

_M145_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M145_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M145_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M145_DETERMINISTIC_REQUIRED"),
    ("local_only", "M145_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M145_SAFE_REFS_ONLY_REQUIRED"),
    ("safety_modes_only", "M145_SAFETY_MODES_ONLY_REQUIRED"),
    ("disabled_by_default", "M145_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m144_covered", "M145_M101_M144_COVERAGE_REQUIRED"),
    ("enterprise_safety_modes_bound", "M145_ENTERPRISE_SAFETY_MODE_REF_REQUIRED"),
    ("pro_safety_modes_bound", "M145_PRO_SAFETY_MODE_REF_REQUIRED"),
    ("workspace_boundaries_bound", "M145_WORKSPACE_BOUNDARY_REF_REQUIRED"),
    ("role_policies_bound", "M145_ROLE_POLICY_REF_REQUIRED"),
    ("authority_ceilings_bound", "M145_AUTHORITY_CEILING_REF_REQUIRED"),
    ("feature_availability_bound", "M145_FEATURE_AVAILABILITY_REF_REQUIRED"),
    ("escalation_policies_bound", "M145_ESCALATION_POLICY_REF_REQUIRED"),
    ("audit_replay_bound", "M145_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M145_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M145_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_enterprise_runtime", "M145_ENTERPRISE_RUNTIME_DENIED"),
    ("no_pro_runtime", "M145_PRO_RUNTIME_DENIED"),
    ("no_plan_enforcement", "M145_PLAN_ENFORCEMENT_DENIED"),
    ("no_billing_runtime", "M145_BILLING_RUNTIME_DENIED"),
    ("no_account_tenant_runtime", "M145_ACCOUNT_TENANT_RUNTIME_DENIED"),
    ("no_role_runtime", "M145_ROLE_RUNTIME_DENIED"),
    ("no_auth_runtime", "M145_AUTH_RUNTIME_DENIED"),
    ("no_backend_route", "M145_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control", "M145_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency", "M145_DEPENDENCY_DENIED"),
    ("no_production_authority", "M145_PRODUCTION_AUTHORITY_DENIED"),
]

_M145_POLICY_DENIALS = {
    "enterprise_runtime_enabled": "M145_ENTERPRISE_RUNTIME_DENIED",
    "pro_runtime_enabled": "M145_PRO_RUNTIME_DENIED",
    "safety_mode_runtime_enabled": "M145_SAFETY_MODE_RUNTIME_DENIED",
    "plan_enforcement_enabled": "M145_PLAN_ENFORCEMENT_DENIED",
    "billing_runtime_enabled": "M145_BILLING_RUNTIME_DENIED",
    "billing_plan_boundary_enabled": "M145_BILLING_PLAN_BOUNDARY_DENIED",
    "account_tenant_runtime_enabled": "M145_ACCOUNT_TENANT_RUNTIME_DENIED",
    "role_runtime_enabled": "M145_ROLE_RUNTIME_DENIED",
    "workspace_sharing_enabled": "M145_WORKSPACE_SHARING_DENIED",
    "auth_runtime_enabled": "M145_AUTH_RUNTIME_DENIED",
    "login_enabled": "M145_LOGIN_DENIED",
    "session_cookie_enabled": "M145_SESSION_COOKIE_DENIED",
    "credential_handling_enabled": "M145_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_enabled": "M145_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_enabled": "M145_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_enabled": "M145_EXECUTION_DENIED",
    "tool_execution_enabled": "M145_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M145_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M145_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M145_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M145_NETWORK_ACCESS_DENIED",
    "mobile_sensor_enabled": "M145_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M145_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M145_MODEL_CALL_DENIED",
    "memory_write_enabled": "M145_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M145_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M145_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M145_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M145_DEPENDENCY_DENIED",
    "beta_release_enabled": "M145_BETA_RELEASE_DENIED",
    "production_authority_granted": "M145_PRODUCTION_AUTHORITY_DENIED",
}

_M145_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M145_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "enterprise_runtime_requested": "M145_ENTERPRISE_RUNTIME_DENIED",
    "pro_runtime_requested": "M145_PRO_RUNTIME_DENIED",
    "safety_mode_runtime_requested": "M145_SAFETY_MODE_RUNTIME_DENIED",
    "plan_enforcement_requested": "M145_PLAN_ENFORCEMENT_DENIED",
    "billing_runtime_requested": "M145_BILLING_RUNTIME_DENIED",
    "billing_plan_boundary_requested": "M145_BILLING_PLAN_BOUNDARY_DENIED",
    "account_tenant_runtime_requested": "M145_ACCOUNT_TENANT_RUNTIME_DENIED",
    "role_runtime_requested": "M145_ROLE_RUNTIME_DENIED",
    "workspace_sharing_requested": "M145_WORKSPACE_SHARING_DENIED",
    "auth_runtime_requested": "M145_AUTH_RUNTIME_DENIED",
    "login_requested": "M145_LOGIN_DENIED",
    "session_cookie_requested": "M145_SESSION_COOKIE_DENIED",
    "credential_handling_requested": "M145_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_requested": "M145_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_requested": "M145_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "production_authority_requested": "M145_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_private_content": "M145_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_prompt": "M145_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M145_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M145_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M145_SECRET_DENIED",
    "dependency_requested": "M145_DEPENDENCY_DENIED",
}

_M145_RECORD_DENIALS = {
    "enterprise_runtime_started": "M145_ENTERPRISE_RUNTIME_DENIED",
    "pro_runtime_started": "M145_PRO_RUNTIME_DENIED",
    "safety_mode_runtime_started": "M145_SAFETY_MODE_RUNTIME_DENIED",
    "plan_enforcement_performed": "M145_PLAN_ENFORCEMENT_DENIED",
    "billing_runtime_started": "M145_BILLING_RUNTIME_DENIED",
    "billing_plan_boundary_performed": "M145_BILLING_PLAN_BOUNDARY_DENIED",
    "account_tenant_runtime_started": "M145_ACCOUNT_TENANT_RUNTIME_DENIED",
    "role_runtime_started": "M145_ROLE_RUNTIME_DENIED",
    "workspace_sharing_performed": "M145_WORKSPACE_SHARING_DENIED",
    "auth_runtime_started": "M145_AUTH_RUNTIME_DENIED",
    "login_enabled": "M145_LOGIN_DENIED",
    "session_cookie_enabled": "M145_SESSION_COOKIE_DENIED",
    "credential_handling_performed": "M145_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_started": "M145_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_started": "M145_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_performed": "M145_EXECUTION_DENIED",
    "tool_execution_performed": "M145_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M145_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M145_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M145_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M145_NETWORK_ACCESS_DENIED",
    "mobile_sensor_performed": "M145_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M145_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M145_MODEL_CALL_DENIED",
    "memory_write_performed": "M145_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M145_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M145_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M145_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M145_DEPENDENCY_DENIED",
    "beta_release_enabled": "M145_BETA_RELEASE_DENIED",
    "production_authority_granted": "M145_PRODUCTION_AUTHORITY_DENIED",
}
