#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.communications import (  # noqa: E402
    CommunicationsReceiptNotFound,
    CommunicationsService,
    build_default_communications_service,
)


def _json(value: Any) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    elif isinstance(value, tuple):
        value = [item.model_dump(mode="json") for item in value]
    print(json.dumps(value, indent=2, sort_keys=True))


def _render_providers(service: CommunicationsService, as_json: bool) -> int:
    providers = service.inspect_provider_posture()
    if as_json:
        _json(providers)
        return 0
    print("Communications providers")
    for provider in providers:
        availability = provider.availability
        print(f"- {provider.provider_ref}: {provider.provider_status.value}")
        print(f"  Adapter: {provider.adapter_ref}")
        print(f"  Runtime readiness: {availability.runtime_readiness_status.value}")
        print(f"  Authority: {availability.authority_posture.value}")
        print(f"  Blockers: {', '.join(provider.blocker_codes)}")
    print("No provider network operation was performed.")
    return 0


def _render_session(service: CommunicationsService, as_json: bool) -> int:
    posture = service.inspect_session_posture()
    if as_json:
        _json(posture)
        return 0
    print("Communications session")
    print(f"- Provider: {posture.provider_ref}")
    print(f"- Status: {posture.status.value}")
    print(f"- Freshness: {posture.freshness.value}")
    print(f"- Blockers: {', '.join(posture.blocker_codes)}")
    print("No authentication or synchronization was performed.")
    return 0


def _render_rooms(service: CommunicationsService, as_json: bool, limit: int) -> int:
    page = service.list_rooms(limit=limit)
    if as_json:
        _json(page)
        return 0
    print("Communications rooms")
    print(f"- Returned: {page.pagination.returned_count}")
    print(f"- Freshness: {page.freshness.value}")
    print(f"- Blockers: {', '.join(page.blocker_codes)}")
    print("No message content was read.")
    return 0


def _render_failed_sends(
    service: CommunicationsService, as_json: bool, limit: int
) -> int:
    page = service.list_failed_sends(limit=limit)
    if as_json:
        _json(page)
        return 0
    print("Communications failed sends")
    print(f"- Returned: {page.pagination.returned_count}")
    print(f"- Blockers: {', '.join(page.blocker_codes)}")
    print("No send runtime exists and no send was performed.")
    return 0


def _render_security(service: CommunicationsService, as_json: bool) -> int:
    posture = service.inspect_security_posture()
    if as_json:
        _json(posture)
        return 0
    print("Communications security posture")
    print(f"- Encryption: {posture.encryption_posture_ref}")
    print(f"- Key lifecycle: {posture.key_lifecycle_posture_ref}")
    print(f"- Cache: {posture.cache_posture_ref}")
    print(f"- Blockers: {', '.join(posture.blocker_codes)}")
    print("No credentials, crypto runtime, or local cache were opened.")
    return 0


def _render_receipt(
    service: CommunicationsService, as_json: bool, receipt_ref: str
) -> int:
    try:
        receipt = service.lookup_receipt(receipt_ref)
    except CommunicationsReceiptNotFound:
        print("Communications receipt not found (reference-only diagnostic).")
        return 2
    if as_json:
        _json(receipt)
        return 0
    print("Communications receipt")
    print(f"- Receipt: {receipt.receipt_ref}")
    print(f"- Outcome: {receipt.outcome.value}")
    print(f"- Provider: {receipt.provider_ref}")
    print(f"- Blockers: {', '.join(receipt.blocker_codes)}")
    print("Receipt is content-free; no provider operation was performed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect backend-owned communications contracts without Matrix runtime."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("providers", "session", "security"):
        command = subparsers.add_parser(name)
        command.add_argument("--json", action="store_true", help="Emit safe JSON.")
    for name in ("rooms", "failed-sends"):
        command = subparsers.add_parser(name)
        command.add_argument("--limit", type=int, default=25)
        command.add_argument("--json", action="store_true", help="Emit safe JSON.")
    receipt = subparsers.add_parser("receipt")
    receipt.add_argument("receipt_ref")
    receipt.add_argument("--json", action="store_true", help="Emit safe JSON.")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    service: CommunicationsService | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    active_service = service or build_default_communications_service()
    if args.command == "providers":
        return _render_providers(active_service, args.json)
    if args.command == "session":
        return _render_session(active_service, args.json)
    if args.command == "rooms":
        return _render_rooms(active_service, args.json, args.limit)
    if args.command == "failed-sends":
        return _render_failed_sends(active_service, args.json, args.limit)
    if args.command == "security":
        return _render_security(active_service, args.json)
    return _render_receipt(active_service, args.json, args.receipt_ref)


if __name__ == "__main__":
    raise SystemExit(main())
