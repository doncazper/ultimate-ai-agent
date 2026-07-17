from .constants import (
    MATRIX_MEDIA_CANCEL_POLICY_REF,
    MATRIX_MEDIA_PREVIEW_POLICY_REF,
    MATRIX_MEDIA_PROGRESS_POLICY_REF,
    MATRIX_MEDIA_QUARANTINE_POLICY_REF,
    MATRIX_MEDIA_RETRY_POLICY_REF,
    MATRIX_ROOMS_MEDIA_LANES,
    MATRIX_SEARCH_INDEX_POLICY_REF,
)
from .contracts import MatrixRoomsMediaPosture, stable_matrix_rooms_media_ref


def build_default_matrix_rooms_media_posture() -> MatrixRoomsMediaPosture:
    operations = tuple(
        f"operation-ref:matrix-rooms-media:{operation.value.replace('_', '-')}"
        for operation in MATRIX_ROOMS_MEDIA_LANES
    )
    values = {
        "authority_lane_refs": tuple(
            lane.lane_ref for lane in MATRIX_ROOMS_MEDIA_LANES.values()
        ),
        "implemented_core_operation_refs": operations,
        "blocked_live_operation_refs": operations,
        "media_type_policy_ref": "media-type-policy-ref:matrix:png-jpeg-gif-text-v1",
        "quarantine_policy_ref": MATRIX_MEDIA_QUARANTINE_POLICY_REF,
        "preview_policy_ref": MATRIX_MEDIA_PREVIEW_POLICY_REF,
        "progress_policy_ref": MATRIX_MEDIA_PROGRESS_POLICY_REF,
        "cancel_policy_ref": MATRIX_MEDIA_CANCEL_POLICY_REF,
        "retry_policy_ref": MATRIX_MEDIA_RETRY_POLICY_REF,
        "search_index_policy_ref": MATRIX_SEARCH_INDEX_POLICY_REF,
        "reason_refs": (
            "reason-ref:matrix-rooms-media:runtime-enrollment-required",
            "reason-ref:matrix-rooms-media:exact-account-session-required",
            "reason-ref:matrix-rooms-media:request-scoped-authority-required",
            "reason-ref:matrix-rooms-media:element-external-facility-required",
        ),
    }
    values["posture_ref"] = stable_matrix_rooms_media_ref(
        "posture-ref:matrix-rooms-media", values
    )
    return MatrixRoomsMediaPosture.model_validate(values)


__all__ = ["build_default_matrix_rooms_media_posture"]
