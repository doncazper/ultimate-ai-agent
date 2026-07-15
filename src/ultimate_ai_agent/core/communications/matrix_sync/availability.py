from __future__ import annotations

from .constants import MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS, MATRIX_SYNC_LANES, MatrixSyncOperation
from .contracts import (
    MatrixSyncFreshness,
    MatrixSyncPosture,
    MatrixSyncRuntimeStatus,
)


def build_default_matrix_sync_posture() -> MatrixSyncPosture:
    return MatrixSyncPosture(
        adapter_ref="adapter-ref:communications:matrix-sync-v1",
        runtime_status=MatrixSyncRuntimeStatus.configuration_required,
        freshness=MatrixSyncFreshness.unavailable,
        credential_posture_ref="credential-posture-ref:matrix:one-use-broker-not-enrolled",
        cache_posture_ref="cache-posture-ref:matrix:protected-cache-helper-not-installed",
        authority_lane_refs=tuple(
            lane.lane_ref
            for lane in sorted(MATRIX_SYNC_LANES.values(), key=lambda item: item.operation.value)
        ),
        concrete_transport_operation_refs=tuple(
            f"operation-ref:matrix-sync:{operation.value.replace('_', '-')}"
            for operation in sorted(
                MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS,
                key=lambda item: item.value,
            )
        ),
        uncomposed_executor_operation_refs=tuple(
            f"operation-ref:matrix-sync:{operation.value.replace('_', '-')}"
            for operation in sorted(
                set(MatrixSyncOperation) - MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS,
                key=lambda item: item.value,
            )
        ),
        blocker_refs=(
            "blocker-ref:matrix-sync:credential-broker-enrollment-required",
            "blocker-ref:matrix-sync:protected-cache-helper-install-required",
            "blocker-ref:matrix-sync:canonical-operation-executors-required",
        ),
        evidence_refs=(
            "evidence-ref:matrix-sync:exact-authority-catalog",
            "evidence-ref:matrix-sync:loopback-read-and-encrypted-cache-tests",
        ),
        safe_summary=(
            "Twelve exact Matrix authority lanes are declared. Two GET transports and "
            "protected-cache/key primitives are loopback-tested; ten canonical dispatch "
            "executors remain uncomposed. Live sync is configuration-required."
        ),
        sync_enabled=False,
    )
