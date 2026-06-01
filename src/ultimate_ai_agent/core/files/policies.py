from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.files.enums import FileKind


class FileManagerPolicy(BaseModel):
    allow_overwrite_without_hash: bool = False
    strict_contract_paths: bool = False
    allowed_update_paths: List[str] = Field(default_factory=list)
    protected_kinds: List[FileKind] = Field(
        default_factory=lambda: [
            FileKind.canonical,
            FileKind.spec,
            FileKind.adr,
            FileKind.schema,
            FileKind.prompt,
            FileKind.eval,
        ]
    )
    policy_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
