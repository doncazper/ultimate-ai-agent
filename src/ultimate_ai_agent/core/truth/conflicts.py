import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.truth.enums import SourceConflictSeverity, SourceFreshnessStatus, TruthSourceType


class SourceConflictReport(BaseModel):
    conflict_id: str
    claim_id: Optional[str] = None
    source_ids: List[str] = Field(default_factory=list)
    severity: SourceConflictSeverity
    description: str
    resolution_policy: str
    preferred_source_id: Optional[str] = None
    reason_codes: List[str] = Field(default_factory=list)
    requires_human_review: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(extra="forbid")


def resolve_source_conflict(claim_id: str, sources: list, description: str, hard_live_fact: bool = False) -> SourceConflictReport:
    source_ids = [source.source_id for source in sources]
    canonical = [source for source in sources if source.source_type == TruthSourceType.canonical_file]
    memory = [source for source in sources if source.source_type == TruthSourceType.memory]
    structured = [source for source in sources if source.source_type in [TruthSourceType.api, TruthSourceType.database, TruthSourceType.provider_result]]
    documents = [
        source
        for source in sources
        if source.source_type in [TruthSourceType.approved_document, TruthSourceType.file, TruthSourceType.canonical_file]
    ]

    if canonical and memory:
        preferred = sorted(canonical, key=lambda item: item.canonical_priority or 999)[0]
        return SourceConflictReport(
            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
            claim_id=claim_id,
            source_ids=source_ids,
            severity=SourceConflictSeverity.medium,
            description=description,
            resolution_policy="canonical_wins",
            preferred_source_id=preferred.source_id,
            reason_codes=["CANONICAL_OVERRIDES_MEMORY"],
        )

    if hard_live_fact and structured and documents:
        stale_structured = [
            source
            for source in structured
            if source.metadata.get("freshness_status") in [SourceFreshnessStatus.stale, "stale", SourceFreshnessStatus.expired, "expired"]
        ]
        if stale_structured:
            return SourceConflictReport(
                conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                claim_id=claim_id,
                source_ids=source_ids,
                severity=SourceConflictSeverity.high,
                description=description,
                resolution_policy="human_review_for_stale_structured_conflict",
                reason_codes=["STALE_STRUCTURED_SOURCE_CONFLICT"],
                requires_human_review=True,
            )
        preferred = sorted(structured, key=lambda item: (-item.authority_rank, item.source_id))[0]
        return SourceConflictReport(
            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
            claim_id=claim_id,
            source_ids=source_ids,
            severity=SourceConflictSeverity.medium,
            description=description,
            resolution_policy="structured_source_wins_for_live_fact",
            preferred_source_id=preferred.source_id,
            reason_codes=["STRUCTURED_SOURCE_OVERRIDES_DOCUMENT"],
        )

    return SourceConflictReport(
        conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
        claim_id=claim_id,
        source_ids=source_ids,
        severity=SourceConflictSeverity.medium,
        description=description,
        resolution_policy="human_review_required",
        reason_codes=["CONFLICT_UNRESOLVED"],
        requires_human_review=True,
    )
