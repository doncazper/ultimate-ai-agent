# Governed Browser And External Actions — Queue 01

Status: active program; items 01–12 are `implemented_inactive`.
All real external targets remain inactive.

This document records the first ten coherent Queue 01 groups. They implement
exact authority semantics, an isolated injected browser-broker boundary, an
external-action transaction kernel, and a readable Action Inbox execution
envelope, plus registered Evidence Recipes for exact injected observation,
registered same-origin visible-click / GET-form action plans, and registered
exact POST-form schemas, plus a real hash-pinned macOS Keychain opaque-handle
adapter and inactive per-origin session lifecycle, plus registered
human-present MFA, passkey, and CAPTCHA handoff-only contracts without
activating real external targets, plus an app-owned bounded download
quarantine and exact fingerprinted upload-plan boundary, plus exact plan-only
communications, publishing, account-creation, legal-consent, delete, purchase,
booking, checkout/payment, and financial-transaction contracts.
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
| 07. Registered exact POST-form schemas | `implemented_inactive` | A content-derived schema registry binds the exact origin, snapshot, prior observation, source/destination safe URL refs, visible form/proof, bounded safe-ref-only field definitions, encoding, and total byte ceiling. A separate registered recipe binds the exact field-to-opaque-value refs and `form_fill` lease scope, then produces one injected POST-schema plan and content-free receipt through the existing kernel and gateway. | Schema-plan only: the gateway envelope remains internal GET, and no field value is resolved, request body is materialized, browser/session starts, form is filled/submitted, authenticated state is used, network call or external mutation occurs, or real external target is enabled; Queue 02 remains required. |
| 08. Real macOS Keychain opaque-handle adapter and per-origin session lifecycle | `implemented_inactive` | A purpose-specific Security.framework helper stores, probes, and idempotently deletes one exact origin/opaque-handle/generation item in device-only, nonsynchronizing macOS Keychain storage. Python invokes only an owner-controlled absolute helper through a source-hash-sealed, executable-hash-pinned, bounded local subprocess. Registered lifecycle recipes bind exactly one operation-specific authority ref and compose PolicyEngine, LocalApprovalAuthority, exact AuthorityLease, shared budget, readiness/deadline/human-presence/safe-disable/kill-switch checks, at-most-once dispatch, and a safe-ref-only SQLite session record. Duplicate enrollment is rejected, expired preparation is blocked, and a missing credential is a deterministic failed precondition rather than an ambiguous effect. | Keychain enrollment and deletion are local governed operations only. Session state is `prepared_inactive`: no browser session, authentication, cookie use, navigation, live network, external mutation, real external target, route, or UI control is enabled. Queue 02 remains required. |
| 09. Human-present MFA, passkey, and CAPTCHA handoff only | `implemented_inactive` | An immutable registry binds one visible challenge kind, content-derived challenge/schema/handoff refs, exact origin and page snapshot, prior observation, visibility proof, handoff surface, expiry, current human-presence assertion, and exact `prepare` capability. Material-like values hidden inside handoff refs are denied unless the ref is a SHA-256-pinned identifier. The existing transaction kernel rejects implied broader lease capabilities and produces a content-free human-action handoff and receipt only after PolicyEngine, LocalApprovalAuthority, exact AuthorityLease, shared budget, readiness, deadline, safe-disable, and kill-switch validation. Its recipe-bound transaction fingerprint prevents a receipt for one registered recipe from being replayed as another. | Handoff only: UAA does not handle challenge material or responses, operate a passkey, solve or bypass CAPTCHA, open a browser, start a session, authenticate, navigate, use cookies, call a network, complete the challenge, mutate an external target, expose a route/UI handler, or enable a real external target. An external facility and Queue 02 validation remain required. |
| 10. Download quarantine and exact artifact-bound upload plans | `implemented_inactive` | A registered, unexpired recipe binds one exact `download` or `upload` capability, origin, snapshot, artifact, source download transaction, derived quarantine, app-owned store, transfer surface, visibility proof, schema, byte limit, and single operation authority. Upload plans additionally bind the exact content fingerprint, source download receipt, registered source download recipe, and recipe-bound source execution request. Injected download bytes pass the shared transaction gates before bounded owner-only artifact and service-proof writes. Upload planning requires the exact unexpired source receipt, its stored request fingerprint, and the service-owned proof sidecar before re-reading quarantine and verifying its fingerprint. | UAA does not download from a network or browser and does not upload anything. No ordinary path, raw artifact, upload body, browser/session, navigation, authentication/cookies, live network, external mutation, real external target, route, or UI control is enabled. Queue 01 item 13 and Queue 02 remain required. |
| 11. Exact communications, publishing, account creation, legal consent, and delete contracts | `implemented_inactive` | One immutable registry binds each operation to its exact capability, hash-pinned target, schema, input-artifact set, single operation-authority ref, page snapshot, expiry, reversibility, rollback, and reconciliation refs. Legal consent additionally requires one exact legal instrument and explicit accept or decline; account creation cannot imply legal consent. Delete additionally requires the exact deletion target. The shared kernel produces only a content-free plan-only contract and receipt after PolicyEngine, LocalApprovalAuthority, exact AuthorityLease, budget, readiness, deadline, human-presence, safe-disable, and kill-switch checks. | Contract preparation is not execution. UAA does not send, does not publish, does not create an account, does not record legal consent, and does not delete. Payload materialization, browser/session activity, live network, external mutation, real external targets, runtime routes, and UI controls remain disabled. A separate exact execution promotion plus Queue 02 validation is required. |
| 12. Exact purchases/bookings, checkout/payment, and financial-transaction contracts | `implemented_inactive` | One immutable registry binds each operation to its exact `purchase` or `purchase_under_budget` capability, counterparty target, quote, currency, opaque payment-handle ref, positive amount, exact spend ceiling, input artifacts, operation-specific booking/checkout/instrument and cancellation/refund policy refs, snapshot, expiry, reversibility, rollback, and reconciliation. The shared kernel produces only a content-free plan after PolicyEngine, LocalApprovalAuthority, exact AuthorityLease, budget, readiness, deadline, human-presence, safe-disable, and kill-switch checks. | Contract preparation is not financial execution. UAA does not resolve payment data, does not purchase, does not book, does not open checkout, does not pay, and does not transfer funds. Browser/session activity, live network, external mutation, real external targets, runtime routes, and UI controls remain disabled. A separate exact monetary-budget revalidation and execution promotion plus Queue 02 validation is required. |

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

