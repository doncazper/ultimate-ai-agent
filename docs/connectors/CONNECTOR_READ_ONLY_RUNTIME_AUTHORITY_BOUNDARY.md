# Connector Read-Only Runtime Authority Boundary

M125 connector read-only runtime is safe-ref-only. Connector scope refs,
connector allowlist refs, operation allowlist refs, safe metadata preview refs,
data minimization refs, redaction refs, audit refs, replay refs, and no-effect
receipt plan refs are not authority to access live connector accounts.

The record is source-messages-connector-contract-review-bound to the accepted
M124 Messages Connector Contract Review and remains non-authoritative outside
the reviewed safe metadata preview refs.

The contract grants no live connector runtime, no account auth, no network
access, no credential handling, no raw connector content, no full content read,
no connector write, no connector send, no connector delete, no connector
export, no connector bulk export, no attachment download, no model call, no
memory write, no context injection, no execution, no backend route, no Control
Center control, no dependency, no M126 work, no beta release, and no production
authority.

M126 remains future. M150 remains the planned v1.2.0-alpha target.
