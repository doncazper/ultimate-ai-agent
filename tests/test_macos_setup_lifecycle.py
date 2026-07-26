from __future__ import annotations

import pytest

from scripts.dev import uaa_setup_lifecycle as cli
from ultimate_ai_agent.core.macos_setup_assistant import (
    MacOSSetupLifecycleContract,
    MacOSSetupLifecycleOperationName,
    MacOSSetupLifecycleOperationStatus,
    MacOSSetupLifecycleState,
    build_default_macos_setup_assistant_plan,
    build_macos_setup_lifecycle_contract,
    inspect_macos_setup_lifecycle_operation,
)


def test_lifecycle_contract_exposes_all_required_states_and_commands() -> None:
    contract = build_macos_setup_lifecycle_contract()

    assert contract.status == "blocked_by_authority"
    assert contract.current_state == MacOSSetupLifecycleState.prerequisites
    assert contract.state_sequence == list(MacOSSetupLifecycleState)
    assert [operation.operation for operation in contract.operations] == list(
        MacOSSetupLifecycleOperationName
    )
    assert {
        operation.operation: operation.status for operation in contract.operations
    } == {
        MacOSSetupLifecycleOperationName.plan: (
            MacOSSetupLifecycleOperationStatus.available_read_only
        ),
        MacOSSetupLifecycleOperationName.status: (
            MacOSSetupLifecycleOperationStatus.available_read_only
        ),
        MacOSSetupLifecycleOperationName.install: (
            MacOSSetupLifecycleOperationStatus.blocked_by_authority
        ),
        MacOSSetupLifecycleOperationName.verify: (
            MacOSSetupLifecycleOperationStatus.blocked_by_authority
        ),
        MacOSSetupLifecycleOperationName.repair: (
            MacOSSetupLifecycleOperationStatus.blocked_by_authority
        ),
        MacOSSetupLifecycleOperationName.stop: (
            MacOSSetupLifecycleOperationStatus.blocked_by_authority
        ),
        MacOSSetupLifecycleOperationName.rollback: (
            MacOSSetupLifecycleOperationStatus.blocked_by_authority
        ),
        MacOSSetupLifecycleOperationName.receipts: (
            MacOSSetupLifecycleOperationStatus.available_read_only
        ),
    }
    assert all(operation.authority_granted is False for operation in contract.operations)
    assert all(
        operation.state_change_performed is False
        for operation in contract.operations
    )
    assert contract.activation_authorized is False
    assert contract.installation_performed is False
    assert contract.process_launched is False
    assert contract.health_probe_performed is False
    assert contract.file_mutation_performed is False
    assert contract.credential_write_performed is False
    assert contract.subprocess_executed is False
    assert contract.live_network_request_performed is False
    assert contract.production_authority_enabled is False


def test_health_contract_names_complete_proof_without_claiming_live_checks() -> None:
    health = build_macos_setup_lifecycle_contract().health_contract

    assert health.required_check_refs == [
        "health-check-ref:setup-process-identity",
        "health-check-ref:setup-api-manifest-version",
        "health-check-ref:setup-loopback-bind",
        "health-check-ref:setup-control-center-compatibility",
        "health-check-ref:setup-forbidden-authority-absent",
    ]
    assert health.status == "blocked_by_authority"
    assert health.live_probe_performed is False
    assert health.process_identity_verified is False
    assert health.api_manifest_version_verified is False
    assert health.loopback_bind_verified is False
    assert health.control_center_compatibility_verified is False
    assert health.forbidden_authority_absence_verified is False


def test_setup_summary_embeds_the_same_python_lifecycle_contract() -> None:
    plan = build_default_macos_setup_assistant_plan()

    assert plan.lifecycle == build_macos_setup_lifecycle_contract()
    assert plan.lifecycle.python_core_service_ref == (
        "python-core-service:macos-setup-lifecycle"
    )
    assert plan.lifecycle.api_surface_ref == (
        "api-surface:control-center-setup-summary"
    )
    assert plan.lifecycle.cli_surface_ref == (
        "repo-local-command:macos-setup-lifecycle"
    )


