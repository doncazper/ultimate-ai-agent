# Checkpoint M125 Master Plan

Goal: add a deterministic, local, safe-ref-only Connector Read-Only Runtime
contract bound to M124 Messages Connector Contract Review.

Scope:
- source connector read-only runtime contracts
- exact M124 source binding
- safe metadata preview refs only
- connector scope refs, connector allowlist refs, operation allowlist refs
- data minimization refs and redaction refs
- audit/replay/no-effect receipt plan refs
- tests, static verification, documentation integrity, and Foundation Gate

Non-goals: live connector runtime, account auth, network access, credential
handling, raw connector content, full content read, connector write, connector
send, connector delete, connector export, connector bulk export, attachment
download, model call, memory write, context injection, execution, backend route,
Control Center control, dependency, M126 work, beta release, or production
authority.
