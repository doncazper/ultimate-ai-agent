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


PLUGIN_MARKETPLACE_POLICY_DRAFT_DOCS = [
    "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT.md",
    "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_POLICY.md",
    "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_AUTHORITY_BOUNDARY.md",
    "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_RECEIPT_PLAN.md",
    "docs/productization/PLUGIN_MARKETPLACE_POLICY_DRAFT_NON_GOALS.md",
    "docs/productization/M144_TO_M145_BOUNDARY.md",
    "docs/roadmap/M101_M150_CAPABILITY_CHARTERS.md",
]
REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS = tuple(
    f"checkpoint:m{index}" for index in range(101, 144)
)


class PluginMarketplacePolicyDraftStatus(str, Enum):
    policy_draft_recorded = "policy_draft_recorded"


class _PluginMarketplacePolicyDraftModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class PluginMarketplacePolicyDraftPolicy(_PluginMarketplacePolicyDraftModel):
    policy_ref: str = "plugin-marketplace-policy-draft:m144"
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    policy_draft_only: bool = True
    disabled_by_default_required: bool = True
    m101_m143_coverage_required: bool = True
    marketplace_policy_refs_required: bool = True
    publisher_policy_refs_required: bool = True
    listing_review_refs_required: bool = True
    provenance_review_refs_required: bool = True
    signature_review_refs_required: bool = True
    sandbox_review_refs_required: bool = True
    permission_mapping_refs_required: bool = True
    approval_policy_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_plugin_install_required: bool = True
    no_plugin_enablement_required: bool = True
    no_plugin_execution_required: bool = True
    no_marketplace_runtime_required: bool = True
    no_marketplace_publish_required: bool = True
    no_external_plugin_authority_required: bool = True
    no_package_import_required: bool = True
    no_network_plugin_fetch_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    m145_future_only: bool = True
    plugin_marketplace_runtime_enabled: bool = False
    marketplace_publish_enabled: bool = False
    plugin_install_enabled: bool = False
    plugin_enablement_enabled: bool = False
    plugin_execution_enabled: bool = False
    external_plugin_authority_enabled: bool = False
    external_plugin_loading_enabled: bool = False
    marketplace_listing_mutation_enabled: bool = False
    package_import_enabled: bool = False
    runtime_import_enabled: bool = False
    network_plugin_fetch_enabled: bool = False
    package_download_enabled: bool = False
    artifact_upload_enabled: bool = False
    signature_verification_runtime_enabled: bool = False
    credential_handling_enabled: bool = False
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
        try:
            _validate_safe_payload(self.metadata)
        except ValueError as exc:
            raise ValueError("M144_SECRET_LIKE_MARKETPLACE_POLICY_CONTENT_DENIED") from exc
        return self


class PluginMarketplacePolicyDraftRequest(_PluginMarketplacePolicyDraftModel):
    request_ref: str
    policy_draft_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    marketplace_policy_refs: list[str]
    publisher_policy_refs: list[str]
    listing_review_refs: list[str]
    provenance_review_refs: list[str]
    signature_review_refs: list[str]
    sandbox_review_refs: list[str]
    permission_mapping_refs: list[str]
    approval_policy_refs: list[str]
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
    policy_draft_only: bool = True
    disabled_by_default_required: bool = True
    m101_m143_coverage_required: bool = True
    marketplace_policy_refs_required: bool = True
    publisher_policy_refs_required: bool = True
    listing_review_refs_required: bool = True
    provenance_review_refs_required: bool = True
    signature_review_refs_required: bool = True
    sandbox_review_refs_required: bool = True
    permission_mapping_refs_required: bool = True
    approval_policy_refs_required: bool = True
    audit_replay_required: bool = True
    revocation_required: bool = True
    no_effect_receipt_required: bool = True
    no_plugin_install_required: bool = True
    no_plugin_enablement_required: bool = True
    no_plugin_execution_required: bool = True
    no_marketplace_runtime_required: bool = True
    no_marketplace_publish_required: bool = True
    no_external_plugin_authority_required: bool = True
    no_package_import_required: bool = True
    no_network_plugin_fetch_required: bool = True
    no_dependency_required: bool = True
    no_production_authority_required: bool = True
    plugin_marketplace_runtime_requested: bool = False
    marketplace_publish_requested: bool = False
    plugin_install_requested: bool = False
    plugin_enablement_requested: bool = False
    plugin_execution_requested: bool = False
    external_plugin_authority_requested: bool = False
    external_plugin_loading_requested: bool = False
    marketplace_listing_mutation_requested: bool = False
    package_import_requested: bool = False
    runtime_import_requested: bool = False
    network_plugin_fetch_requested: bool = False
    package_download_requested: bool = False
    artifact_upload_requested: bool = False
    signature_verification_runtime_requested: bool = False
    credential_handling_requested: bool = False
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
    contains_raw_manifest_content: bool = False
    contains_raw_package_content: bool = False
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


