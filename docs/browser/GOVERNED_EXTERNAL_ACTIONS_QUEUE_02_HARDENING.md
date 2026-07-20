# Governed Browser And External Actions — Queue 02 Hardening

Status: complete source hardening gate; every Queue 01 lane remains
`implemented_inactive`. No lane was activated.

Queue 02 adversarially hardens the thirteen existing Queue 01 lanes without
adding a capability category, runtime route, browser engine, provider adapter,
live network transport, external mutation, or standing authority. Its new
activation decision is an immutable evidence read model. Even complete
evidence can produce only `eligible_for_separate_activation_review`; it cannot
enable a lane.

## Shared Kernel Repairs

The audit found and fixed defects in the shared boundary rather than masking
them in individual lane services:

- readiness now binds its own content-derived ref plus the exact observed
  origin, recipient, schema, transaction, artifacts, resources, page snapshot,
  and content-free hostile-state signals;
- exact approval, AuthorityLease, and readiness are revalidated before the
  durable start, after the start claim, and after dispatch; the existing
  approval-authority lock serializes the final validation and bounded dispatch
  handoff against concurrent revocation; normal completion retains the lock
  through final validation, while a timed-out worker reacquires it after the
  callback stops, and the latest decision proof is retained in the terminal
  receipt;
- allowed budget reservation, release, and settlement records require exact
  receipt proof, including on ledger replay where the original semantic status
  remains authoritative and a replayed denial cannot become an allow;
  pre-start blocks retain the release proof, and missing
  settlement proof becomes `outcome_ambiguous`; shared-capacity denial occurs
  before budget reservation, while any post-start guard that proves dispatch
  was never invoked releases unused budget and restart recovery reconciles an
  exact prior release before it
  attempts ambiguous settlement of the persisted reservation; a lost start
  claim releases only a distinct losing reservation and
  never releases the idempotent reservation still owned by the winning start;
  a pre-claim denial first owns the durable close transition before releasing,
  and a losing caller returns its own verified release proof even when the
  winner has already terminalized;
- dispatch has one SQLite-backed nonblocking capacity slot plus a process-held
  OS file lock shared by every kernel instance using the transaction store. The
  exact slot is claimed before budget reservation and the durable start, so it
  covers pre-dispatch revalidation and prevents restart recovery from stealing
  a live start. Dispatch has a maximum thirty-second deadline; the caller
  returns at that deadline even
  when an arbitrary callback remains live, but the detached worker retains the
  sole durable/process slot through callback completion, budget settlement, and
  terminal close. A worker that has not begun dispatch by the caller deadline
  is cancelled before invocation; the caller durably releases the unused
  reservation and closes the slot before returning, so delayed worker progress
  is not required for cleanup and it cannot start the callback after reporting
  timeout. The worker also rechecks deadline and readiness authority immediately
  before dispatch. Exceptions, invalid results,
  deadline overruns, or capacity
  exhaustion are content-free, request-bound, ambiguous, and never
  automatically retried, and no terminal receipt is written while a detached
  callback remains live; a lock-protocol-marked stale SQLite slot is reaped
  only after the OS lock proves the prior process no longer owns dispatch,
  while an unproven legacy row remains fail closed;
- terminal writes use SQLite compare-and-swap from the exact expected state,
  so a concurrent or stale writer cannot overwrite a receipt; a caller that
  loses a pre-start finish transition re-reads durable terminal/state truth and
  returns a content-free ambiguity proof instead of raising through the
  operator boundary;
- a competing execution caller no longer terminalizes a start owned by another
  caller; every normal kernel execution attempts safe restart recovery before
  returning a start conflict, so all wrapper services share the same recovery
  path without redispatch; recovery may settle an orphan as ambiguous only
  after the maximum dispatch window and a five-second settlement grace, never
  a shorter recoverer-selected timeout, and never while the exact durable
  dispatch slot remains owned; if the budget ledger already contains the exact
  settlement from a crash between settlement and transaction close, recovery
  reuses that durable proof instead of conflicting or losing accounting truth;
  if a no-dispatch guard already durably released the reservation before a
  crash, recovery retains that exact release proof and does not falsely settle
  the released reservation;
- durable and returned external-action receipts recompute their own exact
  content-derived identity when read or deserialized, and bounded hostile reason
  sets keep terminal budget accounting failures explicit alongside an overflow
  proof;
