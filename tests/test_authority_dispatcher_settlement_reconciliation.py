from pathlib import Path
from typing import Any

import pytest

from tests.test_authority_dispatcher import (
    FILESYSTEM_ROOT_REF,
    _descriptor,
    _lease,
    _request,
)
from ultimate_ai_agent.core.authority import (
    AuthorityBudgetStatus,
    AuthorityCapability,
    AuthorityDispatchRequest,
    AuthorityDispatchStatus,
    AuthorityDomain,
    TrustMode,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    ToolRuntimeAuthorityDispatchAdapter,
)
from ultimate_ai_agent.core.tools.runtime import FilesystemSafeRoot


def test_settled_start_reconciles_terminal_truth_without_second_invocation(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "authority"
    root = tmp_path / "safe-root"
    (root / "notes").mkdir(parents=True)
    (root / "notes" / "report.md").write_text("bounded", encoding="utf-8")
    lease_store, lease = _lease(
        state_dir,
        mode=TrustMode.full_local_workspace_session,
        domain=AuthorityDomain.files,
        capability=AuthorityCapability.read,
    )
    adapter = ToolRuntimeAuthorityDispatchAdapter(
        _descriptor(filesystem=True),
        safe_roots=[
            FilesystemSafeRoot(
                root_ref=FILESYSTEM_ROOT_REF,
                root_path=root,
                safe_label="Test dispatch safe root",
            )
        ],
    )
    invoke = adapter.invoke
    invocation_count = 0

    def counted_invoke(request: AuthorityDispatchRequest):
        nonlocal invocation_count
        invocation_count += 1
        return invoke(request)

    adapter.invoke = counted_invoke  # type: ignore[method-assign]
    dispatcher = AuthorityDispatcher(
        state_dir,
        adapters=[adapter],
        lease_store=lease_store,
    )
    request = _request(
        lease.lease_ref,
        suffix="settlement-terminal-crash",
        filesystem=True,
    )
    dispatcher.prepare(request)
    append = dispatcher._append

    def crash_before_terminal(receipt: Any) -> None:
        if receipt.status == AuthorityDispatchStatus.succeeded.value:
            raise RuntimeError("simulated crash after budget settlement")
        append(receipt)

    dispatcher._append = crash_before_terminal  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash after budget settlement"):
        dispatcher.execute(request)
    dispatcher._append = append  # type: ignore[method-assign]

    recovered = dispatcher.dispatch(request)
    replay = dispatcher.dispatch(request)

    assert recovered.receipt.status == AuthorityDispatchStatus.succeeded.value
    assert recovered.replayed is True
    assert recovered.recovery_required is False
    assert (
        "reason-ref:authority-dispatch:settlement-reconciled"
        in recovered.receipt.reason_refs
    )
    assert replay.receipt.receipt_ref == recovered.receipt.receipt_ref
    assert invocation_count == 1
    assert [
        receipt.status for receipt in dispatcher.budget_store.list_receipts()
    ] == [
        AuthorityBudgetStatus.reserved.value,
        AuthorityBudgetStatus.started.value,
        AuthorityBudgetStatus.settled.value,
    ]
    assert [receipt.status for receipt in dispatcher.list_receipts()] == [
        AuthorityDispatchStatus.prepared.value,
        AuthorityDispatchStatus.started.value,
        AuthorityDispatchStatus.succeeded.value,
    ]
