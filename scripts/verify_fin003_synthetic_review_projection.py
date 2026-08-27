#!/usr/bin/env python3
"""Verify the bounded FIN-003 synthetic review-projection slice."""

from __future__ import annotations

import json
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
from ultimate_ai_agent.core.finance.import_commit import (  # noqa: E402
    build_import_commit_record,
)
from ultimate_ai_agent.core.finance.import_preview import (  # noqa: E402
    preview_synthetic_csv_fixture,
)
from ultimate_ai_agent.core.finance.models import FinanceSnapshot  # noqa: E402
from ultimate_ai_agent.core.finance.review_projection import (  # noqa: E402
    build_finance_review_projection,
)


BOOK_FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
IMPORT_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
REQUIRED_PATHS = (
    "src/ultimate_ai_agent/core/finance/review_projection.py",
    "scripts/dev/uaa_finance.py",
    "tests/test_fin003_synthetic_review_projection.py",
    "docs/product/UAA_FINANCE_FIN003_SYNTHETIC_REVIEW_PROJECTION.md",
)
REQUIRED_DOC_PHRASES = (
    "synthetic-only",
    "read-only",
    "no categorization decision",
    "no real financial data",
    "independent fin-000 promotion",
)


def _committed_snapshot() -> FinanceSnapshot:
    fixture = load_finance_fixture(BOOK_FIXTURE_REF)
    manifest = load_finance_fixture_manifest()
    before = FinanceSnapshot(
        repository_ref="repository-ref:finance:fin003-verifier",
        revision=1,
        generation=1,
        fixture_manifest_ref=manifest.manifest_ref,
        applied_fixture_refs=(fixture.fixture_ref,),
        books=(fixture.book,),
        legal_entities=fixture.legal_entities,
        accounts=fixture.accounts,
        journal_entries=fixture.journal_entries,
    )
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


def verify() -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_PATHS:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            failures.append(f"required regular file missing: {relative}")
    if failures:
        return failures

    snapshot = _committed_snapshot()
    projection = build_finance_review_projection(snapshot)
    if projection != build_finance_review_projection(snapshot.model_copy(deep=True)):
        failures.append("FIN003 projection is not deterministic")
    if len(projection.review_items) != 2:
        failures.append("FIN003 review item census drifted")
    if len(projection.review_batches) != 1 or len(projection.action_inbox) != 1:
        failures.append("FIN003 batch or Action Inbox census drifted")
    if projection.source_snapshot_ref != snapshot.snapshot_ref:
        failures.append("FIN003 source snapshot binding drifted")
    posture = (
        projection.read_model_only,
        projection.synthetic_only,
        not projection.arbitrary_input_allowed,
        not projection.raw_financial_values_included,
        not projection.real_financial_data_included,
        not projection.connector_authority_granted,
        not projection.decision_authority_granted,
        not projection.execution_authority_granted,
        not projection.mutation_performed,
    )
    if not all(posture):
        failures.append("FIN003 read-only authority posture drifted")
    serialized = json.dumps(projection.model_dump(mode="json"), sort_keys=True)
    for forbidden in (
        "amount_minor",
        "source_fingerprint",
        "observation_ref",
        "office-supply",
        "service-income",
    ):
        if forbidden in serialized:
            failures.append(f"FIN003 projection leaked forbidden content: {forbidden}")
    cli_source = (ROOT / "scripts/dev/uaa_finance.py").read_text(encoding="utf-8")
    if (
        '"review"' not in cli_source
        or "build_finance_review_projection" not in cli_source
    ):
        failures.append("FIN003 CLI inspection command missing")
    doc_text = (
        (ROOT / "docs/product/UAA_FINANCE_FIN003_SYNTHETIC_REVIEW_PROJECTION.md")
        .read_text(encoding="utf-8")
        .lower()
    )
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in doc_text:
            failures.append(f"FIN003 truth phrase missing: {phrase}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("FIN-003 synthetic review projection verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