## Registered Exact POST-Form Schemas

`GovernedPostFormSchema` is a content-derived, immutable registry entry. It
contains no raw field name, default value, or form content. The schema binds
the exact authority origin, page snapshot, prior untrusted observation,
source/destination safe URL refs, visible form element and proof, up to five
safe `form-field-ref:` definitions, per-field encoded-byte ceilings, one total
byte ceiling, the exact `POST` method, and the
`application/x-www-form-urlencoded` encoding. Cross-origin destinations,
duplicate fields, unknown encodings, multipart content, and unregistered
schema refs fail closed. Five is the maximum fully populated field count that
fits the authority binding's sixteen-resource ceiling after the five fixed
observation, URL, element, and visibility-proof resources are bound.

`GovernedPostFormRecipe` is registered separately and binds that schema to one
exact external-action authority binding and an exact field-to-opaque-value map.
Required fields must be present, optional fields may be omitted, and unknown or
duplicate fields and values are rejected. Every schema field, opaque
`form-field-value-ref:`, prior observation, safe URL, visible element, and
visibility proof must already be an exact resource in the AuthorityLease-bound
request. The binding must carry the exact schema ref, current snapshot,
same-origin ref, local-validation target, and `form_fill` capability. Generic
`execute`, `admin`, or `destructive` authority cannot substitute.

`ExactPostFormService` uses the existing transaction kernel and injected
`browser_action_dry_run` gateway:

