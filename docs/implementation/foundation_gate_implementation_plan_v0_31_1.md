# Foundation Gate Implementation Plan v0.31.1

Status: active
Current through: v0.31.1
Purpose: Foundation Gate and verifier alignment for README polish baseline normalization.

## Scope

v0.31.1 is a docs-only normalization release. It keeps the v0.31.0 M27 Tool
Broker v2 Foundation Gate criteria intact and updates active release metadata so
the repository has a clean tagged v0.31.x baseline before M28.

Foundation Gate must continue to verify:

- M27 Tool Broker v2 contracts remain validation-only and preview-only.
- no tool execution, action execution, backend execution route, file mutation,
  memory write, network call, browser automation, plugin enablement,
  model/provider call, context injection, dependency, or production authority is
  introduced.
- OpenAPI path count remains `74`.
- M28-M40 remain planned/provisional.

## Non-Goals

v0.31.1 does not implement Approval Authority v2, Action Policy Expansion, M28,
or any new runtime behavior.

## Skill Package Security Rule

All skills are untrusted packages by default. Future skill packages still need a manifest,
declared permissions, source/provenance metadata, static review, sandbox test execution,
Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities before use.

v0.31.1 does not enable MCP runtime, Agent Skills runtime, AGENTS.md runtime
loading, plugin enablement, tool execution, action execution, browser
automation, or production authority.
