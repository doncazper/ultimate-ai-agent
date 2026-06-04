# M36 To M37 Boundary

Status: active M36 boundary documentation.
Current through: **v0.40.1**.

M36 implements CCC File Review Surface, Review-Only. It adds a frontend
display surface for redacted review packets, redaction summaries, exact
binding refs, review-only decision status, approval gate contract status, and
receipt plan metadata.

M36 does not capture approvals. M36 does not persist approvals. M36 does not
add backend routes. M36 displays safe refs only, keeps packet selection and
expansion as local read-only UI state, and makes no mutating request from the
file review surface. M36 does not add context proposal, context injection,
memory writes, export, execution, raw file display, full-file reads, file
mutation, file picker/browser/upload/root selector, or dependencies.

M37 remains planned/provisional as Review Approval Capture, Review-Only
Persistence. M37 must receive its own implementation prompt, tests, static
verification, documentation, Foundation Gate coverage, and release review
before any approval capture or persistence exists.

M38 remains planned/provisional as Safe Context Proposal From Approved Review.
M36 adds no context proposal and no context injection.
