# Autonomy Policy Rule Contracts

M63 policy rules are deterministic records. A rule contains safe refs for
allowed actors, allowed resources, allowed capabilities, required allowlist
entries, max authority mode, risk ceiling, duration ceiling, revocation, and
audit/replay. Rules are contract-only and review-only.

Rules must stay actor-bound, resource-bound, and capability-bound. Missing
policy rules, missing allowlist refs, missing revocation, missing audit/replay,
or secret-like metadata are denied. Rules also deny policy activation, session
start, autonomous actions, background worker, execution, tool execution, shell
execution, network tools, browser automation, backend route, dependency, memory
write, context injection, model/provider authority, and production authority.

Approval refs are identifiers only. They do not make a rule authoritative and do
not authorize a session. Skill Package Security Rule remains in force. M64
remains future.
