# FCC-MEM-016 Through FCC-MEM-020 Memory Diagnostics, Citation Integrity, Feedback, Maintenance, And Context Manifest

Status: Implemented as backend-owned read models plus one idempotent feedback
receipt route. Product UI polish remains partial.

These lanes add teeth to governed Memory without changing its authority model.
Memory remains recall and proposal material, not truth, hidden prompt context,
automatic action authority, connector authority, or production authority.

## Implemented Surfaces

| Lane | Route | CLI | Contract |
|---|---|---|---|
| FCC-MEM-016 Retrieval Diagnostics | `GET /control-center/memory/retrieval-diagnostics` | `memory-retrieval-diagnostics` | `contract-ref:fcc-mem-016-retrieval-diagnostics:v1` |
| FCC-MEM-017 Citation Integrity | `GET /control-center/memory/citation-integrity` | `memory-citation-integrity` | `contract-ref:fcc-mem-017-citation-integrity:v1` |
| FCC-MEM-018 Feedback Quality Queue | `GET /control-center/memory/quality-issues` | `memory-quality-issues` | `contract-ref:fcc-mem-018-feedback-quality-queue:v1` |
| FCC-MEM-018 Feedback Receipt | `POST /control-center/memory/feedback` | `record-memory-feedback` | `contract-ref:fcc-mem-018-feedback-quality-queue:v1` |
| FCC-MEM-019 Maintenance Runs | `GET /control-center/memory/maintenance-runs` | `memory-maintenance-runs` | `contract-ref:fcc-mem-019-proposal-only-maintenance-runs:v1` |
| FCC-MEM-020 Context Manifest | `GET /control-center/memory/context-manifest` | `memory-context-manifest` | `contract-ref:fcc-mem-020-context-manifest:v1` |

All routes are local-only Control Center surfaces, reflected in OpenAPI,
`/api/manifest`, the frozen API route inventory, route-status docs, and CLI
inspection commands.

## FCC-MEM-016 Retrieval Diagnostics

Retrieval diagnostics replace vague QMD language with plain UAA product
language. The read model reports:

- candidate count
- included and excluded refs
- excluded reason refs
- rank signals
- source mix
- stale, duplicate, conflict, and missing-evidence pressure
- token estimate
- deterministic cache key ref
- cache hit/miss posture
- blocked reason refs

The cache key is deterministic evidence, not a runtime cache store. Current
status is `cache_hit=false` with `miss_no_runtime_cache_store`.

## FCC-MEM-017 Citation Integrity

Citation integrity validates visible context-pack proposal refs before they can
be treated as usable proposal material. It checks reviewed memory posture,
source/evidence/receipt refs when claimed, deleted state, superseded or merged
state, forget-request state, and orphan posture.

Failed validation blocks the proposal inside the read model and emits
Evidence Timeline proof event projections. The GET route does not append
durable events as a side effect.

## FCC-MEM-018 Feedback And Quality Issues

Operator feedback is captured as an idempotent receipt. Supported feedback
kinds are:

- `useful`
- `stale`
- `missing`
- `wrong`
- `duplicate`
- `conflict`
- `irrelevant`
- `privacy_concern`

Feedback targets must resolve to visible Memory, impact graph, context-pack,
follow-up, Today, Action, or Evidence refs. Orphan targets are rejected. The
quality issue queue ranks feedback-derived issues together with stale,
duplicate, conflict, missing-evidence, and privacy pressure.

Feedback is a ranking and review signal only. It does not rewrite memory.

## FCC-MEM-019 Proposal-Only Maintenance Runs

Maintenance runs are scan projections over quality issues and citation
integrity results. They may propose:

- merge
- supersede
- forget request
- stale review
- missing-evidence repair
- citation repair

The lane is proposal-only. No proposal is applied by the scan.

## FCC-MEM-020 Context Manifest

Context Manifest V1 makes context-pack use inspectable before any future use.
Each manifest item explains:

- what would be included
- what would be excluded
- why included/excluded refs
- citation integrity status/result refs
- risk posture ref
- token budget and token estimate
- cache key ref
- expiration
- quality issue refs
- safe-disable refs
- authority flags

The manifest is not prompt context. It is an approvable proposal artifact only.

## Safety Boundary

The implemented lanes preserve these explicit blocked states:

- no hidden prompt injection
- no automatic context use
- no automatic memory write
- no auto-merge
- no auto-supersede
- no auto-forget
- no delete/export execution
- no semantic search
- no vector DB
- no embeddings
- no provider/model calls
- no connector writes
- no action execution
- no CRM/account sync
- no production authority

The feedback route is the only mutating route in this lane. It records a local
feedback receipt with idempotency posture and returns safe refs only. It does
not mutate reviewed recall records.

## Verification

Focused coverage:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_mem_016_020_memory_diagnostics.py
PYTHONPATH=src .venv/bin/python scripts/verify_fcc_mem_016_020_memory_diagnostics.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python scripts/verify_uaa_p1_080_api_route_classification.py
```

These checks prove the contracts, routes, CLI parity, route inventory posture,
idempotent feedback receipt behavior, safe-ref-only output, and blocked
authority flags.
