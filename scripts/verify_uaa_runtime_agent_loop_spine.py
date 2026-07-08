#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.manifest import build_api_manifest  # noqa: E402
from ultimate_ai_agent.core.control_center.agent_loop import (  # noqa: E402
    ACTION_TOOL_LANE_POSTURE_CATEGORY_IDS,
    ACTION_TOOL_LANE_POSTURE_CONTRACT_REF,
    AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS,
    AGENT_LOOP_THREAD_CONTRACT_REF,
    AGENT_LOOP_THREAD_ROUTE_REF,
    DURABLE_ORCHESTRATION_POSTURE_CATEGORY_IDS,
    DURABLE_ORCHESTRATION_POSTURE_CONTRACT_REF,
    EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF,
    EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS,
    HIGH_MATURITY_COMPONENT_IDS,
    HIGH_MATURITY_SPINE_CONTRACT_REF,
    SYSTEM_AGENT_EVAL_CATEGORY_IDS,
    SYSTEM_AGENT_EVAL_COVERAGE_CONTRACT_REF,
    build_agent_loop_thread_read_model,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


def main() -> int:
    failures: list[str] = []
    temp_dir = tempfile.TemporaryDirectory(prefix="uaa-agent-loop-verifier-")
    repo = FounderLoopRepository(Path(temp_dir.name) / "founder-loop")
    today = repo.today_summary(limit=12)
    thread = build_agent_loop_thread_read_model(
        today_summary=today,
        actions_inbox=repo.actions_inbox(limit=50),
        evidence_timeline=repo.evidence_timeline(limit=50),
        memory_review=repo.memory_review(limit=20),
        proof_index={"items": []},
        trust_authority_matrix={"lanes": []},
    )

    if thread.get("contract_ref") != AGENT_LOOP_THREAD_CONTRACT_REF:
        failures.append("Agent Loop contract ref drifted")
    if thread.get("route_ref") != AGENT_LOOP_THREAD_ROUTE_REF:
        failures.append("Agent Loop route ref drifted")
    for field in [
        "backend_owned",
        "local_read_model_only",
        "safe_refs_only",
    ]:
        if thread.get(field) is not True:
            failures.append(f"Agent Loop {field} must be true")
    if thread.get("raw_content_included") is not False:
        failures.append("Agent Loop must not include raw content")

    high_maturity = thread.get("high_maturity_spine_readiness")
    if not isinstance(high_maturity, dict):
        failures.append("High-Maturity Agent Spine readiness map missing")
    else:
        if high_maturity.get("contract_ref") != HIGH_MATURITY_SPINE_CONTRACT_REF:
            failures.append("High-Maturity Agent Spine contract ref drifted")
        if high_maturity.get("route_ref") != AGENT_LOOP_THREAD_ROUTE_REF:
            failures.append("High-Maturity Agent Spine route ref drifted")
        if not str(high_maturity.get("cli_ref", "")).endswith(
            "inspect-high-maturity-spine"
        ):
            failures.append("High-Maturity Agent Spine CLI ref missing")
        for field in [
            "backend_owned",
            "local_read_model_only",
            "safe_refs_only",
        ]:
            if high_maturity.get(field) is not True:
                failures.append(f"High-Maturity Agent Spine {field} must be true")
        if high_maturity.get("raw_content_included") is not False:
            failures.append("High-Maturity Agent Spine must not include raw content")
        rows = high_maturity.get("rows")
        if not isinstance(rows, list):
            failures.append("High-Maturity Agent Spine rows missing")
        else:
            weakness_ids = [row.get("weakness_id") for row in rows if isinstance(row, dict)]
            if weakness_ids != list(HIGH_MATURITY_COMPONENT_IDS):
                failures.append("High-Maturity Agent Spine W1-W13 coverage drifted")
            for row in rows:
                if not isinstance(row, dict):
                    failures.append("High-Maturity Agent Spine row is not an object")
                    continue
                if row.get("safe_refs_only") is not True:
                    failures.append(
                        f"High-Maturity Agent Spine row not safe-ref-only: {row.get('weakness_id')}"
                    )
                for forbidden_flag in [
                    "authority_broadened",
                    "runtime_model_calls_added",
                    "provider_sdk_calls_added",
                    "live_web_fetching_added",
                    "browser_automation_added",
                    "connector_writes_added",
                    "unrestricted_shell_added",
                    "plugin_runtime_import_added",
                    "production_authority_added",
                ]:
                    if row.get(forbidden_flag) is not False:
                        failures.append(
                            "High-Maturity Agent Spine broadened authority: "
                            f"{row.get('weakness_id')} {forbidden_flag}"
                        )
                for required_list in ["evidence_refs", "test_refs"]:
                    if not row.get(required_list):
                        failures.append(
                            "High-Maturity Agent Spine row missing "
                            f"{required_list}: {row.get('weakness_id')}"
                        )
            action_tool = high_maturity.get("action_tool_lane_posture")
            if not isinstance(action_tool, dict):
                failures.append(
                    "High-Maturity Agent Spine action/tool lane posture missing"
                )
            else:
                if action_tool.get("contract_ref") != (
                    ACTION_TOOL_LANE_POSTURE_CONTRACT_REF
                ):
                    failures.append("action/tool lane posture contract drifted")
                if set(action_tool.get("category_ids") or []) != set(
                    ACTION_TOOL_LANE_POSTURE_CATEGORY_IDS
                ):
                    failures.append("action/tool lane posture categories drifted")
                if action_tool.get("entry_count") != len(
                    action_tool.get("rows") or []
                ):
                    failures.append("action/tool lane posture entry count drifted")
                expected_counts = {
                    "preview_only_count": 4,
                    "exact_local_mutation_count": 1,
                    "exact_runtime_lane_count": 5,
                    "proposal_only_count": 5,
                    "blocked_count": 3,
                }
                for field, expected in expected_counts.items():
                    if action_tool.get(field) != expected:
                        failures.append(
                            f"action/tool lane posture {field} drifted"
                        )
                for field in [
                    "backend_owned",
                    "local_read_model_only",
                    "safe_refs_only",
                ]:
                    if action_tool.get(field) is not True:
                        failures.append(
                            f"action/tool lane posture {field} must be true"
                        )
                for field in [
                    "raw_content_included",
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
                    if action_tool.get(field) is not False:
                        failures.append(
                            f"action/tool lane posture {field} must be false"
                        )
                action_tool_rows = action_tool.get("rows")
                if not isinstance(action_tool_rows, list):
                    failures.append("action/tool lane posture rows missing")
                else:
                    if (
                        sum(
                            1
                            for row in action_tool_rows
                            if isinstance(row, dict)
                            and row.get("exact_runtime_lane_available") is True
                        )
                        != 5
                    ):
                        failures.append("action/tool exact runtime lane count drifted")
                    if (
                        sum(
                            1
                            for row in action_tool_rows
                            if isinstance(row, dict)
                            and row.get("exact_local_mutation_available") is True
                        )
                        != 1
                    ):
                        failures.append("action/tool exact local lane count drifted")
                    for row in action_tool_rows:
                        if not isinstance(row, dict):
                            failures.append(
                                "action/tool lane posture row is not an object"
                            )
                            continue
                        for field in ["safe_refs_only", "operator_visible", "inspectable_now"]:
                            if row.get(field) is not True:
                                failures.append(
                                    "action/tool lane posture row required true "
                                    f"field drifted: {row.get('capability_id')} {field}"
                                )
                        for field in [
                            "raw_content_included",
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
                            if row.get(field) is not False:
                                failures.append(
                                    "action/tool lane posture broadened authority: "
                                    f"{row.get('capability_id')} {field}"
                                )
            durable = high_maturity.get("durable_orchestration_posture")
            if not isinstance(durable, dict):
                failures.append(
                    "High-Maturity Agent Spine durable orchestration posture missing"
                )
            else:
                if durable.get("contract_ref") != (
                    DURABLE_ORCHESTRATION_POSTURE_CONTRACT_REF
                ):
                    failures.append("durable orchestration posture contract drifted")
                if durable.get("category_count") != len(
                    DURABLE_ORCHESTRATION_POSTURE_CATEGORY_IDS
                ):
                    failures.append("durable orchestration category count drifted")
                if durable.get("implemented_or_blocked_count") != len(
                    DURABLE_ORCHESTRATION_POSTURE_CATEGORY_IDS
                ):
                    failures.append("durable orchestration implementation count drifted")
                if durable.get("existing_exact_runtime_lane_count") != 1:
                    failures.append("durable orchestration exact lane count drifted")
                for field in [
                    "backend_owned",
                    "local_read_model_only",
                    "safe_refs_only",
                ]:
                    if durable.get(field) is not True:
                        failures.append(
                            f"durable orchestration posture {field} must be true"
                        )
                for field in [
                    "raw_content_included",
                    "new_execution_authority_added",
                    "retry_execution_enabled",
                    "recovery_execution_enabled",
                    "cancel_execution_enabled",
                    "dead_letter_execution_enabled",
                    "background_worker_enabled",
                    "scheduler_enabled",
                    "autonomous_execution_enabled",
                    "provider_model_calls_added",
                    "connector_writes_added",
                    "unrestricted_shell_added",
                    "production_authority_added",
                ]:
                    if durable.get(field) is not False:
                        failures.append(
                            f"durable orchestration posture {field} must be false"
                        )
                durable_rows = durable.get("rows")
                if not isinstance(durable_rows, list):
                    failures.append("durable orchestration posture rows missing")
                else:
                    durable_ids = [
                        row.get("category_id")
                        for row in durable_rows
                        if isinstance(row, dict)
                    ]
                    if durable_ids != list(DURABLE_ORCHESTRATION_POSTURE_CATEGORY_IDS):
                        failures.append("durable orchestration category ids drifted")
                    exact_rows = [
                        row
                        for row in durable_rows
                        if isinstance(row, dict)
                        and row.get("existing_exact_runtime_lane") is True
                    ]
                    if [row.get("category_id") for row in exact_rows] != [
                        "approved_runtime_command_step"
                    ]:
                        failures.append("durable orchestration exact lane drifted")
                    for row in durable_rows:
                        if not isinstance(row, dict):
                            failures.append(
                                "durable orchestration posture row is not an object"
                            )
                            continue
                        if row.get("safe_refs_only") is not True:
                            failures.append(
                                "durable orchestration row must be safe-ref-only: "
                                f"{row.get('category_id')}"
                            )
                        for field in [
                            "raw_content_included",
                            "raw_payloads_persisted",
                            "read_model_executes_work",
                            "control_center_mints_authority",
                            "new_execution_authority_added",
                            "retry_execution_enabled",
                            "recovery_execution_enabled",
                            "cancel_execution_enabled",
                            "dead_letter_execution_enabled",
                            "background_worker_enabled",
                            "scheduler_enabled",
                            "autonomous_execution_enabled",
                            "provider_model_calls_added",
                            "connector_writes_added",
                            "unrestricted_shell_added",
                            "production_authority_added",
                        ]:
                            if row.get(field) is not False:
                                failures.append(
                                    "durable orchestration posture broadened "
                                    f"authority: {row.get('category_id')} {field}"
                                )
                        for required_list in [
                            "evidence_refs",
                            "test_refs",
                            "blocked_authority_refs",
                        ]:
                            if not row.get(required_list):
                                failures.append(
                                    "durable orchestration row missing "
                                    f"{required_list}: {row.get('category_id')}"
                                )
            external_info = high_maturity.get("external_information_handling")
            if not isinstance(external_info, dict):
                failures.append(
                    "High-Maturity Agent Spine external information posture missing"
                )
            else:
                if external_info.get("contract_ref") != (
                    EXTERNAL_INFORMATION_HANDLING_CONTRACT_REF
                ):
                    failures.append("external information contract ref drifted")
                if external_info.get("category_count") != len(
                    EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS
                ):
                    failures.append(
                        "external information posture category count drifted"
                    )
                if external_info.get("implemented_or_blocked_count") != len(
                    EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS
                ):
                    failures.append(
                        "external information posture implementation count drifted"
                    )
                if external_info.get("existing_exact_network_lane_count") != 1:
                    failures.append(
                        "external information posture exact network lane count drifted"
                    )
                for field in [
                    "backend_owned",
                    "local_read_model_only",
                    "safe_refs_only",
                ]:
                    if external_info.get(field) is not True:
                        failures.append(
                            f"external information posture {field} must be true"
                        )
                for field in [
                    "raw_content_included",
                    "new_live_web_fetching_added",
                    "browser_observe_enabled",
                    "browser_action_execution_enabled",
                    "provider_search_enabled",
                    "provider_sdk_calls_added",
                    "connector_writes_added",
                    "memory_writes_added",
                    "context_injection_added",
                    "production_authority_added",
                ]:
                    if external_info.get(field) is not False:
                        failures.append(
                            f"external information posture {field} must be false"
                        )
                external_rows = external_info.get("rows")
                if not isinstance(external_rows, list):
                    failures.append("external information posture rows missing")
                else:
                    external_ids = [
                        row.get("category_id")
                        for row in external_rows
                        if isinstance(row, dict)
                    ]
                    if external_ids != list(EXTERNAL_INFORMATION_POSTURE_CATEGORY_IDS):
                        failures.append(
                            "external information posture category ids drifted"
                        )
                    exact_rows = [
                        row
                        for row in external_rows
                        if isinstance(row, dict)
                        and row.get("existing_exact_network_lane") is True
                    ]
                    if [row.get("category_id") for row in exact_rows] != [
                        "allowlisted_gateway_preview"
                    ]:
                        failures.append(
                            "external information exact network lane identity drifted"
                        )
                    for row in external_rows:
                        if not isinstance(row, dict):
                            failures.append(
                                "external information posture row is not an object"
                            )
                            continue
                        if row.get("safe_refs_only") is not True:
                            failures.append(
                                "external information row must be safe-ref-only: "
                                f"{row.get('category_id')}"
                            )
                        for field in [
                            "raw_content_included",
                            "untrusted_content_can_instruct_agent",
                            "external_content_can_grant_authority",
                            "new_live_web_fetching_added",
                            "browser_action_execution_enabled",
                            "provider_sdk_calls_added",
                            "connector_writes_added",
                            "memory_writes_added",
                            "context_injection_added",
                            "production_authority_added",
                        ]:
                            if row.get(field) is not False:
                                failures.append(
                                    "external information posture broadened "
                                    f"authority: {row.get('category_id')} {field}"
                                )
                        for required_list in [
                            "evidence_refs",
                            "test_refs",
                            "blocked_authority_refs",
                        ]:
                            if not row.get(required_list):
                                failures.append(
                                    "external information row missing "
                                    f"{required_list}: {row.get('category_id')}"
                                )
            system_eval = high_maturity.get("system_eval_coverage")
            if not isinstance(system_eval, dict):
                failures.append("High-Maturity Agent Spine system eval coverage missing")
            else:
                if system_eval.get("contract_ref") != (
                    SYSTEM_AGENT_EVAL_COVERAGE_CONTRACT_REF
                ):
                    failures.append("system eval coverage contract ref drifted")
                if system_eval.get("category_count") != len(
                    SYSTEM_AGENT_EVAL_CATEGORY_IDS
                ):
                    failures.append("system eval coverage category count drifted")
                if system_eval.get("implemented_count") != len(
                    SYSTEM_AGENT_EVAL_CATEGORY_IDS
                ):
                    failures.append("system eval coverage implemented count drifted")
                for field in [
                    "backend_owned",
                    "local_read_model_only",
                    "safe_refs_only",
                ]:
                    if system_eval.get(field) is not True:
                        failures.append(f"system eval coverage {field} must be true")
                for field in [
                    "raw_content_included",
                    "model_intelligence_scored",
                    "runtime_model_calls_added",
                    "provider_sdk_calls_added",
                    "tool_execution_added",
                    "shell_execution_added",
                    "browser_automation_added",
                    "connector_writes_added",
                    "memory_writes_added",
                    "context_injection_added",
                    "production_authority_added",
                ]:
                    if system_eval.get(field) is not False:
                        failures.append(f"system eval coverage {field} must be false")
                eval_rows = system_eval.get("rows")
                if not isinstance(eval_rows, list):
                    failures.append("system eval coverage rows missing")
                else:
                    eval_ids = [
                        row.get("category_id")
                        for row in eval_rows
                        if isinstance(row, dict)
                    ]
                    if eval_ids != list(SYSTEM_AGENT_EVAL_CATEGORY_IDS):
                        failures.append("system eval coverage category ids drifted")
                    for row in eval_rows:
                        if not isinstance(row, dict):
                            failures.append("system eval coverage row is not an object")
                            continue
                        if row.get("safe_refs_only") is not True:
                            failures.append(
                                "system eval coverage row must be safe-ref-only: "
                                f"{row.get('category_id')}"
                            )
                        for field in [
                            "model_intelligence_scored",
                            "runtime_model_calls_added",
                            "provider_sdk_calls_added",
                            "tool_execution_added",
                            "shell_execution_added",
                            "browser_automation_added",
                            "connector_writes_added",
                            "memory_writes_added",
                            "context_injection_added",
                            "production_authority_added",
                        ]:
                            if row.get(field) is not False:
                                failures.append(
                                    "system eval coverage broadened authority: "
                                    f"{row.get('category_id')} {field}"
                                )
                        for required_list in [
                            "evidence_refs",
                            "test_refs",
                            "invariant_refs",
                        ]:
                            if not row.get(required_list):
                                failures.append(
                                    "system eval coverage row missing "
                                    f"{required_list}: {row.get('category_id')}"
                                )

    authority = thread.get("authority_posture")
    if not isinstance(authority, dict):
        failures.append("Agent Loop authority posture missing")
    else:
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
            if authority.get(denied_flag) is not False:
                failures.append(f"Agent Loop broadened authority: {denied_flag}")

    blocked_refs = set(thread.get("blocked_authority_refs") or [])
    missing_blocked_refs = set(AGENT_LOOP_THREAD_BLOCKED_AUTHORITY_REFS) - blocked_refs
    if missing_blocked_refs:
        failures.append(
            "Agent Loop missing blocked authority refs: "
            + ", ".join(sorted(missing_blocked_refs))
        )

    manifest = build_api_manifest(app)
    route_index = {(route.method, route.path): route for route in manifest.routes}
    route = route_index.get(("GET", "/control-center/agent-loop/thread"))
    if route is None:
        failures.append("GET /control-center/agent-loop/thread missing from manifest")
    else:
        if route.side_effect_class != "local_dev_workspace_only":
            failures.append("Agent Loop route side-effect class drifted")
        if route.route_classification != "local_sensitive":
            failures.append("Agent Loop route classification drifted")
    if (
        "control_center_agent_loop_thread_read_model"
        not in manifest.capabilities_declared
    ):
        failures.append("Agent Loop manifest capability missing")

    docs = [
        ROOT / "docs/control_center/UAA_RUNTIME_AGENT_LOOP_SPINE.md",
        ROOT / "docs/control_center/UAA_RUNTIME_CAPABILITY_SCOREBOARD.md",
    ]
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        compact_text = " ".join(text.split())
        if AGENT_LOOP_THREAD_CONTRACT_REF not in text:
            failures.append(f"Agent Loop contract ref missing from {doc}")
        if doc.name == "UAA_RUNTIME_AGENT_LOOP_SPINE.md":
            for fragment in [
                "exact AuthorityLease scope",
                "AuthorityLease-gated capabilities",
                "High-Maturity Agent Spine",
                "W1-W13",
            ]:
                if fragment not in compact_text:
                    failures.append(
                        f"AuthorityLease capability wording missing from {doc}: {fragment}"
                    )
            for stale in ["graduated lanes"]:
                if stale in compact_text:
                    failures.append(f"stale authority wording remains in {doc}: {stale}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("UAA runtime Agent Loop Spine verifier passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
