# FIN-002 Synthetic CSV Import Preview

Status: implemented bounded synthetic-only preview core; no import commit authority

Baseline: v0.104.0 / 0.104.0

## Outcome

This slice advances the Finance queue without treating visual polish or the
independent FIN-000 promotion review as a prerequisite for ordinary
development. It implements deterministic typed contracts for one allowlisted
synthetic CSV profile, immutable source observations, transaction candidates,
duplicate detection, bounded quarantine records, redacted preview output, and
a no-op rollback proof.

The founder-approved private-dogfood direction is enough to build and refine
this synthetic surface through use. Independent FIN-000 promotion remains
pending and is still required before any real-data or higher-authority lane.

## Exact Boundary

The only public preview input is an allowlisted fixture ref plus optional prior
fingerprint refs. Arbitrary operator-supplied financial data is rejected. The
module and CLI expose no file path, caller byte stream, pasted CSV, directory,
OCR, connector, API, or UI input.

The three deterministic fixtures cover:

- two valid synthetic rows;
- a semantic duplicate with a different row ref;
- invalid amount, invalid direction, and spreadsheet-formula-shaped cells.

Every successful row becomes a `SourceObservation` and
`TransactionCandidate` bound to safe refs. Duplicate rows expose only their
fingerprint refs. Rejected rows expose a safe quarantine ref, row-position ref,
and bounded reason code; raw cell values are not returned or persisted.

## Rollback Truth

Preview performs no mutation and changes no persistent state. Its rollback
proof binds the exact preview and candidate refs while truthfully recording
`mutation_performed=false`, `persistent_state_changed=false`, and
`rollback_required=false`. Import commit, repository mutation, and rollback
execution remain future separately authorized work.

## Explicit Non-Goals

- no real financial data;
- no arbitrary file or pasted-content ingestion;
- no OFX, QFX, QIF, PDF, image, or OCR support;
- no protected source-document persistence;
- no import commit or Finance repository mutation;
- no connector, provider, browser, network, API, or Control Center route;
- no accounting, tax, legal, filing, payment, transfer, or production
  authority.

## Inspection

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance_import.py manifest
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance_import.py preview \
  --fixture-ref fixture-ref:finance/FIN-002:synthetic-csv-clean:v1
PYTHONPATH=src .venv/bin/python scripts/verify_fin002_synthetic_import_preview.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_fin002_synthetic_import_preview.py
```

CLI output is a redacted structural read model. It never prints raw fixture
rows or grants mutation authority.

## Next Safe Slice

Add an exact approval-bound synthetic commit lane that revalidates the current
preview and fingerprint census immediately before writing to the FIN-001
protected repository. Keep arbitrary input, real data, additional formats, and
OCR independently gated.

