#!/usr/bin/env python3
"""Bounded CLI parity for the FIN-001 synthetic protected-book kernel."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.authority import (  # noqa: E402
    AuthorityLeaseStore as AuthorityLeaseStore,
)
from ultimate_ai_agent.core.finance.operator_workflow import (  # noqa: E402
    FinancePreparedMutation,
    confirm_finance_mutation,
    finance_authority_state_dir,
)
from ultimate_ai_agent.core.finance.authority import (  # noqa: E402
    FinanceMutationPreview,
    FinanceMutationRequest,
)
from ultimate_ai_agent.core.finance.crypto import (  # noqa: E402
    MacOSFinanceCryptoBackend,
)
from ultimate_ai_agent.core.finance.import_commit import (  # noqa: E402
    FIN002_IMPORT_SAFE_DISABLE_REF,
)
from ultimate_ai_agent.core.finance.import_preview import (  # noqa: E402
    preview_synthetic_csv_fixture,
)
from ultimate_ai_agent.core.finance.repository import FinanceRepository  # noqa: E402
from ultimate_ai_agent.core.finance.review_projection import (  # noqa: E402
    build_finance_review_projection,
)
from ultimate_ai_agent.core.finance.review_decision_preview import (  # noqa: E402
    build_finance_review_decision_preview_request,
    preview_finance_review_decision,
)
from ultimate_ai_agent.core.finance.review_decision_commit import (  # noqa: E402
    FIN003_REVIEW_SAFE_DISABLE_REF,
    preview_finance_review_persistence,
)
from ultimate_ai_agent.core.finance.service import (  # noqa: E402
    FinanceKernelService,
    finance_repository_ref,
    finance_target_ref,
)
from ultimate_ai_agent.core.finance.workspace import (  # noqa: E402
    FINANCE_WORKSPACE_MAX_BODY_BYTES,
    FinanceWorkspace,
    FinanceWorkspaceIntent,
    FinanceWorkspacePreparation,
    finance_workspace_body_within_limits,
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
    """Retain the existing CLI inspection helper over the shared Core location."""

    return finance_authority_state_dir(repository_dir)


def _request(args: argparse.Namespace) -> FinanceMutationRequest:
    backup_path = getattr(args, "backup_path", None)
    import_fixture_ref = getattr(args, "import_fixture_ref", None)
    review_item_ref = getattr(args, "review_item_ref", None)
    decision = getattr(args, "decision", None)
    compensates_event_ref = getattr(args, "compensates_event_ref", None)
    if args.operation in {"review_decision", "review_undo"}:
        if (
            review_item_ref is None
            or import_fixture_ref is not None
            or backup_path is not None
        ):
            raise ValueError("FIN003_REVIEW_CLI_SCOPE_INVALID")
        snapshot = _service(args).repository.load_snapshot_read_only(
            request_ref=args.request_ref
        )
        if snapshot.revision != args.expected_revision:
            raise ValueError("FINANCE_STALE_REVISION")
        review_preview = preview_finance_review_persistence(
            snapshot,
            review_item_ref=review_item_ref,
            decision=decision,
            compensates_event_ref=compensates_event_ref,
            request_ref=args.request_ref,
            idempotency_ref=args.idempotency_ref,
        )
        if review_preview.operation != args.operation:
            raise ValueError("FIN003_REVIEW_CLI_OPERATION_MISMATCH")
        return FinanceMutationRequest(
            operation=args.operation,
            repository_ref=review_preview.repository_ref,
            review_preview=review_preview,
            expected_revision=args.expected_revision,
            request_ref=args.request_ref,
            idempotency_ref=args.idempotency_ref,
            safe_disable_ref=FIN003_REVIEW_SAFE_DISABLE_REF,
        )
    if any(
        value is not None
        for value in (review_item_ref, decision, compensates_event_ref)
    ):
        raise ValueError("FIN003_REVIEW_CLI_OPERATION_MISMATCH")
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
    return _emit_prepared_bundle(request, preview)


def _emit_prepared_bundle(
    request: FinanceMutationRequest, preview: FinanceMutationPreview
) -> int:
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


def _read_prepared_bundle(
    path: Path,
) -> tuple[FinanceMutationRequest, FinanceMutationPreview]:
    raw = _read_json(path)
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
    return request, preview


def command_refresh_review(args: argparse.Namespace) -> int:
    """Re-present the exact old review intent, never recover or renew authority."""

    request, old_preview = _read_prepared_bundle(args.bundle)
    if request.operation not in {"review_decision", "review_undo"}:
        raise ValueError("FIN003_REVIEW_REFRESH_SCOPE_INVALID")
    service = _service(args)
    expected = service.prepare(request, now=old_preview.prepared_at)
    if (
        old_preview != expected
        or request.approval_ref != expected.expected_approval_ref
        or request.exact_scope_ref != expected.exact_scope_ref
        or request.action_envelope_ref != expected.action_envelope_ref
    ):
        raise ValueError("FIN003_REVIEW_REFRESH_BINDING_INVALID")
    # The source intent is unchanged, even when a staged generation prevents
    # read-only inspection. A separate confirmed run must obtain fresh current
    # authority and then recover/replay or validate the exact source under lock.
    return _emit_prepared_bundle(request, service.prepare(request))


def command_run(args: argparse.Namespace) -> int:
    if not args.confirmed:
        raise ValueError("FINANCE_OPERATOR_CONFIRMATION_REQUIRED")
    if args.safe_disable_engaged:
        raise ValueError("FINANCE_SAFE_DISABLE_ENGAGED")
    request, preview = _read_prepared_bundle(args.bundle)
    result = confirm_finance_mutation(
        _service(args),
        FinancePreparedMutation(request=request, preview=preview),
        confirmed=args.confirmed,
        actor_ref="actor-ref:finance:local-cli-operator",
        backup_path=args.backup_path,
        safe_disable_engaged=lambda: args.safe_disable_engaged,
    )
    _json(result)
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
    elif args.command == "review-decision-preview":
        snapshot = repository.load_snapshot_read_only(request_ref=args.request_ref)
        request = build_finance_review_decision_preview_request(
            snapshot,
            review_item_ref=args.review_item_ref,
            decision=args.decision,
        )
        payload = preview_finance_review_decision(snapshot, request).model_dump(
            mode="json"
        )
    else:
        payload = repository.export_redacted(request_ref=args.request_ref)
    _json(payload)
    return 0


def command_workspace(args: argparse.Namespace) -> int:
    """Inspect or operate the same server-configured book as Control Center."""

    workspace = FinanceWorkspace.from_env()
    if args.command == "workspace":
        view = workspace.read_view(
            item_offset=args.item_offset,
            history_offset=args.history_offset,
            limit=args.limit,
        )
        _json(view.model_dump(mode="json"))
        return 0 if view.status in {"ready", "book_setup_required"} else 2
    if args.command == "workspace-prepare":
        intent = FinanceWorkspaceIntent(
            operation=args.operation,
            expected_revision=args.expected_revision,
            request_ref=args.request_ref,
            idempotency_ref=args.idempotency_ref,
            review_item_ref=args.review_item_ref,
            decision=args.decision,
            compensates_event_ref=args.compensates_event_ref,
        )
        _json(workspace.prepare(intent).model_dump(mode="json"))
        return 0
    if args.command == "workspace-run" and not args.confirmed:
        raise ValueError("FINANCE_OPERATOR_CONFIRMATION_REQUIRED")
    if getattr(args, "safe_disable_engaged", False):
        raise ValueError("FINANCE_SAFE_DISABLE_ENGAGED")
    raw = FinanceRepository._read_regular(
        args.bundle, max_bytes=FINANCE_WORKSPACE_MAX_BODY_BYTES
    )
    if not finance_workspace_body_within_limits(raw):
        raise ValueError("FINANCE_WORKSPACE_REQUEST_BODY_LIMIT_EXCEEDED")
    preparation = FinanceWorkspacePreparation.model_validate_json(raw)
    if args.command == "workspace-refresh":
        _json(workspace.refresh_preparation(preparation).model_dump(mode="json"))
    else:
        _json(workspace.commit(preparation, confirmed=args.confirmed))
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
        choices=(
            "create",
            "import_commit",
            "review_decision",
            "review_undo",
            "backup",
            "restore",
            "delete",
        ),
        required=True,
    )
    prepare.add_argument("--expected-revision", type=int, required=True)
    prepare.add_argument("--request-ref", required=True)
    prepare.add_argument("--idempotency-ref", required=True)
    prepare.add_argument("--backup-path", type=Path)
    prepare.add_argument("--import-fixture-ref")
    prepare.add_argument("--review-item-ref")
    prepare.add_argument("--decision", choices=("confirm", "reject", "defer"))
    prepare.add_argument("--compensates-event-ref")
    prepare.set_defaults(func=command_prepare)
    refresh = commands.add_parser("refresh-review", parents=[shared])
    refresh.add_argument("--bundle", type=Path, required=True)
    refresh.set_defaults(func=command_refresh_review)
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
    decision_preview = commands.add_parser("review-decision-preview", parents=[shared])
    decision_preview.add_argument("--request-ref", required=True)
    decision_preview.add_argument("--review-item-ref", required=True)
    decision_preview.add_argument(
        "--decision", choices=("confirm", "reject", "defer"), required=True
    )
    decision_preview.set_defaults(func=command_read)
    workspace = commands.add_parser("workspace")
    workspace.add_argument("--item-offset", type=int, default=0)
    workspace.add_argument("--history-offset", type=int, default=0)
    workspace.add_argument("--limit", type=int, default=50)
    workspace.set_defaults(func=command_workspace)
    workspace_prepare = commands.add_parser("workspace-prepare")
    workspace_prepare.add_argument(
        "--operation",
        choices=("create", "import_commit", "review_decision", "review_undo"),
        required=True,
    )
    workspace_prepare.add_argument("--expected-revision", type=int, required=True)
    workspace_prepare.add_argument("--request-ref", required=True)
    workspace_prepare.add_argument("--idempotency-ref", required=True)
    workspace_prepare.add_argument("--review-item-ref")
    workspace_prepare.add_argument("--decision", choices=("confirm", "reject", "defer"))
    workspace_prepare.add_argument("--compensates-event-ref")
    workspace_prepare.set_defaults(func=command_workspace)
    for name in ("workspace-run", "workspace-refresh"):
        workspace_action = commands.add_parser(name)
        workspace_action.add_argument("--bundle", type=Path, required=True)
        if name == "workspace-run":
            workspace_action.add_argument("--confirmed", action="store_true")
            workspace_action.add_argument("--safe-disable-engaged", action="store_true")
        workspace_action.set_defaults(func=command_workspace)
    return result


def _safe_error_code(exc: Exception) -> str:
    """Never serialize exception text or Pydantic input into the CLI receipt."""

    candidate = str(exc)
    if re.fullmatch(r"(?:FINANCE|FIN00[123])_[A-Z0-9_]{1,100}", candidate):
        return candidate
    return "FINANCE_CLI_REQUEST_FAILED"


def main() -> int:
    args = parser().parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        _json(
            {
                "schema_version": "uaa-finance-cli-error.v1",
                "ok": False,
                "error_code": _safe_error_code(exc),
                "raw_input_included": False,
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
