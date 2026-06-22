# Codex Governed Growth Prompts

Status: reusable prompt pack for governed growth work

Use these prompts for future Codex tasks in `doncazper/ultimate-ai-agent`.
They are templates and operating guidance only. They grant no runtime authority
and do not replace `AGENTS.md`, `README.md`, `VERSION.md`, the product truth
packet, the current board, or route/API/verifier requirements.

## Shared Context For Every Prompt

Codex must understand these terms exactly as defined here.

### Governed Growth

Governed growth means UAA can improve over time by creating reviewable artifacts
from approved work: memory candidates, skill candidates, skill patch candidates,
usage receipts, curator proposals, and verifier/fixer proposals. Growth is
artifact-based, not online model-weight training and not autonomous production
mutation.

### Candidate Engine

A candidate engine is a proposal generator. It receives redacted, safe-ref inputs
from completed runs and emits typed candidate records. It does not write memory,
update skills, inject context, execute skills, call providers, run shell
commands, fetch accounts, mutate connectors, modify files, or create background
sessions.

A candidate engine decides among:

```text
no_op_decision
memory_candidate
skill_create_candidate
skill_patch_candidate
skill_merge_candidate
skill_archive_candidate
skill_disable_candidate
verifier_fix_candidate
```

Decision order:

```text
1. No-op when the lesson is not reusable.
2. Propose a memory candidate only for stable user/product facts.
3. Patch an existing accepted skill before creating a new one.
4. Merge overlapping skills before creating a duplicate.
5. Create a new skill only when no existing skill fits.
6. Archive/disable only as a reviewable proposal.
7. Generate verifier/fixer candidates only from failed validation refs.
```

### Skill Package

A skill package is procedural memory. It is inspectable guidance first, not
runtime execution authority.

Canonical shape:

```text
.uaa/skills/<skill_id>/SKILL.md
.uaa/skills/<skill_id>/manifest.json
.uaa/skills/<skill_id>/references/*
.uaa/skills/<skill_id>/templates/*
.uaa/skills/<skill_id>/scripts/*
.uaa/skills/<skill_id>/usage.json
```

Scripts inside a skill package are inspectable only until a later accepted
milestone separately grants runtime import/execution with PolicyEngine,
LocalApprovalAuthority, revocation, rollback, route metadata, OpenAPI checks,
Foundation Gate checks, tests, and release evidence.

### Hard Boundaries

Every prompt below inherits these non-goals unless it explicitly says otherwise:

```text
Do not add runtime model calls.
Do not add provider SDK calls.
Do not add web fetching.
Do not add connector writes.
Do not add automatic memory writes.
Do not add automatic context injection.
Do not add plugin runtime import.
Do not add arbitrary skill execution.
Do not add callable extension catalog behavior.
Do not add shell/subprocess execution.
Do not add unrestricted network or browser automation.
Do not add mobile control.
Do not add public beta, public distribution, production readiness, or production authority.
Do not treat model/provider output, memory recall, preview output, or review text as authority.
Do not persist raw prompts, raw responses, raw provider payloads, raw local paths, raw logs, usernames, hostnames, serials, environment dumps, credentials, tokens, cookies, or private content.
```

## Prompt 0: Read And Produce A Focused Plan

Use this when starting a new Codex session before implementation.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: prepare the governed growth implementation plan for Ultimate AI Agent.
This is a planning-only session unless explicitly continued into Prompt 1.

Read first:
- AGENTS.md
- README.md
- VERSION.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
- docs/kanban/current_board.md
- docs/strategy/FOUNDER_COMMAND_CENTER_MASTER_PLAN.md
- docs/strategy/FOUNDER_COMMAND_CENTER_MVP_SPEC.md
- docs/control_center/FOUNDER_LOOP_V1_MILESTONES.md
- docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md
- docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md
- docs/tooling/EXTENSION_ACTIVATION_GRANTS.md
- docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md
- docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md
- docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md
- docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md
- docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md
- docs/roadmap/GOVERNED_GROWTH_SPINE.md
- docs/codex/CODEX_GOVERNED_GROWTH_PROMPTS.md

