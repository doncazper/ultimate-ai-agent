# UAA Governed Self-Improvement Implementation Plan

Status: recovered product and implementation plan; planning-only.
Source confidence: high from archived design evidence and current contracts.

The historical repository prompt referenced by an archived task did not
survive in the current tree. This document preserves the recovered outcome,
loop, authority boundaries, and finite implementation sequence without
claiming verbatim source recovery.

It grants no self-modification, automatic code change, hidden memory update,
automatic training, skill activation, Git mutation, pull request, merge,
release, deployment, provider/model, browser, connector, shell, production, or
standing authority.

## Product Outcome

Governed self-improvement should be a central UAA capability: UAA may notice
where it is weak, explain the evidence, decide what kind of remedy might help,
and propose the improvement. Human governance applies to adoption and
consequential execution—not to the mere recognition that improvement is
needed.

The whole loop is:

```text
observe outcomes, failures, friction, and repeated work
  -> identify remedy category
  -> form an evidence-backed improvement proposal
  -> Action Inbox: accept, edit, reject, or defer
  -> accepted proposal becomes a separately scoped implementation task
  -> dedicated branch/worktree and bounded change
  -> tests, evals, and verification
  -> draft PR or review packet returns to Action Inbox
  -> reviewed outcome informs future recommendations
```

This is autonomous self-assessment under human-governed adoption, not
unrestricted self-modification.

## Observations And Remedy Categories

Eligible observations are redacted, bounded, and provenance-bound:

- repeated deterministic test/eval failure;
- recurring operator correction or rejection reason;
- repeated manual step in a governed workflow;
- latency, reliability, readability, or setup friction above an accepted
  budget;
- a missing capability edge in the System Capability Map;
- a blocked workflow with a named missing dependency;
- incident, rollback, reconciliation, or safe-disable evidence;
- documentation/runtime contradiction;
- operator-submitted improvement feedback.

Each candidate must choose one primary remedy category:

- bug fix;
- workflow or UX improvement;
- skill/capability proposal;
- integration contract;
- documentation or runbook correction;
- configuration/default change;
- evaluation or observability improvement;
- intentional exclusion/no-change recommendation.

The category controls which later authority and verifier set would be needed.
It does not grant that authority.

## Canonical Contracts

### ImprovementObservation

Contains observation ref, source/evidence refs, affected capability/product,
implementation truth, recurrence/frequency posture, severity, operator impact,
privacy class, observed revision, and expiry. Raw prompts, responses, logs,
payloads, paths, usernames, and hostnames are excluded from durable evidence.

### ImprovementCandidate

Groups compatible observations into one bounded problem statement with:

- exact affected scope and owner;
- known facts, assumptions, unknowns, and contradictions;
- suggested remedy category and alternatives;
- confidence and expected operator value;
- risks, authority implications, and non-goals;
- dedupe/supersession binding.

### ImprovementProposal

The reviewable proposal contains:

- immutable proposal ref/hash and source revision set;
- outcome hypothesis and measurable acceptance criteria;
- exact files/components or product surfaces in scope when known;
- implementation, migration, safe-disable, rollback/revert, and evidence plans;
- tests/evals required and historical-failure fixtures;
- dependencies, conflicts, cost/effort band, and uncertainty;
- requested child authority lanes, each exact and independently reviewable;
- statement of what UAA may observe/propose now versus what remains blocked.

### ImprovementDecision

Action Inbox owns `accepted_for_scoping`, `edited`, `rejected`, `deferred`,
`duplicate`, `superseded`, and `blocked`. Acceptance authorizes only creation of
a bounded task/spec. It does not authorize implementation, Git, skill
activation, recurring execution, merge, release, or deployment.

### ImprovementExecutionPacket

For an accepted proposal, a separately governed development lane may create a
packet binding task/spec, branch/worktree, base/head revisions, diff hash,
tests/evals, verifier results, review findings, rollback/revert plan, receipts,
and remaining risks. Each mutating development step follows the existing exact
lane that owns it.

### ImprovementOutcome

Records accepted, rejected, reverted, superseded, failed safely, blocked, or
unknown results; measured outcome; regressions; operator decision; and future
recommendation impact. It cannot rewrite the observations or approval history.

## Authority Model

The only candidate for bounded autonomous graduation inside this program is a
revocable, metadata-only `improvement/propose` lane. If separately accepted,
it may read allowlisted redacted evidence and create an ImprovementProposal.
It may not:

- apply a change;
- modify source, docs, config, memory, prompts, skills, tests, thresholds, or
  trusted computing base components;
- create or switch a branch/worktree;
- commit, push, open/update a PR, merge, tag, release, deploy, or publish;
- activate a skill, workflow, connector, provider, model, browser, shell, or
  recurring task;
- expand its own scope, policy, lease, budget, or evidence access;
- treat successful tests as approval.

Implementation, Git, skill activation, recurring workflows, external actions,
and deployment each require their existing exact authority lane and a new
approval bound to the precise payload/revision.

Changes to PolicyEngine, LocalApprovalAuthority, approval validation,
redaction, evidence integrity, route classification, Foundation Gate, secret
handling, or other trusted computing base boundaries remain blocked from
autonomous implementation.

