# Control Center Smoke E2E Report

Status: local smoke completed with findings
Date: 2026-07-01
Branch: `codex/fcc-thread-001-unified-work-thread`
PR: `#88`

This report records a local-only Control Center smoke and hands-on QA pass for
the FCC thread branch. It is not production evidence, not a public release
claim, and not runtime authority. The run used local backend/frontend servers,
safe refs, redacted summaries, and no screenshots, traces, credentials, raw
payloads, raw prompts, raw responses, or provider payloads.

The prompt explicitly requested Computer Use for local product inspection. That
does not change the standing repository boundary: browser/computer automation is
not a UAA runtime capability, and no product authority was added or exercised.

## Summary

- Focused backend, API, verifier, and frontend checks passed.
- The documented local launcher started backend and frontend, but protected API
  routes failed closed until a local bearer was supplied.
- With an ephemeral local bearer, backend read routes for Today, Action Inbox,
  and Morning Briefing returned backend-owned read models.
- Computer Use confirmed that Today, Morning Briefing, Evidence Timeline, Memory
  Review, Chat, and Settings render with honest blocked/degraded/no-authority
  labels.
- Action Inbox and Plans backend reads returned `200`, but the browser UI stayed
  on `Loading local Control Center`; this is the highest-priority UI finding.
- The global degraded banner is broader than the Founder Loop state: provider
  credential/cost posture fallback makes the whole shell look degraded even when
  founder-loop read models are available.
- No provider/model calls, A2A/MCP/browser runtime dispatch, live web fetching,
  connector writes, CRM writes, email/calendar sends, shell execution,
  background autonomy, billing authority, or production authority were added or
  exercised.

## Local Setup

Initial local launcher:

```bash
./scripts/dev/uaa start
```

Observed behavior:

- `/health` returned healthy local API status.
- Protected Control Center API routes returned
  `LOCAL_API_AUTH_NOT_CONFIGURED` without a local bearer.
- This is a safe fail-closed posture, but the local product smoke path needs
  clearer setup guidance.

Manual local bearer smoke:

- A temporary local bearer was generated outside the repository.
- Backend and frontend were started with the bearer in process environment only.
- The bearer value was not written to the report, repository, logs, screenshots,
  or docs.
- The temporary bearer file was removed after the smoke run.
- Local servers were stopped after the run.

Harness note:

- When direct `uvicorn` output was attached to an interactive exec session, API
  access logs accumulated until the session was polled. During that interval,
  route transitions appeared stalled. Future e2e harnesses should prefer the
  repo launcher logs or quiet access logs so stdout backpressure cannot distort
  UI findings.

## Automated Checks

| Check | Result | Notes |
|---|---:|---|
| `git diff --check` | pass | Pre-report diff check. |
| `PYTHONPATH=src .venv/bin/python scripts/verify_control_center_release_surface.py` | pass | Release surface verification passed. |
| `PYTHONPATH=src .venv/bin/python -m pytest tests/test_fcc_thread_001_unified_work_thread.py` | pass | 4 tests passed. |
| `PYTHONPATH=src .venv/bin/python scripts/verify_fcc_thread_001_unified_work_thread.py` | pass | FCC-THREAD-001 verifier passed. |
| `PYTHONPATH=src .venv/bin/python scripts/dev/uaa_founder_loop.py inspect-work-thread` | pass | Safe-ref CLI inspection returned no default state and did not create state. |
| `npm --prefix apps/control-center run test -- --run src/App.test.tsx` | pass | 112 frontend tests passed. |
| `make frontend-check` | pass | Typecheck, lint, Vitest, and build passed; Vite reported existing large chunk warnings. |

Additional post-report documentation and product-language checks are listed in
the verification section after this report is committed.

## Backend Read Smoke

Authenticated local read checks used the same local backend and bearer as the
frontend smoke run.

| Route | Result | Safe summary |
|---|---:|---|
| `/control-center/today/summary` | `200` | `storage_backed_partial_loop`; shared founder-loop state and product-spine contract refs visible. |
| `/control-center/actions/inbox` | `200` | `storage_backed_review_queue`; decision routes are exact-scoped; proposal-only and no-execution states visible. |
| `/control-center/morning-briefing/summary` | `200` | `storage_backed_briefing_skeleton`; email/calendar/connectors/model sources remain blocked. |

The CLI inspection path returned:

- status: `metadata_only_no_state_found`
- storage state: `state_not_found_no_write`
- steps: empty
- authority flags: all false

That is the correct safe posture when no default local state has been written.

## Computer Use Walkthrough

Computer Use was limited to the local Control Center and did not submit forms,
enter credentials, upload files, execute actions, or interact with provider,
connector, email, calendar, CRM, shell, or model-runtime controls.

