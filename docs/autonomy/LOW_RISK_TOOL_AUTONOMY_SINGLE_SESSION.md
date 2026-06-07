# Low-Risk Tool Autonomy, Single Session

M92 defines Low-Risk Tool Autonomy, Single Session as review-only,
low-risk only, single-session only, deterministic, local-only contract
metadata. It binds a proposed single session to an exact M91 Autonomous Tool
Execution Contract decision and an exact low-risk autonomous dry run record.

The contract is safe refs only. It may describe one reviewed, low-risk tool
autonomy session for later human review, but it grants no runtime authority and
performs no side effects.

## Boundary

- Exact M91 Autonomous Tool Execution Contract binding is required.
- Exact low-risk autonomous dry run binding is required.
- The single session scope is safe refs only.
- Approval refs are identifiers only.
- Evaluator boundaries revalidate safety-critical fields, bound M91 decisions,
  bound dry-run records, no-authority flags, safe refs, and receipt plans.
- Safe summary only receipt metadata is allowed.

## Non-Authority

M92 adds no real tool execution, no autonomous execution, no session start, no
additional session, no multi-tool run, no command execution, no shell execution,
no subprocess execution, no filesystem mutation, no network access, no browser
automation, no plugin execution, no remote execution, no model call, no memory
write, no context injection, no background worker, no backend route, no Control
Center control, no dependency, no raw tool payload, no raw provider payload,
and no production authority.

M93 remains future.
