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


MULTI_USER_PRODUCT_BOUNDARY_DOCS = [
    "docs/productization/MULTI_USER_PRODUCT_BOUNDARY.md",
    "docs/productization/MULTI_USER_PRODUCT_BOUNDARY_POLICY.md",
    "docs/productization/MULTI_USER_PRODUCT_BOUNDARY_AUTHORITY_BOUNDARY.md",
    "docs/productization/MULTI_USER_PRODUCT_BOUNDARY_RECEIPT_PLAN.md",
    "docs/productization/MULTI_USER_PRODUCT_BOUNDARY_NON_GOALS.md",
    "docs/productization/M141_TO_M142_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 141)
)


class MultiUserProductBoundaryStatus(str, Enum):
    product_boundary_review = "product_boundary_review"


class _MultiUserProductBoundaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class MultiUserProductBoundaryPolicy(_MultiUserProductBoundaryModel):
    policy_ref: str = "multi-user-product-boundary-policy:m141"
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    product_boundary_only: bool = True
    m101_m140_coverage_required: bool = True
    actor_boundary_required: bool = True
    workspace_boundary_required: bool = True
    tenant_boundary_required: bool = True
    role_boundary_required: bool = True
    privacy_boundary_required: bool = True
    audit_replay_required: bool = True
    revocation_readiness_required: bool = True
    no_effect_receipt_required: bool = True
    no_multi_user_runtime_required: bool = True
    no_account_tenancy_required: bool = True
    no_auth_runtime_required: bool = True
    no_workspace_sharing_required: bool = True
    no_production_authority_required: bool = True
    m142_future_only: bool = True
    multi_user_runtime_enabled: bool = False
    account_tenancy_enabled: bool = False
    tenant_runtime_enabled: bool = False
    workspace_sharing_enabled: bool = False
    identity_federation_enabled: bool = False
    org_admin_runtime_enabled: bool = False
    cross_workspace_access_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_enabled: bool = False
    persistent_identity_store_enabled: bool = False
    account_connector_enabled: bool = False
    production_runtime_enabled: bool = False
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
    alpha_privacy_review_enabled: bool = False
    alpha_release_enabled: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M141_SECRET_LIKE_PRODUCT_BOUNDARY_CONTENT_DENIED") from exc
        return self


class MultiUserProductBoundaryRequest(_MultiUserProductBoundaryModel):
    request_ref: str
    product_boundary_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    user_boundary_refs: list[str]
    workspace_boundary_refs: list[str]
    tenant_boundary_refs: list[str]
    role_boundary_refs: list[str]
    privacy_boundary_refs: list[str]
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
    product_boundary_only: bool = True
    m101_m140_coverage_required: bool = True
    actor_boundary_required: bool = True
    workspace_boundary_required: bool = True
    tenant_boundary_required: bool = True
    role_boundary_required: bool = True
    privacy_boundary_required: bool = True
    audit_replay_required: bool = True
    revocation_readiness_required: bool = True
    no_effect_receipt_required: bool = True
    no_multi_user_runtime_required: bool = True
    no_account_tenancy_required: bool = True
    no_auth_runtime_required: bool = True
    no_workspace_sharing_required: bool = True
    no_production_authority_required: bool = True
    multi_user_runtime_requested: bool = False
    account_tenancy_requested: bool = False
    tenant_runtime_requested: bool = False
    workspace_sharing_requested: bool = False
    identity_federation_requested: bool = False
    org_admin_runtime_requested: bool = False
    cross_workspace_access_requested: bool = False
    auth_runtime_requested: bool = False
    login_requested: bool = False
    session_cookie_requested: bool = False
    credential_handling_requested: bool = False
    persistent_identity_store_requested: bool = False
    account_connector_requested: bool = False
    production_runtime_requested: bool = False
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
    alpha_privacy_review_requested: bool = False
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
    def validate_shape(self):
        for value, field_name in _request_ref_pairs(self):
            _validate_m61_ref(value, field_name)
        _validate_safe_payload(self.safe_summary)
        return self