class PluginMarketplacePolicyDraftRecord(_PluginMarketplacePolicyDraftModel):
    record_ref: str
    policy_draft_ref: str
    request_ref: str
    baseline_ref: str
    actor_ref: str
    accepted_checkpoint_refs: list[str]
    marketplace_policy_refs: list[str]
    publisher_policy_refs: list[str]
    listing_review_refs: list[str]
    provenance_review_refs: list[str]
    signature_review_refs: list[str]
    sandbox_review_refs: list[str]
    permission_mapping_refs: list[str]
    approval_policy_refs: list[str]
    audit_ref: str
    replay_ref: str
    revocation_ref: str
    kill_switch_ref: str
    no_effect_receipt_plan_ref: str
    status: PluginMarketplacePolicyDraftStatus = (
        PluginMarketplacePolicyDraftStatus.policy_draft_recorded
    )
    contract_only: bool = True
    review_only: bool = True
    deterministic: bool = True
    local_only: bool = True
    safe_refs_only: bool = True
    policy_draft_only: bool = True
    disabled_by_default: bool = True
    m101_m143_covered: bool = True
    marketplace_policy_bound: bool = True
    publisher_policy_bound: bool = True
    listing_review_bound: bool = True
    provenance_review_bound: bool = True
    signature_review_bound: bool = True
    sandbox_review_bound: bool = True
    permission_mapping_bound: bool = True
    approval_policy_bound: bool = True
    audit_replay_bound: bool = True
    revocation_bound: bool = True
    no_effect_receipt_required: bool = True
    no_plugin_install: bool = True
    no_plugin_enablement: bool = True
    no_plugin_execution: bool = True
    no_marketplace_runtime: bool = True
    no_marketplace_publish: bool = True
    no_external_plugin_authority: bool = True
    no_package_import: bool = True
    no_network_plugin_fetch: bool = True
    no_dependency: bool = True
    no_production_authority: bool = True
    plugin_marketplace_runtime_started: bool = False
    marketplace_publish_performed: bool = False
    plugin_install_performed: bool = False
    plugin_enablement_performed: bool = False
    plugin_execution_performed: bool = False
    external_plugin_authority_granted: bool = False
    external_plugin_loaded: bool = False
    marketplace_listing_mutation_performed: bool = False
    package_import_performed: bool = False
    runtime_import_performed: bool = False
    network_plugin_fetch_performed: bool = False
    package_download_performed: bool = False
    artifact_upload_performed: bool = False
    signature_verification_runtime_performed: bool = False
    credential_handling_performed: bool = False
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
            raise ValueError("M144_REASON_CODE_REQUIRED")
        return self


