# Human Checkpoint Scheduling Receipt Plan

M134 receipt plans are no-effect receipt plans. They store safe summaries and
safe refs only.

Required receipt bindings:

- checkpoint schedule ref
- exact scope ref
- M133 supervisor decision ref
- M132 trusted workflow decision ref
- checkpoint plan ref
- schedule plan ref
- checkpoint window ref
- consent ref
- expiration ref
- reminder plan ref
- escalation plan ref
- audit ref
- replay ref
- revocation ref
- kill-switch ref

The receipt must not store raw prompts, raw provider payloads, secrets, raw
private content, or raw notification bodies. It must also record no checkpoint
scheduled state, no scheduling, no prompt, no notification delivery, no calendar
write, no approval capture, no escalation runtime, no execution, no tool
execution, no shell execution, no network access, no browser automation, no
plugin execution, no connector runtime, no model call, no memory write, no
context injection, no backend route, no Control Center control, no dependency,
no beta release, and no production authority.
