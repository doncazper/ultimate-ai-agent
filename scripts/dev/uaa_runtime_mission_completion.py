from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path
import sys

from ultimate_ai_agent.core.authority.contracts import (
    AuthorityLeaseStore,
    authority_state_dir,
)
from ultimate_ai_agent.core.authority.dispatcher import AuthorityDispatcher
from ultimate_ai_agent.core.execution.mission_completion import (
    MissionCompletionCorruptionError,
    MissionCompletionStore,
    PortableEvidenceManagedSigningInspection,
)
from ultimate_ai_agent.core.execution.portable_mission_evidence import (
    build_portable_mission_evidence_bundle,
    build_portable_mission_evidence_inspection,
    verify_portable_mission_evidence_bundle,
)
from ultimate_ai_agent.core.evidence_signing import (
    PortableEvidenceKeyLifecycleError,
    PortableEvidenceKeyLifecycleLedger,
    verify_signed_portable_evidence_artifact,
)


MISSION_COMPLETION_CLI_REF = (
    "repo-local-command:uaa-runtime-inspect-authority-mission-completions"
)
PORTABLE_EVIDENCE_MAX_BYTES = 4 * 1024 * 1024
SIGNED_PORTABLE_EVIDENCE_MAX_BYTES = 5 * 1024 * 1024
PORTABLE_EVIDENCE_PUBLIC_KEY_BUNDLE_MAX_BYTES = 1024 * 1024


def _signing_lifecycle(state_dir: Path) -> PortableEvidenceKeyLifecycleLedger:
    return PortableEvidenceKeyLifecycleLedger(state_dir / "portable_evidence_signing")


def _managed_signing_inspection(
    state_dir: Path,
) -> PortableEvidenceManagedSigningInspection:
    inspection = _signing_lifecycle(state_dir).inspect()
    return PortableEvidenceManagedSigningInspection(
        status=inspection.status,
        active_key_ref=inspection.active_key_ref,
        active_key_version_ref=inspection.active_key_version_ref,
        active_public_key_fingerprint_ref=(
            inspection.active_public_key_fingerprint_ref
        ),
        lifecycle_terminal_entry_hash_ref=(
            inspection.lifecycle_terminal_entry_hash_ref
        ),
        reason_refs=inspection.reason_refs,
    )