def build_plugin_marketplace_policy_draft_record(
    request: PluginMarketplacePolicyDraftRequest,
    policy: PluginMarketplacePolicyDraftPolicy | None = None,
) -> PluginMarketplacePolicyDraftRecord:
    active_policy = validate_plugin_marketplace_policy_draft_policy(
        policy or PluginMarketplacePolicyDraftPolicy()
    )
    validated_request = validate_plugin_marketplace_policy_draft_request(request)
    record = PluginMarketplacePolicyDraftRecord(
        record_ref=f"plugin-marketplace-policy-draft-record:{_ref_suffix(validated_request.policy_draft_ref)}",
        policy_draft_ref=validated_request.policy_draft_ref,
        request_ref=validated_request.request_ref,
        baseline_ref=validated_request.baseline_ref,
        actor_ref=validated_request.actor_ref,
        accepted_checkpoint_refs=list(validated_request.accepted_checkpoint_refs),
        marketplace_policy_refs=list(validated_request.marketplace_policy_refs),
        publisher_policy_refs=list(validated_request.publisher_policy_refs),
        listing_review_refs=list(validated_request.listing_review_refs),
        provenance_review_refs=list(validated_request.provenance_review_refs),
        signature_review_refs=list(validated_request.signature_review_refs),
        sandbox_review_refs=list(validated_request.sandbox_review_refs),
        permission_mapping_refs=list(validated_request.permission_mapping_refs),
        approval_policy_refs=list(validated_request.approval_policy_refs),
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
        policy_draft_only=active_policy.policy_draft_only,
        disabled_by_default=active_policy.disabled_by_default_required,
        m101_m143_covered=active_policy.m101_m143_coverage_required,
        marketplace_policy_bound=active_policy.marketplace_policy_refs_required,
        publisher_policy_bound=active_policy.publisher_policy_refs_required,
        listing_review_bound=active_policy.listing_review_refs_required,
        provenance_review_bound=active_policy.provenance_review_refs_required,
        signature_review_bound=active_policy.signature_review_refs_required,
        sandbox_review_bound=active_policy.sandbox_review_refs_required,
        permission_mapping_bound=active_policy.permission_mapping_refs_required,
        approval_policy_bound=active_policy.approval_policy_refs_required,
        audit_replay_bound=active_policy.audit_replay_required,
        revocation_bound=active_policy.revocation_required,
        no_effect_receipt_required=active_policy.no_effect_receipt_required,
        no_plugin_install=active_policy.no_plugin_install_required,
        no_plugin_enablement=active_policy.no_plugin_enablement_required,
        no_plugin_execution=active_policy.no_plugin_execution_required,
        no_marketplace_runtime=active_policy.no_marketplace_runtime_required,
        no_marketplace_publish=active_policy.no_marketplace_publish_required,
        no_external_plugin_authority=(
            active_policy.no_external_plugin_authority_required
        ),
        no_package_import=active_policy.no_package_import_required,
        no_network_plugin_fetch=active_policy.no_network_plugin_fetch_required,
        no_dependency=active_policy.no_dependency_required,
        no_production_authority=active_policy.no_production_authority_required,
        reason_codes=[
            "M144_PLUGIN_MARKETPLACE_POLICY_DRAFT_REVIEW_ONLY",
            "M144_M101_M143_COVERED",
            "M144_DISABLED_BY_DEFAULT",
            "M144_NO_PLUGIN_INSTALL",
            "M144_NO_PLUGIN_ENABLEMENT",
            "M144_NO_PLUGIN_EXECUTION",
            "M144_NO_MARKETPLACE_RUNTIME",
            "M144_NO_MARKETPLACE_PUBLISH",
            "M144_NO_EXTERNAL_PLUGIN_AUTHORITY",
            "M144_NO_PACKAGE_IMPORT",
            "M144_NO_NETWORK_PLUGIN_FETCH",
            "M144_NO_PRODUCTION_AUTHORITY",
            "M145_REMAINS_FUTURE",
        ],
        safe_summary=(
            "M144 records a contract-only plugin marketplace policy draft using "
            "safe marketplace policy, publisher policy, listing review, "
            "provenance review, signature review, sandbox review, permission "
            "mapping, approval policy, audit, replay, revocation, kill-switch, "
            "and no-effect receipt refs. It keeps plugin marketplace work "
            "disabled by default and grants no marketplace runtime, marketplace "
            "publish, plugin install, plugin enablement, plugin execution, "
            "external plugin authority, package import, network plugin fetch, "
            "backend route, Control Center control, dependency, or production "
            "authority."
        ),
    )
    return validate_plugin_marketplace_policy_draft_record(record)


