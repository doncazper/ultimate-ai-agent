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


ULTIMATE_AI_AGENT_ALPHA_DOCS = [
    "docs/productization/ULTIMATE_AI_AGENT_ALPHA.md",
    "docs/productization/ULTIMATE_AI_AGENT_ALPHA_POLICY.md",
    "docs/productization/ULTIMATE_AI_AGENT_ALPHA_AUTHORITY_BOUNDARY.md",
    "docs/productization/ULTIMATE_AI_AGENT_ALPHA_RECEIPT_PLAN.md",
    "docs/productization/ULTIMATE_AI_AGENT_ALPHA_NON_GOALS.md",
    "docs/productization/M150_ALPHA_TO_BETA_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 150)
)
M150_PRODUCT_TARGET_REF = "product-target:v1.2.0-alpha"
M150_PRODUCT_TARGET_VERSION = "v1.2.0-alpha"


class UltimateAiAgentAlphaStatus(str, Enum):
    alpha_target_recorded = "alpha_target_recorded"


class _UltimateAiAgentAlphaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class UltimateAiAgentAlphaPolicy(_UltimateAiAgentAlphaModel):
    policy_ref: str = "ultimate-ai-agent-alpha-policy:m150"
    product_target_ref: str = M150_PRODUCT_TARGET_REF
    contract_only: bool = True
    review_only: bool = True
    alpha_target_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    disabled_by_default_required: bool = True
    m101_m149_coverage_required: bool = True
    alpha_target_refs_required: bool = True
    release_candidate_freeze_refs_required: bool = True
    alpha_readiness_refs_required: bool = True
    evidence_index_refs_required: bool = True
    blocker_summary_refs_required: bool = True
    signoff_review_refs_required: bool = True
    beta_promotion_gate_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_release_publication_required: bool = True
    no_release_tag_required: bool = True
    no_tag_creation_required: bool = True
    no_artifact_build_required: bool = True
    no_artifact_upload_required: bool = True
    no_artifact_export_required: bool = True
    no_external_distribution_required: bool = True
    no_app_store_submission_required: bool = True
    no_testflight_submission_required: bool = True
    no_beta_release_required: bool = True
    no_release_automation_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    beta_future_only: bool = True
    release_publication_enabled: bool = False
    release_tag_enabled: bool = False
    tag_creation_enabled: bool = False
    artifact_build_enabled: bool = False
    artifact_upload_enabled: bool = False
    artifact_export_enabled: bool = False
    external_distribution_enabled: bool = False
    app_store_submission_enabled: bool = False
    testflight_submission_enabled: bool = False
    beta_release_enabled: bool = False
    release_automation_enabled: bool = False
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
    production_authority_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_shape(self):
        _validate_m61_ref(self.policy_ref, "policy_ref")
        _validate_m61_ref(self.product_target_ref, "product_target_ref")
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M150_SECRET_LIKE_ALPHA_CONTENT_DENIED") from exc
        return self


class UltimateAiAgentAlphaRequest(_UltimateAiAgentAlphaModel):
    request_ref: str
    alpha_target_ref: str
    product_target_ref: str = M150_PRODUCT_TARGET_REF
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    alpha_target_refs: list[str]
    release_candidate_freeze_refs: list[str]
    alpha_readiness_refs: list[str]
    evidence_index_refs: list[str]
    blocker_summary_refs: list[str]
    signoff_review_refs: list[str]
    beta_promotion_gate_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    safe_summary: str
    contract_only: bool = True
    review_only: bool = True
    alpha_target_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    disabled_by_default_required: bool = True
    m101_m149_coverage_required: bool = True
    alpha_target_refs_required: bool = True
    release_candidate_freeze_refs_required: bool = True
    alpha_readiness_refs_required: bool = True
    evidence_index_refs_required: bool = True
    blocker_summary_refs_required: bool = True
    signoff_review_refs_required: bool = True
    beta_promotion_gate_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_release_publication_required: bool = True
    no_release_tag_required: bool = True
    no_tag_creation_required: bool = True
    no_artifact_build_required: bool = True
    no_artifact_upload_required: bool = True
    no_artifact_export_required: bool = True
    no_external_distribution_required: bool = True
    no_app_store_submission_required: bool = True
    no_testflight_submission_required: bool = True
    no_beta_release_required: bool = True
    no_release_automation_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    release_publication_requested: bool = False
    release_tag_requested: bool = False
    tag_creation_requested: bool = False
    artifact_build_requested: bool = False
    artifact_upload_requested: bool = False
    artifact_export_requested: bool = False
    external_distribution_requested: bool = False
    app_store_submission_requested: bool = False
    testflight_submission_requested: bool = False
    beta_release_requested: bool = False
    release_automation_requested: bool = False
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


