# FIN-003 Synthetic Review Projection

Status: implemented bounded synthetic-only, read-only projection

## Outcome

The first FIN-003 slice converts current FIN-002B synthetic import lineage into
strict Finance Review batches and Action Inbox pointers. The projection is
deterministic, content-bound to the current `FinanceSnapshot`, ordered by
newest import revision and stable refs, and available through the existing
`uaa_finance.py review` CLI inspection path.

Each review item contains safe refs for its book, import commit, transaction
candidate, and suspense journal entry. It states only `needs_review`, a fixed
reason/consequence posture, and `confidence_posture=not_scored`. The projection
does not expose amounts, descriptions, source fingerprints, observations, raw
source content, or arbitrary operator input.

## Authority boundary

This is a read-only projection over the protected local Finance repository. It
makes no categorization decision, does not confirm, correct, reject, defer,
split, allocate, or learn a rule, and cannot mutate the Finance book or the
canonical Action Inbox. It adds no API or Control Center surface.

There is no real financial data, file input, OCR, connector, accountant access,
payment, filing, professional advice, provider/model call, browser action,
background sync, public release, or production authority. Independent FIN-000 promotion
remains required before any real-data or higher-authority Finance lane.

## Inspection and verification

For an initialized protected synthetic repository:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py review \
  --repository-dir PATH \
  --helper-path PATH \
  --helper-sha256 SHA256 \
  --request-ref request-ref:finance:fin003-review
PYTHONPATH=src .venv/bin/python scripts/verify_fin003_synthetic_review_projection.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fin003_synthetic_review_projection.py
```

The verifier fixes the expected synthetic census, confirms stable projection
output and source-snapshot binding, scans serialized output for financial
values and source-content markers, and checks that every authority flag remains
false.

## Remaining FIN-003 work

Categorization and other review decisions, canonical Action Inbox persistence,
rule proposals and learning, confidence scoring, grouping by merchant or
recurrence, bulk ChangeSets, API/UI surfaces, and any real-data handling remain
separately scoped and gated.