def validate_plugin_marketplace_policy_draft_policy(
    policy: PluginMarketplacePolicyDraftPolicy,
) -> PluginMarketplacePolicyDraftPolicy:
    payload = _model_payload(policy)
    if _has_secret_like_extra(payload, PluginMarketplacePolicyDraftPolicy):
        raise ValueError("M144_SECRET_LIKE_MARKETPLACE_POLICY_CONTENT_DENIED")
    validated = PluginMarketplacePolicyDraftPolicy.model_validate(payload)
    for field_name, reason in _M144_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M144_POLICY_DENIALS, _model_payload(validated))
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M144_SECRET_LIKE_MARKETPLACE_POLICY_CONTENT_DENIED") from exc
    return validated


def validate_plugin_marketplace_policy_draft_request(
    request: PluginMarketplacePolicyDraftRequest,
) -> PluginMarketplacePolicyDraftRequest:
    payload = _model_payload(request)
    if _has_secret_like_extra(payload, PluginMarketplacePolicyDraftRequest):
        raise ValueError("M144_SECRET_LIKE_MARKETPLACE_POLICY_CONTENT_DENIED")
    _deny_enabled(_M144_REQUEST_DENIALS, payload)
    validated = PluginMarketplacePolicyDraftRequest.model_validate(payload)
    for field_name, reason in _M144_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M144_REQUEST_DENIALS, _model_payload(validated))
    if validated.side_effects_performed:
        raise ValueError("M144_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _request_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M144_SECRET_LIKE_MARKETPLACE_POLICY_CONTENT_DENIED") from exc
    return validated


def validate_plugin_marketplace_policy_draft_record(
    record: PluginMarketplacePolicyDraftRecord,
) -> PluginMarketplacePolicyDraftRecord:
    payload = _model_payload(record)
    if _has_secret_like_extra(payload, PluginMarketplacePolicyDraftRecord):
        raise ValueError("M144_SECRET_LIKE_MARKETPLACE_POLICY_CONTENT_DENIED")
    _deny_enabled(_M144_RECORD_DENIALS, payload)
    validated = PluginMarketplacePolicyDraftRecord.model_validate(payload)
    for field_name, reason in _M144_RECORD_REQUIRED_TRUE:
        if not getattr(validated, field_name):
            raise ValueError(reason)
    _deny_enabled(_M144_RECORD_DENIALS, _model_payload(validated))
    if (
        validated.status
        != PluginMarketplacePolicyDraftStatus.policy_draft_recorded
    ):
        raise ValueError("M144_POLICY_DRAFT_STATUS_REQUIRED")
    if validated.side_effects_performed:
        raise ValueError("M144_SIDE_EFFECTS_DENIED")
    _validate_accepted_checkpoints(validated.accepted_checkpoint_refs)
    for values, field_name, reason in _record_ref_lists(validated):
        _validate_ref_list(values, field_name, reason)
    if "M144_PLUGIN_MARKETPLACE_POLICY_DRAFT_REVIEW_ONLY" not in validated.reason_codes:
        raise ValueError("M144_REASON_CODE_REQUIRED")
    try:
        _validate_safe_payload(validated.metadata)
    except ValueError as exc:
        raise ValueError("M144_SECRET_LIKE_MARKETPLACE_POLICY_CONTENT_DENIED") from exc
    return validated