class MultiUserProductBoundaryRecord(_MultiUserProductBoundaryModel):
    record_ref: str
    product_boundary_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    user_boundary_refs: list[str]
    workspace_boundary_refs: list[str]
    tenant_boundary_refs: list[str]
    role_boundary_refs: list[str]
    privacy_boundary_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: MultiUserProductBoundaryStatus = (
        MultiUserProductBoundaryStatus.product_boundary_review
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    product_boundary_only: bool = True
    m101_m140_covered: bool = True
    actor_boundary_bound: bool = True
    workspace_boundary_bound: bool = True
    tenant_boundary_bound: bool = True
    role_boundary_bound: bool = True
    privacy_boundary_bound: bool = True
    audit_replay_bound: bool = True
    revocation_readiness_bound: bool = True
    no_effect_receipt_required: bool = True
    no_multi_user_runtime: bool = True
    no_account_tenancy: bool = True
    no_auth_runtime: bool = True
    no_workspace_sharing: bool = True
    no_production_authority: bool = True
    multi_user_runtime_started: bool = False
    account_tenancy_enabled: bool = False
    tenant_runtime_started: bool = False
    workspace_sharing_enabled: bool = False
    identity_federation_enabled: bool = False
    org_admin_runtime_started: bool = False
    cross_workspace_access_enabled: bool = False
    auth_runtime_started: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_performed: bool = False
    persistent_identity_store_enabled: bool = False
    account_connector_enabled: bool = False
    production_runtime_enabled: bool = False
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
    alpha_privacy_review_enabled: bool = False
    alpha_release_enabled: bool = False
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
            raise ValueError("M141_REASON_CODE_REQUIRED")
        return self


def build_multi_user_product_boundary_record(
    request: MultiUserProductBoundaryRequest,
    policy: MultiUserProductBoundaryPolicy | None = None,
) -> MultiUserProductBoundaryRecord:
    active_policy = validate_multi_user_product_boundary_policy(
        policy or MultiUserProductBoundaryPolicy()
    )
    validated_request = validate_multi_user_product_boundary_request(request)
    record = MultiUserProductBoundaryRecord(
        record_ref=(
            "multi-user-product-boundary-record:"
            f"{_ref_suffix(validated_request.product_boundary_ref)}"
        ),
        product_boundary_ref=validated_request.product_boundary_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        user_boundary_refs=list(validated_request.user_boundary_refs),
        workspace_boundary_refs=list(validated_request.workspace_boundary_refs),
        tenant_boundary_refs=list(validated_request.tenant_boundary_refs),
        role_boundary_refs=list(validated_request.role_boundary_refs),
        privacy_boundary_refs=list(validated_request.privacy_boundary_refs),
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
        product_boundary_only=active_policy.product_boundary_only,
        m101_m140_covered=active_policy.m101_m140_coverage_required,
        actor_boundary_bound=active_policy.actor_boundary_required,
        workspace_boundary_bound=active_policy.workspace_boundary_required,
        tenant_boundary_bound=active_policy.tenant_boundary_required,
        role_boundary_bound=active_policy.role_boundary_required,
        privacy_boundary_bound=active_policy.privacy_boundary_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_readiness_bound=active_policy.revocation_readiness_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_multi_user_runtime=active_policy.no_multi_user_runtime_required,
        no_account_tenancy=active_policy.no_account_tenancy_required,
        no_auth_runtime=active_policy.no_auth_runtime_required,
        no_workspace_sharing=active_policy.no_workspace_sharing_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M141_MULTI_USER_PRODUCT_BOUNDARY_REVIEW_ONLY",
            "M141_M101_M140_COVERED",
            "M141_NO_MULTI_USER_RUNTIME",
            "M141_NO_ACCOUNT_TENANCY",
            "M141_NO_AUTH_OR_IDENTITY_FEDERATION",
            "M141_NO_WORKSPACE_SHARING",
            "M141_NO_PRODUCTION_AUTHORITY",
            "M142_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M141 records a contract-only multi-user product boundary using "
            "safe user, workspace, tenant, role, privacy, audit, replay, "
            "revocation, kill-switch, and no-effect receipt refs. It grants no "
            "multi-user runtime, account tenancy, tenant runtime, workspace "
            "sharing, identity federation, auth runtime, login, session material, "
            "private auth material handling, persistent identity store, connector action, "
            "network access, execution, model call, memory write, context "
            "injection, backend route, Control Center control, dependency, "
            "alpha privacy review, beta release, or production authority."
        ),
    )
    return validate_multi_user_product_boundary_record(record)


