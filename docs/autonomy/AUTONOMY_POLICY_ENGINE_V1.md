# Autonomy Policy Engine v1

M63 adds Autonomy Policy Engine v1 as contract-only and review-only validation
over M62 scoped autonomy session contracts. The engine compares a proposed
session request against policy rules, actor-bound refs, resource-bound refs,
capability-bound refs, allowlist refs, a risk ceiling, a duration ceiling,
revocation requirements, and audit/replay requirements.

The M63 decision is non-authoritative. It can say a policy matched for review,
but approval refs are identifiers and cannot grant authority. M63 performs no
policy activation, no session start, no autonomous actions, no background
worker, no execution, no tool execution, no shell execution, no network tools,
no browser automation, no backend route, no dependency, no memory write, no
context injection, and no production authority.

AuthorityLease V1 integration is metadata-only for M63. When an evaluation
request includes an `AuthorityActionRequest`, the decision records the
AuthorityLease policy decision ref, outcome, required domain/capability refs,
reason refs, receipt/audit refs, rollback/safe-disable refs, and operator
message. `allow` or `ask` means the policy review can show the action is inside
an active lease scope; it still does not start a session or execute work.
`deny` or `degrade_to_draft` keeps the policy review blocked with readable
missing-scope reasons.

Skill Package Security Rule remains in force for this milestone. M64 remains
future.
