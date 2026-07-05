# Phases 01-09: Critical Runtime Delegation And Capabilities

These phases establish the safe control-plane foundation. Each phase must run
through the wrapper's one-phase branch, review, fix, harden, test, PR, merge,
and sync loop.

## Shared Acceptance For Phases 01-09

- UAA remains the authority owner.
- Hermes is optional and externally configured.
- Control Center never talks directly to Hermes with secrets.
- Python core owns durable truth.
- CLI/API/Core parity exists for operator-relevant state.
- Runtime data uses safe refs and redacted summaries.
- Blocked controls are visibly blocked and cannot mutate.

## Phase 01: Runtime Delegation Adapter

Branch: `codex/hermes-adoption-01-runtime-delegation-adapter`
Commit: `Add Hermes runtime delegation adapter contract`

Full-strength: UAA can delegate tasks to Hermes, Codex, Claude, UAA-native, or
local runtimes while enforcing UAA authority.

Repo-safe: add a Python-owned `RuntimeDelegationAdapter` contract and a Hermes
adapter read model with no live execution by default.

Blocked / needs authority: live run submission, model calls, tool execution,
browser, shell, connector writes, background autonomy.

Exact promotion path: require configured endpoint, credential ref, loopback or
approved network policy, approval binding, run receipt, event redaction, stop
support, CLI/API/UI parity, and focused tests.

Required work:

- Inspect existing runtime/provider adapter code.
- Define runtime identity, endpoint posture, authority mode, capability refs,
  health refs, blocked reasons, and next safe action.
- Add CLI inspection, API read route if appropriate, and Control Center
  readiness display.
- Add docs explaining "UAA controls authority; runtime provides capability."

Verification focus: adapter contract tests, redaction tests, product truth,
OpenAPI/API tests if routes are added.

## Phase 02: Capabilities Discovery Endpoint Pattern

Branch: `codex/hermes-adoption-02-capability-discovery`
Commit: `Add runtime capability discovery posture`

Full-strength: UAA discovers runtime capabilities before surfacing controls.

Repo-safe: add backend-owned runtime capability read models for models, runs,
events, approvals, sessions, skills, toolsets, jobs, and blocked actions.

Blocked / needs authority: direct runtime calls unless an exact connector is
accepted; runtime capability cannot grant UAA permission.

Exact promotion path: signed/hashed capability snapshot, freshness policy,
redaction, policy evaluation, and operator-visible trust labels.

Required work:

- Add capability taxonomy and status labels.
- Distinguish runtime-supported from UAA-authorized.
- Ensure stale or unreachable runtime states degrade safely.
- Add CLI/API/UI inspection.

Verification focus: stale capability handling, blocked labels, no UI-only
truth, no secret exposure.

## Phase 03: Runs API With Events, Stop, And Approval

Branch: `codex/hermes-adoption-03-runtime-runs-events`
Commit: `Add runtime run event contract posture`

Full-strength: UAA can create, monitor, stop, and approve delegated runtime
runs.

Repo-safe: create UAA read/proposal contracts for external runtime runs,
events, stop posture, and approval-wait states without starting real runs.

Blocked / needs authority: POST run creation and stop/approval execution unless
exact approval lane exists.

Exact promotion path: idempotent run creation, approval ref, receipt refs,
event stream redaction, cancellation proof, retry/recovery, CLI/API/Core parity.

Required work:

- Model external run lifecycle states.
- Map runtime run states to UAA durable run states.
- Add event ref grammar and proof binding.
- Add blocked/proposal UI states.

Verification focus: state transitions, no fake completion, no mutation route
without approval.

## Phase 04: Approval Bridge

Branch: `codex/hermes-adoption-04-approval-bridge`
Commit: `Add runtime approval bridge posture`

Full-strength: runtime pending approvals appear in UAA Action Inbox, and UAA
approval resolves the runtime wait safely.

Repo-safe: implement approval bridge contracts and read models. If execution is
not already authorized, keep resolution blocked and generate unblock prompt.

Blocked / needs authority: sending approval decisions to Hermes or any runtime
without exact local approval authority.

Exact promotion path: exact scope, idempotency key, approval envelope, runtime
run id safe ref, side-effect class, timeout, denial receipt, and proof link.

Required work:

- Define runtime approval envelope fields.
- Bind envelope to Action Inbox and Proof.
- Add deny/default timeout posture.
- Add UI that separates "runtime requested" from "UAA approved."

