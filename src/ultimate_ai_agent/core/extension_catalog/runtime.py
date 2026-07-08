from hashlib import sha256
from pathlib import Path

from ultimate_ai_agent.core.extension_catalog.contracts import (
    ExtensionActivationStatus,
    ExtensionBlockedState,
    ExtensionCallablePosture,
    ExtensionCapabilityKind,
    ExtensionCatalogVisibilityStatus,
    ExtensionFullInstructionLoadPosture,
    ExtensionGrantStatus,
    ExtensionHashStatus,
    ExtensionPackageKind,
    ExtensionProgressiveDisclosureStatus,
    ExtensionProvenanceStatus,
    ExtensionRiskClass,
    ExtensionSafeAdoptionPosture,
    ExtensionTrustPosture,
    InspectableExtensionCapability,
    InspectableExtensionCatalog,
    InspectableExtensionCatalogEntry,
    InspectableExtensionFileHash,
    InspectableExtensionPackageIdentity,
    InspectableExtensionProvenance,
    InspectableExtensionRequestedGrant,
    SkillBundleProposal,
    SkillBundleProposalPostureReadModel,
    SkillBundleProposalStatus,
    SkillWriteApprovalGateReadModel,
    SkillWriteDiffPreview,
    SkillWriteProposal,
    SkillWriteProposalKind,
    SkillWriteReviewStatus,
    validate_skill_bundle_proposal_posture,
    validate_skill_write_approval_gate,
    validate_inspectable_extension_catalog,
)


INSPECTABLE_EXTENSION_CATALOG_DOCS = [
    "doc:plugin-skill-ecosystem-boundary",
    "doc:inspectable-extension-catalog",
    "doc:extension-activation-grants",
    "doc:runtime-extensibility-final",
    "doc:hermes-runtime-progressive-skill-disclosure",
    "doc:hermes-runtime-skill-write-approval-gate",
    "doc:hermes-runtime-skill-bundle-proposals",
]

INSPECTABLE_EXTENSION_CATALOG_SCHEMAS = [
    "schema:plugin-skill-trust-manifest",
    "schema:inspectable-extension-catalog",
    "schema:extension-activation-grant",
]

EXTENSION_CATALOG_BLOCKED_CAPABILITIES = [
    "callable_extension_catalog",
    "automatic_skill_instruction_loading",
    "hidden_skill_activation",
    "full_instruction_auto_load",
    "plugin_runtime_import",
    "arbitrary_plugin_execution",
    "skill_runtime_import",
    "external_marketplace_fetch",
    "direct_skill_write",
    "automatic_skill_enablement",
    "skill_bundle_activation",
    "skill_bundle_tool_execution",
    "skill_bundle_context_injection",
    "connector_writes",
    "shell_subprocess_execution",
    "unrestricted_network_access",
    "browser_automation",
    "mobile_control",
    "public_distribution",
]

_REPO_ROOT = Path(__file__).resolve().parents[4]


SKILL_WRITE_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:skill-write-no-direct-file-write",
    "blocked-authority:skill-write-no-runtime-import",
    "blocked-authority:skill-write-no-execution",
    "blocked-authority:skill-write-no-connector-write",
    "blocked-authority:skill-write-no-shell-execution",
    "blocked-authority:skill-write-no-provider-model-call",
    "blocked-authority:skill-write-no-browser-automation",
    "blocked-authority:skill-write-no-production-authority",
]


SKILL_BUNDLE_BLOCKED_AUTHORITY_REFS = [
    "blocked-authority:skill-bundle-no-activation",
    "blocked-authority:skill-bundle-no-skill-enable",
    "blocked-authority:skill-bundle-no-tool-execution",
    "blocked-authority:skill-bundle-no-context-injection",
    "blocked-authority:skill-bundle-no-runtime-import",
    "blocked-authority:skill-bundle-no-provider-model-call",
    "blocked-authority:skill-bundle-no-connector-write",
    "blocked-authority:skill-bundle-no-shell-execution",
    "blocked-authority:skill-bundle-no-browser-automation",
    "blocked-authority:skill-bundle-no-production-authority",
]


def _safe_file_hash(file_ref: str, rel_path: str) -> InspectableExtensionFileHash:
    path = _REPO_ROOT / rel_path
    if not path.exists():
        return InspectableExtensionFileHash(
            file_ref=file_ref,
            hash_status=ExtensionHashStatus.missing,
        )
    digest = sha256(path.read_bytes()).hexdigest()
    return InspectableExtensionFileHash(
        file_ref=file_ref,
        hash_value=f"sha256:{digest}",
        hash_status=ExtensionHashStatus.reviewed,
    )


