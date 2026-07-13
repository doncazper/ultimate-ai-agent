from __future__ import annotations

from datetime import datetime, timedelta

from ultimate_ai_agent import __version__
from ultimate_ai_agent.core.capabilities.enums import (
    CapabilityCostClass,
    CapabilityHealthStatus,
    CapabilityKind,
    CoordinationMode,
    RiskLevel,
    SideEffectLevel,
)
from ultimate_ai_agent.core.capabilities.models import (
    CapabilityCatalogEntry,
    CapabilityManifest,
    SafetyPolicy,
)
from ultimate_ai_agent.core.extension_catalog import (
    build_default_inspectable_extension_catalog,
)
from ultimate_ai_agent.core.control_center.founder_loop_mission_refs import (
    FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
    FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
    FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.providers import (
    GovernedProviderInvocationReadiness,
    ProviderAuthRequirement,
    ProviderCapability,
    ProviderCostClass,
    ProviderDomain,
    ProviderHealthMetadata,
    ProviderManifest,
    ProviderStatus,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import RuntimeSafeDisableState
from ultimate_ai_agent.core.sandbox_calculation.contracts import (
    SEALED_CALCULATION_ADAPTER_REF,
    SEALED_CALCULATION_CAPABILITY_REF,
    SEALED_CALCULATION_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.time import utc_now

from .adapters import (
    snapshot_from_capability_catalog_entry,
    snapshot_from_capability_manifest,
    snapshots_from_extension_catalog,
    snapshot_from_provider_manifest,
)
from .contracts import (
    AuthorityPosture,
    CapabilityAvailabilityReadModel,
    CatalogStatus,
    CompatibilityStatus,
    ConfigurationStatus,
    CostPosture,
    DerivedRuntimeReadinessStatus,
    FreshnessStatus,
    HealthStatus,
    ResourceBudgetStatus,
    SafeDisableStatus,
    WebHybridAvailabilityReadModel,
    WebHybridCapabilityLanePosture,
    WebResearchAggregationPosture,
    build_capability_availability_snapshot,
)


def build_capability_availability_read_model(
    *, checked_at: datetime | None = None
) -> CapabilityAvailabilityReadModel:
    observed_at = (checked_at or utc_now()).replace(microsecond=0)

    filesystem_metadata_mission = build_capability_availability_snapshot(
        snapshot_ref=(
            "capability-availability-ref:founder-loop-filesystem-metadata-v1"
        ),
        capability_ref=FOUNDER_LOOP_FILESYSTEM_CAPABILITY_REF,
        adapter_ref=FOUNDER_LOOP_FILESYSTEM_ADAPTER_REF,
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.unknown,
        health_status=HealthStatus.unknown,
        authority_posture=AuthorityPosture.approval_required,
        resource_status=ResourceBudgetStatus.unknown,
        cost_posture=CostPosture.not_metered,
        safe_disable_status=SafeDisableStatus.unknown,
        declared_or_observed_version_ref=f"version-ref:{__version__}",
        checked_at=observed_at,
        freshness_status=FreshnessStatus.unknown,
        reason_codes=[
            "EXACT_FILESYSTEM_METADATA_MISSION_IMPLEMENTED",
            "CANONICAL_MISSION_DISPATCH_PATH_VERIFIED",
            "REQUEST_SCOPED_AUTHORITY_REEVALUATION_REQUIRED",
        ],
        blocker_codes=[
            "CURRENT_ROOT_IDENTITY_OBSERVATION_REQUIRED",
            "CURRENT_SAFE_DISABLE_OBSERVATION_REQUIRED",
            "CURRENT_RESOURCE_RESERVATION_REQUIRED",
            "EXACT_LOCAL_APPROVAL_REQUIRED",
            "EXACT_MISSION_SCOPED_LEASE_REQUIRED",
        ],
        evidence_refs=[
            "proof-ref:founder-loop-filesystem-metadata:mission-dispatch",
            "receipt-contract-ref:authority-mission-completion:v1",
            FOUNDER_LOOP_FILESYSTEM_SAFE_DISABLE_REF,
        ],
        probe_refs=[],
        source_ref="capability-manifest-ref:founder-loop-filesystem-metadata-v1",
        safe_summary=(
            "Exact predeclared filesystem metadata is implemented, while current "
            "root, resource, health, and safe-disable availability remain unknown "
            "until immediate request-scoped evaluation; it is never globally callable."
        ),
    )

    sealed_calculation = build_capability_availability_snapshot(
        snapshot_ref="capability-availability-ref:sealed-calculation-v1",
        capability_ref=SEALED_CALCULATION_CAPABILITY_REF,
        adapter_ref=SEALED_CALCULATION_ADAPTER_REF,
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.unknown,
        configuration_status=ConfigurationStatus.unknown,
        health_status=HealthStatus.unknown,
        authority_posture=AuthorityPosture.lease_required,
        resource_status=ResourceBudgetStatus.unknown,
        cost_posture=CostPosture.not_metered,
        safe_disable_status=SafeDisableStatus.unknown,
        declared_or_observed_version_ref=f"version-ref:{__version__}",
        checked_at=observed_at,
        freshness_status=FreshnessStatus.unknown,
        reason_codes=[
            "SEALED_DETERMINISTIC_CALCULATION_IMPLEMENTED",
            "CANONICAL_MISSION_DISPATCH_PATH_VERIFIED",
            "NO_PER_INVOCATION_APPROVAL_AFTER_EXACT_LEASE",
            "CODE_OUTPUT_IS_EVIDENCE_NOT_AUTHORITY",
        ],
        blocker_codes=[
            "CURRENT_DOCKER_DESKTOP_OBSERVATION_REQUIRED",
            "CURRENT_PLATFORM_COMPATIBILITY_OBSERVATION_REQUIRED",
            "CURRENT_PINNED_IMAGE_ATTESTATION_REQUIRED",
            "CURRENT_SAFE_DISABLE_OBSERVATION_REQUIRED",
            "CURRENT_OPERATION_RESERVATION_REQUIRED",
            "EXACT_MISSION_SCOPED_LEASE_REQUIRED",
        ],
        evidence_refs=[
            "test-contract-ref:sealed-calculation:adversarial-isolation-v1",
            "receipt-contract-ref:sealed-calculation-execution-v1",
            SEALED_CALCULATION_SAFE_DISABLE_REF,
        ],
        probe_refs=[],
        source_ref="capability-manifest-ref:sealed-calculation-v1",
        safe_summary=(
            "Exact bounded arithmetic is implemented through an attested local "
            "container and canonical mission dispatch. Current image, runtime, "
            "safe-disable, budget, and exact lease posture are re-evaluated before "
            "each start; availability never grants global code or shell authority."
        ),
    )

    ready_for_policy = snapshot_from_capability_manifest(
        _declaration_manifest(
            capability_id="api-contract-metadata",
            name="API contract metadata",
            description="Expose stable API contract metadata without runtime execution.",
        ),
        checked_at=observed_at,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.configured,
        health_status=HealthStatus.healthy,
        authority_posture=AuthorityPosture.eligible_for_policy_evaluation,
        resource_status=ResourceBudgetStatus.available,
        safe_disable_status=SafeDisableStatus.inactive,
        freshness_status=FreshnessStatus.current,
        evidence_refs=["evidence-ref:api-manifest-contract"],
        probe_refs=["probe-ref:deterministic-local-contract-build"],
        source_ref="capability-manifest-ref:api-contract-metadata",
        safe_summary=(
            "Deterministic local metadata contract is runtime-ready for one request-scoped policy evaluation; availability alone grants no execution."
        ),
    )

    declared_unavailable = snapshot_from_capability_manifest(
        _declaration_manifest(
            capability_id="manual-local-loopback-smoke-validation",
            name="Manual local loopback smoke validation",
            description="Validate the declared manual local smoke boundary.",
            approval_required=True,
            risk_level=RiskLevel.high,
        ),
        checked_at=observed_at,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.not_configured,
        health_status=HealthStatus.unknown,
        authority_posture=AuthorityPosture.approval_required,
        resource_status=ResourceBudgetStatus.available,
        safe_disable_status=SafeDisableStatus.inactive,
        freshness_status=FreshnessStatus.current,
        evidence_refs=["evidence-ref:runtime-readiness-manual-smoke-boundary"],
        source_ref="capability-manifest-ref:manual-local-loopback-smoke",
        safe_summary=(
            "Manual local smoke capability is declared but unavailable because configuration and current health are not proven."
        ),
    )

    simulated_manifest = _declaration_manifest(
        capability_id="simulated-model-runtime",
        name="Simulated model runtime",
        description="Return deterministic non-authoritative simulated responses.",
    )
    configured_but_blocked = snapshot_from_capability_catalog_entry(
        CapabilityCatalogEntry.from_manifest(
            simulated_manifest,
            health_status=CapabilityHealthStatus.healthy,
            reason_codes=["SIMULATED_RUNTIME_HEALTH_DECLARED"],
        ),
        checked_at=observed_at,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.configured,
        authority_posture=AuthorityPosture.blocked,
        resource_status=ResourceBudgetStatus.available,
        safe_disable_status=SafeDisableStatus.inactive,
        freshness_status=FreshnessStatus.current,
        evidence_refs=["evidence-ref:simulated-runtime-contract"],
        source_ref="capability-catalog-ref:simulated-model-runtime",
        blocker_codes=["SIMULATED_OUTPUT_NOT_EXECUTION_AUTHORITY"],
        safe_summary=(
            "Simulated runtime metadata is configured and healthy, while invocation authority remains blocked and outputs remain non-authoritative."
        ),
    )

    stale_unknown = snapshot_from_capability_manifest(
        _declaration_manifest(
            capability_id="runtime-capability-discovery",
            name="Runtime capability discovery",
            description="Inspect optional runtime capability metadata without live discovery.",
        ),
        checked_at=observed_at,
        compatibility_status=CompatibilityStatus.unknown,
        configuration_status=ConfigurationStatus.configured,
        health_status=HealthStatus.stale,
        authority_posture=AuthorityPosture.blocked,
        resource_status=ResourceBudgetStatus.unknown,
        safe_disable_status=SafeDisableStatus.inactive,
        freshness_status=FreshnessStatus.stale,
        expires_at=observed_at - timedelta(seconds=1),
        evidence_refs=["evidence-ref:runtime-capability-static-readiness"],
        source_ref="capability-manifest-ref:runtime-capability-discovery",
        blocker_codes=["LIVE_RUNTIME_DISCOVERY_NOT_PERFORMED"],
        safe_summary=(
            "Optional runtime discovery is stale and unverified; unknown compatibility and health fail closed without a live probe."
        ),
    )

    provider_budget_blocked = snapshot_from_provider_manifest(
        _governed_provider_contract_manifest(),
        readiness=GovernedProviderInvocationReadiness(),
        checked_at=observed_at,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.configured,
        health_status=HealthStatus.healthy,
        resource_status=ResourceBudgetStatus.unknown,
        safe_disable_status=SafeDisableStatus.inactive,
        freshness_status=FreshnessStatus.current,
        evidence_refs=["evidence-ref:governed-provider-readiness-contract"],
        probe_refs=["probe-ref:deterministic-provider-contract-validation"],
        blocker_codes=["BUDGET_DECISION_REF_REQUIRED"],
        source_ref="provider-manifest-ref:governed-provider-contract",
        safe_summary=(
            "Governed provider contract metadata is configured and healthy, but metered budget status and invocation authority remain blocked."
        ),
    )

    safe_disable_state = RuntimeSafeDisableState()
    safe_disabled = build_capability_availability_snapshot(
        snapshot_ref="capability-availability-ref:governed-runtime-safe-disabled",
        capability_ref="capability-ref:governed-runtime-command",
        adapter_ref="adapter-ref:runtime-gateway-command",
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=ConfigurationStatus.configured,
        health_status=HealthStatus.healthy,
        authority_posture=AuthorityPosture.lease_required,
        resource_status=ResourceBudgetStatus.available,
        cost_posture=CostPosture.not_metered,
        safe_disable_status=(
            SafeDisableStatus.active
            if safe_disable_state.active
            else SafeDisableStatus.inactive
        ),
        declared_or_observed_version_ref=f"version-ref:{__version__}",
        checked_at=observed_at,
        freshness_status=FreshnessStatus.current,
        reason_codes=["RUNTIME_GATEWAY_SAFE_DISABLE_STATE_NORMALIZED"],
        blocker_codes=["AUTHORITY_LEASE_REQUIRED"],
        evidence_refs=[safe_disable_state.safe_disable_posture_ref],
        source_ref=safe_disable_state.safe_disable_ref,
        safe_summary=(
            "Governed runtime command capability is safe-disabled; this override blocks every otherwise-positive readiness input."
        ),
    )

    inspectable_extensions = snapshots_from_extension_catalog(
        build_default_inspectable_extension_catalog(),
        checked_at=observed_at,
    )

    snapshots = [
        filesystem_metadata_mission,
        sealed_calculation,
        declared_unavailable,
        configured_but_blocked,
        stale_unknown,
        provider_budget_blocked,
        safe_disabled,
        ready_for_policy,
        *inspectable_extensions,
    ]
    readiness_counts = {
        status.value: sum(item.runtime_readiness_status == status for item in snapshots)
        for status in DerivedRuntimeReadinessStatus
    }
    authority_counts = {
        status.value: sum(item.authority_posture == status for item in snapshots)
        for status in AuthorityPosture
    }
    return CapabilityAvailabilityReadModel(
        read_model_ref="capability-availability-read-model-ref:control-center:v1",
        generated_at=observed_at,
        source_ref="source-ref:python-core-capability-availability",
        web_hybrid=build_web_hybrid_availability_read_model(),
        snapshots=snapshots,
        snapshot_count=len(snapshots),
        readiness_counts=readiness_counts,
        authority_counts=authority_counts,
        reason_codes=[
            "CANONICAL_CAPABILITY_AVAILABILITY_NORMALIZATION_ACTIVE",
            "REQUEST_SCOPED_INVOCATION_DECISION_REQUIRED",
            "EXECUTION_EVIDENCE_REMAINS_SEPARATE",
        ],
        blocker_codes=sorted(
            {code for item in snapshots for code in item.blocker_codes}
        ),
        safe_summary=(
            "Backend-owned capability availability separates declaration, observed runtime readiness, exact request authority evaluation, and later execution receipts. Unknown and stale observations fail closed."
        ),
    )


def build_web_hybrid_availability_read_model() -> WebHybridAvailabilityReadModel:
    from ultimate_ai_agent.core.web_access.firecrawl_cloud import (
        FIRECRAWL_CLOUD_ADAPTER_REF,
        FIRECRAWL_CLOUD_CAPABILITY_REF,
        FIRECRAWL_CLOUD_LANE_REF,
        FIRECRAWL_CLOUD_PROVIDER_REF,
    )
    from ultimate_ai_agent.core.web_access.firecrawl_markdown import (
        FIRECRAWL_MARKDOWN_ADAPTER_REF,
        FIRECRAWL_MARKDOWN_CAPABILITY_REF,
        FIRECRAWL_MARKDOWN_LANE_REF,
        FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
    )
    from ultimate_ai_agent.core.web_access.searxng_search import (
        SEARXNG_SEARCH_ADAPTER_REF,
        SEARXNG_SEARCH_CAPABILITY_REF,
        SEARXNG_SEARCH_LANE_REF,
        SEARXNG_SEARCH_PROVIDER_REF,
    )

    return WebHybridAvailabilityReadModel(
        research_aggregation=WebResearchAggregationPosture(
            proof_refs=[
                "proof-ref:web-research-aggregation:deterministic-bounds",
                "proof-ref:web-research-aggregation:untrusted-citations",
                "proof-ref:web-research-aggregation:provider-observations",
            ],
            blocker_codes=[
                "CURRENT_RESEARCH_OBSERVATIONS_NOT_INJECTED",
                "REQUEST_SCOPED_RETRIEVAL_AUTHORITY_REQUIRED",
                "MEMORY_AND_ACTION_PROMOTION_DENIED",
            ],
            safe_summary=(
                "Bounded cited research aggregation is implemented for deterministic "
                "injected observations. This read-only surface performs no retrieval "
                "and has no current citations; provider readiness, latency, cost, "
                "context, routing, exclusions, and redaction remain explicit."
            ),
        ),
        lanes=[
            WebHybridCapabilityLanePosture(
                lane_ref=SEARXNG_SEARCH_LANE_REF,
                capability_ref=SEARXNG_SEARCH_CAPABILITY_REF,
                display_label="SearXNG read-only search",
                runtime_availability="requires_current_loopback_observation",
                provider_ref=SEARXNG_SEARCH_PROVIDER_REF,
                adapter_ref=SEARXNG_SEARCH_ADAPTER_REF,
                approval_posture="exact_local_approval_and_lease_required",
                cost_posture="not_metered",
                reason_codes=["EXACT_READ_ONLY_SEARCH_IMPLEMENTED"],
                blocker_codes=["CURRENT_RUNTIME_OBSERVATION_REQUIRED"],
            ),
            WebHybridCapabilityLanePosture(
                lane_ref=FIRECRAWL_MARKDOWN_LANE_REF,
                capability_ref=FIRECRAWL_MARKDOWN_CAPABILITY_REF,
                display_label="Self-hosted one-page markdown",
                runtime_availability="requires_current_loopback_observation",
                provider_ref=FIRECRAWL_SELF_HOSTED_PROVIDER_REF,
                adapter_ref=FIRECRAWL_MARKDOWN_ADAPTER_REF,
                approval_posture="exact_local_approval_and_lease_required",
                cost_posture="not_metered",
                reason_codes=["EXACT_LOCAL_MARKDOWN_IMPLEMENTED"],
                blocker_codes=["CURRENT_RUNTIME_OBSERVATION_REQUIRED"],
            ),
            WebHybridCapabilityLanePosture(
                lane_ref=FIRECRAWL_CLOUD_LANE_REF,
                capability_ref=FIRECRAWL_CLOUD_CAPABILITY_REF,
                display_label="Firecrawl Cloud free-plan one-page markdown",
                runtime_availability="requires_credential_and_current_credit_snapshot",
                provider_ref=FIRECRAWL_CLOUD_PROVIDER_REF,
                adapter_ref=FIRECRAWL_CLOUD_ADAPTER_REF,
                approval_posture="exact_approval_lease_budget_and_reservation_required",
                cost_posture="metered_free_plan_only",
                reason_codes=["EXACT_FREE_PLAN_CLOUD_MARKDOWN_IMPLEMENTED"],
                blocker_codes=[
                    "CURRENT_CREDIT_SNAPSHOT_NOT_OBSERVED_BY_READ_ONLY_ROUTE",
                    "PAID_USAGE_DENIED",
                ],
            ),
        ],
        proof_refs=[
            "proof-ref:web-hybrid:deterministic-contracts",
            "proof-ref:web-hybrid:live-local-search",
            "proof-ref:web-hybrid:live-local-markdown",
            "proof-ref:web-hybrid:live-cloud-one-credit",
        ],
        blocker_codes=[
            "CURRENT_RUNTIME_OBSERVATION_REQUIRED",
            "CURRENT_CREDIT_SNAPSHOT_NOT_OBSERVED_BY_READ_ONLY_ROUTE",
            "CURRENT_CIRCUIT_STATE_NOT_OBSERVED_BY_READ_ONLY_ROUTE",
            "REQUEST_SCOPED_AUTHORITY_REQUIRED",
            "PAID_USAGE_DENIED",
        ],
        safe_summary=(
            "Exact read-only search, local markdown, free-plan cloud markdown, and one-step local-first routing are implemented. This read-only view performs no probe or provider call; current availability, quota, circuit, approval, lease, and budget truth must be evaluated for each request."
        ),
    )


def _declaration_manifest(
    *,
    capability_id: str,
    name: str,
    description: str,
    approval_required: bool = False,
    risk_level: RiskLevel = RiskLevel.low,
) -> CapabilityManifest:
    return CapabilityManifest(
        id=capability_id,
        version=__version__,
        kind=CapabilityKind.deterministic,
        name=name,
        description=description,
        examples=["Inspect safe contract metadata."],
        anti_examples=["Do not treat metadata as execution authority."],
        input_schema={"type": "object", "additionalProperties": False},
        output_schema={"type": "object", "additionalProperties": False},
        input_modes=["safe_refs"],
        output_modes=["safe_summary"],
        side_effects=SideEffectLevel.none,
        risk_level=risk_level,
        approval_required=approval_required or None,
        deterministic=True,
        estimated_cost_class=CapabilityCostClass.none,
        allowed_coordination_modes=[CoordinationMode.direct_tool],
        safety=SafetyPolicy(approval_required=approval_required),
    )


def _governed_provider_contract_manifest() -> ProviderManifest:
    return ProviderManifest(
        provider_id="governed-provider-contract",
        display_name="Governed Provider Contract",
        domain=ProviderDomain.generic,
        status=ProviderStatus.blocked,
        auth_requirement=ProviderAuthRequirement.none,
        cost_class=ProviderCostClass.paid,
        capabilities=[ProviderCapability.generic_query],
        health_metadata=ProviderHealthMetadata(
            status="healthy",
            last_checked_at="deterministic-contract-validation",
        ),
        owner="core",
        source="provider-readiness-contract",
        version=__version__,
    )
