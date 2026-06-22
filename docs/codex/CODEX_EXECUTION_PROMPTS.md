# Codex Execution Prompts

Status: reusable prompt library for future repo work

Use these prompts for future Codex tasks in `doncazper/ultimate-ai-agent`.
They are templates, not runtime configuration. They grant no authority and do
not replace `AGENTS.md`, `README.md`, `VERSION.md`,
`docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`, or
`docs/kanban/current_board.md`.

## 1. Planning-Only Task Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: [describe planning task].

Scope: planning/docs only. Do not implement runtime behavior, backend routes,
frontend controls, dependencies, model/provider calls, shell/subprocess
execution, unrestricted browsing, connector writes, plugin runtime import,
mobile control, memory writes, context injection, public distribution, public
beta, or production authority.

Read first: AGENTS.md, README.md, VERSION.md,
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md,
docs/kanban/current_board.md, and any files named by the task.

Deliverables: update the smallest relevant docs. Keep the result subordinate to
current baseline truth and checkpoint-m168. Avoid duplicating existing roadmap
material.

For Founder Command Center permission-mode work, preserve the MVP permission
vocabulary: Observe, Draft, Propose, Approve once, Approve rule, Autopilot
micro-scope, and Kill switch. Names grant no authority.

Validation: run .venv/bin/python scripts/verify_documentation_integrity.py if
available.

Final summary must list files changed, tests/verifiers run, skipped checks with
reasons, and blocked items.
```

## 13. UAA-P1-082 Explicit Loopback CORS Allowlist Prompt

Use this prompt only after UAA-P1-081 Centralized FastAPI Security Headers is
complete, verified, committed, and pushed. This prompt implements explicit local
Control Center CORS allowlisting only. It does not grant auth, sessions,
idempotency enforcement, rate limits, route authority, connector authority,
provider/model authority, action execution, public beta, distribution,
production readiness, or production authority.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement UAA-P1-082 Explicit Loopback CORS Allowlist as the next
documented milestone after UAA-P1-081.

Review these documents first:
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[openapi_contract.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/api/openapi_contract.md)
[route_inventory.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/api/route_inventory.md)
[LOCAL_BACKEND_CONNECTION.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/LOCAL_BACKEND_CONNECTION.md)

Also inspect SPECS.md, specs.md, SDLC.md, sdlc.md if present. If absent, note
that AGENTS.md and the listed docs are the active process/spec guidance.

Scope:
- Add a server-side CORS policy for exact local Control Center dev/preview
  origins only: `http://localhost:5173`, `http://127.0.0.1:5173`,
  `http://[::1]:5173`, `http://localhost:4173`,
  `http://127.0.0.1:4173`, and `http://[::1]:4173`.
- Allow only the browser methods and headers needed by the current local
  Control Center contract.
- Prove wildcard CORS, CORS credentials, external origins, LAN/private IP
  origins, wrong local ports, `0.0.0.0`, and `null` origins remain denied.
- Prove CORS is browser hardening, not authentication or route authority.
- Preserve the current OpenAPI path count, stable operation IDs, route
  classifications, side-effect classes, and route behavior.

Non-goals:
- Do not add auth, sessions, idempotency enforcement, rate limiting,
  dependencies, routes, operation IDs, connector writes, model/provider calls,
  shell/subprocess execution, action execution, memory writes, Code apply,
  public beta, public distribution, production readiness, or production
  authority.

Review/fix:
- Perform adversarial self-review for wildcard CORS, broad host/port patterns,
  credentials exposure, accidental Authorization headers, false auth claims,
  route/OpenAPI drift, hidden production-readiness claims, stale currentness
  docs, and P1-081 verifier drift.
- Fix P0/P1 findings before hardening.

Hardening:
- Run focused tests:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_cors.py tests/test_api_security_headers.py tests/test_api_manifest.py -q`
- Run the P1-082 verifier:
  `.venv/bin/python scripts/verify_uaa_p1_082_loopback_cors.py`
- Run OpenAPI, documentation integrity, and frontend safety checks:
  `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
  `.venv/bin/python scripts/verify_documentation_integrity.py`
  `.venv/bin/python scripts/verify_control_center_frontend.py`
- Run `git diff --check`.

Commit/push:
- Stage only files changed for UAA-P1-082 plus already-accepted currentness docs
  that must stay coherent.
- Commit with message: `implement UAA-P1-082 loopback CORS allowlist`.
- Push the current branch. Do not force push.

Next prompt:
- After commit/push succeeds, recommend or execute UAA-P1-083 Local Bearer Or
  Session Gate For Sensitive Routes if the conveyor continues and the scope
  remains safe.
- Use an incremental UAA-P1-082.1 only if loopback CORS cannot be completed
  safely in one commit.
```

## 12. UAA-P1-081 FastAPI Security Headers Prompt

Use this prompt only after UAA-P1-080 API Route Classification And
Public/Protected Inventory is complete, verified, committed, and pushed. This
prompt implements centralized FastAPI response security headers only. It does
not grant auth, sessions, CORS, idempotency enforcement, rate limits, route
authority, connector authority, provider/model authority, action execution,
public beta, distribution, production readiness, or production authority.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement UAA-P1-081 Centralized FastAPI Security Headers as the next
documented milestone after UAA-P1-080.

Review these documents first:
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[openapi_contract.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/api/openapi_contract.md)
[route_inventory.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/api/route_inventory.md)
[UAA_P1_080_API_ROUTE_CLASSIFICATION_INVENTORY.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/api/UAA_P1_080_API_ROUTE_CLASSIFICATION_INVENTORY.md)

Also inspect SPECS.md, specs.md, SDLC.md, sdlc.md if present. If absent, note
that AGENTS.md and the listed docs are the active process/spec guidance.

Scope:
- Add centralized FastAPI response security headers for handled responses:
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
  `X-Frame-Options: DENY`, `Permissions-Policy` denying unused browser
  capabilities, `Content-Security-Policy` with strict posture and documented
  local dev loopback exceptions, and HTTPS-only HSTS.
- Add tests proving headers on success and handled error responses.
- Prove HSTS is HTTPS-only and no CORS headers are introduced.
- Add docs, schema/verifier coverage, and active currentness updates.
- Preserve the current OpenAPI path count, stable operation IDs, route
  classifications, side-effect classes, and route behavior.

Non-goals:
- Do not add auth, sessions, CORS, idempotency enforcement, rate limiting,
  dependencies, routes, operation IDs, connector writes, model/provider calls,
  shell/subprocess execution, action execution, memory writes, Code apply,
  public beta, public distribution, production readiness, or production
  authority.

Review/fix:
- Perform adversarial self-review for route/OpenAPI drift, accidental CORS,
  false auth/security claims, hidden production-readiness claims, missing error
  response headers, HSTS on HTTP, and stale currentness docs.
- Fix P0/P1 findings before hardening.

Hardening:
- Run focused tests:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_security_headers.py tests/test_api_manifest.py -q`
- Run the P1-081 verifier:
  `.venv/bin/python scripts/verify_uaa_p1_081_fastapi_security_headers.py`
- Run OpenAPI, documentation integrity, and frontend safety checks:
  `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
  `.venv/bin/python scripts/verify_documentation_integrity.py`
  `.venv/bin/python scripts/verify_control_center_frontend.py`
- Run `git diff --check`.

Commit/push:
- Stage only files changed for UAA-P1-081 plus already-accepted currentness docs
  that must stay coherent.
- Commit with message: `implement UAA-P1-081 FastAPI security headers`.
- Push the current branch. Do not force push.

Next prompt:
- After commit/push succeeds, recommend or execute UAA-P1-082 Explicit Loopback
  CORS Allowlist if the conveyor continues and the scope remains safe.
- Use an incremental UAA-P1-081.1 only if centralized headers cannot be
  completed safely in one commit.
```

## 11. UAA-P1-080 API Route Classification Prompt

Use this prompt only after UAA-P1-079 User Intent Understanding V1 is complete,
verified, committed, and pushed. This prompt starts the planned API boundary
hardening lane with classification/inventory truth only. It does not grant
middleware, auth, CORS, security headers, idempotency enforcement, rate limits,
connector authority, provider/model authority, action execution, public beta,
distribution, production readiness, or production authority.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement UAA-P1-080 API Route Classification And Public/Protected
Inventory as the next documented milestone after UAA-P1-079.

Review these documents first:
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[openapi_contract.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/api/openapi_contract.md)
[route_inventory.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/api/route_inventory.md)
[ROUTE_STATUS_MANIFEST.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/ROUTE_STATUS_MANIFEST.md)
[OPERATOR_SHELL_GAP_MAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/OPERATOR_SHELL_GAP_MAP.md)

Also inspect SPECS.md, specs.md, SDLC.md, sdlc.md if present. If absent, note
that AGENTS.md and the listed docs are the active process/spec guidance.

