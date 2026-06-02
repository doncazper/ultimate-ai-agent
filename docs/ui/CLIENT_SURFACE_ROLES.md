# Client Surface Roles

Status: Active UI strategy clarification for v0.19.1. Documentation only.

## Python Agent Core

Python Agent Core is the brain and authority layer. It owns governance decisions, policy checks, approvals, consent, tool authorization, event logging, secrets, redaction, and Foundation Gate evidence.

## OpenWebUI

OpenWebUI is the preferred conversational web shell for local LLM chat. OpenWebUI is not the agent brain and must not bypass Python Agent Core. A future OpenWebUI adapter may be reviewed later, but no OpenWebUI integration is implemented yet.

## CCC Web

CCC Web is the current TypeScript web Control Center under `apps/control-center`. It is a governance, control, status, and preview surface. It is read-only/preview-only until future reviewed milestones add authority through Python Agent Core contracts.

## CCC iOS

CCC iOS is a future native mobile control client for approvals, status, receipts, and user-reviewed capture. No iOS app is implemented yet. No Swift, React Native, Expo, Flutter, native package, camera, microphone, location, notification, contacts, calendar, photos, App Store Connect, signing, provisioning, keychain, or entitlement workflow exists yet.

## CCC Android

CCC Android is a future native mobile control client for approvals, status, receipts, and user-reviewed capture. No Android app is implemented yet. No Kotlin, Java, React Native, Expo, Flutter, Gradle, Android Studio, native package, camera, microphone, location, notification, contacts, calendar, photos, Play Store, signing, keystore, permission, background service, or notification channel workflow exists yet.

## CCC macOS

CCC macOS is a future desktop/local companion client for status, menu bar, local runtime, receipt, and approval surfaces. No macOS app is implemented yet. No Swift, AppKit, SwiftUI, native package, signing, notarization, keychain, entitlement, menu bar agent, or background agent workflow exists yet.

## Mobile Companion

Mobile Companion remains a future governed sensor/capture device client concept. It is a control, approval, capture, receipt, and status surface, not the agent brain. Sensor work must wait for Mobile Companion and Device Capability Broker contracts.

## Open Design System

Open Design System is design governance for CCC surfaces. Open Design does not replace OpenWebUI. Design docs guide custom CCC Web, CCC iOS, CCC Android, and CCC macOS surfaces without enabling design tools or design-to-code workflows.
## M19 Mobile Companion Contract Planning

v0.23.0 / M19 adds Mobile Companion Contract/API Planning only. CCC Web remains
the current TypeScript Web Control Center. CCC iOS and CCC Android are future
native mobile control clients only. No CCC native implementation is added, no
Android app is implemented yet, no iOS app is implemented yet, and no macOS app
is implemented yet.

All CCC clients are control surfaces, not the agent brain. All CCC clients must
use Python Agent Core authority. M19 adds no native build workflow, no mobile
sensor access, no OS permission integration, no signing, keystore,
provisioning, App Store, or Play Store workflow. Device Capability Broker is
required before sensors. Capture cannot silently become memory.

## M20 Device Capability Broker Contract

v0.24.0 / M20 implements Device Capability Broker Contract as contract-only
planning and validation. CCC Web remains the current TypeScript Web Control
Center. CCC iOS, CCC Android, and CCC macOS remain future clients. M20 adds no
native client, sensor access, OS permission integration, device pairing
runtime, backend API route, dependency, runtime execution, model/provider call,
remote execution, plugin enablement, OpenWebUI integration, or production
authority. Device output is not trusted control input by default. M21 remains
planned/provisional.
