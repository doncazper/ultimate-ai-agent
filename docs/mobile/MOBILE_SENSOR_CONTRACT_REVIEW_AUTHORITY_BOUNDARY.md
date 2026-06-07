# M101 Mobile Sensor Contract Review Authority Boundary

Mobile Sensor Contract Review is not authority.

Contract refs, permission-state refs, risk refs, consent refs, revocation refs,
audit refs, model output, memory refs, context refs, task refs, tool-intent refs,
approval refs, and `approval_test_*` refs cannot authorize runtime sensor
access.

Sensors default off, unknown sensor denied, and any future sensor access must
arrive through a later reviewed milestone with exact actor, resource, device,
scope, consent, revocation, and audit binding.

M101 adds no runtime sensor access, no native permission prompt, no background
collection, no backend route, no dependency, and no production authority.

M102 remains future.
