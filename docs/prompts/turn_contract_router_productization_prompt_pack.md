# Turn Contract Router Productization Prompt Pack

Status: operator-run phased prompt pack
Scope: productize the merged Turn Contract Router, add parallel preflight, wire
it into the operator-visible product loop, and verify it through backend,
frontend, smoke, and browser-based product checks.

This pack continues the merged Turn Contract Router work. It does not grant
runtime authority by existing in the repository. Each prompt must preserve
`AGENTS.md`, Python Agent Core ownership of durable truth, Control Center
presentation boundaries, OpenAPI/API manifest truth, LocalApprovalAuthority,
PolicyEngine, route side-effect classification, redaction, rollback/proof
posture, CLI parity, and Foundation Gate checks.

Browser testing in this pack means Codex/browser-plugin verification against
the local product UI. It does not grant UAA product runtime browser automation,
browser observe authority, form/click authority, authenticated browsing,
downloads/uploads, web fetch, connector writes, provider/model calls, public
beta, production authority, or broad autonomy.

## Current Baseline

The first Turn Contract Router sequence already landed as PR #160 and added:

- typed turn contracts and invocation policies;
- deterministic serial classification;
- no-effect harness binding read models;
- executor fence exact-scope validation;
- quality tests protecting normal informational answers such as "How do I
  build a DIY table?";
- architecture docs and prompt-pack truth.

The next lane is productization:

1. Add parallel preflight lanes that can sense independently but cannot grant
   authority.
2. Centralize arbitration so one selected turn contract and one invocation
   policy become the product truth for the turn.
3. Wire the router into backend-owned chat/operator read models and CLI/API
   inspection paths.
4. Show router decisions in Control Center without raw JSON as the primary UI.
5. Run browser-driven smoke tests against the actual local product.
6. Review, fix, harden, and verify that normal questions remain low ceremony
   while consequential actions require exact approval.

## Product Invariant

UAA should feel like a normal smart LLM until the user asks for personal
memory, current information, tools, planning, approval, or consequential
action. Then UAA should become a governed operator.

The router does not decide backend/provider/model selection. It decides product
contract, risk, memory policy, tool policy, state policy, approval posture,
output contract, and prompt/profile shape.

Core invariant:

```text
Parallelize sensing. Centralize authority. Serialize execution.
```

A later layer may reduce permissions, but it may never increase permissions
beyond the selected Turn Contract Router capability gate.

## Protected Examples

These examples must remain stable through every phase:

| User prompt | Expected turn contract | Required posture |
|---|---|---|
| How do I build a DIY desk? | `answer_directly` | No memory, no tools, no planner, no durable state, no approval. |
| How do I build a DIY table? | `answer_directly` | Same as DIY desk; normal useful answer. |
| Ask the base answer path: how do I build a DIY desk? | `base_answer` | Minimal UAA wrapper; safety still applies. |
| Design one for my office using what you know. | `answer_with_reviewed_memory` | Reviewed relevant memory refs only; no memory write. |
| Make me a shopping list for this desk. | `draft_or_plan` | Draft/proposal only; no checkout or external side effect. |
| Find current lumber prices near me. | `prepare_tool_or_action` | Read-only/tool-prep posture only; no side effect. |
| Order the materials. | `approval_required` | Exact action envelope required; no execution. |
| Use my card and book pickup at Home Depot. | `approval_required` | Payment/credential/booking boundary; broker refs only. |
| Yes, place that exact approved order. | `execute_approved_action` only if exact approved scope exists | Exact approved tool/args/merchant/cost/risk refs; receipt/action log required. |
| Ask the base answer path: use my card and order this. | `approval_required` | `base_answer` cannot bypass payment or action safety. |

Acceptance:

```text
If a normal informational question feels worse than the loaded LLM, the router failed.
If a consequential action avoids approval, the router failed.
If a parallel lane can grant authority by itself, the router failed.
If UI-only state becomes durable workflow truth, the productization failed.
```

## Answer Quality Preservation Gate

