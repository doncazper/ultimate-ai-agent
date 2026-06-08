# Mobile Kill Switch + Revocation Policy

M108 policy keeps Mobile Kill Switch + Revocation contract-only, review-only,
and safe refs only.

Required bindings:

- actor-bound
- device-bound
- approval-bound
- revocation-bound
- audit required
- replay required

Denied behavior:

- no revocation execution
- no kill switch execution
- no approval revocation
- no session stop
- no notification delivery
- no push trigger
- no background worker
- no scheduler
- no daemon
- no device token handling
- no external service
- no network sync
- no raw approval payload
- no dependency
- no memory write
- no context injection
- no execution
- no backend route
- no Control Center control
- no production authority

M109 remains future.
