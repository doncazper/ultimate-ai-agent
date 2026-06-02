# Trace Redaction Policy

Status: Active for v0.20.0 / M16 Event Timeline + Run/Receipt Trace Viewer.

M16 trace displays are redacted summary-only. Trace views may display safe refs and safe summaries, but they must not display raw payloads.

Allowed display classes:

- safe event refs.
- safe receipt refs.
- safe evidence refs.
- safe run refs and correlation refs.
- event type.
- source surface.
- actor summary.
- status.
- timestamp.
- redaction status.
- safe message.
- relation type and relation summary.
- Foundation Gate criterion refs and evidence status summaries.

Forbidden display classes:

- no raw prompts.
- no raw secrets.
- no raw file contents.
- no raw memory contents.
- no raw credentials.
- no raw provider payloads.
- no raw event payload dumps.
- no raw receipt payload dumps.
- no unreviewed tool arguments.
- no production telemetry export.
- no external telemetry export.
- no OpenTelemetry export.
- no cloud traces.

The frontend static verifier rejects raw M16 trace fields and credential-like trace fields in mock fixtures. Foundation Gate criterion `m16_event_timeline_trace_viewer_safe` verifies that the route remains read-only, summary-only, and free of execution/export controls.

No backend route is added. OpenAPI path count remains `74`.
