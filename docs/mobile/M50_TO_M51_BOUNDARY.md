# M50 to M51 Boundary

M50 implements Mobile Approval Audit Hardening for M49 safe-ref-only mobile
review approval capture records. It does not start M51.

Allowed in M50:

- deterministic mobile approval audit reports
- safe-ref-only audit entries
- record status and decision consistency checks
- duplicate idempotency mismatch detection
- evaluator revalidation of model_copy-mutated audit fields
- secret-like metadata denial
- raw path-like mutation denial
- documentation, documentation-integrity checks, static verification, tests,
  and Foundation Gate coverage

Blocked in M50:

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
- backend mobile audit routes
- backend mobile approval execution routes
- native audit UI
- arbitrary mobile filesystem browsing
- credential or cookie handling
- dependency changes
- production authority
- M51 implementation

M51 remains future after M50. M51 may only add OpenWebUI Bridge Adapter Pilot
work after a dedicated implementation, validation, and strict pushed-release
review. OpenWebUI remains a shell/bridge, not the agent brain.