class UltimateAiAgentAlphaRecord(_UltimateAiAgentAlphaModel):
    record_ref: str
    alpha_target_ref: str
    product_target_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    alpha_target_refs: list[str]
    release_candidate_freeze_refs: list[str]
    alpha_readiness_refs: list[str]
    evidence_index_refs: list[str]
    blocker_summary_refs: list[str]
    signoff_review_refs: list[str]
    beta_promotion_gate_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: UltimateAiAgentAlphaStatus = UltimateAiAgentAlphaStatus.alpha_target_recorded
    contract_only: bool = True
    review_only: bool = True
    alpha_target_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    disabled_by_default: bool = True
    m101_m149_covered: bool = True
    alpha_targets_bound: bool = True
    release_candidate_freezes_bound: bool = True
    alpha_readiness_bound: bool = True
    evidence_indexes_bound: bool = True
    blocker_summaries_bound: bool = True
    signoff_reviews_bound: bool = True
    beta_promotion_gates_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    no_effect_receipt_required: bool = True
    no_release_publication: bool = True
    no_release_tag: bool = True
    no_tag_creation: bool = True
    no_artifact_build: bool = True
    no_artifact_upload: bool = True
    no_artifact_export: bool = True
    no_external_distribution: bool = True
    no_app_store_submission: bool = True
    no_testflight_submission: bool = True
    no_beta_release: bool = True
    no_release_automation: bool = True
    no_backend_route: bool = True
    no_control_center_control: bool = True
    no_dependency: bool = True
    no_production_authority: bool = True
    release_publication_started: bool = False
    release_tag_created: bool = False
    tag_creation_performed: bool = False
    artifact_build_performed: bool = False
    artifact_upload_started: bool = False
    artifact_export_started: bool = False
    external_distribution_started: bool = False
    app_store_submission_started: bool = False
    testflight_submission_started: bool = False
    beta_release_enabled: bool = False
    release_automation_started: bool = False
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
            raise ValueError("M150_REASON_CODE_REQUIRED")
        return self


