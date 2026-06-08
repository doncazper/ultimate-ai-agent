# Background Task Contract Receipt Plan

M105 receipt plans store safe refs only:

- background task plan ref
- safe device ref
- safe task summary ref
- safe cadence ref
- safe purpose ref
- consent ref
- revocation ref
- audit ref
- no-effect reason codes

Receipt plans store no background worker output, no scheduler output, no daemon
state, no OS permission prompt state, no push trigger evidence, no device token,
no external service payload, no raw task payload, no memory write, no context
injection, no execution output, and no production authority.

M106 remains future.
