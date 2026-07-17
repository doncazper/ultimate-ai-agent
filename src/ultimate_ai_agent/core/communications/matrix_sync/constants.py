from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ultimate_ai_agent.core.authority.authority_constants import (
    MATRIX_CACHE_KEY_CREATE_TOOL_REF,
    MATRIX_CACHE_KEY_DELETE_TOOL_REF,
    MATRIX_CACHE_KEY_ROTATE_TOOL_REF,
    MATRIX_CACHE_MIGRATE_TOOL_REF,
    MATRIX_CACHE_PURGE_TOOL_REF,
    MATRIX_CACHE_READ_TOOL_REF,
    MATRIX_CACHE_WRITE_TOOL_REF,
    MATRIX_RECEIPT_PROJECT_READ_TOOL_REF,
    MATRIX_ROOM_STATE_READ_TOOL_REF,
    MATRIX_SYNC_READ_TOOL_REF,
    MATRIX_TIMELINE_PAGINATE_READ_TOOL_REF,
    MATRIX_TYPING_PROJECT_READ_TOOL_REF,
)
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityDomain,
    TrustMode,
)


MATRIX_SYNC_SCHEMA_VERSION = "uaa-matrix-sync.v1"
MATRIX_SYNC_PROVIDER_REF = "provider-ref:communications:matrix"
MATRIX_SYNC_ADAPTER_RUNTIME_REF = "runtime-ref:matrix-js-sdk:read-only-sync-v1"
MATRIX_SYNC_TARGET_REF = "target-ref:communications:matrix-exact-homeserver"
MATRIX_SYNC_CREDENTIAL_BACKEND_REF = "credential-backend-ref:matrix:one-use-broker-v1"
MATRIX_SYNC_CACHE_BACKEND_REF = "cache-backend-ref:matrix:protected-container-v1"
MATRIX_SYNC_CACHE_SCHEMA_REF = "cache-schema-ref:matrix:protected-container-v1"
MATRIX_SYNC_SAFE_DISABLE_REF = "safe-disable-ref:communications:matrix-sync"
MATRIX_SYNC_KILL_SWITCH_REF = "kill-switch-ref:authority-lease-local"
MATRIX_SYNC_BUDGET_REF = "budget-ref:communications:matrix-sync-zero-cost"
MATRIX_SYNC_RETENTION_REF = "retention-ref:matrix-cache:bounded-local-v1"
MATRIX_SYNC_BACKUP_POSTURE_REF = "backup-posture-ref:matrix-cache:disabled-v1"
MATRIX_SYNC_MAX_ROOMS = 128
MATRIX_SYNC_MAX_EVENTS = 500
MATRIX_SYNC_MAX_BYTES = 1024 * 1024
MATRIX_SYNC_MAX_CACHE_BYTES = 16 * 1024 * 1024
MATRIX_SYNC_MAX_CACHE_EVENTS = 5_000
MATRIX_SYNC_MAX_ROOM_EVENT_REFS = 2_000
MATRIX_SYNC_CACHE_MIN_FREE_BYTES = 8 * 1024 * 1024
MATRIX_SYNC_MAX_RELATION_DEPTH = 16


class MatrixSyncOperation(str, Enum):
    sync_read = "sync_read"
    timeline_paginate_read = "timeline_paginate_read"
    room_state_read = "room_state_read"
    receipt_project_read = "receipt_project_read"
    typing_project_read = "typing_project_read"
    cache_read = "cache_read"
    cache_write = "cache_write"
    cache_migrate = "cache_migrate"
    cache_purge = "cache_purge"
    cache_key_create = "cache_key_create"
    cache_key_rotate = "cache_key_rotate"
    cache_key_delete = "cache_key_delete"


MATRIX_SYNC_COMPOSED_DISPATCH_OPERATIONS = frozenset(
    {
        MatrixSyncOperation.sync_read,
        MatrixSyncOperation.timeline_paginate_read,
    }
)


@dataclass(frozen=True)
class MatrixSyncLane:
    operation: MatrixSyncOperation
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    tool_ref: str
    tool_name: str
    authority_domain: AuthorityDomain
    authority_capability: AuthorityCapability
    required_mode: TrustMode
    approval_required: bool
    network_read: bool
    side_effect_class: str
    risk: str


def _lane(
    operation: MatrixSyncOperation,
    *,
    tool_ref: str,
    domain: AuthorityDomain,
    capability: AuthorityCapability,
    mode: TrustMode,
    approval_required: bool,
    network_read: bool,
    side_effect_class: str,
    risk: str,
) -> MatrixSyncLane:
    slug = operation.value.replace("_", "-")
    return MatrixSyncLane(
        operation=operation,
        lane_ref=f"authority-lane-ref:matrix-{slug}",
        capability_ref=f"authority-capability-ref:matrix-{slug}-v1",
        adapter_ref=f"authority-adapter-ref:matrix-{slug}-v1",
        tool_ref=tool_ref,
        tool_name=f"matrix_sync_{operation.value}",
        authority_domain=domain,
        authority_capability=capability,
        required_mode=mode,
        approval_required=approval_required,
        network_read=network_read,
        side_effect_class=side_effect_class,
        risk=risk,
    )


