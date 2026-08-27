from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest
from pydantic import ValidationError
from scripts.dev import uaa_finance

from ultimate_ai_agent.core.finance.fixtures import (
    load_finance_fixture,
    load_finance_fixture_manifest,
)
from ultimate_ai_agent.core.finance.import_commit import build_import_commit_record
from ultimate_ai_agent.core.finance.import_preview import (
    preview_synthetic_csv_fixture,
)
from ultimate_ai_agent.core.finance.models import (
    FinanceSnapshot,
    JournalEntry,
    JournalFlow,
    Posting,
    PostingSide,
    stable_finance_ref,
)
from ultimate_ai_agent.core.finance.repository import (
    FINANCE_REPOSITORY_LOCK_FILE,
    FINANCE_REPOSITORY_PENDING_COMMIT_FILE,
    FinanceRepository,
    FinanceRepositoryError,
)
from ultimate_ai_agent.core.finance.review_projection import (
    FIN003_RANKING_BASIS_REF,
    FinanceActionInboxProjection,
    FinanceReviewBatch,
    FinanceReviewItem,
    FinanceReviewProjection,
    build_finance_review_projection,
)


BOOK_FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
IMPORT_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"


def _book_snapshot() -> FinanceSnapshot:
    """Build the base synthetic protected-book snapshot."""

    fixture = load_finance_fixture(BOOK_FIXTURE_REF)
    manifest = load_finance_fixture_manifest()
    return FinanceSnapshot(
        repository_ref="repository-ref:finance:fin003-test",
        revision=1,
        generation=1,
        fixture_manifest_ref=manifest.manifest_ref,
        applied_fixture_refs=(fixture.fixture_ref,),
        books=(fixture.book,),
        legal_entities=fixture.legal_entities,
        accounts=fixture.accounts,
        journal_entries=fixture.journal_entries,
    )


def _committed_snapshot() -> FinanceSnapshot:
    """Build one committed synthetic import snapshot."""

    before = _book_snapshot()
    preview = preview_synthetic_csv_fixture(IMPORT_FIXTURE_REF)
    record, entries = build_import_commit_record(preview, before=before)
    return FinanceSnapshot.model_validate(
        {
            **before.model_dump(mode="python"),
            "revision": 2,
            "generation": 2,
            "applied_fixture_refs": (*before.applied_fixture_refs, preview.fixture_ref),
            "journal_entries": (*before.journal_entries, *entries),
            "import_commits": (record,),
        }
    )


def _reversal_for(target: JournalEntry, *, suffix: str) -> JournalEntry:
    """Build an exact synthetic reversal for a test journal entry."""

    postings = tuple(
        Posting(
            posting_ref=f"posting-ref:finance:fin003-{suffix}-{index}",
            account_ref=posting.account_ref,
            commodity_ref=posting.commodity_ref,
            side=(
                PostingSide.credit
                if posting.side == PostingSide.debit.value
                else PostingSide.debit
            ),
            amount_minor=posting.amount_minor,
            fixture_ref=posting.fixture_ref,
        )
        for index, posting in enumerate(target.postings, start=1)
    )
    return JournalEntry(
        journal_entry_ref=f"journal-entry-ref:finance:fin003-{suffix}",
        book_ref=target.book_ref,
        flow=JournalFlow.reversal,
        fixture_ref=target.fixture_ref,
        postings=postings,
        reverses_journal_entry_ref=target.journal_entry_ref,
    )


def test_projection_is_empty_and_read_only_before_any_import() -> None:
    """A book with no imports has an empty authority-free projection."""

    projection = build_finance_review_projection(_book_snapshot())

    assert projection.review_items == ()
    assert projection.review_batches == ()
    assert projection.action_inbox == ()
    assert projection.read_model_only is True
    assert projection.mutation_performed is False
    assert projection.decision_authority_granted is False
    assert projection.execution_authority_granted is False


def test_projection_maps_synthetic_import_lineage_without_values() -> None:
    """Committed lineage becomes ranked content-free review pointers."""

    snapshot = _committed_snapshot()
    record = snapshot.import_commits[0]
    projection = build_finance_review_projection(snapshot)

    assert projection.source_snapshot_ref == snapshot.snapshot_ref
    assert projection.source_revision == 2
    assert projection.ranking_basis_ref == FIN003_RANKING_BASIS_REF
    assert len(projection.review_items) == 2
    assert len(projection.review_batches) == 1
    assert len(projection.action_inbox) == 1
    assert tuple(item.rank for item in projection.review_items) == (1, 2)
    assert tuple(item.candidate_ref for item in projection.review_items) == (
        record.candidate_refs
    )
    assert tuple(item.journal_entry_ref for item in projection.review_items) == (
        record.journal_entry_refs
    )
    assert projection.review_batches[0].review_item_refs == tuple(
        item.review_item_ref for item in projection.review_items
    )
    assert (
        projection.action_inbox[0].review_batch_ref
        == projection.review_batches[0].review_batch_ref
    )

    serialized = json.dumps(projection.model_dump(mode="json"), sort_keys=True)
    for forbidden in (
        "amount_minor",
        "source_fingerprint",
        "observation_ref",
        "office-supply",
        "service-income",
    ):
        assert forbidden not in serialized


