# Execute Turn Contract Router Productization End To End

Status: operator-run wrapper prompt
Target: enterprise-grade Turn Contract Router productization

Use this prompt in a fresh Codex thread when you want the full
Turn Contract Router productization pack implemented end to end, one phase at a
time, with review/fix/harden gates before every merge.

```text
You are Codex working in the local Ultimate AI Agent repository checkout.

Mission:
Implement the Turn Contract Router productization program end to end so the
enterprise integration branch becomes robust. Work phase-by-phase, review,
fix, harden, test, browser-smoke user-visible behavior, merge each green phase,
then continue until every phase in the productization prompt pack is complete
or a genuine external blocker prevents completion.

Primary prompt pack:
- docs/prompts/turn_contract_router_productization_prompt_pack.md

Supporting prompt/spec docs:
- AGENTS.md
- docs/prompts/turn_contract_router_phase_pack.md
- docs/prompts/turn_contract_router_execute_wrapper.prompt.md
- docs/architecture/TURN_CONTRACT_ROUTER.md
- docs/strategy/AGENT_HARNESS_ROUTING_DISCUSSION.md
- docs/control_center/PRODUCT_LANGUAGE_RULES.md
- docs/control_center/OPERATOR_SHELL_GAP_MAP.md
- docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
- docs/api/openapi_contract.md
- docs/api/route_inventory.md
- src/ultimate_ai_agent/core/decision_router/
- tests/test_turn_contract_router_*.py

Enterprise integration branch policy:
1. Inspect branches before work:
   - `git status --short --branch`
   - `git branch --all`
   - `git remote -v`
   - `gh pr list --state open --limit 50` if `gh` is available.
2. If an exact enterprise integration branch already exists locally or on
   origin, use that branch as the integration target.
3. If no enterprise branch exists, create:
   - `codex/enterprise-turn-router-productization`
   from clean, up-to-date `main`, and use it as the enterprise integration
   branch for this program.
4. Do not merge into `main` unless the operator explicitly asked for `main`.
   Merge phase branches into the enterprise integration branch.
5. Never force-push. Never delete, retarget, move, or mutate historical tags.
6. Preserve unrelated dirty files. If the current checkout is dirty, isolate
   unrelated work with a clearly named stash or worktree before starting.

Persistence rules:
- Do not stop after analysis.
- Do not stop after one phase.
- Do not stop after writing a plan.
- Continue through every phase in order.
- If a test fails, fix the issue and rerun the focused test.
- If review finds a bug, fix it and add regression coverage.
- If browser smoke finds a UI/product issue, fix it before moving on.
- If a phase cannot merge because of an external blocker such as missing
  credentials, unavailable remote, unavailable required service, or branch
  protection, document the blocker precisely, keep the branch/PR ready, then
  continue only to safe independent follow-up work that does not pretend the
  blocked phase is merged.
- Stop only for unsafe authority expansion, destructive conflict requiring
  operator judgment, missing credentials that prevent all further work,
  unrecoverable environment failure, or explicit operator pause/stop.

Program phase order:
1. Prompt 01 - Parallel Preflight Contracts
2. Prompt 02 - Parallel Preflight Engine And Arbitration
3. Prompt 03 - CLI And API Router Preview
4. Prompt 04 - Control Center Router Diagnostics
5. Prompt 05 - Chat/Harness Binding Integration
6. Prompt 06 - Browser Product Smoke Harness
7. Prompt 07 - Review Fix Harden And Regression Sweep
8. Prompt 99 - Final Product Truth And Handoff

For each phase:
1. Read the phase prompt completely from
   `docs/prompts/turn_contract_router_productization_prompt_pack.md`.
2. Create the phase branch from the current enterprise integration branch.
3. Implement only that phase.
4. Keep Python Agent Core as durable truth.
5. Keep Control Center as presentation only.
6. Keep product behavior out of React-only state.
7. Add backend, CLI, API, frontend, docs, and verifier updates required by the
   phase.
8. Add focused tests for the changed files.
9. Review the diff adversarially for:
   - authority creep;
   - over-routing normal prompts into ceremony;
   - under-routing consequential actions;
   - any parallel lane granting authority;
   - raw prompt/response/path/log/credential persistence;
   - missing OpenAPI/API manifest truth;
   - route side-effect misclassification;
   - UI-only durable truth;
   - raw JSON as primary operator UI;
   - unsupported product claims;
   - browser smoke gaps.
10. Fix every actionable issue found in review.
11. Harden with regression tests for every issue fixed.
12. Run focused tests and the phase's listed verification commands.
13. Run broader checks when API, docs, frontend, or route surfaces changed.
14. For frontend or user-visible phases, start the local product and use the
    Codex in-app Browser tool to test the actual UI. If Browser is unavailable,
    use Playwright and record the fallback.
15. Inspect `git diff` and `git status`.
16. Stage only files belonging to the phase.
17. Commit with the exact commit message listed by the phase.
18. Push the phase branch.
19. Open or update a PR targeting the enterprise integration branch.
20. Wait for checks/reviews where available.
21. Fix review/check issues and rerun verification.
22. Merge the PR into the enterprise integration branch only when green.
23. Pull the enterprise integration branch after merge.
24. Continue to the next phase.

Protected behavior that must remain true:
- "How do I build a DIY desk?" routes to `answer_directly`.
- "How do I build a DIY table?" routes to `answer_directly`.
- Normal informational prompts such as "Explain how photosynthesis works" and
  "What is a clean way to organize a closet?" route to `answer_directly`
  without unnecessary ceremony.
- Simple code/explanation prompts route to a useful direct answer posture, not
  operator/action mode.
- Direct/base answers expose no memory, no tools, no planner, no durable state,
  no approval, and no side effects.
- Direct/base answer UI must feel lightweight: no primary approval treatment,
  no warning-heavy blocked state, no unnecessary tool/memory panels, and no
  forced plan unless the user asks for a plan.
- "Design one for my office using what you know" routes to reviewed-memory
  posture with reviewed refs only and no write.
- "Make me a shopping list for this desk" routes to draft/proposal posture.
- "Find current lumber prices near me" routes to read-only/tool-prep posture.
- "Order the materials" routes to approval-required posture.
- "Use my card and book pickup at Home Depot" routes to approval-required
  posture with payment/credential/booking risk.
- "Ask the base answer path: use my card and order this" must not bypass
  approval.
- `execute_approved_action` requires exact approved scope and ExecutorFence
  validation before any future side effect.
- A parallel preflight lane may sense, but it may never grant authority.

Hard authority boundaries:
- Do not add broad runtime authority.
- Do not add direct web fetching.
- Do not add product runtime browser automation.
- Do not add browser clicks/forms/auth/download/upload authority.
- Do not add connector writes.
- Do not add unrestricted shell/subprocess execution.
- Do not add provider SDK sprawl or remote provider authority.
- Do not add plugin runtime import.
- Do not add remote execution.
- Do not add public beta, public release, public distribution, production
  readiness, production deploy, or broad autonomy claims.
- Model/provider/local runtime calls may only be wired if an already merged,
  accepted RuntimeGateway lane exists and the phase explicitly scopes it.

Required verification menu:
Run the focused subset for every phase, then broaden as needed.

Minimum router suite:
```bash
git diff --check
.venv/bin/python -m pytest tests/test_turn_contract_router_classifier.py \
  tests/test_turn_contract_router_contracts.py \
  tests/test_turn_contract_router_harness_binding.py \
  tests/test_turn_contract_router_executor_fence.py \
  tests/test_turn_contract_router_preflight_plan.py \
  tests/test_turn_contract_router_quality.py