def build_ultimate_ai_agent_alpha_record(
    request: UltimateAiAgentAlphaRequest,
    policy: UltimateAiAgentAlphaPolicy | None = None,
) -> UltimateAiAgentAlphaRecord:
    active_policy = validate_ultimate_ai_agent_alpha_policy(
        policy or UltimateAiAgentAlphaPolicy()
    )
    validated_request = validate_ultimate_ai_agent_alpha_request(request)
    record = UltimateAiAgentAlphaRecord(
        record_ref=(
            "ultimate-ai-agent-alpha-record:"
            f"{_ref_suffix(validated_request.alpha_target_ref)}"
        ),
        alpha_target_ref=validated_request.alpha_target_ref,
        product_target_ref=active_policy.product_target_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        alpha_target_refs=list(validated_request.alpha_target_refs),
        release_candidate_freeze_refs=list(
            validated_request.release_candidate_freeze_refs
        ),
        alpha_readiness_refs=list(validated_request.alpha_readiness_refs),
        evidence_index_refs=list(validated_request.evidence_index_refs),
        blocker_summary_refs=list(validated_request.blocker_summary_refs),
        signoff_review_refs=list(validated_request.signoff_review_refs),
        beta_promotion_gate_refs=list(validated_request.beta_promotion_gate_refs),
        audit_ref=validated_request.audit_ref,
        replay_ref=validated_request.replay_ref,
        revocation_ref=validated_request.revocation_ref,
        kill_switch_ref=validated_request.kill_switch_ref,
        no_effect_receipt_plan_ref=validated_request.no_effect_receipt_plan_ref,
        contract_only=active_policy.contract_only,
        review_only=active_policy.review_only,
        alpha_target_only=active_policy.alpha_target_only,
        deterministic=active_policy.deterministic,
        local_only=active_policy.local_only,
        safe_refs_only=active_policy.safe_refs_only,
        disabled_by_default=active_policy.disabled_by_default_required,
        m101_m149_covered=active_policy.m101_m149_coverage_required,
        alpha_targets_bound=active_policy.alpha_target_refs_required,
        release_candidate_freezes_bound=(
            active_policy.release_candidate_freeze_refs_required
        ),
        alpha_readiness_bound=active_policy.alpha_readiness_refs_required,
        evidence_indexes_bound=active_policy.evidence_index_refs_required,
        blocker_summaries_bound=active_policy.blocker_summary_refs_required,
        signoff_reviews_bound=active_policy.signoff_review_refs_required,
        beta_promotion_gates_bound=active_policy.beta_promotion_gate_refs_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_release_publication=active_policy.no_release_publication_required,
        no_release_tag=active_policy.no_release_tag_required,
        no_tag_creation=active_policy.no_tag_creation_required,
        no_artifact_build=active_policy.no_artifact_build_required,
        no_artifact_upload=active_policy.no_artifact_upload_required,
        no_artifact_export=active_policy.no_artifact_export_required,
        no_external_distribution=active_policy.no_external_distribution_required,
        no_app_store_submission=active_policy.no_app_store_submission_required,
        no_testflight_submission=active_policy.no_testflight_submission_required,
        no_beta_release=active_policy.no_beta_release_required,
        no_release_automation=active_policy.no_release_automation_required,
        no_backend_route=active_policy.no_backend_route_required,
        no_control_center_control=active_policy.no_control_center_control_required,
        no_dependency=active_policy.no_dependency_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M150_ULTIMATE_AI_AGENT_ALPHA_REVIEW_ONLY",
            "M150_M101_M149_COVERED",
            "M150_ALPHA_TARGET_ONLY",
            "M150_DISABLED_BY_DEFAULT",
            "M150_NO_RELEASE_PUBLICATION",
            "M150_NO_RELEASE_TAG",
            "M150_NO_TAG_CREATION",
            "M150_NO_ARTIFACT_BUILD",
            "M150_NO_ARTIFACT_UPLOAD",
            "M150_NO_ARTIFACT_EXPORT",
            "M150_NO_EXTERNAL_DISTRIBUTION",
            "M150_NO_APP_STORE_SUBMISSION",
            "M150_NO_TESTFLIGHT_SUBMISSION",
            "M150_NO_BETA_RELEASE",
            "M150_NO_RELEASE_AUTOMATION",
            "M150_NO_BACKEND_ROUTE",
            "M150_NO_PRODUCTION_AUTHORITY",
            "BETA_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M150 records the Ultimate AI Agent v1.2.0-alpha target using safe "
            "alpha target, release candidate freeze, alpha readiness, evidence "
            "index, blocker summary, signoff review, beta promotion gate, audit, "
            "replay, revocation, kill-switch, and no-effect receipt refs. It "
            "does not publish a release, create a tag, build or upload artifacts, "
            "export artifacts, distribute externally, submit to App Store or "
            "TestFlight, enable beta, start release automation, add routes or "
            "controls, add dependencies, or grant production authority."
        ),
    )
    return validate_ultimate_ai_agent_alpha_record(record)


