"""Exact synthetic FIN-003 review persistence previews and history binding."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, StrictInt, model_validator

from ultimate_ai_agent.core.finance.models import (
    FINANCE_REVIEW_EVENT_LIMIT,
    FinanceReviewDecision,
    FinanceReviewDecisionRecord,
    FinanceSnapshot,
    _FinanceModel,
    finance_review_lineage_ref,
    stable_finance_ref,
)
from ultimate_ai_agent.core.finance.review_projection import (
    build_finance_review_projection,
)


FIN003_REVIEW_CAPABILITY_REF = (
    "capability-ref:finance/FIN-003/synthetic-review-decision"
)
FIN003_REVIEW_LANE_REF = "authority-lane-ref:finance/FIN-003/synthetic-review-decision"
FIN003_REVIEW_ADAPTER_REF = (
    "authority-adapter-ref:finance/FIN-003/protected-review-decision:v1"
)
FIN003_REVIEW_TOOL_REF = "tool-ref:finance/FIN-003/synthetic-review-decision:v1"
FIN003_REVIEW_SAFE_DISABLE_REF = (
    "safe-disable-ref:finance/FIN-003/synthetic-review-decision"
)
FIN003_REVIEW_ROLLBACK_REF = (
    "rollback-contract-ref:finance/FIN-003/compensating-review-undo:v1"
)
FIN003_REVIEW_READINESS_REF = (
    "readiness-ref:finance/FIN-003/protected-synthetic-review-decision"
)
FIN003_REVIEW_BUDGET_REF = "budget-ref:finance/FIN-003:one-review-decision"
FIN003_REVIEW_START_DEADLINE_REF = (
    "deadline-ref:finance/FIN-003:review-decision-prepared-window"
)
FIN003_REVIEW_KILL_SWITCH_REF = "kill-switch-ref:finance/FIN-003:local"
FIN003_REVIEW_EXACT_TARGET_REF = "target-ref:finance/FIN-003:protected-local-repository"


def _consequences(
    operation: str, decision: FinanceReviewDecision | None
) -> tuple[str, ...]:
    disposition = {
        "confirm": "acknowledgement-not-categorization-or-validation",
        "reject": "review-disposition-not-posting-reversal",
        "defer": "follow-up-remains-open",
    }
    change = (
        "append-compensation-and-restore-prior-review-posture"
        if operation == "review_undo"
        else disposition[decision]
    )
    return (
        f"consequence-ref:finance/FIN-003:{change}",
        "consequence-ref:finance/FIN-003:journal-postings-and-balances-unchanged",
        "consequence-ref:finance/FIN-003:separate-exact-approval-and-lease-required",
    )


class FinanceReviewPersistencePreview(_FinanceModel):
    """Preview one exact disposition/undo; this object grants no authority."""

    schema_version: Literal["uaa-finance-review-persistence-preview.v1"] = (
        "uaa-finance-review-persistence-preview.v1"
    )
    preview_ref: str
    operation: Literal["review_decision", "review_undo"]
    repository_ref: str
    source_snapshot_ref: str
    source_revision: StrictInt = Field(..., ge=2)
    projection_ref: str
    review_item_ref: str
    lineage_ref: str
    book_ref: str
    import_commit_ref: str
    candidate_ref: str
    journal_entry_ref: str
    decision: FinanceReviewDecision | None = None
    compensates_event_ref: str | None = None
    prior_effective_event_ref: str | None = None
    previous_history_event_ref: str | None = None
    request_ref: str
    idempotency_ref: str
    consequence_refs: tuple[str, ...] = Field(..., min_length=3, max_length=3)
    synthetic_only: Literal[True] = True
    decision_persisted: Literal[False] = False
    execution_authority_granted: Literal[False] = False
    ledger_mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_binding(self) -> "FinanceReviewPersistencePreview":
        if self.operation == "review_decision":
            if self.decision is None or self.compensates_event_ref is not None:
                raise ValueError("FIN003_PERSISTENCE_DECISION_SCOPE_INVALID")
        elif (
            self.decision is not None
            or self.compensates_event_ref is None
            or self.compensates_event_ref != self.prior_effective_event_ref
        ):
            raise ValueError("FIN003_PERSISTENCE_UNDO_SCOPE_INVALID")
        if self.lineage_ref != finance_review_lineage_ref(
            repository_ref=self.repository_ref,
            book_ref=self.book_ref,
            import_commit_ref=self.import_commit_ref,
            candidate_ref=self.candidate_ref,
            journal_entry_ref=self.journal_entry_ref,
        ):
            raise ValueError("FIN003_PERSISTENCE_LINEAGE_INVALID")
        if self.consequence_refs != _consequences(self.operation, self.decision):
            raise ValueError("FIN003_PERSISTENCE_CONSEQUENCES_INVALID")
        if self.preview_ref != stable_finance_ref(
            "review-persistence-preview-ref:finance/FIN-003",
            self.model_dump(mode="json", exclude={"preview_ref"}),
        ):
            raise ValueError("FIN003_PERSISTENCE_PREVIEW_REF_INVALID")
        return self


def preview_finance_review_persistence(
    snapshot: FinanceSnapshot,
    *,
    review_item_ref: str,
    request_ref: str,
    idempotency_ref: str,
    decision: FinanceReviewDecision | None = None,
    compensates_event_ref: str | None = None,
) -> FinanceReviewPersistencePreview:
    """Bind a preview to the exact current item and history, without writing."""

    before = FinanceSnapshot.model_validate(
        snapshot.model_dump(mode="python", warnings=False)
    )
    if len(before.review_decisions) >= FINANCE_REVIEW_EVENT_LIMIT:
        raise ValueError("FIN003_REVIEW_HISTORY_CAPACITY_EXHAUSTED")
    if (decision is None) == (compensates_event_ref is None):
        raise ValueError("FIN003_PERSISTENCE_OPERATION_REQUIRED")
    projection = build_finance_review_projection(before)
    matches = [
        item
        for item in projection.review_items
        if item.review_item_ref == review_item_ref
    ]
    if len(matches) != 1:
        raise ValueError("FIN003_PERSISTENCE_ITEM_NOT_CURRENT")
    item = matches[0]
    lineage = {
        "repository_ref": before.repository_ref,
        "book_ref": item.book_ref,
        "import_commit_ref": item.import_commit_ref,
        "candidate_ref": item.candidate_ref,
        "journal_entry_ref": item.journal_entry_ref,
    }
    lineage_ref = finance_review_lineage_ref(**lineage)
    prior = before.effective_review_decisions().get(lineage_ref)
    if compensates_event_ref is not None and (
        prior is None or compensates_event_ref != prior.event_ref
    ):
        raise ValueError("FIN003_PERSISTENCE_UNDO_TARGET_NOT_CURRENT")
    operation = (
        "review_undo" if compensates_event_ref is not None else "review_decision"
    )
    # Validate the literal before using it as a consequence-map key.
    if decision is not None and decision not in {"confirm", "reject", "defer"}:
        raise ValueError("FIN003_PERSISTENCE_DECISION_UNSUPPORTED")
    payload = {
        **lineage,
        "operation": operation,
        "source_snapshot_ref": before.snapshot_ref,
        "source_revision": before.revision,
        "projection_ref": projection.projection_ref,
        "review_item_ref": review_item_ref,
        "lineage_ref": lineage_ref,
        "decision": decision,
        "compensates_event_ref": compensates_event_ref,
        "prior_effective_event_ref": prior.event_ref if prior else None,
        "previous_history_event_ref": before.review_decisions[-1].event_ref
        if before.review_decisions
        else None,
        "request_ref": request_ref,
        "idempotency_ref": idempotency_ref,
        "consequence_refs": _consequences(operation, decision),
    }
    provisional = FinanceReviewPersistencePreview.model_construct(**payload)
    data = provisional.model_dump(mode="json", exclude={"preview_ref"}, warnings=False)
    return FinanceReviewPersistencePreview.model_validate(
        {
            **data,
            "preview_ref": stable_finance_ref(
                "review-persistence-preview-ref:finance/FIN-003", data
            ),
        }
    )


def build_finance_review_decision_record(
    snapshot: FinanceSnapshot, preview: FinanceReviewPersistencePreview
) -> FinanceReviewDecisionRecord:
    """Rebuild the exact preview at the current source before making a record."""

    bound = FinanceReviewPersistencePreview.model_validate(
        preview.model_dump(mode="python", warnings=False)
    )
    current = preview_finance_review_persistence(
        snapshot,
        review_item_ref=bound.review_item_ref,
        request_ref=bound.request_ref,
        idempotency_ref=bound.idempotency_ref,
        decision=bound.decision,
        compensates_event_ref=bound.compensates_event_ref,
    )
    if current != bound:
        raise ValueError("FIN003_PERSISTENCE_PREVIEW_NOT_CURRENT")
    payload = {
        key: getattr(bound, key)
        for key in (
            "operation",
            "repository_ref",
            "book_ref",
            "import_commit_ref",
            "candidate_ref",
            "journal_entry_ref",
            "lineage_ref",
            "review_item_ref",
            "decision",
            "compensates_event_ref",
            "prior_effective_event_ref",
            "previous_history_event_ref",
            "request_ref",
            "idempotency_ref",
        )
    }
    payload.update(
        decision_preview_ref=bound.preview_ref,
        before_snapshot_ref=bound.source_snapshot_ref,
        before_revision=bound.source_revision,
    )
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
