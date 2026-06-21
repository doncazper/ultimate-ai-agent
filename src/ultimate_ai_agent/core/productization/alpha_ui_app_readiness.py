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


ALPHA_UI_APP_READINESS_DOCS = [
    "docs/productization/ALPHA_UI_APP_READINESS.md",
    "docs/productization/ALPHA_UI_APP_READINESS_POLICY.md",
    "docs/productization/ALPHA_UI_APP_READINESS_AUTHORITY_BOUNDARY.md",
    "docs/productization/ALPHA_UI_APP_READINESS_RECEIPT_PLAN.md",
    "docs/productization/ALPHA_UI_APP_READINESS_NON_GOALS.md",
    "docs/productization/M143_TO_M144_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 143)
)


class AlphaUiAppReadinessStatus(str, Enum):
    readiness_review_recorded = "readiness_review_recorded"


class _AlphaUiAppReadinessModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class AlphaUiAppReadinessPolicy(_AlphaUiAppReadinessModel):
    policy_ref: str = "alpha-ui-app-readiness-policy:m143"
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    alpha_ui_app_readiness_only: bool = True
    m101_m142_coverage_required: bool = True
    ui_readiness_refs_required: bool = True
    app_readiness_refs_required: bool = True
    privacy_review_refs_required: bool = True
    accessibility_review_refs_required: bool = True
    release_blocker_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_readiness_required: bool = True
    no_effect_receipt_required: bool = True
    no_alpha_ui_runtime_required: bool = True
    no_app_readiness_execution_required: bool = True
    no_app_build_required: bool = True
    no_app_store_connect_required: bool = True
    no_alpha_release_required: bool = True
    no_production_authority_required: bool = True
    m144_future_only: bool = True
    alpha_ui_runtime_enabled: bool = False
    app_readiness_execution_enabled: bool = False
    app_build_enabled: bool = False
    app_signing_enabled: bool = False
    app_store_connect_enabled: bool = False
    testflight_upload_enabled: bool = False
    alpha_release_enabled: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    privacy_review_execution_enabled: bool = False
    raw_private_content_access_enabled: bool = False
    auth_runtime_enabled: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_enabled: bool = False
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
            raise ValueError("M143_SECRET_LIKE_APP_READINESS_CONTENT_DENIED") from exc
        return self


class AlphaUiAppReadinessRequest(_AlphaUiAppReadinessModel):
    request_ref: str
    readiness_review_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    ui_readiness_refs: list[str]
    app_readiness_refs: list[str]
    privacy_review_refs: list[str]
    accessibility_review_refs: list[str]
    release_blocker_refs: list[str]
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
    alpha_ui_app_readiness_only: bool = True
    m101_m142_coverage_required: bool = True
    ui_readiness_refs_required: bool = True
    app_readiness_refs_required: bool = True
    privacy_review_refs_required: bool = True
    accessibility_review_refs_required: bool = True
    release_blocker_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_readiness_required: bool = True
    no_effect_receipt_required: bool = True
    no_alpha_ui_runtime_required: bool = True
    no_app_readiness_execution_required: bool = True
    no_app_build_required: bool = True
    no_app_store_connect_required: bool = True
    no_alpha_release_required: bool = True
    no_production_authority_required: bool = True
    alpha_ui_runtime_requested: bool = False
    app_readiness_execution_requested: bool = False
    app_build_requested: bool = False
    app_signing_requested: bool = False
    app_store_connect_requested: bool = False
    testflight_upload_requested: bool = False
    alpha_release_requested: bool = False
    beta_release_requested: bool = False
    production_authority_requested: bool = False
    privacy_review_execution_requested: bool = False
    raw_private_content_access_requested: bool = False
    auth_runtime_requested: bool = False
    login_requested: bool = False
    session_cookie_requested: bool = False
    credential_handling_requested: bool = False
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