def validate_ultimate_ai_agent_alpha_policy(
    policy: UltimateAiAgentAlphaPolicy,
) -> UltimateAiAgentAlphaPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, UltimateAiAgentAlphaPolicy):
        raise ValueError("M150_SECRET_LIKE_ALPHA_CONTENT_DENIED")
    validated = UltimateAiAgentAlphaPolicy.model_validate(payload)
    for field_name, reason in _M150_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M150_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M150_SECRET_LIKE_ALPHA_CONTENT_DENIED") from exc
    return validated


def validate_ultimate_ai_agent_alpha_request(
    request: UltimateAiAgentAlphaRequest,
) -> UltimateAiAgentAlphaRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, UltimateAiAgentAlphaRequest):
        raise ValueError("M150_SECRET_LIKE_ALPHA_CONTENT_DENIED")
    _deny_enabled(_M150_REQUEST_DENIALS, payload)
    validated = UltimateAiAgentAlphaRequest.model_validate(payload)
    for field_name, reason in _M150_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M150_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M150_SIDE_EFFECTS_DENIED")
    if validated.product_target_ref != M150_PRODUCT_TARGET_REF:
        raise ValueError("M150_PRODUCT_TARGET_REF_REQUIRED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _request_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M150_SECRET_LIKE_ALPHA_CONTENT_DENIED") from exc
    return validated