| Surface | Status | Findings |
|---|---|---|
| Today | rendered | Shows shared founder-loop proof path from Morning Briefing to Weekly Review, scenario refs, decision receipt refs, memory candidate, weekly artifact status, and explicit authority-boundary labels. |
| Morning Briefing | rendered | Shows storage-backed briefing skeleton, Morning Briefing V1 contract ref, blocked email/calendar/notification/provider/model sources, and the Weekly CEO Review V1 summary. |
| Action Inbox | backend ok, UI loading issue | Backend reads returned `200`, but browser route stayed on `Loading local Control Center`. Mutation authority remained unexercised. |
| Evidence Timeline | rendered | Shows backend-owned safe-ref timeline, receipt/audit refs, idempotency refs, and blocked provider/model/runtime/rollback execution. |
| Memory Review | rendered | Shows backend-owned safe-ref review model, a related review candidate, and blocked memory write/context injection/delete/export/CRM sync behavior. |
| Weekly Review | rendered inside briefing/today loop | Shows completed/deferred/rejected/blocked/stale/unresolved counts and ties back to action and evidence refs without claiming production authority. |
| Plans | backend ok, UI loading issue | Backend request wave returned `200`, but browser route stayed on `Loading local Control Center`. |
| Chat | rendered blocked/degraded | Shows local operator chat blocked, `/v1/models` unavailable without local gateway readiness, no exchange body/completion content, and disabled proposal controls. |
| Settings | rendered | Shows provider diagnostics as metadata/guidance only, no credential collection, blocked provider invocation, CostGovernor/budget posture, kill-switch posture, and disabled router dry-run authority. |

Computer Use note:

- A stale browser element index briefly focused an existing non-local tab. No
  click, form entry, credential entry, copy, download, upload, or external-site
  interaction occurred. The run immediately returned to the local Control Center.

## Ad Hoc Browser Route Smoke

An additional headless route smoke was run as an exploratory aid, not as a
release gate. It found no browser console or page errors, but it was not stable
enough to treat as pass/fail evidence because several routes still displayed
global loading text while route data requests were completing.

Observed route states:

- `/today`: expected text not reliably visible before timeout.
- `/briefing`: expected text not reliably visible before timeout.
- `/actions`: loading text remained visible.
- `/evidence`: expected text not reliably visible before timeout.
- `/memory`: expected text not reliably visible before timeout.
- `/plans`: loading text remained visible.
- `/chat`: expected text not reliably visible before timeout.
- `/settings`: loading text remained visible.

This points to a route-level readiness/testability gap rather than hidden
authority. A future Playwright smoke should use stable surface-level loaded
markers and should not depend on global all-route fetch completion.

## Product Findings

1. Action Inbox and Plans need route-loading triage.
   Backend reads are available, but the browser can remain stuck on the local
   loading screen. This should be fixed before treating PR #88 as demo-ready.

2. Local smoke auth setup is safe but awkward.
   Protected API routes fail closed without a local bearer. That is correct, but
   the local launcher or smoke docs should make the dev-only bearer path clearer
   without weakening auth.

3. The global degraded banner is too broad for product proof demos.
   Provider readiness/cost fallback currently paints the whole shell as
   degraded even when backend-owned founder-loop read models render correctly.
   Splitting provider diagnostics from founder-loop health would make the
   product state easier to understand.

4. The Evidence route mixes backend timeline content with older evidence viewer
   cards.
   The older cards are redacted and marked non-authoritative, but the route would
   be clearer if backend-owned timeline content and legacy/mock evidence cards
   were visually separated.

5. Headless e2e needs stable loaded markers.
   The route shell can render navigation and loading text at the same time, which
   makes content-based browser checks noisy. Surface-specific test ids or
   backend-state loaded markers would make smoke tests more reliable.

## Recommendations

- Fix the Action Inbox and Plans loading behavior before marking the branch
  ready.
- Add a dev-only documented local auth smoke path that keeps protected routes
  fail-closed by default.
- Split provider/settings diagnostic degradation from Founder Loop read-model
  health in the top-level banner.
- Add stable loaded markers for Today, Briefing, Actions, Evidence, Memory,
  Plans, Chat, and Settings so Playwright smoke can become a focused gate.
- Keep mutation controls disabled or omitted until exact backend/core/API
  contracts exist.
- Continue using CLI/repo-local inspection for the same backend-owned state; do
  not create a separate frontend truth source.

## Verification

Post-report checks to run:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_product_truth.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_release_surface.py
```

`make verify` should still be run before merge if practical. If skipped, the
skip reason must be recorded in the final PR/reporting summary.

## Authority Boundary

This smoke/e2e pass stayed within no-new-authority scope:

- no provider/model calls.
- no A2A, MCP, or browser runtime dispatch.
- no live web fetching.
- no connector writes.
- no CRM writes, email/calendar sends, or account sync.
- no shell/subprocess execution added to product behavior.
- no memory writes or hidden context injection.
- no background autonomy.
- no billing authority.
- no public beta, public release, production readiness, or broad autonomy claim.
