# Mobile Companion Non-Goals

Status: Current M19 non-goals doc through v0.23.1.

M19 explicitly does not add:

- M20 Device Capability Broker implementation.
- mobile app implementation.
- Android app.
- iOS app.
- macOS app.
- Swift, Kotlin, Java, React Native, Expo, Flutter, Capacitor, Ionic, Gradle,
  Android Studio, Xcode, AppKit, SwiftUI, or native package work.
- native build workflow.
- signing, keystore, provisioning, App Store, or Play Store workflow.
- OS permission integration.
- camera, microphone, location, notifications, contacts, calendar, files,
  photos, Bluetooth, NFC, biometrics, or background service access.
- backend API routes.
- OpenAPI path count changes.
- runtime execution.
- model/provider calls.
- remote execution.
- plugin enablement.
- mobile approval execution.
- raw prompt, raw file, raw memory, raw credential, raw secret, or raw capture
  display.
- silent capture.
- silent memory write.

Phone/mobile is not the agent brain. Capture cannot silently become memory.
Device Capability Broker is required before sensors. M20 is implemented as
contract-only planning and validation.

## v0.23.1 Hardening Note

v0.23.1 does not remove any M19 non-goal. Contacts/calendar access, secret-like
metadata refs, external sends, OS permission integration, background services,
notification runtime, Android implementation, iOS implementation, macOS
implementation, native build workflows, signing, keystore, provisioning, App
Store workflow, Play Store workflow, Device Capability Broker implementation,
and production authority remain out of scope.

## v0.24.0 M20 Device Capability Broker Contract

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation. It remains a non-goal to add sensor access, OS
permission integration, native clients, pairing runtime, mobile storage
runtime, backend API routes, background services, notification runtime,
dependencies, runtime execution, model/provider calls, remote execution, plugin
enablement, OpenWebUI integration, or production authority. M21 remains
planned/provisional.
