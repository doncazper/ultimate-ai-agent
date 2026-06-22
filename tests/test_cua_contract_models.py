from __future__ import annotations

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.cua import (
    ComputerUseActionEnvelope,
    ComputerUseActionKind,
    ComputerUseActionMode,
    ComputerUseCapabilityContract,
    ComputerUseDoctorResult,
    build_blocked_computer_use_action_envelope,
    build_default_computer_use_capability_contract,
    build_default_computer_use_doctor_result,
    validate_computer_use_action_envelope,
    validate_computer_use_capability_contract,
    validate_computer_use_doctor_result,
)


def test_cua_capability_contract_accepts_safe_blocked_state() -> None:
    contract = build_default_computer_use_capability_contract()

    assert contract.status.value == "blocked"
    assert contract.driver_presence.value == "absent"
    assert contract.contract_only is True
    assert contract.runtime_driver_enabled is False
    assert contract.action_execution_enabled is False

    validate_computer_use_capability_contract(contract)


def test_cua_action_envelope_accepts_blocked_proposal_state() -> None:
    envelope = build_blocked_computer_use_action_envelope()

    assert envelope.proposed_action == ComputerUseActionKind.click
    assert envelope.action_mode == ComputerUseActionMode.blocked
    assert envelope.element_token_ref.startswith("element-token-ref:")
    assert envelope.snapshot_ref.startswith("snapshot-ref:")

    validate_computer_use_action_envelope(envelope)


def test_cua_capture_can_be_observe_only_proposal_without_execution() -> None:
    blocked = build_blocked_computer_use_action_envelope(
        action_envelope_ref="cua-action-envelope:observe-capture",
        proposed_action=ComputerUseActionKind.capture,
    )
    envelope = ComputerUseActionEnvelope(
        **{
            **blocked.model_dump(mode="python"),
            "action_mode": ComputerUseActionMode.observe_only,
        }
    )

    validate_computer_use_action_envelope(envelope)
    assert envelope.action_execution_performed is False


def test_cua_contract_rejects_raw_screenshots_ocr_and_private_ui_text() -> None:
    payload = build_default_computer_use_capability_contract().model_dump(mode="python")
    payload["evidence_refs"] = ["evidence:raw_screenshot_private_ui"]

    with pytest.raises(ValidationError):
        ComputerUseCapabilityContract(**payload)

    payload["evidence_refs"] = ["evidence:raw_ocr_private_screen"]
    with pytest.raises(ValidationError):
        ComputerUseCapabilityContract(**payload)


def test_cua_contract_rejects_raw_local_paths_and_provider_payloads() -> None:
    payload = build_default_computer_use_capability_contract().model_dump(mode="python")
    payload["evidence_refs"] = ["evidence:/Users/private/screen"]

    with pytest.raises(ValidationError):
        ComputerUseCapabilityContract(**payload)

    payload["evidence_refs"] = ["evidence:provider_payload"]
    with pytest.raises(ValidationError):
        ComputerUseCapabilityContract(**payload)


@pytest.mark.parametrize(
    "field_name",
    [
        "runtime_driver_enabled",
        "screenshot_capture_enabled",
        "os_accessibility_probe_enabled",
        "browser_automation_enabled",
        "native_desktop_automation_enabled",
        "action_execution_enabled",
        "connector_write_enabled",
        "provider_call_enabled",
        "subprocess_driver_launch_enabled",
        "production_authority_enabled",
    ],
)
def test_cua_contract_rejects_unsafe_authority_flags(field_name: str) -> None:
    payload = build_default_computer_use_capability_contract().model_dump(mode="python")
    payload[field_name] = True
    contract = ComputerUseCapabilityContract(**payload)

    with pytest.raises(ValueError):
        validate_computer_use_capability_contract(contract)


def test_cua_mutating_actions_must_remain_blocked() -> None:
    blocked = build_blocked_computer_use_action_envelope()
    envelope = ComputerUseActionEnvelope(
        **{
            **blocked.model_dump(mode="python"),
            "action_mode": ComputerUseActionMode.proposal_only,
        }
    )

    with pytest.raises(ValueError):
        validate_computer_use_action_envelope(envelope)


@pytest.mark.parametrize(
    "field_name",
    [
        "password_entry_requested",
        "credential_entry_requested",
        "two_factor_handling_requested",
        "permission_dialog_interaction_requested",
        "security_settings_change_requested",
        "account_deletion_requested",
        "billing_change_requested",
        "connector_write_requested",
        "shell_payload_typing_requested",
        "prompt_or_screenshot_instruction_authority_requested",
        "automatic_execution_requested",
    ],
)
def test_cua_action_envelope_rejects_forbidden_action_requests(field_name: str) -> None:
    payload = build_blocked_computer_use_action_envelope().model_dump(mode="python")
    payload[field_name] = True
    envelope = ComputerUseActionEnvelope(**payload)

    with pytest.raises(ValueError):
        validate_computer_use_action_envelope(envelope)


def test_cua_doctor_result_is_contract_only_and_does_not_inspect_host() -> None:
    result = build_default_computer_use_doctor_result()

    assert result.status.value == "unavailable"
    assert result.driver_launch_performed is False
    validate_computer_use_doctor_result(result)

    payload = result.model_dump(mode="python")
    payload["os_permission_inspection_performed"] = True
    unsafe = ComputerUseDoctorResult(**payload)

    with pytest.raises(ValueError):
        validate_computer_use_doctor_result(unsafe)
