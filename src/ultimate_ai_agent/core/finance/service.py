"""Governed execution service for the FIN-001 synthetic local kernel."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLease
from ultimate_ai_agent.core.finance.authority import (
    FinanceMutationGate,
    FinanceMutationPreview,
    FinanceMutationRequest,
)
from ultimate_ai_agent.core.finance.models import stable_finance_ref
from ultimate_ai_agent.core.finance.repository import (
    FinanceBackupMetadata,
    FinanceMutationOperation,
    FinanceMutationReceipt,
    FinanceRepository,
    FinanceRepositoryError,
)


def finance_repository_ref(root: Path) -> str:
    return stable_finance_ref(
        "repository-ref:finance/FIN-001",
        {"canonical_path": str(root.expanduser().resolve(strict=False))},
    )


def finance_target_ref(path: Path) -> str:
    return stable_finance_ref(
        "backup-path-ref:finance/FIN-001",
        {"canonical_path": str(path.expanduser().resolve(strict=False))},
    )


class FinanceKernelService:
    """Revalidate all three authorities at the final persistence boundary."""

    def __init__(self, repository: FinanceRepository) -> None:
        self.repository = repository
        self.gate = FinanceMutationGate()

    def prepare(
        self,
        request: FinanceMutationRequest,
        *,
        now: datetime | None = None,
    ) -> FinanceMutationPreview:
        self._validate_path_bindings(request)
        return self.gate.prepare(request, now=now)

    def execute(
        self,
        request: FinanceMutationRequest,
        *,
        preview: FinanceMutationPreview,
        approval_authority: LocalApprovalAuthority,
        lease_provider: Callable[[], Sequence[AuthorityLease]],
        clock: Callable[[], datetime] | None = None,
        backup_path: Path | None = None,
        safe_disable_engaged: Callable[[], bool] | None = None,
        kill_switch_engaged: Callable[[], bool] | None = None,
    ) -> FinanceMutationReceipt | tuple[FinanceBackupMetadata, FinanceMutationReceipt]:
        self._validate_path_bindings(request, backup_path=backup_path)
        now_provider = clock or (lambda: datetime.now(UTC))
        disabled = safe_disable_engaged or (lambda: False)
        killed = kill_switch_engaged or (lambda: False)

        def authorize():
            return self.gate.authorize(
                request,
                preview=preview,
                approval_authority=approval_authority,
                active_authority_leases=lease_provider(),
                now=now_provider(),
                safe_disable_engaged=disabled(),
                kill_switch_engaged=killed(),
            )

        permit = authorize()
        revalidate = authorize
        if request.operation == FinanceMutationOperation.create.value:
            return self.repository.create_from_fixture(
                permit=permit,
                revalidate=revalidate,
            )
        if request.operation == FinanceMutationOperation.backup.value:
            assert backup_path is not None
            return self.repository.backup(
                backup_path,
                permit=permit,
                revalidate=revalidate,
            )
        if request.operation == FinanceMutationOperation.restore.value:
            assert backup_path is not None
            return self.repository.restore(
                backup_path,
                permit=permit,
                revalidate=revalidate,
            )
        if request.operation == FinanceMutationOperation.delete.value:
            return self.repository.delete(permit=permit, revalidate=revalidate)
        raise FinanceRepositoryError("FINANCE_MUTATION_OPERATION_UNSUPPORTED")

    def _validate_path_bindings(
        self,
        request: FinanceMutationRequest,
        *,
        backup_path: Path | None = None,
    ) -> None:
        if request.repository_ref != finance_repository_ref(self.repository.root):
            raise FinanceRepositoryError("FINANCE_REPOSITORY_REF_PATH_MISMATCH")
        if request.operation in {"backup", "restore"}:
            if backup_path is None:
                if request.target_ref is None:
                    raise FinanceRepositoryError("FINANCE_TARGET_REF_REQUIRED")
                return
            if request.target_ref != finance_target_ref(backup_path):
                raise FinanceRepositoryError("FINANCE_TARGET_REF_PATH_MISMATCH")
        elif backup_path is not None:
            raise FinanceRepositoryError("FINANCE_BACKUP_PATH_OUT_OF_SCOPE")
