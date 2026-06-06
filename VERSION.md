# Ultimate AI Agent Version

Current active baseline: **v0.71.0**

v0.71.0 implements M67 Revocation + Kill Switch. It adds contract-only,
review-only, deterministic revocation and kill-switch records that bind exact
revocation intent to exact scoped approval bundle refs, source scope refs, audit
replay view refs, simulation result refs, actor refs, resource refs, capability
refs, allowlist refs, revocation refs, audit refs, replay refs, and approval
refs as identifiers only. It records revocation requested and kill-switch
requested states for review while revalidating the scoped approval bundle at
evaluator boundaries, and adds tests, documentation-integrity checks, static
verification, and Foundation Gate coverage.

It adds no revocation action, kill-switch activation, session stop, process
kill, policy activation, session start, autonomous actions, background worker,
execution, tool execution, shell execution, network tools, browser automation,
plugin execution, mobile sensor access, remote execution, memory writes, context
injection, model/provider authority, backend routes, Control Center controls,
dependencies, M68 work, or production authority.
