# Foundation Gate Implementation Plan v0.89.0

v0.89.0 adds Foundation Gate coverage for M85 Read-Only Command Allowlist.

The Skill Package Security Rule remains unchanged. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities before any future enablement.

Gate coverage:

- M85 contract validation
- exact M84 binding
- safe refs only
- safe summary only
- evaluator boundaries revalidate
- no shell string
- no raw command
- no raw output
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
- M86 remains future
