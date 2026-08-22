# ECO-008 EntityLink And ChangeSet Engine

Status: implemented bounded local Python Core contract. No route, CLI, UI,
connector, external write, provider/model call, or production authority is
granted.

ECO-008 turns the planning-only `EntityLink` and `ChangeSetPlan` vocabulary
into a governed local shared-core lane. It persists typed links and can update
existing Tasks, Boards, and Calendar aggregates in one ECO-001 SQLite
transaction without copying canonical truth or claiming atomicity outside that
transaction.

## Implemented boundary

- `EntityLinkRepository` persists exact workspace/privacy/provenance/deletion
  bindings. Removing a link tombstones only the link record; neither endpoint
  is deleted or changed. Exact create/remove replay remains durable.
- `ChangeSetEngine.prepare_local` reads current encrypted aggregate state,
  validates each owning domain model, derives keyed private-value
  fingerprints, computes content-free top-level field diffs, orders a unique
  acyclic dependency set, and produces an immutable `ChangeSetPlan`.
- The concrete local mutation adapters are deliberately limited to existing
  Task/TaskOccurrence, Board/BoardTemplate, and CalendarSet records. The engine
  repeats Task reference/cycle checks, Board Task-projection checks, Calendar
  lifecycle/identity/Task-reference checks, protected undo normalization,
  canonical search terms, retention binding, workspace binding, and optimistic
  version/fingerprint checks immediately before commit.
- One exact `LocalApprovalAuthority` request binds the workspace,
  idempotency ref, operation and target refs, plan/scope fingerprints,
  capabilities, and rollback plans. It cannot mint authority from the review
  plan.
- Domain updates and the encrypted ChangeSet rollback ledger commit through
  the existing ECO-001 unit of work. An injected fault, stale version, changed
  fingerprint, missing related record, or unsupported domain rolls back the
  complete local transaction.
- Exact replays return the original encrypted unit-of-work receipt. Conflicting
  idempotency reuse fails closed.
- `prepare_undo`/`prepare_rollback` reads the encrypted ledger, verifies its
  plan, scope, old/new private fingerprints, current target bindings, and
  domain invariants, then prepares a new exact approval scope. Rollback is a
  second atomic local transaction and preserves each domain's protected undo
  history.
- External operations remain `external_compensating` contracts. The engine can
  project ordered observed outcomes, partial-completion truth, next safe
  action, and compensation-plan refs; it never invokes or persists an external
  action.

## Privacy and evidence

Replacement and rollback payloads are encrypted inside the existing ECO-001
record and receipt envelopes. Review output contains field refs and keyed
before/after fingerprints, not field values. The ChangeSet ledger is also
encrypted; durable safe summaries contain only refs, state, version, and
fingerprints.

The test crypto backend and path resolver remain test-only. ECO-008 does not
promote a production Keychain/path backend and does not change the ECO-001
schema.

## Explicit limits

- Existing records only; create, delete, archive, retention, and expiry changes
  remain in their owning domain lifecycle lanes.
- Local atomic execution supports only Tasks, Boards, and Calendar aggregates.
  CRM and Inbox records may be linked but are not mutated through ECO-008.
- No external execution, connector read/write, send, account access, browser,
  shell/subprocess, network, provider/model, scheduler, or background worker.
- No route, CLI, Control Center review screen, existing-product cutover,
  public release, or production authority.
- A `ChangeSetPlan`, field diff, outcome projection, approval ref, or rollback
  plan is evidence or a proposal; none is standing authority.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_eco_001_local_data.py \
  tests/test_eco_002_tasks.py \
  tests/test_eco_003_boards.py \
  tests/test_eco_004_calendar.py \
  tests/test_eco_008_changesets.py \
  tests/test_eco_008_verifier.py
PYTHONPATH=src .venv/bin/python scripts/verify_eco_008_changesets.py
```
