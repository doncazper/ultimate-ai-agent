from __future__ import annotations

from .constants import MATRIX_MESSAGING_LANES, MatrixMessagingOperation
from .contracts import MatrixMessagingPosture, stable_matrix_messaging_ref


def build_default_matrix_messaging_posture() -> MatrixMessagingPosture:
    authority_lane_refs = tuple(
        MATRIX_MESSAGING_LANES[operation].lane_ref
        for operation in MatrixMessagingOperation
    )
    executor_operation_refs = tuple(
        f"operation-ref:matrix-messaging:{operation.value.replace('_', '-')}"
        for operation in MatrixMessagingOperation
    )
    values: dict[str, object] = {
        "runtime_status": "configuration_required",
        "authority_lane_refs": authority_lane_refs,
        "live_executor_operation_refs": executor_operation_refs,
        "blocked_operation_refs": executor_operation_refs,
        "broker_ref": "component-ref:matrix-rust-broker:v1",
        "crypto_store_ref": "crypto-store-ref:matrix:encrypted-sqlite-v1",
        "outbox_store_ref": "outbox-store-ref:matrix:encrypted-dedicated-v1",
        "reason_refs": (
            "reason-ref:matrix-messaging:runtime-artifact-enrollment-required",
            "reason-ref:matrix-messaging:unlocked-login-keychain-required",
            "reason-ref:matrix-messaging:exact-account-session-required",
            "reason-ref:matrix-messaging:request-scoped-authority-required",
        ),
        "element_interoperability_status": "external_facility_required",
        "safe_summary": (
            "Exact manual messaging executors are implemented for the bounded loopback Matrix lane; runtime enrollment, an unlocked Keychain, and fresh request-scoped authority remain required."
        ),
    }
    values["posture_ref"] = stable_matrix_messaging_ref(
        "posture-ref:matrix-messaging", values
    )
    return MatrixMessagingPosture.model_validate(values)


__all__ = ["build_default_matrix_messaging_posture"]
