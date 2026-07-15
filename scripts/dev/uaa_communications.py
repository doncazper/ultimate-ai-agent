#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.communications import (  # noqa: E402
    CommunicationsReceiptNotFound,
    CommunicationsService,
    build_default_communications_service,
)
from ultimate_ai_agent.core.approvals import LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.authority import (  # noqa: E402
    AuthorityLeaseStore,
    authority_lease_kill_switch_engaged,
)
from ultimate_ai_agent.core.communications.matrix_harness import (  # noqa: E402
    MATRIX_HARNESS_LANES,
    DockerMatrixHarnessBackend,
    MatrixHarnessAuthorityDispatchAdapter,
    MatrixHarnessCommand,
    MatrixHarnessOperation,
    build_matrix_harness_dispatch_request,
    capture_exact_matrix_harness_approval,
    default_matrix_harness_backend_config,
    execute_matrix_harness_command,
    issue_exact_matrix_harness_lease,
    matrix_harness_request_fingerprint_ref,
    stable_matrix_harness_ref,
)
from ultimate_ai_agent.core.communications.matrix_session import (  # noqa: E402
    MATRIX_DISCOVERY_PENDING_FRESHNESS_REF,
    MATRIX_DISCOVERY_PENDING_OBSERVATION_REF,
    MATRIX_SESSION_LANES,
    MatrixSessionCommand,
    MatrixSessionOperation,
    MatrixSessionTransientInput,
    capture_exact_matrix_session_approval,
    execute_matrix_session_command,
    issue_exact_matrix_session_lease,
    matrix_homeserver_ref,
    matrix_redirect_target_ref,
    matrix_session_request_fingerprint_ref,
    stable_matrix_session_ref,
)
from ultimate_ai_agent.core.communications.matrix_sync import (  # noqa: E402
    build_default_matrix_sync_posture,
)
from ultimate_ai_agent.core.time import utc_now  # noqa: E402


def _json(value: Any) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    elif isinstance(value, tuple):
        value = [item.model_dump(mode="json") for item in value]
    print(json.dumps(value, indent=2, sort_keys=True))


def _render_providers(service: CommunicationsService, as_json: bool) -> int:
    providers = service.inspect_provider_posture()
    if as_json:
        _json(providers)
        return 0
    print("Communications providers")
    for provider in providers:
        availability = provider.availability
        print(f"- {provider.provider_ref}: {provider.provider_status.value}")
        print(f"  Adapter: {provider.adapter_ref}")
        print(f"  Runtime readiness: {availability.runtime_readiness_status.value}")
        print(f"  Authority: {availability.authority_posture.value}")
        print(f"  Blockers: {', '.join(provider.blocker_codes)}")
    print("No provider network operation was performed.")
    return 0


def _render_session(service: CommunicationsService, as_json: bool) -> int:
    posture = service.inspect_session_posture()
    if as_json:
        _json(posture)
        return 0
    print("Communications session")
    print(f"- Provider: {posture.provider_ref}")
    print(f"- Status: {posture.status.value}")
    print(f"- Freshness: {posture.freshness.value}")
    print(f"- Blockers: {', '.join(posture.blocker_codes)}")
    print("No authentication or synchronization was performed.")
    return 0


def _render_rooms(service: CommunicationsService, as_json: bool, limit: int) -> int:
    page = service.list_rooms(limit=limit)
    if as_json:
        _json(page)
        return 0
    print("Communications rooms")
    print(f"- Returned: {page.pagination.returned_count}")
    print(f"- Freshness: {page.freshness.value}")
    print(f"- Blockers: {', '.join(page.blocker_codes)}")
    print("No message content was read.")
    return 0


def _render_failed_sends(
    service: CommunicationsService, as_json: bool, limit: int
) -> int:
    page = service.list_failed_sends(limit=limit)
    if as_json:
        _json(page)
        return 0
    print("Communications failed sends")
    print(f"- Returned: {page.pagination.returned_count}")
    print(f"- Blockers: {', '.join(page.blocker_codes)}")
    print("No send runtime exists and no send was performed.")
    return 0


