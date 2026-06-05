# M49 to M50 Boundary

M49 implements Mobile Review Approval Capture as exact-scope, review-only,
safe-ref-only contract and persistence logic. It does not start M50.

Allowed in M49:

- mobile review approval capture contracts
- approve-review-only and deny-review-only decision kinds
- exact binding for actor, mobile surface, review packet, preview result,
  redaction summary, file ref, and safe path ref
- replay-safe idempotency and revoked/expired approval denial
- safe-ref-only approval records
- safe-ref-only receipt plans
- evaluator revalidation of safety-critical fields
- tests, documentation, static verification, documentation-integrity checks,
  and Foundation Gate coverage

Blocked in M49:

- raw file access
- raw content
- full-file content
- unredacted preview
- raw absolute path storage
- context proposal
- context injection
- memory write
- export
- approval execution
- tool execution
- task/action execution
- mobile sensor access
- background collection
- backend mobile approval capture route
- backend mobile approval execution route
- native approval capture UI
- arbitrary mobile filesystem browsing
- credential or cookie handling
- dependency changes
- production authority
- M50 implementation

M50 remains future after M49. M50 may only add Mobile Approval Audit
Hardening after a dedicated implementation, validation, and strict
pushed-release review.
