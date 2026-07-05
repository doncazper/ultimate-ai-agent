# Phase 06: Follow-Up Queue

Branch: `codex/crm-06-follow-up-queue`

Commit: `Add CRM follow-up queue`

Goal: Build the core CRM work loop: a smart follow-up queue.

Implement:

- Follow-up queue read model.
- Follow-up statuses: `due`, `upcoming`, `stale`, `blocked`, `proposed`,
  `completed`.
- Priority and reason refs.
- Relationship refs.
- Opportunity refs.
- Evidence/memory refs.
- Action Inbox handoff proposal.

UI:

- Today-style CRM follow-up queue.
- Smart filters.
- proof drawer.
- blocked external action labels.

Rules:

- No sends.
- No calendar writes.
- No connector writes.
- Handoff to Action Inbox remains proposal-only unless an exact local mutation
  lane exists.

Tests:

- follow-up queue backend.
- UI filters/actions.
- Action Inbox proposal remains proposal-only.

Verification:

- focused tests
- frontend check if UI changed
- `git diff --check`
