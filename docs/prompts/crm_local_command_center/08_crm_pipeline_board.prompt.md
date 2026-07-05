# Phase 08: Pipeline And Opportunity Board

Branch: `codex/crm-08-pipeline-board`

Commit: `Add CRM pipeline board`

Goal: Add a local pipeline board inspired by deal pipelines, but UAA-native and
generic across founder/operator workflows.

Objects:

- opportunity
- deal
- partnership
- investor
- customer
- candidate
- project
- renewal
- vendor

Implement:

- Pipeline read model.
- Stages.
- Opportunity cards.
- Local preview drag/drop.
- Proof/evidence refs.
- Blocked durable reorder until exact mutation lane.

Optional if safe:

- Exact local persisted reorder with idempotency, approval ref, receipt, and
  rollback posture.

Tests:

- pipeline rendering.
- no UI-only durable truth.
- mutation flags blocked unless exact lane implemented.

Verification:

- focused backend/frontend tests
- frontend check
- `git diff --check`
