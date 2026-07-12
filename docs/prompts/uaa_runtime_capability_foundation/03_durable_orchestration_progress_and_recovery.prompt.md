# Phase 03: Memory, Learning, And Governed Context

Goal: mature provenance-bound recall and learning without automatic memory
truth or hidden context injection.

## Required Work

1. Inspect existing memory intake, review, provenance, ranked retrieval,
   corrections, memory-to-loop binding, evidence, CLI/API/UI, and deletion
   postures.
2. Implement typed source and memory refs, context manifests, included and
   excluded source refs with reasons, token/content budgets, confidence,
   freshness, conflict, and sensitivity posture.
3. Implement idempotent accept, reject, correct, supersede, forget, expire, and
   feedback decisions with content-free receipts.
4. Ensure corrections and supersession order deterministically, deleted or
   excluded sources cannot reappear, and stale/conflicting recall fails closed.
5. Add a deterministic retrieval-quality benchmark with safe synthetic refs;
   do not persist raw source content.
6. Produce reviewable memory candidates. Materialization into model context is
   preview-only unless a separate exact accepted context-injection lane exists.
7. Expose the same readable backend truth through existing CLI/API/macOS UI.

## Required Proofs

- corrections win deterministically;
- reject, supersede, forget, and expiry are idempotent;
- excluded, deleted, stale, or conflicting sources do not leak;
- provenance and included/excluded reasons reproduce retrieval selection;
- memory and retrieved content cannot grant tools, actions, approvals, or
  leases; and
- context manifests and receipts contain no raw source content.

## Authority Boundary

Memory is recall, not truth or authority. Automatic memory writes, automatic
truth promotion, hidden context injection, connector writes, sends, runtime
model authority, and action execution from memory remain denied.

## Exit

Governed memory review and retrieval are deterministic, provenance-bound,
correctable, budgeted, redacted, and operator-visible.
