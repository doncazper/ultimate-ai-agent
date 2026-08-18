# UAA Finance Workflow Case Study 001

Status: recorded privacy-safe product-learning input; planning-only authority
Baseline: v0.104.0 / 0.104.0
Date: 2026-08-16
Safe source ref: `finance-cleanup-case-001`
Parent contract: `docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md`

## Purpose And Privacy Boundary

This case study generalizes a real operator-assisted financial-organization and
tax-readiness workflow into durable UAA product requirements. The source work
included private statements, account activity, entity relationships, merchant
decisions, and tax questions. None of its raw prompts, names, amounts, account
suffixes, local paths, filenames, statement text, tax positions, or generated
workbook content is reproduced here.

The case study is evidence of a user need and workflow shape. It is not evidence
that UAA currently implements financial ingestion, bookkeeping, tax treatment,
or accountant-package generation.

## Operator Job To Be Done

The operator had financial activity spread across multiple deposit accounts,
credit cards, and business entities, with personal and business spending partly
commingled. The immediate goal was not to file a return automatically. It was
to transform heterogeneous statements into a reconciled, traceable,
accountant-friendly package while the operator supplied missing context in
manageable batches.

The successful workflow was:

```text
collect statements
-> inventory accounts, periods and formats
-> extract with text parsing or OCR
-> normalize transactions with source lineage
-> reconcile every supplied statement period
-> match transfers and prevent double counting
-> suggest entity/category/treatment
-> rank ambiguity into grouped review batches
-> capture operator decisions and exceptions
-> isolate accountant-only questions
-> regenerate summaries and accountant packet
```

This is a primary UAA Finance golden path.

## What Worked

### Evidence-first intake

The workflow began by inventorying files, account titles, periods, page counts,
formats, and extraction quality. It distinguished:

- statement files from receipts and other documents;
- in-period from out-of-period material;
- complete monthly sequences from missing periods;
- machine-readable content from image-like pages requiring OCR;
- explicit account/entity ownership from ownership needing review;
- a final supplied balance from actual evidence that an account was closed.

Product lesson: source readiness and coverage must be visible before
categorization. A polished dashboard must not hide a missing statement, partial
period, extraction warning, or non-zero final supplied balance.

### Dual extraction and visual verification

Some statements appeared image-only to ordinary extraction but exposed usable
structured content through another path. OCR remained valuable as a visual
cross-check. Parsing had to accommodate different layouts, continuation lines,
date formats, signs, category headings, and multi-column pages.

Product lesson: UAA needs an adapter/parser pipeline with confidence and
diagnostics, not one universal PDF parser. Every extracted row retains a source
document and page/region ref. The operator can compare the normalized candidate
with a protected source preview.

### Reconciliation before interpretation

Every supplied account period was checked against statement totals before broad
classification. Extraction and formula errors were corrected before the package
was treated as usable. A missing closure document remained an explicit gap even
though other supplied periods reconciled.

Product lesson: reconciliation is a first-order product state. “Imported” does
not mean “complete,” and “all supplied periods reconcile” does not mean “the
year or account history is complete.” Coverage, extraction integrity,
reconciliation, and closure proof are separate statuses.

### One normalized ledger, multiple views

The output used one master transaction table with source lineage, entity and
category suggestions, final override fields, review status, and notes. Dashboard,
entity/category summaries, review queue, merchant review, reconciliation, and
source inventory were projections from that master table.

Product lesson: UAA must not make the spreadsheet the canonical database. The
protected Finance repository owns truth; registers, grouped reviews, reports,
and exports project from it. XLSX/CSV/neutral-ledger packages remain important
interoperability artifacts.

### Transfers and balance-sheet items first

The highest-risk early error was counting transfers, credit-card payments,
owner/intercompany movements, loan flows, reimbursements, or related-party
activity as ordinary income or expense.

Product lesson: the review workflow starts with candidate transfer pairs and
balance-sheet classification before deduction hunting. A proposed transfer
shows both legs, dates, amounts, accounts, entities, confidence, unmatched
differences, and the P&L consequence of accepting or rejecting it.

