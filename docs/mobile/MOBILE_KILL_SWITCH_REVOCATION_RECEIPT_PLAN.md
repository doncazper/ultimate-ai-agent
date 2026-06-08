# Mobile Kill Switch + Revocation Receipt Plan

M108 receipt plans store safe refs and safe summaries only.

Receipt metadata may include:

- source M107 approval renewal UX report ref
- source baseline ref
- actor-bound ref
- device-bound ref
- approval-bound ref
- revocation-bound ref
- safe revocation refs
- safe kill switch refs
- safe revocation reason refs
- safe kill switch reason refs
- audit ref
- replay ref

Receipts store no raw approval payload, no device token, no external-service
payload, no network sync result, no notification delivery evidence, no push
trigger evidence, no background worker output, no scheduler output, no daemon
output, no memory write, no context injection, no execution output, no backend
route result, no Control Center control result, and no production authority
evidence.

M109 remains future.
