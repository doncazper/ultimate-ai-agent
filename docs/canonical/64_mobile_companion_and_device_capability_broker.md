# 64 - Mobile Companion and Device Capability Broker

Status: Future planning only, v0.14.4

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

v0.14.4 does not implement:

```text
mobile app
sensor access
OS permission integration
background services
phone-as-agent-brain behavior
autonomous mobile actions
runtime Device Capability Broker
```
