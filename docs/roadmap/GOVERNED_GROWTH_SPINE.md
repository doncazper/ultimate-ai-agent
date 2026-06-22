# Governed Growth Spine

Status: proposed planning artifact for Codex alignment

Scope: define how Ultimate AI Agent should adapt Hermes-Agent-style
self-improvement ideas without adding runtime authority. This document is a
shared implementation brief only. It does not add backend routes, Control Center
controls, dependencies, runtime model calls, memory writes, context injection,
skill execution, plugin runtime import, connector writes, shell/subprocess
execution, unrestricted network or browser automation, public beta, public
distribution, production readiness, or production authority.

## Source Inputs

This plan distills the Hermes-Agent deep-dive into a UAA-native growth model.
The transferable Hermes ideas are artifact-based procedural memory, skill
packages, post-run reflection, curation, usage metadata, rollback, and optional
offline eval/training. The non-transferable default is ungoverned autonomous
mutation.

UAA should use the phrase `governed growth`, not unrestricted
`self-improvement`, when naming product and implementation work.

## Product Promise

UAA should grow by noticing reusable lessons from approved work, proposing them
as reviewable memories or skills, showing evidence refs, and letting the
operator accept, edit, reject, merge, disable, archive, or roll back those
artifacts.

User-facing promise:

```text
UAA notices reusable lessons from your approved work, proposes them as memories
or skills, shows the evidence, and lets you accept, edit, reject, disable, or
roll them back.
```

Implementation promise:

```text
Growth is artifact-based, reviewable, permissioned, reversible, and testable.
The model may propose growth artifacts, but model output is never authority to
write memory, inject context, execute skills, mutate connectors, run shell
commands, or modify production state.
```

## Definitions

### Growth Artifact

A durable, typed, reviewable object that records a lesson or procedure. Growth
artifacts include memory candidates, skill candidates, skill patch candidates,
usage receipts, curator proposals, verifier/fixer proposals, and review
decision receipts.

### Skill Package

A skill package is UAA procedural memory. It is a versioned package of reusable
instructions and optional support files. It starts as inspectable guidance, not
executable authority.

Canonical shape:

```text
.uaa/skills/<skill_id>/SKILL.md
.uaa/skills/<skill_id>/manifest.json
.uaa/skills/<skill_id>/references/*
.uaa/skills/<skill_id>/templates/*
.uaa/skills/<skill_id>/scripts/*
.uaa/skills/<skill_id>/usage.json
```

Safety rule: a script inside a skill package is content for inspection only
until a later accepted milestone separately grants runtime import, execution,
policy evaluation, approval binding, revocation enforcement, audit receipts,
rollback, abuse-case tests, OpenAPI impact, Foundation Gate impact, and release
evidence.

### Candidate

A candidate is a proposed artifact, not an accepted memory, skill, action, or
runtime behavior. Candidates are safe-ref records with redacted summaries and
explicit blocked authority flags.

Candidate types:

```text
memory_candidate
skill_create_candidate
skill_patch_candidate
skill_merge_candidate
skill_archive_candidate
skill_disable_candidate
verifier_fix_candidate
no_op_decision
```

Candidate states:

```text
proposed
needs_review
accepted
edited
merged
rejected
deferred
blocked
stale
superseded
```

### Reflection Candidate Engine

The Reflection Candidate Engine is a post-run proposal service. It reviews
redacted run summaries, evidence refs, validation refs, approval refs, rollback
refs, and loaded skill refs after a completed task. It decides whether there is
a reusable lesson and emits only candidates.

It is not a background autonomous worker. It does not write memory, update
skills, inject context, call providers, run shell commands, fetch accounts,
execute connectors, or mutate product state.

Decision order:

```text
1. Return no_op_decision when the lesson is not reusable.
2. Propose memory_candidate only for stable user/product facts.
3. Propose skill_patch_candidate when an existing accepted skill should improve.
4. Propose skill_merge_candidate when two skills overlap.
5. Propose skill_create_candidate only when no existing skill fits.
6. Propose skill_archive_candidate only when usage/quality evidence supports it.
7. Propose verifier_fix_candidate only from failed validation with exact refs.
```

Required inputs:

```text
run_ref
task_summary_ref
redacted_transcript_summary_ref
source_surface_ref
approval_decision_refs
evidence_refs
validation_result_refs
rollback_receipt_refs
loaded_skill_refs
policy_result_refs
operator_actor_ref
```

