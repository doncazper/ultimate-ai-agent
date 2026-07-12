from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from ultimate_ai_agent.core.authority import (
    AuthorityLeaseStore,
    authority_lease_kill_switch_engaged,
)
from ultimate_ai_agent.core.runtime_gateway.storage import RuntimeInvocationStore
from ultimate_ai_agent.core.safe_refs import hash_text
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.sandbox_calculation.backend import (
    SealedCalculationBackendError,
    discover_local_docker_backend,
)
from ultimate_ai_agent.core.sandbox_calculation.mission import (
    SealedCalculationMissionRequest,
    SealedCalculationMissionService,
)
from ultimate_ai_agent.core.sandbox_calculation.adapter import (
    SEALED_CALCULATION_GRAMMAR_POLICY_REF,
)
from ultimate_ai_agent.core.sandbox_calculation.contracts import (
    SEALED_CALCULATION_ADAPTER_REF,
    SEALED_CALCULATION_CAPABILITY_REF,
    SEALED_CALCULATION_TARGET_REF,
)


ROOT = Path(__file__).resolve().parents[2]
SECCOMP_PROFILE = ROOT / "packaging" / "sealed-calculation" / "seccomp.json"


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    sealed = subparsers.add_parser(
        "sealed-calculation",
        help="Run one exact arithmetic expression from stdin under a mission lease.",
    )
    commands = sealed.add_subparsers(dest="sealed_calculation_command", required=True)
    inspect = commands.add_parser(
        "inspect",
        help="Inspect current local backend readiness without executing.",
    )
    inspect.add_argument("--json", action="store_true", help="Emit safe JSON.")
    inspect.set_defaults(func=_inspect)

    prepare = commands.add_parser(
        "prepare",
        help="Hash one stdin expression and print exact safe lease resource refs.",
    )
    prepare.add_argument("--input-ref", required=True, help="Safe transient input ref.")
    prepare.add_argument("--mission-ref", required=True, help="Exact mission ref.")
    prepare.add_argument("--json", action="store_true", help="Emit safe JSON.")
    prepare.set_defaults(func=_prepare)

    run = commands.add_parser(
        "run",
        help="Read one bounded expression from stdin and execute the exact leased lane.",
    )
    for argument in (
        "request-ref",
        "input-ref",
        "plan-ref",
        "mission-ref",
        "run-ref",
        "step-ref",
        "lease-ref",
        "owner-ref",
    ):
        run.add_argument(f"--{argument}", required=True, help=f"Safe {argument}.")
    run.add_argument(
        "--request-created-at",
        required=True,
        help="Timezone-aware ISO request creation time, reused unchanged for replay.",
    )
    run.add_argument(
        "--start-deadline",
        required=True,
        help="Timezone-aware ISO start deadline, reused unchanged for exact replay.",
    )
    run.add_argument("--json", action="store_true", help="Emit safe JSON.")
    run.set_defaults(func=_run)


def _discover(state_dir: Path | None = None):
    runtime_store = RuntimeInvocationStore(state_dir)
    return discover_local_docker_backend(
        seccomp_profile=SECCOMP_PROFILE,
        kill_switch=authority_lease_kill_switch_engaged,
        safe_disabled=runtime_store.operator_safe_disable_active,
    )


def _inspect(args: argparse.Namespace) -> int:
    try:
        state_dir = Path(args.state_dir) if args.state_dir else None
        backend = _discover(state_dir)
    except (SealedCalculationBackendError, ValueError) as exc:
        payload = {
            "schema_version": "uaa-sealed-calculation-cli.v1",
            "status": "configuration_required",
            "reason_code": _safe_backend_reason(exc),
            "execution_performed": False,
            "safe_summary": "Sealed calculation backend is not currently available.",
        }
    else:
        reasons = backend.readiness_reason_codes()
        payload = {
            "schema_version": "uaa-sealed-calculation-cli.v1",
            "status": "ready_for_exact_lease_evaluation" if not reasons else "blocked",
            "attestation_ref": backend.attestation.attestation_ref,
            "image_id_ref": backend.attestation.image_id_ref,
            "limits_ref": backend.attestation.limits_ref,
            "reason_codes": reasons,
            "execution_performed": False,
            "global_authority_granted": False,
            "safe_summary": (
                "Sealed arithmetic readiness is current; an exact mission lease is still required."
                if not reasons
                else "Sealed arithmetic readiness failed closed."
            ),
        }
    _emit(payload, as_json=args.json)
    return 0


