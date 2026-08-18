# UAA Finance & Compliance Threat Model

Status: accepted planning boundary for FIN-000; no runtime authority
Baseline: v0.104.0 / 0.104.0
Date: 2026-08-18
Product contract: `docs/product/UAA_FINANCE_COMPLIANCE_PRODUCT_CONTRACT.md`
Storage decision: `docs/decisions/ADR-0063-finance-protected-local-data-boundary.md`
Acceptance matrix: `docs/product/UAA_FINANCE_FIN000_ACCEPTANCE_MATRIX.md`

## Scope

This threat model defines the security and privacy boundary for the proposed
local-first Finance & Compliance product. It covers financial, tax, identity,
receipt, statement, export, backup, accountant-handoff, and future connector
data. It does not implement a store, parser, route, connector, model call,
payment, filing, or professional workflow.

Every future implementation slice must retain the workspace invariants:
Python Core owns truth and authority; the CLI and Control Center use the same
contracts; policy, exact approval, AuthorityLease, idempotency, audit,
redaction, rollback or safe-disable, OpenAPI, and Foundation Gate checks remain
hard boundaries. Promotion of one exact lane grants no adjacent authority.

## Protected Assets

- books, legal entities, jurisdictions, accounts, balances, observations,
  candidates, journal entries, postings, reconciliations, and close state;
- transaction descriptions, merchant/payee data, allocations, business purpose,
  tax treatments, accountant questions, and professional responses;
- statements, receipts, tax forms, filings, addresses, identifiers, account and
  routing numbers, document regions, extraction output, and source metadata;
- compliance obligations, applicability rationales, effective dates, source
  citations, contested state, and filing instances;
- encryption keys, credential handles, adapter account refs, approval refs,
  idempotency refs, audit receipts, backups, exports, and deletion tombstones.

Raw protected content belongs only in the dedicated encrypted Finance data
plane or an explicit encrypted export. Governance records contain safe refs,
hashes, bounded counts, posture, reason codes, and redacted summaries.

## Trust Boundaries

1. Operator input and imported files are untrusted until type, size, schema,
   archive, content, duplication, book/entity, and source-period checks pass.
2. The protected Finance repository owns canonical financial truth. React,
   Memory, News, Chat, model output, previews, fixtures, and provider payloads do
   not.
3. Keychain stores opaque key or credential material. Durable Finance records,
   APIs, CLI output, logs, receipts, tests, screenshots, and backups never store
   raw secrets.
4. Evidence stores protected artifacts or protected refs. Ordinary evidence
   timelines and telemetry receive content-free summaries only.
5. Accountant packets and backups are explicit artifacts with independent
   manifests, keys, retention, expiry, revocation, and deletion posture.
6. Every future external adapter is disabled by default and separately scoped.
   Provider integration is not execution authority.

## Threats And Required Controls

