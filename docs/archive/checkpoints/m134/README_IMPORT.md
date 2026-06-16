# M134 Archive Import Notes

Checkpoint M134 - Human Checkpoint Scheduling is imported as a local,
contract-only, review-only, deterministic, safe-ref-only checkpoint under the
v1.7.2 product baseline.

The archive preserves safe refs for Mode 5, M133 supervisor decision, M132
trusted workflow decision, checkpoint plan, schedule plan, checkpoint window,
reviewer ref, consent, expiration, reminder plan, escalation plan, pause
condition, stop condition, risk decision, audit, replay, revocation,
kill-switch, and no-effect receipt.

The archive imports no scheduler, prompt runtime, notification delivery,
reminder runtime, calendar write, approval capture, escalation runtime,
supervisor runtime, recovery execution, backend route, Control Center control,
dependency, beta release, or production authority.
