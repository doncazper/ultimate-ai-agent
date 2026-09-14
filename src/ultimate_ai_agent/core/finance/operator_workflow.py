"""Shared, exact-confirmed Finance operator workflow; shells are not authority."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import hashlib
import os
from pathlib import Path
import stat
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.authority.approval_validation import (
    issue_authority_lease_with_backend_approval,
)
from ultimate_ai_agent.core.finance.authority import (
    FinanceMutationPreview,
    FinanceMutationRequest,
    build_finance_lease_issue_request,
)
from ultimate_ai_agent.core.finance.import_commit import FinanceImportCommitProof
from ultimate_ai_agent.core.finance.models import stable_finance_ref
from ultimate_ai_agent.core.finance.service import FinanceKernelService
from ultimate_ai_agent.core.planning.validation import validate_task_ref


class FinancePreparedMutation(BaseModel):
    """The existing CLI preparation envelope, also carried by the local API."""

    schema_version: Literal["uaa-finance-prepared-mutation-bundle.v1"] = (
        "uaa-finance-prepared-mutation-bundle.v1"
    )
    request: FinanceMutationRequest
    preview: FinanceMutationPreview
    mutation_performed: Literal[False] = False
    operator_confirmation_required: Literal[True] = True

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


def prepare_finance_mutation(
    service: FinanceKernelService,
    request: FinanceMutationRequest,
    *,
    now: datetime | None = None,
) -> FinancePreparedMutation:
    """Prepare without creating a book, key, approval store or lease."""

    preview = service.prepare(request, now=now)
    bound = FinanceMutationRequest.model_validate(
        {
            **request.model_dump(mode="python"),
            "approval_ref": preview.expected_approval_ref,
            "exact_scope_ref": preview.exact_scope_ref,
            "action_envelope_ref": preview.action_envelope_ref,
        }
    )
    return FinancePreparedMutation(request=bound, preview=preview)


def finance_authority_state_dir(repository_dir: Path) -> Path:
    """Use the existing private, repository-bound CLI authority location."""

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


def confirm_finance_mutation(
    service: FinanceKernelService,
    bundle: FinancePreparedMutation,
    *,
    confirmed: bool,
    actor_ref: str,
    safe_disable_engaged: Callable[[], bool],
    backup_path: Path | None = None,
) -> dict[str, object]:
    """Capture exact confirmation, then execute through the existing Core gate.

    Current policy, stored approval, active lease, safe-disable, source and
    revision are still revalidated by FinanceKernelService at promotion. This
    function does not reimplement generation recovery or create standing access.
    """

    if confirmed is not True:
        raise ValueError("FINANCE_OPERATOR_CONFIRMATION_REQUIRED")
    if safe_disable_engaged():
        raise ValueError("FINANCE_SAFE_DISABLE_ENGAGED")
    validate_task_ref(actor_ref, "finance_operator_actor_ref")
    request, preview = bundle.request, bundle.preview
    service._validate_path_bindings(request, backup_path=backup_path)
    # Reject substituted preparation before creating any authority state. The
    # service repeats this validation, including expiry, immediately before use.
    expected = prepare_finance_mutation(service, request, now=preview.prepared_at)
    if bundle != expected:
        raise ValueError("FINANCE_PREPARED_BUNDLE_BINDING_INVALID")

    approvals = LocalApprovalAuthority()
    approvals.create_request(preview.approval_request)
    approvals.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id=actor_ref,
        approval_ref=preview.expected_approval_ref,
        expires_at=preview.expires_at,
    )
    lease_store = AuthorityLeaseStore(
        finance_authority_state_dir(service.repository.root)
    )
    lease_binding = {"payload_fingerprint_ref": preview.payload_fingerprint_ref}
    if request.operation in {"review_decision", "review_undo"}:
        # A repeated bundle cannot revive a revoked lease. A freshly presented,
        # separately confirmed preview may authorize retry of the same intent.
        lease_binding["reviewed_authority_preview_ref"] = preview.preview_ref
    issue_idempotency_ref = stable_finance_ref(
        "idempotency-ref:finance/FIN-001:lease-issue", lease_binding
    )
    _requirement, _grant, lease, lease_receipt = (
        issue_authority_lease_with_backend_approval(
            lease_store,
            build_finance_lease_issue_request(preview),
            idempotency_ref=issue_idempotency_ref,
            approved_by_actor_id=actor_ref,
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
        backup_path=backup_path,
        safe_disable_engaged=safe_disable_engaged,
    )
    payload: dict[str, object]
    if isinstance(result, tuple):
        evidence, receipt = result
        payload = {
            "import_commit"
            if isinstance(evidence, FinanceImportCommitProof)
            else "backup": evidence.model_dump(mode="json"),
            "receipt": receipt.model_dump(mode="json"),
        }
    else:
        payload = {"receipt": result.model_dump(mode="json")}
    return {
        "schema_version": "uaa-finance-cli-mutation-result.v1",
        **payload,
        "lease_receipt_ref": lease_receipt.receipt_ref,
        "synthetic_only": True,
        "real_financial_data_included": False,
    }