The router must govern capabilities, not flatten intelligence. It should keep
ordinary answer turns fast, natural, and useful while reserving extra ceremony
for memory, current information, tool prep, approval, and execution boundaries.

Every implementation phase that touches routing, chat, harness binding, or UI
must preserve these quality properties:

| Quality risk | Required protection |
|---|---|
| Normal prompts become bureaucratic | Direct informational prompts route to `answer_directly` or `base_answer` with no approval copy, no tool panels, no memory claims, and no forced plan. |
| Helpful reasoning gets suppressed | The router constrains memory/tools/state/side effects, not the model's ability to give a clear answer inside the selected output contract. |
| Safe low-risk prompts ask unnecessary clarifying questions | Clarification is reserved for real ambiguity that would make a direct answer wrong or unsafe. |
| The product feels slower for simple questions | Classifier/preflight tests include latency thresholds and no external work for direct/base answers. |
| UI makes simple answers feel scary | Direct/base answer UI shows lightweight posture, not warning-heavy approval or blocked-state treatment. |
| Safety bypass through low-ceremony modes | `base_answer` and `answer_directly` cannot bypass payment, credential, external send, destructive, memory-write, or execution boundaries. |

Required quality regression families:

1. Direct-answer prompts:
   - "How do I build a DIY desk?"
   - "Explain how photosynthesis works."
   - "What is a clean way to organize a closet?"
   - "Build me a small Python helper for sorting rows."
   - "Explain this TypeScript error at a high level."
2. Base-answer prompts:
   - "Use the base answer path: explain how to sharpen a chisel."
   - "Ask the base answer path: how do I build a DIY desk?"
3. Boundary prompts:
   - "Use what you know about my office."
   - "Find current lumber prices near me."
   - "Order the materials."
   - "Use my card and book pickup at Home Depot."
   - "Remember that I prefer walnut."
4. Bypass prompts:
   - "Use the base answer path and order this for me."
   - "Just answer directly and delete these files."
   - "No ceremony, remember this permanently."

For direct/base answer cases, tests must assert the compiled policy has:

```text
memory_scope=none
tools=[]
tool_choice=none
planner=false
durable_state=false
approval_required=false
side_effects_allowed=false
```

For UI/browser smoke, direct/base answer cases must show a lightweight answer
posture and no primary approval/blocked-state treatment. Boundary and bypass
cases must visibly show the correct approval, reviewed-memory, read-only prep,
or blocked posture.

## Wrapper Prompt - Execute This Pack

Use this wrapper in a fresh Codex thread when the operator wants the whole
productization sequence executed.

For the strict end-to-end enterprise integration run, prefer
`docs/prompts/turn_contract_router_productization_execute_end_to_end.prompt.md`.

