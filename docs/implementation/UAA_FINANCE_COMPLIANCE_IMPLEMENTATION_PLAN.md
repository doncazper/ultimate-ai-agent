# UAA Finance & Compliance Implementation Plan

Status: proposed planning-only implementation program
Baseline: v0.104.0 / 0.104.0
Date: 2026-08-16
Product contract: `docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md`
Workflow case study: `docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md`
Queue placement: `docs/roadmap/UAA_FINANCE_COMPLIANCE_QUEUE_INSERTION.md`
Threat model: `docs/security/UAA_FINANCE_COMPLIANCE_THREAT_MODEL.md`
Storage decision:
`docs/decisions/ADR-0063-finance-protected-local-data-boundary.md`
FIN-000 matrix: `docs/product/UAA_FINANCE_FIN000_ACCEPTANCE_MATRIX.md`
Parent program:
`docs/implementation/UAA_COHERENT_APP_ECOSYSTEM_IMPLEMENTATION_PLAN.md`

## Implementation Decision

Build a UAA-native Finance & Compliance module. Do not white-label a full
ledger product. Do not begin with live financial connections. Establish the
local accounting truth, review loop, evidence boundary, and cross-app ownership
first; promote each external read or professional handoff as a separate exact
lane later.

The execution shape is:

```text
FIN-000 contract + threat model + founder-accepted private-dogfood direction
        |
        v
shared ecosystem foundations through ECO-008
        |
        v
FIN-001..FIN-008 local books, review, evidence, reconciliation and readiness
        |
        v
ECO-009 exact read-only connector platform
        |
        +--> FIN-CONN-001 one financial read adapter
        +--> COMP-CONN-001 one licensed compliance read adapter
        |
        v
accountant collaboration -> optional professional filing handoff
```

This plan grants no runtime behavior or authority.

## Dependency Gate

Implementation does not become the active product lane until:

- `ECO-001` shared local data, key, migration, backup, and protected-data
  boundaries are accepted;
- `ECO-003` first-class Boards/Kanban ownership and migration are accepted;
- `ECO-004` Calendar projections and source ownership are accepted;
- `ECO-006` Today/Briefing and `ECO-007` Inbox/source-artifact workbench
  contracts are stable;
- `FCC-INBOX-001` Action Inbox and approval-envelope UX is stable;
- `ECO-008` cross-app ChangeSets, receipts, conflicts, and undo are accepted;
- the current Founder Loop/Action Inbox priority remains healthy and the board
  explicitly promotes the Finance lane.

`FIN-000` planning and render work may proceed before those runtime gates. It
cannot displace the active Founder Command Center implementation spine.

## Work Packages

### `FIN-000` Product contract, threat model, and render acceptance

Planning evidence is indexed in
`docs/product/UAA_FINANCE_FIN000_ACCEPTANCE_MATRIX.md`. The founder accepted
the displayed render direction for private dogfooding; the independent render
checklist remains pending and cannot be represented as promotion evidence.

Deliver:

- accepted product contract and canonical ownership matrix;
- security/privacy threat model for financial, tax, identity, receipt, export,
  backup, and connector data;
- architecture decision for protected local finance storage and keys;
- versioned schema and migration strategy;
- typed adapter boundaries with all providers disabled;
- synthetic desktop/narrow render pack for the twelve required surfaces;
- accessibility, keyboard, empty, loading, degraded, conflict, and recovery
  state matrix;
- parity scorecard for the seven reference products and explicit clean-room
  exclusions.
- accepted privacy-safe workflow requirements and synthetic golden scenario
  derived from `docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md`.

Exit: reviewers can tell what UAA will build, what owns each record, what is
blocked, how failure is recovered, and how every screen fits UAA. No runtime is
added.

### `FIN-001` Protected local book and double-entry kernel

Founder private-dogfood direction acceptance clears the FIN-000 visual
prerequisite for this bounded package. The activation record merged and the
coordinator claimed `dev-task:finance-fin001-synthetic-kernel` at revision 164.
The implementation provides the contracts, deterministic fixture, protected
repository, exact authority gate, and bounded CLI described in
`docs/product/UAA_FINANCE_FIN001_SYNTHETIC_KERNEL.md`. PR 428 merged the exact
candidate after all hosted checks and clean exact-head review, and Queue V2
recorded completion and its terminal packet at revision 166. The decision does not
authorize persistent real financial data, a connector, advice, filing, or
professional-readiness claims. Those remain behind independent promotion and
their exact later capability gates.

