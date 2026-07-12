from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ultimate_ai_agent.core.extension_catalog.contracts import (
    SAFE_REF_PATTERN,
    ExtensionHashStatus,
    ExtensionProvenanceStatus,
    ExtensionTrustPosture,
    InspectableExtensionCatalog,
    InspectableExtensionCatalogEntry,
    _ExtensionCatalogModel,
)
from ultimate_ai_agent.core.extension_catalog.runtime import (
    PINNED_EXTENSION_FILE_HASHES_BY_REF,
    PINNED_EXTENSION_IDENTITIES,
    build_default_inspectable_extension_catalog,
)


class ExtensionDeveloperValidationStatus(str, Enum):
    validated_metadata_only = "validated_metadata_only"
    blocked = "blocked"


class ExtensionSignatureStatus(str, Enum):
    not_present = "not_present"
    unknown = "unknown"


class ExtensionDeveloperValidationResult(_ExtensionCatalogModel):
    schema_version: Literal["uaa_extension_developer_validation.v1"] = (
        "uaa_extension_developer_validation.v1"
    )
    validation_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    catalog_entry_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    package_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    manifest_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    version_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    status: ExtensionDeveloperValidationStatus
    compatibility_status: Literal["supported", "unknown"]
    configuration_status: Literal["not_configured"] = "not_configured"
    health_status: Literal["unknown"] = "unknown"
    authority_posture: Literal["blocked"] = "blocked"
    resource_status: Literal["unknown"] = "unknown"
    safe_disable_status: Literal["unknown"] = "unknown"
    provenance_status: ExtensionProvenanceStatus
    reviewed_hash_count: int = Field(..., ge=0)
    declared_hash_count: int = Field(..., ge=0)
    hashes_verified_against_pinned_values: bool
    signature_status: ExtensionSignatureStatus
    signature_verified: Literal[False] = False
    safe_disable_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    rollback_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    reason_codes: list[str] = Field(default_factory=list)
    blocker_codes: list[str] = Field(default_factory=list)
    activation_metadata_grants_authority: Literal[False] = False
    catalog_visibility_grants_authority: Literal[False] = False
    runtime_import_enabled: Literal[False] = False
    execution_enabled: Literal[False] = False
    safe_summary: str = Field(..., min_length=1, max_length=500)

    @field_validator("reason_codes", "blocker_codes")
    @classmethod
    def validate_codes(cls, values: list[str]) -> list[str]:
        if any(re.fullmatch(r"[A-Z][A-Z0-9_]*", value) is None for value in values):
            raise ValueError("EXTENSION_DEVELOPER_CODE_INVALID")
        if len(values) != len(set(values)):
            raise ValueError("EXTENSION_DEVELOPER_CODE_DUPLICATE")
        return values

    @model_validator(mode="after")
    def validate_result(self) -> "ExtensionDeveloperValidationResult":
        if self.reviewed_hash_count > self.declared_hash_count:
            raise ValueError("EXTENSION_DEVELOPER_REVIEWED_HASH_COUNT_INVALID")
        if (
            self.status
            == ExtensionDeveloperValidationStatus.validated_metadata_only.value
        ):
            if self.blocker_codes:
                raise ValueError("EXTENSION_DEVELOPER_VALIDATED_BLOCKERS_DENIED")
            if not self.hashes_verified_against_pinned_values:
                raise ValueError("EXTENSION_DEVELOPER_PINNED_HASHES_REQUIRED")
            if self.compatibility_status != "supported":
                raise ValueError("EXTENSION_DEVELOPER_COMPATIBILITY_REQUIRED")
            if self.provenance_status != ExtensionProvenanceStatus.reviewed.value:
                raise ValueError("EXTENSION_DEVELOPER_PROVENANCE_REQUIRED")
        if (
            self.status == ExtensionDeveloperValidationStatus.blocked.value
            and not self.blocker_codes
        ):
            raise ValueError("EXTENSION_DEVELOPER_BLOCKER_REQUIRED")
        if self.status == ExtensionDeveloperValidationStatus.blocked.value:
            if self.compatibility_status != "unknown":
                raise ValueError("EXTENSION_DEVELOPER_BLOCKED_COMPATIBILITY_INVALID")
            if (
                "EXTENSION_PROVENANCE_NOT_REVIEWED" in self.blocker_codes
                and self.provenance_status == ExtensionProvenanceStatus.reviewed.value
            ):
                raise ValueError("EXTENSION_DEVELOPER_PROVENANCE_BLOCKER_CONTRADICTION")
            if (
                "EXTENSION_PINNED_HASH_VALIDATION_FAILED" in self.blocker_codes
                and self.hashes_verified_against_pinned_values
            ):
                raise ValueError("EXTENSION_DEVELOPER_HASH_BLOCKER_CONTRADICTION")
        return self