def test_operation_inspection_uses_same_contract_and_fails_closed() -> None:
    install = inspect_macos_setup_lifecycle_operation("install")
    status = inspect_macos_setup_lifecycle_operation("status")

    assert install.status == MacOSSetupLifecycleOperationStatus.blocked_by_authority
    assert install.approval_required is True
    assert install.mutation_required is True
    assert install.target_state == MacOSSetupLifecycleState.installed
    assert status.status == MacOSSetupLifecycleOperationStatus.available_read_only
    assert status.approval_required is False
    assert status.mutation_required is False
    assert status.current_state == MacOSSetupLifecycleState.prerequisites


@pytest.mark.parametrize(
    "field_name",
    [
        "activation_authorized",
        "installation_performed",
        "process_launched",
        "health_probe_performed",
        "repair_performed",
        "stop_performed",
        "rollback_performed",
        "file_mutation_performed",
        "credential_write_performed",
        "subprocess_executed",
        "live_network_request_performed",
        "production_authority_enabled",
    ],
)
def test_lifecycle_contract_rejects_every_side_effect_claim(
    field_name: str,
) -> None:
    payload = build_macos_setup_lifecycle_contract().model_dump(mode="json")
    payload[field_name] = True

    with pytest.raises(ValueError, match="MACOS_SETUP_LIFECYCLE_"):
        MacOSSetupLifecycleContract.model_validate(payload)


@pytest.mark.parametrize(
    "field_name",
    [
        "authority_granted",
        "state_change_performed",
        "subprocess_executed",
        "file_mutation_performed",
        "process_mutation_performed",
        "credential_write_performed",
        "network_request_performed",
        "receipt_persisted",
    ],
)
def test_lifecycle_operation_rejects_every_execution_claim(
    field_name: str,
) -> None:
    payload = inspect_macos_setup_lifecycle_operation("install").model_dump(
        mode="json",
    )
    payload[field_name] = True

    with pytest.raises(ValueError, match="MACOS_SETUP_LIFECYCLE_"):
        type(inspect_macos_setup_lifecycle_operation("install")).model_validate(
            payload,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "process_identity_verified",
        "api_manifest_version_verified",
        "loopback_bind_verified",
        "control_center_compatibility_verified",
        "forbidden_authority_absence_verified",
        "live_probe_performed",
    ],
)
def test_health_contract_rejects_every_unproven_health_claim(
    field_name: str,
) -> None:
    health = build_macos_setup_lifecycle_contract().health_contract
    payload = health.model_dump(mode="json")
    payload[field_name] = True

    with pytest.raises(
        ValueError,
        match="MACOS_SETUP_HEALTH_PROOF_DENIED_WITHOUT_LIVE_PROBE",
    ):
        type(health).model_validate(payload)


def test_cli_read_only_status_is_human_readable_and_successful(capsys) -> None:
    assert cli.main(["status"]) == 0

    output = capsys.readouterr().out
    assert "macOS setup lifecycle: status" in output
    assert "status: available_read_only" in output
    assert "current state: prerequisites" in output
    assert "no setup side effect was performed" in output


def test_cli_install_is_human_readable_and_blocked(capsys) -> None:
    assert cli.main(["install"]) == cli.BLOCKED_EXIT_CODE

    output = capsys.readouterr().out
    assert "macOS setup lifecycle: install" in output
    assert "status: blocked_by_authority" in output
    assert "target state: installed" in output
    assert "accept the exact scoped setup authority milestone" in output


def test_cli_json_uses_safe_refs_and_reports_no_execution(capsys) -> None:
    assert cli.main(["verify", "--json"]) == cli.BLOCKED_EXIT_CODE

    output = capsys.readouterr().out
    assert '"status": "blocked_by_authority"' in output
    assert '"live_probe_required": true' in output
    assert '"subprocess_executed": false' in output
    assert '"network_request_performed": false' in output
