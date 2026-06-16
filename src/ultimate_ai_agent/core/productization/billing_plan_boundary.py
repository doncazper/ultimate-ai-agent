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


BILLING_PLAN_BOUNDARY_DOCS = [
    "docs/productization/BILLING_PLAN_BOUNDARY.md",
    "docs/productization/BILLING_PLAN_BOUNDARY_POLICY.md",
    "docs/productization/BILLING_PLAN_BOUNDARY_AUTHORITY_BOUNDARY.md",
    "docs/productization/BILLING_PLAN_BOUNDARY_RECEIPT_PLAN.md",
    "docs/productization/BILLING_PLAN_BOUNDARY_NON_GOALS.md",
    "docs/productization/M146_TO_M147_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M146_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 146)
)


class BillingPlanBoundaryStatus(str, Enum):
    boundary_recorded = "boundary_recorded"


class _BillingPlanBoundaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class BillingPlanBoundaryPolicy(_BillingPlanBoundaryModel):
    policy_ref: str = "billing-plan-boundary-policy:m146"
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    billing_boundary_only: bool = True
    disabled_by_default_required: bool = True
    m101_m145_coverage_required: bool = True
    billing_boundary_refs_required: bool = True
    plan_boundary_refs_required: bool = True
    entitlement_boundary_refs_required: bool = True
    pricing_disclosure_refs_required: bool = True
    payment_provider_boundary_refs_required: bool = True
    upgrade_downgrade_policy_refs_required: bool = True
    support_refund_policy_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_payment_processing_required: bool = True
    no_checkout_runtime_required: bool = True
    no_plan_enforcement_required: bool = True
    no_billing_runtime_required: bool = True
    no_account_plan_runtime_required: bool = True
    no_entitlement_runtime_required: bool = True
    no_auth_runtime_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    m147_future_only: bool = True
    payment_processing_enabled: bool = False
    checkout_runtime_enabled: bool = False
    subscription_management_enabled: bool = False
    plan_enforcement_enabled: bool = False
    billing_runtime_enabled: bool = False
    external_billing_provider_enabled: bool = False
    account_plan_runtime_enabled: bool = False
    entitlement_runtime_enabled: bool = False
    pricing_runtime_enabled: bool = False
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
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M146_SECRET_LIKE_BILLING_BOUNDARY_CONTENT_DENIED") from exc
        return self


