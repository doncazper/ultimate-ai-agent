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


PUBLIC_DOCS_WIKI_READINESS_DOCS = [
    "docs/productization/PUBLIC_DOCS_WIKI_READINESS.md",
    "docs/productization/PUBLIC_DOCS_WIKI_READINESS_POLICY.md",
    "docs/productization/PUBLIC_DOCS_WIKI_READINESS_AUTHORITY_BOUNDARY.md",
    "docs/productization/PUBLIC_DOCS_WIKI_READINESS_RECEIPT_PLAN.md",
    "docs/productization/PUBLIC_DOCS_WIKI_READINESS_NON_GOALS.md",
    "docs/productization/M147_TO_M148_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 147)
)


class PublicDocsWikiReadinessStatus(str, Enum):
    readiness_recorded = "readiness_recorded"


class _PublicDocsWikiReadinessModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class PublicDocsWikiReadinessPolicy(_PublicDocsWikiReadinessModel):
    policy_ref: str = "public-docs-wiki-readiness-policy:m147"
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    docs_readiness_only: bool = True
    disabled_by_default_required: bool = True
    m101_m146_coverage_required: bool = True
    public_doc_refs_required: bool = True
    wiki_readiness_refs_required: bool = True
    docs_index_refs_required: bool = True
    canonical_map_refs_required: bool = True
    release_note_refs_required: bool = True
    disclosure_review_refs_required: bool = True
    publishing_checklist_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_public_publish_required: bool = True
    no_wiki_publish_required: bool = True
    no_wiki_automation_required: bool = True
    no_github_wiki_runtime_required: bool = True
    no_docs_site_deploy_required: bool = True
    no_external_distribution_required: bool = True
    no_artifact_upload_required: bool = True
    no_release_publish_required: bool = True
    no_docs_runtime_required: bool = True
    no_auth_runtime_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    m148_future_only: bool = True
    public_publish_enabled: bool = False
    wiki_publish_enabled: bool = False
    wiki_automation_enabled: bool = False
    github_wiki_runtime_enabled: bool = False
    docs_site_deploy_enabled: bool = False
    external_distribution_enabled: bool = False
    artifact_upload_enabled: bool = False
    release_publish_enabled: bool = False
    docs_runtime_enabled: bool = False
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
            raise ValueError("M147_SECRET_LIKE_PUBLIC_DOCS_CONTENT_DENIED") from exc
        return self


class PublicDocsWikiReadinessRequest(_PublicDocsWikiReadinessModel):
    request_ref: str
    public_doc_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    public_doc_refs: list[str]
    wiki_readiness_refs: list[str]
    docs_index_refs: list[str]
    canonical_map_refs: list[str]
    release_note_refs: list[str]
    disclosure_review_refs: list[str]
    publishing_checklist_refs: list[str]
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
    docs_readiness_only: bool = True
    disabled_by_default_required: bool = True
    m101_m146_coverage_required: bool = True
    public_doc_refs_required: bool = True
    wiki_readiness_refs_required: bool = True
    docs_index_refs_required: bool = True
    canonical_map_refs_required: bool = True
    release_note_refs_required: bool = True
    disclosure_review_refs_required: bool = True
    publishing_checklist_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_public_publish_required: bool = True
    no_wiki_publish_required: bool = True
    no_wiki_automation_required: bool = True
    no_github_wiki_runtime_required: bool = True
    no_docs_site_deploy_required: bool = True
    no_external_distribution_required: bool = True
    no_artifact_upload_required: bool = True
    no_release_publish_required: bool = True
    no_docs_runtime_required: bool = True
    no_auth_runtime_required: bool = True
    no_backend_route_required: bool = True
    no_control_center_control_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    public_publish_requested: bool = False
    wiki_publish_requested: bool = False
    wiki_automation_requested: bool = False
    github_wiki_runtime_requested: bool = False
    docs_site_deploy_requested: bool = False
    external_distribution_requested: bool = False
    artifact_upload_requested: bool = False
    release_publish_requested: bool = False
    docs_runtime_requested: bool = False
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


