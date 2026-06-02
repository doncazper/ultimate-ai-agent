# Device Capability Broker Contract

Status: M20 contract-only. No runtime broker is implemented.

The Device Capability Broker is the future governance boundary for device
capabilities across CCC iOS, CCC Android, CCC macOS, and mobile web/PWA
surfaces. M20 defines the contract before any future device or mobile sensor
implementation.

M20 adds no sensor access, no OS permission integration, no native app, no
backend API route, no runtime execution, no model/provider call, no remote
execution, no plugin enablement, no dependency, and no production authority.
M20 adds no backend API route and no Device Capability Broker runtime implementation.
External sends are not allowed. M21 remains planned/provisional.

The broker contract requires every future device capability to declare purpose,
risk classification, permission scope, consent boundary, retention rule,
redaction rule, receipt requirement, revocation rule, trust boundary, and a
validation decision before implementation.

Device and mobile clients are control surfaces, not the agent brain. They must
use Python Agent Core authority and cannot bypass Approval Authority, Consent
Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.

Device Capability Broker output is not trusted control input by default. Device
output must be validated, redacted, receipt-backed, and reviewed before future
use. Capture cannot silently become memory. Capture cannot trigger external
sends.

M20 does not request camera, microphone, location, notification, contacts,
calendar, photos, files, clipboard, Bluetooth, NFC, biometrics, background
service, local network, or OS permissions.
