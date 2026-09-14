from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.finance.fixtures import (
    load_finance_fixture,
    load_finance_fixture_manifest,
)
from ultimate_ai_agent.core.finance.import_commit import build_import_commit_record
from ultimate_ai_agent.core.finance.import_preview import preview_synthetic_csv_fixture
from ultimate_ai_agent.core.finance.models import (
    FINANCE_REVIEW_EVENT_LIMIT,
    FinanceReviewDecisionRecord,
    FinanceSnapshot,
    finance_review_lineage_ref,
    stable_finance_ref,
)
from ultimate_ai_agent.core.finance.repository import FinanceRepository
from ultimate_ai_agent.core.finance.review_decision_commit import (
    FinanceReviewPersistencePreview,
    build_finance_review_decision_record,
    preview_finance_review_persistence,
)
from ultimate_ai_agent.core.finance.review_projection import (
    FinanceReviewProjection,
    build_finance_review_projection,
)


def _snapshot() -> FinanceSnapshot:
    fixture = load_finance_fixture("fixture-ref:finance/FIN-001:balanced-local-book:v1")
    before = FinanceSnapshot(
        repository_ref="repository-ref:finance:fin003-history-test",
        revision=1,
        generation=1,
        fixture_manifest_ref=load_finance_fixture_manifest().manifest_ref,
        applied_fixture_refs=(fixture.fixture_ref,),
        books=(fixture.book,),
        legal_entities=fixture.legal_entities,
        accounts=fixture.accounts,
        journal_entries=fixture.journal_entries,
    )
    preview = preview_synthetic_csv_fixture(
        "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
    )
    record, entries = build_import_commit_record(preview, before=before)
    return FinanceSnapshot.model_validate(
        {
            **before.model_dump(mode="python"),
            "revision": 2,
            "generation": 2,
            "applied_fixture_refs": (*before.applied_fixture_refs, preview.fixture_ref),
            "import_commits": (record,),
            "journal_entries": (*before.journal_entries, *entries),
        }
    )


def _rehash(payload: dict) -> FinanceReviewDecisionRecord:
    provisional = FinanceReviewDecisionRecord.model_construct(**payload)
    data = provisional.model_dump(mode="json", exclude={"event_ref"}, warnings=False)
    return FinanceReviewDecisionRecord.model_validate(
        {
            **data,
            "event_ref": stable_finance_ref(
                "review-decision-record-ref:finance/FIN-003", data
            ),
        }
    )


def _record(
    snapshot: FinanceSnapshot, *, decision: str | None = "confirm", item_index: int = 0
) -> FinanceReviewDecisionRecord:
    imported = snapshot.import_commits[0]
    lineage = {
        "repository_ref": snapshot.repository_ref,
        "book_ref": snapshot.books[0].book_ref,
        "import_commit_ref": imported.commit_ref,
        "candidate_ref": imported.candidate_refs[item_index],
        "journal_entry_ref": imported.journal_entry_refs[item_index],
    }
    lineage_ref = finance_review_lineage_ref(**lineage)
    prior = snapshot.effective_review_decisions().get(lineage_ref)
    return _rehash(
        {
            **lineage,
            "operation": "review_decision" if decision is not None else "review_undo",
            "lineage_ref": lineage_ref,
            "review_item_ref": "review-item-ref:finance:history-test",
            "decision_preview_ref": "review-preview-ref:finance:history-test",
            "before_snapshot_ref": snapshot.snapshot_ref,
            "before_revision": snapshot.revision,
            "request_ref": f"request-ref:finance:history-{snapshot.revision}",
            "idempotency_ref": f"idempotency-ref:finance:history-{snapshot.revision}",
            "decision": decision,
            "compensates_event_ref": prior.event_ref
            if decision is None and prior
            else None,
            "prior_effective_event_ref": prior.event_ref if prior else None,
            "previous_history_event_ref": (
                snapshot.review_decisions[-1].event_ref
                if snapshot.review_decisions
                else None
            ),
        }
    )


def _append(
    snapshot: FinanceSnapshot, record: FinanceReviewDecisionRecord
) -> FinanceSnapshot:
    return FinanceSnapshot.model_validate(
        {
            **snapshot.model_dump(mode="python"),
            "revision": snapshot.revision + 1,
            "generation": snapshot.generation + 1,
            "review_decisions": (*snapshot.review_decisions, record),
        }
    )


def test_empty_history_preserves_legacy_hash_and_stored_snapshot_read() -> None:
    snapshot = _snapshot()
    legacy = snapshot.model_dump(mode="json", exclude={"review_decisions"})
    legacy_ref = stable_finance_ref("finance-snapshot-ref", legacy)
    assert snapshot.snapshot_ref == legacy_ref
    assert FinanceSnapshot.model_validate(legacy).snapshot_ref == legacy_ref
    connection = FinanceRepository._new_connection()
    try:
        connection.execute(
            "INSERT INTO snapshots(revision, snapshot_ref, payload_json) VALUES (?, ?, ?)",
            (snapshot.revision, legacy_ref, json.dumps(legacy)),
        )
        reopened = FinanceRepository._read_snapshot(connection)
        assert reopened == snapshot
        assert reopened.review_decisions == ()
    finally:
        connection.close()


