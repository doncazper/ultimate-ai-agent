# OpenWebUI Safe Handoff Execution

M77 adds OpenWebUI Safe Handoff Execution as an exact approval binding, Agent
Core-only handoff record over safe refs. A safe handoff result records that the
Python Agent Core accepted an already-reviewed bridge envelope and exact-bound
approval ref for governance review.

OpenWebUI is a shell/bridge, not the brain. Agent Core remains authority.
OpenWebUI safe handoff execution is not a live OpenWebUI connection, not an
OpenWebUI runtime call, not a provider call, not a model call, not model
authority, not tool execution, not memory write, not context injection, not a
network call, not credentials or cookies access, not raw prompt exposure, not
raw provider payload exposure, not raw content exposure, not a backend route,
not a Control Center control, no Control Center control, not a dependency, and
not production authority.

The handoff is exact-bound to `bridge_envelope_ref`, `session_ref`,
`safe_conversation_ref`, `actor_ref`, and `approval_ref`. Approval refs are
identifiers only; `approval_test_*` is denied. Evaluator boundaries revalidate
safety-critical fields and reject model_copy-mutated raw payload, runtime,
context, memory, tool, network, credential, and production authority flags.

M78 remains future.
