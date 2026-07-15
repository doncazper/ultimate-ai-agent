from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ultimate_ai_agent.core.authority.authority_constants import (
    MATRIX_AUTH_METHODS_READ_TOOL_REF,
    MATRIX_CREDENTIAL_DELETE_TOOL_REF,
    MATRIX_CREDENTIAL_STORE_ROTATE_TOOL_REF,
    MATRIX_DISCOVERY_READ_TOOL_REF,
    MATRIX_SESSION_LOGOUT_TOOL_REF,
    MATRIX_SESSION_CREDENTIAL_AUTH_CREATE_TOOL_REF,
    MATRIX_SESSION_REFRESH_TOOL_REF,
    MATRIX_SESSION_REVOKE_ALL_TOOL_REF,
    MATRIX_SESSION_SSO_CALLBACK_TOOL_REF,
    MATRIX_SESSION_SSO_LAUNCH_TOOL_REF,
)
from ultimate_ai_agent.core.authority.contracts import (
    AuthorityCapability,
    AuthorityDomain,
    TrustMode,
)


MATRIX_SESSION_SCHEMA_VERSION = "uaa-matrix-session.v1"
MATRIX_SESSION_PROVIDER_REF = "provider-ref:communications:matrix"
MATRIX_SESSION_TARGET_REF = "target-ref:communications:matrix-exact-homeserver"
MATRIX_SESSION_CREDENTIAL_BACKEND_REF = (
    "credential-backend-ref:matrix:macos-keychain-v1"
)
MATRIX_SESSION_SAFE_DISABLE_REF = "safe-disable-ref:communications:matrix-session"
MATRIX_SESSION_KILL_SWITCH_REF = "kill-switch-ref:authority-lease-local"
MATRIX_SESSION_BUDGET_REF = "budget-ref:communications:matrix-session-zero-cost"
MATRIX_DISCOVERY_PENDING_OBSERVATION_REF = (
    "observation-ref:matrix-discovery:pending"
)
MATRIX_DISCOVERY_PENDING_FRESHNESS_REF = "freshness-ref:matrix-discovery:pending"


class MatrixSessionOperation(str, Enum):
    discovery_read = "discovery_read"
    auth_methods_read = "auth_methods_read"
    credential_auth_create = "credential_auth_create"
    sso_launch = "sso_launch"
    sso_callback_consume = "sso_callback_consume"
    refresh = "refresh"
    logout = "logout"
    revoke_all = "revoke_all"
    credential_store_rotate = "credential_store_rotate"
    credential_delete = "credential_delete"


@dataclass(frozen=True)
class MatrixSessionLane:
    operation: MatrixSessionOperation
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    tool_ref: str
    tool_name: str
    authority_domain: AuthorityDomain
    authority_capability: AuthorityCapability
    required_mode: TrustMode
    approval_required: bool
    side_effect_class: str
    risk: str


def _lane(
    operation: MatrixSessionOperation,
    *,
    tool_ref: str,
    domain: AuthorityDomain,
    capability: AuthorityCapability,
    mode: TrustMode,
    approval_required: bool,
    side_effect_class: str,
    risk: str,
) -> MatrixSessionLane:
    suffix = operation.value.replace("_", "-")
    if operation in {
        MatrixSessionOperation.discovery_read,
        MatrixSessionOperation.auth_methods_read,
        MatrixSessionOperation.credential_store_rotate,
        MatrixSessionOperation.credential_delete,
    }:
        ref_slug = f"matrix-{suffix}"
    else:
        ref_slug = f"matrix-session-{suffix}"
    return MatrixSessionLane(
        operation=operation,
        lane_ref=f"authority-lane-ref:{ref_slug}",
        capability_ref=f"authority-capability-ref:{ref_slug}-v1",
        adapter_ref=f"authority-adapter-ref:{ref_slug}-v1",
        tool_ref=tool_ref,
        tool_name=f"matrix_session_{operation.value}",
        authority_domain=domain,
        authority_capability=capability,
        required_mode=mode,
        approval_required=approval_required,
        side_effect_class=side_effect_class,
        risk=risk,
    )


