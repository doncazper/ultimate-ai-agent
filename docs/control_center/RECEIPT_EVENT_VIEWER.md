# Receipt And Event Viewer

Status: Active for v0.19.1 / M15 Approval Queue + Receipt/Event Viewer UI safety hardening.

The Receipt Viewer and Event Viewer are read-only and preview-only CCC Web surfaces. They show redacted summary-only records for inspection and review. They are not the Event Ledger, not receipt authority, and not execution authority.

The Receipt Viewer may show:

- receipt refs.
- related event refs.
- action type summary.
- actor summary.
- status.
- risk and data classification.
- redaction status.
- safe message.
- timestamp.
- related approval refs.

The Event Viewer may show:

- event refs.
- event type.
- actor summary.
- source surface.
- result/status.
- reason codes.
- timestamp.
- related refs.
- redaction status.
- safe message.

Receipt and event records in CCC Web must remain redacted and summary-only. The UI must not expose raw event payloads, raw prompt bodies, raw file bodies, raw memory contents, raw provider payloads, raw secrets, raw credentials, or unredacted debug data.

v0.19.1 hardening requires selected receipt detail panels to state that receipt detail is redacted summary metadata only, and selected event detail panels to state that event detail is redacted summary metadata only.

M15 uses visibly mock, non-authoritative frontend fallback summaries for receipt and event detail panels. This patch adds no receipt mutation route, no event mutation route, no raw event route, and no OpenAPI path.

M16 Event Timeline + Run/Receipt Trace Viewer remains future work. M15 adds only summary list and selected-detail inspection panels.
