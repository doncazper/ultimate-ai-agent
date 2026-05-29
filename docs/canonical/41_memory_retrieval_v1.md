# 41 — Memory Retrieval V1

Status: M4 foundation spec, v0.5.3
Owner: Memory / Retrieval

## Purpose

Memory V1 must define not only where memories live, but how they are retrieved, ranked, filtered, and protected from poisoning.

## Retrieval stack

```text
Postgres: canonical structured memory store
pgvector: semantic embeddings in the same database
Postgres full-text search: keyword/BM25-style matching
Metadata filters: scope, project, entity, type, status, sensitivity
Reranker: model or deterministic scoring layer for final ordering
Context Pack Builder: token-budgeted memory injection
```

## Memory chunking

```text
Atomic structured memories: one record per decision/preference/constraint/event.
Long artifacts: chunk by heading/section with source path and byte/line refs.
Conversations: summarize into candidate memories; do not dump raw transcript as primary memory.
Provider/news/email results: store normalized summaries and source refs, not raw private content by default.
```

## Ranking factors

```text
semantic similarity
keyword match
source authority
scope match
recency
confidence/trust score
status active vs superseded
canonical-file linkage
sensitivity/access policy
user/project relevance
```

## Poisoning defenses

```text
External content cannot create high-confidence memory without classification.
Memories from untrusted sources are marked as observations, not facts.
Canonical files outrank memory.
Conflicting memories require supersession or disputed status.
Private memories cannot leak across scopes.
```

## M4 acceptance

Memory retrieval passes precision/recall evals for project decisions, supersession, source-linked recall, and privacy boundaries.
