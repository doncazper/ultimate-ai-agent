# Foundation Gate Implementation Plan v0.29.0

Status: Active for v0.29.0 / M25.

## Scope

v0.29.0 adds Foundation Gate criteria for M25 Truth Source Router + Evidence
Claim Checker.

## Gate Criteria

- M25 truth/evidence contract files exist.
- Default truth manifest disables external verification, web search, model
  verification, memory-as-authority, and automatic claim verification.
- Source priority ordering is deterministic.
- Memory-only verification is denied.
- Model/runtime/OpenWebUI output verification is denied.
- Arbitrary refs and claim self-verification are rejected.
- Stale, conflicted, revoked, deleted, or superseded sources are denied for
  verified status.
- Primary-source-backed evidence can support verified status.
- Raw content and secret-like content are rejected.
- No web/model/provider calls are added.
- No memory writes are added.
- No backend truth verification/search/model routes are added.
- OpenAPI path count remains `74`.
- M26 remains planned/provisional and future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before use.

M25 does not enable skill packages, plugins, runtime tools, package installers,
or external execution.