```text
prepare → PolicyEngine → LocalApprovalAuthority → exact AuthorityLease
→ budget reserve → readiness/deadline/safe-disable/kill-switch revalidate
→ WebAccessGateway → isolated injected schema planner → verify → budget settle
```

The gateway request itself remains an internal GET dry-run envelope. `POST` is
only the registered method in the returned safe-ref-only plan. The planner must
prove schema registration, exact field binding, visible target, and same
origin while declaring field resolution, body materialization, browser/session
startup, navigation, form fill/submission, authenticated state, cookies,
download/upload, live network, and external mutation false. Content-bearing or
unknown transport output is blocked before it can enter evidence.

The plan remains separate from the content-free receipt. Replay does not invoke
the planner and returns no field/value mapping. Settlement uncertainty
suppresses the plan and remains non-retryable. This is a registered exact POST
schema and injected plan only: no request body, browser engine, route, UI
control, network transport, authenticated session, external effect, or real
external target is enabled.

## Real macOS Keychain Opaque Handles And Inactive Origin Sessions

`MacOSGovernedBrowserKeychainAdapter` is a purpose-specific local credential
boundary. It accepts one registered origin ref, opaque credential-handle ref,
credential-generation ref, and their derived Keychain item ref. Enrollment
accepts credential material only as a bounded mutable buffer, zeroes that
buffer after the helper call, and never returns material. Immutable buffers
are rejected before dispatch. Probe requests only Keychain attributes.
Duplicate store is rejected and requires a fresh credential-generation ref;
delete is idempotent. Receipts contain safe refs and explicit false posture
flags, never credential data.

The native helper uses `Security.framework` generic-password storage with
`kSecAttrAccessibleWhenUnlockedThisDeviceOnly` and synchronization disabled.
It supports only `version`, `store`, `probe`, and `delete`. It cannot open a
browser, authenticate a site, use cookies, navigate, make a network call, or
grant execution authority. Runtime invocation requires an absolute
owner-controlled regular executable, an exact operator-supplied SHA-256
fingerprint, a descriptor-to-private-temporary copy with a second fingerprint
check, fixed environment, bounded input/output, timeout, `shell=False`, and no
automatic retry. The installer builds from the repository Swift package and
writes only content-free hash metadata into the fixed private helper root.

`GovernedBrowserOriginSessionRecipeRegistry` accepts only exact registered
local-validation operations for enrollment, preparation, revalidation, close,
and revocation. Every recipe binds its action request, exactly one
operation-specific authority ref, registration, origin, page snapshot,
credential handle and generation, Keychain item, session and session
generation, creation/expiry window, and exact `execute` capability. A binding
with no operation ref, the wrong operation ref, or more than one lifecycle
operation ref is denied before approval or Keychain access.
The operation still travels through the existing external-action transaction
kernel:

```text
prepare → PolicyEngine → LocalApprovalAuthority → exact AuthorityLease
→ budget reserve → readiness/deadline/human-presence/safe-disable/kill-switch
  revalidate → Keychain/store transition → verify → budget settle
```

The durable session store contains only safe refs, timestamps, posture, and a
derived state receipt. It never stores credential or web content. Preparation
creates `prepared_inactive`, not a live browser session, and refuses a recipe
whose session window has already expired. Revalidation can mark the record
expired and reports that transition as failed rather than successful; close
and revoke are exact terminal transitions. A deterministic missing-credential
probe, duplicate store, locked Keychain, untrusted helper, or other proven
non-mutating local precondition is recorded as failed without retry, while
uncertain helper failures after the durable start claim remain
`outcome_ambiguous`. Mutable credential buffers are zeroized even when adapter
or lifecycle-request validation fails. Native helper input is read
incrementally with a hard 16 KiB cap, helper file stat/open failures map to
the existing untrusted precondition, and every Keychain query explicitly
disables authentication UI. Replay does not call Keychain again or return a
state projection.

This item is a real local macOS Keychain adapter, not real browser
authentication. There is no browser session, authentication, passkey/MFA
flow, cookie jar, browser engine, navigation, network transport, external
target, route, Control Center control, or standing authority.

## Human-Present Challenge Handoff Only

