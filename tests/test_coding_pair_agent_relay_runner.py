from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.dev import uaa_coding
from ultimate_ai_agent.core.code import (
    CODING_PAIR_AGENT_RELAY_LANE_REF,
    CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS,
    CodingPairAgentRelayReadModel,
    build_coding_multi_agent_review,
    build_coding_pair_agent_relay_read_model,
    validate_pair_agent_relay_transition,
)


ROOT = Path(__file__).resolve().parents[1]


def test_pair_agent_relay_read_model_is_preview_readiness_only() -> None:
    relay = build_coding_pair_agent_relay_read_model()
    payload = relay.model_dump(mode="json")

    assert relay.schema_version == "uaa-coding-pair-agent-relay-runner.v1"
    assert relay.lane_ref == CODING_PAIR_AGENT_RELAY_LANE_REF
    assert relay.canonical_lane_name == "coding_pair_agent_foreground_relay_runner"
    assert relay.status == "preview_readiness_execution_blocked"
    assert relay.backend_owned is True
    assert relay.preview_only is True
    assert relay.readiness_only is True
    assert relay.safe_refs_only is True
    assert relay.execution_promoted is False
    assert relay.foreground_adapter_execution_enabled is False
    assert relay.local_agent_process_execution_enabled is False
    assert relay.provider_sdk_call_enabled is False
    assert relay.provider_model_call_enabled is False
    assert relay.background_dispatch_enabled is False
    assert relay.generic_agent_bus_enabled is False
    assert relay.arbitrary_command_text_allowed is False
    assert relay.shell_subprocess_execution_enabled is False
    assert relay.plugin_runtime_import_enabled is False
    assert relay.browser_automation_enabled is False
    assert relay.connector_write_enabled is False
    assert relay.git_mutation_enabled is False
    assert relay.automatic_patch_apply_enabled is False
    assert relay.raw_transcript_durable is False
    assert relay.raw_prompt_persisted is False
    assert relay.raw_response_persisted is False
    assert relay.provider_payload_persisted is False
    assert relay.raw_log_persisted is False
    assert relay.raw_local_path_persisted is False
    assert relay.production_authority_enabled is False
    assert relay.broad_autonomy_enabled is False
    assert set(CODING_PAIR_AGENT_RELAY_REQUIRED_BLOCKED_REFS).issubset(
        relay.blocked_authority_refs
    )
    assert "scripts/dev/uaa_coding.py inspect-pair-agent-relay" in (
        relay.cli_inspection_refs
    )
    assert "/Users/" not in json.dumps(payload)
    assert "raw_prompt_value" not in json.dumps(payload)
    assert "raw_response_value" not in json.dumps(payload)


def test_pair_agent_run_contract_enforces_two_slots_and_bounded_limits() -> None:
    relay = build_coding_pair_agent_relay_read_model()
    run = relay.run_contract

    assert run.state == "blocked"
    assert len(run.agent_slots) == 2
    assert {slot.slot_id for slot in run.agent_slots} == {"agent_a", "agent_b"}
    assert run.max_turns == 6
    assert run.wall_clock_timeout_seconds == 900
    assert run.per_turn_output_limit_bytes == 12000
    assert run.background_dispatch_enabled is False
    assert run.unbounded_turns_enabled is False
    assert run.unbounded_timeout_enabled is False
    assert run.unbounded_output_enabled is False
    assert run.arbitrary_command_text_allowed is False
    assert {
        "stop-condition-ref:coding-pair:max-turns",
        "stop-condition-ref:coding-pair:timeout",
        "stop-condition-ref:coding-pair:user-stop",
        "stop-condition-ref:coding-pair:policy-block",
    }.issubset(set(run.stop_condition_refs))


