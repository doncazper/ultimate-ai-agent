# FIN-001 Synthetic-Only Activation Record

Status: ready for an exact Queue claim after merge of this record. This is a
verified reservation, not an active claim or a statement that Finance runtime
already exists.

## Decision

The founder's private-dogfood direction acceptance in PR 425 cleared the
FIN-000 visual prerequisite. The required shared foundations are accepted, and
the `product_surface` lane was vacant at coordinator revision 162. FIN-001 is
therefore reserved as the next product-surface WIP item, subject to a fresh
vacancy check and exact claim after merge.

The machine-readable decision is
`docs/product/finance_fin001_activation_v1.json`; its verifier is
`scripts/verify_fin001_activation.py`.

The promoted work item is the separately bounded
`dev-task:finance-fin001-synthetic-kernel`. The broader Queue V2 Q26 program
record stays blocked and cannot be used as the implementation handoff for this
slice. Queue receipt
`developer-work-receipt-ref:sha256:9352c6acbdff3bcd1e5493f3` records the exact
task. Block receipt
`developer-work-receipt-ref:sha256:44573429fe043729321aee47` records its
`blocked` state under
`blocker-ref:finance/FIN-001/pr426-activation-merge-pending`; the coordinator
cannot claim it until this activation PR merges and an explicit unblock is
recorded.

After merge, the coordinator must still show the `product_surface` lane as
vacant, then emit a claim receipt for this exact task. Until that transition is
recorded, the package is ready but not In Progress.

## Dependency Checklist

- Action Inbox: Queue V2 Q00 completed.
- Today: Queue V2 Q08 completed.
- ECO-001 shared local data: Queue V2 Q11 completed.
- first-class Boards/Kanban: Queue V2 Q13 completed.
- local Calendar: Queue V2 Q14 completed.
- ECO-008 EntityLink and ChangeSet guarantees: Queue V2 Q19 completed.
- Weekly CEO Review private trial, the remaining direct Queue V2 dependency:
  Q21 completed.
- FIN-000 contract, threat model, protected-data ADR, implementation sequence,
  and founder private-dogfood direction are present and remain normative.

## Exact First Slice

Implement only the Python-core `Book`, `LegalEntity`, `FinancialAccount`,
`JournalEntry`, and `Posting` contracts; balanced-posting validation; a
synthetic-only local repository; deterministic fixtures; explicit safe-disable
behavior; and synthetic backup/restore proof. Add CLI inspection and mutation
parity for this bounded core. Do not add an API route or Control Center action
in this slice.

Mutation inputs are limited to refs in a versioned deterministic fixture
manifest while this slice remains synthetic-only. Arbitrary operator-supplied
book, entity, account, journal, posting, memo, counterparty, or amount values
must fail closed before persistence. Focused tests must prove unknown fixture
refs and direct financial values are rejected; accepting real data requires a
separate reviewed promotion.

Tests and durable evidence use synthetic values and safe refs. The repository
schema is versioned and uses the ADR-0063 encrypted SQLite boundary from its
first synthetic record. A random per-repository key is available only through
an opaque Keychain handle; key material never enters configuration, CLI output,
logs, receipts, or fixtures. Migration, cryptographic and explicit deletion,
encrypted backup/restore round trips, key-unavailable failure, reversal
behavior, commodity balancing, stale-revision rejection, and redaction are
focused acceptance cases.

Every CLI mutation must call the same Python core through an exact
LocalApprovalAuthority scope that binds operation, book, current revision,
request ref, and intended record refs. Replays are idempotent; changed payloads
under the same request ref fail closed. The core appends a redacted mutation
receipt before reporting success and provides a tested reversal or rollback
path. Focused tests must cover denied or stale approval, exact replay,
changed-payload conflict, receipt integrity, rollback, and safe-disable.

## Non-Goals And Authority Boundary

No real financial data, statement/file import, OCR, connector, bank access,
accountant access, advice, tax or compliance filing, payment, transfer,
provider/model call, browser runtime, background sync, public release, or
supported deployment is included. This record grants no authority beyond the
exact synthetic implementation scope, and no UI or route may imply otherwise.

Independent FIN-000 role acceptance remains required before real-data or any
higher-authority promotion. Cosmetic dogfood changes remain expected and do
not silently expand this exact scope.
