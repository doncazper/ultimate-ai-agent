# M125 to M126 Boundary

Checkpoint M125 implements Connector Read-Only Runtime only. It records safe
metadata preview refs, connector scope refs, connector allowlist refs, operation
allowlist refs, data minimization refs, redaction refs, audit refs, replay refs,
accepted checkpoint refs, and a no-effect receipt plan. It is
source-messages-connector-contract-review-bound to M124.

M126 remains future as Connector Approval Capture. M125 does not add connector
approval capture, approval persistence, live connector runtime, account auth,
network access, credential handling, raw connector content, full content read,
connector write, connector send, connector delete, connector export, connector
bulk export, attachment download, model call, memory write, context injection,
execution, backend route, Control Center control, dependency, beta release, or
production authority.

M150 remains the planned v1.0.0-alpha target.
