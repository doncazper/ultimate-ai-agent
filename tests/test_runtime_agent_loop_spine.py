from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.dev import uaa_founder_loop
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.control_center.agent_loop import (
    ACTION_TOOL_LANE_POSTURE_CATEGORY_IDS,
    ACTION_TOOL_LANE_POSTURE_CONTRACT_REF,
    AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF,
    AGENT_LOOP_THREAD_CONTRACT_REF,
    AGENT_LOOP_THREAD_ROUTE_REF,
    DURABLE_ORCHESTRATION_POSTURE_CATEGORY_IDS,
    DURABLE_ORCHESTRATION_POSTURE_CONTRACT_REF,
    EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF,
    EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS,
    HIGH_MATURITY_COMPONENT_IDS,
    HIGH_MATURITY_SPINE_CONTRACT_REF,
    MODEL_PROVIDER_POSTURE_CATEGORY_IDS,
    MODEL_PROVIDER_POSTURE_CONTRACT_REF,
    SYSTEM_AGENT_EVAL_CATEGORY_IDS,
    SYSTEM_AGENT_EVAL_COVERAGE_CONTRACT_REF,
    build_agent_loop_thread_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


client = TestClient(app)


def _repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FounderLoopRepository:
    state_dir = tmp_path / "founder-loop"
    monkeypatch.setenv("UAA_FOUNDER_LOOP_STATE_DIR", str(state_dir))
    return FounderLoopRepository.from_env()


def _assert_safe_agent_loop_thread(thread: dict[str, object]) -> None:
    assert thread["schema_version"] == "runtime_agent_loop_thread.v1"
    assert thread["contract_ref"] == AGENT_LOOP_THREAD_CONTRACT_REF
    assert thread["route_ref"] == AGENT_LOOP_THREAD_ROUTE_REF
    assert thread["backend_owned"] is True
    assert thread["local_read_model_only"] is True
    assert thread["safe_refs_only"] is True
    assert thread["raw_content_included"] is False

    approval_posture = thread["approval_posture"]
    assert isinstance(approval_posture, dict)
    assert approval_posture["control_center_mints_authority"] is False
    assert approval_posture["action_execution_enabled"] is False
    assert approval_posture["approval_refs_are_identifiers_only"] is True

    authority_posture = thread["authority_posture"]
    assert isinstance(authority_posture, dict)
    assert authority_posture["python_core_owns_truth"] is True
    for denied_flag in [
        "control_center_mints_authority",
        "runtime_model_calls_enabled",
        "provider_sdk_calls_enabled",
        "live_web_fetching_enabled",
        "browser_automation_enabled",
        "connector_writes_enabled",
        "unrestricted_shell_enabled",
        "plugin_runtime_import_enabled",
        "memory_write_authority_enabled",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ]:
        assert authority_posture[denied_flag] is False

    plan = thread["plan"]
    assert isinstance(plan, dict)
    assert plan["steps"]
    assert all(step["execution_enabled"] is False for step in plan["steps"])
    assert thread["surface_bindings"]
    matrix = thread["operator_decision_matrix"]
    assert isinstance(matrix, dict)
    assert matrix["schema_version"] == "runtime_cockpit_cli_api_parity.v1"
    assert matrix["contract_ref"] == AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF
    assert matrix["backend_owned"] is True
    assert matrix["control_center_presentation_only"] is True
    assert matrix["safe_refs_only"] is True
    assert matrix["raw_content_included"] is False
    assert matrix["ui_mints_authority"] is False
    assert matrix["mutation_controls_enabled"] is False
    assert matrix["row_count"] == len(matrix["rows"])
    assert matrix["rows"]
    assert {row["surface"] for row in matrix["rows"]} >= {
        "Today",
        "Action Inbox",
        "Evidence",
        "Memory",
        "Trust",
    }
    for row in matrix["rows"]:
        assert row["backend_truth_required"] is True
        assert row["mutation_enabled"] is False
        assert row["backend_route_ref"].startswith("GET ")
        assert row["cli_ref"].startswith("scripts/dev/")
        assert row["primary_ref"]
    assert thread["blocked_authority_refs"]
    high_maturity = thread["high_maturity_spine_readiness"]
    assert isinstance(high_maturity, dict)
    assert high_maturity["schema_version"] == "high_maturity_agent_spine_coverage.v1"
    assert high_maturity["contract_ref"] == HIGH_MATURITY_SPINE_CONTRACT_REF
    assert high_maturity["backend_owned"] is True
    assert high_maturity["local_read_model_only"] is True
    assert high_maturity["safe_refs_only"] is True
    assert high_maturity["raw_content_included"] is False
    assert high_maturity["route_ref"] == AGENT_LOOP_THREAD_ROUTE_REF
    assert high_maturity["cli_ref"].endswith("inspect-high-maturity-spine")
    assert high_maturity["weakness_count"] == len(HIGH_MATURITY_COMPONENT_IDS)
    assert high_maturity["usable_or_better_count"] == len(HIGH_MATURITY_COMPONENT_IDS)
    assert high_maturity["overall_projection_0_100"] >= 70
    rows = high_maturity["rows"]
    assert [row["weakness_id"] for row in rows] == list(HIGH_MATURITY_COMPONENT_IDS)
    rows_by_id = {row["weakness_id"]: row for row in rows}
    assert rows_by_id["W2"]["status"] == "implemented"
    assert rows_by_id["W2"]["maturity"] == "strong"
    assert rows_by_id["W2"]["score_0_10"] == 8
    assert DURABLE_ORCHESTRATION_POSTURE_CONTRACT_REF in rows_by_id["W2"][
        "evidence_refs"
    ]
    durable = high_maturity["durable_orchestration_posture"]
    assert durable["contract_ref"] == DURABLE_ORCHESTRATION_POSTURE_CONTRACT_REF
    assert durable["backend_owned"] is True
    assert durable["local_read_model_only"] is True
    assert durable["safe_refs_only"] is True
    assert durable["raw_content_included"] is False
    assert durable["category_count"] == len(DURABLE_ORCHESTRATION_POSTURE_CATEGORY_IDS)
    assert durable["implemented_or_blocked_count"] == len(
        DURABLE_ORCHESTRATION_POSTURE_CATEGORY_IDS
    )
    assert durable["canonical_lifecycle_state_count"] > 0
    assert durable["canonical_event_type_count"] > 0
    assert durable["existing_exact_runtime_lane_count"] == 1
    assert durable["new_execution_authority_added"] is False
    assert durable["retry_execution_enabled"] is False
    assert durable["recovery_execution_enabled"] is False
    assert durable["cancel_execution_enabled"] is False
    assert durable["dead_letter_execution_enabled"] is False
    assert durable["background_worker_enabled"] is False
    assert durable["scheduler_enabled"] is False
    assert durable["autonomous_execution_enabled"] is False
    assert durable["provider_model_calls_added"] is False
    assert durable["connector_writes_added"] is False
    assert durable["unrestricted_shell_added"] is False
    assert durable["production_authority_added"] is False
    durable_rows = durable["rows"]
    assert [row["category_id"] for row in durable_rows] == list(
        DURABLE_ORCHESTRATION_POSTURE_CATEGORY_IDS
    )
    exact_runtime_rows = [
        row for row in durable_rows if row["existing_exact_runtime_lane"] is True
    ]
    assert [row["category_id"] for row in exact_runtime_rows] == [
        "approved_runtime_command_step"
    ]
    for durable_row in durable_rows:
        assert durable_row["safe_refs_only"] is True
        assert durable_row["raw_content_included"] is False
        assert durable_row["raw_payloads_persisted"] is False
        assert durable_row["read_model_executes_work"] is False
        assert durable_row["control_center_mints_authority"] is False
        assert durable_row["new_execution_authority_added"] is False
        assert durable_row["retry_execution_enabled"] is False
        assert durable_row["recovery_execution_enabled"] is False
        assert durable_row["cancel_execution_enabled"] is False
        assert durable_row["dead_letter_execution_enabled"] is False
        assert durable_row["background_worker_enabled"] is False
        assert durable_row["scheduler_enabled"] is False
        assert durable_row["autonomous_execution_enabled"] is False
        assert durable_row["provider_model_calls_added"] is False
        assert durable_row["connector_writes_added"] is False
        assert durable_row["unrestricted_shell_added"] is False
        assert durable_row["production_authority_added"] is False
        assert durable_row["evidence_refs"]
        assert durable_row["test_refs"]
        assert durable_row["blocked_authority_refs"]
    assert rows_by_id["W6"]["status"] == "implemented"
    assert rows_by_id["W6"]["maturity"] == "strong"
    assert rows_by_id["W6"]["score_0_10"] == 8
    assert rows_by_id["W5"]["status"] == "implemented"
    assert rows_by_id["W5"]["maturity"] == "strong"
    assert rows_by_id["W5"]["score_0_10"] == 8
    assert ACTION_TOOL_LANE_POSTURE_CONTRACT_REF in rows_by_id["W5"][
        "evidence_refs"
    ]
    action_tool = high_maturity["action_tool_lane_posture"]
    assert action_tool["contract_ref"] == ACTION_TOOL_LANE_POSTURE_CONTRACT_REF
    assert action_tool["catalog_contract_ref"] == (
        "contract-ref:runtime-action-tool-code-catalog:v1"
    )
    assert action_tool["backend_owned"] is True
    assert action_tool["local_read_model_only"] is True
    assert action_tool["safe_refs_only"] is True
    assert action_tool["raw_content_included"] is False
    assert action_tool["entry_count"] == len(action_tool["rows"])
    assert action_tool["preview_only_count"] == 4
    assert action_tool["exact_local_mutation_count"] == 1
    assert action_tool["exact_runtime_lane_count"] == 5
    assert action_tool["proposal_only_count"] == 5
    assert action_tool["blocked_count"] == 3
    assert set(action_tool["category_ids"]) == set(
        ACTION_TOOL_LANE_POSTURE_CATEGORY_IDS
    )
    for flag in [
        "generic_tool_execution_enabled",
        "unrestricted_shell_execution_enabled",
        "browser_automation_enabled",
        "connector_write_enabled",
        "plugin_runtime_import_enabled",
        "remote_execution_enabled",
        "provider_model_call_enabled",
        "background_autonomy_enabled",
        "production_authority_enabled",
    ]:
        assert action_tool[flag] is False
    exact_runtime = [
        row for row in action_tool["rows"] if row["exact_runtime_lane_available"]
    ]
    assert len(exact_runtime) == 5
    exact_local = [
        row for row in action_tool["rows"] if row["exact_local_mutation_available"]
    ]
    assert len(exact_local) == 1
    for lane_row in action_tool["rows"]:
        assert lane_row["safe_refs_only"] is True
        assert lane_row["raw_content_included"] is False
        assert lane_row["operator_visible"] is True
        assert lane_row["inspectable_now"] is True
        for flag in [
            "generic_tool_execution_enabled",
            "unrestricted_shell_execution_enabled",
            "browser_automation_enabled",
            "connector_write_enabled",
            "plugin_runtime_import_enabled",
            "remote_execution_enabled",
            "provider_model_call_enabled",
            "background_autonomy_enabled",
            "production_authority_enabled",
        ]:
            assert lane_row[flag] is False
    assert rows_by_id["W8"]["status"] == "implemented"
    assert rows_by_id["W8"]["maturity"] == "strong"
    assert rows_by_id["W8"]["score_0_10"] == 8
    assert MODEL_PROVIDER_POSTURE_CONTRACT_REF in rows_by_id["W8"][
        "evidence_refs"
    ]
    model_provider = high_maturity["model_provider_management"]
    assert model_provider["contract_ref"] == MODEL_PROVIDER_POSTURE_CONTRACT_REF
    assert model_provider["control_plane_contract_ref"] == (
        "contract-ref:model-provider-control-plane:v1"
    )
    assert model_provider["backend_owned"] is True
    assert model_provider["local_read_model_only"] is True
    assert model_provider["safe_refs_only"] is True
    assert model_provider["raw_content_included"] is False
    assert model_provider["category_count"] == len(MODEL_PROVIDER_POSTURE_CATEGORY_IDS)
    assert [row["category_id"] for row in model_provider["rows"]] == list(
        MODEL_PROVIDER_POSTURE_CATEGORY_IDS
    )
    assert model_provider["provider_adapter_count"] >= 2
    assert model_provider["delegated_runtime_model_count"] >= 1
    assert model_provider["model_slot_count"] == 8
    assert model_provider["role_count"] == 7
    assert model_provider["research_provider_count"] >= 1
    assert model_provider["router_trace_count"] >= 1
    assert model_provider["exact_tiny_provider_lane_available"] is True
    assert model_provider["exact_credential_validation_lane_available"] is True
    for flag in [
        "provider_sdk_call_enabled",
        "remote_model_call_enabled",
        "live_provider_network_call_enabled_by_default",
        "provider_router_execution_enabled",
        "model_router_execution_enabled",
        "model_output_authority_enabled",
        "memory_write_from_model_output_enabled",
        "runtime_selection_mutation_enabled",
        "local_runtime_process_started",
        "local_runtime_model_call_performed",
        "provider_payload_persisted",
        "production_authority_added",
    ]:
        assert model_provider[flag] is False
    for provider_row in model_provider["rows"]:
        assert provider_row["safe_refs_only"] is True
        assert provider_row["raw_content_included"] is False
        assert provider_row["evidence_refs"]
        assert provider_row["test_refs"]
        assert provider_row["blocked_authority_refs"]
        for flag in [
            "provider_sdk_call_enabled",
            "remote_model_call_enabled",
            "live_provider_network_call_enabled_by_default",
            "provider_router_execution_enabled",
            "model_router_execution_enabled",
            "model_output_authority_enabled",
            "memory_write_from_model_output_enabled",
            "runtime_selection_mutation_enabled",
            "local_runtime_process_started",
            "local_runtime_model_call_performed",
            "provider_payload_persisted",
            "production_authority_added",
        ]:
            assert provider_row[flag] is False
    assert "contract-ref:coding-patch-proposal-signed-evidence:v1" in (
        rows_by_id["W6"]["evidence_refs"]
    )
    assert "scripts/dev/uaa_coding.py verify-patch-proposal-evidence" in (
        rows_by_id["W6"]["evidence_refs"]
    )
    assert "contract-ref:coding-patch-proposal-signed-evidence:v1" in (
        rows_by_id["W9"]["evidence_refs"]
    )
    assert "tests/test_coding_cockpit_read_model.py" in rows_by_id["W9"]["test_refs"]
    assert rows_by_id["W7"]["status"] == "implemented"
    assert rows_by_id["W7"]["maturity"] == "strong"
    assert rows_by_id["W7"]["score_0_10"] == 8
    assert EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF in rows_by_id["W7"][
        "evidence_refs"
    ]
    external_info = high_maturity["external_information_handling"]
    assert external_info["contract_ref"] == EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF
    assert external_info["backend_owned"] is True
    assert external_info["local_read_model_only"] is True
    assert external_info["safe_refs_only"] is True
    assert external_info["raw_content_included"] is False
    assert external_info["category_count"] == len(
        EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS
    )
    assert external_info["implemented_or_blocked_count"] == len(
        EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS
    )
    assert external_info["existing_exact_network_lane_count"] == 1
    assert external_info["new_live_web_fetching_added"] is False
    assert external_info["browser_observe_enabled"] is False
    assert external_info["browser_action_execution_enabled"] is False
    assert external_info["provider_search_enabled"] is False
    assert external_info["provider_sdk_calls_added"] is False
    assert external_info["connector_writes_added"] is False
    assert external_info["memory_writes_added"] is False
    assert external_info["context_injection_added"] is False
    assert external_info["production_authority_added"] is False
    external_rows = external_info["rows"]
    assert [row["category_id"] for row in external_rows] == list(
        EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS
    )
    exact_rows = [
        row for row in external_rows if row["existing_exact_network_lane"] is True
    ]
    assert [row["category_id"] for row in exact_rows] == [
        "allowlisted_gateway_preview"
    ]
    for external_row in external_rows:
        assert external_row["safe_refs_only"] is True
        assert external_row["raw_content_included"] is False
        assert external_row["untrusted_content_can_instruct_agent"] is False
        assert external_row["external_content_can_grant_authority"] is False
        assert external_row["new_live_web_fetching_added"] is False
        assert external_row["browser_action_execution_enabled"] is False
        assert external_row["provider_sdk_calls_added"] is False
        assert external_row["connector_writes_added"] is False
        assert external_row["memory_writes_added"] is False
        assert external_row["context_injection_added"] is False
        assert external_row["production_authority_added"] is False
        assert external_row["evidence_refs"]
        assert external_row["test_refs"]
        assert external_row["blocked_authority_refs"]
    assert rows_by_id["W12"]["status"] == "implemented"
    assert rows_by_id["W12"]["maturity"] == "strong"
    assert rows_by_id["W12"]["score_0_10"] == 8
    assert SYSTEM_AGENT_EVAL_COVERAGE_CONTRACT_REF in rows_by_id["W12"][
        "evidence_refs"
    ]
    eval_coverage = high_maturity["system_eval_coverage"]
    assert eval_coverage["contract_ref"] == SYSTEM_AGENT_EVAL_COVERAGE_CONTRACT_REF
    assert eval_coverage["backend_owned"] is True
    assert eval_coverage["local_read_model_only"] is True
    assert eval_coverage["safe_refs_only"] is True
    assert eval_coverage["raw_content_included"] is False
    assert eval_coverage["category_count"] == len(SYSTEM_AGENT_EVAL_CATEGORY_IDS)
    assert eval_coverage["implemented_count"] == len(SYSTEM_AGENT_EVAL_CATEGORY_IDS)
    assert eval_coverage["model_intelligence_scored"] is False
    assert eval_coverage["runtime_model_calls_added"] is False
    assert eval_coverage["provider_sdk_calls_added"] is False
    assert eval_coverage["tool_execution_added"] is False
    eval_rows = eval_coverage["rows"]
    assert [row["category_id"] for row in eval_rows] == list(
        SYSTEM_AGENT_EVAL_CATEGORY_IDS
    )
    for eval_row in eval_rows:
        assert eval_row["safe_refs_only"] is True
        assert eval_row["model_intelligence_scored"] is False
        assert eval_row["runtime_model_calls_added"] is False
        assert eval_row["provider_sdk_calls_added"] is False
        assert eval_row["evidence_refs"]
        assert eval_row["test_refs"]
        assert eval_row["invariant_refs"]
    for row in rows:
        assert row["safe_refs_only"] is True
        assert row["authority_broadened"] is False
        assert row["runtime_model_calls_added"] is False
        assert row["provider_sdk_calls_added"] is False
        assert row["live_web_fetching_added"] is False
        assert row["browser_automation_added"] is False
        assert row["connector_writes_added"] is False
        assert row["unrestricted_shell_added"] is False
        assert row["plugin_runtime_import_added"] is False
        assert row["production_authority_added"] is False
        assert row["evidence_refs"]
        assert row["test_refs"]
        assert row["gap"]
        assert row["recommendation"]
    serialized = json.dumps(thread).lower()
    for unsafe_fragment in [
        "api_key",
        "/users/",
    ]:
        assert unsafe_fragment not in serialized
    assert "raw_prompt_omitted" in serialized
    assert "raw_response_omitted" in serialized
    assert "raw_provider_payload_omitted" in serialized


def test_agent_loop_thread_builder_composes_existing_safe_refs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    today = repo.today_summary(limit=12)
    thread = build_agent_loop_thread_read_model(
        today_summary=today,
        actions_inbox=repo.actions_inbox(limit=50),
        evidence_timeline=repo.evidence_timeline(limit=50),
        memory_review=repo.memory_review(limit=20),
        proof_index={"items": []},
        trust_authority_matrix={"lanes": []},
    )

    _assert_safe_agent_loop_thread(thread)
    assert thread["work_request"]["request_ref"].startswith(
        ("founder-action:", "work-request-ref:", "plan-ref:")
    )
    assert thread["current_state"]["next_safe_operator_decision"]


def test_agent_loop_thread_api_route_is_read_only_and_redacted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _repo(monkeypatch, tmp_path)

    response = client.get("/control-center/agent-loop/thread")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["operation"] == "control_center_agent_loop_thread"
    assert "safe_refs_only" in body["redactions_applied"]
    assert "read_only_control_center_projection" in body["redactions_applied"]
    _assert_safe_agent_loop_thread(body["data"])


def test_agent_loop_thread_cli_inspection_uses_same_backend_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    state_dir = tmp_path / "founder-loop"

    exit_code = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "inspect-agent-loop",
            "--limit",
            "8",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["command_ref"] == "repo-local-command:founder-loop-agent-loop-thread"
    assert output["safe_refs_only"] is True
    assert output["raw_content_omitted"] is True
    assert output["raw_paths_omitted"] is True
    _assert_safe_agent_loop_thread(output["agent_loop_thread"])


def test_cockpit_parity_cli_inspects_same_operator_matrix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    state_dir = tmp_path / "founder-loop"

    exit_code = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "inspect-cockpit-parity",
            "--limit",
            "8",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["command_ref"] == (
        "repo-local-command:founder-loop-cockpit-cli-api-parity"
    )
    assert output["safe_refs_only"] is True
    assert output["raw_content_omitted"] is True
    assert output["raw_paths_omitted"] is True
    matrix = output["operator_decision_matrix"]
    assert matrix["contract_ref"] == AGENT_LOOP_COCKPIT_PARITY_CONTRACT_REF
    assert matrix["route_ref"] == AGENT_LOOP_THREAD_ROUTE_REF
    assert matrix["cli_ref"].endswith("inspect-cockpit-parity")
    assert matrix["operator_can_decide_from_cockpit"] is True
    assert matrix["ui_mints_authority"] is False
    assert matrix["mutation_controls_enabled"] is False


def test_high_maturity_spine_cli_inspects_same_w1_w13_readiness(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    state_dir = tmp_path / "founder-loop"

    exit_code = uaa_founder_loop.main(
        [
            "--state-dir",
            str(state_dir),
            "inspect-high-maturity-spine",
            "--limit",
            "8",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["command_ref"] == (
        "repo-local-command:founder-loop-high-maturity-spine"
    )
    assert output["safe_refs_only"] is True
    assert output["raw_content_omitted"] is True
    assert output["raw_paths_omitted"] is True
    readiness = output["high_maturity_spine_readiness"]
    assert readiness["contract_ref"] == HIGH_MATURITY_SPINE_CONTRACT_REF
    assert readiness["route_ref"] == AGENT_LOOP_THREAD_ROUTE_REF
    assert readiness["cli_ref"].endswith("inspect-high-maturity-spine")
    assert [row["weakness_id"] for row in readiness["rows"]] == list(
        HIGH_MATURITY_COMPONENT_IDS
    )
    assert readiness["blocked_authority_refs"]
