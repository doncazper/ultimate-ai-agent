#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.runtime_action_bridge import (  # noqa: E402
    build_runtime_action_inbox_bridge_read_model,
)
from ultimate_ai_agent.core.authority import (  # noqa: E402
    AuthorityActionRequest,
    AuthorityDomain,
    AuthorityCapability,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseRevokeRequest,
    AuthorityLeaseStore,
    AuthorityMissionPlanRequest,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (  # noqa: E402
    build_authority_lease_operator_approval_grant,
    validate_authority_lease_approval,
)
from ultimate_ai_agent.core.control_center.runtime_parity_loop import (  # noqa: E402
    build_runtime_parity_loop_read_model,
)
from ultimate_ai_agent.core.execution import (  # noqa: E402
    build_sample_staged_orchestration_read_model,
    build_sample_turn_run_approval_chain,
)
from ultimate_ai_agent.core.providers.control_plane import (  # noqa: E402
    build_model_provider_control_plane_read_model,
)
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RuntimeInvocationConflictError,
    RuntimeInvocationNotFoundError,
    RuntimeInvocationStore,
    RuntimeCommandExecutionRequest,
    RuntimeCommandIntent,
    RuntimeGateway,
    active_runtime_authority_leases,
    HermesChatRequest,
    HermesCliAdapter,
    build_portable_evidence_envelope,
    build_default_runtime_capabilities,
    build_hermes_context_pack_read_model,
    build_governed_product_pilot_authority_profile,
    build_runtime_interface_mode_read_model,
    build_runtime_approval_bridge_read_model,
    build_runtime_capability_discovery_read_model_from_authority_catalog,
    build_runtime_context_budget_pressure_read_model,
    build_runtime_delegation_adapter_read_model,
    build_runtime_doctor_diagnostics_read_model,
    build_runtime_background_jobs_read_model,
    build_runtime_hardline_command_blocklist_read_model,
    build_runtime_managed_scope_policy_read_model,
    build_runtime_mcp_catalog_filtering_read_model,
    build_runtime_subagent_isolation_read_model,
    build_runtime_worktree_per_agent_read_model,
    build_runtime_lsp_diagnostics_read_model,
    build_runtime_preview_rail_read_model,
    build_runtime_slash_command_registry_read_model,
    build_runtime_interrupt_redirect_read_model,
    build_runtime_logging_profile_read_model,
    build_runtime_result_classification_read_model,
    build_runtime_voice_media_posture_read_model,
    build_runtime_messaging_gateway_posture_read_model,
    build_runtime_remote_execution_posture_read_model,
    build_runtime_plugin_metadata_posture_read_model,
    build_runtime_skill_marketplace_posture_read_model,
    build_runtime_profile_isolation_read_model,
    build_runtime_prompt_stability_tiers_read_model,
    build_runtime_run_events_read_model,
    build_runtime_session_continuity_read_model,
    build_runtime_session_search_read_model,
    build_runtime_session_lineage_read_model,
    build_runtime_streaming_progress_read_model,
    build_runtime_tool_registry_availability_read_model_from_authority_catalog,
    build_runtime_usage_cost_analytics_read_model,
    build_runtime_virtual_provider_moa_read_model,
    build_runtime_action_signed_evidence,
    build_runtime_checkpoint_rollback_read_model,
    build_runtime_context_references_read_model,
    verify_portable_evidence_envelope,
    verify_runtime_action_signed_evidence,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import (  # noqa: E402
    RuntimeActionInboxApprovalDecision,
    RuntimeApprovalBindingRequest,
    RuntimeSafeDisableRequest,
)


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _bridge_payload(read_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:governed-runtime-action-inbox-bridge",
        "runtime_action_inbox_bridge_read_model": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }


def _runtime_payload(read_model: dict[str, Any], command_ref: str) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": command_ref,
        "runtime_read_model": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }


def _authority_payload(read_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-authority-state",
        "authority_state_read_model": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
        "execution_performed": False,
    }


def _parity_loop_payload(read_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-parity-loop",
        "runtime_parity_loop_read_model": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
        "execution_performed": False,
    }


def _read_model(store: RuntimeInvocationStore) -> dict[str, Any]:
    return build_runtime_action_inbox_bridge_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )


def _authority_scope_label(item: dict[str, Any]) -> str:
    if not item.get("authority_scope_required"):
        return "not required"
    if item.get("authority_scope_allowed"):
        return "allowed by active lease"
    return "requires active lease"


def _print_bridge_summary(read_model: dict[str, Any]) -> None:
    print("Governed runtime Action Inbox bridge")
    print(f"Status: {read_model['status']}")
    print(f"Contract: {read_model['contract_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Summary: {read_model['operator_summary']}")
    print(
        "Counts: "
        f"items={read_model['item_count']} "
        f"pending={read_model['pending_approval_count']} "
        f"approved={read_model['approved_pending_execution_count']} "
        f"receipts={read_model['receipt_recorded_count']} "
        f"blocked={read_model['blocked_count']}"
    )
    print(
        "Authority: exact focused pytest, repo-verifier, frontend-check, and repo-doctor "
        "bridges only; broad runtime remains blocked"
    )
    print("Blocked: " + ", ".join(read_model["blocked_authority_refs"] or ["none"]))
    print("Items:")
    if not read_model["items"]:
        print("- none")
        return
    for item in read_model["items"]:
        approval = "validated" if item["approval_validated"] else "not_validated"
        execution = "performed" if item["execution_performed"] else "not_performed"
        print(
            f"- {item['invocation_ref']} "
            f"intent={item.get('command_intent') or 'not_applicable'} "
            f"status={item['status']} approval={approval} execution={execution}"
        )
        print(f"  envelope: {item['action_envelope_ref']}")
        print(f"  scope: {item['exact_scope_ref']}")
        print(f"  authority scope: {_authority_scope_label(item)}")
        print(
            "  authority outcome: "
            f"{item.get('authority_decision_outcome') or 'missing'}"
        )
        print(f"  authority lease: {item.get('authority_lease_ref') or 'none'}")
        print(
            "  authority requirement: "
            f"{item.get('authority_required_mode_ref') or 'active-mode'} + "
            f"{item.get('authority_domain_ref') or 'authority-domain-ref:unknown'} "
            f"domain + "
            f"{item.get('authority_capability_ref') or 'authority-capability-ref:unknown'} "
            f"capability"
        )
        print(f"  authority audit: {item.get('authority_audit_ref') or 'none'}")
        print(
            f"  authority receipt: {item.get('authority_policy_receipt_ref') or 'none'}"
        )
        print(
            "  authority reason refs: "
            + ", ".join(item["authority_reason_refs"] or ["none"])
        )
        if item.get("authority_operator_message"):
            print(f"  authority message: {item['authority_operator_message']}")
        print(f"  receipt refs: {', '.join(item['receipt_refs'] or ['none'])}")
        print(f"  evidence refs: {', '.join(item['evidence_refs'] or ['none'])}")
        print(
            "  blocked reason refs: "
            + ", ".join(item["blocked_reason_refs"] or ["none"])
        )


def _print_parity_loop(read_model: dict[str, Any]) -> None:
    print("UAA GoatCitadel runtime parity loop")
    print(f"Status: {read_model['status']}")
    print(f"Parity: {read_model['parity_status']}")
    print(f"Contract: {read_model['contract_ref']}")
    print(f"API: {read_model['api_route_ref']}")
    print(f"Control Center: {read_model['control_center_route_ref']}")
    print(f"Summary: {read_model['operator_summary']}")
    print(
        "Counts: "
        f"invocations={read_model['runtime_invocation_count']} "
        f"receipts={read_model['runtime_receipt_count']} "
        f"signed_evidence={read_model['runtime_signed_evidence_count']} "
        f"timeline={read_model['runtime_timeline_event_count']}"
    )
    print(
        "Stages: "
        f"implemented={read_model['implemented_stage_count']} "
        f"partial={read_model['partial_stage_count']} "
        f"blocked={read_model['blocked_stage_count']}"
    )
    for stage in read_model["stages"]:
        print(f"- {stage['label']} status={stage['status']}")
        print(f"  stage: {stage['stage_ref']}")
        print(f"  cli: {stage['cli_ref']}")
        print(f"  api: {stage['api_route_ref']}")
        print(f"  summary: {stage['safe_summary']}")
    print("Still blocked: " + ", ".join(read_model["blocked_authority_refs"]))


def _print_status(read_model: dict[str, Any]) -> None:
    print("Governed runtime status")
    print(f"Status: {read_model['status']}")
    print(f"Profile: {read_model['runtime_profile_status']}")
    print(f"Local model: {read_model['local_model_readiness']}")
    print(f"Command runtime: {read_model['command_runtime_readiness']}")
    print(
        "Safe-disable: "
        + ("active" if read_model["safe_disable_active"] else "inactive")
    )
    print(f"Safe-disable ref: {read_model['safe_disable_ref']}")
    print(f"Summary: {read_model['operator_summary']}")
    print(
        "Counts: "
        f"items={read_model['item_count']} "
        f"pending={read_model['pending_approval_count']} "
        f"approved={read_model['approved_pending_execution_count']} "
        f"receipts={read_model['receipt_recorded_count']} "
        f"timeline={len(read_model['evidence_timeline'])}"
    )
    print("Blocked: " + ", ".join(read_model["blocked_authority_refs"] or ["none"]))


