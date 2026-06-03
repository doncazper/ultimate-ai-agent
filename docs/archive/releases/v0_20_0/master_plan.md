Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.20.0

Status: Historical master plan for v0.20.0.

v0.20.0 implements M16 Event Timeline + Run/Receipt Trace Viewer.

Implemented scope:

- frontend-only `/events/timeline` route in CCC Web.
- read-only event timeline summary list.
- selected run/receipt trace summary panel.
- event relation/ref summary panel.
- Foundation Gate evidence summary panel.
- safe mock event and trace data.
- frontend tests for the route and redaction boundary.
- static frontend verifier checks for raw M16 trace fields, credential-like trace fields, export endpoints, dangerous controls, and missing M16 boundary copy.
- Foundation Gate criterion `m16_event_timeline_trace_viewer_safe`.
- Control Center docs for event timeline, run/receipt trace viewer, and trace redaction policy.

Architecture boundary:

- Python Agent Core remains the brain.
- Event Ledger remains the source of truth for event records.
- Approval Authority remains the only approval authority.
- Control Center is a governance/control/status/preview surface only.
- CCC Web timeline and trace panels display safe refs and summaries only.
- v0.20.0 adds no backend API routes and keeps OpenAPI path count unchanged at `74`.

Not implemented in v0.20.0:

- M16 hardening follow-up work.
- approval execution.
- approval grant/reject mutation.
- backend timeline, trace, receipt detail, event detail, or evidence detail routes.
- raw event payload dumps.
- raw prompt, secret, file, memory, credential, provider payload, or unreviewed tool argument display.
- production telemetry export, external observability integration, OpenTelemetry export, or cloud traces.
- Evidence/File/Memory Viewer.
- OpenWebUI bridge code.
- runtime execution or model/provider calls.
- remote execution or remote worker dispatch.
- mobile app, sensor API, OS permission integration, or native CCC implementation.
- plugin enablement, Chrome authenticated profile control, Computer Use automation, native build workflow, scanner runtime, Skill Factory, self-improvement, production persistence, or external action.