def _render_security(service: CommunicationsService, as_json: bool) -> int:
    posture = service.inspect_security_posture()
    if as_json:
        _json(posture)
        return 0
    print("Communications security posture")
    print(f"- Encryption: {posture.encryption_posture_ref}")
    print(f"- Key lifecycle: {posture.key_lifecycle_posture_ref}")
    print(f"- Cache: {posture.cache_posture_ref}")
    print(f"- Blockers: {', '.join(posture.blocker_codes)}")
    print("No credentials, crypto runtime, or local cache were opened.")
    return 0


def _render_matrix_sync_posture(as_json: bool) -> int:
    posture = build_default_matrix_sync_posture()
    if as_json:
        _json(posture)
        return 0
    print("Matrix read-only sync")
    print(f"- Runtime: {posture.runtime_status.value}")
    print(f"- Freshness: {posture.freshness.value}")
    print(f"- Declared authority lanes: {len(posture.authority_lane_refs)}")
    print(
        "- Concrete GET transports: "
        f"{len(posture.concrete_transport_operation_refs)}"
    )
    print(
        "- Uncomposed exact executors: "
        f"{len(posture.uncomposed_executor_operation_refs)}"
    )
    print(f"- Blockers: {', '.join(posture.blocker_refs)}")
    print("- External writes: denied")
    print("- Message sends: denied")
    print("- Encrypted events: placeholder only until MSG-MX-007")
    print("No credential, message content, provider payload, or local path is shown.")
    return 0


def _render_receipt(
    service: CommunicationsService, as_json: bool, receipt_ref: str
) -> int:
    try:
        receipt = service.lookup_receipt(receipt_ref)
    except CommunicationsReceiptNotFound:
        print("Communications receipt not found (reference-only diagnostic).")
        return 2
    if as_json:
        _json(receipt)
        return 0
    print("Communications receipt")
    print(f"- Receipt: {receipt.receipt_ref}")
    print(f"- Outcome: {receipt.outcome.value}")
    print(f"- Provider: {receipt.provider_ref}")
    print(f"- Blockers: {', '.join(receipt.blocker_codes)}")
    print("Receipt is content-free; no provider operation was performed.")
    return 0


def _matrix_harness_command(
    args: argparse.Namespace,
    backend: DockerMatrixHarnessBackend | None = None,
) -> MatrixHarnessCommand:
    operation = MatrixHarnessOperation(args.harness_operation.replace("-", "_"))
    if args.deadline_seconds < 10 or args.deadline_seconds > 300:
        raise ValueError("MATRIX_HARNESS_DEADLINE_OUT_OF_RANGE")
    if args.confirm and not MATRIX_HARNESS_LANES[operation].approval_required:
        raise ValueError("MATRIX_HARNESS_READ_CONFIRMATION_FORBIDDEN")
    start_deadline = utc_now() + timedelta(seconds=args.deadline_seconds)
    lifecycle = None
    if not args.lifecycle_generation_ref or not args.expected_state_ref:
        selected_backend = backend or DockerMatrixHarnessBackend(
            default_matrix_harness_backend_config(ROOT),
            kill_switch_engaged=authority_lease_kill_switch_engaged,
        )
        lifecycle = selected_backend.lifecycle_record()
    lease_ref = args.lease_ref or stable_matrix_harness_ref(
        "authority-lease-ref:matrix-harness:requested",
        {
            "operation": operation.value,
            "mission_ref": args.mission_ref,
            "run_ref": args.run_ref,
            "idempotency_ref": args.idempotency_ref,
        },
    )
    values = {
        "operation": operation,
        "request_ref": args.request_ref,
        "task_ref": args.task_ref,
        "mission_ref": args.mission_ref,
        "run_ref": args.run_ref,
        "dispatch_ref": args.dispatch_ref,
        "idempotency_ref": args.idempotency_ref,
        "lease_ref": lease_ref,
        "lifecycle_generation_ref": (
            args.lifecycle_generation_ref
            or (lifecycle.generation_ref if lifecycle is not None else "")
        ),
        "expected_state_ref": (
            args.expected_state_ref
            or (lifecycle.state_ref if lifecycle is not None else "")
        ),
        "start_deadline": start_deadline,
    }
    values["request_fingerprint_ref"] = matrix_harness_request_fingerprint_ref(**values)
    return MatrixHarnessCommand(**values)


