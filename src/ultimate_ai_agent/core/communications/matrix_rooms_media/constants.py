from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ultimate_ai_agent.core.authority import (
    AuthorityCapability,
    AuthorityDomain,
    TrustMode,
)


MATRIX_ROOMS_MEDIA_SCHEMA_VERSION = "uaa-matrix-rooms-media.v1"
MATRIX_ROOMS_MEDIA_TARGET_REF = (
    "target-ref:communications:matrix-rooms-media-exact-scope"
)
MATRIX_ROOMS_MEDIA_PROVIDER_REF = "provider-ref:communications:matrix"
MATRIX_ROOMS_MEDIA_RUNTIME_REF = "runtime-ref:matrix-rust-sdk:0.18.0"
MATRIX_ROOMS_MEDIA_BUDGET_REF = "budget-ref:matrix-rooms-media:zero-cost-v1"
MATRIX_ROOMS_MEDIA_SAFE_DISABLE_REF = "safe-disable-ref:matrix-messenger:enabled"
MATRIX_ROOMS_MEDIA_KILL_SWITCH_REF = "kill-switch-ref:matrix-messenger:clear"
MATRIX_ROOMS_MEDIA_RETENTION_REF = "retention-ref:matrix-rooms-media:bounded-v1"
MATRIX_ROOMS_MEDIA_LIMIT_POLICY_REF = "limit-policy-ref:matrix-rooms-media:bounded-v1"
MATRIX_MEDIA_ROOT_POLICY_REF = "filesystem-root-policy-ref:matrix-media:app-owned-v1"
MATRIX_MEDIA_QUARANTINE_POLICY_REF = (
    "quarantine-policy-ref:matrix-media:before-preview-v1"
)
MATRIX_MEDIA_PREVIEW_POLICY_REF = (
    "preview-policy-ref:matrix-media:metadata-allowlist-v1"
)
MATRIX_MEDIA_PARSER_REF = "parser-ref:matrix-media:metadata-only-v1"
MATRIX_MEDIA_PROGRESS_POLICY_REF = "progress-policy-ref:matrix-media:content-free-v1"
MATRIX_MEDIA_CANCEL_POLICY_REF = (
    "cancel-policy-ref:matrix-media:bounded-process-termination-v1"
)
MATRIX_MEDIA_RETRY_POLICY_REF = (
    "retry-policy-ref:matrix-media:manual-idempotent-no-auto-uncertain-v1"
)
MATRIX_SEARCH_INDEX_POLICY_REF = "search-index-policy-ref:matrix:encrypted-hmac-v1"


class MatrixRoomsMediaOperation(str, Enum):
    dm_create = "dm_create"
    room_create = "room_create"
    room_join = "room_join"
    room_leave = "room_leave"
    invite_send = "invite_send"
    invite_accept = "invite_accept"
    invite_reject = "invite_reject"
    invite_withdraw = "invite_withdraw"
    room_power_role_write = "room_power_role_write"
    space_mapping_write = "space_mapping_write"
    notification_settings_write = "notification_settings_write"
    history_visibility_write = "history_visibility_write"
    pin_write = "pin_write"
    account_room_preference_write = "account_room_preference_write"
    search_local_read = "search_local_read"
    media_upload = "media_upload"
    media_download_quarantine = "media_download_quarantine"
    media_materialize = "media_materialize"
    media_preview = "media_preview"
    media_cleanup = "media_cleanup"


NETWORK_OPERATIONS = frozenset(
    operation
    for operation in MatrixRoomsMediaOperation
    if operation
    not in {
        MatrixRoomsMediaOperation.search_local_read,
        MatrixRoomsMediaOperation.media_materialize,
        MatrixRoomsMediaOperation.media_preview,
        MatrixRoomsMediaOperation.media_cleanup,
    }
)
EXTERNAL_MUTATION_OPERATIONS = NETWORK_OPERATIONS - {
    MatrixRoomsMediaOperation.media_download_quarantine,
}
DESTRUCTIVE_OPERATIONS = frozenset(
    {
        MatrixRoomsMediaOperation.invite_reject,
        MatrixRoomsMediaOperation.room_leave,
        MatrixRoomsMediaOperation.media_cleanup,
    }
)
MEDIA_OPERATIONS = frozenset(
    {
        MatrixRoomsMediaOperation.media_upload,
        MatrixRoomsMediaOperation.media_download_quarantine,
        MatrixRoomsMediaOperation.media_materialize,
        MatrixRoomsMediaOperation.media_preview,
        MatrixRoomsMediaOperation.media_cleanup,
    }
)


@dataclass(frozen=True)
class MatrixRoomsMediaLane:
    operation: MatrixRoomsMediaOperation
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    tool_ref: str
    tool_name: str
    authority_domain: AuthorityDomain
    authority_capability: AuthorityCapability
    requested_domains: dict[AuthorityDomain, tuple[AuthorityCapability, ...]]
    required_mode: TrustMode
    side_effect_class: str


