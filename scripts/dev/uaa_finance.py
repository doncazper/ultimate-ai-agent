#!/usr/bin/env python3
"""Bounded CLI parity for the FIN-001 synthetic protected-book kernel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority  # noqa: E402
from ultimate_ai_agent.core.authority import AuthorityLeaseStore  # noqa: E402
from ultimate_ai_agent.core.authority.approval_validation import (  # noqa: E402
    issue_authority_lease_with_backend_approval,
)
from ultimate_ai_agent.core.finance.authority import (  # noqa: E402
    FinanceMutationPreview,
    FinanceMutationRequest,
    build_finance_lease_issue_request,
)
from ultimate_ai_agent.core.finance.crypto import (  # noqa: E402
    MacOSFinanceCryptoBackend,
)
from ultimate_ai_agent.core.finance.models import stable_finance_ref  # noqa: E402
from ultimate_ai_agent.core.finance.import_commit import (  # noqa: E402
    FIN002_IMPORT_SAFE_DISABLE_REF,
    FinanceImportCommitProof,
)
from ultimate_ai_agent.core.finance.import_preview import (  # noqa: E402
    preview_synthetic_csv_fixture,
)
from ultimate_ai_agent.core.finance.repository import FinanceRepository  # noqa: E402
from ultimate_ai_agent.core.finance.review_projection import (  # noqa: E402
    build_finance_review_projection,
)
from ultimate_ai_agent.core.finance.service import (  # noqa: E402
    FinanceKernelService,
    finance_repository_ref,
    finance_target_ref,
)


FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
MAX_BUNDLE_BYTES = 2 * 1024 * 1024


def _json(value: object) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))


def _read_json(path: Path) -> dict[str, Any]:
    metadata = os.lstat(path)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_size <= 0
        or metadata.st_size > MAX_BUNDLE_BYTES
    ):
        raise ValueError("FINANCE_CLI_BUNDLE_FILE_INVALID")
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError("FINANCE_CLI_BUNDLE_INVALID")
    return payload


def _backend(args: argparse.Namespace) -> MacOSFinanceCryptoBackend:
    return MacOSFinanceCryptoBackend(
        helper_path=args.helper_path,
        expected_helper_sha256=args.helper_sha256,
    )


def _service(args: argparse.Namespace) -> FinanceKernelService:
    return FinanceKernelService(
        FinanceRepository(args.repository_dir, crypto_backend=_backend(args))
    )


def _authority_state_dir(repository_dir: Path) -> Path:
    canonical = repository_dir.expanduser().resolve(strict=False)
    digest = hashlib.sha256(str(canonical).encode("utf-8")).hexdigest()
    parent = canonical.parent / ".uaa-finance-authority"
    state_dir = parent / digest
    for directory in (parent, state_dir):
        try:
            directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        except FileExistsError:
            pass
        metadata = os.lstat(directory)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise ValueError("FINANCE_AUTHORITY_STATE_DIR_INVALID")
    return state_dir


def _request(args: argparse.Namespace) -> FinanceMutationRequest:
    backup_path = getattr(args, "backup_path", None)
    import_fixture_ref = getattr(args, "import_fixture_ref", None)
    import_preview = None
    if args.operation == "import_commit":
        if import_fixture_ref is None:
            raise ValueError("FIN002_IMPORT_FIXTURE_REF_REQUIRED")
        snapshot = _service(args).repository.load_snapshot(request_ref=args.request_ref)
        existing_fingerprints = tuple(
            ref
            for item in snapshot.import_commits
            for ref in item.source_fingerprint_refs
        )
        import_preview = preview_synthetic_csv_fixture(
            import_fixture_ref,
            existing_fingerprint_refs=existing_fingerprints,
        )
    return FinanceMutationRequest(
        operation=args.operation,
        repository_ref=finance_repository_ref(args.repository_dir),
        fixture_ref=(
            FIXTURE_REF
            if args.operation == "create"
            else import_fixture_ref
            if args.operation == "import_commit"
            else None
        ),
        target_ref=finance_target_ref(backup_path) if backup_path else None,
        import_preview_ref=(import_preview.preview_ref if import_preview else None),
        import_profile_ref=(import_preview.profile_ref if import_preview else None),
        import_fixture_manifest_ref=(
            import_preview.import_fixture_manifest_ref if import_preview else None
        ),
        import_candidate_refs=(
            tuple(item.candidate_ref for item in import_preview.candidates)
            if import_preview
            else ()
        ),
        import_source_fingerprint_refs=(
            tuple(item.source_fingerprint_ref for item in import_preview.observations)
            if import_preview
            else ()
        ),
        expected_revision=args.expected_revision,
        request_ref=args.request_ref,
        idempotency_ref=args.idempotency_ref,
        safe_disable_ref=(
            FIN002_IMPORT_SAFE_DISABLE_REF
            if args.operation == "import_commit"
            else "safe-disable-ref:finance/FIN-001:synthetic-mutations"
        ),
    )


def command_status(args: argparse.Namespace) -> int:
    readiness = _backend(args).readiness()
    _json(
        {
            "schema_version": "uaa-finance-cli-status.v1",
            "repository_ref": finance_repository_ref(args.repository_dir),
            "crypto": readiness.model_dump(mode="json"),
            "metadata_present": (
                args.repository_dir / "finance_repository_v1.json"
            ).is_file(),
            "ciphertext_present": (
                args.repository_dir / "finance_repository_v1.enc"
            ).is_file(),
            "synthetic_only": True,
            "real_financial_data_allowed": False,
            "mutation_performed": False,
        }
    )
    return 0 if readiness.status == "ready" else 2


def command_prepare(args: argparse.Namespace) -> int:
    request = _request(args)
    service = _service(args)
    preview = service.prepare(request)
    bound_request = FinanceMutationRequest.model_validate(
        {
            **request.model_dump(mode="python"),
            "approval_ref": preview.expected_approval_ref,
            "exact_scope_ref": preview.exact_scope_ref,
            "action_envelope_ref": preview.action_envelope_ref,
        }
    )
    _json(
        {
            "schema_version": "uaa-finance-prepared-mutation-bundle.v1",
            "request": bound_request.model_dump(mode="json"),
            "preview": preview.model_dump(mode="json"),
            "mutation_performed": False,
            "operator_confirmation_required": True,
        }
    )
    return 0


def command_run(args: argparse.Namespace) -> int:
    if not args.confirmed:
        raise ValueError("FINANCE_OPERATOR_CONFIRMATION_REQUIRED")
    raw = _read_json(args.bundle)
    if (
        set(raw)
        != {
            "schema_version",
            "request",
            "preview",
            "mutation_performed",
            "operator_confirmation_required",
        }
        or raw.get("schema_version") != "uaa-finance-prepared-mutation-bundle.v1"
    ):
        raise ValueError("FINANCE_PREPARED_BUNDLE_SHAPE_INVALID")
    if (
        raw.get("mutation_performed") is not False
        or raw.get("operator_confirmation_required") is not True
    ):
        raise ValueError("FINANCE_PREPARED_BUNDLE_POSTURE_INVALID")
    request = FinanceMutationRequest.model_validate(raw["request"])
    preview = FinanceMutationPreview.model_validate(raw["preview"])
    service = _service(args)
    service._validate_path_bindings(request, backup_path=args.backup_path)

    approvals = LocalApprovalAuthority()
    approvals.create_request(preview.approval_request)
    approvals.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:local-cli-operator",
        approval_ref=preview.expected_approval_ref,
        expires_at=preview.expires_at,
    )
    lease_store = AuthorityLeaseStore(_authority_state_dir(args.repository_dir))
    issue_request = build_finance_lease_issue_request(
        preview,
    )
    issue_idempotency_ref = stable_finance_ref(
        "idempotency-ref:finance/FIN-001:lease-issue",
        {"payload_fingerprint_ref": preview.payload_fingerprint_ref},
    )
    _requirement, _grant, lease, lease_receipt = (
        issue_authority_lease_with_backend_approval(
            lease_store,
            issue_request,
            idempotency_ref=issue_idempotency_ref,
            approved_by_actor_id="actor-ref:finance:local-cli-operator",
        )
    )
    if lease is None or lease_receipt.status not in {"issued", "replayed"}:
        raise ValueError("FINANCE_EXACT_LEASE_ISSUANCE_DENIED")
    result = service.execute(
        request,
        preview=preview,
        approval_authority=approvals,
        lease_provider=lambda: lease_store.list_leases(active_only=True),
        clock=lambda: datetime.now(UTC),
        backup_path=args.backup_path,
        safe_disable_engaged=lambda: args.safe_disable_engaged,
    )
    if isinstance(result, tuple):
        evidence, receipt = result
        if isinstance(evidence, FinanceImportCommitProof):
            payload = {
                "import_commit": evidence.model_dump(mode="json"),
                "receipt": receipt.model_dump(mode="json"),
            }
        else:
            payload = {
                "backup": evidence.model_dump(mode="json"),
                "receipt": receipt.model_dump(mode="json"),
            }
    else:
        payload = {"receipt": result.model_dump(mode="json")}
    _json(
        {
            "schema_version": "uaa-finance-cli-mutation-result.v1",
            **payload,
            "lease_receipt_ref": lease_receipt.receipt_ref,
            "synthetic_only": True,
            "real_financial_data_included": False,
        }
    )
    return 0


def command_read(args: argparse.Namespace) -> int:
    """Emit a redacted, integrity, export, or non-mutating review read model."""

    repository = FinanceRepository(args.repository_dir, crypto_backend=_backend(args))
    if args.command == "inspect":
        payload = repository.export_redacted(request_ref=args.request_ref)
    elif args.command == "check":
        payload = repository.check_integrity(request_ref=args.request_ref)
    elif args.command == "review":
        snapshot = repository.load_snapshot_read_only(request_ref=args.request_ref)
        payload = build_finance_review_projection(snapshot).model_dump(mode="json")
    else:
        payload = repository.export_redacted(request_ref=args.request_ref)
    _json(payload)
    return 0


def parser() -> argparse.ArgumentParser:
    """Build the bounded Finance CLI parser."""

    result = argparse.ArgumentParser(description=__doc__)
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--repository-dir", type=Path, required=True)
    shared.add_argument("--helper-path", type=Path, required=True)
    shared.add_argument("--helper-sha256", required=True)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("status", parents=[shared]).set_defaults(func=command_status)
    prepare = commands.add_parser("prepare", parents=[shared])
    prepare.add_argument(
        "--operation",
        choices=("create", "import_commit", "backup", "restore", "delete"),
        required=True,
    )
    prepare.add_argument("--expected-revision", type=int, required=True)
    prepare.add_argument("--request-ref", required=True)
    prepare.add_argument("--idempotency-ref", required=True)
    prepare.add_argument("--backup-path", type=Path)
    prepare.add_argument("--import-fixture-ref")
    prepare.set_defaults(func=command_prepare)
    run = commands.add_parser("run", parents=[shared])
    run.add_argument("--bundle", type=Path, required=True)
    run.add_argument("--backup-path", type=Path)
    run.add_argument("--confirmed", action="store_true")
    run.add_argument("--safe-disable-engaged", action="store_true")
    run.set_defaults(func=command_run)
    for name in ("inspect", "check", "export", "review"):
        read = commands.add_parser(name, parents=[shared])
        read.add_argument("--request-ref", required=True)
        read.set_defaults(func=command_read)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        _json(
            {
                "schema_version": "uaa-finance-cli-error.v1",
                "ok": False,
                "error_code": str(exc).split(":", 1)[0],
                "raw_input_included": False,
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
