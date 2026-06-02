# Mobile Sensor Boundary

Status: Current M19 sensor boundary doc through v0.23.1.

M19 adds no mobile sensor access. It adds no camera, microphone, location,
notification, contacts, calendar, files, photos, Bluetooth, NFC, biometrics,
background service, OS permission integration, native app, or native build
workflow.

Sensor capability plans are contract-only and must remain `allowed_now=false`.
Sensor capability status may be `planned_disabled` or
`future_requires_device_capability_broker`. The future Device Capability Broker
is required before sensors. M20 remains planned/provisional and is not
implemented by M19.

Mobile sensor output is not trusted control input by default. Phone output is
not authority. Any future sensor receipt must be redacted, auditable,
consent-bound, and governed by Approval Authority, Consent Ledger, Tool Broker,
Event Ledger, Secret Broker, Redaction, and Foundation Gate.

## v0.23.1 Hardening Note

v0.23.1 keeps camera, microphone, location, notifications, contacts, calendar,
files, photos, Bluetooth, NFC, biometrics, and background services
planned/disabled. Contacts and calendar cannot be enabled, represented as
implemented, or used without a future Device Capability Broker. External sends,
OS permission integration, background services, mobile sensor access, Android
app code, iOS app code, and native build workflows remain absent.