- replay projections no longer treat recomputable receipt hashes as durable
  provenance. A package-internal typed validation context is issued only after
  the concrete kernel and its construction-bound concrete transaction store
  atomically read one durable row from the store's construction-bound path and
  prove its exact recipe-bound request fingerprint, terminal state,
  transaction/intent/binding, non-replayed receipt payload, and recomputed
  receipt ref. Mutable instance connector, lock, path, store, and serializer
  substitutions cannot redirect or rewrite that proof source. The context keeps
  immutable canonical snapshots rather than caller-owned model aliases. Each
  wrapper compares the complete projected
  kernel receipt to that durable terminal receipt, allowing only the
  presentation replay bit to differ. It then validates one
  lane/operation-specific ordered evidence envelope. Blocked envelopes are
  empty; failed and succeeded envelopes match the exact lane grammar.
  Ambiguous envelopes must also prove their ambiguity path: every deterministic
  kernel proof is recomputed and bound to its exact primary reason, post-start
  guard proofs commit to the final ordered and bounded terminal reasons, and
  lane evidence requires an exact settlement, post-dispatch revalidation, or
  explicitly classified operation-specific ambiguity transition. Prepared and
  started rows are never accepted as terminal proof. Missing or mutated
  context, reordered or resized evidence, state-only substitution, and
  accounting-proof disagreement all fail closed. Cross-operation, cross-recipe, and
  cross-transaction substitution all fail closed even when every
  content-derived wrapper hash is
  recomputed. Artifact envelopes also bind the wrapper projection to the exact
  artifact, quarantine, source transaction, and origin scope. Download evidence
  binds artifact, quarantine, fingerprint, quarantine projection, and service
  proof; upload-plan evidence additionally binds the exact source download
  receipt/recipe and upload-plan ref;
- dynamic observation, action-plan, POST-form-plan, and origin-session evidence
  is also backed by an independent content-free operation proof written before
  the lane dispatch result returns. Its ref is the final ordered evidence
  element and binds the construction-time proof store, lane, operation and
  scope, exact request fingerprint, transaction, intent, authority binding,
  dispatch outcome, complete base evidence, and typed safe-ref-only material.
  The immutable proof store is owner-only, bounded, no-follow, and
  construction-bound to its root and proof-directory identities. Each service
  is bound to its exact kernel, registry, gateway or Keychain/session
  dependencies, and proof store. Replay independently attests both the
  operation proof and exact terminal kernel row. A distinct immutable
  terminal-binding record is minted immediately after, and only after, the
  fresh durable terminal commit is exactly re-attested. It binds the request
  fingerprint and complete canonical non-replayed receipt, including state,
  ordered evidence, reasons, approval/authority refs, budget reservation,
  release or settlement, and the optional operation-proof ref. Idempotent
  finish, replay, conflict, legacy, and crash-incomplete rows never synthesize
  or backfill that record. Every replay context, including proof-less
  deterministic kernel ambiguity, requires the exact binding and includes its
  ref in the authenticated envelope. A missing, mutated, reordered, foreign,
  or legacy proof or terminal binding fails closed; replay never reconstructs
  one by calling the gateway, planner, helper, or Keychain. These local content
  hashes provide structural provenance only: they are not signatures,
  external timestamps, non-repudiation, or execution authority. Coordinated
  owner-level rewriting of both the transaction ledger and immutable proof
  store remains an explicit residual threat. No raw content, credential
  material, profile path, cookie, or new browser/network authority is
  persisted or granted;
- external-operation contract receipts recompute the referenced kernel receipt
  from their copied transaction, state, proof, evidence, and original kernel
  reason fields, even when the operator-facing contract adds a scoped failure
  reason;
- every operator-facing lane receipt retains the kernel budget release proof,
  including action, observation, POST form, origin-session, human-handoff,
  artifact-transfer, external-operation, financial, and task-composition
  projections; browser-action and POST-form wrapper identities recompute over
  that release proof so substitution is rejected during validation, and each
  result wrapper accepts only its own lane-specific receipt prefix;
- idempotency identifiers must be SHA-256-pinned safe refs; and
- authority-binding artifact and resource scopes are immutable tuples, and the
  kernel reconstructs a validated internal request snapshot before any durable
  prepare, so provider callbacks cannot mutate nested scope after fingerprint or
  budget proof creation.

## Complete Adversarial Campaign

The focused Queue 02 campaign and the retained Queue 01 suites cover the exact
required classes below. All fixtures are local, injected, safe-ref-only, and
content-free; this evidence does not stand in for a live external facility.