Required output invariants:

```text
candidate_ref is stable and unique
candidate_kind is explicit
source refs are safe refs only
raw prompt/response/provider payload/path/log/private content is not persisted
confidence is present
ambiguity posture is present
blocked authority flags are present
recommended operator action is present
rollback/safe-disable posture is present when relevant
```

### Review Inbox

The Review Inbox is the product surface where operators decide whether growth
candidates become accepted artifacts. It should be part of Founder Command
Center only after backend-owned decision records exist. UI-only acceptance state
is not enough.

Minimum operator decisions:

```text
accept
edit
reject
defer
merge
archive
disable
reopen
```

Each decision must produce a safe receipt ref. Acceptance of a candidate is not
runtime execution authority.

### Usage Receipt

A usage receipt records that a memory or skill influenced a proposal. Usage
receipts let UAA show why it used a skill, support curation, and prove no hidden
authority was granted.

Minimum usage fields:

```text
usage_ref
skill_ref or memory_ref
run_ref
surface_ref
used_as: read_only_guidance | proposal_context | verifier_context
outcome_ref
accepted_by_operator: true | false | unknown
failure_ref optional
rollback_ref optional
created_at_ref
```

### Curator

The Curator proposes lifecycle changes for accepted skills and memories based on
usage, quality, duplication, conflict, and staleness. It is proposal-only in the
first milestone. It must not archive, merge, delete, disable, or rewrite
artifacts without a review decision.

### Verifier/Fixer Loop

The Verifier/Fixer Loop is the safer UAA interpretation of self-healing for code
work. It means:

```text
agent proposes patch
independent verifier evaluates patch against task and baseline
failed checks produce targeted repair proposal
repair is re-verified
apply remains approval-bound
rollback remains available
```

It does not mean autonomous self-modifying production code.

## Data Contracts To Introduce First

Codex should implement contracts before behavior. Suggested Pydantic model names
can be adjusted to match existing UAA style:

```python
class SkillPackageContract(BaseModel): ...
class SkillCandidateContract(BaseModel): ...
class SkillPatchCandidateContract(BaseModel): ...
class GrowthCandidateDecisionContract(BaseModel): ...
class SkillUsageReceiptContract(BaseModel): ...
class ReflectionCandidateInputContract(BaseModel): ...
class ReflectionCandidateOutputContract(BaseModel): ...
class CuratorProposalContract(BaseModel): ...
class VerifierFixCandidateContract(BaseModel): ...
```

Required blocked-authority fields for every root contract:

```text
memory_write_enabled: false
context_injection_enabled: false
runtime_import_enabled: false
execution_enabled: false
connector_writes_enabled: false
shell_execution_enabled: false
network_access_enabled: false
browser_automation_enabled: false
mobile_control_enabled: false
provider_model_authority_enabled: false
public_distribution_claimed: false
production_authority_claimed: false
```

## Proposed Milestone Conveyor

### GGS-001 Governed Growth Charter And Contracts

Goal: add planning docs, schemas, fixtures, and contract tests for governed
growth. No routes and no runtime behavior.

Deliverables:

```text
docs/roadmap/GOVERNED_GROWTH_SPINE.md
docs/schemas/governed_growth_candidate.schema.json
src/ultimate_ai_agent/core/growth/contracts.py
tests/test_governed_growth_contracts.py
```

Acceptance:

```text
contracts validate safe example fixtures
blocked authority flags default false
no accepted memory/skill write path exists
no route count changes
no dependencies added
```

### GGS-002 Skill Package Registry Read-Only View

Goal: add a persistence-neutral read-only catalog of skill package metadata and
candidate states.

Deliverables:

```text
src/ultimate_ai_agent/core/growth/skill_registry.py
docs/schemas/skill_package_registry.schema.json
tests/test_skill_package_registry.py
optional GET route only if current API conveyor allows route work
```

Acceptance:

```text
list/view metadata only
raw skill contents, raw local paths, raw prompts, raw responses, raw logs, and
private content are never returned
scripts are inspectable only and not executable
activation remains blocked/future-scoped
```

### GGS-003 Reflection Candidate Engine V1

Goal: create deterministic candidate-building logic around redacted inputs and
structured decisions. This is proposal-only.

