# Redacted File Preview Redaction Policy

Status: active M33 documentation.
Current active baseline: **v0.38.1**

M33 redacts before result creation. Raw preview bytes may be read only inside the
bounded redaction pipeline and must not leave that boundary.

The redactor conservatively handles:

- secret-like assignments such as API keys, tokens, cookies, passwords, and
  client secrets.
- bearer tokens.
- private-key markers.
- high-entropy-looking tokens.

The redaction summary records counts and categories only. It must not include
the matched secret value, raw absolute path, raw file body, raw prompt, raw model
output, raw transcript, credentials, private keys, browser profile data, signing
assets, or local-only sensitive data.

If content is binary, unsupported encoding, oversized, or unsafe after decoding,
the preview is denied instead of returned.

v0.37.1 adds a second result-boundary guard: a redacted-preview result is denied
if its preview text still contains secret-like content. This preserves
redaction-before-return even if an internal caller tries to bypass the normal
redaction pipeline.

v0.38.0 implemented M34 Broader File Capability Review as
planning/docs/verifier work only. M35 remains planned/provisional for Safe File
Review Workflow Contracts.
