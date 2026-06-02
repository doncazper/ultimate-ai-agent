# CCC iOS and Android Strategy

Status: Current M19 CCC native mobile strategy doc for v0.23.0.

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
