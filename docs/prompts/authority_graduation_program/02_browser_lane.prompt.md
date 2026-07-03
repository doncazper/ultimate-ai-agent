# Authority Lane 02: Browser

Goal: Prepare browser authority without jumping to clicks or forms.

Allowed next promotion: Level 1 observe-only, only after Web Evidence is stable.

Scope:

- Observe page metadata/screenshot/text summary through an approved gateway.
- Redacted observation refs only.
- No authenticated state.
- No Control Center action controls unless backend-owned.

Still blocked:

- Clicks, typing, forms, downloads, uploads.
- Cookies, account sessions, authenticated browsing.
- Browser action dry-run unless separately scoped.
- Browser execution of external workflows.

Promotion condition:

One safe observe-only run against a local/test page creates redacted observation
refs and denied-action receipts.

Tests/verifiers:

- browser gateway ladder tests.
- no-click/no-form/no-cookie tests.
- visual/status tests if UI changes.
- product-language checks.

If blocked:

Generate an unblock prompt for the exact missing observe-only contract, not for
browser action execution.
