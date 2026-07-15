from __future__ import annotations

from datetime import datetime

from ultimate_ai_agent.core.capability_availability import (
    AuthorityPosture,
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


def build_matrix_crypto_availability(*, checked_at: datetime):
    return build_capability_availability_snapshot(
        snapshot_ref="snapshot-ref:communications:matrix-crypto-v1",
        capability_ref="capability-ref:communications:matrix-crypto-v1",
        provider_ref="provider-ref:communications:matrix",
        adapter_ref="adapter-ref:communications:matrix-crypto-required-v1",
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.unknown,
        configuration_status=ConfigurationStatus.not_configured,
        health_status=HealthStatus.unknown,
        authority_posture=AuthorityPosture.lease_required,
        resource_status=ResourceBudgetStatus.available,
        cost_posture=CostPosture.not_metered,
        safe_disable_status=SafeDisableStatus.unknown,
        freshness_status=FreshnessStatus.unknown,
        declared_or_observed_version_ref="version-ref:matrix-js-sdk:41-9-0",
        checked_at=checked_at,
        source_ref="source-ref:communications:matrix-crypto-contracts",
        reason_codes=[
            "MATRIX_CRYPTO_EXACT_AUTHORITY_CONTRACTS_ACCEPTED",
            "MATRIX_CRYPTO_REQUEST_SCOPED_EVALUATION_REQUIRED",
        ],
        blocker_codes=[
            "MATRIX_CRYPTO_PERSISTENT_RUST_BACKEND_REQUIRED",
            "MATRIX_CRYPTO_AUTHENTICATED_SESSION_REQUIRED",
            "MATRIX_CRYPTO_LIVE_EXECUTOR_UNCOMPOSED",
        ],
        evidence_refs=[
            "evidence-ref:matrix-crypto:authority-contract-tests",
            "evidence-ref:matrix-crypto:fail-closed-adapter-boundary",
        ],
        safe_summary=(
            "Matrix crypto is inspectable and exact-authority scoped, but no live "
            "persistent Rust-crypto executor is configured."
        ),
    )
