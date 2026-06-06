# Foundation Gate Implementation Plan v0.81.0

v0.81.0 adds Foundation Gate coverage for M77 OpenWebUI Safe Handoff Execution.

Gate criteria verify:
- M77 contract files, docs, tests, and builders exist.
- Safe handoff execution requires exact approval binding.
- Approval refs alone and `approval_test_*` cannot authorize handoff.
- Evaluator boundaries revalidate safety-critical fields.
- No live OpenWebUI connection, OpenWebUI runtime call, provider call, model
  call, model authority, tool execution, memory write, context injection,
  network call, credentials or cookies, raw prompt, raw provider payload, raw
  content, backend route, Control Center control, dependency, or production
  authority is added.
- M78 remains future.

## Skill Package Security Rule

All skills are untrusted packages by default. A future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted.
