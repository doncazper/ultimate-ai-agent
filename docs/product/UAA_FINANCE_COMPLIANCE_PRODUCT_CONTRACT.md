# UAA Finance & Compliance Product Contract

Status: proposed planning-only product contract; no runtime authority
Baseline: v0.104.0 / 0.104.0
Date: 2026-08-16
Program IDs: `FIN-000` through `FIN-FILE-001`
Parent plan: `docs/implementation/UAA_COHERENT_APP_ECOSYSTEM_IMPLEMENTATION_PLAN.md`
Queue placement: `docs/roadmap/UAA_FINANCE_COMPLIANCE_QUEUE_INSERTION.md`
Implementation plan:
`docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md`
Render brief:
`docs/design/control_center_north_star/renders/finance-compliance-v1/README.md`
Workflow case study:
`docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md`
Threat model: `docs/security/UAA_FINANCE_COMPLIANCE_THREAT_MODEL.md`
Storage decision:
`docs/decisions/ADR-0063-finance-protected-local-data-boundary.md`
FIN-000 matrix: `docs/product/UAA_FINANCE_FIN000_ACCEPTANCE_MATRIX.md`

## Executive Decision

UAA will build a first-party, local-first Finance & Compliance application. It
will not white-label a complete finance product. The product will combine the
best durable ideas from Actual Budget, Beancount, Copilot Money, Ramp,
QuickBooks, Keeper, and Harbor Compliance while preserving UAA's own object
ownership, governance, evidence, CLI parity, visual language, and local data
boundary.

The top-level navigation label is **Finance**. **Finance & Compliance** is the
full product/program name. “Financing” is not used because it implies obtaining
credit rather than operating books and obligations.

The product promise is:

> Keep books continuously organized, explainable, and ready for review so the
> operator and their accountant do not reconstruct the year at tax time.

UAA may prepare tax-readiness packets and filing handoffs. It must not describe
suggestions as accounting, tax, or legal advice; represent estimates as final;
or claim automatic filing before a separately accepted professional or filing
partner lane exists.

This contract adds no account connection, financial aggregation, transaction
import, receipt ingestion, compliance-data feed, tax calculation, filing,
payment, external write, provider/model call, browser automation, background
sync, multi-user access, or production authority.

## Why This Belongs In UAA

Finance is not an isolated dashboard. Financial work produces decisions,
deadlines, evidence, recurring work, questions, and plans that already belong
in the Founder Command Center loop:

```text
observe -> review -> decide -> post -> reconcile -> prepare -> hand off
              |        |          |          |
              v        v          v          v
        Action Inbox  Evidence  Calendar  Work Board / Today
```

The UAA advantage is one governed operating loop:

- a questionable transaction becomes an Action Inbox decision;
- a missing receipt becomes an evidence request and a Today item;
- a monthly close becomes a reusable Work Board;
- an estimated-tax or license date becomes a Calendar projection;
- an accountant question stays linked to the transaction and its proof;
- a reviewed categorization may propose a rule without becoming truth silently;
- the Morning Briefing can show review load, stale accounts, cash risks, and
  upcoming obligations without duplicating their canonical records.

## Product Principles

### Continuous readiness, not periodic reconstruction

Capture category, business purpose, receipt, allocation, and uncertainty while
context is fresh. The review queue should be small, comprehensible, and easy to
clear daily or weekly.

### Bookkeeping truth is stronger than a transaction feed

A bank observation is evidence that something appeared at a source. It is not
automatically a verified accounting entry. UAA keeps three layers distinct:

1. immutable source observation;
2. normalized transaction candidate and suggestions;
3. reviewed, balanced ledger entry.

### Double-entry underneath, approachable language above

Every finalized financial event posts balanced debits and credits. The default
interface uses plain terms such as account, category, transfer, split,
business/personal, receipt, and review. An advanced inspector exposes postings,
source lineage, adjustments, reconciliation, and export diagnostics.

### Suggestions must earn trust

Rules and local learning accelerate review but do not hide uncertainty. Every
suggestion carries a reason, confidence posture, source scope, and correction
path. Low-confidence or high-consequence items abstain and go to review.

### Desired outcomes do not rewrite facts

Tax-planning goals are separate from bookkeeping and tax facts. UAA cannot
classify a personal/family cost as business, shift an expense between people or
entities, invent a mixed-use percentage, or infer professional/business status
merely because the operator wants a deduction or has losses. It may identify a
documented exact reimbursement or other lawful candidate, explain missing
support, and route filing-status, basis, at-risk, passive, related-party,
business-status, dependent, and tax-treatment questions to a professional.

