# FCC-MEM-018 Memory Feedback / Quality Issue Queue

Repository: this repository.

Goal: capture operator memory feedback as governed quality signals and make
those signals visible as a quality issue queue. This closes the gap where
GoatCitadel is ahead: useful/stale/missing/wrong/duplicate/conflict/
irrelevant/privacy-concern feedback must become ranking input and review
pressure, never automatic memory writes.

## Required First Audit

Before editing, inspect:

- `docs/control_center/FCC_MEM_001_MEMORY_WORKBENCH.md`
- `docs/control_center/FCC_MEM_015_MEMORY_IMPACT_GRAPH_AND_FOLLOW_UP_QUEUE.md`
- `src/ultimate_ai_agent/core/memory/workbench.py`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `src/ultimate_ai_agent/api/founder_loop.py`
- `scripts/dev/uaa_founder_loop.py`
- `tests/test_fcc_mem_001_memory_workbench.py`

## Implementation Scope

Create a backend-owned feedback receipt contract and quality issue read model.
Prefer:

- `POST /control-center/memory/feedback`
- `GET /control-center/memory/quality-issues`
- CLI: `record-memory-feedback`
- CLI: `memory-quality-issues`
- contract ref: `contract-ref:fcc-mem-018-feedback-quality-queue:v1`

Feedback kinds must include:

- `useful`
- `stale`
- `missing`
- `wrong`
- `duplicate`
- `conflict`
- `irrelevant`
- `privacy_concern`

The feedback receipt must validate target refs against visible Memory, impact
graph, follow-up, context-pack, Today, Action, and Evidence refs where
available. The quality issue queue must group and rank feedback-derived issues
alongside stale, duplicate, conflict, missing-evidence, and privacy pressure.

## Safety Requirements

Feedback recording must be idempotent, receipt-backed, safe-ref-only, and
non-authoritative. It must explicitly report:

- `memory_write_performed=false`
- `automatic_memory_write_authorized=false`
- `delete_execution_authorized=false`
- `context_injection_authorized=false`
- `action_execution_authorized=false`
- `production_authority_enabled=false`

## Verification

Add focused tests and a verifier proving idempotent feedback receipts,
orphan-target rejection, quality issue projection, route manifest posture,
rate-limit/idempotency posture, CLI parity, and no automatic memory mutation.