```

When parallel preflight is added:
```bash
.venv/bin/python -m pytest tests/test_turn_contract_router_parallel_preflight.py
```

When API/routes/manifest change:
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```

When docs/product truth change:
```bash
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only
```

When Control Center changes:
```bash
make frontend-check
.venv/bin/python scripts/verify_control_center_frontend.py
```

Browser smoke requirements:
For phases 04, 05, 06, 07, and 99, run browser smoke against the actual local
product:
1. Start the local dev server using the repo's existing workflow.
2. Open the relevant Control Center route in the Codex in-app Browser.
3. Check for console errors.
4. Exercise protected sample prompts or sample buttons:
   - DIY desk;
   - DIY table;
   - normal explanation;
   - simple code answer;
   - office memory;
   - shopping list;
   - current lumber prices;
   - order materials;
   - card and pickup;
   - base-answer bypass attempt.
5. Confirm visible routed contracts and policy summaries match backend output.
6. Confirm no raw JSON is the primary UI.
7. Confirm unsupported authority is disabled, blocked, or absent.
8. Confirm layout is usable on desktop and a narrow/mobile viewport if the
   route is responsive.
9. Record the local URL, browser observations, and any screenshots/console
   findings in the phase report.

Review agents:
When the diff is non-trivial, use bounded subagents or equivalent focused
reviews for:
- safety/authority review;
- backend/API contract review;
- frontend/product-language review;
- test/verifier review.

If subagents are unavailable, perform the same reviews manually and document
the results.

Final hardening pass:
After Prompt 07, run a full sweep before Prompt 99:
1. Re-run all router tests.
2. Re-run API/manifest/OpenAPI checks if any route changed.
3. Re-run docs/product truth checks.
4. Re-run frontend checks.
5. Re-run browser smoke.
6. Search for forbidden overclaims:
   - production-ready;
   - public beta ready;
   - unrestricted browsing;
   - unrestricted tools;
   - broad autonomy;
   - connector writes enabled;
   - provider authority enabled;
   - product runtime browser automation enabled.
7. Search for old naming drift:
   - `raw_model`;
   - `base_model`;
   - `model_route_hint`;
   - `model_route_lane`;
   - `raw_answer_draft`.
8. Fix real findings or document why they are historical/irrelevant.
9. Run an answer-quality preservation matrix:
   - direct DIY desk/table;
   - normal explanation;
   - simple code answer;
   - base-answer harmless prompt;
   - office memory prompt;
   - current-info prompt;
   - order/payment prompt;
   - base-answer safety bypass prompt.
10. For every direct/base case, verify:
   - `memory_scope=none`;
   - `tools=[]`;
   - `tool_choice=none`;
   - `planner=false`;
   - `durable_state=false`;
   - `approval_required=false`;
   - `side_effects_allowed=false`;
   - UI/browser posture is lightweight and not warning-heavy.
11. For every boundary/bypass case, verify approval/review/read-only prep is
    required and no execution occurs.

Final report:
When the full sequence is complete, report:
- enterprise integration branch used;
- phase branches;
- PR URLs;
- merge SHAs;
- commits pushed;
- files changed by phase;
- tests/verifiers run;
- browser smoke local URL and observations;
- issues found during review/fix/harden;
- how each issue was fixed;
- skipped checks and exact reasons;
- authority promoted;
- authority still blocked;
- remaining product gaps;
- security/safety residual risks;
- recommendations for next implementation lane.

Do not claim completion unless the code is implemented, reviewed, hardened,
tested, browser-smoked where required, pushed, and merged into the enterprise
integration branch, or the final report clearly marks the exact external
blocker.
```
