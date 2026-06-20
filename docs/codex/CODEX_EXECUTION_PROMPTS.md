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
starting from the accepted UAA-P1-011 readable-loop baseline: local Control
Center macOS-first Setup Assistant hardening, first product loop readability,
Action Inbox / approval envelope UX, Morning Briefing skeleton, then read-only
email/calendar integration contracts later.

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
