from __future__ import annotations

import json
import subprocess
import sys
import warnings
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
from ultimate_ai_agent.core.finance.models import FinanceSnapshot, stable_finance_ref
from ultimate_ai_agent.core.finance.review_decision_preview import (
    FIN003_PREVIEW_UNCHANGED_CONSEQUENCE_REF,
    FinanceReviewDecisionPreview,
    FinanceReviewDecisionPreviewRequest,
    build_finance_review_decision_preview_request,
    preview_finance_review_decision,
)
from ultimate_ai_agent.core.finance.review_projection import (
    build_finance_review_projection,
)


BOOK_FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
IMPORT_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
DECISION_CONSEQUENCE_REFS = {
    "confirm": (
        "consequence-ref:finance/FIN-003:confirmation-requires-separate-approved-apply",
        FIN003_PREVIEW_UNCHANGED_CONSEQUENCE_REF,
    ),
    "reject": (
        "consequence-ref:finance/FIN-003:rejection-requires-separate-approved-apply",
        FIN003_PREVIEW_UNCHANGED_CONSEQUENCE_REF,
    ),
    "defer": (
        "consequence-ref:finance/FIN-003:deferral-requires-separate-approved-apply",
        FIN003_PREVIEW_UNCHANGED_CONSEQUENCE_REF,
    ),
}