### Financial and compliance facts remain sourced

Balances, ledger entries, deadlines, requirements, and filing states are never
Memory facts. Memory may retain reviewed preferences such as preferred labels
or briefing cadence, but it cannot become the source of financial or legal
truth.

### Useful before connectors

The first product is manual and file-import capable. Live bank and compliance
providers arrive only after the local object model, review loop, redaction,
reconciliation, and adapter contracts are accepted.

### Designed from real cleanup work

`docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md` converts a real
multi-account, multi-entity, commingled-finance cleanup workflow into redacted
product requirements. Source inventory, extraction diagnostics, statement
coverage, reconciliation, transfer matching, grouped review batches,
accountant-only questions, and packet readiness are first-order product states,
not implementation details hidden behind a generic transaction table.

## Clean-Room Reference Synthesis

These are product lessons, not a direction to clone screens, copy proprietary
text, or import incompatible code.

| Reference | Lesson UAA keeps | UAA interpretation |
|---|---|---|
| Actual Budget | local-first ownership; import rules; schedules; reconciliation | native Python bookkeeping core, deterministic rule engine, recurring-pattern review, and explicit reconciliation sessions |
| Beancount | durable double-entry; account declarations; validation; balance assertions | balanced immutable journal entries, typed postings, assertions, reversible adjustments, and CLI-verifiable exports |
| Copilot Money | a focused “to review” inbox; per-user categorization learning; abstention | Finance review items project into Action Inbox; learning is per book, explainable, confidence-gated, and correction-driven |
| Ramp | capture receipts, memos, and accounting context at the moment of spend | immediate context/evidence requests, missing-item posture, receipt matching, and transaction-linked business purpose |
| QuickBooks | accountant/client questions attached to exact transactions; period review | transaction-linked questions, bounded accountant workspace/export, monthly close, and unresolved-item tracking |
| Keeper | approachable deduction review and stepwise tax preparation | plain-language tax-readiness checklist, source-linked potential treatments, document collection, human review, and export/handoff |
| Harbor Compliance | entity/jurisdiction inventory and maintained obligation calendar | sourced obligations with provenance, applicability, effective dates, review state, calendar projections, and licensed provider adapter later |

### License and source boundary

- Actual Budget is MIT licensed. Selective reuse is legally possible only with
  preserved notices and dependency/security review; the preferred path is a
  UAA-native Python implementation of the learned patterns.
- Beancount is GPL-2.0-only. UAA may learn accounting concepts and public
  behavior, but must not copy or adapt GPL implementation code into the MIT
  repository without a separately approved legal and architecture decision.
- Copilot, Ramp, QuickBooks, Keeper, and Harbor are proprietary references.
  Benchmark observable capabilities and outcomes; do not copy code, protected
  assets, product text, datasets, or distinctive screen composition.
- Harbor requirement data is maintained commercial content. UAA must not scrape
  or reproduce it. A future feed requires a license, contract, data provenance,
  freshness policy, and safe-disable behavior.

## Canonical Ownership

| Concern | Canonical owner | Finance behavior |
|---|---|---|
| books, accounts, source observations, candidates, journal entries, postings, classifications, reconciliations, tax-readiness state | Finance | owns truth and history |
| legal entities, jurisdictions, obligations, filing instances, source citations | Finance & Compliance | owns applicability and review state |
| pending human decisions | Action Inbox | projects a Finance decision envelope; does not own the transaction |
| dates and reminders | Calendar | projects an obligation, close date, or recurring payment; does not own the source record |
| multi-step close, return, renewal, or cleanup work | Work Board / Plans | projects linked work; individual transactions do not become cards |
| receipts, statements, citations, accountant messages, reconciliation proofs | Evidence | stores protected artifacts or safe refs under the sensitive-data policy |
| daily priority | Today / Briefing | ranks projections; does not copy Finance state |
| reviewed preferences | Memory | may retain preference refs; never stores balances, filings, deadlines, or tax conclusions as truth |
| regulatory reporting | News | creates untrusted source candidates; never silently changes an obligation |

Cross-surface records use stable refs and typed projections. A decision in
Action Inbox resolves through the Python core and produces the same receipt
available to CLI inspection. React state may hold only presentation choices.

## Core Lifecycle And Invariants