Verification focus: approval scope validation, denial path, timeout path,
Action Inbox parity.

## Phase 05: Streaming Tool Progress

Branch: `codex/hermes-adoption-05-streaming-tool-progress`
Commit: `Add runtime streaming progress read model`

Full-strength: UAA shows delegated runtime tool progress live in task timelines.

Repo-safe: add redacted event ingestion/read model contracts and fixture-backed
or locally stored event previews.

Blocked / needs authority: live SSE/WebSocket subscription unless an exact
read-only transport lane exists.

Exact promotion path: loopback or approved transport, bounded event retention,
redaction, reconnect semantics, event hashes, and proof refs.

Required work:

- Define runtime event types: token, tool started, tool completed, warning,
  approval wait, stopped, failed, completed.
- Add summary display and CLI inspection.
- Store safe refs, not raw tool payloads.

Verification focus: redaction, bounded previews, event ordering, stale stream
labeling.

## Phase 06: Profiles As Isolated Agents

Branch: `codex/hermes-adoption-06-runtime-profiles`
Commit: `Add runtime profile isolation posture`

Full-strength: UAA can manage multiple isolated runtime profiles for coding,
research, operations, CRM, and review.

Repo-safe: add profile metadata read model: profile ref, role, configured
status, authority profile, workspace scope, memory scope, toolset posture, and
blocked reasons.

Blocked / needs authority: creating/deleting runtime profiles, writing runtime
config, copying secrets, or changing runtime defaults.

Exact promotion path: explicit operator approval, profile storage contract,
secret refs, rollback/safe-disable, CLI parity, and audit receipt.

Required work:

- Model UAA runtime profile refs separate from Hermes profile names.
- Add safe display labels and profile health.
- Document isolation assumptions and limitations.

Verification focus: no raw paths/secrets, no cross-profile authority bleed.

## Phase 07: Model / Provider Catalog UX

Branch: `codex/hermes-adoption-07-model-provider-catalog`
Commit: `Harden runtime model provider catalog posture`

Full-strength: UAA shows available providers, models, costs, credentials,
readiness, and runtime defaults across UAA-native and delegated runtimes.

Repo-safe: add read-only catalog/readiness integration and labels. Do not add
new provider calls unless already authorized.

Blocked / needs authority: credential collection, OAuth, provider SDK calls,
remote model invocation, and billing actions.

Exact promotion path: credential ref, secret vault binding, redacted diagnostic
receipt, cost policy, model-output truth handling, and exact invocation lane.

Required work:

- Extend provider catalog to include delegated runtime model availability.
- Separate "runtime says available" from "UAA may invoke."
- Show cost/latency metadata where safe and sourced.

Verification focus: secret redaction, cost-label accuracy, no invocation.

## Phase 08: Main Vs Auxiliary Model Slots

Branch: `codex/hermes-adoption-08-model-slot-posture`
Commit: `Add main auxiliary model slot posture`

Full-strength: UAA can route main thinking and auxiliary tasks to separate
models for quality, speed, and cost.

Repo-safe: add model-slot contracts for main, summarization, title, approval
scoring, compression, retrieval, vision, and review. Keep execution blocked
unless exact model authority exists.

Blocked / needs authority: live auxiliary calls, provider SDK use, runtime
selection mutation, and hidden model routing.

Exact promotion path: route decision trace, cost estimate, approval/profile
mapping, model-output truth envelope, and receipts.

Required work:

- Add read model for configured/intended model slots.
- Add warnings when auxiliary tasks would use expensive or unavailable models.
- Bind to provider readiness and Trust.

Verification focus: no hidden routing, no raw prompt persistence.

## Phase 09: Toolsets

Branch: `codex/hermes-adoption-09-toolsets`
Commit: `Add runtime toolset capability posture`

Full-strength: UAA governs tool groups by runtime, profile, task, and authority
mode.

Repo-safe: add toolset read models showing enabled, configured, blocked,
approval-required, and unsupported states.

Blocked / needs authority: enabling tools in Hermes, invoking tools, or
changing toolset config.

Exact promotion path: exact toolset grant, per-tool side-effect class,
approval binding, safe-disable, receipt, and verifier coverage.

Required work:

- Define UAA toolset taxonomy that can map Hermes toolsets without copying.
- Show per-toolset "runtime supports" vs "UAA allows."
- Add CLI/API/UI parity.

Verification focus: blocked high-authority toolsets remain blocked.

