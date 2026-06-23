from __future__ import annotations

from typing import Any

from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionRequest,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest
from ultimate_ai_agent.core.memory import (
    MemoryContextPackActionProposalRequest,
    MemoryReviewDecisionKind,
    MemoryReviewDecisionRequest,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository


class FounderLoopControlCenterService:
    """API-facing summary service for storage-backed Founder Loop surfaces."""

    def __init__(self, repository: FounderLoopRepository) -> None:
        self.repository = repository

    @classmethod
    def from_env(cls) -> "FounderLoopControlCenterService":
        return cls(FounderLoopRepository.from_env())

    def today_summary(self) -> dict:
        return self.repository.today_summary()

    def evidence_timeline(self) -> dict:
        return self.repository.evidence_timeline()

    def actions_inbox(self) -> dict:
        return self.repository.actions_inbox()

    def memory_review(self) -> dict:
        return self.repository.memory_review()

    def memory_l1_hot_index(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_l1_hot_index(query_ref=query_ref, limit=limit)

    def memory_l2_factual_graph_temporal_index(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_l2_factual_graph_temporal_index(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_l3_identity_session_preference_index(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_l3_identity_session_preference_index(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_context_pack_proposals(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_context_pack_proposals(
            query_ref=query_ref,
            limit=limit,
        )

    def record_memory_context_pack_action_proposal(
        self,
        *,
        context_pack_ref: str,
        request: MemoryContextPackActionProposalRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.record_memory_context_pack_action_proposal(
            context_pack_ref=context_pack_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def promote_today_item_to_action_envelope(
        self,
        *,
        request: FounderLoopActionEnvelopePromotionRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.promote_today_item_to_action_envelope(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def record_action_decision(
        self,
        *,
        action_id: str,
        decision: str,
        request: FounderLoopActionDecisionRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.record_action_decision(
            action_id=action_id,
            decision=decision,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def action_receipt(self, *, action_id: str) -> dict[str, Any] | None:
        return self.repository.latest_action_receipt(action_id)

    def commit_local_task(
        self,
        *,
        action_id: str,
        request: FounderLoopLocalTaskCommitRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.commit_local_task(
            action_id=action_id,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def record_chat_turn_receipt(
        self,
        *,
        request: ChatTurnReceiptRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.record_chat_turn_receipt(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def chat_turn_receipt(self, *, turn_ref: str) -> dict[str, Any] | None:
        return self.repository.latest_chat_turn_receipt(turn_ref)

    def record_chat_handoff(
        self,
        *,
        turn_ref: str,
        request: ChatHandoffRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.record_chat_handoff(
            turn_ref=turn_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def record_memory_review_decision(
        self,
        *,
        candidate_ref: str,
        decision: MemoryReviewDecisionKind,
        request: MemoryReviewDecisionRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.record_memory_review_decision(
            candidate_ref=candidate_ref,
            decision=decision,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def memory_review_receipt(self, *, candidate_ref: str) -> dict[str, Any] | None:
        return self.repository.latest_memory_review_receipt(candidate_ref)

    def morning_briefing_summary(self) -> dict:
        return self.repository.morning_briefing()

    def storage_status(self) -> dict:
        status = self.repository.storage_status()
        status["backup_manifest"] = self.repository.backup_manifest()
        return status
