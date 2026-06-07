# M101 Mobile Sensor Contract Review

M101 implements Mobile Sensor Contract Review as contract-only governance. It
defines sensor capability classes, permission-state contracts, sensor risk
classification, consent, revocation, and audit requirements before any sensor
runtime exists.

Sensors default off. Unknown sensor classes are denied. The review report is
safe-summary-only and non-authoritative.

There is no background collection.

M101 adds no runtime sensor access, no native permission prompt, no background
collection, no raw sensor payload, no backend route, no Control Center control,
no dependency, no memory write, no context injection, no execution, and no
production authority.

M102 remains future.
