#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.providers import (  # noqa: E402
    ProviderCredentialValidationReceiptStore,
    build_provider_credential_validation_readiness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect exact-approved provider credential validation posture."
    )
    parser.add_argument(
        "--receipts-path",
        default=None,
        help="Optional JSONL validation receipt path to inspect. Defaults to posture only.",
    )
    args = parser.parse_args()

    payload = {
        "readiness": build_provider_credential_validation_readiness().model_dump(
            mode="json"
        ),
        "receipt_storage": {
            "inspected": bool(args.receipts_path),
            "receipt_count": 0,
            "receipt_refs": [],
            "safe_schema_only": True,
            "raw_credential_or_provider_payload_stored": False,
            "model_invocation_recorded": False,
        },
    }
    if args.receipts_path:
        store = ProviderCredentialValidationReceiptStore(Path(args.receipts_path))
        receipts = store.list_receipts()
        payload["receipt_storage"] = {
            "inspected": True,
            "receipt_count": len(receipts),
            "receipt_refs": [receipt.receipt_ref for receipt in receipts],
            "provider_refs": [receipt.provider_ref for receipt in receipts],
            "credential_refs": [receipt.credential_ref for receipt in receipts],
            "safe_schema_only": True,
            "raw_credential_or_provider_payload_stored": False,
            "model_invocation_recorded": False,
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
