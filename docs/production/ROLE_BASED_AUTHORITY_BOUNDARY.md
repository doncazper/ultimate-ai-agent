# Role-Based Authority Boundary

Checkpoint M116 is contract-only and review-only. Role refs, authority scope
refs, permission boundary refs, separation-of-duty refs, and the break-glass
boundary ref are descriptive safe refs. They are identifiers for review, not
runtime authority and not permission enforcement.

M116 records actor-bound, baseline-bound,
source-production-audit-retention-bound, user-bound, workspace-bound,
role-bound, authority-scope-bound, permission-boundary-bound, and
separation-of-duty-bound metadata for later review. These bindings do not grant
production authority.

M116 adds no production runtime, no authority runtime, no role enforcement, no
permission enforcement, no auth runtime, no login, no session cookie handling,
no OAuth flow, no token exchange, no credential handling, no account action, no
network access, no model call, no memory write, no context injection, no
execution, no backend route, no Control Center control, no dependency, no M117
work, no beta release, and no production authority.

M117 remains future. M150 remains the planned v1.2.0-alpha target.
