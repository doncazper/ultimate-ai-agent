# UAA Cross-Platform Social Publishing Implementation Plan

Status: recovered whole-vision plan with a proposal/dry-run Q30 slice.
Source confidence: high from archived design evidence and current Social,
ecosystem, Action Inbox, Evidence, and external-action contracts.

Implementation status: Q30-P0 through Q30-P4 are implemented locally as a
content-free synthetic fixture kernel and repo-local CLI. Canonical Studio-owned
draft refs, per-platform variants, fixture capability contracts, compatibility
findings, immutable plans, exact dry-run review envelopes, independent simulated
settlements, content-free receipts, replay conflict checks, failed-only retry
plans, and unknown-outcome reconciliation are covered. Q30-P5 API/Control Center
parity and Q30-P6 acceptance freeze remain next; no live adapter exists.
Focused verifier: `scripts/verify_social_publishing_q30.py`.

Q30 grants no account connection, authentication, platform read/write,
publish/send, upload, browser, network, background scheduler, provider SDK,
production, public, or standing authority.

## Product Outcome

The flagship workflow is “create once, adapt visibly, approve exactly, publish
independently, reconcile honestly, learn from outcomes.”

An operator should be able to:

1. create one canonical post and media set;
2. generate or author platform-specific variants;
3. inspect exact side-by-side differences and compatibility findings;
4. approve one exact bundle covering named accounts, payloads, and timing;
5. publish only through separately graduated platform/action lanes;
6. receive one independent receipt per destination;
7. preserve known successes and retry only eligible failed destinations;
8. reconcile unknown outcomes before retry;
9. return engagement evidence to Social Media Intelligence.

UAA must not blindly send identical content to every platform or hide rewrites
behind a generic “optimized” label.

## Q30 Admitted Slice

Q30 stops at platform-neutral planning, exact variants, compatibility review,
approval-envelope preparation, and deterministic dry-run settlements. It may
simulate succeeded/failed/blocked outcomes using fixtures. It cannot connect an
account or call a platform.

The slice proves that live adapters could later be added without changing the
canonical nouns, ownership, approval hash, per-target idempotency, partial-
failure, evidence, and reconciliation semantics.

## Activation Gates For Any Later Live Lane

No platform write lane may be proposed for graduation until all of the
following are independently implemented and verified:

- Work Board owns production tasks and dependencies;
- CRM owns people/organization relationships and outreach boundaries;
- Communications owns comments/messages and human-controlled response lanes;
- Studio owns durable draft and media-asset identity/versioning;
- Calendar owns scheduled time and timezone truth;
- Social Media Intelligence provides accepted read-only account/performance
  contracts;
- Action Inbox supports exact multi-target parent/child approval envelopes;
- Evidence supports independent child attempts, settlements, receipts, and
  reconciliation;
- PolicyEngine and LocalApprovalAuthority bind exact payload hashes, accounts,
  operations, costs, expiry, and idempotency;
- opaque credential handles and revocation/safe-disable posture exist;
- platform terms, permissions, review requirements, rate/cost posture, test
  account, rollback/correction plan, and reconciliation read lane are accepted.

An available SDK, connector, browser, or credential is not activation.

## Ownership

- Studio owns canonical drafts, media assets, edits, and versions.
- Calendar owns desired publish time, timezone, conflicts, and schedule views.
- Work Board owns content-production tasks and handoffs.
- Social Media Intelligence owns observed performance and recommendations.
- Communications owns comments, messages, response drafts, and human send.
- CRM owns people, organizations, collaborators, and relationship context.
- Platform adapters own only their exact accepted read/write operations.
- Action Inbox owns exact plan and execution review.
- Evidence owns child attempts, settlements, receipts, and reconciliation.
- Memory receives only reviewed, provenance-bound learning.
- Python Agent Core owns the canonical publishing state machine. UI state never
  becomes publication truth.

## Typed Nouns

### SocialPostDraft

Canonical intent: draft ref/version/hash, owner/workspace, campaign/content
pillar, objective, canonical body, link refs, canonical media versions,
audience posture, status, provenance, and retention.

### SocialPlatformVariant