## Ownership And Product Integration

- Capability Evaluation Lab owns repeatable cases, baselines, attribution,
  and regression evidence.
- Autocorrect owns reviewed correction candidates and feedback that may become
  observations.
- Health/diagnostics own runtime readiness and recommendation inputs.
- System Capability Map owns typed implementation/dependency truth and missing
  edges; connectivity never grants authority.
- Action Inbox owns proposal and review decisions.
- Work Board/Tasks own accepted implementation work and state.
- Governed Code Workbench/developer tooling owns scoped change preparation.
- Evidence owns content-free receipts and revision proof.
- Memory may retain only separately reviewed preferences or lessons with
  provenance, staleness, correction, and deletion controls.
- Python Agent Core owns all canonical self-improvement nouns and transitions.

Any UI route must have CLI/API parity and a stable OpenAPI contract. React may
own only filters, expanded sections, selected proposals, and layout choices.

## Ranking And Dedupe

Proposal ranking should remain explainable and deterministic in the first
slice. Inputs may include recurrence, severity, operator time saved, affected
workflow criticality, regression risk, evidence quality, implementation cost,
dependency readiness, and prior reviewed outcomes.

Ranking never suppresses a security or data-integrity issue. Duplicate
observations attach to one candidate. Changed scope or acceptance creates a new
proposal revision; it does not mutate accepted history.

## Finite Phase Sequence

### Q29-S0: Baseline and typed nouns

Inventory existing health recommendations, Action Inbox, Evidence, evaluation,
Work Board, Code Workbench, developer feedback, and Git approval contracts.
Define the five canonical nouns and explicit unavailable states. No routes or
mutation.

### Q29-S1: Observation adapters

Add allowlisted read-only adapters for redacted evaluation failures, reviewed
correction decisions, health recommendations, and operator feedback. Prove
source rights, bounds, dedupe, retention, and safe refs.

### Q29-S2: Candidate classification

Implement deterministic candidate grouping, remedy categorization, known/
assumed/unknown separation, risk classification, and owner/dependency routing.

### Q29-S3: Proposal builder

Build evidence-backed proposals with hypotheses, acceptance criteria, scope,
non-goals, tests/evals, rollback, authority implications, and alternatives.
Keep the lane proposal-only and safe-disabled by default.

### Q29-S4: Action Inbox review

Add readable proposal review, exact revision/hash binding, accept/edit/reject/
defer, idempotency, receipts, stale blocking, CLI/API/UI parity, and route
classification. Acceptance produces only a scoped task/spec.

### Q29-S5: Task decomposition handoff

Map accepted proposals into bounded Work Board tasks, dependencies, suggested
branch/worktree posture, verifier plan, and explicit authority requests. Do not
start implementation automatically.

### Q29-S6: Governed implementation packet

Compose existing development lanes so an separately authorized task can create
a scoped patch in an isolated worktree. Bind base/head revisions, diff hash,
files, commands, budgets, receipts, and rollback/revert plan. No broad code
execution flag.

### Q29-S7: Tests, evals, and independent review

Run only approved focused commands, compare historical failures and current
baselines, collect content-free evidence, and return failures to the task. Do
not weaken assertions, thresholds, redaction, or safety checks to obtain green.

### Q29-S8: Draft PR/review return

Through a separately authorized exact GitHub lane, prepare a draft PR or local
review packet. Return it to Action Inbox with changes, evidence, risk,
unresolved findings, and revert plan. No auto-merge.

### Q29-S9: Outcome learning

After human adoption/rejection/revert, record measured outcome and propose
adjustments to ranking, fixtures, workflows, or documentation. Any behavioral
rule change is another proposal.

### Q29-S10: Acceptance and hardening

Run adversarial authority tests, redaction review, replay/concurrency tests,
safe-disable and rollback/revert drills, docs/product-language checks, and the
Foundation Gate. Permit at most two bounded repair passes; unresolved edge
cases become owned follow-ups rather than an endless acceptance loop.

## Required Failure Tests

- proposal tries to include raw prompt/response/log/private path content;
- changed observation set or proposal hash at decision time;
- acceptance interpreted as implementation or Git authority;
- duplicate or conflicting idempotency reuse;
- proposed change touches trusted computing base boundaries;
- tests pass but approval is absent/expired/wrong scope;
- proposal attempts to weaken a failing test or verifier;
- implementation packet includes unrelated dirty files;
- PR head differs from verified revision;
- unknown execution or Git outcome receives a blind retry;
- reverted/rejected outcome is rewritten as successful learning;
- memory receives a lesson without separate review and provenance.

## Definition Of Done For Q29

Q29 is complete when UAA can transform allowlisted redacted observations into
an explainable improvement proposal, receive a revision-bound human decision,
create a bounded implementation packet only through separately authorized
lanes, return tests/evals/review evidence, and record the reviewed outcome.

It is not complete merely because UAA can display recommendations, and it does
not grant automatic implementation, PR, merge, release, deployment, skill
activation, or self-modification authority.
