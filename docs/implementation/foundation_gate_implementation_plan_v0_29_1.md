# Foundation Gate Implementation Plan v0.29.1

Status: Historical for v0.29.1 / M25 hardening.

## Scope

v0.29.1 hardens Foundation Gate coverage for M25 Truth Source Router +
Evidence Claim Checker unknown/arbitrary ref denial.

## Gate Criteria

- M25 truth/evidence contract files exist.
- Default truth manifest disables external verification, web search, model
  verification, memory-as-authority, and automatic claim verification.
- Source priority ordering is deterministic.
- Memory-only verification is denied.
- Model/runtime/OpenWebUI output verification is denied.
- Arbitrary, unknown, and claim self-verifying refs are rejected.
- Explicit `TruthSourceKind.unknown` evidence cannot support
  `evidence_supported` or `verified_by_primary_source`.
- Inferred unknown refs such as unrecognized prefixes cannot verify truth.
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
