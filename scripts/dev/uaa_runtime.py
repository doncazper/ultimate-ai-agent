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
from ultimate_ai_agent.core.execution import (  # noqa: E402
    build_sample_staged_orchestration_read_model,
    build_sample_turn_run_approval_chain,
)
from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RuntimeInvocationConflictError,
    RuntimeInvocationNotFoundError,
    RuntimeInvocationStore,
    build_portable_evidence_envelope,
    build_default_runtime_capabilities,
    build_governed_product_pilot_authority_profile,
    verify_portable_evidence_envelope,
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
    print(
        "Blocked: "
        + ", ".join(read_model["blocked_authority_refs"] or ["none"])
    )
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
    print(f"Sealed default preserved: {read_model['sealed_default_hard_rules_preserved']}")
    print(f"RuntimeGateway required: {read_model['runtime_gateway_required']}")
    print(f"Control Center mints authority: {read_model['control_center_mints_authority']}")
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
    print("Blocked authority refs: " + ", ".join(receipt.blocked_authority_refs or ["none"]))
    if receipt.command_receipt_metadata is not None:
        metadata = receipt.command_receipt_metadata
        print(f"Command status: {metadata.status_category}")
        print(f"Exit code: {metadata.exit_code if metadata.exit_code is not None else 'none'}")
        print(f"Timed out: {metadata.timed_out}")
        print(f"Output summary: {metadata.output_summary}")


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


def _status(args: argparse.Namespace) -> int:
    read_model = _read_model(_runtime_store(args))
    if args.json:
        _print_json(_runtime_payload(read_model, "repo-local-command:governed-runtime-status"))
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


def _portable_evidence_payload(command_ref: str, envelope: dict[str, Any]) -> dict[str, Any]:
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
        envelope_payload: dict[str, Any] = build_portable_evidence_envelope().model_dump(
            mode="json"
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


def _receipt_record_for_ref(store: RuntimeInvocationStore, receipt_ref: str) -> Any | None:
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
        "Blocked broad authority: "
        + ", ".join(payload["blocked_broad_authority_refs"])
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
                "receipt": record.receipt.model_dump(mode="json") if record.receipt else None,
                "invocation_ref": record.invocation_ref,
                "safe_refs_only": True,
                "raw_content_omitted": True,
                "raw_command_output_omitted": True,
            }
        )
    else:
        _print_receipt(record)
    return 0


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
        print(f"Turn: {chain.linkage.turn_ref.ref if chain.linkage.turn_ref else 'not_available'}")
        print(f"Run: {chain.linkage.durable_run_ref.ref}")
        print(f"Approval: {chain.linkage.approval_ref.ref if chain.linkage.approval_ref else 'not_available'}")
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
    authority_profile.add_argument("--json", action="store_true", help="Emit safe JSON.")
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
    invocations_list = invocation_subparsers.add_parser("list", help="List invocations.")
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
        decision_parser.add_argument("--json", action="store_true", help="Emit safe JSON.")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
