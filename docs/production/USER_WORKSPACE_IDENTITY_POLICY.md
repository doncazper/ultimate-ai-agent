# User/Workspace Identity Policy

Status: Checkpoint M112. Contract-only and review-only.

The M112 policy requires a user/workspace identity model to stay contract-only,
review-only, safe-ref-only, actor-bound, baseline-bound,
source-threat-model-bound, audit-bound, and replay-safe.

The policy requires safe refs, user refs, workspace refs, identity boundary
refs, audit refs, replay refs, and a no-effect receipt plan.

The policy denies production authority, production runtime, auth runtime,
login, session cookie handling, credential handling, persistent identity store
behavior, account connector behavior, network access, model call, memory
write, context injection, execution, tool execution, shell execution, browser
automation, plugin execution, mobile sensor access, background worker work,
remote execution, backend route changes, Control Center control changes, and
dependency changes.

M113 remains future.
