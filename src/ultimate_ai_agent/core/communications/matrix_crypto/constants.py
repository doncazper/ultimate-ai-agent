from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityDomain,
    TrustMode,
)


MATRIX_CRYPTO_SCHEMA_VERSION = "uaa-matrix-crypto.v1"
MATRIX_CRYPTO_PROVIDER_REF = "provider-ref:communications:matrix"
MATRIX_CRYPTO_RUNTIME_REF = "runtime-ref:matrix-rust-crypto:adapter-required-v1"
MATRIX_CRYPTO_TARGET_REF = "target-ref:communications:matrix-crypto-exact-scope"
MATRIX_CRYPTO_STORE_BACKEND_REF = (
    "crypto-store-backend-ref:matrix:persistent-rust-store-required-v1"
)
MATRIX_CRYPTO_KEY_BACKEND_REF = (
    "credential-backend-ref:matrix:device-only-keychain-crypto-v1"
)
MATRIX_CRYPTO_BACKUP_BACKEND_REF = (
    "backup-backend-ref:matrix:dedicated-wrapping-key-required-v1"
)
MATRIX_CRYPTO_SAFE_DISABLE_REF = "safe-disable-ref:communications:matrix-crypto"
MATRIX_CRYPTO_KILL_SWITCH_REF = "kill-switch-ref:authority-lease-local"
MATRIX_CRYPTO_BUDGET_REF = "budget-ref:communications:matrix-crypto-zero-cost"


class MatrixCryptoOperation(str, Enum):
    crypto_store_initialize = "crypto_store_initialize"
    crypto_store_key_rotate = "crypto_store_key_rotate"
    crypto_store_key_delete = "crypto_store_key_delete"
    verification_request = "verification_request"
    verification_cancel = "verification_cancel"
    verification_confirm = "verification_confirm"
    device_revoke = "device_revoke"
    cross_signing_bootstrap = "cross_signing_bootstrap"
    backup_status_read = "backup_status_read"
    backup_configure = "backup_configure"
    backup_rotate = "backup_rotate"
    recovery_restore = "recovery_restore"
    identity_reset = "identity_reset"
    local_backup_create = "local_backup_create"
    local_backup_restore = "local_backup_restore"
    local_backup_delete = "local_backup_delete"
    local_backup_expiry_reconcile = "local_backup_expiry_reconcile"


_READ_OPERATIONS = frozenset({MatrixCryptoOperation.backup_status_read})
_DESTRUCTIVE_OPERATIONS = frozenset(
    {
        MatrixCryptoOperation.crypto_store_key_delete,
        MatrixCryptoOperation.device_revoke,
        MatrixCryptoOperation.identity_reset,
        MatrixCryptoOperation.local_backup_delete,
        MatrixCryptoOperation.local_backup_expiry_reconcile,
    }
)


@dataclass(frozen=True)
class MatrixCryptoLane:
    operation: MatrixCryptoOperation
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    tool_ref: str
    authority_domain: AuthorityDomain
    authority_capability: AuthorityCapability
    required_mode: TrustMode
    approval_required: bool
    destructive: bool
    side_effect_class: str
    risk: str


def _lane(operation: MatrixCryptoOperation) -> MatrixCryptoLane:
    slug = operation.value.replace("_", "-")
    read_only = operation in _READ_OPERATIONS
    destructive = operation in _DESTRUCTIVE_OPERATIONS
    if read_only:
        domain = AuthorityDomain.messages
        capability = AuthorityCapability.read
        mode = TrustMode.read_only
        side_effect_class = "local_sensitive"
        risk = "low"
    elif destructive:
        domain = AuthorityDomain.system_settings
        capability = AuthorityCapability.destructive
        mode = TrustMode.full_machine_access_session
        side_effect_class = "destructive_local_sensitive"
        risk = "high"
    else:
        domain = (
            AuthorityDomain.messages
            if operation
            in {
                MatrixCryptoOperation.verification_request,
                MatrixCryptoOperation.verification_cancel,
                MatrixCryptoOperation.verification_confirm,
                MatrixCryptoOperation.cross_signing_bootstrap,
                MatrixCryptoOperation.backup_configure,
                MatrixCryptoOperation.backup_rotate,
            }
            else AuthorityDomain.system_settings
        )
        capability = AuthorityCapability.mutate
        mode = TrustMode.ask_before_changes
        side_effect_class = (
            "authenticated_connector_mutation"
            if domain == AuthorityDomain.messages
            else "local_sensitive"
        )
        risk = "high"
    return MatrixCryptoLane(
        operation=operation,
        lane_ref=f"authority-lane-ref:matrix-crypto-{slug}",
        capability_ref=f"authority-capability-ref:matrix-crypto-{slug}-v1",
        adapter_ref=f"authority-adapter-ref:matrix-crypto-{slug}-v1",
        tool_ref=f"tool-ref:matrix-crypto-{slug}-v1",
        authority_domain=domain,
        authority_capability=capability,
        required_mode=mode,
        approval_required=not read_only,
        destructive=destructive,
        side_effect_class=side_effect_class,
        risk=risk,
    )


MATRIX_CRYPTO_LANES = {
    operation: _lane(operation) for operation in MatrixCryptoOperation
}


def matrix_crypto_lane(operation: MatrixCryptoOperation | str) -> MatrixCryptoLane:
    return MATRIX_CRYPTO_LANES[MatrixCryptoOperation(operation)]


def matrix_crypto_rollback_ref(operation: MatrixCryptoOperation | str) -> str:
    """Return the backend-owned rollback or irreversibility posture."""

    resolved = MatrixCryptoOperation(operation)
    slug = resolved.value.replace("_", "-")
    prefix = (
        "irreversibility-ref:matrix-crypto"
        if resolved in _DESTRUCTIVE_OPERATIONS
        else "rollback-readiness-ref:matrix-crypto"
    )
    return f"{prefix}:{slug}"
