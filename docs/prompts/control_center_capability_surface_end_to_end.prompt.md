# Execute Control Center Capability Surface Follow-Ups End To End

Role: You are a principal engineer, product architect, release engineer, and
adversarial governance reviewer for Ultimate AI Agent's Control Center
capability-surface coverage.

Goal: take the capability-surface coverage seed from useful governance artifact
to maintained product/engineering infrastructure. Execute the four follow-ups
end to end:

1. Watch and report CI for the capability-surface commit or current branch.
2. Integrate `scripts/verify_control_center_capability_surface.py` into the
   broader repo verifier stack.
3. Make the capability manifest more generated from source truth while
   preserving human annotations.
4. Add a read-only Control Center capability-surface view when it can be backed
   by Python/API manifest truth without becoming a raw JSON dump.

This prompt does not grant runtime authority. Do not add provider/model calls,
runtime web fetching, browser automation, connector writes, plugin runtime
import, unrestricted shell/subprocess execution, memory writes, context
injection, background autonomy, public beta/release claims, production
readiness, or production authority.

## Read First

Read these files before editing:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/control_center/CAPABILITY_SURFACE_COVERAGE.md`
- `docs/control_center/capability_surface_manifest.json`
- `docs/control_center/ROUTE_STATUS_MANIFEST.md`
- `docs/control_center/UI_WIRING_REPORT.md`
- `docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`
- `docs/control_center/release_surface_manifest.json`
- `scripts/verify_control_center_capability_surface.py`
- `tests/test_control_center_capability_surface_manifest.py`
- `scripts/verify_all.py`
- `Makefile`
- `scripts/run_foundation_gate.py`
- `apps/control-center/src/routes.tsx`
- `apps/control-center/src/api/client.ts`

Then inspect:

```bash
pwd
git status --short --branch
git branch --show-current
git rev-parse HEAD
git remote -v
rg "capability_surface|verify_control_center_capability_surface|release_surface|route_status_manifest|navItems|api/manifest|Control Center" Makefile scripts tests docs apps src
```

Do not proceed from a dirty or stale base unless the dirty files are explicitly
the files you are about to change. Preserve unrelated user changes.

## Phase 1: CI Watch And Baseline Report

Use the safest available CI inspection path:

- Prefer the GitHub connector/app if available.
- Otherwise use `gh` if installed and authenticated.
- Otherwise record that CI inspection is blocked by local environment.

Check the latest pushed `main` commit and any active checks for the
capability-surface work. Report check names, conclusions, failure URLs/log refs
when available, and whether failures are related to this work. If checks fail,
inspect logs, implement only scoped fixes, and rerun focused local checks before
continuing.

Do not add product web fetching or runtime browser behavior while inspecting
CI. CI inspection is a development workflow only.

## Phase 2: Broader Verifier Integration

Wire capability-surface verification into the existing repo verification stack
using the smallest established local pattern.

Inspect existing verifier entrypoints before editing:

- `scripts/verify_all.py`
- `Makefile`
- `scripts/run_foundation_gate.py`
- `docs/production/RELEASE_VERIFICATION_LANES.md`
- any verification manifest or maintainability policy that already lists
  Control Center release-surface checks.

Expected outcome:

- `scripts/verify_control_center_capability_surface.py` runs from the broader
  verification stack, preferably wherever
  `scripts/verify_control_center_release_surface.py` is already treated as a
  required Control Center governance check.
- Docs that list verification lanes mention the new capability-surface verifier.
- The integration does not create duplicate or slow redundant execution in
  tight focused loops.

Required checks after this phase:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_capability_surface.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_capability_surface_manifest.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_release_surface.py
.venv/bin/python scripts/verify_documentation_integrity.py
```

If you modify the broader verifier stack, run the relevant broader command or
explain the exact blocker.

## Phase 3: Generated Manifest Hardening

Make the capability manifest more generated without erasing human product
judgment.

Design target:

- Generated/source-owned fields come from current repo truth:
  - API route method/path/operation id from live `/api/manifest` construction.
  - UI route coverage from `docs/control_center/release_surface_manifest.json`
    and `apps/control-center/src/routes.tsx`.
  - visible action ids from `docs/control_center/route_status_manifest.json`.
  - side-effect and route classifications from the API manifest where useful.