def test_projection_is_deterministic_and_content_bound() -> None:
    """The projection is deterministic and rejects graph or source drift."""

    snapshot = _committed_snapshot()
    first = build_finance_review_projection(snapshot)
    second = build_finance_review_projection(snapshot.model_copy(deep=True))
    assert first == second

    payload = first.model_dump(mode="python")
    payload["source_revision"] = 3
    with pytest.raises(ValidationError, match="FIN003_REVIEW_PROJECTION_REF_INVALID"):
        FinanceReviewProjection.model_validate(payload)

    graph_payload = first.model_dump(mode="python")
    graph_payload["action_inbox"] = ()
    with pytest.raises(
        ValidationError, match="FIN003_REVIEW_PROJECTION_ACTION_GRAPH_INVALID"
    ):
        FinanceReviewProjection.model_validate(graph_payload)


def test_projection_cross_binds_batch_scope_to_review_items() -> None:
    """A batch cannot claim a different book or import than its items."""

    projection = build_finance_review_projection(_committed_snapshot())
    batch_payload = projection.review_batches[0].model_dump(mode="python")
    batch_payload["book_ref"] = "book-ref:finance:fin003-other-book"
    batch_payload["review_batch_ref"] = stable_finance_ref(
        "review-batch-ref:finance/FIN-003",
        {
            key: value
            for key, value in batch_payload.items()
            if key != "review_batch_ref"
        },
    )
    changed_batch = FinanceReviewBatch.model_validate(batch_payload)
    action_payload = projection.action_inbox[0].model_dump(mode="python")
    action_payload["review_batch_ref"] = changed_batch.review_batch_ref
    action_payload["action_projection_ref"] = stable_finance_ref(
        "action-projection-ref:finance/FIN-003",
        {
            key: value
            for key, value in action_payload.items()
            if key != "action_projection_ref"
        },
    )
    changed_action = FinanceActionInboxProjection.model_validate(action_payload)
    payload = projection.model_dump(mode="python")
    payload["review_batches"] = (changed_batch,)
    payload["action_inbox"] = (changed_action,)

    with pytest.raises(ValidationError, match="FIN003_REVIEW_BATCH_SCOPE_INVALID"):
        FinanceReviewProjection.model_validate(payload)


def test_projection_rejects_non_suspense_import_entry() -> None:
    """Imported review entries must preserve the suspense flow contract."""

    snapshot = _committed_snapshot()
    record = snapshot.import_commits[0]
    changed_entries = tuple(
        entry.model_copy(update={"flow": "adjustment"})
        if entry.journal_entry_ref == record.journal_entry_refs[0]
        else entry
        for entry in snapshot.journal_entries
    )
    changed = snapshot.model_copy(update={"journal_entries": changed_entries})

    with pytest.raises(ValueError, match="FIN003_REVIEW_JOURNAL_FLOW_INVALID"):
        build_finance_review_projection(changed)


def test_projection_resolves_reversal_chain_parity() -> None:
    """One reversal suppresses an item and a second restores it."""

    snapshot = _committed_snapshot()
    imported_ref = snapshot.import_commits[0].journal_entry_refs[0]
    imported = next(
        entry
        for entry in snapshot.journal_entries
        if entry.journal_entry_ref == imported_ref
    )
    first_reversal = _reversal_for(imported, suffix="reversal-one")
    once_reversed = FinanceSnapshot.model_validate(
        {
            **snapshot.model_dump(mode="python"),
            "revision": 3,
            "generation": 3,
            "journal_entries": (*snapshot.journal_entries, first_reversal),
        }
    )
    assert len(build_finance_review_projection(once_reversed).review_items) == 1

    second_reversal = _reversal_for(first_reversal, suffix="reversal-two")
    twice_reversed = FinanceSnapshot.model_validate(
        {
            **once_reversed.model_dump(mode="python"),
            "revision": 4,
            "generation": 4,
            "journal_entries": (*once_reversed.journal_entries, second_reversal),
        }
    )
    assert len(build_finance_review_projection(twice_reversed).review_items) == 2


