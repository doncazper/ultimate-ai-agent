# v0.43.0 README Import

Status: historical release packet after acceptance.
Release: **v0.43.0 / M39 - CCC Context Proposal Surface**.

v0.43.0 adds a read-only CCC surface for safe context proposals created by M38.
The surface displays safe mock proposal data, proposal-only status,
approved-review provenance, exact binding refs, redaction verification, safe
proposal sections, and receipt-plan metadata.

## Boundaries

- display-only and proposal-only.
- mock and non-authoritative.
- exact binding refs remain visible.
- no context handoff.
- no context injection.
- no OpenWebUI handoff.
- no memory writes.
- no export.
- no execution.
- no model/provider calls.
- no raw file content or raw absolute paths.
- no approval mutation controls.
- no backend routes.
- no dependencies.

M40 remains future.
