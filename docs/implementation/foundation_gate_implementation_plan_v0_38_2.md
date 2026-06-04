# Foundation Gate Implementation Plan v0.38.2

Status: active Foundation Gate plan for v0.38.2.

v0.38.2 repairs M34 current-baseline labels and documentation-integrity
coverage after the v0.38.1 Yellow review. It is docs, verifier, Foundation
Gate, and release metadata work only.

## Gate Coverage

Foundation Gate must cover:

- active docs identify v0.38.2 as the current active baseline.
- active docs do not claim v0.38.0 or v0.38.1 as the current active baseline.
- v0.38.0 remains the historical M34 Broader File Capability Review
  implementation release.
- v0.38.1 remains a superseded M34 hardening release.
- documentation integrity fails when active current-baseline labels drift from
  the version files.
- M34 remains implemented/released as planning/docs/verifier-only work.
- M35 remains planned/provisional.
- M36-M60 remain planned/provisional.
- OpenAPI path count remains `74`.
- no backend raw-file, review, context, memory, or execute routes are added.

## Blocked Drift

Gate must fail if active docs imply stale current-baseline status, M35
implementation, file review UI implementation, approval persistence, raw
file/context/memory/tool execution routes, route count changes, or production
authority.

## No New Authority

v0.38.2 adds no runtime file capability, raw file reads, full-file reads,
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
