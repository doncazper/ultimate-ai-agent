# Safe Context Proposal From Approved Review

Status: active M38 documentation.
Release: v0.42.0 / M38 - Safe Context Proposal From Approved Review.

M38 adds safe context proposal contracts built from an exact-scope approved
redacted file review record. A proposal is non-authoritative and proposal-only:
it is not context injection, not OpenWebUI handoff, not memory write, not truth,
not export, not execution, and not production authority.

The proposal is built only from approved redacted review materials. It never
reads raw files, never returns raw content, never stores raw content, never
stores full-file content, and never stores unredacted preview text. It carries
safe refs, bounded redacted sections, source-chain provenance, redaction
verification, and receipt-plan metadata.

M38 requires exact approved-review binding across:

- approval_ref and approved review record
- review_packet_ref
- preview_result_ref
- redaction_summary_ref
- file_ref
- safe_path_ref/path_ref
- actor_ref

`approval_ref` alone is not authority. approval_ref alone is not authority.
`approval_test_` refs are not runtime
authority. Memory refs, context pack refs, tool intent refs, model output refs,
runtime output refs, OpenWebUI refs, and Control Center refs cannot authorize
context proposal creation, context injection, memory writes, export, execution,
model calls, or raw file access.

M39 remains planned/provisional for the future Control Center context proposal
surface. M40 remains future for context handoff approval with no injection.
OpenWebUI bridge work remains future M51/M52.
