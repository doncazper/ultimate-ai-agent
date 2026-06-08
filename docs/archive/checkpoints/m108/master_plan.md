# Checkpoint M108 Master Plan

## Scope

Implement Mobile Kill Switch + Revocation contracts only.

## Allowed

- safe revocation refs
- safe kill switch refs
- safe revocation reason refs
- safe kill switch reason refs
- M107 approval renewal UX source report binding
- actor-bound, device-bound, approval-bound, revocation-bound review records
- audit and replay refs
- no-effect receipt plans
- tests, docs, verifiers, Foundation Gate coverage

## Not Allowed

- revocation execution
- kill switch execution
- approval revocation
- session stop
- notification delivery
- push trigger
- background worker
- scheduler
- daemon
- device token handling
- external service
- network sync
- raw approval payload
- dependency
- memory write
- context injection
- execution
- backend route
- Control Center control
- production authority
- M109 implementation

## Versioning

This is a checkpoint milestone. Product SemVer remains v1.7.2. M150 remains
planned as v1.0.0-alpha.
