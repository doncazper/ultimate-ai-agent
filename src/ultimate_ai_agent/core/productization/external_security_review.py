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


EXTERNAL_SECURITY_REVIEW_DOCS = [
    "docs/productization/EXTERNAL_SECURITY_REVIEW.md",
    "docs/productization/EXTERNAL_SECURITY_REVIEW_POLICY.md",
    "docs/productization/EXTERNAL_SECURITY_REVIEW_AUTHORITY_BOUNDARY.md",
    "docs/productization/EXTERNAL_SECURITY_REVIEW_RECEIPT_PLAN.md",
    "docs/productization/EXTERNAL_SECURITY_REVIEW_NON_GOALS.md",
    "docs/productization/M148_TO_M149_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 148)
)


class ExternalSecurityReviewStatus(str, Enum):
    readiness_recorded = "readiness_recorded"


class _ExternalSecurityReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class ExternalSecurityReviewPolicy(_ExternalSecurityReviewModel):
    policy_ref: str = "external-security-review-policy:m148"
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    external_security_review_only: bool = True
    disabled_by_default_required: bool = True
    m101_m147_coverage_required: bool = True
    security_review_refs_required: bool = True
    threat_model_refs_required: bool = True
    review_scope_refs_required: bool = True
    evidence_index_refs_required: bool = True
    finding_summary_refs_required: bool = True
    disclosure_review_refs_required: bool = True
    remediation_plan_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_external_vendor_handoff_required: bool = True
    no_security_vendor_handoff_required: bool = True
    no_external_review_automation_required: bool = True
    no_scanner_runtime_required: bool = True
    no_vulnerability_scan_required: bool = True
    no_repository_export_required: bool = True
    no_artifact_export_required: bool = True
    no_issue_export_required: bool = True
    no_security_review_runtime_required: bool = True
    no_auth_runtime_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    m149_future_only: bool = True
    external_vendor_handoff_enabled: bool = False
    security_vendor_handoff_enabled: bool = False
    external_review_automation_enabled: bool = False
    scanner_runtime_enabled: bool = False
    vulnerability_scan_enabled: bool = False
    repository_export_enabled: bool = False
    artifact_export_enabled: bool = False
    issue_export_enabled: bool = False
    security_review_runtime_enabled: bool = False
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
            raise ValueError("M148_SECRET_LIKE_SECURITY_REVIEW_CONTENT_DENIED") from exc
        return self


class ExternalSecurityReviewRequest(_ExternalSecurityReviewModel):
    request_ref: str
    security_review_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    security_review_refs: list[str]
    threat_model_refs: list[str]
    review_scope_refs: list[str]
    evidence_index_refs: list[str]
    finding_summary_refs: list[str]
    disclosure_review_refs: list[str]
    remediation_plan_refs: list[str]
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
    external_security_review_only: bool = True
    disabled_by_default_required: bool = True
    m101_m147_coverage_required: bool = True
    security_review_refs_required: bool = True
    threat_model_refs_required: bool = True
    review_scope_refs_required: bool = True
    evidence_index_refs_required: bool = True
    finding_summary_refs_required: bool = True
    disclosure_review_refs_required: bool = True
    remediation_plan_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_external_vendor_handoff_required: bool = True
    no_security_vendor_handoff_required: bool = True
    no_external_review_automation_required: bool = True
    no_scanner_runtime_required: bool = True
    no_vulnerability_scan_required: bool = True
    no_repository_export_required: bool = True
    no_artifact_export_required: bool = True
    no_issue_export_required: bool = True
    no_security_review_runtime_required: bool = True
    no_auth_runtime_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    external_vendor_handoff_requested: bool = False
    security_vendor_handoff_requested: bool = False
    external_review_automation_requested: bool = False
    scanner_runtime_requested: bool = False
    vulnerability_scan_requested: bool = False
    repository_export_requested: bool = False
    artifact_export_requested: bool = False
    issue_export_requested: bool = False
    security_review_runtime_requested: bool = False
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


