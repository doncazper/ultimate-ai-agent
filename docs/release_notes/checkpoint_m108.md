# Checkpoint M108 Release Notes

Checkpoint M108 adds Mobile Kill Switch + Revocation contracts while the
product baseline remains v1.7.2.

Added:

- contract-only mobile kill-switch and revocation records
- safe revocation refs and safe kill switch refs
- safe revocation reason refs and safe kill switch reason refs
- actor-bound, device-bound, approval-bound, revocation-bound audit/replay
  requirements
- tests, static verifier coverage, documentation integrity coverage, and
  Foundation Gate coverage

Not added:

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
- no M109 work

M109 remains future.
