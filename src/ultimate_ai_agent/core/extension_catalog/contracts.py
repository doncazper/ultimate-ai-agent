from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SAFE_REF_PATTERN = r"^[a-z][a-z0-9_-]*:[a-z0-9][a-z0-9_.:-]*$"
SHA256_PATTERN = r"^sha256:[a-f0-9]{64}$"


class ExtensionPackageKind(str, Enum):
    plugin = "plugin"
    skill = "skill"
    connector_manifest = "connector_manifest"
    tooling_bundle = "tooling_bundle"


class ExtensionCapabilityKind(str, Enum):
    documentation_helper = "documentation_helper"
    read_only_inspection = "read_only_inspection"
    local_preview = "local_preview"
    tooling_metadata = "tooling_metadata"
    blocked_runtime = "blocked_runtime"


class ExtensionRiskClass(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ExtensionProvenanceStatus(str, Enum):
    reviewed = "reviewed"
    blocked = "blocked"
    unknown = "unknown"


class ExtensionHashStatus(str, Enum):
    reviewed = "reviewed"
    missing = "missing"
    unknown = "unknown"


class ExtensionGrantStatus(str, Enum):
    requested = "requested"
    blocked = "blocked"
    future_scoped = "future_scoped"


class ExtensionActivationStatus(str, Enum):
    inactive = "inactive"
    blocked = "blocked"
    revoked = "revoked"
    future_scoped = "future_scoped"


class ExtensionActivationGrantStatus(str, Enum):
    granted = "granted"
    revoked = "revoked"
    stale = "stale"
    blocked = "blocked"


class ExtensionActivationGrantStaleness(str, Enum):
    current = "current"
    stale = "stale"


class ExtensionRevocationStatus(str, Enum):
    requested = "requested"
    revoked = "revoked"


class ExtensionBlockedState(str, Enum):
    not_blocked = "not_blocked"
    blocked = "blocked"
    unknown = "unknown"
    future_scoped = "future_scoped"


class ExtensionCatalogVisibilityStatus(str, Enum):
    implemented = "implemented"
    partial = "partial"
    planned = "planned"
    mock_only = "mock_only"
    blocked = "blocked"
    deprecated = "deprecated"
    contradicted = "contradicted"
    unknown = "unknown"


class ExtensionTrustPosture(str, Enum):
    reviewed_metadata = "reviewed_metadata"
    unknown_blocked = "unknown_blocked"
    blocked_by_policy = "blocked_by_policy"
    future_review_required = "future_review_required"


class ExtensionCallablePosture(str, Enum):
    inspectable_only = "inspectable_only"
    blocked_runtime = "blocked_runtime"
    future_exact_lane_required = "future_exact_lane_required"


class ExtensionSafeAdoptionPosture(str, Enum):
    repo_owned_metadata_only = "repo_owned_metadata_only"
    reviewed_adaptation_required = "reviewed_adaptation_required"
    blocked_until_scoped_milestone = "blocked_until_scoped_milestone"


class ExtensionProgressiveDisclosureStatus(str, Enum):
    metadata_indexed = "metadata_indexed"
    full_instructions_blocked = "full_instructions_blocked"
    future_review_required = "future_review_required"
    blocked = "blocked"


class ExtensionFullInstructionLoadPosture(str, Enum):
    metadata_only = "metadata_only"
    operator_selected_review_required = "operator_selected_review_required"
    blocked_runtime_import = "blocked_runtime_import"


class SkillWriteProposalKind(str, Enum):
    create_skill = "create_skill"
    update_skill = "update_skill"


class SkillWriteReviewStatus(str, Enum):
    awaiting_operator_review = "awaiting_operator_review"
    revision_requested = "revision_requested"
    rejected = "rejected"
    blocked = "blocked"


class SkillBundleProposalStatus(str, Enum):
    proposal_only = "proposal_only"
    review_required = "review_required"
    blocked = "blocked"


class _ExtensionCatalogModel(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True, extra="forbid", protected_namespaces=()
    )


class InspectableExtensionPackageIdentity(_ExtensionCatalogModel):
    package_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    package_name: str = Field(..., min_length=1, max_length=120)
    package_kind: ExtensionPackageKind
    version_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    publisher_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)


class InspectableExtensionProvenance(_ExtensionCatalogModel):
    source_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    review_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    license_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    provenance_status: ExtensionProvenanceStatus


