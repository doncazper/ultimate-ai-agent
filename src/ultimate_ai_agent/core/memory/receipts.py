from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.time import utc_now


class MemoryRetentionReceipt(BaseModel):
    receipt_id: str = Field(..., min_length=1)
    memory_id: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    safe_message: str = "Memory action recorded as recall governance metadata."
    event_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    receipt_refs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    redaction_status: str = "redacted_summary_only"
    raw_content_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
