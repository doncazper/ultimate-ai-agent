# Authority Lane 09: Action Execution

Goal: Turn reviewed actions into real outcomes one exact action kind at a time.

Allowed next promotion: one new exact Action kind after current local task lane
evidence is reviewed.

Scope:

- Backend-owned Action envelope.
- Exact approval.
- Idempotency.
- Receipt/evidence/proof refs.
- Rollback/safe-disable posture.
- No UI-only eligibility.

Still blocked:

- Broad approve-all.
- Generic external effects.
- Connector writes unless Connector Write lane grants them.
- Shell execution unless Shell lane grants it.
- Autonomous execution.

Promotion condition:

One exact Action kind can be approved, executed, replayed safely, denied when
out of scope, and explained through Proof/Evidence.

Tests/verifiers:

- Action Inbox state machine tests.
- approval scope tests.
- local task/action receipt tests.
- Evidence Timeline tests.
- frontend no-unsafe-control tests.

If blocked:

Generate an unblock prompt for the missing Action contract, approval scope,
receipt, evidence, idempotency, or rollback posture.
