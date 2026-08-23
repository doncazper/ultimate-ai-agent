# UAA Autocorrect Controls Implementation Plan

Status: reconstructed product and implementation plan; proposal-only baseline.
Source confidence: medium. No exact archived prompt was located.

This plan strengthens Queue V2 Q28 without pretending that historical wording
was recovered. It combines the accepted recovery contract, Queue V2 outcome,
ECO-008 ChangeSet semantics, Action Inbox revision binding, Evidence receipts,
and UAA's assistant-utility invariant.

It grants no automatic correction, canonical-state mutation, prompt rewrite,
memory rewrite, connector write, model/provider call, browser, shell,
background, production, or public authority.

## Product Outcome

Autocorrect is UAA's reviewable correction layer. It should notice a likely
mistake or inconsistency, explain the evidence, show the exact proposed change,
and let the operator accept, edit, reject, defer, or suppress the pattern.

The larger loop is:

```text
observed candidate
  -> deterministic validation and bounded evidence
  -> exact correction proposal against a canonical revision
  -> operator decision
  -> separately approved ChangeSet apply lane
  -> receipt and optional rollback
  -> reviewed correction-pattern feedback
```

The Q28 slice stops at proposal controls plus a separately gated local
ChangeSet handoff. A correction suggestion is never permission to edit.

## Intended Correction Families

The first implementation should support only deterministic, locally provable
families whose owning domains already expose validation and revision truth:

- stale or conflicting Task, Board, Calendar, CRM, or source-artifact links;
- invalid lifecycle/status combinations;
- missing required normalized metadata where the value is deterministically
  derivable from existing canonical data;
- duplicate projections that point to the same canonical object;
- explicit operator correction of a prior UAA proposal;
- versioned configuration inconsistencies with an allowlisted schema fix.

Not admitted in the initial slice:

- free-form rewriting of messages, prompts, memories, documents, or code;
- inferred factual corrections without cited evidence;
- identity merge, financial classification, legal/compliance conclusion, or
  other consequential domain judgment;
- create, delete, archive, retention, account, connector, or external action;
- model-generated replacement values treated as truth.

## Canonical Contracts

### CorrectionCandidate

Records a suspected problem without storing unnecessary private content:

- stable candidate ref and correction-family ref;
- owning domain, canonical target ref, workspace/privacy class;
- observed revision and keyed content fingerprint;
- violated invariant or operator-feedback ref;
- bounded evidence refs and deterministic detector version;
- confidence band: `certain`, `high`, `review_required`, or `unknown`;
- detected timestamp, expiry, and supersession posture.

Confidence is descriptive. It never changes the approval requirement.

### CorrectionProposal

Binds one candidate to one exact proposed result:

- proposal ref and immutable proposal hash;
- candidate ref and source revision/fingerprint;
- keyed before/after fingerprints and content-free field diff;
- private preview handle where the owning surface may reveal values;
- consequence summary, conflicts, exceptions, and unknowns;
- ChangeSet plan ref when ECO-008 supports the domain;
- safe-disable, rollback-readiness, and expiry posture;
- detector/rule version and redacted reason summary.

The proposal cannot contain wildcard targets, unresolved objects, or an
unbounded “fix similar items” scope.

### CorrectionDecision

Operator choices are `accepted_for_apply`, `edited`, `rejected`, `deferred`,
`suppressed_pattern`, `superseded`, and `blocked`. Every decision binds the
proposal hash and revision. `accepted_for_apply` authorizes only creation of an
exact child approval request; it does not execute the ChangeSet.

### CorrectionFeedback

Captures reviewed reasons such as wrong target, wrong rule, insufficient
evidence, unsuitable wording, expected exception, or correct proposal. It is a
versioned input to future proposal ranking and rule review—not automatic
training, hidden memory, or permission to weaken an invariant.

## Ownership And Parity

- Owning product domains retain canonical record truth and validation.
- ECO-008 owns supported local ChangeSet preparation, exact local apply,
  receipts, conflict checks, and rollback.
- Action Inbox owns correction decision envelopes.
- Evidence owns content-free durable decisions and receipts.
- Memory may receive only separately reviewed, provenance-bound preference or
  exception records.