class PublicDocsWikiReadinessRecord(_PublicDocsWikiReadinessModel):
    record_ref: str
    public_doc_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    public_doc_refs: list[str]
    wiki_readiness_refs: list[str]
    docs_index_refs: list[str]
    canonical_map_refs: list[str]
    release_note_refs: list[str]
    disclosure_review_refs: list[str]
    publishing_checklist_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: PublicDocsWikiReadinessStatus = (
        PublicDocsWikiReadinessStatus.readiness_recorded
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    docs_readiness_only: bool = True
    disabled_by_default: bool = True
    m101_m146_covered: bool = True
    public_docs_bound: bool = True
    wiki_readiness_bound: bool = True
    docs_indexes_bound: bool = True
    canonical_maps_bound: bool = True
    release_notes_bound: bool = True
    disclosure_reviews_bound: bool = True
    publishing_checklists_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    no_effect_receipt_required: bool = True
    no_public_publish: bool = True
    no_wiki_publish: bool = True
    no_wiki_automation: bool = True
    no_github_wiki_runtime: bool = True
    no_docs_site_deploy: bool = True
    no_external_distribution: bool = True
    no_artifact_upload: bool = True
    no_release_publish: bool = True
    no_docs_runtime: bool = True
    no_auth_runtime: bool = True
    no_backend_route: bool = True
    no_control_center_control: bool = True
    no_dependency: bool = True
    no_production_authority: bool = True
    public_publish_started: bool = False
    wiki_publish_started: bool = False
    wiki_automation_started: bool = False
    github_wiki_runtime_performed: bool = False
    docs_site_deploy_started: bool = False
    external_distribution_performed: bool = False
    artifact_upload_started: bool = False
    release_publish_started: bool = False
    docs_runtime_performed: bool = False
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
            raise ValueError("M147_REASON_CODE_REQUIRED")
        return self


def build_public_docs_wiki_readiness_record(
    request: PublicDocsWikiReadinessRequest,
    policy: PublicDocsWikiReadinessPolicy | None = None,
) -> PublicDocsWikiReadinessRecord:
    active_policy = validate_public_docs_wiki_readiness_policy(
        policy or PublicDocsWikiReadinessPolicy()
    )
    validated_request = validate_public_docs_wiki_readiness_request(request)
    record = PublicDocsWikiReadinessRecord(
        record_ref=f"public-docs-wiki-readiness-record:{_ref_suffix(validated_request.public_doc_ref)}",
        public_doc_ref=validated_request.public_doc_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        public_doc_refs=list(
            validated_request.public_doc_refs
        ),
        wiki_readiness_refs=list(validated_request.wiki_readiness_refs),
        docs_index_refs=list(validated_request.docs_index_refs),
        canonical_map_refs=list(validated_request.canonical_map_refs),
        release_note_refs=list(
            validated_request.release_note_refs
        ),
        disclosure_review_refs=list(
            validated_request.disclosure_review_refs
        ),
        publishing_checklist_refs=list(validated_request.publishing_checklist_refs),
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
        docs_readiness_only=active_policy.docs_readiness_only,
        disabled_by_default=active_policy.disabled_by_default_required,
        m101_m146_covered=active_policy.m101_m146_coverage_required,
        public_docs_bound=(
            active_policy.public_doc_refs_required
        ),
        wiki_readiness_bound=active_policy.wiki_readiness_refs_required,
        docs_indexes_bound=active_policy.docs_index_refs_required,
        canonical_maps_bound=active_policy.canonical_map_refs_required,
        release_notes_bound=(
            active_policy.release_note_refs_required
        ),
        disclosure_reviews_bound=(
            active_policy.disclosure_review_refs_required
        ),
        publishing_checklists_bound=active_policy.publishing_checklist_refs_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_public_publish=active_policy.no_public_publish_required,
        no_wiki_publish=active_policy.no_wiki_publish_required,
        no_wiki_automation=active_policy.no_wiki_automation_required,
        no_github_wiki_runtime=active_policy.no_github_wiki_runtime_required,
        no_docs_site_deploy=active_policy.no_docs_site_deploy_required,
        no_external_distribution=active_policy.no_external_distribution_required,
        no_artifact_upload=(
            active_policy.no_artifact_upload_required
        ),
        no_release_publish=active_policy.no_release_publish_required,
        no_docs_runtime=active_policy.no_docs_runtime_required,
        no_auth_runtime=active_policy.no_auth_runtime_required,
        no_backend_route=active_policy.no_backend_route_required,
        no_control_center_control=active_policy.no_control_center_control_required,
        no_dependency=active_policy.no_dependency_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M147_PUBLIC_DOCS_WIKI_READINESS_REVIEW_ONLY",
            "M147_M101_M146_COVERED",
            "M147_DISABLED_BY_DEFAULT",
            "M147_NO_PUBLIC_PUBLISH",
            "M147_NO_WIKI_PUBLISH",
            "M147_NO_WIKI_AUTOMATION",
            "M147_NO_GITHUB_WIKI_RUNTIME",
            "M147_NO_DOCS_SITE_DEPLOY",
            "M147_NO_EXTERNAL_DISTRIBUTION",
            "M147_NO_ARTIFACT_UPLOAD",
            "M147_NO_RELEASE_PUBLISH",
            "M147_NO_DOCS_RUNTIME",
            "M147_NO_AUTH_RUNTIME",
            "M147_NO_BACKEND_ROUTE",
            "M147_NO_PRODUCTION_AUTHORITY",
            "M148_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M147 records contract-only public docs + wiki readiness refs using "
            "safe public doc, wiki readiness, docs index, canonical map, "
            "release note, disclosure review, publishing checklist, audit, "
            "replay, revocation, kill-switch, and no-effect receipt refs. It "
            "grants no public publishing, wiki publishing, wiki automation, "
            "GitHub wiki runtime, docs-site deploy, external distribution, "
            "artifact upload, release publishing, docs runtime, auth runtime, "
            "backend route, Control Center control, dependency, beta release, "
            "or production authority."
        ),
    )
    return validate_public_docs_wiki_readiness_record(record)


