# Foundation Gate Implementation Plan v1.3.0

v1.3.0 adds M99 Foundation Gate coverage for Autonomy v1 Safety Freeze.

Gate coverage:
- M99 Autonomy v1 Safety Freeze contracts exist.
- Reports are freeze-only and review-only.
- Reports require M61-M98 coverage, no broad unsandboxed autonomy, no global
  autonomy switch, and no production authority.
- Evaluator boundaries revalidate model-copy-mutated request, policy, and
  report fields.
- Static safety checks deny shell execution, browser action, network mutation,
  plugin execution, scheduler, background worker, mobile sensor, memory write,
  context injection, raw prompt/provider payload exposure, raw file export,
  full-file read, backend route, dependency, broad autonomy, and production
  authority drift.
- Route checks verify no autonomy escape routes were added.
- Roadmap currentness marks M99 implemented/released and keeps M100
  planned/provisional.

M100 remains future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must
provide a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be considered for enablement.
