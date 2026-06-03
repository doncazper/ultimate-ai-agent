Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.19.1

Status: Current master plan for v0.19.1.

v0.19.1 is a focused M15 hardening patch for Approval Queue + Receipt/Event Viewer UI safety.

Implemented hardening scope:

- explicit approval authority boundary copy in Approval Queue and detail surfaces.
- explicit statement that approval refs are identifiers only and never authority.
- explicit receipt detail redacted-summary metadata copy.
- explicit event detail redacted-summary metadata copy.
- frontend tests for authority boundary copy and redacted receipt/event detail copy.
- static frontend verifier checks for raw M15 review fields, credential-like review fields, dangerous controls, and missing authority-boundary copy.
- Foundation Gate hardening for M15 authority, redaction, and raw-field safety.

Architecture boundary:

- Python Agent Core remains the brain.
- Approval Authority remains the only approval authority.
- Control Center is a governance/control/status/preview surface only.
- CCC Web must not bypass Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
- v0.19.1 adds no backend API routes and keeps OpenAPI path count unchanged at `74`.

Not implemented in v0.19.1:

- M16 Event Timeline + Run/Receipt Trace Viewer.
- approval execution.
- approval grant/reject mutation.
- backend approval queue, receipt, or event detail routes.
- Evidence/File/Memory Viewer.
- OpenWebUI bridge code.
- runtime execution or model/provider calls.
- remote execution or remote worker dispatch.
- mobile app, sensor API, OS permission integration, or native CCC implementation.
- plugin enablement, Chrome authenticated profile control, Computer Use automation, native build workflow, scanner runtime, Skill Factory, self-improvement, production persistence, or external action.
