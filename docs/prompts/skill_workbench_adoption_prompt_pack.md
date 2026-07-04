# Skill Workbench Discovery And Adoption Prompt Pack

Status: operator-run prompt pack
Purpose: Build UAA's Skill Workbench as a governed discovery, review, and
adoption system for external skill marketplaces such as OpenClaw Clawhub and
the Hermes skill catalog without direct install, direct execution, or wholesale
code import.

These prompts are execution prompts, not runtime system prompts. They do not
grant authority by themselves. Every implementation must preserve `AGENTS.md`,
Python Agent Core authority, Control Center shell boundaries, OpenAPI/API
manifest truth, LocalApprovalAuthority, PolicyEngine, redaction, route
side-effect classification, WebAccessGateway boundaries, operational maturity
gates, and Foundation Gate checks.

## Product Doctrine

Call the feature **Skill Workbench**, not Skill Store.

The product posture is:

```text
discover metadata
-> inspect source reputation and permissions
-> create adoption candidate
-> optionally fetch source into quarantine after exact approval
-> statically review code, manifest, dependencies, license, and permissions
-> rewrite/adapt into UAA-owned skill shape
-> test and verify
-> enable locally only after explicit acceptance
```

External skill code is reference material, never trusted runtime authority.
UAA must not take marketplace code wholesale, install it automatically, import
it at runtime, execute it, or let marketplace popularity substitute for review.

## Non-Negotiable Boundaries

Allowed by this prompt pack when scoped in an individual lane:

- docs, contracts, schemas, fixtures, verifiers, tests, and read-only UI;
- metadata-only discovery contracts for marketplace listings;
- safe marketplace refs, skill refs, rating refs, popularity refs, license refs,
  maintainer refs, and source refs;
- metadata cache/read models with explicit freshness and provenance posture;
- adoption candidate records and review reports;
- quarantine contracts and blocked states;
- static analysis contracts and fixture-only test examples;
- UAA-owned local skill registry contracts after review.

Not allowed unless a later exact lane explicitly grants it:

- direct marketplace install;
- plugin runtime import or dynamic execution;
- running external skill code;
- executing package manager install scripts;
- direct web fetching outside `ultimate_ai_agent.core.web_access`;
- browser automation or opening marketplace webpages as the product UX;
- authenticated browsing, cookies, account login, form filling, downloads, or
  uploads;
- connector writes;
- credential access or secret resolution;
- shell/subprocess execution over untrusted code;
- provider/model calls;
- raw prompt, raw response, raw marketplace payload, raw code, raw local path,
  credential, secret-like value, or environment dump in durable evidence;
- public marketplace, public beta, public release, public distribution,
  production readiness, or production authority claims.

## Merge-Gated Execution Discipline

Each prompt lane is a separate merge-gated PR slice.

For every lane:

1. Start from a clean synced base branch or explicitly document dirty blockers.
2. Create a scoped branch.
3. Implement only that lane.
4. Run focused tests/verifiers plus documentation integrity.
5. Review the diff for authority creep, raw data, unsupported claims, direct
   install/execute paths, and UI-only product truth.
6. Commit only scoped files.
7. Push the branch.
8. Open or update the PR.
9. Merge only after checks pass and the operator accepts the lane.
10. Sync the base branch before starting the next lane.

Do not batch lanes into one giant PR. If a lane is blocked, commit a blocker
report only when it is useful and accepted; otherwise stop with the smallest
next safe action.

## Prompt 00 - Execute All Lanes With Merge Gates

Role: You are a principal engineer, product owner, and supply-chain security
reviewer working inside the Ultimate AI Agent repository.

Goal: Execute this prompt pack end to end as a sequence of small merge-gated
PRs. After each lane, verify, commit, push, open/update PR, merge after
operator acceptance, sync base, and only then continue.

Required first read:

