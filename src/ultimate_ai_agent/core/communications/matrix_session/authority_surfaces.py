from __future__ import annotations

from typing import Any

from .constants import MATRIX_SESSION_LANES, MatrixSessionOperation


_HANDOFF_BLOCKED_OPERATIONS = {
    MatrixSessionOperation.credential_auth_create,
    MatrixSessionOperation.refresh,
    MatrixSessionOperation.logout,
    MatrixSessionOperation.revoke_all,
    MatrixSessionOperation.credential_store_rotate,
    MatrixSessionOperation.credential_delete,
}
_SSO_BLOCKED_OPERATIONS = {
    MatrixSessionOperation.sso_launch,
    MatrixSessionOperation.sso_callback_consume,
}


def build_matrix_session_lane_catalog_entries(
    *,
    active_leases: list[Any],
    kill_switch_engaged: bool,
) -> list[Any]:
    from ultimate_ai_agent.core.authority.contracts import _authority_lane_entry

    entries: list[Any] = []
    for operation, lane in MATRIX_SESSION_LANES.items():
        runtime_blocked = operation in (
            _HANDOFF_BLOCKED_OPERATIONS | _SSO_BLOCKED_OPERATIONS
        )
        blocked_reason_refs = [
            "reason-ref:matrix-session:exact-session-lease-required",
            "reason-ref:matrix-session:request-scoped-evaluation-required",
        ]
        if operation in _HANDOFF_BLOCKED_OPERATIONS:
            blocked_reason_refs.append(
                "reason-ref:matrix-session:authenticated-one-use-handoff-required"
            )
        if operation in _SSO_BLOCKED_OPERATIONS:
            blocked_reason_refs.append(
                "reason-ref:matrix-session:sso-broker-required"
            )
        entries.append(
            _authority_lane_entry(
                lane_id=f"matrix.session.{operation.value}",
                label=f"Matrix {operation.value.replace('_', ' ')}",
                status=(
                    "blocked"
                    if runtime_blocked
                    else "approval_required"
                    if lane.approval_required
                    else "implemented"
                ),
                authority_domain=lane.authority_domain,
                authority_capability=lane.authority_capability,
                required_mode=lane.required_mode,
                side_effect_class=lane.side_effect_class,
                risk="blocked" if runtime_blocked else lane.risk,
                allowed_inputs_schema={
                    "request": "exact_safe_refs_and_complete_fingerprint",
                    "target": "validated_exact_homeserver_and_endpoint_class",
                    "authority": "exact_session_lease_required",
                    "deadline": "bounded_prestart_deadline",
                    "budget": "explicit_zero_cost_operation_budget",
                },
                denied_capabilities=[
                    "raw authentication-material import",
                    "credentials in URLs, logs, receipts, fixtures, or API output",
                    "unvalidated redirects or private-network targets",
                    "embedded browser or arbitrary browser automation",
                    "message sync, room reads, sends, media, or crypto initialization",
                    "global connected, authorized, or callable state",
                ],
                approval_scope=(
                    "fresh exact LocalApprovalAuthority validation bound to the complete request"
                    if lane.approval_required
                    else "no mutation approval; exact current session lease still required"
                ),
                idempotency_required=True,
                rollback_posture=(
                    "Not applicable to a content-free read; safe-disable blocks new starts."
                    if not runtime_blocked
                    else "Blocked-unimplemented; no session or credential mutation starts."
                ),
                receipt_kind="matrix_session_content_free_receipt",
                cli_inspection_ref=(
                    "scripts/dev/uaa_communications.py matrix-session "
                    f"{operation.value.replace('_', '-')}"
                ),
                api_operation_ref=(
                    "POST /control-center/communications/matrix/"
                    f"{operation.value.replace('_', '-')}"
                ),
                control_center_surface_ref="control-center-surface:messenger-session-posture",
                source_refs=[
                    lane.lane_ref,
                    lane.capability_ref,
                    lane.adapter_ref,
                    lane.tool_ref,
                    "provider-ref:communications:matrix",
                ],
                blocked_reason_refs=blocked_reason_refs,
                unsupported_adapter_refs=(
                    [
                        "adapter-ref:matrix-session-authenticated-handoff:not-implemented"
                    ]
                    if operation in _HANDOFF_BLOCKED_OPERATIONS
                    else ["adapter-ref:matrix-session-sso-broker:not-implemented"]
                    if operation in _SSO_BLOCKED_OPERATIONS
                    else []
                ),
                active_leases=active_leases,
                kill_switch_engaged=kill_switch_engaged,
            )
        )
    return entries


def build_matrix_session_authority_mappings() -> list[Any]:
    from ultimate_ai_agent.core.authority.contracts import _mapping

    return [
        _mapping(
            lane.lane_ref,
            f"Matrix {operation.value.replace('_', ' ')}",
            lane.authority_domain,
            lane.authority_capability,
            lane.required_mode,
            (
                "accepted_exact_authority_runtime_blocked_authenticated_handoff_required"
                if operation in _HANDOFF_BLOCKED_OPERATIONS
                else "accepted_exact_authority_runtime_blocked_sso_broker_required"
                if operation in _SSO_BLOCKED_OPERATIONS
                else "implemented_exact_session_lease_required"
            ),
            [
                "POST /control-center/communications/matrix/"
                f"{operation.value.replace('_', '-')}"
            ],
            [
                "scripts/dev/uaa_communications.py matrix-session "
                f"{operation.value.replace('_', '-')}"
            ],
            (
                "Exact Matrix discovery/session lane requiring request-scoped policy, "
                "approval when mutating, session lease, budget, readiness, target, "
                "kill-switch, safe-disable, idempotency, and content-free receipt checks."
            ),
        )
        for operation, lane in MATRIX_SESSION_LANES.items()
    ]
