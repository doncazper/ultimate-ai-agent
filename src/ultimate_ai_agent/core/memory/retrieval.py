from datetime import timezone
import re
from typing import List, Tuple

from ultimate_ai_agent.core.memory.enums import MemoryConflictState, MemoryReviewState
from ultimate_ai_agent.core.memory.records import MemoryRecord
from ultimate_ai_agent.core.time import utc_now


def tokenize(text: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9_]+", text.lower()) if token]


def score_memory(record: MemoryRecord, query: str, tags: List[str]) -> Tuple[float, List[str]]:
    query_tokens = tokenize(query)
    source_ref_text = " ".join(
        str(value)
        for source_ref in record.source_refs
        for value in [
            source_ref.source_ref,
            source_ref.source_id,
            source_ref.evidence_ref,
            source_ref.event_ref,
            *source_ref.evidence_refs,
            *source_ref.event_refs,
            *source_ref.receipt_refs,
            *source_ref.metadata_refs,
        ]
        if value
    )
    content_tokens = set(
        tokenize(
            " ".join(
                [
                    record.safe_summary or "",
                    record.summary or "",
                    " ".join(record.tags),
                    source_ref_text,
                    " ".join(record.evidence_refs),
                    " ".join(record.receipt_refs),
                    " ".join(record.metadata_refs),
                ]
            )
        )
    )
    tag_set = {tag.lower() for tag in record.tags}
    score = 0.0
    reasons: List[str] = []

    for token in query_tokens:
        if token in content_tokens:
            score += 2.0
            reasons.append(f"keyword:{token}")
        if token in tag_set:
            score += 1.5
            reasons.append(f"tag:{token}")

    for tag in tags:
        if tag.lower() in tag_set:
            score += 2.5
            reasons.append(f"requested_tag:{tag.lower()}")

    if record.source_refs:
        score += 0.1
        reasons.append("source_linked")
    if record.evidence_refs:
        score += 0.2
        reasons.append("evidence_linked")
    if record.receipt_refs:
        score += 0.2
        reasons.append("receipt_linked")
    if record.review_state == MemoryReviewState.user_reviewed:
        score += 0.5
        reasons.append("user_reviewed")
    score += max(0.0, min(float(record.confidence_score), 1.0)) * 0.5
    score += max(0.0, min(float(record.trust_score), 1.0)) * 0.5
    reasons.append("confidence_trust_weighted")
    if record.created_at:
        age_seconds = (
            utc_now() - record.created_at.astimezone(timezone.utc)
        ).total_seconds()
        if age_seconds < 60 * 60 * 24 * 7:
            score += 0.4
            reasons.append("recent")
        elif age_seconds < 60 * 60 * 24 * 30:
            score += 0.2
            reasons.append("month_recent")
    if record.stale_state != MemoryConflictState.none:
        score -= 0.5
        reasons.append("stale_penalty")
    if record.conflict_state != MemoryConflictState.none:
        score -= 0.5
        reasons.append("conflict_penalty")

    return max(0.0, score), reasons
