from __future__ import annotations

import re
from datetime import datetime

from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityCostClass,
    CapabilityHealthStatus,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityCatalogEntry,
    CapabilityManifest,
)
from ultimate_ai_agent.core.extension_catalog.contracts import (
    ExtensionCallablePosture,
    ExtensionCatalogVisibilityStatus,
    InspectableExtensionCatalog,
    InspectableExtensionCatalogEntry,
)
from ultimate_ai_agent.core.extension_catalog.ecosystem import (
    extension_availability_snapshot_ref,
    validate_extension_catalog_entry_for_development,
)
from ultimate_ai_agent.core.providers import (
    GovernedProviderInvocationReadiness,
    ProviderCapability,
    ProviderCostClass,
    ProviderManifest,
    ProviderStatus,
)
from ultimate_ai_agent.core.time import utc_now

from .contracts import (
    AuthorityPosture,
    CapabilityAvailabilitySnapshot,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    CostPosture,
    FreshnessStatus,
    HealthStatus,
    ResourceBudgetStatus,
    SafeDisableStatus,
    build_capability_availability_snapshot,
)


_REF_FRAGMENT_RE = re.compile(r"[^a-z0-9_.:-]+")


def snapshot_from_capability_manifest(
    manifest: CapabilityManifest,
    *,
    checked_at: datetime | None = None,
    compatibility_status: CompatibilityStatus = CompatibilityStatus.unknown,
    configuration_status: ConfigurationStatus = ConfigurationStatus.unknown,
    health_status: HealthStatus = HealthStatus.unknown,
    authority_posture: AuthorityPosture | None = None,
    resource_status: ResourceBudgetStatus = ResourceBudgetStatus.unknown,
    safe_disable_status: SafeDisableStatus = SafeDisableStatus.unknown,
    freshness_status: FreshnessStatus = FreshnessStatus.unknown,
    expires_at: datetime | None = None,
    evidence_refs: list[str] | None = None,
    probe_refs: list[str] | None = None,
    reason_codes: list[str] | None = None,
    blocker_codes: list[str] | None = None,
    source_ref: str | None = None,
    safe_summary: str | None = None,
) -> CapabilityAvailabilitySnapshot:
    """Normalize declaration metadata without inferring runtime observations."""

    capability_fragment = _ref_fragment(manifest.id)
    catalog_status = (
        CatalogStatus.unsupported
        if manifest.quality.deprecated
        else CatalogStatus.supported
    )
    posture = authority_posture or _manifest_authority_posture(manifest)
    return build_capability_availability_snapshot(
        snapshot_ref=f"capability-availability-ref:{capability_fragment}",
        capability_ref=f"capability-ref:{capability_fragment}",
        catalog_status=catalog_status,
        compatibility_status=compatibility_status,
        configuration_status=configuration_status,
        health_status=health_status,
        authority_posture=posture,
        resource_status=resource_status,
        cost_posture=_capability_cost_posture(manifest.estimated_cost_class),
        safe_disable_status=safe_disable_status,
        declared_or_observed_version_ref=(
            f"version-ref:{_ref_fragment(manifest.version)}"
        ),
        checked_at=checked_at or utc_now(),
        expires_at=expires_at,
        freshness_status=freshness_status,
        reason_codes=[
            "CAPABILITY_MANIFEST_DECLARATION_NORMALIZED",
            *(reason_codes or []),
        ],
        blocker_codes=blocker_codes or [],
        evidence_refs=evidence_refs or [],
        probe_refs=probe_refs or [],
        source_ref=(source_ref or f"capability-manifest-ref:{capability_fragment}"),
        safe_summary=(
            safe_summary
            or "Capability declaration normalized without assuming configuration, health, resources, or execution authority."
        ),
    )