class InspectableExtensionFileHash(_ExtensionCatalogModel):
    file_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    hash_algorithm: Literal["sha256"] = "sha256"
    hash_value: str | None = Field(default=None, pattern=SHA256_PATTERN)
    hash_status: ExtensionHashStatus = ExtensionHashStatus.unknown


class InspectableExtensionCapability(_ExtensionCatalogModel):
    capability_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    capability_kind: ExtensionCapabilityKind
    risk_class: ExtensionRiskClass
    safe_purpose: str = Field(..., min_length=1, max_length=240)


class InspectableExtensionRequestedGrant(_ExtensionCatalogModel):
    grant_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    scope_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    status: ExtensionGrantStatus


class InspectableExtensionCatalogEntry(_ExtensionCatalogModel):
    catalog_entry_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    manifest_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    compact_skill_index_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    metadata_summary_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    package_identity: InspectableExtensionPackageIdentity
    provenance: InspectableExtensionProvenance
    file_hashes: list[InspectableExtensionFileHash] = Field(default_factory=list)
    declared_capabilities: list[InspectableExtensionCapability] = Field(
        default_factory=list
    )
    risk_class: ExtensionRiskClass
    requested_grants: list[InspectableExtensionRequestedGrant] = Field(
        default_factory=list
    )
    activation_status: ExtensionActivationStatus = ExtensionActivationStatus.inactive
    blocked_state: ExtensionBlockedState = ExtensionBlockedState.unknown
    blocker_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    visibility_status: ExtensionCatalogVisibilityStatus
    trust_posture: ExtensionTrustPosture
    callable_posture: ExtensionCallablePosture
    required_grant_refs: list[str] = Field(default_factory=list)
    blocked_reason: str = Field(..., min_length=1, max_length=240)
    review_evidence_refs: list[str] = Field(default_factory=list)
    safe_adoption_posture: ExtensionSafeAdoptionPosture
    progressive_disclosure_status: ExtensionProgressiveDisclosureStatus
    full_instruction_load_posture: ExtensionFullInstructionLoadPosture
    metadata_first: Literal[True] = True
    operator_selected_before_full_instruction: Literal[True] = True
    automatic_instruction_loading_enabled: Literal[False] = False
    hidden_activation_enabled: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=500)


class SkillWriteDiffPreview(_ExtensionCatalogModel):
    diff_preview_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    target_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    change_summary_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    raw_diff_persisted: Literal[False] = False
    raw_file_content_persisted: Literal[False] = False


class SkillWriteProposal(_ExtensionCatalogModel):
    proposal_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    proposal_kind: SkillWriteProposalKind
    skill_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    target_skill_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    staged_artifact_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    review_decision_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    review_status: SkillWriteReviewStatus
    diff_previews: list[SkillWriteDiffPreview] = Field(default_factory=list)
    blocked_execution_labels: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    receipt_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    file_write_performed: Literal[False] = False
    skill_enablement_performed: Literal[False] = False
    runtime_import_performed: Literal[False] = False
    execution_performed: Literal[False] = False
    raw_instruction_body_persisted: Literal[False] = False


class SkillWriteApprovalGateReadModel(_ExtensionCatalogModel):
    schema_version: Literal["uaa_skill_write_approval_gate.v1"] = (
        "uaa_skill_write_approval_gate.v1"
    )
    gate_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    status: Literal["staged_review_only"] = "staged_review_only"
    proposal_count: int = Field(..., ge=0)
    proposals: list[SkillWriteProposal] = Field(default_factory=list)
    review_queue_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    required_authority_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    file_write_enabled: Literal[False] = False
    direct_skill_write_enabled: Literal[False] = False
    skill_enablement_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    execution_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    production_authority_enabled: Literal[False] = False


