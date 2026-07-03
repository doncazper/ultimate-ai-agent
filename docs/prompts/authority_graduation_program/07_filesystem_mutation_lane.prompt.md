# Authority Lane 07: Filesystem Mutation

Goal: Make safe file writes real without allowing broad filesystem authority.

Allowed next promotion: Level 2 exact approved write for one safe path class.

Scope:

- Diff proposal first.
- Exact approval.
- Safe path policy.
- Atomic write.
- Rollback patch/receipt.
- Secret/path redaction.

Still blocked:

- Broad delete/export.
- Home-directory writes.
- Secret material writes.
- Unreviewed generated changes.
- Writes outside approved path class.

Promotion condition:

One safe path class can be proposed, approved, written, audited, and rolled
back.

Tests/verifiers:

- file review approval tests.
- path policy tests.
- secret redaction tests.
- atomic write/rollback tests.

If blocked:

Generate an unblock prompt for the missing safe path, diff proposal, approval,
atomic write, or rollback contract.