class AlphaUiAppReadinessRecord(_AlphaUiAppReadinessModel):
    record_ref: str
    readiness_review_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    ui_readiness_refs: list[str]
    app_readiness_refs: list[str]
    privacy_review_refs: list[str]
    accessibility_review_refs: list[str]
    release_blocker_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: AlphaUiAppReadinessStatus = (
        AlphaUiAppReadinessStatus.readiness_review_recorded
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    alpha_ui_app_readiness_only: bool = True
    m101_m142_covered: bool = True
    ui_readiness_bound: bool = True
    app_readiness_bound: bool = True
    privacy_review_bound: bool = True
    accessibility_review_bound: bool = True
    release_blocker_bound: bool = True
    audit_replay_bound: bool = True
    revocation_readiness_bound: bool = True
    no_effect_receipt_required: bool = True
    no_alpha_ui_runtime: bool = True
    no_app_readiness_execution: bool = True
    no_app_build: bool = True
    no_app_store_connect: bool = True
    no_alpha_release: bool = True
    no_production_authority: bool = True
    alpha_ui_runtime_started: bool = False
    app_readiness_execution_performed: bool = False
    app_build_performed: bool = False
    app_signing_performed: bool = False
    app_store_connect_performed: bool = False
    testflight_upload_performed: bool = False
    alpha_release_enabled: bool = False
    beta_release_enabled: bool = False
    production_authority_granted: bool = False
    privacy_review_execution_performed: bool = False
    raw_private_content_accessed: bool = False
    auth_runtime_started: bool = False
    login_enabled: bool = False
    session_cookie_enabled: bool = False
    credential_handling_performed: bool = False
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
            raise ValueError("M143_REASON_CODE_REQUIRED")
        return self


def build_alpha_ui_app_readiness_record(
    request: AlphaUiAppReadinessRequest,
    policy: AlphaUiAppReadinessPolicy | None = None,
) -> AlphaUiAppReadinessRecord:
    active_policy = validate_alpha_ui_app_readiness_policy(
        policy or AlphaUiAppReadinessPolicy()
    )
    validated_request = validate_alpha_ui_app_readiness_request(request)
    record = AlphaUiAppReadinessRecord(
        record_ref=f"alpha-ui-app-readiness-record:{_ref_suffix(validated_request.readiness_review_ref)}",
        readiness_review_ref=validated_request.readiness_review_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        ui_readiness_refs=list(validated_request.ui_readiness_refs),
        app_readiness_refs=list(validated_request.app_readiness_refs),
        privacy_review_refs=list(validated_request.privacy_review_refs),
        accessibility_review_refs=list(validated_request.accessibility_review_refs),
        release_blocker_refs=list(validated_request.release_blocker_refs),
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
        alpha_ui_app_readiness_only=active_policy.alpha_ui_app_readiness_only,
        m101_m142_covered=active_policy.m101_m142_coverage_required,
        ui_readiness_bound=active_policy.ui_readiness_refs_required,
        app_readiness_bound=active_policy.app_readiness_refs_required,
        privacy_review_bound=active_policy.privacy_review_refs_required,
        accessibility_review_bound=active_policy.accessibility_review_refs_required,
        release_blocker_bound=active_policy.release_blocker_refs_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_readiness_bound=active_policy.revocation_readiness_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_alpha_ui_runtime=active_policy.no_alpha_ui_runtime_required,
        no_app_readiness_execution=active_policy.no_app_readiness_execution_required,
        no_app_build=active_policy.no_app_build_required,
        no_app_store_connect=active_policy.no_app_store_connect_required,
        no_alpha_release=active_policy.no_alpha_release_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M143_ALPHA_UI_APP_READINESS_REVIEW_ONLY",
            "M143_M101_M142_COVERED",
            "M143_NO_ALPHA_UI_RUNTIME",
            "M143_NO_APP_READINESS_EXECUTION",
            "M143_NO_APP_BUILD",
            "M143_NO_APP_STORE_CONNECT",
            "M143_NO_ALPHA_RELEASE",
            "M143_NO_PRODUCTION_AUTHORITY",
            "M144_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M143 records contract-only alpha UI and app readiness review refs "
            "using safe UI, app, privacy, accessibility, release-blocker, audit, "
            "replay, revocation, kill-switch, and no-effect receipt refs. It "
            "grants no alpha UI runtime, app readiness execution, app build, app "
            "signing, App Store Connect, TestFlight upload, alpha release, beta "
            "release, execution, model call, memory write, context injection, "
            "backend route, Control Center control, dependency, or production "
            "authority."
        ),
    )
    return validate_alpha_ui_app_readiness_record(record)