Deliver:

- `Book`, `LegalEntity`, `FinancialAccount`, `JournalEntry`, and `Posting`
  contracts;
- balanced-posting validation by commodity;
- opening balance, transfer, split, reversal, adjustment, and suspense flows;
- append-oriented event/history model with optimistic concurrency;
- local protected repository, migrations, fixtures, backup/restore proof, and
  safe-delete posture;
- a versioned allowlist of deterministic fixture refs; all arbitrary
  operator-supplied financial values fail closed before persistence;
- CLI create/inspect/check/export parity with current PolicyEngine decision,
  exact LocalApprovalAuthority, and an active
  `capability-ref:finance/FIN-001/synthetic-book-mutation` AuthorityLease
  with an exact Finance-owned authority binding and revalidation
  immediately before persistence, plus revision, idempotency, audit-receipt,
  request-ref uniqueness, canonical path binding, owner-private cross-process
  serialization, crash-recoverable generation commits, retryable
  tombstone-first delete, and rollback binding for every local mutation;
  coarse generic leases and
  denied, unknown, or stale policy, approval, and expired or revoked leases
  fail closed, and imports remain FIN-002;
- API manifest, OpenAPI, side-effect classification, policy, approval,
  idempotency, receipt, and rollback coverage where routes later exist.

Exit evidence: a synthetic local book can be created, validated,
redacted-exported, backed up, restored, and cryptographically deleted without
the UI or any connector. Protected merge and Queue V2 disposition evidence are
recorded; this does not activate FIN-002 or real-data handling.

### `FIN-002` Manual capture and file import pipeline

Deliver:

- manual transaction capture;
- versioned CSV/OFX/QFX/QIF import profiles as separately reviewed parsers;
- protected source/statement inventory with account/entity binding, period
  coverage, page count, duplicates, in/out-of-period posture, missing-period
  candidates, balance evidence, and closure gaps;
- versioned PDF extraction adapters with text/structured parsing first and a
  separately reviewed local OCR fallback, protected source-region previews,
  parser confidence, and diagnostics;
- immutable `SourceObservation` and normalized `TransactionCandidate`;
- source fingerprinting, deduplication, transfer candidates, replay defense,
  quarantine, bounded failures, and import preview;
- mapping templates and safe import rollback;
- synthetic fixture corpus with malformed and adversarial files.

Exit: an operator can import a statement, preview consequences, reject or
commit the import, and trace every candidate to source without losing raw
lineage. “Imported,” “extracted,” “source period complete,” “reconciled,” and
“account closure proven” remain distinct states. Format support must be
truthfully listed rather than implied.

### `FIN-003` Review inbox, rules, and learning loop

Deliver:

- Finance review read model and Action Inbox projections;
- confirm, correct, reject, defer, transfer-link, split, allocate, and request
  context decisions;
- deterministic rule engine with ordered conditions/actions, examples,
  exclusions, conflicts, versioning, preview, and rollback;
- repeated-correction rule proposals;
- per-book learning-evaluation harness and abstention thresholds before any
  local classifier is accepted;
- explanation and confidence posture on every suggestion;
- bulk proposals that retain exact per-item consequences and receipts.
- ranked `ReviewBatch` groups for normalized merchants/payees, transfer
  candidates, and recurring patterns using consequence, ambiguity, safe
  coverage, recency, deadline, and anomaly;
- structured entity, transaction type, category, tax treatment, business-use,
  purpose, evidence, status, and notes decisions with `unknown`, `needs
  evidence`, and `ask accountant` states;
- group ChangeSet preview with affected refs, representative safe examples,
  exclusions, outliers, conflicts, reconciled/closed items, exceptions,
  historical reach, and rollback.
- tax-integrity guardrails that keep desired outcomes separate from facts,
  block unsupported personal/family-to-business or cross-person/entity shifts
  and invented blanket allocations, and allow only exact evidenced
  reimbursement/allocation proposals or professional-review escalation.

Exit: repeated decisions become reviewable automation, low-confidence items
abstain, and corrections never silently rewrite posted or reconciled history.