def snapshot_from_capability_catalog_entry(
    entry: CapabilityCatalogEntry,
    *,
    checked_at: datetime | None = None,
    compatibility_status: CompatibilityStatus = CompatibilityStatus.unknown,
    configuration_status: ConfigurationStatus = ConfigurationStatus.unknown,
    authority_posture: AuthorityPosture | None = None,
    resource_status: ResourceBudgetStatus = ResourceBudgetStatus.unknown,
    safe_disable_status: SafeDisableStatus = SafeDisableStatus.unknown,
    freshness_status: FreshnessStatus = FreshnessStatus.unknown,
    expires_at: datetime | None = None,
    evidence_refs: list[str] | None = None,
    probe_refs: list[str] | None = None,
    reason_codes: list[str] | None = None,
    blocker_codes: list[str] | None = None,
    source_ref: str | None = None,
    safe_summary: str | None = None,
) -> CapabilityAvailabilitySnapshot:
    """Normalize catalog disclosure while preserving unknown configuration."""

    capability_fragment = _ref_fragment(entry.id)
    catalog_status = (
        CatalogStatus.unsupported if entry.deprecated else CatalogStatus.supported
    )
    posture = authority_posture or (
        AuthorityPosture.approval_required
        if entry.approval_required
        else AuthorityPosture.eligible_for_policy_evaluation
    )
    return build_capability_availability_snapshot(
        snapshot_ref=f"capability-availability-ref:{capability_fragment}",
        capability_ref=f"capability-ref:{capability_fragment}",
        catalog_status=catalog_status,
        compatibility_status=compatibility_status,
        configuration_status=configuration_status,
        health_status=_catalog_health_status(entry.health_status),
        authority_posture=posture,
        resource_status=resource_status,
        cost_posture=_capability_cost_posture(entry.estimated_cost_class),
        safe_disable_status=safe_disable_status,
        checked_at=checked_at or utc_now(),
        expires_at=expires_at,
        freshness_status=freshness_status,
        reason_codes=[
            "CAPABILITY_CATALOG_ENTRY_NORMALIZED",
            *entry.reason_codes,
            *(reason_codes or []),
        ],
        blocker_codes=blocker_codes or [],
        evidence_refs=evidence_refs or [],
        probe_refs=probe_refs or [],
        source_ref=(source_ref or f"capability-catalog-ref:{capability_fragment}"),
        safe_summary=(
            safe_summary
            or "Capability catalog entry normalized without treating visibility or health metadata as execution authority."
        ),
    )


def snapshot_from_provider_manifest(
    manifest: ProviderManifest,
    *,
    capability: ProviderCapability | None = None,
    readiness: GovernedProviderInvocationReadiness | None = None,
    checked_at: datetime | None = None,
    compatibility_status: CompatibilityStatus = CompatibilityStatus.unknown,
    configuration_status: ConfigurationStatus = ConfigurationStatus.unknown,
    health_status: HealthStatus | None = None,
    resource_status: ResourceBudgetStatus = ResourceBudgetStatus.unknown,
    safe_disable_status: SafeDisableStatus = SafeDisableStatus.unknown,
    freshness_status: FreshnessStatus = FreshnessStatus.unknown,
    expires_at: datetime | None = None,
    evidence_refs: list[str] | None = None,
    probe_refs: list[str] | None = None,
    reason_codes: list[str] | None = None,
    blocker_codes: list[str] | None = None,
    source_ref: str | None = None,
    safe_summary: str | None = None,
) -> CapabilityAvailabilitySnapshot:
    """Normalize one exact provider capability; provider enabled is not configured."""

    selected = capability or _single_provider_capability(manifest)
    if selected not in manifest.capabilities:
        raise ValueError("PROVIDER_CAPABILITY_NOT_DECLARED")
    provider_fragment = _ref_fragment(manifest.provider_id)
    capability_fragment = _ref_fragment(selected.value)
    catalog_status = (
        CatalogStatus.unsupported
        if manifest.status == ProviderStatus.deprecated.value
        else CatalogStatus.supported
    )
    readiness_blockers = list(readiness.blocker_codes) if readiness else []
    readiness_reasons = ["PROVIDER_READINESS_POSTURE_NORMALIZED"] if readiness else []
    return build_capability_availability_snapshot(
        snapshot_ref=(
            f"capability-availability-ref:{provider_fragment}:{capability_fragment}"
        ),
        capability_ref=(f"capability-ref:{provider_fragment}:{capability_fragment}"),
        provider_ref=f"provider-ref:{provider_fragment}",
        catalog_status=catalog_status,
        compatibility_status=compatibility_status,
        configuration_status=configuration_status,
        health_status=health_status or _provider_health_status(manifest),
        authority_posture=AuthorityPosture.blocked,
        resource_status=resource_status,
        cost_posture=_provider_cost_posture(manifest.cost_class),
        safe_disable_status=safe_disable_status,
        declared_or_observed_version_ref=(
            f"version-ref:{_ref_fragment(manifest.version)}"
        ),
        checked_at=checked_at or utc_now(),
        expires_at=expires_at,
        freshness_status=freshness_status,
        reason_codes=[
            "PROVIDER_MANIFEST_DECLARATION_NORMALIZED",
            *readiness_reasons,
            *(reason_codes or []),
        ],
        blocker_codes=[
            "PROVIDER_MANIFEST_DOES_NOT_GRANT_EXECUTION_AUTHORITY",
            *readiness_blockers,
            *(blocker_codes or []),
        ],
        evidence_refs=evidence_refs or [],
        probe_refs=probe_refs or [],
        source_ref=(source_ref or f"provider-manifest-ref:{provider_fragment}"),
        safe_summary=(
            safe_summary
            or "Provider declaration and readiness metadata normalized without inferring configuration, compatibility, budget, health, or invocation authority."
        ),
    )