def validate_alpha_ui_app_readiness_policy(
    policy: AlphaUiAppReadinessPolicy,
) -> AlphaUiAppReadinessPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, AlphaUiAppReadinessPolicy):
        raise ValueError("M143_SECRET_LIKE_APP_READINESS_CONTENT_DENIED")
    validated = AlphaUiAppReadinessPolicy.model_validate(payload)
    for field_name, reason in _M143_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M143_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M143_SECRET_LIKE_APP_READINESS_CONTENT_DENIED") from exc
    return validated


def validate_alpha_ui_app_readiness_request(
    request: AlphaUiAppReadinessRequest,
) -> AlphaUiAppReadinessRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, AlphaUiAppReadinessRequest):
        raise ValueError("M143_SECRET_LIKE_APP_READINESS_CONTENT_DENIED")
    _deny_enabled(_M143_REQUEST_DENIALS, payload)
    validated = AlphaUiAppReadinessRequest.model_validate(payload)
    for field_name, reason in _M143_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M143_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M143_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in [
        (validated.ui_readiness_refs, "ui_readiness_ref", "M143_UI_READINESS_REF_REQUIRED"),
        (
            validated.app_readiness_refs,
            "app_readiness_ref",
            "M143_APP_READINESS_REF_REQUIRED",
        ),
        (
            validated.privacy_review_refs,
            "privacy_review_ref",
            "M143_PRIVACY_REVIEW_REF_REQUIRED",
        ),
        (
            validated.accessibility_review_refs,
            "accessibility_review_ref",
            "M143_ACCESSIBILITY_REVIEW_REF_REQUIRED",
        ),
        (
            validated.release_blocker_refs,
            "release_blocker_ref",
            "M143_RELEASE_BLOCKER_REF_REQUIRED",
        ),
    ]:
        _validate_ref_list(values, field_name, reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M143_SECRET_LIKE_APP_READINESS_CONTENT_DENIED") from exc
    return validated


def validate_alpha_ui_app_readiness_record(
    record: AlphaUiAppReadinessRecord,
) -> AlphaUiAppReadinessRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, AlphaUiAppReadinessRecord):
        raise ValueError("M143_SECRET_LIKE_APP_READINESS_CONTENT_DENIED")
    _deny_enabled(_M143_RECORD_DENIALS, payload)
    validated = AlphaUiAppReadinessRecord.model_validate(payload)
    for field_name, reason in _M143_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M143_RECORD_DENIALS, _model_payload(validated))
    if validated.status != AlphaUiAppReadinessStatus.readiness_review_recorded:
        raise ValueError("M143_APP_READINESS_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M143_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in [
        (validated.ui_readiness_refs, "ui_readiness_ref", "M143_UI_READINESS_REF_REQUIRED"),
        (
            validated.app_readiness_refs,
            "app_readiness_ref",
            "M143_APP_READINESS_REF_REQUIRED",
        ),
        (
            validated.privacy_review_refs,
            "privacy_review_ref",
            "M143_PRIVACY_REVIEW_REF_REQUIRED",
        ),
        (
            validated.accessibility_review_refs,
            "accessibility_review_ref",
            "M143_ACCESSIBILITY_REVIEW_REF_REQUIRED",
        ),
        (
            validated.release_blocker_refs,
            "release_blocker_ref",
            "M143_RELEASE_BLOCKER_REF_REQUIRED",
        ),
    ]:
        _validate_ref_list(values, field_name, reason)
    if "M143_ALPHA_UI_APP_READINESS_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M143_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M143_SECRET_LIKE_APP_READINESS_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: AlphaUiAppReadinessRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.readiness_review_ref, "readiness_review_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: AlphaUiAppReadinessRecord) -> list[Any]:
    return [
        (record.record_ref, "record_ref"),
        (record.readiness_review_ref, "readiness_review_ref"),
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
        raise ValueError("M143_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M143_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M143_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M143_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M143_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M143_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M143_REQUIRED_TRUE = [
    ("contract_only", "M143_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M143_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M143_DETERMINISTIC_REQUIRED"),
    ("local_only", "M143_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M143_SAFE_REFS_ONLY_REQUIRED"),
    ("alpha_ui_app_readiness_only", "M143_ALPHA_UI_APP_READINESS_ONLY_REQUIRED"),
    ("m101_m142_coverage_required", "M143_M101_M142_COVERAGE_REQUIRED"),
    ("ui_readiness_refs_required", "M143_UI_READINESS_REF_REQUIRED"),
    ("app_readiness_refs_required", "M143_APP_READINESS_REF_REQUIRED"),
    ("privacy_review_refs_required", "M143_PRIVACY_REVIEW_REF_REQUIRED"),
    ("accessibility_review_refs_required", "M143_ACCESSIBILITY_REVIEW_REF_REQUIRED"),
    ("release_blocker_refs_required", "M143_RELEASE_BLOCKER_REF_REQUIRED"),
    ("audit_replay_required", "M143_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_required", "M143_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M143_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_alpha_ui_runtime_required", "M143_ALPHA_UI_RUNTIME_DENIED"),
    (
        "no_app_readiness_execution_required",
        "M143_APP_READINESS_EXECUTION_DENIED",
    ),
    ("no_app_build_required", "M143_APP_BUILD_DENIED"),
    ("no_app_store_connect_required", "M143_APP_STORE_CONNECT_DENIED"),
    ("no_alpha_release_required", "M143_ALPHA_RELEASE_DENIED"),
    ("no_production_authority_required", "M143_PRODUCTION_AUTHORITY_DENIED"),
]

_M143_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M143_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M143_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M143_DETERMINISTIC_REQUIRED"),
    ("local_only", "M143_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M143_SAFE_REFS_ONLY_REQUIRED"),
    ("alpha_ui_app_readiness_only", "M143_ALPHA_UI_APP_READINESS_ONLY_REQUIRED"),
    ("m101_m142_covered", "M143_M101_M142_COVERAGE_REQUIRED"),
    ("ui_readiness_bound", "M143_UI_READINESS_REF_REQUIRED"),
    ("app_readiness_bound", "M143_APP_READINESS_REF_REQUIRED"),
    ("privacy_review_bound", "M143_PRIVACY_REVIEW_REF_REQUIRED"),
    ("accessibility_review_bound", "M143_ACCESSIBILITY_REVIEW_REF_REQUIRED"),
    ("release_blocker_bound", "M143_RELEASE_BLOCKER_REF_REQUIRED"),
    ("audit_replay_bound", "M143_AUDIT_REPLAY_REQUIRED"),
    ("revocation_readiness_bound", "M143_REVOCATION_READINESS_REQUIRED"),
    ("no_effect_receipt_required", "M143_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_alpha_ui_runtime", "M143_ALPHA_UI_RUNTIME_DENIED"),
    ("no_app_readiness_execution", "M143_APP_READINESS_EXECUTION_DENIED"),
    ("no_app_build", "M143_APP_BUILD_DENIED"),
    ("no_app_store_connect", "M143_APP_STORE_CONNECT_DENIED"),
    ("no_alpha_release", "M143_ALPHA_RELEASE_DENIED"),
    ("no_production_authority", "M143_PRODUCTION_AUTHORITY_DENIED"),
]

