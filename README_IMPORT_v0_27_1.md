# README Import v0.27.1

Status: Current import README for v0.27.1 / M23 Local LLM Call Safety
Hardening.

Start with:

- `VERSION.md`
- `ultimate_ai_agent_master_plan_v0_27_1.md`
- `docs/release_notes/v0_27_1.md`
- `docs/implementation/foundation_gate_implementation_plan_v0_27_1.md`
- `docs/runtime/FIRST_LOCAL_LLM_CALL.md`
- `docs/runtime/FIRST_LOCAL_LLM_CALL_M23.md`
- `docs/runtime/M23_FIXED_PROMPT_POLICY.md`
- `docs/runtime/M23_LOCAL_MODEL_CALL_POLICY.md`
- `docs/runtime/M23_LOCAL_MODEL_CALL_SAFETY.md`
- `docs/runtime/M23_LOCAL_MODEL_CALL_RECEIPTS.md`
- `docs/runtime/M23_NON_AUTHORITATIVE_OUTPUT_POLICY.md`
- `docs/runtime/M23_MANUAL_CLI_USAGE.md`
- `docs/runtime/M23_TO_M24_BOUNDARY.md`
- `docs/runtime/LOCAL_RUNTIME_M22_TO_M23_BOUNDARY.md`
- `docs/roadmap/POST_M20_CAPABILITY_LAYER_ROADMAP.md`
- `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`
- `docs/canonical/09_roadmap.md`

v0.27.1 hardens the existing M23 manual/CLI-only, loopback-only,
fixed-prompt-only local model call path. It strengthens endpoint-label safety,
approval validation evidence checks, response redaction/cap tests, static
verifier coverage, Foundation Gate checks, and Foundation Gate report atomic
write/replace safety.

This release adds no backend API route, OpenAPI path count change, runtime
activation, endpoint probe, arbitrary prompt path, user-content model call,
provider SDK, runtime package, tokenizer, billing API, OpenWebUI runtime bridge,
Control Center execution control, tool execution, memory write, file write,
dependency, or production authority. M24 remains future.