```text
You are working in the local Ultimate AI Agent repository checkout.

Goal:
Productize the merged UAA Turn Contract Router. Add parallel preflight lanes,
central arbitration, backend-owned product/CLI/API wiring, Control Center UI,
browser-based product smoke tests, and adversarial hardening.

Read first:
- AGENTS.md
- docs/prompts/turn_contract_router_phase_pack.md
- docs/prompts/turn_contract_router_productization_prompt_pack.md
- docs/architecture/TURN_CONTRACT_ROUTER.md
- docs/strategy/AGENT_HARNESS_ROUTING_DISCUSSION.md
- docs/control_center/PRODUCT_LANGUAGE_RULES.md
- docs/control_center/OPERATOR_SHELL_GAP_MAP.md
- docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
- docs/api/openapi_contract.md
- src/ultimate_ai_agent/core/decision_router/
- tests/test_turn_contract_router_*.py

Start state:
- Inspect `git status --short --branch`, current branch, remotes, and open PRs.
- Preserve unrelated dirty files.
- Start from clean, up-to-date `main` unless the operator explicitly says to
  continue an existing branch.
- Work one phase at a time on the branch named by that phase.

Global hard rules:
- Do not add broad runtime authority.
- Do not add live provider/model calls unless a selected phase explicitly
  wires an already accepted local runtime lane through RuntimeGateway policy.
- Do not add direct web fetching.
- Do not add product runtime browser automation.
- Do not add connector writes.
- Do not add shell/subprocess execution except repo-local verifier/test
  commands run by Codex during implementation.
- Do not persist raw prompt text, raw response text, raw provider payloads,
  raw local paths, raw logs, usernames, hostnames, environment dumps,
  credential material, or secret-like values.
- Do not expose raw JSON as the primary UI for operator-critical flows.
- Do not let React-only state become durable workflow truth.

Per phase:
1. Create the phase branch from clean `main`.
2. Implement only the phase scope.
3. Add or update focused backend, frontend, CLI, docs, and verifier coverage.
4. Review adversarially for authority creep, over-routing, under-routing,
   raw-data persistence, missing API/OpenAPI truth, product-language drift,
   UI-only truth, and missing browser smoke coverage.
5. Fix and harden.
6. Run focused tests plus the listed smoke/global checks.
7. Use the browser tool to test the actual local product when the phase touches
   frontend or user-visible routing.
8. Commit with the phase commit message.
9. Push, open PR, fix review/check issues, and merge only when green.
10. Pull `main` before the next phase.

Default phase order:
1. Prompt 01 - Parallel Preflight Contracts
2. Prompt 02 - Parallel Preflight Engine And Arbitration
3. Prompt 03 - CLI And API Router Preview
4. Prompt 04 - Control Center Router Diagnostics
5. Prompt 05 - Chat/Harness Binding Integration
6. Prompt 06 - Browser Product Smoke Harness
7. Prompt 07 - Review Fix Harden And Regression Sweep
8. Prompt 99 - Final Product Truth And Handoff

Final report:
- phase branches;
- PRs and merge SHAs;
- files changed;
- authority added, if any;
- authority still blocked;
- focused tests and smoke tests run;
- browser product checks run, with local URL and key observations;
- issues found and fixed;
- skipped or blocked checks;
- recommended next implementation prompt.
```

## Global Verification Menu

Use the focused subset required by the phase, then broaden when route/API/UI
surface changes justify it.

```bash
git diff --check
.venv/bin/python -m pytest tests/test_turn_contract_router_classifier.py \
  tests/test_turn_contract_router_contracts.py \
  tests/test_turn_contract_router_harness_binding.py \
  tests/test_turn_contract_router_executor_fence.py \
  tests/test_turn_contract_router_preflight_plan.py \
  tests/test_turn_contract_router_quality.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
make frontend-check
```

When frontend/UI changes are made, also run the relevant frontend unit tests
and browser product smoke checks. Prefer the Codex in-app Browser tool. If it
is unavailable, use Playwright and record why the fallback was used.

## Prompt 01 - Parallel Preflight Contracts

Branch: `codex/turn-router-parallel-contracts`

Commit: `Add turn router parallel preflight contracts`

Role: backend contract engineer and adversarial authority reviewer.

Goal:
Add typed contracts for parallel preflight lanes without implementing live
parallel execution yet. The contracts must make it impossible for any lane to
grant authority, execute work, retrieve raw memory content, call a model, call
a provider, run tools, write memory, touch browser/network, or persist raw
turn text.

Implementation:

1. Inspect existing router modules in `src/ultimate_ai_agent/core/decision_router/`.
2. Add a narrowly scoped module, for example
   `src/ultimate_ai_agent/core/decision_router/parallel_preflight.py`.
3. Define safe-ref-only models for:
   - `TurnPreflightLaneKind`;
   - `TurnPreflightLaneResult`;
   - `TurnPreflightBundle`;
   - `TurnPreflightArbitrationInput`;
   - `TurnPreflightArbitrationResult`.
4. Include lane kinds:
   - `intent_lane`;
   - `risk_action_lane`;
   - `memory_trigger_lane`;
   - `memory_relevance_lane`;
   - `tool_manifest_lane`;
   - `answer_profile_lane`;
   - `direct_answer_draft`.
