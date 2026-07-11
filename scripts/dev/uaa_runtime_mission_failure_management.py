from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from ultimate_ai_agent.core.authority.contracts import authority_state_dir
from ultimate_ai_agent.core.approvals.decisions import ApprovalValidationRequest
from ultimate_ai_agent.core.execution.durable_mission_controls import (
    MissionControlConflictError,
    MissionControlCorruptionError,
    MissionControlEvent,
    MissionControlRequest,
)
from ultimate_ai_agent.core.execution.mission_failure_management import (
    AuthorityMissionFailureManagementService,
    MissionApprovalDecision,
    MissionApprovalDecisionRequest,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepConflictError,
    MissionStepCorruptionError,
)


def _request(args: argparse.Namespace, event: MissionControlEvent) -> MissionControlRequest:
    return MissionControlRequest(
        control_ref=args.control_ref,
        event=event,
        plan_ref=args.plan_ref,
        plan_fingerprint_ref=args.plan_fingerprint_ref,
        mission_ref=args.mission_ref,
        run_ref=args.run_ref,
        lease_ref=args.lease_ref,
        idempotency_ref=args.idempotency_ref,
        reason_ref=args.reason_ref,
        dead_letter_step_ref=getattr(args, "dead_letter_step_ref", None),
        dead_letter_receipt_ref=getattr(args, "dead_letter_receipt_ref", None),
        dead_letter_entry_hash_ref=getattr(
            args,
            "dead_letter_entry_hash_ref",
            None,
        ),
        safe_summary=args.summary,
    )


def _run(args: argparse.Namespace, *, dead_letter_recovery: bool) -> int:
    state_dir = Path(args.state_dir) if args.state_dir else authority_state_dir()
    service = AuthorityMissionFailureManagementService(state_dir)
    event = (
        MissionControlEvent.dead_letter_recovery_requested
        if dead_letter_recovery
        else MissionControlEvent.cancellation_requested
    )
    try:
        request = _request(args, event)
        result = (
            service.request_dead_letter_recovery(request)
            if dead_letter_recovery
            else service.cancel(request)
        )
    except (
        MissionControlConflictError,
        MissionControlCorruptionError,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        print(
            f"Authority mission control denied: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1
    payload = result.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print("Authority mission control")
    print(f"Event: {payload['event']}")
    print(f"Status: {payload['status']}")
    print(f"Receipt: {payload['control_receipt_ref']}")
    print(f"Evidence hash: {payload['control_entry_hash_ref']}")
    print("Execution performed: false")
    print("Execution authority granted: false")
    print("Fresh request-scoped authority remains required: true")
    return 0


def cancel(args: argparse.Namespace) -> int:
    return _run(args, dead_letter_recovery=False)


def request_dead_letter_recovery(args: argparse.Namespace) -> int:
    return _run(args, dead_letter_recovery=True)


def record_approval_decision(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir) if args.state_dir else authority_state_dir()
    try:
        payload = (
            sys.stdin.read()
            if args.validation_request_file == "-"
            else Path(args.validation_request_file).read_text(encoding="utf-8")
        )
        validation = ApprovalValidationRequest.model_validate_json(payload)
        result = AuthorityMissionFailureManagementService(state_dir).resolve_approval(
            MissionApprovalDecisionRequest(
                step_ref=args.step_ref,
                approval_request_ref=args.approval_request_ref,
                approval_ref=args.approval_ref,
                approval_scope_fingerprint_ref=(
                    args.approval_scope_fingerprint_ref
                ),
                approval_validation_request=validation,
                decision=MissionApprovalDecision(args.decision),
                operator_ref=args.operator_ref,
                idempotency_ref=args.idempotency_ref,
                reason_ref=args.reason_ref,
                safe_summary=args.summary,
            )
        )
    except (
        MissionControlConflictError,
        MissionControlCorruptionError,
        MissionStepConflictError,
        MissionStepCorruptionError,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        print(
            f"Authority mission approval decision denied: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 1
    payload = result.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print("Authority mission approval decision")
    print(f"Decision: {payload['decision']}")
    print(f"Status: {payload['status']}")
    print(f"Receipt: {payload['control_receipt_ref']}")
    print(f"Evidence hash: {payload['control_entry_hash_ref']}")
    print("Execution performed: false")
    print("Execution authority granted: false")
    print("Worker-side fresh exact approval validation required: true")
    return 0


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--control-ref", required=True)
    parser.add_argument("--plan-ref", required=True)
    parser.add_argument("--plan-fingerprint-ref", required=True)
    parser.add_argument("--mission-ref", required=True)
    parser.add_argument("--run-ref", required=True)
    parser.add_argument("--lease-ref", required=True)
    parser.add_argument("--idempotency-ref", required=True)
    parser.add_argument("--reason-ref", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--json", action="store_true")


def register_parser(subparsers: object) -> None:
    cancel_parser = subparsers.add_parser(
        "cancel-authority-mission",
        help="Append one exact mission cancellation fence without executing work.",
    )
    _common_arguments(cancel_parser)
    cancel_parser.set_defaults(func=cancel)

    recovery_parser = subparsers.add_parser(
        "request-authority-mission-dead-letter-recovery",
        help="Record an explicit recovery intent without replaying dead-lettered work.",
    )
    _common_arguments(recovery_parser)
    recovery_parser.add_argument("--dead-letter-step-ref", required=True)
    recovery_parser.add_argument("--dead-letter-receipt-ref", required=True)
    recovery_parser.add_argument("--dead-letter-entry-hash-ref", required=True)
    recovery_parser.set_defaults(func=request_dead_letter_recovery)

    approval_parser = subparsers.add_parser(
        "record-authority-mission-approval-decision",
        help=(
            "Record exact approval evidence; the worker must still freshly validate "
            "authority before execution."
        ),
    )
    approval_parser.add_argument("--step-ref", required=True)
    approval_parser.add_argument("--approval-request-ref", required=True)
    approval_parser.add_argument("--approval-ref", required=True)
    approval_parser.add_argument(
        "--approval-scope-fingerprint-ref",
        required=True,
    )
    approval_parser.add_argument(
        "--decision",
        choices=[item.value for item in MissionApprovalDecision],
        required=True,
    )
    approval_parser.add_argument("--operator-ref", required=True)
    approval_parser.add_argument(
        "--validation-request-file",
        required=True,
        help="Secret-clean typed validation JSON file, or '-' for stdin.",
    )
    approval_parser.add_argument("--idempotency-ref", required=True)
    approval_parser.add_argument("--reason-ref", required=True)
    approval_parser.add_argument("--summary", required=True)
    approval_parser.add_argument("--json", action="store_true")
    approval_parser.set_defaults(func=record_approval_decision)
