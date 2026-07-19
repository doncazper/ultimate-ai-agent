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
  durable start, after the start claim, and after dispatch;
- allowed budget reservation, release, and settlement records require exact
  receipt proof; pre-start blocks retain the release proof, and missing
  settlement proof becomes `outcome_ambiguous`;
- dispatch has one nonblocking capacity slot and a maximum thirty-second
  deadline; exceptions, invalid results, deadline overruns, or capacity
  exhaustion are content-free, request-bound, ambiguous, and never
  automatically retried, and no terminal receipt is written while a detached
  callback remains live;
- terminal writes use SQLite compare-and-swap from the exact expected state,
  so a concurrent or stale writer cannot overwrite a receipt;
- a competing execution caller no longer terminalizes a start owned by another
  caller; explicit restart recovery may settle an orphan as ambiguous only
  after the bounded dispatch window and a five-second settlement grace;
- durable and returned external-action receipts recompute their own exact
  content-derived identity when read or deserialized;
- idempotency identifiers must be SHA-256-pinned safe refs; and
- the kernel reconstructs a validated internal request snapshot before any
  durable prepare, severing caller-owned mutable aliases and rejecting drift.

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
| timeout after dispatch | Bounded dispatch returns non-retryable `outcome_ambiguous`. |
| crash, replay, interruption, restart, and settlement recovery | Fresh starts cannot be recovered while an owner may still be live; after the dispatch-plus-settlement grace, orphan recovery, terminal replay, CAS writes, and mandatory settlement proof preserve ambiguity truth without redispatch. |
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
| cross-lane non-interference | Exact transaction, operation, schema, resource, artifact, and evidence refs prevent cross-lane reuse. |
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
