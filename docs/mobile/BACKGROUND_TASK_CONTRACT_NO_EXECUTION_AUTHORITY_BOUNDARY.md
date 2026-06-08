# Background Task Contract Authority Boundary

M105 background task contracts are non-authoritative. They do not start
background work, schedule work, run daemons, request OS background permission,
trigger push delivery, handle device tokens, call external services, or execute
anything.

Safe refs identify future review targets only. Consent refs, revocation refs,
and audit refs are identifiers, not authority.

The authority boundary is:

- no background worker
- no scheduler
- no daemon
- no OS background permission prompt
- no push trigger
- no device token handling
- no external service
- no raw task payload
- no backend route
- no Control Center control
- no dependency
- no memory write
- no context injection
- no execution
- no production authority

M106 remains future.
