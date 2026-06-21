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


ALPHA_PRIVACY_REVIEW_DOCS = [
    "docs/productization/ALPHA_PRIVACY_REVIEW.md",
    "docs/productization/ALPHA_PRIVACY_REVIEW_POLICY.md",
    "docs/productization/ALPHA_PRIVACY_REVIEW_AUTHORITY_BOUNDARY.md",
    "docs/productization/ALPHA_PRIVACY_REVIEW_RECEIPT_PLAN.md",
    "docs/productization/ALPHA_PRIVACY_REVIEW_NON_GOALS.md",
    "docs/productization/M142_TO_M143_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 142)
)


class AlphaPrivacyReviewStatus(str, Enum):
    privacy_review_recorded = "privacy_review_recorded"


class _AlphaPrivacyReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AlphaPrivacyReviewPolicy(_AlphaPrivacyReviewModel):
    policy_ref: str = "alpha-privacy-review-policy:m142"
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    alpha_privacy_review_only: bool = True
    m101_m141_coverage_required: bool = True
    privacy_review_refs_required: bool = True
    data_boundary_refs_required: bool = True
    disclosure_review_refs_required: bool = True
    consent_review_refs_required: bool = True
    retention_review_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_readiness_required: bool = True
    no_effect_receipt_required: bool = True
    no_privacy_review_execution_required: bool = True
    no_alpha_signoff_required: bool = True
    no_alpha_ui_runtime_required: bool = True
    no_production_authority_required: bool = True
    m143_future_only: bool = True
    privacy_review_execution_enabled: bool = False
    alpha_privacy_signoff_enabled: bool = False
    alpha_ui_runtime_enabled: bool = False
    alpha_release_enabled: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    multi_user_runtime_enabled: bool = False
    account_tenancy_enabled: bool = False
    workspace_sharing_enabled: bool = False
    identity_federation_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_enabled: bool = False
    raw_private_content_access_enabled: bool = False
    raw_prompt_payload_exposure_enabled: bool = False
    execution_enabled: bool = False
    tool_execution_enabled: bool = False
    shell_execution_enabled: bool = False
    browser_action_enabled: bool = False
    connector_action_enabled: bool = False
    network_access_enabled: bool = False
    plugin_execution_enabled: bool = False
    mobile_sensor_enabled: bool = False
    remote_execution_enabled: bool = False
    model_call_enabled: bool = False
    memory_write_enabled: bool = False
    context_injection_enabled: bool = False
    backend_route_enabled: bool = False
    control_center_control_enabled: bool = False
    dependency_added: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self) -> Any:
        _validate_m61_ref(self.policy_ref, "policy_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M142_SECRET_LIKE_PRIVACY_REVIEW_CONTENT_DENIED") from exc
        return self


class AlphaPrivacyReviewRequest(_AlphaPrivacyReviewModel):
    request_ref: str
    privacy_review_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    privacy_review_refs: list[str]
    data_boundary_refs: list[str]
    disclosure_review_refs: list[str]
    consent_review_refs: list[str]
    retention_review_refs: list[str]
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
    alpha_privacy_review_only: bool = True
    m101_m141_coverage_required: bool = True
    privacy_review_refs_required: bool = True
    data_boundary_refs_required: bool = True
    disclosure_review_refs_required: bool = True
    consent_review_refs_required: bool = True
    retention_review_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_readiness_required: bool = True
    no_effect_receipt_required: bool = True
    no_privacy_review_execution_required: bool = True
    no_alpha_signoff_required: bool = True
    no_alpha_ui_runtime_required: bool = True
    no_production_authority_required: bool = True
    privacy_review_execution_requested: bool = False
    alpha_privacy_signoff_requested: bool = False
    alpha_ui_runtime_requested: bool = False
    alpha_release_requested: bool = False
    beta_release_requested: bool = False
    production_authority_requested: bool = False
    multi_user_runtime_requested: bool = False
    account_tenancy_requested: bool = False
    workspace_sharing_requested: bool = False
    identity_federation_requested: bool = False
    auth_runtime_requested: bool = False
    login_requested: bool = False
    session_cookie_requested: bool = False
    credential_handling_requested: bool = False
    raw_private_content_access_requested: bool = False
    raw_prompt_payload_exposure_requested: bool = False
    execution_requested: bool = False
    tool_execution_requested: bool = False
    shell_execution_requested: bool = False
    browser_action_requested: bool = False
    connector_action_requested: bool = False
    network_access_requested: bool = False
    plugin_execution_requested: bool = False
    mobile_sensor_requested: bool = False
    remote_execution_requested: bool = False
    model_call_requested: bool = False
    memory_write_requested: bool = False
    context_injection_requested: bool = False
    backend_route_requested: bool = False
    control_center_control_requested: bool = False
    dependency_requested: bool = False
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


