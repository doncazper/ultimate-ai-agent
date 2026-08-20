# ECO-001 Shared Local Data Foundation

Status: accepted bounded foundation on 2026-08-20.

## Accepted implementation

ECO-001 selects application-layer authenticated encryption over SQLite for the
first shared application-data primitive. `EcosystemLocalDataPlatform` supplies:

- an explicit versioned schema with a canonical shape fingerprint, transactional
  initialization, and a fail-closed future-schema check;
- module-owned record metadata and workspace-scoped private payloads;
- injected key lifecycle with create, probe, rotation, loss, and locked states;
- AES-GCM private-value envelopes whose associated data binds workspace,
  record, key version, and record version;
- workspace-keyed blind-index search with deterministic rebuild;
- exact `LocalApprovalAuthority` validation for every exposed write primitive,
  with action, resource, subject, risk, and classification scope checked before
  mutation and expiry evaluated against a core-owned clock;
- optimistic version conflicts, permanent deletion tombstones, encrypted
  replay material, workspace-keyed request fingerprints, and atomic local
  change sets of at most 64 operations;
- archive and exact delete primitives that remove private ciphertext and search
  entries in the same local transaction;
- read-only retention candidate selection limited to records that are both
  archived and expired, with deletion remaining a separate exact operation;
- canonical UTC retention timestamps plus SQLite and deep encrypted-content,
  replay-receipt, search-index, and reference-integrity inspection;
- retry-safe key rotation with a durable pending-cleanup phase, permanent
  historical key-version refs, and reader/rotation coordination;
- size-bounded encrypted full backup, deep authenticated restore preview, and
  atomic no-replace restore to a new destination resolved from a trusted,
  immutable safe-ref mapping with directory durability; and
- a size-bounded, read-only legacy JSON inventory preview that records only a
  source fingerprint and candidate count.

The SQLite governance plane stores safe references, hashes, versions, bounded
timestamps, and status metadata. Private JSON and private search terms appear
only inside authenticated ciphertext. Keys are dependency-injected and are
never read from environment variables or persisted in SQLite. The included
in-memory backend is explicitly test-only and is not a macOS keychain claim.

## Transaction and recovery boundary

A unit of work holds the local approval validation lock across the exact grant
check and `BEGIN IMMEDIATE` transaction, enforces one workspace, validates each
record version, and persists its approval-bound, content-free operation receipt
in the same commit. Private request equality material is authenticated and
encrypted; the visible replay fingerprint is keyed. A conflicting idempotency
replay, stale version, or attempt to reuse a deleted record ref fails closed.
Fault tests prove that an interruption after an intermediate operation rolls
back the complete unit.

Backups use SQLite's online backup API, validate the canonical schema shape,
probe every workspace key, decrypt every private and replay envelope, validate
complete receipt/event bindings, and verify every blind-index token before
encrypting the complete snapshot into an authenticated container. Backup and
restore publication use atomic no-replace links and fsync the destination
directory. Restore preview decrypts only into a temporary location and performs
no cutover; restore-to-new authenticates and validates one in-memory snapshot
before publishing those same bytes. Existing Founder Loop, Work Board, CRM,
task receipt, evidence, memory, and connector stores remain their historical
truth until separately previewed and accepted cutovers.

## Explicitly not accepted

- No production Keychain backend or recovery escrow.
- No existing application-store migration or source deletion.
- No incremental backup, cloud sync, connector, route, UI, background worker,
  or automatic retention execution.
- No external transaction or compensation claim.
- No export/public distribution/production-readiness claim.

These gaps do not prevent dependent application cores from building against
the generic repository boundary. They do prevent any production or cutover
claim. Each app lane must add its module schema, migration preview, authority
binding, performance evidence, and accepted recovery drill before cutover.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_eco_001_local_data.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_eco_001_local_data.py
```

The focused suite covers ciphertext-at-rest, WAL posture, workspace isolation,
exact approval denial, locked and lost keys, atomic rollback, encrypted exact
replay, stale conflicts, deletion tombstones, archive/delete, search rebuild,
retry-safe key cleanup, canonical retention timestamps, deep backup integrity,
backup and JSON size limits, single-open no-replace restore, trusted destination
bindings, directory fsync, transactional initialization rollback, schema-shape
counterfeits, strict JSON numbers, caller-time expiry bypass, active-reader key
rotation, historical key reuse, fractional retention precision, unsupported
schemas, ciphertext tampering, unsafe governance refs, and read-only migration
preview.