MATRIX_SYNC_LANES = {
    MatrixSyncOperation.sync_read: _lane(
        MatrixSyncOperation.sync_read,
        tool_ref=MATRIX_SYNC_READ_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        mode=TrustMode.read_only,
        approval_required=False,
        network_read=True,
        side_effect_class="governed_network_read_only",
        risk="low",
    ),
    MatrixSyncOperation.timeline_paginate_read: _lane(
        MatrixSyncOperation.timeline_paginate_read,
        tool_ref=MATRIX_TIMELINE_PAGINATE_READ_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        mode=TrustMode.read_only,
        approval_required=False,
        network_read=True,
        side_effect_class="governed_network_read_only",
        risk="low",
    ),
    MatrixSyncOperation.room_state_read: _lane(
        MatrixSyncOperation.room_state_read,
        tool_ref=MATRIX_ROOM_STATE_READ_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        mode=TrustMode.read_only,
        approval_required=False,
        network_read=True,
        side_effect_class="governed_network_read_only",
        risk="low",
    ),
    MatrixSyncOperation.receipt_project_read: _lane(
        MatrixSyncOperation.receipt_project_read,
        tool_ref=MATRIX_RECEIPT_PROJECT_READ_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        mode=TrustMode.read_only,
        approval_required=False,
        network_read=False,
        side_effect_class="read_only",
        risk="low",
    ),
    MatrixSyncOperation.typing_project_read: _lane(
        MatrixSyncOperation.typing_project_read,
        tool_ref=MATRIX_TYPING_PROJECT_READ_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        mode=TrustMode.read_only,
        approval_required=False,
        network_read=False,
        side_effect_class="read_only",
        risk="low",
    ),
    MatrixSyncOperation.cache_read: _lane(
        MatrixSyncOperation.cache_read,
        tool_ref=MATRIX_CACHE_READ_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        mode=TrustMode.read_only,
        approval_required=False,
        network_read=False,
        side_effect_class="local_sensitive",
        risk="low",
    ),
    MatrixSyncOperation.cache_write: _lane(
        MatrixSyncOperation.cache_write,
        tool_ref=MATRIX_CACHE_WRITE_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.mutate,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        network_read=False,
        side_effect_class="local_sensitive",
        risk="high",
    ),
    MatrixSyncOperation.cache_migrate: _lane(
        MatrixSyncOperation.cache_migrate,
        tool_ref=MATRIX_CACHE_MIGRATE_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.mutate,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        network_read=False,
        side_effect_class="local_sensitive",
        risk="high",
    ),
    MatrixSyncOperation.cache_purge: _lane(
        MatrixSyncOperation.cache_purge,
        tool_ref=MATRIX_CACHE_PURGE_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.destructive,
        mode=TrustMode.full_machine_access_session,
        approval_required=True,
        network_read=False,
        side_effect_class="destructive_local_sensitive",
        risk="high",
    ),
    MatrixSyncOperation.cache_key_create: _lane(
        MatrixSyncOperation.cache_key_create,
        tool_ref=MATRIX_CACHE_KEY_CREATE_TOOL_REF,
        domain=AuthorityDomain.system_settings,
        capability=AuthorityCapability.write,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        network_read=False,
        side_effect_class="local_sensitive",
        risk="high",
    ),
    MatrixSyncOperation.cache_key_rotate: _lane(
        MatrixSyncOperation.cache_key_rotate,
        tool_ref=MATRIX_CACHE_KEY_ROTATE_TOOL_REF,
        domain=AuthorityDomain.system_settings,
        capability=AuthorityCapability.write,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        network_read=False,
        side_effect_class="local_sensitive",
        risk="high",
    ),
    MatrixSyncOperation.cache_key_delete: _lane(
        MatrixSyncOperation.cache_key_delete,
        tool_ref=MATRIX_CACHE_KEY_DELETE_TOOL_REF,
        domain=AuthorityDomain.system_settings,
        capability=AuthorityCapability.destructive,
        mode=TrustMode.full_machine_access_session,
        approval_required=True,
        network_read=False,
        side_effect_class="destructive_local_sensitive",
        risk="high",
    ),
}


def matrix_sync_lane(operation: MatrixSyncOperation | str) -> MatrixSyncLane:
    return MATRIX_SYNC_LANES[MatrixSyncOperation(operation)]
