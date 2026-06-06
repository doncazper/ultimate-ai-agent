# Scoped Autonomy Session Contracts

Status: M62 / v0.66.0 implemented-released contract.

M62 adds scoped autonomy session contracts as contract-only and review-only
records. A scoped autonomy session request can describe actor-bound,
resource-bound, duration-bound, allowlist-bound, revocable, auditable, and
replayable session intent. It does not start a session and does not activate
autonomy.

Required bindings:

- actor-bound session request
- resource-bound scope
- capability refs
- allowlist refs
- duration-bound window
- risk class
- revocation ref
- audit/replay refs

M62 adds no session start, no session activation, no autonomous actions, no
background worker, no execution, no tool execution, no shell execution, no
network tools, no browser automation, no plugin execution, no mobile sensor
access, no remote execution, no memory write, no context injection, no
model/provider authority, no backend route, no Control Center control, no
dependency, and no production authority.

M63 remains future.
