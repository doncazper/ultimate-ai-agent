# Capability Manifest Schema

Status: M20 contract-only schema documentation.

The M20 manifest records planned device platforms, capability kinds, status,
purpose, risk level, data classification, permission scope, capture mode,
retention policy ref, redaction policy ref, revocation policy ref, receipt
requirement, safe summary, and metadata refs.

All `allowed_now` values are false in M20. All `implemented_now` values are
false in M20. Every future capability requires an explicit future milestone
before implementation.

Capability status values are contract-only, planned-disabled, blocked,
future-requires-broker, future-requires-pairing, future-requires-user-approval,
or not-implemented. Camera, microphone, location, notifications, contacts,
calendar, photos, files, clipboard, Bluetooth, NFC, biometrics, local network,
motion, health, and screen capture remain planned-disabled or
future-requires-broker.

The manifest must not contain secrets, raw payloads, raw prompts, raw files,
raw memory, location coordinates, audio buffers, image bytes, contact records,
calendar entries, photo data, biometric data, local file contents, home
directory paths, credentials, or OS permission runtime claims.