### `FIN-004` Receipt, context, and evidence capture

Deliver:

- protected receipt/statement/document refs;
- transaction matching with operator confirmation and duplicate handling;
- missing receipt, memo, business purpose, participant, project/client/property,
  and business-use requirements;
- mobile/narrow capture contract and local file/photo ingestion posture;
- Evidence Timeline safe summaries and protected artifact access boundary;
- retention, replacement, deletion, export, and orphan-recovery behavior.

Exit: the operator can complete transaction context while it is fresh and can
prove what evidence supports a posting without leaking raw content into logs.

Email forwarding, OCR/provider calls, mobile background capture, and merchant
retrieval remain separately gated.

### `FIN-005` Reconciliation, recurring patterns, and period close

Deliver:

- statement-based reconciliation sessions, cleared/uncleared posture,
  difference diagnosis, exception queue, close, and governed reopen;
- separate source-period coverage, extraction integrity, statement
  reconciliation, and documentary account-closure proof;
- recurring-pattern detection and operator-confirmed schedules;
- debt principal/interest/fee handling and payment schedules;
- month/quarter/year close checklists and Work Board templates;
- balance assertions, stale-account detection, and closed-period controls.

Exit: a period can be reconciled and closed with a reproducible receipt and
cannot be silently altered afterward.

### `FIN-006` Cross-surface Founder Loop integration

Deliver:

- Today and Morning Briefing projections;
- Calendar saved view for obligations, recurring payments, and closes;
- Action Inbox envelopes for review, evidence, rules, exceptions, and questions;
- Work Board templates for Monthly Close, Tax Readiness, License Renewal, Debt
  Paydown, and Cleanup;
- Chat explain/navigation/proposal contracts;
- Memory exclusion tests and approved-preference-only intake;
- source-linked regulatory News candidate path that cannot mutate obligations.

Exit: one canonical Finance object is visible and actionable across UAA without
copying truth or allowing a shell to mint authority.

### `FIN-007` Reports, spending intelligence, and planning

Deliver:

- cash flow, profit/loss, balance sheet, income/expense, category, merchant,
  entity, project/client/property, debt, recurring spend, and evidence-completeness
  reports;
- budgets, forecasts, scenarios, and variance views separated visibly from
  posted facts;
- exact report lineage, as-of date, accounting basis, book, currency, filters,
  and completeness posture;
- exportable reconciliations and audit trail.

Exit: every number is reproducible from ledger postings or labeled projection
inputs; generated summaries never substitute for reports.

### `FIN-008` Tax readiness and accountant packet

Deliver:

- tax-year/period readiness checklist;
- potential treatment/deduction review kept separate from book categories;
- estimated-payment records and reminders without payment execution;
- unresolved-treatment and missing-document queues;
- transaction-linked accountant questions;
- known/missing fact summaries, evidence refs, operator position, desired
  decision, answer state, and reviewed exact ChangeSet application for each
  accountant question;
- reproducible accountant packet with schema, manifest, hashes, reports,
  attachments, unresolved items, and retention/delete controls;
- CSV and a durable neutral ledger export; compatibility exports are evaluated
  separately and truthfully.

Exit: an operator can give an accountant a coherent, scoped, reproducible
packet. UAA still does not assert that the books or return are professionally
approved.

### `COMP-001` Manual compliance obligation registry

Deliver:

- entity and jurisdiction profile;
- manual obligation and filing-instance capture;
- official-source citation, retrieval/as-of date, applicability rationale,
  effective date, freshness, owner, due-window, recurrence, status, and evidence;
- Calendar, Today, Action Inbox, and Work Board projections;
- contested/unknown/expired-source posture and periodic source review.

Exit: obligations are useful and auditable without pretending UAA maintains a
nationwide legal dataset.

### `FIN-CONN-001` First exact read-only financial adapter

Starts only after `ECO-009` and a separate provider decision.

Deliver for one named provider and one bounded capability set:

- explicit institution/account enrollment and revocation;
- opaque credential handles and provider isolation;
- accounts, balances, and transaction observations only;
- bounded history, pagination, cursor/checkpoint, duplicate, replay, outage,
  stale, revoked, institution-reconnect, and data-deletion behavior;
- provider field mapping, source lineage, rate limits, cost limits, kill switch,
  safe-disable, and reconciliation;
