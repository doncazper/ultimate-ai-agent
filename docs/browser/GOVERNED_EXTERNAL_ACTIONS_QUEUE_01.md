# Governed Browser And External Actions — Queue 01

Status: active program; items 01–06 are `implemented_inactive`.

This document records the first four coherent Queue 01 groups. They implement
exact authority semantics, an isolated injected browser-broker boundary, an
external-action transaction kernel, and a readable Action Inbox execution
envelope, plus registered Evidence Recipes for exact injected observation,
and registered same-origin visible-click / GET-form action plans without
activating real external targets.
It grants no standing browser authority, unrestricted browsing, provider SDK
call, live network fetch, click, form submission, authenticated session,
download, upload, purchase, publishing action, or production authority.

## Terminal Classification

| Queue 01 item | Classification | Current evidence | Still blocked |
|---|---|---|---|
| 01. Exact authority semantics | `implemented_inactive` | Exact origin, recipient, field schema, transaction, artifact, resource, action-count, page-snapshot, start-deadline, and human-presence binding; `admin` and `destructive` no longer imply unrelated capabilities. | Real external execution and standing grants. |
| 02. Isolated browser broker | `implemented_inactive` | Injected observation adapter behind `WebAccessGateway`, bounded concurrency, exact origin refs, ephemeral private profile directories, ordinary-profile denial, hostile-content quarantine, and external mutation disabled. | Browser engine, navigation, real network, ordinary user profiles, clicks, forms, auth/cookies, downloads/uploads, and external mutation. |
| 03. External-action transaction kernel | `implemented_inactive` | Durable safe-ref intent precedes effects; exact policy, LocalApprovalAuthority, AuthorityLease, budget reservation, readiness, page snapshot, deadline, human-presence, safe-disable, and kill-switch checks precede one dispatch; verify and settlement produce a content-free receipt. | Real external targets and adversarial cross-lane validation required by Queue 02. |
| 04. Action Inbox execution envelope | `implemented_inactive` | Backend-owned content-free projection exposes readable exact scope, side-effect and data-classification posture, expiry, reversibility, retry truth, approval fingerprint, expected/observed receipts, reconciliation state, and manual-only Open in browser / Human takeover controls. | No UI handler, browser launch, approval validation, dispatch, real external target, or automatic retry; Queue 02 remains required. |
| 05. Evidence Recipes and exact browser observation | `implemented_inactive` | A registered Evidence Recipe binds the exact authority binding, origin, page snapshot, schema, target, safe URL ref, capture fields, and size limits. The service composes the existing transaction kernel, WebAccessGateway, and isolated broker to return one bounded redacted evidence projection plus a separate content-free receipt during injected local validation. | No browser engine, live navigation/network, arbitrary recipe, raw DOM/screenshot, authenticated profile, browser action, external mutation, or real external target; Queue 02 remains required. |
| 06. Same-origin visible clicks and GET forms | `implemented_inactive` | A registered action recipe binds the exact `click` or `form_fill` lease capability, prior observation, page snapshot, source/destination safe URL refs, same origin, visible element/proof, field schema, and opaque GET-form value refs. The existing kernel and WebAccessGateway produce one injected action plan plus a separate content-free receipt. | Plan-only: no browser session, navigation, click, form fill/submission, request body, network call, authenticated profile, external mutation, or real external target; Queue 02 remains required. |

## Exact Authority Is Not A Superuser Hierarchy

`AuthorityCapability.admin` and `AuthorityCapability.destructive` are exact
capability classes. They no longer expand to every unrelated capability. A
browser-admin lease cannot authorize click, form-fill, upload, download,
message-send, payment, shell, provider, or other action merely because its
label sounds powerful.

Every external-action binding is one immutable scope containing:

- one normalized HTTPS origin, or loopback HTTP origin for injected local
  validation only;
- one recipient ref and one field-schema ref;
- one transaction ref and exactly one action;
- explicit artifact and resource refs;
- one page-snapshot ref;
- an aware start deadline; and
- one human-presence ref plus current human-present posture.

