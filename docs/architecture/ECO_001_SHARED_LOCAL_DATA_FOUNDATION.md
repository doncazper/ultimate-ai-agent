# ECO-001 Shared Local Data Foundation

Status: accepted bounded foundation on 2026-08-20.

## Accepted implementation

ECO-001 selects application-layer authenticated encryption over SQLite for the
first shared application-data primitive. `EcosystemLocalDataPlatform` supplies:

- an explicit versioned schema and fail-closed future-schema check;
- module-owned record metadata and workspace-scoped private payloads;
- injected key lifecycle with create, probe, rotation, loss, and locked states;
- AES-GCM private-value envelopes whose associated data binds workspace,
  record, key version, and record version;
- workspace-keyed blind-index search with deterministic rebuild;
- optimistic version conflicts, exact idempotency replay, and atomic local
  change sets of at most 64 operations;
- archive and exact delete primitives that remove private ciphertext and search
  entries in the same local transaction;
- read-only retention candidate selection limited to records that are both
  archived and expired, with deletion remaining a separate exact operation;
- SQLite and reference-integrity inspection;
- encrypted full backup, authenticated restore preview, and restore to a new
  destination without overwriting an existing store; and
- a read-only legacy JSON inventory preview that records only a source
  fingerprint and candidate count.

The SQLite governance plane stores safe references, hashes, versions, bounded
timestamps, and status metadata. Private JSON and private search terms appear
only inside authenticated ciphertext. Keys are dependency-injected and are
never read from environment variables or persisted in SQLite. The included
in-memory backend is explicitly test-only and is not a macOS keychain claim.

## Transaction and recovery boundary

A unit of work uses `BEGIN IMMEDIATE`, enforces one workspace, validates each
record version, and persists its content-free operation receipts in the same
commit. A conflicting idempotency replay or stale record version fails closed.
Fault tests prove that an interruption after an intermediate operation rolls
back the complete unit.

Backups use SQLite's online backup API, run an integrity check, then encrypt the
complete snapshot into an authenticated container before publication. Restore
preview decrypts only into a temporary location and performs no cutover.
Restore-to-new refuses an existing destination. Existing Founder Loop, Work
Board, CRM, task receipt, evidence, memory, and connector stores remain their
historical truth until separately previewed and accepted cutovers.

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
locked and lost keys, atomic rollback, exact replay, stale conflicts,
archive/delete, search rebuild, key rotation, backup corruption, restore
preview, restore-to-new, unsupported schemas, ciphertext tampering, unsafe
governance refs, and read-only migration preview.