Subagent plan:
- Use one read-only explorer/reviewer for the P1-080 route-classification gap
  and safety review when subagent capacity is available.
- If subagent capacity is exhausted, close stale completed agents and retry
  once. If still blocked, proceed locally and record the attempted delegation.
- Subagents are advisory. The main Codex run owns implementation, integration,
  verification, commit/push, and next-prompt recommendation.

Scope:
- Add explicit route classification vocabulary:
  `public_metadata`, `local_readonly`, `local_sensitive`,
  `mutating_requires_authority`.
- Classify every existing FastAPI route in `/api/manifest`.
- Surface the classification through the existing `/control-center/routes`
  inventory and Control Center API Routes UI.
- Add or update route-status manifest posture so visible Control Center route
  refs can be compared against `/api/manifest`.
- Add docs, schema/verifier coverage, and focused tests.
- Preserve the current OpenAPI path count, stable operation IDs, existing
  side-effect classes, and route behavior.

Non-goals:
- Do not add routes, middleware, auth, sessions, CORS, security headers,
  idempotency enforcement, rate limiting, dependencies, connector writes,
  model/provider calls, shell/subprocess execution, action execution, memory
  writes, Code apply, public beta, public distribution, production readiness,
  or production authority.

Acceptance criteria:
- Every `/api/manifest` route has exactly one route classification from the
  allowed vocabulary.
- `public_metadata` is limited to harmless metadata/status routes.
- `local_readonly` identifies local read-only route inventory/status surfaces
  that do not expose sensitive user/workspace state.
- `local_sensitive` identifies routes that expose or accept sensitive local
  state, previews, validation payloads, evidence, memory, files, model/runtime
  posture, observability, approvals, or connector-adjacent data without
  mutation authority.
- `mutating_requires_authority` identifies mutation-like or authority-bearing
  local routes that must stay exact-scoped, approval-bound, idempotent,
  auditable, rollback-aware, redacted, and tested before product authority is
  claimed.
- `/control-center/routes` and the API Routes UI display classification in
  human-readable form and do not expose raw JSON as the primary UI.
- Route-status manifest backend route refs include classification and tests
  compare those refs with `/api/manifest`.
- Active docs mark UAA-P1-080 complete and keep UAA-P1-081 as the next
  planned/queued API boundary-hardening milestone.

Review/fix:
- Perform adversarial self-review for route/OpenAPI drift, broad auth claims,
  false public exposure claims, hidden production readiness, classification
  gaps, route-status mismatch, unsafe product copy, and redaction/evidence
  leakage.
- Fix P0/P1 findings before hardening.

Hardening:
- Run focused route/API tests:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py -q`
- Run the P1-080 verifier.
- Run OpenAPI, documentation integrity, and frontend safety checks:
  `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
  `.venv/bin/python scripts/verify_documentation_integrity.py`
  `.venv/bin/python scripts/verify_control_center_frontend.py`
- Run `make frontend-check` if frontend files change.
- Run `git diff --check`.

Commit/push:
- Stage only files changed for UAA-P1-080.
- Commit with message: `implement UAA-P1-080 API route classification`.
- Push the current branch. Do not force push.

Next prompt:
- After commit/push succeeds, recommend or execute UAA-P1-081 Centralized
  FastAPI Security Headers if the conveyor continues and the scope remains safe.
- Use an incremental UAA-P1-080.1 only if route classification cannot be
  completed safely in one commit.
```

## 2. Frontend-Only Safe Control Center Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: [describe Control Center UI task].

Scope: frontend only under apps/control-center unless docs/tests require
updates. Do not add backend routes, dependencies, runtime authority, connector
runtime, shell/browser/plugin/mobile/remote execution, credential collection,
provider/model authority, memory writes, or context injection.

Read first: AGENTS.md, docs/control_center/OPERATOR_SHELL_GAP_MAP.md,
docs/control_center/PRODUCT_LANGUAGE_RULES.md,
docs/kanban/current_board.md, apps/control-center/src/routes.tsx,
apps/control-center/src/components/OperatorFlowPanels.tsx,
apps/control-center/src/api/client.ts, and apps/control-center/src/App.test.tsx.

Requirements: human-readable UI first; no raw JSON as primary UI; implemented,
planned, partial, blocked, skipped, mock-only, and missing states stay distinct;
every visible action names route posture or says local UI state only.

Tests: run make frontend-check if dependencies are installed. At minimum run
apps/control-center tests relevant to the changed surface.

Final summary must list files changed, tests run, blocked checks, and any
authority boundaries preserved.
```

## 3. Backend Route Contract Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: [describe route or contract task].

Scope: typed contract/API work only as explicitly requested. Do not add broad
runtime authority. Do not add model/provider calls, shell/subprocess execution,
unrestricted network/browser behavior, connector writes, plugin runtime import,
mobile control, hidden memory writes, raw content export, or public release
claims.

Read first: AGENTS.md, src/ultimate_ai_agent/api/app.py,
src/ultimate_ai_agent/api/manifest.py, tests/test_api_manifest.py,
tests/test_control_center_api_routes.py, docs/api/openapi_contract.md, and
docs/control_center/PRODUCT_LANGUAGE_RULES.md.

Requirements: keep OpenAPI operation IDs stable unless explicitly scoped; keep
route side-effect classes accurate; update /api/manifest expectations when
capabilities change; add tests for allowed and denied paths; keep error output
redacted.

Validation: run PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py,
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py, and any
focused tests for the changed route.

Final summary must list files changed, tests run, route/operation ID impact,
side-effect class impact, and blocked items.
```

## 4. Test/Eval Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: [describe test/eval gap].

Scope: tests, fixtures, safe mock data, and verifier updates only. Do not add
runtime authority or product claims.

Read first: AGENTS.md, docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md,
docs/control_center/PRODUCT_LANGUAGE_RULES.md, and the target source/test files.

Requirements: tests must distinguish pass, fail, skipped, blocked, mock,
partial, and not-scoped states where relevant. Do not introduce raw prompt,
response, provider payload, path, log, environment, credential, username,
hostname, or secret-like fixtures.

Validation: run the focused tests and the relevant verifier. If the test suite
cannot run, report the exact blocker.

Final summary must list files changed, tests run, failing/skipped tests, and
remaining risk.
```

## 5. Docs Currentness Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: [describe currentness repair].

Scope: docs/index/currentness only. Do not change runtime behavior,
dependencies, API routes, Control Center controls, or release tags.

Read first: AGENTS.md, README.md, VERSION.md, docs/README.md,
docs/DOCUMENTATION_INDEX.md, docs/canonical/09_roadmap.md,
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md, docs/kanban/current_board.md,
and SECURITY.md.

Requirements: preserve current baseline truth from README.md and VERSION.md;
preserve checkpoint-m168 context; do not claim public distribution, public
beta, production authority, broad autonomy, unrestricted shell/browser/network
authority, connector writes, plugin runtime import, provider/model authority,
or mobile runtime.

Validation: run .venv/bin/python scripts/verify_documentation_integrity.py and
scripts/release/check_version_truth.py if available.

Final summary must list files changed, checks run, stale refs repaired, and
any unresolved baseline ambiguity.
```

## 6. Refactor-With-No-Route-Drift Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: [describe refactor].

Scope: refactor only. Preserve behavior, schemas, route paths, methods,
operation IDs, route side-effect classes, blocked capabilities, declared
capabilities, and API manifest truth unless the task explicitly scopes an API
change.

Read first: AGENTS.md, docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md,
src/ultimate_ai_agent/api/app.py, src/ultimate_ai_agent/api/manifest.py,
tests/test_api_manifest.py, tests/test_control_center_api_routes.py, and
scripts/verify_openapi_contract.py.

Requirements: refactor one low-risk route group first; add tests before moving
complex route families; no new dependencies; no authority expansion.

Validation: run PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py,
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py, and
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py.

Final summary must list files changed, route drift result, operation ID result,
tests run, and blockers.
```

## 7. Safety/Redaction Review Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: review [files/PR/surface] for safety and redaction risks.

Scope: review and targeted fixes only. Prioritize bugs, authority bypass,
unsafe claims, raw evidence leaks, missing tests, and product-language
regressions.

Read first: AGENTS.md, SECURITY.md,
docs/control_center/PRODUCT_LANGUAGE_RULES.md,
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md, and the changed files.

Check for: raw prompt/response/provider payload, raw path/log/environment,
username/hostname, credential/secret-like output, model output as authority,
PolicyEngine bypass, LocalApprovalAuthority bypass, side-effect class drift,
OpenAPI drift, unscoped mutation, connector writes, plugin runtime import,
shell/browser/network/mobile/remote authority, and unsupported public claims.

Validation: run focused tests and redaction/security verifiers where feasible.

