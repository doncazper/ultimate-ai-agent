# Scoped Autonomy Session Scope Policy

Status: M62 / v0.66.0 implemented-released policy.

Scoped autonomy session contracts are disabled by default and dry-run first.
Every M62 scope must be actor-bound, resource-bound, duration-bound, and tied
to explicit allowlist refs. Revocation and audit/replay refs are required.

Approval refs are identifiers only. approval_test_* refs are never runtime
authority. A review-only approval ref cannot authorize session start, session
activation, autonomous actions, execution, tool execution, shell execution,
network tools, browser automation, background worker behavior, memory writes,
context injection, plugin execution, mobile sensor access, remote execution, or
production authority.

M62 validates contracts for review. It adds no backend route and no dependency.