class SkillBundleProposal(_ExtensionCatalogModel):
    proposal_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    bundle_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    bundle_name: str = Field(..., min_length=1, max_length=120)
    proposal_status: SkillBundleProposalStatus
    skill_refs: list[str] = Field(..., min_length=1)
    context_pack_refs: list[str] = Field(..., min_length=1)
    toolset_refs: list[str] = Field(..., min_length=1)
    authority_profile_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    verification_refs: list[str] = Field(..., min_length=1)
    blocked_authority_refs: list[str] = Field(..., min_length=1)
    proof_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    activation_performed: Literal[False] = False
    skill_enablement_performed: Literal[False] = False
    tool_execution_performed: Literal[False] = False
    context_injection_performed: Literal[False] = False
    runtime_import_performed: Literal[False] = False
    provider_model_call_performed: Literal[False] = False
    connector_write_performed: Literal[False] = False
    shell_execution_performed: Literal[False] = False
    browser_automation_performed: Literal[False] = False
    production_authority_performed: Literal[False] = False


class SkillBundleProposalPostureReadModel(_ExtensionCatalogModel):
    schema_version: Literal["uaa_skill_bundle_proposal_posture.v1"] = (
        "uaa_skill_bundle_proposal_posture.v1"
    )
    posture_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    status: Literal["proposal_only"] = "proposal_only"
    proposal_count: int = Field(..., ge=0)
    proposals: list[SkillBundleProposal] = Field(default_factory=list)
    bundle_review_queue_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    required_authority_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    blocked_authority_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)
    bundle_activation_enabled: Literal[False] = False
    skill_enablement_enabled: Literal[False] = False
    tool_execution_enabled: Literal[False] = False
    context_injection_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    provider_model_call_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    production_authority_enabled: Literal[False] = False


class InspectableExtensionCatalog(_ExtensionCatalogModel):
    schema_version: Literal["uaa_inspectable_extension_catalog.v1"] = (
        "uaa_inspectable_extension_catalog.v1"
    )
    catalog_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    catalog_status: Literal["read_only_inspection"] = "read_only_inspection"
    generated_from_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    entries: list[InspectableExtensionCatalogEntry] = Field(default_factory=list)
    read_only: Literal[True] = True
    inspectable_catalog_enabled: Literal[True] = True
    progressive_disclosure_enabled: Literal[True] = True
    metadata_first_index_enabled: Literal[True] = True
    callable_catalog_enabled: Literal[False] = False
    automatic_instruction_loading_enabled: Literal[False] = False
    full_instruction_auto_load_enabled: Literal[False] = False
    hidden_skill_activation_enabled: Literal[False] = False
    skill_runtime_import_enabled: Literal[False] = False
    external_marketplace_fetch_enabled: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    execution_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    mobile_control_enabled: Literal[False] = False
    public_distribution_claimed: Literal[False] = False
    blocked_capabilities: list[str] = Field(default_factory=list)
    compact_skill_index_refs: list[str] = Field(default_factory=list)
    progressive_disclosure_refs: list[str] = Field(default_factory=list)
    skill_write_approval_gate: SkillWriteApprovalGateReadModel
    skill_bundle_proposal_posture: SkillBundleProposalPostureReadModel
    docs_refs: list[str] = Field(default_factory=list)
    schema_refs: list[str] = Field(default_factory=list)
    developer_guidance_refs: list[str] = Field(default_factory=list)
    final_hardening_refs: list[str] = Field(default_factory=list)
    safe_summary: str = Field(..., min_length=1, max_length=500)


class ExtensionActivationGrantRecord(_ExtensionCatalogModel):
    schema_version: Literal["uaa_extension_activation_grant.v1"] = (
        "uaa_extension_activation_grant.v1"
    )
    activation_grant_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    package_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    manifest_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    version_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    actor_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    approval_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    scope_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    capability_refs: list[str] = Field(..., min_length=1)
    requested_grant_refs: list[str] = Field(..., min_length=1)
    grant_status: ExtensionActivationGrantStatus
    staleness_status: ExtensionActivationGrantStaleness = (
        ExtensionActivationGrantStaleness.current
    )
    exact_scope: Literal[True] = True
    overbroad_scope: Literal[False] = False
    revocation_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    audit_refs: list[str] = Field(..., min_length=1)
    receipt_refs: list[str] = Field(default_factory=list)
    replay_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    runtime_import_enabled: Literal[False] = False
    execution_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    mobile_control_enabled: Literal[False] = False
    public_distribution_claimed: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=500)