def _run(args: argparse.Namespace) -> int:
    expression = _read_expression()
    try:
        state_dir = Path(args.state_dir) if args.state_dir else None
        backend = _discover(state_dir)
        lease_store = AuthorityLeaseStore(state_dir)
        service = SealedCalculationMissionService(
            state_dir=state_dir or lease_store.state_dir,
            backend=backend,
            lease_store=lease_store,
        )
        result = service.run(
            SealedCalculationMissionRequest(
                request_ref=args.request_ref,
                input_ref=args.input_ref,
                expression=expression,
                expression_sha256=hash_text(expression),
                plan_ref=args.plan_ref,
                mission_ref=args.mission_ref,
                run_ref=args.run_ref,
                step_ref=args.step_ref,
                lease_ref=args.lease_ref,
                request_created_at=datetime.fromisoformat(args.request_created_at),
                start_deadline=datetime.fromisoformat(args.start_deadline),
            ),
            owner_ref=args.owner_ref,
        )
    except (SealedCalculationBackendError, ValueError) as exc:
        payload = {
            "schema_version": "uaa-sealed-calculation-cli.v1",
            "status": "blocked",
            "reason_code": _safe_backend_reason(exc),
            "execution_performed": False,
            "raw_expression_persisted": False,
            "global_authority_granted": False,
            "safe_summary": "Sealed calculation was denied before a confirmed execution.",
        }
        _emit(payload, as_json=args.json)
        return 2
    finally:
        expression = ""
    payload = {
        "schema_version": "uaa-sealed-calculation-cli.v1",
        "status": result.orchestration.status,
        "mission_ref": result.orchestration.mission_ref,
        "run_ref": result.orchestration.run_ref,
        "expression_sha256": result.expression_sha256,
        "output_sha256": result.output_sha256,
        "result_preview": result.result_preview,
        "evidence_refs": result.orchestration.evidence_refs,
        "result_is_evidence_not_authority": True,
        "raw_expression_persisted": False,
        "global_authority_granted": False,
        "safe_summary": result.safe_summary,
    }
    _emit(payload, as_json=args.json)
    return 0 if result.orchestration.status == "succeeded" else 2


def _prepare(args: argparse.Namespace) -> int:
    validate_execution_ref(args.input_ref, "sealed_calculation_input_ref")
    validate_execution_ref(args.mission_ref, "sealed_calculation_mission_ref")
    expression = _read_expression()
    try:
        state_dir = Path(args.state_dir) if args.state_dir else None
        backend = _discover(state_dir)
        expression_sha256 = hash_text(expression)
        resource_refs = [
            SEALED_CALCULATION_CAPABILITY_REF,
            SEALED_CALCULATION_ADAPTER_REF,
            SEALED_CALCULATION_TARGET_REF,
            args.input_ref,
            f"expression-hash-ref:sha256:{expression_sha256}",
            SEALED_CALCULATION_GRAMMAR_POLICY_REF,
            backend.attestation.attestation_ref,
            backend.attestation.limits_ref,
            args.mission_ref,
        ]
    except (SealedCalculationBackendError, ValueError) as exc:
        payload = {
            "schema_version": "uaa-sealed-calculation-cli.v1",
            "status": "configuration_required",
            "reason_code": _safe_backend_reason(exc),
            "execution_performed": False,
            "raw_expression_persisted": False,
            "global_authority_granted": False,
            "safe_summary": "Exact lease resources could not be prepared safely.",
        }
        _emit(payload, as_json=args.json)
        return 2
    finally:
        expression = ""
    payload = {
        "schema_version": "uaa-sealed-calculation-cli.v1",
        "status": "exact_lease_resources_prepared",
        "required_mode": "delegated_mission_autonomous_window",
        "required_domain": "workspace",
        "required_capability": "execute",
        "expression_sha256": expression_sha256,
        "request_created_at": datetime.now().astimezone().isoformat(),
        "resource_refs": resource_refs,
        "execution_performed": False,
        "raw_expression_persisted": False,
        "global_authority_granted": False,
        "safe_summary": (
            "Exact content-free lease resource refs are ready for operator-approved "
            "mission lease issuance."
        ),
    }
    _emit(payload, as_json=args.json)
    return 0


def _read_expression() -> str:
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    raw = stream.read(514)
    if isinstance(raw, str):
        encoded = raw.encode("utf-8")
    else:
        encoded = raw
    if len(encoded) > 513:
        raise ValueError("SEALED_CALCULATION_EXPRESSION_SIZE_LIMIT_EXCEEDED")
    try:
        expression = encoded.decode("utf-8").rstrip("\r\n")
    except UnicodeError as exc:
        raise ValueError("SEALED_CALCULATION_EXPRESSION_ENCODING_INVALID") from exc
    if not expression or len(expression.encode("utf-8")) > 512:
        raise ValueError("SEALED_CALCULATION_EXPRESSION_SIZE_LIMIT_EXCEEDED")
    return expression


def _safe_backend_reason(exc: Exception) -> str:
    reason = str(exc)
    if re.fullmatch(r"SEALED_CALCULATION_[A-Z0-9_:.-]{1,96}", reason):
        return reason
    return "SEALED_CALCULATION_BACKEND_UNAVAILABLE"


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print("Sealed deterministic calculation")
    print(f"Status: {payload['status']}")
    print(f"Summary: {payload['safe_summary']}")
    if payload.get("result_preview") is not None:
        print(f"Result evidence: {payload['result_preview']}")
        print(f"Output hash: {payload['output_sha256']}")
    if payload.get("attestation_ref") is not None:
        print(f"Attestation: {payload['attestation_ref']}")
        print(f"Limits: {payload['limits_ref']}")
    resource_refs = payload.get("resource_refs")
    if isinstance(resource_refs, list):
        print("Exact lease resources:")
        for ref in resource_refs:
            print(f"- {ref}")
    print("Code output is evidence, not authority.")
    print("Broad code, shell, network, host files, and global authority remain denied.")
