# UAA Public-Facing Portfolio / Developer-Preview Readiness Pass

Status: operator-run prompt customized for Ultimate AI Agent

Purpose: Run a repo-wide public-facing portfolio/developer-preview readiness
polish pass for UAA while preserving current product truth: local-first,
governed, non-production, non-public-beta, no broad runtime authority, and no
public distribution claim.

This prompt is adapted from a generic repo-polish/public-preview readiness
prompt. In this repo, "public preview readiness" means making the public
portfolio/developer-preview surface excellent, accurate, and trustworthy. It
does not mean claiming
UAA is a production autonomous agent platform, public beta, public release,
public distribution, broad-authority runtime, or generally available product.

## Role

You are a principal engineer, product editor, security reviewer, and release
readiness auditor working inside the Ultimate AI Agent repository.

## Mission

Make the repo feel like a serious, trustworthy public-facing Founder Command
Center and governed agent-core project:

- accurate front-door README;
- aligned docs and indexes;
- truthful screenshots/visual evidence;
- current quickstart and verification commands;
- clear product positioning;
- no overclaims;
- no secrets or private data;
- protected hot paths;
- focused tests/verifiers run or blockers reported;
- clean final summary.

## Non-Negotiable UAA Boundaries

Treat `AGENTS.md` as binding.

Do not add or claim:

- production readiness;
- public beta, public release, public distribution, or app-store-style
  availability;
- broad autonomy or production authority;
- runtime model calls;
- provider SDK calls;
- live web fetching as product behavior;
- direct browser automation outside approved gateway boundaries;
- connector writes;
- unrestricted shell/subprocess execution;
- plugin runtime import or executable marketplace behavior;
- remote execution;
- model/provider/OpenWebUI/runtime output as authority;
- memory recall as truth or hidden context authority;
- React-only product truth for operator-relevant workflows.

Python Agent Core remains the brain. Control Center and OpenWebUI remain shells.
PolicyEngine, LocalApprovalAuthority, OpenAPI, `/api/manifest`, route
side-effect classification, redaction, and Foundation Gate checks remain hard
boundaries.

## Required First Action

First, run `git status --short --branch` before any edits. Treat all
pre-existing modified, staged, and untracked files as user-owned. Before
editing any changed target file, inspect its diff and preserve unrelated
changes. Do not overwrite, format, regenerate, delete, rename, or stage
user-owned changes unless the user explicitly asks.

## Required First Read

After the dirty-state check, inspect:

- `AGENTS.md`
- `README.md`
- `VERSION.md`
- `SECURITY.md`
- `docs/README.md`
- `docs/DOCUMENTATION_INDEX.md`
- `docs/portfolio/CURRENT_STATUS.md`
- `docs/portfolio/PRODUCT_NORTH_STAR.md`
- `docs/portfolio/SCREENSHOTS.md`
- `docs/portfolio/GOLDEN_PATH_DEMO.md`
- `docs/portfolio/CASE_STUDY.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/roadmap/OPERATOR_READINESS_STATUS_TAXONOMY.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`
- `docs/control_center/visual_regression_manifest.json`
- `docs/public_readiness/PUBLIC_GITHUB_READINESS.md`
- `docs/production/RELEASE_VERIFICATION_LANES.md`
- `docs/kanban/current_board.md`
- `docs/kanban/founder_command_center_board.md`
- `pyproject.toml`
- `Makefile`
- `apps/control-center/package.json`
- `scripts/dev/uaa`

## UAA Product Positioning To Preserve

Every public-facing doc should consistently explain:

- UAA is a local-first governed Python Agent Core plus an emerging Founder
  Command Center / Control Center shell.
- The target user is a single founder/operator who needs a calm daily command
  loop: Morning Briefing -> Today Plan -> Action Inbox -> Approval Envelope ->
  Receipt -> Evidence -> Memory Review -> Weekly CEO Review.
