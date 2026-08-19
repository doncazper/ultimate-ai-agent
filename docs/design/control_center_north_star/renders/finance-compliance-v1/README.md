# Finance & Compliance V1 Render Brief

Status: planning-only render brief; image renders pending review
Baseline: v0.104.0 / 0.104.0
Date: 2026-08-16
Program: `FIN-000`
Product contract: `docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md`
Workflow case study: `docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md`
Threat model: `docs/security/UAA_FINANCE_COMPLIANCE_THREAT_MODEL.md`
FIN-000 matrix: `docs/product/UAA_FINANCE_FIN000_ACCEPTANCE_MATRIX.md`

## Purpose

This directory defines the required north-star render pack for UAA Finance &
Compliance before implementation. Renders are product targets, not evidence of
working routes, storage, connectors, calculations, filing, or authority.

The pack must feel unmistakably like the Founder Command Center: calm macOS-first
desktop density, restrained color, readable hierarchy, posture labels, exact
consequences, a strong table/list grammar, and a contextual right inspector. It
must not look like a generic fintech template pasted into UAA.

## Required Renders

1. `01-finance-command-desktop.png`
   - account freshness, review load, unreconciled periods, missing evidence,
     cash posture, upcoming obligations, recurring changes, and readiness gaps;
   - one primary “Review transactions” action, not a wall of metrics.
2. `02-source-statement-inbox-desktop.png`
   - books/accounts and uploaded sources with period coverage, extraction
     method, duplicates, in/out-of-period state, entity binding, parse warnings,
     balance evidence, missing periods, and closure gaps;
   - a selected statement opens protected extraction diagnostics and source
     preview without exposing raw values in generic shell chrome.
3. `03-extraction-reconciliation-workbench.png`
   - beginning/ending balance evidence, source totals, normalized totals,
     difference, transaction/page coverage, extraction confidence, excluded
     sections, exceptions, and re-run/rollback posture;
   - visibly distinguish imported, extracted, complete, reconciled, and closure
     proven.
4. `04-transfer-balance-sheet-review.png`
   - candidate transfer/card-payment pairs, loans, reimbursements,
     contributions/distributions, refunds, and investment flows with both legs,
     entity/account context, confidence, exceptions, and P&L consequence.
5. `05-review-batches-desktop.png`
   - ranked merchant/payee or recurring-pattern groups, safe examples, affected
     count/period, entity/category/type/allocation proposals, evidence state,
     outliers, exceptions, and “unknown / ask accountant” paths;
   - batch size supports one focused review session rather than a giant queue.
6. `06-transaction-review-desktop.png`
   - keyboard-friendly candidate queue, filters, confidence/reason, proposed
     category, evidence state, and exact review actions;
   - selected item opens the inspector without losing queue position.
7. `07-transaction-evidence-inspector.png`
   - original source observation, normalized candidate, balanced postings,
     category/tax treatment distinction, split/business use, receipt, business
     purpose, linked question, history, and correction path.
8. `08-books-reconciliation-desktop.png`
   - books/accounts, statement period, cleared/uncleared totals, difference,
     exceptions, close posture, and governed reopen/adjustment language.
9. `09-tax-readiness-accountant-desktop.png`
   - year/period checklist, missing forms/evidence, unresolved treatments,
     accountant questions, reconciliation/source-coverage posture, packet
     inclusion manifest, exclusions, and unresolved-gap preview;
   - “Prepare packet,” never a fake “File taxes” action.
10. `10-compliance-obligations-desktop.png`
   - entities, jurisdictions, obligations, applicability, source/as-of date,
     freshness, due window, owner, status, evidence, and contested state.
11. `11-calendar-finance-saved-view.png`
   - UAA Calendar with Finance & Compliance saved view for closes, recurring
     payments, estimated taxes, renewals, and filing windows;
   - every item visibly projects from its owning record.
12. `12-founder-loop-finance-projections.png`
   - Today, Morning Briefing, Action Inbox, and Work Board examples showing the
     same Finance refs across daily review, decisions, and multi-step work.

After desktop acceptance, add narrow variants for command, review, evidence
capture, and upcoming obligations. Use synthetic names, amounts, institutions,
entities, tax years, jurisdictions, account suffixes, and document refs only.

## UAA Visual Contract

Follow:

- `docs/portfolio/PRODUCT_NORTH_STAR.md`;
- `docs/design/STATUS_AND_RISK_VISUAL_LANGUAGE.md`;
- `docs/control_center/PRODUCT_LANGUAGE_RULES.md`;
- existing Founder Loop and coherent ecosystem renders.

Required traits:

- existing UAA sidebar/shell, toolbar, spacing, radius, typography, and panel
  hierarchy;
- high information density with calm grouping and generous row legibility;
- textual status plus color/icon; never color-only meaning;
- neutral posture for healthy state, amber for review/stale/estimated, red only
  for actual blocked/overdue/high-consequence state;
- exact “as of,” source, book/entity, completeness, and blocked/planned labels;
- table and list layouts that work with keyboard and screen reader order;
- empty, loading, stale, disconnected, conflict, no-book, no-source, and restore
  states included in the design review, even if not all are hero images.

Avoid:

- neon fintech gradients, crypto/trading visual language, gamified savings
  rings, confetti, fake credit scores, or unsourced “AI saved you” claims;
- dashboard cards without an operational next step;
- a separate design system, navigation shell, Action Inbox, Calendar, or board;
- raw JSON as the main inspector;
- fake Connect bank, Sync, Invite accountant, Pay, Submit, Sign, or File buttons;
- implying a suggestion, estimate, calendar date, or render is verified truth.

## Interaction Notes To Show

- Review actions are confirm, correct, split, transfer, personal/business,
  attach evidence, ask, defer, and propose rule.
- Source intake shows coverage and extraction/reconciliation posture before
  categorization, including missing and out-of-period material.
- Review Batches explain rank, preview affected records and outliers, capture
  entity/type/category/business-use/purpose/evidence separately, and preserve
  per-transaction exceptions.
- Unsupported blanket allocations and personal/family-to-business shifts show
  a clear blocked explanation and evidence/professional-review next step;
  documented exact reimbursements remain distinct reviewable proposals.
- A suggestion explains “why” and shows confidence posture without pretending a
  probability is professional certainty.
- Rule creation previews affected items, conflicts, exclusions, historical
  reach, and rollback.
- Reconciliation shows the target, current difference, exceptions, and the
  consequence of closing or reopening.
- Tax readiness separates bookkeeping categories, potential tax treatments,
  missing information, professional review, and filing state.
- Compliance items show source, applicability, freshness, and review state near
  the date—not hidden in a detail drawer.
- Calendar/Today/Board projections deep-link to the canonical Finance object.

## Render Acceptance Checklist

- [ ] All twelve desktop renders exist at readable resolution.
- [ ] Command, review, capture, and obligation narrow states exist.
- [ ] A single fixture story stays coherent across every surface.
- [ ] Every visible datum has a canonical owner.
- [ ] Planned, fixture, stale, blocked, estimated, and verified states are
      visually and textually distinct.
- [ ] No control implies unavailable runtime authority.
- [ ] Review and correction consequences are readable before commitment.
- [ ] Sensitive values are synthetic and no raw local paths/usernames appear.
- [ ] Keyboard, focus, contrast, zoom, reduced motion, and screen-reader reading
      order are documented.
- [ ] Product, design, accounting-domain, privacy/security, and implementation
      reviewers record acceptance or requested changes.

Until this checklist is signed off, `FIN-000` remains proposed and the images
must not be treated as implementation evidence.
