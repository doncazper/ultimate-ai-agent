# Mobile Companion Contract

Status: Current M19 contract/API planning doc through v0.23.1.

M19 implements Mobile Companion Contract/API Planning only. It adds Python
contract models and validation helpers under
`src/ultimate_ai_agent/core/mobile_companion/`; it adds no backend API route,
no frontend route, no mobile app, no Android app, no iOS app, no native build
workflow, no mobile sensor access, and no OS permission integration.

The Mobile Companion is a future control, approval/status, receipt, capture
inbox, emergency stop, and status dashboard surface. Phone/mobile is not the
agent brain. Python Agent Core remains the only authority for approvals,
consent, tools, events, secrets, redaction, receipts, Foundation Gate, and
governed source systems.

M19 contract rules:

- all mobile client plans are contract-only and `implemented_now=false`.
- all capability plans default to `allowed_now=false`.
- iOS and Android are future planned clients only.
- no Swift, Kotlin, Java, React Native, Expo, Flutter, Gradle, Android Studio,
  Xcode, signing, keystore, provisioning, App Store, or Play Store workflow is
  added.
- no camera, microphone, location, notifications, contacts, calendar, files,
  photos, Bluetooth, NFC, or biometrics access is enabled.
- sensor capability plans require a future Device Capability Broker before any
  implementation.
- mobile approval execution is not implemented.
- arbitrary strings, mobile output, phone output, sensor output, and capture
  output are not authority.
- phone output is not trusted control input.
- capture cannot silently become memory.
- safe summaries and metadata refs must not contain secrets, raw prompts, raw
  files, raw memory, raw location, raw camera, raw microphone, raw contacts,
  raw calendar, or raw photos.

M20 Device Capability Broker remains planned/provisional. M19 does not
implement M20. No native build workflow is added.

## v0.23.1 Hardening Note

v0.23.1 is a cleanup/hardening patch. Contacts and calendar are
planned/disabled capabilities and require a future Device Capability Broker.
Metadata refs must not contain secrets, API keys, tokens, passwords,
Authorization values, Cookie values, raw prompts, raw files, raw memory, raw
credentials, or raw mobile content. External sends are not allowed. OS
permissions are not integrated. Background services are not enabled. Android
support is planned, not implemented. iOS support is planned, not implemented.
No mobile app, native build workflow, mobile sensor access, OS permission
integration, signing, keystore, provisioning, App Store workflow, or Play Store
workflow exists.

## v0.24.0 M20 Device Capability Broker Contract

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation. M20 adds no sensor access, OS permission integration,
native clients, pairing runtime, mobile storage runtime, backend API route,
dependency, background service, notification runtime, runtime execution,
model/provider call, remote execution, plugin enablement, OpenWebUI
integration, or production authority. Device Capability Broker output is not
trusted control input by default. Capture cannot silently become memory. M21
remains planned/provisional.

## v0.46.0 M42 Product Contract Refresh

v0.46.0 implements M42 Mobile Companion Product Contract Refresh as
planning/docs/contracts/verifier work only. M42 refreshes product roles,
review-only/read-only surface boundaries, M43 read-only API boundary
readiness, and M44 future iOS skeleton sequencing. M42 adds no mobile app, no
iOS app, no Android app, no native package, no native build workflow, no
signing or store workflow, no TestFlight pipeline, no backend route, no mobile
API route, no approval capture, no approval execution, no mobile sensor access,
no OS permission integration, no background service, no notification runtime,
no device pairing runtime, no raw payload exposure, no memory write, no context
injection, no dependency, and no production authority.
