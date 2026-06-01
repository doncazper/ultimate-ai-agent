from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FileSnapshot(BaseModel):
    snapshot_id: str
    path: str
    content_hash: str
    content_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_ref: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