def validate_ultimate_ai_agent_alpha_record(
    record: UltimateAiAgentAlphaRecord,
) -> UltimateAiAgentAlphaRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, UltimateAiAgentAlphaRecord):
        raise ValueError("M150_SECRET_LIKE_ALPHA_CONTENT_DENIED")
    _deny_enabled(_M150_RECORD_DENIALS, payload)
    validated = UltimateAiAgentAlphaRecord.model_validate(payload)
    for field_name, reason in _M150_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M150_RECORD_DENIALS, _model_payload(validated))
    if validated.status != UltimateAiAgentAlphaStatus.alpha_target_recorded:
        raise ValueError("M150_ALPHA_STATUS_REQUIRED")
    if validated.product_target_ref != M150_PRODUCT_TARGET_REF:
        raise ValueError("M150_PRODUCT_TARGET_REF_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M150_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _record_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    if "M150_ULTIMATE_AI_AGENT_ALPHA_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M150_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M150_SECRET_LIKE_ALPHA_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: UltimateAiAgentAlphaRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.alpha_target_ref, "alpha_target_ref"),
        (request.product_target_ref, "product_target_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: UltimateAiAgentAlphaRecord):
    return [
        (record.record_ref, "record_ref"),
        (record.alpha_target_ref, "alpha_target_ref"),
        (record.product_target_ref, "product_target_ref"),
        (record.request_ref, "request_ref"),
        (record.baseline_ref, "baseline_ref"),
        (record.actor_ref, "actor_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _request_ref_lists(request: UltimateAiAgentAlphaRequest):
    return [
        (request.alpha_target_refs, "alpha_target_ref", "M150_ALPHA_TARGET_REF_REQUIRED"),
        (
            request.release_candidate_freeze_refs,
            "release_candidate_freeze_ref",
            "M150_RELEASE_CANDIDATE_FREEZE_REF_REQUIRED",
        ),
        (
            request.alpha_readiness_refs,
            "alpha_readiness_ref",
            "M150_ALPHA_READINESS_REF_REQUIRED",
        ),
        (
            request.evidence_index_refs,
            "evidence_index_ref",
            "M150_EVIDENCE_INDEX_REF_REQUIRED",
        ),
        (
            request.blocker_summary_refs,
            "blocker_summary_ref",
            "M150_BLOCKER_SUMMARY_REF_REQUIRED",
        ),
        (
            request.signoff_review_refs,
            "signoff_review_ref",
            "M150_SIGNOFF_REVIEW_REF_REQUIRED",
        ),
        (
            request.beta_promotion_gate_refs,
            "beta_promotion_gate_ref",
            "M150_BETA_PROMOTION_GATE_REF_REQUIRED",
        ),
    ]


def _record_ref_lists(record: UltimateAiAgentAlphaRecord):
    return [
        (record.alpha_target_refs, "alpha_target_ref", "M150_ALPHA_TARGET_REF_REQUIRED"),
        (
            record.release_candidate_freeze_refs,
            "release_candidate_freeze_ref",
            "M150_RELEASE_CANDIDATE_FREEZE_REF_REQUIRED",
        ),
        (
            record.alpha_readiness_refs,
            "alpha_readiness_ref",
            "M150_ALPHA_READINESS_REF_REQUIRED",
        ),
        (
            record.evidence_index_refs,
            "evidence_index_ref",
            "M150_EVIDENCE_INDEX_REF_REQUIRED",
        ),
        (
            record.blocker_summary_refs,
            "blocker_summary_ref",
            "M150_BLOCKER_SUMMARY_REF_REQUIRED",
        ),
        (
            record.signoff_review_refs,
            "signoff_review_ref",
            "M150_SIGNOFF_REVIEW_REF_REQUIRED",
        ),
        (
            record.beta_promotion_gate_refs,
            "beta_promotion_gate_ref",
            "M150_BETA_PROMOTION_GATE_REF_REQUIRED",
        ),
    ]


def _validate_accepted_checkpoints(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M150_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M150_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M150_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M150_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M150_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M150_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M150_REQUIRED_TRUE = [
    ("contract_only", "M150_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M150_REVIEW_ONLY_REQUIRED"),
    ("alpha_target_only", "M150_ALPHA_TARGET_ONLY_REQUIRED"),
    ("deterministic", "M150_DETERMINISTIC_REQUIRED"),
    ("local_only", "M150_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M150_SAFE_REFS_ONLY_REQUIRED"),
    ("disabled_by_default_required", "M150_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m149_coverage_required", "M150_M101_M149_COVERAGE_REQUIRED"),
    ("alpha_target_refs_required", "M150_ALPHA_TARGET_REF_REQUIRED"),
    (
        "release_candidate_freeze_refs_required",
        "M150_RELEASE_CANDIDATE_FREEZE_REF_REQUIRED",
    ),
    ("alpha_readiness_refs_required", "M150_ALPHA_READINESS_REF_REQUIRED"),
    ("evidence_index_refs_required", "M150_EVIDENCE_INDEX_REF_REQUIRED"),
    ("blocker_summary_refs_required", "M150_BLOCKER_SUMMARY_REF_REQUIRED"),
    ("signoff_review_refs_required", "M150_SIGNOFF_REVIEW_REF_REQUIRED"),
    ("beta_promotion_gate_refs_required", "M150_BETA_PROMOTION_GATE_REF_REQUIRED"),
    ("audit_replay_required", "M150_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M150_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M150_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_release_publication_required", "M150_RELEASE_PUBLICATION_DENIED"),
    ("no_release_tag_required", "M150_RELEASE_TAG_DENIED"),
    ("no_tag_creation_required", "M150_TAG_CREATION_DENIED"),
    ("no_artifact_build_required", "M150_ARTIFACT_BUILD_DENIED"),
    ("no_artifact_upload_required", "M150_ARTIFACT_UPLOAD_DENIED"),
    ("no_artifact_export_required", "M150_ARTIFACT_EXPORT_DENIED"),
    ("no_external_distribution_required", "M150_EXTERNAL_DISTRIBUTION_DENIED"),
    ("no_app_store_submission_required", "M150_APP_STORE_SUBMISSION_DENIED"),
    ("no_testflight_submission_required", "M150_TESTFLIGHT_SUBMISSION_DENIED"),
    ("no_beta_release_required", "M150_BETA_RELEASE_DENIED"),
    ("no_release_automation_required", "M150_RELEASE_AUTOMATION_DENIED"),
    ("no_backend_route_required", "M150_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control_required", "M150_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency_required", "M150_DEPENDENCY_DENIED"),
    ("no_production_authority_required", "M150_PRODUCTION_AUTHORITY_DENIED"),
]

_M150_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M150_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M150_REVIEW_ONLY_REQUIRED"),
    ("alpha_target_only", "M150_ALPHA_TARGET_ONLY_REQUIRED"),
    ("deterministic", "M150_DETERMINISTIC_REQUIRED"),
    ("local_only", "M150_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M150_SAFE_REFS_ONLY_REQUIRED"),
    ("disabled_by_default", "M150_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m149_covered", "M150_M101_M149_COVERAGE_REQUIRED"),
    ("alpha_targets_bound", "M150_ALPHA_TARGET_REF_REQUIRED"),
    (
        "release_candidate_freezes_bound",
        "M150_RELEASE_CANDIDATE_FREEZE_REF_REQUIRED",
    ),
    ("alpha_readiness_bound", "M150_ALPHA_READINESS_REF_REQUIRED"),
    ("evidence_indexes_bound", "M150_EVIDENCE_INDEX_REF_REQUIRED"),
    ("blocker_summaries_bound", "M150_BLOCKER_SUMMARY_REF_REQUIRED"),
    ("signoff_reviews_bound", "M150_SIGNOFF_REVIEW_REF_REQUIRED"),
    ("beta_promotion_gates_bound", "M150_BETA_PROMOTION_GATE_REF_REQUIRED"),
    ("audit_replay_bound", "M150_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M150_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M150_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_release_publication", "M150_RELEASE_PUBLICATION_DENIED"),
    ("no_release_tag", "M150_RELEASE_TAG_DENIED"),
    ("no_tag_creation", "M150_TAG_CREATION_DENIED"),
    ("no_artifact_build", "M150_ARTIFACT_BUILD_DENIED"),
    ("no_artifact_upload", "M150_ARTIFACT_UPLOAD_DENIED"),
    ("no_artifact_export", "M150_ARTIFACT_EXPORT_DENIED"),
    ("no_external_distribution", "M150_EXTERNAL_DISTRIBUTION_DENIED"),
    ("no_app_store_submission", "M150_APP_STORE_SUBMISSION_DENIED"),
    ("no_testflight_submission", "M150_TESTFLIGHT_SUBMISSION_DENIED"),
    ("no_beta_release", "M150_BETA_RELEASE_DENIED"),
    ("no_release_automation", "M150_RELEASE_AUTOMATION_DENIED"),
    ("no_backend_route", "M150_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control", "M150_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency", "M150_DEPENDENCY_DENIED"),
    ("no_production_authority", "M150_PRODUCTION_AUTHORITY_DENIED"),
]

_M150_POLICY_DENIALS = {
    "release_publication_enabled": "M150_RELEASE_PUBLICATION_DENIED",
    "release_tag_enabled": "M150_RELEASE_TAG_DENIED",
    "tag_creation_enabled": "M150_TAG_CREATION_DENIED",
    "artifact_build_enabled": "M150_ARTIFACT_BUILD_DENIED",
    "artifact_upload_enabled": "M150_ARTIFACT_UPLOAD_DENIED",
    "artifact_export_enabled": "M150_ARTIFACT_EXPORT_DENIED",
    "external_distribution_enabled": "M150_EXTERNAL_DISTRIBUTION_DENIED",
    "app_store_submission_enabled": "M150_APP_STORE_SUBMISSION_DENIED",
    "testflight_submission_enabled": "M150_TESTFLIGHT_SUBMISSION_DENIED",
    "beta_release_enabled": "M150_BETA_RELEASE_DENIED",
    "release_automation_enabled": "M150_RELEASE_AUTOMATION_DENIED",
    "auth_runtime_enabled": "M150_AUTH_RUNTIME_DENIED",
    "login_enabled": "M150_LOGIN_DENIED",
    "session_cookie_enabled": "M150_SESSION_COOKIE_DENIED",
    "credential_handling_enabled": "M150_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_enabled": "M150_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_enabled": "M150_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_enabled": "M150_EXECUTION_DENIED",
    "tool_execution_enabled": "M150_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M150_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M150_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M150_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M150_NETWORK_ACCESS_DENIED",
    "mobile_sensor_enabled": "M150_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M150_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M150_MODEL_CALL_DENIED",
    "memory_write_enabled": "M150_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M150_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M150_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M150_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M150_DEPENDENCY_DENIED",
    "production_authority_granted": "M150_PRODUCTION_AUTHORITY_DENIED",
}

_M150_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M150_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "release_publication_requested": "M150_RELEASE_PUBLICATION_DENIED",
    "release_tag_requested": "M150_RELEASE_TAG_DENIED",
    "tag_creation_requested": "M150_TAG_CREATION_DENIED",
    "artifact_build_requested": "M150_ARTIFACT_BUILD_DENIED",
    "artifact_upload_requested": "M150_ARTIFACT_UPLOAD_DENIED",
    "artifact_export_requested": "M150_ARTIFACT_EXPORT_DENIED",
    "external_distribution_requested": "M150_EXTERNAL_DISTRIBUTION_DENIED",
    "app_store_submission_requested": "M150_APP_STORE_SUBMISSION_DENIED",
    "testflight_submission_requested": "M150_TESTFLIGHT_SUBMISSION_DENIED",
    "release_automation_requested": "M150_RELEASE_AUTOMATION_DENIED",
    "production_authority_requested": "M150_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_private_content": "M150_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_prompt": "M150_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M150_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M150_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M150_SECRET_DENIED",
    "dependency_requested": "M150_DEPENDENCY_DENIED",
}

_M150_RECORD_DENIALS = {
    "release_publication_started": "M150_RELEASE_PUBLICATION_DENIED",
    "release_tag_created": "M150_RELEASE_TAG_DENIED",
    "tag_creation_performed": "M150_TAG_CREATION_DENIED",
    "artifact_build_performed": "M150_ARTIFACT_BUILD_DENIED",
    "artifact_upload_started": "M150_ARTIFACT_UPLOAD_DENIED",
    "artifact_export_started": "M150_ARTIFACT_EXPORT_DENIED",
    "external_distribution_started": "M150_EXTERNAL_DISTRIBUTION_DENIED",
    "app_store_submission_started": "M150_APP_STORE_SUBMISSION_DENIED",
    "testflight_submission_started": "M150_TESTFLIGHT_SUBMISSION_DENIED",
    "beta_release_enabled": "M150_BETA_RELEASE_DENIED",
    "release_automation_started": "M150_RELEASE_AUTOMATION_DENIED",
    "auth_runtime_started": "M150_AUTH_RUNTIME_DENIED",
    "login_enabled": "M150_LOGIN_DENIED",
    "session_cookie_enabled": "M150_SESSION_COOKIE_DENIED",
    "credential_handling_performed": "M150_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_started": "M150_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_started": "M150_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_performed": "M150_EXECUTION_DENIED",
    "tool_execution_performed": "M150_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M150_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M150_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M150_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M150_NETWORK_ACCESS_DENIED",
    "mobile_sensor_performed": "M150_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M150_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M150_MODEL_CALL_DENIED",
    "memory_write_performed": "M150_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M150_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M150_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M150_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M150_DEPENDENCY_DENIED",
    "production_authority_granted": "M150_PRODUCTION_AUTHORITY_DENIED",
}
