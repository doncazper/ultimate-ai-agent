# README Import v0.29.2

v0.29.2 hardens local-dev API authority and raw preview safety before M26.

Start with:

- `VERSION.md`
- `README.md`
- `ultimate_ai_agent_master_plan_v0_29_2.md`
- `docs/release_notes/v0_29_2.md`
- `docs/implementation/foundation_gate_implementation_plan_v0_29_2.md`
- `docs/truth/TRUTH_SOURCE_ROUTER.md`
- `docs/truth/EVIDENCE_CLAIM_CHECKER.md`
- `docs/truth/CLAIM_VERIFICATION_POLICY.md`
- `docs/truth/M25_TO_M26_BOUNDARY.md`

M25 remains deterministic, local, contract-only, and validation-only over
provided refs. v0.29.2 removes test-prefixed approval-ref fallback authority
from Tool Broker/kernel mutation paths, keeps public `/kernel/tasks/run`
local-dev mutation requests dry-run-only, returns metadata-only file read
previews by default, prevents raw exception-message echo from API handlers, and
keeps memory/model truth authority helpers fail-closed for direct unsafe refs.

It adds no web search, external verification, source fetching, model/provider
calls, retrieval/RAG/vector/embedding functionality, memory writes, evidence
mutation, backend truth verification routes, dependencies, M26 context-pack
builder, backend route expansion, or production authority. M26 remains future.
