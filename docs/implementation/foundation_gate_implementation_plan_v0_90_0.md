# Foundation Gate Implementation Plan v0.90.0

v0.90.0 implements M86 Shell Approval Gate v1.

Foundation Gate coverage:

- M86 shell approval gate contract criteria.
- M86 shell approval gate static safety criteria.
- M86 shell approval gate route boundary criteria.
- M86 roadmap currentness criteria.

The Skill Package Security Rule remains unchanged. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities.

M86 adds no shell string, raw command, raw output, command execution, subprocess
execution, shell execution, process spawn, filesystem mutation, network access,
tool execution, browser automation, plugin execution, remote execution, model
call, memory write, context injection, background worker, backend route, Control
Center control, dependency, M87 work, or production authority.