@pytest.mark.parametrize("decision", ["confirm", "reject", "defer"])
def test_history_roundtrip_and_undo_preserve_ledger(decision: str) -> None:
    before = _snapshot()
    event = _record(before, decision=decision)
    after = _append(before, event)
    assert after.snapshot_ref != before.snapshot_ref
    assert after.effective_review_decisions()[event.lineage_ref] == event
    assert FinanceSnapshot.model_validate_json(after.model_dump_json()) == after
    undo = _record(after, decision=None)
    undone = _append(after, undo)
    assert undone.effective_review_decisions() == {}
    assert undone.review_decisions == (event, undo)
    assert undone.journal_entries == before.journal_entries
    assert undone.account_balances() == before.account_balances()
    assert undone.redacted_read_model()["counts"]["review_decision_events"] == 2


def test_undo_restores_previous_effective_decision_without_erasing_history() -> None:
    initial = _snapshot()
    first = _record(initial, decision="defer")
    deferred = _append(initial, first)
    second = _record(deferred, decision="confirm")
    confirmed = _append(deferred, second)
    undone = _append(confirmed, _record(confirmed, decision=None))
    assert undone.effective_review_decisions()[first.lineage_ref] == first
    assert len(undone.review_decisions) == 3


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("candidate_ref", "candidate-ref:finance:unknown", "LINEAGE_REF_INVALID"),
        ("lineage_ref", "review-lineage-ref:finance:unknown", "LINEAGE_REF_INVALID"),
        ("decision", None, "RECORD_SCOPE_INVALID"),
        ("compensates_event_ref", "event-ref:finance:unknown", "RECORD_SCOPE_INVALID"),
        ("ledger_postings_changed", True, "literal_error"),
        ("categorization_performed", True, "literal_error"),
    ],
)
def test_recomputed_record_hash_does_not_authorize_invalid_scope(
    field, value, error
) -> None:
    record = _record(_snapshot())
    with pytest.raises(ValidationError, match=error):
        _rehash({**record.model_dump(mode="python"), field: value})


@pytest.mark.parametrize(
    ("field", "error"),
    [
        ("request_ref", "IDENTITY_REUSED"),
        ("idempotency_ref", "IDENTITY_REUSED"),
        ("before_revision", "GENERATION_INVALID"),
        ("previous_history_event_ref", "GENERATION_INVALID"),
        ("prior_effective_event_ref", "EFFECTIVE_BINDING_INVALID"),
    ],
)
def test_history_rejects_rebound_identity_generation_and_effective_decision(
    field, error
) -> None:
    before = _snapshot()
    first = _record(before)
    after = _append(before, first)
    second = _record(after, decision="defer")
    changed = _rehash(
        {**second.model_dump(mode="python"), field: getattr(first, field)}
    )
    with pytest.raises(ValidationError, match=error):
        _append(after, changed)


def test_history_rejects_cross_item_compensation_even_with_recomputed_hash() -> None:
    before = _snapshot()
    first = _record(before)
    after = _append(before, first)
    other = _record(after, item_index=1)
    after_other = _append(after, other)
    undo = _record(after_other, decision=None)
    rebound = _rehash(
        {
            **undo.model_dump(mode="python"),
            "prior_effective_event_ref": other.event_ref,
            "compensates_event_ref": other.event_ref,
        }
    )
    with pytest.raises(ValidationError, match="EFFECTIVE_BINDING_INVALID"):
        _append(after_other, rebound)


def test_history_rejects_unknown_lineage_after_both_hashes_are_recomputed() -> None:
    before = _snapshot()
    record = _record(before)
    data = {
        **record.model_dump(mode="python"),
        "candidate_ref": "candidate-ref:finance:unknown",
    }
    data["lineage_ref"] = finance_review_lineage_ref(
        **{
            name: data[name]
            for name in (
                "repository_ref",
                "book_ref",
                "import_commit_ref",
                "candidate_ref",
                "journal_entry_ref",
            )
        }
    )
    rebound = _rehash(data)
    with pytest.raises(ValidationError, match="LINEAGE_UNKNOWN"):
        _append(before, rebound)


def test_history_has_a_bounded_capacity_without_eviction() -> None:
    before = _snapshot()
    record = _record(before)
    with pytest.raises(ValidationError, match="too_long"):
        FinanceSnapshot.model_validate(
            {
                **before.model_dump(mode="python"),
                "review_decisions": (record,) * (FINANCE_REVIEW_EVENT_LIMIT + 1),
            }
        )


def _preview(snapshot: FinanceSnapshot, **changes) -> FinanceReviewPersistencePreview:
    return preview_finance_review_persistence(
        snapshot,
        **{
            "review_item_ref": build_finance_review_projection(snapshot)
            .review_items[0]
            .review_item_ref,
            "request_ref": f"request-ref:finance:persistence-{snapshot.revision}",
            "idempotency_ref": f"idempotency-ref:finance:persistence-{snapshot.revision}",
            "decision": "confirm",
            **changes,
        },
    )