Final summary must lead with findings by severity, then tests run, residual
risk, and suggested next fixes.
```

## 8. Founder Workflow Implementation Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement [Morning Briefing / Action Inbox / Memory Review / Evidence
Timeline / Weekly CEO Review] for the Founder Command Center.

Scope: implement the smallest slice needed for the named workflow. Do not add
unrestricted runtime authority, live connector runtime, connector writes,
shell/subprocess execution, browser automation, plugin runtime import, mobile
runtime, model/provider authority, automatic memory writes, context injection,
dependencies, public distribution, or production authority.

Read first: AGENTS.md,
docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md,
docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md,
docs/kanban/founder_command_center_board.md,
docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md,
docs/control_center/OPERATOR_SHELL_GAP_MAP.md,
docs/control_center/PRODUCT_LANGUAGE_RULES.md, and current source/test files
for the target workflow.

Implementation lane: follow
docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md#next-implementation-lane,
starting from the accepted UAA-P1-011 readable-loop baseline: Today product
spine, Evidence history, Memory source/provenance and review decisions, Plans
to Action envelopes, Chat local operator surface, governed Code workbench,
Setup Assistant hardening, first product loop readability, Action Inbox /
approval envelope UX, Morning Briefing skeleton, then read-only email/calendar
integration contracts later.

Requirements: readable product UI first; exact route/status/evidence refs;
blocked states with next safe action; no fake completion; tests for happy,
blocked, denied, and mock/degraded paths.
Use the planning-only permission vocabulary from the MVP spec when relevant:
Observe, Draft, Propose, Approve once, Approve rule, Autopilot micro-scope, and
Kill switch. Naming a mode does not grant authority or bypass PolicyEngine,
LocalApprovalAuthority, scoped milestones, tests, receipts, audit, revocation, or
rollback/safe-disable requirements.
When using these labels in implementation tasks, render Approve once, Approve
rule, Autopilot micro-scope, and Kill switch as planned, blocked, disabled, or
status-only text unless the current task explicitly implements an accepted
backend contract. Do not add enabled controls, action handlers, routes, approval
refs, standing grants, background sessions, connector writes, or
revocation/kill-switch mutations from these labels alone.

Validation: run focused Python tests, make frontend-check when frontend changes,
OpenAPI contract when backend routes change, and documentation integrity when
docs change.

Final summary must list files changed, tests run, skipped checks with reasons,
authority boundaries preserved, and blocked items.
```

## 9. FCC-MAC-001 macOS Setup Assistant Hardening Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: FCC-MAC-001 macOS Setup Assistant hardening.

Goal: harden the existing macOS-first Setup Assistant dry-run/read-only
foundation. Improve truthful blocked states, bounded preview handling,
approval-envelope language, receipt refs, rollback refs, and local prerequisite
visibility without adding setup mutation authority.

Scope: Control Center setup preview, setup assistant contracts/tests, and the
smallest required docs. Treat v0.102.3 as the current code-bearing baseline:
the setup panel and read-only `/control-center/setup-assistant/summary` route
already exist. First inspect what is already implemented, then close only the
remaining hardening gaps.

Do not add installer execution, model download, LaunchAgent install/load/start,
background-service install/load/start, bridge enablement, credential handling,
shell/subprocess execution, receipt persistence, audit persistence, rollback
execution, signed installer readiness, public distribution, public beta,
production authority, model/provider calls, connector runtime, connector
writes, plugin runtime import, browser automation, mobile control, automatic
memory writes, or context injection.

Read first: AGENTS.md, README.md, VERSION.md,
docs/kanban/current_board.md,
docs/kanban/founder_command_center_board.md,
docs/macos/UAA-setup-assistant-plan.md,
docs/control_center/OPERATOR_SHELL_GAP_MAP.md,
docs/control_center/PRODUCT_LANGUAGE_RULES.md,
apps/control-center/src/components/MacOSSetupAssistantPanel.tsx,
apps/control-center/src/api/macosSetupAssistant.ts,
apps/control-center/src/api/types.ts,
apps/control-center/src/mocks/controlCenterData.ts,
apps/control-center/src/App.test.tsx,
tests/test_control_center_api_routes.py, and
tests/test_macos_setup_assistant.py.

Requirements:

- Keep `/setup` and `/control-center/setup-assistant/summary` inspection-only.
- Make every approval-required setup step show dry-run approval-envelope refs,
  receipt refs, rollback refs, idempotency/stale-state posture, and a next safe
  action.
- Make blocked and not-scoped states explicit for installer actions, model
  downloads, LaunchAgent work, background services, bridges, credentials,
  rollback execution, signed installer/distribution, and production authority.
- Keep model choices as recommendation classes only; do not imply live download,
  model selection authority, or provider/model output authority.
- Ensure bounded terminal/log previews are clearly preview-only, redacted, and
  unable to expose raw paths, raw logs, prompts, transcripts, provider payloads,
  usernames, hostnames, environment dumps, credentials, tokens, or secret-like
  values.
- Improve local prerequisite visibility using existing safe route/status refs
  only, such as health/version/runtime readiness/capability matrix/local model
  readiness refs. Do not add lifecycle controls.
- Use human-readable UI first; no raw JSON as the primary setup UI.
- Preserve route paths, operation IDs, route side-effect classes, API manifest
  truth, and product-language distinctions between implemented, partial,
  planned, blocked, skipped, mock-only, and missing states.
- If docs currently describe this work as future even though v0.102.3 already
  implements the baseline, update only the smallest relevant text so the board
  and setup plan distinguish baseline-done from remaining hardening follow-up.

Suggested implementation approach:

1. Audit the current setup assistant route, contracts, mock data, frontend
   normalization, panel rendering, and tests.
2. Add or tighten focused tests before changing UI/contract behavior where
   feasible.
3. Improve setup panel copy and metadata rendering so dry-run approval
   envelopes, receipt refs, rollback refs, bounded previews, and blockers are
   obvious to an operator.
4. Update route/status docs only if the code behavior or currentness language
   changes.

Validation: run focused setup assistant tests first:
PYTHONPATH=src .venv/bin/python -m pytest tests/test_macos_setup_assistant.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py

If frontend files change, run:
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py

If backend route contracts change, run:
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py

If docs change, run:
.venv/bin/python scripts/verify_documentation_integrity.py