Also inspect SPECS.md, specs.md, SDLC.md, and sdlc.md if present. If absent,
note that AGENTS.md and the listed docs are the active process/spec guidance.

Produce a focused implementation plan for GGS-001 only.

GGS-001 means: Governed Growth Charter And Contracts. It should introduce typed
contracts, schemas, examples, and tests for growth candidates before any runtime
behavior exists.

Required plan sections:
1. Files to inspect further.
2. Existing code locations likely to host contracts.
3. Exact files to add/change.
4. Proposed contract names and fields.
5. Tests to add.
6. Verification commands.
7. Non-goals and blocked authorities.
8. Risks or ambiguities.

Do not implement anything in Prompt 0. Do not add routes, UI, dependencies,
runtime behavior, provider calls, memory writes, context injection, skill writes,
skill execution, connector writes, shell/subprocess authority, public beta,
distribution, or production authority.

Final response must list the focused plan and explicitly say whether Prompt 1 is
safe to run next.
```

## Prompt 1: Implement GGS-001 Governed Growth Contracts

Use this as the first implementation prompt.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-001 Governed Growth Charter And Contracts.

Definition:
GGS-001 creates the typed, testable contract layer for governed growth. It does
not build the Reflection Candidate Engine runtime, Review Inbox UI, skill write
path, memory write path, callable skill registry, curator service, provider
call, background daemon, verifier/fixer execution, or product authority.

Read first:
- AGENTS.md
- README.md
- VERSION.md
- docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md
- docs/kanban/current_board.md
- docs/roadmap/GOVERNED_GROWTH_SPINE.md
- docs/codex/CODEX_GOVERNED_GROWTH_PROMPTS.md
- docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md
- docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md
- docs/tooling/EXTENSION_ACTIVATION_GRANTS.md
- docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md
- docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md
- docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md
- docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md
- docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md

Also inspect existing contract/model/schema/test patterns under:
- src/ultimate_ai_agent/core
- docs/schemas
- tests
- scripts/verify_*.py

Scope:
- Add a growth contracts module in the existing core style, likely under
  `src/ultimate_ai_agent/core/growth/contracts.py` or the closest existing
  package pattern.
- Add `__init__.py` only if needed by existing package conventions.
- Add a JSON schema doc if existing docs/schemas patterns make that appropriate.
- Add focused tests for contract defaults, allowed states, denied authority
  invariants, safe-ref behavior, and invalid cases.
- Add or update the smallest relevant docs/index entries only if required by the
  repository documentation integrity policy.

Required contract concepts:
- GrowthCandidateKind
- GrowthCandidateState
- GrowthAuthorityPosture
- GrowthSourceRefs
- ReflectionCandidateInputContract
- ReflectionCandidateOutputContract
- MemoryCandidateContract
- SkillPackageContract
- SkillCandidateContract
- SkillPatchCandidateContract
- SkillUsageReceiptContract
- GrowthCandidateDecisionContract
- CuratorProposalContract
- VerifierFixCandidateContract

Do not overbuild. It is acceptable to implement these as Pydantic models,
Enums/Literals, validators, and helper constructors only.

Required root blocked-authority fields must default to false:
- memory_write_enabled
- context_injection_enabled
- runtime_import_enabled
- execution_enabled
- connector_writes_enabled
- shell_execution_enabled
- network_access_enabled
- browser_automation_enabled
- mobile_control_enabled
- provider_model_authority_enabled
- public_distribution_claimed
- production_authority_claimed

Required validation behavior:
- Candidate refs must be non-empty safe refs, not raw paths.
- Source refs must be safe refs only.
- Candidate kind/state must be explicit.
- Low-confidence or conflicting/ambiguous input must support ask/defer posture.
- `accepted` review state must not flip any blocked-authority field to true.
- Skill package `scripts` metadata must not imply execution authority.
- Verifier/fixer contracts must require baseline/current validation refs and
  rollback/safe-disable posture.
- Usage receipts must distinguish `read_only_guidance`, `proposal_context`, and
  `verifier_context`.

Non-goals:
- No backend routes.
- No Control Center UI.
- No persistence store.
- No background worker.
- No provider/model calls.
- No memory writes.
- No skill writes.
- No context injection.
- No runtime import or skill execution.
- No connector writes.
- No shell/subprocess execution.
- No OpenAPI route-count change unless a docs-only schema route already exists
  and the task explicitly discovers it is required. Prefer no route change.
- No dependencies.
- No production/public-beta/distribution claims.

Review/fix:
- Adversarially inspect for false authority claims, raw content leakage, raw path
  leakage, accidental route additions, accidental dependency additions, and
  product-truth drift.
- Fix P0/P1 issues before finishing.

Validation:
- Run focused tests for the new contracts.
- Run documentation integrity if docs/indexes change.
- Run `git diff --check`.
- If available and not too expensive, run existing manifest/OpenAPI tests to
  prove no route drift.

Commit guidance:
- Stage only GGS-001 files.
- Commit message: `add governed growth contracts`.
- Do not force push.

Final summary must list files changed, tests/verifiers run, skipped checks with
reasons, and remaining blocked items.
```

