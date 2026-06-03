# Foundation Gate Implementation Plan v0.28.0

Status: Active M24 gate plan.

## Scope

v0.28.0 adds Foundation Gate coverage for M24 Memory Provider Abstraction + Local Memory Store.

## Gate Criteria

- Memory provider modules and M24 docs exist.
- Default memory manifest is local/dev only.
- Memory is recall, not authority.
- Memory is not ground truth.
- Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.
- Reviewed safe write is allowed for local store.
- Unreviewed write is rejected.
- Automatic writes, model-output writes, local LLM output writes, OpenWebUI chat memory writes, mobile capture writes, and tool output writes are rejected.
- Secret-like content, raw prompts, raw model output, raw file content, raw transcripts, and raw export are rejected.
- Cloud providers, vector DB, embeddings, context injection, background workers, production persistence, and backend mutation routes remain absent.
- OpenAPI path count remains `74`.
- M25 remains future.

## Non-Goals

This plan adds no runtime execution, model/provider call, tool execution, remote execution, mobile sensor access, plugin enablement, dependency, backend mutation route, context injection, or M25 claim verification.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before use.

M24 does not enable skill packages, plugins, runtime tools, package installers,
or external execution.
