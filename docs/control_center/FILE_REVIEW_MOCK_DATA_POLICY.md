# File Review Mock Data Policy

Status: active M36 documentation.
Current through: **v0.40.1**.

The M36 Control Center file review surface may use local mock data when the
local backend is unavailable or when no live read-only summary endpoint exists.
That mock data must be visibly mock and non-authoritative.

## Mock Data Requirements

- mock packets use safe refs only.
- mock packets never use private path-shaped values, traversal fragments, raw
  absolute path labels, or caller-selected root strings as display refs.
- mock packets include redacted preview text only.
- mock packets include redaction summary text only.
- mock packets include exact binding refs.
- mock packets include review-only decision status.
- mock packets include approval gate contract status.
- mock packets include receipt plan metadata showing no raw content storage,
  no approval capture, no approval persistence, no context proposal, no context
  injection, no memory writes, no export, and no execution.
- no mutating request is made to load, select, or expand mock file review
  packets.

## Forbidden Mock Data

Mock data must not include raw file content, full-file content, unredacted
preview, raw absolute paths, real-looking secrets, credentials, tokens,
cookies, provider payloads, production user data, approval capture state,
approval persistence state, context proposal state, context injection state,
memory write state, export state, or execution state.

M37 remains planned/provisional. M38 remains planned/provisional.
