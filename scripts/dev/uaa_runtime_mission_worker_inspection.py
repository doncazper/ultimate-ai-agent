from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from ultimate_ai_agent.core.authority.contracts import authority_state_dir
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatchCorruptionError,
)
from ultimate_ai_agent.core.execution.durable_mission_steps import (
    MissionStepCorruptionError,
)
from ultimate_ai_agent.core.execution.durable_mission_worker import (
    MissionWorkerCorruptionError,
)
from ultimate_ai_agent.core.execution.mission_worker_inspection import (
    MISSION_WORKER_INSPECTION_CLI_REF,
    build_local_mission_worker_inspection,
)


def _payload(read_model: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": MISSION_WORKER_INSPECTION_CLI_REF,
        "authority_mission_worker": read_model,
        "safe_refs_only": True,
        "raw_task_inputs_omitted": True,
        "raw_paths_omitted": True,
        "raw_logs_omitted": True,
        "raw_provider_payloads_omitted": True,
        "execution_performed": False,
        "mutation_performed": False,
        "approval_or_lease_minted": False,
    }


def inspect(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir) if args.state_dir else authority_state_dir()
    try:
        model = build_local_mission_worker_inspection(state_dir=state_dir).model_dump(
            mode="json"
        )
    except (
        AuthorityDispatchCorruptionError,
        MissionStepCorruptionError,
        MissionWorkerCorruptionError,
        OSError,
        UnicodeError,
        ValueError,
    ):
        print(
            "Authority mission worker inspection: local state could not be validated.",
            file=sys.stderr,
        )
        return 1
    if args.json:
        print(json.dumps(_payload(model), indent=2, sort_keys=True))
        return 0
    print("Authority mission worker inspection")
    print(f"Configured: {str(model['configuration_enabled']).lower()}")
    print(f"Canonical platform: {model['canonical_platform']}")
    print(f"Observed platform: {model['observed_platform']}")
    print(f"Platform execution supported: {model['platform_execution_supported']}")
    print(f"Queue: {model['queued_job_count']}/{model['queue_capacity']}")
    print(
        f"History: {model['total_job_count']} total, "
        f"{model['omitted_terminal_job_count']} omitted terminal"
    )
    print(f"Active claims: {model['active_claim_count']}")
    print(f"Stale claims: {model['stale_claim_count']}")
    print(f"Kill switch engaged: {model['kill_switch_engaged']}")
    for job in model["jobs"]:
        print(
            f"- {job['job_safe_ref']}: {job['recovery_status']} "
            f"generation={job['generation']}"
        )
        print(
            f"  event={job['latest_event']} heartbeat={job['heartbeat_freshness']} "
            f"last_heartbeat={job['last_heartbeat_at'] or 'not observed'}"
        )
        print(f"  claim_expiry={job['claim_expires_at'] or 'not claimed'}")
        print("  steps=" + ", ".join(step["status"] for step in job["steps"]))
        print(
            "  reasons="
            + (", ".join(job["reason_refs"]) if job["reason_refs"] else "none")
        )
        print(
            "  evidence="
            + (", ".join(job["evidence_refs"]) if job["evidence_refs"] else "none")
        )
    print(f"Summary: {model['operator_summary']}")
    print("Inspection grants execution authority: false")
    print("Request-scoped authority still required: true")
    print("Linux surface: render placeholder")
    print("Windows surface: render placeholder")
    return 0


def register_parser(subparsers: object) -> None:
    parser = subparsers.add_parser(
        "inspect-authority-mission-worker",
        help="Inspect the disabled-by-default local AuthorityLease mission worker.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the redacted backend-owned worker projection as safe JSON.",
    )
    parser.set_defaults(func=inspect)
