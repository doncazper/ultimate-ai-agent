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

## v0.24.1 M20 Hardening Note

v0.24.1 keeps capture contract-only. User gesture is future contract metadata
only and cannot imply current capture execution. Silent capture, passive
capture, background capture, continuous capture, automatic memory writes,
external sends, raw payloads, geolocation coordinates, audio/image/contact/
calendar/photo/biometric payload-like metadata, and private local paths are
blocked. M21 remains planned/provisional.