- `AGENTS.md`
- `README.md`
- `docs/README.md`
- `docs/DOCUMENTATION_INDEX.md`
- `docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md`
- `docs/strategy/DELEGATED_LIFE_OS_NORTH_STAR.md`
- `docs/control_center/OPERATOR_SHELL_GAP_MAP.md`
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`
- `docs/control_center/USABLE_AUTHORITY_GRADUATION_PLAN.md`
- `docs/control_center/AUTHORITY_RAMP_CONVEYOR.md`
- `docs/network/WEB_ACCESS_GATEWAY.md`
- `docs/network/WEB_ACCESS_PROVIDER_AUTHORITY_SEQUENCE.md`
- `docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md`
- `docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md`
- `docs/tooling/EXTENSION_ACTIVATION_GRANTS.md`
- `docs/canonical/40_credentials_secret_broker_and_provider_registry.md`
- `docs/canonical/42_autonomy_levels_and_standing_approvals.md`

Required first commands:

```bash
git status --short --branch
rg -n "skill|plugin|marketplace|extension|catalog|Clawhub|Hermes|adoption|quarantine" docs src apps tests scripts
```

Lane sequence:

1. Prompt 01 - Skill Workbench Charter And Product Boundary
2. Prompt 02 - External Skill Catalog Metadata Contracts
3. Prompt 03 - Marketplace Search And Popularity Read Models
4. Prompt 04 - Control Center Skills Tab Read-Only UX
5. Prompt 05 - Adoption Candidate And Quarantine Contracts
6. Prompt 06 - Static Review And Risk Report Pipeline
7. Prompt 07 - UAA-Owned Skill Rewrite/Adaptation Workflow
8. Prompt 08 - Local Skill Registry And Enablement Gates
9. Prompt 09 - Verifiers, Product Language, And Docs Currentness
10. Prompt 99 - Blocker Report And Follow-Up Prompt Generator

Default verification for each lane:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
git diff --check
```

Add focused tests/verifiers for changed source, route, frontend, schema,
manifest, or UI files. If frontend files change, run `make frontend-check` or
the focused equivalent. If API routes change, run OpenAPI/API manifest checks.

Required final response after every lane:

- lane completed or blocked;
- branch, commit, PR, and merge status;
- files changed;
- tests/verifiers run;
- skipped checks and reasons;
- authority intentionally not added;
- next lane or blocker.

## Prompt 01 - Skill Workbench Charter And Product Boundary

Role: Product architect and supply-chain security reviewer.

Goal: Create the planning and authority boundary for Skill Workbench before any
runtime behavior exists.

Required outcome:

- Add a scoped milestone doc such as
  `docs/control_center/SKILL_WORKBENCH_DISCOVERY_AND_ADOPTION.md`.
- Define Skill Workbench as a Control Center surface over Python Agent Core
  contracts, not a plugin store.
- Define user-visible surfaces:
  - Discover;
  - Popular;
  - Search;
  - Skill detail;
  - Adoption queue;
  - Review report;
  - Local UAA-owned skills;
  - Blocked/rejected candidates.
- Define source marketplaces as metadata providers only:
  - OpenClaw Clawhub;
  - Hermes skill catalog, with exact source name to be verified later;
  - optional GitHub/curated lists after separate scope.
- Define status labels:
  - `external_metadata_only`;
  - `candidate`;
  - `quarantined_untrusted`;
  - `review_required`;
  - `rejected`;
  - `adapted_uaa_owned`;
  - `enabled_local`;
  - `blocked_by_policy`.
- Define the key rule: external code is evidence/reference, never executable
  authority.
- Add docs/index/product-language updates.

Authority boundary:

- Docs/contracts only.
- No backend route, no UI control, no catalog fetch, no source download, no
  plugin execution, no marketplace install, no production claim.

Merge gate:

- Verify docs.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 02 - External Skill Catalog Metadata Contracts

Role: Python Core contract engineer.

Goal: Define marketplace listing contracts that can represent external skill
metadata without fetching or executing marketplace code.

Required outcome:

- Add Python contracts for:
  - marketplace source;
  - skill listing;
  - version;
  - maintainer;
  - category;
  - description;
  - popularity/download/rating/review aggregates;
  - freshness;
  - license;
  - declared permissions;
  - declared dependencies;
  - source/provenance refs;
  - blocked authority refs.
- Add fixture examples for Clawhub-like and Hermes-like listings. Use synthetic
  safe refs only; do not copy real marketplace payloads unless separately
  fetched through an approved gateway lane.
- Make popularity and rating fields optional because marketplaces may not expose
  a star system or comparable review data.
- Add tests proving missing rating/popularity data degrades to
  `unknown_not_trusted`, not trusted.
- Add redaction and raw-payload denial tests.

Authority boundary:

- Metadata contracts and fixtures only.
- No live network fetch.
- No marketplace login.
- No package download.
- No code execution.

Merge gate:

- Run focused tests plus docs verifier.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 03 - Marketplace Search And Popularity Read Models

Role: Backend read-model engineer.

Goal: Add safe read models for browsing and searching marketplace metadata
inside UAA without opening marketplace webpages.

Required outcome:

