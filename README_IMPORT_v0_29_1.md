# README Import v0.29.1

v0.29.1 hardens M25 Truth Source Router + Evidence Claim Checker safety.

Start with:

- `VERSION.md`
- `README.md`
- `ultimate_ai_agent_master_plan_v0_29_1.md`
- `docs/truth/TRUTH_SOURCE_ROUTER.md`
- `docs/truth/EVIDENCE_CLAIM_CHECKER.md`
- `docs/truth/CLAIM_VERIFICATION_POLICY.md`
- `docs/truth/M25_TO_M26_BOUNDARY.md`

M25 remains contract-only and validation-only over provided refs. v0.29.1
denies unknown and arbitrary truth source refs, explicit
`TruthSourceKind.unknown` evidence, and self-verifying refs for all
verification-success statuses. It adds no web search, external verification,
model/provider calls, retrieval/RAG/vector functionality, memory writes,
evidence mutation, backend routes, dependencies, M26 context-pack builder, or
production authority. M26 remains future.
