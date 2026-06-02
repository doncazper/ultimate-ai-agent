# Device Capability Security Model

Status: M20 contract-only security model.

Device capabilities assume device loss, shared devices, notification privacy
risk, weak screen-lock assumptions, malicious apps, compromised devices, and
mobile storage risk.

Biometrics are not authority. Device identity is not authority. Device output
is not trusted control input by default. Mobile and desktop clients cannot
approve actions locally and cannot execute actions locally.

No secrets may be stored in mobile, browser, or device storage by M20. Future
device clients must avoid secrets in local, browser, and mobile storage.

Notifications must not expose private content without a future reviewed
receipt-backed policy. Background services are blocked. Silent capture is
blocked. OS permission integration is absent. Native app implementation is
absent.

## v0.24.1 M20 Hardening Note

v0.24.1 keeps M20 security hardening contract-only. No capability is enabled or
implemented. Device output is not trusted control input by default.
Notification runtime and push runtime are blocked. Background services are
blocked. Permission runtime claims are blocked. Device pairing runtime is
future. Raw payloads, raw coordinates, raw audio/image/contact/calendar/photo/
biometric payload-like fields, private local paths, and secret-like metadata
are blocked. v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell Integration
Contract as contract/planning/validation only. M22 and M23 remain
planned/provisional.