def validate_public_docs_wiki_readiness_policy(
    policy: PublicDocsWikiReadinessPolicy,
) -> PublicDocsWikiReadinessPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, PublicDocsWikiReadinessPolicy):
        raise ValueError("M147_SECRET_LIKE_PUBLIC_DOCS_CONTENT_DENIED")
    validated = PublicDocsWikiReadinessPolicy.model_validate(payload)
    for field_name, reason in _M147_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M147_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M147_SECRET_LIKE_PUBLIC_DOCS_CONTENT_DENIED") from exc
    return validated


def validate_public_docs_wiki_readiness_request(
    request: PublicDocsWikiReadinessRequest,
) -> PublicDocsWikiReadinessRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, PublicDocsWikiReadinessRequest):
        raise ValueError("M147_SECRET_LIKE_PUBLIC_DOCS_CONTENT_DENIED")
    _deny_enabled(_M147_REQUEST_DENIALS, payload)
    validated = PublicDocsWikiReadinessRequest.model_validate(payload)
    for field_name, reason in _M147_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M147_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M147_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _request_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M147_SECRET_LIKE_PUBLIC_DOCS_CONTENT_DENIED") from exc
    return validated


def validate_public_docs_wiki_readiness_record(
    record: PublicDocsWikiReadinessRecord,
) -> PublicDocsWikiReadinessRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, PublicDocsWikiReadinessRecord):
        raise ValueError("M147_SECRET_LIKE_PUBLIC_DOCS_CONTENT_DENIED")
    _deny_enabled(_M147_RECORD_DENIALS, payload)
    validated = PublicDocsWikiReadinessRecord.model_validate(payload)
    for field_name, reason in _M147_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M147_RECORD_DENIALS, _model_payload(validated))
    if validated.status != PublicDocsWikiReadinessStatus.readiness_recorded:
        raise ValueError("M147_READINESS_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M147_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _record_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    if "M147_PUBLIC_DOCS_WIKI_READINESS_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M147_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M147_SECRET_LIKE_PUBLIC_DOCS_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: PublicDocsWikiReadinessRequest) -> list[Any]:
    return [
        (request.request_ref, "request_ref"),
        (request.public_doc_ref, "public_doc_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: PublicDocsWikiReadinessRecord) -> list[Any]:
    return [
        (record.record_ref, "record_ref"),
        (record.public_doc_ref, "public_doc_ref"),
        (record.request_ref, "request_ref"),
        (record.baseline_ref, "baseline_ref"),
        (record.actor_ref, "actor_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _request_ref_lists(request: PublicDocsWikiReadinessRequest) -> list[Any]:
    return [
        (
            request.public_doc_refs,
            "public_doc_ref",
            "M147_PUBLIC_DOC_REF_REQUIRED",
        ),
        (
            request.wiki_readiness_refs,
            "wiki_readiness_ref",
            "M147_WIKI_READINESS_REF_REQUIRED",
        ),
        (
            request.docs_index_refs,
            "docs_index_ref",
            "M147_DOCS_INDEX_REF_REQUIRED",
        ),
        (
            request.canonical_map_refs,
            "canonical_map_ref",
            "M147_CANONICAL_MAP_REF_REQUIRED",
        ),
        (
            request.release_note_refs,
            "release_note_ref",
            "M147_RELEASE_NOTE_REF_REQUIRED",
        ),
        (
            request.disclosure_review_refs,
            "disclosure_review_ref",
            "M147_DISCLOSURE_REVIEW_REF_REQUIRED",
        ),
        (
            request.publishing_checklist_refs,
            "publishing_checklist_ref",
            "M147_PUBLISHING_CHECKLIST_REF_REQUIRED",
        ),
    ]


def _record_ref_lists(record: PublicDocsWikiReadinessRecord) -> list[Any]:
    return [
        (
            record.public_doc_refs,
            "public_doc_ref",
            "M147_PUBLIC_DOC_REF_REQUIRED",
        ),
        (
            record.wiki_readiness_refs,
            "wiki_readiness_ref",
            "M147_WIKI_READINESS_REF_REQUIRED",
        ),
        (
            record.docs_index_refs,
            "docs_index_ref",
            "M147_DOCS_INDEX_REF_REQUIRED",
        ),
        (
            record.canonical_map_refs,
            "canonical_map_ref",
            "M147_CANONICAL_MAP_REF_REQUIRED",
        ),
        (
            record.release_note_refs,
            "release_note_ref",
            "M147_RELEASE_NOTE_REF_REQUIRED",
        ),
        (
            record.disclosure_review_refs,
            "disclosure_review_ref",
            "M147_DISCLOSURE_REVIEW_REF_REQUIRED",
        ),
        (
            record.publishing_checklist_refs,
            "publishing_checklist_ref",
            "M147_PUBLISHING_CHECKLIST_REF_REQUIRED",
        ),
    ]


def _validate_accepted_checkpoints(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M147_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M147_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M147_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M147_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M147_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M147_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M147_REQUIRED_TRUE = [
    ("contract_only", "M147_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M147_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M147_DETERMINISTIC_REQUIRED"),
    ("local_only", "M147_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M147_SAFE_REFS_ONLY_REQUIRED"),
    ("docs_readiness_only", "M147_DOCS_READINESS_ONLY_REQUIRED"),
    ("disabled_by_default_required", "M147_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m146_coverage_required", "M147_M101_M146_COVERAGE_REQUIRED"),
    (
        "public_doc_refs_required",
        "M147_PUBLIC_DOC_REF_REQUIRED",
    ),
    ("wiki_readiness_refs_required", "M147_WIKI_READINESS_REF_REQUIRED"),
    ("docs_index_refs_required", "M147_DOCS_INDEX_REF_REQUIRED"),
    ("canonical_map_refs_required", "M147_CANONICAL_MAP_REF_REQUIRED"),
    (
        "release_note_refs_required",
        "M147_RELEASE_NOTE_REF_REQUIRED",
    ),
    (
        "disclosure_review_refs_required",
        "M147_DISCLOSURE_REVIEW_REF_REQUIRED",
    ),
    ("publishing_checklist_refs_required", "M147_PUBLISHING_CHECKLIST_REF_REQUIRED"),
    ("audit_replay_required", "M147_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M147_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M147_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_public_publish_required", "M147_PUBLIC_PUBLISH_DENIED"),
    ("no_wiki_publish_required", "M147_WIKI_PUBLISH_DENIED"),
    ("no_wiki_automation_required", "M147_WIKI_AUTOMATION_DENIED"),
    ("no_github_wiki_runtime_required", "M147_GITHUB_WIKI_RUNTIME_DENIED"),
    ("no_docs_site_deploy_required", "M147_DOCS_SITE_DEPLOY_DENIED"),
    ("no_external_distribution_required", "M147_EXTERNAL_DISTRIBUTION_DENIED"),
    ("no_artifact_upload_required", "M147_ARTIFACT_UPLOAD_DENIED"),
    ("no_release_publish_required", "M147_RELEASE_PUBLISH_DENIED"),
    ("no_docs_runtime_required", "M147_DOCS_RUNTIME_DENIED"),
    ("no_auth_runtime_required", "M147_AUTH_RUNTIME_DENIED"),
    ("no_backend_route_required", "M147_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control_required", "M147_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency_required", "M147_DEPENDENCY_DENIED"),
    ("no_production_authority_required", "M147_PRODUCTION_AUTHORITY_DENIED"),
]

_M147_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M147_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M147_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M147_DETERMINISTIC_REQUIRED"),
    ("local_only", "M147_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M147_SAFE_REFS_ONLY_REQUIRED"),
    ("docs_readiness_only", "M147_DOCS_READINESS_ONLY_REQUIRED"),
    ("disabled_by_default", "M147_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m146_covered", "M147_M101_M146_COVERAGE_REQUIRED"),
    ("public_docs_bound", "M147_PUBLIC_DOC_REF_REQUIRED"),
    ("wiki_readiness_bound", "M147_WIKI_READINESS_REF_REQUIRED"),
    ("docs_indexes_bound", "M147_DOCS_INDEX_REF_REQUIRED"),
    ("canonical_maps_bound", "M147_CANONICAL_MAP_REF_REQUIRED"),
    ("release_notes_bound", "M147_RELEASE_NOTE_REF_REQUIRED"),
    ("disclosure_reviews_bound", "M147_DISCLOSURE_REVIEW_REF_REQUIRED"),
    ("publishing_checklists_bound", "M147_PUBLISHING_CHECKLIST_REF_REQUIRED"),
    ("audit_replay_bound", "M147_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M147_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M147_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_public_publish", "M147_PUBLIC_PUBLISH_DENIED"),
    ("no_wiki_publish", "M147_WIKI_PUBLISH_DENIED"),
    ("no_wiki_automation", "M147_WIKI_AUTOMATION_DENIED"),
    ("no_github_wiki_runtime", "M147_GITHUB_WIKI_RUNTIME_DENIED"),
    ("no_docs_site_deploy", "M147_DOCS_SITE_DEPLOY_DENIED"),
    ("no_external_distribution", "M147_EXTERNAL_DISTRIBUTION_DENIED"),
    ("no_artifact_upload", "M147_ARTIFACT_UPLOAD_DENIED"),
    ("no_release_publish", "M147_RELEASE_PUBLISH_DENIED"),
    ("no_docs_runtime", "M147_DOCS_RUNTIME_DENIED"),
    ("no_auth_runtime", "M147_AUTH_RUNTIME_DENIED"),
    ("no_backend_route", "M147_BACKEND_ROUTE_DENIED"),
    ("no_control_center_control", "M147_CONTROL_CENTER_CONTROL_DENIED"),
    ("no_dependency", "M147_DEPENDENCY_DENIED"),
    ("no_production_authority", "M147_PRODUCTION_AUTHORITY_DENIED"),
]

_M147_POLICY_DENIALS = {
    "public_publish_enabled": "M147_PUBLIC_PUBLISH_DENIED",
    "wiki_publish_enabled": "M147_WIKI_PUBLISH_DENIED",
    "wiki_automation_enabled": "M147_WIKI_AUTOMATION_DENIED",
    "github_wiki_runtime_enabled": "M147_GITHUB_WIKI_RUNTIME_DENIED",
    "docs_site_deploy_enabled": "M147_DOCS_SITE_DEPLOY_DENIED",
    "external_distribution_enabled": "M147_EXTERNAL_DISTRIBUTION_DENIED",
    "artifact_upload_enabled": "M147_ARTIFACT_UPLOAD_DENIED",
    "release_publish_enabled": "M147_RELEASE_PUBLISH_DENIED",
    "docs_runtime_enabled": "M147_DOCS_RUNTIME_DENIED",
    "auth_runtime_enabled": "M147_AUTH_RUNTIME_DENIED",
    "login_enabled": "M147_LOGIN_DENIED",
    "session_cookie_enabled": "M147_SESSION_COOKIE_DENIED",
    "credential_handling_enabled": "M147_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_enabled": "M147_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_enabled": "M147_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_enabled": "M147_EXECUTION_DENIED",
    "tool_execution_enabled": "M147_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M147_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M147_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M147_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M147_NETWORK_ACCESS_DENIED",
    "mobile_sensor_enabled": "M147_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M147_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M147_MODEL_CALL_DENIED",
    "memory_write_enabled": "M147_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M147_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M147_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M147_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M147_DEPENDENCY_DENIED",
    "beta_release_enabled": "M147_BETA_RELEASE_DENIED",
    "production_authority_granted": "M147_PRODUCTION_AUTHORITY_DENIED",
}

_M147_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M147_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "public_publish_requested": "M147_PUBLIC_PUBLISH_DENIED",
    "wiki_publish_requested": "M147_WIKI_PUBLISH_DENIED",
    "wiki_automation_requested": "M147_WIKI_AUTOMATION_DENIED",
    "github_wiki_runtime_requested": "M147_GITHUB_WIKI_RUNTIME_DENIED",
    "docs_site_deploy_requested": "M147_DOCS_SITE_DEPLOY_DENIED",
    "external_distribution_requested": "M147_EXTERNAL_DISTRIBUTION_DENIED",
    "artifact_upload_requested": "M147_ARTIFACT_UPLOAD_DENIED",
    "release_publish_requested": "M147_RELEASE_PUBLISH_DENIED",
    "docs_runtime_requested": "M147_DOCS_RUNTIME_DENIED",
    "auth_runtime_requested": "M147_AUTH_RUNTIME_DENIED",
    "login_requested": "M147_LOGIN_DENIED",
    "session_cookie_requested": "M147_SESSION_COOKIE_DENIED",
    "credential_handling_requested": "M147_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_requested": "M147_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_requested": "M147_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "production_authority_requested": "M147_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_private_content": "M147_RAW_PRIVATE_CONTENT_DENIED",
    "contains_raw_prompt": "M147_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M147_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M147_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M147_SECRET_DENIED",
    "dependency_requested": "M147_DEPENDENCY_DENIED",
}

_M147_RECORD_DENIALS = {
    "public_publish_started": "M147_PUBLIC_PUBLISH_DENIED",
    "wiki_publish_started": "M147_WIKI_PUBLISH_DENIED",
    "wiki_automation_started": "M147_WIKI_AUTOMATION_DENIED",
    "github_wiki_runtime_performed": "M147_GITHUB_WIKI_RUNTIME_DENIED",
    "docs_site_deploy_started": "M147_DOCS_SITE_DEPLOY_DENIED",
    "external_distribution_performed": "M147_EXTERNAL_DISTRIBUTION_DENIED",
    "artifact_upload_started": "M147_ARTIFACT_UPLOAD_DENIED",
    "release_publish_started": "M147_RELEASE_PUBLISH_DENIED",
    "docs_runtime_performed": "M147_DOCS_RUNTIME_DENIED",
    "auth_runtime_started": "M147_AUTH_RUNTIME_DENIED",
    "login_enabled": "M147_LOGIN_DENIED",
    "session_cookie_enabled": "M147_SESSION_COOKIE_DENIED",
    "credential_handling_performed": "M147_CREDENTIAL_HANDLING_DENIED",
    "connector_runtime_started": "M147_CONNECTOR_RUNTIME_DENIED",
    "plugin_marketplace_runtime_started": "M147_PLUGIN_MARKETPLACE_RUNTIME_DENIED",
    "execution_performed": "M147_EXECUTION_DENIED",
    "tool_execution_performed": "M147_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M147_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M147_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M147_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M147_NETWORK_ACCESS_DENIED",
    "mobile_sensor_performed": "M147_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M147_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M147_MODEL_CALL_DENIED",
    "memory_write_performed": "M147_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M147_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M147_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M147_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M147_DEPENDENCY_DENIED",
    "beta_release_enabled": "M147_BETA_RELEASE_DENIED",
    "production_authority_granted": "M147_PRODUCTION_AUTHORITY_DENIED",
}
