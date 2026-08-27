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
    HoldoutCommitment,
    build_holdout_opening_receipt,
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
        description="Verify and open one TAW-00 holdout commitment on its custodian host"
    )
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--private-manifest", type=Path, required=True)
    parser.add_argument("--opening-attestation-ref", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        commitment_path = args.commitment.resolve(strict=True)
        if args.commitment.is_symlink() or not commitment_path.is_file():
            raise ValueError("commitment must be a regular non-symlink file")
        commitment = HoldoutCommitment.model_validate_json(
            commitment_path.read_text(encoding="utf-8")
        )
        private_path = _outside_candidate_tree(args.private_manifest)
        key = bytes.fromhex(os.environ.get("UAA_TAW00_HOLDOUT_HMAC_KEY_HEX", ""))
        opening = build_holdout_opening_receipt(
            commitment,
            opening_attestation_ref=args.opening_attestation_ref,
            secret_key=key,
            private_manifest=private_path.read_bytes(),
        )
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            handle.write(opening.model_dump_json(indent=2) + "\n")
        print(
            json.dumps(
                {
                    "status": "public_opening_receipt_written",
                    "cycle_ref": opening.cycle_ref,
                    "receipt_digest_ref": opening.receipt_digest_ref,
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
