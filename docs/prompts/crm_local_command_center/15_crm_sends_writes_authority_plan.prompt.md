# Phase 15: Exact-Approved Sends And Writes Plan Only

Branch: `codex/crm-15-sends-writes-plan`

Commit: `Add CRM sends and writes authority plan`

Goal: Do not implement broad sends. Create the exact authority plan and blocker
reports for future sends/writes.

Plan lanes:

- exact email send.
- exact SMS send.
- exact calendar write.
- exact external CRM write.
- exact contact sync.
- exact issue/task sync.

For each lane define:

- exact scope.
- approval binding.
- idempotency.
- receipt.
- rollback or compensation posture.
- redaction.
- safe-disable.
- CLI/API parity.
- focused tests.
- UI blocked label.
- copy-ready unblock prompt.

Rules:

- No send/write execution in this phase.
- Keep blocked lanes visible in Trust, CRM, docs, and release-surface truth.

Verification:

- documentation integrity
- product truth verifier
- operational maturity verifier
- `git diff --check`
