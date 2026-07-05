# Execute UAA Hermes Runtime Adoption End To End

Role: principal engineer, agent-runtime architect, product strategist, security
reviewer, release engineer, and adversarial hardening reviewer for UAA.

Goal: implement the 45-phase UAA Hermes Runtime Adoption program end to end.
UAA should become a custom governed control center that can supervise Hermes
Agent and future Codex, Claude, local, and other runtimes without losing UAA's
own product identity, authority model, proof spine, or local-first posture.

This is not a Hermes import project. This is a UAA-native runtime delegation and
operator-control program.

## Read First

Read these files completely before editing:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/prompts/hermes_runtime_adoption/README.md`
- every file in `docs/prompts/hermes_runtime_adoption/`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/control_center/AUTHORITY_GRADUATION_BOARD.md`
- `docs/control_center/GOVERNED_PRODUCT_PILOT_AUTHORITY_PROFILE.md`
- `docs/control_center/MODEL_PROVIDER_CONTROL_PLANE.md`
- `docs/control_center/PROVIDER_ROUTER_DRY_RUN.md`
- `docs/control_center/SKILL_WORKBENCH_DISCOVERY_AND_ADOPTION.md`
- `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`
- `docs/network/WEB_ACCESS_GATEWAY.md`
- `docs/api/openapi_contract.md`
- `docs/api/route_inventory.md`
- `docs/architecture/TARGET_PRODUCT_ARCHITECTURE.md`

Then inspect current implementation:

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse HEAD
git remote -v
rg --files
rg "runtime|provider|model|approval|authority|policy|proof|evidence|receipt|session|run|tool|skill|mcp|plugin|connector|browser|web|shell|command|checkpoint|rollback|logging|trace" src tests apps docs scripts
```

Use Hermes Agent only as a read-only reference. Prefer current official Hermes
docs and repo metadata:

- `https://github.com/NousResearch/hermes-agent`
- `https://github.com/NousResearch/hermes-agent/releases`
- `https://hermes-agent.nousresearch.com/docs/`
- `https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server`
- `https://hermes-agent.nousresearch.com/docs/developer-guide/architecture`
- `https://hermes-agent.nousresearch.com/docs/user-guide/features/tools`
- `https://hermes-agent.nousresearch.com/docs/user-guide/security`
- `https://hermes-agent.nousresearch.com/docs/user-guide/features/memory`
- `https://hermes-agent.nousresearch.com/docs/user-guide/features/skills`

If a local Hermes checkout exists, inspect it read-only. Do not copy code,
vendor packages, import Hermes modules, or treat Hermes docs as granting UAA
authority.

## Non-Negotiable Rules

- Treat `AGENTS.md` as binding.
- Preserve unrelated dirty files and user changes.
- Start each implementation phase from clean, current `main`.
- Do not force-push.
- Do not delete, retarget, move, or force-push historical tags.
- Python Agent Core remains the brain.
- Control Center remains presentation/initiation only.
- No UI-only durable workflow truth.
- No direct browser-to-Hermes secrets.
- No Hermes action equals UAA-approved action unless UAA validates exact
  approval scope.
- Do not add runtime model calls, provider SDK calls, web fetching, connector
  writes, browser automation, unrestricted shell/subprocess execution, plugin
  runtime import, remote execution, public beta/release claims, production
  authority, or broad autonomy unless an exact phase proves a safe lane with
  approval binding, idempotency, receipt, rollback/safe-disable posture,
  redaction, tests, and CLI/API/Core parity.
- Do not persist raw prompts, raw responses, provider payloads, local paths,
  account material, logs, credentials, tokens, cookies, or private data.
- Use safe refs, redacted summaries, bounded previews, and explicit blocked
  states.

## Execution Model

Run exactly one phase at a time. Do not batch phases.

For each phase:

1. Checkout `main`.
2. Pull latest `main` with fast-forward only.
3. Run `git status --short --branch`.
4. Stop if the tree is dirty with unrelated changes.
5. Create the phase branch named in the phase prompt.
6. Inspect existing UAA implementation before editing.
7. Classify the capability as `implemented`, `partial`, `planned`,
   `mock-only`, `blocked`, `deprecated`, `contradicted`, or `unknown`.
