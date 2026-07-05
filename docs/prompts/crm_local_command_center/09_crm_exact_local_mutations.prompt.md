# Phase 09: Exact Local CRM Mutation Lane

Branch: `codex/crm-09-exact-local-mutations`

Commit: `Add exact local CRM mutation lane`

Goal: Add the first real CRM mutation: exact local-only updates with receipt and
rollback posture.

Scope:

- Create/update local CRM follow-up.
- Mark follow-up complete.
- Move opportunity stage locally.
- Add local note summary ref.

Authority:

- Requires exact approval/idempotency.
- No connector writes.
- No sends.
- No account sync.
- No raw body storage.

Receipts:

- mutation_ref
- approval_ref
- idempotency_ref
- before_ref
- after_ref
- rollback_ref
- proof_ref

Tests:

- approval required.
- idempotency replay/conflict.
- receipt proof refs.
- rollback posture.
- no raw private data.
- route classification and OpenAPI manifest updated.

Verification:

- focused backend/API tests
- OpenAPI verifier
- route/release surface verifier
- documentation integrity
- `git diff --check`
