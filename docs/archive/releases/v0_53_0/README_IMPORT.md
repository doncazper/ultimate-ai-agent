# v0.53.0 README Import

v0.53.0 implements M49 Mobile Review Approval Capture.

The release adds exact-scope, actor-bound, resource-bound, replay-safe,
revocable, review-only mobile approval capture contracts. Captured records are
safe refs only and bind to the reviewed mobile surface, review packet, preview
result, redaction summary, file ref, safe path ref, actor ref, approval ref,
idempotency key, and receipt plan ref.

No raw file access, raw content, full-file content, unredacted preview, raw
absolute path, context proposal, context injection, memory write, export,
approval execution, tool execution, action execution, mobile sensor access,
background collection, backend mobile approval route, native approval capture
UI, dependency, production authority, or M50 implementation is added.

M50 remains future.