def inspect(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir) if args.state_dir else authority_state_dir()
    try:
        model = (
            MissionCompletionStore(state_dir)
            .build_read_model(
                portable_evidence_summary=build_portable_mission_evidence_inspection(
                    state_dir
                ),
                managed_signing=_managed_signing_inspection(state_dir),
            )
            .model_dump(mode="json")
        )
    except (
        MissionCompletionCorruptionError,
        PortableEvidenceKeyLifecycleError,
        OSError,
        UnicodeError,
        ValueError,
    ):
        print(
            "Authority mission completion inspection: local state could not be validated.",
            file=sys.stderr,
        )
        return 1
    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": "governed-runtime-cli:v1",
                    "command_ref": MISSION_COMPLETION_CLI_REF,
                    "authority_mission_completions": model,
                    "safe_refs_only": True,
                    "raw_content_omitted": True,
                    "raw_paths_omitted": True,
                    "execution_performed": False,
                    "approval_or_lease_minted": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print("Authority mission completions")
    print(f"Count: {model['completion_count']}")
    integrity = model["integrity_summary"]
    if integrity["manifest_count"]:
        print(
            "Completion integrity: local SHA-256 hash chain verified "
            f"({integrity['manifest_count']} manifest(s))"
        )
    else:
        print("Completion integrity: no completion evidence recorded")
    print(f"Chain ref: {integrity['chain_ref']}")
    print(f"Terminal hash: {integrity['terminal_entry_hash_ref'] or 'none'}")
    signing = model["managed_signing"]
    print(f"Managed Ed25519 key lifecycle: {signing['status']}")
    print(
        "Managed signing execution: requires exact approval, AuthorityLease, "
        "budget, kill-switch, and pinned macOS helper readiness"
    )
    print("Authenticity or external anchoring verified: false")
    portable = model["portable_evidence_summary"]
    print(f"Portable evidence: {portable['status']}")
    print(
        "Portable source records bound: "
        f"{str(portable['source_receipts_bound']).lower()}"
    )
    print("Portable source ledgers verified: false")
    print("Caller-supplied expected binding matched: false")
    for manifest in model["latest_manifests"]:
        print(f"- {manifest['completion_ref']}: {manifest['status']}")
        print(
            "  mission="
            f"{manifest['mission_ref']} run={manifest['run_ref']} "
            f"steps={len(manifest['step_bindings'])}"
        )
        print(
            "  budget="
            f"{len(manifest['budget_bindings'])} settled "
            f"unresolved={any(item['unresolved_cost'] for item in manifest['budget_bindings'])}"
        )
        for binding in manifest["budget_bindings"]:
            print(
                "    reservation="
                f"{binding['reservation_ref']} status={binding['settlement_status']} "
                f"reserved_ops={binding['reserved_operation_count']} "
                f"actual_ops={binding['actual_operation_count']} "
                f"reserved_microusd={binding['reserved_cost_microusd']} "
                f"actual_microusd={binding['actual_cost_microusd']} "
                f"unresolved={str(binding['unresolved_cost']).lower()}"
            )
            print(
                "    receipts="
                f"{binding['reserve_receipt_ref']}, "
                f"{binding['start_receipt_ref']}, "
                f"{binding['settlement_receipt_ref']}"
            )
        print(
            "  evidence="
            f"{manifest['entry_hash_ref']} memory={manifest['memory_candidate_ref']}"
        )
    print(f"Summary: {model['operator_summary']}")
    print("Inspection grants execution authority: false")
    print("Request-scoped authority still required: true")
    return 0


def export_portable(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir) if args.state_dir else authority_state_dir()
    try:
        manifests = MissionCompletionStore(state_dir).list_manifests()
        bundle = build_portable_mission_evidence_bundle(
            manifests,
            leases=AuthorityLeaseStore(state_dir).list_leases(),
            dispatch_receipts=AuthorityDispatcher(
                state_dir,
                adapters=[],
            ).list_receipts(),
        )
    except (OSError, UnicodeError, ValueError, MissionCompletionCorruptionError):
        print("Portable mission evidence export is unavailable.", file=sys.stderr)
        return 1
    print(json.dumps(bundle.model_dump(mode="json"), sort_keys=True))
    return 0


def verify_portable(args: argparse.Namespace) -> int:
    try:
        payload = json.loads(
            read_bounded_regular_file(
                Path(args.input),
                max_bytes=SIGNED_PORTABLE_EVIDENCE_MAX_BYTES,
            )
        )
        if not isinstance(payload, dict):
            raise ValueError("PORTABLE_EVIDENCE_OBJECT_REQUIRED")
        if payload.get("schema_version") == (
            "uaa-portable-mission-evidence-signed-artifact.v1"
        ):
            required = (
                getattr(args, "public_key_bundle", None),
                getattr(args, "expected_public_key_bundle_ref", None),
                getattr(args, "expected_public_key_fingerprint_ref", None),
            )
            if not all(required):
                raise ValueError("PORTABLE_EVIDENCE_SIGNED_TRUST_ANCHOR_REQUIRED")
            public_bundle = json.loads(
                read_bounded_regular_file(
                    Path(args.public_key_bundle),
                    max_bytes=PORTABLE_EVIDENCE_PUBLIC_KEY_BUNDLE_MAX_BYTES,
                )
            )
            result = verify_signed_portable_evidence_artifact(
                payload,
                public_key_bundle=public_bundle,
                expected_public_key_bundle_ref=args.expected_public_key_bundle_ref,
                expected_public_key_fingerprint_ref=(
                    args.expected_public_key_fingerprint_ref
                ),
                expected_bundle_ref=args.expected_bundle_ref,
                expected_envelope_count=args.expected_envelope_count,
            )
            signed = True
        else:
            if getattr(args, "require_signature", False):
                raise ValueError("PORTABLE_EVIDENCE_SIGNATURE_REQUIRED")
            result = verify_portable_mission_evidence_bundle(
                payload,
                expected_bundle_ref=args.expected_bundle_ref,
                expected_envelope_count=args.expected_envelope_count,
            )
            signed = False
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        print("Portable mission evidence could not be safely read.", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result.model_dump(mode="json"), sort_keys=True))
    else:
        print("Portable mission evidence verification")
        if signed:
            print(f"Valid signed artifact: {str(result.valid).lower()}")
            print("Signed artifact: true")
            print(
                f"Local hash chain verified: {str(result.hash_chain_verified).lower()}"
            )
            print(
                "Ed25519 signature verified relative to pinned bundle: "
                f"{str(result.signature_verified).lower()}"
            )
            print(
                "Pinned public-key bundle matched: "
                f"{str(result.public_key_bundle_matched).lower()}"
            )
        else:
            print(f"Valid local hash chain: {str(result.valid).lower()}")
            print(
                "Caller-supplied expected binding matched: "
                f"{str(result.caller_expected_binding_matched).lower()}"
            )
            print("Cryptographic signature verified: false")
        print("External anchor verified: false")
        print("Signer identity verified: false")
        print("Evidence grants execution authority: false")
        for reason_ref in result.reason_refs:
            print(f"- {reason_ref}")
    return 0 if result.valid else 1


