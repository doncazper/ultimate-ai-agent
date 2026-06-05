# Foundation Gate Implementation Plan v0.53.0

v0.53.0 adds Foundation Gate coverage for M49 Mobile Review Approval Capture.

## Skill Package Security Rule

All skills are untrusted packages by default.

Before a skill package can influence execution, the system must require a
manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk
capabilities.

The rule requires a manifest and human approval for high-risk capabilities.

v0.53.0 does not enable skills, plugins, mobile sensors, native approval
capture UI, backend mobile approval routes, execution, export, memory writes,
context injection, or production authority.

Gate coverage:

- M49 mobile review approval capture contracts exist and validate.
- Safe approval capture is exact-scope, actor-bound, resource-bound,
  replay-safe, revocable, review-only, and safe refs only.
- Approval capture binds approval, actor, mobile surface, review packet,
  preview result, redaction summary, file ref, safe path ref, idempotency key,
  and receipt plan refs.
- model_copy-mutated raw file access, raw content, full-file content,
  unredacted preview, context proposal, context injection, memory write,
  export, execution, approval execution, mobile sensor access, and background
  collection flags are denied.
- `approval_test_` refs are denied.
- OpenAPI remains at 75 paths and adds no mobile approval, context, memory,
  export, sensor, background, or tool execution route.
- Active roadmap docs mark M49 implemented/released and keep M50-M60
  planned/provisional.

v0.53.0 adds no raw file access, raw content, full-file content, unredacted
preview, raw absolute path storage, context proposal, context injection, memory
write, export, execution, mobile sensor access, background collection, backend
mobile approval route, native approval capture UI, dependency, production
authority, or M50 implementation.
