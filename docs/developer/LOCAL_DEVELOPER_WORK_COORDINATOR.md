# Local Developer Work Coordinator

Status: implemented local-developer coordination v1. It is deliberately
separate from the UAA Python Agent Core, Control Center, and product-runtime
authority model.

The coordinator turns the existing strategic queue into explicit, durable
developer work handoffs. It is not a second roadmap and it never makes a
Markdown item executable by itself.

## What It Does

- Indexes the canonical current board, Founder Command Center board, runtime
  roadmap, and Phase 0/1 task breakdown. The catalog currently exposes the
  existing planning candidates, including the continuous authority conveyor,
  rather than replacing that months-long queue with a small local list.
- Requires an explicit triage record before a candidate can be claimed: a
  canonical source reference and fingerprint, branch reference, isolated
  worktree reference, priority, dependencies, acceptance checks, verifier
  checks, merge gates, an explicit in-scope/out-of-scope contract, and a
  task-appropriate `gpt-5.6-sol` thinking level.
- Provides a durable, fsync-backed, recoverable transaction journal so every
  snapshot mutation and idempotency receipt commit together. Registered Mac
  and Beast nodes can claim bounded work without double ownership. A node
  must declare its safe transport reference, reviewed capabilities, and ready
  posture before it may claim work; its idle and active liveness is recorded by
  a separate node heartbeat. Use one explicitly configured shared local state
  directory for both machines.
- Enforces at most three claims globally, at most two claims per named node,
  one claim in each `shared_core`, `product_surface`, and
  `verification_read_only` lane, and only one `exclusive` task at a time.
  Active tasks cannot share a branch or worktree reference. Use `exclusive`
  for a bounded authority-changing lane, not as a broad global lock.
- Treats a nonempty authoritative V2 queue with zero admitted nonterminal work
  as queue starvation and a control-plane failure rather than successful idle.
- Runs four fixed, read-only Git metadata checks: dirty-entry count, registered
  and prunable worktree counts, non-merged branch metadata, and local-main
  divergence from `origin/main`. It never passes user-provided text to a shell
  or Git command.
- Produces safe-ref-only receipts, handoff JSON, and scout reports. It omits
  raw paths, file contents, Git diffs, terminal output, and credentials.
- Records every discovered issue as exactly one of `must_fix_now`,
  `defer_safely`, or `dismiss_with_evidence`. Safe deferral requires a durable
  follow-up reference; an adjacent issue may not silently broaden the PR.

## What It Does Not Do

- It does not start Codex or any other developer agent, connect to Beast,
  create or delete worktrees, create branches, commit, push, merge, prune,
  rebase, pull, delete branches, or query GitHub. Pull-request inspection stays
  in a separately authorized app/operator lane; v1 only contains a fail-closed
  parser contract for externally supplied safe PR metadata.
- It does not run test suites or arbitrary shell commands. Workers run the
  bounded implementation and verifier commands in their isolated worktrees,
  then record evidence references themselves.
- It has no product-runtime authority. It does not call models/providers,
  browse, use connectors, grant UAA approvals, or alter UAA policy.

Those limits are intentional for v1: Git and remote-worker mutation need their
own exact developer-operations admission path. The read-only scout makes the
current risks visible first, so cleanup and merging are reviewed rather than
silent side effects.

The broader Git-operations proposal is explicitly deferred as
`follow-up-ref:developer-operations-exact-admission-v1`. It is not part of
`contract-ref:developer-coordinator-durable-v1`, cannot be admitted by a
queue entry, and must receive its own threat model, branch, owner, acceptance
checks, verifier, and merge gates before any developer Git mutation is added.

## Operating Flow

1. Inspect canonical work with `catalog`. Planning candidates remain
   non-dispatchable. `inspect` validates Queue-of-Record V2 and reports its
   admission, supersession, and starvation health.
2. Register each reviewed node and record an initial node heartbeat. A
   non-ready or unregistered node cannot claim work.
3. Create exactly one triaged task with a pre-created isolated branch/worktree
   reference, focused acceptance and verifier references, and explicit merge
   gates.
4. Print a handoff for `node-ref:mac` or `node-ref:beast`. On the target
   machine, an operator starts the bounded local worker and has it explicitly
   claim the task from the same shared ledger.
5. The worker implements and verifies in that isolated worktree. It records a
   heartbeat, scope dispositions, evidence references, then completion or a
   safe blocker reference.
6. Run `scout` before any cleanup or merge. A dirty worktree, stale/prunable
   worktree registration, local-main divergence, or non-merged branch is a
   review gate, not a reason to run a destructive command automatically.
7. A human reviews PR status and exact verifier evidence before any explicit
   merge or cleanup operation outside this coordinator.