def export_public_key_bundle(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir) if args.state_dir else authority_state_dir()
    try:
        bundle = _signing_lifecycle(state_dir).public_key_bundle(
            issuer_ref=args.issuer_ref,
        )
    except (PortableEvidenceKeyLifecycleError, OSError, UnicodeError, ValueError):
        print("Portable evidence public-key bundle is unavailable.", file=sys.stderr)
        return 1
    print(json.dumps(bundle.model_dump(mode="json"), sort_keys=True))
    return 0


def read_bounded_regular_file(
    path: Path,
    *,
    max_bytes: int = PORTABLE_EVIDENCE_MAX_BYTES,
) -> str:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > max_bytes
        ):
            raise ValueError("PORTABLE_EVIDENCE_INPUT_UNSAFE")
        payload = os.read(descriptor, max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError("PORTABLE_EVIDENCE_INPUT_TOO_LARGE")
        return payload.decode("utf-8")
    finally:
        os.close(descriptor)


def register_parser(subparsers: object) -> None:
    parser = subparsers.add_parser(
        "inspect-authority-mission-completions",
        help="Inspect content-free AuthorityLease mission completion evidence.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the redacted backend-owned completion read model as safe JSON.",
    )
    parser.set_defaults(func=inspect)

    export_parser = subparsers.add_parser(
        "export-authority-mission-evidence",
        help="Export the bounded content-free portable mission evidence bundle.",
    )
    export_parser.set_defaults(func=export_portable)

    verify_parser = subparsers.add_parser(
        "verify-authority-mission-evidence",
        help="Verify a bounded portable mission evidence bundle offline.",
    )
    verify_parser.add_argument("--input", required=True)
    verify_parser.add_argument("--expected-bundle-ref")
    verify_parser.add_argument("--expected-envelope-count", type=int)
    verify_parser.add_argument("--public-key-bundle")
    verify_parser.add_argument("--expected-public-key-bundle-ref")
    verify_parser.add_argument("--expected-public-key-fingerprint-ref")
    verify_parser.add_argument("--require-signature", action="store_true")
    verify_parser.add_argument("--json", action="store_true")
    verify_parser.set_defaults(func=verify_portable)

    public_key_parser = subparsers.add_parser(
        "export-portable-evidence-public-key-bundle",
        help="Export safe public trust metadata for offline signature verification.",
    )
    public_key_parser.add_argument(
        "--issuer-ref",
        default="issuer-ref:portable-evidence:local-operator",
    )
    public_key_parser.set_defaults(func=export_public_key_bundle)
