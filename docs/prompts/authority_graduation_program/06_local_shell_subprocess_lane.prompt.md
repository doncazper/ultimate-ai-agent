# Authority Lane 06: Local Shell / Subprocess

Goal: Permit narrow, useful local commands without opening arbitrary shell.

Allowed next promotion: Level 2 manual foreground allowlisted command.

Scope:

- One allowlisted command family.
- Exact approval.
- Bounded cwd/env.
- Timeout.
- Redacted stdout/stderr summary refs.
- Receipt, audit, and safe-disable refs.

Still blocked:

- Arbitrary shell.
- Privileged commands.
- Network shell behavior unless separately scoped.
- Background processes.
- Package installs without review.

Promotion condition:

One allowlisted command executes foreground with exact approval, receipt,
bounded output, and denial paths for unapproved/unsafe commands.

Tests/verifiers:

- command proposal tests.
- allowlist tests.
- output redaction tests.
- no unrestricted subprocess tests.
- CLI parity tests.

If blocked:

Generate an unblock prompt for the missing command classifier, approval scope,
redaction, timeout, or safe-disable rule.
