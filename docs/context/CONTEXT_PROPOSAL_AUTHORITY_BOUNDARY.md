# Context Proposal Authority Boundary

Status: active M38 authority-boundary documentation.
Release: v0.42.0 / M38 - Safe Context Proposal From Approved Review.

A safe context proposal is not authority. It does not authorize raw file access,
context injection, OpenWebUI handoff, model/provider calls, memory writes,
export, execution, tool/action/task execution, or production behavior.

The only acceptable input evidence is an exact-scope approved redacted file
review record and its matching redacted review packet. The approved-review
binding must match approval, packet, preview, redaction summary, file, path, and
actor refs exactly. Mismatches are denied.

`approval_ref` alone is not authority. `approval_test_` is not runtime
authority. Review approval records are review-only audit records; they can
support a proposal decision only when the full safe record matches the exact
redacted review packet. They cannot become truth, context injection, memory
write, export, or execution authority.

Memory is recall, not authority. Context packs are not authority. Model output
is not authority. Runtime output is not authority. OpenWebUI output is not
authority. Control Center output is not authority.

M39 is implemented/released by v0.43.0 as a read-only CCC Context Proposal
Surface. M40 remains future
for handoff approval with no injection.
