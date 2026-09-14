# Q34 News And Source Intelligence Functional Adoption

Status: bounded founder-private implementation candidate; terminal Queue V2
status requires protected merge, green post-merge qualification, disposition,
and isolated-worktree cleanup.

## Adopted product loop

The Control Center `/news` surface now supports an ordinary founder-private
loop over operator-entered, already-redacted source artifacts:

1. register an exact local source and classify its source kind;
2. add a redacted signal with its actual publication time;
3. inspect source, provenance, freshness, confidence, cross-source coverage,
   conflict, rank reasons, and Morning Briefing eligibility;
4. search or page through every active signal, including lower-ranked and
   deduplicated artifacts, and correct a source or signal from the normal UI;
5. set or remove a topic preference;
6. archive and recover a signal, independently safe-disable and recover any
   source, or undo the most recent reviewed change; and
7. consume the bounded ranked refs in Today and Morning Briefing.

The Python Agent Core owns sources, artifacts, clustering, ranking,
preferences, archive state, source state, revisions, undo, and receipts. React
holds presentation state only: active filter, selected item, current form
values, and the one pending confirmation.

## Core, API, CLI, and UI parity

Python-owned state and mutations live in
`src/ultimate_ai_agent/core/news_signals/adoption.py`. The protected API is:

- `GET /control-center/news-signals/adoption`
- `POST /control-center/news-signals/adoption/preview`
- `POST /control-center/news-signals/adoption/approval`
- `POST /control-center/news-signals/adoption/commit`

The read endpoint exposes a bounded active-item page with offset, limit, and a
redaction-safe search query while retaining the deduplicated curated summary.
The read-only `python scripts/inspect_news_signals_adoption.py` command reports
the same safe posture without printing private source or signal text by
default. Inspection failures, including invalid arguments, emit a fixed blocked
JSON result and exit 2 without a traceback, path, or supplied value.
Construction, reads, and previews do not create or migrate News storage.
The workspace and inspection command distinguish `missing`, `q24_only`,
`migration_required`, and `ready` storage from source-readiness status; Today
and Morning Briefing projections carry the same storage posture. Existing Q24
sources and artifacts remain visible without silently adopting their database.
`apps/control-center/src/components/NewsSignalsPreviewPanel.tsx`
provides the normal readable workflow.

Today (including the NorthStar workspace) and Morning Briefing render a
read-only News digest from the same local summary. They preserve the Python
projection's selected refs and ordering, show source, confidence, conflict and
snapshot freshness, and link back to News for inspection. They do not rank or
summarize content in the browser. Explicit refresh reads local state only.
The summary includes at most eight `projection_items`, independently of its
ranked page, so eligible Today and Briefing records remain readable even when
higher-ranked stale records fill that page.
Unavailable backend ownership, failed refresh, or inconsistent projection
identities hide the prior items; missing sources, safe-disabled sources and a
valid empty selection remain distinct. These displays do not bypass the
existing first-loop setup gate or authorize candidate execution.
These entry routes request only their ten existing shell, authority, Today,
Actions, Evidence, Agent Loop and Briefing read dependencies, rather than
waiting on unrelated runtime, memory and integration surfaces. They reuse the
same validators and backend-instance/revision binding. Every previously
required route must still be backend-owned; unrequested routes remain
non-authoritative. These compound local reads run serially within one
eight-second deadline covering queue wait, request and response-body parsing.
Expired reads are aborted and queued requests cannot start after that deadline.
If the bound Today or Briefing read fails, an explicit `Retry local read`
control starts a fresh read through the same hook and current backend binding.
It is shown only after backend truth is admitted, disappears while loading,
and never resubmits an approval or save. Failed content remains hidden until
the existing route ownership and response validation checks pass.
The full-loader concurrency policy and truth gates remain unchanged.
Unapproved Agent Loop items check for an approved receipt before rebuilding
generated action payloads. Approved items still validate their current action
revision and exact unrevoked grant; no cached approval or shared read cache is
introduced.
Action reads admit and order generated sources before projecting only the
returned window; returned items retain all detail and authority checks.
The compound Agent Loop read builds its three distinct Today windows once per
call, preserving their six-, twelve- and fifty-item limits. Evidence, Memory,
Proof and Trust use those repository-owned inputs through the existing
projection builders. Nothing is cached across calls or supplied by the browser;
this read-only assembly is neither an atomic storage snapshot nor authority.
Standalone route contracts and required-read failure behavior remain intact.
The backend vault readiness retains its explicit adapter-not-scoped reason,
and the external-intake description uses bounded safety-compatible wording.
The existing frontend authority and raw-content validators remain unchanged.

