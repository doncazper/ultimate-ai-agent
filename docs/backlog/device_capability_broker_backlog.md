# Device Capability Broker Backlog

Status: Future planning only, v0.14.4

The Device Capability Broker is future governance for phone/device capabilities. It is planned before any mobile sensor integration and does not exist as runtime code in v0.14.4.

## Mobile Phase A - Planning/Contracts

- define capability categories and risk classes.
- document manifest and permission lifecycle.
- define evidence, receipt, redaction, retention, and revocation requirements.
- no runtime broker.

## Mobile Phase B - Control Center Readiness

- approval queue contracts.
- receipt viewer contracts.
- event viewer contracts.
- permission review and revocation contracts.
- notification policy contracts.

## Mobile Phase C - Web Control Center First

- browser UI for pending approvals.
- browser UI for receipts and event refs.
- browser UI for capability status.
- no mobile sensors yet.

## Mobile Phase D - Mobile Companion Shell

- device registry placeholder.
- app instance status placeholder.
- approval notification planning.
- emergency stop / kill switch planning.
- no camera, microphone, or GPS yet.

## Mobile Phase E - Mobile Capture Inbox

- typed note capability.
- selected share-sheet import.
- selected file/photo import.
- user review before memory or file write.

## Mobile Phase F - Camera/OCR

- camera capture manifest.
- document scan manifest.
- QR scan manifest.
- OCR evidence refs and user review.
- no automatic memory write.

## Mobile Phase G - Location

- one-time location manifest.
- navigation session manifest.
- approximate/precise policy.
- no background location by default.

## Mobile Phase H - Microphone/Voice

- push-to-talk manifest.
- short clip manifest.
- transcription review flow.
- no passive always-listening.

## Mobile Phase I - Advanced Device Capabilities

- NFC scan manifest.
- Bluetooth nearby summary manifest.
- motion/activity context manifest.
- contacts/calendar scoped lookup.
- biometrics/passkey local unlock.
- emergency stop / kill switch hardening.

## Explicit Non-Goals

- no runtime Device Capability Broker in v0.14.4.
- no sensor API integration.
- no OS permission integration.
- no hidden capture.
- no background surveillance.
- no mobile autonomous actions.
