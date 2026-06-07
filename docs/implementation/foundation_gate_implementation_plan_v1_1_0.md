# Foundation Gate Implementation Plan v1.1.0

v1.1.0 extends the Foundation Gate for M97 Recurring Automation Contracts.

The gate checks:

- recurring automation contract module exists
- policy is disabled by default and contract-only
- approval renewal required
- expiration required
- stop conditions required
- audit and revocation required
- receipt plans store safe refs only
- evaluator boundaries revalidate model-copy-mutated fields
- no recurrence runtime
- no background execution
- no cron
- no daemon
- no scheduler
- no side effects
- no backend route
- no dependency
- no production authority
- M98 remains future

M97 adds no runtime recurring automation and no production authority.

## Skill Package Security Rule

All skills are untrusted packages by default.

Skill and plugin review requires a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities before any future enablement can
be considered.

M97 does not enable skills, plugins, recurrence runtime, background execution,
cron, daemon, scheduler, backend routes, dependency changes, or production
authority.