One exact destination adaptation: platform, account ref, draft/media versions,
exact rendered payload hash, private preview handle, adaptation reasons,
operator edits, link/hashtag/mention posture, accessibility fields, and
supersession lineage.

### SocialDistributionTarget

Exact platform, account, operation, content format, capability posture,
requested time/timezone, and adapter/version refs. Wildcard platforms or
accounts are invalid.

### SocialCompatibilityFinding

Deterministic finding with severity (`info`, `warning`, `blocking`, `unknown`),
constraint ref, affected field/media, bounded explanation, suggested remedy,
platform-capability source/version, and reviewed override posture. Unknown
constraints fail closed for live execution.

### SocialPublishPlan

Immutable plan binding canonical draft/version/hash, media versions, every
target, every child payload hash, desired times, findings, cost/rate posture,
parent and child idempotency refs, expiry, safe-disable, correction/rollback,
and reconciliation posture.

### SocialPublishApprovalEnvelope

Exact review contract binding the plan hash, all child target/account/payload
hashes, requested operations, timing, cost ceiling where applicable, expiry,
and child authority requirements. Approval cannot be expanded after decision.

### SocialPublishAttempt

One target's immutable attempt number, idempotency ref, approval/lease refs,
payload hash, adapter version, start/end timestamps, and redacted outcome refs.

### SocialPublishSettlement

Independent target outcome:

- `succeeded`;
- `policy_rejected`;
- `platform_rejected`;
- `rate_limited`;
- `auth_expired`;
- `failed_safely`;
- `unknown`;
- `cancelled_before_dispatch`.

### SocialPublishReceipt

Content-free durable proof of target/account/operation, payload fingerprint,
attempt/settlement, platform object safe ref when known, timing, evidence,
reconciliation posture, correction capability, and no-retry truth.

### SocialPublishReconciliationResult

Records an exact read-lane check for an unknown outcome, matched/unmatched or
still-unknown result, evidence refs, next safe action, and whether retry needs
a new approval.

## Platform Capability Contracts

Q30 should define versioned capability data for Instagram, X, and TikTok using
fixtures only. Each contract must distinguish known, unavailable, and unknown:

- account type and eligibility;
- supported text, image, video, carousel, story/reel/short-form formats;
- media count, size, duration, aspect ratio, encoding, caption, alt-text, link,
  hashtag, and mention constraints;
- native scheduling and draft support;
- permissions, app review, business verification, and test-account needs;
- rate limits, quota, paid-tier, and cost posture;
- edit/delete/correction and reconciliation capabilities;
- credential revocation and adapter safe-disable;
- source/version/last-reviewed timestamp.

Do not purchase plans, start trials, create accounts, change account type, or
request production permissions within Q30.

## Create Once, Adapt Per Platform

Canonical text is a source, not a payload to broadcast blindly. Variant
generation must:

- preserve meaning, claims, calls to action, sensitive-content posture, and
  approved links;
- expose every text/media difference;
- state the reason for each adaptation;
- keep operator edits as new immutable versions;
- never silently remove disclosures or alter factual claims;
- never manufacture mentions, hashtags, endorsements, consent, or rights;
- block when media rights or platform constraints are unknown.

Model assistance may be added later only as proposal generation. It does not
establish compatibility or publication authority.

## Exact Multi-Target Approval

One parent decision may approve a bundle only when the envelope displays and
binds every child:

- platform and exact account;
- operation and payload hash;
- visible preview/diff;
- media versions and rights posture;
- desired timing and timezone;
- blocking/warning/unknown findings;
- cost/rate posture;
- retry, correction, reconciliation, and expiry rules.

Each child still requires its own eligible adapter and exact execution lease.
Approval of Instagram never grants X or TikTok authority. Adding/removing a
target, changing text/media/account/time, or resolving a blocking finding
creates a new plan and approval.

## Partial Failure And Retry

Fan-out is a set of independent child transactions, never an all-or-nothing
fiction across external platforms.

- Preserve every known success and its receipt.
- Never retry a succeeded child.
- Retry only an explicitly eligible failed/rate-limited child with stable
  per-target idempotency and the required approval/lease posture.
