# Authority Lane 12: Credential / OAuth / Account

Goal: Let UAA use test credentials and OAuth grants safely before any production
account authority.

Allowed next promotion: test-account credential/OAuth enrollment with least
scope and revocation.

Scope:

- Test account only.
- Least-privilege scopes.
- Secret values never displayed or exported.
- Redacted vault refs.
- Revocation and rotation.
- No broad account sync unless Connector Read lane grants it.

Still blocked:

- Production accounts.
- Broad scopes.
- Secret export.
- Connector writes.
- Account sync beyond the scoped read lane.

Promotion condition:

One test-account enrollment and revocation cycle works with redacted refs and no
secret leakage.

Tests/verifiers:

- credential vault tests.
- OAuth scope tests.
- revocation/rotation tests.
- no secret leakage tests.
- connector read/write boundary tests.

If blocked:

Generate an unblock prompt for the missing vault, OAuth scope, test-account,
revocation, or redaction component.