def validate_multi_user_product_boundary_policy(
    policy: MultiUserProductBoundaryPolicy,
) -> MultiUserProductBoundaryPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, MultiUserProductBoundaryPolicy):
        raise ValueError("M141_SECRET_LIKE_PRODUCT_BOUNDARY_CONTENT_DENIED")
    validated = MultiUserProductBoundaryPolicy.model_validate(payload)
    for field_name, reason in _M141_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M141_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M141_SECRET_LIKE_PRODUCT_BOUNDARY_CONTENT_DENIED") from exc
    return validated


def validate_multi_user_product_boundary_request(
    request: MultiUserProductBoundaryRequest,
) -> MultiUserProductBoundaryRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, MultiUserProductBoundaryRequest):
        raise ValueError("M141_SECRET_LIKE_PRODUCT_BOUNDARY_CONTENT_DENIED")
    _deny_enabled(_M141_REQUEST_DENIALS, payload)
    validated = MultiUserProductBoundaryRequest.model_validate(payload)
    for field_name, reason in _M141_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M141_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M141_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    _validate_ref_list(
        validated.user_boundary_refs,
        "user_boundary_ref",
        "M141_USER_BOUNDARY_REF_REQUIRED",
    )
    _validate_ref_list(
        validated.workspace_boundary_refs,
        "workspace_boundary_ref",
        "M141_WORKSPACE_BOUNDARY_REF_REQUIRED",
    )
    _validate_ref_list(
        validated.tenant_boundary_refs,
        "tenant_boundary_ref",
        "M141_TENANT_BOUNDARY_REF_REQUIRED",
    )
    _validate_ref_list(
        validated.role_boundary_refs,
        "role_boundary_ref",
        "M141_ROLE_BOUNDARY_REF_REQUIRED",
    )
    _validate_ref_list(
        validated.privacy_boundary_refs,
        "privacy_boundary_ref",
        "M141_PRIVACY_BOUNDARY_REF_REQUIRED",
    )
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M141_SECRET_LIKE_PRODUCT_BOUNDARY_CONTENT_DENIED") from exc
    return validated