`GovernedHumanChallengeHandoffRecipeRegistry` accepts immutable recipes for
exactly three challenge classes: MFA, passkey, and CAPTCHA. A recipe binds the
exact authority binding, origin, current page snapshot, prior untrusted
observation, visible-challenge proof, human-presence ref, handoff-surface ref,
content-derived challenge/schema/handoff refs, a window of at most ten minutes,
and the exact `prepare` capability. The challenge schema ref is the binding's
field schema, and every challenge, observation, visibility, surface, and
handoff ref must already be in the exact AuthorityLease resource scope.
Material-like values hidden inside those refs are denied unless the identifier
is SHA-256-pinned. The lease must contain only the exact browser `prepare`
capability; a broader capability that merely implies `prepare` is rejected.
Unknown recipes, absent human presence, stale handoffs, scope drift, and real
external targets fail closed.

`ExactGovernedHumanChallengeHandoffService` uses the existing transaction
kernel:

```text
prepare → PolicyEngine → LocalApprovalAuthority → exact AuthorityLease
→ budget reserve → readiness/deadline/human-presence/safe-disable/kill-switch
  revalidate → prepare content-free human handoff → verify → budget settle
```

A successful result states only the safe refs, challenge kind, required human
action, expiry, and explicit false posture. The human must complete the
challenge on an external facility. The service does not handle challenge
material or a challenge response, invoke a passkey, solve or bypass CAPTCHA,
open a browser, start or use an authenticated session, navigate, use cookies,
make a network call, or perform an external mutation. The transaction is
at-most-once; a replay returns only a content-free replay receipt and no
handoff projection. A call before the recipe window is a non-mutating
preflight block unless the exact transaction already has a terminal receipt.
The transaction fingerprint includes the selected registered recipe, so a
receipt created for one recipe cannot be replayed as a different recipe.
Handoff receipt refs are recomputed from the complete safe-ref-only payload,
and a registered handoff window cannot outlive the bound start deadline.
Uncertain post-start state remains non-retryable.

No raw MFA value, passkey challenge, WebAuthn payload, CAPTCHA site key,
CAPTCHA response, credential material, URL, page content, or provider payload
is accepted or stored. This group adds no route, Control Center control,
browser adapter, provider SDK, external facility integration, real target, or
standing authority.

## Download Quarantine And Artifact-Bound Upload Plans

`GovernedArtifactTransferRecipeRegistry` accepts only immutable exact
`download_quarantine` and `upload_quarantined_artifact_plan` recipes. Each
recipe binds its authority binding, operation-specific authority ref, origin,
page snapshot, one SHA-256-pinned artifact ref, one quarantine ref, the
source download transaction from which that quarantine ref must be recomputed,
the app-owned quarantine-store ref, transfer schema and visible surface refs, a
maximum byte count, a window of at most ten minutes, and exactly one
`download` or `upload` browser capability. An upload recipe additionally binds
the content fingerprint of the already-quarantined artifact, the exact
content-free terminal source download receipt, the registered source download
recipe, and a distinct prior download transaction rather than its own upload
transaction. Both source proof refs are part of the schema and exact authority
resource set. A generic, administrative, destructive, implied-broader, or
identifier-only approval cannot substitute for the exact lease and approval.
Execution also requires exactly one matching artifact-transfer operation
authority ref; a persisted recipe and lease carrying an additional operation
authority fail closed.

`ExactGovernedArtifactTransferService` reuses the shared transaction kernel:

```text
prepare → PolicyEngine → LocalApprovalAuthority → exact AuthorityLease
→ budget reserve → readiness/deadline/human-presence/safe-disable/kill-switch
  revalidate → quarantine write or fingerprinted plan → verify → budget settle
```