The normal `/news` route obtains a current, validated backend truth envelope
and supplies its revision, process identity, and snapshot to the exact approval
and commit requests. First-run local intake does not depend on a prior unrelated
founder-loop completion receipt. Loading, invalid, unavailable, or expired
backend truth hides the intake controls; recovery requires a fresh review, not
automatic resubmission. This binding does not replace PolicyEngine or exact
operator approval and does not claim complete founder-loop evidence.
Workspace reads and previews validate the expected backend identity too. A
backend revision or process change resets the owned workspace, draft and pending
confirmation. Routine truth-snapshot rotation preserves drafts, search and
pagination while invalidating the pending review; a new review uses the fresh
snapshot, and an old approval cannot continue into a commit. Late reads or
previews cannot populate a replacement owner. Signal corrections keep their
original source fixed, including in the source selector.
The complete active-item list exposes topic preference and removal actions,
including signals omitted from the curated or deduplicated stream.
The signal form wraps within the available News viewport, including after the
first source is saved. Browser regressions check each field and review control
against that inner viewport on desktop and narrow layouts.

Every mutation binds the current revision, payload fingerprint, exact preview,
operator confirmation, exact approval, idempotency ref, and an
operation-budget-one `workspace/write` AuthorityLease. Completed commits
return durable exact-replay receipts with rollback refs. Rebound payloads,
stale revisions, substituted previews or approvals, expired approvals, replay
conflicts, malformed state, and unsafe identifiers fail closed.
Malformed or unavailable authority files produce a bounded authority-state
error; conflicting durable lease history produces an explicit conflict.

The reviewed state identity includes the exact bounded undo snapshot, and the
durable receipt identity covers every stable lifecycle, approval, and authority
evidence field. Snapshot substitution or receipt-field substitution therefore
invalidates the reviewed or replayed operation before state is changed or
evidence is returned.

The exact approval ref is retained in source reason refs and signal provenance
refs, so the read model cannot silently detach a source or artifact from the
review that admitted it.

Corrections retain that admission provenance and unrelated topic interests.
Topic, story-group, and claim identities remain
unchanged when their optional correction labels are blank; publication time
retains its full stored precision unless the operator edits it. Each correction
records its own exact approval in its durable mutation receipt and advances the
artifact revision. Admission refs therefore stay bounded even after repeated
corrections, including shared Q24 artifacts already at the 24-ref limit.

## Storage, recovery, and capacity

The adoption store reuses the Q24 SQLite repository and adds bounded local
preferences, archive metadata, undo state, and mutation receipts. Initialization
or supported schema migration is included in the exact preview and occurs only
with an approved save, in the same transaction as the change and receipt.
An incomplete adopted schema fails closed instead of being silently recreated.
Undo restores the prior source/artifact snapshot while retaining schema and the
audit history; it does not delete the database or approval evidence.

