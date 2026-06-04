# File Review Review-Only Policy

Status: active M36 documentation.
Current through: **v0.40.1**.

The M36 CCC file review surface is review-only. It can show redacted packet
metadata and exact binding refs, but it cannot mutate approval state or create
authority.

## Required UI Properties

- The surface must show that packet data is mock and non-authoritative when
  fallback data is used.
- Packet selection and expansion are display-only.
- Packet selection and expansion are local read-only UI state.
- The surface displays safe refs only.
- No mutating request is made by the file review surface.
- Review-only decision status is informational.
- Approval gate contract status is informational.
- Receipt plan metadata is informational.

## Forbidden Controls

The surface must not include approve, deny, submit, save, mark-reviewed,
export, download, copy raw, file picker, browse, upload, root selector, raw
file open, context proposal, context injection, memory write, execute, run,
tool, or model-call controls.

## No Authority

M36 adds no approval capture, no approval persistence, no raw file display, no
context proposal, no context injection, no memory writes, no export, no
execution, no backend routes, no dependencies, and no production authority.

M37 remains planned/provisional. M38 remains planned/provisional.
