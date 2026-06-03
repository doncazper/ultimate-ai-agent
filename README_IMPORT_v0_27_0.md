# README Import v0.27.0

Status: Historical import README for v0.27.0 / M23 First Real Local LLM Call,
Non-Tool, Non-Authoritative. Superseded by v0.27.1.

Start with:

- `VERSION.md`
- `ultimate_ai_agent_master_plan_v0_27_0.md`
- `docs/release_notes/v0_27_0.md`
- `docs/implementation/foundation_gate_implementation_plan_v0_27_0.md`
- `docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md`
- `docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md`
- `docs/runtime/LOCAL_MODEL_RUNTIME_ACTIVATION_CONTRACT.md`
- `docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md`
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`
- `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`
- `docs/canonical/09_roadmap.md`

v0.27.0 adds a manual/CLI-only, loopback-only, fixed-prompt-only local model
call path. The path is dry-run by default, requires `--execute-local-call`,
requires validated local approval for execution, uses fake transport in tests
and Foundation Gate, and records non-authoritative receipts.

This release adds no backend API route, OpenAPI path count change, runtime
activation, endpoint probe, arbitrary prompt path, user-content model call,
provider SDK, runtime package, tokenizer, billing API, OpenWebUI runtime bridge,
Control Center execution control, tool execution, memory write, file write,
dependency, or production authority. M24-M40 remain planned/provisional.
