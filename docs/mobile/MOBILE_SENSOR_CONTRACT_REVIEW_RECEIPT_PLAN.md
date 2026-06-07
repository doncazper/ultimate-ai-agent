# M101 Mobile Sensor Contract Review Receipt Plan

M101 receipt planning is redacted and safe-summary-only.

Allowed receipt metadata:

- sensor contract refs
- permission-state refs
- risk classification refs
- consent and revocation requirement refs
- audit requirement refs
- no-effect reason codes

Denied receipt content:

- raw sensor payload
- location coordinates
- image, photo, microphone, motion, Bluetooth, NFC, biometric, clipboard, or
  local-network payloads
- native permission prompt output
- background collection data
- secrets or credentials

The receipt plan records no side effects. It grants no sensor access, memory
write, context injection, execution, backend route, dependency, or production
authority.
