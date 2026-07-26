from __future__ import annotations

from ultimate_ai_agent.core.macos_setup_assistant.contracts import (
    MacOSSetupHealthContract,
    MacOSSetupLifecycleContract,
    MacOSSetupLifecycleOperation,
    MacOSSetupLifecycleOperationName,
    MacOSSetupLifecycleOperationStatus,
    MacOSSetupLifecycleState,
)


_READ_ONLY_OPERATIONS = {
    MacOSSetupLifecycleOperationName.plan,
    MacOSSetupLifecycleOperationName.status,
    MacOSSetupLifecycleOperationName.receipts,
}

_TARGET_STATES = {
    MacOSSetupLifecycleOperationName.plan: MacOSSetupLifecycleState.prerequisites,
    MacOSSetupLifecycleOperationName.status: MacOSSetupLifecycleState.prerequisites,
    MacOSSetupLifecycleOperationName.install: MacOSSetupLifecycleState.installed,
    MacOSSetupLifecycleOperationName.verify: MacOSSetupLifecycleState.healthy,
    MacOSSetupLifecycleOperationName.repair: MacOSSetupLifecycleState.healthy,
    MacOSSetupLifecycleOperationName.stop: MacOSSetupLifecycleState.stopping,
    MacOSSetupLifecycleOperationName.rollback: MacOSSetupLifecycleState.rolled_back,
    MacOSSetupLifecycleOperationName.receipts: MacOSSetupLifecycleState.prerequisites,
}

_OPERATION_SUMMARIES = {
    MacOSSetupLifecycleOperationName.plan: (
        "Inspect the exact local setup lifecycle plan without changing local state."
    ),
    MacOSSetupLifecycleOperationName.status: (
        "Inspect backend-owned lifecycle posture without probing or launching a process."
    ),
    MacOSSetupLifecycleOperationName.install: (
        "Installation remains blocked until an exact setup mutation milestone is accepted."
    ),
    MacOSSetupLifecycleOperationName.verify: (
        "Live process and readiness verification remains blocked until probe authority is accepted."
    ),
    MacOSSetupLifecycleOperationName.repair: (
        "Repair remains blocked until exact artifact scope and rollback authority are accepted."
    ),
    MacOSSetupLifecycleOperationName.stop: (
        "Process stop remains blocked until exact process identity and control authority are accepted."
    ),
    MacOSSetupLifecycleOperationName.rollback: (
        "Rollback execution remains blocked until an exact installed artifact receipt exists."
    ),
    MacOSSetupLifecycleOperationName.receipts: (
        "Inspect planned receipt and rollback refs without claiming a durable setup receipt."
    ),
}


def build_macos_setup_lifecycle_contract() -> MacOSSetupLifecycleContract:
    return MacOSSetupLifecycleContract(
        state_sequence=list(MacOSSetupLifecycleState),
        operations=[
            _build_operation(operation)
            for operation in MacOSSetupLifecycleOperationName
        ],
        health_contract=MacOSSetupHealthContract(
            required_check_refs=[
                "health-check-ref:setup-process-identity",
                "health-check-ref:setup-api-manifest-version",
                "health-check-ref:setup-loopback-bind",
                "health-check-ref:setup-control-center-compatibility",
                "health-check-ref:setup-forbidden-authority-absent",
            ],
            safe_summary=(
                "The complete readiness proof is typed but no live process, API, "
                "bind, compatibility, or authority probe has run."
            ),
        ),
        authority_prerequisite_ref="authority-prerequisite:macos-setup-exact-lifecycle",
        authority_state_ref="authority-state:macos-setup-lifecycle:not-granted",
        python_core_service_ref="python-core-service:macos-setup-lifecycle",
        api_surface_ref="api-surface:control-center-setup-summary",
        cli_surface_ref="repo-local-command:macos-setup-lifecycle",
        control_center_surface_ref="control-center-surface:macos-setup-lifecycle",
        safe_disable_ref="safe-disable-ref:macos-setup-lifecycle:disabled",
        rollback_contract_ref="rollback-contract-ref:macos-setup-lifecycle",
        receipt_contract_ref="receipt-contract-ref:macos-setup-lifecycle",
        blocked_reason_refs=[
            "blocked-reason-ref:setup-install-authority-missing",
            "blocked-reason-ref:setup-process-authority-missing",
            "blocked-reason-ref:setup-file-mutation-authority-missing",
            "blocked-reason-ref:setup-credential-write-authority-missing",
        ],
        safe_summary=(
            "Lifecycle state, command, health, receipt, and rollback contracts are "
            "available for inspection; every live activation remains blocked by authority."
        ),
    )


def inspect_macos_setup_lifecycle_operation(
    operation: MacOSSetupLifecycleOperationName | str,
) -> MacOSSetupLifecycleOperation:
    operation_name = MacOSSetupLifecycleOperationName(operation)
    contract = build_macos_setup_lifecycle_contract()
    return next(
        item for item in contract.operations if item.operation == operation_name
    )


def _build_operation(
    operation: MacOSSetupLifecycleOperationName,
) -> MacOSSetupLifecycleOperation:
    read_only = operation in _READ_ONLY_OPERATIONS
    return MacOSSetupLifecycleOperation(
        operation=operation,
        command_ref=f"repo-local-command:macos-setup-lifecycle:{operation.value}",
        status=(
            MacOSSetupLifecycleOperationStatus.available_read_only
            if read_only
            else MacOSSetupLifecycleOperationStatus.blocked_by_authority
        ),
        current_state=MacOSSetupLifecycleState.prerequisites,
        target_state=_TARGET_STATES[operation],
        safe_summary=_OPERATION_SUMMARIES[operation],
        exact_scope_ref=f"scope-ref:macos-setup-lifecycle:{operation.value}",
        approval_ref=f"approval-ref:macos-setup-lifecycle:{operation.value}",
        idempotency_key_ref=f"idempotency-ref:macos-setup-lifecycle:{operation.value}",
        receipt_ref=f"receipt-plan:macos-setup-lifecycle:{operation.value}",
        rollback_ref=f"rollback-plan:macos-setup-lifecycle:{operation.value}",
        safe_disable_ref=f"safe-disable-ref:macos-setup-lifecycle:{operation.value}",
        evidence_refs=[
            "docs-ref:uaa-setup-assistant-plan",
            "packaging-proof:local-macos-app-bundle",
        ],
        verifier_refs=[
            "pytest:test-macos-setup-lifecycle",
            "verifier:control-center-frontend",
        ],
        reason_codes=(
            ["MACOS_SETUP_LIFECYCLE_READ_ONLY_INSPECTION"]
            if read_only
            else [
                "MACOS_SETUP_LIFECYCLE_AUTHORITY_NOT_GRANTED",
                "MACOS_SETUP_LIFECYCLE_NO_SIDE_EFFECTS",
            ]
        ),
        mutation_required=operation
        in {
            MacOSSetupLifecycleOperationName.install,
            MacOSSetupLifecycleOperationName.repair,
            MacOSSetupLifecycleOperationName.stop,
            MacOSSetupLifecycleOperationName.rollback,
        },
        live_probe_required=operation == MacOSSetupLifecycleOperationName.verify,
        approval_required=not read_only,
    )
