# Foundation Gate Implementation Plan v0.29.2

Status: historical implementation plan for v0.29.2 / M25 hardening.

## Scope

v0.29.2 strengthens Foundation Gate coverage for local-dev API authority and
raw preview safety. It keeps M25 deterministic, local, contract-only, and
validation-only over provided refs.

## Gate Criteria

- M25 truth/evidence contract checks remain active.
- Default truth manifest disables external verification, web search, model
  verification, memory-as-authority, and automatic claim verification.
- Memory-only verification remains denied.
- Model/runtime/OpenWebUI output verification remains denied.
- Arbitrary, unknown, and claim self-verifying refs remain rejected.
- Public `/kernel/tasks/run` local-dev mutation requests are dry-run-only.
- Core Tool Broker/kernel mutation paths reject test-prefixed approval refs
  unless they are backed by explicit local approval authority.
- Public file read preview responses are metadata-only by default and mark raw
  content omitted.
- Secret-like file preview refs are rejected without raw echo.
- API handlers do not use raw exception strings as safe messages or details.
- OpenAPI path count remains `74`.
- No backend truth verification/search/model routes are added.
- M26 remains planned/provisional and future.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before use.

v0.29.2 does not enable skill packages, plugins, runtime tools, package
installers, external execution, or M26 context-pack behavior.