def _run_matrix_harness(args: argparse.Namespace) -> int:
    try:
        store = AuthorityLeaseStore()
        approvals = LocalApprovalAuthority()
        backend = DockerMatrixHarnessBackend(
            default_matrix_harness_backend_config(ROOT),
            kill_switch_engaged=authority_lease_kill_switch_engaged,
        )
        command = _matrix_harness_command(args, backend)
        lane = MATRIX_HARNESS_LANES[command.operation]
        if args.issue_exact_lease:
            issue_exact_matrix_harness_lease(
                command,
                store=store,
                confirmed=args.confirm,
            )
        approval_ref = None
        if lane.approval_required and args.confirm:
            adapter = MatrixHarnessAuthorityDispatchAdapter(
                operation=command.operation,
                backend=backend,
                authority_leases_provider=lambda: store.list_leases(active_only=False),
            )
            approval_ref = capture_exact_matrix_harness_approval(
                build_matrix_harness_dispatch_request(command, adapter=adapter),
                approval_authority=approvals,
                confirmed=True,
            )
        result = execute_matrix_harness_command(
            command,
            repo_root=ROOT,
            authority_state_dir=store.state_dir,
            approval_ref=approval_ref,
            backend=backend,
            lease_store=store,
            approval_authority=approvals,
        )
    except (OSError, RuntimeError, ValueError):
        print("Matrix harness operation blocked (reference-only diagnostic).")
        return 2
    if args.json:
        _json(result)
    else:
        print("Disposable Matrix harness")
        print(f"- Operation: {command.operation.value}")
        print(f"- Dispatch status: {result.receipt.status}")
        print(f"- Receipt: {result.receipt.receipt_ref}")
        print(f"- Reasons: {', '.join(result.receipt.reason_refs) or 'none'}")
        evidence_refs = (
            result.adapter_result.evidence_refs
            if result.adapter_result is not None
            else result.receipt.evidence_refs
        )
        print(f"- Evidence: {', '.join(evidence_refs) or 'none'}")
        safe_output = (
            result.adapter_result.safe_output
            if result.adapter_result is not None
            else {}
        )
        if safe_output.get("lifecycle_generation_ref"):
            print(f"- Next generation: {safe_output['lifecycle_generation_ref']}")
            print(f"- Next state: {safe_output['lifecycle_state_ref']}")
        print("No raw output, credentials, message content, or local paths are shown.")
    return 0 if result.receipt.status == "succeeded" else 2


