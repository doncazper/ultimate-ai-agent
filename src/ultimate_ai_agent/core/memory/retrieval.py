import re
from typing import List, Tuple

from ultimate_ai_agent.core.memory.records import MemoryRecord


def tokenize(text: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9_]+", text.lower()) if token]


def score_memory(record: MemoryRecord, query: str, tags: List[str]) -> Tuple[float, List[str]]:
    query_tokens = tokenize(query)
    content_tokens = set(tokenize(f"{record.content} {record.summary or ''}"))
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

    return score, reasons
