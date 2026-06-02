# CCC Native Client Strategy

Status: Active CCC client strategy clarification for v0.19.0. Documentation only.

CCC means Control Center Clients. CCC is not only the current web Control Center; it is the custom governance/control client family for CCC Web, CCC iOS, CCC Android, and CCC macOS. All CCC clients are control surfaces, not the agent brain.

## CCC Web

CCC Web is the current TypeScript web Control Center under `apps/control-center`. It is a governance/control/status/preview surface over Python Agent Core APIs.

CCC Web remains read-only/preview-only until future reviewed milestones add authority through explicit backend contracts. It must not execute actions locally, bypass approvals, resolve credentials, enable plugins, dispatch remote workers, call models/providers, or access mobile sensors.

## CCC iOS

CCC iOS is a future native mobile control client. It may become an approval, status, receipt, and user-reviewed capture surface after dedicated contracts and milestones.

Current boundary:

- no iOS app is implemented yet.
- no Swift, React Native, Expo, Flutter, or native package is added yet.
- no camera, microphone, location, notification, contacts, calendar, or photos access is added yet.
- no App Store Connect, signing, provisioning, keychain, or entitlements work is added yet.

## CCC Android

CCC Android is a future native mobile control client. It may become an approval, status, receipt, and user-reviewed capture surface after dedicated contracts and milestones.

Current boundary:

- no Android app is implemented yet.
- no Kotlin, Java, React Native, Expo, Flutter, Gradle, Android Studio, or native package is added yet.
- no camera, microphone, location, notification, contacts, calendar, or photos access is added yet.
- no Play Store, signing, keystore, permissions, background service, or notification channel work is added yet.

Android-specific planning notes:

- Android permissions must be explicit and scoped.
- no background location by default.
- no passive microphone.
- no silent photo, contact, or calendar scans.
- no background service without reviewed policy.
- no notification runtime without receipt-backed policy.
- no Play Store, signing, or keystore workflow until a dedicated release milestone.

## CCC macOS

CCC macOS is a future desktop/local companion client. It may become a status, menu bar, local runtime, receipt, and approval surface after dedicated contracts and milestones.

Current boundary:

- no macOS app is implemented yet.
- no Swift, AppKit, SwiftUI, or native package is added yet.
- no signing, notarization, keychain, entitlements, or menu bar agent work is added yet.

macOS-specific planning notes:

- no keychain workflow until a dedicated release milestone.
- no menu bar workflow until a dedicated release milestone.
- no background agent workflow until a dedicated release milestone.
- no notarization workflow until a dedicated release milestone.

## Shared CCC Principles

All CCC clients must follow these principles:

- all CCC clients are control surfaces, not the agent brain.
- all CCC clients must use Python Agent Core authority.
- all CCC clients must respect Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, and Foundation Gate.
- all CCC clients must use stable API/OpenAPI contracts.
- all CCC clients must avoid secrets in local, browser, and mobile storage.
- all CCC clients must be auditable and receipt-backed.
- all CCC clients must not bypass approvals or execute actions locally.

## Future Native-Client Sequence

Native-client implementation must happen:

- after Web Control Center foundations.
- after OpenWebUI strategy docs.
- after Mobile Companion and Device Capability Broker contracts.
- before any sensor implementation.
- only through dedicated native iOS, Android, and macOS milestones.
- only after explicit plugin/tooling approval for native build systems.

## iOS-Specific Planning Notes

iOS permissions must be explicit and scoped. There is no background location by default, no passive microphone, no silent photo scan, no silent contacts scan, and no silent calendar scan. There is no App Store, signing, provisioning, or keychain workflow until a dedicated release milestone.

## Explicit Non-Implementation Statement

This patch adds no CCC native implementation.
No CCC native implementation is added.
This patch adds no Android app.
This patch adds no iOS app.
This patch adds no macOS app.
This patch adds no native build workflow.
No native build workflow is added.
This patch adds no mobile sensor access.
No mobile sensor access is added.
This patch adds no OS permission integration.
No OS permission integration is added.
This patch adds no signing, keystore, provisioning, App Store, or Play Store workflow.
No signing, keystore, provisioning, App Store, or Play Store workflow is added.
