from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from ultimate_ai_agent.core.authority.contracts import authority_state_dir
from ultimate_ai_agent.core.execution.mission_completion import (
    MissionCompletionCorruptionError,
    MissionCompletionStore,
)


MISSION_COMPLETION_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-mission-completions"
)


def inspect(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir) if args.state_dir else authority_state_dir()
    try:
        model = MissionCompletionStore(state_dir).build_read_model().model_dump(
            mode="json"
        )
    except (MissionCompletionCorruptionError, OSError, UnicodeError, ValueError):
        print(
            "Authority mission completion inspection: local state could not be validated.",
            file=sys.stderr,
        )
        return 1
    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": "governed-runtime-cli:v1",
                    "command_ref": MISSION_COMPLETION_CLI_REF,
                    "authority_mission_completions": model,
                    "safe_refs_only": True,
                    "raw_content_omitted": True,
                    "raw_paths_omitted": True,
                    "execution_performed": False,
                    "approval_or_lease_minted": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print("Authority mission completions")
    print(f"Count: {model['completion_count']}")
    for manifest in model["latest_manifests"]:
        print(f"- {manifest['completion_ref']}: {manifest['status']}")
        print(
            "  mission="
            f"{manifest['mission_ref']} run={manifest['run_ref']} "
            f"steps={len(manifest['step_bindings'])}"
        )
        print(
            "  budget="
            f"{len(manifest['budget_bindings'])} settled "
            f"unresolved={any(item['unresolved_cost'] for item in manifest['budget_bindings'])}"
        )
        print(
            "  evidence="
            f"{manifest['entry_hash_ref']} memory={manifest['memory_candidate_ref']}"
        )
    print(f"Summary: {model['operator_summary']}")
    print("Inspection grants execution authority: false")
    print("Request-scoped authority still required: true")
    return 0


def register_parser(subparsers: object) -> None:
    parser = subparsers.add_parser(
        "inspect-authority-mission-completions",
        help="Inspect content-free AuthorityLease mission completion evidence.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the redacted backend-owned completion read model as safe JSON.",
    )
    parser.set_defaults(func=inspect)
