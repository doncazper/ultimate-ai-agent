from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

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
from ultimate_ai_agent.core.communications.contracts import (
    CommunicationsProviderDescriptor,
    CommunicationsProviderStatus,
)

from .backend import (
    MATRIX_SESSION_SAFE_DISABLE_ENV,
    default_matrix_session_backend_config,
)
from .constants import MATRIX_SESSION_PROVIDER_REF


MATRIX_SESSION_ADAPTER_REF = "adapter-ref:communications:matrix-session-v1"
MATRIX_SESSION_CAPABILITY_REF = "capability-ref:communications:matrix-session-v1"


def build_matrix_session_provider_descriptor(
    *, repo_root: Path, checked_at: datetime
) -> CommunicationsProviderDescriptor:
    blocker_codes = [
        "MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED",
        "MATRIX_SYNC_RUNTIME_NOT_IMPLEMENTED",
        "MATRIX_MESSAGE_READ_RUNTIME_NOT_IMPLEMENTED",
        "MATRIX_MESSAGE_WRITE_RUNTIME_NOT_IMPLEMENTED",
        "MATRIX_CRYPTO_RUNTIME_NOT_INITIALIZED",
        "MATRIX_MEDIA_RUNTIME_NOT_IMPLEMENTED",
        "MATRIX_SSO_BROKER_NOT_IMPLEMENTED",
    ]
    try:
        default_matrix_session_backend_config(repo_root)
    except (OSError, RuntimeError, ValueError):
        configuration = ConfigurationStatus.not_configured
        blocker_codes.insert(0, "MATRIX_SESSION_RUNTIME_NOT_CONFIGURED")
    else:
        configuration = ConfigurationStatus.configured
    safe_disabled = os.getenv(MATRIX_SESSION_SAFE_DISABLE_ENV, "").strip().lower() in {
        "1", "true", "yes", "on"
    }
    if safe_disabled:
        blocker_codes.insert(0, "MATRIX_SESSION_SAFE_DISABLED")
    availability = build_capability_availability_snapshot(
        snapshot_ref="snapshot-ref:communications:matrix-session-v1",
        capability_ref=MATRIX_SESSION_CAPABILITY_REF,
        provider_ref=MATRIX_SESSION_PROVIDER_REF,
        adapter_ref=MATRIX_SESSION_ADAPTER_REF,
        catalog_status=CatalogStatus.supported,
        compatibility_status=CompatibilityStatus.supported,
        configuration_status=configuration,
        health_status=HealthStatus.unknown,
        authority_posture=AuthorityPosture.lease_required,
        resource_status=ResourceBudgetStatus.available,
        cost_posture=CostPosture.not_metered,
        safe_disable_status=(
            SafeDisableStatus.active if safe_disabled else SafeDisableStatus.inactive
        ),
        freshness_status=FreshnessStatus.unknown,
        declared_or_observed_version_ref="version-ref:matrix-js-sdk:41-9-0",
        checked_at=checked_at,
        source_ref="source-ref:communications:matrix-session-runtime",
        reason_codes=[
            "MATRIX_DISCOVERY_EXACT_LANE_IMPLEMENTED",
            "MATRIX_SESSION_READ_AUTHORITY_ACCEPTED",
            "MATRIX_PROVIDER_PARTIAL_RUNTIME",
        ],
        blocker_codes=blocker_codes,
        evidence_refs=[
            "evidence-ref:communications:matrix-session-sdk-pin",
            "evidence-ref:communications:matrix-session-authority-tests",
        ],
        safe_summary=(
            "Exact Matrix discovery and authentication-method reads are available "
            "for fresh request-scoped evaluation; eight session mutations and "
            "all later provider features remain blocked."
        ),
    )
    return CommunicationsProviderDescriptor(
        provider_ref=MATRIX_SESSION_PROVIDER_REF,
        adapter_ref=MATRIX_SESSION_ADAPTER_REF,
        capability_ref=MATRIX_SESSION_CAPABILITY_REF,
        provider_status=CommunicationsProviderStatus.partial,
        availability=availability,
        reason_codes=[
            "MATRIX_DISCOVERY_EXACT_LANE_IMPLEMENTED",
            "MATRIX_PROVIDER_PARTIAL_RUNTIME",
        ],
        blocker_codes=blocker_codes,
        evidence_refs=["evidence-ref:communications:matrix-session-sdk-pin"],
        safe_summary=(
            "Matrix has two governed read lanes; authenticated session, synchronization, "
            "message, crypto, media, and SSO callback runtime remain blocked."
        ),
    )
