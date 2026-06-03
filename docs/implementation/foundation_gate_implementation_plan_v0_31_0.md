# Foundation Gate Implementation Plan v0.31.0

Status: active
Current through: v0.31.0
Purpose: M27 Tool Broker v2 Foundation Gate criteria and verifier plan.

## M27 Criteria

Foundation Gate must verify:

- Tool Broker v2 contracts exist.
- default manifest disables tool execution, backend routes, shell execution,
  file mutation, network calls, browser automation, plugin enablement, memory
  writes, Event Ledger mutation, model/provider calls, context-pack authority,
  context injection, and production authority.
- safe metadata-only tool intent previews can be allowed without execution.
- unknown tools are denied.
- target ref/kind mismatches are denied.
- unknown target refs are denied.
- side-effecting intents are denied.
- approval_ref is not authority.
- context packs are not authority.
- caller-declared risk cannot downgrade catalog risk.
- declared no-side-effect metadata cannot hide catalog side effects.
- raw, secret-like, model-output, runtime-output, and OpenWebUI-output inputs
  are rejected.
- no backend tool execution route drift.
- M28-M40 remain planned/provisional.

## Skill Package Security Rule

All skills are untrusted packages by default. Future skill packages still need a manifest,
declared permissions, source/provenance metadata, static review, sandbox test execution,
Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support,
and human approval for high-risk capabilities before use.

M27 does not enable MCP runtime, Agent Skills runtime, AGENTS.md runtime
loading, plugin enablement, tool execution, browser automation, or production
authority.
