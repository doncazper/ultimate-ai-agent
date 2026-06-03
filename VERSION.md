# Ultimate AI Agent Version

Current active baseline: **v0.29.1**

v0.29.1 hardens M25 Truth Source Router + Evidence Claim Checker safety. It
denies unknown and arbitrary truth source refs for all verification-success
statuses, blocks explicit TruthSourceKind.unknown evidence from producing
evidence_supported or verified_by_primary_source results, adds regression tests
for random refs, unknown source kinds, and self-verification, and strengthens
Foundation Gate coverage for arbitrary/unknown truth refs.

It adds no web search, external verification, model/provider calls,
retrieval/RAG/vector/embedding functionality, memory writes, backend truth
verification routes, dependencies, M26 context-pack builder, or production
authority. OpenAPI path count remains `74`. M26 remains future.
