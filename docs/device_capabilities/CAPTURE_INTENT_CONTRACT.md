# Capture Intent Contract

Status: M20 contract-only capture planning.

Future capture intents must require an explicit user gesture. M20 allows only
manual-selected planned capture contracts. No silent capture is allowed. No
background capture is allowed. No passive capture is allowed. No continuous
capture is allowed.

M20 allows no raw payload. M20 allows no automatic memory write. Capture cannot
silently become memory. Capture cannot silently write files. Capture cannot
trigger external sends.

Future capture must be redacted, classified, consent-bound, retention-bound,
revocation-aware, and receipt-backed before any implementation. Future capture
receipts must use safe refs and must not include raw photos, audio, location,
contact, calendar, file, clipboard, biometric, or credential content.
