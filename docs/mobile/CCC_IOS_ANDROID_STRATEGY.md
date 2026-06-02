# CCC iOS and Android Strategy

Status: Current M19 CCC native mobile strategy doc through v0.23.1.

CCC means Control Center Clients. CCC iOS and CCC Android are future native
mobile control clients for approval/status/receipt/capture surfaces. They are
not the agent brain and must use Python Agent Core authority.

Android planning notes:

- no Android app is implemented yet.
- no Kotlin, Java, React Native, Expo, Flutter, Gradle, Android Studio, or
  native package is added.
- Android permissions must be explicit and scoped.
- no background location by default.
- no passive microphone.
- no silent photo/contact/calendar scans.
- no background service without reviewed policy.
- no notification runtime without receipt-backed policy.
- no Play Store/signing/keystore workflow until a dedicated release milestone.

iOS planning notes:

- no iOS app is implemented yet.
- no Swift, React Native, Expo, Flutter, or native package is added.
- iOS permissions must be explicit and scoped.
- no camera, microphone, location, notifications, contacts, calendar, or photos
  access is enabled.
- no App Store/signing/provisioning/keychain workflow until a dedicated release
  milestone.

This patch adds no CCC native implementation, no Android app, no iOS app, no
native build workflow, no mobile sensor access, no OS permission integration,
and no signing, keystore, provisioning, App Store, or Play Store workflow.

## v0.23.1 Hardening Note

v0.23.1 is a cleanup/hardening patch only. Android support is planned, not
implemented. iOS support is planned, not implemented. Contacts and calendar are
planned/disabled and require a future Device Capability Broker. Metadata refs
must not contain secrets. External sends, OS permission integration, background
services, notification runtime, native build workflows, signing, keystore,
provisioning, App Store workflow, and Play Store workflow remain absent.

## v0.24.0 M20 Device Capability Broker Contract

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation. CCC iOS and CCC Android remain future clients only.
M20 adds no Android app, iOS app, native package, sensor access, OS permission
integration, background service, notification runtime, pairing runtime,
backend API route, dependency, native build workflow, signing, keystore,
provisioning, App Store workflow, Play Store workflow, or production authority.
v0.25.0 implements M21 OpenWebUI Bridge + Chat Shell Integration Contract as
contract/planning/validation only. v0.26.0 implements M22 contract-only, and
M23 remains planned/provisional.
