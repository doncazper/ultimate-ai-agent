# Authority Lane 05: Connector Write / Send

Goal: Move connector output from review theatre to a safe draft/send-to-self
ladder.

Allowed next promotion: send-to-self/test target only after the implemented
draft-only proposal refs are bound to a real test connector, exact approval,
target allowlist, idempotency, receipt storage, and safe-disable proof.

Scope:

- One send-to-self/test-target action bound to an existing connector draft
  proposal ref.
- Exact approval.
- Idempotency key.
- Target allowlist.
- Receipt/evidence/proof refs.
- No raw body/contact/token/cookie persistence.

Still blocked:

- Real external recipients.
- Batches.
- Destructive writes.
- Auto-send.
- Production connector writes.

Promotion condition:

Draft-only proposal refs exist first. A later send-to-self/test-target action
proves target allowlisting, exact approval, idempotency, revocation, failure
posture, and no raw payload leakage.

Tests/verifiers:

- connector delivery queue tests.
- no-send/no-write UI tests.
- send-to-self receipt tests when promoted.
- redaction tests.
- approval scope tests.

If blocked:

Generate an unblock prompt for the missing draft contract, target allowlist,
approval scope, idempotency, or redaction rule.