def validate_multi_user_product_boundary_record(
    record: MultiUserProductBoundaryRecord,
) -> MultiUserProductBoundaryRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, MultiUserProductBoundaryRecord):
        raise ValueError("M141_SECRET_LIKE_PRODUCT_BOUNDARY_CONTENT_DENIED")
    _deny_enabled(_M141_RECORD_DENIALS, payload)
    validated = MultiUserProductBoundaryRecord.model_validate(payload)
    for field_name, reason in _M141_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M141_RECORD_DENIALS, _model_payload(validated))
    if validated.status != MultiUserProductBoundaryStatus.product_boundary_review:
        raise ValueError("M141_PRODUCT_BOUNDARY_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M141_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in [
        (validated.user_boundary_refs, "user_boundary_ref", "M141_USER_BOUNDARY_REF_REQUIRED"),
        (
            validated.workspace_boundary_refs,
            "workspace_boundary_ref",
            "M141_WORKSPACE_BOUNDARY_REF_REQUIRED",
        ),
        (
            validated.tenant_boundary_refs,
            "tenant_boundary_ref",
            "M141_TENANT_BOUNDARY_REF_REQUIRED",
        ),
        (validated.role_boundary_refs, "role_boundary_ref", "M141_ROLE_BOUNDARY_REF_REQUIRED"),
        (
            validated.privacy_boundary_refs,
            "privacy_boundary_ref",
            "M141_PRIVACY_BOUNDARY_REF_REQUIRED",
        ),
    ]:
        _validate_ref_list(values, field_name, reason)
    if "M141_MULTI_USER_PRODUCT_BOUNDARY_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M141_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M141_SECRET_LIKE_PRODUCT_BOUNDARY_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: MultiUserProductBoundaryRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.product_boundary_ref, "product_boundary_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: MultiUserProductBoundaryRecord):
    return [
        (record.record_ref, "record_ref"),
        (record.product_boundary_ref, "product_boundary_ref"),
        (record.request_ref, "request_ref"),
        (record.baseline_ref, "baseline_ref"),
        (record.actor_ref, "actor_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _validate_accepted_checkpoints(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M141_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M141_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M141_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M141_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M141_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M141_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M141_REQUIRED_TRUE = [
    ("contract_only", "M141_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M141_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M141_DETERMINISTIC_REQUIRED"),
    ("local_only", "M141_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M141_SAFE_REFS_ONLY_REQUIRED"),
    ("product_boundary_only", "M141_PRODUCT_BOUNDARY_ONLY_REQUIRED"),
    ("m101_m140_coverage_required", "M141_M101_M140_COVERAGE_REQUIRED"),
    ("actor_boundary_required", "M141_ACTOR_BOUNDARY_REQUIRED"),
    ("workspace_boundary_required", "M141_WORKSPACE_BOUNDARY_REQUIRED"),
    ("tenant_boundary_required", "M141_TENANT_BOUNDARY_REQUIRED"),
    ("role_boundary_required", "M141_ROLE_BOUNDARY_REQUIRED"),
    ("privacy_boundary_required", "M141_PRIVACY_BOUNDARY_REQUIRED"),
    ("audit_replay_required", "M141_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_required", "M141_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M141_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_multi_user_runtime_required", "M141_MULTI_USER_RUNTIME_DENIED"),
    ("no_account_tenancy_required", "M141_ACCOUNT_TENANCY_DENIED"),
    ("no_auth_runtime_required", "M141_AUTH_RUNTIME_DENIED"),
    ("no_workspace_sharing_required", "M141_WORKSPACE_SHARING_DENIED"),
    ("no_production_authority_required", "M141_PRODUCTION_AUTHORITY_DENIED"),
]

_M141_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M141_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M141_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M141_DETERMINISTIC_REQUIRED"),
    ("local_only", "M141_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M141_SAFE_REFS_ONLY_REQUIRED"),
    ("product_boundary_only", "M141_PRODUCT_BOUNDARY_ONLY_REQUIRED"),
    ("m101_m140_covered", "M141_M101_M140_COVERAGE_REQUIRED"),
    ("actor_boundary_bound", "M141_ACTOR_BOUNDARY_REQUIRED"),
    ("workspace_boundary_bound", "M141_WORKSPACE_BOUNDARY_REQUIRED"),
    ("tenant_boundary_bound", "M141_TENANT_BOUNDARY_REQUIRED"),
    ("role_boundary_bound", "M141_ROLE_BOUNDARY_REQUIRED"),
    ("privacy_boundary_bound", "M141_PRIVACY_BOUNDARY_REQUIRED"),
    ("audit_replay_bound", "M141_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_bound", "M141_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M141_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_multi_user_runtime", "M141_MULTI_USER_RUNTIME_DENIED"),
    ("no_account_tenancy", "M141_ACCOUNT_TENANCY_DENIED"),
    ("no_auth_runtime", "M141_AUTH_RUNTIME_DENIED"),
    ("no_workspace_sharing", "M141_WORKSPACE_SHARING_DENIED"),
    ("no_production_authority", "M141_PRODUCTION_AUTHORITY_DENIED"),
]

