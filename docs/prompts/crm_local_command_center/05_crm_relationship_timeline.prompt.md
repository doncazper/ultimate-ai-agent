# Phase 05: Relationship Timeline And Evidence Binding

Branch: `codex/crm-05-relationship-timeline`

Commit: `Bind CRM relationship timeline to evidence and memory`

Goal: Make CRM useful by binding relationship history to UAA Evidence and
Memory.

Implement:

- Relationship timeline read model.
- Event kinds: `note_ref`, `follow_up_ref`, `memory_ref`, `evidence_ref`,
  `opportunity_ref`, `proposal_ref`, `decision_ref`.
- "Why shown" explanation.
- stale/conflict posture.
- proof links.

Rules:

- Timeline events store safe summaries and refs only.
- Memory remains recall, not truth.
- No raw communication bodies.
- No connector or account sync.

Tests:

- timeline shape.
- evidence refs present.
- memory provenance present.
- no raw content.
- UI timeline renders and filters.

Verification:

- focused backend/frontend tests
- documentation integrity
- `git diff --check`
