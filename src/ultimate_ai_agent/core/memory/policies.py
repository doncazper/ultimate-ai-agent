from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.memory.enums import MemoryRetrievalMode, MemorySensitivity, MemoryStatus


class MemoryRetrievalPolicy(BaseModel):
    retrieval_mode: MemoryRetrievalMode = MemoryRetrievalMode.keyword
    max_results: int = Field(default=5, ge=0, le=50)
    include_sensitivity_levels: List[MemorySensitivity] = Field(
        default_factory=lambda: [
            MemorySensitivity.public,
            MemorySensitivity.user_private,
            MemorySensitivity.project_private,
            MemorySensitivity.system_internal,
        ]
    )
    exclude_statuses: List[MemoryStatus] = Field(
        default_factory=lambda: [
            MemoryStatus.deleted,
            MemoryStatus.revoked,
            MemoryStatus.quarantined,
            MemoryStatus.superseded,
            MemoryStatus.corrected,
        ]
    )
    prefer_recent: bool = True
    prefer_source_linked: bool = True
    require_consent_for_sensitive: bool = True
    allow_hybrid_contract_only: bool = True
    reranker_ref: Optional[str] = None
    embedding_model_ref: Optional[str] = None
    vector_index_ref: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")
