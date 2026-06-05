# Mobile Approval Audit Hardening

v0.54.0 / M50 implements Mobile Approval Audit Hardening for the M49 mobile
review approval capture records.

The audit layer is review-only and safe-ref-only. It produces deterministic
audit reports over already-captured mobile review approval records and verifies
that records remain safe references only.

M50 audits:

- approval refs, actor refs, mobile surface refs, review packet refs, preview
  result refs, redaction summary refs, file refs, safe path refs, and
  idempotency keys.
- approve-review-only and deny-review-only status consistency.
- duplicate idempotency keys with mismatched record fingerprints.
- model_copy-mutated unsafe fields.
- secret-like metadata.
- raw path-like safe path mutations.

M50 denies:

- raw content
- full-file content
- unredacted preview
- raw absolute paths
- context proposal
- context injection
- memory write
- export
- execution
- approval execution
- mobile sensor access
- background collection
- backend route creation
- native audit UI
- production authority

In explicit gate terms: M50 adds no raw content, no context injection, no memory write, no export, no execution, no mobile sensor access, and no backend route.

Audit reports are non-authoritative. A passed audit is evidence that the mobile
approval capture records remain safe for review; it is not approval authority,
tool authority, context authority, execution authority, export authority, or
production authority.

The audit report safe message must never echo raw content, secrets, raw paths,
or mutated payloads. M50 keeps all receipt/audit outputs safe-ref-only.

M51 remains future. M51 may only start OpenWebUI bridge adapter pilot work after
a dedicated implementation, validation, and strict pushed-release review.
