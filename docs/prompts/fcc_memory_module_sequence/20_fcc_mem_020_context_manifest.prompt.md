# FCC-MEM-020 Context Manifest V1

Repository: this repository.

Goal: add actual context manifests as inspectable proposal artifacts. A context
manifest must show what would be used, why, what was excluded, citations, risk
posture, token budget, token estimate, cache key, expiration, authority flags,
and safe-disable refs. It must still block hidden prompt injection and any
automatic context use.

## Required First Audit

Before editing, inspect:

- `docs/memory/GOVERNED_COGNITIVE_MEMORY_SPINE_ROADMAP.md`
- `docs/control_center/FCC_MEM_015_MEMORY_IMPACT_GRAPH_AND_FOLLOW_UP_QUEUE.md`
- `src/ultimate_ai_agent/core/memory/context_packs.py`
- `src/ultimate_ai_agent/core/memory/workbench.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `src/ultimate_ai_agent/api/founder_loop.py`
- `tests/test_governed_memory_context_pack_proposals.py`

## Implementation Scope

Create a backend-owned proposal-only context manifest read model. Prefer:

- `GET /control-center/memory/context-manifest`
- CLI: `memory-context-manifest`
- contract ref: `contract-ref:fcc-mem-020-context-manifest:v1`

Each manifest item must include:

- context manifest ref
- context pack ref
- proposal ref
- included memory refs
- excluded memory refs
- why-included refs
- why-excluded refs
- citation integrity status/result ref
- risk posture ref
- token budget
- token estimate
- cache key ref
- expiration timestamp
- safe-disable refs
- quality issue refs
- blocked-state refs
- authority flags

## Safety Requirements

The read model must explicitly report:

- `proposal_only=true`
- `approval_required_before_use=true`
- `context_injection_authorized=false`
- `hidden_prompt_context_authorized=false`
- `automatic_context_injection_authorized=false`
- `memory_write_authorized=false`
- `action_execution_authorized=false`
- `connector_write_authorized=false`
- `model_provider_authority_allowed=false`
- `production_authority_enabled=false`

## Verification

Add focused tests and a verifier proving manifest items are citation-aware,
safe-ref-only, bounded by retrieval diagnostics, route/CLI/docs aligned, and
never used as hidden prompt context without a later accepted milestone.
