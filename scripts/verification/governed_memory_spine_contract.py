from __future__ import annotations


SUCCESS_MESSAGE = "Governed Cognitive Memory Spine V1 verification passed."
SPINE_DOC = "docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_V1.md"
ROADMAP_DOC = "docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md"
HANDOFF_DOC = "docs/codex/GOVERNED_COGNITIVE_MEMORY_SPINE_HANDOFF.md"
FCC_DOC = "docs/control_center/FCC_V1_005_MEMORY_REVIEW_DECISIONS.md"
MEMORY_WRITE_POLICY_DOC = "docs/memory/MEMORY_WRITE_POLICY.md"
MEMORY_REVIEW_PROVENANCE_DOC = "docs/memory/MEMORY_REVIEW_AND_PROVENANCE.md"
MEMORY_RETENTION_DOC = "docs/memory/MEMORY_RETENTION_DELETE_EXPORT.md"
DOC_INDEX = "docs/DOCUMENTATION_INDEX.md"
RELEASE_SURFACE_PATH = "docs/control_center/release_surface_manifest.json"
ROUTE_STATUS_PATH = "docs/control_center/route_status_manifest.json"
MEMORY_RECEIPT_ROUTE = (
    "GET",
    "/control-center/memory/review/{candidate_ref}/receipt",
)
MEMORY_L1_INDEX_ROUTE = ("GET", "/control-center/memory/l1-index")
MEMORY_L2_INDEX_ROUTE = ("GET", "/control-center/memory/l2-index")
MEMORY_L3_INDEX_ROUTE = ("GET", "/control-center/memory/l3-index")
MEMORY_CONTEXT_PACK_ROUTE = ("GET", "/control-center/memory/context-packs")
MEMORY_CONTEXT_PACK_ACTION_ROUTE = (
    "POST",
    "/control-center/memory/context-packs/{context_pack_ref}/action-proposal",
)
MEMORY_DECISION_ROUTES = {
    ("POST", "/control-center/memory/review/{candidate_ref}/accept"),
    ("POST", "/control-center/memory/review/{candidate_ref}/correct"),
    ("POST", "/control-center/memory/review/{candidate_ref}/reject"),
}
FORBIDDEN_CLAIMS = [
    "memory is truth authority",
    "hidden context injection is enabled",
    "automatic memory writes are enabled",
    "connector writes are enabled",
    "crm sync is enabled",
    "provider calls are enabled",
    "production ready memory",
    "public beta memory",
    "phase 6 is implemented",
    "context injection is enabled",
    "context packs inject prompts",
    "context packs write prompt context",
    "context pack execution is enabled",
    "phase 6 is shipped",
    "phase 6 is available",
    "memory-derived execution is enabled",
    "memory execution hooks are available",
    "context packs execute actions",
    "l3 memory is truth authority",
    "l3 context injection is enabled",
    "l3 crm sync is enabled",
    "l3 account sync is enabled",
    "l3 action execution is enabled",
    "embeddings are enabled",
    "vector db is enabled",
    "semantic search is enabled",
    "background indexing is enabled",
    "automatic recall is enabled",
]
PHASE6_RUNTIME_GLOBS = (
    "src/ultimate_ai_agent/api/**/*.py",
    "src/ultimate_ai_agent/core/memory/**/*.py",
)
PHASE6_FORBIDDEN_RUNTIME_SNIPPETS = (
    "/control-center/memory/execute",
    "/control-center/memory/execution",
    "execute_memory_hook(",
    "execute_from_memory(",
    "execute_from_context_pack(",
    "computer_use(action=",
    "subprocess.run(",
    "subprocess.Popen(",
    "playwright.",
)
L1_DENIED_FLAGS = (
    "context_injection_authorized",
    "automatic_recall_authorized",
    "automatic_memory_write_authorized",
    "embedding_index_enabled",
    "vector_db_enabled",
    "semantic_search_enabled",
    "background_indexing_enabled",
    "source_truth_authority",
    "connector_write_authorized",
    "automatic_action_execution_authorized",
    "production_authority_enabled",
)
L2_DENIED_FLAGS = (
    "truth_authority_enabled",
    "context_injection_authorized",
    "automatic_recall_authorized",
    "automatic_memory_write_authorized",
    "embedding_index_enabled",
    "vector_db_enabled",
    "semantic_search_enabled",
    "llm_entity_extraction_enabled",
    "background_indexing_enabled",
    "context_pack_injection_authorized",
    "connector_write_authorized",
    "external_crm_sync_authorized",
    "account_sync_authorized",
    "automatic_action_execution_authorized",
    "production_authority_enabled",
)
L3_DENIED_FLAGS = (
    "truth_authority_enabled",
    "crm_truth_authority_enabled",
    "context_injection_authorized",
    "automatic_recall_authorized",
    "automatic_memory_write_authorized",
    "embedding_index_enabled",
    "vector_db_enabled",
    "semantic_search_enabled",
    "llm_extraction_enabled",
    "background_indexing_enabled",
    "context_pack_injection_authorized",
    "phase5_context_pack_proposals_enabled",
    "phase6_execution_hooks_enabled",
    "connector_write_authorized",
    "external_crm_sync_authorized",
    "account_sync_authorized",
    "automatic_action_execution_authorized",
    "production_authority_enabled",
)
CONTEXT_PACK_PROPOSAL_DENIED_FLAGS = (
    "context_injection_authorized",
    "hidden_prompt_context_authorized",
    "automatic_context_injection_authorized",
    "prompt_context_written",
    "truth_authority_enabled",
    "approval_authority_granted",
    "connector_write_authorized",
    "external_crm_sync_authorized",
    "account_sync_authorized",
    "automatic_action_execution_authorized",
    "model_provider_authority_allowed",
    "production_authority_enabled",
    "embedding_index_enabled",
    "vector_db_enabled",
    "semantic_search_enabled",
    "background_indexing_enabled",
    "phase6_execution_hooks_enabled",
    "raw_content_stored",
)
CONTEXT_PACK_INDEX_DENIED_FLAGS = CONTEXT_PACK_PROPOSAL_DENIED_FLAGS + (
    "context_injection_performed",
    "provider_model_call_performed",
)
CONTEXT_PACK_REQUIRED_FIELDS = (
    "source_memory_record_refs",
    "l1_preview_refs",
    "l2_projection_refs",
    "l3_representation_refs",
    "included_summary_refs",
    "inclusion_reason_refs",
    "source_refs",
    "evidence_refs",
    "receipt_refs",
    "approval_requirement_refs",
    "blocked_state_refs",
    "evidence_answer_refs",
)