```text
SourceObservation
  -> TransactionCandidate
  -> TransferCandidate / ReviewBatch / ClassificationSuggestion
  -> ReviewDecision / AccountantQuestion
  -> JournalEntry + balanced Postings
  -> ReconciliationSession
  -> PeriodClose / TaxReadinessPacket / AccountantExport
```

Required invariants:

- source observations are immutable and deduplicated by provider/file identity
  plus bounded fingerprints;
- candidate normalization never destroys the original description or source
  lineage;
- every posted journal entry balances by commodity and book policy;
- transfers link both sides and do not inflate income or expense;
- splits and business-use allocations preserve amounts exactly;
- finalized corrections use reversal or adjusting entries rather than silent
  history rewriting;
- reconciled periods cannot be changed without an explicit reopen/adjustment
  workflow and receipt;
- every classification records actor, reason/rule, confidence posture, time,
  prior state, resulting state, and evidence refs;
- tax treatments remain distinct from bookkeeping categories;
- compliance obligations include source, jurisdiction, entity, applicability,
  effective/freshness dates, confidence, and reviewed/contested state;
- calendar and board records are projections and remain traceable to their
  owning Finance object.

## Domain Model

The minimum durable model is:

- `Book`: accounting boundary, base currency, basis, fiscal year, and policy;
- `LegalEntity`: person, sole proprietorship, LLC, corporation, partnership,
  nonprofit, or other reviewed entity type;
- `JurisdictionProfile`: applicable federal, state/province, county, city, or
  other jurisdiction refs with source posture;
- `TaxContextProfile`: period-scoped operator-supplied filing/relationship,
  ownership, business activity, accounting, and planning facts plus source and
  professional-review posture; it is context, never a tax conclusion;
- `FinancialAccount`: bank, credit union, cash, credit card, vehicle loan,
  mortgage, personal loan, line of credit, asset, liability, income, expense,
  equity, tax, or suspense account;
- `SourceDocument` and `StatementPeriod`: protected file ref, account/period
  binding, extraction method/version, page coverage, balances/totals, coverage,
  duplicate, in/out-of-period, parse, reconciliation, and closure-proof posture;
- `SourceObservation`: immutable imported or manually captured source record;
- `TransactionCandidate`: normalized, deduplicated, reviewable observation;
- `TransferCandidate`: proposed relationship between two or more observations
  with amount/date/account/entity matching, difference, and P&L consequence;
- `JournalEntry` and `Posting`: balanced accounting truth;
- `ClassificationSuggestion`: proposed payee, category, transfer, split,
  entity, tax treatment, business use, and explanation;
- `ReviewDecision`: accept, correct, reject, defer, split, link transfer,
  request context, attach evidence, or propose rule;
- `ReviewBatch`: ranked, versioned merchant/payee/pattern group with affected
  refs, examples, conflicts, exceptions, proposed ChangeSet, and rollback;
- `LearnedRule`: deterministic, versioned, scoped, testable rule with examples,
  exclusions, conflicts, rollback, and operator approval;
- `EvidenceAttachment`: protected receipt/statement/document ref and matching
  metadata;
- `RecurringPattern`: detected or operator-defined schedule, never an assumed
  future posting;
- `ReconciliationSession`: statement range, target balance, cleared postings,
  difference, exceptions, close receipt, and reopen posture;
- `ComplianceObligation`: sourced requirement, applicability, cadence, dates,
  owner, status, evidence, and review freshness;
- `FilingInstance`: one occurrence of an obligation and its lifecycle;
- `AccountantQuestion`: exact object-linked question, response, requested
  evidence, due date, and resolution state;
- `TaxReadinessPacket`: period-scoped checklist, unresolved issues, source refs,
  reports, and export manifest;
- `ExportPacket`: reproducible accountant or filing handoff with schema version,
  content manifest, hashes, generation receipt, and deletion/retention posture.

## Review And Learning Contract

The Finance review queue supports:

- confirm or change category and payee;
- mark personal, business, mixed use, reimbursement, transfer, refund, income,
  debt principal, interest, fee, or tax payment;
- split by amount, percentage, entity, project, client, property, or tax
  treatment;
- add business purpose and participants;
- attach, replace, or mark missing evidence;
- merge duplicated observations or pair transfer legs;
- ask the operator or accountant a transaction-linked question;
- approve, revise, or reject a proposed rule;
- defer with a reason and next-review date.

