# Foundation Gate Implementation Plan - v0.47.0

Status: Current active Foundation Gate plan for v0.47.0.

v0.47.0 implements M43 Mobile API Boundary, Read-Only. Foundation Gate coverage
must prove the boundary is contract-only, read-only, redacted summary only,
route-stable, sensor-free, raw-data-free, mutation-free, and non-authoritative.

## M43 Criteria

- M43 mobile API boundary contracts exist.
- Default M43 boundary is contract-only and read-only.
- Planned endpoint refs are GET-only and redacted summary only.
- Endpoint refs are metadata refs, not callable routes.
- Backend routes are not added.
- Mobile mutation, approval capture, approval execution, sensor access,
  credential handling, cookie handling, raw data, raw payload exposure, raw
  absolute path exposure, context injection, memory write, export, execution,
  background collection, and production authority flags are denied, including
  model_copy-mutated objects.
- No OpenAPI route drift from the accepted 75-path boundary.
- No native mobile implementation files or dependencies.
- Active roadmap marks M43 implemented/released and M44-M60
  planned/provisional.

## Skill Package Security Rule

All skills are untrusted packages by default. A skill package requires:

- a manifest.
- declared permissions.
- source/provenance metadata.
- static review.
- sandbox test execution.
- Tool Broker permission mapping.
- Event Ledger logging.
- version pinning.
- revocation/disable support.
- human approval for high-risk capabilities.

These checks are required before any future runtime use.

M43 does not enable skills, plugins, mobile sensors, native builds, mobile
runtime routes, or execution authority.
