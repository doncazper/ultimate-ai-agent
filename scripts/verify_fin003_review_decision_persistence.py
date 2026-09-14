#!/usr/bin/env python3
"""Verify FIN-003's bounded synthetic history and exact review contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.finance.fixtures import (  # noqa: E402
    load_finance_fixture,
    load_finance_fixture_manifest,
)
from ultimate_ai_agent.core.finance.import_commit import build_import_commit_record  # noqa: E402
from ultimate_ai_agent.core.finance.import_preview import preview_synthetic_csv_fixture  # noqa: E402
from ultimate_ai_agent.core.finance.models import FinanceSnapshot  # noqa: E402
from ultimate_ai_agent.core.finance.review_decision_commit import (  # noqa: E402
    build_finance_review_decision_record,
    preview_finance_review_persistence,
)
from ultimate_ai_agent.core.finance.review_projection import (  # noqa: E402
    build_finance_review_projection,
)


def _source() -> FinanceSnapshot:
    fixture = load_finance_fixture("fixture-ref:finance/FIN-001:balanced-local-book:v1")
    before = FinanceSnapshot(
        repository_ref="repository-ref:finance:fin003-persistence-verifier",
        revision=1,
        generation=1,
        fixture_manifest_ref=load_finance_fixture_manifest().manifest_ref,
        applied_fixture_refs=(fixture.fixture_ref,),
        books=(fixture.book,),
        legal_entities=fixture.legal_entities,
        accounts=fixture.accounts,
        journal_entries=fixture.journal_entries,
    )
    imported = preview_synthetic_csv_fixture(
        "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
    )
    record, entries = build_import_commit_record(imported, before=before)
    return FinanceSnapshot.model_validate(
        {
            **before.model_dump(mode="python"),
            "revision": 2,
            "generation": 2,
            "applied_fixture_refs": (
                *before.applied_fixture_refs,
                imported.fixture_ref,
            ),
            "journal_entries": (*before.journal_entries, *entries),
            "import_commits": (record,),
        }
    )


def verify() -> list[str]:
    failures: list[str] = []
    before = _source()
    item = build_finance_review_projection(before).review_items[0]
    for decision, state in (
        ("confirm", "confirmed"),
        ("reject", "rejected"),
        ("defer", "deferred"),
    ):
        preview = preview_finance_review_persistence(
            before,
            review_item_ref=item.review_item_ref,
            request_ref=f"request-ref:finance:verify-{decision}",
            idempotency_ref=f"idempotency-ref:finance:verify-{decision}",
            decision=decision,  # type: ignore[arg-type]
        )
        record = build_finance_review_decision_record(before, preview)
        saved = FinanceSnapshot.model_validate(
            {
                **before.model_dump(mode="python"),
                "revision": 3,
                "generation": 3,
                "review_decisions": (record,),
            }
        )
        reopened = FinanceSnapshot.model_validate_json(saved.model_dump_json())
        projection = build_finance_review_projection(reopened)
        current = projection.review_items[0]
        if (
            current.state != state
            or current.lineage_ref != item.lineage_ref
            or current.effective_decision_ref != record.event_ref
            or projection.decision_history != saved.review_decisions
        ):
            failures.append(f"FIN003 {decision} history/projection binding drifted")
        undo_preview = preview_finance_review_persistence(
            reopened,
            review_item_ref=current.review_item_ref,
            request_ref=f"request-ref:finance:undo-{decision}",
            idempotency_ref=f"idempotency-ref:finance:undo-{decision}",
            compensates_event_ref=record.event_ref,
        )
        undo = build_finance_review_decision_record(reopened, undo_preview)
        final = FinanceSnapshot.model_validate(
            {
                **reopened.model_dump(mode="python"),
                "revision": 4,
                "generation": 4,
                "review_decisions": (*reopened.review_decisions, undo),
            }
        )
        if (
            final.effective_review_decisions()
            or final.review_decisions[0] != record
            or final.journal_entries != before.journal_entries
            or final.account_balances() != before.account_balances()
            or build_finance_review_projection(final).review_items[0].state
            != "needs_review"
        ):
            failures.append(f"FIN003 {decision} compensation or ledger truth drifted")
        if (
            preview.execution_authority_granted
            or preview.decision_persisted
            or preview.ledger_mutation_performed
            or not preview.synthetic_only
        ):
            failures.append(f"FIN003 {decision} preview authority drifted")
    doc = (
        (
            ROOT
            / "docs/product/UAA_FINANCE_FIN003_SYNTHETIC_REVIEW_DECISION_PERSISTENCE.md"
        )
        .read_text(encoding="utf-8")
        .lower()
    )
    for phrase in (
        "synthetic-only",
        "append-only",
        "no api or ui authority",
        "there is no real financial data",
        "does not complete fin-003 or q26",
        "refresh-review",
        "balances remain unchanged",
    ):
        if phrase not in doc:
            failures.append(f"FIN003 persistence truth phrase missing: {phrase}")
    return failures


def main() -> int:
    failures = verify()
    for failure in failures:
        print(f"FAIL: {failure}")
    if not failures:
        print("FIN-003 synthetic review persistence contract verification passed.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