## Prompt 2: Implement GGS-002 Read-Only Skill Package Registry

Run this only after GGS-001 is complete, committed, verified, and current docs
are coherent.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-002 Skill Package Registry Read-Only View.

Definition:
The registry is an inspectable metadata surface for skill package candidates and
accepted skill packages. It is not a callable catalog, not a runtime import
layer, not a skill execution layer, and not a write path.

Read first:
- AGENTS.md
- docs/roadmap/GOVERNED_GROWTH_SPINE.md
- docs/codex/CODEX_GOVERNED_GROWTH_PROMPTS.md
- GGS-001 contracts and tests
- docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md
- docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md
- docs/tooling/EXTENSION_ACTIVATION_GRANTS.md

Scope:
- Add a read-only skill package registry/builder around existing GGS-001
  contracts.
- Add fixtures for candidate, accepted-read-only, blocked, stale, revoked, and
  future-scoped skill package states.
- Return safe metadata only: skill ref, version ref, title, description,
  category, tags, source evidence refs, review state, activation posture,
  blocked-authority flags, usage summary refs, rollback/safe-disable refs.
- If and only if route work is explicitly appropriate in the current repo state,
  add one read-only route. Otherwise keep this as core-only plus docs/tests.

Do not return:
- raw SKILL.md contents
- raw scripts
- raw templates
- raw references
- raw local paths
- raw prompts
- raw responses
- raw provider payloads
- raw logs
- usernames, hostnames, serials, environment dumps, credentials, tokens,
  cookies, or private content

Non-goals:
- No skill create/update/delete.
- No skill execution.
- No runtime import.
- No callable catalog.
- No provider/model calls.
- No memory writes.
- No context injection.
- No connector writes.
- No shell/subprocess execution.
- No public beta/distribution/production authority.

Validation:
- Tests must prove read-only behavior, blocked authority defaults, no raw content
  exposure, and fail-closed behavior for invalid package metadata.
- Run focused tests and relevant verifiers.

