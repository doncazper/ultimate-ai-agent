from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RetrievalLogEntry(BaseModel):
    retrieval_id: str
    run_id: str
    query: str
    grounding_policy_ref: Optional[str] = None
    source_ids_considered: List[str] = Field(default_factory=list)
    source_ids_selected: List[str] = Field(default_factory=list)
    chunks_or_refs: List[str] = Field(default_factory=list)
    filters_applied: List[str] = Field(default_factory=list)
    reranker_ref: Optional[str] = None
    result_count: int = Field(default=0, ge=0)
    redactions_applied: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