MATRIX_SESSION_LANES = {
    MatrixSessionOperation.discovery_read: _lane(
        MatrixSessionOperation.discovery_read,
        tool_ref=MATRIX_DISCOVERY_READ_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        mode=TrustMode.read_only,
        approval_required=False,
        side_effect_class="governed_network_read_only",
        risk="low",
    ),
    MatrixSessionOperation.auth_methods_read: _lane(
        MatrixSessionOperation.auth_methods_read,
        tool_ref=MATRIX_AUTH_METHODS_READ_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.read,
        mode=TrustMode.read_only,
        approval_required=False,
        side_effect_class="governed_network_read_only",
        risk="low",
    ),
    MatrixSessionOperation.credential_auth_create: _lane(
        MatrixSessionOperation.credential_auth_create,
        tool_ref=MATRIX_SESSION_CREDENTIAL_AUTH_CREATE_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.mutate,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        side_effect_class="authenticated_connector_mutation",
        risk="high",
    ),
    MatrixSessionOperation.sso_launch: _lane(
        MatrixSessionOperation.sso_launch,
        tool_ref=MATRIX_SESSION_SSO_LAUNCH_TOOL_REF,
        domain=AuthorityDomain.browser,
        capability=AuthorityCapability.execute,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        side_effect_class="system_browser_exact_launch",
        risk="high",
    ),
    MatrixSessionOperation.sso_callback_consume: _lane(
        MatrixSessionOperation.sso_callback_consume,
        tool_ref=MATRIX_SESSION_SSO_CALLBACK_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.mutate,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        side_effect_class="authenticated_connector_mutation",
        risk="high",
    ),
    MatrixSessionOperation.refresh: _lane(
        MatrixSessionOperation.refresh,
        tool_ref=MATRIX_SESSION_REFRESH_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.mutate,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        side_effect_class="authenticated_connector_mutation",
        risk="high",
    ),
    MatrixSessionOperation.logout: _lane(
        MatrixSessionOperation.logout,
        tool_ref=MATRIX_SESSION_LOGOUT_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.mutate,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        side_effect_class="authenticated_connector_mutation",
        risk="high",
    ),
    MatrixSessionOperation.revoke_all: _lane(
        MatrixSessionOperation.revoke_all,
        tool_ref=MATRIX_SESSION_REVOKE_ALL_TOOL_REF,
        domain=AuthorityDomain.messages,
        capability=AuthorityCapability.destructive,
        mode=TrustMode.full_machine_access_session,
        approval_required=True,
        side_effect_class="destructive_external",
        risk="high",
    ),
    MatrixSessionOperation.credential_store_rotate: _lane(
        MatrixSessionOperation.credential_store_rotate,
        tool_ref=MATRIX_CREDENTIAL_STORE_ROTATE_TOOL_REF,
        domain=AuthorityDomain.system_settings,
        capability=AuthorityCapability.write,
        mode=TrustMode.ask_before_changes,
        approval_required=True,
        side_effect_class="local_sensitive",
        risk="high",
    ),
    MatrixSessionOperation.credential_delete: _lane(
        MatrixSessionOperation.credential_delete,
        tool_ref=MATRIX_CREDENTIAL_DELETE_TOOL_REF,
        domain=AuthorityDomain.system_settings,
        capability=AuthorityCapability.destructive,
        mode=TrustMode.full_machine_access_session,
        approval_required=True,
        side_effect_class="destructive_local_sensitive",
        risk="high",
    ),
}


def matrix_session_lane(
    operation: MatrixSessionOperation | str,
) -> MatrixSessionLane:
    return MATRIX_SESSION_LANES[MatrixSessionOperation(operation)]
