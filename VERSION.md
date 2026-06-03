# Ultimate AI Agent Version

Current active baseline: **v0.29.0**

v0.29.0 implements M25 Truth Source Router + Evidence Claim Checker. It adds
deterministic truth source contracts, source priority ordering,
claim/evidence/verification models, evidence chain validation,
conflict/staleness/revocation handling, documentation, documentation-integrity
checks, static safety verification, and Foundation Gate coverage.

It enforces that memory is recall rather than authority, model/runtime/OpenWebUI
output cannot verify truth, arbitrary refs cannot self-authorize claims, and
verified status requires primary/source-backed evidence. It adds no web search,
external verification, model/provider calls, retrieval/RAG/vector/embedding
functionality, source crawling, memory writes, evidence mutation, backend
mutation routes, dependencies, or production authority. OpenAPI path count
remains `74`. M26 remains future.