## Queue-of-Record V2

`docs/roadmap/UAA_DEVELOPER_QUEUE_V2_MANIFEST.json` is the authoritative
developer queue. It contains the complete Q00-Q36 dependency-wave order, exact
WIP lanes, merge-order constraints for overlapping recovery work, two stale
draft pull-request triage records, eleven visible gated programs, and the
programs that must remain embedded rather than becoming duplicate top-level
tasks.

Admission is explicit, idempotent, and ledger-only. It creates no agent,
branch, worktree, commit, pull request, connector, provider call, or product
authority. It admits all thirty-seven records but claims none. Owners use the
normal claim path after proving the named isolated branch/worktree and next
gate. The eleven authority-heavy entries are descriptive gated records and are
not admitted as executable tasks.

A reviewed manifest extension may also change a still-queued predecessor
contract. First use `preview-queue-v2-amendment` to obtain and review the exact
approval scope without mutation. `amend-queue-v2-item` then replaces only a
never-claimed queued record, requires both that exact scope and the exact prior
canonical-source fingerprint, preserves the task's identity and worktree
bindings, and emits a durable amendment receipt containing safe approval,
scope, approving-actor, and prior-fingerprint refs bound by an authorization
proof fingerprint. The proof also persists and binds the exact pre-amendment
task-revision ref so it remains independently auditable after replacement. It fails closed for
claimed, previously claimed, blocked, review, or terminal tasks. Queue health
reports semantic contract drift separately from missing admission so an
appended wave cannot conceal an obsolete predecessor scope.

New and amended canonical records carry source-aware per-item contracts and
durable dependency bindings. A legacy prerequisite that predates those fields
is accepted only when its exact historical fingerprint has a reviewed
`legacy-source-acceptance-ref` bound to that item's current source set in the
manifest. Editing those sources without refreshing the explicit transition ref
fails manifest validation; unrelated item edits do not invalidate the binding.

Canonical claims also require a durable source-aware contract reconciliation
bound to the exact task revisions reviewed. Admission, queued amendment, and
later task transitions invalidate that reconciliation; none of those commands
may silently grant a replacement approval. Any stale, incomplete, or
source-drifted reconciliation clears claim readiness, and the coordinator never
resolves this gate from an ambient worktree manifest. After the final intended
queue mutation, first preview the complete approval scope without mutation:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" \
  preview-queue-v2-reconciliation \
  --idempotency-ref idempotency-ref:queue-v2-reviewed-reconciliation --pretty
```

Review and copy the exact `approval_scope_ref`. The scope binds the complete
canonical contract map, every current task revision, every legacy transition
and source binding, the current snapshot revision, the actor, and the
idempotency ref. Then reconcile that unchanged state:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" \
  reconcile-queue-v2 \
  --idempotency-ref idempotency-ref:queue-v2-reviewed-reconciliation \
  --confirm-reconciliation reconcile-queue-v2 \
  --approve-exact-scope developer-queue-reconciliation-scope-ref:sha256:copy-exact-preview-value \
  --pretty
```

An intervening mutation makes the preview stale and requires a new preview.
The durable receipt preserves the reviewed maps, snapshot revision, result ref,
approval scope, approving actor ref, and proof ref for restart and audit.

The immutable `docs/roadmap/UAA_REMAINING_QUEUE_MANIFEST.json` and the local
`docs/roadmap/UAA_DEVELOPER_QUEUE_RECOVERY_MANIFEST.json` remain historical
evidence. Their former recovery command now fails closed with
`DEVELOPER_QUEUE_RECOVERY_SUPERSEDED_BY_V2`; this prevents the rescued subset
from duplicating work already represented by Q00-Q36.

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" \
  preview-queue-v2-amendment \
  --item-id Q31 \
  --expected-current-fingerprint-ref planning-fingerprint-ref:sha256:reviewed-prior \
  --idempotency-ref idempotency-ref:queue-v2-q31-reviewed-amendment --pretty
```

Review and copy the preview's exact `approval_scope_ref` and
`current_task_revision_ref`, then pass both without editing them. The revision
binding makes the approval stale after any intervening task transition, even if
the task later returns to queued state:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" \
  amend-queue-v2-item \
  --item-id Q31 \
  --expected-current-fingerprint-ref planning-fingerprint-ref:sha256:reviewed-prior \
  --expected-current-task-revision-ref developer-work-task-revision-ref:sha256:copy-exact-preview-value \
  --idempotency-ref idempotency-ref:queue-v2-q31-reviewed-amendment \
  --confirm-amendment amend-queue-v2-item \
  --approve-exact-scope developer-work-amendment-scope-ref:sha256:copy-exact-preview-value \
  --pretty

PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" \
  preview-queue-v2-admission \
  --idempotency-prefix idempotency-ref:queue-v2-admission \
  --item-id Q32 --item-id Q33 --item-id Q34 --item-id Q35 --item-id Q36 \
  --pretty

PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" \
  admit-queue-v2 \
  --idempotency-prefix idempotency-ref:queue-v2-admission \
  --item-id Q32 --item-id Q33 --item-id Q34 --item-id Q35 --item-id Q36 \
  --expected-snapshot-revision copy-exact-preview-value \
  --confirm-admission admit-queue-v2 \
  --approve-exact-scope developer-queue-admission-scope-ref:sha256:copy-exact-preview-value \
  --pretty

PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" inspect --pretty
```

