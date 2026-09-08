from __future__ import annotations

from typing import Any

from ultimate_ai_agent.core.control_center.action_decisions import (
    FounderLoopActionDecisionRequest,
    FounderLoopActionEnvelopePromotionRequest,
)
from ultimate_ai_agent.core.control_center.backend_truth import (
    build_control_center_backend_truth,
)
from ultimate_ai_agent.core.control_center.agent_loop import (
    build_agent_loop_thread_read_model,
)
from ultimate_ai_agent.core.control_center.local_tasks import (
    FounderLoopLocalTaskCommitRequest,
)
from ultimate_ai_agent.core.control_center.proof import (
    build_control_center_proof_detail,
    build_control_center_proof_index,
)
from ultimate_ai_agent.core.control_center.start_here import (
    build_control_center_start_here_summary,
)
from ultimate_ai_agent.core.control_center.trust_authority import (
    build_trust_authority_matrix_read_model,
)
from ultimate_ai_agent.core.control_center.web_evidence_product_slice import (
    WebEvidenceProductSliceRequest,
    build_web_evidence_product_slice_receipt,
)
from ultimate_ai_agent.core.authority import AuthorityLease
from ultimate_ai_agent.core.chat import ChatHandoffRequest, ChatTurnReceiptRequest
from ultimate_ai_agent.core.memory import (
    ManualMemoryCandidateRequest,
    MemoryContextPackActionProposalRequest,
    MemoryFeedbackRequest,
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

    def backend_truth(self) -> dict[str, Any]:
        return build_control_center_backend_truth(repo=self.repository)

    def start_here_summary(self) -> dict:
        return build_control_center_start_here_summary(
            today_summary=self.repository.today_summary()
        )

    def proof_index(self) -> dict:
        return build_control_center_proof_index(
            today_summary=self.repository.today_summary(limit=50)
        )

    def proof_detail(self, proof_ref: str) -> dict:
        return build_control_center_proof_detail(
            today_summary=self.repository.today_summary(limit=50),
            proof_ref=proof_ref,
        )

    def trust_authority_matrix(self) -> dict:
        return build_trust_authority_matrix_read_model(
            today_summary=self.repository.today_summary()
        )

    def evidence_timeline(self) -> dict:
        return self.repository.evidence_timeline()

    def agent_loop_thread(self) -> dict[str, Any]:
        return build_agent_loop_thread_read_model(
            today_summary=self.repository.today_summary(limit=12),
            actions_inbox=self.repository.actions_inbox(limit=50),
            evidence_timeline=self.repository.evidence_timeline(limit=50),
            memory_review=self.repository.memory_review(limit=20),
            proof_index=self.proof_index(),
            trust_authority_matrix=self.trust_authority_matrix(),
        )

    def attach_web_evidence(
        self,
        request: WebEvidenceProductSliceRequest,
        *,
        transport: Any | None = None,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> dict[str, Any]:
        receipt = build_web_evidence_product_slice_receipt(
            request,
            transport=transport,
            active_authority_leases=active_authority_leases,
        )
        durable_record = self.repository.record_web_evidence_attachment(receipt)
        replayed = bool(durable_record.get("replayed", False))
        response = receipt.model_copy(update={"replayed": replayed}).model_dump(
            mode="json"
        )
        response["durable_record_ref"] = durable_record["attachment_ref"]
        return response

    def actions_inbox(self) -> dict:
        return self.repository.actions_inbox()

    def memory_review(self) -> dict:
        return self.repository.memory_review()

    def memory_workbench(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_workbench(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )

    def memory_search(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        kind: str | None = None,
        source_ref: str | None = None,
        project_ref: str | None = None,
        person_ref: str | None = None,
        org_ref: str | None = None,
        deal_ref: str | None = None,
        review_state: str | None = None,
        quality_state: str | None = None,
        stale_state: str | None = None,
        conflict_state: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_search(
            query_ref=query_ref,
            safe_query=safe_query,
            kind=kind,
            source_ref=source_ref,
            project_ref=project_ref,
            person_ref=person_ref,
            org_ref=org_ref,
            deal_ref=deal_ref,
            review_state=review_state,
            quality_state=quality_state,
            stale_state=stale_state,
            conflict_state=conflict_state,
            limit=limit,
        )

    def memory_impact_graph(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_impact_graph(query_ref=query_ref, limit=limit)

    def memory_follow_up_queue(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_follow_up_queue(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_recall_health_v2(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_recall_health_v2(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_retrieval_diagnostics(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_retrieval_diagnostics(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_citation_integrity(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_citation_integrity(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_quality_issues(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_quality_issues(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_maintenance_runs(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_maintenance_runs(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_context_manifest(
        self,
        *,
        query_ref: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_context_manifest(
            query_ref=query_ref,
            limit=limit,
        )

    def memory_l1_hot_index(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_l1_hot_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )

    def memory_l2_factual_graph_temporal_index(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_l2_factual_graph_temporal_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )

    def memory_l3_identity_session_preference_index(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_l3_identity_session_preference_index(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )

    def memory_context_pack_proposals(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_context_pack_proposals(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )

    def memory_context_pack_preview(
        self,
        *,
        context_pack_ref: str,
    ) -> dict[str, Any]:
        return self.repository.memory_context_pack_preview(
            context_pack_ref=context_pack_ref,
        )

    def record_memory_feedback(
        self,
        *,
        request: MemoryFeedbackRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.record_memory_feedback(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def memory_observation_candidates(
        self,
        *,
        query_ref: str | None = None,
        safe_query: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return self.repository.memory_observation_candidates(
            query_ref=query_ref,
            safe_query=safe_query,
            limit=limit,
        )

    def memory_probe(self, *, entity_ref: str, limit: int = 20) -> dict[str, Any]:
        return self.repository.memory_probe(entity_ref=entity_ref, limit=limit)

    def memory_contradictions(self, *, limit: int = 20) -> dict[str, Any]:
        return self.repository.memory_contradictions(limit=limit)

    def record_memory_context_pack_action_proposal(
        self,
        *,
        context_pack_ref: str,
        request: MemoryContextPackActionProposalRequest,
        idempotency_key_ref: str,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> dict[str, Any]:
        return self.repository.record_memory_context_pack_action_proposal(
            context_pack_ref=context_pack_ref,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            active_authority_leases=active_authority_leases,
        )

    def promote_today_item_to_action_envelope(
        self,
        *,
        request: FounderLoopActionEnvelopePromotionRequest,
        idempotency_key_ref: str,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> dict[str, Any]:
        return self.repository.promote_today_item_to_action_envelope(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            active_authority_leases=active_authority_leases,
        )

    def record_action_decision(
        self,
        *,
        action_id: str,
        decision: str,
        request: FounderLoopActionDecisionRequest,
        idempotency_key_ref: str,
        active_authority_leases: list[AuthorityLease] | None = None,
    ) -> dict[str, Any]:
        return self.repository.record_action_decision(
            action_id=action_id,
            decision=decision,
            request=request,
            idempotency_key_ref=idempotency_key_ref,
            active_authority_leases=active_authority_leases,
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

    def record_manual_memory_candidate(
        self,
        *,
        request: ManualMemoryCandidateRequest,
        idempotency_key_ref: str,
    ) -> dict[str, Any]:
        return self.repository.record_manual_memory_candidate(
            request=request,
            idempotency_key_ref=idempotency_key_ref,
        )

    def memory_review_receipt(self, *, candidate_ref: str) -> dict[str, Any] | None:
        return self.repository.latest_memory_review_receipt(candidate_ref)

    def morning_briefing_summary(self) -> dict:
        return self.repository.morning_briefing()

    def source_readiness(self) -> dict:
        return self.repository.source_readiness()

    def storage_status(self) -> dict:
        status = self.repository.storage_status()
        status["backup_manifest"] = self.repository.backup_manifest()
        return status
