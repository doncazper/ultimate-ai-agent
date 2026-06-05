# v0.53.0 Master Plan

Milestone: M49 - Mobile Review Approval Capture.

Scope:

- Add mobile review approval capture contracts.
- Add approve-review-only and deny-review-only decision kinds.
- Bind approvals exactly to actor, mobile surface, review packet, preview
  result, redaction summary, file ref, and safe path ref.
- Add safe-ref-only mobile approval records and receipt plans.
- Add replay-safe idempotency and revoked/expired approval denial.
- Add evaluator revalidation for model_copy-mutated safety fields.
- Add tests, static verifier coverage, documentation-integrity checks, and
  Foundation Gate criteria.
- Update currentness docs and version metadata.

Non-goals:

- no raw file access
- no raw content
- no full-file content
- no unredacted preview
- no raw absolute path
- no context proposal
- no context injection
- no memory write
- no export
- no approval execution
- no tool execution
- no action execution
- no mobile sensor access
- no background collection
- no backend mobile approval route
- no native approval capture UI
- no dependency
- no production authority
- no M50 implementation