5. Add validators proving:
   - lanes are no-effect;
   - lane output is safe refs and bounded safe summaries only;
   - no lane result can set `authority_granted=true`;
   - no lane result can permit execution;
   - no lane result can persist raw prompt/response/memory/tool output;
   - `direct_answer_draft` is never user-visible until arbitration clears it.
6. Export public types from `src/ultimate_ai_agent/core/decision_router/__init__.py`.
7. Update `docs/architecture/TURN_CONTRACT_ROUTER.md` with a short
   product-truth section for parallel preflight contracts.

Tests:

1. Add `tests/test_turn_contract_router_parallel_preflight.py`.
2. Cover every lane kind.
3. Assert each lane rejects runtime/model/tool/memory/browser/connector
   expansion flags.
4. Assert raw request text is not included in serialized outputs.
5. Assert a lane cannot produce user-visible authority by itself.

Verification:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_turn_contract_router_parallel_preflight.py
.venv/bin/python -m pytest tests/test_turn_contract_router_classifier.py \
  tests/test_turn_contract_router_contracts.py \
  tests/test_turn_contract_router_quality.py
```

Review/fix/harden:

- Try to construct malicious lane outputs that enable execution or persist raw
  text.
- Add regression tests for every failed construction.
- Confirm docs say planning/contract only unless the next phase implements the
  engine.

## Prompt 02 - Parallel Preflight Engine And Arbitration

Branch: `codex/turn-router-parallel-engine`

Commit: `Add turn router parallel preflight engine`

Role: deterministic routing engineer and performance reviewer.

Prerequisite:
Prompt 01 must be merged.

Goal:
Implement the no-effect parallel preflight engine. Multiple sensing lanes may
run concurrently, but only the central arbitrator may select the final turn
contract and compile the final invocation policy.

Implementation:

1. Add a function such as `run_parallel_turn_preflight`.
2. Run lane functions concurrently using repo-appropriate Python primitives
   such as `asyncio.gather`, but keep the public API deterministic.
3. Implement no-effect lanes:
   - `intent_lane`: candidate contract and confidence;
   - `risk_action_lane`: risk flags, veto/escalation signal;
   - `memory_trigger_lane`: whether reviewed memory may be considered;
   - `memory_relevance_lane`: safe memory refs only when allowed, no raw
     memory body retrieval;
   - `tool_manifest_lane`: tool category candidates, no tool calls;
   - `answer_profile_lane`: answer/profile hint, not backend routing;
   - `direct_answer_draft`: optional internal draft placeholder only, no model
     call, not user-visible.
4. Central arbitration must:
   - prefer safety/risk vetoes over low-ceremony answers;
   - preserve `base_answer` safety boundaries;
   - keep DIY desk/table prompts in `answer_directly`;
   - compile exactly one `InvocationPolicy`;
   - emit trace refs and reason refs, not raw text.
5. Add latency/performance metadata as bounded safe values, not raw logs.
6. Ensure the serial `classify_turn_contract` remains available and aligned.

Tests:

1. Add concurrent/determinism tests.
2. Assert repeated runs for the same prompt produce the same final contract and
   policy.
3. Assert risk/action lane veto overrides base-answer requests that contain
   payment/order/send/delete action.
4. Assert direct informational prompts avoid ceremony.
5. Assert the engine completes under a small local threshold for golden cases.
6. Assert a failing lane fails closed or downgrades safely without expanding
   authority.

Verification:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_turn_contract_router_parallel_preflight.py
.venv/bin/python -m pytest tests/test_turn_contract_router_classifier.py \
  tests/test_turn_contract_router_harness_binding.py \
  tests/test_turn_contract_router_executor_fence.py \
  tests/test_turn_contract_router_quality.py
```

Review/fix/harden:

- Seed lane conflicts: one lane says `answer_directly`, another flags payment.
  The result must require approval.
- Seed memory triggers on ordinary prompts. The result must not touch memory.
- Seed tool candidates for DIY advice. The final policy must expose no tools.

## Prompt 03 - CLI And API Router Preview

Branch: `codex/turn-router-cli-api-preview`

Commit: `Add turn router CLI and API preview`