class ExtensionEcosystemReadModel(InspectableExtensionCatalog):
    schema_version: Literal["uaa_extension_ecosystem_read_model.v1"] = (
        "uaa_extension_ecosystem_read_model.v1"
    )
    availability_snapshot_refs: list[str] = Field(default_factory=list)
    availability_snapshot_count: int = Field(..., ge=0)
    developer_validation_results: list[ExtensionDeveloperValidationResult] = Field(
        default_factory=list
    )
    developer_validation_count: int = Field(..., ge=0)
    plugin_metadata_boundary_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    skill_marketplace_boundary_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    mcp_catalog_boundary_ref: str = Field(..., pattern=SAFE_REF_PATTERN)
    catalog_visibility_grants_authority: Literal[False] = False
    activation_metadata_grants_authority: Literal[False] = False
    request_scoped_invocation_decision_required: Literal[True] = True

    @model_validator(mode="after")
    def validate_ecosystem_counts(self) -> "ExtensionEcosystemReadModel":
        if self.availability_snapshot_count != len(self.availability_snapshot_refs):
            raise ValueError("EXTENSION_ECOSYSTEM_AVAILABILITY_COUNT_DRIFT")
        if self.developer_validation_count != len(self.developer_validation_results):
            raise ValueError("EXTENSION_ECOSYSTEM_VALIDATION_COUNT_DRIFT")
        expected_snapshot_refs = [
            extension_availability_snapshot_ref(entry, capability.capability_ref)
            for entry in self.entries
            for capability in entry.declared_capabilities
        ]
        if self.availability_snapshot_refs != expected_snapshot_refs:
            raise ValueError("EXTENSION_ECOSYSTEM_AVAILABILITY_BINDING_DRIFT")
        expected_results = [
            validate_extension_catalog_entry_for_development(entry)
            for entry in self.entries
        ]
        if [item.model_dump(mode="json") for item in self.developer_validation_results] != [
            item.model_dump(mode="json") for item in expected_results
        ]:
            raise ValueError("EXTENSION_ECOSYSTEM_VALIDATION_BINDING_DRIFT")
        return self


