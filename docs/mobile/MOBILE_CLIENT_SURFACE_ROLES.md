# Mobile Client Surface Roles

Status: Current M19 mobile client role planning doc for v0.23.0.

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