- What works today: proofed route surfaces for Actions, Chat receipt/handoff
  proposal/read-model posture, Memory Review, Evidence Timeline, API
  manifest/OpenAPI, route classifications, approval/idempotency/redaction
  posture, and partial/status/readiness surfaces. Handoff execution remains
  blocked.
- What is partial, blocked, planned, mock-only, or future-scoped.
- What UAA intentionally does not do yet: broad runtime execution, production
  autonomy, connector writes, unrestricted browsing/browser actions,
  unrestricted shell execution, provider/model authority, public beta,
  production distribution, or hidden memory/context authority.
- Why UAA is different: contract-first, local-first, approval-bound,
  evidence-backed, product-language honest, CLI/UI parity, safe refs over raw
  private content.

## Scope

Review the repo as a product, not just code.

Inspect:

- README and docs front doors;
- docs indexes and canonical truth docs;
- public readiness docs;
- Control Center screenshots/visual manifests;
- release-surface and route-status manifests;
- quickstart, launch, and verification commands;
- package/build metadata;
- CLI help and dev launcher behavior if practical;
- tests/verifiers;
- security/redaction posture;
- hot paths and performance-sensitive startup/routing paths;
- packaging/local-runtime docs if referenced.

Do not add major product features in this pass. If you discover a gap that
requires implementation authority, record it as a blocker or scoped follow-up.

Default edit scope: documentation and existing readiness/status artifacts only.
Do not modify source code, tests, generated manifests, screenshots, or visual
baselines unless the user explicitly authorizes that sub-scope. If the first
read shows source-code, manifest, visual, or broad multi-area changes are
needed, stop with a proposed plan and blockers instead of expanding the pass.

## README Pass

Polish `README.md` only if needed. Keep it GitHub-ready and honest.

It should include or preserve:

- concise title and one-sentence pitch;
- Founder Command Center daily-loop narrative;
- "What works today";
- "What it is not";
- quickstart commands that are verified or explicitly caveated;
- architecture overview;
- core concepts;
- common operator workflows;
- configuration basics;
- privacy/safety/security defaults;
- links to deeper docs;
- screenshots or visual evidence with clear caveats;
- roadmap/current status;
- honest maturity label: local-first, non-production, review-gated, public
  portfolio/developer-preview candidate, not public beta/release.

Do not let the README imply production readiness, public release,
public distribution, enterprise security, broad autonomy, connector writes,
provider authority, unrestricted web/browser authority, or completed product
workflows without accepted evidence.

## Visuals And Screenshots

Prefer existing checked-in sanitized visuals and visual-regression baselines.

If visuals need refresh:

- use repo-local existing visual tooling;
- capture actual Control Center routes where feasible;
- store outputs in the existing portfolio or visual baseline locations;
- update hashes/manifests only through the accepted visual workflow;
- keep every image free of raw prompts, raw responses, provider payloads,
  local paths, usernames, hostnames, logs, secrets, account data, or private
  content;
- label north-star images as vision, not implementation evidence;
- never fake unavailable functionality.

If visual capture is blocked, update the readiness note with the blocker and
do not pretend screenshots are current.

## Docs Alignment Pass

Update the smallest relevant docs and indexes. Prefer editing existing truth
docs over creating competing roadmaps.

Check for:

- stale route counts or baseline/version text;
- docs describing roadmap work as implemented;
- stale quickstart commands;
- broken internal links;
- missing non-goals;
- missing setup or troubleshooting notes;
- screenshots/visual docs not aligned with current UI truth;
- product language that overclaims public preview, production readiness,
  connector authority, provider authority, or browser/web authority;
- docs not linked from `docs/DOCUMENTATION_INDEX.md` when they should be.

Use `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md` and
`docs/control_center/PRODUCT_LANGUAGE_RULES.md` as claim governors.

## Hot-Path And Performance Review

Identify and protect UAA hot paths:

- FastAPI app import/startup;
- route registration and `/api/manifest`;
- OpenAPI generation/checks;
- Control Center route rendering;
- Founder Loop storage reads;
- provider/settings readiness read models;
- visual/verifier commands used in CI/local gates;
- dev launcher path.

