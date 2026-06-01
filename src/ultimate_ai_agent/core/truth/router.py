from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.hygiene.actor_context import ActorContext
from ultimate_ai_agent.core.truth.enums import GroundingMode, TruthSourceType, TruthTaskClass
from ultimate_ai_agent.core.truth.grounding import HIGH_STAKES_TASKS, GroundingPolicy
from ultimate_ai_agent.core.truth.sources import TruthSourceManifest, is_source_selectable


STRUCTURED_SOURCE_TYPES = [
    TruthSourceType.api,
    TruthSourceType.database,
    TruthSourceType.provider_result,
]


DEFAULT_REQUIRED_SOURCE_TYPES = {
    TruthTaskClass.project_truth: [TruthSourceType.canonical_file],
    TruthTaskClass.live_status: STRUCTURED_SOURCE_TYPES,
    TruthTaskClass.weather: [TruthSourceType.provider_result, TruthSourceType.api],
    TruthTaskClass.news: [TruthSourceType.provider_result, TruthSourceType.approved_document],
    TruthTaskClass.metrics: STRUCTURED_SOURCE_TYPES,
    TruthTaskClass.policy: [TruthSourceType.canonical_file, TruthSourceType.approved_document],
    TruthTaskClass.code_status: [
        TruthSourceType.canonical_file,
        TruthSourceType.api,
        TruthSourceType.database,
        TruthSourceType.event_ledger,
        TruthSourceType.file,
    ],
    TruthTaskClass.factual_answer: [
        TruthSourceType.canonical_file,
        TruthSourceType.approved_document,
        TruthSourceType.api,
        TruthSourceType.database,
        TruthSourceType.provider_result,
        TruthSourceType.event_ledger,
        TruthSourceType.world_state,
        TruthSourceType.file,
        TruthSourceType.user_instruction,
    ],
    TruthTaskClass.research: [
        TruthSourceType.canonical_file,
        TruthSourceType.approved_document,
        TruthSourceType.api,
        TruthSourceType.database,
        TruthSourceType.provider_result,
        TruthSourceType.external_source,
        TruthSourceType.file,
    ],
}


SOURCE_SELECTION_PRIORITY = {
    TruthSourceType.canonical_file: 0,
    TruthSourceType.database: 1,
    TruthSourceType.api: 2,
    TruthSourceType.provider_result: 3,
    TruthSourceType.event_ledger: 4,
    TruthSourceType.world_state: 5,
    TruthSourceType.approved_document: 6,
    TruthSourceType.file: 7,
    TruthSourceType.user_instruction: 8,
    TruthSourceType.external_source: 9,
    TruthSourceType.memory: 10,
    TruthSourceType.model_output: 99,
}


class TruthRouteRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    actor_context: ActorContext
    task_class: TruthTaskClass
    question_or_claim: str = Field(..., min_length=1)
    grounding_policy: GroundingPolicy
    available_sources: List[TruthSourceManifest] = Field(default_factory=list)
    data_classification: str = "public"
    consent_refs: List[str] = Field(default_factory=list)
    context_refs: List[str] = Field(default_factory=list)
    current_time: Optional[datetime] = None
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class TruthRouteDecision(BaseModel):
    request_id: str
    run_id: str
    selected_source_ids: List[str] = Field(default_factory=list)
    rejected_source_ids: List[str] = Field(default_factory=list)
    required_source_types: List[TruthSourceType] = Field(default_factory=list)
    reason_codes: List[str] = Field(default_factory=list)
    required_next_action: Optional[str] = None
    requires_human_review: bool = False
    safe_message: str
    unsupported_claim_behavior: str
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class TruthSourceRouter:
    """Deterministic source-selection policy; it never fetches or executes providers."""

    def route(self, request: TruthRouteRequest) -> TruthRouteDecision:
        policy = request.grounding_policy
        required_source_types = self._required_source_types(request)
        reason_codes: List[str] = []
        rejected_source_ids: List[str] = []
        eligible_sources: List[TruthSourceManifest] = []
        saw_memory = False

        for source in request.available_sources:
            rejected_reason = self._rejection_reason(source, request)
            if rejected_reason:
                rejected_source_ids.append(source.source_id)
                self._append_reason(reason_codes, rejected_reason)
                continue
            if source.source_type == TruthSourceType.memory:
                saw_memory = True
            eligible_sources.append(source)

        selected_sources = self._select_sources(eligible_sources, required_source_types, policy)

        if saw_memory and selected_sources and any(source.source_type != TruthSourceType.memory for source in selected_sources):
            self._append_reason(reason_codes, "MEMORY_SUPPORTING_ONLY")

        if not selected_sources and self._sources_are_required(request):
            self._append_reason(reason_codes, "REQUIRED_SOURCE_UNAVAILABLE")
            next_action = policy.unsupported_claim_behavior or "ask_for_source"
            return TruthRouteDecision(
                request_id=request.request_id,
                run_id=request.run_id,
                selected_source_ids=[],
                rejected_source_ids=rejected_source_ids,
                required_source_types=required_source_types,
                reason_codes=reason_codes,
                required_next_action=next_action,
                requires_human_review=self._requires_human_review(policy),
                safe_message="No approved source is available for this grounded claim.",
                unsupported_claim_behavior=policy.unsupported_claim_behavior,
                event_ref=request.event_ref,
            )

        return TruthRouteDecision(
            request_id=request.request_id,
            run_id=request.run_id,
            selected_source_ids=[source.source_id for source in selected_sources],
            rejected_source_ids=rejected_source_ids,
            required_source_types=required_source_types,
            reason_codes=reason_codes,
            required_next_action="human_review" if self._requires_human_review(policy) else None,
            requires_human_review=self._requires_human_review(policy),
            safe_message="Approved source route selected." if selected_sources else "No grounded source route was required.",
            unsupported_claim_behavior=policy.unsupported_claim_behavior,
            event_ref=request.event_ref,
        )

    def _required_source_types(self, request: TruthRouteRequest) -> List[TruthSourceType]:
        policy = request.grounding_policy
        if policy.required_source_types:
            return list(policy.required_source_types)
        if policy.grounding_mode == GroundingMode.canonical_required:
            return [TruthSourceType.canonical_file]
        if policy.grounding_mode == GroundingMode.api_or_database_required:
            return [TruthSourceType.api, TruthSourceType.database, TruthSourceType.provider_result]
        if policy.grounding_mode == GroundingMode.none:
            return []
        return list(DEFAULT_REQUIRED_SOURCE_TYPES.get(request.task_class, []))

    def _rejection_reason(self, source: TruthSourceManifest, request: TruthRouteRequest) -> Optional[str]:
        if source.source_type == TruthSourceType.model_output:
            return "MODEL_OUTPUT_NOT_AUTHORITY"
        if source.source_type in request.grounding_policy.forbidden_source_types:
            return "SOURCE_TYPE_FORBIDDEN"
        if source.data_classification == "credential_secret":
            return "SECRET_SOURCE_BLOCKED"
        if not is_source_selectable(source, request.consent_refs):
            return "CONSENT_REQUIRED"
        return None

    def _select_sources(
        self,
        sources: List[TruthSourceManifest],
        required_source_types: List[TruthSourceType],
        policy: GroundingPolicy,
    ) -> List[TruthSourceManifest]:
        candidate_types = required_source_types or policy.preferred_source_types
        if candidate_types:
            sources = [source for source in sources if source.source_type in candidate_types]
        if not sources:
            return []

        ranked = sorted(
            sources,
            key=lambda source: (
                SOURCE_SELECTION_PRIORITY.get(source.source_type, 50),
                source.canonical_priority if source.canonical_priority is not None else 999,
                -source.authority_rank,
                source.source_id,
            ),
        )
        count = max(1, policy.min_evidence_count)
        return ranked[:count]

    def _sources_are_required(self, request: TruthRouteRequest) -> bool:
        policy = request.grounding_policy
        if policy.grounding_mode in {
            GroundingMode.sources_required,
            GroundingMode.canonical_required,
            GroundingMode.api_or_database_required,
            GroundingMode.human_review_required,
        }:
            return True
        return bool(self._required_source_types(request))

    def _requires_human_review(self, policy: GroundingPolicy) -> bool:
        return (
            policy.require_human_review
            or policy.grounding_mode == GroundingMode.human_review_required
            or policy.task_class in HIGH_STAKES_TASKS
        )

    @staticmethod
    def _append_reason(reason_codes: List[str], reason_code: str) -> None:
        if reason_code not in reason_codes:
            reason_codes.append(reason_code)