Admission is one atomic mutation bound to the selected drafts and exact ledger
revision. If its result is uncertain, rerun the identical revision, scope, and
idempotency values; the durable receipt replays without duplicating tasks. A successful
inspection reports thirty-seven admitted records, no contract drift, and no
starvation risk. Use
repeatable `--item-id` arguments to admit only a reviewed manifest extension
without replaying the unchanged prefix of the queue. The
two current owner-held units are claimed separately so admission cannot create
or duplicate workers.

If an already-completed source-aware record later has legitimate canonical
contract drift, do not reopen or rewrite its terminal evidence. Use
`preview-queue-v2-completed-migration` with an exact reviewed evidence ref, then
pass its task revision and approval scope to
`migrate-queue-v2-completed-item`. The lane accepts only completed source-aware
records, preserves lifecycle and completion evidence, invalidates stale
reconciliation, and emits a proof-bound migration receipt.

## Commands

The default state home is host-level rather than worktree-level, so every
isolated Codex worktree on the Mac observes the same queue. Set the same state
directory on Mac and Beast only if it is an intentionally
shared, access-controlled developer volume that guarantees atomic replacement
and cross-host POSIX advisory locking. Do not use a consumer sync folder or
two independently replicated directories: that can duplicate claims. The
default host-level location is suitable for the Mac only; Beast must use an
explicit verified shared transport before it claims from the same ledger.

```bash
export UAA_DEVELOPER_COORDINATOR_STATE_DIR="<shared-local-state-dir>"

PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py catalog --pretty
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" \
  initialize --idempotency-ref idempotency-ref:developer-queue-init --pretty
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" register-node \
  --node-ref node-ref:mac \
  --transport-ref developer-transport-ref:mac-host-local \
  --capability queue_claim --capability local_worktree \
  --capability local_verification \
  --idempotency-ref idempotency-ref:register-mac \
  --confirm-register register-node --pretty
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" node-heartbeat \
  --node-ref node-ref:mac --idempotency-ref idempotency-ref:mac-heartbeat-001 --pretty
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py scout --pretty
```

Triage requires every bounded worktree and merge-safety input. For example,
replace the safe-reference placeholders with the exact reviewed values:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" triage \
  --planning-item-ref planning-item-ref:docs-kanban-founder-command-center-board/fcc-today-render-001 \
  --task-ref dev-task:fcc-today-render-001 \
  --branch-ref branch-ref:codex/fcc-today-render-001 \
  --worktree-ref worktree-ref:mac/fcc-today-render-001 \
  --workstream-ref workstream-ref:founder-command-center \
  --wip-lane product_surface \
  --scope-contract-ref scope-contract-ref:fcc-today-render-001 \
  --in-scope-ref scope-ref:today-render/accepted-composition \
  --out-of-scope-ref scope-ref:today-render/no-new-backend-authority \
  --sol-thinking high \
  --acceptance-ref acceptance-ref:today-render-fidelity \
  --verifier-ref verifier-ref:frontend-focused \
  --merge-gate-ref merge-gate-ref:clean-worktree \
  --next-safe-action "Implement the accepted Today render correction only." \
  --idempotency-ref idempotency-ref:triage-today-render \
  --confirm-triage triage --pretty
```

Then prepare and claim a Mac/Beast handoff:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" handoff \
  --task-ref dev-task:fcc-today-render-001 --node-ref node-ref:mac --pretty

PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" claim-next \
  --node-ref node-ref:mac --idempotency-ref idempotency-ref:mac-claim-001 --pretty
```

