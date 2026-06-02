# Device Receipt And Redaction Policy

Status: M20 contract-only receipt and redaction policy.

Every future device capability requires a receipt. Sensitive device data
requires redaction. Device receipts must use safe refs and safe summaries.

Receipts must not log raw payloads, secrets, credentials, prompts, raw memory,
raw file contents, raw photos, audio, location coordinates, contact records,
calendar entries, clipboard contents, biometric data, or provider payloads.

Capture receipts must show purpose, capability kind, data classification,
redaction status, retention summary, consent refs, evidence refs when safe,
revocation refs when safe, and the validation decision.

M20 adds no receipt runtime and no raw payload storage. Capture cannot silently
become memory and cannot trigger external sends.

## v0.24.1 M20 Hardening Note

v0.24.1 requires device receipt plans to remain redacted receipt contracts.
Receipt plans must not mark receipt requirements as not applicable. Receipt
plans must not allow raw storage. Safe summaries and metadata refs must reject
secret-like values, raw device payload-like fields, geolocation coordinates,
and private local paths. v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell
Integration Contract as contract/planning/validation only. M22 and M23 remain
planned/provisional.
