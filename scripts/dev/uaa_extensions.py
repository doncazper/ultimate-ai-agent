#!/usr/bin/env python3
"""Inspect UAA extension ecosystem metadata.

This CLI exposes the same Python-core read model used by the Control Center
extension catalog route. It does not install, import, execute, enable, or
fetch extension packages.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.extension_catalog import (
    ExtensionInstallDisabledRecordDeleteRequest,
    ExtensionInstallDisabledRecordIssueRequest,
    build_default_exact_extension_adapter_manifest,
    build_exact_extension_adapter_read_model,
    build_default_extension_install_disabled_posture,
    build_default_skill_bundle_proposal_posture,
    build_default_skill_write_approval_gate,
    delete_extension_install_disabled_record,
    issue_extension_install_disabled_record,
    load_exact_extension_adapter_manifest,
)
from ultimate_ai_agent.core.extension_catalog.ecosystem import (
    build_default_extension_ecosystem_read_model,
)


def inspect_catalog() -> dict[str, object]:
    catalog = build_default_extension_ecosystem_read_model()
    return catalog.model_dump(mode="json")


def render_catalog_summary(payload: dict[str, object]) -> str:
    validations = payload.get("developer_validation_results", [])
    if not isinstance(validations, list):
        raise ValueError("EXTENSION_CATALOG_VALIDATION_RESULTS_INVALID")
    lines = [
        "UAA extension ecosystem",
        "Inspectable never means callable; every invocation requires fresh request-scoped evaluation.",
        (
            f"Entries: {len(payload.get('entries', []))} | "
            f"capability snapshots: {payload.get('availability_snapshot_count', 0)} | "
            f"developer validations: {payload.get('developer_validation_count', 0)}"
        ),
        "",
    ]
    for item in validations:
        if not isinstance(item, dict):
            continue
        blockers = item.get("blocker_codes", [])
        blocker_text = ", ".join(str(value) for value in blockers) or "none"
        lines.extend(
            [
                f"- {item.get('package_ref', 'extension-package:unknown')}",
                (
                    f"  manifest={item.get('manifest_ref', 'manifest-ref:unknown')} "
                    f"version={item.get('version_ref', 'version:unknown')}"
                ),
                (
                    "  metadata="
                    f"{item.get('status', 'blocked')} "
                    f"compatibility={item.get('compatibility_status', 'unknown')} "
                    f"configuration={item.get('configuration_status', 'unknown')} "
                    f"health={item.get('health_status', 'unknown')} "
                    f"authority={item.get('authority_posture', 'blocked')} "
                    f"budget={item.get('resource_status', 'unknown')} "
                    f"safe-disable={item.get('safe_disable_status', 'unknown')}"
                ),
                (
                    f"  provenance={item.get('provenance_status', 'unknown')} "
                    "pinned-hashes="
                    f"{'verified' if item.get('hashes_verified_against_pinned_values') is True else 'unverified'} "
                    f"signature={item.get('signature_status', 'unknown')}"
                ),
                (
                    "  safe-disable-ref="
                    f"{item.get('safe_disable_ref', 'safe-disable-ref:unknown')} "
                    f"rollback={item.get('rollback_ref', 'rollback-ref:unknown')} "
                    f"blockers={blocker_text}"
                ),
            ]
        )
    return "\n".join(lines)


def validate_catalog_entry(entry_ref: str) -> dict[str, object]:
    ecosystem = build_default_extension_ecosystem_read_model()
    for result in ecosystem.developer_validation_results:
        if result.catalog_entry_ref == entry_ref or result.package_ref == entry_ref:
            return result.model_dump(mode="json")
    raise ValueError("EXTENSION_DEVELOPER_ENTRY_NOT_FOUND")


def render_validation_summary(payload: dict[str, object]) -> str:
    blockers = payload.get("blocker_codes", [])
    blocker_text = ", ".join(str(value) for value in blockers) or "none"
    return "\n".join(
        [
            "UAA extension developer validation",
            f"Package: {payload['package_ref']}",
            f"Manifest: {payload['manifest_ref']}",
            f"Version: {payload['version_ref']}",
            f"Status: {payload['status']}",
            (
                "Pinned hashes: "
                f"{payload['reviewed_hash_count']}/{payload['declared_hash_count']}"
            ),
            f"Blockers: {blocker_text}",
            "Runtime import: blocked",
            "Catalog validation never grants activation or execution authority.",
        ]
    )


def inspect_exact_adapter() -> dict[str, object]:
    return build_exact_extension_adapter_read_model().model_dump(mode="json")


def render_exact_adapter_summary(payload: dict[str, object]) -> str:
    manifest = payload.get("manifest")
    posture = payload.get("runtime_posture")
    if not isinstance(manifest, dict) or not isinstance(posture, dict):
        raise ValueError("EXACT_EXTENSION_READ_MODEL_INVALID")
    blockers = payload.get("blocker_codes", [])
    blocker_text = ", ".join(str(item) for item in blockers) or "none"
    return "\n".join(
        [
            "UAA exact extension adapter",
            f"Registration: {manifest['registration_ref']}",
            f"Package: {manifest['package_ref']}",
            f"Capability: {manifest['capability_ref']}",
            f"Adapter: {manifest['adapter_ref']}",
            (
                "Runtime posture: "
                f"compatibility={posture['compatibility_status']} "
                f"configuration={posture['configuration_status']} "
                f"health={posture['health_status']} "
                f"budget={posture['budget_status']} "
                f"safe-disable={posture['safe_disable_status']} "
                f"kill-switch={posture['kill_switch_status']}"
            ),
            (
                "Ready for request-scoped evaluation: "
                f"{'yes' if payload['ready_for_request_scoped_evaluation'] else 'no'}"
            ),
            f"Blockers: {blocker_text}",
            "General extension runtime: disabled",
            "Runtime package import: disabled",
            (
                "Callability still requires fresh PolicyEngine, AuthorityLease, "
                "target, budget, kill-switch, safe-disable, and idempotency checks."
            ),
        ]
    )


def _safe_extension_denial_code(exc: ValueError) -> str:
    match = re.search(r"EXTENSION_INSTALL_DISABLED_[A-Z0-9_]+", str(exc))
    return match.group(0) if match else "EXTENSION_INSTALL_DISABLED_REQUEST_DENIED"


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
    receipt = issue_extension_install_disabled_record(
        ExtensionInstallDisabledRecordIssueRequest(
            approval_ref=args.approval_ref,
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
    receipt = delete_extension_install_disabled_record(
        ExtensionInstallDisabledRecordDeleteRequest(
            approval_ref=args.approval_ref,
        ),
        leases=authority_store.list_leases(active_only=True),
        idempotency_key_ref=args.idempotency_ref,
        storage_root=authority_store.state_dir,
    )
    return receipt.model_dump(mode="json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    catalog_parser = subparsers.add_parser(
        "inspect-catalog",
        help="Print a readable read-only extension ecosystem summary.",
    )
    catalog_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the same backend-owned truth as redacted safe-ref JSON.",
    )
    validate_parser = subparsers.add_parser(
        "validate-entry",
        help=(
            "Validate one known pinned extension entry for metadata-only developer "
            "feedback without importing or executing it."
        ),
    )
    validate_parser.add_argument("entry_ref")
    validate_parser.add_argument("--json", action="store_true")
    exact_parser = subparsers.add_parser(
        "inspect-exact-adapter",
        help="Inspect the one repo-owned AuthorityDispatcher extension binding.",
    )
    exact_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the same backend-owned truth as redacted safe-ref JSON.",
    )
    validate_exact_parser = subparsers.add_parser(
        "validate-exact-adapter-manifest",
        help="Validate a bounded file against the one reviewed adapter binding.",
    )
    validate_exact_parser.add_argument("manifest_path", type=Path)
    validate_exact_parser.add_argument("--json", action="store_true")
    subparsers.add_parser(
        "exact-adapter-manifest-template",
        help="Print the reviewed exact-adapter manifest without writing a file.",
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
            "Request an exact disabled extension metadata receipt. This fails "
            "closed until a core-owned approval resolver is available."
        ),
    )
    record_parser.add_argument("--approval-ref", required=True)
    record_parser.add_argument(
        "--idempotency-ref",
        default="idempotency-ref:extension-install-disabled:uaa-plugin-skill-boundary:v1",
    )
    record_parser.add_argument("--authority-state-dir")
    rollback_parser = subparsers.add_parser(
        "rollback-install-disabled-receipt",
        help=(
            "Request rollback of disabled extension metadata. This fails closed "
            "until a core-owned approval resolver is available."
        ),
    )
    rollback_parser.add_argument("--approval-ref", required=True)
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
        payload = inspect_catalog()
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(render_catalog_summary(payload))
        return 0
    if args.command == "validate-entry":
        try:
            payload = validate_catalog_entry(args.entry_ref)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(render_validation_summary(payload))
        return 0
    if args.command == "inspect-exact-adapter":
        payload = inspect_exact_adapter()
        print(
            json.dumps(payload, indent=2, sort_keys=True)
            if args.json
            else render_exact_adapter_summary(payload)
        )
        return 0
    if args.command == "validate-exact-adapter-manifest":
        try:
            manifest = load_exact_extension_adapter_manifest(args.manifest_path)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        payload = {
            "status": "validated_exact_repo_owned_binding",
            "manifest": manifest.model_dump(mode="json"),
            "runtime_import_performed": False,
            "execution_performed": False,
            "invocation_authorized": False,
        }
        print(
            json.dumps(payload, indent=2, sort_keys=True)
            if args.json
            else "\n".join(
                [
                    "UAA exact extension manifest validation",
                    f"Status: {payload['status']}",
                    f"Registration: {manifest.registration_ref}",
                    "Runtime import: not performed",
                    "Execution: not performed",
                    "Authority: not granted",
                ]
            )
        )
        return 0
    if args.command == "exact-adapter-manifest-template":
        print(
            json.dumps(
                build_default_exact_extension_adapter_manifest().model_dump(
                    mode="json"
                ),
                indent=2,
                sort_keys=True,
            )
        )
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
        try:
            payload = record_install_disabled_receipt(args)
        except ValueError as exc:
            print(
                f"UAA extension mutation blocked: {_safe_extension_denial_code(exc)}",
                file=sys.stderr,
            )
            return 1
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.command == "rollback-install-disabled-receipt":
        try:
            payload = rollback_install_disabled_receipt(args)
        except ValueError as exc:
            print(
                f"UAA extension mutation blocked: {_safe_extension_denial_code(exc)}",
                file=sys.stderr,
            )
            return 1
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