Deliverables:

```text
src/ultimate_ai_agent/core/growth/reflection_candidates.py
tests/test_reflection_candidate_engine.py
docs/control_center/GOVERNED_GROWTH_REVIEW_INBOX.md or equivalent planning doc
```

Acceptance:

```text
no direct memory writes
no direct skill writes
no context injection
no provider calls required for deterministic tests
no autonomous background sessions
invalid/missing refs fail closed
low confidence emits ask/defer posture
```

### GGS-004 Growth Review Decisions

Goal: add backend-owned review decision records for candidates. UI can follow
only after backend semantics exist.

Deliverables:

```text
GrowthCandidateDecisionContract
accept/edit/reject/defer/merge/archive/disable/reopen validators
decision receipt refs
focused tests
```

Acceptance:

```text
acceptance changes review state only
acceptance does not execute or inject anything
edit decisions preserve source refs and audit refs
rejected candidates cannot become active via stale refs
```

### GGS-005 Skill Usage Receipts

Goal: record when accepted procedural memory influenced a proposal.

Deliverables:

```text
SkillUsageReceiptContract
usage receipt builder
safe fixture examples
tests for no raw content leakage
```

Acceptance:

```text
usage receipts are safe refs only
use_as field distinguishes read-only guidance from proposal context
receipts support later curation but do not mutate skills
```

### GGS-006 Curator Proposals

Goal: add proposal-only stale/merge/archive/disable suggestions.

Deliverables:

```text
CuratorProposalContract
usage summary fixture
curator proposal builder
focused tests
```

Acceptance:

```text
curator cannot mutate accepted artifacts
curator cannot delete files
curator cannot silently archive or merge
all changes require review decisions
```

### GGS-007 Verifier/Fixer Proposal Loop

Goal: add self-healing for governed code work as verifier-backed repair
proposals, not autonomous apply.

Deliverables:

```text
VerifierFixCandidateContract
baseline/current validation refs
repair proposal refs
rollback refs
focused tests around failure and safe no-op
```

Acceptance:

```text
failed validation creates repair candidate only
apply remains approval-bound
rollback refs are present
no shell/subprocess authority is added beyond existing verifier commands
```

### GGS-008 Offline Eval And Trajectory Planning

Goal: plan redacted trajectories and evaluation harnesses for measuring growth
quality.

Deliverables:

```text
growth quality benchmark plan
redacted trajectory schema
skill quality metrics
no runtime training authority
```

Acceptance:

```text
no online model-weight update claim
no external training service dependency
no provider/model authority claim
```

## Non-Goals For All GGS Milestones

Do not add:

```text
autonomous skill writes
automatic memory writes
automatic context injection
arbitrary skill script execution
plugin runtime import
callable extension catalog
connector writes
unrestricted shell/subprocess execution
unrestricted network or browser automation
background mutation daemon
online model-weight updates
provider/model output as authority
public beta/public distribution/production authority claims
```

## Safety And Evidence Rules

All artifacts must use safe refs, redacted summaries, bounded previews, and
explicit blocked states. Durable docs, reports, tests, fixtures, and logs must
not include raw prompts, raw responses, raw provider payloads, raw local paths,
raw logs, usernames, hostnames, serials, environment dumps, credential material,
secrets, tokens, cookies, or private content.

## Codex Implementation Rules

When Codex implements any GGS milestone:

```text
1. Read AGENTS.md, README.md, VERSION.md, PRODUCT_RELEASE_TRUTH_PACKET,
   current_board, Founder Command Center docs, plugin/skill boundary docs,
   memory docs, and this file first.
2. Treat this file as planning guidance, not authority.
3. Implement one milestone per branch.
4. Prefer contracts, fixtures, validators, and tests before routes or UI.
5. Do not add dependencies unless the prompt explicitly scopes them.
6. Do not update route counts unless a route milestone explicitly requires it.
7. Keep OpenAPI operation IDs stable.
8. Run focused tests plus documentation integrity when possible.
9. Report skipped checks as blockers, not success.
10. Final summary must list files changed, tests/verifiers run, skipped checks,
    and remaining blocked items.
```

## Rollback

To roll back this planning artifact, remove this file and any docs/index entries
that point to it. No runtime authority needs rollback because this file adds no
runtime behavior.