def build_default_skill_write_approval_gate() -> SkillWriteApprovalGateReadModel:
    gate = SkillWriteApprovalGateReadModel(
        gate_ref="skill-write-gate:hermes-runtime-adoption-phase-14",
        proposal_count=1,
        review_queue_ref="review-queue:skill-write-proposals",
        required_authority_ref="authority-ref:local-approval-skill-write-review",
        blocked_authority_refs=list(SKILL_WRITE_BLOCKED_AUTHORITY_REFS),
        verifier_refs=["verifier:hermes-runtime-adoption-phase-14"],
        next_safe_action_refs=[
            "next-safe-action:review-staged-skill-diff-preview",
            "next-safe-action:keep-skill-write-blocked-until-exact-lane",
        ],
        safe_summary=(
            "Skill write proposals are staged for review with diff-preview refs; "
            "no skill files are written and no skill is enabled or imported."
        ),
        proposals=[
            SkillWriteProposal(
                proposal_ref="skill-write-proposal:uaa-doc-helper-draft",
                proposal_kind=SkillWriteProposalKind.create_skill,
                skill_ref="skill:uaa-doc-helper-draft",
                target_skill_ref="skill-target:uaa-owned-skill-review-queue",
                staged_artifact_ref="staged-artifact:skill-write-doc-helper-draft",
                review_decision_ref="skill-write-review:awaiting-operator",
                review_status=SkillWriteReviewStatus.awaiting_operator_review,
                diff_previews=[
                    SkillWriteDiffPreview(
                        diff_preview_ref="skill-write-diff-preview:doc-helper",
                        target_ref="skill-target:uaa-owned-skill-review-queue",
                        change_summary_ref="change-summary:skill-write-doc-helper",
                        safe_summary=(
                            "Proposed skill metadata and instructions are "
                            "represented by safe refs only; raw diff and file "
                            "content are omitted."
                        ),
                    )
                ],
                blocked_execution_labels=[
                    "blocked-label:skill-write-file-write",
                    "blocked-label:skill-runtime-import",
                    "blocked-label:skill-execution",
                ],
                proof_refs=["proof-ref:hermes-runtime-adoption:phase-14"],
                receipt_refs=[],
                safe_summary=(
                    "Draft skill write proposal awaits operator review and exact "
                    "future approval before any file mutation lane can exist."
                ),
            )
        ],
    )
    return validate_skill_write_approval_gate(gate)


def build_default_skill_bundle_proposal_posture() -> (
    SkillBundleProposalPostureReadModel
):
    posture = SkillBundleProposalPostureReadModel(
        posture_ref="skill-bundle-posture:hermes-runtime-adoption-phase-15",
        proposal_count=1,
        bundle_review_queue_ref="review-queue:skill-bundle-proposals",
        required_authority_ref="authority-ref:local-approval-skill-bundle-review",
        blocked_authority_refs=list(SKILL_BUNDLE_BLOCKED_AUTHORITY_REFS),
        verifier_refs=["verifier:hermes-runtime-adoption-phase-15"],
        next_safe_action_refs=[
            "next-safe-action:review-skill-bundle-proposal",
            "next-safe-action:map-constituent-skill-trust-before-activation",
            "next-safe-action:keep-bundle-activation-blocked-until-exact-lane",
        ],
        safe_summary=(
            "Skill bundles are proposal metadata only: they combine safe refs "
            "for skills, context, toolsets, authority profile, and verifier "
            "expectations without enabling skills, injecting context, importing "
            "runtime code, or executing tools."
        ),
        proposals=[
            SkillBundleProposal(
                proposal_ref="skill-bundle-proposal:founder-loop-review",
                bundle_ref="skill-bundle:founder-loop-review",
                bundle_name="Founder Loop Review Bundle",
                proposal_status=SkillBundleProposalStatus.proposal_only,
                skill_refs=[
                    "skill:uaa-skill-metadata-index",
                    "skill:operator-loop-review-helper",
                ],
                context_pack_refs=[
                    "context-pack:founder-loop-safe-summary",
                    "context-pack:authority-posture-safe-summary",
                ],
                toolset_refs=[
                    "toolset:read-only-inspection",
                    "toolset:proof-ref-inspection",
                ],
                authority_profile_ref="authority-profile:sealed-default",
                verification_refs=[
                    "verifier:hermes-runtime-adoption-phase-15",
                    "verifier:inspectable-extension-catalog",
                ],
                blocked_authority_refs=list(SKILL_BUNDLE_BLOCKED_AUTHORITY_REFS),
                proof_refs=["proof-ref:hermes-runtime-adoption:phase-15"],
                next_safe_action_refs=[
                    "next-safe-action:review-skill-bundle-constituents",
                    "next-safe-action:define-exact-activation-lane",
                ],
                safe_summary=(
                    "Proposed reusable operator-review bundle with safe refs for "
                    "skills, context, tools, authority profile, and verification; "
                    "activation and execution remain blocked."
                ),
            )
        ],
    )
    return validate_skill_bundle_proposal_posture(posture)


