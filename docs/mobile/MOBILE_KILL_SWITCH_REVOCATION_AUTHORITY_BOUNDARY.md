# Mobile Kill Switch + Revocation Authority Boundary

M108 Mobile Kill Switch + Revocation records are non-authoritative review
records. They may say that revocation or kill switch review is requested, but
they do not perform revocation execution, kill switch execution, approval
revocation, or session stop.

Safe refs are required:

- safe revocation refs
- safe kill switch refs
- safe revocation reason refs
- safe kill switch reason refs
- M107 approval renewal UX source refs
- actor-bound refs
- device-bound refs
- approval-bound refs
- revocation-bound refs
- audit refs
- replay refs

The authority boundary denies notification delivery, push trigger, background
worker, scheduler, daemon, device token handling, external service, network
sync, raw approval payload, dependency, memory write, context injection,
execution, backend route, Control Center control, and production authority.

M109 remains future.