class ExtensionActivationRevocationRecord(_ExtensionCatalogModel):
    schema_version: Literal["uaa_extension_activation_revocation.v1"] = (
        "uaa_extension_activation_revocation.v1"
    )
    revocation_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    activation_grant_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    package_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    manifest_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    version_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    actor_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    approval_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    scope_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    revocation_status: ExtensionRevocationStatus = ExtensionRevocationStatus.revoked
    exact_scope: Literal[True] = True
    audit_refs: list[str] = Field(..., min_length=1)
    receipt_refs: list[str] = Field(default_factory=list)
    replay_ref: str = Field(..., min_length=1, pattern=SAFE_REF_PATTERN)
    runtime_import_enabled: Literal[False] = False
    execution_enabled: Literal[False] = False
    connector_writes_enabled: Literal[False] = False
    shell_execution_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    mobile_control_enabled: Literal[False] = False
    public_distribution_claimed: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=500)


CATALOG_DENIED_TRUE_FLAGS = (
    "callable_catalog_enabled",
    "automatic_instruction_loading_enabled",
    "full_instruction_auto_load_enabled",
    "hidden_skill_activation_enabled",
    "skill_runtime_import_enabled",
    "external_marketplace_fetch_enabled",
    "runtime_import_enabled",
    "execution_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "network_access_enabled",
    "browser_automation_enabled",
    "mobile_control_enabled",
    "public_distribution_claimed",
)

SKILL_WRITE_GATE_DENIED_TRUE_FLAGS = (
    "file_write_enabled",
    "direct_skill_write_enabled",
    "skill_enablement_enabled",
    "runtime_import_enabled",
    "execution_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "provider_model_call_enabled",
    "browser_automation_enabled",
    "production_authority_enabled",
)

SKILL_WRITE_PROPOSAL_DENIED_TRUE_FLAGS = (
    "file_write_performed",
    "skill_enablement_performed",
    "runtime_import_performed",
    "execution_performed",
    "raw_instruction_body_persisted",
)

SKILL_BUNDLE_POSTURE_DENIED_TRUE_FLAGS = (
    "bundle_activation_enabled",
    "skill_enablement_enabled",
    "tool_execution_enabled",
    "context_injection_enabled",
    "runtime_import_enabled",
    "provider_model_call_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "browser_automation_enabled",
    "production_authority_enabled",
)

SKILL_BUNDLE_PROPOSAL_DENIED_TRUE_FLAGS = (
    "activation_performed",
    "skill_enablement_performed",
    "tool_execution_performed",
    "context_injection_performed",
    "runtime_import_performed",
    "provider_model_call_performed",
    "connector_write_performed",
    "shell_execution_performed",
    "browser_automation_performed",
    "production_authority_performed",
)

ACTIVATION_GRANT_DENIED_TRUE_FLAGS = (
    "runtime_import_enabled",
    "execution_enabled",
    "connector_writes_enabled",
    "shell_execution_enabled",
    "network_access_enabled",
    "browser_automation_enabled",
    "mobile_control_enabled",
    "public_distribution_claimed",
)

MISSING_APPROVAL_REFS = {
    "approval:missing",
    "approval:none",
    "approval:unknown",
}


