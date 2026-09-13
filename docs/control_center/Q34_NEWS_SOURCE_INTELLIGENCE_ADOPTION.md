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
default. `apps/control-center/src/components/NewsSignalsPreviewPanel.tsx`
provides the normal readable workflow.

Every mutation binds the current revision, payload fingerprint, exact preview,
operator confirmation, exact approval, idempotency ref, and an
operation-budget-one `workspace/write` AuthorityLease. Completed commits
return durable exact-replay receipts with rollback refs. Rebound payloads,
stale revisions, substituted previews or approvals, expired approvals, replay
conflicts, malformed state, and unsafe identifiers fail closed.

The reviewed state identity includes the exact bounded undo snapshot, and the
durable receipt identity covers every stable lifecycle, approval, and authority
evidence field. Snapshot substitution or receipt-field substitution therefore
invalidates the reviewed or replayed operation before state is changed or
evidence is returned.

The exact approval ref is retained in source reason refs and signal provenance
refs, so the read model cannot silently detach a source or artifact from the
review that admitted it.

## Storage, recovery, and capacity

The adoption store reuses the Q24 SQLite repository and adds bounded local
preferences, archive metadata, undo state, and mutation receipts. The state
directory is owner-only mode `0700`; the database and sidecars are hardened to
`0600`. This is founder-private plaintext on disk, not application-level
encryption. Host disk encryption remains the device boundary.

Manual archive/recover, source safe-disable/recover, and one-step undo are
available. The store is bounded to 24 sources, 2,000 artifacts, 128 topic
preferences, 2,048 receipts, a 4 MiB undo snapshot, 256 KiB API request bodies,
and JSON nesting depth 32. Ordinary mutations reserve the final receipt slot
for one last reviewed undo, so capacity exhaustion cannot strand the latest
reversible change. Automatic backup, automatic multi-computer sync, and
concurrent merge are not included.

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
- `tests/test_queue_v2_q34_news_source_intelligence.py`
- `apps/control-center/src/api/client.newsSignalsAdoption.test.ts`
- `apps/control-center/src/components/NewsSignalsPreviewPanel.test.tsx`
- OpenAPI/API manifest, capability/release-surface, documentation, frontend,
  Foundation Gate, security, hosted CI, and post-merge qualification gates

Live adapters remain later exact lanes governed by `WebAccessGateway`, source
permission and terms review, credentials, audit, retention, revocation, and
safe-disable evidence. Completing this local adoption item does not promote any
such adapter.