The queue has transaction and grouped **Review Batch** modes. Groups are ranked
by consequence, ambiguity, safe coverage, recency, deadline, and anomaly. A
group answer proposes a versioned ChangeSet across matching candidates; it
previews affected records, entities, periods, exclusions, outliers, closed or
reconciled items, evidence gaps, conflicts, historical reach, and rollback.
One accepted group decision may resolve many records, but every transaction
retains its own final state, receipt, source lineage, and exception posture.

The default structured questions are: which entity benefited; what was
purchased or received; what was the business purpose; what portion was
personal; what transaction type applies; what evidence exists; and whether a
professional decision is required. `Unknown`, `needs evidence`, and `ask
accountant` are valid outcomes rather than invitations to guess.

Learning order:

1. explicit operator rules;
2. deterministic normalized-payee and exact/partial match rules;
3. repeated-correction rule proposals with examples and exceptions;
4. a local per-book classifier only after an accepted evaluation and privacy
   milestone;
5. no model suggestion when confidence, data sufficiency, or consequence gates
   fail.

No rule is created from one ambiguous correction. A rule proposal previews the
records it would affect, conflicts, estimated coverage, and rollback. Historical
application is a separate exact ChangeSet. No training signal crosses books,
entities, privacy workspaces, or users.

## Product Surfaces

### Setup And Source Readiness

The first-run workflow captures books, entities, business activities, period,
accounting posture, accountant preferences, and privacy choices. Source &
Statement Inbox inventories files/accounts, periods, extraction method, page
coverage, duplicates, in/out-of-period state, ownership binding, parse warnings,
available balance evidence, missing periods, and closure gaps before broad
classification begins.

### Finance Command View

The home view shows current review load, account freshness, cash posture,
unreconciled periods, missing evidence, upcoming obligations, recurring
changes, and tax-readiness gaps. It prioritizes work, not vanity charts.

### Transactions And Review

A dense, keyboard-friendly register and review inbox support search, saved
views, bulk proposals, splits, transfers, receipts, business purpose, rules,
and a source/posting inspector. Bulk work never hides per-item consequences.
Review Batches condense high-volume ambiguity into small ranked sets of
merchant/payee, transfer, or recurring-pattern decisions with explicit
exceptions.

### Books And Accounts

The operator manages books, entities, chart of accounts, opening balances,
statements, reconciliation, period close, import/export, backup, and restore.
The reconciliation workbench distinguishes import success, source coverage,
extraction integrity, statement balance proof, supplied-period reconciliation,
and actual account-closure evidence.

### Spending And Planning

Reports cover cash flow, income/expense, category, merchant, entity, project,
client, property, recurring spend, debt, and budget/forecast variance. Forecasts
are visibly distinct from posted facts.

### Tax Readiness And Accountant

A year/period workflow organizes documents, unresolved treatments, questions,
deduction candidates, estimated-payment records, reconciliations, and export
packets. “Ready” means the configured checklist is satisfied; it never means a
return is legally correct or filed.

Transaction-linked accountant questions are a deliberate workflow. They carry
known facts, missing facts, evidence, operator position, desired decision, and
affected records. A reply produces a proposed exact ChangeSet for operator
review rather than silently altering the books.

### Compliance

Entity and jurisdiction views show obligations, source citations, applicability,
freshness, owners, filing instances, Calendar projections, and evidence. Manual
obligations come first; a licensed maintained feed comes later.

## Cross-Surface Behavior

- **Today:** high-value reviews, stale accounts, urgent evidence gaps, cash
  risks, and upcoming obligations.
- **Morning Briefing:** bounded counts, changes since last review, due items,
  reconciliation posture, and links into owning records.
- **Action Inbox:** classification, transfer pairing, receipt/context request,
  split, rule approval, reconciliation exceptions, accountant questions, and
  obligation review.
- **Calendar:** estimated taxes, renewals, reports, recurring payments, close
  dates, and filing windows as typed projections with source/freshness state.
- **Work Board / Plans:** reusable Monthly Close, Tax Return, License Renewal,
  Debt Paydown, and Finance Cleanup templates.
- **Evidence:** receipts, statements, source citations, correspondence,
  reconciliations, exports, and approval receipts.
- **Memory:** reviewed preferences only; never financial or compliance truth.
- **News:** relevant changes may propose a source review; they cannot mutate an
  obligation.
- **Chat:** explain records, compare scenarios, prepare proposals, and navigate;
  it cannot post, file, pay, or decide silently.