Final summary must list files changed, tests/verifiers run, skipped checks with
reasons, setup authority boundaries preserved, route/operation ID impact,
side-effect class impact, and remaining blocked items.
```

## 10. Today-Spine And Founder Loop V1 Milestone Conveyor Prompt

Use this prompt to run the UAA-P1-067 through FCC-V1-007 conveyor. The
conveyor is repo-local process guidance only. It does not grant runtime
authority, connector authority, provider/model authority, unrestricted shell,
public beta, public distribution, or production readiness.

Current conveyor status: UAA-P1-067 through UAA-P1-080 are complete when the
active docs show UAA-P1-080 API Route Classification And Public/Protected
Inventory has landed with its contract, schema, fixture, verifier, tests,
Control Center visibility, and pushed commit. UAA-P1-081 and UAA-P1-082 are
complete when active docs show centralized FastAPI security headers and
explicit loopback CORS allowlisting have landed with verifier/test evidence and
pushed commits. UAA-P1-083 is complete when active docs show the local
protected-route bearer gate has landed with verifier/test evidence and a pushed
commit. UAA-P1-084 is complete when active docs show the mutating-route
idempotency header gate has landed with verifier/test evidence and a pushed
commit. UAA-P1-085 is complete when active docs show targeted local
fixed-window rate limits have landed with verifier/test evidence and a pushed
commit. UAA-P1-086 is complete for API boundary-hardening enforcement tests,
UAA-P1-087.1 is complete for local launcher dual-surface boot readiness, and
UAA-P1-087.2a is complete for the private trial packet/read-only tuning
surface, and UAA-P1-087.2b is complete for the private trial findings capture
and acceptance ledger, and UAA-P1-087.2c is complete for the unanswered manual
review scaffold. Full UAA-P1-087.2 in-person private UI functional tuning and
UAA-P1-087.3 native SwiftUI boot cockpit planning/source-only scaffold are
deferred until more Founder Loop implementation exists and accepted or revised
local/private findings can be recorded later. FCC-V1-000 Control Center
Release Surface Manifest is complete for route-status truth, manifest/schema,
verifier, and focused tests without adding backend routes or runtime authority.
The conveyor now advances through the remaining FCC-V1 productization lane:
FCC-V1-001 API Perimeter For Real Mutations, FCC-V1-002 Action Inbox Backend State Machine,
FCC-V1-003 Founder Loop V1 Vertical Slice, FCC-V1-004 Chat Durable Receipt And
Handoff, FCC-V1-005 Memory Review Decisions, FCC-V1-006 Evidence Timeline
Productization, and FCC-V1-007 Promotion And Proof Lane before broader
P2/provider, packaging, public distribution, or commercialization expansion.
The conveyor
auto-advances after each successful milestone commit/push until the active
bounded sequence is complete, verified, and pushed. Do not stop after merely
recommending the next prompt; create and execute the next milestone prompt in
the same Codex run until all conveyor milestones are complete or a real
blocker/safety split requires stopping.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement the next Today-spine Founder Command Center milestone in the
documented conveyor. Start with UAA-P1-067 Today-Spine Founder Command Center
beta-readiness planning unless the reviewed docs show UAA-P1-067 is already
complete. Then choose the next incomplete documented milestone in order:
UAA-P1-068, UAA-P1-069, UAA-P1-070, UAA-P1-071, UAA-P1-072, UAA-P1-073,
UAA-P1-074, UAA-P1-075, UAA-P1-076, UAA-P1-077, UAA-P1-078, then UAA-P1-079.
Stop after UAA-P1-079 is complete and verified. Do not invent milestones after
UAA-P1-079 unless the active roadmap explicitly documents them.

If a later accepted prompt starts the API Boundary Hardening Lane, use this
extension order after UAA-P1-079: UAA-P1-080, UAA-P1-081, UAA-P1-082,
UAA-P1-083, UAA-P1-084, UAA-P1-085, UAA-P1-086, then UAA-P1-087.1,
UAA-P1-087.2a, UAA-P1-087.2b, and UAA-P1-087.2c. Treat full UAA-P1-087.2 and
UAA-P1-087.3 as deferred unless active docs later promote them with enough
Founder Loop implementation evidence for manual review.

If active docs show the Founder Loop V1 productization lane is accepted, use
this extension order after UAA-P1-087.2c or the current prerequisite breakpoint:
FCC-V1-000, FCC-V1-001, FCC-V1-002, FCC-V1-003, FCC-V1-004, FCC-V1-005,
FCC-V1-006, and FCC-V1-007. Stop only after FCC-V1-007 is complete and
verified, or when a real blocker or safety split prevents safe continuation.

Review the following documents first:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[FOUNDER_LOOP_V1_MILESTONES.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md)

Also review repo process/spec guidance before choosing scope:
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[agents_md_support.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/standards/agents_md_support.md)
[RELEASE_PROCESS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/maintenance/RELEASE_PROCESS.md)

If present, also review `SPECS.md`, `specs.md`, `SDLC.md`, `sdlc.md`, or the
closest task-specific spec, ADR, schema, standards, or process docs discovered
with `rg --files`. Treat these documents as contributor guidance, not runtime
configuration or product authority.

When no literal spec/SDLC file exists, treat these as the fallback
process/spec baseline when relevant:
[05_development_workflow.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/canonical/05_development_workflow.md)
[definition_of_ready.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_ready.md)
[definition_of_done.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_done.md)
[foundation_first_build_policy.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/operating/foundation_first_build_policy.md)
[PRODUCT_LANGUAGE_RULES.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/PRODUCT_LANGUAGE_RULES.md)

Milestone selection:
1. Inspect the active docs and git history/status.
2. Identify the first incomplete milestone in the documented order.
3. If the selected milestone is too large for one safe change, create an
   incremental prompt for the smallest useful slice using suffixes such as
   UAA-P1-067.1, UAA-P1-067.2, etc. Incremental prompts must stay inside the
   parent milestone acceptance criteria and must not create competing roadmap
   truth.
4. If the selected milestone can be completed in one pass, create the exact
   implementation prompt for that milestone.

Subagent usage:
- Use subagents for nontrivial conveyor milestones. At minimum, spawn a scoped
  explorer or reviewer for independent gap/safety review before hardening.
  Skip subagents only for tiny mechanical edits, and record the reason.
- Good subagent splits: current-state explorer, contract/test gap explorer,
  adversarial product-language reviewer, or redaction/evidence reviewer.
- Default conveyor subagents are read-only inspectors/reviewers. Any
  write-capable subagent requires an explicit disjoint file set and the same
  AGENTS/process/invariant brief.
- Subagents are advisory unless explicitly assigned a disjoint write set. They
  must not revert user or other-agent changes, create competing roadmap truth,
  add runtime authority, or bypass policy/approval/OpenAPI/redaction checks.
- Each subagent prompt must cite the relevant `AGENTS.md`, spec/process docs,
  scope, non-goals, and authority/redaction/product-claim boundaries.
- The main Codex run owns final integration, verification, commit/push, and the
  next-prompt recommendation. Do not treat subagent output as product truth
  without reviewing it against the active docs and verifiers.

Before editing, create the milestone prompt in the repo:
- Add or update the relevant section in
  docs/codex/CODEX_EXECUTION_PROMPTS.md, or add a subordinate prompt artifact
  only if the prompt is too large for that file.
- The created prompt must include: scope, non-goals, files to read, acceptance
  criteria, implementation steps, subagent review plan, review/fix phase,
  hardening phase, validation commands, commit/push instructions, and the
  next-prompt recommendation rule.
- After creating the prompt, execute that created prompt in the same Codex run
  unless doing so would be unsafe, ambiguous, or too large. If execution is not
  safe, stop after creating the prompt and explain the blocker.

Global safety boundaries:
- Do not add production authority, public beta, public distribution, broad
  autonomy, unrestricted shell/subprocess execution, unrestricted network or
  browser automation, connector writes, plugin runtime import, mobile control,
  provider/model authority, automatic memory writes, hidden context injection,
  raw prompt/response/provider payload/path/log evidence, credential material,
  usernames, hostnames, environment dumps, or secret-like durable output.
- Preserve Python Agent Core as the brain. Control Center and OpenWebUI are
  shells.
- Mutating paths must be exact-scoped, approval-bound, idempotent, auditable,
  rollback-aware, redacted, and tested.
- Product behavior must not live only in React state. UI-only state is limited
  to presentation concerns.

Execution workflow:
1. Review: read the required docs, process/spec guidance, and closest
   task-specific specs/ADRs/schemas/standards; inspect current code/tests/docs
   for the selected milestone; and write down the exact current gap.
2. Delegate: for nontrivial milestones, spawn one or more scoped subagents for
   current-state inspection, contract/test gaps, or adversarial safety review.
   Continue non-overlapping local work while they run. Integrate only reviewed
   findings that fit the active docs and repo invariants.
3. Implement: make the smallest scoped changes needed to satisfy the selected
   milestone or incremental slice.
4. Review and fix: perform an adversarial self-review before hardening. Look
   for stale roadmap truth, unsafe product claims, route/OpenAPI drift,
   authority expansion, raw/private evidence leaks, missing tests, UI-only
   product behavior, broken CLI/API parity, and unclear next-prompt state.
   Include relevant subagent findings in this review. Fix all P0/P1 issues
   found by the review before moving on.
5. Harden: add or tighten tests, static verifiers, docs integrity checks,
   redaction checks, frontend checks, OpenAPI/API manifest checks, or Foundation
   Gate report-only checks as appropriate for the changed files.
6. Verify: run focused tests first, then required verifiers. At minimum for
   docs/planning changes run:
   .venv/bin/python scripts/verify_documentation_integrity.py
   git diff --check
   For backend route/API changes also run:
   PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
   PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
   For frontend changes also run:
   make frontend-check
   .venv/bin/python scripts/verify_control_center_frontend.py
7. Commit and push: only after checks pass, inspect git status, stage only the
   files changed for this milestone, commit with a concise milestone message,
   and push the current branch. Do not stage unrelated user changes. If push is
   blocked by credentials, remote state, branch policy, or failing checks, do
   not force it; report the blocker and leave the work unpushed.
8. Advance: after commit/push succeeds, immediately identify the next
   incomplete documented milestone, create/update its prompt, and execute it in
   the same run. Add or update a "Next prompt" section in
   docs/backlog/codex_recommendation_log.md only as conveyor state, not as a
   stopping point. Stop only when:
   - all milestones through UAA-P1-079 are complete and verified for the
     Today-spine conveyor, or all milestones through UAA-P1-087.3 are complete
     and verified when the API boundary/private-operator-trial lane is active,
     or all milestones through FCC-V1-007 are complete and verified when the
     Founder Loop V1 productization lane is active,
   - the next slice is too large or unsafe and needs an incremental prompt that
     cannot be executed safely in the same run,
   - verification, push, dependencies, or repo state blocks progress, or
   - the user asks to pause/stop.

Definition of complete for a milestone:
- The scoped acceptance criteria in the reviewed roadmap/board/task docs are
  satisfied.
- Active docs and boards mark the milestone truthfully.
- Relevant tests/verifiers pass or blockers are reported.
- Product language distinguishes implemented, partial, planned, blocked,
  skipped, mock-only, and missing states.
- The final summary records literal spec/SDLC files found or absent, process
  docs consulted or skipped with reasons, subagents used or skipped with
  reason, and confirms no runtime authority, raw private evidence, public beta,
  public release, production readiness, or production authority claim was
  introduced.
- No unsafe authority or raw/private evidence was introduced.
- A commit was created and pushed, or the exact push blocker is recorded.
- The next prompt is either created and executed in the same run or an exact
  blocker explains why auto-advance stopped.

Initial milestone prompt to create and execute:

Task: UAA-P1-067 Today-Spine Founder Command Center private beta-readiness
planning only.

Goal: complete the planning/currentness milestone that defines the conveyor
from UAA-P1-067 through UAA-P1-079. Make Today the product spine, keep robust
reviewed memory as the differentiator, and ensure every documented module feeds
Today, Actions, Evidence, and Memory rather than claiming standalone completion.

Scope: docs, boards, prompt library, recommendation log, and verifier
alignment only unless the reviewed docs already scope a focused test/verifier
change. Do not add backend routes, frontend controls, dependencies, runtime
behavior, connector runtime, provider/model calls, shell/browser/plugin/mobile
authority, automatic memory writes, context injection, public beta, public
distribution, or production authority.

Read first:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[agents_md_support.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/standards/agents_md_support.md)
[RELEASE_PROCESS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/maintenance/RELEASE_PROCESS.md)

If present, also read `SPECS.md`, `specs.md`, `SDLC.md`, `sdlc.md`, and the
closest task-specific spec, ADR, schema, standards, or process docs discovered
with `rg --files`. Treat these documents as contributor guidance, not runtime
configuration or product authority. When no literal spec/SDLC file exists,
consult the fallback process/spec docs listed in the global conveyor prompt
when relevant.

Acceptance criteria:
- When UAA-P1-067 is still incomplete, active docs mark it as the
  planning/currentness milestone in progress; after completion, active docs
  mark it complete and promote the next incomplete documented milestone.
- The milestone conveyor order is explicit: UAA-P1-068 Today spine,
  UAA-P1-069 Evidence history, UAA-P1-070 memory provenance, UAA-P1-071 Memory
  Review decisions, UAA-P1-072 business memory and quality, UAA-P1-073 Plans to
  Action envelopes, UAA-P1-074 Chat operator surface, UAA-P1-075 governed Code,
  UAA-P1-076 cross-surface memory intake, UAA-P1-077 memory-to-loop binding,
  UAA-P1-078 private beta-readiness gate, and UAA-P1-079 later intent
  understanding.
- The docs explain that Today is the product spine and every module feeds
  Today, Actions, Evidence, and Memory.
- The docs explain that Evidence must read as history, Plans must produce
  reviewable Action envelopes, Chat must be a real local operator surface, and
  Code must be narrower than Goat but better governed.
- UAA-P1-066 remains a queued read-only local model support lane and does not
  displace the product spine.
- The prompt conveyor is recorded so future Codex runs create, execute, review,
  harden, commit, push, and then auto-advance to the next documented milestone
  until all documented milestones are complete.
- Nontrivial conveyor runs use at least one scoped subagent for gap review,
  contract/test review, or adversarial safety/product-language review before
  hardening. Subagent findings are advisory and must preserve the same
  authority, redaction, OpenAPI, policy, and product-language boundaries.

Review/fix phase:
- After edits, perform an adversarial review for stale milestone numbering,
  unsafe beta/public/production claims, missing stop condition, missing commit
  and push instructions, missing next-prompt recommendation rule, and any text
  implying runtime authority.
- Fix issues before hardening.

Hardening/validation:
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run .venv/bin/python scripts/verify_uaa_p1_065_founder_command_center_review_cleanup.py
- Run .venv/bin/python scripts/verify_agent_module_maturity_map.py if maturity
  docs changed.
- Run focused pytest for any verifier changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-067.
- Commit with message: docs: add UAA-P1-067 milestone conveyor
- Push the current branch. If push is blocked, report the exact blocker and do
  not force-push.

Auto-advance rule:
- If UAA-P1-067 is incomplete, create and execute UAA-P1-067.1 with the same
  review-doc list and the remaining acceptance criteria.
- If UAA-P1-067 is complete, create and execute UAA-P1-068 Today Product Spine
  Contract with the same review-doc list in the same run unless blocked.
```

