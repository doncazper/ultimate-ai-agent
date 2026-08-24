#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.evals.tool_aware_corpus import (  # noqa: E402
    build_holdout_commitment,
)


def _outside_candidate_tree(path: Path) -> Path:
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file():
        raise ValueError("private manifest must be a regular non-symlink file")
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return resolved
    raise ValueError("private holdout material cannot be read from the candidate tree")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a public TAW-00 commitment on an independent custodian host"
    )
    parser.add_argument("--private-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cycle-ref", required=True)
    parser.add_argument("--custodian-ref", required=True)
    parser.add_argument("--creation-order-evidence-ref", required=True)
    parser.add_argument("--custodian-attestation-ref", required=True)
    args = parser.parse_args()
    try:
        private_path = _outside_candidate_tree(args.private_manifest)
        key_hex = os.environ.get("UAA_TAW00_HOLDOUT_HMAC_KEY_HEX", "")
        key = bytes.fromhex(key_hex)
        commitment = build_holdout_commitment(
            cycle_ref=args.cycle_ref,
            custodian_ref=args.custodian_ref,
            creation_order_evidence_ref=args.creation_order_evidence_ref,
            custodian_attestation_ref=args.custodian_attestation_ref,
            secret_key=key,
            private_manifest=private_path.read_bytes(),
        )
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            handle.write(commitment.model_dump_json(indent=2) + "\n")
        print(
            json.dumps(
                {
                    "status": "public_commitment_written",
                    "cycle_ref": commitment.cycle_ref,
                    "commitment_digest": commitment.commitment_digest,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "blocked", "reason_code": type(exc).__name__},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
