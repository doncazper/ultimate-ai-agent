#!/usr/bin/env python3
"""Render safe Firecrawl Cloud free-credit posture without secret material."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from ultimate_ai_agent.core.web_access import (
    FIRECRAWL_CLOUD_DEFAULT_SECRET_FILE,
    CreditTransport,
    FirecrawlCloudCredential,
    reconcile_firecrawl_cloud_credits,
    resolve_firecrawl_cloud_credential,
)


def inspect_cloud_credit_payload(
    *,
    credential: FirecrawlCloudCredential,
    transport: CreditTransport | None = None,
    fetched_at: datetime | None = None,
) -> dict[str, Any]:
    result = reconcile_firecrawl_cloud_credits(
        credential,
        transport=transport,
        fetched_at=fetched_at,
    )
    snapshot = result.snapshot
    return {
        "status": result.status.value,
        "plan_kind": snapshot.plan_kind.value if snapshot else "unknown",
        "plan_credits": snapshot.plan_credits if snapshot else None,
        "remaining_credits": snapshot.remaining_credits if snapshot else None,
        "max_concurrency": snapshot.max_concurrency if snapshot else None,
        "billing_period_ref": snapshot.billing_period_ref if snapshot else None,
        "snapshot_ref": snapshot.snapshot_ref if snapshot else None,
        "reconciliation_receipt_ref": result.reconciliation_receipt_ref,
        "credential_ref": snapshot.credential_ref
        if snapshot
        else credential.credential_ref,
        "reason_codes": list(result.reason_codes),
        "free_plan_execution_candidate": bool(
            snapshot is not None and snapshot.plan_kind.value == "free"
        ),
        "request_scoped_approval_lease_and_budget_required": True,
        "paid_usage_allowed": False,
        "credential_material_returned": False,
        "raw_provider_payload_returned": False,
        "local_path_returned": False,
    }


def render_summary(payload: Mapping[str, Any]) -> str:
    reasons = ", ".join(str(item) for item in payload.get("reason_codes", [])) or "none"
    return "\n".join(
        [
            "Firecrawl Cloud credit posture",
            f"Status: {payload['status']}",
            f"Plan: {payload['plan_kind']}",
            f"Plan credits: {_display(payload.get('plan_credits'))}",
            f"Remaining credits: {_display(payload.get('remaining_credits'))}",
            f"Concurrency ceiling: {_display(payload.get('max_concurrency'))}",
            f"Billing period: {_display(payload.get('billing_period_ref'))}",
            f"Snapshot: {_display(payload.get('snapshot_ref'))}",
            f"Receipt: {payload['reconciliation_receipt_ref']}",
            "Cloud execution still requires exact approval, AuthorityLease, reservation, and budget evaluation.",
            "Paid usage: denied",
            f"Posture: {reasons}",
        ]
    )


def _display(value: Any) -> str:
    return "unknown" if value is None else str(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect safe Firecrawl Cloud free-credit posture."
    )
    parser.add_argument(
        "--secret-file",
        type=Path,
        default=FIRECRAWL_CLOUD_DEFAULT_SECRET_FILE,
        help="Exact ignored Firecrawl credential file.",
    )
    parser.add_argument("--json", action="store_true", help="Emit safe JSON.")
    args = parser.parse_args()
    credential = resolve_firecrawl_cloud_credential(args.secret_file)
    payload = inspect_cloud_credit_payload(credential=credential)
    if args.json:
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    else:
        print(render_summary(payload))
    return 0 if payload["status"] == "succeeded" else 2


if __name__ == "__main__":
    raise SystemExit(main())
