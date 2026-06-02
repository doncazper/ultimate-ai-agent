# Run Receipt Trace Viewer

Status: Active for v0.20.0 / M16 Event Timeline + Run/Receipt Trace Viewer.

The Run Receipt Trace Viewer is the selected-detail panel inside `/events/timeline`. It gives CCC Web a safe read-only trace summary for a selected event or receipt relationship.

Allowed trace fields:

- event refs.
- receipt refs.
- Foundation Gate evidence refs.
- parent and child event refs.
- run ref and correlation ref when represented as safe identifiers.
- source surface.
- actor summary.
- timestamp.
- status.
- redaction status.
- safe summary message.

Not allowed:

- execution controls.
- approval execution.
- tool execution.
- model/provider execution.
- external export.
- cloud traces.
- OpenTelemetry export.
- raw event payloads.
- raw prompts.
- raw secrets.
- raw file contents.
- raw memory contents.
- raw credentials.
- raw provider payloads.
- raw tool arguments unless a future reviewed milestone defines an explicitly safe summary contract.

No backend route is added for M16. The viewer uses frontend mock trace data in this release. The Python Agent Core, Event Ledger, Approval Authority, Consent Ledger, Tool Broker, Secret Broker, Redaction, and Foundation Gate remain authoritative.