class AlphaPrivacyReviewRecord(_AlphaPrivacyReviewModel):
    record_ref: str
    privacy_review_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    privacy_review_refs: list[str]
    data_boundary_refs: list[str]
    disclosure_review_refs: list[str]
    consent_review_refs: list[str]
    retention_review_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: AlphaPrivacyReviewStatus = (
        AlphaPrivacyReviewStatus.privacy_review_recorded
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    alpha_privacy_review_only: bool = True
    m101_m141_covered: bool = True
    privacy_review_bound: bool = True
    data_boundary_bound: bool = True
    disclosure_review_bound: bool = True
    consent_review_bound: bool = True
    retention_review_bound: bool = True
    audit_replay_bound: bool = True
    revocation_readiness_bound: bool = True
    no_effect_receipt_required: bool = True
    no_privacy_review_execution: bool = True
    no_alpha_signoff: bool = True
    no_alpha_ui_runtime: bool = True
    no_production_authority: bool = True
    privacy_review_execution_performed: bool = False
    alpha_privacy_signoff_enabled: bool = False
    alpha_ui_runtime_started: bool = False
    alpha_release_enabled: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    multi_user_runtime_started: bool = False
    account_tenancy_enabled: bool = False
    workspace_sharing_enabled: bool = False
    identity_federation_enabled: bool = False
    auth_runtime_started: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_performed: bool = False
    raw_private_content_accessed: bool = False
    raw_prompt_payload_exposed: bool = False
    execution_performed: bool = False
    tool_execution_performed: bool = False
    shell_execution_performed: bool = False
    browser_action_performed: bool = False
    connector_action_performed: bool = False
    network_access_performed: bool = False
    plugin_execution_performed: bool = False
    mobile_sensor_performed: bool = False
    remote_execution_performed: bool = False
    model_call_performed: bool = False
    memory_write_performed: bool = False
    context_injection_performed: bool = False
    backend_route_added: bool = False
    control_center_control_added: bool = False
    dependency_added: bool = False
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
            raise ValueError("M142_REASON_CODE_REQUIRED")
        return self


def build_alpha_privacy_review_record(
    request: AlphaPrivacyReviewRequest,
    policy: AlphaPrivacyReviewPolicy | None = None,
) -> AlphaPrivacyReviewRecord:
    active_policy = validate_alpha_privacy_review_policy(
        policy or AlphaPrivacyReviewPolicy()
    )
    validated_request = validate_alpha_privacy_review_request(request)
    record = AlphaPrivacyReviewRecord(
        record_ref=f"alpha-privacy-review-record:{_ref_suffix(validated_request.privacy_review_ref)}",
        privacy_review_ref=validated_request.privacy_review_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        privacy_review_refs=list(validated_request.privacy_review_refs),
        data_boundary_refs=list(validated_request.data_boundary_refs),
        disclosure_review_refs=list(validated_request.disclosure_review_refs),
        consent_review_refs=list(validated_request.consent_review_refs),
        retention_review_refs=list(validated_request.retention_review_refs),
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
        alpha_privacy_review_only=active_policy.alpha_privacy_review_only,
        m101_m141_covered=active_policy.m101_m141_coverage_required,
        privacy_review_bound=active_policy.privacy_review_refs_required,
        data_boundary_bound=active_policy.data_boundary_refs_required,
        disclosure_review_bound=active_policy.disclosure_review_refs_required,
        consent_review_bound=active_policy.consent_review_refs_required,
        retention_review_bound=active_policy.retention_review_refs_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_readiness_bound=active_policy.revocation_readiness_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_privacy_review_execution=active_policy.no_privacy_review_execution_required,
        no_alpha_signoff=active_policy.no_alpha_signoff_required,
        no_alpha_ui_runtime=active_policy.no_alpha_ui_runtime_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M142_ALPHA_PRIVACY_REVIEW_REVIEW_ONLY",
            "M142_M101_M141_COVERED",
            "M142_NO_PRIVACY_REVIEW_EXECUTION",
            "M142_NO_ALPHA_PRIVACY_SIGNOFF",
            "M142_NO_ALPHA_UI_RUNTIME",
            "M142_NO_RAW_PRIVATE_CONTENT",
            "M142_NO_PRODUCTION_AUTHORITY",
            "M143_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M142 records a contract-only alpha privacy review using safe "
            "privacy, data-boundary, disclosure, consent, retention, audit, "
            "replay, revocation, kill-switch, and no-effect receipt refs. It "
            "grants no privacy review execution, alpha sign-off, alpha UI "
            "runtime, raw private content access, auth runtime, login, session "
            "material, private auth material handling, execution, model call, "
            "memory write, context injection, backend route, Control Center "
            "control, dependency, beta release, or production authority."
        ),
    )
    return validate_alpha_privacy_review_record(record)


