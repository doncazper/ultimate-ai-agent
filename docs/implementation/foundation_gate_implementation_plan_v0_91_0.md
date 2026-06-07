# Foundation Gate Implementation Plan v0.91.0

v0.91.0 adds Foundation Gate coverage for M87 Sandboxed Command Audit Replay.

The Skill Package Security Rule remains unchanged. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities.

Gate checks cover:

- contract-only, review-only, replay-view-only audit replay contracts.
- exact M86 Shell Approval Gate v1 binding.
- exact replay step binding.
- safe refs only and safe summary only receipt plans.
- evaluator boundaries revalidate model-copy-mutated M86 decisions, replay
  steps, execution flags, raw-content flags, and receipt plans.
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
- no production authority.
- M88 remains future.