### Grouped review reduced an impossible queue

A large row-level review queue became tractable when recurring payees were
normalized into groups and ranked by a combination of financial impact,
frequency, ambiguity, and likely coverage. The operator could answer a compact
batch of merchant/payee questions, then apply each decision to matching
transactions while preserving exceptions.

Product lesson: UAA needs both transaction review and **Review Batches**. A
group decision is a proposed rule/ChangeSet, never a blind bulk edit. Before
commit it previews:

- affected transaction count and period;
- accounts and entities involved;
- representative source-safe examples;
- total inflow/outflow posture without exposing it outside Finance;
- proposed entity, category, transaction type, business-use percentage, and
  evidence requirement;
- exclusions, outliers, conflicts, reconciled/closed items, and historical
  reach;
- per-item consequences and rollback.

### Context was more valuable than a category alone

The useful operator decisions captured:

- which legal entity or personal owner benefited;
- what was purchased or received;
- the business purpose;
- whether and how much was personal/mixed use;
- whether the item was a transfer, loan, contribution, distribution,
  reimbursement, income, expense, refund, debt payment, or investment activity;
- whether supporting evidence existed;
- whether a professional should decide the tax treatment.

Product lesson: a one-column category picker is inadequate. Entity, book,
transaction type, category, tax treatment, allocation, purpose, evidence, and
review state are distinct fields with distinct authority.

### Accountant questions were an output, not a failure

Some questions could not be resolved safely from statements or operator intent
alone: debt principal/interest/escrow splits, depreciation, related-party
classification, business-use allocations, entity treatment, and whether an
activity met a tax-law status test. The workflow preserved facts and routed the
decision instead of forcing an answer.

Product lesson: `Ask accountant` is a successful terminal state for the current
review stage. The question includes the exact records, known facts, missing
facts, operator position, evidence, relevant period, and desired decision. It
must not encode a generated conclusion as truth.

### Desired tax outcome was not classification authority

The workflow also exposed a boundary that must be structural in UAA: an
operator may want losses, deductions, reimbursements, household costs, or
related-party activity to produce a particular tax result, but that desired
result cannot establish who incurred an expense, which entity benefited,
whether an item was ordinary/necessary, the business-use percentage, filing
status, loss availability, or deductibility.

Product lesson: UAA may record a tax-planning objective separately from facts
and route lawful alternatives for review. It must block or escalate proposals
that merely move personal/family expenses into a business, shift expenses
between people without a genuine transaction, invent a mixed-use percentage,
or treat losses as proof of business/professional status. Legitimate
reimbursements require an exact expense, entity, payer/payee relationship,
business purpose, date, amount, evidence, and applicable plan/policy posture.
Loss use, related-party treatment, filing status, basis, at-risk, passive,
business-status, dependent, and similar questions remain sourced professional
decisions.

## Friction UAA Should Remove

The session required bespoke scripts, OCR experiments, parser corrections,
workbook generation, formula debugging, visual sheet review, merchant grouping,
and back-and-forth text answers. UAA should make these normal product workflows:

- guided source intake instead of ad hoc folder inspection;
- parser/extraction diagnostics instead of opaque import success;
- persistent reconciliation state instead of workbook formulas as proof;
- grouped question batches instead of long chat enumerations;
- decision forms with entity/category/allocation/evidence fields instead of
  parsing answers from prose;
- reversible rule application instead of one-off workbook rewrites;
- accountant question objects instead of notes buried in cells;
- live packet readiness instead of regenerating a workbook to discover gaps;
- protected source previews instead of repeatedly opening statements manually.

Chat remains useful for explanation and free-form context, but structured
Finance UI owns the durable decisions.

## Required Product Surfaces

### Setup And Scope

Capture tax/accounting period, books, legal entities, entity types, ownership
context, business activities, base currency, accounting basis posture,
accountant category/template preferences, and privacy/retention choices.

### Source & Statement Inbox