- policy, approval, CLI/API inspection, audit, redaction, contract fixtures, and
  provider-sandbox evidence.

No transfer, payment, account modification, lending, trading, or statement of
universal institution coverage is implied.

### `COMP-CONN-001` First licensed compliance data adapter

Starts only after `COMP-001`, `ECO-009`, legal/commercial review, and a named
licensed provider.

Deliver:

- source license and allowed-use record;
- entity/jurisdiction query boundaries;
- source version, retrieved/effective dates, coverage, confidence, and freshness;
- proposed-obligation diff into Action Inbox;
- no silent overwrite of reviewed obligations;
- outage, stale data, contradiction, source retirement, safe-disable, and
  retention behavior.

### `FIN-CPA-001` Accountant collaboration

Starts only after `FIN-008` and a multi-party data/access threat model.

Deliver exact-scoped invitation/access, transaction-linked questions, requested
documents, review status, export/import or portal boundary, expiry/revocation,
activity receipts, and data deletion. Shared access does not create accounting
authority and is not a general multi-user platform grant.

### `FIN-FILE-001` Professional preparation or filing handoff

Optional and last. Starts only through a separately accepted partner, legal,
security, support, consent/signature, identity, payment, error/rejection,
amendment, audit, retention, revocation, and incident-response program.

The default posture remains export to an accountant. No generic “File” button
may appear before this exact lane is implemented and independently accepted.

## Surface Delivery Sequence

1. local book/setup and synthetic demo;
2. Source & Statement Inbox plus extraction diagnostics;
3. reconciliation workbench and transfer review;
4. transactions/register, Review Batches, and decision forms;
5. transaction/evidence inspector;
6. reconciliation close and governed reopen;
7. Finance Command View and spending reports;
8. Today, Action Inbox, Calendar, and Work Board projections;
9. tax readiness, accountant questions, and packet builder;
10. compliance registry;
11. one read-only financial adapter;
12. one licensed compliance adapter;
13. accountant collaboration;
14. optional filing handoff.

Desktop and narrow states ship per milestone. The implementation cannot defer
accessibility, keyboard behavior, loading/empty/error/recovery states, or CLI
parity until a final polish phase.

## Verification Matrix

Each runtime milestone must include, as applicable:

- domain invariant/property tests for balanced postings, exact amounts,
  transfers, splits, reversals, and closed periods;
- repository migration, backup/restore, deletion, corruption, and concurrency
  tests;
- parser fixtures, deduplication, replay, malformed input, and import rollback;
- multi-format source inventory, extraction diagnostics, local OCR fallback,
  page/region lineage, missing-period, out-of-period, and incomplete-closure
  fixtures;
- policy, approval, idempotency, receipt, redaction, and rollback tests;
- OpenAPI operation ID, manifest, route classification, and CLI parity checks;
- cross-surface ownership and projection tests;
- the thirteen-step synthetic golden scenario in
  `docs/product/UAA_FINANCE_WORKFLOW_CASE_STUDY_001.md`;
- suggestion precision/coverage/abstention evaluation on synthetic labeled
  corpora with no cross-book leakage;
- accessibility, keyboard, responsive layout, empty/degraded/error/recovery,
  and performance evidence;
- provider contract/sandbox tests only for the exact enabled adapter;
- documentation integrity, Foundation Gate, and truthful product-language
  checks.

## Product Metrics

Metrics must use protected local aggregation or synthetic evaluation. Candidate
measures include:

- median and p95 age of unreviewed candidates;
- percent reviewed before 7, 30, and 90 days;
- missing-evidence rate by policy;
- rule acceptance, correction, false-positive, and rollback rates;
- classifier precision, coverage, and abstention by book, never raw examples;
- unreconciled-account age and close duration;
- number of unresolved accountant questions;
- readiness checklist completion and days before target handoff;
- stale or unsourced compliance obligations;
- projection drift or orphan count across UAA surfaces.

No product metric may become an authority shortcut or export raw financial
content.

## Definition Of Done

The full program is not done until a new operator can create or import a book,
keep it current through the review loop, reconcile and close a period, preserve
receipts and context, understand spending, prepare an accountant packet, track
sourced obligations, recover from failures, and inspect the same truth through
UI, API, and CLI—with external capabilities labeled exactly and no silent
authority.