| Required campaign class | Evidence posture |
|---|---|
| authority and capability confusion | Exact capability/lease tests retain admin/destructive non-expansion, exact resource scope, and cross-family denial. |
| changed, expired, revoked, missing, and mismatched approvals or leases | Initial and repeated approval/lease validation covers absent, stale, revoked, changed, and mismatched scope. |
| cross-origin redirects | A trusted hostile-state signal blocks before dispatch. |
| DOM swaps | Snapshot and explicit DOM-swap signals block before dispatch. |
| hidden fields | The hostile-state signal and exact form schema prevent silent fields. |
| changed form actions | Exact same-origin action/schema refs and the hostile-state signal block drift. |
| misleading controls | Visibility proof plus the hostile-state signal fail closed. |
| unexpected pop-ups and downloads | Separate popup and download signals block dispatch. |
| page mutation between approval and dispatch | Repeated readiness checks bind the exact snapshot and mutation signal. |
| duplicate submission | One action, durable start ownership, idempotency, and duplicate-submit signals prevent retry. |
| timeout after dispatch | Bounded dispatch returns non-retryable `outcome_ambiguous` at the deadline, retains sole ownership while the callback is live, and closes durably only after it stops. |
| crash, replay, interruption, restart, and settlement recovery | Fresh starts cannot be recovered while an owner may still be live; ownership spans settlement and terminal close, while orphan recovery, terminal replay, prior release/settlement reconciliation, CAS writes, mandatory accounting proof, exact durable-terminal provenance, and typed ordered evidence envelopes preserve ambiguity truth without redispatch. |
| concurrent execution | Only the durable start owner dispatches; contenders cannot terminalize or clobber it. |
| kill-switch races | Revalidation after start changes the result to ambiguous without retry. |
| safe-disable races | Revalidation after start changes the result to ambiguous without retry. |
| secret and credential canaries | Content-free hashed signal reasons block and no material enters a receipt. |
| prompt-injection-shaped page content | Untrusted instruction-shaped content is a blocking signal, never authority. |
| raw-content and path leakage | Separate leak signals block; receipts retain only bounded safe refs. |
| session fixation and origin confusion | Exact session/origin bindings plus both hostile signals fail closed. |
| upload artifact substitution | Exact source receipt, recipe, quarantine proof, and content fingerprint remain mandatory. |
| download filename/type/signature attacks | Separate filename, media-type, and signature signals block transfer preparation. |
| recipient/content/amount/total substitution | Every observed/requested dimension is exact and independently revalidated. |
| payment, publishing, account, consent, deletion, and transfer retry denial | All operation contracts remain plan-only, at-most-once, and `automatic_retry_allowed=false`. |
| resource exhaustion and bounded cleanup | Dispatch capacity is one, hostile resource count is bounded to four, and unverified cleanup blocks. |
| cross-lane non-interference | Recipe-bound kernel fingerprints plus exact transaction, operation, schema, resource, artifact, durable receipt, and ordered evidence-envelope refs prevent cross-lane reuse. |
| full macOS packaged golden journeys | A clean packaged checkpoint install must pass CLI, API manifest, Control Center, and helper smoke without enabling a live target; it remains distinct from live external evidence. |

## Activation Matrix

Each decision is separate. A neighboring lane cannot promote another lane,
and no decision value means active. The matrix is intentionally conservative:
`blocked_pending_live_evidence` is available only after adapter, configuration,
facility, and target readiness are present but one or more proof gates remain;
no current lane has reached that posture.

| Queue 01 lane | Queue 02 posture | Missing evidence |
|---|---|---|
| 01 exact authority binding | `configuration_required` | No external activation configuration exists. |
| 02 isolated browser broker | `adapter_required` | Only the injected observation/planning adapter exists. |
| 03 external-action kernel | `external_facility_required` | No live target/adapter facility exists for external execution evidence. |
| 04 Action Inbox envelope | `configuration_required` | No browser/dispatch handler or activation configuration exists. |
| 05 Evidence Recipes | `external_facility_required` | No live governed browser facility exists. |
| 06 visible click / GET form | `external_facility_required` | No live governed browser facility exists. |
| 07 exact POST form | `external_facility_required` | No live governed browser facility exists. |
| 08 Keychain / origin session | `external_facility_required` | Local Keychain proof is not an authenticated browser facility. |
| 09 human challenge handoff | `external_facility_required` | Handoff-only contracts have no live browser facility. |
| 10 artifact transfer | `external_facility_required` | Quarantine and upload planning have no live transfer facility. |
| 11 external-operation contracts | `external_facility_required` | Plan-only contracts have no execution facility. |
| 12 financial-operation contracts | `external_facility_required` | Plan-only contracts have no monetary execution facility. |
| 13 task composer | `external_facility_required` | Composition is plan-only, cannot inherit step authority, and has no execution facility. |

The evidence model separately requires implementation, focused and adversarial
tests, request-scoped policy, exact approval, AuthorityLease evaluation, target
and adapter readiness, budget posture, kill switch, safe-disable, deadline,
idempotency, receipt, reconciliation, recovery, macOS packaged-golden, external
facility, configuration, and live evidence. Satisfying every field still only
allows a later separately scoped activation review.

## Verification

Focused source checks:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue02_hardening.py \
  tests/test_governed_browser_queue01_group*.py
PYTHONPATH=src .venv/bin/python \
  scripts/verify_governed_browser_queue02_hardening.py
```

The complete repository closeout also runs documentation integrity, static
safety, security/redaction, OpenAPI, route classification, API manifest,
CLI/UI parity, frontend, hostile-site, product-truth, Ruff, diff, Foundation
Gate, exact-head CI/review, and clean packaged macOS smoke. Skipped or blocked
checks must remain explicit evidence gaps; they cannot be converted into an
activation claim.

Queue 02 grants no broad browser, admin, destructive, provider, network,
payment, connector, shell, or production authority. Historical checkpoint tags
remain immutable.
