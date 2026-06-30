#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultimate_ai_agent.core.providers import (
    TinyProviderInvocationReceiptStore,
    build_tiny_provider_invocation_readiness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the tiny exact-approved provider lane posture."
    )
    parser.add_argument(
        "--receipts-path",
        default=None,
        help="Optional JSONL receipt path to inspect. Defaults to posture only.",
    )
    args = parser.parse_args()

    payload = {
        "readiness": build_tiny_provider_invocation_readiness().model_dump(mode="json"),
        "receipt_storage": {
            "inspected": bool(args.receipts_path),
            "receipt_count": 0,
            "receipt_refs": [],
            "safe_schema_only": True,
            "raw_prompt_response_provider_exchange_stored": False,
        },
    }
    if args.receipts_path:
        store = TinyProviderInvocationReceiptStore(Path(args.receipts_path))
        receipts = store.list_receipts()
        payload["receipt_storage"] = {
            "inspected": True,
            "receipt_count": len(receipts),
            "receipt_refs": [receipt.receipt_ref for receipt in receipts],
            "usage_receipt_refs": [receipt.usage_receipt_ref for receipt in receipts],
            "cost_receipt_refs": [receipt.cost_receipt_ref for receipt in receipts],
            "safe_schema_only": True,
            "raw_prompt_response_provider_exchange_stored": False,
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
