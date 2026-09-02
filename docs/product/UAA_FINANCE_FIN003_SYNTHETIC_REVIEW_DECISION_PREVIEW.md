# FIN-003 Synthetic Review Decision Preview

Status: implemented bounded synthetic-only, content-free preview

## Outcome

This second FIN-003 slice lets the private operator preview confirm, reject, or defer
for one exact current synthetic Finance review item. The core
revalidates the supplied `FinanceSnapshot`, rebuilds the FIN-003 projection,
and binds the request and result to the exact projection ref, source snapshot
ref, source revision, and review-item ref.

The result emits only those binding refs, the selected allowlisted decision,
and two consequence refs: one states that the selected decision requires a
separate approved apply, and the other states that the preview leaves the
review item and book unchanged. It exposes no book, import, candidate, journal,
observation, source-fingerprint, amount, description, or raw-content fields.

## Authority boundary

No decision is persisted. The preview does not change review state, mutate the
ledger or Action Inbox, apply a categorization, accept correction input, create
a rule proposal, or grant approval or execution authority. `correct`, `split`,
`allocate`, rule learning, bulk decisions, and every apply path remain outside
this slice.

There is no real financial data, arbitrary file or value input, API or Control
Center route, connector, provider/model call, accountant access, payment,
filing, external write, public release, or production authority. A separate
approved apply contract with exact policy, approval, lease, idempotency,
receipt, rollback, and redaction proof is required before any decision may
change durable state.

## Inspection and verification

For an initialized protected synthetic repository, first obtain a current
`review_item_ref` from `uaa_finance.py review`, then run:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py \
  review-decision-preview \
  --repository-dir PATH \
  --helper-path PATH \
  --helper-sha256 SHA256 \
  --request-ref request-ref:finance:fin003-decision-preview \
  --review-item-ref REVIEW_ITEM_REF \
  --decision confirm
PYTHONPATH=src .venv/bin/python \
  scripts/verify_fin003_synthetic_review_decision_preview.py
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_fin003_synthetic_review_decision_preview.py
```

The CLI loads the current protected snapshot through the existing read-only
repository path. It does not accept a serialized projection or financial
payload from the caller.

## Remaining FIN-003 work

Decision persistence or apply, corrections, splits, allocations, context
requests, rule proposals and learning, confidence scoring, grouped or bulk
ChangeSets, API/UI surfaces, and real-data handling remain separately scoped
and gated.
