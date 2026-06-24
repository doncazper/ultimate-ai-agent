# FCC-MEM-021 Memory Read Models UI + Proposal Bridge

Repository: this repository.

Goal: wire MEM-016 through MEM-020 into the Founder Command Center UI and
Action Inbox proposal lane while preserving the hard boundary that context
manifests are inspectable proposal artifacts only.

## Required First Audit

Before editing, inspect:

- `docs/control_center/FCC_MEM_016_020_MEMORY_DIAGNOSTICS_CITATIONS_FEEDBACK_MAINTENANCE_CONTEXT.md`
- `docs/control_center/FCC_HEALTH_001_SELF_HEALING_RECOMMENDATIONS_TO_INBOX.md`
- `src/ultimate_ai_agent/core/storage/founder_loop.py`
- `src/ultimate_ai_agent/core/control_center/health_recommendations.py`
- `apps/control-center/src/api/endpoints.ts`
- `apps/control-center/src/api/client.ts`
- `apps/control-center/src/api/types.ts`
- `apps/control-center/src/components/FounderLoopPanels.tsx`
- `apps/control-center/src/App.test.tsx`

## Implementation Scope

Add Control Center API client/types and Memory UI sections for:

- MEM-016 retrieval diagnostics
- MEM-017 citation integrity
- MEM-018 quality issues and feedback receipts
- MEM-019 proposal-only maintenance runs
- MEM-020 context manifest preview

Extend `loadControlCenterData` so these read models use safe fallback states
when endpoints fail.

Add bounded feedback controls that post to
`POST /control-center/memory/feedback` with idempotency keys. Feedback must
create quality issue signals only.

Bridge memory quality and maintenance signals into Action Inbox by reusing the
existing `self_heal_recommendation` envelope with memory-specific
recommendation refs. The Action Inbox item must remain proposal-only and expose
blocked authority refs.

## Safety Requirements

Do not add:

- no hidden context use
- context injection
- context manifest apply/use controls
- automatic retrieval execution
- memory writes from feedback
- auto-merge
- auto-supersede
- auto-forget
- maintenance execution
- shell/subprocess execution
- connector writes
- provider/model calls
- vector database or embeddings
- production authority

Action Inbox `approve`, `reject`, and `defer` decisions for memory proposals
may record operator receipts only. They must not perform maintenance or mutate
memory.

## Verification

Add or extend focused tests and a verifier proving:

- MEM-016 through MEM-020 endpoints are loaded through the API client.
- Memory UI renders each read model without raw JSON as the primary UI.
- Failed endpoints show non-authoritative fallback states.
- Feedback controls call the feedback route with idempotency keys.
- Action Inbox renders memory recommendations as proposal-only.
- Memory proposal decisions create receipts without memory mutation.
- Context manifest read models remain blocked from actual context use.
- No hidden auto-maintenance, provider call, connector write, shell execution,
  or context injection authority is introduced.