def _request_ref_pairs(request: PluginMarketplacePolicyDraftRequest):
    return [
        (request.request_ref, "request_ref"),
        (request.policy_draft_ref, "policy_draft_ref"),
        (request.baseline_ref, "baseline_ref"),
        (request.actor_ref, "actor_ref"),
        (request.audit_ref, "audit_ref"),
        (request.replay_ref, "replay_ref"),
        (request.revocation_ref, "revocation_ref"),
        (request.kill_switch_ref, "kill_switch_ref"),
        (request.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _record_ref_pairs(record: PluginMarketplacePolicyDraftRecord):
    return [
        (record.record_ref, "record_ref"),
        (record.policy_draft_ref, "policy_draft_ref"),
        (record.request_ref, "request_ref"),
        (record.baseline_ref, "baseline_ref"),
        (record.actor_ref, "actor_ref"),
        (record.audit_ref, "audit_ref"),
        (record.replay_ref, "replay_ref"),
        (record.revocation_ref, "revocation_ref"),
        (record.kill_switch_ref, "kill_switch_ref"),
        (record.no_effect_receipt_plan_ref, "no_effect_receipt_plan_ref"),
    ]


def _request_ref_lists(request: PluginMarketplacePolicyDraftRequest):
    return [
        (
            request.marketplace_policy_refs,
            "marketplace_policy_ref",
            "M144_MARKETPLACE_POLICY_REF_REQUIRED",
        ),
        (
            request.publisher_policy_refs,
            "publisher_policy_ref",
            "M144_PUBLISHER_POLICY_REF_REQUIRED",
        ),
        (
            request.listing_review_refs,
            "listing_review_ref",
            "M144_LISTING_REVIEW_REF_REQUIRED",
        ),
        (
            request.provenance_review_refs,
            "provenance_review_ref",
            "M144_PROVENANCE_REVIEW_REF_REQUIRED",
        ),
        (
            request.signature_review_refs,
            "signature_review_ref",
            "M144_SIGNATURE_REVIEW_REF_REQUIRED",
        ),
        (
            request.sandbox_review_refs,
            "sandbox_review_ref",
            "M144_SANDBOX_REVIEW_REF_REQUIRED",
        ),
        (
            request.permission_mapping_refs,
            "permission_mapping_ref",
            "M144_PERMISSION_MAPPING_REF_REQUIRED",
        ),
        (
            request.approval_policy_refs,
            "approval_policy_ref",
            "M144_APPROVAL_POLICY_REF_REQUIRED",
        ),
    ]


def _record_ref_lists(record: PluginMarketplacePolicyDraftRecord):
    return [
        (
            record.marketplace_policy_refs,
            "marketplace_policy_ref",
            "M144_MARKETPLACE_POLICY_REF_REQUIRED",
        ),
        (
            record.publisher_policy_refs,
            "publisher_policy_ref",
            "M144_PUBLISHER_POLICY_REF_REQUIRED",
        ),
        (
            record.listing_review_refs,
            "listing_review_ref",
            "M144_LISTING_REVIEW_REF_REQUIRED",
        ),
        (
            record.provenance_review_refs,
            "provenance_review_ref",
            "M144_PROVENANCE_REVIEW_REF_REQUIRED",
        ),
        (
            record.signature_review_refs,
            "signature_review_ref",
            "M144_SIGNATURE_REVIEW_REF_REQUIRED",
        ),
        (
            record.sandbox_review_refs,
            "sandbox_review_ref",
            "M144_SANDBOX_REVIEW_REF_REQUIRED",
        ),
        (
            record.permission_mapping_refs,
            "permission_mapping_ref",
            "M144_PERMISSION_MAPPING_REF_REQUIRED",
        ),
        (
            record.approval_policy_refs,
            "approval_policy_ref",
            "M144_APPROVAL_POLICY_REF_REQUIRED",
        ),
    ]


def _validate_accepted_checkpoints(refs: list[str]) -> None:
    if not refs:
        raise ValueError("M144_ACCEPTED_CHECKPOINTS_REQUIRED")
    if len(refs) != len(set(refs)):
        raise ValueError("M144_CHECKPOINT_REF_DUPLICATE")
    for ref in refs:
        _validate_m61_ref(ref, "accepted_checkpoint_ref")
    missing = [ref for ref in REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS if ref not in refs]
    if missing:
        raise ValueError("M144_CHECKPOINT_REF_REQUIRED")
    unexpected = [ref for ref in refs if ref not in REQUIRED_M144_ACCEPTED_CHECKPOINT_REFS]
    if unexpected:
        raise ValueError("M144_CHECKPOINT_REF_UNEXPECTED")


def _validate_ref_list(values: list[str], field_name: str, required_reason: str) -> None:
    if not values:
        raise ValueError(required_reason)
    if len(values) != len(set(values)):
        raise ValueError("M144_REF_DUPLICATE")
    for value in values:
        _validate_m61_ref(value, field_name)


def _deny_enabled(denials: dict[str, str], payload: dict[str, Any]) -> None:
    for field_name, reason in denials.items():
        if payload.get(field_name):
            raise ValueError(reason)


_M144_REQUIRED_TRUE = [
    ("contract_only", "M144_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M144_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M144_DETERMINISTIC_REQUIRED"),
    ("local_only", "M144_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M144_SAFE_REFS_ONLY_REQUIRED"),
    ("policy_draft_only", "M144_POLICY_DRAFT_ONLY_REQUIRED"),
    ("disabled_by_default_required", "M144_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m143_coverage_required", "M144_M101_M143_COVERAGE_REQUIRED"),
    ("marketplace_policy_refs_required", "M144_MARKETPLACE_POLICY_REF_REQUIRED"),
    ("publisher_policy_refs_required", "M144_PUBLISHER_POLICY_REF_REQUIRED"),
    ("listing_review_refs_required", "M144_LISTING_REVIEW_REF_REQUIRED"),
    ("provenance_review_refs_required", "M144_PROVENANCE_REVIEW_REF_REQUIRED"),
    ("signature_review_refs_required", "M144_SIGNATURE_REVIEW_REF_REQUIRED"),
    ("sandbox_review_refs_required", "M144_SANDBOX_REVIEW_REF_REQUIRED"),
    ("permission_mapping_refs_required", "M144_PERMISSION_MAPPING_REF_REQUIRED"),
    ("approval_policy_refs_required", "M144_APPROVAL_POLICY_REF_REQUIRED"),
    ("audit_replay_required", "M144_AUDIT_REPLAY_REQUIRED"),
    ("revocation_required", "M144_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M144_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_plugin_install_required", "M144_PLUGIN_INSTALL_DENIED"),
    ("no_plugin_enablement_required", "M144_PLUGIN_ENABLEMENT_DENIED"),
    ("no_plugin_execution_required", "M144_PLUGIN_EXECUTION_DENIED"),
    ("no_marketplace_runtime_required", "M144_MARKETPLACE_RUNTIME_DENIED"),
    ("no_marketplace_publish_required", "M144_MARKETPLACE_PUBLISH_DENIED"),
    (
        "no_external_plugin_authority_required",
        "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED",
    ),
    ("no_package_import_required", "M144_PACKAGE_IMPORT_DENIED"),
    ("no_network_plugin_fetch_required", "M144_NETWORK_PLUGIN_FETCH_DENIED"),
    ("no_dependency_required", "M144_DEPENDENCY_DENIED"),
    ("no_production_authority_required", "M144_PRODUCTION_AUTHORITY_DENIED"),
]

_M144_RECORD_REQUIRED_TRUE = [
    ("contract_only", "M144_CONTRACT_ONLY_REQUIRED"),
    ("review_only", "M144_REVIEW_ONLY_REQUIRED"),
    ("deterministic", "M144_DETERMINISTIC_REQUIRED"),
    ("local_only", "M144_LOCAL_ONLY_REQUIRED"),
    ("safe_refs_only", "M144_SAFE_REFS_ONLY_REQUIRED"),
    ("policy_draft_only", "M144_POLICY_DRAFT_ONLY_REQUIRED"),
    ("disabled_by_default", "M144_DISABLED_BY_DEFAULT_REQUIRED"),
    ("m101_m143_covered", "M144_M101_M143_COVERAGE_REQUIRED"),
    ("marketplace_policy_bound", "M144_MARKETPLACE_POLICY_REF_REQUIRED"),
    ("publisher_policy_bound", "M144_PUBLISHER_POLICY_REF_REQUIRED"),
    ("listing_review_bound", "M144_LISTING_REVIEW_REF_REQUIRED"),
    ("provenance_review_bound", "M144_PROVENANCE_REVIEW_REF_REQUIRED"),
    ("signature_review_bound", "M144_SIGNATURE_REVIEW_REF_REQUIRED"),
    ("sandbox_review_bound", "M144_SANDBOX_REVIEW_REF_REQUIRED"),
    ("permission_mapping_bound", "M144_PERMISSION_MAPPING_REF_REQUIRED"),
    ("approval_policy_bound", "M144_APPROVAL_POLICY_REF_REQUIRED"),
    ("audit_replay_bound", "M144_AUDIT_REPLAY_REQUIRED"),
    ("revocation_bound", "M144_REVOCATION_REQUIRED"),
    ("no_effect_receipt_required", "M144_NO_EFFECT_RECEIPT_REQUIRED"),
    ("no_plugin_install", "M144_PLUGIN_INSTALL_DENIED"),
    ("no_plugin_enablement", "M144_PLUGIN_ENABLEMENT_DENIED"),
    ("no_plugin_execution", "M144_PLUGIN_EXECUTION_DENIED"),
    ("no_marketplace_runtime", "M144_MARKETPLACE_RUNTIME_DENIED"),
    ("no_marketplace_publish", "M144_MARKETPLACE_PUBLISH_DENIED"),
    ("no_external_plugin_authority", "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED"),
    ("no_package_import", "M144_PACKAGE_IMPORT_DENIED"),
    ("no_network_plugin_fetch", "M144_NETWORK_PLUGIN_FETCH_DENIED"),
    ("no_dependency", "M144_DEPENDENCY_DENIED"),
    ("no_production_authority", "M144_PRODUCTION_AUTHORITY_DENIED"),
]

_M144_POLICY_DENIALS = {
    "plugin_marketplace_runtime_enabled": "M144_MARKETPLACE_RUNTIME_DENIED",
    "marketplace_publish_enabled": "M144_MARKETPLACE_PUBLISH_DENIED",
    "plugin_install_enabled": "M144_PLUGIN_INSTALL_DENIED",
    "plugin_enablement_enabled": "M144_PLUGIN_ENABLEMENT_DENIED",
    "plugin_execution_enabled": "M144_PLUGIN_EXECUTION_DENIED",
    "external_plugin_authority_enabled": "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED",
    "external_plugin_loading_enabled": "M144_EXTERNAL_PLUGIN_LOADING_DENIED",
    "marketplace_listing_mutation_enabled": "M144_MARKETPLACE_MUTATION_DENIED",
    "package_import_enabled": "M144_PACKAGE_IMPORT_DENIED",
    "runtime_import_enabled": "M144_RUNTIME_IMPORT_DENIED",
    "network_plugin_fetch_enabled": "M144_NETWORK_PLUGIN_FETCH_DENIED",
    "package_download_enabled": "M144_PACKAGE_DOWNLOAD_DENIED",
    "artifact_upload_enabled": "M144_ARTIFACT_UPLOAD_DENIED",
    "signature_verification_runtime_enabled": "M144_SIGNATURE_RUNTIME_DENIED",
    "credential_handling_enabled": "M144_CREDENTIAL_HANDLING_DENIED",
    "execution_enabled": "M144_EXECUTION_DENIED",
    "tool_execution_enabled": "M144_TOOL_EXECUTION_DENIED",
    "shell_execution_enabled": "M144_SHELL_EXECUTION_DENIED",
    "browser_action_enabled": "M144_BROWSER_ACTION_DENIED",
    "connector_action_enabled": "M144_CONNECTOR_ACTION_DENIED",
    "network_access_enabled": "M144_NETWORK_ACCESS_DENIED",
    "mobile_sensor_enabled": "M144_MOBILE_SENSOR_DENIED",
    "remote_execution_enabled": "M144_REMOTE_EXECUTION_DENIED",
    "model_call_enabled": "M144_MODEL_CALL_DENIED",
    "memory_write_enabled": "M144_MEMORY_WRITE_DENIED",
    "context_injection_enabled": "M144_CONTEXT_INJECTION_DENIED",
    "backend_route_enabled": "M144_BACKEND_ROUTE_DENIED",
    "control_center_control_enabled": "M144_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M144_DEPENDENCY_DENIED",
    "production_authority_granted": "M144_PRODUCTION_AUTHORITY_DENIED",
}

_M144_REQUEST_DENIALS = {
    **{
        key.replace("_enabled", "_requested"): value
        for key, value in _M144_POLICY_DENIALS.items()
        if key.endswith("_enabled")
    },
    "plugin_marketplace_runtime_requested": "M144_MARKETPLACE_RUNTIME_DENIED",
    "marketplace_publish_requested": "M144_MARKETPLACE_PUBLISH_DENIED",
    "plugin_install_requested": "M144_PLUGIN_INSTALL_DENIED",
    "plugin_enablement_requested": "M144_PLUGIN_ENABLEMENT_DENIED",
    "plugin_execution_requested": "M144_PLUGIN_EXECUTION_DENIED",
    "external_plugin_authority_requested": "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED",
    "external_plugin_loading_requested": "M144_EXTERNAL_PLUGIN_LOADING_DENIED",
    "marketplace_listing_mutation_requested": "M144_MARKETPLACE_MUTATION_DENIED",
    "package_import_requested": "M144_PACKAGE_IMPORT_DENIED",
    "runtime_import_requested": "M144_RUNTIME_IMPORT_DENIED",
    "network_plugin_fetch_requested": "M144_NETWORK_PLUGIN_FETCH_DENIED",
    "package_download_requested": "M144_PACKAGE_DOWNLOAD_DENIED",
    "artifact_upload_requested": "M144_ARTIFACT_UPLOAD_DENIED",
    "signature_verification_runtime_requested": "M144_SIGNATURE_RUNTIME_DENIED",
    "production_authority_requested": "M144_PRODUCTION_AUTHORITY_DENIED",
    "contains_raw_manifest_content": "M144_RAW_MANIFEST_CONTENT_DENIED",
    "contains_raw_package_content": "M144_RAW_PACKAGE_CONTENT_DENIED",
    "contains_raw_prompt": "M144_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_raw_provider_payload": "M144_RAW_PROMPT_PAYLOAD_DENIED",
    "contains_cookie_or_credential": "M144_CREDENTIAL_COOKIE_ACCESS_DENIED",
    "contains_secret": "M144_SECRET_DENIED",
    "dependency_requested": "M144_DEPENDENCY_DENIED",
}

_M144_RECORD_DENIALS = {
    "plugin_marketplace_runtime_started": "M144_MARKETPLACE_RUNTIME_DENIED",
    "marketplace_publish_performed": "M144_MARKETPLACE_PUBLISH_DENIED",
    "plugin_install_performed": "M144_PLUGIN_INSTALL_DENIED",
    "plugin_enablement_performed": "M144_PLUGIN_ENABLEMENT_DENIED",
    "plugin_execution_performed": "M144_PLUGIN_EXECUTION_DENIED",
    "external_plugin_authority_granted": "M144_EXTERNAL_PLUGIN_AUTHORITY_DENIED",
    "external_plugin_loaded": "M144_EXTERNAL_PLUGIN_LOADING_DENIED",
    "marketplace_listing_mutation_performed": "M144_MARKETPLACE_MUTATION_DENIED",
    "package_import_performed": "M144_PACKAGE_IMPORT_DENIED",
    "runtime_import_performed": "M144_RUNTIME_IMPORT_DENIED",
    "network_plugin_fetch_performed": "M144_NETWORK_PLUGIN_FETCH_DENIED",
    "package_download_performed": "M144_PACKAGE_DOWNLOAD_DENIED",
    "artifact_upload_performed": "M144_ARTIFACT_UPLOAD_DENIED",
    "signature_verification_runtime_performed": "M144_SIGNATURE_RUNTIME_DENIED",
    "credential_handling_performed": "M144_CREDENTIAL_HANDLING_DENIED",
    "execution_performed": "M144_EXECUTION_DENIED",
    "tool_execution_performed": "M144_TOOL_EXECUTION_DENIED",
    "shell_execution_performed": "M144_SHELL_EXECUTION_DENIED",
    "browser_action_performed": "M144_BROWSER_ACTION_DENIED",
    "connector_action_performed": "M144_CONNECTOR_ACTION_DENIED",
    "network_access_performed": "M144_NETWORK_ACCESS_DENIED",
    "mobile_sensor_performed": "M144_MOBILE_SENSOR_DENIED",
    "remote_execution_performed": "M144_REMOTE_EXECUTION_DENIED",
    "model_call_performed": "M144_MODEL_CALL_DENIED",
    "memory_write_performed": "M144_MEMORY_WRITE_DENIED",
    "context_injection_performed": "M144_CONTEXT_INJECTION_DENIED",
    "backend_route_added": "M144_BACKEND_ROUTE_DENIED",
    "control_center_control_added": "M144_CONTROL_CENTER_CONTROL_DENIED",
    "dependency_added": "M144_DEPENDENCY_DENIED",
    "production_authority_granted": "M144_PRODUCTION_AUTHORITY_DENIED",
}
