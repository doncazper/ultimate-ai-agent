# FIN-001 Synthetic-Only Activation Record

Status: implementation candidate under the active exact Queue V2 claim for
`dev-task:finance-fin001-synthetic-kernel`. The source slice is implemented and
focused verification is green; completion still requires exact-head review,
merge proof, and a coordinator completion receipt. This is not real-data,
supported-deployment, public-release, or production authority.

## Decision

The founder's private-dogfood direction acceptance in PR 425 cleared the
FIN-000 visual prerequisite. PR 426 merged the activation record; the
coordinator then removed only the merge-pending blocker and claimed this exact
task at revision 164. The active implementation remains bounded to the
synthetic kernel below.

The machine-readable activation decision is the immutable pre-claim snapshot
`docs/product/finance_fin001_activation_v1.json`; its verifier is
`scripts/verify_fin001_activation.py`. It truthfully continues to report the
state at activation-record authorship, not current queue state. Current
implementation evidence is owned by the separate FIN-001 kernel verifier below.

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

The unblock receipt is
`developer-work-receipt-ref:sha256:18ad9730b00b4f6d3adef255`; the claim receipt
is `developer-work-receipt-ref:sha256:c86d5a854141da20eb393205`. Neither receipt
completes the task. Completion requires this candidate's protected merge SHA,
exact-head checks, and a fresh coordinator disposition.

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

Every CLI mutation must call the same Python core only after both a current
PolicyEngine allow decision and an exact LocalApprovalAuthority scope bind the
operation, book, current revision, request ref, and intended record refs. The
same operation also requires an active AuthorityLease for exact capability
`capability-ref:finance/FIN-001/synthetic-book-mutation`, revalidated
immediately before persistence. FIN-001 must own and verify that exact binding
inside the Finance boundary without broadening the shared authority catalog; a
generic or coarse `workspace/mutate` lease cannot satisfy it. Denied, unknown,
or stale policy and approval states and coarse, expired,
or revoked leases fail closed. Replays are idempotent;
changed payloads under the same request ref fail closed. The core appends a
redacted mutation receipt before reporting success and provides a tested
reversal or rollback path. Focused tests must cover policy denial and
staleness, denied or stale approval, expired or revoked lease, exact replay,
coarse-lease denial, changed-payload conflict, receipt integrity, rollback, and
safe-disable.

## Non-Goals And Authority Boundary

No real financial data, statement/file import, OCR, connector, bank access,
accountant access, advice, tax or compliance filing, payment, transfer,
provider/model call, browser runtime, background sync, public release, or
supported deployment is included. This record grants no authority beyond the
exact synthetic implementation scope, and no UI or route may imply otherwise.

Independent FIN-000 role acceptance remains required before real-data or any
higher-authority promotion. Cosmetic dogfood changes remain expected and do
not silently expand this exact scope.

## Implemented Candidate Evidence

The candidate implementation is documented in
`docs/product/UAA_FINANCE_FIN001_SYNTHETIC_KERNEL.md`. Its authoritative
surfaces are the `ultimate_ai_agent.core.finance` Python package,
`docs/product/finance_fin001_fixture_manifest_v1.json`, the bounded
`scripts/dev/uaa_finance.py` CLI, the exact Finance AuthorityLease catalog
binding, `tests/test_fin001_synthetic_kernel.py`, and
`scripts/verify_fin001_synthetic_kernel.py`.

The repository serializes SQLite in memory and persists only authenticated
ciphertext. Production-local operation uses the already pinned native macOS
protected-cache helper through a Finance-scoped facade, dedicated opaque
content-derived key handles, and Finance-specific authenticated context. The
helper returns no key material. The memory backend is test-only.

No API route or Control Center action is added. The CLI exposes status,
prepare, explicit-confirmation mutation, inspect, check, and redacted export.
It accepts only the canonical fixture ref for creation; it does not accept
financial values, memos, counterparties, imports, or real records.
