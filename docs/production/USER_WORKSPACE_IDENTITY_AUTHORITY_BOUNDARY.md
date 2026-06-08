# User/Workspace Identity Authority Boundary

Status: Checkpoint M112. Contract-only and review-only.

User refs and workspace refs are review identifiers only. They do not grant
production authority, production runtime, auth runtime, login, session cookie
handling, credential handling, persistent identity store behavior, account
connector behavior, network access, model call authority, memory write
authority, context injection authority, execution authority, tool execution,
shell execution, browser automation, plugin execution, mobile sensor access,
background worker authority, remote execution, backend route authority, Control
Center control authority, or dependency authority.

The user/workspace identity model is bound to the M111 Production Threat Model
by safe refs. It is actor-bound, baseline-bound, source-threat-model-bound,
audit-bound, and replay-safe.

M113 remains future.
