# v0.91.0 Master Plan

M87 delivers Sandboxed Command Audit Replay as a contract-only, review-only,
replay-view-only milestone.

Implementation scope:

- add sandboxed command audit replay contracts.
- bind audit replay to exact M86 Shell Approval Gate v1 decisions.
- bind exact replay step refs.
- store safe refs only and safe summary only.
- revalidate safety-critical fields at evaluator boundaries.
- add docs, tests, static verification, documentation-integrity checks, and
  Foundation Gate coverage.

Non-goals:

- no replay runner.
- no replay execution.
- no command execution.
- no subprocess execution.
- no shell execution.
- no process spawn.
- no filesystem mutation.
- no network access.
- no tool execution.
- no browser automation.
- no plugin execution.
- no remote execution.
- no model call.
- no memory write.
- no context injection.
- no background worker.
- no backend route.
- no Control Center control.
- no dependency.
- no M88 work.
- no production authority.