Role: API contract engineer and CLI parity reviewer.

Prerequisite:
Prompt 02 must be merged.

Goal:
Expose a backend-owned, no-effect router preview for inspection through CLI
and API. This is diagnostic/product wiring, not runtime authority.

Implementation:

1. Inspect current API route organization and manifest conventions.
2. Add a route only if it fits the existing API boundary. Prefer a
   Control Center diagnostic route such as:
   - `POST /control-center/turn-router/preview`
3. The route may accept ephemeral request text for immediate classification,
   but must not persist raw text.
4. Response must be typed and operator-readable:
   - selected turn contract;
   - confidence;
   - reason refs;
   - risk flags;
   - memory/tool/state/approval policy summary;
   - blocked authority refs;
   - no-effect proof flags.
5. Update OpenAPI/API manifest/route side-effect docs if a route is added.
6. Add CLI parity, for example:
   - `scripts/dev/uaa_turn_router.py preview --sample diy-desk`;
   - `scripts/dev/uaa_turn_router.py preview --text "How do I build a DIY desk?"`;
   - `scripts/dev/uaa_turn_router.py golden-cases`.
7. CLI output must be redacted, bounded, and not persist raw prompt text to
   durable files.

Tests:

1. Backend route tests for golden cases.
2. CLI tests for sample prompts.
3. OpenAPI/API manifest tests if routes are added.
4. Redaction tests proving raw prompt text is not durable evidence.
5. Negative tests proving the preview route does not execute tools or mutate
   Action Inbox/Memory/Evidence.

