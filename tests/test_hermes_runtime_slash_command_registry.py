import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.runtime_gateway import (
    RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS,
    RUNTIME_SLASH_COMMAND_REGISTRY_CONTRACT_REF,
    RuntimeSlashCommandRegistryEntry,
    RuntimeSlashCommandRegistryReadModel,
    build_runtime_slash_command_registry_read_model,
)


client = TestClient(app)


def test_slash_command_registry_is_metadata_only_read_model() -> None:
    read_model = build_runtime_slash_command_registry_read_model()

    assert read_model.schema_version == "runtime_slash_command_registry.v1"
    assert read_model.contract_ref == RUNTIME_SLASH_COMMAND_REGISTRY_CONTRACT_REF
    assert read_model.status == "metadata_registry_all_commands_disabled"
    assert read_model.route_ref == "GET /api/runtime/slash-command-registry"
    assert read_model.cli_ref == "uaa runtime inspect-slash-command-registry"
    assert read_model.command_count == 6
    assert read_model.metadata_ready_count == 3
    assert read_model.disabled_count == 2
    assert read_model.blocked_count == 1
    assert read_model.command_contract_visible is True
    assert read_model.side_effect_class_visible is True
    assert read_model.approval_policy_visible is True
    assert read_model.idempotency_policy_visible is True
    assert read_model.receipt_plan_visible is True
    assert read_model.cli_api_alignment_visible is True
    assert read_model.chat_trigger_enabled is False
    assert read_model.runtime_invocation_enabled is False
    assert read_model.state_mutation_enabled is False
    assert read_model.shell_execution_enabled is False
    assert read_model.provider_call_enabled is False
    assert read_model.browser_automation_enabled is False
    assert read_model.connector_write_enabled is False
    assert read_model.control_center_mints_authority is False
    assert read_model.raw_prompt_persisted is False
    assert read_model.raw_response_persisted is False
    assert set(RUNTIME_SLASH_COMMAND_REGISTRY_BLOCKED_AUTHORITY_REFS).issubset(
        set(read_model.blocked_authority_refs)
    )


def test_slash_command_entries_are_disabled_or_blocked() -> None:
    read_model = build_runtime_slash_command_registry_read_model()
    statuses_by_trigger = {
        command.trigger_label: command.command_status for command in read_model.commands
    }

    assert statuses_by_trigger == {
        "/explain": "metadata_ready",
        "/plan": "metadata_ready",
        "/proof": "metadata_ready",
        "/run-tests": "disabled_requires_exact_lane",
        "/ask-agent": "disabled_requires_exact_lane",
        "/apply-patch": "blocked_high_authority",
    }
    for command in read_model.commands:
        assert command.command_ref.startswith("slash-command-ref:")
        assert command.docs_ref.startswith("docs-ref:")
        assert command.approval_policy_ref.startswith("approval-policy-ref:")
        assert command.idempotency_policy_ref.startswith("idempotency-policy-ref:")
        assert command.receipt_plan_ref.startswith("receipt-plan-ref:")
        assert command.proof_ref.startswith("proof-ref:")
        assert command.visible_in_control_center is True
        assert command.registered_metadata_only is True
        assert command.chat_trigger_enabled is False
        assert command.runtime_invocation_enabled is False
        assert command.state_mutation_enabled is False
        assert command.shell_execution_enabled is False
        assert command.provider_call_enabled is False
        assert command.browser_automation_enabled is False
        assert command.connector_write_enabled is False
        assert command.control_center_mints_authority is False
        assert command.raw_prompt_persisted is False
        assert command.raw_response_persisted is False


@pytest.mark.parametrize(
    "field",
    [
        "chat_trigger_enabled",
        "runtime_invocation_enabled",
        "state_mutation_enabled",
        "shell_execution_enabled",
        "provider_call_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "control_center_mints_authority",
        "raw_prompt_persisted",
        "raw_response_persisted",
    ],
)
def test_slash_command_registry_denies_authority_flags(field: str) -> None:
    payload = build_runtime_slash_command_registry_read_model().model_dump(
        mode="json"
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_SLASH_COMMAND_REGISTRY_AUTHORITY_DENIED",
    ):
        RuntimeSlashCommandRegistryReadModel(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "chat_trigger_enabled",
        "runtime_invocation_enabled",
        "state_mutation_enabled",
        "shell_execution_enabled",
        "provider_call_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "control_center_mints_authority",
        "raw_prompt_persisted",
        "raw_response_persisted",
    ],
)
def test_slash_command_entry_denies_authority_flags(field: str) -> None:
    payload = (
        build_runtime_slash_command_registry_read_model()
        .commands[0]
        .model_dump(mode="json")
    )
    payload[field] = True

    with pytest.raises(
        ValueError,
        match="RUNTIME_SLASH_COMMAND_ENTRY_AUTHORITY_DENIED",
    ):
        RuntimeSlashCommandRegistryEntry(**payload)


def test_slash_command_registry_api_returns_safe_read_model() -> None:
    response = client.get("/api/runtime/slash-command-registry")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "api_runtime_slash_command_registry"
    data = body["data"]
    assert data["route_ref"] == "GET /api/runtime/slash-command-registry"
    assert data["command_count"] == 6
    assert data["chat_trigger_enabled"] is False
    assert data["runtime_invocation_enabled"] is False
    assert data["state_mutation_enabled"] is False
    assert data["provider_call_enabled"] is False
    assert data["raw_prompt_persisted"] is False
    assert data["raw_response_persisted"] is False
    serialized = json.dumps(body).lower()
    assert "raw_prompt_value" not in serialized
    assert "raw_response_value" not in serialized
    assert "provider_payload_value" not in serialized


def test_slash_command_registry_cli_uses_same_read_model() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_runtime.py",
            "inspect-slash-command-registry",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    read_model = payload["runtime_slash_command_registry"]
    assert payload["metadata_only"] is True
    assert payload["safe_refs_only"] is True
    assert payload["raw_prompts_omitted"] is True
    assert payload["raw_responses_omitted"] is True
    assert payload["command_execution_performed"] is False
    assert payload["runtime_invocation_performed"] is False
    assert payload["state_mutation_performed"] is False
    assert payload["shell_execution_performed"] is False
    assert payload["provider_call_performed"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["connector_write_performed"] is False
    assert read_model["route_ref"] == "GET /api/runtime/slash-command-registry"
    assert read_model["cli_ref"] == "uaa runtime inspect-slash-command-registry"
    assert read_model["command_count"] == 6
