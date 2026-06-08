# Mobile Sensor Audit Ledger Policy

M109 policy requires contract-only, review-only, safe refs, actor-bound,
device-bound, sensor-scope-bound, audit, and replay fields.

The policy denies sensor access, sensor read, raw sensor payload, location
access, camera access, photos access, microphone access, background collection,
notification delivery, push trigger, background worker, scheduler, daemon,
device token handling, external service, network sync, raw audit payload,
dependency, memory write, context injection, execution, backend route, Control
Center control, native mobile UI, and production authority.

Evaluator boundaries revalidate current object fields, including model-copy
mutations. M110 remains future.