def validate_inspectable_extension_catalog(
    catalog: InspectableExtensionCatalog,
) -> InspectableExtensionCatalog:
    for field_name in CATALOG_DENIED_TRUE_FLAGS:
        if getattr(catalog, field_name):
            raise ValueError(f"EXTENSION_CATALOG_{field_name.upper()}_DENIED")
    if not catalog.read_only:
        raise ValueError("EXTENSION_CATALOG_READ_ONLY_REQUIRED")
    if not catalog.inspectable_catalog_enabled:
        raise ValueError("EXTENSION_CATALOG_INSPECTION_REQUIRED")
    if not catalog.progressive_disclosure_enabled:
        raise ValueError("EXTENSION_CATALOG_PROGRESSIVE_DISCLOSURE_REQUIRED")
    if not catalog.metadata_first_index_enabled:
        raise ValueError("EXTENSION_CATALOG_METADATA_FIRST_REQUIRED")
    _validate_safe_ref_list(
        catalog.compact_skill_index_refs,
        "EXTENSION_CATALOG_COMPACT_SKILL_INDEX_REF_REQUIRED",
    )
    _validate_safe_ref_list(
        catalog.progressive_disclosure_refs,
        "EXTENSION_CATALOG_PROGRESSIVE_DISCLOSURE_REF_REQUIRED",
    )
    validate_skill_write_approval_gate(catalog.skill_write_approval_gate)
    validate_skill_bundle_proposal_posture(catalog.skill_bundle_proposal_posture)
    for entry in catalog.entries:
        _validate_safe_ref_list(
            [entry.compact_skill_index_ref, entry.metadata_summary_ref],
            "EXTENSION_CATALOG_SKILL_METADATA_REF_REQUIRED",
        )
        _validate_safe_ref_list(
            entry.review_evidence_refs,
            "EXTENSION_CATALOG_REVIEW_EVIDENCE_REF_REQUIRED",
        )
        if not entry.metadata_first:
            raise ValueError("EXTENSION_CATALOG_ENTRY_METADATA_FIRST_REQUIRED")
        if not entry.operator_selected_before_full_instruction:
            raise ValueError("EXTENSION_CATALOG_ENTRY_OPERATOR_SELECTION_REQUIRED")
        if entry.automatic_instruction_loading_enabled:
            raise ValueError("EXTENSION_CATALOG_ENTRY_AUTO_INSTRUCTION_LOAD_DENIED")
        if entry.hidden_activation_enabled:
            raise ValueError("EXTENSION_CATALOG_ENTRY_HIDDEN_ACTIVATION_DENIED")
        if entry.required_grant_refs:
            _validate_safe_ref_list(
                entry.required_grant_refs,
                "EXTENSION_CATALOG_REQUIRED_GRANT_REF_REQUIRED",
            )
        if entry.callable_posture not in {
            ExtensionCallablePosture.inspectable_only.value,
            ExtensionCallablePosture.blocked_runtime.value,
            ExtensionCallablePosture.future_exact_lane_required.value,
        }:
            raise ValueError("EXTENSION_CATALOG_CALLABLE_POSTURE_DENIED")
        if entry.activation_status not in {
            ExtensionActivationStatus.inactive.value,
            ExtensionActivationStatus.blocked.value,
            ExtensionActivationStatus.revoked.value,
            ExtensionActivationStatus.future_scoped.value,
        }:
            raise ValueError("EXTENSION_CATALOG_ACTIVE_STATUS_DENIED")
        if (
            entry.blocked_state
            in {
                ExtensionBlockedState.blocked.value,
                ExtensionBlockedState.unknown.value,
            }
            and not entry.blocker_refs
        ):
            raise ValueError("EXTENSION_CATALOG_BLOCKER_REF_REQUIRED")
    return catalog


def validate_skill_bundle_proposal_posture(
    posture: SkillBundleProposalPostureReadModel,
) -> SkillBundleProposalPostureReadModel:
    for field_name in SKILL_BUNDLE_POSTURE_DENIED_TRUE_FLAGS:
        if getattr(posture, field_name):
            raise ValueError(f"SKILL_BUNDLE_POSTURE_{field_name.upper()}_DENIED")
    if posture.proposal_count != len(posture.proposals):
        raise ValueError("SKILL_BUNDLE_POSTURE_PROPOSAL_COUNT_MISMATCH")
    _validate_safe_ref_list(
        posture.blocked_authority_refs,
        "SKILL_BUNDLE_POSTURE_BLOCKED_AUTHORITY_REF_REQUIRED",
    )
    _validate_safe_ref_list(
        posture.verifier_refs,
        "SKILL_BUNDLE_POSTURE_VERIFIER_REF_REQUIRED",
    )
    _validate_safe_ref_list(
        posture.next_safe_action_refs,
        "SKILL_BUNDLE_POSTURE_NEXT_ACTION_REF_REQUIRED",
    )
    for proposal in posture.proposals:
        for field_name in SKILL_BUNDLE_PROPOSAL_DENIED_TRUE_FLAGS:
            if getattr(proposal, field_name):
                raise ValueError(f"SKILL_BUNDLE_PROPOSAL_{field_name.upper()}_DENIED")
        _validate_safe_ref_list(
            proposal.skill_refs,
            "SKILL_BUNDLE_PROPOSAL_SKILL_REF_REQUIRED",
        )
        _validate_safe_ref_list(
            proposal.context_pack_refs,
            "SKILL_BUNDLE_PROPOSAL_CONTEXT_REF_REQUIRED",
        )
        _validate_safe_ref_list(
            proposal.toolset_refs,
            "SKILL_BUNDLE_PROPOSAL_TOOLSET_REF_REQUIRED",
        )
        _validate_safe_ref_list(
            proposal.verification_refs,
            "SKILL_BUNDLE_PROPOSAL_VERIFICATION_REF_REQUIRED",
        )
        _validate_safe_ref_list(
            proposal.blocked_authority_refs,
            "SKILL_BUNDLE_PROPOSAL_BLOCKED_AUTHORITY_REF_REQUIRED",
        )
        _validate_safe_ref_list(
            proposal.next_safe_action_refs,
            "SKILL_BUNDLE_PROPOSAL_NEXT_ACTION_REF_REQUIRED",
        )
    return posture