8. State:
   - full-strength version;
   - repo-safe version;
   - blocked / needs authority;
   - exact promotion path.
9. Implement only the smallest UAA-native slice authorized by the phase.
10. Add or update backend/core contracts, API, CLI, Control Center, docs, tests,
    verifiers, route side-effect classification, and OpenAPI where relevant.
11. Review the diff adversarially for:
    - authority creep;
    - UI-only truth;
    - raw-data leakage;
    - missing approval binding;
    - missing idempotency or replay behavior;
    - missing rollback or safe-disable posture;
    - missing redaction;
    - route/API manifest drift;
    - product-language overclaims;
    - unsupported Hermes parity claims;
    - missing CLI/API/Core parity.
12. Fix and harden until no in-scope high or medium risk remains.
13. Run focused tests and required hygiene.
14. Commit only scoped files with the phase commit message.
15. Push the phase branch.
16. Open a focused draft PR.
17. Fix CI and review issues.
18. Mark ready only when scope is clean.
19. Merge to `main` only when green, using the repo's accepted merge process.
20. Pull latest `main`.
21. Run post-merge hygiene.
22. Continue to the next phase.

If PR infrastructure is unavailable, use local merge commits into a dedicated
integration branch and state that PR creation was blocked. Do not squash away
phase history unless the operator explicitly changes the process.

## Phase Prompt Volumes

Execute phase prompts from these files in order:

1. `01_critical_runtime_delegation_and_capabilities.prompt.md` for phases 01-09.
2. `02_tools_memory_context_and_rollback.prompt.md` for phases 10-18.
3. `03_orchestration_coding_and_runtime_safety.prompt.md` for phases 19-27.
4. `04_operator_surfaces_extensions_and_diagnostics.prompt.md` for phases 28-36.
5. `05_advanced_lanes_and_final_report.prompt.md` for phases 37-45.

## Required Hygiene After Every Phase

Run focused checks for changed files plus:

```bash
git diff --check
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py
.venv/bin/python scripts/verify_operational_maturity.py
```

Run these when routes/API changed:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
```

Run these when Control Center/release-surface files changed:

```bash
.venv/bin/python scripts/verify_control_center_release_surface.py
make frontend-check
make frontend-visual-check
```

Run this when authority, runtime, command execution, provider, connector,
memory write, background, browser, or release posture changed:

```bash
.venv/bin/python scripts/run_foundation_gate.py --command-mode report-only
```

If an environment dependency blocks a check, report it and do not claim
success.

## Blocked Lane Handling

If a phase cannot safely graduate capability:

1. Do not weaken the full-strength goal.
2. Keep the full-strength goal visible in docs.
3. Keep or mark the capability blocked in Trust/product truth.
4. Create or update a blocker report under `docs/control_center/` or
   `docs/roadmap/`.
5. Include missing contracts, approval binding, rollback/safe-disable,
   redaction, CLI parity, tests, evidence, and exact scope.
6. Generate a copy-ready unblock prompt.
7. Add tests/verifiers proving the blocked UI and docs do not claim authority.
8. Merge that truthful blocked/readiness work if green.
9. Continue if the next phase does not depend on unsafe authority.

## Final Hardening

After phase 45 merges, run at least three full hardening passes:

1. Security and authority pass.
2. Product-language and operator UX pass.
3. Verification and contract drift pass.

Fix any high or medium issue, commit, push, and merge the hardening branch.

## Final Report

Create a Markdown report under:

```text
reports/hermes_runtime_adoption/YYYY-MM-DD_hermes_runtime_adoption_report.md
```

The report must include:

- start branch, start commit, final main commit;
- phase branches;
- PR URLs and merge SHAs;
- files changed per phase;
- tests/verifiers run per phase with pass/fail/skipped;
- skipped checks and why;
- hardening issues found and fixed;
- known gaps grouped by severity;
- authority promoted by exact lane;
- authority still blocked;
- Hermes patterns borrowed as UAA-native designs;
- Hermes patterns explicitly not merged;
- recommendations;
- next exact PR lanes;
- final `git status --short --branch`;
- confirmation that UAA remains the control center and no broad authority was
  added.