- Human-owned fields remain explicit and reviewable:
  - `capability_id`
  - label
  - Python/core owner
  - CLI/script path
  - authority posture
  - status
  - missing reason
  - tests/evidence refs
  - capability grouping decisions

Preferred implementation:

- Add a repo-local script such as
  `scripts/generate_control_center_capability_surface.py`.
- Preserve manual annotations through a stable overlay or by updating only
  generated sections with deterministic ordering.
- Add a `--check` mode that fails if generated fields drift.
- Update `scripts/verify_control_center_capability_surface.py` to call the
  generator check, or add a focused test that proves generation is current.
- Do not silently rewrite human annotations.
- Do not introduce raw local paths, raw logs, raw prompts, provider payloads,
  credentials, usernames, hostnames, or secret-like values into durable docs or
  generated output.

Required checks after this phase:

```bash
PYTHONPATH=src .venv/bin/python scripts/generate_control_center_capability_surface.py --check
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_capability_surface.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_capability_surface_manifest.py -q
```

If a full generator would be too large for one safe pass, implement the first
deterministic generated check for route/action/API drift and document the exact
remaining manual fields.

## Phase 4: Read-Only Control Center View

Add a read-only Control Center view for capability-surface coverage only if it
can be backed by Python/API-owned manifest truth and rendered as operator
readable state, not raw JSON.

Implementation requirements:

- Python Agent Core/API remains the truth owner.
- Add a read-only route only if needed, such as
  `GET /control-center/capabilities/surface`.
- The route must expose bounded, redacted, typed rows derived from
  `docs/control_center/capability_surface_manifest.json` plus source-truth
  validation posture.
- Add CLI or repo-local script inspection parity if the route becomes
  operator-critical.
- Add Control Center UI route/nav entry only if product-language and release
  surface manifests can be updated safely in the same pass.
- UI must show implemented, partial, backend-only, mock/static, and blocked
  states distinctly.
- UI must show missing reasons and authority posture in human-readable form.
- UI must not present raw JSON as the primary operator experience.
- UI must not add action execution, approval grants, provider/model calls,
  connector writes, file writes, browser behavior, runtime activation, or
  production claims.

If a UI view is not safe in this pass, do not fake it. Instead, add an explicit
blocked/next-lane note to the capability-surface doc and keep the verifier
integration and generation hardening complete.

Relevant frontend checks when UI files change:

```bash
make frontend-check
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_frontend.py
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_release_surface.py
```

Use browser/visual verification only if the route is actually added to the
visible UI and the local frontend environment is available.

## Final Hardening Loop

After all phases:

1. Review the diff for authority expansion, stale claims, raw evidence leaks,
   API/OpenAPI/manifest drift, missing CLI parity, UI-only durable truth, and
   missing tests.
2. Run focused tests for every changed file.
3. Run these baseline checks unless blocked:

```bash
git diff --check
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_capability_surface.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_capability_surface_manifest.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_control_center_release_surface.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_release_surface_manifest.py tests/test_control_center_route_status_manifest.py -q
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py -q
```

Run `make frontend-check` if frontend code changed. Run
`.venv/bin/python -I -B -S scripts/run_foundation_gate.py --command-mode report-only`
if Foundation Gate integration or release verification lanes changed.

## Git Finalization

When verification passes:

1. Stage only intentional files.
2. Commit with a scoped message.
3. Push the branch.
4. If working through PRs, open a draft PR, watch checks, fix failures, then
   merge to `main` with a merge commit when green.
5. If the operator explicitly requested direct `main`, ensure `main` is current
   with `origin/main`, commit only scoped changes, and push without force.

Never force-push or rewrite historical tags. Do not include unrelated dirty
worktree changes.

## Final Response Requirements

Report:

- CI checks inspected and outcome;
- verifier integration point;
- generated-manifest strategy and files changed;
- Control Center view added, or exact reason it remained blocked;
- files changed;
- tests/verifiers run with pass/fail/blocker;
- authority explicitly not added;
- remaining gaps;
- commit hash and push/PR result if git finalization succeeds.