class ExternalSecurityReviewRecord(_ExternalSecurityReviewModel):
    record_ref: str
    security_review_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    security_review_refs: list[str]
    threat_model_refs: list[str]
    review_scope_refs: list[str]
    evidence_index_refs: list[str]
    finding_summary_refs: list[str]
    disclosure_review_refs: list[str]
    remediation_plan_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: ExternalSecurityReviewStatus = (
        ExternalSecurityReviewStatus.readiness_recorded
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    external_security_review_only: bool = True
    disabled_by_default: bool = True
    m101_m147_covered: bool = True
    security_reviews_bound: bool = True
    threat_model_bound: bool = True
    review_scopes_bound: bool = True
    evidence_indexes_bound: bool = True
    finding_summaries_bound: bool = True
    disclosure_reviews_bound: bool = True
    remediation_plans_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    no_effect_receipt_required: bool = True
    no_external_vendor_handoff: bool = True
    no_security_vendor_handoff: bool = True
    no_external_review_automation: bool = True
    no_scanner_runtime: bool = True
    no_vulnerability_scan: bool = True
    no_repository_export: bool = True
    no_artifact_export: bool = True
    no_issue_export: bool = True
    no_security_review_runtime: bool = True
    no_auth_runtime: bool = True
    no_backend_route: bool = True
    no_control_center_control: bool = True
    no_dependency: bool = True
    no_production_authority: bool = True
    external_vendor_handoff_started: bool = False
    security_vendor_handoff_started: bool = False
    external_review_automation_started: bool = False
    scanner_runtime_performed: bool = False
    vulnerability_scan_started: bool = False
    repository_export_performed: bool = False
    artifact_export_started: bool = False
    issue_export_started: bool = False
    security_review_runtime_performed: bool = False
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
            raise ValueError("M148_REASON_CODE_REQUIRED")
        return self


def build_external_security_review_record(
    request: ExternalSecurityReviewRequest,
    policy: ExternalSecurityReviewPolicy | None = None,
) -> ExternalSecurityReviewRecord:
    active_policy = validate_external_security_review_policy(
        policy or ExternalSecurityReviewPolicy()
    )
    validated_request = validate_external_security_review_request(request)
    record = ExternalSecurityReviewRecord(
        record_ref=f"external-security-review-record:{_ref_suffix(validated_request.security_review_ref)}",
        security_review_ref=validated_request.security_review_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        security_review_refs=list(
            validated_request.security_review_refs
        ),
        threat_model_refs=list(validated_request.threat_model_refs),
        review_scope_refs=list(validated_request.review_scope_refs),
        evidence_index_refs=list(validated_request.evidence_index_refs),
        finding_summary_refs=list(
            validated_request.finding_summary_refs
        ),
        disclosure_review_refs=list(
            validated_request.disclosure_review_refs
        ),
        remediation_plan_refs=list(validated_request.remediation_plan_refs),
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
        external_security_review_only=active_policy.external_security_review_only,
        disabled_by_default=active_policy.disabled_by_default_required,
        m101_m147_covered=active_policy.m101_m147_coverage_required,
        security_reviews_bound=(
            active_policy.security_review_refs_required
        ),
        threat_model_bound=active_policy.threat_model_refs_required,
        review_scopes_bound=active_policy.review_scope_refs_required,
        evidence_indexes_bound=active_policy.evidence_index_refs_required,
        finding_summaries_bound=(
            active_policy.finding_summary_refs_required
        ),
        disclosure_reviews_bound=(
            active_policy.disclosure_review_refs_required
        ),
        remediation_plans_bound=active_policy.remediation_plan_refs_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_external_vendor_handoff=active_policy.no_external_vendor_handoff_required,
        no_security_vendor_handoff=active_policy.no_security_vendor_handoff_required,
        no_external_review_automation=active_policy.no_external_review_automation_required,
        no_scanner_runtime=active_policy.no_scanner_runtime_required,
        no_vulnerability_scan=active_policy.no_vulnerability_scan_required,
        no_repository_export=active_policy.no_repository_export_required,
        no_artifact_export=(
            active_policy.no_artifact_export_required
        ),
        no_issue_export=active_policy.no_issue_export_required,
        no_security_review_runtime=active_policy.no_security_review_runtime_required,
        no_auth_runtime=active_policy.no_auth_runtime_required,
        no_backend_route=active_policy.no_backend_route_required,
        no_control_center_control=active_policy.no_control_center_control_required,
        no_dependency=active_policy.no_dependency_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M148_EXTERNAL_SECURITY_REVIEW_REVIEW_ONLY",
            "M148_M101_M147_COVERED",
            "M148_DISABLED_BY_DEFAULT",
            "M148_NO_EXTERNAL_VENDOR_HANDOFF",
            "M148_NO_SECURITY_VENDOR_HANDOFF",
            "M148_NO_EXTERNAL_REVIEW_AUTOMATION",
            "M148_NO_SCANNER_RUNTIME",
            "M148_NO_VULNERABILITY_SCAN",
            "M148_NO_REPOSITORY_EXPORT",
            "M148_NO_ARTIFACT_EXPORT",
            "M148_NO_ISSUE_EXPORT",
            "M148_NO_SECURITY_REVIEW_RUNTIME",
            "M148_NO_AUTH_RUNTIME",
            "M148_NO_BACKEND_ROUTE",
            "M148_NO_PRODUCTION_AUTHORITY",
            "M149_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M148 records contract-only external security review refs using "
            "safe security review, threat model, review scope, evidence index, "
            "finding summary, disclosure review, remediation plan, audit, "
            "replay, revocation, kill-switch, and no-effect receipt refs. It "
            "grants no external vendor handoff, security vendor handoff, external review automation, "
            "scanner runtime, vulnerability scan, repository export, "
            "artifact export, issue export, security review runtime, auth runtime, "
            "backend route, Control Center control, dependency, beta release, "
            "or production authority."
        ),
    )
    return validate_external_security_review_record(record)


