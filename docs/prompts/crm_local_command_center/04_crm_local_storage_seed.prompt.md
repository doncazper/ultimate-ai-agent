# Phase 04: Local CRM Storage Seed

Branch: `codex/crm-04-local-storage-seed`

Commit: `Add local CRM storage seed`

Goal: Add local durable CRM storage for safe refs and redacted summaries.

Implement:

- Local SQLite/JSONL storage aligned with existing Founder Loop storage style.
- Seed-safe sample records for local testing.
- Idempotent initialization.
- Storage status refs.
- No raw contact body/content persistence.

Storage objects:

- people
- organizations
- relationships
- opportunities
- follow-ups
- timeline events
- smart list memberships
- pipeline positions

CLI:

- `scripts/dev/uaa_crm.py inspect-storage`
- `scripts/dev/uaa_crm.py seed-demo`
- `scripts/dev/uaa_crm.py clear-demo` with explicit local-only guard

Tests:

- storage init/replay.
- no raw sensitive fields.
- CLI inspection.
- no connector/sync flags.

Verification:

- focused storage pytest
- documentation integrity
- product truth verifier
- `git diff --check`
