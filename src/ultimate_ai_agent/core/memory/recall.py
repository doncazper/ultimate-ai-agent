from typing import Iterable, List

from ultimate_ai_agent.core.memory.records import MemoryRecord


def build_recall_summaries(records: Iterable[MemoryRecord], limit: int = 5) -> List[str]:
    """Return safe recall summaries only; M24 does not alter prompts."""

    return [record.safe_summary or record.summary or "" for record in list(records)[:limit] if record.safe_summary or record.summary]