def validate_skill_write_approval_gate(
    gate: SkillWriteApprovalGateReadModel,
) -> SkillWriteApprovalGateReadModel:
    for field_name in SKILL_WRITE_GATE_DENIED_TRUE_FLAGS:
        if getattr(gate, field_name):
            raise ValueError(f"SKILL_WRITE_GATE_{field_name.upper()}_DENIED")
    if gate.proposal_count != len(gate.proposals):
        raise ValueError("SKILL_WRITE_GATE_PROPOSAL_COUNT_MISMATCH")
    _validate_safe_ref_list(
        gate.blocked_authority_refs,
        "SKILL_WRITE_GATE_BLOCKED_AUTHORITY_REF_REQUIRED",
    )
    _validate_safe_ref_list(
        gate.verifier_refs,
        "SKILL_WRITE_GATE_VERIFIER_REF_REQUIRED",
    )
    _validate_safe_ref_list(
        gate.next_safe_action_refs,
        "SKILL_WRITE_GATE_NEXT_ACTION_REF_REQUIRED",
    )
    for proposal in gate.proposals:
        for field_name in SKILL_WRITE_PROPOSAL_DENIED_TRUE_FLAGS:
            if getattr(proposal, field_name):
                raise ValueError(f"SKILL_WRITE_PROPOSAL_{field_name.upper()}_DENIED")
        if not proposal.diff_previews:
            raise ValueError("SKILL_WRITE_PROPOSAL_DIFF_PREVIEW_REQUIRED")
        _validate_safe_ref_list(
            proposal.blocked_execution_labels,
            "SKILL_WRITE_PROPOSAL_BLOCKED_LABEL_REQUIRED",
        )
        _validate_safe_ref_list(
            proposal.proof_refs,
            "SKILL_WRITE_PROPOSAL_PROOF_REF_REQUIRED",
        )
        for diff_preview in proposal.diff_previews:
            if diff_preview.raw_diff_persisted:
                raise ValueError("SKILL_WRITE_DIFF_RAW_DIFF_DENIED")
            if diff_preview.raw_file_content_persisted:
                raise ValueError("SKILL_WRITE_DIFF_RAW_FILE_CONTENT_DENIED")
    return gate


def _validate_safe_ref_list(refs: list[str], reason: str) -> None:
    if not refs:
        raise ValueError(reason)
    for ref in refs:
        if not ref or ":" not in ref:
            raise ValueError(reason)


def validate_extension_activation_grant_record(
    record: ExtensionActivationGrantRecord,
) -> ExtensionActivationGrantRecord:
    for field_name in ACTIVATION_GRANT_DENIED_TRUE_FLAGS:
        if getattr(record, field_name):
            raise ValueError(f"EXTENSION_ACTIVATION_{field_name.upper()}_DENIED")
    if not record.exact_scope or record.overbroad_scope:
        raise ValueError("EXTENSION_ACTIVATION_EXACT_SCOPE_REQUIRED")
    if record.approval_ref in MISSING_APPROVAL_REFS:
        raise ValueError("EXTENSION_ACTIVATION_APPROVAL_REQUIRED")
    _validate_safe_ref_list(
        record.capability_refs, "EXTENSION_ACTIVATION_CAPABILITY_REF_REQUIRED"
    )
    _validate_safe_ref_list(
        record.requested_grant_refs,
        "EXTENSION_ACTIVATION_REQUESTED_GRANT_REF_REQUIRED",
    )
    _validate_safe_ref_list(
        record.audit_refs, "EXTENSION_ACTIVATION_AUDIT_REF_REQUIRED"
    )
    if record.grant_status == ExtensionActivationGrantStatus.granted.value:
        if record.staleness_status != ExtensionActivationGrantStaleness.current.value:
            raise ValueError("EXTENSION_ACTIVATION_STALE_GRANT_DENIED")
    return record


