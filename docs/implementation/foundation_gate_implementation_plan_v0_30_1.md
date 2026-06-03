# Foundation Gate Implementation Plan v0.30.1

Status: active
Current through: v0.30.1
Purpose: M26 recall source identity hardening Foundation Gate criteria and verifier plan.

## M26 Criteria

Foundation Gate must verify:

- Grounded Recall Router contracts exist.
- Evidence-Linked Context Pack Builder contracts exist.
- default manifest disables context injection, vector search, embeddings,
  semantic search, external retrieval, web search, source crawling, automatic
  memory writes, backend routes, model/provider calls, tool execution, and
  production authority.
- source priority keeps source-backed refs above memory.
- source_ref/source_kind consistency is enforced.
- caller-declared source_kind cannot upgrade memory/model/runtime/OpenWebUI refs.
- unknown/arbitrary refs are excluded.
- stale/conflicted/revoked/deleted/superseded candidates are excluded by
  default.
- model/runtime/OpenWebUI output is excluded.
- context packs include safe summaries and refs only.
- no backend recall/context-pack route drift.
- M27 remains planned/provisional.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before use.

Skill packages and plugin/tool capabilities remain governed by existing
Foundation Gate and documentation-integrity checks. M26 does not enable plugins,
MCP runtime, Agent Skills runtime, AGENTS.md runtime loading, tool execution, or
production authority.
