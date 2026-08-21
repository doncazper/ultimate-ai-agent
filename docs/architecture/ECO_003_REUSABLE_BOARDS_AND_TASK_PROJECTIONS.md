# ECO-003 Reusable Boards And Canonical Task Projections

Status: accepted bounded core on 2026-08-21.

## Accepted implementation

ECO-003 establishes a reusable local Boards aggregate on the encrypted ECO-001
data plane. `BoardRepository` supplies:

- multiple encrypted, versioned Boards with private names and descriptions;
- reusable lanes, standalone board-item cards, deterministic contiguous card
  ordering, WIP limits, board-local labels, and saved filters;
- versioned templates that copy configuration without retaining live coupling;
- optimistic expected-version conflicts and a bounded protected undo stack;
- exact `LocalApprovalAuthority` binding to `ecosystem.boards.apply`, including
  workspace, operation, idempotency, and Board or template refs;
- durable exact replay that survives later Board mutations and rejects a changed
  operation context; and
- canonical Task cards that persist only the Task ref, resolve current Task
  truth through `TaskRepository`, and identify Tasks as the canonical owner.

Boards owns board configuration, placement, order, labels, filters, templates,
and standalone `BoardItem` content. Tasks continues to own Task title, notes,
lifecycle, recurrence, dependencies, dates, and mission bindings. A Task card
cannot store title or description shadow fields, so Boards is not a second task
engine.

## Authority, concurrency, and undo boundary

Every Board or template mutation uses one encrypted ECO-001 unit of work. The
local-data plane reserves `module-ref:boards` for the repository-only
`ecosystem.boards.apply` action. Generic local-data calls and raw calls bearing
the Boards action cannot bypass Board schema, ordering, WIP, projection, replay,
or expected-version validation.

Board mutations compare the exact current version before writing. Lane and card
positions are normalized to contiguous, deterministic indices, and a stale
writer fails closed. The prior Board snapshot is retained inside the encrypted
aggregate for at most 20 mutations. Undo is an explicit approved mutation that
restores the latest snapshot at a new monotonic version; private before-state is
never written to governance events, receipts, logs, or default CLI output.

Templates retain lanes and saved-filter configuration only. Instantiation
creates a separate Board aggregate with its own identity, version, and future
history. Task read models resolve the current canonical Task on every read, so
there is no copied mutable truth or stale Board-owned Task title.

## Explicitly not accepted

- No Boards API route, CLI command, Control Center UI, drag surface, or product
  completeness claim.
- No migration or deletion of the existing Founder Loop Work Board.
- No production Keychain/path backend, attachment store, import/export, or
  application-store cutover.
- No mapped Task lifecycle transition, cross-domain ChangeSet, scheduler,
  connector, model/provider call, web fetch, browser runtime, cloud sync,
  collaboration, public release, or production authority.

The core is sufficient for later API/CLI/UI milestones to share one governed
Board contract. Product cutover still requires route and CLI parity, the
approval-preview handshake, migration and recovery evidence, full card detail,
accessibility and performance proof, and packaging acceptance.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_eco_003_boards.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_eco_003_boards.py tests/test_eco_003_verifier.py
```

The focused suite covers ciphertext at rest, exact domain-action isolation,
ordering and WIP invariants, saved filters, optimistic concurrency, exact replay
after later mutations, protected undo, reusable templates, missing Task denial,
and live canonical Task projection without copied private Task truth.
