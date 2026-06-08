# Background Task Contract No Execution Policy

M105 policy requires contract-only, planning-only, safe refs, safe task
summaries, safe cadence refs, consent, revocation, and audit.

Policy validation denies:

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

Evaluator boundaries revalidate model-copy-mutated fields and reject unsafe or
secret-like metadata. M106 remains future.
