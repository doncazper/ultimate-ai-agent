#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.api.app import app  # noqa: E402
from ultimate_ai_agent.api.openapi import verify_openapi_contract  # noqa: E402


def main() -> int:
    print("=== Ultimate AI Agent OpenAPI Contract Verification ===")
    status = verify_openapi_contract(app)
    if status.errors:
        for error in status.errors:
            print(f"FAIL: {error}")
        return 1
    for warning in status.warnings:
        print(f"WARNING: {warning}")
    print("OK: OpenAPI contract is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
