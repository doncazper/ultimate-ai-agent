# Authority Levels

Status: M61 / v0.65.0 implemented-released contract.

M61 defines authority levels for review and validation. It does not activate
autonomy. The default mode off rule is mandatory.

## Level Contract

| Level | Contract meaning | M61 authority |
| --- | --- | --- |
| Mode 0 | Off | No execution and no autonomous action. |
| Mode 1 | Observe only | Defined for future review; no autonomous session. |
| Mode 2 | Dry-run plan | Defined for future review; dry-run first only. |
| Mode 3 | Ask before every action | Defined for future review; explicit approval cannot grant runtime authority in M61. |
| Mode 4 | Scoped autonomy window | Future scoped autonomy window only. |
| Mode 5 | Trusted recurring automation | Future trusted recurring automation only. |
| Mode 6 | Production authority, later | Future only; no production authority. |

Every future risky toggle must include scope, duration, actor, resource binding,
approval record where applicable, revocation, audit/replay, risk class, tests,
docs, static verifier coverage, Foundation Gate coverage, and release review.

## Denials

M61 has no global autonomy switch, no tool execution, no browser automation, no
shell execution, no network tools, no background worker, no autonomous session,
no memory writes, no context injection, no model/provider calls as authority, no
plugin execution, no mobile sensor access, no remote execution, no backend route,
no dependency, and no production authority.

M62 remains future.
