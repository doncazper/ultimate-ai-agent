"""Synthetic-only FIN-003 Finance Review and Action Inbox projections."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, StrictInt, model_validator

from ultimate_ai_agent.core.finance.import_commit import (
    FIN002_SUSPENSE_ACCOUNT_REF,
)
from ultimate_ai_agent.core.finance.models import (
    FinanceSnapshot,
    JournalFlow,
    _FinanceModel,
    stable_finance_ref,
)


FIN003_REVIEW_REASON_REFS = (
    "reason-ref:finance/FIN-003:suspense-categorization-review",
    "reason-ref:finance/FIN-003:synthetic-import-lineage-present",
)
FIN003_REVIEW_CONSEQUENCE_REF = (
    "consequence-ref:finance/FIN-003:posting-remains-in-suspense"
)
FIN003_RANKING_BASIS_REF = (
    "ranking-basis-ref:finance/FIN-003:newest-import-then-stable-lineage"
)
FIN003_NEXT_SAFE_ACTION_REF = (
    "next-safe-action-ref:finance/FIN-003:inspect-synthetic-review-batch"
)


class FinanceReviewItem(_FinanceModel):
    """One content-free review pointer derived from synthetic import lineage."""

    schema_version: Literal["uaa-finance-review-item.v1"] = "uaa-finance-review-item.v1"
    review_item_ref: str
    rank: StrictInt = Field(..., ge=1, le=10_000)
    book_ref: str
    import_commit_ref: str
    candidate_ref: str
    journal_entry_ref: str
    state: Literal["needs_review"] = "needs_review"
    reason_refs: tuple[str, ...] = FIN003_REVIEW_REASON_REFS
    consequence_ref: str = FIN003_REVIEW_CONSEQUENCE_REF
    confidence_posture: Literal["not_scored"] = "not_scored"
    synthetic_only: Literal[True] = True
    raw_financial_values_included: Literal[False] = False
    decision_authority_granted: Literal[False] = False
    mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_item_binding(self) -> "FinanceReviewItem":
        expected = stable_finance_ref(
            "review-item-ref:finance/FIN-003",
            self.model_dump(mode="json", exclude={"review_item_ref"}),
        )
        if self.review_item_ref != expected:
            raise ValueError("FIN003_REVIEW_ITEM_REF_INVALID")
        if self.reason_refs != FIN003_REVIEW_REASON_REFS:
            raise ValueError("FIN003_REVIEW_REASON_REFS_INVALID")
        if self.consequence_ref != FIN003_REVIEW_CONSEQUENCE_REF:
            raise ValueError("FIN003_REVIEW_CONSEQUENCE_REF_INVALID")
        return self


class FinanceReviewBatch(_FinanceModel):
    """One deterministic review batch for an exact synthetic import commit."""

    schema_version: Literal["uaa-finance-review-batch.v1"] = (
        "uaa-finance-review-batch.v1"
    )
    review_batch_ref: str
    rank: StrictInt = Field(..., ge=1, le=10_000)
    book_ref: str
    import_commit_ref: str
    review_item_refs: tuple[str, ...] = Field(..., min_length=1, max_length=128)
    item_count: StrictInt = Field(..., ge=1, le=128)
    state: Literal["needs_review"] = "needs_review"
    ranking_basis_ref: str = FIN003_RANKING_BASIS_REF
    synthetic_only: Literal[True] = True
    raw_financial_values_included: Literal[False] = False
    decision_authority_granted: Literal[False] = False
    mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_batch_binding(self) -> "FinanceReviewBatch":
        if self.item_count != len(self.review_item_refs):
            raise ValueError("FIN003_REVIEW_BATCH_COUNT_INVALID")
        if len(self.review_item_refs) != len(set(self.review_item_refs)):
            raise ValueError("FIN003_REVIEW_BATCH_ITEM_REF_DUPLICATE")
        if self.ranking_basis_ref != FIN003_RANKING_BASIS_REF:
            raise ValueError("FIN003_REVIEW_RANKING_BASIS_INVALID")
        expected = stable_finance_ref(
            "review-batch-ref:finance/FIN-003",
            self.model_dump(mode="json", exclude={"review_batch_ref"}),
        )
        if self.review_batch_ref != expected:
            raise ValueError("FIN003_REVIEW_BATCH_REF_INVALID")
        return self


class FinanceActionInboxProjection(_FinanceModel):
    """Read-only Action Inbox pointer for one finance review batch."""

    schema_version: Literal["uaa-finance-action-inbox-projection.v1"] = (
        "uaa-finance-action-inbox-projection.v1"
    )
    action_projection_ref: str
    rank: StrictInt = Field(..., ge=1, le=10_000)
    review_batch_ref: str
    action_kind: Literal["finance_review_batch"] = "finance_review_batch"
    state: Literal["needs_review"] = "needs_review"
    next_safe_action_ref: str = FIN003_NEXT_SAFE_ACTION_REF
    proposal_only: Literal[True] = True
    synthetic_only: Literal[True] = True
    raw_financial_values_included: Literal[False] = False
    approval_authority_granted: Literal[False] = False
    execution_authority_granted: Literal[False] = False
    mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_action_binding(self) -> "FinanceActionInboxProjection":
        if self.next_safe_action_ref != FIN003_NEXT_SAFE_ACTION_REF:
            raise ValueError("FIN003_NEXT_SAFE_ACTION_REF_INVALID")
        expected = stable_finance_ref(
            "action-projection-ref:finance/FIN-003",
            self.model_dump(mode="json", exclude={"action_projection_ref"}),
        )
        if self.action_projection_ref != expected:
            raise ValueError("FIN003_ACTION_PROJECTION_REF_INVALID")
        return self


class FinanceReviewProjection(_FinanceModel):
    """Complete content-free projection over one current FinanceSnapshot."""

    schema_version: Literal["uaa-finance-review-projection.v1"] = (
        "uaa-finance-review-projection.v1"
    )
    projection_ref: str
    repository_ref: str
    source_snapshot_ref: str
    source_revision: StrictInt = Field(..., ge=0)
    review_items: tuple[FinanceReviewItem, ...] = Field(default=(), max_length=10_000)
    review_batches: tuple[FinanceReviewBatch, ...] = Field(
        default=(), max_length=10_000
    )
    action_inbox: tuple[FinanceActionInboxProjection, ...] = Field(
        default=(), max_length=10_000
    )
    ranking_basis_ref: str = FIN003_RANKING_BASIS_REF
    read_model_only: Literal[True] = True
    synthetic_only: Literal[True] = True
    arbitrary_input_allowed: Literal[False] = False
    raw_financial_values_included: Literal[False] = False
    real_financial_data_included: Literal[False] = False
    connector_authority_granted: Literal[False] = False
    decision_authority_granted: Literal[False] = False
    execution_authority_granted: Literal[False] = False
    mutation_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_projection_binding(self) -> "FinanceReviewProjection":
        item_refs = tuple(item.review_item_ref for item in self.review_items)
        batch_item_refs = tuple(
            item_ref
            for batch in self.review_batches
            for item_ref in batch.review_item_refs
        )
        batch_refs = tuple(batch.review_batch_ref for batch in self.review_batches)
        action_batch_refs = tuple(item.review_batch_ref for item in self.action_inbox)
        if item_refs != batch_item_refs:
            raise ValueError("FIN003_REVIEW_PROJECTION_ITEM_GRAPH_INVALID")
        if batch_refs != action_batch_refs:
            raise ValueError("FIN003_REVIEW_PROJECTION_ACTION_GRAPH_INVALID")
        if tuple(item.rank for item in self.review_items) != tuple(
            range(1, len(self.review_items) + 1)
        ):
            raise ValueError("FIN003_REVIEW_ITEM_RANK_INVALID")
        expected_batch_ranks = tuple(range(1, len(self.review_batches) + 1))
        if tuple(item.rank for item in self.review_batches) != expected_batch_ranks:
            raise ValueError("FIN003_REVIEW_BATCH_RANK_INVALID")
        if tuple(item.rank for item in self.action_inbox) != expected_batch_ranks:
            raise ValueError("FIN003_ACTION_PROJECTION_RANK_INVALID")
        if self.ranking_basis_ref != FIN003_RANKING_BASIS_REF:
            raise ValueError("FIN003_REVIEW_RANKING_BASIS_INVALID")
        expected = stable_finance_ref(
            "review-projection-ref:finance/FIN-003",
            self.model_dump(mode="json", exclude={"projection_ref"}),
        )
        if self.projection_ref != expected:
            raise ValueError("FIN003_REVIEW_PROJECTION_REF_INVALID")
        return self


def _review_item(
    *,
    rank: int,
    book_ref: str,
    import_commit_ref: str,
    candidate_ref: str,
    journal_entry_ref: str,
) -> FinanceReviewItem:
    payload = {
        "rank": rank,
        "book_ref": book_ref,
        "import_commit_ref": import_commit_ref,
        "candidate_ref": candidate_ref,
        "journal_entry_ref": journal_entry_ref,
    }
    provisional = FinanceReviewItem.model_construct(
        review_item_ref="review-item-ref:finance/FIN-003:pending", **payload
    )
    return FinanceReviewItem(
        review_item_ref=stable_finance_ref(
            "review-item-ref:finance/FIN-003",
            provisional.model_dump(mode="json", exclude={"review_item_ref"}),
        ),
        **payload,
    )


def _review_batch(
    *,
    rank: int,
    book_ref: str,
    import_commit_ref: str,
    review_item_refs: tuple[str, ...],
) -> FinanceReviewBatch:
    payload = {
        "rank": rank,
        "book_ref": book_ref,
        "import_commit_ref": import_commit_ref,
        "review_item_refs": review_item_refs,
        "item_count": len(review_item_refs),
    }
    provisional = FinanceReviewBatch.model_construct(
        review_batch_ref="review-batch-ref:finance/FIN-003:pending", **payload
    )
    return FinanceReviewBatch(
        review_batch_ref=stable_finance_ref(
            "review-batch-ref:finance/FIN-003",
            provisional.model_dump(mode="json", exclude={"review_batch_ref"}),
        ),
        **payload,
    )


def _action_projection(
    *, rank: int, review_batch_ref: str
) -> FinanceActionInboxProjection:
    payload = {"rank": rank, "review_batch_ref": review_batch_ref}
    provisional = FinanceActionInboxProjection.model_construct(
        action_projection_ref="action-projection-ref:finance/FIN-003:pending",
        **payload,
    )
    return FinanceActionInboxProjection(
        action_projection_ref=stable_finance_ref(
            "action-projection-ref:finance/FIN-003",
            provisional.model_dump(mode="json", exclude={"action_projection_ref"}),
        ),
        **payload,
    )


def build_finance_review_projection(
    snapshot: FinanceSnapshot,
) -> FinanceReviewProjection:
    """Project outstanding synthetic import lineage without exposing values."""

    if (
        not snapshot.synthetic_only
        or snapshot.real_financial_data_allowed
        or snapshot.connector_authority_granted
        or snapshot.payment_authority_granted
        or snapshot.filing_authority_granted
    ):
        raise ValueError("FIN003_REVIEW_SOURCE_POSTURE_DENIED")

    entries = {item.journal_entry_ref: item for item in snapshot.journal_entries}
    reversed_refs = {
        item.reverses_journal_entry_ref
        for item in snapshot.journal_entries
        if item.reverses_journal_entry_ref is not None
    }
    records = sorted(
        snapshot.import_commits,
        key=lambda item: (-item.before_revision, item.commit_ref),
    )
    review_items: list[FinanceReviewItem] = []
    review_batches: list[FinanceReviewBatch] = []
    action_inbox: list[FinanceActionInboxProjection] = []

    for record in records:
        batch_items: list[FinanceReviewItem] = []
        book_ref: str | None = None
        for candidate_ref, journal_entry_ref in zip(
            record.candidate_refs, record.journal_entry_refs, strict=True
        ):
            if journal_entry_ref in reversed_refs:
                continue
            entry = entries.get(journal_entry_ref)
            if entry is None:
                raise ValueError("FIN003_REVIEW_JOURNAL_REF_UNKNOWN")
            if entry.flow != JournalFlow.suspense.value:
                raise ValueError("FIN003_REVIEW_JOURNAL_FLOW_INVALID")
            if not any(
                posting.account_ref == FIN002_SUSPENSE_ACCOUNT_REF
                for posting in entry.postings
            ):
                raise ValueError("FIN003_REVIEW_SUSPENSE_POSTING_MISSING")
            if book_ref is None:
                book_ref = entry.book_ref
            elif book_ref != entry.book_ref:
                raise ValueError("FIN003_REVIEW_BATCH_BOOK_SCOPE_INVALID")
            item = _review_item(
                rank=len(review_items) + len(batch_items) + 1,
                book_ref=entry.book_ref,
                import_commit_ref=record.commit_ref,
                candidate_ref=candidate_ref,
                journal_entry_ref=journal_entry_ref,
            )
            batch_items.append(item)
        if not batch_items or book_ref is None:
            continue
        batch = _review_batch(
            rank=len(review_batches) + 1,
            book_ref=book_ref,
            import_commit_ref=record.commit_ref,
            review_item_refs=tuple(item.review_item_ref for item in batch_items),
        )
        review_items.extend(batch_items)
        review_batches.append(batch)
        action_inbox.append(
            _action_projection(
                rank=len(action_inbox) + 1,
                review_batch_ref=batch.review_batch_ref,
            )
        )

    payload = {
        "repository_ref": snapshot.repository_ref,
        "source_snapshot_ref": snapshot.snapshot_ref,
        "source_revision": snapshot.revision,
        "review_items": tuple(review_items),
        "review_batches": tuple(review_batches),
        "action_inbox": tuple(action_inbox),
    }
    provisional = FinanceReviewProjection.model_construct(
        projection_ref="review-projection-ref:finance/FIN-003:pending", **payload
    )
    return FinanceReviewProjection(
        projection_ref=stable_finance_ref(
            "review-projection-ref:finance/FIN-003",
            provisional.model_dump(mode="json", exclude={"projection_ref"}),
        ),
        **payload,
    )
