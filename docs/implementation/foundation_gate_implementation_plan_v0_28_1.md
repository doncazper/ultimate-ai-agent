# Foundation Gate Implementation Plan v0.28.1

Status: Active M24 repair gate plan.

## Scope

v0.28.1 hardens Foundation Gate coverage for M24 Contract Repair + Memory Safety
Hardening.

## Gate Criteria

- Package-root `MemoryWriteRequest` resolves to the M24 provider/store write
  request.
- Legacy content-bearing write request usage remains explicit and separate.
- Local memory writes remain reviewed, source-linked, redacted-summary-only, and
  local/dev-only.
- Required M24 guard fields exist before mutation-denial checks run.
- Automatic writes, model-output writes, local LLM output writes, OpenWebUI chat
  memory writes, mobile capture writes, and tool output writes are rejected.
- Secret-like content, raw prompts, raw model output, raw file content, raw
  transcripts, and raw export are rejected.
- In-memory local store reads return defensive copies.
- OpenAPI path count remains `74`.
- M25 remains future.

## Non-Goals

This plan adds no runtime execution, model/provider call, tool execution, remote
execution, mobile sensor access, plugin enablement, dependency, backend mutation
route, context injection, automatic memory write, vector DB, embeddings, cloud
memory provider, or M25 claim verification.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities before use.

v0.28.1 does not enable skill packages, plugins, runtime tools, package
installers, or external execution.
