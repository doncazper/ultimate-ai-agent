# Mobile Permission Receipt Flow

Status: Current M19 permission/receipt planning doc through v0.23.1.

M19 models permission decisions as contract-only planning metadata. It does not
request, grant, store, or integrate OS permissions. It adds no camera,
microphone, location, notification, contacts, calendar, files, photos,
Bluetooth, NFC, biometrics, background service, or mobile app runtime.

Permission planning rules:

- Android permissions must be explicit and scoped in future reviewed milestones.
- iOS permissions must be explicit and scoped in future reviewed milestones.
- no background location by default.
- no passive microphone.
- no silent photo scan.
- no silent contacts scan.
- no silent calendar scan.
- no background service without reviewed policy.
- no notification runtime without receipt-backed policy.
- no Play Store, signing, keystore, App Store, provisioning, entitlement, or
  keychain workflow until a dedicated release milestone.

Receipt planning rules:

- receipt-backed summaries are required for future captures.
- redacted receipt required is the default.
- no raw payload storage is allowed by M19.
- capture cannot silently become memory.
- memory writes require future reviewed policy and Python Agent Core authority.

## v0.23.1 Hardening Note

v0.23.1 keeps all permission and receipt planning contract-only. Contacts and
calendar remain planned/disabled. Metadata refs must be secret-free. External
sends are denied. OS permission integration and background services are not
implemented. Android and iOS remain planned client surfaces only; no app,
permission runtime, notification runtime, signing, keystore, provisioning, App
Store workflow, or Play Store workflow exists.

## v0.24.0 M20 Device Capability Broker Contract

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation. Future device permission lifecycle, receipts,
redaction, revocation, and auditability are defined, but no sensor access, OS
permission integration, native clients, pairing runtime, backend API route,
background service, notification runtime, dependency, runtime execution,
model/provider call, remote execution, plugin enablement, OpenWebUI
integration, or production authority is added. M21 remains planned/provisional.
