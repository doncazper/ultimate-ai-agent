# Phase 14: Optional Exact Connector Read Lanes

Branch: `codex/crm-14-connector-read-lanes`

Commit: `Add CRM connector read posture`

Goal: Add only exact-approved read/metadata connector lanes if existing UAA
connector authority supports it.

Possible lanes:

- local file import.
- email metadata read.
- calendar metadata read.
- contacts metadata read.

Rules:

- No body ingestion unless separately approved.
- No sends/writes.
- No OAuth collection unless exact secret/vault authority exists.
- Use safe refs and redacted summaries.
- If authority is missing, keep blocked and generate unblock prompt.

Tests:

- connector disabled by default.
- safe-disable.
- no writes.
- no raw body persistence.

Verification:

- focused tests
- route/OpenAPI verifier if routes changed
- product truth verifier
- `git diff --check`
