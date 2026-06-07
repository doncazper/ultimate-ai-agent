# Foundation Gate Implementation Plan v1.2.0

v1.2.0 adds M98 Foundation Gate coverage for Scoped Recurring Low-Risk
Automation.

Gate coverage:
- M98 scoped recurring low-risk automation contracts exist.
- Decisions require low-risk read-only scope, strict cadence, approval renewal
  required, renewal expiry, stop conditions required, audit trail, revocation,
  kill switch, safe refs only, and no secret access.
- Evaluator boundaries revalidate model-copy-mutated request, decision, and
  receipt-plan fields.
- Static safety checks deny scheduler, background worker, recurring execution
  runtime, mutating tasks, credential or account actions, shell write, network
  write, browser write, silent background collection, memory write, context
  injection, export, backend route, dependency, and production authority drift.
- Route checks verify no recurring automation runtime routes were added.
- Roadmap currentness marks M98 implemented/released and keeps M99-M100
  planned/provisional.

M99 remains future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must
provide a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be considered for enablement.
