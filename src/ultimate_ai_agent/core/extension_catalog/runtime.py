from hashlib import sha256
from pathlib import Path

from ultimate_ai_agent.core.extension_catalog.contracts import (
    ExtensionActivationStatus,
    ExtensionBlockedState,
    ExtensionCallablePosture,
    ExtensionCapabilityKind,
    ExtensionCatalogVisibilityStatus,
    ExtensionGrantStatus,
    ExtensionHashStatus,
    ExtensionPackageKind,
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
    validate_inspectable_extension_catalog,
)


INSPECTABLE_EXTENSION_CATALOG_DOCS = [
    "doc:plugin-skill-ecosystem-boundary",
    "doc:inspectable-extension-catalog",
    "doc:extension-activation-grants",
    "doc:goatcitadel-catchup-extensibility-final",
]

INSPECTABLE_EXTENSION_CATALOG_SCHEMAS = [
    "schema:plugin-skill-trust-manifest",
    "schema:inspectable-extension-catalog",
    "schema:extension-activation-grant",
]

EXTENSION_CATALOG_BLOCKED_CAPABILITIES = [
    "callable_extension_catalog",
    "plugin_runtime_import",
    "arbitrary_plugin_execution",
    "skill_runtime_import",
    "connector_writes",
    "shell_subprocess_execution",
    "unrestricted_network_access",
    "browser_automation",
    "mobile_control",
    "public_distribution",
]

_REPO_ROOT = Path(__file__).resolve().parents[4]


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


def build_default_inspectable_extension_catalog() -> InspectableExtensionCatalog:
    catalog = InspectableExtensionCatalog(
        catalog_ref="inspectable-catalog:uaa-extension-catalog-v1",
        generated_from_ref="boundary:uaa-p2-049",
        docs_refs=list(INSPECTABLE_EXTENSION_CATALOG_DOCS),
        schema_refs=list(INSPECTABLE_EXTENSION_CATALOG_SCHEMAS),
        developer_guidance_refs=[
            "doc:plugin-skill-ecosystem-boundary",
            "doc:goatcitadel-catchup-extensibility-final",
        ],
        final_hardening_refs=[
            "verifier:goatcitadel-catchup-extensibility-final",
            "scoreboard:uaa-goatcitadel-catchup",
        ],
        blocked_capabilities=list(EXTENSION_CATALOG_BLOCKED_CAPABILITIES),
        safe_summary=(
            "Read-only extension catalog metadata; packages remain non-callable "
            "and runtime import stays disabled."
        ),
        entries=[
            InspectableExtensionCatalogEntry(
                catalog_entry_ref="inspectable-catalog-entry:uaa-plugin-skill-boundary",
                manifest_ref="plugin-skill-manifest:uaa-plugin-skill-boundary",
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
                ],
                safe_adoption_posture=ExtensionSafeAdoptionPosture.repo_owned_metadata_only,
                safe_summary=(
                    "Repo-owned boundary metadata is inspectable; it is not "
                    "callable and grants no runtime authority."
                ),
            ),
            InspectableExtensionCatalogEntry(
                catalog_entry_ref="inspectable-catalog-entry:unknown-extension-candidate",
                manifest_ref="plugin-skill-manifest:unknown-candidate",
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
                safe_summary=(
                    "Unknown extension candidates are visible as blocked "
                    "metadata only and cannot become callable."
                ),
            ),
        ],
    )
    return validate_inspectable_extension_catalog(catalog)