def _committed_snapshot() -> FinanceSnapshot:
    fixture = load_finance_fixture(BOOK_FIXTURE_REF)
    manifest = load_finance_fixture_manifest()
    before = FinanceSnapshot(
        repository_ref="repository-ref:finance:fin003-decision-preview-test",
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


def _request_with(
    request: FinanceReviewDecisionPreviewRequest,
    **updates: object,
) -> FinanceReviewDecisionPreviewRequest:
    payload = {**request.model_dump(mode="python"), **updates}
    payload["decision_request_ref"] = stable_finance_ref(
        "review-decision-request-ref:finance/FIN-003",
        {key: value for key, value in payload.items() if key != "decision_request_ref"},
    )
    return FinanceReviewDecisionPreviewRequest.model_validate(payload)


@pytest.mark.parametrize("decision", ("confirm", "reject", "defer"))
def test_preview_is_deterministic_content_free_and_non_mutating(decision: str) -> None:
    snapshot = _committed_snapshot()
    item = build_finance_review_projection(snapshot).review_items[0]
    request = build_finance_review_decision_preview_request(
        snapshot,
        review_item_ref=item.review_item_ref,
        decision=decision,  # type: ignore[arg-type]
    )

    first = preview_finance_review_decision(snapshot, request)
    second = preview_finance_review_decision(snapshot.model_copy(deep=True), request)

    assert first == second
    assert first.decision == decision
    assert first.consequence_refs == DECISION_CONSEQUENCE_REFS[decision]
    assert first.projection_ref == request.projection_ref
    assert first.source_snapshot_ref == snapshot.snapshot_ref
    assert first.review_item_ref == item.review_item_ref
    assert first.state == "proposal_only"
    assert first.synthetic_only is True
    assert first.content_free is True
    for flag in (
        first.raw_financial_values_included,
        first.real_financial_data_included,
        first.decision_persisted,
        first.review_item_state_changed,
        first.ledger_mutation_performed,
        first.action_inbox_mutation_performed,
        first.correction_input_allowed,
        first.rule_proposal_created,
        first.approval_authority_granted,
        first.execution_authority_granted,
        first.external_write_performed,
    ):
        assert flag is False


def test_request_and_preview_refs_bind_the_complete_contract() -> None:
    snapshot = _committed_snapshot()
    item_ref = build_finance_review_projection(snapshot).review_items[0].review_item_ref
    request = build_finance_review_decision_preview_request(
        snapshot, review_item_ref=item_ref, decision="defer"
    )
    preview = preview_finance_review_decision(snapshot, request)

    request_payload = request.model_dump(mode="python")
    request_payload["source_revision"] = 3
    with pytest.raises(
        ValidationError, match="FIN003_REVIEW_DECISION_REQUEST_REF_INVALID"
    ):
        FinanceReviewDecisionPreviewRequest.model_validate(request_payload)

    preview_payload = preview.model_dump(mode="python")
    preview_payload["decision"] = "reject"
    with pytest.raises(
        ValidationError, match="FIN003_REVIEW_DECISION_CONSEQUENCES_INVALID"
    ):
        FinanceReviewDecisionPreview.model_validate(preview_payload)


@pytest.mark.parametrize(
    "updates",
    (
        {
            "decision_request_ref": (
                "review-decision-request-ref:finance/FIN-003:unrelated"
            )
        },
        {"source_revision": 3},
    ),
)
def test_serialized_preview_rejects_rebound_request_contract(
    updates: dict[str, object],
) -> None:
    snapshot = _committed_snapshot()
    item_ref = build_finance_review_projection(snapshot).review_items[0].review_item_ref
    request = build_finance_review_decision_preview_request(
        snapshot, review_item_ref=item_ref, decision="confirm"
    )
    payload = preview_finance_review_decision(snapshot, request).model_dump(
        mode="python"
    )
    payload.update(updates)
    payload["preview_ref"] = stable_finance_ref(
        "review-decision-preview-ref:finance/FIN-003",
        {key: value for key, value in payload.items() if key != "preview_ref"},
    )

    with pytest.raises(
        ValidationError,
        match="FIN003_REVIEW_DECISION_REQUEST_BINDING_INVALID",
    ):
        FinanceReviewDecisionPreview.model_validate(payload)


def test_untrusted_constructed_values_emit_no_serializer_warning_content() -> None:
    marker = "raw-financial-value-marker"

    class _UnexpectedValue:
        def __repr__(self) -> str:
            return f"<{marker}>"

    snapshot = _committed_snapshot()
    item_ref = build_finance_review_projection(snapshot).review_items[0].review_item_ref
    request = build_finance_review_decision_preview_request(
        snapshot, review_item_ref=item_ref, decision="confirm"
    )
    request_payload = request.model_dump(mode="python")
    request_payload["projection_ref"] = _UnexpectedValue()
    snapshot_payload = snapshot.model_dump(mode="python")
    snapshot_payload["repository_ref"] = _UnexpectedValue()
    forged_requests = (
        request.model_copy(update={"projection_ref": _UnexpectedValue()}),
        FinanceReviewDecisionPreviewRequest.model_construct(**request_payload),
    )
    forged_snapshots = (
        snapshot.model_copy(update={"repository_ref": _UnexpectedValue()}),
        FinanceSnapshot.model_construct(**snapshot_payload),
    )

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        for forged_request in forged_requests:
            with pytest.raises(ValidationError):
                preview_finance_review_decision(snapshot, forged_request)
        for forged_snapshot in forged_snapshots:
            with pytest.raises(ValidationError):
                preview_finance_review_decision(forged_snapshot, request)

    emitted = "\n".join(str(item.message) for item in captured)
    assert marker not in emitted
    assert "PydanticSerializationUnexpectedValue" not in emitted


def test_preview_rejects_stale_projection_and_snapshot_bindings() -> None:
    snapshot = _committed_snapshot()
    item_ref = build_finance_review_projection(snapshot).review_items[0].review_item_ref
    request = build_finance_review_decision_preview_request(
        snapshot, review_item_ref=item_ref, decision="confirm"
    )

    stale_projection = _request_with(
        request,
        projection_ref="review-projection-ref:finance/FIN-003:stale",
    )
    with pytest.raises(
        ValueError, match="FIN003_REVIEW_DECISION_PROJECTION_NOT_CURRENT"
    ):
        preview_finance_review_decision(snapshot, stale_projection)

    stale_snapshot = _request_with(
        request,
        source_snapshot_ref="finance-snapshot-ref:sha256:" + "0" * 64,
    )
    with pytest.raises(ValueError, match="FIN003_REVIEW_DECISION_SNAPSHOT_NOT_CURRENT"):
        preview_finance_review_decision(snapshot, stale_snapshot)


def test_preview_rejects_a_request_after_the_current_snapshot_changes() -> None:
    snapshot = _committed_snapshot()
    item_ref = build_finance_review_projection(snapshot).review_items[0].review_item_ref
    request = build_finance_review_decision_preview_request(
        snapshot, review_item_ref=item_ref, decision="reject"
    )
    advanced = FinanceSnapshot.model_validate(
        {
            **snapshot.model_dump(mode="python"),
            "revision": 3,
            "generation": 3,
        }
    )

    with pytest.raises(
        ValueError, match="FIN003_REVIEW_DECISION_PROJECTION_NOT_CURRENT"
    ):
        preview_finance_review_decision(advanced, request)


def test_preview_rejects_unknown_items_and_unscoped_decisions() -> None:
    snapshot = _committed_snapshot()
    with pytest.raises(ValueError, match="FIN003_REVIEW_DECISION_ITEM_NOT_CURRENT"):
        build_finance_review_decision_preview_request(
            snapshot,
            review_item_ref="review-item-ref:finance/FIN-003:unknown",
            decision="defer",
        )

    item_ref = build_finance_review_projection(snapshot).review_items[0].review_item_ref
    with pytest.raises(ValidationError):
        build_finance_review_decision_preview_request(
            snapshot,
            review_item_ref=item_ref,
            decision="correct",  # type: ignore[arg-type]
        )


def test_serialized_preview_omits_financial_content_and_lineage_details() -> None:
    snapshot = _committed_snapshot()
    item_ref = build_finance_review_projection(snapshot).review_items[0].review_item_ref
    request = build_finance_review_decision_preview_request(
        snapshot, review_item_ref=item_ref, decision="defer"
    )
    serialized = json.dumps(
        preview_finance_review_decision(snapshot, request).model_dump(mode="json"),
        sort_keys=True,
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
        assert forbidden not in serialized


def test_cli_parser_and_command_emit_only_the_preview(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snapshot = _committed_snapshot()
    item_ref = build_finance_review_projection(snapshot).review_items[0].review_item_ref

    class _Repository:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def load_snapshot_read_only(self, *, request_ref: str) -> FinanceSnapshot:
            assert request_ref == "request-ref:finance:fin003-decision-preview-cli"
            return snapshot

    monkeypatch.setattr(uaa_finance, "FinanceRepository", _Repository)
    monkeypatch.setattr(uaa_finance, "_backend", lambda _args: object())
    parsed = uaa_finance.parser().parse_args(
        [
            "review-decision-preview",
            "--repository-dir",
            "protected-book",
            "--helper-path",
            "finance-helper",
            "--helper-sha256",
            "a" * 64,
            "--request-ref",
            "request-ref:finance:fin003-decision-preview-cli",
            "--review-item-ref",
            item_ref,
            "--decision",
            "confirm",
        ]
    )

    assert parsed.func is uaa_finance.command_read
    assert parsed.func(parsed) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "uaa-finance-review-decision-preview.v1"
    assert payload["review_item_ref"] == item_ref
    assert payload["decision"] == "confirm"
    assert payload["ledger_mutation_performed"] is False


def test_fin003_decision_preview_verifier_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify_fin003_synthetic_review_decision_preview.py",
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FIN-003 synthetic review decision preview verification passed." in (
        result.stdout
    )
