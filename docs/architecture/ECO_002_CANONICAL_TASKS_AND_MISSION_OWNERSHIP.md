# ECO-002 Canonical Tasks And Mission Ownership

Status: accepted bounded core on 2026-08-20.

## Accepted implementation

ECO-002 establishes one canonical local Task object on the encrypted ECO-001
data plane. `TaskRepository` supplies:

- encrypted private titles, notes, and checklist text with safe-ref-only public
  metadata and keyed search terms;
- quick capture plus versioned create, save, complete, reopen, archive, restore,
  and archive-before-delete operations;
- exact `LocalApprovalAuthority` binding to `ecosystem.tasks.apply`, including
  workspace, operation, idempotency, and task refs;
- encrypted exact retry semantics that survive later Task mutations, bind the
  public lifecycle operation, and fail closed on changed request context;
- Inbox, Today, Upcoming, Anytime, Waiting, Flagged, Completed, Overdue, project,
  and tag queries;
- same-workspace dependency and hierarchy validation, cycle denial, and active
  reference protection during archive/delete, including cycles spanning parent
  and occurrence links;
- deterministic explicit recurrence plans and distinct occurrence records, with
  no scheduler or background execution;
- exact safe-ref mission, run, plan, owner, evidence, handoff, and recovery
  bindings, with one active Task owner per mission; and
- a size-bounded, immutable, read-only Founder Loop `local_tasks` compatibility
  preview. Historical rows have no private title, so migration candidates require
  an operator-supplied title and no cutover occurs.

Tasks owns task and commitment truth. Plans owns projects. The existing durable
mission subsystem owns mission execution state and receipts. Task mission
bindings are cross-object references, never a second mission program or copied
execution state.

## Authority and recovery boundary

Every mutation passes through the same ECO-001 atomic encrypted unit of work.
The Task-specific action and a content-free request-context ref are included in
encrypted replay material. Exact retries can therefore return their durable
receipt after later mutations without allowing a create, save, complete,
reopen, archive, restore, or delete receipt to satisfy a different lifecycle
operation. The local-data plane binds registered domain actions to their exact
module and record kinds, checks both proposed and existing ownership on upsert,
and rejects generic writes to protected domain modules. Canonical Task writes
also require the internal repository-validation handoff; a raw local-data call
cannot use Task approval to bypass schema, archive, reference, or delete checks.

Pre-ECO-002 `module-ref:tasks` / `record-kind-ref:task` records remain
maintainable only through the separately approved
`ecosystem.tasks.legacy_local_data.apply` compatibility lane. That lane cannot
mutate canonical Task kinds, and the canonical Task lane cannot claim legacy or
foreign records. Archive is a reversible Task-domain state transition available
only through the lifecycle operation; permanent deletion requires an archived,
unreferenced Task and leaves the ECO-001 tombstone.

Recurrence planning is read-only and deterministic. Materialization is a
separate approved mutation bound to the generated occurrence, operation, and
idempotency refs. An exact materialization retry resolves its durable receipt
before checking the parent's current version; a first execution still fails on
a stale plan. The result explicitly records that no scheduler or background work
was started.

## Explicitly not accepted

- No production Keychain/path backend or application-store cutover.
- No Tasks API route, Control Center surface, or product-completeness claim.
- No external task-provider read/write, sync, import, or collaboration.
- No scheduler, notification, reminder, or background recurrence authority.
- No project ownership, mission execution, model/provider call, web fetch,
  browser runtime, public release, or production authority.

The accepted core is sufficient for later Tasks surfaces to use one governed
contract. A product cutover still needs a production key/path implementation,
backup and recovery drill, migration acceptance, route/CLI parity, UI states,
performance evidence, and packaging acceptance.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_eco_002_tasks.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_eco_002_tasks.py tests/test_eco_002_verifier.py
```

The focused suite covers ciphertext at rest, action-scoped authorization,
existing-record ownership, the exact legacy maintenance lane, encrypted durable
lifecycle replay and collision denial, quick capture and lifecycle transitions,
all canonical views, dependency resolution and cycle denial, unique mission
ownership, explicit recurrence, archive/restore/delete safety, and bounded
read-only legacy preview.
