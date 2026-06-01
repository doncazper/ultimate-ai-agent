# Foundation Gate Implementation Plan v0.14.4

v0.14.4 is a docs/planning-only release. It does not add new runtime Foundation Gate criteria because no mobile runtime, Device Capability Broker runtime, API route, dependency, sensor integration, OS permission integration, or background service exists.

Skill Package Security Rule:

All skills are untrusted packages by default. Before any skill package can become an executable or high-trust capability it must have a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Planning additions:

- Mobile Companion is a future control, approval, capture, receipt, and status surface only.
- Phone/mobile is not the agent brain.
- Device Capability Broker is the future governance boundary for mobile device capabilities.
- Mobile sensors are disabled by default and must be explicit-permission, scoped, logged, revocable, and receipt-backed.
- Mobile capture must not silently become memory, approve actions, or trigger external sends.
- Future mobile work must pass through Consent Ledger, Approval Authority, Event Ledger, Redaction, Receipt, and Tool Broker style governance.

Gate continuations:

- no mobile app code.
- no iOS or Android code.
- no React Native, Expo, Flutter, Swift, Kotlin, Capacitor, Ionic, or native mobile package.
- no camera, microphone, location, contacts, calendar, photos, NFC, Bluetooth, motion, biometrics, notification, share-sheet, or sensor API.
- no OS permission integration.
- no mobile background service.
- no device pairing.
- no network calls.
- no autonomous mobile actions.
- no runtime Device Capability Broker.
- no phone-as-agent-brain behavior.