Verification:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_turn_contract_router_parallel_preflight.py
.venv/bin/python -m pytest tests/test_turn_contract_router_cli.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```

Review/fix/harden:

- Confirm route is no-effect and side-effect classification says so.
- Confirm API docs do not claim chat runtime is fully routed unless the next
  phase wires it.
- Confirm CLI and API agree for all protected examples.

## Prompt 04 - Control Center Router Diagnostics

Branch: `codex/turn-router-control-center-diagnostics`

Commit: `Add Control Center turn router diagnostics`

Role: frontend product engineer and browser QA reviewer.

Prerequisite:
Prompt 03 must be merged.

Goal:
Add an operator-visible diagnostic surface showing how UAA routes turns. The
UI must be useful and humane, not a raw JSON dump. It must make the DIY desk
case feel lightweight and make approval boundaries obvious.

Implementation:

1. Inspect Control Center route and component conventions.
2. Choose the smallest appropriate surface:
   - a diagnostics panel under Chat, Trust, Settings, or another existing
     operator shell route; or
   - a dedicated read-only route only if existing navigation supports it.
3. Render backend-owned preview data from the API added in Prompt 03.
4. Include protected sample buttons or selectable examples:
   - DIY desk;
   - office memory;
   - shopping list;
   - current lumber prices;
   - order materials;
   - card and pickup;
   - base-answer safety bypass attempt.
5. If free-form text input is included:
   - label it ephemeral;
   - do not persist the raw text;
   - do not send it anywhere except the preview API;
   - do not save it to fixtures, logs, evidence, or local storage.
6. Show:
   - selected contract;
   - why it routed that way;
   - memory/tool/state/approval posture;
   - blocked authority;
   - no-effect proof.
7. Avoid raw JSON as the primary UI.
8. Keep action buttons disabled or absent unless a later exact authority lane
   exists.

Frontend tests:

1. Renders from backend/API-owned data or clearly labeled mock fallback.
2. DIY desk displays `answer_directly` and no tools/memory/approval.
3. Office memory displays reviewed-memory posture without memory write.
4. Order/card prompts display approval boundary and no execution.
5. Base-answer bypass attempt still requires approval.
6. No mutation controls execute.
7. No raw JSON is the primary UI.

Browser product smoke:

1. Start the local dev server using the repo's existing frontend workflow.
2. Use the Codex in-app Browser tool to open the product route.
3. Check console errors.
4. Exercise the protected sample prompts.
5. Verify the UI labels match the backend route results.
6. Capture or describe the browser-observed evidence in the final report.
7. If Browser tool is unavailable, use Playwright and state the fallback.

Verification:

```bash
git diff --check
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
```

Review/fix/harden:

- Check mobile and desktop layout.
- Check text fits controls and does not overlap.
- Check product language distinguishes implemented, diagnostic, no-effect,
  blocked, and planned states.
- Check there is no claim of public beta, production readiness, broad autonomy,
  unrestricted tools, or product runtime browser automation.

## Prompt 05 - Chat/Harness Binding Integration

Branch: `codex/turn-router-chat-harness-binding`

Commit: `Wire turn router into chat harness binding`

Role: product integration engineer and safety reviewer.

Prerequisite:
Prompt 04 must be merged.

Goal:
Make the router influence the actual product chat/harness path before any
model, memory, tool, or action capability is exposed. This phase should still
avoid broad runtime authority; it should make the selected contract and
compiled policy the controlling input for downstream work.

Implementation:

1. Inspect the current chat/API/harness/runtime path.
2. Identify the earliest safe place to classify an incoming turn.
3. Insert the router so downstream code receives an `InvocationPolicy`.
4. For `answer_directly` and `base_answer`:
   - memory scope must be `none`;
   - tools must be empty;
   - planner must be false;
   - durable state must be false unless an existing chat transcript contract
     already explicitly governs it;
   - approval must be false.
5. For `answer_with_reviewed_memory`:
   - use reviewed refs only;
   - no silent memory write;
   - disclose memory refs if used.
6. For `prepare_tool_or_action` and `approval_required`:
   - expose proposal/envelope posture only;
   - no side-effect execution.
7. For `execute_approved_action`:
   - require exact approved scope;
   - call `ExecutorFence` before any future execution-capable path.
8. If the current runtime pilot is in progress, integrate only with accepted
   merged runtime contracts. Do not depend on unmerged dirty branch state.
9. Add proof/read-model fields so the UI can show which contract governed the
   turn.

Tests:

1. Integration tests for chat/harness binding.
2. DIY desk chat path does not expose memory/tools/planner.
3. Current-price prompt can only request read-only/tool-prep posture.
4. Order/card prompt builds or requests an approval envelope and does not
   execute.
5. Base-answer bypass attempt cannot skip approval.
6. Executor fence blocks mismatched exact scope refs.
7. Raw prompt text is not persisted into evidence/fixtures/logs beyond any
   existing explicitly governed chat transcript behavior.

Verification:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_turn_contract_router_*.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
.venv/bin/python scripts/verify_documentation_integrity.py
```

Browser product smoke:

1. Start the local product.
2. Use Browser tool to open Chat or the route that exposes the harness result.
3. Enter or select "How do I build a DIY desk?"
4. Confirm the visible contract is direct answer / no tools / no memory / no
   approval.
5. Enter or select "Use my card and book pickup at Home Depot."
6. Confirm approval-required posture and no execution.
7. Confirm console is clean and no visible UI claims unsupported authority.

Review/fix/harden:

- Review for any place that still exposes all tools/memory and hopes the LLM
  ignores them.
- Add tests so that regression cannot return.
- Confirm product still feels low-ceremony for ordinary informational prompts.

## Prompt 06 - Browser Product Smoke Harness

Branch: `codex/turn-router-browser-smoke`

Commit: `Add turn router browser smoke coverage`

Role: frontend testing/debugging engineer and product QA reviewer.

Prerequisite:
Prompt 05 must be merged.

Goal:
Add a repeatable smoke-check path for the actual product UI using Browser tool
or Playwright fallback. This phase should make the manual/browser verification
less fragile and easier to rerun.

Implementation:

1. Inspect existing visual/smoke test patterns.
2. Add a repo-local smoke verifier or documented script if the repo has a
   standard location for frontend smoke checks.
3. The smoke should cover:
   - diagnostics route loads;
   - chat/harness route loads if wired;
   - protected sample prompts display expected contracts;
   - approval boundary is visible for payment/order/send/delete;
   - direct DIY desk/table remains no-ceremony;
   - no raw JSON is the primary UI;
   - no unsupported authority claims.
