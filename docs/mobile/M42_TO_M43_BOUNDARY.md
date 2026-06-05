# M42 to M43 Boundary

Status: Active boundary for v0.46.0 / M42.

M42 implements Mobile Companion Product Contract Refresh. It is a contract,
documentation, verifier, and Foundation Gate milestone only. It does not add a
mobile API boundary, backend routes, frontend mobile controls, native clients,
approval capture, approval persistence, sensors, OS permissions, signing,
TestFlight, App Store, Play Store, background services, notification runtime,
device pairing runtime, or production authority.

M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only. M43
must not use M42 product planning as runtime authority. The M43 API boundary
remains read-only, redacted, route-reviewed, non-mutating, and
non-authoritative unless a later reviewed roadmap patch explicitly changes that
scope.

Blocked through M43 unless a future reviewed milestone says otherwise:

- no mobile mutation.
- no approval execution.
- no approval_ref as authority.
- no approval_test_ runtime authority.
- no mobile sensor access.
- no OS permission integration.
- no background collection.
- no raw data or raw payload exposure.
- no credentials/cookie handling.
- no memory writes.
- no context injection.
- no file mutation.
- no tool/action/task execution.
- no production authority.

M44 remains future after M43 and is limited to CCC iOS Skeleton, No Authority.