class BillingPlanBoundaryRequest(_BillingPlanBoundaryModel):
    request_ref: str
    billing_boundary_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    billing_boundary_refs: list[str]
    plan_boundary_refs: list[str]
    entitlement_boundary_refs: list[str]
    pricing_disclosure_refs: list[str]
    payment_provider_boundary_refs: list[str]
    upgrade_downgrade_policy_refs: list[str]
    support_refund_policy_refs: list[str]
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
    billing_boundary_only: bool = True
    disabled_by_default_required: bool = True
    m101_m145_coverage_required: bool = True
    billing_boundary_refs_required: bool = True
    plan_boundary_refs_required: bool = True
    entitlement_boundary_refs_required: bool = True
    pricing_disclosure_refs_required: bool = True
    payment_provider_boundary_refs_required: bool = True
    upgrade_downgrade_policy_refs_required: bool = True
    support_refund_policy_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_payment_processing_required: bool = True
    no_checkout_runtime_required: bool = True
    no_plan_enforcement_required: bool = True
    no_billing_runtime_required: bool = True
    no_account_plan_runtime_required: bool = True
    no_entitlement_runtime_required: bool = True
    no_auth_runtime_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    payment_processing_requested: bool = False
    checkout_runtime_requested: bool = False
    subscription_management_requested: bool = False
    plan_enforcement_requested: bool = False
    billing_runtime_requested: bool = False
    external_billing_provider_requested: bool = False
    account_plan_runtime_requested: bool = False
    entitlement_runtime_requested: bool = False
    pricing_runtime_requested: bool = False
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
    def validate_shape(self):
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class BillingPlanBoundaryRecord(_BillingPlanBoundaryModel):
    record_ref: str
    billing_boundary_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    billing_boundary_refs: list[str]
    plan_boundary_refs: list[str]
    entitlement_boundary_refs: list[str]
    pricing_disclosure_refs: list[str]
    payment_provider_boundary_refs: list[str]
    upgrade_downgrade_policy_refs: list[str]
    support_refund_policy_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: BillingPlanBoundaryStatus = (
        BillingPlanBoundaryStatus.boundary_recorded
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    billing_boundary_only: bool = True
    disabled_by_default: bool = True
    m101_m145_covered: bool = True
    billing_boundaries_bound: bool = True
    plan_boundaries_bound: bool = True
    entitlement_boundaries_bound: bool = True
    pricing_disclosures_bound: bool = True
    payment_provider_boundaries_bound: bool = True
    upgrade_downgrade_policies_bound: bool = True
    support_refund_policies_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    no_effect_receipt_required: bool = True
    no_payment_processing: bool = True
    no_checkout_runtime: bool = True
    no_plan_enforcement: bool = True
    no_billing_runtime: bool = True
    no_account_plan_runtime: bool = True
    no_entitlement_runtime: bool = True
    no_auth_runtime: bool = True
    no_backend_route: bool = True
    no_control_center_control: bool = True
    no_dependency: bool = True
    no_production_authority: bool = True
    payment_processing_started: bool = False
    checkout_runtime_started: bool = False
    subscription_management_started: bool = False
    plan_enforcement_performed: bool = False
    billing_runtime_started: bool = False
    external_billing_provider_performed: bool = False
    account_plan_runtime_started: bool = False
    entitlement_runtime_started: bool = False
    pricing_runtime_performed: bool = False
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
    def validate_shape(self):
        for value, field_name in _record_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        if not self.reason_codes:
            raise ValueError("M146_REASON_CODE_REQUIRED")
        return self


def build_billing_plan_boundary_record(
    request: BillingPlanBoundaryRequest,
    policy: BillingPlanBoundaryPolicy | None = None,
) -> BillingPlanBoundaryRecord:
    active_policy = validate_billing_plan_boundary_policy(
        policy or BillingPlanBoundaryPolicy()
    )
    validated_request = validate_billing_plan_boundary_request(request)
    record = BillingPlanBoundaryRecord(
        record_ref=f"billing-plan-boundary-record:{_ref_suffix(validated_request.billing_boundary_ref)}",
        billing_boundary_ref=validated_request.billing_boundary_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        billing_boundary_refs=list(
            validated_request.billing_boundary_refs
        ),
        plan_boundary_refs=list(validated_request.plan_boundary_refs),
        entitlement_boundary_refs=list(validated_request.entitlement_boundary_refs),
        pricing_disclosure_refs=list(validated_request.pricing_disclosure_refs),
        payment_provider_boundary_refs=list(
            validated_request.payment_provider_boundary_refs
        ),
        upgrade_downgrade_policy_refs=list(
            validated_request.upgrade_downgrade_policy_refs
        ),
        support_refund_policy_refs=list(validated_request.support_refund_policy_refs),
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
        billing_boundary_only=active_policy.billing_boundary_only,
        disabled_by_default=active_policy.disabled_by_default_required,
        m101_m145_covered=active_policy.m101_m145_coverage_required,
        billing_boundaries_bound=(
            active_policy.billing_boundary_refs_required
        ),
        plan_boundaries_bound=active_policy.plan_boundary_refs_required,
        entitlement_boundaries_bound=active_policy.entitlement_boundary_refs_required,
        pricing_disclosures_bound=active_policy.pricing_disclosure_refs_required,
        payment_provider_boundaries_bound=(
            active_policy.payment_provider_boundary_refs_required
        ),
        upgrade_downgrade_policies_bound=(
            active_policy.upgrade_downgrade_policy_refs_required
        ),
        support_refund_policies_bound=active_policy.support_refund_policy_refs_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_payment_processing=active_policy.no_payment_processing_required,
        no_checkout_runtime=active_policy.no_checkout_runtime_required,
        no_plan_enforcement=active_policy.no_plan_enforcement_required,
        no_billing_runtime=active_policy.no_billing_runtime_required,
        no_account_plan_runtime=(
            active_policy.no_account_plan_runtime_required
        ),
        no_entitlement_runtime=active_policy.no_entitlement_runtime_required,
        no_auth_runtime=active_policy.no_auth_runtime_required,
        no_backend_route=active_policy.no_backend_route_required,
        no_control_center_control=active_policy.no_control_center_control_required,
        no_dependency=active_policy.no_dependency_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M146_BILLING_PLAN_BOUNDARY_REVIEW_ONLY",
            "M146_M101_M145_COVERED",
            "M146_DISABLED_BY_DEFAULT",
            "M146_NO_PAYMENT_PROCESSING",
            "M146_NO_CHECKOUT_RUNTIME",
            "M146_NO_PLAN_ENFORCEMENT",
            "M146_NO_BILLING_RUNTIME",
            "M146_NO_ACCOUNT_PLAN_RUNTIME",
            "M146_NO_AUTH_RUNTIME",
            "M146_NO_BACKEND_ROUTE",
            "M146_NO_PRODUCTION_AUTHORITY",
            "M147_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M146 records contract-only billing/plan boundary refs using "
            "safe billing boundary, plan boundary, entitlement boundary, "
            "pricing disclosure, payment provider boundary, upgrade downgrade "
            "policy, support refund policy, audit, replay, revocation, "
            "kill-switch, and no-effect receipt refs. It grants no payment "
            "processing, checkout runtime, plan enforcement, "
            "billing runtime, account plan runtime, auth runtime, backend "
            "route, Control Center control, dependency, beta release, or "
            "production authority."
        ),
    )
    return validate_billing_plan_boundary_record(record)


