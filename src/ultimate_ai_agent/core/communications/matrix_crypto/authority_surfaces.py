from __future__ import annotations

from typing import Any

from .constants import MATRIX_CRYPTO_LANES, MatrixCryptoOperation


def build_matrix_crypto_lane_catalog_entries(
    *, active_leases: list[Any], kill_switch_engaged: bool
) -> list[Any]:
    from ultimate_ai_agent.core.authority.contracts import _authority_lane_entry

    entries: list[Any] = []
    for operation, lane in MATRIX_CRYPTO_LANES.items():
        entries.append(
            _authority_lane_entry(
                lane_id=f"matrix.crypto.{operation.value}",
                label=f"Matrix crypto {operation.value.replace('_', ' ')}",
                status="blocked",
                authority_domain=lane.authority_domain,
                authority_capability=lane.authority_capability,
                required_mode=lane.required_mode,
                side_effect_class=lane.side_effect_class,
                risk="blocked",
                allowed_inputs_schema={
                    "request": "safe_refs_and_complete_fingerprint_only",
                    "scope": "exact_account_device_store_backup_and_recovery_refs",
                    "authority": "fresh_policy_approval_and_session_lease",
                    "deadline": "maximum_five_minute_prestart_window",
                    "budget": "explicit_zero_cost_operation_budget",
                },
                denied_capabilities=[
                    "recovery material in API, CLI, React, logs, receipts, fixtures, or screenshots",
                    "ephemeral crypto claimed as persistent runtime",
                    "unverified device trust or stale verification",
                    "in-place restore or backup rollback",
                    "standing crypto authority or global callable state",
                    "legacy crypto APIs",
                ],
                approval_scope=(
                    "no mutation approval; exact current lease still required"
                    if not lane.approval_required
                    else "fresh exact LocalApprovalAuthority validation bound to the complete request"
                ),
                idempotency_required=True,
                rollback_posture=(
                    "No rollback for a read; safe-disable blocks new starts."
                    if operation == MatrixCryptoOperation.backup_status_read
                    else "No runtime starts until the persistent broker proves exact rollback or irreversibility."
                ),
                receipt_kind="matrix_crypto_content_free_receipt",
                cli_inspection_ref=(
                    "scripts/dev/uaa_communications.py matrix-crypto propose "
                    f"{operation.value.replace('_', '-')}"
                ),
                api_operation_ref=(
                    "POST /control-center/communications/matrix-crypto/proposal"
                ),
                control_center_surface_ref=(
                    "control-center-surface:messenger-sessions-recovery"
                ),
                source_refs=[
                    lane.lane_ref,
                    lane.capability_ref,
                    lane.adapter_ref,
                    "provider-ref:communications:matrix",
                ],
                blocked_reason_refs=[
                    "reason-ref:matrix-crypto:persistent-rust-backend-required",
                    "reason-ref:matrix-crypto:authenticated-session-required",
                    "reason-ref:matrix-crypto:request-scoped-evaluation-required",
                ],
                unsupported_adapter_refs=[
                    "adapter-ref:matrix-crypto:persistent-rust-backend-required"
                ],
                active_leases=active_leases,
                kill_switch_engaged=kill_switch_engaged,
            )
        )
    return entries


def build_matrix_crypto_authority_mappings() -> list[Any]:
    from ultimate_ai_agent.core.authority.contracts import _mapping

    return [
        _mapping(
            lane.lane_ref,
            f"Matrix crypto {operation.value.replace('_', ' ')}",
            lane.authority_domain,
            lane.authority_capability,
            lane.required_mode,
            "accepted_exact_authority_runtime_blocked_persistent_broker_required",
            ["POST /control-center/communications/matrix-crypto/proposal"],
            [
                "scripts/dev/uaa_communications.py matrix-crypto propose "
                f"{operation.value.replace('_', '-')}"
            ],
            (
                "Exact Matrix crypto authority contract requiring fresh request-scoped "
                "policy, approval where mutating, session lease, budget, readiness, "
                "target, kill-switch, safe-disable, idempotency, and content-free receipts."
            ),
            unsupported_adapter_refs=[
                "adapter-ref:matrix-crypto:persistent-rust-backend-required"
            ],
        )
        for operation, lane in MATRIX_CRYPTO_LANES.items()
    ]
