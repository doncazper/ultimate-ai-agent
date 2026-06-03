# Ultimate AI Agent Master Plan v0.29.1

Status: Active master plan for v0.29.1 / M25 hardening.

v0.29.1 hardens M25 Truth Source Router + Evidence Claim Checker. It denies
unknown and arbitrary truth source refs for all verification-success statuses,
blocks explicit `TruthSourceKind.unknown` evidence from producing
`evidence_supported` or `verified_by_primary_source` results, adds regression
tests for random refs, unknown source kinds, and self-verification, and
strengthens Foundation Gate and static verifier coverage for arbitrary/unknown
truth refs.

M25 continues to enforce that memory is recall rather than authority,
model/runtime/OpenWebUI output cannot verify truth, arbitrary refs cannot
self-authorize claims, and verified status requires recognized
primary/source-backed evidence.

v0.29.1 adds no web search, external verification, model/provider calls,
retrieval/RAG/vector/embedding functionality, source crawling, memory writes,
evidence mutation, backend routes, dependencies, M26 context-pack builder, or
production authority.

M26 remains future as Grounded Recall Router + Evidence-Linked Context Pack
Builder.
