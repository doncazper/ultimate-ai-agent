# Control Center Browser QA Report - 2026-07-05

## Scope

- Branch: `codex/control-center-ui-browser-qa`
- Base commit at branch start: `0bcbeee1`
- Local URLs tested: `http://127.0.0.1:5173` and `http://127.0.0.1:8000`
- QA surface: Codex in-app Browser as external rendered UI QA only.
- Authority posture: no UAA runtime browser automation, provider/model calls, connector writes, shell execution authority, Git mutation UI, production/public release claims, or broad autonomy were added.

## Browser Sizes

- Desktop: `1440x900`
- Mobile-ish: `390x844`

## Route Matrix

| Route | Browser coverage | Result |
| --- | --- | --- |
| `/` and `/dashboard` | Screenshot, console check, navigation check | Rendered dashboard overview with backend/degraded state labels. |
| `/start` | Screenshot, route transition | Rendered Start Here with partial/backend-owned language. |
| `/today` | Screenshot, route transition | Rendered Today daily-loop surface. |
| `/work-board` | Screenshot, controls, filters, board/list/proof tabs, keyboard move, mobile width | Rendered Work Board cockpit. Local preview controls stayed local-only; persistence remained blocked. |
| `/actions` | Screenshot, lane filters, blocked/proposal/receipt copy | Rendered Action Inbox without executable broad mutation controls. |
| `/chat` | Read-only control inventory, disabled preview/probe controls, authority language check | Model/tool execution stayed disabled and labeled. |
| `/proof` | Screenshot | Rendered Proof Detail with non-authoritative fallback labeling. |
| `/evidence` | Screenshot | Rendered Evidence Timeline with redacted/backend-owned refs. |
| `/memory` | Screenshot, command-palette navigation | Rendered Memory Review and Workbench with non-authoritative fallback copy. |
| `/trust` | Screenshot | Rendered Trust authority posture and blocked/partial states. |
| `/settings` | Screenshot, provider/authority copy inspection | Rendered settings without approve-all or standing authority claims. |
| `/runtime` | Read-only control inventory | Runtime readiness showed status/capability only; no start/install/run button. |
| `/coding` | Screenshot, desktop/mobile smoke | Coding Cockpit rendered context, timeline, diff/proof, chat, terminal, Git, test, and live preview areas as read-only/proposal surfaces. |
| `/crm` | Screenshot | CRM remained fixture-only/blocked as labeled. |

## Controls Tested

- Global navigation links for primary and supporting routes.
- Command palette open, search, filtered route result, close/navigation behavior.
- Work Board search, clear search, Board/List/Proof tabs, severity/status filters, `Add local draft`, `Reset preview`, `Request persistence lane`, card selection, keyboard card move, and drag attempt.
- Action Inbox lane filters for proposal-only, receipt-recorded, and all lanes.
- Chat route read-only preset/input surface and disabled preview/probe/proposal buttons.
- Runtime route status-only controls.
- Settings provider/status/trust links and copy.
- Disabled/blocked controls were inspected for honest state and no accidental mutation.

## Screenshots And Evidence

Screenshots:

- `reports/control_center/assets/2026-07-05-ui-browser-qa/overview-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/start-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/today-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/work-board-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/actions-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/trust-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/coding-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/settings-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/proof-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/evidence-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/memory-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/crm-desktop.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/overview-mobile.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/work-board-mobile.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/actions-mobile.png`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/coding-mobile.png`

Structured evidence:

- `reports/control_center/assets/2026-07-05-ui-browser-qa/browser-console-logs.json`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/interaction-command-palette-navigation.json`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/interaction-work-board-actions.json`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/interaction-work-board-keyboard-move.json`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/interaction-action-inbox-filters.json`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/interaction-chat-read-only.json`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/interaction-runtime-readiness.json`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/interaction-settings-trust-posture.json`

Console/network:

- Captured console warning/error entries were empty across checked routes.
- A manual unauthenticated backend probe returned `401 Unauthorized`; this was expected and not from the Control Center browser session.
- Authenticated browser reads returned protected backend read models, with some lanes honestly labeled `Backend degraded; verify refs`.

## Bugs Found And Fixed

1. SPA route links did not update the active rendered route after same-origin navigation.
   - Fix: added a same-origin navigation listener and `popstate` path sync in `apps/control-center/src/App.tsx`.
   - Test: `updates the active route when same-origin navigation links are clicked`.

2. Cold backend startup could leave the UI in mock fallback after the local backend recovered.
   - Fix: added bounded retry for local backend unavailable mock fallback in `apps/control-center/src/hooks/useControlCenterData.ts`.
   - Test: `keeps retrying cold local backend fallback until backend reads recover`.