def snapshot_from_extension_catalog_entry(
    entry: InspectableExtensionCatalogEntry,
    *,
    capability_ref: str | None = None,
    checked_at: datetime | None = None,
    compatibility_status: CompatibilityStatus = CompatibilityStatus.unknown,
    configuration_status: ConfigurationStatus = ConfigurationStatus.not_configured,
    health_status: HealthStatus = HealthStatus.unknown,
    resource_status: ResourceBudgetStatus = ResourceBudgetStatus.unknown,
    cost_posture: CostPosture = CostPosture.unknown,
    safe_disable_status: SafeDisableStatus = SafeDisableStatus.unknown,
    freshness_status: FreshnessStatus = FreshnessStatus.current,
    expires_at: datetime | None = None,
    evidence_refs: list[str] | None = None,
    probe_refs: list[str] | None = None,
    reason_codes: list[str] | None = None,
    blocker_codes: list[str] | None = None,
) -> CapabilityAvailabilitySnapshot:
    """Normalize inspectable extension metadata as non-callable runtime posture."""

    declared_ref = capability_ref
    if declared_ref is None:
        if len(entry.declared_capabilities) != 1:
            raise ValueError("EXTENSION_EXACT_CAPABILITY_REF_REQUIRED")
        declared_ref = entry.declared_capabilities[0].capability_ref
    if declared_ref not in {
        item.capability_ref for item in entry.declared_capabilities
    }:
        raise ValueError("EXTENSION_CAPABILITY_NOT_DECLARED")
    package_fragment = _ref_fragment(entry.package_identity.package_ref)
    capability_fragment = _ref_fragment(declared_ref)
    visibility_supported = entry.visibility_status in {
        ExtensionCatalogVisibilityStatus.implemented.value,
        ExtensionCatalogVisibilityStatus.partial.value,
    }
    callable_blocked = entry.callable_posture in {
        ExtensionCallablePosture.inspectable_only.value,
        ExtensionCallablePosture.blocked_runtime.value,
        ExtensionCallablePosture.future_exact_lane_required.value,
    }
    catalog_blockers = (
        ["EXTENSION_CATALOG_ENTRY_NOT_CALLABLE"] if callable_blocked else []
    )
    return build_capability_availability_snapshot(
        snapshot_ref=extension_availability_snapshot_ref(entry, declared_ref),
        capability_ref=f"capability-ref:{capability_fragment}",
        adapter_ref=f"adapter-ref:{package_fragment}",
        catalog_status=(
            CatalogStatus.supported
            if visibility_supported
            else CatalogStatus.unsupported
        ),
        compatibility_status=compatibility_status,
        configuration_status=configuration_status,
        health_status=health_status,
        authority_posture=AuthorityPosture.blocked,
        resource_status=resource_status,
        cost_posture=cost_posture,
        safe_disable_status=safe_disable_status,
        declared_or_observed_version_ref=entry.package_identity.version_ref,
        checked_at=checked_at or utc_now(),
        expires_at=expires_at,
        freshness_status=freshness_status,
        reason_codes=[
            "INSPECTABLE_EXTENSION_CATALOG_ENTRY_NORMALIZED",
            *(reason_codes or []),
        ],
        blocker_codes=[
            *catalog_blockers,
            *(blocker_codes or []),
        ],
        evidence_refs=list(
            dict.fromkeys(
                [
                    *entry.review_evidence_refs,
                    *(evidence_refs or []),
                ]
            )
        ),
        probe_refs=probe_refs or [],
        source_ref=entry.catalog_entry_ref,
        safe_summary=(
            "Inspectable extension metadata normalized; catalog visibility and review posture do not enable runtime import or execution."
        ),
    )


