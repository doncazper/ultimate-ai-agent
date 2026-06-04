# Foundation Gate Implementation Plan v0.38.1

Status: historical Foundation Gate plan superseded by v0.38.2.

v0.38.1 hardens M34 Broader File Capability Review boundary clarity in
documentation, static verification, and Foundation Gate checks only.

## Gate Coverage

Foundation Gate must cover:

- M34 broader file capability review docs exist.
- M34 is implemented/released as planning/docs/verifier-only work by v0.38.0.
- Active README docs do not list v0.38.0 / M34 as planned/provisional.
- Active M33 redacted-preview docs do not say M34 remains planned/provisional
  after v0.38.0.
- M34 does not implement Safe File Review Workflow Contracts.
- M34 does not implement File Review Control Center Surface.
- M34 does not implement review approval capture or approval persistence.
- M34 does not implement context proposal or context injection.
- M34 does not implement raw file access, memory writes, export, execution, or
  runtime file authority.
- OpenAPI path count remains `74`.
- M35 remains planned/provisional.
- M36 remains planned/provisional.

## Blocked Drift

Gate must fail if active docs imply stale M34 currentness, M35 implementation,
file review UI implementation, approval persistence, raw file/context/memory/tool
execution routes, route count changes, or M35 implemented/released status.

## No New Authority

v0.38.1 adds no runtime file capability, raw file reads, full-file reads,
unredacted preview, file review workflow, review approval capture, context
proposal, context injection, memory writes, export, execution, backend routes,
frontend runtime features, dependencies, M35 implementation, or production
authority.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package requires
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be trusted by a runtime boundary.
