# Mobile Background Read-Only Status Sync Receipt Plan

M106 receipt plans store safe refs only.

Allowed receipt fields:
- report ref
- baseline ref
- actor ref
- M105 background task plan refs
- safe device refs
- safe status refs
- safe status summary refs
- safe observed-at refs
- audit refs
- no-effect reason codes

Receipts store no raw status payload, no raw mobile data, no device token, no
push payload, no network response, no background execution evidence, no
background worker PID, no scheduler state, no memory write, no context
injection, no execution output, and no production authority evidence.
