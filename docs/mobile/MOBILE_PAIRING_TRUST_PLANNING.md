# Mobile Pairing Trust Planning

Status: Current M19 pairing/trust planning doc for v0.23.0.

M19 does not implement pairing. It adds no QR pairing, device registry runtime,
push notification channel, background service, mobile app, native build
workflow, keychain, keystore, provisioning, App Store, Play Store, or OS
permission integration.

Future pairing must be explicit, scoped, auditable, revocable, receipt-backed,
and governed by Python Agent Core. A mobile device, phone output, mobile
capture, or sensor signal is not trusted control input by default.

Pairing trust must not bypass Approval Authority, Consent Ledger, Tool Broker,
Event Ledger, Secret Broker, Redaction, or Foundation Gate.
