# Foundation Gate Implementation Plan - v0.46.0

Status: Current active Foundation Gate plan for v0.46.0.

v0.46.0 implements M42 Mobile Companion Product Contract Refresh. Foundation
Gate coverage must prove the refresh is contract-only, route-free,
native-free, sensor-free, and non-authoritative.

## M42 Criteria

- M42 mobile product refresh contracts exist.
- Default M42 refresh is contract_refresh_only.
- Product surfaces remain review-only and read-only.
- M43 read-only API boundary remains future.
- M44 iOS skeleton remains future.
- Native app, mobile API, sensor access, OS permission integration, background
  service, signing/store workflow, approval capture, approval execution, memory
  write, context injection, raw payload exposure, and production authority flags
  are denied, including model_copy-mutated objects.
- No backend route drift.
- No mobile/native implementation files or dependencies.
- Active roadmap marks M42 implemented/released and M43-M60
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

M42 does not enable skills, plugins, mobile sensors, native builds, or
execution authority.
