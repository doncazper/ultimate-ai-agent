# Mobile Permission Receipt Flow

Status: Current M19 permission/receipt planning doc for v0.23.0.

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
