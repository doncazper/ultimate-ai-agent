from pydantic import BaseModel, ConfigDict, Field


class GroundedRecallManifest(BaseModel):
    baseline_version: str = Field(..., min_length=1)
    milestone: str = "M26"
    recall_router_enabled: bool = True
    context_pack_builder_enabled: bool = True
    context_injection_enabled: bool = False
    vector_search_enabled: bool = False
    embeddings_enabled: bool = False
    semantic_search_enabled: bool = False
    rag_ingestion_enabled: bool = False
    external_retrieval_enabled: bool = False
    web_search_enabled: bool = False
    source_crawling_enabled: bool = False
    automatic_memory_write_enabled: bool = False
    backend_routes_added: bool = False
    model_provider_calls_enabled: bool = False
    tool_execution_enabled: bool = False
    production_authority_enabled: bool = False
    safe_summary_only: bool = True

    model_config = ConfigDict(extra="forbid")


def build_grounded_recall_manifest(baseline_version: str = "0.30.0") -> GroundedRecallManifest:
    return GroundedRecallManifest(baseline_version=baseline_version)