def _print_capabilities() -> None:
    capabilities = build_default_runtime_capabilities().model_dump(mode="json")
    print("Governed runtime capabilities")
    print(f"Capabilities ref: {capabilities['capabilities_ref']}")
    print(f"Default profile: {capabilities['default_profile']}")
    print(f"Adapter execution: {capabilities['adapter_execution_enabled']}")
    print(f"Model calls: {capabilities['model_call_enabled']}")
    print(f"Command execution: {capabilities['command_execution_enabled']}")
    print("Implemented authority refs:")
    for ref in capabilities["implemented_authority_refs"]:
        print(f"- {ref}")
    print("Blocked authority refs:")
    for ref in capabilities["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_authority_profile(read_model: dict[str, Any]) -> None:
    print("Governed Product Pilot authority profile")
    print(f"Status: {read_model['status']}")
    print(f"Profile: {read_model['profile_ref']}")
    print(f"Default profile: {read_model['default_runtime_profile']}")
    print(
        f"Sealed default preserved: {read_model['sealed_default_hard_rules_preserved']}"
    )
    print(f"RuntimeGateway required: {read_model['runtime_gateway_required']}")
    print(
        f"Control Center mints authority: {read_model['control_center_mints_authority']}"
    )
    print("Implemented lease-gated authority refs:")
    for ref in read_model["promoted_authority_refs"]:
        print(f"- {ref}")
    print("Lanes:")
    for lane in read_model["lanes"]:
        print(f"- {lane['title']} status={lane['status']}")
        print(f"  lane: {lane['lane_ref']}")
        print(f"  promotion: {lane['promotion_path_ref']}")
    envelope = read_model["portable_evidence_envelope"]
    print(f"Portable evidence: {envelope['signed_envelope_ref']}")
    print("Still blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_role_provider_evidence(read_model: dict[str, Any]) -> None:
    print("Role-based model/provider evidence")
    print(f"Status: {read_model['status']}")
    print(f"Contract: {read_model['contract_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"Roles: {read_model['role_count']}")
    print("Authority: advisory evidence only; no provider/model call was performed")
    for role in read_model["role_evidence"]:
        print(f"- {role['role_label']}: {role['selected_candidate_ref']}")
        print(f"  policy: {role['policy_decision_ref']}")
        print(f"  fallback: {role['fallback_ref']}")
        blocked = [
            candidate["candidate_ref"]
            for candidate in role["candidates"]
            if candidate["local_remote_posture"] == "remote_provider_reference"
        ]
        print("  remote blocked candidates: " + ", ".join(blocked or ["none"]))


def _print_delegation_adapter(read_model: dict[str, Any]) -> None:
    print("Runtime delegation adapter")
    print(f"Status: {read_model['status']}")
    print(f"Runtime: {read_model['runtime_label']}")
    print(f"Adapter: {read_model['adapter_ref']}")
    print(f"Authority mode: {read_model['authority_mode']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Control Center: {read_model['control_center_ref']}")
    endpoint = read_model["endpoint_posture"]
    print(f"Endpoint configured: {endpoint['endpoint_configured']}")
    print(f"Live transport: {endpoint['live_transport_enabled']}")
    print(f"UAA controls authority: {read_model['uaa_controls_authority']}")
    print(f"Live run submission: {read_model['live_run_submission_enabled']}")
    print("Capabilities:")
    for ref in read_model["capability_refs"]:
        print(f"- {ref}")
    print("Blocked:")
    for ref in read_model["blocked_reason_refs"]:
        print(f"- {ref}")
    print("Next safe actions:")
    for ref in read_model["next_safe_action_refs"]:
        print(f"- {ref}")


def _print_interface_mode(read_model: dict[str, Any]) -> None:
    print("Runtime interface mode")
    print(f"Status: {read_model['status']}")
    print(f"Active mode: {read_model['active_mode']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Hermes CLI: {read_model['hermes_cli_posture']['status']}")
    print(f"Context pack: {read_model['context_pack_ref']}")
    print(f"Memory updates: {read_model['memory_update_policy']}")
    print(f"UAA native agent enabled: {read_model['uaa_native_agent_enabled']}")
    print(f"UAA execution enabled: {read_model['uaa_execution_enabled']}")
    print(f"Summary: {read_model['safe_summary']}")
    print("Modes:")
    for profile in read_model["mode_profiles"]:
        print(
            f"- {profile['mode']} status={profile['status']} "
            f"hermes_chat={profile['hermes_cli_chat_enabled']} "
            f"external_only={profile['external_handoff_only']}"
        )
        print(f"  summary: {profile['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_hermes_context_pack(read_model: dict[str, Any]) -> None:
    print("Hermes context pack")
    print(f"Status: {read_model['status']}")
    print(f"Context pack: {read_model['context_pack_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Sections: {read_model['section_count']}")
    print(f"Memory updates: {read_model['memory_update_policy']}")
    print(f"Summary: {read_model['safe_summary']}")
    print(
        "Raw exposure: "
        f"memory={read_model['raw_memory_records_exposed']} "
        f"crm={read_model['raw_crm_records_exposed']} "
        f"chat={read_model['raw_chat_transcripts_exposed']} "
        f"paths={read_model['raw_local_paths_exposed']}"
    )
    for section in read_model["sections"]:
        print(f"- {section['source_surface']}: {section['section_ref']}")
        print(f"  summary: {section['safe_summary']}")


def _print_hermes_chat(receipt: dict[str, Any]) -> None:
    print("Hermes interface-mode chat")
    print(f"Status: {receipt['status']}")
    print(f"Mode: {receipt['mode']}")
    print(f"Receipt: {receipt['receipt_ref']}")
    print(f"Query ref: {receipt['query_ref']}")
    print(f"Context pack: {receipt['context_pack_ref']}")
    print(f"Execution performed: {receipt['execution_performed']}")
    print(f"External handoff only: {receipt['external_handoff_only']}")
    print(f"Output summary: {receipt.get('output_summary') or 'none'}")
    print(f"Memory updates: {receipt['memory_update_policy']}")
    if receipt.get("authority_decision_ref"):
        print(
            "Authority: "
            f"outcome={receipt.get('authority_decision_outcome') or 'unknown'} "
            f"lease={receipt.get('authority_lease_ref') or 'none'}"
        )
        print(
            "Requires: "
            f"{receipt.get('authority_required_mode_ref') or 'active-mode'} + "
            f"{receipt.get('authority_domain_ref') or 'domain'} + "
            f"{receipt.get('authority_capability_ref') or 'capability'}"
        )
        print(f"Authority decision: {receipt['authority_decision_ref']}")
    print("Blocked:")
    for ref in receipt["blocked_reason_refs"] or ["none"]:
        print(f"- {ref}")


def _print_capability_discovery(read_model: dict[str, Any]) -> None:
    print("Runtime capability discovery")
    print(f"Status: {read_model['status']}")
    print(f"Runtime: {read_model['runtime_label']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority state: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(f"Runtime reachable: {read_model['runtime_reachable']}")
    print(f"Live discovery performed: {read_model['live_discovery_performed']}")
    print(f"Freshness: {read_model['freshness_status']}")
    print(
        "Runtime supported capabilities: "
        f"{read_model['runtime_supported_capability_count']}"
    )
    print(
        "UAA authorized execution capabilities: "
        f"{read_model['uaa_authorized_capability_count']}"
    )
    toolset_posture = read_model["toolset_posture"]
    print("Toolset posture:")
    print(f"- status: {toolset_posture['status']}")
    print(f"- toolsets: {toolset_posture['toolset_count']}")
    print(f"- runtime supported: {toolset_posture['runtime_supported_count']}")
    print(f"- UAA execution allowed: {toolset_posture['uaa_allowed_execution_count']}")
    print(f"- invocation enabled: {toolset_posture['live_tool_invocation_enabled']}")
    for record in toolset_posture["records"]:
        print(
            f"- {record['display_label']}: "
            f"runtime={record['runtime_support_status']} "
            f"uaa={record['uaa_allowance_status']} "
            f"side_effect={record['side_effect_class']}"
        )
    print("Capability groups:")
    for group in read_model["capability_groups"]:
        print(f"- {group['group_kind']} runtime={group['runtime_support_status']}")
        print(f"  uaa={group['uaa_authorization_status']}")
        print(f"  summary: {group['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_tool_registry(read_model: dict[str, Any]) -> None:
    print("Runtime tool registry availability")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority state: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(f"Tools: {read_model['tool_count']}")
    print(f"UAA-native tools: {read_model['uaa_native_count']}")
    print(f"Delegated references: {read_model['delegated_reference_count']}")
    print(f"Preview available: {read_model['preview_available_count']}")
    print(f"Invocation enabled: {read_model['tool_invocation_enabled']}")
    print(f"Remote discovery enabled: {read_model['remote_discovery_enabled']}")
    print("Registry entries:")
    for entry in read_model["entries"]:
        print(
            f"- {entry['display_label']}: "
            f"origin={entry['origin']} "
            f"availability={entry['availability_status']} "
            f"authority={entry['authority_class']} "
            f"risk={entry['risk_class']}"
        )
        print(f"  side_effect={entry['side_effect_class']}")
        print(f"  summary: {entry['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_virtual_provider_moa(read_model: dict[str, Any]) -> None:
    print("Runtime virtual provider multi-agent posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Presets: {read_model['preset_count']}")
    print(f"Agent slots: {read_model['agent_slot_count']}")
    print(f"Live fan-out: {read_model['live_model_fanout_enabled']}")
    print(f"Provider SDK: {read_model['provider_sdk_enabled']}")
    print("Presets:")
    for preset in read_model["presets"]:
        print(
            f"- {preset['display_label']}: "
            f"status={preset['status']} slots={preset['slot_count']}"
        )
        print(f"  approval={preset['approval_mode_ref']}")
        print(f"  trace={preset['route_decision_trace_ref']}")
        print(f"  summary: {preset['safe_summary']}")
        for slot in preset["slots"]:
            print(
                f"  - {slot['display_label']}: role={slot['role']} "
                f"runtime={slot['runtime_ref']}"
            )
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_usage_cost_analytics(read_model: dict[str, Any]) -> None:
    print("Runtime usage and cost analytics posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Records: {read_model['record_count']}")
    print(f"Estimated input units: {read_model['total_estimated_input_tokens']}")
    print(f"Estimated output units: {read_model['total_estimated_output_tokens']}")
    print(f"Estimated total units: {read_model['total_estimated_tokens']}")
    print(
        f"Estimated minor cost units: {read_model['total_estimated_cost_minor_units']}"
    )
    print(f"Provider calls: {read_model['provider_call_enabled']}")
    print(f"Provider SDK: {read_model['provider_sdk_enabled']}")
    print(f"Billing actions: {read_model['billing_action_enabled']}")
    print(f"Operator export: {read_model['operator_export_available']}")
    print("Records:")
    for record in read_model["records"]:
        print(
            f"- {record['display_label']}: "
            f"source={record['source_kind']} status={record['status']} "
            f"runtime={record['runtime_ref']}"
        )
        print(
            "  "
            f"units={record['estimated_total_tokens']} "
            f"cost_minor={record['estimated_cost_minor_units']} "
            f"latency_ms={record['latency_ms']}"
        )
        print(f"  summary: {record['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_prompt_stability_tiers(read_model: dict[str, Any]) -> None:
    print("Runtime prompt stability tier posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Tiers: {read_model['tier_count']}")
    print(f"Safe manifest required: {read_model['safe_prompt_manifest_required']}")
    print(f"Hashes required: {read_model['prompt_hashes_required']}")
    print(f"Raw prompt persistence: {read_model['raw_prompt_persistence_enabled']}")
    print(f"Hidden injection: {read_model['hidden_prompt_injection_enabled']}")
    print(f"Model output authority: {read_model['model_output_authority_enabled']}")
    print("Tiers:")
    for tier in read_model["tiers"]:
        print(
            f"- {tier['display_label']}: "
            f"kind={tier['tier_kind']} stability={tier['stability_class']}"
        )
        print(f"  manifest={tier['manifest_ref']}")
        print(f"  hash={tier['tier_hash_ref']}")
        print(f"  cache_candidate={tier['cache_candidate']}")
        print(f"  summary: {tier['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_context_budget_pressure(read_model: dict[str, Any]) -> None:
    print("Runtime context budget pressure posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Pressure: {read_model['pressure_level']}")
    print(
        "Budget: "
        f"{read_model['estimated_token_count']}/"
        f"{read_model['token_budget_limit']} "
        f"remaining={read_model['token_budget_remaining']}"
    )
    print(f"Segments: {read_model['segment_count']}")
    print(f"Proposals: {read_model['proposal_count']}")
    print(f"Hidden compression: {read_model['hidden_compression_enabled']}")
    print(f"Automatic mutation: {read_model['automatic_context_mutation_enabled']}")
    print(f"Model summarization: {read_model['model_summarization_enabled']}")
    print("Segments:")
    for segment in read_model["segments"]:
        print(
            f"- {segment['display_label']}: "
            f"pressure={segment['pressure_level']} "
            f"tokens={segment['token_estimate']}/"
            f"{segment['token_budget_limit']}"
        )
        print(f"  summary: {segment['safe_summary']}")
    print("Proposals:")
    for proposal in read_model["proposals"]:
        print(
            f"- {proposal['display_label']}: "
            f"kind={proposal['proposal_kind']} "
            f"delta={proposal['expected_token_delta']}"
        )
        print(f"  summary: {proposal['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_hardline_command_blocklist(read_model: dict[str, Any]) -> None:
    print("Runtime hardline command blocklist floor")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Non-overridable floor: {read_model['non_overridable_floor']}")
    print(f"Override bypass permitted: {read_model['override_bypass_permitted']}")
    print(f"Classifications: {read_model['classification_count']}")
    print(f"Denied classifications: {read_model['denied_classification_count']}")
    print(f"Allowed classifications: {read_model['allowed_classification_count']}")
    print("Classifications:")
    for classification in read_model["classifications"]:
        print(
            f"- {classification['candidate_ref']}: "
            f"status={classification['status']} "
            f"category={classification['denial_category']}"
        )
        print(f"  reason={classification['denial_reason_ref']}")
        print(f"  summary: {classification['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_managed_scope_policy(read_model: dict[str, Any]) -> None:
    print("Runtime managed scope policy")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Policy profile: {read_model['policy_profile_ref']}")
    print(f"Profile label: {read_model['profile_label']}")
    print(f"Pinned sources: {read_model['pinned_source_count']}")
    print(f"Active pins: {read_model['active_pinned_source_count']}")
    print(f"Drift warnings: {read_model['drift_warning_count']}")
    print(
        "Writes/delivery/enforcement: "
        f"system_config={read_model['system_config_write_enabled']} "
        f"privileged={read_model['privileged_write_enabled']} "
        f"mdm={read_model['mdm_delivery_enabled']} "
        f"production={read_model['production_enforcement_claimed']}"
    )
    print("Pinned sources:")
    for source in read_model["pinned_sources"]:
        print(
            f"- {source['display_label']}: "
            f"kind={source['source_kind']} "
            f"precedence={source['precedence']} "
            f"drift={source['drift_status']}"
        )
        print(f"  source={source['source_ref']}")
    print("Drift warnings:")
    for warning in read_model["drift_warnings"]:
        print(f"- {warning['warning_ref']} status={warning['status']}")
        print(f"  summary: {warning['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_doctor_diagnostics(read_model: dict[str, Any]) -> None:
    print("Runtime doctor diagnostics")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Diagnostics: {read_model['diagnostic_count']}")
    print(
        "Counts: "
        f"ok={read_model['ok_count']} "
        f"review={read_model['review_count']} "
        f"blocked={read_model['blocked_count']} "
        f"unavailable={read_model['unavailable_count']}"
    )
    print(
        "Mutations: "
        f"installs={read_model['install_enabled']} "
        f"service_starts={read_model['service_start_enabled']} "
        f"credential_writes={read_model['credential_write_enabled']} "
        f"runtime_config={read_model['runtime_config_mutation_enabled']}"
    )
    print("Diagnostic items:")
    for item in read_model["diagnostics"]:
        print(
            f"- {item['display_label']}: "
            f"domain={item['domain']} status={item['status']}"
        )
        print(f"  summary: {item['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_session_continuity(read_model: dict[str, Any]) -> None:
    print("Runtime session continuity")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Primary session: {read_model['primary_session_ref']}")
    print(
        "Surfaces: "
        f"total={read_model['surface_count']} "
        f"current={read_model['current_count']} "
        f"stale={read_model['stale_count']} "
        f"conflict={read_model['conflict_count']} "
        f"blocked={read_model['blocked_count']}"
    )
    print(
        "Blocked transports: "
        f"external_message_gateway={read_model['external_message_gateway_enabled']} "
        f"account_sync={read_model['account_sync_enabled']} "
        f"connector_write={read_model['connector_write_enabled']} "
        f"remote_session={read_model['remote_session_enabled']}"
    )
    print("Surfaces:")
    for surface in read_model["surfaces"]:
        print(
            f"- {surface['source_label']}: "
            f"source={surface['source']} state={surface['continuity_state']}"
        )
        print(f"  session={surface['session_ref']}")
        print(f"  route={surface['route_ref']}")
        print(f"  summary: {surface['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_mcp_catalog_filtering(read_model: dict[str, Any]) -> None:
    print("Runtime MCP catalog filtering")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(
        "Servers: "
        f"total={read_model['server_count']} "
        f"reviewed={read_model['reviewed_metadata_count']} "
        f"review_required={read_model['review_required_count']} "
        f"activation_blocked={read_model['activation_blocked_count']}"
    )
    print(
        "Tools: "
        f"total={read_model['tool_slice_count']} "
        f"metadata={read_model['metadata_visible_tool_count']} "
        f"filtered={read_model['filtered_blocked_tool_count']} "
        f"grant_required={read_model['grant_required_tool_count']}"
    )
    print(
        "Blocked activation: "
        f"install={read_model['install_enabled']} "
        f"subprocess={read_model['subprocess_runtime_enabled']} "
        f"oauth={read_model['oauth_login_enabled']} "
        f"tool_invocation={read_model['tool_invocation_enabled']} "
        f"connector_write={read_model['connector_write_enabled']}"
    )
    print("Servers:")
    for server in read_model["servers"]:
        print(
            f"- {server['display_label']}: "
            f"state={server['catalog_state']} tools={server['tool_count']}"
        )
        print(f"  filter={server['filter_contract_ref']}")
        print(f"  summary: {server['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_background_jobs(read_model: dict[str, Any]) -> None:
    print("Runtime background jobs")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(
        "Jobs: "
        f"total={read_model['job_count']} "
        f"proposal={read_model['proposal_count']} "
        f"paused={read_model['paused_count']} "
        f"approval_required={read_model['approval_required_count']} "
        f"execution_blocked={read_model['execution_blocked_count']}"
    )
    print(
        "Blocked controls: "
        f"pause={read_model['pause_enabled']} "
        f"resume={read_model['resume_enabled']} "
        f"run_now={read_model['run_now_enabled']} "
        f"scheduler={read_model['scheduler_enabled']} "
        f"worker={read_model['background_worker_enabled']}"
    )
    print("Job proposals:")
    for job in read_model["jobs"]:
        print(
            f"- {job['display_label']}: "
            f"status={job['status']} schedule={job['schedule_policy']}"
        )
        print(f"  job={job['job_ref']}")
        print(f"  approval={job['approval_scope_ref']}")
        print(f"  receipt={job['receipt_plan_ref']}")
        print(f"  summary: {job['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_subagent_isolation(read_model: dict[str, Any]) -> None:
    print("Runtime subagent isolation")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(
        "Roles: "
        f"total={read_model['role_count']} "
        f"contract_ready={read_model['contract_ready_count']} "
        f"review_ready={read_model['review_ready_count']} "
        f"blocked_dispatch={read_model['blocked_dispatch_count']}"
    )
    print(f"Review artifacts: {read_model['review_artifact_count']}")
    print(
        "Blocked controls: "
        f"dispatch={read_model['live_dispatch_enabled']} "
        f"fanout={read_model['background_fanout_enabled']} "
        f"tool_sharing={read_model['tool_sharing_enabled']} "
        f"memory_transfer={read_model['cross_agent_memory_transfer_enabled']}"
    )
    print("Roles:")
    for role in read_model["roles"]:
        print(
            f"- {role['display_label']}: "
            f"status={role['readiness_status']} scope={role['scope_envelope_ref']}"
        )
        print(f"  context={role['context_pack_ref']}")
        print(f"  tools={role['tool_grant_ref']}")
        print(f"  memory={role['memory_grant_ref']}")
        print(f"  receipt={role['receipt_plan_ref']}")
    print("Artifacts:")
    for artifact in read_model["review_artifacts"]:
        print(f"- {artifact['display_label']}: kind={artifact['artifact_kind']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_worktree_per_agent(read_model: dict[str, Any]) -> None:
    print("Runtime worktree per agent")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority: {read_model['authority_state_route_ref']}")
    print(
        "Lanes: "
        f"total={read_model['lane_count']} "
        f"proposal={read_model['proposal_count']} "
        f"review_ready={read_model['review_ready_count']} "
        f"mutation_blocked={read_model['mutation_blocked_count']}"
    )
    print(
        "Authority decisions: "
        f"total={read_model['authority_state_decision_count']} "
        f"allow={read_model['authority_state_allowed_count']} "
        f"degrade={read_model['authority_state_degraded_count']} "
        f"deny={read_model['authority_state_denied_count']}"
    )
    print(
        "Blocked controls: "
        f"create={read_model['git_worktree_create_enabled']} "
        f"delete={read_model['git_worktree_delete_enabled']} "
        f"branch={read_model['branch_mutation_enabled']} "
        f"write={read_model['file_write_enabled']} "
        f"commit={read_model['commit_enabled']} "
        f"push={read_model['push_enabled']}"
    )
    print("Lanes:")
    for lane in read_model["lanes"]:
        print(
            f"- {lane['display_label']}: "
            f"status={lane['lane_status']} isolation={lane['isolation_mode']} "
            f"authority={lane['authority_state_decision_outcome']}"
        )
        print(f"  authority_decision={lane['authority_state_decision_ref']}")
        print(f"  branch={lane['branch_proposal_ref']}")
        print(f"  worktree={lane['worktree_ref']}")
        print(f"  checkpoint={lane['checkpoint_plan_ref']}")
        print(f"  rollback={lane['rollback_plan_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_lsp_diagnostics(read_model: dict[str, Any]) -> None:
    print("Runtime LSP diagnostics")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(
        "Diagnostics: "
        f"total={read_model['diagnostic_count']} "
        f"placeholder={read_model['evidence_placeholder_count']} "
        f"proof_ready={read_model['proof_ready_count']} "
        f"execution_blocked={read_model['execution_blocked_count']}"
    )
    print(
        "Blocked controls: "
        f"server={read_model['language_server_started']} "
        f"install={read_model['dependency_install_enabled']} "
        f"shell={read_model['shell_execution_enabled']} "
        f"file_read={read_model['file_read_enabled']}"
    )
    print("Diagnostic contracts:")
    for item in read_model["diagnostics"]:
        print(
            f"- {item['display_label']}: "
            f"language={item['language']} status={item['status']}"
        )
        print(f"  evidence={item['evidence_ref']}")
        print(f"  receipt={item['receipt_plan_ref']}")
        print(f"  proof={item['proof_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_preview_rail(read_model: dict[str, Any]) -> None:
    print("Runtime preview rail")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(
        "Slots: "
        f"total={read_model['slot_count']} "
        f"safe_ref_ready={read_model['safe_ref_ready_count']} "
        f"placeholder={read_model['bounded_preview_placeholder_count']} "
        f"execution_blocked={read_model['execution_blocked_count']}"
    )
    print(
        "Blocked controls: "
        f"browser={read_model['browser_automation_enabled']} "
        f"raw_file={read_model['raw_sensitive_file_display_enabled']} "
        f"runtime_payload={read_model['direct_runtime_payload_rendering_enabled']} "
        f"screenshot={read_model['screenshot_capture_enabled']}"
    )
    print("Preview slots:")
    for slot in read_model["slots"]:
        print(
            f"- {slot['display_label']}: "
            f"kind={slot['slot_kind']} status={slot['slot_status']}"
        )
        print(f"  source={slot['source_ref']}")
        print(f"  preview={slot['bounded_preview_ref']}")
        print(f"  receipt={slot['receipt_plan_ref']}")
        print(f"  proof={slot['proof_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_slash_command_registry(read_model: dict[str, Any]) -> None:
    print("Runtime slash command registry")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(
        "Commands: "
        f"total={read_model['command_count']} "
        f"metadata_ready={read_model['metadata_ready_count']} "
        f"disabled={read_model['disabled_count']} "
        f"blocked={read_model['blocked_count']}"
    )
    print(
        "Execution flags: "
        f"chat={read_model['chat_trigger_enabled']} "
        f"runtime={read_model['runtime_invocation_enabled']} "
        f"mutation={read_model['state_mutation_enabled']} "
        f"shell={read_model['shell_execution_enabled']}"
    )
    print("Registered commands:")
    for command in read_model["commands"]:
        print(
            f"- {command['trigger_label']} {command['display_label']}: "
            f"status={command['command_status']} "
            f"authority={command['authority_class']} "
            f"side_effect={command['side_effect_class']}"
        )
        print(f"  approval={command['approval_policy_ref']}")
        print(f"  receipt={command['receipt_plan_ref']}")
        print(f"  proof={command['proof_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_interrupt_redirect(read_model: dict[str, Any]) -> None:
    print("Runtime interrupt / redirect posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(
        "Actions: "
        f"total={read_model['proposal_count']} "
        f"proposal={read_model['read_only_proposal_count']} "
        f"approval_future={read_model['approval_required_future_lane_count']} "
        f"blocked={read_model['blocked_count']}"
    )
    print(
        "Live controls: "
        f"stop_post={read_model['live_stop_post_enabled']} "
        f"process_kill={read_model['process_kill_enabled']} "
        f"runtime_mutation={read_model['runtime_mutation_enabled']} "
        f"background={read_model['background_autonomy_enabled']}"
    )
    print("Run-control proposals:")
    for proposal in read_model["proposals"]:
        print(
            f"- {proposal['display_label']}: "
            f"kind={proposal['action_kind']} status={proposal['action_status']} "
            f"side_effect={proposal['side_effect_class']}"
        )
        print(f"  approval={proposal['approval_scope_ref']}")
        print(f"  idempotency={proposal['idempotency_ref']}")
        print(f"  receipt={proposal['receipt_plan_ref']}")
        print(f"  recovery={proposal['recovery_state_ref']}")
        print(f"  proof={proposal['proof_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_logging_profile(read_model: dict[str, Any]) -> None:
    print("Runtime logging profile posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(f"Active profile: {read_model['active_profile_ref']}")
    print(
        "Profiles: "
        f"total={read_model['profile_count']} "
        f"quiet={read_model['quiet_default_count']} "
        f"flagged={read_model['disabled_until_flagged_count']} "
        f"blocked_raw={read_model['blocked_raw_detail_count']}"
    )
    print(
        "Persistence/export: "
        f"verbose={read_model['verbose_logging_enabled']} "
        f"raw_logs={read_model['raw_logs_persisted']} "
        f"telemetry={read_model['remote_telemetry_export_enabled']} "
        f"background_stream={read_model['background_log_stream_enabled']}"
    )
    print("Logging profiles:")
    for profile in read_model["profiles"]:
        print(
            f"- {profile['display_label']}: "
            f"kind={profile['profile_kind']} status={profile['profile_status']} "
            f"retention={profile['retention_class']}"
        )
        print(f"  flag={profile['flag_scope_ref']}")
        print(f"  ttl={profile['ttl_policy_ref']}")
        print(f"  redaction={profile['redaction_verifier_ref']}")
        print(f"  proof={profile['proof_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_result_classification(read_model: dict[str, Any]) -> None:
    print("Runtime result classification posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(
        "Classes: "
        f"total={read_model['classification_count']} "
        f"evidence={read_model['evidence_count']} "
        f"mutation={read_model['mutation_count']} "
        f"blocked={read_model['blocked_count']} "
        f"untrusted={read_model['untrusted_data_count']}"
    )
    print(
        "Authority flags: "
        f"truth={read_model['tool_output_as_truth_enabled']} "
        f"action={read_model['action_authority_enabled']} "
        f"raw_output={read_model['raw_output_persisted']}"
    )
    print("Result classes:")
    for item in read_model["classifications"]:
        print(
            f"- {item['display_label']}: "
            f"kind={item['result_kind']} status={item['verification_status']}"
        )
        print(f"  provenance={item['provenance_policy_ref']}")
        print(f"  receipt={item['receipt_requirement_ref']}")
        print(f"  proof={item['proof_binding_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_voice_media_posture(read_model: dict[str, Any]) -> None:
    print("Runtime voice/media posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"Doc: {read_model['doc_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority state: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(
        "Lanes: "
        f"total={read_model['lane_count']} "
        f"blocked={read_model['blocked_lane_count']}"
    )
    print(
        "Authority flags: "
        f"microphone={read_model['microphone_access_enabled']} "
        f"camera={read_model['camera_access_enabled']} "
        f"upload={read_model['file_upload_enabled']} "
        f"transcription={read_model['transcription_enabled']} "
        f"generation={read_model['media_generation_enabled']} "
        f"provider={read_model['provider_calls_enabled']} "
        f"delivery={read_model['external_delivery_enabled']}"
    )
    print("Voice/media lanes:")
    for lane in read_model["lanes"]:
        print(
            f"- {lane['display_label']}: "
            f"kind={lane['lane_kind']} status={lane['status']}"
        )
        print(f"  consent={lane['consent_ref']}")
        print(f"  redaction={lane['redaction_policy_ref']}")
        print(f"  receipt={lane['receipt_plan_ref']}")
        print(f"  safe-disable={lane['safe_disable_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_messaging_gateway_posture(read_model: dict[str, Any]) -> None:
    print("Runtime messaging gateway posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"Doc: {read_model['doc_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority state: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(
        "Platforms: "
        f"total={read_model['platform_count']} "
        f"blocked={read_model['blocked_platform_count']}"
    )
    print(
        "Authority flags: "
        f"connector_runtime={read_model['connector_runtime_enabled']} "
        f"connector_read={read_model['connector_read_enabled']} "
        f"sends={read_model['send_enabled']} "
        f"oauth={read_model['oauth_enabled']} "
        f"webhooks={read_model['webhook_exposure_enabled']} "
        f"sync={read_model['account_sync_enabled']} "
        f"writes={read_model['external_write_enabled']}"
    )
    print("Messaging platforms:")
    for platform in read_model["platforms"]:
        print(
            f"- {platform['display_label']}: "
            f"kind={platform['platform_kind']} status={platform['status']}"
        )
        print(f"  connector={platform['connector_label_ref']}")
        print(f"  inbound={platform['inbound_readiness_ref']}")
        print(f"  outbound={platform['outbound_write_label_ref']}")
        print(f"  redaction={platform['redaction_policy_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_remote_execution_posture(read_model: dict[str, Any]) -> None:
    print("Runtime remote execution backend posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"Doc: {read_model['doc_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority state: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(
        "Backends: "
        f"total={read_model['backend_count']} "
        f"blocked={read_model['blocked_backend_count']}"
    )
    print(
        "Authority flags: "
        f"remote={read_model['remote_execution_enabled']} "
        f"ssh={read_model['ssh_enabled']} "
        f"cloud={read_model['cloud_sandbox_enabled']} "
        f"shell={read_model['remote_shell_enabled']} "
        f"sync={read_model['file_sync_enabled']} "
        f"secrets={read_model['remote_secret_access_enabled']} "
        f"process={read_model['remote_process_control_enabled']}"
    )
    print("Execution backends:")
    for backend in read_model["backends"]:
        print(
            f"- {backend['display_label']}: "
            f"kind={backend['backend_kind']} status={backend['status']}"
        )
        print(f"  workspace={backend['workspace_boundary_ref']}")
        print(f"  credentials={backend['credential_policy_ref']}")
        print(f"  network={backend['network_policy_ref']}")
        print(f"  receipt={backend['receipt_plan_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_plugin_metadata_posture(read_model: dict[str, Any]) -> None:
    print("Runtime plugin metadata posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"Doc: {read_model['doc_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority state: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(
        "Surfaces: "
        f"total={read_model['surface_count']} "
        f"blocked={read_model['blocked_surface_count']}"
    )
    print(
        "Authority flags: "
        f"runtime_import={read_model['runtime_import_enabled']} "
        f"hooks={read_model['hook_execution_enabled']} "
        f"install={read_model['package_install_enabled']} "
        f"marketplace={read_model['marketplace_content_execution_enabled']} "
        f"code={read_model['plugin_code_execution_enabled']} "
        f"connector_write={read_model['connector_write_enabled']} "
        f"provider={read_model['provider_call_enabled']} "
        f"shell={read_model['shell_execution_enabled']}"
    )
    print("Plugin surfaces:")
    for surface in read_model["surfaces"]:
        print(
            f"- {surface['display_label']}: "
            f"kind={surface['surface_kind']} status={surface['status']}"
        )
        print(f"  manifest={surface['reviewed_manifest_ref']}")
        print(f"  scan={surface['static_scan_ref']}")
        print(f"  grant={surface['activation_grant_ref']}")
        print(f"  receipt={surface['receipt_plan_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_skill_marketplace_posture(read_model: dict[str, Any]) -> None:
    print("Runtime skill marketplace posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"Doc: {read_model['doc_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Authority state: {read_model['authority_state_route_ref']}")
    print(f"Authority mapping: {read_model['authority_state_mapping_ref']}")
    print(
        "Authority decision: "
        f"{read_model['authority_state_decision_outcome']} "
        f"({read_model['authority_state_decision_ref']})"
    )
    print(
        "Stages: "
        f"total={read_model['stage_count']} "
        f"review_required={read_model['review_required_count']} "
        f"execution_blocks={read_model['blocked_execution_count']}"
    )
    print(
        "Authority flags: "
        f"popularity_is_trust={read_model['external_popularity_is_trust']} "
        f"external_code={read_model['external_code_execution_enabled']} "
        f"direct_install={read_model['direct_marketplace_install_enabled']} "
        f"runtime_import={read_model['runtime_import_enabled']} "
        f"skill_write={read_model['automatic_skill_write_enabled']} "
        f"provider={read_model['provider_call_enabled']} "
        f"browser={read_model['browser_automation_enabled']} "
        f"connector_write={read_model['connector_write_enabled']}"
    )
    print("Skill marketplace stages:")
    for stage in read_model["stages"]:
        print(
            f"- {stage['display_label']}: "
            f"kind={stage['stage_kind']} status={stage['status']}"
        )
        print(f"  signal={stage['signal_policy_ref']}")
        print(f"  quarantine={stage['quarantine_ref']}")
        print(f"  adaptation={stage['adaptation_ref']}")
        print(f"  grant={stage['activation_grant_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_session_search(read_model: dict[str, Any]) -> None:
    print("Runtime session/run search")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Query ref: {read_model['query_ref']}")
    print(f"Sensitive context guard: {read_model['sensitive_context_guard_ref']}")
    print(
        "Sensitive context bypass enabled: "
        f"{read_model['sensitive_context_bypass_enabled']}"
    )
    print(f"Results: {read_model['result_count']}")
    print(f"Session refs: {read_model['session_ref_count']}")
    print(f"Run refs: {read_model['run_ref_count']}")
    print("Results:")
    for result in read_model["results"]:
        print(
            f"- {result['title']}: kind={result['result_kind']} "
            f"session={result['session_ref']}"
        )
        print(f"  run={result.get('run_ref') or 'none'}")
        print(f"  context={result['attachable_context_ref']}")
        print(f"  summary: {result['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_session_lineage(read_model: dict[str, Any]) -> None:
    print("Runtime session lineage and forks")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Nodes: {read_model['node_count']}")
    print(f"Forks: {read_model['fork_count']}")
    print(f"Max depth: {read_model['max_lineage_depth']}")
    print(f"Raw transcript clone enabled: {read_model['raw_transcript_clone_enabled']}")
    print(f"Runtime dispatch enabled: {read_model['runtime_dispatch_enabled']}")
    print("Lineage nodes:")
    for node in read_model["nodes"]:
        print(
            f"- {node['node_ref']}: kind={node['node_kind']} "
            f"session={node['session_ref']}"
        )
        print(f"  parent={node.get('parent_node_ref') or 'none'}")
        print(f"  children={len(node['child_node_refs'])}")
        print(f"  summary: {node['safe_summary']}")
    print("Forks:")
    for fork in read_model["forks"]:
        print(
            f"- {fork['fork_ref']}: status={fork['status']} branch={fork['branch_ref']}"
        )
        print(f"  parent={fork['parent_session_ref']}")
        print(f"  child={fork['child_session_ref']}")
        print(f"  envelope={fork['redacted_fork_envelope_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_context_references(read_model: dict[str, Any]) -> None:
    print("Runtime context references")
    print(f"Status: {read_model['status']}")
    print(f"Preview: {read_model['preview_ref']}")
    print(f"Preview hash: {read_model['preview_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"References: {read_model['reference_count']}")
    print(f"Included: {read_model['included_count']}")
    print(f"Candidates: {read_model['candidate_count']}")
    print(f"Blocked: {read_model['blocked_count']}")
    print(f"Sensitive context guard: {read_model['sensitive_context_guard_ref']}")
    print(
        "Sensitive context bypass enabled: "
        f"{read_model['sensitive_context_bypass_enabled']}"
    )
    print(
        "Token budget: "
        f"{read_model['estimated_token_count']}/"
        f"{read_model['token_budget_limit']}"
    )
    print("References:")
    for ref in read_model["references"]:
        print(
            f"- {ref['display_label']}: kind={ref['ref_kind']} "
            f"status={ref['status']} ref={ref['context_ref']}"
        )
        print(f"  tokens={ref['token_estimate']}")
        print(f"  summary: {ref['safe_summary']}")
        print(f"  why={', '.join(ref['why_included_refs'])}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_checkpoint_rollback(read_model: dict[str, Any]) -> None:
    print("Runtime checkpoint rollback posture")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Lanes: {read_model['lane_count']}")
    print(f"Checkpoint available: {read_model['checkpoint_available_count']}")
    print(f"Exact core rollback receipts: {read_model['exact_core_supported_count']}")
    print(f"Rollback route enabled: {read_model['rollback_execution_route_enabled']}")
    for lane in read_model["lanes"]:
        print(f"- {lane['lane_ref']}: kind={lane['lane_kind']} status={lane['status']}")
        print(f"  checkpoint={lane['checkpoint_ref']}")
        print(f"  rollback_plan={lane['rollback_plan_ref']}")
        print(f"  summary: {lane['safe_summary']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_run_events(read_model: dict[str, Any]) -> None:
    print("Runtime run events")
    print(f"Status: {read_model['status']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Proposals: {read_model['proposal_count']}")
    print(f"Approval waits: {read_model['approval_wait_count']}")
    print(f"Completed runs: {read_model['completed_run_count']}")
    print(f"Create route enabled: {read_model['create_run_route_enabled']}")
    print(f"Stop route enabled: {read_model['stop_run_route_enabled']}")
    print(
        "Approval resolution route enabled: "
        f"{read_model['approval_resolution_route_enabled']}"
    )
    print("Lifecycle mappings:")
    for mapping in read_model["lifecycle_mappings"]:
        print(
            f"- {mapping['runtime_state']} -> "
            f"{mapping['uaa_durable_run_state']}: {mapping['operator_label']}"
        )
    print("Run proposals:")
    for proposal in read_model["run_proposals"]:
        print(f"- {proposal['runtime_run_ref']} state={proposal['runtime_state']}")
        print(f"  durable={proposal['uaa_durable_run_ref']}")
        print(f"  stop={proposal['stop_posture']}")
        print(f"  approval={proposal['approval_resolution_posture']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_approval_bridge(read_model: dict[str, Any]) -> None:
    print("Runtime approval bridge")
    print(f"Status: {read_model['status']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Pending runtime approvals: {read_model['pending_runtime_approval_count']}")
    print(f"Denied previews: {read_model['denied_preview_count']}")
    print(f"Timeout previews: {read_model['timeout_preview_count']}")
    print(f"Runtime resolutions sent: {read_model['runtime_resolution_sent_count']}")
    posture = read_model["fail_closed_timeout_posture"]
    print(f"Fail-closed policy: {posture['policy_ref']}")
    print(
        "Timeout/ambiguous waits: "
        f"expired_deny={posture['expired_waits_default_to_deny']} "
        f"ambiguous_deny={posture['ambiguous_waits_default_to_deny']}"
    )
    print(
        "Broad approval controls: "
        f"auto_approve={posture['auto_approve_enabled']} "
        f"approve_all={posture['approve_all_enabled']} "
        f"standing={posture['standing_broad_authority_enabled']}"
    )
    projection = read_model["action_inbox_projection"]
    print(f"Action Inbox item: {projection['action_inbox_item_ref']}")
    print(f"Action Inbox status: {projection['status']}")
    print("Envelopes:")
    for envelope in read_model["envelopes"]:
        print(f"- {envelope['runtime_approval_ref']} state={envelope['state']}")
        print(f"  run={envelope['runtime_run_ref']}")
        print(f"  scope={envelope['requested_scope_ref']}")
        print(f"  resolution={envelope['resolution_posture']}")
    scope = read_model["scope_validation"]
    print(f"Scope validation: {scope['status']} matches={scope['scope_matches']}")
    print("Decision previews:")
    for preview in read_model["decision_previews"]:
        print(f"- {preview['decision_kind']} sent={preview['runtime_resolution_sent']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_streaming_progress(read_model: dict[str, Any]) -> None:
    print("Runtime streaming progress")
    print(f"Status: {read_model['status']}")
    print(f"Stream state: {read_model['stream_state']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Events: {read_model['event_count']}")
    print(f"Live subscription: {read_model['live_subscription_enabled']}")
    print(f"SSE transport: {read_model['sse_transport_enabled']}")
    print(f"WebSocket transport: {read_model['websocket_transport_enabled']}")
    print(f"Stale stream: {read_model['stale_stream']}")
    print("Event previews:")
    for event in read_model["event_previews"]:
        print(f"- #{event['sequence']} {event['event_kind']} {event['event_ref']}")
        print(f"  proof={event['proof_ref']}")
        print(f"  hash={event['event_hash_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_profiles(read_model: dict[str, Any]) -> None:
    print("Runtime profile isolation")
    print(f"Status: {read_model['status']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Profiles: {read_model['profile_count']}")
    print(f"Configured: {read_model['configured_profile_count']}")
    print(f"Blocked: {read_model['blocked_profile_count']}")
    print(
        "Create/delete/config/default changes: "
        f"{read_model['profile_creation_enabled']}/"
        f"{read_model['profile_deletion_enabled']}/"
        f"{read_model['runtime_config_write_enabled']}/"
        f"{read_model['runtime_default_change_enabled']}"
    )
    print("Profiles:")
    for profile in read_model["profiles"]:
        print(
            f"- {profile['display_label']} role={profile['role']} "
            f"health={profile['profile_health']}"
        )
        print(f"  uaa={profile['profile_ref']}")
        print(f"  delegated={profile['delegated_runtime_profile_ref']}")
        print(f"  workspace={profile['workspace_scope_ref']}")
        print(f"  memory={profile['memory_scope_ref']}")
    print("Blocked:")
    for ref in read_model["blocked_authority_refs"]:
        print(f"- {ref}")


def _print_invocation(record: Any) -> None:
    print("Governed runtime invocation")
    print(f"Invocation: {record.invocation_ref}")
    print(f"Status: {record.status}")
    print(f"Authority: {record.request.requested_authority}")
    print(f"Profile: {record.request.requested_profile}")
    print(f"Policy: {record.policy_decision.policy_decision_ref}")
    print(f"Payload: {record.payload_fingerprint_ref}")
    print(f"Safe-disable: {record.safe_disable.safe_disable_ref}")
    if record.action_inbox_envelope is not None:
        envelope = record.action_inbox_envelope
        print(f"Envelope: {envelope.action_envelope_ref}")
        print(f"Approval ref: {envelope.approval_ref}")
        print(f"Approval validated: {envelope.approval_validated}")
    if record.receipt is not None:
        print(f"Receipt: {record.receipt.receipt_ref}")
        print(f"Execution performed: {record.receipt.execution_performed}")


def _print_invocations(records: list[Any]) -> None:
    print("Governed runtime invocations")
    if not records:
        print("- none")
        return
    for record in records:
        receipt_ref = record.receipt.receipt_ref if record.receipt else "none"
        print(f"- {record.invocation_ref} status={record.status} receipt={receipt_ref}")


def _print_receipt(record: Any) -> None:
    receipt = record.receipt
    if receipt is None:
        print("Governed runtime receipt")
        print("Receipt: not recorded")
        print(f"Invocation: {record.invocation_ref}")
        return
    print("Governed runtime receipt")
    print(f"Receipt: {receipt.receipt_ref}")
    print(f"Invocation: {record.invocation_ref}")
    print(f"Status: {receipt.invocation_status}")
    print(f"Execution performed: {receipt.execution_performed}")
    print(f"Command performed: {receipt.command_execution_performed}")
    print(f"Model call performed: {receipt.model_call_performed}")
    print("Evidence refs: " + ", ".join(receipt.evidence_refs or ["none"]))
    print(
        "Blocked authority refs: "
        + ", ".join(receipt.blocked_authority_refs or ["none"])
    )
    if receipt.command_receipt_metadata is not None:
        metadata = receipt.command_receipt_metadata
        print(f"Command status: {metadata.status_category}")
        print(
            f"Exit code: {metadata.exit_code if metadata.exit_code is not None else 'none'}"
        )
        print(f"Timed out: {metadata.timed_out}")
        print(f"Output summary: {metadata.output_summary}")
    try:
        evidence = build_runtime_action_signed_evidence(record)
    except ValueError:
        evidence = None
    if evidence is not None:
        print(f"Signed evidence: {evidence.signed_envelope_ref}")
        print(f"Evidence verifier: {evidence.verifier_ref}")


def _runtime_store(args: argparse.Namespace) -> RuntimeInvocationStore:
    active_leases = active_runtime_authority_leases()
    if args.state_dir is None:
        return RuntimeInvocationStore(active_authority_leases=active_leases)
    return RuntimeInvocationStore(
        Path(args.state_dir),
        active_authority_leases=active_leases,
    )


def _inspect_action_inbox_bridge(args: argparse.Namespace) -> int:
    store = _runtime_store(args)
    read_model = _read_model(store)
    if args.json:
        _print_json(_bridge_payload(read_model))
    else:
        _print_bridge_summary(read_model)
    return 0


def _inspect_parity_loop(args: argparse.Namespace) -> int:
    store = _runtime_store(args)
    read_model = build_runtime_parity_loop_read_model(
        store.list_invocations(),
        entries=store.list_entries(),
    )
    if args.json:
        _print_json(_parity_loop_payload(read_model))
    else:
        _print_parity_loop(read_model)
    return 0


def _status(args: argparse.Namespace) -> int:
    read_model = _read_model(_runtime_store(args))
    if args.json:
        _print_json(
            _runtime_payload(read_model, "repo-local-command:governed-runtime-status")
        )
    else:
        _print_status(read_model)
    return 0


def _capabilities(args: argparse.Namespace) -> int:
    capabilities = build_default_runtime_capabilities().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:governed-runtime-capabilities",
        "capabilities": capabilities,
        "safe_refs_only": True,
        "raw_content_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_capabilities()
    return 0


def _command_run(args: argparse.Namespace) -> int:
    try:
        request = RuntimeCommandExecutionRequest(
            intent=args.intent,
            requested_profile=args.profile,
            mission_ref=args.mission_ref,
            target_refs=args.target_ref or [],
            safe_summary=args.summary,
            timeout_seconds=args.timeout_seconds,
            output_byte_limit=args.output_byte_limit,
            metadata_refs=args.metadata_ref or [],
        )
        result = RuntimeGateway(store=_runtime_store(args)).invoke_command(
            request,
            idempotency_ref=args.idempotency_ref,
        )
    except RuntimeInvocationConflictError:
        payload = {
            "schema_version": "governed-runtime-cli:v1",
            "command_ref": "repo-local-command:uaa-runtime-command-run",
            "success": False,
            "trace_id": args.idempotency_ref,
            "error_category": "RUNTIME_INVOCATION_IDEMPOTENCY_CONFLICT",
            "safe_message": (
                "The governed runtime idempotency ref already has a different "
                "payload fingerprint."
            ),
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "raw_paths_omitted": True,
            "raw_command_output_omitted": True,
            "execution_performed": False,
        }
        if args.json:
            _print_json(payload)
        else:
            print("Governed runtime command run")
            print("Status: conflict")
            print(f"Trace: {args.idempotency_ref}")
            print(f"Error: {payload['error_category']}")
            print(payload["safe_message"])
        return 1
    except ValidationError:
        payload = {
            "schema_version": "governed-runtime-cli:v1",
            "command_ref": "repo-local-command:uaa-runtime-command-run",
            "success": False,
            "trace_id": args.idempotency_ref,
            "error_category": "RUNTIME_COMMAND_REQUEST_INVALID",
            "safe_message": "The governed runtime command request failed safe validation.",
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "raw_paths_omitted": True,
            "raw_command_output_omitted": True,
            "execution_performed": False,
        }
        if args.json:
            _print_json(payload)
        else:
            print("Governed runtime command run")
            print("Status: invalid")
            print(f"Trace: {args.idempotency_ref}")
            print(f"Error: {payload['error_category']}")
            print(payload["safe_message"])
        return 2

    receipt = result.record.receipt
    metadata = receipt.command_receipt_metadata if receipt else None
    success = (
        result.error_category is None
        and result.record.status == "receipt_recorded"
        and result.exit_code == 0
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-command-run",
        "success": success,
        "trace_id": result.record.invocation_ref,
        "record": result.record.model_dump(mode="json"),
        "replayed": result.replayed,
        "execution_performed": bool(receipt and receipt.execution_performed),
        "adapter_execution_enabled": result.record.policy_decision.adapter_execution_enabled,
        "command_execution_enabled": result.command_execution_enabled,
        "command_execution_performed": bool(
            receipt and receipt.command_execution_performed
        ),
        "mission_ref": request.mission_ref,
        "shell_strings_accepted": False,
        "raw_output_persisted": False,
        "output_summary": result.output_summary,
        "output_summary_returned": result.output_summary_returned,
        "output_persisted": False,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "error_category": result.error_category,
        "receipt_ref": receipt.receipt_ref if receipt else None,
        "metadata_ref": metadata.redacted_output_ref if metadata else None,
        "blocked_authority_refs": (
            receipt.blocked_authority_refs
            if receipt
            else result.record.policy_decision.blocked_authority_refs
        ),
        "blocked_runtime_authority": [
            "arbitrary_command_text",
            "shell_execution",
            "networked_commands",
            "raw_command_output_persistence",
            "browser_automation",
            "connector_write",
            "plugin_runtime_import",
            "remote_provider_model_call",
            "production_authority",
        ],
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Governed runtime command run")
        print(f"Status: {result.record.status}")
        print(f"Invocation: {result.record.invocation_ref}")
        print(f"Intent: {request.intent}")
        print(f"Mission: {request.mission_ref or 'none'}")
        print(f"Policy: {result.record.policy_decision.policy_decision_ref}")
        print(
            f"Authority decision: "
            f"{result.record.policy_decision.authority_decision_outcome or 'not_evaluated'}"
        )
        print(
            f"Authority lease: "
            f"{result.record.policy_decision.authority_lease_ref or 'none'}"
        )
        print(f"Receipt: {payload['receipt_ref'] or 'none'}")
        print(f"Command enabled: {result.command_execution_enabled}")
        print(f"Command performed: {payload['command_execution_performed']}")
        print(
            f"Exit code: {result.exit_code if result.exit_code is not None else 'none'}"
        )
        print(f"Timed out: {result.timed_out}")
        print(f"Error: {result.error_category or 'none'}")
        if result.output_summary:
            print(f"Output summary: {result.output_summary}")
    return 0 if success else 1


def _authority_profile(args: argparse.Namespace) -> int:
    profile = build_governed_product_pilot_authority_profile()
    read_model = profile.model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-authority-profile",
        "authority_profile": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_authority_profile(read_model)
    return 0


def _authority_domain_summary(domains: dict[str, list[str]]) -> str:
    if not domains:
        return "none"
    parts = []
    for domain, capabilities in sorted(domains.items()):
        capability_text = ", ".join(str(capability) for capability in capabilities)
        parts.append(f"{domain}: {capability_text or 'none'}")
    return "; ".join(parts)


def _authority_constraint_summary(constraints: dict[str, Any]) -> str:
    if not constraints:
        return "none"
    return ", ".join(
        f"{key}={json.dumps(value, sort_keys=True)}"
        for key, value in sorted(constraints.items())
    )


def _authority_ref_summary(refs: list[str]) -> str:
    return ", ".join(refs) if refs else "none"


def _authority_counts_summary(
    counts: dict[str, Any],
    ordered_keys: list[str] | None = None,
) -> str:
    if ordered_keys:
        items = [(key, counts.get(key, 0)) for key in ordered_keys if key in counts]
    else:
        items = sorted(counts.items())
    return ", ".join(f"{key}={value}" for key, value in items) if items else "none"


def _inspect_authority_state(args: argparse.Namespace) -> int:
    read_model = AuthorityLeaseStore().build_state_read_model().model_dump(mode="json")
    if args.json:
        _print_json(_authority_payload(read_model))
    else:
        print("Authority modes and mission leases")
        print(f"Active mode: {read_model['active_mode']}")
        print(f"Contract: {read_model['contract_ref']}")
        print(f"API: {read_model['api_ref']}")
        print(f"Summary: {read_model['operator_summary']}")
        print(f"Mode readiness: {len(read_model['mode_catalog'])}")
        for mode_entry in read_model["mode_catalog"]:
            approval = (
                "approval_required"
                if mode_entry["approval_required"]
                else "approval_not_required"
            )
            issue_ready = (
                "issue_ready" if mode_entry["issue_ready"] else "not_issue_ready"
            )
            print(
                f"- {mode_entry['mode']} scope={mode_entry['scope']} "
                f"status={mode_entry['status']} {approval} {issue_ready}"
            )
            print(f"  summary: {mode_entry['operator_summary']}")
            print(
                "  default request: "
                f"{_authority_domain_summary(mode_entry['default_requested_domains'])}"
            )
            print(
                "  default grant: "
                f"{_authority_domain_summary(mode_entry['granted_default_domains'])}"
            )
            print(
                "  denied defaults: "
                f"{_authority_ref_summary(mode_entry['denied_default_domain_refs'])}"
            )
            print(
                "  unsupported adapters: "
                f"{_authority_ref_summary(mode_entry['unsupported_adapter_refs'])}"
            )
            print(
                "  blocked reasons: "
                f"{_authority_ref_summary(mode_entry['blocked_reason_refs'])}"
            )
        print(f"Active leases: {len(read_model['active_leases'])}")
        for lease in read_model["active_leases"]:
            print(
                f"- {lease['lease_ref']} mode={lease['mode']} "
                f"scope={lease['scope']} status={lease['status']}"
            )
            print(f"  issued={lease['issued_at']} expires={lease['expires_at']}")
            print(f"  domains: {_authority_domain_summary(lease['domains'])}")
            print(
                f"  constraints: {_authority_constraint_summary(lease['constraints'])}"
            )
            print(
                f"  safe-disable={lease['safe_disable_ref']} "
                f"rollback={lease['rollback_ref']} "
                f"kill-switch={lease['kill_switch_ref']}"
            )
            print(
                "  unsupported adapters: "
                f"{_authority_ref_summary(lease['unsupported_adapter_refs'])}"
            )
        print(f"Capability mappings: {len(read_model['capability_mappings'])}")
        summary = read_model["decision_summary"]
        print(f"Decision summary: {summary['operator_summary']}")
        print(
            "Outcome counts: "
            f"{_authority_counts_summary(summary['outcome_counts'], read_model['policy_outcomes'])}"
        )
        print(
            "Domain counts: "
            f"{_authority_counts_summary(summary['domain_counts'], read_model['target_domains'])}"
        )
        print(f"Status counts: {_authority_counts_summary(summary['status_counts'])}")
        print(
            f"Blocked reasons: {_authority_ref_summary(summary['blocked_reason_refs'])}"
        )
        print(
            "Unsupported adapters: "
            f"{_authority_ref_summary(summary['unsupported_adapter_refs'])}"
        )
        if not args.summary:
            print(f"Decision catalog: {len(read_model['decision_catalog'])}")
            for entry in read_model["decision_catalog"]:
                decision = entry["decision"]
                requirement = _authority_decision_requirement_dict(decision)
                print(
                    f"- {decision['outcome']} {entry['authority_capability_ref']} "
                    f"{decision['domain']}/{decision['capability']}: {requirement}"
                )
                print(f"  catalog: {entry['catalog_ref']}")
                print(f"  source: {entry['lane_ref']}")
                print(f"  status: {entry['status']}")
                print(f"  lease: {decision['lease_ref'] or 'none'}")
                print(f"  reasons: {_authority_ref_summary(decision['reason_refs'])}")
                print(
                    "  unsupported adapters: "
                    f"{_authority_ref_summary(entry['unsupported_adapter_refs'])}"
                )
        print("Sample decisions:")
        for decision in read_model["sample_decisions"]:
            requirement = _authority_decision_requirement_dict(decision)
            print(
                f"- {decision['outcome']} {decision['domain']}/"
                f"{decision['capability']}: {requirement}"
            )
            print(f"  lease: {decision['lease_ref'] or 'none'}")
            print(f"  reasons: {_authority_ref_summary(decision['reason_refs'])}")
            print(f"  message: {decision['operator_message']}")
        print("Recent receipts:")
        for receipt in read_model["recent_receipts"]:
            print(
                f"- {receipt['status']} {receipt['receipt_ref']} "
                f"mode={receipt['mode']} scope={receipt['scope']}"
            )
            print(
                f"  lease-issued={receipt.get('lease_issued_at') or 'none'} "
                f"lease-expires={receipt.get('lease_expires_at') or 'none'}"
            )
            print(f"  granted: {_authority_domain_summary(receipt['granted_domains'])}")
            print(f"  denied: {_authority_ref_summary(receipt['denied_domain_refs'])}")
            print(
                "  unsupported adapters: "
                f"{_authority_ref_summary(receipt['unsupported_adapter_refs'])}"
            )
        print(f"Unknown authority default: {read_model['unknown_authority_default']}")
        print(f"Kill switch visible: {read_model['kill_switch_visible']}")
        print(f"Kill switch engaged: {read_model['kill_switch_engaged']}")
    return 0


def _parse_authority_domains(
    values: list[str] | None,
) -> dict[AuthorityDomain, list[AuthorityCapability]]:
    parsed: dict[AuthorityDomain, list[AuthorityCapability]] = {}
    for value in values or []:
        if ":" not in value:
            raise SystemExit(
                f"authority domain must use domain:capability,capability form: {value}"
            )
        domain_text, capability_text = value.split(":", 1)
        domain = AuthorityDomain(domain_text.strip())
        capabilities = [
            AuthorityCapability(item.strip())
            for item in capability_text.split(",")
            if item.strip()
        ]
        if not capabilities:
            raise SystemExit(f"authority domain has no capabilities: {value}")
        parsed[domain] = capabilities
    return parsed


def _authority_value_label(value: Any) -> str:
    return str(getattr(value, "value", value)).replace("_", " ")


def _authority_ref_labels(refs: list[str], prefix: str) -> str:
    labels = [ref.removeprefix(f"{prefix}:").replace("_", " ") for ref in refs]
    return ", ".join(label for label in labels if label)


def _authority_decision_requirement(decision: Any) -> str:
    mode = (
        _authority_value_label(decision.required_mode)
        if decision.required_mode
        else "active lease"
    )
    domain = _authority_ref_labels(
        list(decision.required_domain_refs),
        "authority-domain-ref",
    ) or _authority_value_label(decision.domain)
    capability = _authority_ref_labels(
        list(decision.required_capability_refs),
        "authority-capability-ref",
    ) or _authority_value_label(decision.capability)
    return f"Requires {mode} + {domain} domain + {capability} capability."


def _authority_decision_requirement_dict(decision: dict[str, Any]) -> str:
    mode = (
        _authority_value_label(decision["required_mode"])
        if decision.get("required_mode")
        else "active lease"
    )
    domain = _authority_ref_labels(
        list(decision.get("required_domain_refs") or []),
        "authority-domain-ref",
    ) or _authority_value_label(decision["domain"])
    capability = _authority_ref_labels(
        list(decision.get("required_capability_refs") or []),
        "authority-capability-ref",
    ) or _authority_value_label(decision["capability"])
    return f"Requires {mode} + {domain} domain + {capability} capability."


def _authority_mission_requirement(plan: Any) -> str:
    mode = _authority_value_label(plan.requested_mode)
    domains = _authority_ref_labels(
        list(plan.required_domain_refs),
        "authority-domain-ref",
    ) or ", ".join(
        domain.replace("_", " ") for domain in sorted(plan.requested_domains)
    )
    capabilities = (
        _authority_ref_labels(
            list(plan.required_capability_refs),
            "authority-capability-ref",
        )
        or "declared capability"
    )
    prefix = "Issue-ready for" if plan.lease_issue_ready else "Requires"
    return (
        f"{prefix} {mode} + {domains} domain scope + {capabilities} capability scope."
    )


def _select_authority_mode(args: argparse.Namespace) -> int:
    approval_grants = [json.loads(value) for value in (args.approval_grant_json or [])]
    if args.approve and (args.approval_ref or approval_grants):
        print(
            "ERROR: --approve captures an exact local approval grant; do not also pass "
            "--approval-ref or --approval-grant-json.",
            file=sys.stderr,
        )
        return 2
    request = AuthorityLeaseIssueRequest(
        mode=TrustMode(args.mode),
        scope=args.scope,
        mission_ref=args.mission_ref,
        requested_domains=_parse_authority_domains(args.domain),
        decision_reason_ref=args.reason_ref,
        duration_minutes=args.duration_minutes,
        safe_summary=args.summary,
        approval_ref=args.approval_ref,
        approval_grants=approval_grants,
    )
    approval_requirement = None
    approval_captured = False
    approval_ref = args.approval_ref
    if args.approve:
        approval_requirement, approval_grant = (
            build_authority_lease_operator_approval_grant(
                request,
                idempotency_ref=args.idempotency_ref,
                approved_by_actor_id=args.approved_by_actor_ref,
            )
        )
        if approval_grant is not None:
            approval_captured = True
            approval_ref = approval_grant.approval_ref
            request = request.model_copy(
                update={
                    "approval_ref": approval_grant.approval_ref,
                    "approval_grants": [approval_grant.model_dump(mode="json")],
                }
            )
    lease, receipt = AuthorityLeaseStore().issue_lease(
        request,
        idempotency_ref=args.idempotency_ref,
        approval_validator=validate_authority_lease_approval,
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-select-authority-mode",
        "lease": lease.model_dump(mode="json") if lease is not None else None,
        "receipt": receipt.model_dump(mode="json"),
        "approval_requirement": (
            approval_requirement.model_dump(mode="json")
            if approval_requirement is not None
            else None
        ),
        "approval_captured": approval_captured,
        "approval_ref": approval_ref,
        "approval_grant_payload_persisted": False,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "execution_performed": False,
        "unsupported_adapters_claimed_execution": False,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Authority mode selection")
        print(f"Status: {receipt.status}")
        print(f"Mode: {receipt.mode}")
        print(f"Lease: {receipt.lease_ref}")
        print(f"Receipt: {receipt.receipt_ref}")
        print(f"Approval required: {receipt.approval_required}")
        print(f"Approval validated: {receipt.approval_validated}")
        print(f"Approval status: {receipt.approval_status}")
        print(f"Approval captured: {approval_captured}")
        if approval_ref:
            print(f"Approval ref: {approval_ref}")
        print(f"Approval scope: {receipt.approval_scope_ref or 'none'}")
        print(f"Granted domains: {len(receipt.granted_domains)}")
        print(f"Denied domains: {len(receipt.denied_domain_refs)}")
    return 0 if receipt.status in {"issued", "replayed"} else 1


def _revoke_authority_lease(args: argparse.Namespace) -> int:
    request = AuthorityLeaseRevokeRequest(
        lease_ref=args.lease_ref,
        decision_reason_ref=args.reason_ref,
        safe_summary=args.summary,
    )
    lease, receipt = AuthorityLeaseStore().revoke_lease(
        request,
        idempotency_ref=args.idempotency_ref,
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-revoke-authority-lease",
        "lease": lease.model_dump(mode="json") if lease is not None else None,
        "receipt": receipt.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "execution_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Authority lease revoke")
        print(f"Status: {receipt.status}")
        print(f"Lease: {receipt.lease_ref}")
        print(f"Receipt: {receipt.receipt_ref}")
    return 0 if receipt.status in {"revoked", "replayed"} else 1


def _preview_authority_decision(args: argparse.Namespace) -> int:
    request = AuthorityActionRequest(
        action_ref=args.action_ref,
        domain=AuthorityDomain(args.domain),
        capability=AuthorityCapability(args.capability),
        safe_summary=args.summary,
        resource_refs=args.resource_ref or [],
        route_ref=args.route_ref,
        capability_ref=args.capability_ref,
        lane_ref=args.lane_ref,
        adapter_ref=args.adapter_ref,
        requested_mode=TrustMode(args.requested_mode) if args.requested_mode else None,
        draft_fallback_available=args.draft_fallback_available,
        unsupported_adapter=args.unsupported_adapter,
        kill_switch_engaged=args.kill_switch_engaged,
    )
    preview = AuthorityLeaseStore().preview_decision(request)
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-preview-authority-decision",
        "authority_decision_preview": preview.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "execution_performed": False,
        "mutation_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        decision = preview.decision
        print("Authority decision preview")
        print(f"Outcome: {decision.outcome}")
        print(f"Domain: {decision.domain}")
        print(f"Capability: {decision.capability}")
        print(f"Capability ref: {decision.capability_ref or 'none'}")
        print(f"Requirement: {_authority_decision_requirement(decision)}")
        print(f"Lease: {decision.lease_ref or 'none'}")
        print(f"Decision: {decision.decision_ref}")
        print(f"Preview receipt: {preview.preview_receipt_ref}")
        print(f"Message: {decision.operator_message}")
    return 0


def _plan_authority_mission(args: argparse.Namespace) -> int:
    request = AuthorityMissionPlanRequest(
        mission_ref=args.mission_ref,
        safe_goal_summary=args.summary,
        requested_mode=TrustMode(args.mode),
        requested_domains=_parse_authority_domains(args.domain),
        decision_reason_ref=args.reason_ref,
        duration_minutes=args.duration_minutes,
        draft_fallback_available=True,
    )
    plan = AuthorityLeaseStore().plan_mission(request)
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-plan-authority-mission",
        "authority_mission_plan": plan.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "execution_performed": False,
        "mutation_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Authority mission plan")
        print(f"Mission: {plan.mission_ref}")
        print(f"Mode: {plan.requested_mode}")
        print(f"Issue ready: {'yes' if plan.lease_issue_ready else 'no'}")
        print(f"Requirement: {_authority_mission_requirement(plan)}")
        print(f"Granted domains: {len(plan.granted_domains)}")
        print(f"Unsupported adapters: {len(plan.unsupported_adapter_refs)}")
        print(f"Action previews: {len(plan.action_previews)}")
        print(f"Plan: {plan.plan_ref}")
        print(f"Next: {plan.next_safe_action}")
    return 0


def _inspect_role_provider_evidence(args: argparse.Namespace) -> int:
    evidence = build_model_provider_control_plane_read_model().role_provider_evidence
    read_model = evidence.model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-role-provider-evidence",
        "role_provider_evidence": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_credentials_omitted": True,
        "raw_provider_payload_omitted": True,
        "raw_paths_omitted": True,
        "execution_performed": False,
        "provider_model_call_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_role_provider_evidence(read_model)
    return 0


def _inspect_delegation_adapter(args: argparse.Namespace) -> int:
    read_model = build_runtime_delegation_adapter_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-delegation-adapter",
        "runtime_delegation_adapter": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "raw_logs_omitted": True,
        "execution_performed": False,
        "live_run_submission_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_delegation_adapter(read_model)
    return 0


def _inspect_interface_mode(args: argparse.Namespace) -> int:
    read_model = build_runtime_interface_mode_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-interface-mode",
        "runtime_interface_mode": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_runtime_output_omitted": True,
        "execution_performed": False,
        "uaa_native_agent_execution_enabled": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_interface_mode(read_model)
    return 0


def _inspect_hermes_context_pack(args: argparse.Namespace) -> int:
    read_model = build_hermes_context_pack_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-hermes-context-pack",
        "hermes_context_pack": read_model,
        "safe_refs_only": True,
        "raw_memory_records_omitted": True,
        "raw_crm_records_omitted": True,
        "raw_chat_transcripts_omitted": True,
        "raw_paths_omitted": True,
        "execution_performed": False,
        "direct_memory_write_enabled": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_hermes_context_pack(read_model)
    return 0


def _hermes_chat(args: argparse.Namespace) -> int:
    try:
        request = HermesChatRequest(
            mode=args.mode,
            query=args.query,
            mission_ref=args.mission_ref,
            operator_submission_acknowledged=True,
        )
    except ValidationError:
        query_digest = hashlib.sha256(args.query.encode("utf-8")).hexdigest()[:24]
        receipt = {
            "schema_version": "hermes_chat_receipt.v1",
            "receipt_ref": f"hermes-chat-receipt-ref:blocked:{query_digest}",
            "status": "blocked_unsafe_input",
            "mode": args.mode,
            "query_ref": f"hermes-query-ref:sha256:{query_digest}",
            "context_pack_ref": "hermes-context-pack-ref:uaa-curated-runtime-interface-mode",
            "execution_performed": False,
            "external_handoff_only": False,
            "output_summary": "Hermes chat was blocked before execution because the query failed interface-mode validation.",
            "memory_update_policy": "candidate_only_review_required",
            "blocked_reason_refs": ["blocked-authority:hermes-unsafe-query-fragment"],
            "unsafe_arg_blocked": True,
            "raw_prompt_persisted": False,
            "raw_response_persisted": False,
            "raw_output_persisted": False,
            "raw_local_path_persisted": False,
            "hidden_output_persistence_enabled": False,
            "idempotency_ref": args.idempotency_ref,
        }
        payload = {
            "schema_version": "governed-runtime-cli:v1",
            "command_ref": "repo-local-command:uaa-runtime-hermes-chat",
            "hermes_chat_receipt": receipt,
            "safe_refs_only": True,
            "raw_query_omitted": True,
            "raw_output_omitted": True,
            "raw_paths_omitted": True,
            "memory_updates_candidate_only": True,
            "execution_performed": False,
        }
        if args.json:
            _print_json(payload)
        else:
            _print_hermes_chat(receipt)
        return 2
    receipt = (
        HermesCliAdapter()
        .chat(
            request,
            idempotency_ref=args.idempotency_ref,
            active_authority_leases=active_runtime_authority_leases(),
        )
        .model_dump(mode="json")
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-hermes-chat",
        "hermes_chat_receipt": receipt,
        "safe_refs_only": True,
        "raw_query_omitted": True,
        "raw_output_omitted": True,
        "raw_paths_omitted": True,
        "memory_updates_candidate_only": True,
        "execution_performed": receipt["execution_performed"],
    }
    if args.json:
        _print_json(payload)
    else:
        _print_hermes_chat(receipt)
    return 0


def _inspect_capability_discovery(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_capability_discovery_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-capability-discovery",
        "runtime_capability_discovery": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "raw_runtime_payload_omitted": True,
        "raw_logs_omitted": True,
        "execution_performed": False,
        "live_discovery_performed": False,
        "runtime_permission_granted": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_capability_discovery(read_model)
    return 0


def _inspect_tool_registry(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_tool_registry_availability_read_model_from_authority_catalog(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-tool-registry",
        "runtime_tool_registry": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "raw_runtime_payload_omitted": True,
        "raw_tool_payload_omitted": True,
        "raw_logs_omitted": True,
        "execution_performed": False,
        "tool_invocation_performed": False,
        "remote_discovery_performed": False,
        "plugin_import_performed": False,
        "connector_write_activation_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_tool_registry(read_model)
    return 0


def _inspect_virtual_provider_moa(args: argparse.Namespace) -> int:
    read_model = build_runtime_virtual_provider_moa_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-virtual-provider-moa",
        "runtime_virtual_provider_moa": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_prompts_omitted": True,
        "raw_responses_omitted": True,
        "provider_payloads_omitted": True,
        "advisor_prompts_omitted": True,
        "agent_outputs_omitted": True,
        "live_model_fanout_performed": False,
        "provider_sdk_call_performed": False,
        "external_runtime_dispatch_performed": False,
        "hidden_advisor_prompt_used": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_virtual_provider_moa(read_model)
    return 0


def _inspect_usage_cost_analytics(args: argparse.Namespace) -> int:
    read_model = build_runtime_usage_cost_analytics_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-usage-cost-analytics",
        "runtime_usage_cost_analytics": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_prompts_omitted": True,
        "raw_responses_omitted": True,
        "provider_payloads_omitted": True,
        "billing_payloads_omitted": True,
        "operator_export_payloads_omitted": True,
        "provider_call_performed": False,
        "provider_sdk_call_performed": False,
        "billing_action_performed": False,
        "live_price_fetch_performed": False,
        "operator_export_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_usage_cost_analytics(read_model)
    return 0


def _inspect_prompt_stability_tiers(args: argparse.Namespace) -> int:
    read_model = build_runtime_prompt_stability_tiers_read_model().model_dump(
        mode="json"
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-prompt-stability-tiers",
        "runtime_prompt_stability_tiers": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_prompts_omitted": True,
        "raw_responses_omitted": True,
        "provider_payloads_omitted": True,
        "prompt_material_omitted": True,
        "operator_turn_text_omitted": True,
        "hidden_prompt_injection_performed": False,
        "context_injection_performed": False,
        "model_call_performed": False,
        "cache_write_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_prompt_stability_tiers(read_model)
    return 0


def _inspect_context_budget_pressure(args: argparse.Namespace) -> int:
    read_model = build_runtime_context_budget_pressure_read_model().model_dump(
        mode="json"
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-context-budget-pressure",
        "runtime_context_budget_pressure": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_context_omitted": True,
        "raw_prompts_omitted": True,
        "raw_responses_omitted": True,
        "provider_payloads_omitted": True,
        "summary_material_omitted": True,
        "hidden_compression_performed": False,
        "automatic_context_mutation_performed": False,
        "model_summarization_call_performed": False,
        "context_injection_performed": False,
        "cache_write_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_context_budget_pressure(read_model)
    return 0


def _inspect_hardline_command_blocklist(args: argparse.Namespace) -> int:
    read_model = build_runtime_hardline_command_blocklist_read_model().model_dump(
        mode="json"
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-hardline-command-blocklist",
        "runtime_hardline_command_blocklist": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_text_omitted": True,
        "raw_command_output_omitted": True,
        "argv_examples_omitted": True,
        "override_bypass_permitted": False,
        "command_execution_performed": False,
        "runner_invocation_performed": False,
        "production_authority_enabled": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_hardline_command_blocklist(read_model)
    return 0


def _inspect_managed_scope_policy(args: argparse.Namespace) -> int:
    read_model = build_runtime_managed_scope_policy_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-managed-scope-policy",
        "runtime_managed_scope_policy": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_config_omitted": True,
        "protected_material_omitted": True,
        "account_material_omitted": True,
        "system_config_write_performed": False,
        "privileged_write_performed": False,
        "mdm_delivery_performed": False,
        "runtime_config_mutation_performed": False,
        "production_enforcement_claimed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_managed_scope_policy(read_model)
    return 0


def _inspect_doctor_diagnostics(args: argparse.Namespace) -> int:
    read_model = build_runtime_doctor_diagnostics_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-doctor-diagnostics",
        "runtime_doctor_diagnostics": read_model,
        "safe_refs_only": True,
        "redacted_status_only": True,
        "raw_logs_omitted": True,
        "raw_paths_omitted": True,
        "provider_payloads_omitted": True,
        "protected_material_omitted": True,
        "install_performed": False,
        "service_start_performed": False,
        "credential_write_performed": False,
        "runtime_config_mutation_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_doctor_diagnostics(read_model)
    return 0


def _inspect_session_continuity(args: argparse.Namespace) -> int:
    read_model = build_runtime_session_continuity_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-session-continuity",
        "runtime_session_continuity": read_model,
        "safe_refs_only": True,
        "redacted_status_only": True,
        "raw_transcripts_omitted": True,
        "raw_prompts_omitted": True,
        "raw_responses_omitted": True,
        "provider_payloads_omitted": True,
        "account_material_omitted": True,
        "external_message_gateway_performed": False,
        "account_sync_performed": False,
        "connector_write_performed": False,
        "remote_session_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_session_continuity(read_model)
    return 0


def _inspect_mcp_catalog_filtering(args: argparse.Namespace) -> int:
    read_model = build_runtime_mcp_catalog_filtering_read_model().model_dump(
        mode="json"
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-mcp-catalog-filtering",
        "runtime_mcp_catalog_filtering": read_model,
        "safe_refs_only": True,
        "metadata_only": True,
        "raw_mcp_manifests_omitted": True,
        "raw_tool_schemas_omitted": True,
        "login_material_omitted": True,
        "connector_payloads_omitted": True,
        "install_performed": False,
        "subprocess_runtime_performed": False,
        "oauth_login_performed": False,
        "tool_invocation_performed": False,
        "connector_write_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_mcp_catalog_filtering(read_model)
    return 0


def _inspect_background_jobs(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_background_jobs_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-background-jobs",
        "runtime_background_jobs": read_model,
        "safe_refs_only": True,
        "proposal_only": True,
        "raw_job_payloads_omitted": True,
        "raw_schedule_material_omitted": True,
        "worker_logs_omitted": True,
        "pause_performed": False,
        "resume_performed": False,
        "run_now_performed": False,
        "scheduler_started": False,
        "background_worker_started": False,
        "autonomous_retry_performed": False,
        "external_delivery_performed": False,
        "provider_call_performed": False,
        "shell_execution_performed": False,
        "connector_write_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_background_jobs(read_model)
    return 0


def _inspect_subagent_isolation(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_subagent_isolation_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-subagent-isolation",
        "runtime_subagent_isolation": read_model,
        "safe_refs_only": True,
        "readiness_only": True,
        "raw_agent_outputs_omitted": True,
        "raw_transcripts_omitted": True,
        "provider_payloads_omitted": True,
        "live_dispatch_performed": False,
        "background_fanout_performed": False,
        "cross_agent_memory_transfer_performed": False,
        "tool_sharing_performed": False,
        "autonomous_delegation_performed": False,
        "provider_call_performed": False,
        "shell_execution_performed": False,
        "connector_write_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_subagent_isolation(read_model)
    return 0


def _inspect_worktree_per_agent(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_worktree_per_agent_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-worktree-per-agent",
        "runtime_worktree_per_agent": read_model,
        "safe_refs_only": True,
        "proposal_only": True,
        "raw_paths_omitted": True,
        "raw_file_content_omitted": True,
        "raw_git_output_omitted": True,
        "git_worktree_create_performed": False,
        "git_worktree_delete_performed": False,
        "branch_mutation_performed": False,
        "file_write_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "shell_execution_performed": False,
        "provider_call_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_worktree_per_agent(read_model)
    return 0


def _inspect_lsp_diagnostics(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_lsp_diagnostics_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-lsp-diagnostics",
        "runtime_lsp_diagnostics": read_model,
        "safe_refs_only": True,
        "evidence_only": True,
        "raw_paths_omitted": True,
        "raw_file_content_omitted": True,
        "raw_diagnostic_payloads_omitted": True,
        "language_server_started": False,
        "dependency_install_performed": False,
        "shell_execution_performed": False,
        "file_read_performed": False,
        "file_write_performed": False,
        "provider_call_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_lsp_diagnostics(read_model)
    return 0


def _inspect_preview_rail(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_preview_rail_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-preview-rail",
        "runtime_preview_rail": read_model,
        "safe_refs_only": True,
        "bounded_preview_only": True,
        "raw_paths_omitted": True,
        "raw_file_content_omitted": True,
        "raw_runtime_payloads_omitted": True,
        "browser_automation_performed": False,
        "screenshot_capture_performed": False,
        "file_read_performed": False,
        "file_write_performed": False,
        "shell_execution_performed": False,
        "provider_call_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_preview_rail(read_model)
    return 0


def _inspect_slash_command_registry(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_slash_command_registry_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-slash-command-registry",
        "runtime_slash_command_registry": read_model,
        "metadata_only": True,
        "safe_refs_only": True,
        "raw_prompts_omitted": True,
        "raw_responses_omitted": True,
        "command_execution_performed": False,
        "runtime_invocation_performed": False,
        "state_mutation_performed": False,
        "shell_execution_performed": False,
        "provider_call_performed": False,
        "browser_automation_performed": False,
        "connector_write_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_slash_command_registry(read_model)
    return 0


def _inspect_interrupt_redirect(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_interrupt_redirect_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-interrupt-redirect",
        "runtime_interrupt_redirect": read_model,
        "proposal_only": True,
        "safe_refs_only": True,
        "raw_runtime_payloads_omitted": True,
        "raw_logs_omitted": True,
        "operator_instruction_text_omitted": True,
        "live_stop_post_performed": False,
        "process_kill_performed": False,
        "runtime_mutation_performed": False,
        "background_autonomy_performed": False,
        "shell_execution_performed": False,
        "provider_call_performed": False,
        "browser_automation_performed": False,
        "connector_write_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_interrupt_redirect(read_model)
    return 0


def _inspect_logging_profile(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_logging_profile_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-logging-profile",
        "runtime_logging_profile": read_model,
        "metadata_only": True,
        "safe_refs_only": True,
        "verbose_logging_toggled": False,
        "raw_logs_omitted": True,
        "raw_prompts_omitted": True,
        "raw_responses_omitted": True,
        "provider_payloads_omitted": True,
        "local_paths_omitted": True,
        "credential_material_omitted": True,
        "remote_telemetry_export_performed": False,
        "background_log_stream_started": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_logging_profile(read_model)
    return 0


def _inspect_result_classification(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_result_classification_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-result-classification",
        "runtime_result_classification": read_model,
        "metadata_only": True,
        "safe_refs_only": True,
        "classification_only": True,
        "tool_output_as_truth": False,
        "action_authority_granted": False,
        "mutation_without_receipt_allowed": False,
        "raw_outputs_omitted": True,
        "provider_payloads_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_result_classification(read_model)
    return 0


def _inspect_voice_media_posture(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_voice_media_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(
        mode="json",
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-voice-media-posture",
        "runtime_voice_media_posture": read_model,
        "metadata_only": True,
        "safe_refs_only": True,
        "voice_media_posture_only": True,
        "microphone_access_performed": False,
        "camera_access_performed": False,
        "file_upload_performed": False,
        "transcription_performed": False,
        "media_generation_performed": False,
        "provider_call_performed": False,
        "external_delivery_performed": False,
        "raw_media_omitted": True,
        "provider_payloads_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_voice_media_posture(read_model)
    return 0


def _inspect_messaging_gateway_posture(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_messaging_gateway_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(
        mode="json",
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": (
            "repo-local-command:uaa-runtime-inspect-messaging-gateway-posture"
        ),
        "runtime_messaging_gateway_posture": read_model,
        "metadata_only": True,
        "safe_refs_only": True,
        "messaging_gateway_posture_only": True,
        "connector_runtime_performed": False,
        "connector_read_performed": False,
        "send_performed": False,
        "oauth_performed": False,
        "webhook_exposure_performed": False,
        "account_sync_performed": False,
        "external_write_performed": False,
        "raw_messages_omitted": True,
        "connector_payloads_omitted": True,
        "account_material_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_messaging_gateway_posture(read_model)
    return 0


def _inspect_remote_execution_posture(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_remote_execution_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(
        mode="json",
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-remote-execution-posture",
        "runtime_remote_execution_posture": read_model,
        "metadata_only": True,
        "safe_refs_only": True,
        "remote_execution_posture_only": True,
        "remote_execution_performed": False,
        "ssh_performed": False,
        "cloud_sandbox_performed": False,
        "remote_shell_performed": False,
        "file_sync_performed": False,
        "remote_secret_access_performed": False,
        "remote_process_control_performed": False,
        "credential_material_omitted": True,
        "remote_paths_omitted": True,
        "remote_logs_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_remote_execution_posture(read_model)
    return 0


def _inspect_plugin_metadata_posture(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_plugin_metadata_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(
        mode="json",
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-plugin-metadata-posture",
        "runtime_plugin_metadata_posture": read_model,
        "metadata_only": True,
        "safe_refs_only": True,
        "plugin_metadata_posture_only": True,
        "runtime_import_performed": False,
        "hook_execution_performed": False,
        "package_install_performed": False,
        "marketplace_content_execution_performed": False,
        "plugin_code_execution_performed": False,
        "connector_write_performed": False,
        "provider_call_performed": False,
        "shell_execution_performed": False,
        "raw_manifests_omitted": True,
        "package_payloads_omitted": True,
        "external_code_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_plugin_metadata_posture(read_model)
    return 0


def _inspect_skill_marketplace_posture(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_runtime_skill_marketplace_posture_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    ).model_dump(
        mode="json",
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-skill-marketplace-posture",
        "runtime_skill_marketplace_posture": read_model,
        "metadata_only": True,
        "safe_refs_only": True,
        "skill_marketplace_posture_only": True,
        "external_popularity_trusted": False,
        "external_code_execution_performed": False,
        "direct_marketplace_install_performed": False,
        "runtime_import_performed": False,
        "automatic_skill_write_performed": False,
        "provider_call_performed": False,
        "browser_automation_performed": False,
        "connector_write_performed": False,
        "raw_marketplace_payloads_omitted": True,
        "external_code_omitted": True,
        "publisher_material_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_skill_marketplace_posture(read_model)
    return 0


def _inspect_session_search(args: argparse.Namespace) -> int:
    try:
        read_model = build_runtime_session_search_read_model(
            query_ref=args.query_ref,
            limit=args.limit,
        ).model_dump(mode="json")
    except ValueError as exc:
        payload = {
            "schema_version": "governed-runtime-cli:v1",
            "command_ref": "repo-local-command:uaa-runtime-inspect-session-search",
            "status": "blocked",
            "error_ref": "RUNTIME_SESSION_SEARCH_REF_DENIED",
            "reason_ref": str(exc) or "invalid_query_ref",
            "safe_refs_only": True,
            "raw_content_omitted": True,
            "raw_paths_omitted": True,
            "raw_transcript_omitted": True,
            "raw_prompt_omitted": True,
            "raw_response_omitted": True,
        }
        _print_json(payload)
        return 1
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-session-search",
        "runtime_session_search": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_transcript_omitted": True,
        "raw_prompt_omitted": True,
        "raw_response_omitted": True,
        "raw_provider_payload_omitted": True,
        "execution_performed": False,
        "memory_write_performed": False,
        "context_injection_performed": False,
        "semantic_provider_call_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_session_search(read_model)
    return 0


def _inspect_session_lineage(args: argparse.Namespace) -> int:
    read_model = build_runtime_session_lineage_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-session-lineage",
        "runtime_session_lineage": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_transcripts_omitted": True,
        "raw_prompts_omitted": True,
        "raw_responses_omitted": True,
        "fork_context_payloads_omitted": True,
        "hidden_context_injection_performed": False,
        "runtime_dispatch_performed": False,
        "provider_model_call_performed": False,
        "shell_execution_performed": False,
        "browser_automation_performed": False,
        "connector_write_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_session_lineage(read_model)
    return 0


def _inspect_context_references(args: argparse.Namespace) -> int:
    read_model = build_runtime_context_references_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-context-references",
        "runtime_context_references": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_file_content_omitted": True,
        "raw_url_body_omitted": True,
        "raw_prompt_omitted": True,
        "raw_response_omitted": True,
        "raw_provider_payload_omitted": True,
        "live_url_fetch_performed": False,
        "automatic_context_injection_performed": False,
        "secret_config_read_performed": False,
        "provider_model_call_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_context_references(read_model)
    return 0


def _inspect_checkpoint_rollback(args: argparse.Namespace) -> int:
    read_model = build_runtime_checkpoint_rollback_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-checkpoint-rollback",
        "runtime_checkpoint_rollback": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "checkpoint_payloads_omitted": True,
        "rollback_payloads_omitted": True,
        "broad_filesystem_snapshot_performed": False,
        "rollback_execution_performed": False,
        "git_mutation_performed": False,
        "provider_model_call_performed": False,
        "shell_execution_performed": False,
        "browser_automation_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_checkpoint_rollback(read_model)
    return 0


def _inspect_run_events(args: argparse.Namespace) -> int:
    read_model = build_runtime_run_events_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-run-events",
        "runtime_run_events": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "raw_runtime_payload_omitted": True,
        "raw_logs_omitted": True,
        "execution_performed": False,
        "run_creation_performed": False,
        "stop_performed": False,
        "approval_resolution_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_run_events(read_model)
    return 0


def _inspect_approval_bridge(args: argparse.Namespace) -> int:
    read_model = build_runtime_approval_bridge_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-approval-bridge",
        "runtime_approval_bridge": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "raw_runtime_payload_omitted": True,
        "raw_logs_omitted": True,
        "execution_performed": False,
        "approval_resolution_sent": False,
        "denial_resolution_sent": False,
        "timeout_resolution_sent": False,
        "fail_closed_timeout_policy_ref": read_model["fail_closed_timeout_posture"][
            "policy_ref"
        ],
        "auto_approve_enabled": read_model["fail_closed_timeout_posture"][
            "auto_approve_enabled"
        ],
        "approve_all_enabled": read_model["fail_closed_timeout_posture"][
            "approve_all_enabled"
        ],
        "standing_broad_authority_enabled": read_model["fail_closed_timeout_posture"][
            "standing_broad_authority_enabled"
        ],
    }
    if args.json:
        _print_json(payload)
    else:
        _print_approval_bridge(read_model)
    return 0


def _inspect_streaming_progress(args: argparse.Namespace) -> int:
    read_model = build_runtime_streaming_progress_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-streaming-progress",
        "runtime_streaming_progress": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_provider_payload_omitted": True,
        "raw_runtime_payload_omitted": True,
        "raw_tool_payload_omitted": True,
        "raw_logs_omitted": True,
        "raw_runtime_payload_persisted": False,
        "raw_tool_payload_persisted": False,
        "raw_generated_content_persisted": False,
        "raw_log_persisted": False,
        "raw_prompt_persisted": False,
        "raw_response_persisted": False,
        "execution_performed": False,
        "live_subscription_performed": False,
        "sse_subscription_performed": False,
        "websocket_subscription_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_streaming_progress(read_model)
    return 0


def _inspect_profiles(args: argparse.Namespace) -> int:
    read_model = build_runtime_profile_isolation_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-profiles",
        "runtime_profile_isolation": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_profile_names_omitted": True,
        "sensitive_material_omitted": True,
        "execution_performed": False,
        "profile_creation_performed": False,
        "profile_deletion_performed": False,
        "runtime_config_write_performed": False,
        "sensitive_material_copy_performed": False,
        "runtime_default_change_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_profiles(read_model)
    return 0


def _portable_evidence_payload(
    command_ref: str, envelope: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": command_ref,
        "portable_evidence_envelope": envelope,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }


def _export_evidence_envelope(args: argparse.Namespace) -> int:
    envelope = build_portable_evidence_envelope().model_dump(mode="json")
    payload = _portable_evidence_payload(
        "repo-local-command:uaa-runtime-export-evidence-envelope",
        envelope,
    )
    if args.json:
        _print_json(payload)
    else:
        print("Governed Product Pilot portable evidence envelope")
        print(f"Envelope: {envelope['envelope_ref']}")
        print(f"Receipt: {envelope['receipt_ref']}")
        print(f"Evidence: {envelope['evidence_ref']}")
        print(f"Hash: {envelope['envelope_hash_ref']}")
        print(f"Signed ref: {envelope['signed_envelope_ref']}")
        print("Safe refs only: true")
    return 0


def _verification_payload(result: Any) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-verify-evidence-envelope",
        "verification": result.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }


def _verify_evidence_envelope(args: argparse.Namespace) -> int:
    if args.profile:
        envelope_payload: dict[str, Any] = (
            build_portable_evidence_envelope().model_dump(mode="json")
        )
    else:
        envelope_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = verify_portable_evidence_envelope(envelope_payload)
    payload = _verification_payload(result)
    if args.json:
        _print_json(payload)
    else:
        verification = payload["verification"]
        print("Governed Product Pilot evidence envelope verification")
        print(f"Status: {verification['verification_status']}")
        print(f"Envelope: {verification['envelope_ref']}")
        print(f"Hash valid: {verification['envelope_hash_valid']}")
        print(f"Signed ref valid: {verification['signed_envelope_ref_valid']}")
        print(f"Redaction valid: {verification['redaction_status_valid']}")
        print(f"Tamper detected: {verification['tamper_detected']}")
        print("Input path echoed: false")
    return 0 if result.verification_status == "passed" else 1


def _invocations_list(args: argparse.Namespace) -> int:
    records = _runtime_store(args).list_invocations()
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:governed-runtime-invocations-list",
        "invocations": [record.model_dump(mode="json") for record in records],
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        _print_invocations(records)
    return 0


def _invocations_show(args: argparse.Namespace) -> int:
    try:
        record = _runtime_store(args).get_invocation(args.invocation_ref)
    except RuntimeInvocationNotFoundError:
        print("Invocation not found")
        return 1
    if args.json:
        _print_json(
            {
                "schema_version": "governed-runtime-cli:v1",
                "command_ref": "repo-local-command:governed-runtime-invocation-show",
                "record": record.model_dump(mode="json"),
                "safe_refs_only": True,
                "raw_content_omitted": True,
            }
        )
    else:
        _print_invocation(record)
    return 0


def _receipt_record_for_ref(
    store: RuntimeInvocationStore, receipt_ref: str
) -> Any | None:
    for record in store.list_invocations():
        if record.receipt is not None and record.receipt.receipt_ref == receipt_ref:
            return record
    return None


def _record_for_action_selector(
    store: RuntimeInvocationStore,
    selector_ref: str,
) -> Any | None:
    try:
        return store.get_invocation(selector_ref)
    except RuntimeInvocationNotFoundError:
        pass
    for record in store.list_invocations():
        envelope = record.action_inbox_envelope
        if envelope is not None and envelope.approval_ref == selector_ref:
            return record
    return None


def _approval_request_from_record(
    record: Any,
    decision: RuntimeActionInboxApprovalDecision,
) -> RuntimeApprovalBindingRequest | None:
    envelope = record.action_inbox_envelope
    if envelope is None:
        return None
    return RuntimeApprovalBindingRequest(
        decision=decision,
        action_envelope_ref=envelope.action_envelope_ref,
        exact_scope_ref=envelope.exact_scope_ref,
        expected_payload_fingerprint_ref=record.payload_fingerprint_ref,
        expected_policy_decision_ref=record.policy_decision.policy_decision_ref,
        adapter_id=envelope.adapter_id,
        command_intent=envelope.command_intent,
        risk_class=envelope.risk_class,
        expires_at=envelope.expires_at,
        safe_summary="CLI recorded an exact runtime Action Inbox decision.",
    )


def _action_decision_preflight_payload(
    record: Any,
    selector_ref: str,
    decision: RuntimeActionInboxApprovalDecision,
) -> dict[str, Any]:
    envelope = record.action_inbox_envelope
    return {
        "schema_version": "governed-runtime-cli-action-preflight:v1",
        "selector_ref": selector_ref,
        "decision": decision.value,
        "invocation_ref": record.invocation_ref,
        "status": record.status,
        "command_intent": envelope.command_intent if envelope is not None else None,
        "action_envelope_ref": (
            envelope.action_envelope_ref if envelope is not None else None
        ),
        "exact_scope_ref": envelope.exact_scope_ref if envelope is not None else None,
        "approval_ref": envelope.approval_ref if envelope is not None else None,
        "expected_payload_fingerprint_ref": record.payload_fingerprint_ref,
        "expected_policy_decision_ref": record.policy_decision.policy_decision_ref,
        "approval_records_only": True,
        "execution_performed_by_approval": False,
        "approval_can_enable_later_exact_execute": decision
        == RuntimeActionInboxApprovalDecision.approve,
        "blocked_broad_authority_refs": [
            "blocked-authority:runtime-unrestricted-command-execution",
            "blocked-authority:runtime-command-execution-without-gateway-allowlist",
            "blocked-authority:runtime-browser-automation",
            "blocked-authority:runtime-connector-writes",
        ],
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }


def _print_action_decision_preflight(payload: dict[str, Any]) -> None:
    print("Governed runtime Action Inbox decision preflight")
    print(f"Decision: {payload['decision']}")
    print(f"Invocation: {payload['invocation_ref']}")
    print(f"Current status: {payload['status']}")
    print(f"Command intent: {payload['command_intent'] or 'not_available'}")
    print(f"Envelope: {payload['action_envelope_ref'] or 'not_available'}")
    print(f"Scope: {payload['exact_scope_ref'] or 'not_available'}")
    print(f"Payload fingerprint: {payload['expected_payload_fingerprint_ref']}")
    print(f"Policy decision: {payload['expected_policy_decision_ref']}")
    print("Approval records a decision only; it does not execute the command.")
    print(
        "Execution still requires a RuntimeGateway execute request with active "
        "AuthorityLease scope."
    )
    print(
        "Blocked broad authority: " + ", ".join(payload["blocked_broad_authority_refs"])
    )


def _action_decision_idempotency_ref(
    action_decision: str,
    selector_ref: str,
    record: Any,
) -> str:
    envelope = record.action_inbox_envelope
    canonical = json.dumps(
        {
            "action_decision": action_decision,
            "selector_ref": selector_ref,
            "invocation_ref": record.invocation_ref,
            "action_envelope_ref": (
                envelope.action_envelope_ref if envelope is not None else None
            ),
            "payload_fingerprint_ref": record.payload_fingerprint_ref,
            "policy_decision_ref": record.policy_decision.policy_decision_ref,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]
    return f"idempotency-ref:governed-runtime-cli-action:{digest}"


def _receipts_show(args: argparse.Namespace) -> int:
    record = _receipt_record_for_ref(_runtime_store(args), args.receipt_ref)
    if record is None:
        print("Receipt not found")
        return 1
    if args.json:
        _print_json(
            {
                "schema_version": "governed-runtime-cli:v1",
                "command_ref": "repo-local-command:governed-runtime-receipt-show",
                "receipt": record.receipt.model_dump(mode="json")
                if record.receipt
                else None,
                "invocation_ref": record.invocation_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_command_output_omitted": True,
            }
        )
    else:
        _print_receipt(record)
    return 0


def _receipts_evidence(args: argparse.Namespace) -> int:
    record = _receipt_record_for_ref(_runtime_store(args), args.receipt_ref)
    if record is None:
        print("Receipt not found")
        return 1
    try:
        envelope = build_runtime_action_signed_evidence(record)
    except ValueError:
        print("Runtime action signed evidence not available")
        return 1
    payload = _portable_evidence_payload(
        "repo-local-command:governed-runtime-receipt-signed-evidence",
        envelope.model_dump(mode="json"),
    )
    payload["runtime_action_signed_evidence"] = payload.pop(
        "portable_evidence_envelope"
    )
    if args.json:
        _print_json(payload)
    else:
        print("Governed runtime action signed evidence")
        print(f"Envelope: {envelope.envelope_ref}")
        print(f"Receipt: {envelope.receipt_ref}")
        print(f"Hash: {envelope.envelope_hash_ref}")
        print(f"Signed ref: {envelope.signed_envelope_ref}")
        print(f"Verifier: {envelope.verifier_ref}")
        print("Safe refs only: true")
    return 0


def _receipts_verify_evidence(args: argparse.Namespace) -> int:
    envelope_payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = verify_runtime_action_signed_evidence(envelope_payload)
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:governed-runtime-receipt-verify-signed-evidence",
        "verification": result.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_command_output_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Governed runtime action signed evidence verification")
        print(f"Envelope: {result.envelope_ref}")
        print(f"Status: {result.verification_status}")
        print(f"Hash valid: {result.envelope_hash_valid}")
        print(f"Signed ref valid: {result.signed_envelope_ref_valid}")
        print(f"Tamper detected: {result.tamper_detected}")
    return 0 if result.verification_status == "passed" else 1


def _action_decision(args: argparse.Namespace) -> int:
    decision = (
        RuntimeActionInboxApprovalDecision.approve
        if args.action_decision == "approve"
        else RuntimeActionInboxApprovalDecision.deny
    )
    store = _runtime_store(args)
    selected = _record_for_action_selector(store, args.approval_selector_ref)
    if selected is None:
        print("Runtime approval selector not found")
        return 1
    request = _approval_request_from_record(selected, decision)
    if request is None:
        print("Runtime approval envelope not found")
        return 1
    preflight = _action_decision_preflight_payload(
        selected,
        args.approval_selector_ref,
        decision,
    )
    if (
        decision == RuntimeActionInboxApprovalDecision.approve
        and not args.confirm_exact_runtime_action
    ):
        if args.json:
            _print_json(
                {
                    "schema_version": "governed-runtime-cli:v1",
                    "command_ref": "repo-local-command:governed-runtime-action-approve-preflight",
                    "preflight": preflight,
                    "mutation_performed": False,
                    "confirmation_required": "--confirm-exact-runtime-action",
                }
            )
        else:
            _print_action_decision_preflight(preflight)
            print("Re-run with --confirm-exact-runtime-action to record approval.")
        return 2
    if not args.json:
        _print_action_decision_preflight(preflight)
    idempotency_ref = args.idempotency_ref or _action_decision_idempotency_ref(
        args.action_decision,
        args.approval_selector_ref,
        selected,
    )
    try:
        record = store.bind_approval(
            selected.invocation_ref,
            request,
            idempotency_ref=idempotency_ref,
        )
    except RuntimeInvocationNotFoundError:
        print("Runtime invocation not found")
        return 1
    except RuntimeInvocationConflictError:
        print("Runtime approval decision idempotency conflict")
        return 1
    except ValueError:
        print("Runtime approval decision validation failed")
        return 1
    if args.json:
        _print_json(
            {
                "schema_version": "governed-runtime-cli:v1",
                "command_ref": f"repo-local-command:governed-runtime-action-{args.action_decision}",
                "record": record.model_dump(mode="json"),
                "preflight": preflight,
                "safe_refs_only": True,
                "raw_content_omitted": True,
            }
        )
    else:
        _print_invocation(record)
    return 0


def _safe_disable(args: argparse.Namespace) -> int:
    state = _runtime_store(args).safe_disable(
        RuntimeSafeDisableRequest(reason_ref=args.reason_ref),
        idempotency_ref=args.idempotency_ref,
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:governed-runtime-safe-disable",
        "safe_disable": state.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Governed runtime safe-disable")
        print(f"Safe-disable ref: {state.safe_disable_ref}")
        print(f"Posture ref: {state.safe_disable_posture_ref}")
        print(f"Active: {state.active}")
        print(f"Profile: {state.profile}")
        print(f"Reason: {state.reason_ref}")
    return 0


def _inspect_turn_run_approval_chain(args: argparse.Namespace) -> int:
    chain = build_sample_turn_run_approval_chain()
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-turn-run-approval-chain",
        "turn_run_approval_chain": chain.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_logs_omitted": True,
        "approval_ref_grants_authority": False,
        "execution_performed": False,
    }
    if args.json:
        _print_json(payload)
    else:
        print("Turn -> Durable Run -> Approval chain")
        print(f"Chain: {chain.chain_ref}")
        print(f"State: {chain.current_state}")
        print(
            f"Turn: {chain.linkage.turn_ref.ref if chain.linkage.turn_ref else 'not_available'}"
        )
        print(f"Run: {chain.linkage.durable_run_ref.ref}")
        print(
            f"Approval: {chain.linkage.approval_ref.ref if chain.linkage.approval_ref else 'not_available'}"
        )
        print(f"Transitions: {len(chain.transitions)}")
        print("Approval refs are identifiers only; no execution was performed.")
    return 0


def _inspect_staged_orchestration(args: argparse.Namespace) -> int:
    authority_state = AuthorityLeaseStore().build_state_read_model()
    read_model = build_sample_staged_orchestration_read_model(
        authority_decision_catalog=authority_state.decision_catalog,
    )
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-inspect-staged-orchestration",
        "staged_orchestration": read_model.model_dump(mode="json"),
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_logs_omitted": True,
        "execution_performed": False,
        "background_autonomy_enabled": False,
    }
    if args.json:
        _print_json(payload)
    else:
        plan = read_model.plan
        print("Staged orchestration engine read model")
        print(f"Plan: {plan.plan_ref}")
        print(f"Status: {plan.status}")
        print(f"Stages: {read_model.progress.total_stage_count}")
        print(f"Steps: {read_model.progress.total_step_count}")
        print(f"Validation: {read_model.validation.status}")
        print(
            "Authority: "
            f"read={read_model.authority_state_decision_outcome} "
            f"runtime_command={read_model.runtime_command_authority_state_decision_outcome}"
        )
        print(f"Read decision: {read_model.authority_state_decision_ref}")
        print(
            "Runtime command decision: "
            f"{read_model.runtime_command_authority_state_decision_ref}"
        )
        print("No background autonomy, hidden model calls, or execution performed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uaa_runtime",
        description="Inspect governed runtime pilot state through safe refs.",
    )
    parser.add_argument(
        "--state-dir",
        help="Use an explicit local runtime state directory; the value is not echoed.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Inspect governed runtime status.")
    status.add_argument("--json", action="store_true", help="Emit safe JSON.")
    status.set_defaults(func=_status)

    capabilities = subparsers.add_parser(
        "capabilities",
        help="Inspect governed runtime capabilities.",
    )
    capabilities.add_argument("--json", action="store_true", help="Emit safe JSON.")
    capabilities.set_defaults(func=_capabilities)

    command = subparsers.add_parser(
        "command",
        help="Run governed RuntimeGateway command capabilities.",
    )
    command_subparsers = command.add_subparsers(dest="runtime_command", required=True)
    command_run = command_subparsers.add_parser(
        "run",
        help="Run an exact allowlisted RuntimeGateway command with receipts.",
    )
    command_run.add_argument(
        "intent",
        choices=[intent.value for intent in RuntimeCommandIntent],
        help="Allowlisted RuntimeGateway command intent.",
    )
    command_run.add_argument(
        "--profile",
        default="local-runtime",
        choices=["local-runtime", "operator-approved"],
        help="Requested runtime profile.",
    )
    command_run.add_argument(
        "--mission-ref",
        default=None,
        help="Safe mission ref for mission-scoped authority evaluation.",
    )
    command_run.add_argument(
        "--target-ref",
        action="append",
        help="Safe target ref included in the command request scope.",
    )
    command_run.add_argument(
        "--metadata-ref",
        action="append",
        help="Safe metadata ref included in the command request.",
    )
    command_run.add_argument(
        "--idempotency-ref",
        required=True,
        help="Safe idempotency ref for the command run.",
    )
    command_run.add_argument(
        "--summary",
        required=True,
        help="Safe bounded command summary.",
    )
    command_run.add_argument(
        "--timeout-seconds",
        type=float,
        default=5.0,
        help="Bounded command timeout.",
    )
    command_run.add_argument(
        "--output-byte-limit",
        type=int,
        default=4096,
        help="Bounded output byte limit for redacted summary generation.",
    )
    command_run.add_argument("--json", action="store_true", help="Emit safe JSON.")
    command_run.set_defaults(func=_command_run)

    authority_profile = subparsers.add_parser(
        "authority-profile",
        help="Inspect the Governed Product Pilot authority profile.",
    )
    authority_profile.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    authority_profile.set_defaults(func=_authority_profile)

    authority_state = subparsers.add_parser(
        "inspect-authority-state",
        help="Inspect AuthorityLease V1 modes, domains, leases, and decisions.",
    )
    authority_state.add_argument("--json", action="store_true", help="Emit safe JSON.")
    authority_state.add_argument(
        "--summary",
        action="store_true",
        help="Print a compact operator-readable authority summary before detailed refs.",
    )
    authority_state.set_defaults(func=_inspect_authority_state)

    authority_preview = subparsers.add_parser(
        "preview-authority-decision",
        help="Preview an AuthorityLease policy decision without execution.",
    )
    authority_preview.add_argument(
        "--action-ref", required=True, help="Safe action ref."
    )
    authority_preview.add_argument(
        "--domain",
        required=True,
        choices=[domain.value for domain in AuthorityDomain],
        help="Authority domain to evaluate.",
    )
    authority_preview.add_argument(
        "--capability",
        required=True,
        choices=[capability.value for capability in AuthorityCapability],
        help="Authority capability to evaluate.",
    )
    authority_preview.add_argument(
        "--summary",
        required=True,
        help="Safe bounded action summary.",
    )
    authority_preview.add_argument(
        "--resource-ref", action="append", help="Safe resource ref."
    )
    authority_preview.add_argument("--route-ref", default=None, help="Route ref.")
    authority_preview.add_argument(
        "--capability-ref",
        default=None,
        help="Authority capability ref for the previewed action.",
    )
    authority_preview.add_argument(
        "--lane-ref",
        default=None,
        help="Legacy lane ref compatibility alias; prefer --capability-ref.",
    )
    authority_preview.add_argument("--adapter-ref", default=None, help="Adapter ref.")
    authority_preview.add_argument(
        "--requested-mode",
        default=None,
        choices=[mode.value for mode in TrustMode],
        help="Requested trust mode for operator copy.",
    )
    authority_preview.add_argument(
        "--draft-fallback-available",
        action="store_true",
        help="Return degrade_to_draft when authority is absent.",
    )
    authority_preview.add_argument(
        "--unsupported-adapter",
        action="store_true",
        help="Mark the requested adapter as unsupported.",
    )
    authority_preview.add_argument(
        "--kill-switch-engaged",
        action="store_true",
        help="Simulate an engaged kill switch.",
    )
    authority_preview.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    authority_preview.set_defaults(func=_preview_authority_decision)

    mission_plan = subparsers.add_parser(
        "plan-authority-mission",
        help="Plan a mission-scoped AuthorityLease without execution.",
    )
    mission_plan.add_argument("--mission-ref", required=True, help="Safe mission ref.")
    mission_plan.add_argument(
        "--mode",
        default=TrustMode.delegated_mission_autonomous_window.value,
        choices=[mode.value for mode in TrustMode],
        help="Requested trust mode for the mission lease.",
    )
    mission_plan.add_argument(
        "--domain",
        action="append",
        required=True,
        help="Domain capabilities in domain:capability,capability form.",
    )
    mission_plan.add_argument(
        "--reason-ref",
        default="reason-ref:authority-mission-plan-cli",
        help="Safe decision reason ref for the issue draft.",
    )
    mission_plan.add_argument(
        "--duration-minutes",
        type=int,
        default=120,
        help="Mission lease duration in minutes.",
    )
    mission_plan.add_argument(
        "--summary",
        required=True,
        help="Safe bounded mission summary.",
    )
    mission_plan.add_argument("--json", action="store_true", help="Emit safe JSON.")
    mission_plan.set_defaults(func=_plan_authority_mission)

    select_authority = subparsers.add_parser(
        "select-authority-mode",
        help="Issue a session-scoped AuthorityLease for implemented domains.",
    )
    select_authority.add_argument(
        "--mode",
        required=True,
        choices=[mode.value for mode in TrustMode],
        help="Trust mode to request.",
    )
    select_authority.add_argument(
        "--domain",
        action="append",
        help=(
            "Domain capabilities in domain:capability,capability form; omit to "
            "use the backend AuthorityLease mode default scope."
        ),
    )
    select_authority.add_argument(
        "--scope",
        default="session",
        choices=["session", "mission"],
        help="Lease scope.",
    )
    select_authority.add_argument(
        "--reason-ref",
        required=True,
        help="Safe decision reason ref.",
    )
    select_authority.add_argument(
        "--idempotency-ref",
        required=True,
        help="Safe idempotency ref.",
    )
    select_authority.add_argument(
        "--duration-minutes",
        type=int,
        default=60,
        help="Lease duration in minutes.",
    )
    select_authority.add_argument(
        "--mission-ref",
        default=None,
        help="Mission ref when requesting a mission-scoped lease.",
    )
    select_authority.add_argument(
        "--approval-ref",
        default=None,
        help="Safe LocalApprovalAuthority approval ref for authority-increasing leases.",
    )
    select_authority.add_argument(
        "--approve",
        action="store_true",
        help=(
            "Capture an exact local operator approval grant before issuing an "
            "authority-increasing lease."
        ),
    )
    select_authority.add_argument(
        "--approved-by-actor-ref",
        default="operator-ref:local-cli-user",
        help="Safe operator actor ref used when --approve captures the exact grant.",
    )
    select_authority.add_argument(
        "--approval-grant-json",
        action="append",
        help=(
            "Redacted ApprovalGrant JSON used only for exact local validation; "
            "not persisted in authority receipts."
        ),
    )
    select_authority.add_argument(
        "--summary",
        required=True,
        help="Safe bounded operator summary.",
    )
    select_authority.add_argument("--json", action="store_true", help="Emit safe JSON.")
    select_authority.set_defaults(func=_select_authority_mode)

    revoke_authority = subparsers.add_parser(
        "revoke-authority-lease",
        help="Revoke an AuthorityLease and emit a safe receipt.",
    )
    revoke_authority.add_argument("--lease-ref", required=True, help="Lease ref.")
    revoke_authority.add_argument(
        "--reason-ref",
        required=True,
        help="Safe decision reason ref.",
    )
    revoke_authority.add_argument(
        "--idempotency-ref",
        required=True,
        help="Safe idempotency ref.",
    )
    revoke_authority.add_argument(
        "--summary",
        required=True,
        help="Safe bounded operator summary.",
    )
    revoke_authority.add_argument("--json", action="store_true", help="Emit safe JSON.")
    revoke_authority.set_defaults(func=_revoke_authority_lease)

    export_evidence = subparsers.add_parser(
        "export-evidence-envelope",
        help="Export a safe portable evidence envelope for offline inspection.",
    )
    export_evidence.add_argument("--json", action="store_true", help="Emit safe JSON.")
    export_evidence.set_defaults(func=_export_evidence_envelope)

    verify_evidence = subparsers.add_parser(
        "verify-evidence-envelope",
        help="Verify a safe portable evidence envelope offline.",
    )
    evidence_source = verify_evidence.add_mutually_exclusive_group(required=True)
    evidence_source.add_argument(
        "--profile",
        action="store_true",
        help="Verify the current governed product pilot profile envelope.",
    )
    evidence_source.add_argument(
        "--input",
        help="Read an envelope JSON file without echoing the local path.",
    )
    verify_evidence.add_argument("--json", action="store_true", help="Emit safe JSON.")
    verify_evidence.set_defaults(func=_verify_evidence_envelope)

    invocations = subparsers.add_parser(
        "invocations",
        help="Inspect governed runtime invocations.",
    )
    invocation_subparsers = invocations.add_subparsers(
        dest="invocations_command",
        required=True,
    )
    invocations_list = invocation_subparsers.add_parser(
        "list", help="List invocations."
    )
    invocations_list.add_argument("--json", action="store_true", help="Emit safe JSON.")
    invocations_list.set_defaults(func=_invocations_list)
    invocations_show = invocation_subparsers.add_parser("show", help="Show invocation.")
    invocations_show.add_argument("invocation_ref")
    invocations_show.add_argument("--json", action="store_true", help="Emit safe JSON.")
    invocations_show.set_defaults(func=_invocations_show)

    receipts = subparsers.add_parser(
        "receipts",
        help="Inspect governed runtime receipts.",
    )
    receipt_subparsers = receipts.add_subparsers(dest="receipts_command", required=True)
    receipt_show = receipt_subparsers.add_parser("show", help="Show receipt.")
    receipt_show.add_argument("receipt_ref")
    receipt_show.add_argument("--json", action="store_true", help="Emit safe JSON.")
    receipt_show.set_defaults(func=_receipts_show)
    receipt_evidence = receipt_subparsers.add_parser(
        "evidence",
        help="Export signed evidence for a runtime receipt.",
    )
    receipt_evidence.add_argument("receipt_ref")
    receipt_evidence.add_argument("--json", action="store_true", help="Emit safe JSON.")
    receipt_evidence.set_defaults(func=_receipts_evidence)
    receipt_verify_evidence = receipt_subparsers.add_parser(
        "verify-evidence",
        help="Verify a runtime receipt signed evidence envelope without echoing paths.",
    )
    receipt_verify_evidence.add_argument("--input", required=True)
    receipt_verify_evidence.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    receipt_verify_evidence.set_defaults(func=_receipts_verify_evidence)

    actions = subparsers.add_parser(
        "actions",
        help="Record exact runtime Action Inbox decisions.",
    )
    action_subparsers = actions.add_subparsers(dest="action_decision", required=True)
    for decision in ("approve", "deny"):
        decision_parser = action_subparsers.add_parser(
            decision,
            help=f"Record a runtime Action Inbox {decision} decision.",
        )
        decision_parser.add_argument(
            "approval_selector_ref",
            help=(
                "Approval or invocation safe ref used only to select the exact "
                "backend-owned Action Inbox envelope."
            ),
        )
        decision_parser.add_argument(
            "--idempotency-ref",
            default=None,
            help="Safe idempotency ref for the decision.",
        )
        decision_parser.add_argument(
            "--confirm-exact-runtime-action",
            action="store_true",
            help=(
                "Required for approve after reviewing the exact command "
                "preflight. Approval records a decision only; execution still "
                "requires a RuntimeGateway execute request with active "
                "AuthorityLease scope."
            ),
        )
        decision_parser.add_argument(
            "--json", action="store_true", help="Emit safe JSON."
        )
        decision_parser.set_defaults(func=_action_decision)

    safe_disable = subparsers.add_parser(
        "safe-disable",
        help="Record governed runtime safe-disable posture.",
    )
    safe_disable.add_argument(
        "--idempotency-ref",
        default="idempotency-ref:governed-runtime-cli-safe-disable",
        help="Safe idempotency ref for safe-disable.",
    )
    safe_disable.add_argument(
        "--reason-ref",
        default="reason-ref:governed-runtime-cli-safe-disable",
        help="Safe reason ref for safe-disable.",
    )
    safe_disable.add_argument("--json", action="store_true", help="Emit safe JSON.")
    safe_disable.set_defaults(func=_safe_disable)

    chain = subparsers.add_parser(
        "inspect-turn-run-approval-chain",
        help="Inspect the canonical Turn -> Durable Run -> Approval chain read model.",
    )
    chain.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref read model as JSON for automation.",
    )
    chain.set_defaults(func=_inspect_turn_run_approval_chain)

    staged = subparsers.add_parser(
        "inspect-staged-orchestration",
        help="Inspect the no-effect staged orchestration engine read model.",
    )
    staged.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref staged orchestration read model as JSON.",
    )
    staged.set_defaults(func=_inspect_staged_orchestration)

    role_provider = subparsers.add_parser(
        "inspect-role-provider-evidence",
        help="Inspect advisory role-based model/provider selection evidence.",
    )
    role_provider.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref role evidence read model as JSON.",
    )
    role_provider.set_defaults(func=_inspect_role_provider_evidence)

    delegation = subparsers.add_parser(
        "inspect-delegation-adapter",
        help="Inspect the Hermes runtime delegation adapter readiness contract.",
    )
    delegation.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref delegation adapter read model as JSON.",
    )
    delegation.set_defaults(func=_inspect_delegation_adapter)

    interface_mode = subparsers.add_parser(
        "inspect-interface-mode",
        help="Inspect runtime interface mode over Hermes without UAA agent execution.",
    )
    interface_mode.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime interface mode read model as JSON.",
    )
    interface_mode.set_defaults(func=_inspect_interface_mode)

    hermes_context_pack = subparsers.add_parser(
        "inspect-hermes-context-pack",
        help="Inspect the curated Hermes context pack without exposing raw records.",
    )
    hermes_context_pack.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref Hermes context pack read model as JSON.",
    )
    hermes_context_pack.set_defaults(func=_inspect_hermes_context_pack)

    hermes_chat = subparsers.add_parser(
        "hermes-chat",
        help="Submit an exact governed Hermes chat request with redacted receipt.",
    )
    hermes_chat.add_argument(
        "--mode",
        choices=("shell_guarded", "operator_override"),
        required=True,
        help="Interface mode for the explicit operator-submitted Hermes chat.",
    )
    hermes_chat.add_argument(
        "--query",
        required=True,
        help="Transient Hermes query; it is hashed only and not persisted.",
    )
    hermes_chat.add_argument(
        "--mission-ref",
        default=None,
        help="Optional mission ref for mission-scoped AuthorityLease matching.",
    )
    hermes_chat.add_argument(
        "--idempotency-ref",
        default="idempotency-ref:hermes-chat-cli",
        help="Safe idempotency ref for the Hermes chat receipt.",
    )
    hermes_chat.add_argument(
        "--json",
        action="store_true",
        help="Emit the redacted Hermes chat receipt as JSON.",
    )
    hermes_chat.set_defaults(func=_hermes_chat)

    capability_discovery = subparsers.add_parser(
        "inspect-capability-discovery",
        help="Inspect runtime capability discovery posture without live runtime calls.",
    )
    capability_discovery.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref capability discovery read model as JSON.",
    )
    capability_discovery.set_defaults(func=_inspect_capability_discovery)

    tool_registry = subparsers.add_parser(
        "inspect-tool-registry",
        help="Inspect runtime tool registry availability without invocation.",
    )
    tool_registry.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime tool registry read model as JSON.",
    )
    tool_registry.set_defaults(func=_inspect_tool_registry)

    virtual_provider_moa = subparsers.add_parser(
        "inspect-virtual-provider-moa",
        help="Inspect virtual multi-agent provider presets without fan-out.",
    )
    virtual_provider_moa.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref virtual provider preset read model as JSON.",
    )
    virtual_provider_moa.set_defaults(func=_inspect_virtual_provider_moa)

    usage_cost_analytics = subparsers.add_parser(
        "inspect-usage-cost-analytics",
        help="Inspect redacted runtime usage and cost accounting posture.",
    )
    usage_cost_analytics.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime usage and cost read model as JSON.",
    )
    usage_cost_analytics.set_defaults(func=_inspect_usage_cost_analytics)

    prompt_stability_tiers = subparsers.add_parser(
        "inspect-prompt-stability-tiers",
        help="Inspect read-only prompt/input stability tier posture.",
    )
    prompt_stability_tiers.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref prompt stability tier read model as JSON.",
    )
    prompt_stability_tiers.set_defaults(func=_inspect_prompt_stability_tiers)

    context_budget_pressure = subparsers.add_parser(
        "inspect-context-budget-pressure",
        help="Inspect read-only context budget pressure and compression posture.",
    )
    context_budget_pressure.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref context budget pressure read model as JSON.",
    )
    context_budget_pressure.set_defaults(func=_inspect_context_budget_pressure)

    hardline_command_blocklist = subparsers.add_parser(
        "inspect-hardline-command-blocklist",
        help="Inspect the read-only non-overridable command deny floor.",
    )
    hardline_command_blocklist.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref hardline command blocklist read model as JSON.",
    )
    hardline_command_blocklist.set_defaults(func=_inspect_hardline_command_blocklist)

    managed_scope_policy = subparsers.add_parser(
        "inspect-managed-scope-policy",
        help="Inspect read-only local managed scope policy posture.",
    )
    managed_scope_policy.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref managed scope policy read model as JSON.",
    )
    managed_scope_policy.set_defaults(func=_inspect_managed_scope_policy)

    doctor_diagnostics = subparsers.add_parser(
        "inspect-doctor-diagnostics",
        help="Inspect redacted local runtime doctor diagnostics posture.",
    )
    doctor_diagnostics.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime doctor diagnostics read model as JSON.",
    )
    doctor_diagnostics.set_defaults(func=_inspect_doctor_diagnostics)

    session_continuity = subparsers.add_parser(
        "inspect-session-continuity",
        help="Inspect read-only multi-surface runtime session continuity posture.",
    )
    session_continuity.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref session continuity read model as JSON.",
    )
    session_continuity.set_defaults(func=_inspect_session_continuity)

    mcp_catalog_filtering = subparsers.add_parser(
        "inspect-mcp-catalog-filtering",
        help="Inspect MCP catalog metadata filters without installing or invoking tools.",
    )
    mcp_catalog_filtering.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref MCP catalog filtering read model as JSON.",
    )
    mcp_catalog_filtering.set_defaults(func=_inspect_mcp_catalog_filtering)

    background_jobs = subparsers.add_parser(
        "inspect-background-jobs",
        help="Inspect durable background job proposals without scheduler execution.",
    )
    background_jobs.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref background job posture as JSON.",
    )
    background_jobs.set_defaults(func=_inspect_background_jobs)

    subagent_isolation = subparsers.add_parser(
        "inspect-subagent-isolation",
        help="Inspect subagent role isolation posture without live dispatch.",
    )
    subagent_isolation.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref subagent isolation posture as JSON.",
    )
    subagent_isolation.set_defaults(func=_inspect_subagent_isolation)

    worktree_per_agent = subparsers.add_parser(
        "inspect-worktree-per-agent",
        help="Inspect worktree-per-agent posture without Git or file mutation.",
    )
    worktree_per_agent.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref worktree-per-agent posture as JSON.",
    )
    worktree_per_agent.set_defaults(func=_inspect_worktree_per_agent)

    lsp_diagnostics = subparsers.add_parser(
        "inspect-lsp-diagnostics",
        help="Inspect semantic diagnostic evidence posture without LSP execution.",
    )
    lsp_diagnostics.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref LSP diagnostics posture as JSON.",
    )
    lsp_diagnostics.set_defaults(func=_inspect_lsp_diagnostics)

    preview_rail = subparsers.add_parser(
        "inspect-preview-rail",
        help="Inspect safe-ref preview rail posture without rendering raw payloads.",
    )
    preview_rail.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref preview rail posture as JSON.",
    )
    preview_rail.set_defaults(func=_inspect_preview_rail)

    slash_command_registry = subparsers.add_parser(
        "inspect-slash-command-registry",
        help="Inspect governed slash command metadata without execution.",
    )
    slash_command_registry.add_argument(
        "--json",
        action="store_true",
        help="Emit the governed slash command registry as JSON.",
    )
    slash_command_registry.set_defaults(func=_inspect_slash_command_registry)

    interrupt_redirect = subparsers.add_parser(
        "inspect-interrupt-redirect",
        help="Inspect run-control interrupt and redirect posture without mutation.",
    )
    interrupt_redirect.add_argument(
        "--json",
        action="store_true",
        help="Emit the interrupt/redirect run-control posture as JSON.",
    )
    interrupt_redirect.set_defaults(func=_inspect_interrupt_redirect)

    logging_profile = subparsers.add_parser(
        "inspect-logging-profile",
        help="Inspect governed logging profile posture without toggling verbosity.",
    )
    logging_profile.add_argument(
        "--json",
        action="store_true",
        help="Emit the governed logging profile posture as JSON.",
    )
    logging_profile.set_defaults(func=_inspect_logging_profile)

    result_classification = subparsers.add_parser(
        "inspect-result-classification",
        help="Inspect runtime result taxonomy without promoting output authority.",
    )
    result_classification.add_argument(
        "--json",
        action="store_true",
        help="Emit the runtime result taxonomy as JSON.",
    )
    result_classification.set_defaults(func=_inspect_result_classification)

    voice_media_posture = subparsers.add_parser(
        "inspect-voice-media-posture",
        help="Inspect voice/media runtime posture without media access or generation.",
    )
    voice_media_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the runtime voice/media posture as JSON.",
    )
    voice_media_posture.set_defaults(func=_inspect_voice_media_posture)

    messaging_gateway_posture = subparsers.add_parser(
        "inspect-messaging-gateway-posture",
        help="Inspect messaging gateway readiness without connector runtime.",
    )
    messaging_gateway_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the messaging gateway posture as JSON.",
    )
    messaging_gateway_posture.set_defaults(func=_inspect_messaging_gateway_posture)

    remote_execution_posture = subparsers.add_parser(
        "inspect-remote-execution-posture",
        help="Inspect execution backend posture without remote execution.",
    )
    remote_execution_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the remote execution backend posture as JSON.",
    )
    remote_execution_posture.set_defaults(func=_inspect_remote_execution_posture)

    plugin_metadata_posture = subparsers.add_parser(
        "inspect-plugin-metadata-posture",
        help="Inspect plugin architecture metadata without runtime import.",
    )
    plugin_metadata_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the plugin metadata posture as JSON.",
    )
    plugin_metadata_posture.set_defaults(func=_inspect_plugin_metadata_posture)

    skill_marketplace_posture = subparsers.add_parser(
        "inspect-skill-marketplace-posture",
        help="Inspect external skill marketplace adoption posture without execution.",
    )
    skill_marketplace_posture.add_argument(
        "--json",
        action="store_true",
        help="Emit the skill marketplace posture as JSON.",
    )
    skill_marketplace_posture.set_defaults(func=_inspect_skill_marketplace_posture)

    session_search = subparsers.add_parser(
        "inspect-session-search",
        help="Inspect safe-ref session/run search separate from durable memory.",
    )
    session_search.add_argument("--query-ref", default=None)
    session_search.add_argument("--limit", type=int, default=20)
    session_search.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref session search read model as JSON.",
    )
    session_search.set_defaults(func=_inspect_session_search)

    session_lineage = subparsers.add_parser(
        "inspect-session-lineage",
        help="Inspect safe-ref session lineage and fork posture without dispatch.",
    )
    session_lineage.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref session lineage read model as JSON.",
    )
    session_lineage.set_defaults(func=_inspect_session_lineage)

    context_references = subparsers.add_parser(
        "inspect-context-references",
        help="Inspect governed context reference preview without live fetch or injection.",
    )
    context_references.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref context reference read model as JSON.",
    )
    context_references.set_defaults(func=_inspect_context_references)

    checkpoint_rollback = subparsers.add_parser(
        "inspect-checkpoint-rollback",
        help="Inspect checkpoint and rollback posture without executing rollback.",
    )
    checkpoint_rollback.add_argument(
        "--json",
        action="store_true",
        help="Emit checkpoint and rollback posture as JSON.",
    )
    checkpoint_rollback.set_defaults(func=_inspect_checkpoint_rollback)

    run_events = subparsers.add_parser(
        "inspect-run-events",
        help="Inspect runtime run/event/approval-wait posture without mutation.",
    )
    run_events.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime run events read model as JSON.",
    )
    run_events.set_defaults(func=_inspect_run_events)

    approval_bridge = subparsers.add_parser(
        "inspect-approval-bridge",
        help="Inspect runtime approval bridge posture without sending decisions.",
    )
    approval_bridge.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime approval bridge read model as JSON.",
    )
    approval_bridge.set_defaults(func=_inspect_approval_bridge)

    streaming_progress = subparsers.add_parser(
        "inspect-streaming-progress",
        help="Inspect redacted runtime streaming progress previews without live transport.",
    )
    streaming_progress.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime streaming progress read model as JSON.",
    )
    streaming_progress.set_defaults(func=_inspect_streaming_progress)

    profiles = subparsers.add_parser(
        "inspect-profiles",
        help="Inspect isolated runtime profile metadata without changing config.",
    )
    profiles.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref runtime profile isolation read model as JSON.",
    )
    profiles.set_defaults(func=_inspect_profiles)

    bridge = subparsers.add_parser(
        "inspect-action-inbox-bridge",
        help="Inspect the runtime Action Inbox execution bridge read model.",
    )
    bridge.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref read model as JSON for automation.",
    )
    bridge.set_defaults(func=_inspect_action_inbox_bridge)

    parity_loop = subparsers.add_parser(
        "inspect-parity-loop",
        help="Inspect the complete runtime parity loop across cockpit, CLI, and API refs.",
    )
    parity_loop.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe-ref parity loop read model as JSON.",
    )
    parity_loop.set_defaults(func=_inspect_parity_loop)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