_M143_POLICY_DENIALS = {
    "alpha_ui_runtime_enabled": "M143_ALPHA_UI_RUNTIME_DENIED",
    "app_readiness_execution_enabled": "M143_APP_READINESS_EXECUTION_DENIED",
    "app_build_enabled": "M143_APP_BUILD_DENIED",
    "app_signing_enabled": "M143_APP_SIGNING_DENIED",
    "app_store_connect_enabled": "M143_APP_STORE_CONNECT_DENIED",
    "testflight_upload_enabled": "M143_TESTFLIGHT_UPLOAD_DENIED",
    "alpha_release_enabled": "M143_ALPHA_RELEASE_DENIED",
    "beta_release_enabled": "M143_BETA_RELEASE_DENIED",
    "production_authority_granted": "M143_PRODUCTION_AUTHORITY_DENIED",
    "privacy_review_execution_enabled": "M143_PRIVACY_REVIEW_EXECUTION_DENIED",
    "raw_private_content_access_enabled": "M143_RAW_PRIVATE_CONTENT_DENIED",
    "auth_runtime_enabled": "M143_AUTH_RUNTIME_DENIED",
    "login_enabled": "M143_LOGIN_DENIED",
    "session_cookie_enabled": "M143_SESSION_COOKIE_DENIED",
    "credential_handling_enabled": "M143_CREDENTIAL_HANDLING_DENIED",
    "execution_enabled": "M143_EXECUTION_DENIED",
    "tool_execution_enabled": "M143_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M143_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M143_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M143_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M143_NETWORK_ACCESS_DENIED",
    "plugin_execution_enabled": "M143_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_enabled": "M143_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M143_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M143_MODEL_CALL_DENIED",
    "memory_write_enabled": "M143_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M143_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M143_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M143_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M143_DEPENDENCY_DENIED",
}

