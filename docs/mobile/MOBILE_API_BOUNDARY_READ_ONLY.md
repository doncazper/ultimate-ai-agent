# Mobile API Boundary, Read-Only

Status: Current M43 mobile API boundary contract for v0.47.0.

v0.47.0 / M43 implements Mobile API Boundary, Read-Only as contract-only,
documentation, verifier, and Foundation Gate work. It defines planned endpoint
refs for future mobile clients, but it adds no backend route and no mobile API
route runtime.

The M43 boundary is read-only and redacted summary only. Planned endpoint refs
may describe future manifest summaries, approval-status summaries, receipt
summaries, review-packet summaries, and device-status summaries. They are
metadata refs, not callable routes, not authority, and not execution permission.

M43 boundary rules:

- contract-only.
- read-only.
- redacted summary only.
- planned endpoint refs only.
- no backend route.
- no mobile API route runtime.
- no mobile mutation.
- no approval capture.
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
- no network/provider/model call.
- no browser automation execution.
- no remote execution.
- no plugin enablement.
- no production authority.

Python Agent Core remains the authority boundary. Mobile clients are future
governance/control surfaces; they are not the agent brain, not truth authority,
and not execution authority. Model output, runtime output, memory refs, context
pack refs, tool-intent refs, task-plan refs, and approval refs cannot authorize
mobile API behavior.

M44 remains future and is limited to CCC iOS Skeleton, No Authority.
