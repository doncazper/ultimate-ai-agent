# ECO-007 Inbox And Source-Artifact Workbench

Status: accepted bounded local repository on 2026-08-21. This is not connector
access, account authentication, background sync, a product-surface cutover,
external communication, public release, or production authority.

## Accepted behavior

ECO-007 adds an encrypted, workspace-scoped repository for manual and synthetic
source work. Inbox canonically owns source bindings, source artifacts,
conversation threads, attachment refs, communication items, and communication
drafts. Tasks, Calendar, CRM, and Boards continue to own records in their
domains.

The accepted repository supports:

- manual and synthetic source bindings with explicit privacy and retention;
- content-free import plans followed by exact approval-bound commits;
- encrypted private artifact titles and content on the ECO-001 data plane;
- triage state, classification, typed same-workspace links, tags, and defer
  posture;
- conversation threads bound to existing artifacts from one binding;
- blind-index search, archive, expiry, and retention-candidate inspection; and
- reviewed source proposals that can feed the ECO-006 Today projection.

Every mutation uses the exact repository-only `ecosystem.inbox.apply` action,
an idempotency ref, operation ref, record ref, and related binding/artifact
refs. Generic ECO-001 mutation cannot create or alter protected Inbox records.

## Privacy and evidence boundary

Artifact title and content are private encrypted payload fields. Safe summaries,
plans, receipts, evidence, and result refs contain digests and safe refs rather
than raw content, raw queries, local paths, provider payloads, prompts,
responses, or logs. Search normalizes the private query, uses keyed blind
indexes, and returns only a query hash ref plus workspace-bound artifact
records. A caller already authorized to read that workspace may receive the
decrypted artifact; unrelated workspaces receive no result.

Source locators, participant refs, attachment refs, evidence refs, links, and
other durable identifiers must be safe refs. Raw path-shaped and secret-shaped
identifiers fail closed. Manual import conservatively rejects obvious
secret-shaped content instead of persisting it as an ordinary artifact.

## Proposal-only downstream handoff

An Inbox proposal identifies one source artifact, intended target owner,
proposed target ref, summary ref, and evidence refs. Creation starts in
`proposed`; review may mark it accepted for a later ChangeSet, rejected, or
superseded. Review changes only the proposal record. It never creates a Task,
Event, CRM record, Board placement, draft send, or archive operation in another
domain.

The proposal permanently reports `mutation_authorized=false`,
`target_write_performed=false`, `raw_content_included=false`, and
`model_output_is_authority=false`. Only an accepted proposal can become an
ECO-006 `source_proposal` candidate, which still grants no target mutation.
ECO-008 remains responsible for separately reviewed cross-app ChangeSets.

## Explicit exclusions

ECO-007 adds no API route, CLI command, Control Center UI, file picker, file
read, email/calendar/message connector, OAuth, cookie, credential, live account
read, send/write, web fetch, browser automation, provider/model call,
subprocess, notification, scheduler, background worker, production key/path
backend, migration/cutover, public distribution, or production authority.

Existing Founder Loop Source Inbox and Action Inbox surfaces remain
compatibility product truth. They are not silently migrated to this repository.

## Verification

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_eco_007_inbox.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_eco_007_inbox.py tests/test_eco_007_verifier.py
```

The focused proof covers encryption at rest, content-free planning, exact
approval and replay, manual/synthetic binding enforcement, workspace isolation,
thread and link integrity, blind-index search, proposal-only review and Today
handoff, archive/retention posture, safe-ref rejection, repository-only domain
enforcement, and static denial of network, browser, and subprocess runtime.
