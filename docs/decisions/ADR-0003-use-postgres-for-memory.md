# ADR-0003: Use Postgres as Canonical Memory Store

Status: Accepted; expanded in v0.4.9

## Decision

Use Postgres as the canonical memory store for MVP, with optional pgvector/full-text indexing. Do not start with multiple SQL databases.

## Rationale

The memory system needs structured fields, source references, permissions, temporal validity, supersession, export/delete, joins, and auditability. Postgres provides a stable source of truth while retrieval indexes can be derived from it.
