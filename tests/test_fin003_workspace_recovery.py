"""Browser lifetime cannot own the exact identity of an attempted Finance save."""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from ultimate_ai_agent.core.finance import workspace as workspace_module
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.operator_workflow import prepare_finance_mutation
from ultimate_ai_agent.core.finance.workspace import (
    FinanceWorkspace,
    FinanceWorkspaceConfiguration,
    FinanceWorkspaceIntent,
)
from ultimate_ai_agent.core.finance.workspace_recovery import (
    FinanceWorkspaceRecoveryStore,
)


@pytest.fixture
def workspace(tmp_path):
    return FinanceWorkspace(
        FinanceWorkspaceConfiguration(tmp_path / "book", tmp_path / "helper", "a" * 64),
        crypto_backend=InMemoryFinanceCryptoBackend(),
    )


def _intent(operation, revision, **extra):
    return FinanceWorkspaceIntent(
        operation=operation,
        expected_revision=revision,
        request_ref=f"request-ref:finance:recovery-{operation}",
        idempotency_ref=f"idempotency-ref:finance:recovery-{operation}",
        **extra,
    )


def _prepare(workspace, operation):
    if operation != "create":
        workspace.commit(workspace.prepare(_intent("create", 0)), confirmed=True)
    if operation in {"review_decision", "review_undo"}:
        workspace.commit(workspace.prepare(_intent("import_commit", 1)), confirmed=True)
    if operation == "review_undo":
        item = workspace.read_view().review_items[0]
        workspace.commit(
            workspace.prepare(
                _intent(
                    "review_decision",
                    2,
                    review_item_ref=item.review_item_ref,
                    decision="confirm",
                )
            ),
            confirmed=True,
        )
    view = workspace.read_view()
    extra = {}
    if operation in {"review_decision", "review_undo"}:
        item = view.review_items[0]
        extra["review_item_ref"] = item.review_item_ref
        if operation == "review_decision":
            extra["decision"] = "confirm"
        else:
            extra["compensates_event_ref"] = item.effective_decision_ref
    return workspace.prepare(_intent(operation, view.revision, **extra))


def _reopen(workspace):
    return FinanceWorkspace(
        workspace.configuration, crypto_backend=workspace.service.repository.crypto
    )


OPERATIONS = ["create", "import_commit", "review_decision", "review_undo"]


@pytest.mark.parametrize("operation", OPERATIONS)
def test_restart_retains_attempt_before_any_execution_and_requires_same_intent(
    workspace, monkeypatch, operation
):
    preparation = _prepare(workspace, operation)
    original = workspace_module.confirm_finance_mutation

    def stopped(*args, **kwargs):
        raise RuntimeError("FINANCE_SYNTHETIC_INTERRUPTION")

    monkeypatch.setattr(workspace_module, "confirm_finance_mutation", stopped)
    with pytest.raises(RuntimeError, match="SYNTHETIC_INTERRUPTION"):
        workspace.commit(preparation, confirmed=True)
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)
    before = store.read()
    reopened = _reopen(workspace)
    retained = reopened.read_view().recovery
    assert retained is not None and retained.result is None
    assert retained.preparation.bundle.request == preparation.bundle.request
    assert store.read() == before  # read and fresh presentation are non-mutating
    replacement = retained.intent.model_copy(
        update={"request_ref": "request-ref:finance:replacement"}
    )
    with pytest.raises(ValueError, match="SAME_INTENT"):
        reopened.prepare(replacement)
    with pytest.raises(ValueError, match="OPERATOR_CONFIRMATION_REQUIRED"):
        reopened.commit(retained.preparation, confirmed=False)
    reopened.safe_disable_engaged = lambda: True
    with pytest.raises(ValueError, match="SAFE_DISABLE_ENGAGED"):
        reopened.commit(retained.preparation, confirmed=True)
    assert store.read() == before
    reopened.safe_disable_engaged = lambda: False
    monkeypatch.setattr(workspace_module, "confirm_finance_mutation", original)
    fresh = reopened.refresh_preparation(retained.preparation)
    assert store.read() == before
    result = reopened.commit(fresh, confirmed=True)
    assert (
        result["receipt"]["after_revision"]
        == preparation.bundle.request.expected_revision + 1
    )
    assert (
        reopened.read_view().recovery.result.receipt.receipt_ref
        == result["receipt"]["receipt_ref"]
    )


