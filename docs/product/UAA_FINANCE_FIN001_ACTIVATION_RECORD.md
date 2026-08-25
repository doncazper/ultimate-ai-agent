# FIN-001 Synthetic-Only Activation Record

Status: activated for bounded implementation after merge of this record. This
is a Queue V2 WIP decision, not a claim that Finance runtime already exists.

## Decision

The founder's private-dogfood direction acceptance in PR 425 cleared the
FIN-000 visual prerequisite. The required shared foundations are accepted, and
the `product_surface` lane has no prior active task. FIN-001 is therefore the
explicit next product-surface WIP item.

The machine-readable decision is
`docs/product/finance_fin001_activation_v1.json`; its verifier is
`scripts/verify_fin001_activation.py`.

The promoted work item is the separately bounded
`dev-task:finance-fin001-synthetic-kernel`. The broader Queue V2 Q26 program
record stays blocked and cannot be used as the implementation handoff for this
slice. Queue receipt
`developer-work-receipt-ref:sha256:9352c6acbdff3bcd1e5493f3` records the exact
task; it stays blocked until this activation PR merges.

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

Tests and durable evidence use synthetic values and safe refs. The repository
schema is versioned; migration, explicit deletion, backup/restore round trips,
reversal behavior, commodity balancing, stale-revision rejection, and
redaction are focused acceptance cases. Any unavailable protected-storage or
key boundary must fail closed before real-data promotion; no key enrollment is
needed or allowed for this synthetic-only slice.

## Non-Goals And Authority Boundary

No real financial data, statement/file import, OCR, connector, bank access,
accountant access, advice, tax or compliance filing, payment, transfer,
provider/model call, browser runtime, background sync, public release, or
supported deployment is included. This record grants no authority beyond the
exact synthetic implementation scope, and no UI or route may imply otherwise.

Independent FIN-000 role acceptance remains required before real-data or any
higher-authority promotion. Cosmetic dogfood changes remain expected and do
not silently expand this exact scope.
