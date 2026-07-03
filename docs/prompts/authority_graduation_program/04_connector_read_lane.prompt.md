# Authority Lane 04: Connector Read

Goal: Replace pretend connector readiness with a real read-only test-account
lane.

Allowed next promotion: Level 1 read-only metadata/test-account sync.

Scope:

- One connector.
- Test account only.
- Least-privilege read-only OAuth/scope proof if required.
- Metadata refs and redacted summaries only.
- No raw body/contact/file/account persistence.
- CLI inspection.

Still blocked:

- Sends/writes.
- Archive/delete/label/move.
- Calendar/CRM mutation.
- Production accounts.
- Background polling.

Promotion condition:

One test-account read-only sync produces metadata receipts and denied-scope
receipts without leaking raw account data.

Tests/verifiers:

- connector read contract tests.
- OAuth/scope tests.
- no raw account/contact/body tests.
- revocation tests.
- frontend product-language tests if visible.

If blocked:

Generate an unblock prompt for the smallest missing OAuth, test-account,
redaction, or read adapter contract.
