from __future__ import annotations

from typing import Any

from .constants import MATRIX_HARNESS_LANES


def build_matrix_harness_lane_catalog_entries(
    *,
    active_leases: list[Any],
    kill_switch_engaged: bool,
) -> list[Any]:
    from ultimate_ai_agent.core.authority.contracts import (
        AuthorityDomain,
        TrustMode,
        _authority_lane_entry,
    )

    entries: list[Any] = []
    for operation, lane in MATRIX_HARNESS_LANES.items():
        approval_required = lane.approval_required
        entries.append(
            _authority_lane_entry(
                lane_id=f"matrix.harness.{operation.value}",
                label=f"Disposable Matrix harness {operation.value}",
                status=("approval_required" if approval_required else "implemented"),
                authority_domain=AuthorityDomain.messages,
                authority_capability=lane.authority_capability,
                required_mode=(
                    TrustMode.approved_safe_local_work_session
                    if approval_required
                    else TrustMode.read_only
                ),
                side_effect_class=lane.side_effect_class,
                risk=lane.risk,
                allowed_inputs_schema={
                    "request": "exact_safe_refs_and_complete_fingerprint",
                    "target": "fixed_loopback_disposable_synapse_harness",
                    "image": "official_digest_pinned_preprovisioned_only",
                    "lifecycle": "expected_state_and_generation_bound",
                    "authority": "exact_mission_lease_required",
                },
                denied_capabilities=[
                    "public binding",
                    "federation",
                    "open registration",
                    "production use",
                    "persistent credentials",
                    "real account authentication",
                    "message connector reads or writes",
                    "automatic image pull",
                    "raw output or path persistence",
                ],
                approval_scope=(
                    "fresh exact LocalApprovalAuthority validation bound to the complete request"
                    if approval_required
                    else "no mutation approval; exact current mission lease still required"
                ),
                idempotency_required=True,
                rollback_posture=(
                    "Stop and reset are separate exact approval-bound containment lanes; "
                    "uncertain partial lifecycle operations enter recovery-required posture."
                ),
                receipt_kind="matrix_harness_content_free_lifecycle_receipt",
                cli_inspection_ref=(
                    f"scripts/dev/uaa_communications.py harness {operation.value.replace('_', '-')}"
                ),
                api_operation_ref=(
                    "POST /control-center/communications/harness/"
                    f"{operation.value.replace('_', '-')}"
                ),
                control_center_surface_ref=(
                    "control-center-surface:communications-harness-readiness"
                ),
                source_refs=[
                    lane.lane_ref,
                    lane.capability_ref,
                    lane.adapter_ref,
                    lane.tool_ref,
                    "provider-ref:communications:matrix-local-synapse",
                ],
                blocked_reason_refs=[
                    "reason-ref:matrix-harness:exact-mission-lease-required",
                    "reason-ref:matrix-harness:image-preprovision-required",
                ],
                active_leases=active_leases,
                kill_switch_engaged=kill_switch_engaged,
            )
        )
    return entries


def build_matrix_harness_authority_mappings() -> list[Any]:
    from ultimate_ai_agent.core.authority.contracts import (
        AuthorityDomain,
        TrustMode,
        _mapping,
    )

    mappings: list[Any] = []
    for operation, lane in MATRIX_HARNESS_LANES.items():
        mappings.append(
            _mapping(
                lane.lane_ref,
                f"Disposable Matrix harness {operation.value}",
                AuthorityDomain.messages,
                lane.authority_capability,
                (
                    TrustMode.approved_safe_local_work_session
                    if lane.approval_required
                    else TrustMode.read_only
                ),
                "implemented_exact_mission_lease_required",
                [
                    "POST /control-center/communications/harness/"
                    f"{operation.value.replace('_', '-')}"
                ],
                [
                    "scripts/dev/uaa_communications.py harness "
                    f"{operation.value.replace('_', '-')}"
                ],
                (
                    "Exact loopback-only disposable Synapse harness lane with a pinned "
                    "pre-provisioned image, request-scoped policy, lease, approval when "
                    "mutating, budget, readiness, kill-switch, safe-disable, lifecycle "
                    "generation, ownership, idempotency, and content-free receipt checks."
                ),
            )
        )
    return mappings