_M143_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M143_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "app_build_requested": "M143_APP_BUILD_DENIED",
    "app_signing_requested": "M143_APP_SIGNING_DENIED",
    "app_store_connect_requested": "M143_APP_STORE_CONNECT_DENIED",
    "testflight_upload_requested": "M143_TESTFLIGHT_UPLOAD_DENIED",
    "production_authority_requested": "M143_PRODUCTION_AUTHORITY_DENIED",
    "raw_private_content_access_requested": "M143_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_private_content": "M143_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_prompt": "M143_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M143_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M143_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M143_SECRET_DENIED",
    "dependency_requested": "M143_DEPENDENCY_DENIED",
}

_M143_RECORD_DENIALS = {
    "alpha_ui_runtime_started": "M143_ALPHA_UI_RUNTIME_DENIED",
    "app_readiness_execution_performed": "M143_APP_READINESS_EXECUTION_DENIED",
    "app_build_performed": "M143_APP_BUILD_DENIED",
    "app_signing_performed": "M143_APP_SIGNING_DENIED",
    "app_store_connect_performed": "M143_APP_STORE_CONNECT_DENIED",
    "testflight_upload_performed": "M143_TESTFLIGHT_UPLOAD_DENIED",
    "alpha_release_enabled": "M143_ALPHA_RELEASE_DENIED",
    "beta_release_enabled": "M143_BETA_RELEASE_DENIED",
    "production_authority_granted": "M143_PRODUCTION_AUTHORITY_DENIED",
    "privacy_review_execution_performed": "M143_PRIVACY_REVIEW_EXECUTION_DENIED",
    "raw_private_content_accessed": "M143_RAW_PRIVATE_CONTENT_DENIED",
    "auth_runtime_started": "M143_AUTH_RUNTIME_DENIED",
    "login_enabled": "M143_LOGIN_DENIED",
    "session_cookie_enabled": "M143_SESSION_COOKIE_DENIED",
    "credential_handling_performed": "M143_CREDENTIAL_HANDLING_DENIED",
    "execution_performed": "M143_EXECUTION_DENIED",
    "tool_execution_performed": "M143_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M143_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M143_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M143_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M143_NETWORK_ACCESS_DENIED",
    "plugin_execution_performed": "M143_PLUGIN_EXECUTION_DENIED",
    "mobile_sensor_performed": "M143_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M143_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M143_MODEL_CALL_DENIED",
    "memory_write_performed": "M143_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M143_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M143_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M143_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M143_DEPENDENCY_DENIED",
}
