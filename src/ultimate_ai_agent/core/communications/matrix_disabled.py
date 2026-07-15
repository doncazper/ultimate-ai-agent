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
from ultimate_ai_agent.core.communications.contracts import (
    CommunicationsProviderDescriptor,
    CommunicationsProviderStatus,
)


MATRIX_PROVIDER_REF = "provider-ref:communications:matrix"
MATRIX_ADAPTER_REF = "adapter-ref:communications:matrix-disabled"
MATRIX_CAPABILITY_REF = "capability-ref:communications:matrix-inspection"
MATRIX_SNAPSHOT_REF = "snapshot-ref:communications:matrix-disabled"


class CommunicationsAdapterDisabled(RuntimeError):
    """Raised when a disabled communications adapter is invoked."""


class DisabledMatrixAdapter:
    """Inspection-only shell. It owns no SDK, account, network, or crypto state."""

    provider_ref = MATRIX_PROVIDER_REF
    adapter_ref = MATRIX_ADAPTER_REF
    capability_ref = MATRIX_CAPABILITY_REF

    def inspect_descriptor(
        self, *, checked_at: datetime
    ) -> CommunicationsProviderDescriptor:
        availability = build_capability_availability_snapshot(
            snapshot_ref=MATRIX_SNAPSHOT_REF,
            capability_ref=self.capability_ref,
            provider_ref=self.provider_ref,
            adapter_ref=self.adapter_ref,
            catalog_status=CatalogStatus.unsupported,
            compatibility_status=CompatibilityStatus.unknown,
            configuration_status=ConfigurationStatus.not_configured,
            health_status=HealthStatus.unknown,
            authority_posture=AuthorityPosture.blocked,
            resource_status=ResourceBudgetStatus.unknown,
            cost_posture=CostPosture.unknown,
            safe_disable_status=SafeDisableStatus.unknown,
            freshness_status=FreshnessStatus.unknown,
            checked_at=checked_at,
            source_ref="source-ref:communications:matrix-disabled-contract",
            safe_summary=(
                "Matrix is an inspection-only disabled adapter with no account, "
                "network, synchronization, message, crypto, or media runtime."
            ),
            reason_codes=["MATRIX_ADAPTER_DECLARATION_ONLY"],
            blocker_codes=[
                "MATRIX_SDK_NOT_INSTALLED",
                "MATRIX_NETWORK_AUTHORITY_NOT_ACCEPTED",
                "MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED",
                "MATRIX_MESSAGE_READ_AUTHORITY_NOT_ACCEPTED",
                "MATRIX_MESSAGE_WRITE_AUTHORITY_NOT_ACCEPTED",
                "MATRIX_CRYPTO_RUNTIME_NOT_IMPLEMENTED",
                "MATRIX_MEDIA_RUNTIME_NOT_IMPLEMENTED",
            ],
            evidence_refs=["evidence-ref:communications:matrix-disabled-contract"],
        )
        return CommunicationsProviderDescriptor(
            provider_ref=self.provider_ref,
            adapter_ref=self.adapter_ref,
            capability_ref=self.capability_ref,
            provider_status=CommunicationsProviderStatus.unsupported,
            availability=availability,
            reason_codes=["MATRIX_ADAPTER_DECLARATION_ONLY"],
            blocker_codes=[
                "MATRIX_SDK_NOT_INSTALLED",
                "MATRIX_NETWORK_AUTHORITY_NOT_ACCEPTED",
                "MATRIX_ACCOUNT_SESSION_NOT_CONFIGURED",
            ],
            evidence_refs=["evidence-ref:communications:matrix-disabled-contract"],
            safe_summary="Matrix runtime is unavailable; inspection exposes blocked posture only.",
        )

    @staticmethod
    def _deny() -> None:
        raise CommunicationsAdapterDisabled("MATRIX_ADAPTER_RUNTIME_DISABLED")

    def authenticate(self, *_args: object, **_kwargs: object) -> None:
        self._deny()

    def synchronize(self, *_args: object, **_kwargs: object) -> None:
        self._deny()

    def read_messages(self, *_args: object, **_kwargs: object) -> None:
        self._deny()

    def send_message(self, *_args: object, **_kwargs: object) -> None:
        self._deny()

    def initialize_crypto(self, *_args: object, **_kwargs: object) -> None:
        self._deny()

    def transfer_media(self, *_args: object, **_kwargs: object) -> None:
        self._deny()
