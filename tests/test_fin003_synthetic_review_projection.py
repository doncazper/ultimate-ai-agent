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
from ultimate_ai_agent.core.finance.models import FinanceSnapshot
from ultimate_ai_agent.core.finance.review_projection import (
    FIN003_RANKING_BASIS_REF,
    FinanceReviewItem,
    FinanceReviewProjection,
    build_finance_review_projection,
)


BOOK_FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
IMPORT_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"


def _book_snapshot() -> FinanceSnapshot:
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


def test_projection_is_empty_and_read_only_before_any_import() -> None:
    projection = build_finance_review_projection(_book_snapshot())

    assert projection.review_items == ()
    assert projection.review_batches == ()
    assert projection.action_inbox == ()
    assert projection.read_model_only is True
    assert projection.mutation_performed is False
    assert projection.decision_authority_granted is False
    assert projection.execution_authority_granted is False


def test_projection_maps_synthetic_import_lineage_without_values() -> None:
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


def test_projection_rejects_non_suspense_import_entry() -> None:
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


def test_projection_models_reject_secret_like_refs() -> None:
    item = build_finance_review_projection(_committed_snapshot()).review_items[0]
    payload = item.model_dump(mode="python")
    payload["candidate_ref"] = "candidate-ref:sk_live_abc123"
    with pytest.raises(ValidationError):
        FinanceReviewItem.model_validate(payload)


def test_finance_cli_exposes_review_as_read_only_projection(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot = _committed_snapshot()

    class _Repository:
        def load_snapshot(self, *, request_ref: str) -> FinanceSnapshot:
            assert request_ref == "request-ref:finance:fin003-cli"
            return snapshot

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
    result = subprocess.run(
        [sys.executable, "scripts/verify_fin003_synthetic_review_projection.py"],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FIN-003 synthetic review projection verification passed." in result.stdout