def validate_billing_plan_boundary_policy(
    policy: BillingPlanBoundaryPolicy,
) -> BillingPlanBoundaryPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, BillingPlanBoundaryPolicy):
        raise ValueError("M146_SECRET_LIKE_BILLING_BOUNDARY_CONTENT_DENIED")
    validated = BillingPlanBoundaryPolicy.model_validate(payload)
    for field_name, reason in _M146_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M146_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M146_SECRET_LIKE_BILLING_BOUNDARY_CONTENT_DENIED") from exc
    return validated


def validate_billing_plan_boundary_request(
    request: BillingPlanBoundaryRequest,
) -> BillingPlanBoundaryRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, BillingPlanBoundaryRequest):
        raise ValueError("M146_SECRET_LIKE_BILLING_BOUNDARY_CONTENT_DENIED")
    _deny_enabled(_M146_REQUEST_DENIALS, payload)
    validated = BillingPlanBoundaryRequest.model_validate(payload)
    for field_name, reason in _M146_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M146_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M146_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _request_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M146_SECRET_LIKE_BILLING_BOUNDARY_CONTENT_DENIED") from exc
    return validated


def validate_billing_plan_boundary_record(
    record: BillingPlanBoundaryRecord,
) -> BillingPlanBoundaryRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, BillingPlanBoundaryRecord):
        raise ValueError("M146_SECRET_LIKE_BILLING_BOUNDARY_CONTENT_DENIED")
    _deny_enabled(_M146_RECORD_DENIALS, payload)
    validated = BillingPlanBoundaryRecord.model_validate(payload)
    for field_name, reason in _M146_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M146_RECORD_DENIALS, _model_payload(validated))
    if validated.status != BillingPlanBoundaryStatus.boundary_recorded:
        raise ValueError("M146_BOUNDARY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M146_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _record_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    if "M146_BILLING_PLAN_BOUNDARY_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M146_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M146_SECRET_LIKE_BILLING_BOUNDARY_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: BillingPlanBoundaryRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.billing_boundary_ref, "billing_boundary_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: BillingPlanBoundaryRecord):
    return [
        (record.record_ref, "record_ref"),
        (record.billing_boundary_ref, "billing_boundary_ref"),
        (record.request_ref, "request_ref"),
        (record.baseline_ref, "baseline_ref"),
        (record.actor_ref, "actor_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _request_ref_lists(request: BillingPlanBoundaryRequest):
    return [
        (
            request.billing_boundary_refs,
            "billing_boundary_ref",
            "M146_BILLING_BOUNDARY_REF_REQUIRED",
        ),
        (
            request.plan_boundary_refs,
            "plan_boundary_ref",
            "M146_PLAN_BOUNDARY_REF_REQUIRED",
        ),
        (
            request.entitlement_boundary_refs,
            "entitlement_boundary_ref",
            "M146_ENTITLEMENT_BOUNDARY_REF_REQUIRED",
        ),
        (
            request.pricing_disclosure_refs,
            "pricing_disclosure_ref",
            "M146_PRICING_DISCLOSURE_REF_REQUIRED",
        ),
        (
            request.payment_provider_boundary_refs,
            "payment_provider_boundary_ref",
            "M146_PAYMENT_PROVIDER_BOUNDARY_REF_REQUIRED",
        ),
        (
            request.upgrade_downgrade_policy_refs,
            "upgrade_downgrade_policy_ref",
            "M146_UPGRADE_DOWNGRADE_POLICY_REF_REQUIRED",
        ),
        (
            request.support_refund_policy_refs,
            "support_refund_policy_ref",
            "M146_SUPPORT_REFUND_POLICY_REF_REQUIRED",
        ),
    ]


def _record_ref_lists(record: BillingPlanBoundaryRecord):
    return [
        (
            record.billing_boundary_refs,
            "billing_boundary_ref",
            "M146_BILLING_BOUNDARY_REF_REQUIRED",
        ),
        (
            record.plan_boundary_refs,
            "plan_boundary_ref",
            "M146_PLAN_BOUNDARY_REF_REQUIRED",
        ),
        (
            record.entitlement_boundary_refs,
            "entitlement_boundary_ref",
            "M146_ENTITLEMENT_BOUNDARY_REF_REQUIRED",
        ),
        (
            record.pricing_disclosure_refs,
            "pricing_disclosure_ref",
            "M146_PRICING_DISCLOSURE_REF_REQUIRED",
        ),
        (
            record.payment_provider_boundary_refs,
            "payment_provider_boundary_ref",
            "M146_PAYMENT_PROVIDER_BOUNDARY_REF_REQUIRED",
        ),
        (
            record.upgrade_downgrade_policy_refs,
            "upgrade_downgrade_policy_ref",
            "M146_UPGRADE_DOWNGRADE_POLICY_REF_REQUIRED",
        ),
        (
            record.support_refund_policy_refs,
            "support_refund_policy_ref",
            "M146_SUPPORT_REFUND_POLICY_REF_REQUIRED",
        ),
    ]


def _validate_accepted_checkpoints(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M146_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M146_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M146_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M146_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M146_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M146_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M146_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M146_REQUIRED_TRUE = [
    ("contract_only", "M146_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M146_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M146_DETERMINISTIC_REQUIRED"),
    ("local_only", "M146_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M146_SAFE_REFS_ONLY_REQUIRED"),
    ("billing_boundary_only", "M146_BILLING_BOUNDARY_ONLY_REQUIRED"),
    ("disabled_by_default_required", "M146_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m145_coverage_required", "M146_M101_M145_COVERAGE_REQUIRED"),
    (
        "billing_boundary_refs_required",
        "M146_BILLING_BOUNDARY_REF_REQUIRED",
    ),
    ("plan_boundary_refs_required", "M146_PLAN_BOUNDARY_REF_REQUIRED"),
    ("entitlement_boundary_refs_required", "M146_ENTITLEMENT_BOUNDARY_REF_REQUIRED"),
    ("pricing_disclosure_refs_required", "M146_PRICING_DISCLOSURE_REF_REQUIRED"),
    (
        "payment_provider_boundary_refs_required",
        "M146_PAYMENT_PROVIDER_BOUNDARY_REF_REQUIRED",
    ),
    (
        "upgrade_downgrade_policy_refs_required",
        "M146_UPGRADE_DOWNGRADE_POLICY_REF_REQUIRED",
    ),
    ("support_refund_policy_refs_required", "M146_SUPPORT_REFUND_POLICY_REF_REQUIRED"),
    ("audit_replay_required", "M146_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M146_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M146_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_payment_processing_required", "M146_PAYMENT_PROCESSING_DENIED"),
    ("no_checkout_runtime_required", "M146_CHECKOUT_RUNTIME_DENIED"),
    ("no_plan_enforcement_required", "M146_PLAN_ENFORCEMENT_DENIED"),
    ("no_billing_runtime_required", "M146_BILLING_RUNTIME_DENIED"),
    ("no_account_plan_runtime_required", "M146_ACCOUNT_PLAN_RUNTIME_DENIED"),
    ("no_entitlement_runtime_required", "M146_ENTITLEMENT_RUNTIME_DENIED"),
    ("no_auth_runtime_required", "M146_AUTH_RUNTIME_DENIED"),
    ("no_backend_route_required", "M146_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control_required", "M146_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency_required", "M146_DEPENDENCY_DENIED"),
    ("no_production_authority_required", "M146_PRODUCTION_AUTHORITY_DENIED"),
]

_M146_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M146_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M146_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M146_DETERMINISTIC_REQUIRED"),
    ("local_only", "M146_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M146_SAFE_REFS_ONLY_REQUIRED"),
    ("billing_boundary_only", "M146_BILLING_BOUNDARY_ONLY_REQUIRED"),
    ("disabled_by_default", "M146_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m145_covered", "M146_M101_M145_COVERAGE_REQUIRED"),
    ("billing_boundaries_bound", "M146_BILLING_BOUNDARY_REF_REQUIRED"),
    ("plan_boundaries_bound", "M146_PLAN_BOUNDARY_REF_REQUIRED"),
    ("entitlement_boundaries_bound", "M146_ENTITLEMENT_BOUNDARY_REF_REQUIRED"),
    ("pricing_disclosures_bound", "M146_PRICING_DISCLOSURE_REF_REQUIRED"),
    ("payment_provider_boundaries_bound", "M146_PAYMENT_PROVIDER_BOUNDARY_REF_REQUIRED"),
    ("upgrade_downgrade_policies_bound", "M146_UPGRADE_DOWNGRADE_POLICY_REF_REQUIRED"),
    ("support_refund_policies_bound", "M146_SUPPORT_REFUND_POLICY_REF_REQUIRED"),
    ("audit_replay_bound", "M146_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M146_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M146_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_payment_processing", "M146_PAYMENT_PROCESSING_DENIED"),
    ("no_checkout_runtime", "M146_CHECKOUT_RUNTIME_DENIED"),
    ("no_plan_enforcement", "M146_PLAN_ENFORCEMENT_DENIED"),
    ("no_billing_runtime", "M146_BILLING_RUNTIME_DENIED"),
    ("no_account_plan_runtime", "M146_ACCOUNT_PLAN_RUNTIME_DENIED"),
    ("no_entitlement_runtime", "M146_ENTITLEMENT_RUNTIME_DENIED"),
    ("no_auth_runtime", "M146_AUTH_RUNTIME_DENIED"),
    ("no_backend_route", "M146_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control", "M146_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency", "M146_DEPENDENCY_DENIED"),
    ("no_production_authority", "M146_PRODUCTION_AUTHORITY_DENIED"),
]

_M146_POLICY_DENIALS = {
    "payment_processing_enabled": "M146_PAYMENT_PROCESSING_DENIED",
    "checkout_runtime_enabled": "M146_CHECKOUT_RUNTIME_DENIED",
    "subscription_management_enabled": "M146_SUBSCRIPTION_MANAGEMENT_DENIED",
    "plan_enforcement_enabled": "M146_PLAN_ENFORCEMENT_DENIED",
    "billing_runtime_enabled": "M146_BILLING_RUNTIME_DENIED",
    "external_billing_provider_enabled": "M146_EXTERNAL_BILLING_PROVIDER_DENIED",
    "account_plan_runtime_enabled": "M146_ACCOUNT_PLAN_RUNTIME_DENIED",
    "entitlement_runtime_enabled": "M146_ENTITLEMENT_RUNTIME_DENIED",
    "pricing_runtime_enabled": "M146_PRICING_RUNTIME_DENIED",
    "auth_runtime_enabled": "M146_AUTH_RUNTIME_DENIED",
    "login_enabled": "M146_LOGIN_DENIED",
    "session_cookie_enabled": "M146_SESSION_COOKIE_DENIED",
    "credential_handling_enabled": "M146_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_enabled": "M146_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_enabled": "M146_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_enabled": "M146_EXECUTION_DENIED",
    "tool_execution_enabled": "M146_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M146_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M146_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M146_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M146_NETWORK_ACCESS_DENIED",
    "mobile_sensor_enabled": "M146_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M146_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M146_MODEL_CALL_DENIED",
    "memory_write_enabled": "M146_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M146_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M146_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M146_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M146_DEPENDENCY_DENIED",
    "beta_release_enabled": "M146_BETA_RELEASE_DENIED",
    "production_authority_granted": "M146_PRODUCTION_AUTHORITY_DENIED",
}

_M146_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M146_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "payment_processing_requested": "M146_PAYMENT_PROCESSING_DENIED",
    "checkout_runtime_requested": "M146_CHECKOUT_RUNTIME_DENIED",
    "subscription_management_requested": "M146_SUBSCRIPTION_MANAGEMENT_DENIED",
    "plan_enforcement_requested": "M146_PLAN_ENFORCEMENT_DENIED",
    "billing_runtime_requested": "M146_BILLING_RUNTIME_DENIED",
    "external_billing_provider_requested": "M146_EXTERNAL_BILLING_PROVIDER_DENIED",
    "account_plan_runtime_requested": "M146_ACCOUNT_PLAN_RUNTIME_DENIED",
    "entitlement_runtime_requested": "M146_ENTITLEMENT_RUNTIME_DENIED",
    "pricing_runtime_requested": "M146_PRICING_RUNTIME_DENIED",
    "auth_runtime_requested": "M146_AUTH_RUNTIME_DENIED",
    "login_requested": "M146_LOGIN_DENIED",
    "session_cookie_requested": "M146_SESSION_COOKIE_DENIED",
    "credential_handling_requested": "M146_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_requested": "M146_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_requested": "M146_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "production_authority_requested": "M146_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_private_content": "M146_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_prompt": "M146_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M146_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M146_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M146_SECRET_DENIED",
    "dependency_requested": "M146_DEPENDENCY_DENIED",
}

_M146_RECORD_DENIALS = {
    "payment_processing_started": "M146_PAYMENT_PROCESSING_DENIED",
    "checkout_runtime_started": "M146_CHECKOUT_RUNTIME_DENIED",
    "subscription_management_started": "M146_SUBSCRIPTION_MANAGEMENT_DENIED",
    "plan_enforcement_performed": "M146_PLAN_ENFORCEMENT_DENIED",
    "billing_runtime_started": "M146_BILLING_RUNTIME_DENIED",
    "external_billing_provider_performed": "M146_EXTERNAL_BILLING_PROVIDER_DENIED",
    "account_plan_runtime_started": "M146_ACCOUNT_PLAN_RUNTIME_DENIED",
    "entitlement_runtime_started": "M146_ENTITLEMENT_RUNTIME_DENIED",
    "pricing_runtime_performed": "M146_PRICING_RUNTIME_DENIED",
    "auth_runtime_started": "M146_AUTH_RUNTIME_DENIED",
    "login_enabled": "M146_LOGIN_DENIED",
    "session_cookie_enabled": "M146_SESSION_COOKIE_DENIED",
    "credential_handling_performed": "M146_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_started": "M146_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_started": "M146_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_performed": "M146_EXECUTION_DENIED",
    "tool_execution_performed": "M146_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M146_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M146_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M146_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M146_NETWORK_ACCESS_DENIED",
    "mobile_sensor_performed": "M146_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M146_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M146_MODEL_CALL_DENIED",
    "memory_write_performed": "M146_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M146_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M146_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M146_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M146_DEPENDENCY_DENIED",
    "beta_release_enabled": "M146_BETA_RELEASE_DENIED",
    "production_authority_granted": "M146_PRODUCTION_AUTHORITY_DENIED",
}