def _matrix_session_command(args: argparse.Namespace) -> MatrixSessionCommand:
    operation = MatrixSessionOperation(args.session_operation.replace("-", "_"))
    if args.deadline_seconds < 10 or args.deadline_seconds > 300:
        raise ValueError("MATRIX_SESSION_DEADLINE_OUT_OF_RANGE")
    lane = MATRIX_SESSION_LANES[operation]
    if args.confirm and not lane.approval_required:
        raise ValueError("MATRIX_SESSION_READ_CONFIRMATION_FORBIDDEN")
    request_created_at = utc_now()
    start_deadline = request_created_at + timedelta(seconds=args.deadline_seconds)
    endpoint = args.discovery_origin or args.homeserver_url
    if endpoint is None:
        raise ValueError("MATRIX_SESSION_TRANSIENT_TARGET_REQUIRED")
    endpoint_class_ref = (
        "endpoint-class-ref:matrix:local-harness"
        if endpoint == "http://127.0.0.1:18008"
        else "endpoint-class-ref:matrix:public-https"
    )
    lease_ref = args.lease_ref or stable_matrix_session_ref(
        "authority-lease-ref:matrix-session:requested",
        {
            "operation": operation.value,
            "mission_ref": args.mission_ref,
            "run_ref": args.run_ref,
            "idempotency_ref": args.idempotency_ref,
        },
    )
    values: dict[str, object] = {
        "operation": operation,
        "request_ref": args.request_ref,
        "task_ref": args.task_ref,
        "mission_ref": args.mission_ref,
        "run_ref": args.run_ref,
        "dispatch_ref": args.dispatch_ref,
        "idempotency_ref": args.idempotency_ref,
        "lease_ref": lease_ref,
        "homeserver_ref": matrix_homeserver_ref(endpoint),
        "endpoint_class_ref": endpoint_class_ref,
        "discovery_observation_ref": (
            MATRIX_DISCOVERY_PENDING_OBSERVATION_REF
            if operation == MatrixSessionOperation.discovery_read
            else args.discovery_observation_ref
        ),
        "discovery_freshness_ref": (
            MATRIX_DISCOVERY_PENDING_FRESHNESS_REF
            if operation == MatrixSessionOperation.discovery_read
            else args.discovery_freshness_ref
        ),
        "account_ref": args.account_ref,
        "device_ref": args.device_ref,
        "session_ref": args.session_ref,
        "session_generation_ref": args.session_generation_ref,
        "credential_item_ref": args.credential_item_ref,
        "credential_version_ref": args.credential_version_ref,
        "next_credential_version_ref": args.next_credential_version_ref,
        "crypto_store_ref": args.crypto_store_ref,
        "callback_attempt_ref": args.callback_attempt_ref,
        "target_refs": tuple(args.target_ref),
        "readiness_ref": args.readiness_ref,
        "request_created_at": request_created_at,
        "start_deadline": start_deadline,
    }
    if args.callback_url:
        values["redirect_target_ref"] = matrix_redirect_target_ref(args.callback_url)
    values["request_fingerprint_ref"] = matrix_session_request_fingerprint_ref(**values)
    return MatrixSessionCommand(**values)


