# ADR-0052: Use Hybrid Retrieval for Source Grounding

Status: Accepted.
Date: v0.5.6.

## Context

Factual retrieval cannot depend on vector search alone. Exact identifiers, legal phrases, policy titles, SKUs, dates, file paths, function names, and issue IDs are often best retrieved by keyword search. Semantic queries and fuzzy phrasing benefit from vector search. High-quality grounding needs metadata filters, access controls, source authority ranking, freshness ranking, and reranking.

## Decision

Use hybrid retrieval for source-grounded answers: keyword search + vector search + metadata filters + access-control filters + semantic reranking + source/freshness ranking.

## Consequences

- Retrieval logs must capture methods used and candidate sources.
- High-stakes or verified outputs must not rely on a single opaque vector hit.
- Exact identifiers must be recoverable through keyword retrieval.
- Permission filters must apply before content enters model context.
- Reranking must prefer authoritative, current, permitted sources.
