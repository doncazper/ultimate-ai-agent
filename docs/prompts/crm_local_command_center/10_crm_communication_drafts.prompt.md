# Phase 10: Communication Draft Center

Branch: `codex/crm-10-communication-drafts`

Commit: `Add CRM communication draft center`

Goal: Add draft-only CRM communications.

Draft kinds:

- email draft
- text draft
- call script
- meeting agenda
- follow-up note
- calendar invite draft

Rules:

- Drafts are local review artifacts only.
- No sends.
- No account auth.
- No calendar writes.
- No connector writes.
- Draft content must be bounded, redacted, or stored as a local-only safe
  artifact according to UAA policy.

UI:

- Draft center in CRM.
- Relationship-linked drafts.
- Proof refs.
- "Send blocked" labels.

Tests:

- draft-only contracts.
- blocked sends.
- UI language.
- no raw private data persistence.

Verification:

- focused tests
- frontend check if UI changed
- documentation integrity
- `git diff --check`