Final summary must list files changed, tests/verifiers run, skipped checks, and
blocked items.
```

## Prompt 3: Implement GGS-003 Reflection Candidate Engine V1

Run this only after GGS-001 is complete and preferably after GGS-002 exists.

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-003 Reflection Candidate Engine V1.

Definition:
The Reflection Candidate Engine is a deterministic proposal service over
redacted run/evidence/approval/validation refs. It emits candidates. It does not
write accepted memory, write skills, inject context, call providers, run tools,
create background sessions, or mutate product state.

Candidate engine means:
- input: safe refs and redacted summaries from completed UAA-managed work
- decision: choose no-op, memory candidate, skill create/patch/merge/archive/
  disable candidate, or verifier/fixer candidate
- output: typed candidate record with confidence, ambiguity posture, source refs,
  recommended operator action, blocked-authority flags, and rollback/safe-disable
  posture

Read first:
- AGENTS.md
- docs/roadmap/GOVERNED_GROWTH_SPINE.md
- docs/codex/CODEX_GOVERNED_GROWTH_PROMPTS.md
- GGS-001 contracts and tests
- GGS-002 registry if present
- memory provenance/review docs
- governed code workbench docs

Scope:
- Add `reflection_candidates.py` or closest existing pattern.
- Implement deterministic helper functions and validators.
- Add fixture-driven tests that simulate completed runs without provider calls.
- Include decision order exactly:
  1. no-op when not reusable
  2. memory for stable user/product facts
  3. patch existing skill before create
  4. merge overlapping skills before duplicate create
  5. create only when no existing skill fits
  6. archive/disable only as proposal
  7. verifier/fixer only from failed validation refs

Required tests:
- successful no-op decision
- memory candidate with stable source refs
- skill patch candidate preferred over new skill when existing skill fits
- skill create candidate when no existing skill fits
- low-confidence decision asks/defers
- invalid raw path/source content fails closed
- accepted candidate does not gain write/execution/context authority
- verifier/fixer candidate requires baseline/current validation refs and rollback
  posture

Non-goals:
- No LLM/provider calls.
- No background daemon.
- No automatic writes.
- No context injection.
- No skill execution.
- No route/UI unless separately scoped.
- No production authority.

Validation:
- Run focused tests.
- Run docs/OpenAPI checks if touched.
- Run `git diff --check`.

Final summary must list files changed, tests/verifiers run, skipped checks, and
blocked items.
```

## Prompt 4: Implement GGS-004 Growth Review Decisions

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-004 Growth Review Decisions.

Definition:
Growth Review Decisions are backend-owned decision records for candidates. They
make accept/edit/reject/defer/merge/archive/disable/reopen visible and durable.
They do not execute skills, write memory, inject context, or make artifacts
runtime-active.

Scope:
- Add decision validators and receipt refs around GGS candidates.
- Add tests for each decision type.
- Ensure rejected/stale/superseded candidates cannot become active via stale refs.
- Ensure edit decisions preserve source refs and audit refs.
- Ensure accepted state does not flip blocked-authority fields.
- Add docs for Review Inbox semantics if not already present.

Non-goals:
- No UI-only state as source of truth.
- No automatic memory or skill writes.
- No context injection.
- No skill execution.
- No plugin runtime import.
- No connector writes.
- No route unless explicitly scoped by current roadmap.

Validation and final summary follow the shared rules.
```

## Prompt 5: Implement GGS-005 Skill Usage Receipts

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-005 Skill Usage Receipts.

Definition:
A usage receipt records that an accepted skill or memory influenced a proposal.
It is evidence and telemetry, not authority. It supports explainability and later
curation.

Scope:
- Add usage receipt contract/builder if not already present.
- Add safe fixture examples.
- Add tests proving safe refs only, no raw content leakage, and clear `used_as`
  semantics.

Required `used_as` values:
- read_only_guidance
- proposal_context
- verifier_context

Non-goals:
- No automatic recall.
- No context injection.
- No skill execution.
- No writes to accepted skill content.
- No curator mutation.

Validation and final summary follow the shared rules.
```

## Prompt 6: Implement GGS-006 Curator Proposals

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-006 Curator Proposals.

Definition:
The Curator proposes stale/archive/merge/disable actions using usage receipts,
quality refs, conflict refs, and staleness refs. It cannot perform the action.

Scope:
- Add curator proposal model/builder.
- Add fixture-driven tests for stale, duplicate, low-quality, conflict, and no-op
  cases.
- Require review decision refs before any lifecycle state change is considered
  accepted.

Non-goals:
- No automatic archive.
- No automatic merge.
- No delete.
- No file writes.
- No background daemon.
- No provider/model calls.