## 11. UAA-P1-068 Today Product Spine Contract Prompt

Use this prompt when UAA-P1-067 is complete and UAA-P1-068 is the first
incomplete Today-spine milestone. This prompt is contract/test/docs first and
auto-advances after successful commit/push.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: UAA-P1-068 Today Product Spine Contract.

Goal: define and implement the shared Today spine contract that every module
must feed: Today, Actions, Evidence, and Memory. Today must expose priorities,
blockers, follow-up posture, plan/action state, memory review count,
stale-source posture, and next safe actions. Loop visibility is necessary but
not sufficient for completion; normal Definition of Done, typed contracts,
redaction, policy/approval boundaries, OpenAPI/API manifest checks when routes
change, CLI or repo-local inspection paths, and tests still apply.

Read first:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[agents_md_support.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/standards/agents_md_support.md)
[definition_of_ready.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_ready.md)
[definition_of_done.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_done.md)
[foundation_first_build_policy.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/operating/foundation_first_build_policy.md)
[PRODUCT_LANGUAGE_RULES.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/PRODUCT_LANGUAGE_RULES.md)

If present, also read SPECS.md, specs.md, SDLC.md, sdlc.md, and the closest
task-specific spec, ADR, schema, standards, or process docs discovered with
rg --files. Treat these documents as contributor guidance, not runtime
configuration or product authority.

Subagent plan:
- Use at least one read-only subagent for contract/test gap review.
- Use at least one read-only subagent for adversarial product-language,
  redaction, and authority review.
- Subagents are advisory. The main Codex run owns integration, verification,
  commit/push, and auto-advance.

Scope:
- Existing Today summary route/payload, TypeScript API type, read-only Today
  render, docs, schema, focused tests, and verifier.
- Do not add a new route, operation ID, side-effect class, backend mutation,
  frontend mutation control, connector runtime, account auth, automatic
  refresh, background execution, model/provider authority, automatic memory
  write, hidden context injection, raw private evidence, public beta, public
  distribution, production readiness, or production authority.

Acceptance criteria:
- Existing `GET /control-center/today/summary` exposes
  `contract-ref:today-product-spine:v1`.
- Required loop surfaces are Today, Actions, Evidence, and Memory.
- Required Today signals are priorities, blockers, follow-ups or follow-up
  posture, plan/action state, memory review count, stale-source posture, and
  next safe actions.
- Every module feed row has four loop outputs, safe current refs or missing
  contract refs, a partial/planned/blocked/implemented status, and
  `standalone_complete_allowed: false`.
- Completion contract says loop visibility is necessary but not sufficient.
- Fixtures are synthetic safe refs only and deny raw prompts, raw responses,
  raw provider payloads, raw paths, raw logs, account IDs, usernames,
  hostnames, credential material, and secret-like values.
- Today renders the contract read-only without approve/run/send/write/sync/
  execute controls.
- Active docs mark UAA-P1-068 complete and promote UAA-P1-069 Evidence History
  Grammar as the next incomplete milestone.

Review/fix:
- Perform adversarial review for standalone-complete claims, unsafe beta or
  production language, route/OpenAPI drift, raw evidence leakage, authority
  expansion, and UI mutation controls.
- Fix P0/P1 issues before hardening.

Hardening:
- Run PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_founder_loop_storage.py
  tests/test_control_center_founder_loop_api.py
  tests/test_uaa_p1_068_today_product_spine_contract.py
- Run .venv/bin/python scripts/verify_uaa_p1_068_today_product_spine_contract.py
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run make frontend-check when frontend files changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-068 plus any conveyor auto-advance fix
  intentionally made for this run.
- Commit with message: implement UAA-P1-068 today product spine contract
- Push the current branch.

Auto-advance:
- After commit/push succeeds, immediately create/update and execute the
  UAA-P1-069 Evidence History Grammar prompt in the same run unless blocked.
- Stop only for an exact blocker, unsafe scope split, failed verification,
  failed push, or user pause/stop.
