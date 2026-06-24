# FCC-MEM-016 Retrieval Diagnostics Read Model

Repository: this repository.

Goal: add plain-UAA retrieval diagnostics for governed Memory. This is the
QMD-style statistics lane, but the product language must call it retrieval
diagnostics. The output must explain what memory candidates were considered,
included, excluded, ranked, cached, and blocked without adding semantic search,
embeddings, vector DBs, context injection, memory writes, provider/model calls,
or production authority.

## Required First Audit

Before editing, inspect:

- `docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md`
- `docs/control_center/FCC_MEM_015_MEMORY_IMPACT_GRAPH_AND_FOLLOW_UP_QUEUE.md`
- `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md`
- `src/ultimate_ai_agent/core/memory/workbench.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `scripts/dev/uaa_founder_loop.py`
- `tests/test_fcc_mem_015_memory_impact_graph_followup_queue.py`

## Implementation Scope

Create a backend-owned safe-ref-only read model exposed through Python core,
API, and CLI. Prefer:

- `GET /control-center/memory/retrieval-diagnostics`
- CLI: `memory-retrieval-diagnostics`
- contract ref: `contract-ref:fcc-mem-016-retrieval-diagnostics:v1`

The read model must include candidate count, included refs, excluded refs,
excluded reason refs, rank signals, source mix, stale/conflict/duplicate/
missing-evidence pressure, token estimate, deterministic cache key ref, cache
hit/miss posture, and blocked reason refs.

## Safety Requirements

The lane must explicitly report:

- `safe_refs_only=true`
- `context_injection_authorized=false`
- `memory_write_authorized=false`
- `semantic_search_enabled=false`
- `vector_db_enabled=false`
- `embedding_search_enabled=false`
- `model_provider_authority_allowed=false`
- `production_authority_enabled=false`

No raw prompts, raw responses, raw provider payloads, raw paths, raw logs,
credentials, usernames, hostnames, or unredacted source content may be stored
in durable evidence, docs, tests, fixtures, or CLI output.

## Verification

Add focused tests and a verifier proving the route, CLI, contract fields,
OpenAPI/API manifest route inventory, docs, and blocked-state posture. Update
the frozen route inventory and route-status docs if a backend route is added.