The approval request also binds the exact lease and inactive adapter ref.
Approval refs remain identifiers only and are freshly validated by
`LocalApprovalAuthority`; a matching identifier without a registered exact
grant authorizes nothing.

## Isolated Broker Boundary

`IsolatedBrowserBrokerAdapter` is an injected `BROWSER_OBSERVE` adapter behind
the existing `WebAccessGateway` policy and audit boundary. It creates a new
temporary private profile directory per call and removes it before returning.
The transport receives no ordinary browser-profile path. Concurrency is
bounded from one to four sessions and rejects work when the bound is occupied.

The Queue 01 adapter is observation-only. It denies a wrong origin ref, an
ordinary-profile request, any mutation request, and any request kind other than
injected observation. Hostile local fixture content remains untrusted data,
cannot become instructions, and is quarantined in the gateway evidence bundle.
No Playwright, Selenium, Browserbase, Firecrawl, browser SDK, provider SDK, or
network transport is added.

## Transaction Order And Crash Truth

The kernel enforces this order:

```text
prepare → authorize → reserve → revalidate → dispatch → verify → settle
```

Preparation writes only the transaction ref, request fingerprint, state, and
content-free receipt JSON to a local SQLite ledger before any dispatch. The
same transaction ref plus a different fingerprint is an idempotency conflict.
The durable `started` claim is single-writer. A dispatch exception or a budget
settlement failure after start becomes `outcome_ambiguous`; it is never
automatically retried. A terminal replay returns the stored content-free
receipt and does not invoke the adapter again.

The default budget adapter denies. The explicit shared-ledger adapter reserves
and settles through `AuthorityBudgetStore`, including exact LocalApprovalAuthority
validation. Revalidation occurs after reservation and immediately before the
durable start claim. A snapshot change, expired deadline, missing human
presence, stale readiness, broker-integrity failure, safe-disable, or kill
switch releases the unused reservation and blocks dispatch.

## Action Inbox Execution Envelope

`ExternalActionInboxExecutionEnvelope` is a backend-owned read model for one
exact `ExternalActionExecutionRequest` and, when present, its matching
content-free receipt. It intentionally omits the raw origin and approval
identifier. The operator sees a bounded readable scope plus safe refs for the
lease, inactive adapter, exact origin, recipient, schema, transaction,
artifacts, resources, page snapshot, and human-presence assertion.

The envelope makes consequences visible before any later exact execution
lane:

- side effects distinguish injected local validation from inactive external
  mutation;
- data classification is `project_private`;
- the aware deadline is rendered as active or expired;
- reversibility remains not applicable for local validation or unknown/manual
  review for a generic external operation;
- the approval fingerprint binds the exact approval identifier, subject,
  resources, risk, classification, and expiry but is never authority;
- expected and observed receipt refs remain content-free;
- success with evidence is reconciled as verified, while failed, started, or
  `outcome_ambiguous` truth requires manual reconciliation and forbids retry;
  and
- current safe-disable, kill-switch, expiry, human-presence, and inactive-target
  blockers remain visible as reason refs.

The `Open in browser` and `Human takeover` controls are typed manual-handoff
records only. They are visible for operator comprehension but have no handler,
never open a browser, never automate a profile, never mutate an external
target, and record `performed=false`. An expired request makes both handoffs
unavailable. Adding a Control Center handler, browser launch, approval capture,
or dispatch route is outside this group.

## Registered Evidence Recipes And Exact Observation

`GovernedBrowserEvidenceRecipe` is an immutable capture contract, not a caller
selected browser instruction. A recipe is accepted only from
`GovernedBrowserEvidenceRecipeRegistry`, and its stable recipe ref covers the
exact transaction binding, origin ref, page-snapshot ref, field-schema ref,
target ref, safe URL ref, fixed capture fields, and bounded preview and visible
text limits. The target and safe URL refs must already be exact resources in
the AuthorityLease-bound action request.

`ExactBrowserObservationService` does not add a parallel authority path. A
successful first observation uses the existing external-action kernel, in this
order:

