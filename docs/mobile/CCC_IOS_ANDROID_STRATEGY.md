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
