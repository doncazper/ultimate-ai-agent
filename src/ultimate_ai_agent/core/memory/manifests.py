from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from ultimate_ai_agent.core.memory.enums import MemoryProviderKind, MemoryProviderStatus
from ultimate_ai_agent.core.time import utc_now


class MemoryProviderProfile(BaseModel):
    provider_ref: str = Field(..., min_length=1)
    provider_kind: MemoryProviderKind
    status: MemoryProviderStatus = MemoryProviderStatus.local_dev_only
    local_only: bool = True
    cloud_backed: bool = False
    supports_writes: bool = True
    supports_deletes: bool = True
    supports_export: bool = True
    supports_vector_search: bool = False
    supports_embeddings: bool = False
    supports_automatic_writes: bool = False
    supports_context_injection: bool = False
    supports_background_workers: bool = False
    production_ready: bool = False
    docs_refs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class MemoryProviderManifest(BaseModel):
    manifest_id: str = "memory_provider_manifest_m24"
    baseline_version: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=utc_now)
    providers: List[MemoryProviderProfile] = Field(default_factory=list)
    default_provider_ref: str = "local_dev_memory"
    local_store_enabled: bool = True
    cloud_providers_enabled: bool = False
    vector_search_enabled: bool = False
    embeddings_enabled: bool = False
    automatic_writes_enabled: bool = False
    recall_injection_enabled: bool = False
    context_pack_injection_enabled: bool = False
    auto_decay_enabled: bool = False
    background_workers_enabled: bool = False
    docs_refs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


def build_default_memory_provider_manifest(
    baseline_version: str,
    provider_kind: MemoryProviderKind = MemoryProviderKind.local_in_memory,
) -> MemoryProviderManifest:
    provider = MemoryProviderProfile(
        provider_ref="local_dev_memory",
        provider_kind=provider_kind,
        status=MemoryProviderStatus.local_dev_only,
        docs_refs=[
            "docs/memory/MEMORY_PROVIDER_ABSTRACTION.md",
            "docs/memory/LOCAL_MEMORY_STORE.md",
            "docs/memory/MEMORY_WRITE_POLICY.md",
        ],
        warnings=[
            "Memory is recall, not authority.",
            "M24 has no automatic writes, vector search, embeddings, cloud providers, or context injection.",
        ],
    )
    return MemoryProviderManifest(
        baseline_version=baseline_version,
        providers=[provider],
        docs_refs=[
            "docs/memory/MEMORY_PROVIDER_ABSTRACTION.md",
            "docs/memory/MEMORY_RECORD_SCHEMA.md",
            "docs/memory/MEMORY_SECURITY_MODEL.md",
        ],
        warnings=[
            "Local store is dev/local foundation only and is not a production persistence claim.",
            "Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.",
        ],
    )
