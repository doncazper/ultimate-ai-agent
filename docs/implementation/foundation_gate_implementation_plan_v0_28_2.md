# Foundation Gate Implementation Plan v0.28.2

Status: Active docs-only cleanup gate plan.

## Scope

v0.28.2 is a documentation-only cleanup after the accepted stable v0.28.1 M24
baseline. It removes a duplicate/conflicting planned/provisional v0.28.1
roadmap row and keeps the correct implemented v0.28.1 M24 hardening row.

## Gate Criteria

- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md` has only one v0.28.1 row.
- The retained v0.28.1 row marks M24 Contract Repair + Memory Safety Hardening
  as implemented/released.
- v0.28.2 adds no code behavior change, test change, dependency, backend route,
  OpenAPI path count change, runtime/model/provider behavior, memory authority,
  or M25 work.
- OpenAPI path count remains `74`.

## Non-Goals

This plan adds no runtime execution, model/provider call, tool execution, remote
execution, mobile sensor access, plugin enablement, dependency, backend mutation
route, context injection, automatic memory write, vector DB, embeddings, cloud
memory provider, production persistence, or M25 claim verification.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before use.

v0.28.2 does not enable skill packages, plugins, runtime tools, package
installers, or external execution.