Use `heartbeat`, `complete`, `cancel`, `block`, `unblock`, `release`, and
`inspect --include-scout` to maintain the ledger. `complete` requires focused
evidence references. `unblock` is an explicit reviewed transition; it does not
silently retry or reassign work. It requires the one exact expected blocker and
a reviewed evidence ref, and it fails without changing state if another blocker
has been added. For merge-gated work, use the exact `merge-commit-ref` produced
by the merged prerequisite after fetching `origin/main`; the coordinator
requires a full 40-hex commit and proves that it is an ancestor of the protected
remote-main ref and that its commit message names the exact `prNNN` encoded in
the blocker ref before changing queue state. `cancel` applies only to unclaimed
work, requires an exact reason ref plus explicit confirmation, and is
idempotent.

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" unblock \
  --task-ref dev-task:fcc-today-render-001 \
  --expected-blocker-ref blocker-ref:pr123-activation-merge-pending \
  --evidence-ref merge-commit-ref:"$PR_MERGE_SHA" \
  --idempotency-ref idempotency-ref:unblock-after-merge --pretty
```

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" cancel \
  --task-ref dev-task:fcc-today-render-001 \
  --cancellation-reason-ref cancellation-ref:superseded-by-accepted-scope \
  --idempotency-ref idempotency-ref:cancel-today-render \
  --confirm-cancel cancel-task --pretty
```

After completion, record one terminal scope packet before the associated Codex
task may be archived. This binds the final scope dispositions, durable
deferrals, and completion evidence to the archive decision; the CLI does not
archive a Codex task itself.

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" record-terminal-packet \
  --task-ref dev-task:fcc-today-render-001 \
  --terminal-scope-packet-ref terminal-packet-ref:fcc-today-render-001 \
  --idempotency-ref idempotency-ref:archive-ready-today-render \
  --confirm-archive-ready archive-ready --pretty
```

Classify an issue before changing the PR:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py \
  --state-dir "$UAA_DEVELOPER_COORDINATOR_STATE_DIR" record-scope-disposition \
  --task-ref dev-task:fcc-today-render-001 \
  --finding-ref finding-ref:adjacent-layout-hardening \
  --classification defer_safely \
  --safe-summary "Adjacent layout hardening is outside the accepted correction." \
  --deferred-follow-up-ref follow-up-ref:layout-hardening \
  --idempotency-ref idempotency-ref:defer-layout --pretty
```

## Scope, Deferral, And Loop Policy

Every task must name its owned outcomes and explicit non-goals. A finding is
`must_fix_now` only when evidence shows it breaks the locked acceptance criteria,
an invariant, required verification, or exact merge gate. It requires evidence
of the repair before completion. `defer_safely` is for adjacent hardening, edge
cases, or independent improvement; it requires a durable follow-up reference.
`dismiss_with_evidence` is for a duplicate, superseded, or unsupported finding.

Do one complete in-scope repair batch, then rerun only affected checks. Never
spin in repeated broad qualifications, CI requests, review requests, or polling
without a changed candidate or material new evidence. After two repeats of the
same non-progress condition, record a concise escalation and move to an
independent ready task until an owner or external state resolves it.

## Nodes, Threads, And Communication

Node references are unbounded: `node-ref:mac`, `node-ref:beast`, and a future
third machine use the same claim/handoff protocol. Each needs its own isolated
worktree and access to the verified shared ledger. Do not give two nodes the
same branch or worktree reference.

For each task, keep one Codex thread as its primary owner and communicate at
claim, before the first shared-file change, focused verification completion,
scope disposition, PR publication, review/CI material change, block,
post-merge proof, and cleanup. The app-level coordinator sets the worker model
to `gpt-5.6-sol` and selects thinking as follows:

- `medium`: inventory, documentation-only, read-only scouting, and bounded
  mechanical cleanup review.
- `high`: normal focused frontend, test, packaging, or single-module work.
- `xhigh`: cross-surface state changes, approval/idempotency/recovery/security
  work, merge-conflict resolution, or an adversarial final qualification.

Threads are archive-ready only after the task is merged or explicitly canceled,
post-merge or final evidence is recorded, no active handoff remains, and the
owner has written the terminal scope/deferral packet through
`record-terminal-packet`. The coordinator exposes this gate in `inspect`; the
Codex app monitor may archive a task only after that gate is true. It does not
archive an active or genuinely useful blocked thread.

The Codex app monitor named `UAA developer coordinator health monitor` applies
this policy every three hours as a read-only control loop. It reports only
material changes and can archive a terminal UAA task thread; it cannot create
workers, mutate Git/GitHub, or grant runtime authority. A new remote computer
must appear as a connected Codex host with an explicitly configured project and
a verified shared-ledger transport before it may receive a handoff.

## Required Merge And Cleanup Discipline

The coordinator does not claim that a task is merge-ready merely because it is
completed. A PR/branch remains review-required until its exact acceptance and
verifier evidence are available, the source fingerprint is still current, the
target worktree is clean, current main has been reconciled in a clean isolated
worktree, and a human has reviewed conflicts and GitHub state. Stale worktree
registrations must be classified before an explicit prune command.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_developer_orchestrator.py -q
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py catalog --pretty
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_developer_queue.py scout --pretty
```
