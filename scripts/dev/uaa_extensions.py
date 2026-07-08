#!/usr/bin/env python3
"""Inspect UAA extension ecosystem metadata.

This CLI exposes the same Python-core read model used by the Control Center
extension catalog route. It does not install, import, execute, enable, or
fetch extension packages.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.extension_catalog import (
    ExtensionInstallDisabledRecordDeleteRequest,
    ExtensionInstallDisabledRecordIssueRequest,
    build_default_extension_install_disabled_posture,
    build_default_inspectable_extension_catalog,
    build_default_skill_bundle_proposal_posture,
    build_default_skill_write_approval_gate,
    delete_extension_install_disabled_record,
    issue_extension_install_disabled_record,
)


def inspect_catalog() -> dict[str, object]:
    catalog = build_default_inspectable_extension_catalog()
    return catalog.model_dump(mode="json")


def inspect_skill_write_gate() -> dict[str, object]:
    gate = build_default_skill_write_approval_gate()
    return gate.model_dump(mode="json")


def inspect_skill_bundles() -> dict[str, object]:
    posture = build_default_skill_bundle_proposal_posture()
    return posture.model_dump(mode="json")


def inspect_install_disabled_posture() -> dict[str, object]:
    posture = build_default_extension_install_disabled_posture()
    return posture.model_dump(mode="json")


def record_install_disabled_receipt(args: argparse.Namespace) -> dict[str, object]:
    authority_store = AuthorityLeaseStore(
        Path(args.authority_state_dir) if args.authority_state_dir else None
    )
    approval_grants = [
        json.loads(Path(path).read_text(encoding="utf-8"))
        for path in args.approval_grant_file
    ]
    receipt = issue_extension_install_disabled_record(
        ExtensionInstallDisabledRecordIssueRequest(
            approval_ref=args.approval_ref,
            approval_grants=approval_grants,
        ),
        leases=authority_store.list_leases(active_only=True),
        idempotency_key_ref=args.idempotency_ref,
        storage_root=authority_store.state_dir,
    )
    return receipt.model_dump(mode="json")


def rollback_install_disabled_receipt(args: argparse.Namespace) -> dict[str, object]:
    authority_store = AuthorityLeaseStore(
        Path(args.authority_state_dir) if args.authority_state_dir else None
    )
    approval_grants = [
        json.loads(Path(path).read_text(encoding="utf-8"))
        for path in args.approval_grant_file
    ]
    receipt = delete_extension_install_disabled_record(
        ExtensionInstallDisabledRecordDeleteRequest(
            approval_ref=args.approval_ref,
            approval_grants=approval_grants,
        ),
        leases=authority_store.list_leases(active_only=True),
        idempotency_key_ref=args.idempotency_ref,
        storage_root=authority_store.state_dir,
    )
    return receipt.model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "inspect-catalog",
        help="Print read-only extension catalog metadata as safe-ref JSON.",
    )
    subparsers.add_parser(
        "inspect-skill-write-gate",
        help="Print staged skill-write approval gate metadata as safe-ref JSON.",
    )
    subparsers.add_parser(
        "inspect-skill-bundles",
        help="Print proposal-only skill bundle posture as safe-ref JSON.",
    )
    subparsers.add_parser(
        "inspect-install-disabled-posture",
        help="Print extension install-disabled posture as safe-ref JSON.",
    )
    record_parser = subparsers.add_parser(
        "record-install-disabled-receipt",
        help=(
            "Record an exact disabled extension install metadata receipt after "
            "AuthorityLease and LocalApprovalAuthority validation."
        ),
    )
    record_parser.add_argument("--approval-ref", required=True)
    record_parser.add_argument(
        "--approval-grant-file",
        action="append",
        default=[],
        help="Path to one exact LocalApprovalAuthority grant JSON payload.",
    )
    record_parser.add_argument(
        "--idempotency-ref",
        default="idempotency-ref:extension-install-disabled:uaa-plugin-skill-boundary:v1",
    )
    record_parser.add_argument("--authority-state-dir")
    rollback_parser = subparsers.add_parser(
        "rollback-install-disabled-receipt",
        help=(
            "Rollback/delete the local disabled extension install metadata receipt "
            "after AuthorityLease and exact LocalApprovalAuthority validation."
        ),
    )
    rollback_parser.add_argument("--approval-ref", required=True)
    rollback_parser.add_argument(
        "--approval-grant-file",
        action="append",
        default=[],
        help="Path to one exact rollback LocalApprovalAuthority grant JSON payload.",
    )
    rollback_parser.add_argument(
        "--idempotency-ref",
        default=(
            "idempotency-ref:extension-install-disabled-delete:"
            "uaa-plugin-skill-boundary:v1"
        ),
    )
    rollback_parser.add_argument("--authority-state-dir")
    args = parser.parse_args(argv)

    if args.command == "inspect-catalog":
        print(json.dumps(inspect_catalog(), indent=2, sort_keys=True))
        return 0
    if args.command == "inspect-skill-write-gate":
        print(json.dumps(inspect_skill_write_gate(), indent=2, sort_keys=True))
        return 0
    if args.command == "inspect-skill-bundles":
        print(json.dumps(inspect_skill_bundles(), indent=2, sort_keys=True))
        return 0
    if args.command == "inspect-install-disabled-posture":
        print(json.dumps(inspect_install_disabled_posture(), indent=2, sort_keys=True))
        return 0
    if args.command == "record-install-disabled-receipt":
        print(json.dumps(record_install_disabled_receipt(args), indent=2, sort_keys=True))
        return 0
    if args.command == "rollback-install-disabled-receipt":
        print(
            json.dumps(
                rollback_install_disabled_receipt(args),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
