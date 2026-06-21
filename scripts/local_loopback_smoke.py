#!/usr/bin/env python3
from typing import Any
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pydantic import ValidationError  # noqa: E402

from ultimate_ai_agent.core.approvals import ApprovalGrant, LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.hygiene.actor_context import ActorContext, ActorType, AuthoritySource  # noqa: E402
from ultimate_ai_agent.core.hygiene.policies import ClassificationValue, DataClassification  # noqa: E402
from ultimate_ai_agent.core.model_runtime import (  # noqa: E402
    DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT,
    ManualLoopbackSmokePolicy,
    ManualLoopbackSmokeRequest,
    ModelRuntimeKind,
    StdlibLoopbackSmokeTransport,
    smoke_approval_validation_request,
)
from ultimate_ai_agent.core.model_runtime.loopback import LoopbackRuntimeEndpoint  # noqa: E402


def build_transport() -> Any:
    return StdlibLoopbackSmokeTransport()


def main(argv: list[str] | None = None, *, transport: Any | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manual local loopback smoke test. Not for user data or production execution.")
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--approval-ref", required=True)
    parser.add_argument("--enable-manual-local-smoke", action="store_true")
    parser.add_argument("--expected-marker", default="UAA_LOCAL_SMOKE_OK")
    parser.add_argument("--approval-grant-json")
    args = parser.parse_args(argv)

    if not args.enable_manual_local_smoke:
        return _print_denial(["ENABLE_MANUAL_LOCAL_SMOKE_REQUIRED"], "Manual local smoke requires the explicit enable flag.")

    try:
        grant = ApprovalGrant(**json.loads(args.approval_grant_json)) if args.approval_grant_json else None
        actor_id = grant.granted_to_actor_id if grant is not None else "manual_operator"
        run_id = grant.run_id if grant is not None else "run_manual_local_smoke"
        endpoint_id = grant.approved_resource_refs[0] if grant is not None and grant.approved_resource_refs else "manual_local_smoke_endpoint"
        data_classification = (
            grant.data_classification
            if grant is not None
            else DataClassification(classification=ClassificationValue.public, source="manual_local_smoke")
        )
        endpoint = LoopbackRuntimeEndpoint(
            endpoint_id=endpoint_id,
            base_url=args.endpoint,
            allowed_hosts=["127.0.0.1", "localhost", "::1"],
            runtime_kind=ModelRuntimeKind.local_stub,
            model_id=args.model,
            enabled=True,
            owner="manual_operator",
            source="scripts/local_loopback_smoke.py",
            version="0.0.0",
        )
        request = ManualLoopbackSmokeRequest(
            smoke_request_id="smoke_req_1",
            run_id=run_id,
            endpoint=endpoint,
            model_id=args.model,
            approval_ref=args.approval_ref,
            fixed_prompt=DEFAULT_MANUAL_LOOPBACK_SMOKE_PROMPT,
            expected_marker=args.expected_marker,
            policy=ManualLoopbackSmokePolicy(policy_id="manual_local_smoke_policy", enable_manual_smoke=True),
            actor_context=ActorContext(
                actor_type=ActorType.human_user,
                actor_id=actor_id,
                authority_source=AuthoritySource.manual_operator_action,
                approval_ref=args.approval_ref,
            ),
            data_classification=data_classification,
        )
        approval_decision = _approval_decision_from_grant(request, grant)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        return _print_validation_error(exc)

    active_transport = transport or build_transport()
    result = active_transport.send_smoke(request, approval_decision)
    print(json.dumps(result.model_dump(mode="json")))
    return 0 if result.success else 1


def _approval_decision_from_grant(request: ManualLoopbackSmokeRequest, grant: ApprovalGrant | None) -> Any:
    if grant is None:
        return None
    authority = LocalApprovalAuthority()
    authority.load_grant_for_validation(grant)
    return authority.validate(smoke_approval_validation_request(request))


def _print_denial(reason_codes: list[str], safe_message: str) -> int:
    print(
        json.dumps(
            {
                "success": False,
                "allowed": False,
                "status": "blocked",
                "reason_codes": reason_codes,
                "safe_message": safe_message,
            }
        )
    )
    return 1


def _print_validation_error(exc: Exception) -> int:
    print(
        json.dumps(
            {
                "success": False,
                "allowed": False,
                "status": "blocked",
                "reason_codes": ["MODEL_RUNTIME_VALIDATION_FAILED"],
                "safe_message": "Manual local loopback smoke payload validation failed.",
                "caused_by": [type(exc).__name__],
            }
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