Reads use a bounded, owner-private temporary snapshot of the database and its
committed WAL, without changing source files, schema, modes, or sidecars.
The snapshot is removed after inspection. Concurrent file drift or a pending
rollback journal produces a safe retryable error; reads never ignore a live WAL
or repair durable state. Each copied database or WAL file is limited to 128 MiB.
On an approved save, the POSIX state directory is hardened to `0700` and the
database and sidecars to `0600`; inspection does not chmod existing Q24 state.
File hardening occurs before the mutation transaction commits, so failure
rolls back the new mutation and receipt. An exact committed replay rechecks and
repairs the private-file postcondition; if repair fails it explicitly reports
`NEWS_SIGNALS_ADOPTION_COMMITTED_HARDENING_REQUIRED` instead of claiming a new
uncommitted failure.
After a confirmed precommit hardening rollback, the exact bounded lease remains
available for an idempotent retry. The retry still validates the unchanged
request, current state, approval expiry and unrevoked lease. A different failure,
including an unconfirmed rollback or connection close, retains lease revocation.
Windows-equivalent ACL protection is not established by these POSIX checks.
This is founder-private plaintext on disk, not application-level encryption.
Host disk encryption remains the device boundary.

Manual archive/recover, source safe-disable/recover, and one-step undo are
available. The store is bounded to 24 sources, 2,000 artifacts, 128 topic
preferences, 2,048 receipts, a 4 MiB undo snapshot, 256 KiB API request bodies,
and JSON nesting depth 32. Ordinary mutations reserve the final receipt slot
for one last reviewed undo, so capacity exhaustion cannot strand the latest
reversible change. Automatic backup, automatic multi-computer sync, and
concurrent merge are not included.
When copying the whole prior artifact collection would exceed the unchanged
4 MiB undo budget, undo retains a bounded reference delta: changed artifact
content, any prior source labels, source/preference/archive metadata and refs
to unchanged bodies. Resolution requires the exact complete current-state
binding before restoration; later Q24 changes invalidate undo. Existing full
snapshots remain supported. This prevents unrelated artifact bodies from
blocking archive, correction or recovery at the 2,000-record limit.

## Authority boundary

This slice performs no live source fetch, authenticated source access,
background polling, browser action, provider or model call, connector write,
external write, recommendation execution, public release, or production
authority. External content remains untrusted data and never becomes an
instruction or authority source.

## Verification

- `scripts/verify_queue_v2_q34_news_source_intelligence.py`
- `tests/test_q34_news_signals_adoption.py`
- `tests/test_q34_news_signals_adoption_api.py`
- `tests/test_q34_news_signals_adoption_cli.py`
- `tests/test_q34_news_review_recovery.py`
- `tests/test_queue_v2_q34_news_source_intelligence.py`
- `apps/control-center/src/api/client.newsSignalsAdoption.test.ts`
- `apps/control-center/src/api/client.newsReadBoundary.test.ts`
- `apps/control-center/src/components/NewsSignalsPreviewPanel.test.tsx`
- `apps/control-center/src/components/NewsSignalsPreviewPanel.identity.test.tsx`
- `apps/control-center/src/components/NewsSignalsDigest.test.tsx`
- `apps/control-center/src/App.news.test.tsx`
- `apps/control-center/src/App.backendTruth.test.tsx`
- `apps/control-center/src/App.newsHandoff.test.tsx`
- `tests/test_news_handoff_agent_loop_summary.py`
- `apps/control-center/tests/visual/foundation-surfaces.real.spec.ts`
- OpenAPI/API manifest, capability/release-surface, documentation, frontend,
  Foundation Gate, security, hosted CI, and post-merge qualification gates

Live adapters remain later exact lanes governed by `WebAccessGateway`, source
permission and terms review, credentials, audit, retention, revocation, and
safe-disable evidence. Completing this local adoption item does not promote any
such adapter.

The strict handoff read scope applies to governed critical routes; the existing
non-authoritative preview shell keeps its full-loader fallback contract. The
route tests cover that distinction without changing backend admission checks.
Shared Social foundation subject hashes are refreshed from the current source
inventory only; independent promotion remains pending and all authority flags
remain false. The News summary regression is separate from the historical
capability-comparison evaluator corpus, whose artifact and scores are unchanged.
