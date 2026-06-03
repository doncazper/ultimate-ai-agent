Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.20.1

Status: Historical master plan for v0.20.1.

v0.20.1 hardens M16 Event Timeline + Run/Receipt Trace Viewer safety.

Implemented scope:

- frontend interaction coverage for selecting alternate M16 timeline trace summaries.
- accessible selected-state marker on selected timeline cards.
- explicit M16 Foundation Gate OpenAPI path-count guard.
- explicit M16 Foundation Gate no-backend-timeline-route guard.
- frontend verifier coverage for tracked Control Center build and log artifacts.
- generated frontend build-output review hygiene documentation.
- release/version documentation for v0.20.1.
- whole-code bug/safety audit with P2/P3 findings reported only.

Architecture boundary:

- Python Agent Core remains the brain.
- Event Ledger remains the source of truth for event records.
- Approval Authority remains the only approval authority.
- Control Center is a governance/control/status/preview surface only.
- CCC Web timeline and trace panels display safe refs and summaries only.
- selecting `View trace` changes visible selection only.
- v0.20.1 adds no backend API routes and keeps OpenAPI path count unchanged at `74`.

Not implemented in v0.20.1:

- M17 Evidence/File/Memory Viewer.
- approval execution.
- approval grant/reject mutation.
- backend timeline, trace, receipt detail, event detail, or evidence detail routes.
- raw event payload dumps.
- raw prompt, secret, file, memory, credential, provider payload, or unreviewed tool argument display.
- production telemetry export, external observability integration, OpenTelemetry export, or cloud traces.
- OpenWebUI bridge code.
- runtime execution or model/provider calls.
- remote execution or remote worker dispatch.
- mobile app, sensor API, OS permission integration, or native CCC implementation.
- plugin enablement, Chrome authenticated profile control, Computer Use automation, native build workflow, scanner runtime, Skill Factory, self-improvement, production persistence, or external action.