def build_default_inspectable_extension_catalog() -> InspectableExtensionCatalog:
    catalog = InspectableExtensionCatalog(
        catalog_ref="inspectable-catalog:uaa-extension-catalog-v1",
        generated_from_ref="boundary:uaa-p2-049",
        docs_refs=list(INSPECTABLE_EXTENSION_CATALOG_DOCS),
        schema_refs=list(INSPECTABLE_EXTENSION_CATALOG_SCHEMAS),
        developer_guidance_refs=[
            "doc:plugin-skill-ecosystem-boundary",
            "doc:runtime-extensibility-final",
        ],
        final_hardening_refs=[
            "verifier:runtime-extensibility-final",
            "verifier:hermes-runtime-adoption-phase-13",
            "scoreboard:uaa-runtime-capability-foundation",
        ],
        blocked_capabilities=list(EXTENSION_CATALOG_BLOCKED_CAPABILITIES),
        compact_skill_index_refs=[
            "compact-skill-index:uaa-owned-progressive-disclosure",
            "compact-skill-index:unknown-extension-candidates",
        ],
        progressive_disclosure_refs=[
            "progressive-disclosure:metadata-first-index",
            "progressive-disclosure:operator-selected-instructions",
        ],
        skill_write_approval_gate=build_default_skill_write_approval_gate(),
        skill_bundle_proposal_posture=build_default_skill_bundle_proposal_posture(),
        safe_summary=(
            "Read-only extension catalog metadata; packages remain non-callable "
            "and runtime import stays disabled. Skill entries disclose compact "
            "metadata first and never auto-load full instructions."
        ),
        entries=[
            InspectableExtensionCatalogEntry(
                catalog_entry_ref="inspectable-catalog-entry:uaa-plugin-skill-boundary",
                manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
                compact_skill_index_ref=(
                    "compact-skill-index:uaa-plugin-skill-boundary"
                ),
                metadata_summary_ref="skill-metadata:uaa-plugin-skill-boundary",
                package_identity=InspectableExtensionPackageIdentity(
                    package_ref="extension-package:uaa-plugin-skill-boundary",
                    package_name="UAA Plugin Skill Boundary",
                    package_kind=ExtensionPackageKind.tooling_bundle,
                    version_ref="version:uaa-p1-024",
                    publisher_ref="publisher:uaa-repo",
                ),
                provenance=InspectableExtensionProvenance(
                    source_ref="source:uaa-repo-owned-boundary",
                    review_ref="review:uaa-p1-024",
                    license_ref="license:repo",
                    provenance_status=ExtensionProvenanceStatus.reviewed,
                ),
                file_hashes=[
                    _safe_file_hash(
                        "file-ref:plugin-skill-ecosystem-boundary-doc",
                        "docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md",
                    ),
                    _safe_file_hash(
                        "file-ref:plugin-skill-trust-manifest-schema",
                        "docs/schemas/plugin_skill_trust_manifest.schema.json",
                    ),
                    _safe_file_hash(
                        "file-ref:inspectable-extension-catalog-schema",
                        "docs/schemas/inspectable_extension_catalog.schema.json",
                    ),
                ],
                declared_capabilities=[
                    InspectableExtensionCapability(
                        capability_ref="capability:extension-metadata-inspection",
                        capability_kind=ExtensionCapabilityKind.tooling_metadata,
                        risk_class=ExtensionRiskClass.low,
                        safe_purpose=(
                            "Inspect repo-owned extension trust metadata and "
                            "disabled runtime flags."
                        ),
                    )
                ],
                risk_class=ExtensionRiskClass.low,
                requested_grants=[
                    InspectableExtensionRequestedGrant(
                        grant_ref="grant-request:extension-metadata-inspection",
                        scope_ref="scope:read-only-inspection",
                        status=ExtensionGrantStatus.future_scoped,
                    )
                ],
                activation_status=ExtensionActivationStatus.future_scoped,
                blocked_state=ExtensionBlockedState.future_scoped,
                blocker_refs=["blocker:runtime-import-not-scoped"],
                audit_refs=["audit:uaa-p1-024", "audit:uaa-p2-049"],
                visibility_status=ExtensionCatalogVisibilityStatus.implemented,
                trust_posture=ExtensionTrustPosture.reviewed_metadata,
                callable_posture=ExtensionCallablePosture.inspectable_only,
                required_grant_refs=["grant-request:extension-metadata-inspection"],
                blocked_reason=(
                    "Metadata inspection is implemented, but runtime import and "
                    "callable execution require a later exact authority lane."
                ),
                review_evidence_refs=[
                    "audit:uaa-p1-024",
                    "audit:uaa-p2-049",
                    "audit:uaa-p2-050",
                    "audit:hermes-runtime-adoption-phase-13",
                ],
                safe_adoption_posture=ExtensionSafeAdoptionPosture.repo_owned_metadata_only,
                progressive_disclosure_status=(
                    ExtensionProgressiveDisclosureStatus.metadata_indexed
                ),
                full_instruction_load_posture=(
                    ExtensionFullInstructionLoadPosture.operator_selected_review_required
                ),
                safe_summary=(
                    "Repo-owned boundary metadata is inspectable; it is not "
                    "callable and grants no runtime authority."
                ),
            ),
            InspectableExtensionCatalogEntry(
                catalog_entry_ref="inspectable-catalog-entry:uaa-skill-metadata-index",
                manifest_ref="plugin-skill-manifest:uaa-skill-metadata-index",
                compact_skill_index_ref="compact-skill-index:uaa-skill-metadata",
                metadata_summary_ref="skill-metadata:uaa-skill-metadata-index",
                package_identity=InspectableExtensionPackageIdentity(
                    package_ref="extension-package:uaa-skill-metadata-index",
                    package_name="UAA Skill Metadata Index",
                    package_kind=ExtensionPackageKind.skill,
                    version_ref="version:hermes-runtime-adoption-phase-13",
                    publisher_ref="publisher:uaa-repo",
                ),
                provenance=InspectableExtensionProvenance(
                    source_ref="source:uaa-repo-owned-skill-index",
                    review_ref="review:hermes-runtime-adoption-phase-13",
                    license_ref="license:repo",
                    provenance_status=ExtensionProvenanceStatus.reviewed,
                ),
                file_hashes=[
                    _safe_file_hash(
                        "file-ref:skill-workbench-adoption-prompt-pack",
                        "docs/prompts/skill_workbench_adoption_prompt_pack.md",
                    ),
                    _safe_file_hash(
                        "file-ref:inspectable-extension-catalog-doc",
                        "docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md",
                    ),
                ],
                declared_capabilities=[
                    InspectableExtensionCapability(
                        capability_ref="capability:skill-metadata-index",
                        capability_kind=ExtensionCapabilityKind.documentation_helper,
                        risk_class=ExtensionRiskClass.low,
                        safe_purpose=(
                            "Expose compact skill metadata, trust source, review "
                            "status, and blocked runtime posture before any "
                            "full instruction review."
                        ),
                    ),
                    InspectableExtensionCapability(
                        capability_ref="capability:progressive-skill-disclosure",
                        capability_kind=ExtensionCapabilityKind.read_only_inspection,
                        risk_class=ExtensionRiskClass.low,
                        safe_purpose=(
                            "Keep full skill instructions operator-selected and "
                            "review-scoped instead of hidden runtime context."
                        ),
                    ),
                ],
                risk_class=ExtensionRiskClass.low,
                requested_grants=[
                    InspectableExtensionRequestedGrant(
                        grant_ref="grant-request:skill-metadata-inspection",
                        scope_ref="scope:read-only-inspection",
                        status=ExtensionGrantStatus.future_scoped,
                    )
                ],
                activation_status=ExtensionActivationStatus.future_scoped,
                blocked_state=ExtensionBlockedState.future_scoped,
                blocker_refs=[
                    "blocker:full-instruction-auto-load-not-scoped",
                    "blocker:skill-runtime-import-not-scoped",
                ],
                audit_refs=[
                    "audit:hermes-runtime-adoption-phase-13",
                    "audit:uaa-skill-workbench",
                ],
                visibility_status=ExtensionCatalogVisibilityStatus.implemented,
                trust_posture=ExtensionTrustPosture.reviewed_metadata,
                callable_posture=ExtensionCallablePosture.inspectable_only,
                required_grant_refs=["grant-request:skill-metadata-inspection"],
                blocked_reason=(
                    "Skill metadata is indexed, but full instruction loading "
                    "requires explicit operator selection and later review gates."
                ),
                review_evidence_refs=[
                    "audit:hermes-runtime-adoption-phase-13",
                    "audit:uaa-skill-workbench",
                ],
                safe_adoption_posture=ExtensionSafeAdoptionPosture.repo_owned_metadata_only,
                progressive_disclosure_status=(
                    ExtensionProgressiveDisclosureStatus.metadata_indexed
                ),
                full_instruction_load_posture=(
                    ExtensionFullInstructionLoadPosture.operator_selected_review_required
                ),
                safe_summary=(
                    "Compact skill metadata is inspectable; full instructions "
                    "are not auto-loaded and skill runtime import remains blocked."
                ),
            ),
            InspectableExtensionCatalogEntry(
                catalog_entry_ref="inspectable-catalog-entry:unknown-extension-candidate",
                manifest_ref="plugin-skill-manifest:unknown-candidate",
                compact_skill_index_ref=(
                    "compact-skill-index:unknown-extension-candidate"
                ),
                metadata_summary_ref="skill-metadata:unknown-extension-candidate",
                package_identity=InspectableExtensionPackageIdentity(
                    package_ref="extension-package:unknown-extension-candidate",
                    package_name="Unknown Extension Candidate",
                    package_kind=ExtensionPackageKind.plugin,
                    version_ref="version:unknown",
                    publisher_ref="publisher:unknown",
                ),
                provenance=InspectableExtensionProvenance(
                    source_ref="source:unknown",
                    review_ref="review:missing",
                    license_ref="license:unknown",
                    provenance_status=ExtensionProvenanceStatus.unknown,
                ),
                file_hashes=[
                    InspectableExtensionFileHash(
                        file_ref="file-ref:unknown-extension-candidate",
                        hash_status=ExtensionHashStatus.unknown,
                    )
                ],
                declared_capabilities=[
                    InspectableExtensionCapability(
                        capability_ref="capability:unknown-runtime-request",
                        capability_kind=ExtensionCapabilityKind.blocked_runtime,
                        risk_class=ExtensionRiskClass.critical,
                        safe_purpose=(
                            "Unknown runtime capability remains blocked until "
                            "static review and scoped approval exist."
                        ),
                    )
                ],
                risk_class=ExtensionRiskClass.critical,
                requested_grants=[
                    InspectableExtensionRequestedGrant(
                        grant_ref="grant-request:unknown-runtime",
                        scope_ref="scope:unknown",
                        status=ExtensionGrantStatus.blocked,
                    )
                ],
                activation_status=ExtensionActivationStatus.blocked,
                blocked_state=ExtensionBlockedState.unknown,
                blocker_refs=[
                    "blocker:provenance-unknown",
                    "blocker:file-hash-unknown",
                    "blocker:activation-not-approved",
                ],
                audit_refs=["audit:uaa-p2-049"],
                visibility_status=ExtensionCatalogVisibilityStatus.blocked,
                trust_posture=ExtensionTrustPosture.unknown_blocked,
                callable_posture=ExtensionCallablePosture.blocked_runtime,
                required_grant_refs=["grant-request:unknown-runtime"],
                blocked_reason=(
                    "Unknown extension candidates lack reviewed provenance, "
                    "reviewed hashes, and exact activation approval."
                ),
                review_evidence_refs=["audit:uaa-p2-049"],
                safe_adoption_posture=(
                    ExtensionSafeAdoptionPosture.blocked_until_scoped_milestone
                ),
                progressive_disclosure_status=ExtensionProgressiveDisclosureStatus.blocked,
                full_instruction_load_posture=(
                    ExtensionFullInstructionLoadPosture.blocked_runtime_import
                ),
                safe_summary=(
                    "Unknown extension candidates are visible as blocked "
                    "metadata only and cannot become callable."
                ),
            ),
        ],
    )
    return validate_inspectable_extension_catalog(catalog)