def test_pair_agent_artifacts_and_receipts_are_safe_refs_only() -> None:
    relay = build_coding_pair_agent_relay_read_model()

    assert {artifact.artifact_kind for artifact in relay.artifacts} == {
        "outbound_turn_packet",
        "inbound_agent_response",
        "disagreement_summary",
        "candidate_action_list",
        "validation_plan",
        "final_synthesis",
        "blocked_state_report",
    }
    assert {receipt.receipt_kind for receipt in relay.receipts} == {
        "run_created",
        "approval_bound",
        "adapter_started",
        "turn_completed",
        "output_redacted",
        "stop_condition_reached",
        "run_completed",
        "run_blocked",
        "run_failed",
    }
    assert all(artifact.raw_content_omitted for artifact in relay.artifacts)
    assert all(artifact.raw_prompt_omitted for artifact in relay.artifacts)
    assert all(artifact.raw_response_omitted for artifact in relay.artifacts)
    assert all(artifact.provider_payload_omitted for artifact in relay.artifacts)
    assert all(artifact.raw_log_omitted for artifact in relay.artifacts)
    assert all(artifact.raw_local_path_omitted for artifact in relay.artifacts)
    assert all(not artifact.durable_evidence for artifact in relay.artifacts)
    assert all(not receipt.raw_content_included for receipt in relay.receipts)
    assert all(receipt.portable_receipt_ready for receipt in relay.receipts)


def test_pair_agent_relay_rejects_execution_promotion_flags() -> None:
    for flag_name in [
        "execution_promoted",
        "foreground_adapter_execution_enabled",
        "local_agent_process_execution_enabled",
        "provider_sdk_call_enabled",
        "provider_model_call_enabled",
        "background_dispatch_enabled",
        "generic_agent_bus_enabled",
        "arbitrary_command_text_allowed",
        "shell_subprocess_execution_enabled",
        "plugin_runtime_import_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "git_mutation_enabled",
        "automatic_patch_apply_enabled",
        "raw_transcript_durable",
        "raw_prompt_persisted",
        "raw_response_persisted",
        "provider_payload_persisted",
        "raw_log_persisted",
        "raw_local_path_persisted",
        "production_authority_enabled",
        "broad_autonomy_enabled",
    ]:
        payload = build_coding_pair_agent_relay_read_model().model_dump(mode="json")
        payload[flag_name] = True
        with pytest.raises(ValidationError, match=flag_name):
            CodingPairAgentRelayReadModel(**payload)


def test_pair_agent_state_machine_rejects_invalid_transitions() -> None:
    assert validate_pair_agent_relay_transition("created", "pending_approval")
    assert validate_pair_agent_relay_transition("waiting_agent_b", "completed")
    with pytest.raises(ValueError, match="transition denied"):
        validate_pair_agent_relay_transition("created", "completed")
    with pytest.raises(ValueError, match="transition denied"):
        validate_pair_agent_relay_transition("completed", "agent_a_running")


def test_multi_agent_review_nests_pair_agent_relay() -> None:
    review = build_coding_multi_agent_review()

    assert review.pair_agent_relay.lane_ref == CODING_PAIR_AGENT_RELAY_LANE_REF
    assert review.pair_agent_relay.execution_promoted is False
    assert review.pair_agent_relay.foreground_adapter_execution_enabled is False


def test_pair_agent_cli_surfaces_are_no_effect(
    capsys: pytest.CaptureFixture[str],
) -> None:
    commands = [
        "inspect-pair-agent-relay",
        "preview-pair-run",
        "inspect-pair-run",
        "inspect-pair-artifacts",
        "inspect-pair-receipts",
        "start-pair-run-readiness",
        "stop-pair-run-readiness",
    ]
    boundary = subprocess.run(
        [sys.executable, "scripts/dev/uaa_coding.py", commands[0]],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    outputs = [boundary.stdout]
    for command in commands[1:]:
        assert uaa_coding.main([command]) == 0
        outputs.append(capsys.readouterr().out)
    for stdout in outputs:
        payload = json.loads(stdout)
        serialized = json.dumps(payload).lower()
        assert "raw_prompt_value" not in serialized
        assert "raw_response_value" not in serialized
        assert "/users/" not in serialized
        assert "execution_performed" not in payload or payload[
            "execution_performed"
        ] is False


def test_pair_agent_verifier_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/verify_coding_pair_agent_relay_runner.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Coding Pair Agent Relay Runner verifier passed." in result.stdout
