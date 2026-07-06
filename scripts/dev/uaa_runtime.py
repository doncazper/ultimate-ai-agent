#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.control_center.runtime_action_bridge import (  # noqa: E402
    build_runtime_action_inbox_bridge_read_model,
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
    build_portable_evidence_envelope,
    build_default_runtime_capabilities,
    build_governed_product_pilot_authority_profile,
    build_runtime_approval_bridge_read_model,
    build_runtime_capability_discovery_read_model,
    build_runtime_delegation_adapter_read_model,
    build_runtime_profile_isolation_read_model,
    build_runtime_run_events_read_model,
    build_runtime_session_search_read_model,
    build_runtime_streaming_progress_read_model,
    build_runtime_tool_registry_availability_read_model,
    build_runtime_action_signed_evidence,
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
    print("Authority: exact focused pytest bridge only; broad runtime remains blocked")
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
    print("Promoted exact authority:")
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


def _print_capability_discovery(read_model: dict[str, Any]) -> None:
    print("Runtime capability discovery")
    print(f"Status: {read_model['status']}")
    print(f"Runtime: {read_model['runtime_label']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
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


def _print_session_search(read_model: dict[str, Any]) -> None:
    print("Runtime session/run search")
    print(f"Status: {read_model['status']}")
    print(f"Snapshot: {read_model['snapshot_ref']}")
    print(f"Snapshot hash: {read_model['snapshot_hash_ref']}")
    print(f"Route: {read_model['route_ref']}")
    print(f"CLI: {read_model['cli_ref']}")
    print(f"Query ref: {read_model['query_ref']}")
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
    if args.state_dir is None:
        return RuntimeInvocationStore()
    return RuntimeInvocationStore(Path(args.state_dir))


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


def _inspect_capability_discovery(args: argparse.Namespace) -> int:
    read_model = build_runtime_capability_discovery_read_model().model_dump(mode="json")
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
    read_model = build_runtime_tool_registry_availability_read_model().model_dump(
        mode="json"
    )
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
    print("Execution still requires a later exact RuntimeGateway execute request.")
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
    read_model = build_sample_staged_orchestration_read_model()
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

    authority_profile = subparsers.add_parser(
        "authority-profile",
        help="Inspect the Governed Product Pilot authority profile.",
    )
    authority_profile.add_argument(
        "--json", action="store_true", help="Emit safe JSON."
    )
    authority_profile.set_defaults(func=_authority_profile)

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
                "requires a later exact RuntimeGateway execute request."
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