```

## 18. UAA-P1-074 Chat Local Operator Surface Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: execute UAA-P1-074 Chat Local Operator Surface.

Goal: make first-party Control Center Chat a real local operator surface. It
should send a redacted local turn through the governed local gateway, show
model/runtime/auth/tool-denial truth, produce safe evidence refs, and hand off
to Plans or Actions as proposals only.

Read first:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[agents_md_support.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/standards/agents_md_support.md)
[definition_of_ready.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_ready.md)
[definition_of_done.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_done.md)
[PRODUCT_LANGUAGE_RULES.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/PRODUCT_LANGUAGE_RULES.md)
[UAA_P1_073_PLANS_ACTION_ENVELOPES.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/UAA_P1_073_PLANS_ACTION_ENVELOPES.md)

If present, also read SPECS.md, specs.md, SDLC.md, sdlc.md, and the closest
task-specific spec, ADR, schema, standards, or process docs discovered with
rg --files. Treat these documents as contributor guidance, not runtime
configuration or product authority.

Subagent plan:
- Use at least one read-only subagent for contract/test gap review if available.
- Use at least one read-only subagent for adversarial product-language,
  redaction, and authority review if available.
- Subagents are advisory. The main Codex run owns integration, verification,
  commit/push, and auto-advance.

Scope:
- Existing `/v1/chat/completions` local gateway, existing Control Center Chat
  panel, existing Today summary route, Founder Loop Evidence Timeline,
  TypeScript API types/client, docs, schema, focused tests, and verifier.
- Do not add a provider SDK call, web fetch, tool execution, automatic memory
  write, hidden context injection, connector write, shell/subprocess execution,
  action execution, approval grant capture, public beta, public distribution,
  production readiness, or production authority.

Acceptance criteria:
- `core.chat` exposes `contract-ref:chat-local-operator-surface:v1`.
- Today summary exposes Chat local operator contract ref, turn ref, route ref,
  model ref, runtime truth, auth truth, tool-denial truth, safe evidence refs,
  Plans handoff ref, Actions handoff ref, surface bindings, blocked-state refs,
  and denied authority posture.
- Control Center `/chat` can send a redacted local turn through the local
  gateway and show route/model/runtime/auth/tool-denial truth without showing
  completion body content.
- Chat handoff refs are proposal refs only and do not mutate Plans, Actions, or
  Memory.
- Evidence Timeline records Chat local operator history with safe refs and all
  authority blocked states.
- OpenWebUI remains a secondary local/dev shell, not product state owner.
- Active docs mark UAA-P1-074 complete and promote UAA-P1-075 Governed Code
  Workbench V1 as the next incomplete milestone.

Review/fix:
- Perform adversarial review for model output becoming implied truth,
  approval evidence, memory, or execution authority; route/auth/tool-denial
  truth being hidden; handoff refs becoming mutations; unsafe content leakage;
  provider/tool/connector/shell authority creep; route/OpenAPI drift; and unsafe
  beta/production language.
- Fix P0/P1 issues before hardening.

Hardening:
- Run PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_uaa_p1_074_chat_local_operator_surface.py
  tests/test_founder_loop_storage.py
  tests/test_control_center_founder_loop_api.py
- Run .venv/bin/python scripts/verify_uaa_p1_074_chat_local_operator_surface.py
- Run .venv/bin/python -c "import scripts.verify_all as v; v.verify_uaa_p1_074_chat_local_operator_surface()"
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
- Run make frontend-check when frontend files changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-074 plus any conveyor auto-advance fix
  intentionally made for this run.
- Commit with message: implement UAA-P1-074 chat local operator surface
- Push the current branch.

Auto-advance:
- After commit/push succeeds, immediately create/update and execute the
  UAA-P1-075 Governed Code Workbench V1 prompt in the same run unless blocked.
- Do not stop with only a next-prompt recommendation. Stop only for an exact
  blocker, unsafe scope split, failed verification, failed push, or user
  pause/stop.
```

## 19. UAA-P1-075 Governed Code Workbench V1 Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: execute UAA-P1-075 Governed Code Workbench V1.

Goal: make Code narrower than Goat but better governed through repo-local
proposal scope, safe diff summary refs, validation plan/result refs, exact
approval requirement refs, expected apply and rollback receipt refs, and
Evidence Timeline binding.

Read first:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[agents_md_support.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/standards/agents_md_support.md)
[definition_of_ready.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_ready.md)
[definition_of_done.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_done.md)
[PRODUCT_LANGUAGE_RULES.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/PRODUCT_LANGUAGE_RULES.md)
[UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/UAA_P1_074_CHAT_LOCAL_OPERATOR_SURFACE.md)

If present, also read SPECS.md, specs.md, SDLC.md, sdlc.md, and the closest
task-specific spec, ADR, schema, standards, or process docs discovered with
rg --files. Treat these documents as contributor guidance, not runtime
configuration or product authority.

Subagent plan:
- Use at least one read-only subagent for contract/test gap review if available.
- Use at least one read-only subagent for adversarial product-language,
  redaction, and authority review if available.
- Subagents are advisory. The main Codex run owns integration, verification,
  commit/push, and auto-advance.

Scope:
- Existing Today summary route, Founder Loop Evidence Timeline, Python Agent
  Core contract code, TypeScript API types/mocks, docs, schema, focused tests,
  and verifier.
- Do not add a new backend route, OpenAPI operation, apply execution, approval
  grant capture, direct file-write runtime, unrestricted shell,
  shell/subprocess execution, remote execution, broad coding-agent autonomy,
  provider SDK call, web fetch, connector write, diff body storage, memory
  write, hidden context injection, public beta, public distribution,
  production readiness, or production authority.

Acceptance criteria:
- `core.code` exposes `contract-ref:governed-code-workbench:v1`.
- Today summary exposes governed Code contract ref, proposal ref, repo scope
  ref, safe diff summary ref, validation plan/result refs, approval
  requirement ref, expected apply and rollback receipt refs, evidence refs,
  idempotency ref, surface bindings, blocked-state refs, and denied authority
  posture.
- Evidence Timeline records governed Code proposal history with proposed,
  approved, happened, changed, undoable, stale, and blocked answers.
- The happened/changed history makes clear that no files changed and no repo,
  connector, shell, model, memory, or task state changed.
- Control Center types/mocks can display the Code module feed as implemented
  but apply-blocked.
- Active docs mark UAA-P1-075, UAA-P1-076, UAA-P1-077, and UAA-P1-078
  complete, then promote UAA-P1-079 User Intent Understanding V1 as the next
  incomplete milestone.

Review/fix:
- Perform adversarial review for implied apply authority, approval refs becoming
  execution grants, raw diff/file/path leakage, shell/subprocess authority
  creep, provider/tool/connector authority creep, route/OpenAPI drift, and
  unsafe beta/production language.
- Fix P0/P1 issues before hardening.

Hardening:
- Run PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_uaa_p1_075_governed_code_workbench.py
  tests/test_founder_loop_storage.py
  tests/test_control_center_founder_loop_api.py
  tests/test_control_center_api_routes.py
- Run .venv/bin/python scripts/verify_uaa_p1_075_governed_code_workbench.py
- Run .venv/bin/python -c "import scripts.verify_all as v; v.verify_uaa_p1_075_governed_code_workbench()"
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
- Run make frontend-check when frontend files changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-075 plus any conveyor auto-advance fix
  intentionally made for this run.
- Commit with message: implement UAA-P1-075 governed code workbench
- Push the current branch.

Auto-advance:
- After commit/push succeeds, immediately create/update and execute the next
  incomplete Today-spine milestone prompt in the same run unless blocked.
- Do not stop with only a next-prompt recommendation. Stop only for an exact
  blocker, unsafe scope split, failed verification, failed push, or user
  pause/stop.
```

## 15. UAA-P1-071 Memory Review Decision Capture Prompt

```text
review the following documents:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)

Implement UAA-P1-071 - Memory Review Decision Capture.

Also read AGENTS.md. If present, read SPECS.md, specs.md, SDLC.md, sdlc.md,
and the closest task-specific spec, ADR, schema, standards, or process docs
discovered with rg --files. Treat these as contributor guidance, not runtime
configuration or product authority.

Subagent plan:
- Use at least one read-only subagent for core-memory decision-contract review.
- Use at least one read-only subagent for adversarial product-language,
  redaction, mutation-authority, and UI affordance review.
- Subagents are advisory. The main Codex run owns integration, verification,
  commit/push, and auto-advance.

Scope:
- Python core memory review-decision contract, existing
  `GET /control-center/today/summary` memory review payload, TypeScript API
  types, read-only Memory surface visibility, docs, schema, focused tests, and
  verifier.
- Decision states: accept, correct, reject, defer, merge, supersede, and
  forget-request. The wire-safe value may be `forget_request`.
- Decision metadata must include actor refs, source refs, provenance refs,
  evidence refs, stale-state posture, retention posture, audit refs, receipt
  refs, blocked-state refs, source provenance binding, and denied authority
  flags.
- Do not add a new route, operation ID, side-effect class, backend mutation,
  memory write/delete/export, retention execution, reviewed-recall promotion,
  hidden context injection, accept/correct/reject/defer/merge/supersede/forget
  action buttons, connector runtime, account auth, provider/model calls, browser
  import, external assistant import, CRM sync, public beta, public distribution,
  production readiness, or production authority.

Acceptance criteria:
- `core.memory` exposes `contract-ref:memory-review-decision:v1`.
- Today summary exposes memory review decision contract ref, decision states,
  required ref fields, authority posture, and per-memory-candidate decision
  metadata.
- Decision envelopes bind back to
  `contract-ref:memory-source-provenance:v1`, keep source posture
  `untrusted_until_reviewed`, and use redacted-summary-only status.
- All write/delete/export/context-injection/connector/account/model/provider/
  public-beta/public-distribution/production flags remain denied.
- The Control Center renders decision metadata read-only and does not add
  mutation controls.
- Active docs mark UAA-P1-071 complete and promote UAA-P1-072 Business Memory
  And Memory Quality Controls as the next incomplete milestone.