@pytest.mark.parametrize("operation", OPERATIONS)
def test_restart_retains_historical_receipt_when_commit_response_is_lost(
    workspace, operation
):
    preparation = _prepare(workspace, operation)
    result = workspace.commit(preparation, confirmed=True)
    reopened = _reopen(workspace)
    retained = reopened.read_view().recovery
    assert retained.result.model_dump(mode="json") == result
    assert retained.intent.request_ref == preparation.bundle.request.request_ref
    replay = reopened.commit(retained.preparation, confirmed=True)
    assert replay["receipt"]["replayed"] is True
    assert replay["receipt"]["receipt_ref"] == result["receipt"]["receipt_ref"]


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("expired", [False, True])
def test_historical_attempt_replays_after_a_later_completed_action(
    workspace, operation, expired
):
    preparation = _prepare(workspace, operation)
    original = workspace.commit(preparation, confirmed=True)
    view = workspace.read_view()
    if operation == "create":
        next_intent = _intent("import_commit", view.revision)
    else:
        next_intent = _intent(
            "review_decision",
            view.revision,
            review_item_ref=view.review_items[0].review_item_ref,
            decision="defer",
        ).model_copy(
            update={
                "request_ref": "request-ref:finance:later-action",
                "idempotency_ref": "idempotency-ref:finance:later-action",
            }
        )
    later = workspace.commit(workspace.prepare(next_intent), confirmed=True)
    reopened = _reopen(workspace)
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)
    before = store.read()
    assert (
        reopened.read_view().recovery.result.receipt.receipt_ref
        == later["receipt"]["receipt_ref"]
    )
    if expired:
        preparation = preparation.model_copy(
            update={
                "bundle": prepare_finance_mutation(
                    reopened.service,
                    preparation.bundle.request,
                    now=datetime.now(timezone.utc) - timedelta(days=1),
                )
            }
        )
        with pytest.raises(
            workspace_module.FinanceWorkspaceCommitNotAttempted, match="NOT_CURRENT"
        ):
            reopened.commit(preparation, confirmed=True)
    refreshed = reopened.refresh_preparation(preparation)
    assert store.read() == before
    assert refreshed.bundle.request == preparation.bundle.request
    assert (
        refreshed.bundle.preview.payload_fingerprint_ref
        == preparation.bundle.preview.payload_fingerprint_ref
    )
    replay = reopened.commit(refreshed, confirmed=True)
    assert replay["receipt"]["receipt_ref"] == original["receipt"]["receipt_ref"]
    assert replay["receipt"]["replayed"] is True
    assert reopened.read_view().revision == later["receipt"]["after_revision"]


@pytest.mark.parametrize("operation", OPERATIONS)
def test_secondary_result_write_failure_does_not_erase_core_success(
    workspace, monkeypatch, operation
):
    preparation = _prepare(workspace, operation)
    original = FinanceWorkspaceRecoveryStore.write

    def interrupted(store, payload):
        if json.loads(payload)["result"] is not None:
            raise OSError("synthetic result-store failure")
        return original(store, payload)

    monkeypatch.setattr(FinanceWorkspaceRecoveryStore, "write", interrupted)
    result = workspace.commit(preparation, confirmed=True)
    assert result["receipt"]["phase"] == "committed"
    reopened = _reopen(workspace)
    retained = reopened.read_view().recovery
    assert retained.result is None
    monkeypatch.setattr(FinanceWorkspaceRecoveryStore, "write", original)
    replay = reopened.commit(retained.preparation, confirmed=True)
    assert replay["receipt"]["receipt_ref"] == result["receipt"]["receipt_ref"]
    assert replay["receipt"]["replayed"] is True


def test_historical_receipt_remains_available_when_snapshot_read_fails(
    workspace, monkeypatch
):
    result = workspace.commit(_prepare(workspace, "create"), confirmed=True)
    reopened = _reopen(workspace)

    def unavailable(**kwargs):
        raise RuntimeError("FINANCE_SYNTHETIC_READ_UNAVAILABLE")

    monkeypatch.setattr(
        reopened.service.repository, "load_snapshot_read_only", unavailable
    )
    view = reopened.read_view()
    assert view.status == "unavailable"
    assert view.recovery.result.receipt.receipt_ref == result["receipt"]["receipt_ref"]
    assert view.revision is None  # historical receipt is not current book proof