def validate_alpha_privacy_review_policy(
    policy: AlphaPrivacyReviewPolicy,
) -> AlphaPrivacyReviewPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, AlphaPrivacyReviewPolicy):
        raise ValueError("M142_SECRET_LIKE_PRIVACY_REVIEW_CONTENT_DENIED")
    validated = AlphaPrivacyReviewPolicy.model_validate(payload)
    for field_name, reason in _M142_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M142_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M142_SECRET_LIKE_PRIVACY_REVIEW_CONTENT_DENIED") from exc
    return validated


def validate_alpha_privacy_review_request(
    request: AlphaPrivacyReviewRequest,
) -> AlphaPrivacyReviewRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, AlphaPrivacyReviewRequest):
        raise ValueError("M142_SECRET_LIKE_PRIVACY_REVIEW_CONTENT_DENIED")
    _deny_enabled(_M142_REQUEST_DENIALS, payload)
    validated = AlphaPrivacyReviewRequest.model_validate(payload)
    for field_name, reason in _M142_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M142_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M142_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in [
        (
            validated.privacy_review_refs,
            "privacy_review_ref",
            "M142_PRIVACY_REVIEW_REF_REQUIRED",
        ),
        (
            validated.data_boundary_refs,
            "data_boundary_ref",
            "M142_DATA_BOUNDARY_REF_REQUIRED",
        ),
        (
            validated.disclosure_review_refs,
            "disclosure_review_ref",
            "M142_DISCLOSURE_REVIEW_REF_REQUIRED",
        ),
        (
            validated.consent_review_refs,
            "consent_review_ref",
            "M142_CONSENT_REVIEW_REF_REQUIRED",
        ),
        (
            validated.retention_review_refs,
            "retention_review_ref",
            "M142_RETENTION_REVIEW_REF_REQUIRED",
        ),
    ]:
        _validate_ref_list(values, field_name, reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M142_SECRET_LIKE_PRIVACY_REVIEW_CONTENT_DENIED") from exc
    return validated


def validate_alpha_privacy_review_record(
    record: AlphaPrivacyReviewRecord,
) -> AlphaPrivacyReviewRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, AlphaPrivacyReviewRecord):
        raise ValueError("M142_SECRET_LIKE_PRIVACY_REVIEW_CONTENT_DENIED")
    _deny_enabled(_M142_RECORD_DENIALS, payload)
    validated = AlphaPrivacyReviewRecord.model_validate(payload)
    for field_name, reason in _M142_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M142_RECORD_DENIALS, _model_payload(validated))
    if validated.status != AlphaPrivacyReviewStatus.privacy_review_recorded:
        raise ValueError("M142_PRIVACY_REVIEW_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M142_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in [
        (
            validated.privacy_review_refs,
            "privacy_review_ref",
            "M142_PRIVACY_REVIEW_REF_REQUIRED",
        ),
        (
            validated.data_boundary_refs,
            "data_boundary_ref",
            "M142_DATA_BOUNDARY_REF_REQUIRED",
        ),
        (
            validated.disclosure_review_refs,
            "disclosure_review_ref",
            "M142_DISCLOSURE_REVIEW_REF_REQUIRED",
        ),
        (
            validated.consent_review_refs,
            "consent_review_ref",
            "M142_CONSENT_REVIEW_REF_REQUIRED",
        ),
        (
            validated.retention_review_refs,
            "retention_review_ref",
            "M142_RETENTION_REVIEW_REF_REQUIRED",
        ),
    ]:
        _validate_ref_list(values, field_name, reason)
    if "M142_ALPHA_PRIVACY_REVIEW_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M142_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M142_SECRET_LIKE_PRIVACY_REVIEW_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: AlphaPrivacyReviewRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.privacy_review_ref, "privacy_review_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: AlphaPrivacyReviewRecord) -> list[Any]:
    return [
        (record.record_ref, "record_ref"),
        (record.privacy_review_ref, "privacy_review_ref"),
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
        raise ValueError("M142_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M142_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M142_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M142_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M142_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M142_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M142_REQUIRED_TRUE = [
    ("contract_only", "M142_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M142_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M142_DETERMINISTIC_REQUIRED"),
    ("local_only", "M142_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M142_SAFE_REFS_ONLY_REQUIRED"),
    ("alpha_privacy_review_only", "M142_ALPHA_PRIVACY_REVIEW_ONLY_REQUIRED"),
    ("m101_m141_coverage_required", "M142_M101_M141_COVERAGE_REQUIRED"),
    ("privacy_review_refs_required", "M142_PRIVACY_REVIEW_REF_REQUIRED"),
    ("data_boundary_refs_required", "M142_DATA_BOUNDARY_REF_REQUIRED"),
    ("disclosure_review_refs_required", "M142_DISCLOSURE_REVIEW_REF_REQUIRED"),
    ("consent_review_refs_required", "M142_CONSENT_REVIEW_REF_REQUIRED"),
    ("retention_review_refs_required", "M142_RETENTION_REVIEW_REF_REQUIRED"),
    ("audit_replay_required", "M142_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_required", "M142_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M142_NO_EFFECT_RECEIPT_REQUIRED"),
    (
        "no_privacy_review_execution_required",
        "M142_PRIVACY_REVIEW_EXECUTION_DENIED",
    ),
    ("no_alpha_signoff_required", "M142_ALPHA_PRIVACY_SIGNOFF_DENIED"),
    ("no_alpha_ui_runtime_required", "M142_ALPHA_UI_RUNTIME_DENIED"),
    ("no_production_authority_required", "M142_PRODUCTION_AUTHORITY_DENIED"),
]

_M142_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M142_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M142_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M142_DETERMINISTIC_REQUIRED"),
    ("local_only", "M142_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M142_SAFE_REFS_ONLY_REQUIRED"),
    ("alpha_privacy_review_only", "M142_ALPHA_PRIVACY_REVIEW_ONLY_REQUIRED"),
    ("m101_m141_covered", "M142_M101_M141_COVERAGE_REQUIRED"),
    ("privacy_review_bound", "M142_PRIVACY_REVIEW_REF_REQUIRED"),
    ("data_boundary_bound", "M142_DATA_BOUNDARY_REF_REQUIRED"),
    ("disclosure_review_bound", "M142_DISCLOSURE_REVIEW_REF_REQUIRED"),
    ("consent_review_bound", "M142_CONSENT_REVIEW_REF_REQUIRED"),
    ("retention_review_bound", "M142_RETENTION_REVIEW_REF_REQUIRED"),
    ("audit_replay_bound", "M142_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_bound", "M142_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M142_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_privacy_review_execution", "M142_PRIVACY_REVIEW_EXECUTION_DENIED"),
    ("no_alpha_signoff", "M142_ALPHA_PRIVACY_SIGNOFF_DENIED"),
    ("no_alpha_ui_runtime", "M142_ALPHA_UI_RUNTIME_DENIED"),
    ("no_production_authority", "M142_PRODUCTION_AUTHORITY_DENIED"),
]