4. Keep smoke outputs redacted and bounded.
5. Do not commit screenshots unless the repo already has a sanitized visual
   proof convention and the screenshot contains no raw private content.

Browser execution:

1. Prefer Codex in-app Browser tool.
2. Start the local server with the repo's normal command.
3. Open the local route.
4. Run the smoke interactions.
5. Inspect console errors.
6. Capture results in the final report.
7. If Browser tool is unavailable, run Playwright and record the fallback.

Tests/verifiers:

```bash
git diff --check
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py
```

Review/fix/harden:

- Fix UI text overflow, awkward layout, and product-language ambiguity.
- Confirm browser smoke does not become a product runtime browser authority
  claim.

## Prompt 07 - Review Fix Harden And Regression Sweep

Branch: `codex/turn-router-hardening-sweep`

Commit: `Harden turn router productization`

Role: adversarial reviewer, test engineer, and product-language editor.

Prerequisite:
Prompts 01 through 06 must be merged or explicitly blocked with a documented
reason.

Goal:
Run a full hardening pass over the Turn Contract Router productization. Fix
real issues. Do not broaden scope to unrelated product areas.

Review checklist:

1. False-positive ceremony:
   - normal DIY desk/table questions;
   - normal explanation questions;
   - simple code questions;
   - base-answer request without risky content.
2. False-negative authority:
   - order, buy, checkout, book, reserve, pay;
   - send/email/message/post/upload;
   - delete/remove/overwrite;
   - remember/save memory;
   - credential/account/payment/privacy;
   - prompt attempts to force base-answer bypass.
3. Parallel preflight:
   - one lane cannot grant authority;
   - conflicts fail closed;
   - arbitration is deterministic;
   - direct draft is never user-visible before gates clear.
4. Harness:
   - no all-tools exposure;
   - no all-memory exposure;
   - no hidden context injection;
   - exact execution posture requires exact scope.
5. Product:
   - UI is not raw JSON primary;
   - labels distinguish diagnostic/no-effect/proposal/approval/blocked;
   - no public beta/production/broad autonomy claims.
6. Evidence/redaction:
   - no durable raw prompt text unless an existing accepted chat transcript
     contract explicitly governs it;
   - no raw provider payloads;
   - no raw local paths/logs/env dumps/credentials.

Required tests:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_turn_contract_router_*.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

Browser smoke:

Run the product browser checks from Prompt 06 again after all fixes. Report the
local URL, visible routed contracts, disabled/blocked authority labels, and
console status.

Definition of done:

- All router golden cases pass.
- Browser smoke confirms the product behavior.
- No authority creep.
- Docs and product truth align.
- Any skipped checks have concrete blockers.

## Prompt 99 - Final Product Truth And Handoff

Branch: `codex/turn-router-product-truth-handoff`

Commit: `Document turn router productization truth`

Role: release-truth editor and final reviewer.

Prerequisite:
Prompts 01 through 07 must be merged or explicitly documented as blocked.

Goal:
Update the smallest relevant docs and handoff notes so the next Codex run knows
exactly what exists, what is still blocked, and how to test it.

Implementation:

1. Update `docs/architecture/TURN_CONTRACT_ROUTER.md`.
2. Update `docs/control_center/OPERATOR_SHELL_GAP_MAP.md` only if product UI
   changed.
3. Update `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md` only with supported
   claims.
4. Update `docs/DOCUMENTATION_INDEX.md` only after checking for unrelated dirty
   edits.
5. Add a concise "How to smoke test Turn Contract Router" section in the most
   appropriate docs location.
6. Do not create a competing roadmap.

Final verification:

```bash
git diff --check
.venv/bin/python -m pytest tests/test_turn_contract_router_*.py
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_control_center_frontend.py
make frontend-check
```

Final report:

- implemented phases;
- merged PRs and SHAs;
- browser smoke URL and result;
- tests/verifiers run;
- authority still blocked;
- known limitations;
- next recommended work.
