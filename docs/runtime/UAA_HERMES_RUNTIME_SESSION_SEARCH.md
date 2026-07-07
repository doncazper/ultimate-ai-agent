# UAA Hermes Runtime Session Search

Status: Hermes Runtime Adoption Phase 12 repo-safe read model

## Full-Strength Version

UAA can search prior sessions, runs, proof records, coding sessions, and
operator-loop activity without stuffing every transcript into durable memory.
Search results are reviewable refs that the operator can choose to attach to a
task or proof workflow.

## Repo-Safe Version

Phase 12 adds a backend-owned Python Agent Core read model for safe-ref
session/run search posture:

- `GET /api/runtime/session-search`
- `scripts/dev/uaa_runtime.py inspect-session-search`
- `RuntimeSessionSearchReadModel`
- AuthorityState mapping `lane-ref:runtime-session-search-read-model`
  under Read-only `workspace/read`
- safe result refs, session refs, run refs, proof refs, evidence refs, receipt
  refs, and attachable context refs
- bounded summaries and why-matched refs only
- explicit memory-separation posture
- AuthorityState route/CLI/mapping/catalog/decision/reason refs and
  unsupported adapter refs

This is inspection metadata. It performs no raw transcript persistence, no raw
prompt or response exposure, no semantic provider call, no embedding/vector
indexing, no hidden context injection, no memory write, and no action execution.

The API and CLI evaluate the read model against the active AuthorityLease
decision catalog. Unknown authority remains denied, but this read-only
workspace inspection is allowed by the default Read-only lease and includes the
decision refs operators can inspect through `GET /api/runtime/authority-state`
or `scripts/dev/uaa_runtime.py inspect-authority-state`.

## Blocked / Needs Authority

- raw transcript persistence
- raw prompt or response exposure
- provider/model semantic search
- embedding or vector index creation
- hidden context injection
- automatic context attachment
- memory writes derived from search
- action execution from search results
- background indexing
- production authority

## Exact Promotion Path

Future promotion requires redacted indexing contracts, result safe refs,
operator-selected attach flow, retrieval logs, proof binding, approval posture
for any context attachment, redaction tests, CLI/API/Core parity, route
classification updates, and product-language proof that search is not memory or
authority.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_session_search.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_12.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```
