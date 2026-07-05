# Phase 12: Import/Export Local Files

Branch: `codex/crm-12-local-import-export`

Commit: `Add local CRM import export lane`

Goal: Add local import/export for the user's own data without cloud sync.

Import:

- CSV contacts.
- CSV organizations.
- CSV opportunities.
- vCard only if a safe parser exists or is implemented narrowly.

Export:

- redacted CRM snapshot.
- safe refs.
- user-owned CSV export.

Rules:

- Exact approval required.
- Preview before import.
- No raw path persistence.
- No silent merges.
- Identity match candidates are review-only.
- Dedupe proposals before commit.

Tests:

- import preview.
- exact commit.
- idempotency.
- no raw path/content leakage.
- export redaction.

Verification:

- focused import/export tests
- OpenAPI verifier if routes changed
- documentation integrity
- `git diff --check`
