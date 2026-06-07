# M101 to M102 Boundary

M101 implements Mobile Sensor Contract Review only. It defines contract-only
sensor capability classes, permission-state contracts, sensor risk
classification, consent, revocation, and audit requirements.

M102 remains future as Location Sensor, Off by Default.

M101 must not implement M102 behavior. In particular, M101 adds no runtime
sensor access, no location sensor runtime, no native permission prompt, no
background collection, no raw sensor payload, no backend route, no dependency,
no memory write, no context injection, no execution, and no production
authority.