_M141_POLICY_DENIALS = {
    "multi_user_runtime_enabled": "M141_MULTI_USER_RUNTIME_DENIED",
    "account_tenancy_enabled": "M141_ACCOUNT_TENANCY_DENIED",
    "tenant_runtime_enabled": "M141_TENANT_RUNTIME_DENIED",
    "workspace_sharing_enabled": "M141_WORKSPACE_SHARING_DENIED",
    "identity_federation_enabled": "M141_IDENTITY_FEDERATION_DENIED",
    "org_admin_runtime_enabled": "M141_ORG_ADMIN_RUNTIME_DENIED",
    "cross_workspace_access_enabled": "M141_CROSS_WORKSPACE_ACCESS_DENIED",
    "auth_runtime_enabled": "M141_AUTH_RUNTIME_DENIED",
    "login_enabled": "M141_LOGIN_DENIED",
    "session_cookie_enabled": "M141_SESSION_COOKIE_DENIED",
    "credential_handling_enabled": "M141_CREDENTIAL_HANDLING_DENIED",
    "persistent_identity_store_enabled": "M141_PERSISTENT_IDENTITY_STORE_DENIED",
    "account_connector_enabled": "M141_ACCOUNT_CONNECTOR_DENIED",
    "production_runtime_enabled": "M141_PRODUCTION_RUNTIME_DENIED",
    "execution_enabled": "M141_EXECUTION_DENIED",
    "tool_execution_enabled": "M141_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M141_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M141_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M141_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M141_NETWORK_ACCESS_DENIED",
    "plugin_execution_enabled": "M141_PLUGIN_EXECUTION_DENIED",
    "background_worker_enabled": "M141_BACKGROUND_WORKER_DENIED",
    "scheduler_enabled": "M141_SCHEDULER_DENIED",
    "mobile_sensor_enabled": "M141_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M141_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M141_MODEL_CALL_DENIED",
    "memory_write_enabled": "M141_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M141_CONTEXT_INJECTION_DENIED",
    "raw_prompt_payload_exposure_enabled": "M141_RAW_PROMPT_PAYLOAD_DENIED",
    "credential_cookie_access_enabled": "M141_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "backend_route_enabled": "M141_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M141_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M141_DEPENDENCY_DENIED",
    "alpha_privacy_review_enabled": "M141_ALPHA_PRIVACY_REVIEW_DENIED",
    "alpha_release_enabled": "M141_ALPHA_RELEASE_DENIED",
    "beta_release_enabled": "M141_BETA_RELEASE_DENIED",
    "production_authority_granted": "M141_PRODUCTION_AUTHORITY_DENIED",
}

