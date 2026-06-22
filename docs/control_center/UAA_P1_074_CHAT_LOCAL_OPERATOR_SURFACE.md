# UAA-P1-074 Chat Local Operator Surface

Status: implemented as a contract, test, verifier, Today-spine, Evidence
Timeline, and first-party Control Center Chat metadata slice.

This milestone makes Chat a governed local operator surface. Control Center can
send a redacted readiness turn through the local chat gateway, show
model/runtime/auth/tool-denial truth, produce safe evidence refs, and hand off
proposal refs to Plans or Actions. It does not add provider SDK calls, web
fetching, tool execution, memory writes, hidden context injection, connector
writes, shell/subprocess execution, action execution, approval grant capture,
public beta, public distribution, or production authority.

## Contract Ref

`contract-ref:chat-local-operator-surface:v1`

## Turn Requirements

Each Chat local operator turn envelope requires:

- `turn_ref`
- `route_ref`
- `model_ref`
- `runtime_truth`
- `auth_truth`
- `tool_denial_truth`
- `safe_evidence_refs`
- `plans_handoff_ref`
- `actions_handoff_ref`
- `blocked_state_refs`

The route remains `/v1/chat/completions`, but durable Evidence refs use
structured refs such as `route-ref:v1-chat-completions`. The turn envelope is
safe-ref metadata only. Prompt body content, completion body content, provider
payloads, local paths, logs, account identifiers, credential material, and full
transcripts are denied from durable evidence.

## Today-Spine Binding

`GET /control-center/today/summary` now exposes:

- `chat_local_operator_contract_ref`
- `chat_local_operator_status`
- `chat_local_operator_turn_ref`
- `chat_local_operator_route_ref`
- `chat_local_operator_model_ref`
- `chat_local_operator_runtime_truth`
- `chat_local_operator_auth_truth`
- `chat_local_operator_tool_denial_truth`
- `chat_local_operator_tool_denial_ref`
- `chat_local_operator_safe_evidence_refs`
- `chat_local_operator_plans_handoff_ref`
- `chat_local_operator_actions_handoff_ref`
- `chat_local_operator_required_truth_fields`
- `chat_local_operator_required_blocked_refs`
- `chat_local_operator_surface_bindings`
- `chat_local_operator_authority_posture`
- `chat_local_operator_blocked_state_refs`

The Chat module feed now includes
`contract-ref:chat-local-operator-surface:v1` and `/v1/chat/completions`.

## Surface Binding

Chat local operator metadata feeds these surfaces as safe refs only:

- Today: turn contract, runtime/auth/tool-denial truth, and blocked states.
- Chat: first-party local gateway turn readiness and truth display.
- Plans: proposal handoff refs only.
- Actions: proposal handoff refs only.
- Evidence: route/auth/runtime/tool-denial history refs.
- Memory: blocked until cross-surface memory intake is scoped later.

## Authority Boundary

Denied states remain explicit:

- `blocked-state:no-model-output-authority`: model output is not truth or
  authority.
- `blocked-state:no-tool-execution`: no tool execution.
- `blocked-state:no-memory-write`: no memory write.
- `blocked-state:no-context-injection`: no hidden context injection.
- `blocked-state:no-provider-sdk-call`: no provider SDK call.
- `blocked-state:no-web-fetch`: no web fetch.
- `blocked-state:no-connector-write`: no connector write.
- `blocked-state:no-shell-subprocess-execution`: no shell/subprocess
  execution.
- `blocked-state:no-action-execution`: no action execution.
- `blocked-state:no-approval-grant-capture`: no approval grant capture.
- `blocked-state:no-production-authority`: no production authority.

Denied authority flags include `model_output_authority: false`,
`tool_execution_enabled: false`, `memory_write_authorized: false`,
`context_injection_authorized: false`, `provider_sdk_call_enabled: false`,
`web_fetch_enabled: false`, `connector_write_enabled: false`,
`shell_subprocess_execution_enabled: false`, `action_execution_enabled: false`,
`approval_grant_capture_enabled: false`, and
`production_authority_enabled: false`.

OpenWebUI remains a secondary local/dev shell and compatibility surface. It is
not the product state owner and it does not own the Founder Command Center
workflow state.

## Verification

Required proof:

- `tests/test_uaa_p1_074_chat_local_operator_surface.py`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `apps/control-center/src/App.test.tsx`
- `scripts/verify_uaa_p1_074_chat_local_operator_surface.py`
- `docs/schemas/chat_local_operator_surface.schema.json`

## Next Milestone

UAA-P1-075 Governed Code Workbench V1 is complete. UAA-P1-076 Cross-Surface
Memory Intake is next unless hardening finds that UAA-P1-075 needs an
incremental follow-up such as UAA-P1-075.1.