3. Full Control Center read fanout could overload the local backend and produce slow or brittle browser/test behavior.
   - Fix: added a bounded read limiter in `apps/control-center/src/api/client.ts`; full-page loads get isolated limiter instances, while helper reads remain bounded.
   - Tests: pending-read, fallback, M15/M16/M17, Work Board, Coding, and summary endpoint focused suites.

4. Local launcher did not pass configured local Control Center bearer values to protected backend/frontend dev services.
   - Fix: pass only `UAA_API_LOCAL_BEARER` to backend and only `VITE_UAA_LOCAL_API_BEARER` to frontend, with sensitive passthrough tracking.
   - Test: `test_launcher_env_passes_configured_local_control_center_bearers`.

5. Work Board widened the mobile body because nested grid children did not have zero min-width constraints.
   - Fix: added layout constraints and contained horizontal overscroll in `apps/control-center/src/styles.css`.
   - Browser retest: mobile body scroll width matched viewport width; board columns retained intentional internal horizontal scrolling.

6. Visual route-state baselines were flaky because fixture HTML was injected before the app finished fallback rendering.
   - Fix: wait for `Mock fallback active` before injecting route-state visual fixtures.
   - Test: `make frontend-visual-check` passed after hardening.

## Tests And Verifiers

| Check | Result |
| --- | --- |
| `git diff --check` | Passed |
| `npm --prefix apps/control-center test -- --run src/App.test.tsx src/api/client.summaryEndpoints.test.ts --testNamePattern "same-origin navigation\|cold local backend\|live local backend connection\|keeps backend checking state\|M15\|M16\|M17\|Work Board\|Coding\|read endpoints"` | Passed, 23 tests |
| `PYTHONPATH=src .venv/bin/python -m pytest tests/test_dev_launcher.py -k "local_control_center_bearers or backend_env_allows"` | Passed, 2 tests |
| `make frontend-check` | Passed, 191 tests and production build; Vite reported the existing large chunk warning |
| `make frontend-visual-check` | Passed, 36 Playwright visual checks |
| `.venv/bin/python scripts/verify_documentation_integrity.py` | Passed |
| `.venv/bin/python scripts/verify_product_truth.py` | Passed |
| `.venv/bin/python scripts/verify_operational_maturity.py` | Passed |
| `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py` | Passed |
| `.venv/bin/python scripts/verify_control_center_release_surface.py` | Passed |

Skipped checks: none intentionally skipped. The OpenAPI verifier was run even though no API routes changed.

## Authority And Product Language

- Mock fallback, degraded backend state, partial surfaces, fixture-only CRM, read-only runtime, and blocked/persistence lanes remained visible.
- No fake success path was added.
- No blocked control was made executable.
- No raw prompt, response, provider payload, local path, token, cookie, credential, or private data was persisted in report text or fixtures.
- Browser QA did not add UAA-owned runtime browser automation authority.

## Remaining Known Issues

Medium:

- Dev-mode React Strict Mode can still make full Control Center read-model settlement feel slow because the app reads many backend-owned surfaces before route content appears. The bounded limiter prevents overload, but future work should split critical route reads from secondary supporting reads.

Low:

- Coordinate drag through the external browser QA surface did not trigger the Work Board HTML5 drag/drop path reliably. Keyboard movement and unit/browser evidence confirmed the safe local preview move path.
- Several live lanes remain intentionally `Backend degraded; verify refs` when optional read models are partial. This is honest product state, not a browser QA failure.

## Correctly Blocked Features

- Browser automation inside UAA runtime.
- Provider/model execution from the Control Center.
- Connector sends/writes.
- Arbitrary shell/subprocess execution.
- Git commit/push/merge controls.
- Work Board durable mutation/persistence lane.
- Coding Cockpit patch apply, command execution, Git mutation, dev-server/browser-preview automation, and multi-agent execution.
- CRM beyond fixture-only blocked shell.
- Public beta, production, or public distribution claims.

## Final Git Status At Report Creation

Branch: `codex/control-center-ui-browser-qa`

Pending scoped changes:

- `apps/control-center/src/App.test.tsx`
- `apps/control-center/src/App.tsx`
- `apps/control-center/src/api/client.ts`
- `apps/control-center/src/hooks/useControlCenterData.ts`
- `apps/control-center/src/styles.css`
- `apps/control-center/tests/visual/control-center.visual.spec.ts`
- `scripts/dev/uaa_launcher.py`
- `tests/test_dev_launcher.py`
- `reports/control_center/2026-07-05-control-center-browser-qa.md`
- `reports/control_center/assets/2026-07-05-ui-browser-qa/*`

Confirmation: the full UI browser QA goal was preserved, no broad runtime authority was added, and intentionally blocked features stayed blocked.
