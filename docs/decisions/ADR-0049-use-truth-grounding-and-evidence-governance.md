# ADR-0049: Use Truth, Grounding, and Evidence Governance

## Status

Accepted in v0.5.6.

## Context

The Ultimate AI Agent will answer factual questions, inspect files, retrieve documents, use memory, call providers, scan signals, and eventually act proactively. If the model itself becomes the source of truth, the system will hallucinate facts, use stale knowledge, blur memory with authority, and become hard to audit.

## Decision

Use a first-class Truth, Grounding, and Evidence Governance layer.

The model is not the source of truth. Truth comes from governed records, canonical files, approved documents, databases, APIs, provider result envelopes, Event Ledger entries, Structured World State, and source-linked memory when appropriate.

The system will use:

```text
Truth Source Manifests
Grounding Policies
Evidence Manifests
Claim Evidence records
CitationRef records
Source Conflict Reports
Retrieval Logs
Citation and unsupported-claim evals
```

## Consequences

Positive:

```text
Factual answers become auditable.
Hard facts can be routed to APIs/databases instead of stale documents.
Source conflicts become visible.
Stale evidence can be detected.
Memory remains recall, not authority.
High-stakes answers can require review.
```

Tradeoffs:

```text
More metadata and logging are required.
Some answers will be slower because they require retrieval or source refresh.
Some user requests will be refused or caveated when evidence is missing.
```

## Related

```text
docs/canonical/39_verified_task_completion_framework.md
docs/canonical/40_credentials_secret_broker_and_provider_registry.md
docs/canonical/41_memory_retrieval_v1.md
docs/canonical/43_minimum_lovable_kernel.md
docs/canonical/53_structured_world_state.md
docs/canonical/59_truth_grounding_and_evidence_governance.md
```
