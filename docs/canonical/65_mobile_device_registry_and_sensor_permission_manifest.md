# 65 - Mobile Device Registry and Sensor Permission Manifest

Status: Future planning only, v0.14.6

v0.14.5 documentation integrity preserves this as future planning only.
v0.14.6 Codex plugin governance keeps iOS/Xcode tooling disabled until a dedicated Mobile Companion implementation milestone.

This document names future model concepts only. It is not source code, not a runtime schema, not an OpenAPI contract, and not a permission implementation.

No mobile app exists yet. No OS permission integration exists yet. No sensor API exists yet. No background service exists yet.

## MobileDeviceIdentity

Future fields:

```text
device_id
owner_user_id
platform
app_instance_id
trust_status
pairing_status
last_seen_at
capabilities_declared
revocation_status
```

Device identity is not authority by itself. A paired or known device cannot grant itself new powers and cannot convert credentials into consent.

## MobileDeviceCapabilityManifest

Future fields:

```text
device_id
capability_id
capability_type
risk_level
requires_foreground
requires_user_gesture
requires_os_permission
allowed_purposes
denied_purposes
retention_policy
redaction_policy
event_logging_required
receipt_required
revocation_supported
```

Every future device capability must declare its purpose, risk, permission scope, retention, redaction, logging, receipt, and revocation behavior before it can be used.

## MobileSensorCaptureRequest

Future fields:

```text
request_id
device_id
capability_id
purpose
scope
duration
data_classification
approval_ref
consent_ref
event_ref
```

Capture requests require a specific purpose and scope. Arbitrary string refs are not authority. Approval and consent refs must resolve through their governing systems.

## MobileSensorCaptureResult

Future fields:

```text
capture_id
status
source_refs
redactions_applied
evidence_refs
retention_policy
safe_summary
no_raw_secret_fields
```

Capture results must not expose raw secrets or sensitive raw sensor data by default. Results are evidence refs and safe summaries until user-reviewed and governed.

## Future Capability IDs

```text
mobile.camera.capture
mobile.camera.scan_document
mobile.camera.read_qr
mobile.microphone.capture_clip
mobile.microphone.transcribe_clip
mobile.location.current
mobile.location.navigation_session
mobile.location.geofence_event
mobile.notifications.send_to_user
mobile.share_sheet.capture
mobile.photos.selected_import
mobile.contacts.lookup_scoped
mobile.calendar.context_scoped
mobile.nfc.scan_tag
mobile.bluetooth.nearby_summary
mobile.motion.activity_context
mobile.biometrics.local_unlock
mobile.emergency_stop
mobile.kill_switch
```

## Explicit Non-Implementation Statement

These are future schemas only. There is no code yet, no mobile app yet, no OS permission integration yet, no sensor API yet, no background service yet, no iOS/Xcode build workflow, and no simulator/device workflow.

v0.18.3 adds CCC Android terminology for future native client planning only. No Android app, Kotlin, Java, Gradle, Android Studio project, Android permission integration, background service, notification channel, Play Store workflow, signing, keystore, native package, mobile sensor access, or runtime Device Capability Broker is implemented.

## v0.18.4 Post-M20 Device Registry Projection

v0.18.4 links future device registry and permission work to M31-M37 in `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`. M35 is the first planned/provisional Device Capability Broker Implementation, No Sensors Yet milestone; M37 is the first planned/provisional one-governed-sensor milestone.

This patch adds no registry runtime, OS permission integration, Android/iOS app, background service, notification channel, sensor access, signing, keystore, provisioning, App Store workflow, Play Store workflow, or native build workflow.
## M19 Update

v0.23.0 / M19 adds Mobile Companion Contract/API Planning only. It does not
implement a mobile device registry, Device Capability Broker, mobile app, OS
permission integration, background service, notification runtime, pairing flow,
sensor runtime, or native build workflow.

M19 permission planning says iOS and Android permissions must be explicit and
scoped in future reviewed milestones. There is no background location by
default, no passive microphone, no silent photo/contact/calendar scan, no
background service without reviewed policy, no notification runtime without
receipt-backed policy, and no Play Store/signing/keystore/App
Store/provisioning/keychain workflow until a dedicated release milestone.

Device Capability Broker is required before sensors. Capture cannot silently
become memory. Phone/mobile is not the agent brain. M20 remains
planned/provisional.
