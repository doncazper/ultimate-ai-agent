# Notification Planning Authority Boundary

M104 notification plans are non-authoritative records. They describe future
notification candidates for review, but they do not grant runtime authority.

The boundary is strict:

- no push delivery.
- no notification permission prompt.
- no notification scheduling.
- no background task execution.
- no device token handling.
- no external push provider.
- no raw notification body.
- no backend route.
- no Control Center control.
- no dependency.
- no memory write.
- no context injection.
- no execution.
- no production authority.

Safe notification plan refs, consent refs, revocation refs, audit refs, task
plans, context packs, memory refs, model refs, runtime refs, and approval refs
are not authority to send, schedule, or display notifications.

M105 remains future and must not be inferred from M104.
