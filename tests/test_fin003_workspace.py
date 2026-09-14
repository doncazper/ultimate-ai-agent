"""The in-app synthetic journey uses durable Core truth, never UI authority."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from jsonschema import Draft202012Validator

from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.operator_workflow import prepare_finance_mutation
from ultimate_ai_agent.core.finance.repository import FinanceRepository
from ultimate_ai_agent.core.finance.workspace import (
    FINANCE_WORKSPACE_DISABLE_ENV,
    FINANCE_WORKSPACE_HELPER_DIGEST_ENV,
    FINANCE_WORKSPACE_HELPER_ENV,
    FINANCE_WORKSPACE_REPOSITORY_ENV,
    FinanceWorkspace,
    FinanceWorkspaceConfiguration,
    FinanceWorkspaceIntent,
    FinanceWorkspacePreparation,
    finance_workspace_safe_disable,
)


@pytest.fixture
def workspace(tmp_path):
    configuration = FinanceWorkspaceConfiguration(
        tmp_path / "book", tmp_path / "pinned-helper", "a" * 64
    )
    return FinanceWorkspace(
        configuration, crypto_backend=InMemoryFinanceCryptoBackend()
    )


def intent(operation, revision, suffix, **fields):
    return FinanceWorkspaceIntent(
        operation=operation,
        expected_revision=revision,
        request_ref=f"request-ref:finance:workspace-{suffix}",
        idempotency_ref=f"idempotency-ref:finance:workspace-{suffix}",
        **fields,
    )


def commit(workspace, operation, revision, suffix, **fields):
    preparation = workspace.prepare(intent(operation, revision, suffix, **fields))
    return preparation, workspace.commit(preparation, confirmed=True)


def test_sample_setup_import_review_reopen_replay_and_undo(workspace):
    initial = workspace.read_view()
    assert initial.status == "book_setup_required"
    assert initial.revision == 0
    root = workspace.service.repository.root
    assert not root.exists()
    prepared, created = commit(workspace, "create", 0, "create")
    assert created["receipt"]["phase"] == "committed"
    assert workspace.commit(prepared, confirmed=True)["receipt"]["replayed"] is True
    assert workspace.read_view().import_available is True
    imported, result = commit(workspace, "import_commit", 1, "import")
    assert result["receipt"]["after_revision"] == 2
    assert workspace.commit(imported, confirmed=True)["receipt"]["replayed"] is True
    view = workspace.read_view()
    assert view.status == "ready"
    assert view.item_count == 2
    assert view.import_available is False
    before = workspace.service.repository.load_snapshot_read_only(
        request_ref="request-ref:finance:before-review"
    )
    prepared, saved = commit(
        workspace,
        "review_decision",
        2,
        "save",
        review_item_ref=view.review_items[0].review_item_ref,
        decision="confirm",
    )
    reopened = FinanceWorkspace(
        workspace.configuration, crypto_backend=workspace.service.repository.crypto
    )
    read = reopened.read_view()
    assert read.review_items[0].state == "confirmed"
    assert read.history_count == 1
    assert (
        reopened.commit(prepared, confirmed=True)["receipt"]["receipt_ref"]
        == saved["receipt"]["receipt_ref"]
    )
    _undo, result = commit(
        reopened,
        "review_undo",
        3,
        "undo",
        review_item_ref=read.review_items[0].review_item_ref,
        compensates_event_ref=read.review_items[0].effective_decision_ref,
    )
    final = reopened.read_view()
    assert final.review_items[0].state == "needs_review"
    assert final.history_count == 2
    assert result["receipt"]["operation"] == "review_undo"
    after = reopened.service.repository.load_snapshot_read_only(
        request_ref="request-ref:finance:after-review"
    )
    assert after.journal_entries == before.journal_entries
    assert after.account_balances() == before.account_balances()
    assert str(root) not in final.model_dump_json()


def test_missing_configuration_does_not_select_or_initialize_a_book(monkeypatch):
    for name in (
        FINANCE_WORKSPACE_REPOSITORY_ENV,
        FINANCE_WORKSPACE_HELPER_ENV,
        FINANCE_WORKSPACE_HELPER_DIGEST_ENV,
    ):
        monkeypatch.delenv(name, raising=False)
    workspace = FinanceWorkspace.from_env()
    assert workspace.service is None
    assert workspace.read_view().status == "configuration_missing"
    with pytest.raises(ValueError, match="CONFIGURATION_REQUIRED"):
        workspace.prepare(intent("create", 0, "missing"))


def test_environment_cannot_select_memory_crypto(monkeypatch, tmp_path):
    monkeypatch.setenv(FINANCE_WORKSPACE_REPOSITORY_ENV, str(tmp_path / "book"))
    monkeypatch.setenv(FINANCE_WORKSPACE_HELPER_ENV, str(tmp_path / "missing-helper"))
    monkeypatch.setenv(FINANCE_WORKSPACE_HELPER_DIGEST_ENV, "a" * 64)
    workspace = FinanceWorkspace.from_env()
    assert not isinstance(
        workspace.service.repository.crypto, InMemoryFinanceCryptoBackend
    )
    assert workspace.read_view().status == "helper_unavailable"
    assert not (tmp_path / "book").exists()


@pytest.mark.parametrize(
    "values",
    [
        ("relative-book", "/sample-helper", "a" * 64),
        ("/sample-book", "relative-helper", "a" * 64),
        ("/sample-book", "/sample-helper", "unbound"),
    ],
)
def test_configuration_requires_absolute_locations_and_digest(values):
    with pytest.raises(ValueError, match="CONFIGURATION_INVALID"):
        FinanceWorkspaceConfiguration(Path(values[0]), Path(values[1]), values[2])


@pytest.mark.parametrize(
    "value,expected",
    [("false", False), ("0", False), ("true", True), ("unknown", True), ("", True)],
)
def test_safe_disable_configuration_fails_closed(value, expected):
    assert (
        finance_workspace_safe_disable({FINANCE_WORKSPACE_DISABLE_ENV: value})
        is expected
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("operation", "delete"),
        ("operation", "restore"),
        ("expected_revision", True),
        ("expected_revision", -1),
        ("expected_revision", 1),
        ("request_ref", "x" * 201),
        ("repository_dir", "not-admitted"),
        ("review_item_ref", "item-ref:unrelated"),
    ],
)
def test_intent_excludes_broader_authority_and_oversized_inputs(field, value):
    data = intent("create", 0, "bounds").model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        FinanceWorkspaceIntent.model_validate(data)


@pytest.mark.parametrize(
    "value",
    [
        "id:a",
        "id:abcd",
        "idempotency-ref:finance/action",
        "id:review@account",
        "id:abcde ",
        "id:" + "a" * 198,
    ],
)
def test_intent_and_preparation_reject_transport_incompatible_idempotency(
    workspace, value
):
    data = intent("create", 0, "header-shape").model_dump()
    data["idempotency_ref"] = value
    with pytest.raises(ValidationError):
        FinanceWorkspaceIntent.model_validate(data)
    assert not Draft202012Validator(
        FinanceWorkspaceIntent.model_json_schema()
    ).is_valid(data)
    prepared = workspace.prepare(intent("create", 0, "header-shape"))
    payload = prepared.model_dump(mode="json")
    payload["bundle"]["request"]["idempotency_ref"] = value
    with pytest.raises(ValidationError):
        FinanceWorkspacePreparation.model_validate(payload)
    assert not Draft202012Validator(
        FinanceWorkspacePreparation.model_json_schema()
    ).is_valid(payload)
    assert not workspace.configuration.repository_dir.exists()


@pytest.mark.parametrize("value", ["id:abcde", "id:a_B-9.c:D", "id:" + "a" * 197])
def test_transport_compatible_idempotency_boundaries_prepare_without_writes(
    workspace, value
):
    data = intent("create", 0, "header-shape").model_dump()
    data["idempotency_ref"] = value
    prepared = workspace.prepare(FinanceWorkspaceIntent.model_validate(data))
    assert prepared.bundle.request.idempotency_ref == value
    assert Draft202012Validator(
        FinanceWorkspacePreparation.model_json_schema()
    ).is_valid(prepared.model_dump(mode="json"))
    assert not workspace.configuration.repository_dir.exists()


def test_configuration_substitution_is_rejected_before_writes(workspace):
    prepared = workspace.prepare(intent("create", 0, "create"))
    other_configuration = FinanceWorkspaceConfiguration(
        workspace.configuration.repository_dir,
        workspace.configuration.helper_path,
        "b" * 64,
    )
    changed = FinanceWorkspace(
        other_configuration, crypto_backend=workspace.service.repository.crypto
    )
    with pytest.raises(ValueError, match="CONFIGURATION_CHANGED"):
        changed.commit(prepared, confirmed=True)
    assert not workspace.service.repository.root.exists()


def test_unconfirmed_or_disabled_operations_do_not_initialize(workspace):
    prepared = workspace.prepare(intent("create", 0, "create"))
    with pytest.raises(ValueError, match="OPERATOR_CONFIRMATION_REQUIRED"):
        workspace.commit(prepared, confirmed=False)
    workspace.safe_disable_engaged = lambda: True
    with pytest.raises(ValueError, match="SAFE_DISABLE_ENGAGED"):
        workspace.commit(prepared, confirmed=True)
    with pytest.raises(ValueError, match="SAFE_DISABLE_ENGAGED"):
        workspace.prepare(intent("create", 0, "disabled"))
    assert not workspace.service.repository.root.exists()


def test_stale_selection_and_duplicate_import_require_new_review(workspace):
    commit(workspace, "create", 0, "create")
    commit(workspace, "import_commit", 1, "import")
    with pytest.raises(ValueError, match="STALE_REVISION"):
        workspace.prepare(intent("import_commit", 1, "stale"))
    with pytest.raises(ValueError, match="SAMPLE_ALREADY_IMPORTED"):
        workspace.prepare(intent("import_commit", 2, "duplicate"))


def test_interrupted_write_read_is_uncertain_and_does_not_recover(
    workspace, monkeypatch
):
    commit(workspace, "create", 0, "create")
    commit(workspace, "import_commit", 1, "import")
    view = workspace.read_view()
    prepared = workspace.prepare(
        intent(
            "review_decision",
            2,
            "interrupt",
            review_item_ref=view.review_items[0].review_item_ref,
            decision="defer",
        )
    )
    recover = FinanceRepository._recover_pending_commit

    def interrupt(self, **kwargs):
        if self.pending_commit_path.exists():
            raise RuntimeError("FINANCE_TEST_INTERRUPT")
        return recover(self, **kwargs)

    monkeypatch.setattr(FinanceRepository, "_recover_pending_commit", interrupt)
    with pytest.raises(RuntimeError, match="TEST_INTERRUPT"):
        workspace.commit(prepared, confirmed=True)
    path = workspace.service.repository.pending_commit_path
    before = path.read_bytes()
    reopened = FinanceWorkspace(
        workspace.configuration, crypto_backend=workspace.service.repository.crypto
    )
    retained = reopened.read_view()
    assert retained.status == "outcome_uncertain"
    assert retained.pending_review is not None
    assert retained.pending_review.preparation.bundle.request == prepared.bundle.request
    assert path.read_bytes() == before
    monkeypatch.setattr(FinanceRepository, "_recover_pending_commit", recover)
    # Neither the previous browser state nor its preparation is needed.
    refreshed = reopened.refresh_preparation(retained.pending_review.preparation)
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="OPERATOR_CONFIRMATION_REQUIRED"):
        reopened.commit(refreshed, confirmed=False)
    assert path.read_bytes() == before
    reopened.safe_disable_engaged = lambda: True
    with pytest.raises(ValueError, match="SAFE_DISABLE_ENGAGED"):
        reopened.commit(refreshed, confirmed=True)
    assert path.read_bytes() == before
    reopened.safe_disable_engaged = lambda: False
    reopened.commit(refreshed, confirmed=True)
    assert reopened.read_view().review_items[0].state == "deferred"


def staged_review(workspace, monkeypatch, *, undo=False, promoted=None):
    commit(workspace, "create", 0, "create")
    commit(workspace, "import_commit", 1, "import")
    view = workspace.read_view()
    if undo:
        commit(
            workspace,
            "review_decision",
            2,
            "saved",
            review_item_ref=view.review_items[0].review_item_ref,
            decision="confirm",
        )
        view = workspace.read_view()
    prepared = workspace.prepare(
        intent(
            "review_undo" if undo else "review_decision",
            view.revision,
            "interrupted",
            review_item_ref=view.review_items[0].review_item_ref,
            **(
                {"compensates_event_ref": view.review_items[0].effective_decision_ref}
                if undo
                else {"decision": "reject"}
            ),
        )
    )
    recover = FinanceRepository._recover_pending_commit

    def interrupt(self, **kwargs):
        if self.pending_commit_path.exists():
            metadata, _receipt, ciphertext = self._read_pending_generation()
            if promoted in {"ciphertext", "metadata"}:
                self._atomic_write(self.encrypted_path, ciphertext)
            if promoted == "metadata":
                self._atomic_write_json(
                    self.metadata_path, metadata.model_dump(mode="json")
                )
            raise RuntimeError("FINANCE_TEST_INTERRUPT")
        return recover(self, **kwargs)

    with monkeypatch.context() as patched:
        patched.setattr(FinanceRepository, "_recover_pending_commit", interrupt)
        with pytest.raises(RuntimeError, match="TEST_INTERRUPT"):
            workspace.commit(prepared, confirmed=True)
    return prepared


@pytest.mark.parametrize("undo", [False, True])
@pytest.mark.parametrize("promoted", [None, "ciphertext", "metadata"])
def test_pending_inspection_binds_partial_generations_without_writes(
    workspace, monkeypatch, undo, promoted
):
    prepared = staged_review(workspace, monkeypatch, undo=undo, promoted=promoted)
    repository = workspace.service.repository
    before = {
        path.name: path.read_bytes()
        for path in repository.root.iterdir()
        if path.is_file()
    }
    reopened = FinanceWorkspace(
        workspace.configuration, crypto_backend=repository.crypto
    )
    retained = reopened.read_view().pending_review
    assert retained is not None
    assert retained.preparation.bundle.request == prepared.bundle.request
    assert before == {
        path.name: path.read_bytes()
        for path in repository.root.iterdir()
        if path.is_file()
    }
    result = reopened.commit(retained.preparation, confirmed=True)
    assert result["receipt"]["replayed"] is True
    assert reopened.read_view().history_count == (2 if undo else 1)
    assert not repository.pending_commit_path.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("operation", "import_commit"),
        ("request_ref", "request-ref:finance:substituted"),
        ("idempotency_ref", "idempotency-ref:finance:substituted"),
        ("payload_fingerprint_ref", "fingerprint-ref:finance:substituted"),
        ("before_snapshot_ref", "snapshot-ref:finance:substituted"),
        ("after_revision", 999),
        ("proof_refs", []),
    ],
)
def test_pending_header_substitution_never_presents_a_retry(
    workspace, monkeypatch, field, value
):
    staged_review(workspace, monkeypatch)
    path = workspace.service.repository.pending_commit_path
    header, encrypted = path.read_bytes().split(b"\n", 1)
    data = json.loads(header)
    data["receipt"][field] = value
    # Simulate untrusted on-disk header edits; no forged generation is promoted.
    path.write_bytes(json.dumps(data).encode() + b"\n" + encrypted)
    before = path.read_bytes()
    view = workspace.read_view()
    assert view.status == "outcome_uncertain"
    assert view.pending_review is None
    assert path.read_bytes() == before


def test_pending_ciphertext_substitution_never_presents_a_retry(workspace, monkeypatch):
    staged_review(workspace, monkeypatch)
    path = workspace.service.repository.pending_commit_path
    raw = path.read_bytes()
    path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
    before = path.read_bytes()
    assert workspace.read_view().pending_review is None
    assert path.read_bytes() == before


@pytest.mark.parametrize("delta", [timedelta(hours=-1), timedelta(hours=1)])
def test_inapp_preparation_must_be_current_before_authority(workspace, delta):
    original = workspace.prepare(intent("create", 0, "time"))
    prepared = FinanceWorkspacePreparation(
        configuration_ref=original.configuration_ref,
        bundle=prepare_finance_mutation(
            workspace.service,
            original.bundle.request,
            now=datetime.now(timezone.utc) + delta,
        ),
    )
    with pytest.raises(ValueError, match="PREPARATION_NOT_CURRENT"):
        workspace.commit(prepared, confirmed=True)
    assert not (
        workspace.configuration.repository_dir.parent / ".uaa-finance-authority"
    ).exists()


def test_paging_is_bounded_before_loading_and_preserves_totals(workspace):
    with pytest.raises(ValidationError):
        workspace.read_view(limit=101)
    assert not workspace.service.repository.root.exists()
    commit(workspace, "create", 0, "create")
    commit(workspace, "import_commit", 1, "import")
    first = workspace.read_view(limit=1)
    second = workspace.read_view(item_offset=1, limit=1)
    assert first.item_count == second.item_count == 2
    assert len(first.review_items) == len(second.review_items) == 1
    assert (
        first.review_items[0].review_item_ref != second.review_items[0].review_item_ref
    )