def test_preview_unconfirmed_and_disabled_do_not_create_recovery_state(workspace):
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)
    preparation = _prepare(workspace, "create")
    assert store.read() is None and not store.directory.exists()
    assert workspace.read_view().recovery is None
    with pytest.raises(ValueError, match="CONFIRMATION_REQUIRED"):
        workspace.commit(preparation, confirmed=False)
    workspace.safe_disable_engaged = lambda: True
    with pytest.raises(ValueError, match="SAFE_DISABLE"):
        workspace.commit(preparation, confirmed=True)
    assert not store.directory.exists()


def test_another_process_attempt_fails_promptly_without_changing_slot(workspace):
    preparation = _prepare(workspace, "create")
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)
    with store.confirmed_attempt():
        with pytest.raises(
            workspace_module.FinanceWorkspaceCommitNotAttempted, match="ATTEMPT_BUSY"
        ):
            workspace.commit(preparation, confirmed=True)
    assert store.read() is None
    assert not workspace.configuration.repository_dir.exists()


def test_failed_initial_recovery_write_is_not_a_book_attempt(workspace, monkeypatch):
    preparation = _prepare(workspace, "create")

    def cannot_retain(*args, **kwargs):
        raise OSError("synthetic metadata write failure")

    monkeypatch.setattr(FinanceWorkspaceRecoveryStore, "write", cannot_retain)
    with pytest.raises(workspace_module.FinanceWorkspaceCommitNotAttempted):
        workspace.commit(preparation, confirmed=True)
    assert not workspace.configuration.repository_dir.exists()
    assert (
        FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir).read()
        is None
    )


def test_stale_second_tab_cannot_replace_the_completed_attempt_with_a_dead_end(
    workspace,
):
    first = _prepare(workspace, "create")
    other_intent = _intent("create", 0).model_copy(
        update={
            "request_ref": "request-ref:finance:other-tab",
            "idempotency_ref": "idempotency-ref:finance:other-tab",
        }
    )
    second = workspace.prepare(other_intent)
    saved = workspace.commit(first, confirmed=True)
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)
    before = store.read()
    with pytest.raises(
        workspace_module.FinanceWorkspaceCommitNotAttempted, match="ALREADY_EXISTS"
    ):
        workspace.commit(second, confirmed=True)
    assert store.read() == before
    assert (
        workspace.read_view().recovery.result.receipt.receipt_ref
        == saved["receipt"]["receipt_ref"]
    )
    assert workspace.prepare(_intent("import_commit", 1))


@pytest.mark.parametrize(
    "damage", ["oversize", "corrupt", "public", "symlink", "hardlink", "fifo"]
)
def test_damaged_recovery_record_fails_closed_without_replacement(
    workspace, damage, tmp_path
):
    workspace.commit(_prepare(workspace, "create"), confirmed=True)
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)
    if damage == "oversize":
        store.path.write_bytes(b"x" * (128 * 1024 + 1))
    elif damage == "corrupt":
        store.path.write_bytes(b"{not valid}")
    elif damage == "public":
        store.path.chmod(0o644)
    elif damage == "symlink":
        target = tmp_path / "retained-record"
        store.path.rename(target)
        store.path.symlink_to(target)
    elif damage == "hardlink":
        os.link(store.path, tmp_path / "linked-record")
    else:
        store.path.unlink()
        os.mkfifo(store.path, 0o600)
    reopened = _reopen(workspace)
    assert reopened.read_view().status == "unavailable"
    assert reopened.read_view().recovery is None
    with pytest.raises((OSError, RuntimeError, ValueError)):
        reopened.prepare(_intent("import_commit", 1))


@pytest.mark.parametrize("field", ["configuration", "intent", "receipt", "lease"])
def test_retained_binding_substitution_is_not_presented(workspace, field):
    workspace.commit(_prepare(workspace, "create"), confirmed=True)
    store = FinanceWorkspaceRecoveryStore(workspace.configuration.repository_dir)
    payload = json.loads(store.read())
    if field == "configuration":
        payload["preparation"]["configuration_ref"] = "configuration-ref:foreign"
    elif field == "intent":
        payload["intent"]["request_ref"] = "request-ref:foreign"
    elif field == "receipt":
        payload["result"]["receipt"]["request_ref"] = "request-ref:foreign"
    else:
        payload["result"]["lease_receipt_ref"] = "not a safe reference"
    store.write(json.dumps(payload).encode())
    view = _reopen(workspace).read_view()
    assert view.status == "unavailable"
    assert view.recovery is None