_M141_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M141_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "multi_user_runtime_requested": "M141_MULTI_USER_RUNTIME_DENIED",
    "account_tenancy_requested": "M141_ACCOUNT_TENANCY_DENIED",
    "tenant_runtime_requested": "M141_TENANT_RUNTIME_DENIED",
    "workspace_sharing_requested": "M141_WORKSPACE_SHARING_DENIED",
    "identity_federation_requested": "M141_IDENTITY_FEDERATION_DENIED",
    "org_admin_runtime_requested": "M141_ORG_ADMIN_RUNTIME_DENIED",
    "cross_workspace_access_requested": "M141_CROSS_WORKSPACE_ACCESS_DENIED",
    "auth_runtime_requested": "M141_AUTH_RUNTIME_DENIED",
    "login_requested": "M141_LOGIN_DENIED",
    "session_cookie_requested": "M141_SESSION_COOKIE_DENIED",
    "credential_handling_requested": "M141_CREDENTIAL_HANDLING_DENIED",
    "persistent_identity_store_requested": "M141_PERSISTENT_IDENTITY_STORE_DENIED",
    "account_connector_requested": "M141_ACCOUNT_CONNECTOR_DENIED",
    "production_runtime_requested": "M141_PRODUCTION_RUNTIME_DENIED",
    "execution_requested": "M141_EXECUTION_DENIED",
    "tool_execution_requested": "M141_TOOL_EXECUTION_DENIED",
    "shell_execution_requested": "M141_SHELL_EXECUTION_DENIED",
    "browser_action_requested": "M141_BROWSER_ACTION_DENIED",
    "connector_action_requested": "M141_CONNECTOR_ACTION_DENIED",
    "network_access_requested": "M141_NETWORK_ACCESS_DENIED",
    "plugin_execution_requested": "M141_PLUGIN_EXECUTION_DENIED",
    "dependency_requested": "M141_DEPENDENCY_DENIED",
    "alpha_privacy_review_requested": "M141_ALPHA_PRIVACY_REVIEW_DENIED",
    "alpha_release_requested": "M141_ALPHA_RELEASE_DENIED",
    "beta_release_requested": "M141_BETA_RELEASE_DENIED",
    "production_authority_requested": "M141_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_prompt": "M141_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M141_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M141_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M141_SECRET_DENIED",
}

_M141_RECORD_DENIALS = {
    "multi_user_runtime_started": "M141_MULTI_USER_RUNTIME_DENIED",
    "account_tenancy_enabled": "M141_ACCOUNT_TENANCY_DENIED",
    "tenant_runtime_started": "M141_TENANT_RUNTIME_DENIED",
    "workspace_sharing_enabled": "M141_WORKSPACE_SHARING_DENIED",
    "identity_federation_enabled": "M141_IDENTITY_FEDERATION_DENIED",
    "org_admin_runtime_started": "M141_ORG_ADMIN_RUNTIME_DENIED",
    "cross_workspace_access_enabled": "M141_CROSS_WORKSPACE_ACCESS_DENIED",
    "auth_runtime_started": "M141_AUTH_RUNTIME_DENIED",
    "login_enabled": "M141_LOGIN_DENIED",
    "session_cookie_enabled": "M141_SESSION_COOKIE_DENIED",
    "credential_handling_performed": "M141_CREDENTIAL_HANDLING_DENIED",
    "persistent_identity_store_enabled": "M141_PERSISTENT_IDENTITY_STORE_DENIED",
    "account_connector_enabled": "M141_ACCOUNT_CONNECTOR_DENIED",
    "production_runtime_enabled": "M141_PRODUCTION_RUNTIME_DENIED",
    "execution_performed": "M141_EXECUTION_DENIED",
    "tool_execution_performed": "M141_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M141_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M141_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M141_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M141_NETWORK_ACCESS_DENIED",
    "plugin_execution_performed": "M141_PLUGIN_EXECUTION_DENIED",
    "background_worker_started": "M141_BACKGROUND_WORKER_DENIED",
    "scheduler_started": "M141_SCHEDULER_DENIED",
    "mobile_sensor_performed": "M141_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M141_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M141_MODEL_CALL_DENIED",
    "memory_write_performed": "M141_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M141_CONTEXT_INJECTION_DENIED",
    "raw_prompt_payload_exposed": "M141_RAW_PROMPT_PAYLOAD_DENIED",
    "credential_cookie_access_performed": "M141_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "backend_route_added": "M141_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M141_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M141_DEPENDENCY_DENIED",
    "alpha_privacy_review_enabled": "M141_ALPHA_PRIVACY_REVIEW_DENIED",
    "alpha_release_enabled": "M141_ALPHA_RELEASE_DENIED",
    "beta_release_enabled": "M141_BETA_RELEASE_DENIED",
    "production_authority_granted": "M141_PRODUCTION_AUTHORITY_DENIED",
}