| Threat | Consequence | Required control before implementation acceptance |
|---|---|---|
| Oversized, malformed, encrypted, recursive, or adversarial import | resource exhaustion, parser escape, corrupted book | bounded streaming, archive/member/page limits, parser isolation where warranted, quarantine, deterministic failure codes, synthetic adversarial fixtures |
| Source substitution or replay | wrong statement or duplicate observation becomes truth | content fingerprint, source/account/period binding, idempotency, duplicate posture, immutable observation, pre-commit revalidation |
| Cross-book, entity, person, or workspace confusion | private data disclosure or incorrect posting | canonical scoped refs, repository-level partition checks, explicit projection contracts, deny-by-default joins and exports |
| Suggestion or desired outcome overwrites facts | fabricated accounting or tax position | raw fact -> candidate -> suggestion -> human decision -> balanced posting, abstention, evidence requirements, professional-review states |
| Unbalanced, rounded, or silently rewritten entries | inaccurate books and reports | commodity-balanced postings, exact decimal policy, reversals/adjustments, append-oriented history, close/reopen controls |
| Reconciled or closed state mutates silently | lost audit integrity | optimistic revision binding, explicit reopen/adjustment, exact ChangeSet preview, receipts, rollback or compensating entry |
| Raw content leaks through logs, analytics, screenshots, errors, fixtures, or generic Evidence | privacy and credential exposure | deny raw sinks, safe refs, synthetic fixtures, bounded error codes, secret/path scans, screenshot review, no raw payload telemetry |
| Local multi-user or backup disclosure | plaintext financial corpus exposure | encrypted store and WAL/temp/indexes, owner-only permissions, device-only key handling, encrypted backups, lock-on-key-loss posture |
| Key loss, rotation failure, or migration interruption | unreadable or silently reset books | versioned key refs, staged migration, integrity verification, retained rollback generation, explicit unrecoverable state, never create a fresh store as success |
| Export or accountant packet escapes intended scope | broad disclosure or stale professional review | exact inclusion manifest, exclusions, hashes, expiry, retention/delete posture, visible unresolved items, separate export key |
| Connector token or account mix-up | unauthorized reads or writes | opaque credential handles, exact account/provider/capability binding, consent, lease, freshness, revocation, safe-disable, no React access |
| Stale or unlicensed compliance data | missed or false obligation | licensed or official-source provenance, as-of/effective dates, applicability review, contested/expired states, no silent mutation from News |
| Prompt injection in receipts, statements, notes, or source pages | untrusted content drives action | treat source text as data, never instructions; no automatic model context; cited bounded context only under a later exact lane |
| Approval revocation race or duplicate start | mutation after authority ended | serialize final approval/lease revalidation with durable start, at-most-once idempotency claim, terminal/unknown outcome posture |
| Local database tampering or rollback | false balances or hidden history | content-addressed manifests, append-oriented audit, integrity checks, backup generation refs, tamper-visible startup failure |
| Broad delete, payment, filing, or professional-access control appears early | irreversible or regulated effect | controls remain absent or visibly blocked until separately accepted exact lanes with consequence preview and proof |

## Data Lifecycle

### Intake and quarantine

Imports start outside canonical truth. A future parser records a protected
source ref, type/version, bounded fingerprint, account/entity/period binding,
coverage, excluded regions, confidence, warnings, and failure posture. Parser
output remains a candidate until an exact reviewed commit.

### Canonical storage

The repository follows ADR-0063. Every record has a schema version, canonical
owner, book/entity/workspace scope, revision, provenance, created/updated actor
refs, and retention class. Source observations are immutable. Corrections use
new decisions and balanced reversals or adjustments.

### Retrieval and projection

Today, Calendar, Action Inbox, Work Board, Evidence, News, Memory, and Chat
receive typed projections or safe refs. They cannot copy or become the source
of balances, filing state, obligations, or professional answers. Memory may
retain reviewed preferences only.

### Export, backup, and deletion

Backups and accountant packets are different artifact classes. Each has an
exact manifest, schema, source generation, integrity hash, key ref, created-at,
retention, expiry, and deletion posture. Deleting live data does not claim a
backup or exported packet was deleted. Destructive operations require explicit
scope, preview, confirmation, receipt, and recovery/irreversibility language.

## Abuse Cases That Must Fail Closed

- a transaction description, receipt, or imported formula attempts to issue an
  instruction or broaden authority;
- a personal expense is shifted to a business or another person/entity to meet
  a tax goal without exact evidence and review;
- a UI-provided approval ref is treated as authorization without current scope
  validation;
- a connector read silently becomes background sync or a write;
- a stale compliance source silently changes an obligation or due date;
- an export omits unresolved items or labels estimates as verified facts;
- a failed migration opens an empty book or discards the rollback generation;
- a lost key, unknown external outcome, or incomplete cost is reported as
  success;
- logs, receipts, test evidence, or screenshots contain raw protected values.

## Verification Gate

Each runtime PR must add focused tests for the exact assets and threats it
touches, plus redaction and secret/path scans, schema/migration compatibility,
idempotency/replay, stale revision, revocation-at-start, corruption and partial
failure, backup/restore or safe-disable, CLI/API/UI parity where applicable,
OpenAPI/API manifest and route classification for routes, and Foundation Gate
evidence. Synthetic fixtures are mandatory; real financial or tax material is
forbidden in repository evidence.

## Residual Risk And Blocked Work

Application-level encryption, Keychain integration, secure import parsing,
backup/restore, exact deletion, connector credentials, accountant access,
payments, filings, signatures, and professional collaboration are unimplemented.
FIN-000 records their boundaries only. No financial, accounting, tax, legal,
compliance, payment, filing, connector, provider, model, browser, background,
public-release, or production authority is granted.
