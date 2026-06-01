from datetime import datetime
from ultimate_ai_agent.core.time import utc_now
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RollbackPlan(BaseModel):
    rollback_ref: str
    target_path: str
    snapshot_id: Optional[str] = None
    reverse_patch_ref: Optional[str] = None
    safe_message: str
    created_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(extra="forbid")