Show each document/account, period coverage, format, extraction method,
duplicate posture, in/out-of-period state, account/entity binding, page count,
parse warnings, balance availability, and missing-period candidates.

### Extraction And Reconciliation Workbench

Show source totals, normalized totals, beginning/ending balances, calculated
change, difference, excluded/non-transaction sections, parser confidence,
exceptions, source preview, and re-run/rollback posture.

### Transfer And Balance-Sheet Review

Rank candidate transfers, card payments, loans, contributions/distributions,
reimbursements, refunds, and investment flows before ordinary expenses.

### Review Batches

Present ranked merchant/payee or pattern groups in batches small enough for one
focused session. Support direct structured answers, “unknown,” “needs
evidence,” “ask accountant,” and exception marking.

### Transaction Inspector

Keep source observation, normalized candidate, proposed and final accounting,
business/tax allocations, evidence, group/rule membership, history, and
accountant questions together.

### Accountant Questions

Provide open, answered, ready-to-apply, and resolved states. An answered
question proposes exact changes for operator review; it does not mutate books
silently.

### Packet Builder

Show included books/accounts/periods, source coverage, reconciliation, unresolved
items, questions, reports, ledger export, evidence manifest, exclusions,
out-of-period material, hashes, and generation receipt.

## Review Prioritization

A useful default ranking is multi-factor, not largest-dollar-only:

```text
priority = consequence + ambiguity + coverage + recency + deadline + anomaly
```

Where:

- **consequence** includes P&L, balance sheet, tax, closed-period, and entity
  impact;
- **ambiguity** includes weak payee normalization, mixed-use patterns, missing
  purpose, and conflicting prior decisions;
- **coverage** rewards a decision that can safely resolve many candidates;
- **recency** favors capturing context before it is forgotten;
- **deadline** includes close, accountant handoff, filing, and obligation dates;
- **anomaly** includes amount/frequency/entity changes and missing expected
  evidence.

The rank explanation is visible and editable. It never becomes tax authority.

## Decision State Machine

```text
unreviewed
-> needs_context | needs_evidence | ask_accountant | deferred
-> proposed
-> accepted | corrected | rejected | exception
-> posted
-> reconciled
-> closed
```

Reopening a reconciled or closed item requires an adjustment/reopen workflow.
Group decisions create versioned proposals. Exceptions remain attached to the
group so later imports do not erase them.

## Golden Acceptance Scenario

Using synthetic fixtures only, the final Finance acceptance suite must prove:

1. multiple statement formats and a mixed personal/business/entity topology;
2. one source requiring OCR and one exposing structured data;
3. a missing period, an out-of-period document, and incomplete closure proof;
4. exact source lineage for every candidate;
5. statement reconciliation with one deliberate extraction defect caught;
6. matched and unmatched transfers without P&L double counting;
7. a large ambiguous queue condensed into ranked review batches;
8. one group rule accepted, one corrected, and one exception preserved;
9. mixed-use allocation and missing-receipt workflows;
10. an unsupported blanket allocation and personal-to-business shift blocked
    while a documented exact reimbursement remains reviewable;
11. an accountant-only question that returns as a reviewed ChangeSet;
12. a reproducible accountant packet whose readiness accurately reports all
    remaining gaps;
13. the same work visible through Finance UI, Action Inbox, Today, Calendar,
    Work Board, Evidence, API, and CLI without copied truth.

## Product Metrics Learned From The Case

- source-period coverage and unbound-source count;
- extraction/reconciliation pass rate and unresolved difference;
- percent of rows carrying complete source lineage;
- transfer/card-payment match coverage and false-match correction rate;
- raw review rows versus grouped decision count;
- transactions safely resolved per accepted group decision;
- exception and rule-rollback rate;
- median age of missing context/evidence;
- accountant-question turnaround and exact application rate;
- packet readiness by source, reconciliation, classification, evidence, and
  professional-review dimensions.

These metrics use protected local aggregation and must not export raw financial
content to generic telemetry.