_PRIMARY = {
    MatrixRoomsMediaOperation.room_leave: (
        AuthorityDomain.messages,
        AuthorityCapability.destructive,
    ),
    MatrixRoomsMediaOperation.invite_send: (
        AuthorityDomain.messages,
        AuthorityCapability.admin,
    ),
    MatrixRoomsMediaOperation.invite_withdraw: (
        AuthorityDomain.messages,
        AuthorityCapability.admin,
    ),
    MatrixRoomsMediaOperation.room_power_role_write: (
        AuthorityDomain.messages,
        AuthorityCapability.admin,
    ),
    MatrixRoomsMediaOperation.space_mapping_write: (
        AuthorityDomain.messages,
        AuthorityCapability.admin,
    ),
    MatrixRoomsMediaOperation.history_visibility_write: (
        AuthorityDomain.messages,
        AuthorityCapability.admin,
    ),
    MatrixRoomsMediaOperation.invite_reject: (
        AuthorityDomain.messages,
        AuthorityCapability.destructive,
    ),
    MatrixRoomsMediaOperation.search_local_read: (
        AuthorityDomain.messages,
        AuthorityCapability.read,
    ),
    MatrixRoomsMediaOperation.media_upload: (
        AuthorityDomain.messages,
        AuthorityCapability.upload,
    ),
    MatrixRoomsMediaOperation.media_download_quarantine: (
        AuthorityDomain.messages,
        AuthorityCapability.download,
    ),
    MatrixRoomsMediaOperation.media_materialize: (
        AuthorityDomain.files,
        AuthorityCapability.write,
    ),
    MatrixRoomsMediaOperation.media_preview: (
        AuthorityDomain.files,
        AuthorityCapability.read,
    ),
    MatrixRoomsMediaOperation.media_cleanup: (
        AuthorityDomain.files,
        AuthorityCapability.destructive,
    ),
}


def _lane(operation: MatrixRoomsMediaOperation) -> MatrixRoomsMediaLane:
    domain, capability = _PRIMARY.get(
        operation, (AuthorityDomain.messages, AuthorityCapability.mutate)
    )
    requested_domains = {domain: (capability,)}
    if operation == MatrixRoomsMediaOperation.media_upload:
        requested_domains[AuthorityDomain.files] = (AuthorityCapability.read,)
    elif operation == MatrixRoomsMediaOperation.media_download_quarantine:
        requested_domains[AuthorityDomain.files] = (AuthorityCapability.write,)
    slug = operation.value.replace("_", "-")
    destructive = operation in DESTRUCTIVE_OPERATIONS
    local = operation not in NETWORK_OPERATIONS
    return MatrixRoomsMediaLane(
        operation=operation,
        lane_ref=f"authority-lane-ref:matrix-rooms-media-{slug}",
        capability_ref=f"authority-capability-ref:matrix-rooms-media-{slug}-v1",
        adapter_ref=f"authority-adapter-ref:matrix-rooms-media-{slug}-v1",
        tool_ref=f"tool-ref:matrix-rooms-media-{slug}-v1",
        tool_name=f"matrix_rooms_media_{operation.value}",
        authority_domain=domain,
        authority_capability=capability,
        requested_domains=requested_domains,
        required_mode=(
            TrustMode.full_machine_access_session
            if destructive
            else TrustMode.ask_before_changes
        ),
        side_effect_class=(
            "destructive_external"
            if operation
            in {
                MatrixRoomsMediaOperation.room_leave,
                MatrixRoomsMediaOperation.invite_reject,
            }
            else "destructive_local_sensitive"
            if operation == MatrixRoomsMediaOperation.media_cleanup
            else "local_sensitive"
            if local
            else "authenticated_connector_mutation"
        ),
    )


MATRIX_ROOMS_MEDIA_LANES = {
    operation: _lane(operation) for operation in MatrixRoomsMediaOperation
}


def matrix_rooms_media_lane(
    operation: MatrixRoomsMediaOperation | str,
) -> MatrixRoomsMediaLane:
    return MATRIX_ROOMS_MEDIA_LANES[MatrixRoomsMediaOperation(operation)]


def matrix_rooms_media_rollback_ref(operation: MatrixRoomsMediaOperation | str) -> str:
    operation = MatrixRoomsMediaOperation(operation)
    posture = (
        "compensation-readiness"
        if operation in NETWORK_OPERATIONS
        else "rollback-readiness"
    )
    return f"{posture}-ref:matrix-rooms-media:{operation.value.replace('_', '-')}"


__all__ = [
    "DESTRUCTIVE_OPERATIONS",
    "EXTERNAL_MUTATION_OPERATIONS",
    "MATRIX_MEDIA_CANCEL_POLICY_REF",
    "MATRIX_MEDIA_PARSER_REF",
    "MATRIX_MEDIA_PREVIEW_POLICY_REF",
    "MATRIX_MEDIA_PROGRESS_POLICY_REF",
    "MATRIX_MEDIA_RETRY_POLICY_REF",
    "MATRIX_MEDIA_QUARANTINE_POLICY_REF",
    "MATRIX_MEDIA_ROOT_POLICY_REF",
    "MATRIX_ROOMS_MEDIA_BUDGET_REF",
    "MATRIX_ROOMS_MEDIA_KILL_SWITCH_REF",
    "MATRIX_ROOMS_MEDIA_LANES",
    "MATRIX_ROOMS_MEDIA_LIMIT_POLICY_REF",
    "MATRIX_ROOMS_MEDIA_PROVIDER_REF",
    "MATRIX_ROOMS_MEDIA_RETENTION_REF",
    "MATRIX_ROOMS_MEDIA_RUNTIME_REF",
    "MATRIX_ROOMS_MEDIA_SAFE_DISABLE_REF",
    "MATRIX_ROOMS_MEDIA_SCHEMA_VERSION",
    "MATRIX_ROOMS_MEDIA_TARGET_REF",
    "MATRIX_SEARCH_INDEX_POLICY_REF",
    "MEDIA_OPERATIONS",
    "NETWORK_OPERATIONS",
    "MatrixRoomsMediaLane",
    "MatrixRoomsMediaOperation",
    "matrix_rooms_media_lane",
    "matrix_rooms_media_rollback_ref",
]