def validate_extension_catalog_entry_for_development(
    entry: InspectableExtensionCatalogEntry,
) -> ExtensionDeveloperValidationResult:
    package_ref = entry.package_identity.package_ref
    pinned_identity = PINNED_EXTENSION_IDENTITIES.get(package_ref)
    observed_hashes = {item.file_ref: item for item in entry.file_hashes}
    expected_file_refs = pinned_identity.file_refs if pinned_identity else frozenset()
    reviewed_hash_count = sum(
        item.hash_status == ExtensionHashStatus.reviewed.value
        and item.hash_value == PINNED_EXTENSION_FILE_HASHES_BY_REF.get(item.file_ref)
        for item in entry.file_hashes
    )
    hashes_verified = bool(pinned_identity) and (
        set(observed_hashes) == set(expected_file_refs)
        and reviewed_hash_count == len(expected_file_refs)
    )
    reviewed_provenance = (
        pinned_identity is not None
        and entry.provenance.source_ref == pinned_identity.source_ref
        and entry.provenance.review_ref == pinned_identity.review_ref
        and entry.provenance.provenance_status
        == ExtensionProvenanceStatus.reviewed.value
        and entry.trust_posture == ExtensionTrustPosture.reviewed_metadata.value
    )
    manifest_supported = bool(
        pinned_identity and entry.manifest_ref == pinned_identity.manifest_ref
    )
    version_supported = bool(
        pinned_identity
        and entry.package_identity.version_ref == pinned_identity.version_ref
    )
    declaration_supported = bool(
        pinned_identity
        and entry.catalog_entry_ref == pinned_identity.catalog_entry_ref
        and entry.package_identity.publisher_ref == pinned_identity.publisher_ref
        and entry.provenance.license_ref == pinned_identity.license_ref
        and getattr(entry, "safe_disable_ref", pinned_identity.safe_disable_ref)
        == pinned_identity.safe_disable_ref
        and getattr(entry, "rollback_ref", pinned_identity.rollback_ref)
        == pinned_identity.rollback_ref
        and entry.risk_class == pinned_identity.risk_class
        and tuple(
            (item.capability_ref, item.capability_kind, item.risk_class)
            for item in entry.declared_capabilities
        )
        == pinned_identity.capability_identities
        and tuple(
            (item.grant_ref, item.scope_ref, item.status)
            for item in entry.requested_grants
        )
        == pinned_identity.requested_grant_identities
    )
    blockers: list[str] = []
    if not manifest_supported:
        blockers.append("EXTENSION_MANIFEST_COMPATIBILITY_UNKNOWN")
    if not version_supported:
        blockers.append("EXTENSION_VERSION_COMPATIBILITY_UNKNOWN")
    if not reviewed_provenance:
        blockers.append("EXTENSION_PROVENANCE_NOT_REVIEWED")
    if not hashes_verified:
        blockers.append("EXTENSION_PINNED_HASH_VALIDATION_FAILED")
    if not declaration_supported:
        blockers.append("EXTENSION_DECLARATION_IDENTITY_MISMATCH")
    status = (
        ExtensionDeveloperValidationStatus.validated_metadata_only
        if not blockers
        else ExtensionDeveloperValidationStatus.blocked
    )
    return ExtensionDeveloperValidationResult(
        validation_ref=(
            "extension-developer-validation:"
            f"{entry.package_identity.package_ref.split(':', 1)[1]}"
        ),
        catalog_entry_ref=entry.catalog_entry_ref,
        package_ref=entry.package_identity.package_ref,
        manifest_ref=entry.manifest_ref,
        version_ref=entry.package_identity.version_ref,
        status=status,
        compatibility_status=("supported" if not blockers else "unknown"),
        provenance_status=(
            ExtensionProvenanceStatus.reviewed
            if reviewed_provenance
            else ExtensionProvenanceStatus.unknown
        ),
        reviewed_hash_count=reviewed_hash_count,
        declared_hash_count=len(entry.file_hashes),
        hashes_verified_against_pinned_values=hashes_verified,
        signature_status=ExtensionSignatureStatus.not_present,
        safe_disable_ref=(
            pinned_identity.safe_disable_ref
            if pinned_identity
            else "safe-disable-ref:unknown-extension-candidate"
        ),
        rollback_ref=(
            pinned_identity.rollback_ref
            if pinned_identity
            else "rollback-ref:unknown-extension-candidate:none"
        ),
        reason_codes=[
            "EXTENSION_METADATA_VALIDATED_WITHOUT_RUNTIME_IMPORT",
            "EXTENSION_SIGNATURE_NOT_PRESENT_OR_CLAIMED",
        ],
        blocker_codes=blockers,
        safe_summary=(
            "Extension metadata, provenance, version, and pinned file hashes were "
            "validated for inspection only; no signature, activation authority, "
            "runtime import, or execution is claimed."
            if not blockers
            else "Extension developer validation failed closed; metadata remains "
            "inspectable but cannot authorize activation, import, or execution."
        ),
    )


def extension_availability_snapshot_ref(
    entry: InspectableExtensionCatalogEntry,
    capability_ref: str,
) -> str:
    return (
        "capability-availability-ref:"
        f"{entry.package_identity.package_ref}:"
        f"{capability_ref}"
    )


def build_default_extension_ecosystem_read_model() -> ExtensionEcosystemReadModel:
    catalog = build_default_inspectable_extension_catalog()
    validation_results = [
        validate_extension_catalog_entry_for_development(entry)
        for entry in catalog.entries
    ]
    snapshot_refs = [
        extension_availability_snapshot_ref(entry, capability.capability_ref)
        for entry in catalog.entries
        for capability in entry.declared_capabilities
    ]
    return ExtensionEcosystemReadModel.model_validate(
        catalog.model_dump(mode="python")
        | {
            "schema_version": "uaa_extension_ecosystem_read_model.v1",
            "availability_snapshot_refs": snapshot_refs,
            "availability_snapshot_count": len(snapshot_refs),
            "developer_validation_results": validation_results,
            "developer_validation_count": len(validation_results),
            "plugin_metadata_boundary_ref": (
                "runtime-boundary-ref:plugin-metadata-posture"
            ),
            "skill_marketplace_boundary_ref": (
                "runtime-boundary-ref:skill-marketplace-posture"
            ),
            "mcp_catalog_boundary_ref": "runtime-boundary-ref:mcp-catalog-filtering",
        }
    )