The implemented download effect exists only for injected local-validation
bytes. After all shared gates, it validates a declared bounded media type and
size, scans the entire bounded text payload for active content, rejects empty,
mismatched, oversized, or active text payloads, and writes the exact validated
immutable snapshot once to an app-owned quarantine using an owner-only
directory, a derived filename, `O_EXCL`, `O_NOFOLLOW` where supported, and
`0600` file permissions. A concurrent mutation of the caller's buffer cannot
change the bytes written after validation. Oversized input is rejected before
an immutable snapshot is allocated. Directory or file substitution fails
closed. The transient mutable input is zeroized in bounded chunks after every result. The
raw bytes exist only in this purpose-specific quarantine; no ordinary user path
or raw artifact is returned or written into the transaction ledger, receipt,
evidence, docs, or logs. Quarantined content is explicitly untrusted and is not
opened or promoted to authority.

The upload operation is plan-only. It accepts no upload body. It first performs
a bounded read-only inspection of the exact quarantine entry, then requires the
exact bound source download receipt to remain present in a governed transaction
ledger and the bound source recipe to remain present and unexpired in a
registered recipe set. It also requires the exact source transfer request and
verifies the ledger row against the recipe-bound kernel request fingerprint and
idempotency key; a generic kernel caller using the same binding cannot
substitute. It verifies that the recipe is exactly
`download_quarantine`, matches the artifact, origin, quarantine, store, media,
size, source transaction, and receipt binding, and that the receipt has a
stable proof ref, successful terminal state, complete shared-kernel proof, and
exact artifact, quarantine, fingerprint, and fully recomputed hash-pinned
quarantine-projection evidence. The download service also writes a bounded,
owner-only, no-follow content-free proof sidecar beside quarantine and binds
that exact proof ref into the source kernel receipt. Upload requires the
self-hashed sidecar to match the recomputed source projection. A generic
successful external-action receipt—even with the exact recipe-bound request
fingerprint and recomputed deterministic evidence—a pre-seeded file, or a
surviving quarantine without the service-owned proof produces no plan. The
inspection reads only the exact authority-bound quarantine entry. The stored
regular file must remain owner-only, bounded, content-valid, and equal to the
recipe's content fingerprint. Missing, substituted, oversized, invalid, or
drifted content produces no plan. A successful projection contains safe refs,
byte count, media type, expiry, and explicit false posture for body
materialization, browser, network, upload, real target, and external mutation.
The success result contract rejects a quarantine or upload-plan projection
unless its recipe, artifact, quarantine, and source download transaction
exactly match the content-free receipt. Ready receipts require the complete
non-replayed shared-kernel approval, authority, reservation, settlement, and
external-receipt proof refs. Their exact evidence list binds the artifact,
quarantine, content fingerprint, source download receipt and recipe for upload
plans, and the hash-pinned quarantine projection or upload plan, so altered
byte counts, fingerprints, snapshots, transfer surfaces, or source provenance
cannot be paired with an earlier receipt.

The transaction fingerprint includes the registered recipe. A content-free
terminal replay is resolved from the ledger before any transient download
payload requirement, so callers can retrieve the terminal receipt without
retaining or fabricating bytes. Replay does not read or write quarantine again.
Upload-body denial is evaluated before replay, so raw bytes can never accompany
an upload-plan request. Successful replays use `replayed_content_free`; blocked,
failed, or ambiguous terminal replays preserve their original transfer status.
An expired current recipe is rejected during non-mutating preflight before the
kernel claims its transaction, so a later refreshed recipe for the same
transaction is not poisoned by a stale fingerprint. Upload planning also
rejects a source download recipe once its quarantine lifetime has expired.
An exception, non-datetime value, or naive datetime from the injected service
clock returns a content-free blocked receipt before dispatch; an invalid
service clock cannot raise through the governed result boundary. Post-start
storage uncertainty remains `outcome_ambiguous` and is not automatically
retried. This item does not download from a browser or network and does not
upload anything. It adds no browser engine, authenticated session, navigation,
cookies, network transport, external target, API route, Control Center control,
or standing authority.

## Exact High-Consequence Contracts Remain Plan-Only

