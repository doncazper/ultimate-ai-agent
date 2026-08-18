# ADR-0063: Finance Protected Local Data Boundary

Status: accepted design for FIN-000; no runtime authority or implementation
Date: 2026-08-18

## Context

Finance & Compliance will handle materially more sensitive and integrity-heavy
data than ordinary product metadata. The current repository has no accepted
Finance store, schema, key, migration, backup, connector, or route. FIN-000 must
choose a direction without pretending that direction is implemented.

## Decision

Finance uses a dedicated local repository under the future ECO-001 shared local
data platform. The first implementation target is encrypted SQLite with
transactional migrations and append-oriented history. Database pages, WAL,
journals, indexes, temporary material, protected search data, and eligible
backups are inside the encrypted data plane.

The encryption key is a random per-repository key available only through an
opaque, non-synchronizing macOS Keychain handle. It is distinct from connector
credentials, export keys, backup-wrapping keys, Evidence keys, and any model or
provider secret. React, configuration, environment values, API payloads, CLI
output, receipts, logs, fixtures, screenshots, and ordinary backups never
receive raw key material.

The canonical schema starts at `finance-schema:v1` only when FIN-001 is
separately accepted. Every migration is versioned, idempotent, integrity-checked,
restart-safe, and performed against a new staged copy or transactionally safe
generation. The prior encrypted generation remains the rollback source until
the new generation passes invariant and restore checks. Unknown or failed
migration locks the book; it never silently creates a fresh empty store.

Raw source documents and extracted protected regions are separately addressable
from normalized accounting records. Governance receipts store content-free refs
and hashes. Book, entity, workspace, period, and revision scope are enforced by
the repository rather than by UI filtering.

Backups use a distinct wrapping key and carry store, schema, source-key version,
backup-key version, generation, manifest, and integrity refs. Restore occurs in
a staging repository and atomically replaces live state only after verification.
Loss or revocation of a required key produces an explicit locked or
unrecoverable posture.

Exports are not backups. Accountant packets use a separate exact manifest,
export key, expiry, retention, and deletion contract. Live deletion, backup
deletion, export deletion, credential revocation, and key destruction are
separate destructive operations with separate consequences.

All future adapters implement typed, disabled-by-default boundaries. An adapter
cannot open the repository directly or mint canonical truth. Python Core binds
provider, account, capability, consent, AuthorityLease, exact approval where
required, idempotency, freshness, budgets, safe-disable, and audit immediately
before each start.

## Rejected Alternatives

- plaintext SQLite or protected content in generic application stores;
- one key shared by live data, credentials, exports, and backups;
- React-, connector-, model-, provider-, News-, or Memory-owned finance truth;
- silent in-place migration without a verified rollback generation;
- raw content in governance receipts, logs, fixtures, screenshots, or analytics;
- treating backup, export, deletion, revocation, and key destruction as the same
  operation;
- accepting a broad connector or financial-authority flag.

## Consequences

FIN-000 fixes the future storage and key boundary so schema and UI work cannot
invent weaker ownership. It adds no database, dependency, Keychain item,
migration, backup, parser, route, connector, account access, calculation,
payment, filing, provider/model call, or runtime authority. FIN-001 must still
prove the exact implementation with synthetic data, recovery tests, CLI parity,
redacted evidence, and Foundation Gate results.