- Python Agent Core owns detectors, proposals, decisions, and feedback.
- API and CLI expose the same list, inspect, preview, decide, prepare-apply,
  receipt, and rollback-readiness contracts.
- Control Center renders those backend-owned states; React may own only filter,
  selection, and disclosure state.

## Staleness, Replay, And Concurrency

Immediately before decision and again before ChangeSet preparation, compare:

- canonical target identity;
- revision/version;
- keyed content fingerprint;
- proposal hash;
- detector/rule version if the rule affects consequences;
- exact operator-edited replacement payload.

Any difference marks the proposal `stale` or `superseded`. It cannot be
silently rebased. Re-evaluation creates a new proposal ref and new decision.

Stable per-proposal idempotency returns the original decision receipt on exact
replay. Conflicting reuse fails closed. Apply and rollback use their own exact
idempotency refs and approval scopes.

## Rejection Learning

Rejection learning improves suggestion quality while preserving truth:

1. store the decision reason as a provenance-bound feedback record;
2. aggregate only content-free rule/target-class outcomes;
3. propose detector threshold, exception, documentation, or UX changes;
4. evaluate changes against accepted and rejected historical fixtures;
5. require normal review before activating a new detector/rule version;
6. never let rejection disable a security, authority, privacy, or data-
   integrity invariant.

A user rejecting one proposal does not establish a global preference unless
they explicitly approve that separately scoped preference.

## Operator Experience

The Correction Review surface should show:

- what appears wrong;
- why UAA thinks so and which evidence supports it;
- exact before/after values only where the operator is authorized to view them;
- confidence, exceptions, unknowns, affected objects, and downstream effects;
- whether apply is supported, blocked, or requires another domain lane;
- Accept for apply, Edit, Reject, Defer, and Suppress this pattern;
- stale/superseded truth, prior decisions, receipt, and rollback readiness.

No primary workflow should expose raw JSON. The CLI may provide JSON as an
optional machine-readable projection alongside a readable default.

## Milestone Sequence

### Q28-A0: Registry and fixture contract

Define typed nouns, enums, safe refs, redaction, deterministic fixtures, and
proposal hashing. No route or mutation.

### Q28-A1: Deterministic candidate detectors

Implement a very small allowlist against fixture/local canonical data. Prove
false-positive, exception, expired, missing-target, and unknown states.

### Q28-A2: Exact proposals and preview

Add content-free diffs, authorized private preview handles, consequences,
conflicts, expiry, and CLI inspection. No apply.

### Q28-A3: Action Inbox decisions

Add revision-bound decision envelopes, idempotency, edit-as-new-proposal,
receipts, and stale/superseded handling with API/OpenAPI/manifest/CLI parity.

### Q28-A4: ECO-008 local apply handoff

For already-supported local domains only, prepare a separate exact approval
scope and ChangeSet. Do not expand ECO-008 domain authority inside Q28.

### Q28-A5: Rollback and reconciliation

Expose apply receipt, rollback readiness, separately approved rollback, and
unknown-outcome blocking. Prove exact replay and conflicting replay behavior.

### Q28-A6: Reviewed feedback and rule evaluation

Add feedback records, aggregate evaluation, proposed rule-version changes,
safe-disable, and finite regression evidence. No automatic activation.

## Verification

Focused verification must cover:

- proposal hashes and revision binding;
- stale decision and stale apply rejection;
- deterministic false-positive/exception fixtures;
- exact replay and conflicting idempotency reuse;
- no mutation from candidate, proposal, preview, or decision alone;
- ECO-008 domain allowlist and transaction rollback;
- private preview authorization and durable redaction;
- acceptance/rejection feedback separation from training and authority;
- API operation IDs, route side-effect classification, manifest, CLI, and UI
  parity for any added route;
- safe-disable and separately approved rollback.

## Definition Of Done For Q28

Q28 is complete only when a supported deterministic correction can travel from
candidate through readable exact proposal and revision-bound decision to an
optional separately approved local ChangeSet receipt, with stale blocking,
replay safety, rollback posture, redaction, and focused tests.

Q28 completion does not mean UAA can silently autocorrect arbitrary content or
that the whole cross-product correction vision is complete.
