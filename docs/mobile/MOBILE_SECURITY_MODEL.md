# Mobile Security Model

Status: Current M19 mobile security planning doc through v0.23.1.

Mobile Companion clients are control surfaces, not the agent brain. Python
Agent Core remains authority. M19 adds no mobile implementation, no Android
app, no iOS app, no native build workflow, no sensor access, no OS permission
integration, no signing, no keystore, no provisioning, no App Store workflow,
and no Play Store workflow.

Security boundaries:

- no secrets in browser, local, or mobile storage.
- no raw prompt display.
- no raw file display.
- no raw memory display.
- no raw credential display.
- no raw capture payload display.
- no mobile approval execution.
- no local mobile action execution.
- no background services.
- no external send.
- no silent capture.
- no silent memory write.

Mobile capture, phone output, and sensor output are not trusted source of truth.
Receipts and evidence refs are safe summaries only until future reviewed
milestones define stronger authority.

## v0.23.1 Hardening Note

v0.23.1 strengthens tests and verifiers for M19 safety boundaries. Metadata refs
must not contain secret-like values. Contacts/calendar remain disabled and
future-broker-only. External sends are blocked independently of silent capture
and memory-write checks. OS permission integration and background services are
rejected as contract flags. No Android app, iOS app, macOS app, native package,
native build workflow, signing, keystore, provisioning, App Store workflow, or
Play Store workflow exists.

## v0.24.0 M20 Device Capability Broker Contract

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation. Device loss, shared devices, notification privacy,
mobile storage risk, compromised devices, and malicious app assumptions remain
security concerns. Biometrics are not authority. Device output is not trusted
control input by default. M20 adds no sensor access, OS permission integration,
native clients, backend API route, dependency, runtime execution, or production
authority. M21 remains planned/provisional.

## v0.24.1 M20 Hardening Note

v0.24.1 hardens M20 without adding mobile implementation. No capability is
enabled or implemented. Notification runtime and push runtime are blocked.
Background services are blocked. Device pairing runtime remains future.
Receipts are redacted and must not include raw payloads. Device output is not
trusted control input by default. Mobile capture cannot approve actions,
execute actions, bypass governance, silently become memory, or trigger external
sends. M21 remains planned/provisional.