def assert_extension_activation_grant_treatable_as_active(
    record: ExtensionActivationGrantRecord,
) -> ExtensionActivationGrantRecord:
    validate_extension_activation_grant_record(record)
    if record.grant_status == ExtensionActivationGrantStatus.revoked.value:
        raise ValueError("EXTENSION_ACTIVATION_REVOKED_GRANT_DENIED")
    if record.grant_status == ExtensionActivationGrantStatus.stale.value:
        raise ValueError("EXTENSION_ACTIVATION_STALE_GRANT_DENIED")
    if record.grant_status != ExtensionActivationGrantStatus.granted.value:
        raise ValueError("EXTENSION_ACTIVATION_GRANT_NOT_ACTIVE")
    return record


def validate_extension_activation_grant_batch(
    records: list[ExtensionActivationGrantRecord],
) -> list[ExtensionActivationGrantRecord]:
    seen_refs: set[str] = set()
    seen_bindings: set[tuple[str, ...]] = set()
    validated: list[ExtensionActivationGrantRecord] = []
    for record in records:
        validate_extension_activation_grant_record(record)
        if record.activation_grant_ref in seen_refs:
            raise ValueError("EXTENSION_ACTIVATION_DUPLICATE_GRANT_DENIED")
        seen_refs.add(record.activation_grant_ref)
        binding = (
            record.package_ref,
            record.manifest_ref,
            record.version_ref,
            record.actor_ref,
            record.scope_ref,
            *sorted(record.capability_refs),
        )
        if binding in seen_bindings:
            raise ValueError("EXTENSION_ACTIVATION_DUPLICATE_GRANT_DENIED")
        seen_bindings.add(binding)
        validated.append(record)
    return validated


def validate_extension_activation_revocation_record(
    record: ExtensionActivationRevocationRecord,
) -> ExtensionActivationRevocationRecord:
    for field_name in ACTIVATION_GRANT_DENIED_TRUE_FLAGS:
        if getattr(record, field_name):
            raise ValueError(f"EXTENSION_ACTIVATION_{field_name.upper()}_DENIED")
    if not record.exact_scope:
        raise ValueError("EXTENSION_ACTIVATION_EXACT_SCOPE_REQUIRED")
    if record.approval_ref in MISSING_APPROVAL_REFS:
        raise ValueError("EXTENSION_ACTIVATION_APPROVAL_REQUIRED")
    _validate_safe_ref_list(
        record.audit_refs, "EXTENSION_ACTIVATION_AUDIT_REF_REQUIRED"
    )
    return record


def revoke_extension_activation_grant(
    grant: ExtensionActivationGrantRecord,
    revocation: ExtensionActivationRevocationRecord,
) -> ExtensionActivationGrantRecord:
    validate_extension_activation_grant_record(grant)
    validate_extension_activation_revocation_record(revocation)
    binding_pairs = (
        (
            "activation_grant_ref",
            grant.activation_grant_ref,
            revocation.activation_grant_ref,
        ),
        ("package_ref", grant.package_ref, revocation.package_ref),
        ("manifest_ref", grant.manifest_ref, revocation.manifest_ref),
        ("version_ref", grant.version_ref, revocation.version_ref),
        ("actor_ref", grant.actor_ref, revocation.actor_ref),
        ("approval_ref", grant.approval_ref, revocation.approval_ref),
        ("scope_ref", grant.scope_ref, revocation.scope_ref),
    )
    for _field_name, grant_value, revocation_value in binding_pairs:
        if grant_value != revocation_value:
            raise ValueError("EXTENSION_ACTIVATION_REVOCATION_BINDING_MISMATCH")
    return grant.model_copy(
        update={
            "grant_status": ExtensionActivationGrantStatus.revoked,
            "revocation_ref": revocation.revocation_ref,
            "audit_refs": list(
                dict.fromkeys([*grant.audit_refs, *revocation.audit_refs])
            ),
            "receipt_refs": list(
                dict.fromkeys([*grant.receipt_refs, *revocation.receipt_refs])
            ),
            "safe_summary": (
                "Activation grant is revoked and cannot be treated as active; "
                "runtime import and execution remain disabled."
            ),
        }
    )
