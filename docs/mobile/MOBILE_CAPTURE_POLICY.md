# Mobile Capture Policy

Status: Current M19 mobile capture planning doc for v0.23.0.

M19 adds contract-only capture intent plans. It adds no capture runtime, no
camera, no microphone, no location, no photos, no contacts, no calendar, no
files, no notifications, no OS permissions, and no mobile app.

Capture policy:

- capture cannot silently become memory.
- no silent capture.
- no automatic memory write.
- no external send.
- no raw capture payload storage.
- sensitive or forbidden captures cannot be stored without a future reviewed
  policy.
- capture summaries must be redacted and receipt-backed.
- future capture must respect Approval Authority, Consent Ledger, Tool Broker,
  Event Ledger, Secret Broker, Redaction, and Foundation Gate.

M19 safe capture plans are metadata/ref-only. They cannot execute, ingest, scan,
dispatch, or mutate files or memory.
