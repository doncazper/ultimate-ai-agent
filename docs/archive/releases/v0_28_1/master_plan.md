Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.28.1

## Active Baseline

v0.28.1 is the M24 Contract Repair + Memory Safety Hardening release.

## M24 Repair Scope

v0.28.1 keeps M24 as a governed local memory provider/store foundation. It
repairs the public memory request contract so package-root `MemoryWriteRequest`
matches the provider/store write path, while the legacy content-bearing request
model remains explicit as `LegacyMemoryWriteRequest`.

It hardens M24 guard-field tests, clarifies that `source_refs` are required for
local-store writes, returns defensive copies from the in-memory store, and
updates route inventory and release documentation through v0.28.1.

## Safety Boundary

Memory remains recall, not authority. Memory is not ground truth. Canonical
files, evidence manifests, receipts, Event Ledger records, and user-reviewed
sources outrank memory.

v0.28.1 does not add automatic memory writes, model-output writes, local LLM
output writes, OpenWebUI chat memory writes, Control Center memory mutation,
mobile capture writes, tool output writes, cloud memory providers, vector DB,
embeddings, semantic search, RAG ingestion, raw session history, context
injection, backend mutation routes, dependencies, production persistence, broad
filesystem scanning, runtime execution, remote execution, or M25 truth/claim
verification.

## Next Milestone

M25 remains future as Truth Source Router + Evidence Claim Checker.