`ExactGovernedExternalOperationService` prepares registered contracts for
exactly five operation kinds: communication send, artifact publication,
account creation, legal-consent recording, and resource deletion. The
operation-to-capability mapping is exact: communications and publishing require
`send`, account creation requires `write`, legal consent requires `mutate`, and
delete requires `destructive`. The shared kernel also requires the lease to
contain that one capability and the exact complete resource set; another
operation-authority ref or unrelated resource fails closed.

Targets, input manifests, schemas, operation authority, contract, rollback,
reconciliation, legal instrument, and deletion target are content-free
hash-pinned refs. A legal-consent contract cannot exist without an explicit
instrument plus explicit accept or decline decision. Account creation carries
neither field and therefore cannot imply legal consent. A delete contract must
name the exact deletion target and explicit reversibility posture.

The successful projection says `separate_exact_execution_required` and records
false for payload materialization, browser opening, network calls,
communication sent, artifact published, account created, legal consent
recorded, resource deleted, external mutation, and real external target.
Successful replay is content-free and returns no projection. Blocked, failed,
and ambiguous terminal replays retain their original status. Expired recipes
are rejected during non-mutating preflight unless the exact transaction already
has an orphaned started state, which is durably closed as `outcome_ambiguous`.
Idempotency drift returns a content-free blocked receipt instead of escaping as
an exception. This lane does not send, does not publish, does not create an
account, does not record legal consent, and does not delete. It adds no runtime
route or Control Center control. Queue 02 and a separate exact execution
contract remain required before any external effect.

## Exact Financial Contracts Remain Plan-Only

`ExactGovernedFinancialService` prepares registered contracts for exactly four
operation kinds: purchase, booking, checkout/payment, and financial
transaction. Each scope binds one hash-pinned counterparty target, quote,
currency, opaque payment-handle ref, positive amount, exact spend ceiling,
artifact set, operation-specific refs and policy posture, conservative
reversibility, rollback, reconciliation, and expiry. An amount above its exact
spend ceiling fails before any transaction is prepared.

Purchase and checkout/payment require exact `purchase` authority. Booking and
financial transaction require exact `purchase_under_budget` authority. The
shared kernel still requires the lease to contain that one browser capability
and the complete exact resource set. Approval identifiers alone grant nothing.
The payment handle is an opaque hash-pinned identifier only; raw card, bank,
credential, account, or payment data is neither accepted nor recorded.

The successful projection requires a separate financial execution and monetary
budget revalidation. It records false for payment-handle resolution, checkout
opening, purchase, booking, payment, financial transaction, network call,
external mutation, and real external target. Idempotency drift returns a
content-free blocked receipt. An orphaned prior start is preserved as
`outcome_ambiguous`, including after recipe expiry, and ambiguous outcomes are
never retried automatically. This lane does not purchase, does not book, does
not open checkout, does not pay, and does not transfer funds. It adds no
runtime route or Control Center control. Queue 02 and a separate exact
financial execution contract remain required before any monetary effect.

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
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group05.py
.venv/bin/python scripts/verify_governed_browser_queue01_group05.py
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_keychain_adapter.py \
  tests/test_governed_browser_queue01_group06.py \
  tests/test_verify_all_self_scan_hygiene.py
.venv/bin/python scripts/verify_governed_browser_queue01_group06.py
/usr/bin/swift build \
  --package-path tools/macos/governed-browser-keychain-helper \
  -c release
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group07.py
.venv/bin/python scripts/verify_governed_browser_queue01_group07.py
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group08.py \
  tests/test_governed_browser_queue01_group08_hardening.py \
  tests/test_governed_browser_queue01_group08_review_repairs.py \
  tests/test_governed_browser_queue01_group08_review_round05.py
.venv/bin/python scripts/verify_governed_browser_queue01_group08.py
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group09.py
.venv/bin/python scripts/verify_governed_browser_queue01_group09.py
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_governed_browser_queue01_group10.py \
  tests/test_governed_browser_queue01_group10_hardening.py
.venv/bin/python scripts/verify_governed_browser_queue01_group10.py
```

Queue 01 item 13 remains pending and must be implemented in its manifest
order. Queue 02 remains the separate adversarial hardening gate; no status in
this document satisfies or bypasses that gate.
