# ECO-005 First-Class Private CRM Threat Model

Status: accepted for the bounded ECO-005 encrypted repository scope on
2026-08-21. This review does not accept product cutover, production key or path
backends, migration, import/export, external sync, account access, provider or
model calls, background work, public release, or production authority.

## Accepted boundary

The only accepted private-data persistence path is one versioned
`PrivateCrmPortfolio` stored by the ECO-001 encrypted local-data platform. CRM
mutations use the repository-only `ecosystem.crm.apply` lane with exact approval
scope, request-context-bound idempotency, optimistic concurrency, payload
bounds, encrypted receipts, and protected undo. Durable governance state may
contain safe refs, versions, counts, hashes, and lifecycle posture only.

The blind index receives one constant portfolio term. Names, contact values,
notes, activities, follow-ups, relationship types, opportunity values, and
other private fields remain inside the encrypted payload. Reusable Boards owns
pipeline lanes, card ordering, and WIP. CRM read projections must revalidate the
current Board, active card, standalone-card subject kind, and exact
pipeline-object subject ref before exposing placement.

## Assets and trust boundaries

| Asset | Boundary | Accepted control | Fail-closed condition |
|---|---|---|---|
| People, organizations, contact points | ECO-001 encrypted private payload | Workspace key binding, versioned aggregate, no value-bearing evidence | Locked key, invalid payload, workspace mismatch, plaintext marker |
| Private workspace context | CRM workspace policy boundary | Exact workspace refs and referential validation | Missing context, cross-workspace link, unknown policy |
| Private Relationships and Dating data | Most restricted CRM workspace | Excluded from global search, Today, Briefing, Memory, and general export | Any permissive shared-surface flag or ambiguous destination |
| Activities and follow-ups | Encrypted CRM aggregate | Exact approval, value-bound replay fingerprint, optimistic version, bounded undo | Stale version, replay mismatch, invalid time, missing context |
| Pipeline/opportunity metadata | CRM aggregate plus live Boards boundary | CRM keeps refs/metadata only; Boards remains sole lane/order/WIP owner | Missing/archived Board or card, wrong subject kind/ref, archived parent |
| Receipts and evidence | Redacted governance plane | Safe refs and content-free summaries only | Private value, raw payload, local path, secret-like material |
| Search index | ECO-001 encrypted/index boundary | Constant portfolio term only | Private field used as a term or cross-workspace query ambiguity |

## Threats and required controls

| Threat | Example | Accepted mitigation and evidence |
|---|---|---|
| Plaintext disclosure | A name or follow-up title appears in SQLite, logs, or a receipt | ECO-001 encryption, constant-term indexing, safe-summary counts/refs, plaintext-marker tests |
| Workspace isolation bypass | Dating context appears in Sales or Today | Portfolio validators require exact workspace membership; Private Relationships policy is immutable and fail-closed |
| Replay confused deputy | Same idempotency ref is retried with a corrected date | Request context includes the exact replacement value; semantic mismatch raises `ECO_IDEMPOTENCY_REPLAY_CONFLICT` |
| Lost update | Two writers mutate the same portfolio version | Exact expected version and transactional ECO-001 write; stale versions fail closed |
| Duplicate pipeline truth | CRM stores a copied stage that diverges from Boards | CRM schema has no lane, position, or WIP field; read projections resolve live Board state |
| Stale Board binding | A Board-only write archives or repoints a CRM card | Every CRM mutation and every pipeline projection validates live Board/card subject binding |
| Evidence leakage | A safe summary includes contact or activity text | Summary is derived only from refs, counts, version, and archive posture; redaction verifier remains mandatory |
| Payload or undo amplification | Repeated edits grow the aggregate without bound | One-megabyte serialized payload cap and bounded undo depth with oldest-history trimming |
| Generic repository bypass | A caller writes CRM data through ECO-001 generic apply | CRM module/record kind is registered repository-only and generic mutation is rejected |
| Implicit authority expansion | Existing M2 or a future UI is treated as ECO-005 cutover | M2 remains a separate governed JSONL compatibility lane; no ECO-005 route, CLI, UI, migration, or cutover is accepted |

## Deferred threat-review gates

The following remain unavailable until a later scoped milestone supplies its own
implementation evidence and accepted threat review:

- production key lifecycle, locked-state UX, path ownership, database/WAL/temp
  plaintext scans, backup/restore, corrupt-state recovery, and rekey drills;
- migration from M0-M2, duplicate resolution, import parsing, export scoping,
  deletion graphs, retention, and recovery receipts;
- Control Center/API/CLI private-value access, authentication, session binding,
  screen locking, accessibility, screenshots, diagnostics, and support export;
- Today, Briefing, Memory, notifications, search, or cross-workspace projections
  beyond the immutable Private Relationships exclusion contract; and
- CRM/account/contact connectors, email or message sends, calendar writes,
  provider/model use, live web/browser activity, background workers, shared
  users, public distribution, or production authority.

## Acceptance evidence

- `docs/decisions/ADR-0067-first-class-private-crm.md`
- `docs/architecture/ECO_005_FIRST_CLASS_PRIVATE_CRM.md`
- `scripts/verify_eco_005_private_crm.py`
- `tests/test_eco_005_private_crm.py`
- `tests/test_eco_005_verifier.py`

The accepted tests cover encrypted-at-rest markers, repository-only writes,
workspace privacy, exact value-bound replay conflict, concurrency, bounded undo,
and live Board-binding rejection. Any later authority or data-movement lane must
add focused adversarial evidence rather than inheriting this acceptance.
