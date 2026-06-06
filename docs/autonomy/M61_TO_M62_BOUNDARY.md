# M61 To M62 Boundary

Status: M61 / v0.65.0 implemented-released boundary.

M61 implements Autonomy Mode Charter + Authority Levels as contract-only
planning and validation work. It defines Mode 0 through Mode 6, keeps default
mode off, and records the authority ladder: capability exists, disabled by
default, dry-run first, limited allowlist, explicit approval, scoped autonomy
window, audit/replay, revocation, and broader autonomy only after later review.

M61 does not implement M62. M62 remains future.

## Explicit Non-Goals

M61 adds no global autonomy switch, no production authority, no execution, no
tool execution, no browser automation, no shell execution, no network tools, no
background worker, no autonomous session, no memory writes, no context
injection, no model/provider calls as authority, no plugin execution, no mobile
sensor access, no remote execution, no backend route, no Control Center control,
and no dependency.

M62 may define scoped autonomy session contracts only after M61 is accepted
Green.
