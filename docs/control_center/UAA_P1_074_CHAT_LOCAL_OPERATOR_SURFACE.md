# UAA-P1-074 Chat Local Operator Surface

Status: implemented as a contract, test, verifier, Today-spine, Evidence
Timeline, and first-party Control Center Chat metadata slice.

The original metadata milestone makes Chat a governed local operator surface. Control Center can
send a redacted readiness turn through the local chat gateway, show
model/runtime/auth/tool-denial truth, produce safe evidence refs, and hand off
proposal refs to Plans or Actions. It does not add provider SDK calls, web
fetching, tool execution, memory writes, hidden context injection, connector
writes, shell/subprocess execution, action execution, approval grant capture,
public beta, public distribution, or production authority.

The separately accepted founder-private main-conversation follow-up below
introduces only `contract-ref:chat-explicit-local-turn:v1`. Its one-turn local
approval does not promote the original metadata contract's broad authority flags.

## Contract Ref

`contract-ref:chat-local-operator-surface:v1`

### Main conversation presentation

The first-party Chat now prioritizes the actual local conversation: a compact
light sidebar, readable contained transcript, and bottom-anchored composer.
The real model selector, New chat, Reconnect and explicit Send remain wired to
the existing transient conversation and authenticated loopback gateway.
Connection & safety exposes backend proof; Details exposes tab lifetime,
unverified-output warnings and the existing advanced diagnostics/handoffs.
Neither disclosure changes authority. Missing readiness keeps Send disabled;
failed turns preserve the draft and do not retry automatically. Narrow screens
use collapsible navigation. No fake history, cloud, attachment or tool controls
are added. Raw transcript persistence and packaged-startup qualification remain
outside this local developer-launch slice.

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

### Main Chat Local Conversation Follow-Up

The founder-prioritized local conversation client reuses the existing M164
authenticated loopback gateway. Its main composer sends only on explicit Send
or Enter, displays the allowlisted assistant text as plain text, and includes
the current tab's prior turns on follow-up. Model selection is bound for the
conversation; New chat starts a fresh transient display. Reloading loses this
content. The separate content-free checkpoint service still never accepts or
stores message bodies and does not itself grant Send authority.

The normal launcher hands off only the existing Control Center session. The
M164 gateway accepts that local API bearer only with a current backend-truth
envelope, exact revision/process binding, explicit gateway enablement, and a
configured gateway key. The gateway key and backend/provider key remain on the
server; they are not placed in browser URLs or JavaScript. Existing gateway-key
clients retain their original exact M164 contract. No new routes, operation IDs,
general provider authority, or auth-bypass capability are added.

The founder accepted the narrow runtime-rule exception on 2026-10-14. Send or
Enter adds `X-UAA-Operator-Confirmed: send-one-local-turn.v1` to this one request.
A session alone, a generic true value, the model-list read, and the diagnostic
probe cannot create local-turn permission. API session identity is evaluated
before the legacy gateway-key path, including equal-key misconfiguration.
Python snapshots the normalized request and configured loopback target, binds
them with backend revision/instance and attempt identity using a process-keyed
commitment, then captures and validates an exact two-minute
LocalApprovalAuthority grant. The commitment key is never persisted.

The `chat_local_turn_attempts` owner in Founder Loop storage commits a unique
content-free start before transport. The replay key is a stable digest of the
idempotency value, independent of the process-keyed content commitment. Every
duplicate attempt returns 409 without another call, including concurrent,
completed, interrupted, and restarted attempts. No raw reply cache exists.
A failed completion write leaves the start uncertain and non-replayable.
History is bounded at 10,000 attempts and fails closed at capacity; this lane
does not delete evidence or rotate away replay protection automatically.

Server-side ordinary-turn limits are 63 alternating user/assistant messages,
64,000 total characters, a final user message, and at most 1,024 output units.
System instructions, tools, functions, streaming, empty content, and invalid
generation limits are rejected. A fresh explicit Send is needed for each
follow-up. Model-list inspection remains read-only and does not invoke a model.
The old diagnostic probe has no Send confirmation and cannot use this new lane.

Send is available only for the M164 model-list safety contract. The M151
deterministic test shell remains visibly mock-only, even when its model list is
reachable. Backend revision/process replacement clears the transient transcript
and draft; late replies from the previous backend cannot repopulate them.

Fresh installations can open local Chat before completing an unrelated founder
workflow. The first-run exception still requires a valid revision-bound backend
envelope and backend-owned route data; stale, invalid, unavailable-storage,
unbound-revision and mock-backed states remain closed. Opening Chat never sends
a model turn automatically or marks founder-loop evidence complete.
Chat reads only its seven existing required summary endpoints under one bounded
deadline, retaining their normal ownership and payload validators. It does not
wait for unrelated application modules or promote their unread state.

Connection failures keep the draft available and never retry automatically.
A lost reply is an uncertain outcome, not proof that the model did not run.
The client permits at most 63 submitted messages and 64,000 characters of
explicit conversation context, with 32,000 characters per draft. These are
bounded conversation limits, not a claim about model context capacity. The existing
Python gateway continues to validate model identity, roles, output bounds,
loopback transport, authentication, and tools/functions/streaming denial.
Local model IDs may use a bounded namespace/model form, including the configured
Qwen 3.8 27B ID. Absolute paths, traversal, URLs and additional path segments stay
denied; the requested model must still exactly equal the configured model.
No provider transport, cloud call, tool runtime, persistent transcript, or
automatic memory write is added.

The development server proxies the existing /v1 routes to the same exact
loopback backend as Control Center routes. Local setup must configure the
existing gateway, approved model ID, loopback base URL and matching local
bearer. A model list is readiness evidence only; actual send/response proof is
required before calling a particular installation usable.

CLI/API inspection remains available through the existing
./scripts/dev/uaa local-model status command, /v1/models, and the same
/v1/chat/completions request contract. Operators must not put bearer values
or conversation bodies in durable logs or evidence.

The response includes content-free `uaa_safety.local_turn_approval` evidence.
Inspect its `attempt_ref` through the same Python-owned read contract without
issuing or replaying any turn:

```bash
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.chat.local_turn --attempt-ref CHAT_ATTEMPT_REF
```

The read command reports missing, started, completed, or outcome_uncertain and
never prints stored grants, conversation content, credentials, or local paths.
The route-wide manifest remains conservative (`header_shape_gate_only`), because
the legacy M151/gateway-key branches do not acquire this first-party-only store.

Safe disable and rollback use the existing local gateway enablement setting
or stopping only the operator-owned development services. This follow-up does
not modify existing user services or content-free workspace records.
Disable the gateway and restart only the owned backend; an in-flight model turn
cannot be undone, and a missing reply must not be retried automatically. Normal
code revert leaves the content-free attempt records in place. Neither disable
nor rollback deletes replay evidence or grants broader authority.

Required proof:

- `tests/test_uaa_p1_074_chat_local_operator_surface.py`
- `tests/test_chat_exact_local_turn.py`
- `tests/test_m164_llama_cpp_gateway.py`
- `apps/control-center/src/api/client.localConversation.test.ts`
- `tests/test_founder_loop_storage.py`
- `tests/test_control_center_founder_loop_api.py`
- `apps/control-center/src/App.test.tsx`
- `scripts/verify_uaa_p1_074_chat_local_operator_surface.py`
- `docs/schemas/chat_local_operator_surface.schema.json`

## Next Milestone

UAA-P1-075 Governed Code Workbench V1 is complete. UAA-P1-076 Cross-Surface
Memory Intake is next unless hardening finds that UAA-P1-075 needs an
incremental follow-up such as UAA-P1-075.1.
