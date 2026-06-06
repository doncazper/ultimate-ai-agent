# Shell Dry-Run Classifier

M83 implements the Shell Dry-Run Classifier as classifier-only, review-only,
deterministic, and local-only contracts over an M82 command proposal.

The classifier may assign a safe review classification to an already validated
M82 command proposal. It is not a shell, not a subprocess runner, and not a
dry-run execution engine.

M83 keeps:

- no dry-run execution
- no shell string
- no command execution
- no subprocess execution
- no shell execution
- no process spawn
- no filesystem mutation
- no network access
- no tool execution
- no browser automation
- no plugin execution
- no remote execution
- no model call
- no memory write
- no context injection
- no background worker
- no backend route
- no Control Center control
- no dependency
- no production authority

Receipts are safe summary only. Evaluator boundaries revalidate
safety-critical fields.

M84 remains future.
