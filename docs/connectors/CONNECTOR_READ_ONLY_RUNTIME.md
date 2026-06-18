# Connector Read-Only Runtime

Checkpoint M125 adds a Connector Read-Only Runtime contract. It is
deterministic, local, safe-ref-only, and limited to safe metadata preview refs
from already-reviewed connector boundaries. It is bound to the M124 Messages
Connector Contract Review through source-messages-connector-contract-review-bound
refs, actor-bound refs, baseline-bound refs, user-bound refs, workspace-bound
refs, connector scope refs, connector allowlist refs, operation allowlist refs,
data minimization refs, redaction refs, audit refs, replay refs, accepted
checkpoint refs, and a no-effect receipt plan.

M125 permits only safe metadata preview refs for email, calendar, contacts, and
messages. It does not perform a live connector runtime call, does not connect
to accounts, does not authenticate, does not use credentials, does not access a
network, and does not read raw connector content or full content.

M125 adds no live connector runtime, no account auth, no network access, no
credential handling, no raw connector content, no full content read, no
connector write, no connector send, no connector delete, no connector export,
no connector bulk export, no attachment download, no model call, no memory
write, no context injection, no execution, no backend route, no Control Center
control, no dependency, no M126 work, no beta release, and no production
authority.

M126 remains future. M150 remains the planned v1.2.0-alpha target.