def test_projection_models_reject_secret_like_refs() -> None:
    """Canonical refs do not bypass the shared unsafe-content validator."""

    item = build_finance_review_projection(_committed_snapshot()).review_items[0]
    payload = item.model_dump(mode="python")
    payload["candidate_ref"] = "candidate-ref:tokenvalue"
    payload["review_item_ref"] = stable_finance_ref(
        "review-item-ref:finance/FIN-003",
        {key: value for key, value in payload.items() if key != "review_item_ref"},
    )
    with pytest.raises(ValidationError, match="contains unsafe content"):
        FinanceReviewItem.model_validate(payload)


def test_read_only_snapshot_load_does_not_recover_pending_commit(
    tmp_path: Path,
) -> None:
    """Read-only loading fails closed without applying a staged mutation."""

    root = tmp_path / "protected-book"
    root.mkdir(mode=0o700)
    lock_path = root / FINANCE_REPOSITORY_LOCK_FILE
    lock_path.write_bytes(b"")
    lock_path.chmod(0o600)
    pending_path = root / FINANCE_REPOSITORY_PENDING_COMMIT_FILE
    pending_payload = b"content-free-pending-generation"
    pending_path.write_bytes(pending_payload)
    pending_path.chmod(0o600)
    repository = FinanceRepository(root, crypto_backend=object())

    for reader in (
        repository.load_snapshot_read_only,
        repository.check_integrity,
        repository.export_redacted,
    ):
        with pytest.raises(
            FinanceRepositoryError,
            match="FINANCE_PENDING_COMMIT_REQUIRES_MUTATING_RECOVERY",
        ):
            reader(request_ref="request-ref:finance:fin003-read-only-pending")

    assert pending_path.read_bytes() == pending_payload
    assert lock_path.read_bytes() == b""


def test_read_only_snapshot_load_uses_existing_lock_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stable read uses the existing shared lock without changing it."""

    root = tmp_path / "protected-book"
    root.mkdir(mode=0o700)
    lock_path = root / FINANCE_REPOSITORY_LOCK_FILE
    lock_path.write_bytes(b"existing-lock")
    lock_path.chmod(0o600)
    before = lock_path.stat()
    snapshot = _committed_snapshot()
    repository = FinanceRepository(root, crypto_backend=object())
    monkeypatch.setattr(
        repository,
        "_load_snapshot_locked",
        lambda *, request_ref: snapshot,
    )

    loaded = repository.load_snapshot_read_only(
        request_ref="request-ref:finance:fin003-read-only-stable"
    )

    after = lock_path.stat()
    assert loaded == snapshot
    assert lock_path.read_bytes() == b"existing-lock"
    assert after.st_mtime_ns == before.st_mtime_ns


def test_finance_cli_exposes_review_as_read_only_projection(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The review CLI uses only the non-recovering repository read path."""

    snapshot = _committed_snapshot()

    class _Repository:
        def load_snapshot_read_only(self, *, request_ref: str) -> FinanceSnapshot:
            assert request_ref == "request-ref:finance:fin003-cli"
            return snapshot

        def load_snapshot(self, *, request_ref: str) -> FinanceSnapshot:
            raise AssertionError("review must not use the recovering load path")

    monkeypatch.setattr(uaa_finance, "_backend", lambda _args: object())
    monkeypatch.setattr(
        uaa_finance,
        "FinanceRepository",
        lambda _path, *, crypto_backend: _Repository(),
    )
    args = Namespace(
        command="review",
        repository_dir=Path("unused"),
        request_ref="request-ref:finance:fin003-cli",
    )
    assert uaa_finance.command_read(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "uaa-finance-review-projection.v1"
    assert payload["read_model_only"] is True
    assert payload["decision_authority_granted"] is False
    assert payload["mutation_performed"] is False
    assert len(payload["action_inbox"]) == 1


def test_finance_cli_parser_includes_review_command() -> None:
    """The CLI exposes review through the shared bounded read parser."""

    parsed = uaa_finance.parser().parse_args(
        [
            "review",
            "--repository-dir",
            "protected-book",
            "--helper-path",
            "finance-helper",
            "--helper-sha256",
            "a" * 64,
            "--request-ref",
            "request-ref:finance:fin003-parser",
        ]
    )
    assert parsed.command == "review"
    assert parsed.func is uaa_finance.command_read


def test_fin003_verifier_passes() -> None:
    """The standalone FIN-003 verifier passes against the checked-in slice."""

    result = subprocess.run(
        [sys.executable, "scripts/verify_fin003_synthetic_review_projection.py"],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FIN-003 synthetic review projection verification passed." in result.stdout