def snapshots_from_extension_catalog(
    catalog: InspectableExtensionCatalog,
    *,
    checked_at: datetime | None = None,
) -> list[CapabilityAvailabilitySnapshot]:
    """Normalize every declared extension capability without minting authority."""

    observed_at = checked_at or utc_now()
    snapshots: list[CapabilityAvailabilitySnapshot] = []
    for entry in catalog.entries:
        validation = validate_extension_catalog_entry_for_development(entry)
        compatibility_status = CompatibilityStatus(validation.compatibility_status)
        for capability in entry.declared_capabilities:
            snapshots.append(
                snapshot_from_extension_catalog_entry(
                    entry,
                    capability_ref=capability.capability_ref,
                    checked_at=observed_at,
                    compatibility_status=compatibility_status,
                    configuration_status=ConfigurationStatus.not_configured,
                    health_status=HealthStatus.unknown,
                    resource_status=ResourceBudgetStatus.unknown,
                    cost_posture=CostPosture.unknown,
                    safe_disable_status=SafeDisableStatus.unknown,
                    freshness_status=FreshnessStatus.current,
                    evidence_refs=[validation.validation_ref],
                    reason_codes=[
                        "EXTENSION_REQUEST_SCOPED_INVOCATION_DECISION_REQUIRED"
                    ],
                    blocker_codes=[
                        *validation.blocker_codes,
                        "EXTENSION_CONFIGURATION_NOT_PRESENT",
                        "EXTENSION_HEALTH_NOT_OBSERVED",
                        "EXTENSION_SAFE_DISABLE_STATUS_UNKNOWN",
                        "EXTENSION_BUDGET_STATUS_UNKNOWN",
                    ],
                )
            )
    return snapshots


def _manifest_authority_posture(manifest: CapabilityManifest) -> AuthorityPosture:
    if manifest.approval_required or manifest.safety.approval_required:
        return AuthorityPosture.approval_required
    if manifest.side_effects.value in {"write", "external", "destructive"}:
        return AuthorityPosture.lease_required
    return AuthorityPosture.eligible_for_policy_evaluation


def _capability_cost_posture(cost_class: CapabilityCostClass) -> CostPosture:
    if cost_class in {CapabilityCostClass.metered, CapabilityCostClass.high}:
        return CostPosture.metered
    if cost_class == CapabilityCostClass.none:
        return CostPosture.not_metered
    return CostPosture.unknown


def _provider_cost_posture(cost_class: str) -> CostPosture:
    if cost_class in {
        ProviderCostClass.paid.value,
        ProviderCostClass.enterprise.value,
    }:
        return CostPosture.metered
    if cost_class in {
        ProviderCostClass.free_no_key.value,
        ProviderCostClass.free_with_key.value,
    }:
        return CostPosture.not_metered
    return CostPosture.unknown


def _catalog_health_status(status: CapabilityHealthStatus) -> HealthStatus:
    return {
        CapabilityHealthStatus.healthy: HealthStatus.healthy,
        CapabilityHealthStatus.degraded: HealthStatus.degraded,
        CapabilityHealthStatus.unhealthy: HealthStatus.unhealthy,
        CapabilityHealthStatus.unknown: HealthStatus.unknown,
    }[status]


def _provider_health_status(manifest: ProviderManifest) -> HealthStatus:
    if manifest.health_metadata is None:
        return HealthStatus.unknown
    return {
        "healthy": HealthStatus.healthy,
        "degraded": HealthStatus.degraded,
        "unhealthy": HealthStatus.unhealthy,
        "stale": HealthStatus.stale,
    }.get(manifest.health_metadata.status, HealthStatus.unknown)


def _single_provider_capability(manifest: ProviderManifest) -> ProviderCapability:
    if len(manifest.capabilities) != 1:
        raise ValueError("PROVIDER_EXACT_CAPABILITY_REQUIRED")
    return ProviderCapability(manifest.capabilities[0])


def _ref_fragment(value: str) -> str:
    normalized = _REF_FRAGMENT_RE.sub("-", value.strip().lower()).strip("-:.")
    if not normalized:
        raise ValueError("CAPABILITY_AVAILABILITY_REF_FRAGMENT_REQUIRED")
    return normalized