Review/fix:
- Perform adversarial review for decision labels becoming implied memory writes,
  forget-request becoming implied deletion, accept becoming truth/recall
  authority, source refs bypassing provenance, unsafe raw/private text,
  hidden context injection, connector/account/model authority creep, UI mutation
  affordances, and unsafe beta/production language.
- Fix P0/P1 issues before hardening.

Hardening:
- Run PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_uaa_p1_071_memory_review_decision_capture.py
  tests/test_founder_loop_storage.py
  tests/test_control_center_founder_loop_api.py
- Run .venv/bin/python scripts/verify_uaa_p1_071_memory_review_decision_capture.py
- Run .venv/bin/python scripts/verify_uaa_p1_070_memory_source_provenance_model.py
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
- Run make frontend-check when frontend files changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-071 plus any conveyor auto-advance fix
  intentionally made for this run.
- Commit with message: implement UAA-P1-071 memory review decision capture
- Push the current branch.

Auto-advance:
- After commit/push succeeds, immediately create/update and execute the
  UAA-P1-072 Business Memory And Memory Quality Controls prompt in the same run
  unless blocked.
- Do not stop with only a next-prompt recommendation. Stop only for an exact
  blocker, unsafe scope split, failed verification, failed push, or user
  pause/stop.
```

## 16. UAA-P1-072 Business Memory And Memory Quality Controls Prompt

```text
review the following documents:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)

Implement UAA-P1-072 - Business Memory And Memory Quality Controls.

Also read AGENTS.md. If present, read SPECS.md, specs.md, SDLC.md, sdlc.md,
and the closest task-specific spec, ADR, schema, standards, or process docs
discovered with rg --files. Treat these as contributor guidance, not runtime
configuration or product authority.

Subagent plan:
- Use at least one read-only subagent for core-memory quality-contract review.
- Use at least one read-only subagent for adversarial product-language,
  redaction, mutation-authority, source/provenance, and UI affordance review.
- Subagents are advisory. The main Codex run owns integration, verification,
  commit/push, and auto-advance.

Scope:
- Python core business-memory quality contract, existing
  `GET /control-center/today/summary` memory review payload, TypeScript API
  types, read-only Memory surface visibility, docs, schema, focused tests, and
  verifier.
- Candidate kinds: profile, project, relationship, organization, deal,
  opportunity, promise, follow_up, preference, decision, and commitment.
- Quality states: duplicate, conflict, stale_expired, low_confidence,
  source_missing, evidence_missing, blocked, and reviewed.
- Business memory must feed Today, Action Inbox, Evidence Timeline, and Weekly
  CEO Review as safe refs only.
- Do not add a new route, operation ID, side-effect class, backend mutation,
  memory write/delete/export, reviewed-recall promotion, hidden context
  injection, accept/correct/reject/defer/merge/supersede/forget action buttons,
  quality-control action buttons, connector runtime, account auth, external CRM
  writes, account sync, provider/model calls, browser import, external assistant
  import, public beta, public distribution, production readiness, or production
  authority.

Acceptance criteria:
- `core.memory` exposes `contract-ref:business-memory-quality-controls:v1`.
- Today summary exposes business memory contract ref, candidate kind rows,
  quality state rows, required refs, surface bindings, authority posture, and
  per-memory-candidate quality metadata.
- Memory Review items show candidate kind, quality posture, correction path,
  stale-state posture, retention/delete/export posture, related safe entity
  refs, surface refs, blocker refs, and evidence refs.
- Duplicate, conflict, stale/expired, low-confidence, source-missing,
  evidence-missing, blocked, and reviewed posture are visible without treating
  memory as truth or recall authority.
- All write/delete/export/context-injection/external-CRM/account-sync/
  connector/account/model/provider/public-beta/public-distribution/production
  flags remain denied.
- The Control Center renders business memory metadata read-only and does not
  add mutation controls.
- Active docs mark UAA-P1-072 complete and promote UAA-P1-073 Plans To
  Reviewable Action Envelopes as the next incomplete milestone.

Review/fix:
- Perform adversarial review for quality labels becoming implied memory writes,
  reviewed labels becoming truth/recall authority, duplicate/conflict states
  losing correction path, source/evidence-missing posture bypassing safe refs,
  hidden context injection, external CRM/account-sync authority creep,
  connector/account/model authority creep, UI mutation affordances, and unsafe
  beta/production language.
- Fix P0/P1 issues before hardening.

Hardening:
- Run PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_uaa_p1_072_business_memory_quality_controls.py
  tests/test_founder_loop_storage.py
  tests/test_control_center_founder_loop_api.py
- Run .venv/bin/python scripts/verify_uaa_p1_072_business_memory_quality_controls.py
- Run .venv/bin/python scripts/verify_uaa_p1_071_memory_review_decision_capture.py
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
- Run make frontend-check when frontend files changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-072 plus any conveyor auto-advance fix
  intentionally made for this run.
- Commit with message: implement UAA-P1-072 business memory quality controls
- Push the current branch.

Auto-advance:
- After commit/push succeeds, immediately create/update and execute the
  UAA-P1-073 Plans To Reviewable Action Envelopes prompt in the same run unless
  blocked.
- Do not stop with only a next-prompt recommendation. Stop only for an exact
  blocker, unsafe scope split, failed verification, failed push, or user
  pause/stop.
```

## 17. UAA-P1-073 Plans To Reviewable Action Envelopes Prompt

```text
review the following documents:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)

Implement UAA-P1-073 - Plans To Reviewable Action Envelopes.

Also read AGENTS.md. If present, read SPECS.md, specs.md, SDLC.md, sdlc.md,
and the closest task-specific spec, ADR, schema, standards, or process docs
discovered with rg --files. Treat these as contributor guidance, not runtime
configuration or product authority.

Subagent plan:
- Use at least one read-only subagent for plan/action envelope contract review
  when agent capacity is available.
- Use at least one read-only subagent for adversarial product-language,
  redaction, approval-authority, route/OpenAPI, and UI affordance review when
  agent capacity is available.
- Subagents are advisory. The main Codex run owns integration, verification,
  commit/push, and auto-advance.

Scope:
- Python core planning Action envelope contract, existing
  `GET /control-center/today/summary` plan summaries, existing
  `GET /control-center/actions/inbox` action summaries, TypeScript API types,
  read-only Today/Plans/Actions visibility, docs, schema, focused tests, and
  verifier.
- Review actions: approve, edit, reject, and defer.
- Envelope fields: exact scope ref, side-effect class, risk class, approval
  requirement ref, evidence refs, expected receipt refs, idempotency key ref,
  expiry, rollback ref, safe-disable ref, and blocked-state refs.
- Do not add a new route, operation ID, side-effect class, backend mutation,
  action execution, approval grant capture, connector write, shell/subprocess
  execution, model/provider authority, automatic memory write, hidden context
  injection, raw private evidence, public beta, public distribution, production
  readiness, or production authority.

Acceptance criteria:
- `core.planning` exposes `contract-ref:plans-action-envelope:v1`.
- Today summary exposes Action envelope contract ref, review posture rows,
  required ref fields, required blocked refs, surface bindings, authority
  posture, plan action state, and per-plan envelope metadata.
- Action Inbox exposes Action envelope contract ref, review posture rows,
  authority posture, and per-action envelope metadata.
- Evidence Timeline records plan Action envelope history as safe refs.
- Approve/edit/reject/defer posture is visible without creating action
  execution, approval grant capture, reusable approval authority, connector
  writes, shell/subprocess execution, model/provider authority, memory writes,
  public beta, public distribution, production readiness, or production
  authority.
- The Control Center renders envelope metadata read-only and does not add
  mutation controls.
- Active docs mark UAA-P1-073 complete and promote UAA-P1-074 Chat Local
  Operator Surface as the next incomplete milestone.

Review/fix:
- Perform adversarial review for approval refs becoming implied authority,
  review actions becoming controls, exact scope being too vague, receipts or
  rollback implying execution, shell/subprocess/provider/connector authority
  creep, raw prompt/response/path/log leakage, route/OpenAPI drift, and unsafe
  beta/production language.
- Fix P0/P1 issues before hardening.

Hardening:
- Run PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_uaa_p1_073_plans_action_envelopes.py
  tests/test_founder_loop_storage.py
  tests/test_control_center_founder_loop_api.py
- Run .venv/bin/python scripts/verify_uaa_p1_073_plans_action_envelopes.py
- Run .venv/bin/python -c "import scripts.verify_all as v; v.verify_uaa_p1_073_plans_action_envelopes()"
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
- Run make frontend-check when frontend files changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-073 plus any conveyor auto-advance fix
  intentionally made for this run.
- Commit with message: implement UAA-P1-073 plans action envelopes
- Push the current branch.

Auto-advance:
- After commit/push succeeds, immediately create/update and execute the
  UAA-P1-074 Chat Local Operator Surface prompt in the same run unless blocked.
