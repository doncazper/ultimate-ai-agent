# ADR-0004: Use a Memory Service API

Status: Accepted; expanded in v0.4.9

## Decision

Agents do not write directly to memory tables. All reads, writes, updates, supersessions, deletes, exports, and reflection jobs go through the Memory Service API.

## Rationale

This keeps memory scoped, permissioned, deduplicated, source-backed, and auditable.
