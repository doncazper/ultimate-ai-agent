# Mobile Client Surface Roles

Status: Current M19 mobile client role planning doc through v0.23.1.

Mobile clients are control surfaces, not the agent brain. CCC Web remains the
current TypeScript Web Control Center. CCC iOS and CCC Android are future
native mobile control clients. CCC macOS is a future desktop/local companion
client. All CCC clients must use Python Agent Core authority and must respect
Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker,
Redaction, receipts, and Foundation Gate.

Planned client roles:

- CCC Web: current governance/control/status/preview surface; read-only and
  preview-only until future reviewed milestones add authority.
- CCC iOS: future native mobile approval/status/receipt/capture surface; no iOS
  app is implemented yet.
- CCC Android: future native mobile approval/status/receipt/capture surface; no
  Android app is implemented yet.
- Mobile web companion: future browser-accessible mobile companion planning
  surface only.

No client may bypass approvals, execute actions locally, store secrets in
browser/mobile/local storage, or treat mobile output as trusted control input.
M19 adds no native build workflow and no OS permission integration.

## v0.23.1 Hardening Note

v0.23.1 keeps CCC iOS and CCC Android as future planned clients only. Android
support is planned, not implemented. iOS support is planned, not implemented.
No mobile/native client can approve actions locally, execute actions locally,
bypass Python Agent Core authority, enable contacts/calendar, store secret-like
metadata refs, send externally, integrate OS permissions, or run background
services.

## v0.24.0 M20 Device Capability Broker Contract

v0.24.0 implements M20 Device Capability Broker Contract as contract-only
planning and validation for future CCC iOS, CCC Android, CCC macOS, and mobile
web/PWA device capabilities. No client becomes authority. M20 adds no native
client, sensor access, OS permission integration, pairing runtime, backend API
route, dependency, runtime execution, model/provider call, remote execution,
plugin enablement, or production authority. Device output is not trusted
control input by default. M21 remains planned/provisional.
