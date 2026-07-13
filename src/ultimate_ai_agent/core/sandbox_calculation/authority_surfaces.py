from __future__ import annotations

from typing import Any


def build_sealed_arithmetic_lane_catalog_entry(
    *,
    active_leases: list[Any],
    kill_switch_engaged: bool,
) -> Any:
    from ultimate_ai_agent.core.authority.contracts import (
        AuthorityCapability,
        AuthorityDomain,
        TrustMode,
        _authority_lane_entry,
    )

    return _authority_lane_entry(
        lane_id="calculation.sealed_arithmetic",
        label="Sealed deterministic calculation",
        status="implemented",
        authority_domain=AuthorityDomain.workspace,
        authority_capability=AuthorityCapability.execute,
        required_mode=TrustMode.delegated_mission_autonomous_window,
        side_effect_class="sandboxed_compute_read_only",
        risk="low",
        allowed_inputs_schema={
            "expression": "transient_ascii_bounded_arithmetic_only",
            "expression_hash": "exact_sha256_resource_binding",
            "target": "fixed_sealed_calculation_target",
            "backend": "pinned_source_bound_local_container",
            "host_mounts": False,
            "network": False,
        },
        denied_capabilities=[
            "general Python or CodeAct source",
            "shell execution",
            "network access",
            "host filesystem access or mutation",
            "host environment or credentials",
            "package installation",
            "background execution",
            "output as authority",
        ],
        approval_scope=(
            "No per-invocation approval after exact mission-scoped lease "
            "issuance and LocalApprovalAuthority validation"
        ),
        idempotency_required=True,
        rollback_posture=(
            "Disposable no-host-mount container; safe-disable and kill switch "
            "block new starts, with no host mutation to roll back."
        ),
        receipt_kind="sealed_calculation_content_free_execution_receipt",
        cli_inspection_ref="scripts/dev/uaa_runtime.py sealed-calculation inspect",
        api_operation_ref="GET /control-center/capabilities/availability",
        control_center_surface_ref="control-center-surface:actions-inbox",
        source_refs=[
            "lane-ref:sealed-arithmetic-exact-lease",
            "authority-capability-ref:sealed-arithmetic-v1",
            "receipt-contract-ref:sealed-calculation-execution-v1",
        ],
        blocked_reason_refs=[
            "blocked-authority:sealed-calculation:no-general-code",
            "blocked-authority:sealed-calculation:no-shell",
            "blocked-authority:sealed-calculation:no-network",
            "blocked-authority:sealed-calculation:no-host-files",
        ],
        active_leases=active_leases,
        kill_switch_engaged=kill_switch_engaged,
    )


def build_sealed_arithmetic_authority_mapping() -> Any:
    from ultimate_ai_agent.core.authority.contracts import (
        AuthorityCapability,
        AuthorityDomain,
        TrustMode,
        _mapping,
    )

    return _mapping(
        "lane-ref:sealed-arithmetic-exact-lease",
        "Sealed deterministic calculation",
        AuthorityDomain.workspace,
        AuthorityCapability.execute,
        TrustMode.delegated_mission_autonomous_window,
        "implemented_exact_mission_lease_required",
        [
            "GET /control-center/capabilities/availability",
            "GET /api/runtime/authority-missions/completions",
        ],
        [
            "scripts/dev/uaa_runtime.py sealed-calculation inspect",
            "scripts/dev/uaa_runtime.py sealed-calculation prepare",
            "scripts/dev/uaa_runtime.py sealed-calculation run",
        ],
        (
            "Executes one bounded arithmetic expression only after exact "
            "workspace/execute mission lease, policy, budget, kill-switch, "
            "safe-disable, target, input-hash, image-attestation, and atomic "
            "start checks. The exact lease replaces per-call approval; Python, "
            "shell, network, host files, environment, packages, and general "
            "CodeAct remain denied."
        ),
    )
