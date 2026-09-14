# FIN-003 Synthetic Review Decision Persistence

Status: implemented bounded synthetic-only Core/CLI contract; release and queue
qualification are separate evidence gates. This does not complete FIN-003 or Q26.

## What is saved

This separately scoped lane saves one exact current synthetic review decision
in the existing protected Finance generation. `confirm` records an operator
acknowledgement, not categorization or accounting validation. `reject` records
review disposition, not posting reversal or removal. `defer` keeps follow-up
open. Journal entries and balances remain unchanged in all three cases.

The read-only `review` command derives `confirmed`, `rejected`, `deferred`, or
`needs_review` from durable decision history. Batches and Action Inbox pointers
remain `needs_review` while any item is unreviewed or deferred; `reviewed` means
only that every item has a confirm/reject disposition. Postings remain in suspense.
These pointers do not mutate the canonical Action Inbox.

Stable lineage binds repository, book, import commit, candidate and journal entry;
display rank is not identity. A later import may move an item without losing its
decision. Exact `review_undo` appends a compensating record for the current
effective decision and restores the prior review posture. It never erases history
or reverses accounting entries.

## Exact authority and recovery

The dedicated `capability-ref:finance/FIN-003/synthetic-review-decision` requires
the current snapshot/revision, exact current item and decision preview, request
and idempotency binding, current policy, LocalApprovalAuthority approval, active
scope-bound lease, repository path binding and safe-disable checks. Generic
FIN-001/FIN-002 permits cannot substitute. Core repeats those checks under the
existing writer lock immediately before staging the encrypted atomic generation.
Preview alone grants no execution authority. This adds no API or UI authority.

Receipts bind the reviewed preview, history event, before/after snapshot and
compensating-undo contract. Retrying the same reviewed intent with current exact
authority returns the retained committed receipt without a second event. A
competing stale writer fails closed. A staged generation requires an explicitly
confirmed retry of its own intent; another decision cannot recover it. Read-only
review does not repair pending state or report it as successfully committed.

When recovery uses a different current permit, the existing receipt log first
retains a linked `prepared` recovery receipt with that permit, approval decision,
lease and authority decision. This is authorization evidence, not a success
claim. Core revalidates again before promotion and appends the linked `recovered`
receipt only after the protected generation and original committed receipt are
durable. Both records bind the original committed receipt and transition; the
completion also binds its preparation. The original receipt remains immutable
and is returned as the historical replay result. Retrying the same recovery grant
does not duplicate its audit records or the decision history.

An expired or revoked permission is not revived by replay. `refresh-review`
re-presents the unchanged old intent in a fresh preparation without granting
authority, changing state, or claiming its source is still current. The operator
must review and confirm that new bundle separately. Only the confirmed Core run
can validate the current source or recover/replay the exact pending intent.
If the source changed and no exact commit exists, obtain a new current review
item and prepare a new decision instead.

History is append-only and capped at 4,096 records, including undo. The exact
encoded pending generation is capped at 64 MiB and receipts at 8 MiB; both
prepared and committed receipt space is checked before the prepared write.
Reauthorized recovery also reserves its preparation, original commit if missing,
and recovery completion bytes together before writing anything.
Capacity failures do not evict history or partially save a decision. Undo also
needs available capacity and a functioning protected store; unlimited retention
and infallible disk recovery are not claimed. Existing empty-history v1 snapshots
retain their original identity. After upgrading, obtain fresh projection/item
refs; older code is not supported for writing a book with new history fields.

## CLI journey

Use the pinned native helper and an already initialized, allowlisted synthetic
Finance repository. Inspect `review` first to obtain the current source revision
and item ref. `PATH`, `SHA256`, `REVISION` and the uppercase refs below are local
placeholders, not values to copy literally. Capture prepared output in a private
bundle file, review it, and pass that file to `run`.

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py prepare \
  --repository-dir PATH --helper-path PATH --helper-sha256 SHA256 \
  --operation review_decision --expected-revision REVISION \
  --review-item-ref REVIEW_ITEM_REF --decision confirm \
  --request-ref request-ref:finance:review-one \
  --idempotency-ref idempotency-ref:finance:review-one
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py run \
  --repository-dir PATH --helper-path PATH --helper-sha256 SHA256 \
  --bundle PATH --confirmed
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py review \
  --repository-dir PATH --helper-path PATH --helper-sha256 SHA256 \
  --request-ref request-ref:finance:inspect-saved-review
```

For undo, prepare `--operation review_undo` against the fresh revision/item,
replace `--decision` with `--compensates-event-ref EFFECTIVE_EVENT_REF`, and use
new request/idempotency refs. Separately review and confirm that bundle. For an
expired preparation or interrupted exact retry, use `refresh-review --bundle
PATH` with the same repository/helper flags, then separately review and confirm
the refreshed bundle. `run --safe-disable-engaged` rejects before lease issuance.
Errors expose bounded error codes, not input values or exception details.

## Verification and remaining product work

`scripts/verify_fin003_review_decision_persistence.py` checks deterministic
preview/history/projection binding and unchanged ledger truth. The history and
persistence test files cover legacy reads, rehashed substitutions, current
authority, stale/repeated requests, competing writers, bounded capacity, fault
injection at prepared/staged/ciphertext/metadata/receipt boundaries, exact retry,
compensating undo, rank movement and CLI parity. Test-only crypto evidence is
not native Keychain or multi-computer acceptance; those require separate observed
evidence. A local native-helper drill also passed exact-approved synthetic
create/import, decision save, separate-process reopen/replay, compensating undo
and history inspection; its temporary book and Keychain item were deleted through
the approved cleanup lane. This is one macOS host, not hardware portability or
real-data acceptance. Hosted checks, exact-head review and merge proof remain mandatory.

There is no real financial data or arbitrary input, categorization/correction,
split/allocation, transfer linking, rules/learning, bulk decisions, documents/OCR,
connector/provider/model call, accountant access, payment, filing, external write,
production or distribution authority. Independent real-data promotion is still
pending. Full local books/imports, normal Finance UI, receipts/context,
reconciliation, reporting, readiness and cross-module adoption remain required
by `docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md`; this
synthetic-only child cannot prove them complete.
