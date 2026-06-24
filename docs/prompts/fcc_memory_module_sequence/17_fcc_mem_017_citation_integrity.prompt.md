# FCC-MEM-017 Citation Integrity

Repository: this repository.

Goal: validate every context-pack proposal citation/ref before it can be
treated as a usable proposal artifact. Failed citation validation must block
the proposal and emit inspectable Evidence Timeline proof. This is validation
and proof only; it must not inject context, write memory, delete memory, call a
provider/model, or grant truth authority.

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

Create a backend-owned read model exposed through Python core, API, and CLI.
Prefer:

- `GET /control-center/memory/citation-integrity`
- CLI: `memory-citation-integrity`
- contract ref: `contract-ref:fcc-mem-017-citation-integrity:v1`

Validate that every context-pack proposal citation/ref satisfies:

- source ref exists when claimed
- evidence ref exists when claimed
- receipt ref exists when claimed
- memory is reviewed
- memory is not deleted
- memory is not superseded unless intentionally included
- memory is not forget-requested
- memory is not orphaned from the visible proposal/read-model graph

If validation fails, the proposal status must become blocked in the read model
and the output must include Evidence Timeline proof event refs that explain the
blocked citation reason. A GET route may report proof events as a projection,
but it must not append durable evidence as a side effect.

## Safety Requirements

The lane must explicitly report:

- `safe_refs_only=true`
- `proposal_only=true`
- `context_injection_authorized=false`
- `memory_write_authorized=false`
- `truth_authority_enabled=false`
- `model_provider_authority_allowed=false`
- `production_authority_enabled=false`

## Verification

Add focused tests and a verifier proving valid proposals pass, invalid
citations block, proof refs are emitted, OpenAPI/API manifest route inventory
is updated, and docs avoid any claim that citation validation creates truth or
runtime authority.
