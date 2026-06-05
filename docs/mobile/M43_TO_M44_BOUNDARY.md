# M43 to M44 Boundary

Status: Active boundary for v0.47.0 / M43.

M43 implements Mobile API Boundary, Read-Only as contract-only work. It defines
planned endpoint refs and validation rules for future mobile clients. It does
not add a mobile app, iOS app, Android app, native package, backend route,
mobile API route runtime, approval capture, approval execution, mobile sensor
access, OS permission integration, background collection, raw data, raw payload
exposure, raw absolute path exposure, credential handling, cookie handling,
context injection, memory write, export, execution, or production authority.

M43 endpoint refs are non-authoritative metadata. They may describe future
read-only, redacted summary only surfaces, but they cannot be used as callable
routes, approval authority, tool authority, context authority, memory authority,
or execution authority.

Blocked through M44 unless a future reviewed milestone says otherwise:

- no mobile mutation.
- no approval execution.
- no approval_ref as authority.
- no approval_test_ runtime authority.
- no mobile sensor access.
- no OS permission integration.
- no background collection.
- no raw data.
- no raw payload exposure.
- no raw absolute path.
- no credential handling.
- no cookie handling.
- no context injection.
- no memory write.
- no export.
- no execution.
- no file mutation.
- no tool/action/task execution.
- no production authority.

M44 remains future after M43 and is limited to CCC iOS Skeleton, No Authority.
M44 may introduce a skeleton client only after a dedicated reviewed milestone;
it must not inherit mobile API endpoint refs as runtime authority.
