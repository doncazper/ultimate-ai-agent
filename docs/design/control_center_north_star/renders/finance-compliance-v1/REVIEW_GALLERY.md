# FIN-000 Locked Render Review Gallery

Status: review-ready; independent decisions pending

Candidate manifest: `manifest-ref:fin000-render-pack:v1`

Acceptance ledger: `acceptance-ledger-v1.json`

Run `PYTHONPATH=src .venv/bin/python scripts/verify_fin000_render_acceptance.py`
before review. Each preview below links to the full-resolution candidate bound
by the ledger. The images are synthetic planning targets, not implementation
evidence.

## Desktop Candidates

| Candidate | Full-resolution render |
|---|---|
| 01 Finance command | [Open 01](01-finance-command-desktop.png) |
| 02 Source/statement inbox | [Open 02](02-source-statement-inbox-desktop.png) |
| 03 Extraction/reconciliation | [Open 03](03-extraction-reconciliation-workbench.png) |
| 04 Transfer/balance-sheet review | [Open 04](04-transfer-balance-sheet-review.png) |
| 05 Review batches | [Open 05](05-review-batches-desktop.png) |
| 06 Transaction review | [Open 06](06-transaction-review-desktop.png) |
| 07 Transaction evidence inspector | [Open 07](07-transaction-evidence-inspector.png) |
| 08 Books/reconciliation | [Open 08](08-books-reconciliation-desktop.png) |
| 09 Tax readiness/accountant | [Open 09](09-tax-readiness-accountant-desktop.png) |
| 10 Compliance obligations | [Open 10](10-compliance-obligations-desktop.png) |
| 11 Calendar Finance view | [Open 11](11-calendar-finance-saved-view.png) |
| 12 Founder Loop projections | [Open 12](12-founder-loop-finance-projections.png) |

## Narrow Candidates

| Candidate | Full-resolution render |
|---|---|
| 13 Finance command | [Open 13](13-finance-command-narrow.png) |
| 14 Transaction review | [Open 14](14-transaction-review-narrow.png) |
| 15 Evidence capture | [Open 15](15-evidence-capture-narrow.png) |
| 16 Upcoming obligations | [Open 16](16-upcoming-obligations-narrow.png) |

## Finite Review Flags

These are questions for the independent roles, not pre-decided defects:

- In candidate 14, determine whether “Bank feed” conflicts with the pack's
  no-live-connection posture or is sufficiently identified as fixture context.
- In candidate 15, determine whether “Attach evidence” looks executable despite
  the external-actions-blocked and review-only proposal posture.
- In candidates 01 and 09, determine whether the primary review/draft controls
  look too executable for a planning-only render.

Record any requested correction as a safe finding ref in the acceptance ledger.
Do not put raw review notes, personal identifiers, or local paths in durable
repository evidence.
