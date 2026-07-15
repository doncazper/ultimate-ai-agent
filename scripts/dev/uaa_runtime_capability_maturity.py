from __future__ import annotations

import argparse
import json
from typing import Any

from ultimate_ai_agent.core.evals import build_capability_maturity_read_model


def _print_read_model(read_model: dict[str, Any]) -> None:
    print("Capability maturity evidence-gated plan")
    print(f"Verification: {read_model['verification_posture']}")
    print(
        "Weighted score: "
        f"baseline={read_model['baseline_weighted_score']} "
        f"target={read_model['target_weighted_score']} "
        f"verified={read_model['verified_weighted_score']}"
    )
    print(
        "Evidence: "
        f"automated-ready={read_model['automated_evidence_ready_count']} "
        f"manual-review={read_model['manual_validation_required_count']} "
        f"external={read_model['external_dependency_required_count']} "
        f"graduated={read_model['uplift_proven_count']}/{read_model['uplift_target_count']}"
    )
    for item in read_model["components"]:
        print(
            f"- {item['label']}: {item['baseline_score']} -> "
            f"{item['target_score']} ({item['evidence_status']})"
        )
        if item["blocker_codes"]:
            print(f"  blockers: {', '.join(item['blocker_codes'])}")
        print(f"  next proof: {item['next_acceptance_ref']}")
    print(
        "Scores grant no runtime authority. Automated checks cannot satisfy runtime, recovery, operator, or trusted-acceptance gates."
    )


def capability_maturity(args: argparse.Namespace) -> int:
    read_model = build_capability_maturity_read_model().model_dump(mode="json")
    payload = {
        "schema_version": "governed-runtime-cli:v1",
        "command_ref": "repo-local-command:uaa-runtime-capability-maturity",
        "capability_maturity": read_model,
        "safe_refs_only": True,
        "raw_content_omitted": True,
        "authority_granted": False,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_read_model(read_model)
    return 0


def register_capability_truth_parsers(
    subparsers: Any,
    availability_handler: Any,
) -> None:
    availability = subparsers.add_parser(
        "capability-availability",
        help="Inspect backend-owned capability availability without granting authority.",
    )
    availability.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe capability availability read model as JSON.",
    )
    availability.set_defaults(func=availability_handler)

    parser = subparsers.add_parser(
        "capability-maturity",
        help="Inspect the evidence-gated 16-component maturity uplift plan.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the safe backend-owned maturity plan as JSON.",
    )
    parser.set_defaults(func=capability_maturity)
