# M101 Mobile Sensor Contract Review Policy

The M101 policy requires:

- sensor capability classes
- permission-state contract records
- sensor risk classification
- consent and revocation requirements
- audit requirements
- sensors default off
- unknown sensor denied

The policy denies runtime sensor access, native permission prompt, background
collection, raw sensor payload, backend route, dependency, memory write, context
injection, execution, and production authority.

M101 is contract-only. It does not request OS permissions, read device sensors,
collect in the background, or implement M102.
