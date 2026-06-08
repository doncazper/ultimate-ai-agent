# Mobile Sensor Audit Ledger Receipt Plan

M109 receipt plans store safe refs only:

- ledger ref
- source Mobile Kill Switch + Revocation record ref
- source baseline ref
- actor ref
- safe device ref
- safe sensor scope ref
- safe sensor audit entry refs
- audit ref
- replay ref
- safe summary

Receipt plans store no raw sensor payload, no location data, no camera data, no
photos data, no microphone data, no background collection output, no device
token, no notification payload, no network sync output, no raw audit payload, no
memory write, no context injection, no execution result, no backend route
result, no Control Center control result, no dependency evidence, and no
production authority evidence.

M110 remains future.