def validate_external_security_review_policy(
    policy: ExternalSecurityReviewPolicy,
) -> ExternalSecurityReviewPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, ExternalSecurityReviewPolicy):
        raise ValueError("M148_SECRET_LIKE_SECURITY_REVIEW_CONTENT_DENIED")
    validated = ExternalSecurityReviewPolicy.model_validate(payload)
    for field_name, reason in _M148_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M148_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M148_SECRET_LIKE_SECURITY_REVIEW_CONTENT_DENIED") from exc
    return validated


def validate_external_security_review_request(
    request: ExternalSecurityReviewRequest,
) -> ExternalSecurityReviewRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, ExternalSecurityReviewRequest):
        raise ValueError("M148_SECRET_LIKE_SECURITY_REVIEW_CONTENT_DENIED")
    _deny_enabled(_M148_REQUEST_DENIALS, payload)
    validated = ExternalSecurityReviewRequest.model_validate(payload)
    for field_name, reason in _M148_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M148_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M148_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _request_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M148_SECRET_LIKE_SECURITY_REVIEW_CONTENT_DENIED") from exc
    return validated


def validate_external_security_review_record(
    record: ExternalSecurityReviewRecord,
) -> ExternalSecurityReviewRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, ExternalSecurityReviewRecord):
        raise ValueError("M148_SECRET_LIKE_SECURITY_REVIEW_CONTENT_DENIED")
    _deny_enabled(_M148_RECORD_DENIALS, payload)
    validated = ExternalSecurityReviewRecord.model_validate(payload)
    for field_name, reason in _M148_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M148_RECORD_DENIALS, _model_payload(validated))
    if validated.status != ExternalSecurityReviewStatus.readiness_recorded:
        raise ValueError("M148_READINESS_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M148_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _record_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    if "M148_EXTERNAL_SECURITY_REVIEW_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M148_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M148_SECRET_LIKE_SECURITY_REVIEW_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: ExternalSecurityReviewRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.security_review_ref, "security_review_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: ExternalSecurityReviewRecord):
    return [
        (record.record_ref, "record_ref"),
        (record.security_review_ref, "security_review_ref"),
        (record.request_ref, "request_ref"),
        (record.baseline_ref, "baseline_ref"),
        (record.actor_ref, "actor_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _request_ref_lists(request: ExternalSecurityReviewRequest):
    return [
        (
            request.security_review_refs,
            "security_review_ref",
            "M148_SECURITY_REVIEW_REF_REQUIRED",
        ),
        (
            request.threat_model_refs,
            "threat_model_ref",
            "M148_THREAT_MODEL_REF_REQUIRED",
        ),
        (
            request.review_scope_refs,
            "review_scope_ref",
            "M148_REVIEW_SCOPE_REF_REQUIRED",
        ),
        (
            request.evidence_index_refs,
            "evidence_index_ref",
            "M148_EVIDENCE_INDEX_REF_REQUIRED",
        ),
        (
            request.finding_summary_refs,
            "finding_summary_ref",
            "M148_FINDING_SUMMARY_REF_REQUIRED",
        ),
        (
            request.disclosure_review_refs,
            "disclosure_review_ref",
            "M148_DISCLOSURE_REVIEW_REF_REQUIRED",
        ),
        (
            request.remediation_plan_refs,
            "remediation_plan_ref",
            "M148_REMEDIATION_PLAN_REF_REQUIRED",
        ),
    ]


def _record_ref_lists(record: ExternalSecurityReviewRecord):
    return [
        (
            record.security_review_refs,
            "security_review_ref",
            "M148_SECURITY_REVIEW_REF_REQUIRED",
        ),
        (
            record.threat_model_refs,
            "threat_model_ref",
            "M148_THREAT_MODEL_REF_REQUIRED",
        ),
        (
            record.review_scope_refs,
            "review_scope_ref",
            "M148_REVIEW_SCOPE_REF_REQUIRED",
        ),
        (
            record.evidence_index_refs,
            "evidence_index_ref",
            "M148_EVIDENCE_INDEX_REF_REQUIRED",
        ),
        (
            record.finding_summary_refs,
            "finding_summary_ref",
            "M148_FINDING_SUMMARY_REF_REQUIRED",
        ),
        (
            record.disclosure_review_refs,
            "disclosure_review_ref",
            "M148_DISCLOSURE_REVIEW_REF_REQUIRED",
        ),
        (
            record.remediation_plan_refs,
            "remediation_plan_ref",
            "M148_REMEDIATION_PLAN_REF_REQUIRED",
        ),
    ]


def _validate_accepted_checkpoints(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M148_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M148_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M148_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M148_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M148_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M148_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M148_REQUIRED_TRUE = [
    ("contract_only", "M148_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M148_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M148_DETERMINISTIC_REQUIRED"),
    ("local_only", "M148_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M148_SAFE_REFS_ONLY_REQUIRED"),
    ("external_security_review_only", "M148_EXTERNAL_SECURITY_REVIEW_ONLY_REQUIRED"),
    ("disabled_by_default_required", "M148_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m147_coverage_required", "M148_M101_M147_COVERAGE_REQUIRED"),
    (
        "security_review_refs_required",
        "M148_SECURITY_REVIEW_REF_REQUIRED",
    ),
    ("threat_model_refs_required", "M148_THREAT_MODEL_REF_REQUIRED"),
    ("review_scope_refs_required", "M148_REVIEW_SCOPE_REF_REQUIRED"),
    ("evidence_index_refs_required", "M148_EVIDENCE_INDEX_REF_REQUIRED"),
    (
        "finding_summary_refs_required",
        "M148_FINDING_SUMMARY_REF_REQUIRED",
    ),
    (
        "disclosure_review_refs_required",
        "M148_DISCLOSURE_REVIEW_REF_REQUIRED",
    ),
    ("remediation_plan_refs_required", "M148_REMEDIATION_PLAN_REF_REQUIRED"),
    ("audit_replay_required", "M148_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M148_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M148_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_external_vendor_handoff_required", "M148_EXTERNAL_VENDOR_HANDOFF_DENIED"),
    ("no_security_vendor_handoff_required", "M148_SECURITY_VENDOR_HANDOFF_DENIED"),
    ("no_external_review_automation_required", "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED"),
    ("no_scanner_runtime_required", "M148_SCANNER_RUNTIME_DENIED"),
    ("no_vulnerability_scan_required", "M148_VULNERABILITY_SCAN_DENIED"),
    ("no_repository_export_required", "M148_REPOSITORY_EXPORT_DENIED"),
    ("no_artifact_export_required", "M148_ARTIFACT_EXPORT_DENIED"),
    ("no_issue_export_required", "M148_ISSUE_EXPORT_DENIED"),
    ("no_security_review_runtime_required", "M148_SECURITY_REVIEW_RUNTIME_DENIED"),
    ("no_auth_runtime_required", "M148_AUTH_RUNTIME_DENIED"),
    ("no_backend_route_required", "M148_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control_required", "M148_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency_required", "M148_DEPENDENCY_DENIED"),
    ("no_production_authority_required", "M148_PRODUCTION_AUTHORITY_DENIED"),
]

_M148_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M148_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M148_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M148_DETERMINISTIC_REQUIRED"),
    ("local_only", "M148_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M148_SAFE_REFS_ONLY_REQUIRED"),
    ("external_security_review_only", "M148_EXTERNAL_SECURITY_REVIEW_ONLY_REQUIRED"),
    ("disabled_by_default", "M148_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m147_covered", "M148_M101_M147_COVERAGE_REQUIRED"),
    ("security_reviews_bound", "M148_SECURITY_REVIEW_REF_REQUIRED"),
    ("threat_model_bound", "M148_THREAT_MODEL_REF_REQUIRED"),
    ("review_scopes_bound", "M148_REVIEW_SCOPE_REF_REQUIRED"),
    ("evidence_indexes_bound", "M148_EVIDENCE_INDEX_REF_REQUIRED"),
    ("finding_summaries_bound", "M148_FINDING_SUMMARY_REF_REQUIRED"),
    ("disclosure_reviews_bound", "M148_DISCLOSURE_REVIEW_REF_REQUIRED"),
    ("remediation_plans_bound", "M148_REMEDIATION_PLAN_REF_REQUIRED"),
    ("audit_replay_bound", "M148_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M148_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M148_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_external_vendor_handoff", "M148_EXTERNAL_VENDOR_HANDOFF_DENIED"),
    ("no_security_vendor_handoff", "M148_SECURITY_VENDOR_HANDOFF_DENIED"),
    ("no_external_review_automation", "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED"),
    ("no_scanner_runtime", "M148_SCANNER_RUNTIME_DENIED"),
    ("no_vulnerability_scan", "M148_VULNERABILITY_SCAN_DENIED"),
    ("no_repository_export", "M148_REPOSITORY_EXPORT_DENIED"),
    ("no_artifact_export", "M148_ARTIFACT_EXPORT_DENIED"),
    ("no_issue_export", "M148_ISSUE_EXPORT_DENIED"),
    ("no_security_review_runtime", "M148_SECURITY_REVIEW_RUNTIME_DENIED"),
    ("no_auth_runtime", "M148_AUTH_RUNTIME_DENIED"),
    ("no_backend_route", "M148_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control", "M148_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency", "M148_DEPENDENCY_DENIED"),
    ("no_production_authority", "M148_PRODUCTION_AUTHORITY_DENIED"),
]

_M148_POLICY_DENIALS = {
    "external_vendor_handoff_enabled": "M148_EXTERNAL_VENDOR_HANDOFF_DENIED",
    "security_vendor_handoff_enabled": "M148_SECURITY_VENDOR_HANDOFF_DENIED",
    "external_review_automation_enabled": "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED",
    "scanner_runtime_enabled": "M148_SCANNER_RUNTIME_DENIED",
    "vulnerability_scan_enabled": "M148_VULNERABILITY_SCAN_DENIED",
    "repository_export_enabled": "M148_REPOSITORY_EXPORT_DENIED",
    "artifact_export_enabled": "M148_ARTIFACT_EXPORT_DENIED",
    "issue_export_enabled": "M148_ISSUE_EXPORT_DENIED",
    "security_review_runtime_enabled": "M148_SECURITY_REVIEW_RUNTIME_DENIED",
    "auth_runtime_enabled": "M148_AUTH_RUNTIME_DENIED",
    "login_enabled": "M148_LOGIN_DENIED",
    "session_cookie_enabled": "M148_SESSION_COOKIE_DENIED",
    "credential_handling_enabled": "M148_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_enabled": "M148_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_enabled": "M148_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_enabled": "M148_EXECUTION_DENIED",
    "tool_execution_enabled": "M148_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M148_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M148_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M148_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M148_NETWORK_ACCESS_DENIED",
    "mobile_sensor_enabled": "M148_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M148_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M148_MODEL_CALL_DENIED",
    "memory_write_enabled": "M148_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M148_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M148_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M148_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M148_DEPENDENCY_DENIED",
    "beta_release_enabled": "M148_BETA_RELEASE_DENIED",
    "production_authority_granted": "M148_PRODUCTION_AUTHORITY_DENIED",
}

_M148_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M148_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "external_vendor_handoff_requested": "M148_EXTERNAL_VENDOR_HANDOFF_DENIED",
    "security_vendor_handoff_requested": "M148_SECURITY_VENDOR_HANDOFF_DENIED",
    "external_review_automation_requested": "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED",
    "scanner_runtime_requested": "M148_SCANNER_RUNTIME_DENIED",
    "vulnerability_scan_requested": "M148_VULNERABILITY_SCAN_DENIED",
    "repository_export_requested": "M148_REPOSITORY_EXPORT_DENIED",
    "artifact_export_requested": "M148_ARTIFACT_EXPORT_DENIED",
    "issue_export_requested": "M148_ISSUE_EXPORT_DENIED",
    "security_review_runtime_requested": "M148_SECURITY_REVIEW_RUNTIME_DENIED",
    "auth_runtime_requested": "M148_AUTH_RUNTIME_DENIED",
    "login_requested": "M148_LOGIN_DENIED",
    "session_cookie_requested": "M148_SESSION_COOKIE_DENIED",
    "credential_handling_requested": "M148_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_requested": "M148_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_requested": "M148_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "production_authority_requested": "M148_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_private_content": "M148_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_prompt": "M148_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M148_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M148_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M148_SECRET_DENIED",
    "dependency_requested": "M148_DEPENDENCY_DENIED",
}

_M148_RECORD_DENIALS = {
    "external_vendor_handoff_started": "M148_EXTERNAL_VENDOR_HANDOFF_DENIED",
    "security_vendor_handoff_started": "M148_SECURITY_VENDOR_HANDOFF_DENIED",
    "external_review_automation_started": "M148_EXTERNAL_REVIEW_AUTOMATION_DENIED",
    "scanner_runtime_performed": "M148_SCANNER_RUNTIME_DENIED",
    "vulnerability_scan_started": "M148_VULNERABILITY_SCAN_DENIED",
    "repository_export_performed": "M148_REPOSITORY_EXPORT_DENIED",
    "artifact_export_started": "M148_ARTIFACT_EXPORT_DENIED",
    "issue_export_started": "M148_ISSUE_EXPORT_DENIED",
    "security_review_runtime_performed": "M148_SECURITY_REVIEW_RUNTIME_DENIED",
    "auth_runtime_started": "M148_AUTH_RUNTIME_DENIED",
    "login_enabled": "M148_LOGIN_DENIED",
    "session_cookie_enabled": "M148_SESSION_COOKIE_DENIED",
    "credential_handling_performed": "M148_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_started": "M148_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_started": "M148_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_performed": "M148_EXECUTION_DENIED",
    "tool_execution_performed": "M148_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M148_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M148_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M148_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M148_NETWORK_ACCESS_DENIED",
    "mobile_sensor_performed": "M148_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M148_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M148_MODEL_CALL_DENIED",
    "memory_write_performed": "M148_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M148_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M148_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M148_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M148_DEPENDENCY_DENIED",
    "beta_release_enabled": "M148_BETA_RELEASE_DENIED",
    "production_authority_granted": "M148_PRODUCTION_AUTHORITY_DENIED",
}
