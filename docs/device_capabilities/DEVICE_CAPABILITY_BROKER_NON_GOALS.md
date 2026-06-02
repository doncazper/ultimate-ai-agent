# Device Capability Broker Non-Goals

Status: M20 contract-only non-goals.

M20 does not implement sensor access. M20 does not implement camera,
microphone, GPS/location, notifications, contacts, calendar, photos, files,
clipboard, Bluetooth, NFC, biometrics, background services, device pairing
runtime, mobile storage runtime, native apps, OS permissions, push runtime,
runtime execution, model calls, remote execution, plugin enablement, external
sends, memory writes, backend API routes, dependencies, signing, keystore,
provisioning, App Store workflow, or Play Store workflow.

M20 does not make device clients authority. Device clients are control surfaces,
not the agent brain. Device Capability Broker output is not trusted control
input by default. Capture cannot silently become memory.