- **Settings:** books, entities, categories, rules, connector posture, exports,
  retention, privacy, and future accountant access.

## Sensitive Data Boundary

Raw financial and compliance content belongs in a dedicated protected local
data plane. Generic logs, product analytics, documentation, screenshots, test
fixtures, Evidence Timeline summaries, API posture views, and CLI default
output contain safe refs, synthetic data, bounded aggregates, and redacted
summaries only.

Required controls before implementation acceptance include:

- encryption at rest and a documented key lifecycle;
- separate book/entity/workspace access boundaries;
- no raw transaction descriptions, account/routing numbers, tax identifiers,
  statements, receipts, addresses, or filings in ordinary logs or fixtures;
- backup, restore, migration, retention, deletion, and export threat models;
- explicit accountant packet creation and revocation/expiry posture;
- connector credentials represented only by opaque handles;
- source payload quarantine, schema validation, deduplication, replay defense,
  and safe-disable;
- no provider data used for cross-user training or unrelated model context.

An accountant export is an explicit operator artifact, not an operational log
or ordinary UAA evidence record.

## Non-Goals And Denied Claims

The initial product does not:

- replace a CPA, bookkeeper, attorney, payroll system, tax engine, registered
  agent, lender, bank, or compliance professional;
- initiate payments, transfers, loan payments, filings, signatures, or legal
  attestations;
- offer credit, underwriting, debt settlement, investment trading, custody,
  payroll, invoicing, bill pay, or card issuing;
- silently infer entity choice, nexus, filing obligations, deductibility, tax
  position, or legal compliance;
- move personal/family expenses into a business, shift expenses between people
  or entities, invent allocations, or classify activity to manufacture a
  preferred tax result without supportable facts and evidence;
- treat imported data, news, Memory, classifier output, or generated text as
  verified truth;
- promise every institution, jurisdiction, entity type, or tax form at launch;
- display fake Connect, File, Pay, Submit, Sync, or Invite controls.

## Acceptance Bar

Finance becomes a first-class implemented app only when:

- manual/file-import books remain useful without a connector;
- the double-entry core, source/candidate/ledger separation, and reversals are
  tested through Python and inspectable through CLI;
- Action Inbox, Calendar, Today, Work Board, Evidence, and Memory ownership
  boundaries are verified;
- review, rules, learning, reconciliation, and export are explainable and
  recoverable;
- the redacted golden scenario in
  `docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md` passes with synthetic
  multi-format, multi-account, multi-entity fixtures;
- synthetic north-star renders and empty/degraded/error states are accepted;
- security, privacy, backup/restore, redaction, accessibility, keyboard,
  performance, and migration gates pass;
- every provider or professional lane remains exact-scoped and truthfully
  labeled implemented, partial, blocked, configuration-required, or missing.

## Reference Baseline

Public capability references reviewed for this contract:

- Actual Budget: [rules](https://actualbudget.org/docs/budgeting/rules/),
  [schedules](https://actualbudget.org/docs/schedules/),
  [reconciliation](https://actualbudget.org/docs/accounts/reconciliation/), and
  [MIT license](https://github.com/actualbudget/actual/blob/master/LICENSE.txt)
- Beancount: [getting started and validation](https://beancount.github.io/docs/getting_started_with_beancount/)
  and [GPL-2.0 repository](https://github.com/beancount/beancount)
- Copilot: [review-trained spending categorization](https://help.copilot.money/en/articles/8182433-copilot-intelligence-for-spending)
  and [name rules](https://help.copilot.money/en/articles/3971270-creating-name-rules)
- Ramp: [receipt, memo, and accounting-context capture](https://support.ramp.com/submitting-receipts-memos-and-accounting-for-your-ramp-transactions/)
- QuickBooks: [transaction-linked information requests](https://quickbooks.intuit.com/learn-support/en-us/help-article/intuit-assist/request-information-transaction/L8ZXmgZYM_US_en_US)
- Keeper: [deduction review](https://help.keepertax.com/hc/en-us/articles/19969104622615-Web-Dashboard-Deductions)
  and [guided filing workflow](https://help.keepertax.com/hc/en-us/articles/19969146156951-Web-Dashboard-File-Taxes)
- Harbor Compliance: [developer/API boundary](https://developers.harborcompliance.com/)
  and [entity/obligation management](https://www.harborcompliance.com/entity-manager-software)

These links are research inputs, not endorsements, dependencies, or runtime
authority.