_M142_POLICY_DENIALS = {
    "privacy_review_execution_enabled": "M142_PRIVACY_REVIEW_EXECUTION_DENIED",
    "alpha_privacy_signoff_enabled": "M142_ALPHA_PRIVACY_SIGNOFF_DENIED",
    "alpha_ui_runtime_enabled": "M142_ALPHA_UI_RUNTIME_DENIED",
    "alpha_release_enabled": "M142_ALPHA_RELEASE_DENIED",
    "beta_release_enabled": "M142_BETA_RELEASE_DENIED",
    "production_authority_granted": "M142_PRODUCTION_AUTHORITY_DENIED",
    "multi_user_runtime_enabled": "M142_MULTI_USER_RUNTIME_DENIED",
    "account_tenancy_enabled": "M142_ACCOUNT_TENANCY_DENIED",
    "workspace_sharing_enabled": "M142_WORKSPACE_SHARING_DENIED",
    "identity_federation_enabled": "M142_IDENTITY_FEDERATION_DENIED",
    "auth_runtime_enabled": "M142_AUTH_RUNTIME_DENIED",
    "login_enabled": "M142_LOGIN_DENIED",
    "session_cookie_enabled": "M142_SESSION_COOKIE_DENIED",
    "credential_handling_enabled": "M142_CREDENTIAL_HANDLING_DENIED",
    "raw_private_content_access_enabled": "M142_RAW_PRIVATE_CONTENT_DENIED",
    "raw_prompt_payload_exposure_enabled": "M142_RAW_PROMPT_PAYLOAD_DENIED",
    "execution_enabled": "M142_EXECUTION_DENIED",
    "tool_execution_enabled": "M142_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M142_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M142_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M142_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M142_NETWORK_ACCESS_DENIED",
    "plugin_execution_enabled": "M142_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_enabled": "M142_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M142_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M142_MODEL_CALL_DENIED",
    "memory_write_enabled": "M142_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M142_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M142_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M142_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M142_DEPENDENCY_DENIED",
}