- Never blind-retry `unknown`; reconcile through an exact read lane first.
- If reconciliation remains unknown, require an operator decision and prefer
  correction/manual inspection over duplicate publication.
- Payload, target, account, or requested-time change requires a new plan and
  approval.
- Parent status must expose mixed/partial outcomes rather than collapse them
  into generic success or failure.

## Scheduling

Q30 may plan desired times and render conflicts. It does not own a background
publisher. Later scheduling requires its own exact authority, wake/recovery
semantics, deadline/expiry, lease renewal, cancellation, clock/timezone tests,
safe-disable, and startup reconciliation. Recurring publication is a separate
later lane and must not be inferred from one scheduled approval.

## Operator Surfaces

### Studio distribution workspace

Shows canonical draft, platform tabs, exact previews/diffs, compatibility,
media rights, account readiness, and saved immutable variants.

### Calendar

Shows planned, approval-pending, blocked, scheduled-plan, dispatching,
partially settled, reconciliating, succeeded, failed, and cancelled states.
`published` appears only from verified platform settlement.

### Action Inbox

Shows bundle overview plus every child target/payload, findings, timing,
cost/rate posture, expiry, and retry/correction semantics. No raw JSON primary
view.

### Evidence

Shows the parent plan/decision, each child attempt/settlement/receipt,
reconciliation, and correction/rollback limits in a readable timeline.

### Social Media Intelligence

Consumes only verified publication and engagement evidence. It must preserve
platform/account/content identity and never infer outcome from a planned post.

CLI/API surfaces must expose equivalent list, inspect, preview, validate,
prepare-approval, dry-run, settlement, and reconciliation projections.

## Milestone Sequence

### Q30-P0: Baseline and ownership gate

Verify all dependencies and record missing/blocked states. Define nouns and
state machine. No routes, credentials, or adapters.

State: implemented locally for the bounded synthetic fixture contract.

### Q30-P1: Canonical draft and variant contracts

Bind Studio draft/media versions to exact platform variants and content-free
hashes. Add deterministic fixtures and CLI inspection.

State: implemented locally.

### Q30-P2: Capability registry and compatibility engine

Add fixture-only Instagram/X/TikTok contracts, deterministic findings,
unknown blocking, media-rights posture, and versioned source refs.

State: implemented locally with reviewed fixture refs only.

### Q30-P3: Publish plan and exact review

Build immutable plans, parent/child idempotency, readable previews/diffs,
exact multi-target envelope, expiry, and stale/superseded handling.

State: implemented locally for immutable refs, fingerprints, expiry binding,
and exact approve/reject dry-run review; readable UI remains Q30-P5.

### Q30-P4: Deterministic dry-run transaction kernel

Use injected adapters only to simulate independent outcomes. Prove mixed
settlement, replay, no-retry success, failed-only retry eligibility, unknown
reconciliation blocking, and content-free receipts.

State: implemented locally without adapters, network, persistence, or external
side effects.

### Q30-P5: API/CLI/Control Center parity

Add any accepted read/proposal routes with stable OpenAPI operation IDs, route
classification, manifest tests, readable UI, and no execution handler.

State: CLI implemented; API and readable Control Center remain next.

### Q30-P6: Security and acceptance freeze

Run redaction, authority, rights, stale revision, replay, concurrency, unknown
outcome, and product-language tests. Record platform live adapters as blocked
follow-ups, not implied completion.

### Later SP-LIVE lanes

Graduate one platform and one operation at a time only after the activation
gates. Start with a test account, explicit operator-present dispatch, bounded
payload, independent reconciliation read, safe-disable, and correction plan.
Each adapter is its own task/PR/acceptance packet.

## Definition Of Done For Q30

Q30 is complete when an operator can create a canonical fixture draft, inspect
exact platform variants and findings, approve or reject an immutable dry-run
bundle, observe independent simulated settlements/receipts, and prove safe
retry/reconciliation behavior through Python Core, CLI/API, and readable UI as
admitted.

Q30 completion does not mean accounts are connected, content can be published,
background scheduling exists, or the whole cross-platform publishing vision is
complete.