- Do not stop with only a next-prompt recommendation. Stop only for an exact
  blocker, unsafe scope split, failed verification, failed push, or user
  pause/stop.
```

## 12. UAA-P1-069 Evidence History Grammar Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: execute UAA-P1-069 Evidence History Grammar.

Goal: make Evidence read like history: what was proposed, what was approved,
what happened, what changed, what can be undone, what is stale, and what
remains blocked. Memory, Plans, Chat, Code, and Actions must be able to use the
same grammar for receipts, audits, rollback posture, stale states, and blocked
states.

Read first:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[agents_md_support.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/standards/agents_md_support.md)
[definition_of_ready.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_ready.md)
[definition_of_done.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_done.md)
[PRODUCT_LANGUAGE_RULES.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/PRODUCT_LANGUAGE_RULES.md)
[UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md)

If present, also read SPECS.md, specs.md, SDLC.md, sdlc.md, and the closest
task-specific spec, ADR, schema, standards, or process docs discovered with
rg --files. Treat these documents as contributor guidance, not runtime
configuration or product authority.

Subagent plan:
- Use at least one read-only subagent for contract/test gap review.
- Use at least one read-only subagent for adversarial product-language,
  redaction, and authority review.
- Subagents are advisory. The main Codex run owns integration, verification,
  commit/push, and auto-advance.

Scope:
- Existing `GET /control-center/today/summary` payload, Founder Loop evidence
  timeline model/builder, TypeScript API type, read-only Evidence Timeline
  render, route-status manifest, docs, schema, focused tests, and verifier.
- Do not add a new route, operation ID, side-effect class, backend mutation,
  frontend mutation control, SQLite history table, raw evidence/log/path
  display, rollback execution, approval grant, connector runtime, email or
  calendar fetch, model/provider authority, memory write, hidden context
  injection, public beta, public distribution, production readiness, or
  production authority.

Acceptance criteria:
- Existing Today summary exposes `contract-ref:evidence-history-grammar:v1`.
- Required history states/questions are proposed, approved, happened, changed,
  undoable, stale, and blocked.
- Every evidence timeline item answers all seven questions with bounded safe
  summaries and safe refs.
- Approval refs are identifiers only; rollback refs describe undo posture only.
- Timeline items assert `approval_ref_authority`,
  `rollback_execution_enabled`, `memory_truth_authority`,
  `context_injection_authorized`, and `raw_evidence_included` are false.
- Memory-linked evidence does not claim truth, write authority, or context
  injection.
- `/evidence` renders the grammar read-only without approve/run/send/write/
  sync/rollback/show-raw/reveal-raw controls.
- Route-status manifest names `GET /control-center/today/summary` for
  `navigate-evidence`.
- Active docs mark UAA-P1-069 complete and promote UAA-P1-070 Memory Source
  And Provenance Model as the next incomplete milestone.

Review/fix:
- Perform adversarial review for raw evidence leakage, approval authority
  creep, rollback execution implication, memory-as-truth claims, route/OpenAPI
  drift, unsafe beta or production language, and UI mutation controls.
- Fix P0/P1 issues before hardening.

Hardening:
- Run PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_uaa_p1_069_evidence_history_grammar.py
  tests/test_founder_loop_storage.py
  tests/test_control_center_founder_loop_api.py
  tests/test_control_center_api_routes.py
- Run .venv/bin/python scripts/verify_uaa_p1_069_evidence_history_grammar.py
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
- Run make frontend-check when frontend files changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-069 plus any conveyor auto-advance fix
  intentionally made for this run.
- Commit with message: implement UAA-P1-069 evidence history grammar
- Push the current branch.

Auto-advance:
- After commit/push succeeds, immediately create/update and execute the
  UAA-P1-070 Memory Source And Provenance Model prompt in the same run unless
  blocked.
- Stop only for an exact blocker, unsafe scope split, failed verification,
  failed push, or user pause/stop.
```

## 13. UAA-P1-070 Memory Source And Provenance Model Prompt

```text
You are working only in doncazper/ultimate-ai-agent.

Task: execute UAA-P1-070 Memory Source And Provenance Model.

Goal: make Memory candidates robust enough for beta by defining exactly where
each candidate came from without granting recall truth, memory writes, context
injection, connector runtime, account auth, model/provider authority, public
beta, public distribution, or production authority.

Read first:
[OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/roadmap/OPERATOR_RUNTIME_EXCELLENCE_ROADMAP.md)
[current_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/current_board.md)
[founder_command_center_board.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/kanban/founder_command_center_board.md)
[FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/implementation/FOUNDER_COMMAND_CENTER_PHASE_0_1_TASKS.md)
[FOUNDER_COMMAND_CENTER_MVP_SPEC.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md)
[AGENTS.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/AGENTS.md)
[agents_md_support.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/standards/agents_md_support.md)
[definition_of_ready.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_ready.md)
[definition_of_done.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/definitions/definition_of_done.md)
[PRODUCT_LANGUAGE_RULES.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/PRODUCT_LANGUAGE_RULES.md)
[UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/UAA_P1_068_TODAY_PRODUCT_SPINE_CONTRACT.md)
[UAA_P1_069_EVIDENCE_HISTORY_GRAMMAR.md](/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent/docs/control_center/UAA_P1_069_EVIDENCE_HISTORY_GRAMMAR.md)

If present, also read SPECS.md, specs.md, SDLC.md, sdlc.md, and the closest
task-specific spec, ADR, schema, standards, or process docs discovered with
rg --files. Treat these documents as contributor guidance, not runtime
configuration or product authority.

Subagent plan:
- Use at least one read-only subagent for core-memory contract/test gap review.
- Use at least one read-only subagent for adversarial product-language,
  redaction, unsafe provenance, and authority review.
- Subagents are advisory. The main Codex run owns integration, verification,
  commit/push, and auto-advance.

Scope:
- Python core memory source/provenance contract, legacy source-ref validation
  hardening where safe, existing `GET /control-center/today/summary` memory
  review payload, TypeScript API types, read-only Memory surface visibility,
  docs, schema, focused tests, and verifier.
- Do not add a new route, operation ID, side-effect class, backend mutation,
  memory write/delete/export, review decision capture, accept/correct/reject/
  defer controls, connector runtime, account auth, model/provider calls, browser
  import, external assistant import, cross-surface intake, CRM sync, context
  injection, public beta, public distribution, production readiness, or
  production authority.

Acceptance criteria:
- `core.memory` exposes `contract-ref:memory-source-provenance:v1`.
- Required source kinds are manual note, external assistant review summary,
  local chat summary, local coding summary, task plan, action proposal,
  evidence timeline ref, read-only calendar metadata ref, read-only email
  metadata ref, and CRM-lite business record.
- Every source/provenance candidate requires safe source/provenance/evidence
  refs, safe label or redacted summary ref, review-required posture,
  `untrusted_until_reviewed`, redacted-summary-only posture, stale-state
  posture, blocked states, and reason codes.
- External assistant, local chat, local coding, and local model-derived source
  summaries are untrusted until reviewed.
- Prompt bodies, response bodies, provider bodies, local-path bodies, log
  bodies, account identifiers, usernames, hostnames, credential material,
  token material, and private content are denied from durable evidence.
- Today summary exposes memory source contract ref, required kinds, policy
  rows, denied-content refs, review posture, and per-memory item source
  provenance fields.
- Negative authority flags are false for truth authority, write authority,
  automatic write, context injection, connector runtime, account auth,
  model/provider authority, public beta, public distribution, and production
  authority.
- Active docs mark UAA-P1-070 complete and promote UAA-P1-071 Memory Review
  Decision Capture as the next incomplete milestone.

Review/fix:
- Perform adversarial review for unsafe provenance keys/values, legacy memory
  source gaps, source refs becoming implied authority, hidden context injection,
  connector/account/model authority creep, UI mutation affordances, and unsafe
  beta/production language.
- Fix P0/P1 issues before hardening.

Hardening:
- Run PYTHONPATH=src .venv/bin/python -m pytest
  tests/test_uaa_p1_070_memory_source_provenance_model.py
  tests/test_founder_loop_storage.py
  tests/test_control_center_founder_loop_api.py
- Run .venv/bin/python scripts/verify_uaa_p1_070_memory_source_provenance_model.py
- Run .venv/bin/python scripts/verify_documentation_integrity.py
- Run make frontend-check when frontend files changed.
- Run git diff --check.

Commit/push:
- Stage only files changed for UAA-P1-070 plus any conveyor auto-advance fix
  intentionally made for this run.
- Commit with message: implement UAA-P1-070 memory source provenance model
- Push the current branch.

Auto-advance:
- After commit/push succeeds, immediately create/update and execute the
  UAA-P1-071 Memory Review Decision Capture prompt in the same run unless
  blocked.
- Stop only for an exact blocker, unsafe scope split, failed verification,
  failed push, or user pause/stop.
```
