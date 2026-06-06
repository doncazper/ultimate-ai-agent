# OpenWebUI Safe Handoff Authority Boundary

M77 does not make OpenWebUI authority. OpenWebUI is a shell/bridge, not the
brain. Agent Core remains authority for all handoff decisions.

Approval refs identify a reviewed approval; they are not authority by
themselves. Exact approval binding is required. `approval_test_*` is denied.
Expired, revoked, replayed, actor-mismatched, session-mismatched, conversation
mismatched, or bridge-envelope-mismatched approvals are denied.

M77 grants no live OpenWebUI connection, no OpenWebUI runtime call, no provider
call, no model call, no model authority, no tool execution, no memory write, no
context injection, no network call, no credentials or cookies, no raw prompt, no
raw provider payload, no raw content, no backend route, no Control Center
control, no dependency, and no production authority.

Evaluator boundaries revalidate every safety-critical field. M78 remains
future.
