from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from pydantic import ValidationError

from ultimate_ai_agent.core.authority import authority_state_dir
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchCorruptionError,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepCorruptionError,
)
from ultimate_ai_agent.core.execution.mission_step_inspection import (
    MISSION_STEP_INSPECTION_CLI_REF,
    MissionStepInspectionNotInitializedError,
    build_mission_step_inspection_read_model,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref


def _payload(read_model: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": MISSION_STEP_INSPECTION_CLI_REF,
        "mission_step_inspection": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "raw_paths_omitted": True,
        "raw_logs_omitted": True,
        "raw_provider_payloads_omitted": True,
        "execution_performed": False,
        "mutation_performed": False,
        "approval_or_lease_minted": False,
        "autonomous_retry_performed": False,
        "reconciliation_performed": False,
    }


def _ref_summary(refs: list[str]) -> str:
    return ", ".join(refs) if refs else "none"


def inspect(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir) if args.state_dir else authority_state_dir()
    try:
        validate_task_ref(args.step_ref, "mission_step_inspection_ref")
    except ValueError:
        print("Mission step inspection: step ref is invalid.", file=sys.stderr)
        return 1
    try:
        read_model = build_mission_step_inspection_read_model(
            args.step_ref,
            state_dir=state_dir,
        ).model_dump(mode="json")
    except MissionStepInspectionNotInitializedError:
        print("Mission step inspection: state is not initialized.", file=sys.stderr)
        return 1
    except KeyError:
        print("Mission step inspection: requested step was not found.", file=sys.stderr)
        return 1
    except (
        AuthorityDispatchCorruptionError,
        MissionStepCorruptionError,
        ValidationError,
        UnicodeError,
        OSError,
        ValueError,
    ):
        print(
            "Mission step inspection: local state could not be validated.",
            file=sys.stderr,
        )
        return 1
    if args.json:
        print(json.dumps(_payload(read_model), indent=2, sort_keys=True))
        return 0
    print("Authority mission step inspection")
    print(f"Durable status: {read_model['durable_status']}")
    print(f"Claim freshness: {read_model['claim_freshness']}")
    print(f"Mission: {read_model['mission_safe_ref']}")
    print(f"Run: {read_model['run_safe_ref']}")
    print(f"Step: {read_model['step_safe_ref']}")
    print(f"Capability: {read_model['capability_safe_ref']}")
    print(f"Adapter: {read_model['adapter_safe_ref']}")
    print(f"Lease: {read_model['lease_safe_ref']}")
    print(f"Generation: {read_model['generation']}")
    print(f"Deadline: {read_model['deadline']}")
    print(f"Claim expiry: {read_model['claim_expires_at'] or 'not claimed'}")
    print(f"Dispatch: {read_model['dispatch_safe_ref'] or 'not recorded'}")
    print(
        f"Dispatch receipt: {read_model['dispatch_receipt_safe_ref'] or 'not recorded'}"
    )
    print(f"Dispatch binding validated: {read_model['dispatch_binding_validated']}")
    print(f"Reasons: {_ref_summary(read_model['reason_safe_refs'])}")
    print(f"Evidence: {_ref_summary(read_model['evidence_safe_refs'])}")
    print(f"Summary: {read_model['operator_summary']}")
    print("Inspection grants execution authority: false")
    print("Request-scoped authority still required: true")
    print("Adapter invocation performed: false")
    print("Approval or lease minted: false")
    print("Autonomous retry performed: false")
    print("Reconciliation performed: false")
    return 0


def register_parser(subparsers: Any) -> None:
    mission_step = subparsers.add_parser(
        "inspect-authority-mission-step",
        help="Inspect one durable authority mission step without execution.",
    )
    mission_step.add_argument(
        "step_ref",
        help="Exact structured mission step ref to inspect.",
    )
    mission_step.add_argument(
        "--json",
        action="store_true",
        help="Emit the redacted read-only mission step projection as safe JSON.",
    )
    mission_step.set_defaults(func=inspect)
