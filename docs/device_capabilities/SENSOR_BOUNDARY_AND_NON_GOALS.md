# Sensor Boundary And Non-Goals

Status: M20 contract-only safety boundary.

Camera, microphone, location, contacts, calendar, photos, files, clipboard,
Bluetooth, NFC, biometrics, notifications, motion, health, local network, and
screen capture are disabled and planned only.

M20 implements no sensor access. M20 implements no OS permissions. M20
implements no native app. M20 implements no notification runtime. M20
implements no background service. M20 implements no pairing runtime. M20
implements no mobile storage runtime.

Future sensor work must be one capability at a time, after a reviewed
implementation milestone. There is no background location by default. There is
no always-on microphone. There are no silent photos. There is no contact scan.
There is no calendar scan. There is no local network scan. There is no private
data scraping.

Device Capability Broker output is not trusted control input by default.
Capture cannot silently become memory.

## v0.24.1 M20 Hardening Note

v0.24.1 hardens the no-sensor boundary. No sensor is enabled. No sensor is
implemented. Camera, microphone, location, notifications, contacts, calendar,
photos, files, clipboard, Bluetooth, NFC, biometrics, motion, health, local
network, and screen capture remain planned-disabled or future-broker-only.
Background services and notification runtime are blocked. OS permission
integration is absent. Device pairing runtime is future. M21 remains
planned/provisional.
