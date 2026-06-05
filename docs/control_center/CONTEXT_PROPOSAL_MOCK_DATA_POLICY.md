# Context Proposal Mock Data Policy

Status: active for **v0.43.0 / M39 - CCC Context Proposal Surface**.

M39 may use safe mock/demo context proposal data. Mock data must be visibly mock
and non-authoritative. It must use safe refs, redacted summaries, redaction
verification status, safe proposal sections, and receipt-plan metadata.

Mock data must not include raw file content, full-file content, unredacted
preview, raw absolute paths, raw prompts, raw provider payloads, credentials,
cookies, API keys, tokens, passwords, private keys, or secret-like values.

Mock data must keep all no-authority flags false:

- no context handoff.
- no context injection.
- no OpenWebUI handoff.
- no memory writes.
- no export.
- no execution.
- no raw file access.
- no model/provider calls.

M39 mock data is for browser-smoke reviewability only. It adds no backend
routes, dependencies, persistence, or production authority. M40 remains future.