def _run_matrix_session(args: argparse.Namespace) -> int:
    try:
        command = _matrix_session_command(args)
        store = AuthorityLeaseStore()
        approvals = LocalApprovalAuthority()
        if args.issue_exact_lease:
            issue_exact_matrix_session_lease(
                command,
                store=store,
                confirmed=args.confirm,
            )
        approval_ref = None
        if MATRIX_SESSION_LANES[command.operation].approval_required and args.confirm:
            approval_ref = capture_exact_matrix_session_approval(
                command,
                approval_authority=approvals,
                confirmed=True,
            )
        result = execute_matrix_session_command(
            command,
            repo_root=ROOT,
            authority_state_dir=store.state_dir,
            transient_input=MatrixSessionTransientInput(
                endpoint_url=args.homeserver_url,
                discovery_origin=args.discovery_origin,
                callback_url=args.callback_url,
            ),
            approval_ref=approval_ref,
            lease_store=store,
            approval_authority=approvals,
        )
    except (OSError, RuntimeError, ValueError):
        print("Matrix session operation blocked (reference-only diagnostic).")
        return 2
    if args.json:
        _json(result)
    else:
        print("Governed Matrix session")
        print(f"- Operation: {command.operation.value}")
        print(f"- Dispatch status: {result.receipt.status}")
        print(f"- Receipt: {result.receipt.receipt_ref}")
        print(f"- Reasons: {', '.join(result.receipt.reason_refs) or 'none'}")
        evidence = (
            result.adapter_result.evidence_refs
            if result.adapter_result is not None
            else result.receipt.evidence_refs
        )
        print(f"- Evidence: {', '.join(evidence) or 'none'}")
        print(
            "No credentials, provider payloads, raw logs, message content, or local paths are shown."
        )
    return 0 if result.receipt.status == "succeeded" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect communications contracts and run only the exact governed "
            "disposable local Matrix harness lanes."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("providers", "session", "security"):
        command = subparsers.add_parser(name)
        command.add_argument("--json", action="store_true", help="Emit safe JSON.")
    sync_posture = subparsers.add_parser(
        "matrix-sync-status",
        help="Inspect backend-owned Matrix read-only sync and cache posture.",
    )
    sync_posture.add_argument("--json", action="store_true", help="Emit safe JSON.")
    for name in ("rooms", "failed-sends"):
        command = subparsers.add_parser(name)
        command.add_argument("--limit", type=int, default=25)
        command.add_argument("--json", action="store_true", help="Emit safe JSON.")
    receipt = subparsers.add_parser("receipt")
    receipt.add_argument("receipt_ref")
    receipt.add_argument("--json", action="store_true", help="Emit safe JSON.")
    harness = subparsers.add_parser(
        "harness",
        help="Run one exact lease-governed disposable Matrix harness operation.",
    )
    harness_subparsers = harness.add_subparsers(
        dest="harness_operation",
        required=True,
    )
    for operation in MatrixHarnessOperation:
        command = harness_subparsers.add_parser(
            operation.value.replace("_", "-"),
            help=f"Run the exact {operation.value} lane; see the local harness runbook.",
        )
        command.add_argument("--request-ref", required=True)
        command.add_argument("--task-ref", required=True)
        command.add_argument("--mission-ref", required=True)
        command.add_argument("--run-ref", required=True)
        command.add_argument("--dispatch-ref", required=True)
        command.add_argument("--idempotency-ref", required=True)
        command.add_argument("--lease-ref")
        command.add_argument("--lifecycle-generation-ref")
        command.add_argument("--expected-state-ref")
        command.add_argument(
            "--issue-exact-lease",
            action="store_true",
            help="Issue the command-bound mission lease through Python Core before dispatch.",
        )
        command.add_argument("--deadline-seconds", type=int, default=120)
        command.add_argument(
            "--confirm",
            action="store_true",
            help="Capture exact local approval for mutation lanes only.",
        )
        command.add_argument("--json", action="store_true", help="Emit safe JSON.")
    session = subparsers.add_parser(
        "matrix-session",
        help="Run one exact Matrix discovery/read lane or inspect a blocked mutation.",
    )
    session_subparsers = session.add_subparsers(
        dest="session_operation",
        required=True,
    )
    for operation in MatrixSessionOperation:
        command = session_subparsers.add_parser(operation.value.replace("_", "-"))
        for name in (
            "request-ref",
            "task-ref",
            "mission-ref",
            "run-ref",
            "dispatch-ref",
            "idempotency-ref",
            "readiness-ref",
        ):
            command.add_argument(f"--{name}", required=True)
        command.add_argument(
            "--discovery-observation-ref",
            required=operation != MatrixSessionOperation.discovery_read,
            default=MATRIX_DISCOVERY_PENDING_OBSERVATION_REF,
        )
        command.add_argument(
            "--discovery-freshness-ref",
            required=operation != MatrixSessionOperation.discovery_read,
            default=MATRIX_DISCOVERY_PENDING_FRESHNESS_REF,
        )
        command.add_argument("--lease-ref")
        command.add_argument("--homeserver-url")
        command.add_argument("--discovery-origin")
        command.add_argument("--callback-url")
        command.add_argument("--account-ref")
        command.add_argument("--device-ref")
        command.add_argument("--session-ref")
        command.add_argument("--session-generation-ref")
        command.add_argument("--credential-item-ref")
        command.add_argument("--credential-version-ref")
        command.add_argument("--next-credential-version-ref")
        command.add_argument("--crypto-store-ref")
        command.add_argument("--callback-attempt-ref")
        command.add_argument("--target-ref", action="append", default=[])
        command.add_argument("--issue-exact-lease", action="store_true")
        command.add_argument("--deadline-seconds", type=int, default=120)
        command.add_argument("--confirm", action="store_true")
        command.add_argument("--json", action="store_true", help="Emit safe JSON.")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    service: CommunicationsService | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    active_service = service or build_default_communications_service()
    if args.command == "harness":
        return _run_matrix_harness(args)
    if args.command == "matrix-session":
        return _run_matrix_session(args)
    if args.command == "providers":
        return _render_providers(active_service, args.json)
    if args.command == "session":
        return _render_session(active_service, args.json)
    if args.command == "rooms":
        return _render_rooms(active_service, args.json, args.limit)
    if args.command == "failed-sends":
        return _render_failed_sends(active_service, args.json, args.limit)
    if args.command == "security":
        return _render_security(active_service, args.json)
    if args.command == "matrix-sync-status":
        return _render_matrix_sync_posture(args.json)
    return _render_receipt(active_service, args.json, args.receipt_ref)


if __name__ == "__main__":
    raise SystemExit(main())