Validation and final summary follow the shared rules.
```

## Prompt 7: Implement GGS-007 Verifier/Fixer Proposal Loop

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-007 Verifier/Fixer Proposal Loop.

Definition:
This is UAA self-healing for governed code work. A failed validation creates a
repair proposal that must be independently verified. Apply remains
approval-bound and rollback-aware.

Scope:
- Add verifier/fixer candidate contracts/builders around existing governed code
  workbench evidence and validation refs.
- Add tests for failed validation, repair proposal creation, re-verification refs,
  rollback refs, and safe no-op when evidence is incomplete.
- Keep this as proposal/evidence plumbing unless the current roadmap explicitly
  scopes deeper code workbench behavior.

Required sequence:
1. Baseline validation refs exist.
2. Proposed change refs exist.
3. Current validation refs exist.
4. Independent verifier verdict exists.
5. If failed, targeted repair candidate refs exist.
6. Re-verification refs exist after repair proposal.
7. Apply remains approval-bound.
8. Rollback refs remain present.

Non-goals:
- No autonomous code apply.
- No production self-modification.
- No new shell/subprocess authority beyond existing validated verifier lanes.
- No provider/model authority.
- No connector writes.
- No public beta/distribution/production authority.

Validation and final summary follow the shared rules.
```

## Prompt 8: Implement GGS-008 Offline Eval And Growth Metrics Planning

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-008 Offline Eval And Growth Metrics Planning.

Definition:
Plan how UAA will measure governed growth quality using redacted trajectories,
benchmark tasks, skill usefulness, duplication rate, rollback reliability,
operator acceptance rate, and verifier/fixer success rate.

Scope:
- Add docs-only benchmark/metrics plan.
- Add schema planning if the repo already has a schema-planning pattern.
- Define metrics without adding external training services or online model-weight
  update claims.

Non-goals:
- No training pipeline.
- No provider/model calls.
- No external service dependency.
- No online RL.
- No production readiness claim.

Validation and final summary follow the shared rules.
```

## Copy/Paste First Prompt For Codex

Use this first when you want Codex to start immediately with the safest useful
work:

```text
You are working only in doncazper/ultimate-ai-agent.

Task: implement GGS-001 Governed Growth Charter And Contracts.

Read first: AGENTS.md, README.md, VERSION.md,
docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md, docs/kanban/current_board.md,
docs/roadmap/GOVERNED_GROWTH_SPINE.md,
docs/codex/CODEX_GOVERNED_GROWTH_PROMPTS.md,
docs/tooling/PLUGIN_SKILL_ECOSYSTEM_BOUNDARY.md,
docs/tooling/INSPECTABLE_EXTENSION_CATALOG.md,
docs/tooling/EXTENSION_ACTIVATION_GRANTS.md,
docs/control_center/UAA_P1_070_MEMORY_SOURCE_PROVENANCE_MODEL.md,
docs/control_center/UAA_P1_071_MEMORY_REVIEW_DECISION_CAPTURE.md,
docs/control_center/UAA_P1_076_CROSS_SURFACE_MEMORY_INTAKE.md,
docs/control_center/UAA_P1_077_MEMORY_TO_LOOP_BINDING.md, and
docs/control_center/UAA_P1_075_GOVERNED_CODE_WORKBENCH.md.

Implement only the typed contract/test layer for governed growth candidates. A
candidate engine is a proposal generator over redacted safe refs; it emits typed
candidate records and does not write memory, update skills, inject context,
execute skills, call providers, run shell commands, fetch accounts, mutate
connectors, modify files outside this scoped code change, or create background
sessions.

Add Pydantic contracts/enums/validators/fixtures/tests for growth candidates,
skill packages, reflection candidate inputs/outputs, review decisions, usage
receipts, curator proposals, and verifier/fixer candidates. Every root contract
must default all authority flags to false: memory_write_enabled,
context_injection_enabled, runtime_import_enabled, execution_enabled,
connector_writes_enabled, shell_execution_enabled, network_access_enabled,
browser_automation_enabled, mobile_control_enabled,
provider_model_authority_enabled, public_distribution_claimed, and
production_authority_claimed.

Do not add routes, UI, persistence stores, dependencies, provider calls, runtime
model calls, memory writes, skill writes, context injection, runtime import,
skill execution, connector writes, shell/subprocess execution, OpenAPI route
changes, public beta, distribution, production readiness, or production
authority.

Run focused tests, documentation integrity if docs/indexes changed, and `git
diff --check`. Report skipped checks as blockers, not success. Final summary
must list files changed, tests/verifiers run, skipped checks with reasons, and
remaining blocked items.
```