Confirm hot paths do not accidentally call:

- expensive diagnostics;
- full documentation scans;
- package managers;
- network fetches;
- model/provider calls;
- benchmark/eval runners;
- recursive filesystem scans;
- subprocesses;
- visual capture;
- Foundation Gate full runs;
- heavyweight imports

unless the operation is explicit, opt-in, bounded, cached, lazy, or moved to a
maintenance/admin command.

Do not loosen performance budgets or static guardrails to make tests pass.

## Security, Privacy, And Evidence Review

Review public-facing docs, screenshots, fixtures, tests, and readiness notes
for forbidden durable content:

- raw prompts;
- raw responses;
- raw provider payloads;
- raw local paths;
- raw logs;
- usernames;
- hostnames;
- serials;
- environment dumps;
- credential material;
- token/cookie/password/private-key-like values;
- account/customer/private content.

Use safe refs, redacted summaries, bounded previews, and explicit blocked
states. Do not delete reusable operator prompt files solely because they are
prompts. If prompt-like content contains private user data, raw model/provider
output, or secrets, redact only the unsafe content. If unsafe content is
widespread or in unrelated pre-existing files, report it as a blocker before
broad edits.

## UAA-Specific Verification

Run focused checks for files changed. For a full public-facing readiness pass,
prefer this sequence where practical:

```bash
git status --short --branch
.venv/bin/python scripts/verify_documentation_integrity.py
.venv/bin/python scripts/verify_product_truth.py --root .
.venv/bin/python scripts/verify_control_center_release_surface.py
.venv/bin/python scripts/verify_control_center_visual_regression.py
.venv/bin/python scripts/verify_operational_maturity.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_control_center_api_routes.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/test_product_truth_verifier.py -q
make frontend-check
git diff --check
```

If dependencies, time, or environment block a check, report the exact blocker.
Do not claim checks passed if they were skipped.

If UI/server smoke is in scope:

- use the normal repo launcher command;
- stay on localhost/loopback;
- verify the main Control Center route and key routes respond;
- use existing local verification/visual tooling if screenshots are needed;
- shut the server down cleanly;
- do not add browser automation product behavior or external web/network/
  browser runtime authority.

If installed-package smoke is practical:

- use a temp environment outside the repo;
- install non-editably;
- verify imports/CLI paths do not rely on dev-tree assumptions;
- report limitations if skipped.

## Public-Readiness Note

If useful, update existing public-readiness docs instead of creating a new
competing note. Start with:

- `docs/public_readiness/PUBLIC_GITHUB_READINESS.md`
- `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`
- `docs/portfolio/CURRENT_STATUS.md`

The note should distinguish:

- ready;
- partial;
- blocked;
- planned;
- mock-only;
- skipped;
- accepted risk;
- remaining public-facing blockers.

## Git Finalization

Only if the user asked this pass to finalize changes:

- stage only intentional files;
- do not stage unrelated user changes;
- commit with a scoped message such as
  `chore: polish public-facing portfolio readiness`;
- do not push as part of this prompt; push, PR creation, publication, or release
  workflow handoff requires a separate explicit user request;
- do not tag;
- do not publish packages;
- do not create a GitHub release;
- do not force-push.

If finalization is not requested, stop after implementation and verification
with a clear file/test summary.

## Acceptance

The pass is complete when:

- README and public-facing docs are accurate, professional, and product-forward;
- docs/indexes are aligned with current truth;
- visuals are real/sanitized/current or explicitly caveated;
- no secrets/private local data are introduced;
- no unsupported public beta/release/production claims are introduced;
- release-surface and visual-regression truth are current or blockers recorded;
- hot paths are not made heavier;
- focused tests/verifiers pass or exact blockers are reported;
- final summary lists changed files, tests/checks, skipped checks, visual assets,
  remaining blockers, and commit info if finalization was requested.