- Add a read model for:
  - source marketplace list;
  - popular/trending listings;
  - search results;
  - filters by source/category/risk/license/permission/status;
  - skill detail summary;
  - freshness/staleness state;
  - blocked source state.
- If adding routes, keep them read-only and update OpenAPI, `/api/manifest`,
  route inventory, route side-effect docs, and focused tests.
- Prefer fixture/static metadata first unless an accepted WebAccessGateway lane
  grants read-only catalog fetch.
- Search/browse must return UAA-owned safe summaries, not raw marketplace pages.
- Popularity sorting must include source and freshness caveats.

Authority boundary:

- Read-only metadata only.
- No direct web fetch unless separately scoped through WebAccessGateway.
- No browser automation.
- No install/adopt/enable controls yet.

Merge gate:

- Run route/API tests if routes changed.
- Run docs verifier and focused tests.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 04 - Control Center Skills Tab Read-Only UX

Role: Frontend product engineer.

Goal: Add a Skill Workbench tab/surface that browses UAA-owned marketplace
metadata without opening external webpages.

Required outcome:

- Add `/skills` or an equivalent first-party Control Center route.
- UI sections:
  - Discover;
  - Popular;
  - Search;
  - Filters;
  - Skill details;
  - Source/freshness labels;
  - Permission/risk chips;
  - Adoption status;
  - blocked-state explanation.
- Show average rating/review/popularity only when the read model provides it.
  Otherwise show unknown/unavailable, not zero stars.
- Include no install button. If an action exists, it must say review/adoption
  candidate only and remain backend-owned.
- No external marketplace pages open from the primary UX. If source refs are
  shown, they must be safe refs or copyable refs, not uncontrolled browser
  navigation.
- Add frontend tests and visual coverage if the project pattern requires it.

Authority boundary:

- Read-only UI and review posture only.
- No React-only product truth.
- No install, execute, import, source fetch, credential use, or marketplace
  account auth.

Merge gate:

- Run focused frontend checks plus docs verifier.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 05 - Adoption Candidate And Quarantine Contracts

Role: Supply-chain workflow engineer.

Goal: Add the workflow model for adopting an external skill safely without
trusting external code.

Required outcome:

- Add adoption candidate contracts:
  - candidate ref;
  - marketplace listing ref;
  - operator reason;
  - source refs;
  - license refs;
  - risk refs;
  - requested permissions;
  - quarantine status;
  - review checklist refs;
  - rejection/acceptance posture.
- Add quarantine contracts:
  - source snapshot ref;
  - fetch approval ref;
  - checksum refs;
  - no-execute flag;
  - no-install flag;
  - no-network flag;
  - raw-code retention boundary;
  - review-only path.
- If adding mutation route(s), require idempotency, exact LocalApprovalAuthority
  validation where applicable, receipt refs, route classification, OpenAPI/API
  manifest updates, and tests.
- Fixture-only candidate creation is acceptable as the first step if mutation
  authority is not ready.

Authority boundary:

- Creating an adoption candidate does not fetch source, install, run, or enable
  anything.
- Quarantine source fetch remains blocked unless a later exact lane grants it.
- No wholesale code import.

Merge gate:

- Run focused contract/route tests plus docs verifier.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 06 - Static Review And Risk Report Pipeline

Role: Application security and verifier engineer.

Goal: Define and implement static review reports for quarantined or fixture
skill candidates.

Required outcome:

- Add review checks for:
  - manifest shape;
  - declared permissions;
  - file access;
  - network access;
  - shell/subprocess use;
  - credential access;
  - dependency footprint;
  - package scripts;
  - license compatibility;
  - maintainer/source provenance;
  - suspicious strings and secret-like patterns;
  - raw private data risks.
- Add review result model:
  - pass/warn/block;
  - finding refs;
  - evidence refs;
  - recommended disposition;
  - required rewrite/adaptation notes.
- Tests must prove unsafe patterns block adoption.
- The review pipeline must not execute external code. Static analysis only.

Authority boundary:

- No running package scripts.
- No dependency installation from the external candidate.
- No dynamic import.
- No provider/model evaluation of raw code by default.

Merge gate:

- Run focused tests/verifiers plus docs verifier.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 07 - UAA-Owned Skill Rewrite/Adaptation Workflow

Role: Product engineer and code reviewer.

Goal: Model the "make it our own" workflow: external skill ideas become
UAA-owned skills only through review, adaptation, tests, and provenance.

Required outcome:

- Add adaptation plan contracts:
  - external candidate ref;
  - accepted concept summary;
  - rejected external code refs;
  - UAA-owned design refs;
  - permission reduction refs;
  - test plan refs;
  - reviewer decision refs;
  - license/provenance refs.
- Define explicit anti-wholesale-copy checks:
  - no direct vendoring of marketplace code;
  - no retained executable external snippets unless license/review permits and
    the operator explicitly accepts;
  - no hidden dependency adoption.
- Define local UAA-owned skill shape and required docs/tests.
- Add examples as fixtures only.

Authority boundary:

- This lane may define the workflow and examples, but does not enable runtime
  execution unless the existing skill system already has a governed local-only
  enablement path and the lane is separately scoped.

Merge gate:

- Run focused tests/verifiers plus docs verifier.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 08 - Local Skill Registry And Enablement Gates

Role: Core registry engineer.

Goal: Make reviewed UAA-owned skills visible as local capabilities while
keeping external candidates blocked until adapted and approved.

Required outcome:

- Add or extend a local skill registry read model:
  - local skill ref;
  - origin/adaptation refs;
  - permission profile;
  - authority tier;
  - enabled/disabled status;
  - review status;
  - test/verifier refs;
  - safe-disable refs;
  - blocked external candidate refs.
- UI may show Local Skills separately from Discover/Adoption Queue.
- Any enable/disable mutation must be exact scoped, backend-owned, auditable,
  idempotent, safe-disable aware, and tested. If that authority is not ready,
  keep enablement as blocked/planned posture only.

Authority boundary:

- External marketplace candidates cannot become enabled directly.
- Local registry visibility is not execution authority.
- Skill enablement is not broad plugin runtime import.

Merge gate:

- Run focused tests/verifiers plus docs verifier.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 09 - Verifiers, Product Language, And Docs Currentness

Role: Release truth and verifier engineer.

Goal: Add cross-cutting checks so Skill Workbench cannot drift into unsafe
marketplace/install language.

Required outcome:

- Add verifier coverage for:
  - no "store/install/run external skill" claims;
  - Skill Workbench terminology;
  - metadata-only marketplace discovery;
  - no direct marketplace execution path;
  - no raw external code in durable evidence;
  - no UI-only adoption truth;
  - no install button without backend authority;
  - docs/index currentness.
- Update product truth, gap map, docs index, and prompt README as needed.
- Add release-surface and operational-maturity entries if UI/routes were added.

Authority boundary:

- Verification and docs alignment only.
- No new runtime behavior.

Merge gate:

- Run full focused verifier set plus docs verifier.
- Commit, push, PR, merge after acceptance, sync base.

## Prompt 99 - Blocker Report And Follow-Up Prompt Generator

Role: Technical program owner.

Goal: If any lane cannot safely proceed, produce a blocker report and generate
the next exact prompt needed to unblock it.

Required outcome:

- Add a dated blocker report under an appropriate docs path.
- Include:
  - blocked lane;
  - blocker;
  - required authority;
  - affected files/routes/UI;
  - smallest next safe step;
  - tests/verifiers needed;
  - explicit non-goals.
- Generate a follow-up prompt that can be run as one small PR.

Authority boundary:

- Blocker reports do not grant authority.
- Do not implement around the blocker.

Merge gate:

- Commit/push/PR/merge blocker report only if useful and accepted.

## Wrapper Prompt

Use this wrapper when you want an agent to run the full sequence:

```text
You are working in the Ultimate AI Agent repository.

Run `docs/prompts/skill_workbench_adoption_prompt_pack.md` end to end.

Rules:
- Treat AGENTS.md as binding.
- Preserve unrelated user changes.
- Execute one prompt lane at a time.
- Do not batch lanes.
- After each lane: run focused checks, run documentation integrity, run
  `git diff --check`, review for authority creep, commit only scoped files,
  push the branch, open or update the PR, and stop for operator acceptance
  before merge.
- After a lane is merged, sync the base branch before continuing.
- Keep Skill Workbench metadata-only until exact authority exists.
- Do not install, execute, import, or wholesale-copy external marketplace code.
- Use WebAccessGateway contracts for any future marketplace metadata fetch.
- Do not open marketplace webpages as the primary product UX.
- External popularity, stars, downloads, and reviews are discovery signals only,
  not trust.
- Every external skill must become a reviewed UAA-owned adaptation before it can
  be enabled locally.

Start with Prompt 00 in the pack. Report the lane, branch, commit, PR, merge
status, files changed, checks run, skipped checks, intentionally blocked
authority, and next lane after every step.
```
