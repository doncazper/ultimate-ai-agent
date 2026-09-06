"""Synthetic-only FIN-003 review-decision previews."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, StrictInt, model_validator

from ultimate_ai_agent.core.finance.models import (
    FinanceSnapshot,
    _FinanceModel,
    stable_finance_ref,
)
from ultimate_ai_agent.core.finance.review_projection import (
    FinanceReviewItem,
    FinanceReviewProjection,
    build_finance_review_projection,
)


FinanceReviewDecision = Literal["confirm", "reject", "defer"]

FIN003_PREVIEW_UNCHANGED_CONSEQUENCE_REF = (
    "consequence-ref:finance/FIN-003:preview-leaves-review-and-book-unchanged"
)


def _decision_consequence_refs(
    decision: FinanceReviewDecision,
) -> tuple[str, str]:
    """Return the fixed content-free consequences for one preview decision."""

    if decision == "confirm":
        decision_ref = "consequence-ref:finance/FIN-003:confirmation-requires-separate-approved-apply"
    elif decision == "reject":
        decision_ref = (
            "consequence-ref:finance/FIN-003:rejection-requires-separate-approved-apply"
        )
    elif decision == "defer":
        decision_ref = (
            "consequence-ref:finance/FIN-003:deferral-requires-separate-approved-apply"
        )
    else:  # pragma: no cover - the Pydantic literal rejects this first.
        raise ValueError("FIN003_REVIEW_DECISION_UNSUPPORTED")
    return decision_ref, FIN003_PREVIEW_UNCHANGED_CONSEQUENCE_REF


class FinanceReviewDecisionPreviewRequest(_FinanceModel):
    """Content-free request bound to one exact current review projection item."""

    schema_version: Literal["uaa-finance-review-decision-preview-request.v1"] = (
        "uaa-finance-review-decision-preview-request.v1"
    )
    decision_request_ref: str
    projection_ref: str
    source_snapshot_ref: str
    source_revision: StrictInt = Field(..., ge=0)
    review_item_ref: str
    decision: FinanceReviewDecision
    synthetic_only: Literal[True] = True
    arbitrary_input_allowed: Literal[False] = False
    persistence_authority_requested: Literal[False] = False
    mutation_authority_requested: Literal[False] = False

    @model_validator(mode="after")
    def validate_request_binding(self) -> "FinanceReviewDecisionPreviewRequest":
        """Require a canonical request ref over every exact input."""

        expected = stable_finance_ref(
            "review-decision-request-ref:finance/FIN-003",
            self.model_dump(mode="json", exclude={"decision_request_ref"}),
        )
        if self.decision_request_ref != expected:
            raise ValueError("FIN003_REVIEW_DECISION_REQUEST_REF_INVALID")
        return self


class FinanceReviewDecisionPreview(_FinanceModel):
    """Non-persisted consequence preview for one synthetic review item."""

    schema_version: Literal["uaa-finance-review-decision-preview.v1"] = (
        "uaa-finance-review-decision-preview.v1"
    )
    preview_ref: str
    decision_request_ref: str
    projection_ref: str
    source_snapshot_ref: str
    source_revision: StrictInt = Field(..., ge=0)
    review_item_ref: str
    decision: FinanceReviewDecision
    consequence_refs: tuple[str, ...] = Field(..., min_length=2, max_length=2)
    state: Literal["proposal_only"] = "proposal_only"
    synthetic_only: Literal[True] = True
    content_free: Literal[True] = True
    raw_financial_values_included: Literal[False] = False
    real_financial_data_included: Literal[False] = False
    decision_persisted: Literal[False] = False
    review_item_state_changed: Literal[False] = False
    ledger_mutation_performed: Literal[False] = False
    action_inbox_mutation_performed: Literal[False] = False
    correction_input_allowed: Literal[False] = False
    rule_proposal_created: Literal[False] = False
    approval_authority_granted: Literal[False] = False
    execution_authority_granted: Literal[False] = False
    external_write_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_preview_binding(self) -> "FinanceReviewDecisionPreview":
        """Require the fixed decision consequences and a canonical preview ref."""

        if self.consequence_refs != _decision_consequence_refs(self.decision):
            raise ValueError("FIN003_REVIEW_DECISION_CONSEQUENCES_INVALID")
        try:
            FinanceReviewDecisionPreviewRequest(
                decision_request_ref=self.decision_request_ref,
                projection_ref=self.projection_ref,
                source_snapshot_ref=self.source_snapshot_ref,
                source_revision=self.source_revision,
                review_item_ref=self.review_item_ref,
                decision=self.decision,
            )
        except ValueError:
            raise ValueError("FIN003_REVIEW_DECISION_REQUEST_BINDING_INVALID") from None
        expected = stable_finance_ref(
            "review-decision-preview-ref:finance/FIN-003",
            self.model_dump(mode="json", exclude={"preview_ref"}),
        )
        if self.preview_ref != expected:
            raise ValueError("FIN003_REVIEW_DECISION_PREVIEW_REF_INVALID")
        return self


def _current_projection(snapshot: FinanceSnapshot) -> FinanceReviewProjection:
    """Revalidate and project the supplied current synthetic snapshot."""

    current = FinanceSnapshot.model_validate(
        snapshot.model_dump(mode="python", warnings=False)
    )
    return build_finance_review_projection(current)


def _find_review_item(
    projection: FinanceReviewProjection,
    review_item_ref: str,
) -> FinanceReviewItem:
    matches = tuple(
        item
        for item in projection.review_items
        if item.review_item_ref == review_item_ref
    )
    if len(matches) != 1:
        raise ValueError("FIN003_REVIEW_DECISION_ITEM_NOT_CURRENT")
    return matches[0]


def build_finance_review_decision_preview_request(
    snapshot: FinanceSnapshot,
    *,
    review_item_ref: str,
    decision: FinanceReviewDecision,
) -> FinanceReviewDecisionPreviewRequest:
    """Bind one allowed preview decision to the current synthetic projection."""

    projection = _current_projection(snapshot)
    _find_review_item(projection, review_item_ref)
    payload = {
        "projection_ref": projection.projection_ref,
        "source_snapshot_ref": projection.source_snapshot_ref,
        "source_revision": projection.source_revision,
        "review_item_ref": review_item_ref,
        "decision": decision,
    }
    provisional = FinanceReviewDecisionPreviewRequest.model_construct(
        decision_request_ref="review-decision-request-ref:finance/FIN-003:pending",
        **payload,
    )
    return FinanceReviewDecisionPreviewRequest(
        decision_request_ref=stable_finance_ref(
            "review-decision-request-ref:finance/FIN-003",
            provisional.model_dump(
                mode="json", exclude={"decision_request_ref"}, warnings=False
            ),
        ),
        **payload,
    )


def preview_finance_review_decision(
    snapshot: FinanceSnapshot,
    request: FinanceReviewDecisionPreviewRequest,
) -> FinanceReviewDecisionPreview:
    """Preview fixed safe-ref consequences without persisting a decision."""

    bound_request = FinanceReviewDecisionPreviewRequest.model_validate(
        request.model_dump(mode="python", warnings=False)
    )
    projection = _current_projection(snapshot)
    if bound_request.projection_ref != projection.projection_ref:
        raise ValueError("FIN003_REVIEW_DECISION_PROJECTION_NOT_CURRENT")
    if (
        bound_request.source_snapshot_ref != projection.source_snapshot_ref
        or bound_request.source_revision != projection.source_revision
    ):
        raise ValueError("FIN003_REVIEW_DECISION_SNAPSHOT_NOT_CURRENT")
    _find_review_item(projection, bound_request.review_item_ref)

    payload = {
        "decision_request_ref": bound_request.decision_request_ref,
        "projection_ref": projection.projection_ref,
        "source_snapshot_ref": projection.source_snapshot_ref,
        "source_revision": projection.source_revision,
        "review_item_ref": bound_request.review_item_ref,
        "decision": bound_request.decision,
        "consequence_refs": _decision_consequence_refs(bound_request.decision),
    }
    provisional = FinanceReviewDecisionPreview.model_construct(
        preview_ref="review-decision-preview-ref:finance/FIN-003:pending",
        **payload,
    )
    return FinanceReviewDecisionPreview(
        preview_ref=stable_finance_ref(
            "review-decision-preview-ref:finance/FIN-003",
            provisional.model_dump(
                mode="json", exclude={"preview_ref"}, warnings=False
            ),
        ),
        **payload,
    )
