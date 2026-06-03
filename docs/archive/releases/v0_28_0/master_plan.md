Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.28.0

## Active Baseline

v0.28.0 is the M24 Memory Provider Abstraction + Local Memory Store release.

## M24 Scope

M24 adds a governed `MemoryProvider` abstraction, local-only memory record contracts, a local in-memory/dev store, explicit-path stdlib SQLite support, reviewed-write validation, source priority, provenance, trust/confidence metadata, retention/delete/export contracts, conflict/staleness metadata, dedup/decay/archive planning metadata, and recall-planning metadata.

Memory is recall, not authority. Memory is not ground truth. Canonical files, evidence manifests, receipts, Event Ledger records, and user-reviewed sources outrank memory.

## Safety Boundary

M24 does not add automatic memory writes, model-output writes, local LLM output writes, OpenWebUI chat memory writes, Control Center memory mutation, mobile capture writes, tool output writes, cloud memory providers, vector DB, embeddings, semantic search, RAG ingestion, raw session history, context injection, backend mutation routes, dependencies, production persistence, broad filesystem scanning, runtime execution, remote execution, or M25 truth/claim verification.

## Next Milestone

v0.28.1 should be Memory Safety Hardening. M25 remains future as Truth Source Router + Evidence Claim Checker.
