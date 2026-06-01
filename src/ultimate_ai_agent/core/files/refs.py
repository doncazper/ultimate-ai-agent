from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ultimate_ai_agent.core.files.enums import FileKind, FileSensitivity
from ultimate_ai_agent.core.files.validation import validate_safe_file_path


class FileRef(BaseModel):
    file_ref: str = Field(..., min_length=1)
    path: str
    kind: FileKind
    sensitivity: FileSensitivity
    content_hash: Optional[str] = None
    size_bytes: Optional[int] = Field(None, ge=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_event_ref: Optional[str] = None
    canonical_priority: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return validate_safe_file_path(value)
