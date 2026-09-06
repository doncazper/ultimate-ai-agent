#!/usr/bin/env python3
"""Verify the bounded FIN-003 synthetic review-decision preview."""

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
from ultimate_ai_agent.core.finance.review_decision_preview import (  # noqa: E402
    FIN003_PREVIEW_UNCHANGED_CONSEQUENCE_REF,
    build_finance_review_decision_preview_request,
    preview_finance_review_decision,
)
from ultimate_ai_agent.core.finance.review_projection import (  # noqa: E402
    build_finance_review_projection,
)


BOOK_FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
IMPORT_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
DECISIONS = ("confirm", "reject", "defer")
REQUIRED_PATHS = (
    "src/ultimate_ai_agent/core/finance/review_decision_preview.py",
    "scripts/dev/uaa_finance.py",
    "scripts/verify_fin003_synthetic_review_decision_preview.py",
    "tests/test_fin003_synthetic_review_decision_preview.py",
    "docs/product/UAA_FINANCE_FIN003_SYNTHETIC_REVIEW_DECISION_PREVIEW.md",
)
REQUIRED_DOC_PHRASES = (
    "synthetic-only",
    "content-free",
    "confirm, reject, or defer",
    "no decision is persisted",
    "no real financial data",
    "separate approved apply",
)


def _committed_snapshot() -> FinanceSnapshot:
    fixture = load_finance_fixture(BOOK_FIXTURE_REF)
    manifest = load_finance_fixture_manifest()
    before = FinanceSnapshot(
        repository_ref="repository-ref:finance:fin003-decision-preview-verifier",
        revision=1,
        generation=1,
        fixture_manifest_ref=manifest.manifest_ref,
        applied_fixture_refs=(fixture.fixture_ref,),
        books=(fixture.book,),
        legal_entities=fixture.legal_entities,
        accounts=fixture.accounts,
        journal_entries=fixture.journal_entries,
    )
    import_preview = preview_synthetic_csv_fixture(IMPORT_FIXTURE_REF)
    record, entries = build_import_commit_record(import_preview, before=before)
    return FinanceSnapshot.model_validate(
        {
            **before.model_dump(mode="python"),
            "revision": 2,
            "generation": 2,
            "applied_fixture_refs": (
                *before.applied_fixture_refs,
                import_preview.fixture_ref,
            ),
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
    item_ref = projection.review_items[0].review_item_ref
    previews = []
    for decision in DECISIONS:
        request = build_finance_review_decision_preview_request(
            snapshot,
            review_item_ref=item_ref,
            decision=decision,  # type: ignore[arg-type]
        )
        preview = preview_finance_review_decision(snapshot, request)
        if preview != preview_finance_review_decision(
            snapshot.model_copy(deep=True), request
        ):
            failures.append(f"FIN003 {decision} preview is not deterministic")
        if preview.projection_ref != projection.projection_ref:
            failures.append(f"FIN003 {decision} projection binding drifted")
        if preview.source_snapshot_ref != snapshot.snapshot_ref:
            failures.append(f"FIN003 {decision} snapshot binding drifted")
        if preview.review_item_ref != item_ref:
            failures.append(f"FIN003 {decision} item binding drifted")
        if preview.consequence_refs[-1] != FIN003_PREVIEW_UNCHANGED_CONSEQUENCE_REF:
            failures.append(f"FIN003 {decision} unchanged consequence drifted")
        posture = (
            preview.synthetic_only,
            preview.content_free,
            not preview.raw_financial_values_included,
            not preview.real_financial_data_included,
            not preview.decision_persisted,
            not preview.review_item_state_changed,
            not preview.ledger_mutation_performed,
            not preview.action_inbox_mutation_performed,
            not preview.correction_input_allowed,
            not preview.rule_proposal_created,
            not preview.approval_authority_granted,
            not preview.execution_authority_granted,
            not preview.external_write_performed,
        )
        if not all(posture):
            failures.append(f"FIN003 {decision} authority posture drifted")
        previews.append(preview)
    if tuple(item.decision for item in previews) != DECISIONS:
        failures.append("FIN003 decision allowlist drifted")
    if len({item.preview_ref for item in previews}) != len(DECISIONS):
        failures.append("FIN003 decision previews are not content-bound")

    serialized = json.dumps(
        [item.model_dump(mode="json") for item in previews], sort_keys=True
    )
    for forbidden in (
        "amount_minor",
        "book_ref",
        "candidate_ref",
        "journal_entry_ref",
        "import_commit_ref",
        "source_fingerprint",
        "observation_ref",
        "office-supply",
        "service-income",
    ):
        if forbidden in serialized:
            failures.append(f"FIN003 decision preview leaked content: {forbidden}")

    cli_source = (ROOT / "scripts/dev/uaa_finance.py").read_text(encoding="utf-8")
    for phrase in (
        '"review-decision-preview"',
        "build_finance_review_decision_preview_request",
        "preview_finance_review_decision",
        "load_snapshot_read_only",
    ):
        if phrase not in cli_source:
            failures.append(f"FIN003 decision-preview CLI binding missing: {phrase}")
    doc_text = (
        (ROOT / "docs/product/UAA_FINANCE_FIN003_SYNTHETIC_REVIEW_DECISION_PREVIEW.md")
        .read_text(encoding="utf-8")
        .lower()
    )
    for phrase in REQUIRED_DOC_PHRASES:
        if phrase not in doc_text:
            failures.append(f"FIN003 decision-preview truth phrase missing: {phrase}")
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("FIN-003 synthetic review decision preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
