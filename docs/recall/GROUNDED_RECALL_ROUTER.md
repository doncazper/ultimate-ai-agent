# Grounded Recall Router

Status: active
Current through: v0.32.0
Purpose: Define the M26 deterministic recall router contract.

M26 adds a local Grounded Recall Router over caller-provided candidate refs only.
It does not discover sources, crawl files, search the web, call models, or query
external systems.

The router:

- ranks canonical documents, evidence manifests, receipts, Event Ledger records,
  and user-reviewed sources above memory.
- enforces source_ref/source_kind consistency before ranking or selection.
- rejects caller-declared source_kind upgrades for memory, model, runtime, and
  OpenWebUI refs.
- treats memory as recall context only, not truth authority.
- excludes unknown, arbitrary, unstructured, stale, conflicted, revoked, deleted,
  superseded, model-output, runtime-output, OpenWebUI-output, raw, or
  secret-like candidates by default.
- returns safe summaries and refs only.
- records that no memory write, external retrieval, vector search, or context
  injection was performed.

M26 adds no backend recall route, Control Center execution control, context
injection runtime, vector search, embedding runtime, model/provider call, tool
execution, memory write, dependency, or production authority.
