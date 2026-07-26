#!/usr/bin/env python3
"""Inspect the authority-blocked macOS setup lifecycle contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.macos_setup_assistant import (  # noqa: E402
    MacOSSetupLifecycleOperationName,
    MacOSSetupLifecycleOperationStatus,
    inspect_macos_setup_lifecycle_operation,
)


BLOCKED_EXIT_CODE = 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=[operation.value for operation in MacOSSetupLifecycleOperationName],
        help="Lifecycle operation to inspect.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the same safe-ref contract as JSON.",
    )
    args = parser.parse_args(argv)
    operation = inspect_macos_setup_lifecycle_operation(args.operation)
    if args.json:
        print(json.dumps(operation.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        print(f"macOS setup lifecycle: {operation.operation.value}")
        print(f"status: {operation.status.value}")
        print(f"current state: {operation.current_state.value}")
        print(f"target state: {operation.target_state.value}")
        print(f"summary: {operation.safe_summary}")
        print(f"approval ref: {operation.approval_ref}")
        print(f"receipt ref: {operation.receipt_ref}")
        print(f"rollback ref: {operation.rollback_ref}")
        if operation.status == MacOSSetupLifecycleOperationStatus.blocked_by_authority:
            print("next action: accept the exact scoped setup authority milestone")
        else:
            print("next action: inspect only; no setup side effect was performed")
    if operation.status == MacOSSetupLifecycleOperationStatus.blocked_by_authority:
        return BLOCKED_EXIT_CODE
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
