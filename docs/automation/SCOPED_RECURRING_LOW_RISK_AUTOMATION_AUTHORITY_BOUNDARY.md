# Scoped Recurring Low-Risk Automation Authority Boundary

M98 decisions are review-ready metadata, not runtime authority. Approval refs are
identifiers only. `approval_test_*` refs are never runtime authority. Model,
memory, context-pack, task-plan, tool-intent, runtime, OpenWebUI, and approval
refs cannot authorize scoped recurring automation.

M98 low-risk read-only status does not grant scheduler authority, background
worker authority, recurring execution runtime, mutating task authority,
credential or account actions, shell write, network write, browser write,
silent background collection, secret access, memory write, context injection,
export, backend route, dependency change, or production authority.

Every valid decision requires strict cadence, approval renewal required, renewal
expiry, stop conditions required, audit trail, revocation, and kill switch refs.
Evaluator boundaries revalidate model-copy-mutated fields.

M99 remains future.