```text
prepare → PolicyEngine → LocalApprovalAuthority → exact AuthorityLease
→ budget reserve → readiness/deadline/safe-disable/kill-switch revalidate
→ WebAccessGateway → isolated injected broker → verify → budget settle
```

The broker transport must return only the registered fields and exact refs.
Unknown fields, target/snapshot/origin drift, raw DOM, screenshots, secret-like
preview content, authenticated-profile use, navigation, clicks, forms,
downloads/uploads, network calls, or any side effect fail closed. The gateway
returns no raw result from this service. The accepted evidence projection is
bounded, redacted, content-untrusted, instruction-disabled, and tied to an
ephemeral private profile ref.

The durable observation receipt is separate from the bounded evidence
projection and remains content-free. It records only safe refs and the exact
approval-validation, authority-decision, budget reservation/settlement, and
external-action receipt refs. Replaying the same transaction does not call the
broker again and returns only the content-free replay receipt. Ambiguous
outcomes remain non-retryable.

This is injected local validation, not live browser observation. No browser
engine, live URL, provider, network transport, route, Control Center control,
or real external target is enabled.

## Same-Origin Visible Click And GET-Form Plans

`GovernedBrowserActionRecipe` is a registered, immutable plan contract. It is
accepted only from `GovernedBrowserActionRecipeRegistry` and binds one exact
authority binding, `click` or `form_fill` lease capability, prior untrusted
observation ref, current page snapshot, source and destination safe URL refs,
destination origin ref, visible element ref, visibility proof ref, field
schema, and at most sixteen opaque field-value refs. A visible click must have
no field values. A GET form must have at least one structured
`form-field-value-ref:` and cannot contain a raw value or request body.

Same-origin is fail-closed: the destination origin ref must equal the exact
authority-bound origin ref. The prior observation, both safe URLs, element,
visibility proof, and every field-value ref must already be resources in the
exact AuthorityLease-bound request. The shared external-action binding now
carries the exact capability, so generic `execute`, `admin`, or `destructive`
authority cannot substitute for `click` or `form_fill`.

`ExactBrowserActionService` reuses the existing transaction kernel and the
WebAccessGateway `browser_action_dry_run` lane. Its injected action plan follows
the same sequence:

```text
prepare → PolicyEngine → LocalApprovalAuthority → exact AuthorityLease
→ budget reserve → readiness/deadline/safe-disable/kill-switch revalidate
→ WebAccessGateway → isolated injected planner → verify → budget settle
```

The injected planner uses a bounded ephemeral private directory, but starts no
browser session. Its strict result must prove target visibility, same-origin,
exact schema, and GET method while declaring browser session, navigation,
click, form fill/submission, request body, authentication/cookies,
download/upload, network, and external mutation all false. Unknown fields or
posture drift fail content-free.

The plan is safe-ref-only and separate from the content-free receipt. Terminal
replay never invokes the planner again and returns no plan. An uncertain
dispatch or failed settlement becomes `outcome_ambiguous`, suppresses the plan,
and cannot retry automatically. This is an injected action plan, not action
execution: there is no browser session, browser engine, live URL, live network,
route, UI control, or real external target.

## Validation Boundary

The only executable proof in this group is deterministic injected
`local_validation`. The kernel constructor rejects any attempt to enable real
external mutation. An `external` target is blocked before approval, budget, or
dispatch. This local-validation seam exists to prove transaction correctness;
it is not a browser-action or network-authority grant.

Focused verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group01.py \
  tests/test_authority_leases.py \
  tests/test_authority_budgets.py \
  tests/test_web_access_gateway.py
.venv/bin/python scripts/verify_governed_browser_queue01_group01.py
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group02.py
.venv/bin/python scripts/verify_governed_browser_queue01_group02.py
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group03.py
.venv/bin/python scripts/verify_governed_browser_queue01_group03.py
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group04.py
.venv/bin/python scripts/verify_governed_browser_queue01_group04.py
```

Queue 01 items 07–13 remain pending and must be implemented in their manifest
order. Queue 02 remains the separate adversarial hardening gate; no status in
this document satisfies or bypasses that gate.
