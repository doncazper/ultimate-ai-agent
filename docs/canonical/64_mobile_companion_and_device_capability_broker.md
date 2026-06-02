# 64 - Mobile Companion and Device Capability Broker

Status: Future planning only, v0.14.6

v0.14.5 documentation integrity preserves this as future planning only.
v0.14.6 Codex plugin governance keeps iOS/Xcode tooling disabled until a dedicated Mobile Companion implementation milestone.

## Mobile Companion

The Mobile Companion is a future phone surface for control, approvals, capture, receipts, and status. It is not the agent brain.

The Python Agent Core remains the authority for agent decisions and governance. The TypeScript Control Center remains the future user-control layer. A mobile app should use stable API and OpenAPI contracts exposed by the Agent API Boundary rather than bypassing the core.

Default rule: no autonomous phone actions. A phone can present a request, collect user intent, capture user-reviewed input, and show receipts, but it must not silently act as an agent runtime.

## Device Capability Broker

The Device Capability Broker is the future governance boundary for device capabilities. Device capabilities are governed like tools, with additional device-specific privacy limits.

Future capability categories include:

```text
camera
microphone
location
notifications
share sheet
contacts
calendar
photos
files
biometrics
NFC
Bluetooth
motion
network status
```

Each future capability requires:

```text
manifest
risk classification
permission scope
purpose
retention policy
redaction policy
Event Ledger logging
receipt
revocation support
```

## Default Principles

All mobile sensors are disabled by default.

Mobile capture is foreground/user-gesture first. There is no passive always-on microphone, no background location by default, no silent photo library scan, no silent contacts or calendar access, no automatic memory write, no external send or publish without approval, and no silent sensor-to-agent stream.

Mobile sensor capture must never silently become memory. Mobile sensor capture must never silently trigger an external action.

## Capability Lifecycle

Future mobile capability use follows this lifecycle:

```text
declare capability
request permission
capture
redact and classify
create evidence refs
user review
optional memory or file write
receipt
retention or deletion
```

Raw capture is sensitive by default until classified and reviewed.

## Risk Levels

Low:

```text
app status
manual typed note
```

Medium:

```text
selected photo import
selected document import
```

High:

```text
camera capture
microphone clip
precise location
```

Critical or forbidden by default:

```text
always-on microphone
background location history
contacts bulk export
unapproved external send
hidden sensor access
```

## Source-of-Truth Rules

Mobile sensor data is evidence or capture, not truth by itself.

GPS is current context, not permanent memory unless approved. Camera OCR is untrusted extracted evidence until verified. Voice transcript is user-provided capture only after user confirmation. Sensor data cannot approve actions.

## Open-Source and Self-Hosted First

Future mobile work should prefer reusable TypeScript and OpenAPI contracts. React Native, Expo, Flutter, native Swift/Kotlin, or other mobile stacks may be evaluated later, but v0.14.4 makes no commitment.

Free, open-source, and self-hosted notification, pairing, sync, and local-network options should be evaluated first where practical.

## Non-Goals

v0.14.6 does not implement:

```text
mobile app
sensor access
OS permission integration
background services
phone-as-agent-brain behavior
autonomous mobile actions
runtime Device Capability Broker
iOS build workflow
Xcode workflow
simulator/device workflow
signing or provisioning workflow
```

Build iOS Apps / XcodeBuildMCP may be evaluated only in a future Mobile Companion implementation milestone with explicit approval.

## Future Mobile Design Governance

v0.18.2 adds Open Design System and UI Design Governance docs for future Control Center and Mobile Companion UI. Future Mobile Companion UI should inherit:

- repo-owned design source of truth.
- textual status and risk labels, not color-only meaning.
- accessible loading, empty, error, approval, receipt, and capture states.
- secret-free design artifacts and screenshots.
- no design tool, design SaaS, UI generator, screenshot-to-code, or design-to-code authority.

These docs add no mobile app, sensor API, native package, design tool integration, or mobile runtime capability.

## v0.18.3 CCC Native Client Clarification

CCC means Control Center Clients. Future mobile and desktop companion work should use the CCC naming when it is part of the custom governance/control client family:

- CCC Web is the current TypeScript web Control Center.
- CCC iOS is a future native mobile control client.
- CCC Android is a future native mobile control client.
- CCC macOS is a future desktop/local companion client.

CCC iOS and CCC Android are future approval, status, receipt, and user-reviewed capture surfaces only. They are not the agent brain and must use Python Agent Core authority. No Android app, iOS app, macOS app, native package, sensor access, OS permission integration, background service, notification runtime, signing, keystore, provisioning, App Store workflow, Play Store workflow, or native build workflow is added by v0.18.3.

Android planning constraints:

- Android permissions must be explicit and scoped.
- no background location by default.
- no passive microphone.
- no silent photo, contact, or calendar scans.
- no background service without reviewed policy.
- no notification runtime without receipt-backed policy.
- no Play Store, signing, or keystore workflow until a dedicated release milestone.

iOS planning constraints:

- iOS permissions must be explicit and scoped.
- no background location by default.
- no passive microphone.
- no silent photo, contact, or calendar scans.
- no App Store, signing, provisioning, or keychain workflow until a dedicated release milestone.

macOS planning constraints:

- no keychain, menu bar, background agent, signing, entitlement, or notarization workflow until a dedicated release milestone.

## v0.18.4 Post-M20 Mobile/Device Projection

v0.18.4 adds post-M20 roadmap projection docs only. Mobile and device work remains planned/provisional in:

- M31 - CCC Native Client Contract: iOS / Android / macOS.
- M32 - Device Pairing + Trust Handshake Contract.
- M33 - Mobile Approval Surface Prototype, No Sensors.
- M35 - Device Capability Broker Implementation, No Sensors Yet.
- M36 - Mobile Capture Inbox, Selected Input Only.
- M37 - One Governed Sensor Capability.

These milestones require dedicated implementation prompts and review prompts. v0.18.4 adds no mobile app, Android app, iOS app, macOS app, Device Capability Broker implementation, mobile capture, sensor access, OS permission integration, native build workflow, signing, keystore, provisioning, App Store workflow, or Play Store workflow.
