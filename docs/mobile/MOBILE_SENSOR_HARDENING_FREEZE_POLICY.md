# Mobile Sensor Hardening Freeze Policy

Status: Checkpoint M110 policy.

The Mobile Sensor Hardening Freeze policy is contract-only, review-only, and
freeze-only. It requires safe refs, actor-bound records, device-bound records,
sensor-scope-bound records, audit refs, replay refs, hardening checklist refs,
accepted checkpoint refs, and a no-effect receipt plan.

The default policy keeps every runtime authority disabled: no hardening runtime,
no sensor access, no sensor read, no raw sensor payload, no location access, no
camera access, no photos access, no microphone access, no background
collection, no native mobile UI, no notification delivery, no push trigger, no
background worker, no scheduler, no daemon, no device token handling, no
external service, no network sync, no raw audit payload, no backend route, no
Control Center control, no dependency, no memory write, no context injection, no
execution, no broad autonomy, no mobile sensor runtime, and no production
authority.

Any model_copy mutation or constructor input that tries to enable those fields
must be denied during evaluator revalidation. M110 remains a safe checkpoint
over M109, and M111 remains future.
