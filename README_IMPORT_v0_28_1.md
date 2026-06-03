# README Import v0.28.1

Active baseline: v0.28.1.

v0.28.1 repairs the M24 public memory request contract and hardens M24 memory
safety checks. Package-root `MemoryWriteRequest` now refers to the reviewed,
redacted-summary-only provider/store write request used by `LocalMemoryStore`.
The legacy content-bearing memory write request remains explicit as
`LegacyMemoryWriteRequest`.

This patch updates route inventory docs through v0.28.1, hardens Foundation Gate
guard-field checks, clarifies that M24 `source_refs` are required while
evidence/event/receipt refs are supplemental provenance, returns defensive copies
from the in-memory local store, and applies minor memory docs/code polish.

v0.28.1 adds no automatic memory writes, model-output writes, local LLM output
writes, OpenWebUI chat memory writes, Control Center mutation, mobile capture
writes, tool output writes, vector DB, embeddings, cloud memory provider, raw
session history, context injection, backend mutation routes, dependencies,
production persistence, or M25 claim verification.

Start with:

- `VERSION.md`
- `ultimate_ai_agent_master_plan_v0_28_1.md`
- `docs/release_notes/v0_28_1.md`
- `docs/implementation/foundation_gate_implementation_plan_v0_28_1.md`
- `docs/memory/MEMORY_PROVIDER_ABSTRACTION.md`
- `docs/memory/MEMORY_WRITE_POLICY.md`
- `docs/memory/M24_TO_M25_BOUNDARY.md`