@pytest.mark.parametrize("decision", ["confirm", "reject", "defer"])
def test_persistence_preview_rebuilds_one_bound_record_without_mutation(
    decision,
) -> None:
    before = _snapshot()
    original = before.model_dump_json()
    preview = _preview(before, decision=decision)
    record = build_finance_review_decision_record(before, preview)
    assert record.decision == decision
    assert record.decision_preview_ref == preview.preview_ref
    assert record.before_snapshot_ref == before.snapshot_ref
    assert record.before_revision == before.revision
    assert record.request_ref == preview.request_ref
    assert record.idempotency_ref == preview.idempotency_ref
    assert preview.decision_persisted is False
    assert preview.execution_authority_granted is False
    assert "journal-postings-and-balances-unchanged" in preview.consequence_refs[1]
    assert before.model_dump_json() == original


def test_persistence_preview_rejects_stale_source_and_rebound_current_item() -> None:
    before = _snapshot()
    preview = _preview(before)
    changed = _append(before, _record(before, item_index=1))
    with pytest.raises(ValueError, match="NOT_CURRENT"):
        build_finance_review_decision_record(changed, preview)
    with pytest.raises(ValueError, match="ITEM_NOT_CURRENT"):
        _preview(before, review_item_ref="review-item-ref:finance:unknown")


def test_persistence_preview_binds_exact_current_compensation_target() -> None:
    before = _snapshot()
    first = build_finance_review_decision_record(before, _preview(before))
    after = _append(before, first)
    undo_preview = _preview(after, decision=None, compensates_event_ref=first.event_ref)
    undo = build_finance_review_decision_record(after, undo_preview)
    assert undo.compensates_event_ref == first.event_ref
    assert undo.operation == "review_undo"
    undone = _append(after, undo)
    with pytest.raises(ValueError, match="UNDO_TARGET_NOT_CURRENT"):
        _preview(undone, decision=None, compensates_event_ref=first.event_ref)


@pytest.mark.parametrize(
    "field",
    [
        "source_snapshot_ref",
        "lineage_ref",
        "review_item_ref",
        "request_ref",
        "idempotency_ref",
    ],
)
def test_persistence_preview_detects_unreviewed_payload_change(field) -> None:
    preview = _preview(_snapshot())
    data = preview.model_dump(mode="python")
    data[field] = "changed-ref:finance:preview"
    with pytest.raises(ValidationError):
        FinanceReviewPersistencePreview.model_validate(data)


def test_rehashed_consequence_substitution_cannot_claim_accounting_correction() -> None:
    preview = _preview(_snapshot())
    data = preview.model_dump(mode="json", exclude={"preview_ref"})
    data["consequence_refs"][0] = "consequence-ref:finance:posting-reversed"
    data["preview_ref"] = stable_finance_ref(
        "review-persistence-preview-ref:finance/FIN-003", data
    )
    with pytest.raises(ValidationError, match="CONSEQUENCES_INVALID"):
        FinanceReviewPersistencePreview.model_validate(data)


def _rebind(model, key, prefix, **changes):
    data = {**model.model_dump(mode="json", exclude={key}), **changes}
    return type(model).model_validate({**data, key: stable_finance_ref(prefix, data)})


def test_projection_rejects_rehashed_posture_substitution_against_history() -> None:
    before = _snapshot()
    projection = build_finance_review_projection(_append(before, _record(before)))
    item = _rebind(
        projection.review_items[0],
        "review_item_ref",
        "review-item-ref:finance/FIN-003",
        state="rejected",
    )
    batch = _rebind(
        projection.review_batches[0],
        "review_batch_ref",
        "review-batch-ref:finance/FIN-003",
        review_item_refs=[
            item.review_item_ref,
            projection.review_items[1].review_item_ref,
        ],
    )
    action = _rebind(
        projection.action_inbox[0],
        "action_projection_ref",
        "action-projection-ref:finance/FIN-003",
        review_batch_ref=batch.review_batch_ref,
    )
    with pytest.raises(ValidationError, match="PROJECTION_DECISION_INVALID"):
        _rebind(
            projection,
            "projection_ref",
            "review-projection-ref:finance/FIN-003",
            review_items=[
                item.model_dump(mode="json"),
                projection.review_items[1].model_dump(mode="json"),
            ],
            review_batches=[batch.model_dump(mode="json")],
            action_inbox=[action.model_dump(mode="json")],
        )


def test_projection_rejects_duplicate_serialized_decision_history() -> None:
    before = _snapshot()
    projection = build_finance_review_projection(_append(before, _record(before)))
    data = projection.model_dump(mode="json", exclude={"projection_ref"})
    data["decision_history"] *= 2
    data["projection_ref"] = stable_finance_ref(
        "review-projection-ref:finance/FIN-003", data
    )
    with pytest.raises(ValidationError, match="HISTORY_IDENTITY_REUSED"):
        FinanceReviewProjection.model_validate(data)