_M142_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M142_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "privacy_review_execution_requested": "M142_PRIVACY_REVIEW_EXECUTION_DENIED",
    "alpha_privacy_signoff_requested": "M142_ALPHA_PRIVACY_SIGNOFF_DENIED",
    "alpha_ui_runtime_requested": "M142_ALPHA_UI_RUNTIME_DENIED",
    "production_authority_requested": "M142_PRODUCTION_AUTHORITY_DENIED",
    "raw_private_content_access_requested": "M142_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_private_content": "M142_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_prompt": "M142_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M142_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M142_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M142_SECRET_DENIED",
    "dependency_requested": "M142_DEPENDENCY_DENIED",
}

_M142_RECORD_DENIALS = {
    "privacy_review_execution_performed": "M142_PRIVACY_REVIEW_EXECUTION_DENIED",
    "alpha_privacy_signoff_enabled": "M142_ALPHA_PRIVACY_SIGNOFF_DENIED",
    "alpha_ui_runtime_started": "M142_ALPHA_UI_RUNTIME_DENIED",
    "alpha_release_enabled": "M142_ALPHA_RELEASE_DENIED",
    "beta_release_enabled": "M142_BETA_RELEASE_DENIED",
    "production_authority_granted": "M142_PRODUCTION_AUTHORITY_DENIED",
    "multi_user_runtime_started": "M142_MULTI_USER_RUNTIME_DENIED",
    "account_tenancy_enabled": "M142_ACCOUNT_TENANCY_DENIED",
    "workspace_sharing_enabled": "M142_WORKSPACE_SHARING_DENIED",
    "identity_federation_enabled": "M142_IDENTITY_FEDERATION_DENIED",
    "auth_runtime_started": "M142_AUTH_RUNTIME_DENIED",
    "login_enabled": "M142_LOGIN_DENIED",
    "session_cookie_enabled": "M142_SESSION_COOKIE_DENIED",
    "credential_handling_performed": "M142_CREDENTIAL_HANDLING_DENIED",
    "raw_private_content_accessed": "M142_RAW_PRIVATE_CONTENT_DENIED",
    "raw_prompt_payload_exposed": "M142_RAW_PROMPT_PAYLOAD_DENIED",
    "execution_performed": "M142_EXECUTION_DENIED",
    "tool_execution_performed": "M142_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M142_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M142_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M142_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M142_NETWORK_ACCESS_DENIED",
    "plugin_execution_performed": "M142_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_performed": "M142_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M142_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M142_MODEL_CALL_DENIED",
    "memory_write_performed": "M142_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M142_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M142_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M142_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M142_DEPENDENCY_DENIED",
}
