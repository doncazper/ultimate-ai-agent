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
